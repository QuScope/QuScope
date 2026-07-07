"""
Quantum Multislice STEM
=======================

Extends quantum_stem.py's single-slice WPOA STEM to full multislice: at each
probe position, the focused probe is propagated through N slices via the same
alternating phase-grating / Fresnel-propagation sequence used in
quantum_multislice_circuit.py. Then the exit wave is scattered into the same
HAADF/ADF/BF/iDPC detectors as run_stem().
"""

from __future__ import annotations
 
from typing import Dict, List, Optional, Tuple
 
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import DiagonalGate, QFTGate
from qiskit.quantum_info import Statevector
 
from quscope.quantum_ctem.quantum_ctem_circuit import (
    relativistic_wavelength,
    interaction_constant,
)
from quscope.quantum_ctem.quantum_stem import (
    STEMDetectors,
    _focused_probe_k,
    _probe_real,
    _propagate_to_detector,
)
from quscope.quantum_ctem.quantum_frozen_phonon import apply_frozen_phonon_to_potential

MAX_SV_QUBITS = 16    # array-multiply diagonals push this higher than the
                      # circuit-synthesis-bound MAX_SV_QUBITS=14 in quantum_stem.py

def fresnel_propagator_phase(N: int, pixel_size: float, wavelength: float,
                              slice_thickness: float) -> np.ndarray:
    """P(k) = exp(-i*pi*lambda*dz*k^2), flattened, unshifted (matches fft2 ordering)."""
    freq = np.fft.fftfreq(N, d=pixel_size)
    KX, KY = np.meshgrid(freq, freq, indexing="ij")
    k2 = KX ** 2 + KY ** 2
    return np.exp(-1j * np.pi * wavelength * slice_thickness * k2).flatten()
 
 
def build_probe_circuit(n_q: int, grating_list: List[np.ndarray],
                         propagator: np.ndarray) -> QuantumCircuit:
    """
    Assemble the quantum multislice circuit (DiagonalGate + QFTGate throughout)
    for one probe position. This is the "show your work" circuit object.
    Use it for depth/gate-count reporting or single-shot demonstrations. 
    Do not call this inside the scan-position loop -> use the array-based 
    `run_stem_multislice` for that.
    """
    n_half = n_q // 2
    qc = QuantumCircuit(n_q, name="Quantum_Multislice_STEM_Probe")
    n_slices = len(grating_list)
    for s, grating in enumerate(grating_list):
        qc.append(DiagonalGate(grating.tolist()), range(n_q))
        if s < n_slices - 1:
            qc.append(QFTGate(n_half), range(n_half))
            qc.append(QFTGate(n_half), range(n_half, n_q))
            qc.append(DiagonalGate(propagator.tolist()), range(n_q))
            qc.append(QFTGate(n_half).inverse(), range(n_half))
            qc.append(QFTGate(n_half).inverse(), range(n_half, n_q))
    return qc
 
 
def _quantum_multislice_exit_wave(probe_r: np.ndarray, slice_potentials: List[np.ndarray],
                                   sigma: float, propagator: np.ndarray,
                                   n_q: int, n_half: int, N: int) -> np.ndarray:
    """
    Propagate a probe through n_slices via alternating phase-grating and
    QFT-based Fresnel propagation. Diagonal gates applied as exact
    elementwise array multiplication. QFT/IQFT applied as real Qiskit
    circuits via Statevector.evolve().
    """
    qft_circuit = QuantumCircuit(n_q)
    qft_circuit.append(QFTGate(n_half), range(n_half))
    qft_circuit.append(QFTGate(n_half), range(n_half, n_q))
    iqft_circuit = QuantumCircuit(n_q)
    iqft_circuit.append(QFTGate(n_half).inverse(), range(n_half))
    iqft_circuit.append(QFTGate(n_half).inverse(), range(n_half, n_q))
 
    state = probe_r.flatten()
    state = state / (np.linalg.norm(state) + 1e-20)
    n_slices = len(slice_potentials)
 
    for s, V_slice in enumerate(slice_potentials):
        grating = np.exp(1j * sigma * V_slice).flatten()
        state = state * grating
        if s < n_slices - 1:
            state = np.asarray(Statevector(state).evolve(qft_circuit).data)
            state = state * propagator
            state = np.asarray(Statevector(state).evolve(iqft_circuit).data)
 
    return state.reshape(N, N)

