#!/usr/bin/env python3
"""
Find the correct interaction constant by working backwards from abTEM.
"""

import abtem
import numpy as np
from ase.build import mx2
from scipy.constants import c, e, h, m_e

# Create test structure
atoms = mx2(formula="MoS2", kind="2H", a=3.18, thickness=3.19, vacuum=2.0)
atoms = abtem.orthogonalize_cell(atoms) * (3, 2, 1)

# Get abTEM potential
voltage = 200e3
potential_abtem = abtem.Potential(
    atoms, sampling=0.1, gpts=(256, 256), projection="infinite"
)
V_abtem = np.array(potential_abtem.project().array)

# Get wavelength
wavelength_m = h / np.sqrt(2 * m_e * e * voltage * (1 + e * voltage / (2 * m_e * c**2)))
wavelength_A = wavelength_m * 1e10

print("=" * 70)
print("REVERSE ENGINEER CORRECT σ FROM ABTEM")
print("=" * 70)

print(f"\nSetup:")
print(f"  Voltage: {voltage/1e3:.1f} kV")
print(f"  Wavelength: {wavelength_A:.6f} Å")
print(f"  Potential max: {V_abtem.max():.2f} V·Å")

# For MoS₂ at 200 kV, the phase shift should be approximately 0.5-1.5 rad
# Let's assume phase_max ≈ 1.0 rad as reasonable for WPOA

target_phase = 1.0  # rad (reasonable for Mo/S atoms)
sigma_needed = target_phase / V_abtem.max()

print(f"\n" + "=" * 70)
print(f"WORKING BACKWARDS")
print(f"=" * 70)
print(f"\nIf max phase shift should be ~{target_phase} rad:")
print(f"  σ needed = {sigma_needed:.6e} rad/(V·Å)")

# Now let's see what formula gives this
# Try different formulas:

print(f"\n" + "=" * 70)
print(f"TESTING FORMULAS")
print(f"=" * 70)

# Formula 1: Standard (wrong)
sigma_1 = (2 * np.pi * m_e * e * wavelength_m) / (h**2) * 1e20
print(f"\n1. (2πmeλe)/h² × 1e20:")
print(f"   σ = {sigma_1:.6e}")
print(f"   Ratio to needed: {sigma_1/sigma_needed:.2e}")

# Formula 2: Divide by λ instead
sigma_2 = (2 * np.pi * m_e * e) / (wavelength_m * h**2) * 1e-10
print(f"\n2. (2πme·e)/(λ·h²) × 1e-10:")
print(f"   σ = {sigma_2:.6e}")
print(f"   Ratio to needed: {sigma_2/sigma_needed:.2e}")

# Formula 3: No e in numerator
sigma_3 = (2 * np.pi * m_e * wavelength_m) / (h**2) * 1e10
print(f"\n3. (2πmeλ)/h² × 1e10 (no e):")
print(f"   σ = {sigma_3:.6e}")
print(f"   Ratio to needed: {sigma_3/sigma_needed:.2e}")

# Formula 4: me·e·λ/(h²)
sigma_4 = (m_e * e * wavelength_m) / (h**2) * 1e10
print(f"\n4. (me·e·λ)/h² × 1e10:")
print(f"   σ = {sigma_4:.6e}")
print(f"   Ratio to needed: {sigma_4/sigma_needed:.2e}")

# Formula 5: Check what gives ~1e-6
# If σ ≈ 3e-7 and we have 2πmeλe/h² ≈ 5e26
# Then scale factor = 3e-7 / 5e26 = 6e-34
sigma_5 = (2 * np.pi * m_e * e * wavelength_m) / (h**2)
scale_factor = sigma_needed / sigma_5
print(f"\n5. Standard formula with calculated scale:")
print(f"   Base σ = {sigma_5:.6e}")
print(f"   Scale factor needed = {scale_factor:.6e}")
print(f"   This is close to 1/(e² × 1e20) = {1/(e**2 * 1e20):.6e}")

# The Kirkland formula from literature
# σ [1/(V·Å)] = λ[Å]/(2π·a₀·V₀)
# where a₀ = Bohr radius = 0.529 Å, V₀ = m_e·c²/e = 511 keV

a_0 = 0.529177e-10  # Bohr radius in m
V_0 = m_e * c**2 / e  # Rest mass energy in eV

sigma_6 = wavelength_m / (2 * np.pi * a_0 * V_0)
print(f"\n6. Kirkland: λ/(2π·a₀·V₀):")
print(f"   σ = {sigma_6:.6e} rad/(V·m)")
print(f"   σ = {sigma_6 * 1e-10:.6e} rad/(V·Å)")
print(f"   Ratio to needed: {(sigma_6*1e-10)/sigma_needed:.2e}")

print(f"\n" + "=" * 70)
print(f"CONCLUSION")
print(f"=" * 70)

best_match = None
best_ratio = float("inf")

for i, (sigma, name) in enumerate(
    [
        (sigma_1, "Formula 1"),
        (sigma_2, "Formula 2"),
        (sigma_3, "Formula 3"),
        (sigma_4, "Formula 4"),
        (sigma_6 * 1e-10, "Formula 6 (Kirkland)"),
    ],
    1,
):
    ratio = abs(np.log10(sigma / sigma_needed))
    if ratio < best_ratio:
        best_ratio = ratio
        best_match = (i, name, sigma)

if best_match:
    i, name, sigma = best_match
    print(f"\n✅ Best match: {name}")
    print(f"   σ = {sigma:.6e} rad/(V·Å)")
    print(f"   Off by factor of: {sigma/sigma_needed:.2f}")
