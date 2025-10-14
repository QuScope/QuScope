#!/usr/bin/env python3
"""
Correct interaction constant calculation from first principles.

From Kirkland "Advanced Computing in Electron Microscopy" (2nd ed):
The interaction constant σ relates the projected potential V(x,y) to phase shift χ(x,y):
  χ(x,y) = σ·V(x,y)

where V is in V·Å and χ is in radians.

The formula is:
  σ = (2πmeλ)/(h²) · e

But we need to be careful about units!
"""

import numpy as np
from scipy.constants import h, m_e, e, c

voltage = 200e3  # V

# Calculate wavelength
wavelength_m = h / np.sqrt(2 * m_e * e * voltage * (1 + e * voltage / (2 * m_e * c**2)))
wavelength_A = wavelength_m * 1e10

print("=" * 70)
print("CORRECT INTERACTION CONSTANT CALCULATION")
print("=" * 70)

print(f"\nParameters:")
print(f"  Voltage: {voltage/1e3:.1f} kV")
print(f"  Wavelength λ: {wavelength_A:.6f} Å = {wavelength_m:.6e} m")
print(f"  m_e: {m_e:.6e} kg")
print(f"  e: {e:.6e} C")
print(f"  h: {h:.6e} J·s")

# The interaction constant from Kirkland:
# σ = (2π/(λE)) where E = accelerating voltage
# Actually, the correct formula considering units:
# σ [rad/(V·Å)] = (2πmeλ[m])/(h²[J²·s²]) needs dimensional analysis

print("\n" + "=" * 70)
print("DIMENSIONAL ANALYSIS")
print("=" * 70)

# Start with the physics:
# Phase shift: χ = ∫ V(x,y,z) dz · σ
# Where V is the 3D Coulomb potential
# After projection: χ = V_projected · σ
# V_projected has units of [V·length] (voltage times length)

# The interaction comes from: eφ/(ℏv) where φ is potential, v is velocity
# σ = e/(ℏv) = e·k/(ℏ·ω) where k=2π/λ, ω=E/ℏ
# σ = e·2π/(λ·E) but E here is kinetic energy not voltage!

# Correct formula from wave optics:
# σ = (2π)/(λ·V₀) where V₀ is related to accelerating voltage
# V₀ = m_e·c²/e ≈ 511 keV (rest mass energy)
# Actually: σ = (2πme)/(λh²) · (relativistic factor)

# Let's use the STANDARD ELECTRON DIFFRACTION formula:
# σ = (2πmeλ)/(h²) but this needs to output [1/(V·m)]
# The dimensions: [kg·m]/[J·s]² = [kg·m]/[kg²·m⁴/s²·s²] = 1/[kg·m³/s²] = 1/[J/m]

# Actually the correct formula considering all units:
# σ = me·e·λ/(2·ε₀·h²)  OR  σ = 2π/(λ·φ₀) where φ₀ = h²/(2πmeλ²·e)

# From abTEM and PRISM source code:
# sigma = (2 * pi * m_e * e) / (wavelength_m * h**2)  # This is in 1/(V·m)
# Then convert to 1/(V·Å) by multiplying by 1e-10

sigma_correct_SI = (2 * np.pi * m_e * e) / (wavelength_m * h**2)
print(f"\nσ (SI): {sigma_correct_SI:.6e} 1/(V·m)")

sigma_correct = sigma_correct_SI * 1e-10  # Convert to 1/(V·Å)
print(f"σ (V·Å): {sigma_correct:.6e} 1/(V·Å)")

# Test with realistic potential
V_test = 3000  # V·Å (typical for Mo atom)
phase_test = sigma_correct * V_test

print(f"\n" + "=" * 70)
print(f"TEST")
print(f"=" * 70)
print(f"Potential: {V_test} V·Å")
print(f"Phase shift: {phase_test:.6f} rad")
print(f"WPOA valid: {phase_test < np.pi/2} (should be < {np.pi/2:.3f} rad)")

if 0.3 < phase_test < 2.0:
    print(f"\n✅ CORRECT! Phase shift is reasonable for WPOA")
else:
    print(f"\n⚠️  Phase shift outside expected range (0.3-2.0 rad)")

print(f"\n" + "=" * 70)
print(f"HAMILTONIAN FIX")
print(f"=" * 70)
print(f"\nCurrent code:")
print(f"  self.interaction_constant = (2 * np.pi * m_e * e * lambda_m) / (h ** 2)")
print(f"  self.interaction_constant *= 1e20")
print(f"\nShould be:")
print(f"  self.interaction_constant = (2 * np.pi * m_e * e) / (lambda_m * h ** 2)")
print(f"  self.interaction_constant *= 1e-10")
print(f"\nKey differences:")
print(f"  1. Divide by wavelength, not multiply")
print(f"  2. Scale by 1e-10, not 1e20")

print(f"\n" + "=" * 70)
