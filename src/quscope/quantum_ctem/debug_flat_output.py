#!/usr/bin/env python3
"""
Debug why quantum intensity is flat even with correct interaction constant.
"""

import os
import sys

import abtem
import numpy as np
from ase.build import mx2
from scipy.constants import c, e, h, m_e

sys.path.insert(0, os.path.dirname(__file__))
from quantum_simulation import QuantumSimulationParameters, QuantumTEMSimulator

# Setup
voltage = 200e3
grid_size = 256
pixel_size = 0.1

# Create structure
atoms = mx2(formula="MoS2", kind="2H", a=3.18, thickness=3.19, vacuum=2.0)
atoms = abtem.orthogonalize_cell(atoms) * (3, 2, 1)

# Get abTEM potential
potential_abtem = abtem.Potential(
    atoms, sampling=pixel_size, gpts=(grid_size, grid_size), projection="infinite"
)
V_abtem = np.array(potential_abtem.project().array)

print("=" * 70)
print("DEBUG QUANTUM SIMULATION")
print("=" * 70)

print(f"\nPotential:")
print(f"  Shape: {V_abtem.shape}")
print(f"  Range: [{V_abtem.min():.2f}, {V_abtem.max():.2f}] V·Å")
print(f"  Mean: {V_abtem.mean():.2f} V·Å")
print(f"  Non-zero elements: {np.count_nonzero(V_abtem)}/{V_abtem.size}")

# Calculate expected phase
wavelength_m = h / np.sqrt(2 * m_e * e * voltage * (1 + e * voltage / (2 * m_e * c**2)))
hbar = h / (2 * np.pi)
sigma = (m_e * e * wavelength_m) / (2 * np.pi * hbar**2) * 1e-10

phase = sigma * V_abtem
print(f"\nPhase shift:")
print(f"  σ = {sigma:.6e} rad/(V·Å)")
print(f"  Range: [{phase.min():.6f}, {phase.max():.6f}] rad")
print(f"  Mean: {phase.mean():.6f} rad")

# Transmission function
transmission = np.exp(1j * phase)
print(f"\nTransmission function:")
print(
    f"  |t| range: [{np.abs(transmission).min():.6f}, {np.abs(transmission).max():.6f}]"
)
print(
    f"  Phase range: [{np.angle(transmission).min():.6f}, {np.angle(transmission).max():.6f}] rad"
)

# Create incident wave
psi_incident = np.ones((grid_size, grid_size), dtype=complex)
psi_incident = psi_incident / np.sqrt(np.sum(np.abs(psi_incident) ** 2))

print(f"\nIncident wave:")
print(f"  Norm: {np.sum(np.abs(psi_incident)**2):.6f}")
print(
    f"  |ψ| range: [{np.abs(psi_incident).min():.6e}, {np.abs(psi_incident).max():.6e}]"
)

# Apply transmission
psi_exit = psi_incident * transmission

print(f"\nExit wave (after transmission):")
print(f"  Norm: {np.sum(np.abs(psi_exit)**2):.6f}")
print(f"  |ψ| range: [{np.abs(psi_exit).min():.6e}, {np.abs(psi_exit).max():.6e}]")
print(f"  Real part range: [{psi_exit.real.min():.6e}, {psi_exit.real.max():.6e}]")
print(f"  Imag part range: [{psi_exit.imag.min():.6e}, {psi_exit.imag.max():.6e}]")

# Calculate intensity
intensity_direct = np.abs(psi_exit) ** 2

print(f"\nIntensity (direct calculation):")
print(f"  Range: [{intensity_direct.min():.6e}, {intensity_direct.max():.6e}]")
print(f"  Mean: {intensity_direct.mean():.6e}")
print(f"  Std: {intensity_direct.std():.6e}")
print(
    f"  Contrast: {(intensity_direct.max()-intensity_direct.min())/intensity_direct.mean():.6f}"
)

# Now run through the actual simulator
print(f"\n" + "=" * 70)
print("RUNNING THROUGH SIMULATOR")
print("=" * 70)

params = QuantumSimulationParameters(
    acceleration_voltage=voltage,
    grid_size=grid_size,
    pixel_size=pixel_size,
    defocus=0.0,
)

sim = QuantumTEMSimulator(params)
intensity_sim = sim.simulate_with_potential(V_abtem, verbose=True)

print(f"\nSimulator output:")
print(f"  Range: [{intensity_sim.min():.6e}, {intensity_sim.max():.6e}]")
print(f"  Mean: {intensity_sim.mean():.6e}")
print(
    f"  Contrast: {(intensity_sim.max()-intensity_sim.min())/intensity_sim.mean():.6f}"
)

# Compare
print(f"\n" + "=" * 70)
print("COMPARISON")
print("=" * 70)
print(f"Direct calc vs Simulator:")
print(f"  Max ratio: {intensity_direct.max() / intensity_sim.max():.2e}")
print(f"  Mean ratio: {intensity_direct.mean() / intensity_sim.mean():.2e}")
print(f"  Are they equal? {np.allclose(intensity_direct, intensity_sim)}")
