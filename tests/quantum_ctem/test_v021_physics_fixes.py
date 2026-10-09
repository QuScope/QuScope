"""Regression tests for the v0.2.1 physics fixes (found while building qptycho on QuScope).

Reference values: Kirkland, Advanced Computing in Electron Microscopy (lambda = 0.02508 A and
sigma = 7.288e-4 rad/(V A) at 200 kV).
"""

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import StatePreparation
from qiskit.quantum_info import Statevector

from quscope.quantum_ctem.hamiltonian import (
    FreeParticleHamiltonian,
    HamiltonianParameters,
    LensHamiltonian,
    relativistic_wavelength,
)
from quscope.quantum_ctem.quantum_encoding import QuantumPhaseGrating
from quscope.quantum_ctem.quantum_wave_function import QuantumWaveFunction
from quscope.utils.constants import PhysicalConstants

LAM_200 = 0.025079
SIGMA_200 = 7.2884e-4


def params(nx=8, ny=4, pixel=0.5):
    return HamiltonianParameters(acceleration_voltage=200e3, wavelength=relativistic_wavelength(200e3),
                                 grid_size_x=nx, grid_size_y=ny, pixel_size=pixel)


def test_wavelength_and_interaction_constant():
    assert np.isclose(relativistic_wavelength(200e3), LAM_200, atol=1e-6)
    assert np.isclose(params().interaction_constant, SIGMA_200, rtol=1e-4)
    assert np.isclose(PhysicalConstants.calculate_wavelength(200e3), LAM_200, atol=1e-5)
    assert np.isclose(PhysicalConstants.calculate_sigma(200e3), SIGMA_200, rtol=1e-3)


def test_lens_and_propagator_use_inverse_angstrom():
    p = params()
    kx = np.fft.fftfreq(p.grid_size_x, p.pixel_size)[:, None]
    ky = np.fft.fftfreq(p.grid_size_y, p.pixel_size)[None, :]
    k2 = kx**2 + ky**2
    lens = LensHamiltonian(p, {"defocus": 60.0, "cs": 1.0})  # Cs in mm
    expected = np.pi * p.wavelength * 60.0 * k2 + 0.5 * np.pi * p.wavelength**3 * 1e7 * k2**2
    assert np.allclose(lens.chi, expected)
    free = FreeParticleHamiltonian(p)
    assert np.allclose(free.propagator(30.0), np.exp(-1j * np.pi * p.wavelength * 30.0 * k2))


def test_register_matches_flattening_and_qft_on_nonsquare_grid():
    qwf = QuantumWaveFunction(n_qubits_x=3, n_qubits_y=2)
    rng = np.random.default_rng(0)
    psi = rng.normal(size=(8, 4)) + 1j * rng.normal(size=(8, 4))
    psi /= np.linalg.norm(psi)
    qc = QuantumCircuit(5)
    qc.append(StatePreparation(psi.ravel()), range(5))
    qc.compose(qwf.create_2d_qft_circuit(), inplace=True)
    out = Statevector.from_instruction(qc).data.reshape(8, 4)
    assert np.allclose(out, np.fft.ifft2(psi, norm="ortho"), atol=1e-10)


def test_phase_grating_applies_exact_phase():
    rng = np.random.default_rng(1)
    psi = rng.normal(size=(4, 4)) + 1j * rng.normal(size=(4, 4))
    psi /= np.linalg.norm(psi)
    V = rng.uniform(0, 800, size=(4, 4))
    qc = QuantumCircuit(4)
    qc.append(StatePreparation(psi.ravel()), range(4))
    QuantumPhaseGrating(4, 4).apply(qc, V, SIGMA_200, list(range(4)))
    out = Statevector.from_instruction(qc).data.reshape(4, 4)
    assert np.allclose(out, np.exp(1j * SIGMA_200 * V) * psi, atol=1e-10)