def run_stem_multislice(
    V_total: np.ndarray,
    pixel_size: float,
    voltage: float,
    n_slices: int = 4,
    slice_thickness: float = 6.5,
    convergence_mrad: float = 15.0,
    defocus_ang: float = 0.0,
    cs_mm: float = 0.0,
    detectors: Optional[STEMDetectors] = None,
    scan_step_px: int = 1,
    max_qubits: int = MAX_SV_QUBITS,
    use_frozen_phonons: bool = False,
    dw=None,
    n_phonon_configs: int = 8,
    rng_seed: int = 0,
) -> Dict:
    """
    Fully quantum multislice STEM image.
 
    Splits `V_total` evenly into `n_slices` slices (pass a list directly via
    `V_total` already pre-split if you want a physically layered structure
    instead of a uniform split -- just pass a 3D array of shape
    (n_slices, N, N) and it will be used as-is).
 
    Parameters mirror quantum_stem.run_stem() plus the slice geometry.
    Note: choose `pixel_size`/grid such that Nyquist k_max = 1/(2*pixel_size)
    comfortably exceeds your detector angles in 1/Angstrom
    (k = mrad*1e-3/wavelength).
 
    Set `use_frozen_phonons=True` with a `DebyeWaller` instance in `dw` to
    average over `n_phonon_configs` independent thermal displacements of
    the whole potential (each config displaces the full structure once,
    then is re-split into slices). This sidesteps the upstream
    apply_frozen_phonon_to_potential(seed=...) vs rng_seed= keyword
    mismatch in quantum_stem.run_stem() by calling with the correct kwarg.
    """
    if detectors is None:
        detectors = STEMDetectors()
 
    if V_total.ndim == 3:
        N = V_total.shape[1]
        base_slices = [V_total[i] for i in range(V_total.shape[0])]
        V_flat_for_phonon = np.sum(V_total, axis=0)
    else:
        N = V_total.shape[0]
        base_slices = [V_total / n_slices] * n_slices
        V_flat_for_phonon = V_total
 
    if use_frozen_phonons and dw is not None:
        phonon_totals = apply_frozen_phonon_to_potential(
            V_flat_for_phonon, dw, n_phonon_configs, rng_seed=rng_seed
        )
        config_slice_sets = [[Vc / n_slices] * n_slices for Vc in phonon_totals]
    else:
        config_slice_sets = [base_slices]
 
    n_q = 2 * int(np.log2(N))
    n_half = n_q // 2
    if n_q > max_qubits:
        raise ValueError(
            f"Grid too large for statevector simulation: n_qubits={n_q} > "
            f"max_qubits={max_qubits}. Shrink the field of view or grid size."
        )
 
    lam = relativistic_wavelength(voltage)
    sigma = interaction_constant(voltage, lam)
    propagator = fresnel_propagator_phase(N, pixel_size, lam, slice_thickness)
 
    probe_k = _focused_probe_k(N, pixel_size, lam, convergence_mrad, defocus_ang, cs_mm)
    det_masks = detectors.masks(N, pixel_size, lam)
    freq = np.fft.fftshift(np.fft.fftfreq(N, d=pixel_size))
    KX, KY = np.meshgrid(freq, freq, indexing="ij")
 
    scan_coords = list(range(0, N, scan_step_px))
    n_scan = len(scan_coords)
    imgs = {name: np.zeros((n_scan, n_scan)) for name in det_masks}
    idpc_x = np.zeros((n_scan, n_scan))
    idpc_y = np.zeros((n_scan, n_scan))
 
    n_configs = len(config_slice_sets)
    for si, ix in enumerate(scan_coords):
        for sj, iy in enumerate(scan_coords):
            probe_r = _probe_real(probe_k, shift_x=ix - N // 2, shift_y=iy - N // 2)
            sigs_acc = {name: 0.0 for name in det_masks}
            kx_acc = ky_acc = 0.0
            for slice_potentials in config_slice_sets:
                psi_exit = _quantum_multislice_exit_wave(
                    probe_r, slice_potentials, sigma, propagator, n_q, n_half, N
                )
                sigs, I_k, _ = _propagate_to_detector(psi_exit, det_masks)
                for name in det_masks:
                    sigs_acc[name] += sigs[name]
                bf_mask = det_masks["BF"]
                kx_acc += np.sum(KX * I_k * bf_mask) / (np.sum(I_k * bf_mask) + 1e-20)
                ky_acc += np.sum(KY * I_k * bf_mask) / (np.sum(I_k * bf_mask) + 1e-20)
            for name in det_masks:
                imgs[name][si, sj] = sigs_acc[name] / n_configs
            idpc_x[si, sj] = kx_acc / n_configs
            idpc_y[si, sj] = ky_acc / n_configs
 
    idpc = np.gradient(idpc_x, axis=0) + np.gradient(idpc_y, axis=1)
    idpc -= idpc.mean()
    idpc /= (max(abs(idpc.max()), abs(idpc.min())) + 1e-12)
 
    return {
        "HAADF": imgs["HAADF"], "ADF": imgs["ADF"], "ABF": imgs["ABF"],
        "BF": imgs["BF"], "iDPC": idpc,
        "KX": KX, "KY": KY,
        "metadata": {
            "voltage": voltage, "wavelength": lam, "pixel_size": pixel_size,
            "convergence_mrad": convergence_mrad, "n_slices": n_slices,
            "slice_thickness": slice_thickness, "N": N, "n_qubits_total": n_q,
        },
        "metrics": {
            "fully_quantum": True,
            "approach": f"Quantum multislice STEM ({n_slices} slices"
                        + (f", {n_configs} frozen-phonon configs" if use_frozen_phonons and dw is not None else "")
                        + ", diagonal-as-array-multiply + QFT-via-circuit)",
        },
    }
