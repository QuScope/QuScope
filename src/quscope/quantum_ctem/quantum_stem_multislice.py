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

# REMINDER TO ME AFTER WORK: need to add run_stem_multislice for ease of generating the plots
