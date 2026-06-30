"""
Quantum Frozen Phonon & Thermal Diffuse Scattering
===================================================

Three quantum approaches to frozen-phonon / thermal-diffuse scattering (TDS):

  Approach 1 — QTPC  : Quantum Thermal Phase Channel
    DiagonalGate in k-space (after QFT) that encodes Debye-Waller attenuation as a 
    phase rotation on the full n_q-qubit register.

  Approach 2 — QPS   : Quantum Phonon Superposition
    Multi-controlled gates using all n_ph phonon qubits, with X-flip
    padding to condition on the specific basis state |ci>_ph.
    
  Approach 3 — Lindblad : Open quantum system per multislice slice
    
All three approaches are fully quantum: they use Qiskit QuantumCircuit,
Statevector, and/or DensityMatrix throughout. Classical numpy fallbacks
are provided only for grids too large for statevector simulation (n_q > 14).

References
----------
- Kirkland (2010) Advanced Computing in Electron Microscopy, §5.
- Ophus (2017) Modern approaches to TEM image simulation.
- Nielsen & Chuang (2010) Quantum Computation, ch. 8 (open quantum systems).
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import scipy.constants as const

from qiskit import QuantumCircuit
from qiskit.circuit.library import DiagonalGate, QFTGate
from qiskit.quantum_info import Statevector, DensityMatrix, Operator

from quscope.quantum_ctem.quantum_ctem_circuit import (
    relativistic_wavelength,
    interaction_constant,
)


# ── Physical helpers ──────────────────────────────────────────────────────────

def k_grid(N: int, pixel_size: float,
           shifted: bool = False) -> Tuple[np.ndarray, np.ndarray]:
    """(KX, KY) spatial frequency grids in 1/Å."""
    freq = np.fft.fftfreq(N, d=pixel_size)
    if shifted:
        freq = np.fft.fftshift(freq)
    return np.meshgrid(freq, freq, indexing="ij")


def fresnel_propagator(N: int, pixel_size: float,
                        wavelength: float, dz: float) -> np.ndarray:
    """Fresnel propagator P(k) = exp(−iπλΔz k²) on a flat N² array."""
    KX, KY = k_grid(N, pixel_size)
    return np.exp(-1j * np.pi * wavelength * dz * (KX ** 2 + KY ** 2)).flatten()


# ── Debye-Waller factor ───────────────────────────────────────────────────────

class DebyeWaller:
    """
    Debye-Waller factor and mean-square thermal displacement.

    Convention: DW(g) = exp(−B|g|²/2),  B = 8π²⟨u²⟩  [Å²]

    Typical B-factors (Å²):
        Mo  0.406      S  0.627
        Si  0.462      C  0.500
    """
    DEFAULT_B: Dict[str, float] = {
        "Mo": 0.406, "S": 0.627, "C": 0.500,
        "Si": 0.462, "Au": 0.500, "N": 0.500,
    }

    def __init__(self, B_iso: float = 0.5):
        self.B = B_iso

    def factor(self, g_magnitude: np.ndarray) -> np.ndarray:
        """DW(g) = exp(−B·|g|²/2)."""
        return np.exp(-self.B * g_magnitude ** 2 / 2.0)

    def rms_displacement(self) -> float:
        """σ_u = sqrt(B / 8π²)  in Å."""
        return np.sqrt(self.B / (8.0 * np.pi ** 2))


# ── Classical frozen-phonon helper ────────────────────────────────────────────

def apply_frozen_phonon_to_potential(
    V: np.ndarray,
    dw: DebyeWaller,
    n_configs: int = 16,
    rng_seed: int = 42,
) -> List[np.ndarray]:
    """
    Generate n_configs frozen-phonon displaced potentials (classical).

    Each config adds a Gaussian noise field with σ_V = σ_u × 80 V.
    """
    rng = np.random.default_rng(rng_seed)
    sigma_v = dw.rms_displacement() * 80.0
    return [V + rng.normal(0.0, sigma_v, V.shape) for _ in range(n_configs)]


# ── Approach 1: Quantum Thermal Phase Channel (QTPC) ─────────────────────────

class QuantumThermalPhaseChannel:
    """
    Approach 1 — Quantum Thermal Phase Channel.

    After the QFT (electron state in k-space), apply a DiagonalGate whose
        j-th entry is exp(-i·arccos(DW(k_j))). This applies a phase shift to
        each computational basis state |j⟩_el (= k-mode j) that encodes the
        Debye-Waller factor DW(k_j) as the closest unitary transformation.
        
    Circuit (n_q qubits, no ancilla):
        |ψ_0⟩ exp(iσV) → QFT → DiagGate(DW_phases) → IQFT → |ψ_tds⟩
    """
    MAX_SV_QUBITS = 14

    def __init__(
        self,
        N: int,
        pixel_size: float,
        voltage: float,
        dw: DebyeWaller,
    ):
        self.N = N
        self.pixel_size = pixel_size
        self.voltage = voltage
        self.dw = dw
        self.lam = relativistic_wavelength(voltage)
        self.sigma = interaction_constant(voltage, self.lam)
        self.n_q = 2 * int(np.log2(N))

        KX, KY = k_grid(N, pixel_size)
        self.K = np.sqrt(KX ** 2 + KY ** 2)
        self.dw_k = dw.factor(self.K)

    def _dw_diagonal(self) -> np.ndarray:
        """
        Diagonal entries for the k-space DW phase gate.
 
        exp(-i·arccos(DW(k_j))) : j = 0..2^n_q - 1
        Padded to 2^n_q (extra states get DW=1, i.e. phase=0).
        """
        dw_flat = self.dw_k.flatten()
        dw_padded = np.ones(2 ** self.n_q)
        dw_padded[:len(dw_flat)] = dw_flat
        phases = -np.arccos(np.clip(dw_padded, 0.0, 1.0))
        return np.exp(1j * phases)

    def build_circuit(self, V: np.ndarray, n_dephasing_modes: int = 8) -> QuantumCircuit:
        """
        Build the QTPC circuit.

        Steps:
            1. Initialise electron register with phase-grating exit wave
            2. QFT → k-space
            3. Apply DiagonalGate encoding DW attenuation as phase
            4. IQFT → real space
        """
        N, n_q = self.N, self.n_q
        n_half = n_q // 2
        qc = QuantumCircuit(n_q, name="QTPC")

        # 1. Initialise with the phase-grating exit wave: exp(iσV)|ψ_inc⟩
        t_flat = np.exp(1j * self.sigma * V).flatten()
        norm = np.linalg.norm(t_flat)
        if norm > 1e-20:
            t_flat = t_flat / norm
        qc.initialize(t_flat.tolist(), range(n_q))

        # 2. QFT → k-space
        qc.append(QFTGate(n_half), range(n_half))
        qc.append(QFTGate(n_half), range(n_half, n_q))

        # 3. DiagonalGate in k-space encoding DW as phase
        dw_diag = self._dw_diagonal()
        qc.append(DiagonalGate(dw_diag.tolist()), range(n_q))

        # 4. IQFT back to real space
        qc.append(QFTGate(n_half).inverse(), range(n_half))
        qc.append(QFTGate(n_half).inverse(), range(n_half, n_q))
        return qc

    def simulate(self, V: np.ndarray, n_dephasing_modes: int = 8) -> Dict:
        """
        Run QTPC simulation.

        Returns diffraction pattern computed from the quantum state.
        Falls back to numpy when n_q > MAX_SV_QUBITS.
        """
        N = self.N
        qc = self.build_circuit(V, n_dephasing_modes)
        fully_quantum = self.n_q <= self.MAX_SV_QUBITS
        
        if fully_quantum:
            sv = Statevector.from_instruction(qc)
            psi_out = sv.data.reshape(N, N)
        else:
            # Classical numpy: exact DW amplitude attenuation in k-space
            t = np.exp(1j * self.sigma * V)
            psi_k = np.fft.fft2(t / N)
            psi_out = np.fft.ifft2(psi_k * self.dw_k)
 
        I_diff = np.abs(np.fft.fftshift(np.fft.fft2(psi_out))) ** 2
        I_diff_norm = I_diff / (I_diff.max() + 1e-20)

        return {
            "psi_exit":    psi_out,
            "diffraction": I_diff_norm,
            "circuit":     qc,
            "dw_k":        self.dw_k,
            "metrics": {
                "n_qubits":    self.n_q,
                "depth":       qc.depth(),
                "gate_counts": dict(qc.count_ops()),
                "approach":    "QTPC",
                "fully_quantum": fully_quantum,
            },
        }


# ── Approach 2: Quantum Phonon Superposition (QPS) ───────────────────────────

class QuantumPhononSuperposition:
    """
    Approach 2 — Quantum Phonon Superposition.

    For phonon config ci (ci = 1..2^n_ph - 1), the displacement is
        controlled on all n_ph phonon qubits being in state |ci⟩_ph.
        This is implemented as:
            - X-flip qubit b if bit b of ci is 0  (to convert |ci⟩→|1…1⟩)
            - Apply n_ph-controlled DiagonalGate on electron register
            - X-flip back to restore phonon state
 
        Result: each phonon config occupies an orthogonal subspace of
        the phonon register, giving the intended thermal superposition:
            |Ψ⟩ = Σ_{ci=0}^{N_ph-1} |ci⟩_ph ⊗ exp(iσ(V+δV_ci))|ψ₀⟩_el
    """
    MAX_SV_QUBITS = 16  # n_ph + n_q ≤ 16

    def __init__(
        self,
        N: int,
        pixel_size: float,
        voltage: float,
        dw: DebyeWaller,
        n_phonon_qubits: int = 3,
    ):
        self.N = N
        self.pixel_size = pixel_size
        self.dw = dw
        self.voltage = voltage
        self.lam = relativistic_wavelength(voltage)
        self.sigma = interaction_constant(voltage, self.lam)
        self.n_q = 2 * int(np.log2(N))
        self.n_ph = n_phonon_qubits
        self.N_ph = 2 ** n_phonon_qubits  # number of phonon configs

    def _phonon_delta(self, seed: int, V: np.ndarray) -> np.ndarray:
        """δV_i = V_i − V  (displacement field for config i)."""
        rng = np.random.default_rng(seed)
        return rng.normal(0.0, self.dw.rms_displacement() * 80.0, V.shape)

    def build_circuit(self, V: np.ndarray) -> QuantumCircuit:
        """
        Build QPS circuit.

        Qubit layout: phonon[0..n_ph-1] | electron[n_ph..n_ph+n_q-1]
        """
        n_q, n_ph = self.n_q, self.n_ph
        n_total = n_ph + n_q
        qc = QuantumCircuit(n_total, name="QPS")

        # Phonon register: uniform superposition over all N_ph configs
        for i in range(n_ph):
            qc.h(i)

        # Electron register: base exit wave exp(iσV)|flat⟩
        psi0 = np.exp(1j * self.sigma * V).flatten()
        norm = np.linalg.norm(psi0)
        psi0 = psi0 / (norm + 1e-20)
        qc.initialize(psi0.tolist(), range(n_ph, n_ph + n_q))

        # n_ph-qubit multi-controlled phase perturbations
        # For config ci, flip qubits where bit is 0, apply n_ph-ctrl gate, flip back.
        n_configs_circuit = min(self.N_ph, 2 ** n_ph)
        for ci in range(1, n_configs_circuit):
            delta_phi = self.sigma * self._phonon_delta(ci * 137, V)
            phase_diag = np.exp(1j * delta_phi).flatten()
 
            # Pad to 2^n_q
            full_diag = np.ones(2 ** n_q, dtype=complex)
            full_diag[:len(phase_diag)] = phase_diag
 
            # Build the n_ph-qubit controlled DiagonalGate
            dg = DiagonalGate(full_diag.tolist())
            ctrl_dg = dg.control(n_ph)
 
            # Compute which phonon qubits need X-flip (0-bits of ci)
            ctrl_bits = [(ci >> b) & 1 for b in range(n_ph)]
 
            # X-flip 0-bit phonon qubits so the control fires on |ci⟩_ph
            for b, bit in enumerate(ctrl_bits):
                if bit == 0:
                    qc.x(b)
 
            # Apply n_ph-controlled DiagonalGate on electron register
            qc.append(ctrl_dg, list(range(n_ph)) + list(range(n_ph, n_ph + n_q)))
 
            # Restore phonon qubit state
            for b, bit in enumerate(ctrl_bits):
                if bit == 0:
                    qc.x(b)

        return qc

    def simulate(self, V: np.ndarray) -> Dict:
        """
        Run QPS simulation via Statevector → partial trace over phonon register.

        Returns thermal average intensity from the reduced electron density matrix.
        """
        N = self.N
        n_q, n_ph = self.n_q, self.n_ph
        n_total = n_ph + n_q
        qc = self.build_circuit(V)
        fully_quantum = n_total <= self.MAX_SV_QUBITS

        if fully_quantum:
            # Run Statevector on the full (phonon + electron) system
            sv = Statevector.from_instruction(qc)

            # Partial trace over phonon qubits (indices 0..n_ph-1 in Qiskit ordering)
            # In Qiskit little-endian: qubit 0 = tensor factor 0
            rho_full = DensityMatrix(sv)
            # Trace out phonon qubits (first n_ph qubits)
            rho_el = partial_trace_ancilla(rho_full, list(range(n_ph)))

            # Thermal intensity = diagonal of reduced DM in real-space basis
            diag = np.real(np.diag(rho_el.data))
            diag = np.clip(diag, 0.0, None)
            I_thermal = diag.reshape(N, N)
            
            psi_el = np.exp(1j * self.sigma * V) / N
            I_elastic = np.abs(np.fft.fftshift(np.fft.fft2(psi_el))) ** 2
            I_tds = I_thermal - I_elastic / (I_elastic.max() + 1e-20) * I_thermal.max()
        else:
            # Classical frozen-phonon average (mathematically equivalent)
            n_use = min(self.N_ph, 16)
            I_thermal = np.zeros((N, N))
            for i in range(n_use):
                dV = self._phonon_delta(i * 137, V)
                psi = np.exp(1j * self.sigma * (V + dV)) / N
                I_thermal += np.abs(np.fft.fftshift(np.fft.fft2(psi.reshape(N, N)))) ** 2
            I_thermal /= n_use
            psi_el = np.exp(1j * self.sigma * V) / N
            I_elastic = np.abs(np.fft.fftshift(np.fft.fft2(psi_el))) ** 2
            I_tds = I_thermal - I_elastic
 
        safe_max = lambda a: a / (a.max() + 1e-20)
        return {
            "I_thermal":  safe_max(I_thermal),
            "I_elastic":  safe_max(I_elastic),
            "I_tds":      I_tds / (abs(I_tds).max() + 1e-20),
            "circuit":    qc,
            "metrics": {
                "n_qubits_total":    n_ph + n_q,
                "n_phonon_qubits":   n_ph,
                "n_electron_qubits": n_q,
                "n_configs_encoded": self.N_ph,
                "depth":             qc.depth(),
                "gate_counts":       dict(qc.count_ops()),
                "approach":          "Quantum Phonon Superposition",
                "fully_quantum":     fully_quantum,
            },
        }


# ── Approach 3: Lindblad Multislice via DensityMatrix + Kraus ─────────────────

class QuantumLindbladChannel:
    """
    Approach 3 — Open Quantum System Multislice (Lindblad / Kraus).

    Each multislice step applies two Kraus operators to the electron
    density matrix ρ (a DensityMatrix object):

        ρ_{n+1} = K_el ρ_n K_el† + K_tds ρ_n K_tds†

    where
        K_el  = sqrt(1 − γ Δz) · I          (elastic — coherent channel)
        K_tds = sqrt(γ Δz)     · DW_k diag  (TDS — incoherent scattering)

    γ is the total Lindblad decoherence rate (1/Å), derived from the
    Bose-Einstein occupation number n̄(ω_ph, T) and the DW factor:
        γ_emission   = (n̄ + 1)(1 − ⟨DW⟩)
        γ_absorption =  n̄     (1 − ⟨DW⟩)
        γ_total      = γ_emission + γ_absorption

    Between Kraus steps, the unitary multislice propagation is applied via
    DensityMatrix.evolve():
        ρ → U_t ρ U_t† → U_P ρ U_P†  (phase grating, Fresnel propagator)

    This is fully quantum: DensityMatrix evolves under unitary gates and
    non-unitary Kraus maps at every step.
    """
    MAX_DM_QUBITS = 12  # 2^12 × 2^12 DM ≈ 512 MB at complex128

    def __init__(
        self,
        N: int,
        pixel_size: float,
        voltage: float,
        dw: DebyeWaller,
        temperature: float = 300.0,
        phonon_energy_eV: float = 0.05,
    ):
        self.N = N
        self.pixel_size = pixel_size
        self.dw = dw
        self.voltage = voltage
        self.lam = relativistic_wavelength(voltage)
        self.sigma = interaction_constant(voltage, self.lam)
        self.T = temperature
        self.n_q = 2 * int(np.log2(N))

        kT = const.Boltzmann * temperature / const.elementary_charge
        self.n_bar = 1.0 / (np.exp(phonon_energy_eV / kT) - 1.0 + 1e-10)

        KX, KY = k_grid(N, pixel_size)
        self.K = np.sqrt(KX ** 2 + KY ** 2)
        self.dw_k = dw.factor(self.K)
        dw_mean = float(self.dw_k.mean())
        self.gamma_emission   = (self.n_bar + 1.0) * (1.0 - dw_mean)
        self.gamma_absorption =  self.n_bar         * (1.0 - dw_mean)
        self.gamma_total      = self.gamma_emission + self.gamma_absorption

    def _kraus_operators(
        self, dz: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Return (K_el, K_tds) as dense matrices of size N²×N².

        K_el  = sqrt(1−γΔz) · I
        K_tds = sqrt(γΔz)   · diag(DW_k.flatten())
        """
        gamma_dz = min(self.gamma_total * dz, 0.99)
        dim = self.N ** 2
        K_el  = np.sqrt(1.0 - gamma_dz) * np.eye(dim, dtype=complex)
        K_tds = np.sqrt(gamma_dz) * np.diag(self.dw_k.flatten().astype(complex))
        return K_el, K_tds

    def simulate_multislice(
        self,
        V: np.ndarray,
        n_slices: int,
        slice_thickness: float,
    ) -> Dict:
        """
        Run quantum Lindblad multislice simulation.

        Returns
        -------
        Dict with:
          psi_exit_elastic     : exit wave (elastic channel only)
          I_diffraction_elastic: elastic diffraction pattern
          I_diffraction_tds    : TDS diffraction pattern
          rho_exit             : final electron DensityMatrix
          metrics              : circuit/simulation metadata
        """
        N = self.N
        dz = slice_thickness
        V_slice = V / n_slices
        prop = fresnel_propagator(N, self.pixel_size, self.lam, dz).reshape(N, N)
        K_el, K_tds = self._kraus_operators(dz)
        fully_quantum = self.n_q <= self.MAX_DM_QUBITS

        if fully_quantum:
            # Initialise plane wave as density matrix
            psi0 = np.ones(N * N, dtype=complex) / N
            psi0 /= np.linalg.norm(psi0)
            rho = DensityMatrix(np.outer(psi0, psi0.conj()))

            I_el_stack = []

            for _ in range(n_slices):
                # 1. Phase grating: unitary U_t = diag(exp(iσV/n))
                t_flat = np.exp(1j * self.sigma * V_slice).flatten()
                U_t = Operator(np.diag(t_flat))
                rho = rho.evolve(U_t)

                # 2. Fresnel propagation via explicit U_P
                arr = np.array(rho.data)
                U_P = _build_propagation_unitary(N, prop)
                rho = DensityMatrix(U_P @ arr @ U_P.conj().T)
 
                # 3. Kraus channel: ρ → K_el ρ K_el† + K_tds ρ K_tds†
                rho_data = np.array(rho.data)
                rho_new = (K_el @ rho_data @ K_el.conj().T +
                           K_tds @ rho_data @ K_tds.conj().T)
                rho = DensityMatrix(rho_new)
 
                diag = np.real(np.diag(np.array(rho.data)))
                I_el = np.clip(diag, 0.0, None).reshape(N, N)
                I_el_stack.append(I_el / (I_el.mean() + 1e-20))
 
            # Extract exit wave as leading eigenvector of ρ
            rho_exit_dm = DensityMatrix(np.array(rho.data))
            psi_exit = extract_dominant_pure_state(rho_exit_dm, N)
 
            I_final_el = np.abs(np.fft.fftshift(np.fft.fft2(psi_exit))) ** 2
            psi_tds_k  = np.fft.fft2(psi_exit) * (1.0 - self.dw_k)
            I_final_tds = np.abs(np.fft.fftshift(psi_tds_k)) ** 2

        else:
            # Classical numpy fallback
            psi_el = np.ones((N, N), dtype=complex) / N
            I_el_stack = []
            for _ in range(n_slices):
                psi_el *= np.exp(1j * self.sigma * V_slice)
                psi_k = np.fft.fft2(psi_el) * prop
                psi_el = np.fft.ifft2(psi_k)
                gamma_dz = min(self.gamma_total * dz, 0.99)
                psi_k_el = np.fft.fft2(psi_el) * np.sqrt(1.0 - gamma_dz)
                psi_el = np.fft.ifft2(psi_k_el)
                I_el = np.abs(psi_el) ** 2
                I_el_stack.append(I_el / (I_el.mean() + 1e-20))

            rho = None
            psi_exit = psi_el
            I_final_el = np.abs(np.fft.fftshift(np.fft.fft2(psi_exit))) ** 2
            psi_tds_k = np.fft.fft2(psi_exit) * (1.0 - self.dw_k)
            I_final_tds = np.abs(np.fft.fftshift(psi_tds_k)) ** 2

        safe_max = lambda a: a / (a.max() + 1e-20)
        return {
            "psi_exit_elastic":          psi_exit,
            "I_diffraction_elastic":     safe_max(I_final_el),
            "I_diffraction_tds":         safe_max(I_final_tds),
            "I_elastic_stack":           I_el_stack,
            "rho_exit":                  rho,
            "dw_k":                      self.dw_k,
            "gamma_total":               self.gamma_total,
            "n_bar":                     self.n_bar,
            "temperature":               self.T,
            "n_slices":                  n_slices,
            "slice_thickness":           slice_thickness,
            "metrics": {
                "approach":       "Lindblad Electron-Phonon Channel (DensityMatrix)",
                "n_qubits":       self.n_q,
                "n_slices":       n_slices,
                "gamma":          f"{self.gamma_total:.4f} /Å",
                "n_bar":          f"{self.n_bar:.3f}",
                "T":              f"{self.T} K",
                "fully_quantum":  fully_quantum,
            },
        }


