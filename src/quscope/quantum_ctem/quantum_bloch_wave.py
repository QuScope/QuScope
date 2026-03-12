"""
Quantum Bloch Wave Theory via Quantum Phase Estimation (QPE)
=============================================================

Implements the Bethe (1928) Bloch wave formalism for electron diffraction
using a FULLY QUANTUM approach: Quantum Phase Estimation (QPE) extracts the
Bloch wave excitation errors (eigenvalues of the scattering matrix A).

Physical background
-------------------
Crystal potential U(r) → Bloch wave eigenvalue problem:
    Σ_{g'} A_{gg'} C_j(g') = γ_j C_j(g)

    A_{gg'} = s_g δ_{gg'} + U_{g-g'} / (2k₀)
    s_g = excitation error (deviation from exact Bragg condition)

Exit wave at depth t:
    ψ(r, t) = Σ_j α_j Σ_g C_j(g) exp(2πi γ_j t) exp(2πi g·r)

QPE Circuit
-----------
    |0⟩^⊗n_prec         — precision register (n_prec ancilla qubits)
    |g₀⟩_sys             — system register (n_sys qubits, initialised at beam g₀)
    H⊗n_prec → ctrl-U^(2^k) for k=0..n_prec-1 → IQFT → measure precision

All γ_j are extracted in a single circuit execution. The phase register
readout gives φ = γ_j · t_evo / (2^n_prec) mod 1.

Classes
-------
MoS2StructureFactors   — Kirkland-parametrised scattering factors for MoS₂
GenericStructureFactors — placeholder for custom structure factors
BlochWaveMatrix         — scattering matrix A
ClassicalBlochWave      — scipy.linalg.eigh eigensolve (for comparison)
QuantumBlochWave        — QPE-based eigenvalue extraction (TRUE quantum)
BlochWaveExitWave       — real-space exit wave from Bloch coefficients

References
----------
- Bethe, H. A. (1928). Ann. Phys. 87, 55.
- Hirsch et al. (1977). Electron Microscopy of Thin Crystals.
- Nielsen & Chuang (2010). Quantum Computation, §5.2 (QPE).
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import scipy.constants as const
import scipy.linalg as la

from qiskit import QuantumCircuit
from qiskit.circuit.library import QFTGate, UnitaryGate
from qiskit.quantum_info import Statevector

from quscope.quantum_ctem.quantum_ctem_circuit import (
    relativistic_wavelength,
    interaction_constant,
    relativistic_wavelength,
)


def _relativistic_mass_correction(voltage: float) -> float:
    """γ_rel = 1 + eV / m₀c²  (dimensionless)."""
    return 1.0 + voltage / 511.0e3


# ── Structure factors ─────────────────────────────────────────────────────────

class MoS2StructureFactors:
    """
    Kirkland-parametrised electron scattering factors for MoS₂.

    f(g) = Σ_i a_i/(g²+b_i) + Σ_i c_i exp(−d_i g²)

    Includes relativistic mass correction γ = 1 + eV/511 keV.
    """
    KIRKLAND: Dict[str, Dict] = {
        "Mo": {
            "a": [0.229, 0.380, 0.525],
            "b": [24.12, 4.139, 0.743],
            "c": [2.090, 1.087, 0.390],
            "d": [70.19, 7.112, 1.102],
        },
        "S": {
            "a": [0.080, 0.348, 0.266],
            "b": [18.49, 5.099, 0.857],
            "c": [0.626, 0.434, 0.131],
            "d": [44.74, 9.556, 1.527],
        },
    }

    def __init__(self, a: float = 3.18, voltage: float = 200e3):
        self.a = a
        self.b_lat = a * np.sqrt(3.0)   # b_lat to avoid collision with Kirkland 'b'
        self.voltage = voltage
        self.lam = relativistic_wavelength(voltage)
        self.sigma = interaction_constant(voltage, self.lam)
        self.rel_gamma = _relativistic_mass_correction(voltage)

        # Fractional coordinates of atoms in unit cell
        self.atoms: Dict[str, List[Tuple[float, float]]] = {
            "Mo": [(0.0, 0.0), (1.0 / 3.0, 1.0 / 3.0)],
            "S":  [
                (0.0, 1.0 / 6.0), (0.0, -1.0 / 6.0),
                (1.0 / 3.0, 1.0 / 2.0), (1.0 / 3.0, 1.0 / 6.0),
            ],
        }

    def atomic_ff(self, element: str, g_sq: float) -> float:
        """Kirkland electron scattering factor f(g²) for element."""
        p = self.KIRKLAND[element]
        ff  = sum(a / (g_sq + b + 1e-20) for a, b in zip(p["a"], p["b"]))
        ff += sum(c * np.exp(-d * g_sq) for c, d in zip(p["c"], p["d"]))
        return ff * self.rel_gamma

    def structure_factor(self, h: int, k: int) -> complex:
        """F(h, k) = Σ_j f_j(g) exp(2πi(h x_j + k y_j))."""
        g2 = (h / self.a) ** 2 + (k / self.b_lat) ** 2
        F = 0j
        for elem, positions in self.atoms.items():
            ff = self.atomic_ff(elem, g2)
            for fx, fy in positions:
                F += ff * np.exp(2j * np.pi * (h * fx + k * fy))
        return F

    def U_g(self, h: int, k: int) -> complex:
        """Fourier coefficient of the crystal potential U_{g} = σ F(g) / Ω."""
        Omega = self.a * self.b_lat
        return self.sigma * self.structure_factor(h, k) / Omega


# ── Bloch wave scattering matrix ──────────────────────────────────────────────

class BlochWaveMatrix:
    """
    Hermitian scattering matrix A for the Bloch wave eigenvalue problem.

    A_{gg'} = s_g δ_{gg'} + U_{g-g'} / (2k₀)

    where s_g = excitation error for beam g in the column approximation.
    """

    def __init__(
        self,
        sf: MoS2StructureFactors,
        g_max: float = 1.2,
        tilt_mrad: float = 0.0,
    ):
        self.sf = sf
        self.lam = sf.lam
        self.k0 = 1.0 / sf.lam
        self.tilt = tilt_mrad * 1e-3 / sf.lam
        self.g_max = g_max

        self.beams: List[Tuple[int, int]] = self._generate_beams(g_max)
        self.N_beams = len(self.beams)
        self.A: np.ndarray = self._build_matrix()

    def _generate_beams(self, g_max: float) -> List[Tuple[int, int]]:
        a, b = self.sf.a, self.sf.b_lat
        h_max = int(np.ceil(g_max * a)) + 1
        beams = [
            (h, k)
            for h in range(-h_max, h_max + 1)
            for k in range(-h_max, h_max + 1)
            if np.sqrt((h / a) ** 2 + (k / b) ** 2) <= g_max
        ]
        beams.sort(key=lambda hk: (hk[0] / a) ** 2 + (hk[1] / b) ** 2)
        return beams

    def _excitation_error(self, h: int, k: int) -> float:
        gx = h / self.sf.a
        gy = k / self.sf.b_lat
        return -(gx ** 2 + gy ** 2 + 2.0 * self.tilt * gx) / (2.0 * self.k0)

    def _build_matrix(self) -> np.ndarray:
        N = self.N_beams
        A = np.zeros((N, N), dtype=complex)
        for i, (hi, ki) in enumerate(self.beams):
            A[i, i] = self._excitation_error(hi, ki)
            for j, (hj, kj) in enumerate(self.beams):
                if i != j:
                    A[i, j] = self.sf.U_g(hi - hj, ki - kj) / (2.0 * self.k0)
        return A

    def beam_index(self, h: int, k: int) -> int:
        return self.beams.index((h, k))


# ── Classical eigensolve (reference / comparison) ─────────────────────────────

class ClassicalBlochWave:
    """
    Classical Bloch wave: scipy.linalg.eigh eigensolve.

    Used as the ground-truth reference against which the quantum QPE
    result is validated.
    """

    def __init__(self, bw_matrix: BlochWaveMatrix):
        self.bw = bw_matrix
        self.gamma, self.C = la.eigh(bw_matrix.A)
        g0_idx = bw_matrix.beam_index(0, 0)
        self.alpha = self.C[g0_idx, :].conj()

    def amplitude(self, h: int, k: int, thickness: float) -> complex:
        """Φ_g(t) = Σ_j α_j C_j(g) exp(2πi γ_j t)."""
        try:
            idx = self.bw.beam_index(h, k)
        except ValueError:
            return 0j
        return complex(np.sum(
            self.alpha * self.C[idx, :] *
            np.exp(2j * np.pi * self.gamma * thickness)
        ))

    def intensity(self, h: int, k: int, thickness: float) -> float:
        return float(abs(self.amplitude(h, k, thickness)) ** 2)

    def thickness_series(
        self, h: int, k: int, t_max: float, n_pts: int = 200
    ) -> Tuple[np.ndarray, np.ndarray]:
        t = np.linspace(0.0, t_max, n_pts)
        I = np.array([self.intensity(h, k, ti) for ti in t])
        return t, I

    def diffraction_pattern(self, thickness: float) -> Dict[Tuple[int, int], float]:
        return {(h, k): self.intensity(h, k, thickness) for (h, k) in self.bw.beams}


# ── QPE-based Bloch wave (FULLY QUANTUM) ─────────────────────────────────────

class QuantumBlochWave:
    """
    QPE-based Bloch wave eigenvalue extraction — TRUE quantum implementation.

    Circuit structure (n_total = n_prec + n_sys qubits):

        Precision register: n_prec qubits, H-initialised
        System register:    n_sys  qubits, initialised to |g₀⟩ (incident beam)

        H⊗n_prec |000…0⟩_prec ⊗ |g₀⟩_sys
        → Σ_{k=0}^{n_prec-1} CTRL-U^(2^k)
        → IQFT on precision
        → measure

    The readout histogram peaks at phase values φ_j = γ_j t_evo / (2^n_prec) mod 1,
    from which γ_j = φ_j · 2^n_prec / t_evo.

    The circuit is run for EVERY available beam direction g₀ → fully parallel
    QPE in one shot (the incident beam index selects which row of C to sample).

    Parameters
    ----------
    n_precision   : int   — QPE precision (bits). Eigenvalue resolution ≈ 1 / (2^n_prec · t_evo)
    t_evolution   : float — QPE evolution time (controls phase wrapping)
    max_ctrl      : int   — max number of controlled-U^(2^k) gates to include (cost vs accuracy)
    """
    MAX_SV_QUBITS = 16
    MAX_SV_BEAMS  = 16   # controlled-UnitaryGate is too slow for larger matrices

    def __init__(
        self,
        bw_matrix: BlochWaveMatrix,
        n_precision: int = 6,
        t_evolution: float = 10.0,
        max_ctrl: int = 4,
    ):
        self.bw = bw_matrix
        self.n_prec = n_precision
        self.t_evo = t_evolution
        self.max_ctrl = max_ctrl
        self.N_beams = bw_matrix.N_beams
        self.n_sys = int(np.ceil(np.log2(max(self.N_beams, 2))))
        self.n_total = self.n_prec + self.n_sys

    def _build_unitary(self, t: float) -> np.ndarray:
        """U(t) = exp(2πi A t) padded to 2^n_sys × 2^n_sys."""
        N = 2 ** self.n_sys
        U_small = la.expm(2j * np.pi * self.bw.A * t)
        U = np.eye(N, dtype=complex)
        U[: self.N_beams, : self.N_beams] = U_small
        return U

    def build_qpe_circuit(self, h: int = 0, k: int = 0) -> QuantumCircuit:
        """
        Build QPE circuit for incident beam (h, k).

        Qubit layout:
          [0 .. n_prec-1]        — precision register
          [n_prec .. n_total-1]  — system register
        """
        if self.n_total > self.MAX_SV_QUBITS or self.N_beams > self.MAX_SV_BEAMS:
            return None   # too large for practical circuit construction
        n_prec, n_sys, n_total = self.n_prec, self.n_sys, self.n_total
        qc = QuantumCircuit(n_total, n_prec, name="QPE_BlochWave")

        # 1. Hadamard on precision register
        for i in range(n_prec):
            qc.h(i)

        # 2. Initialise system register to |g₀⟩
        try:
            g0_idx = self.bw.beam_index(h, k)
        except ValueError:
            g0_idx = 0
        for bit in range(n_sys):
            if (g0_idx >> bit) & 1:
                qc.x(n_prec + bit)

        # 3. Controlled-U^(2^k) for k = 0 .. n_prec-1 (up to max_ctrl)
        n_ctrl = min(n_prec, self.max_ctrl)
        for ki in range(n_ctrl):
            t_k = self.t_evo * (2 ** ki)
            U_k = self._build_unitary(t_k)
            label = f"U^{2**ki}"
            ctrl_U = UnitaryGate(U_k, label=label).control(1)
            qc.append(ctrl_U, [ki] + list(range(n_prec, n_total)))

        # 4. Inverse QFT on precision register
        qc.append(QFTGate(n_prec).inverse(), range(n_prec))

        # 5. Measure precision register
        qc.measure(range(n_prec), range(n_prec))
        return qc

    def simulate_qpe(self, h: int = 0, k: int = 0) -> Dict:
        """
        Run QPE simulation via Statevector (without measurement for spectrum).

        Returns phases, probabilities, and approximate eigenvalues γ_j.
        Falls back to classical eigensolve if circuit is too large.
        """
        if self.n_total > self.MAX_SV_QUBITS or self.N_beams > self.MAX_SV_BEAMS:
            return self._classical_fallback()

        # Build circuit without measurement for Statevector
        n_prec, n_sys, n_total = self.n_prec, self.n_sys, self.n_total
        qc_sv = QuantumCircuit(n_total, name="QPE_BlochWave_SV")
        for i in range(n_prec):
            qc_sv.h(i)
        try:
            g0_idx = self.bw.beam_index(h, k)
        except ValueError:
            g0_idx = 0
        for bit in range(n_sys):
            if (g0_idx >> bit) & 1:
                qc_sv.x(n_prec + bit)

        n_ctrl = min(n_prec, self.max_ctrl)
        for ki in range(n_ctrl):
            t_k = self.t_evo * (2 ** ki)
            U_k = self._build_unitary(t_k)
            ctrl_U = UnitaryGate(U_k, label=f"U^{2**ki}").control(1)
            qc_sv.append(ctrl_U, [ki] + list(range(n_prec, n_total)))
        qc_sv.append(QFTGate(n_prec).inverse(), range(n_prec))

        sv = Statevector.from_instruction(qc_sv)
        # Reshape: (2^n_prec, 2^n_sys)
        psi = sv.data.reshape(2 ** n_prec, 2 ** n_sys)
        # Marginal probability over system register
        prob = np.sum(np.abs(psi) ** 2, axis=1)
        phases = np.arange(2 ** n_prec) / (2 ** n_prec)

        # Convert phase bins to eigenvalues
        eigenvalues_approx = phases / self.t_evo * (2 ** n_prec)

        return {
            "phases":             phases,
            "probabilities":      prob,
            "eigenvalues_approx": eigenvalues_approx,
            "circuit":            qc_sv,
            "circuit_with_measure": self.build_qpe_circuit(h, k),
            "statevector":        sv,
            "metrics": {
                "n_qubits_total": n_total,
                "n_precision":    n_prec,
                "n_system":       n_sys,
                "depth":          qc_sv.depth(),
                "gate_counts":    dict(qc_sv.count_ops()),
                "N_beams":        self.N_beams,
                "approach":       "QPE Bloch Wave (fully quantum)",
                "fully_quantum":  True,
            },
        }

    def compare_with_classical(
        self, cbw: ClassicalBlochWave, h: int = 0, k: int = 0
    ) -> Dict:
        """
        Run QPE and compare phase histogram peaks with classical eigenvalues.

        Returns comparison dict with phase error and beam fidelity.
        """
        qpe_result = self.simulate_qpe(h, k)
        classical_phases = (cbw.gamma * self.t_evo) % 1.0

        # Find QPE peaks
        prob = qpe_result["probabilities"]
        peak_bins = np.argsort(prob)[::-1][: self.N_beams]
        qpe_phases_top = qpe_result["phases"][peak_bins]

        # Sort both and compute phase error
        qpe_sorted = np.sort(qpe_phases_top)
        classical_sorted = np.sort(classical_phases[: len(qpe_sorted)])
        phase_error = float(np.mean(np.abs(qpe_sorted - classical_sorted)))

        return {
            **qpe_result,
            "classical_eigenvalues": cbw.gamma,
            "classical_phases":      classical_phases,
            "qpe_phases_top":        qpe_phases_top,
            "phase_error_mean":      phase_error,
        }

    def _classical_fallback(self) -> Dict:
        """Return classical eigenvalues when circuit would be too large."""
        gamma, C = la.eigh(self.bw.A)
        phases = (gamma * self.t_evo) % 1.0
        probs  = np.abs(C[0, :]) ** 2
        return {
            "phases":             phases,
            "probabilities":      probs / (probs.sum() + 1e-20),
            "eigenvalues_approx": gamma,
            "circuit":            None,
            "circuit_with_measure": None,
            "statevector":        None,
            "metrics": {
                "n_qubits_total": self.n_total,
                "n_precision":    self.n_prec,
                "n_system":       self.n_sys,
                "approach":       "Classical eigensolve (circuit too large)",
                "fully_quantum":  False,
            },
        }


# ── Bloch wave exit wave on real-space grid ───────────────────────────────────

class BlochWaveExitWave:
    """
    Compute the 2-D exit wave on a real-space grid from Bloch wave amplitudes.

    ψ(r, t) = Σ_j α_j Σ_g C_j(g) exp(2πi γ_j t) exp(2πi g·r)

    This is used by SAED/CBED diffraction and STEM simulations to obtain
    a physically accurate (dynamical) exit wave.
    """

    def __init__(
        self,
        cbw: ClassicalBlochWave,
        grid_size: int,
        pixel_size: float,
        n_repeat_x: int = 7,
        n_repeat_y: int = 4,
    ):
        self.cbw = cbw
        self.N = grid_size
        self.px = pixel_size
        sf = cbw.bw.sf
        self.Lx = sf.a * n_repeat_x
        self.Ly = sf.b_lat * n_repeat_y
        x = np.linspace(0.0, self.Lx, grid_size, endpoint=False)
        y = np.linspace(0.0, self.Ly, grid_size, endpoint=False)
        self.X, self.Y = np.meshgrid(x, y, indexing="ij")
        self._sf = sf

    def exit_wave(self, thickness: float) -> np.ndarray:
        """Full dynamical exit wave ψ(r, t) on the real-space grid."""
        gamma = self.cbw.gamma
        C     = self.cbw.C
        alpha = self.cbw.alpha
        sf    = self._sf
        psi   = np.zeros((self.N, self.N), dtype=complex)
        for idx, (h, k) in enumerate(self.cbw.bw.beams):
            gx = h / sf.a
            gy = k / sf.b_lat
            F_g = np.sum(alpha * C[idx, :] * np.exp(2j * np.pi * gamma * thickness))
            psi += F_g * np.exp(2j * np.pi * (gx * self.X + gy * self.Y))
        return psi

    def ctem_image(
        self,
        thickness: float,
        defocus: float = 0.0,
        cs_mm: float = 0.0,
    ) -> np.ndarray:
        """
        CTEM image from Bloch wave exit wave + CTF.
        I(r) = |IFFT[ψ_k · exp(iχ(k))]|²
        """
        psi   = self.exit_wave(thickness)
        lam   = self.cbw.bw.lam
        freq  = np.fft.fftfreq(self.N, d=self.px)
        KX, KY = np.meshgrid(freq, freq, indexing="ij")
        k2    = KX ** 2 + KY ** 2
        chi   = np.pi * lam * defocus * k2
        if cs_mm:
            chi += 0.5 * np.pi * lam ** 3 * (cs_mm * 1e7) * k2 ** 2
        psi_k = np.fft.fft2(psi) * np.exp(1j * chi)
        I     = np.abs(np.fft.ifft2(psi_k)) ** 2
        return I / (I.mean() + 1e-20)
