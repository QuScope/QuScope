#!/usr/bin/env python3
"""
Debug the interaction constant and phase shift calculation.
"""

import numpy as np
from scipy.constants import h, m_e, e, c
import abtem
from ase.build import mx2

# Parameters
voltage = 200e3  # V
wavelength_m = h / np.sqrt(2 * m_e * e * voltage * (1 + e * voltage / (2 * m_e * c**2)))
wavelength_angstrom = wavelength_m * 1e10

print("=" * 70)
print("INTERACTION CONSTANT DEBUG")
print("=" * 70)

print(f"\nVoltage: {voltage/1e3:.1f} kV")
print(f"Wavelength: {wavelength_angstrom:.6f} Å ({wavelength_m:.6e} m)")

# Calculate interaction constant (different methods)
print("\n" + "=" * 70)
print("METHOD 1: Standard formula σ = 2πmeλ/h²")
print("=" * 70)

sigma_1 = (2 * np.pi * m_e * e * wavelength_m) / (h**2)
print(f"  σ (SI): {sigma_1:.6e} rad·m/J")

# Convert to rad/(V·Å)
sigma_1_VA = sigma_1 * 1e10  # m → Å conversion
print(f"  σ (V·Å): {sigma_1_VA:.6e} rad/(V·Å)")

# What the Hamiltonian calculates
print("\n" + "=" * 70)
print("METHOD 2: Hamiltonian's calculation (* 1e20)")
print("=" * 70)

sigma_2 = (2 * np.pi * m_e * e * wavelength_m) / (h**2)
sigma_2 *= 1e20
print(f"  σ: {sigma_2:.6e} (claimed units: 1/(V·Å²))")

# Correct formula
print("\n" + "=" * 70)
print("METHOD 3: Correct σ = 2πme/(λh²) with proper units")
print("=" * 70)

# σ in SI: rad/(V·m) = (2πme)/(λh²) but need to include e for V
# Actually: σ = (2πmeλ)/(h²) gives kg·m/J·s² = kg·m/(kg·m²/s²)·s² = s²/m
# Then multiply by e to get proper units with Volts
# σ [rad/(V·m)] = (2πmeλ)/(h²) 

# The correct formulation from Kirkland:
# σ = (2πmeλ)/(h²) where this has units of [rad/(V·m)]
# To convert to [rad/(V·Å)], multiply by 1e10

sigma_3_SI = (2 * np.pi * m_e * wavelength_m) / (h**2)  # This is actually [1/m] not [rad/(V·m)]
# Need to multiply by e to get voltage units
sigma_3 = sigma_3_SI * e * 1e10  # Now in [rad/(V·Å)]

print(f"  σ (corrected): {sigma_3:.6e} rad/(V·Å)")

# Test with MoS₂ potential
print("\n" + "=" * 70)
print("PHASE SHIFT TEST")
print("=" * 70)

atoms = mx2(formula='MoS2', kind='2H', a=3.18, thickness=3.19, vacuum=2.0)
atoms = abtem.orthogonalize_cell(atoms) * (3, 2, 1)

potential_abtem = abtem.Potential(
    atoms,
    sampling=0.1,
    gpts=(256, 256),
    projection='infinite'
)
V_abtem = np.array(potential_abtem.project().array)

print(f"\nabTEM potential:")
print(f"  Max: {V_abtem.max():.2f} V·Å")
print(f"  Mean: {V_abtem.mean():.2f} V·Å")

# Calculate phase shifts with each method
phase_1 = sigma_1_VA * V_abtem
phase_2 = sigma_2 * V_abtem  
phase_3 = sigma_3 * V_abtem

print(f"\nPhase shifts (χ = σ · V):")
print(f"  Method 1: max = {np.abs(phase_1).max():.6e} rad")
print(f"  Method 2 (Hamiltonian): max = {np.abs(phase_2).max():.6e} rad")
print(f"  Method 3 (corrected): max = {np.abs(phase_3).max():.6e} rad")

print(f"\nExpected phase shift for MoS₂ at 200 kV:")
print(f"  ~0.5-2.0 rad (WPOA valid if < π/2 = 1.571 rad)")

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)

if 0.3 < np.abs(phase_3).max() < 2.0:
    print("\n✅ Method 3 gives reasonable phase shifts!")
    print(f"   Phase: {np.abs(phase_3).max():.3f} rad (within WPOA regime)")
    print(f"\n   The Hamiltonian needs to use:")
    print(f"   σ = {sigma_3:.6e} rad/(V·Å)")
    print(f"\n   Current Hamiltonian uses * 1e20, should use * (e * 1e10)")
else:
    print(f"\n⚠️  Phase shift still problematic: {np.abs(phase_3).max():.6e} rad")
    print("   Expected: 0.5-2.0 rad")

print("\n" + "=" * 70)