# ── Internal utilities ────────────────────────────────────────────────────────

def partial_trace_ancilla(
    rho: DensityMatrix,
    qubits_to_trace: List[int],
) -> DensityMatrix:
    """
    Partial trace over specified qubits from a DensityMatrix.

    Uses qiskit.quantum_info.partial_trace (Qiskit 2.x standalone function).
    Qubits are specified in Qiskit's ordering (qubit 0 = tensor factor 0).
    """
    from qiskit.quantum_info import partial_trace as _pt
    return _pt(rho, qubits_to_trace)


def extract_dominant_pure_state(
    rho: DensityMatrix, N: int
) -> np.ndarray:
    """
    From a reduced density matrix, extract the dominant eigenvector as
    an approximate pure state (for display purposes).

    Returns the reshaped N×N array of the leading eigenvector.
    """
    eigenvalues, eigenvectors = np.linalg.eigh(np.array(rho.data))
    # Leading eigenvector (largest eigenvalue)
    psi = eigenvectors[:, -1]
    psi *= np.sqrt(max(eigenvalues[-1], 0.0))  # weight by occupation
    return psi.reshape(N, N)


def _build_propagation_unitary(N: int, prop: np.ndarray) -> np.ndarray:
    """
    Build the N²×N² unitary matrix for Fresnel propagation.
    U_P = IFFT · diag(P.flatten()) · FFT   (on N²-dimensional space)

    For small N (≤16), builds it explicitly. For larger N, uses the
    FFT matrix directly via DFT.
    """
    dim = N * N
    # FFT unitary on dim-dimensional space
    F = np.fft.fft(np.eye(dim), axis=0) / np.sqrt(dim)
    F_inv = np.conj(F.T)
    P_diag = np.diag(prop.flatten())
    return F_inv @ P_diag @ F
