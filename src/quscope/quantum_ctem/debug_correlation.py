#!/usr/bin/env python3
"""
Debug the negative correlation between quantum and classical
"""

import sys

import abtem
import matplotlib.pyplot as plt
import numpy as np
from ase.build import mx2

sys.path.insert(0, "src/quscope/quantum_ctem")

from quantum_simulation import QuantumSimulationParameters, QuantumTEMSimulator

# Setup
atoms = mx2(formula="MoS2", kind="2H", a=3.18, thickness=3.19, vacuum=2.0)
atoms = abtem.orthogonalize_cell(atoms) * (3, 2, 1)

# Get potential
V_pot = abtem.Potential(atoms, sampling=0.1, gpts=(256, 256), projection="infinite")
V = np.array(V_pot.project().array)

print("DEBUGGING NEGATIVE CORRELATION")
print("=" * 60)

# Run quantum WITHOUT defocus/Cs
print("\n1. Quantum with NO aberrations (defocus=0, Cs=0)")
params1 = QuantumSimulationParameters(
    acceleration_voltage=200e3, grid_size=256, pixel_size=0.1, defocus=0.0, cs=0.0
)
sim1 = QuantumTEMSimulator(params1)
I1 = sim1.simulate_with_potential(V, verbose=False)
print(f"   Range: [{I1.min():.3e}, {I1.max():.3e}]")
print(f"   Contrast: {(I1.max()-I1.min())/(I1.max()+I1.min()):.4f}")

# Run quantum WITH defocus (positive)
print("\n2. Quantum with POSITIVE defocus=200Å (underfocus)")
params2 = QuantumSimulationParameters(
    acceleration_voltage=200e3,
    grid_size=256,
    pixel_size=0.1,
    defocus=200.0,  # Positive = underfocus
    cs=1.0,
)
sim2 = QuantumTEMSimulator(params2)
I2 = sim2.simulate_with_potential(V, verbose=False)
print(f"   Range: [{I2.min():.3e}, {I2.max():.3e}]")
print(f"   Contrast: {(I2.max()-I2.min())/(I2.max()+I2.min()):.4f}")

# Run quantum WITH NEGATIVE defocus
print("\n3. Quantum with NEGATIVE defocus=-200Å (overfocus)")
params3 = QuantumSimulationParameters(
    acceleration_voltage=200e3,
    grid_size=256,
    pixel_size=0.1,
    defocus=-200.0,  # Negative = overfocus
    cs=1.0,
)
sim3 = QuantumTEMSimulator(params3)
I3 = sim3.simulate_with_potential(V, verbose=False)
print(f"   Range: [{I3.min():.3e}, {I3.max():.3e}]")
print(f"   Contrast: {(I3.max()-I3.min())/(I3.max()+I3.min()):.4f}")

# Run classical
print("\n4. Classical (abTEM) with defocus=200Å")
from classical_validation import ClassicalTEMSimulator, ValidationParameters

params_class = ValidationParameters(
    acceleration_voltage=200e3,
    sample_type="mos2",
    thickness=3.19,
    defocus=200.0,
    cs=1.0,
    grid_size=256,
    pixel_size=0.1,
)
sim_class = ClassicalTEMSimulator(params_class)
I_class = sim_class.simulate(atoms)
print(f"   Range: [{I_class.min():.3e}, {I_class.max():.3e}]")
print(f"   Contrast: {(I_class.max()-I_class.min())/(I_class.max()+I_class.min()):.4f}")


# Correlations
def pearson(a, b):
    a_norm = (a - a.mean()) / (a.std() + 1e-10)
    b_norm = (b - b.mean()) / (b.std() + 1e-10)
    return np.mean(a_norm * b_norm)


print("\n" + "=" * 60)
print("CORRELATIONS WITH CLASSICAL:")
print(f"  No aberrations:      r = {pearson(I1, I_class):.4f}")
print(f"  Defocus +200Å:       r = {pearson(I2, I_class):.4f}")
print(f"  Defocus -200Å:       r = {pearson(I3, I_class):.4f}")

# Try flipping quantum images
print("\nCORRELATIONS AFTER INVERSION (1 - I):")
print(f"  No aberrations:      r = {pearson(1-I1, I_class):.4f}")
print(f"  Defocus +200Å:       r = {pearson(1-I2, I_class):.4f}")
print(f"  Defocus -200Å:       r = {pearson(1-I3, I_class):.4f}")

# Visualize
fig, axes = plt.subplots(2, 4, figsize=(16, 8))


# Normalize all to [0,1] for fair comparison
def norm(I):
    I_n = I - I.min()
    return I_n / (I_n.max() + 1e-10)


I1_n = norm(I1)
I2_n = norm(I2)
I3_n = norm(I3)
I_class_n = norm(I_class)

axes[0, 0].imshow(I1_n, cmap="gray")
axes[0, 0].set_title(f"Quantum: No aberrations\nr={pearson(I1, I_class):.3f}")
axes[0, 0].axis("off")

axes[0, 1].imshow(I2_n, cmap="gray")
axes[0, 1].set_title(f"Quantum: Defocus +200Å\nr={pearson(I2, I_class):.3f}")
axes[0, 1].axis("off")

axes[0, 2].imshow(I3_n, cmap="gray")
axes[0, 2].set_title(f"Quantum: Defocus -200Å\nr={pearson(I3, I_class):.3f}")
axes[0, 2].axis("off")

axes[0, 3].imshow(I_class_n, cmap="gray")
axes[0, 3].set_title("Classical: Defocus +200Å")
axes[0, 3].axis("off")

# Row 2: Inverted quantum
axes[1, 0].imshow(1 - I1_n, cmap="gray")
axes[1, 0].set_title(f"Inverted: No aberrations\nr={pearson(1-I1, I_class):.3f}")
axes[1, 0].axis("off")

axes[1, 1].imshow(1 - I2_n, cmap="gray")
axes[1, 1].set_title(f"Inverted: Defocus +200Å\nr={pearson(1-I2, I_class):.3f}")
axes[1, 1].axis("off")

axes[1, 2].imshow(1 - I3_n, cmap="gray")
axes[1, 2].set_title(f"Inverted: Defocus -200Å\nr={pearson(1-I3, I_class):.3f}")
axes[1, 2].axis("off")

axes[1, 3].imshow(I_class_n, cmap="gray")
axes[1, 3].set_title("Classical (reference)")
axes[1, 3].axis("off")

plt.tight_layout()
plt.savefig("debug_negative_correlation.png", dpi=200)
print("\n✓ Saved: debug_negative_correlation.png")

print("\n" + "=" * 60)
print("DIAGNOSIS:")
if pearson(I2, I_class) < -0.2:
    print("✗ Images are ANTI-CORRELATED - quantum is inverted!")
    print("  Likely causes:")
    print("  1. Wrong sign in CTF or phase grating")
    print("  2. Bright field vs dark field confusion")
    print("  3. exp(+iχ) vs exp(-iχ) sign convention")
elif pearson(I2, I_class) > 0.7:
    print("✓ Good correlation - images match!")
else:
    print("⚠ Low correlation but not inverted - pattern mismatch")
