"""
Quantum Electron Diffraction Pattern Simulation
================================================

Implements six diffraction modes, all backed by TRUE quantum circuits
(Qiskit Statevector / DiagonalGate / QFT) where feasible:

  SAED    — Selected-Area Electron Diffraction
              Engine: Bloch wave (dynamical) OR WPOA quantum circuit
  CBED    — Convergent-Beam Electron Diffraction
              Engine: focused probe × Bloch wave exit wave
  Kikuchi — Kikuchi line contrast (thermal diffuse scattering)
              Engine: quantum frozen-phonon ensemble (QTPC / QPS)
  nBD     — Nano-Beam Diffraction
              Engine: quantum multislice (DiagonalGate + QFT per slice)
  EBSD    — Electron Backscatter Diffraction
              Engine: Kikuchi + Bloch wave modulation, tilted geometry
  WPOA    — Weak Phase Object Approximation
              Engine: single quantum DiagonalGate circuit

All six functions return a consistent dict with 'pattern', 'log_pattern',
'psi_exit' (where applicable), 'KX', 'KY', and 'metrics'.

References
----------
- Williams & Carter (2009). Transmission Electron Microscopy.
- Kirkland (2010). Advanced Computing in Electron Microscopy.
- Ophus (2023). 4D-STEM diffraction. arXiv:2301.00345.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.ndimage import gaussian_filter, zoom

from qiskit import QuantumCircuit
from qiskit.circuit.library import DiagonalGate, QFTGate
from qiskit.quantum_info import Statevector

from quscope.quantum_ctem.quantum_ctem_circuit import (
    relativistic_wavelength,
    interaction_constant,
)
from quscope.quantum_ctem.quantum_frozen_phonon import (
    DebyeWaller,
    apply_frozen_phonon_to_potential,
    QuantumThermalPhaseChannel,
)
from quscope.quantum_ctem.quantum_bloch_wave import (
    ClassicalBlochWave,
    BlochWaveExitWave,
)


# ── k-space helpers ───────────────────────────────────────────────────────────

def _k_grid_shifted(N: int, pixel_size: float) -> Tuple[np.ndarray, np.ndarray]:
    freq = np.fft.fftshift(np.fft.fftfreq(N, d=pixel_size))
    return np.meshgrid(freq, freq, indexing="ij")


def _diffraction_pattern(psi: np.ndarray) -> np.ndarray:
    """|FFT(ψ)|² in shifted k-space."""
    return np.abs(np.fft.fftshift(np.fft.fft2(psi))) ** 2


def _focused_probe(
    N: int,
    pixel_size: float,
    wavelength: float,
    convergence_mrad: float,
    defocus: float = 0.0,
    cs_mm: float = 0.0,
    position: Optional[Tuple[int, int]] = None,
) -> np.ndarray:
    """Focused probe in real space, optionally shifted to (ix, iy)."""
    freq = np.fft.fftfreq(N, d=pixel_size)
    KX, KY = np.meshgrid(freq, freq, indexing="ij")
    K = np.sqrt(KX ** 2 + KY ** 2)
    k_c = convergence_mrad * 1e-3 / wavelength
    A = (K <= k_c).astype(float)
    k2 = KX ** 2 + KY ** 2
    chi = np.pi * wavelength * defocus * k2
    if cs_mm:
        chi += 0.5 * np.pi * wavelength ** 3 * (cs_mm * 1e7) * k2 ** 2
    probe_k = A * np.exp(-1j * chi)
    probe_r = np.fft.ifft2(probe_k)
    probe_r /= np.sqrt(np.sum(np.abs(probe_r) ** 2) + 1e-20)
    if position is not None:
        ix, iy = position
        probe_r = np.roll(np.roll(probe_r, ix - N // 2, axis=0), iy - N // 2, axis=1)
    return probe_r


def _quantum_exit_wave(
    V: np.ndarray,
    sigma: float,
    incident: np.ndarray,
    max_qubits: int = 14,
) -> np.ndarray:
    """
    Quantum exit wave via a single DiagonalGate circuit (WPOA).

    For n_q ≤ max_qubits runs Statevector; otherwise falls back to numpy.
    |ψ_exit⟩ = exp(iσV) |ψ_inc⟩
    """
    N = V.shape[0]
    n_q = 2 * int(np.log2(N))
    if n_q <= max_qubits:
        psi = incident.flatten()
        norm = np.linalg.norm(psi)
        if norm < 1e-20:
            psi = np.ones(N * N, dtype=complex) / N
        else:
            psi = psi / norm
        qc = QuantumCircuit(n_q, name="WPOA_ExitWave")
        qc.initialize(psi.tolist(), range(n_q))
        grating = np.exp(1j * sigma * V).flatten()
        qc.append(DiagonalGate(grating.tolist()), range(n_q))
        sv = Statevector.from_instruction(qc)
        return sv.data.reshape(N, N)
    else:
        return incident * np.exp(1j * sigma * V)


# ── 1. SAED — Selected-Area Electron Diffraction ────────────────────────────

def simulate_saed(
    V: np.ndarray,
    pixel_size: float,
    voltage: float,
    cbw: Optional[ClassicalBlochWave] = None,
    thickness: float = 50.0,
    aperture_radius_ang: Optional[float] = None,
    collection_mrad: float = 150.0,
    use_bloch_wave: bool = True,
) -> Dict:
    """
    Selected-Area Electron Diffraction (SAED).

    Engine:
      use_bloch_wave=True  → dynamical Bloch wave exit wave (most accurate)
      use_bloch_wave=False → WPOA quantum circuit (valid for thin samples)

    Parameters
    ----------
    aperture_radius_ang : SA aperture radius in Å (None uses 45% of field)
    collection_mrad     : detector half-angle in mrad
    """
    N = V.shape[0]
    lam = relativistic_wavelength(voltage)
    sigma = interaction_constant(voltage, lam)
    KX, KY = _k_grid_shifted(N, pixel_size)
    K = np.sqrt(KX ** 2 + KY ** 2)

    if use_bloch_wave and cbw is not None:
        bw_ew = BlochWaveExitWave(cbw, grid_size=N, pixel_size=pixel_size)
        psi_exit = bw_ew.exit_wave(thickness)
        method = f"Bloch wave (dynamical, t={thickness:.0f} Å)"
        fully_quantum = False  # Bloch wave is classical + QPE uses classical fallback
    else:
        psi_inc  = np.ones((N, N), dtype=complex) / N
        psi_exit = _quantum_exit_wave(V, sigma, psi_inc)
        method = "WPOA quantum circuit (DiagonalGate)"
        fully_quantum = 2 * int(np.log2(N)) <= 14

    # SA aperture mask in real space
    r_px = (aperture_radius_ang / pixel_size) if aperture_radius_ang else N * 0.45
    cx, cy = N // 2, N // 2
    xs = np.arange(N)
    X, Y = np.meshgrid(xs, xs, indexing="ij")
    R = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
    psi_sel = psi_exit * (R <= r_px).astype(float)

    I = _diffraction_pattern(psi_sel)
    k_coll = collection_mrad * 1e-3 / lam
    I[K > k_coll] = 0.0

    return {
        "pattern":      I,
        "log_pattern":  np.log10(1.0 + I / (I.max() + 1e-20) * 1e4),
        "psi_exit":     psi_exit,
        "KX": KX, "KY": KY,
        "k_extent":     float(KX.max()),
        "pixel_size":   pixel_size,
        "wavelength":   lam,
        "voltage":      voltage,
        "thickness":    thickness,
        "method":       method,
        "mode":         "SAED",
        "metrics": {"fully_quantum": fully_quantum, "approach": method},
    }


# ── 2. CBED — Convergent-Beam Electron Diffraction ───────────────────────────

def simulate_cbed(
    V: np.ndarray,
    pixel_size: float,
    voltage: float,
    cbw: Optional[ClassicalBlochWave] = None,
    thickness: float = 50.0,
    convergence_mrad: float = 10.0,
    defocus: float = 0.0,
    cs_mm: float = 0.0,
    probe_pos_frac: Tuple[float, float] = (0.5, 0.5),
    use_bloch_wave: bool = True,
) -> Dict:
    """
    Convergent-Beam Electron Diffraction (CBED).

    Engine: focused probe × Bloch wave sample exit wave (most accurate),
    or focused probe × WPOA quantum exit wave.
    """
    N = V.shape[0]
    lam = relativistic_wavelength(voltage)
    sigma = interaction_constant(voltage, lam)
    ix = int(probe_pos_frac[0] * N)
    iy = int(probe_pos_frac[1] * N)

    probe = _focused_probe(N, pixel_size, lam, convergence_mrad,
                           defocus, cs_mm, position=(ix, iy))

    if use_bloch_wave and cbw is not None:
        bw_ew = BlochWaveExitWave(cbw, grid_size=N, pixel_size=pixel_size)
        psi_sample = bw_ew.exit_wave(thickness)
        method = f"Bloch wave (t={thickness:.0f} Å, α={convergence_mrad:.0f} mrad)"
        fully_quantum = False
    else:
        psi_inc  = probe.copy()
        psi_sample = _quantum_exit_wave(V, sigma, psi_inc)
        method = f"WPOA quantum circuit (α={convergence_mrad:.0f} mrad)"
        fully_quantum = 2 * int(np.log2(N)) <= 14

    psi_exit = probe * psi_sample
    I = _diffraction_pattern(psi_exit)
    I /= I.max() + 1e-20
    KX, KY = _k_grid_shifted(N, pixel_size)

    return {
        "pattern":          I,
        "log_pattern":      np.log10(1.0 + I * 1e4),
        "psi_exit":         psi_exit,
        "KX": KX, "KY": KY,
        "k_extent":         float(KX.max()),
        "pixel_size":       pixel_size,
        "wavelength":       lam,
        "convergence_mrad": convergence_mrad,
        "probe_position":   (ix, iy),
        "voltage":          voltage,
        "thickness":        thickness,
        "method":           method,
        "mode":             "CBED",
        "metrics": {"fully_quantum": fully_quantum, "approach": method},
    }


# ── 3. Kikuchi — thermal diffuse scattering ───────────────────────────────────

def simulate_kikuchi(
    V: np.ndarray,
    pixel_size: float,
    voltage: float,
    dw: Optional[DebyeWaller] = None,
    n_phonon_configs: int = 32,
    use_quantum_phonon: bool = True,
    rng_seed: int = 42,
) -> Dict:
    """
    Kikuchi line pattern via quantum frozen-phonon ensemble.

    Physics:
    - TDS electrons are computed over frozen-phonon displaced potentials.
    - The Debye-Waller factor attenuates elastic diffraction; remainder
      is scattered to all angles (diffuse background).
    - Kikuchi contrast = gradient of the TDS intensity (excess / deficit bands).

    Engine:
      use_quantum_phonon=True  → QuantumThermalPhaseChannel (QTPC circuit)
      use_quantum_phonon=False → classical frozen-phonon average
    """
    if dw is None:
        dw = DebyeWaller(0.5)

    N = V.shape[0]
    lam = relativistic_wavelength(voltage)
    sigma = interaction_constant(voltage, lam)
    KX_s, KY_s = _k_grid_shifted(N, pixel_size)
    K_s = np.sqrt(KX_s ** 2 + KY_s ** 2)
    dw_factor_s = dw.factor(K_s)

    if use_quantum_phonon:
        # Use QTPC to get DW-attenuated exit wave, then compute TDS
        qtpc = QuantumThermalPhaseChannel(N, pixel_size, voltage, dw)
        result = qtpc.simulate(V, n_dephasing_modes=min(8, N * N // 4))
        psi_thermal = result["psi_exit"]
        # TDS intensity = total - elastic (direct beam)
        psi_el = np.ones((N, N), dtype=complex) * np.exp(1j * sigma * V) / N
        I_total = np.abs(np.fft.fftshift(np.fft.fft2(psi_thermal))) ** 2
        I_elastic = np.abs(np.fft.fftshift(np.fft.fft2(psi_el))) ** 2
        I_tds_raw = np.abs(I_total - I_elastic * dw_factor_s)
        method = f"QTPC quantum frozen phonon"
        fully_quantum = result["metrics"]["fully_quantum"]
    else:
        # Classical accumulation
        configs = apply_frozen_phonon_to_potential(V, dw, n_phonon_configs, rng_seed)
        I_tds_raw = np.zeros((N, N))
        for V_disp in configs:
            V_k = np.fft.fftshift(np.fft.fft2(V_disp))
            I_el_k = np.abs(V_k * sigma * dw_factor_s) ** 2
            I_tds_raw += gaussian_filter(I_el_k, sigma=N / 8.0)
        I_tds_raw /= n_phonon_configs
        method = f"Classical frozen phonon ({n_phonon_configs} configs)"
        fully_quantum = False

    # Kikuchi contrast = signed gradient magnitude of TDS background
    grad_x = np.gradient(gaussian_filter(I_tds_raw, sigma=N / 16.0), axis=1)
    grad_y = np.gradient(gaussian_filter(I_tds_raw, sigma=N / 16.0), axis=0)
    pattern = np.sqrt(grad_x**2 + grad_y**2)
    scale = max(abs(pattern.max()), abs(pattern.min())) + 1e-12
    pattern /= scale
    log_pat = np.arcsinh(pattern * 5.0) / np.arcsinh(5.0)

    return {
        "pattern":          pattern,
        "log_pattern":      log_pat,
        "I_tds_raw":        I_tds_raw / (I_tds_raw.max() + 1e-20),
        "KX": KX_s, "KY": KY_s,
        "k_extent":         float(KX_s.max()),
        "pixel_size":       pixel_size,
        "wavelength":       lam,
        "voltage":          voltage,
        "dw_B":             dw.B,
        "n_phonon_configs": n_phonon_configs,
        "method":           method,
        "mode":             "Kikuchi",
        "metrics": {"fully_quantum": fully_quantum, "approach": method},
    }


# ── 4. nBD — Nano-Beam Diffraction ───────────────────────────────────────────

def simulate_nbd(
    V: np.ndarray,
    pixel_size: float,
    voltage: float,
    convergence_mrad: float = 1.0,
    probe_pos_frac: Tuple[float, float] = (0.5, 0.5),
    n_slices: int = 1,
    slice_thickness: float = 6.5,
) -> Dict:
    """
    Nano-Beam Diffraction (nBD / μED).

    Near-parallel beam (very small α) → sharp spots, no disc overlap.

    Engine:
      n_slices=1 → WPOA quantum circuit (one DiagonalGate)
      n_slices>1 → quantum multislice (DiagonalGate + QFT per slice)
    """
    N = V.shape[0]
    lam = relativistic_wavelength(voltage)
    sigma = interaction_constant(voltage, lam)
    ix = int(probe_pos_frac[0] * N)
    iy = int(probe_pos_frac[1] * N)

    probe = _focused_probe(N, pixel_size, lam, convergence_mrad,
                           0.0, 0.0, position=(ix, iy))

    n_q = 2 * int(np.log2(N))
    if n_slices > 1 and n_q <= 14:
        # Fully quantum multislice
        from quscope.quantum_ctem.quantum_multislice_circuit import (
            QuantumMultisliceParameters, QuantumMultisliceCircuit,
        )
        from quscope.quantum_ctem.quantum_ctem_circuit import QuantumCTEMParameters
        params = QuantumMultisliceParameters(
            acceleration_voltage=voltage,
            grid_size=N,
            pixel_size=pixel_size,
            defocus=0.0,
            cs=0.0,
            slice_thickness=slice_thickness,
        )
        engine = QuantumMultisliceCircuit(params)
        slice_pots = [V / n_slices] * n_slices
        # Use probe as initial state (not plane wave)
        probe_flat = probe.flatten()
        probe_flat /= np.linalg.norm(probe_flat)
        qc = QuantumCircuit(n_q, name="nBD_Multislice")
        qc.initialize(probe_flat.tolist(), range(n_q))
        prop_phase = engine.propagator_phase
        prop_flat = np.exp(1j * prop_phase).flatten()
        qft_x = QFTGate(n_q // 2)
        for V_n in slice_pots:
            grating = np.exp(1j * sigma * V_n).flatten()
            qc.append(DiagonalGate(grating.tolist()), range(n_q))
            qc.append(qft_x, range(n_q // 2))
            qc.append(qft_x, range(n_q // 2, n_q))
            qc.append(DiagonalGate(prop_flat.tolist()), range(n_q))
            qc.append(qft_x.inverse(), range(n_q // 2))
            qc.append(qft_x.inverse(), range(n_q // 2, n_q))
        sv = Statevector.from_instruction(qc)
        psi_exit = sv.data.reshape(N, N)
        method = f"Quantum multislice ({n_slices} slices)"
        fully_quantum = True
    else:
        psi_exit = _quantum_exit_wave(V, sigma, probe)
        method = "WPOA quantum circuit (single slice)"
        fully_quantum = n_q <= 14

    I = _diffraction_pattern(psi_exit)
    I /= I.max() + 1e-20
    KX, KY = _k_grid_shifted(N, pixel_size)

    return {
        "pattern":          I,
        "log_pattern":      np.log10(1.0 + I * 1e5),
        "psi_exit":         psi_exit,
        "KX": KX, "KY": KY,
        "k_extent":         float(KX.max()),
        "pixel_size":       pixel_size,
        "wavelength":       lam,
        "convergence_mrad": convergence_mrad,
        "probe_position":   (ix, iy),
        "voltage":          voltage,
        "method":           method,
        "mode":             "nBD",
        "metrics": {"fully_quantum": fully_quantum, "approach": method},
    }


# ── 5. EBSD — Electron Backscatter Diffraction ───────────────────────────────

def simulate_ebsd(
    V: np.ndarray,
    pixel_size: float,
    voltage: float,
    dw: Optional[DebyeWaller] = None,
    cbw: Optional[ClassicalBlochWave] = None,
    n_phonon_configs: int = 32,
    tilt_deg: float = 70.0,
    use_quantum_phonon: bool = True,
) -> Dict:
    """
    Electron Backscatter Diffraction (EBSD).

    Physical model:
    - High-tilt geometry (≈70°) — backscattered electrons.
    - Base pattern: Kikuchi pattern from quantum frozen phonon (QTPC).
    - Modulation: Bloch wave structure factors at Bragg positions.
    - Geometry: pattern foreshortened by cos(tilt) along tilt axis.
    """
    if dw is None:
        dw = DebyeWaller(0.5)

    kik = simulate_kikuchi(V, pixel_size, voltage, dw,
                           n_phonon_configs, use_quantum_phonon)
    pattern = kik["pattern"].copy()
    lam = kik["wavelength"]
    fully_quantum = kik["metrics"]["fully_quantum"]

    # Modulate with Bloch wave structure factors if available
    bloch_label = "Kikuchi only"
    if cbw is not None:
        N = V.shape[0]
        sf = cbw.bw.sf
        KX_s, KY_s = _k_grid_shifted(N, pixel_size)
        for (h, k) in cbw.bw.beams[:20]:
            gx = h / sf.a
            gy = k / sf.b_lat
            g_mag = np.sqrt(gx ** 2 + gy ** 2)
            if g_mag == 0:
                continue
            dist = np.sqrt((KX_s - gx) ** 2 + (KY_s - gy) ** 2)
            mask = dist < (0.5 / (N * pixel_size))
            if mask.any():
                I_g = cbw.intensity(h, k, thickness=50.0)
                pattern[mask] += I_g * 0.3
        s = max(abs(pattern.max()), abs(pattern.min())) + 1e-12
        pattern /= s
        bloch_label = "Kikuchi + Bloch wave modulation"

    # Foreshortening due to tilt geometry
    tilt_rad = np.deg2rad(tilt_deg)
    Ny, Nx = pattern.shape
    pattern_tilted = zoom(pattern, (1.0, np.cos(tilt_rad)), order=1)
    if pattern_tilted.shape[1] < Nx:
        pad = Nx - pattern_tilted.shape[1]
        pattern_tilted = np.pad(pattern_tilted, ((0, 0), (pad // 2, pad - pad // 2)))
    elif pattern_tilted.shape[1] > Nx:
        excess = pattern_tilted.shape[1] - Nx
        pattern_tilted = pattern_tilted[:, excess // 2: Nx + excess // 2]

    KX_s, KY_s = _k_grid_shifted(V.shape[0], pixel_size)
    log_pat = np.arcsinh(pattern_tilted * 5.0) / np.arcsinh(5.0)

    return {
        "pattern":     pattern_tilted,
        "log_pattern": log_pat,
        "KX": KX_s, "KY": KY_s,
        "k_extent":    float(KX_s.max()),
        "pixel_size":  pixel_size,
        "wavelength":  lam,
        "voltage":     voltage,
        "tilt_deg":    tilt_deg,
        "dw_B":        dw.B,
        "method":      bloch_label,
        "mode":        "EBSD",
        "metrics": {"fully_quantum": fully_quantum, "approach": bloch_label},
    }


# ── 6. WPOA — Weak Phase Object Approximation ─────────────────────────────────

def simulate_wpoa(
    V: np.ndarray,
    pixel_size: float,
    voltage: float,
    collection_mrad: float = 150.0,
) -> Dict:
    """
    Weak Phase Object Approximation diffraction.

    Single quantum DiagonalGate circuit:
        |ψ_exit⟩ = exp(iσV)|ψ_inc⟩

    Valid for thin (< ~5 nm), light-element samples.
    Always fully quantum for N ≤ 128 (n_q ≤ 14).
    """
    N = V.shape[0]
    lam = relativistic_wavelength(voltage)
    sigma = interaction_constant(voltage, lam)

    psi_inc  = np.ones((N, N), dtype=complex) / N
    psi_exit = _quantum_exit_wave(V, sigma, psi_inc)

    I = _diffraction_pattern(psi_exit)
    KX, KY = _k_grid_shifted(N, pixel_size)
    K = np.sqrt(KX ** 2 + KY ** 2)
    k_coll = collection_mrad * 1e-3 / lam
    I[K > k_coll] = 0.0

    n_q = 2 * int(np.log2(N))
    fully_quantum = n_q <= 14

    return {
        "pattern":       I,
        "log_pattern":   np.log10(1.0 + I / (I.max() + 1e-20) * 1e4),
        "psi_exit":      psi_exit,
        "phase":         np.angle(psi_exit),
        "amplitude":     np.abs(psi_exit),
        "KX": KX, "KY": KY,
        "k_extent":      float(KX.max()),
        "pixel_size":    pixel_size,
        "wavelength":    lam,
        "voltage":       voltage,
        "method":         "WPOA quantum circuit (DiagonalGate)",
        "mode":           "WPOA",
        "metrics": {"fully_quantum": fully_quantum, "approach": "WPOA"},
    }
