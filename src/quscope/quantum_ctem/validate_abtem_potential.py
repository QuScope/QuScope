#!/usr/bin/env python3
"""
Use abTEM potential directly in quantum simulation for proper validation.
This allows isolating the quantum propagation implementation from potential calculation.
"""

import abtem
import matplotlib.pyplot as plt
import numpy as np
from ase.build import mx2

try:
    from .classical_validation import (
        ClassicalTEMSimulator,
        ValidationMetrics,
        ValidationParameters,
    )
    from .quantum_simulation import QuantumSimulationParameters, QuantumTEMSimulator
except ImportError:
    import os
    import sys

    sys.path.insert(0, os.path.dirname(__file__))
    from classical_validation import (
        ClassicalTEMSimulator,
        ValidationMetrics,
        ValidationParameters,
    )
    from quantum_simulation import QuantumSimulationParameters, QuantumTEMSimulator


def validate_with_abtem_potential():
    """Run validation using abTEM potential in both classical and quantum simulations."""

    print("=" * 70)
    print("VALIDATION WITH ABTEM POTENTIAL")
    print("=" * 70)

    # Create MoS₂ structure with orthogonal cell
    print("\n[1/6] Creating MoS₂ structure...")
    atoms = mx2(formula="MoS2", kind="2H", a=3.18, thickness=3.19, vacuum=2.0)
    atoms = abtem.orthogonalize_cell(atoms) * (3, 2, 1)

    n_mo = len([a for a in atoms if a.symbol == "Mo"])
    n_s = len([a for a in atoms if a.symbol == "S"])
    print(f"  ✓ Created: {len(atoms)} atoms (Mo: {n_mo}, S: {n_s})")
    print(f"  Cell: {atoms.cell.lengths()}")

    # Parameters
    voltage = 200e3  # V
    grid_size = 256
    pixel_size = 0.1  # Angstrom

    # Calculate abTEM potential
    print("\n[2/6] Calculating abTEM potential...")
    potential_abtem = abtem.Potential(
        atoms, sampling=pixel_size, gpts=(grid_size, grid_size), projection="infinite"
    )
    V_abtem = np.array(potential_abtem.project().array)

    print(f"  ✓ abTEM potential:")
    print(f"    Shape: {V_abtem.shape}")
    print(f"    Min: {V_abtem.min():.2f} V·Å")
    print(f"    Max: {V_abtem.max():.2f} V·Å")
    print(f"    Mean: {V_abtem.mean():.2f} V·Å")

    # Calculate phase shift
    # Phase shift χ = σ·V where V is in V·Å
    # Interaction parameter: σ = 2πmeλ/h² with λ in Angstroms
    # This gives σ in units of rad/(V·Å) when properly converted
    from scipy.constants import c, e, h, m_e

    wavelength_m = h / np.sqrt(
        2 * m_e * e * voltage * (1 + e * voltage / (2 * m_e * c**2))
    )
    wavelength_angstrom = wavelength_m * 1e10

    # Corrected σ formula: σ = (me·e·λ)/(2π·ℏ²) × 1e-10 for rad/(V·Å)
    hbar = h / (2 * np.pi)
    sigma = (m_e * e * wavelength_m) / (2 * np.pi * hbar**2)  # rad/(V·m) in SI
    sigma *= 1e-10  # Convert to rad/(V·Å)
    phase = sigma * V_abtem  # rad

    print(f"\n  Phase shift (corrected formula):")
    print(f"    σ = {sigma:.6e} rad/(V·Å)")
    print(f"    Max phase: {np.abs(phase).max():.6f} rad")
    print(f"    Mean phase: {np.abs(phase).mean():.6f} rad")
    print(f"    WPOA valid: {np.abs(phase).max() < np.pi/2}")

    # Run classical simulation
    print("\n[3/6] Running classical simulation (abTEM)...")
    params = ValidationParameters(
        acceleration_voltage=voltage,
        sample_type="mos2",
        thickness=3.19,  # Angstroms
        defocus=200.0,  # Angstroms - matching quantum
        cs=1.0,  # mm - typical Cs
        grid_size=grid_size,
        pixel_size=pixel_size,
    )

    classical_sim = ClassicalTEMSimulator(params)
    I_classical = classical_sim.simulate(atoms)

    print(
        f"  ✓ Classical intensity: [{I_classical.min():.6f}, {I_classical.max():.6f}]"
    )

    # Run quantum simulation WITH abTEM potential
    print("\n[4/6] Running quantum simulation (with abTEM potential)...")
    quantum_params = QuantumSimulationParameters(
        acceleration_voltage=voltage,
        grid_size=grid_size,
        pixel_size=pixel_size,
        defocus=200.0,  # Angstroms - matching classical for phase contrast
        cs=1.0,  # mm - typical microscope Cs
    )

    quantum_sim = QuantumTEMSimulator(quantum_params)

    # HACK: Override the potential calculation to use abTEM's potential
    # This tests if our quantum propagation method is correct
    print("  Using abTEM potential directly in quantum simulation...")
    I_quantum = quantum_sim.simulate_with_potential(V_abtem)

    print(f"  ✓ Quantum intensity: [{I_quantum.min():.6f}, {I_quantum.max():.6f}]")

    # Calculate metrics
    print("\n[5/6] Calculating validation metrics...")
    metrics_calc = ValidationMetrics()

    fidelity = metrics_calc.calculate_fidelity(I_quantum, I_classical)
    rmse = metrics_calc.calculate_rmse(I_quantum, I_classical)
    ssim = metrics_calc.calculate_ssim(I_quantum, I_classical)
    pearson = metrics_calc.calculate_pearson_correlation(I_quantum, I_classical)

    print(f"\n  Metrics:")
    print(f"    Fidelity: {fidelity:.6f} (target: 0.999)")
    print(f"    RMSE: {rmse:.6f} (target: 0.010)")
    print(f"    SSIM: {ssim:.6f} (target: 0.950)")
    print(f"    Pearson: {pearson:.6f} (target: 0.990)")

    # Visualize
    print("\n[6/6] Generating comparison figure...")

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))

    # Row 1: Potentials and phase
    im1 = axes[0, 0].imshow(V_abtem, cmap="viridis")
    axes[0, 0].set_title(
        f"abTEM Potential\nMax: {V_abtem.max():.1f} V·Å", fontweight="bold"
    )
    axes[0, 0].axis("off")
    plt.colorbar(im1, ax=axes[0, 0])

    im2 = axes[0, 1].imshow(phase, cmap="RdBu_r", vmin=-np.pi / 2, vmax=np.pi / 2)
    axes[0, 1].set_title(
        f"Phase Shift\nMax: {np.abs(phase).max():.3f} rad", fontweight="bold"
    )
    axes[0, 1].axis("off")
    plt.colorbar(im2, ax=axes[0, 1], label="rad")

    # Line profile
    center = grid_size // 2
    axes[0, 2].plot(V_abtem[center, :], "b-", linewidth=2, label="Potential")
    axes[0, 2].set_xlabel("X pixel")
    axes[0, 2].set_ylabel("V (V·Å)")
    axes[0, 2].set_title("Line Profile (Y=center)", fontweight="bold")
    axes[0, 2].grid(True, alpha=0.3)
    axes[0, 2].legend()

    # Row 2: Intensities
    im3 = axes[1, 0].imshow(I_classical, cmap="gray")
    axes[1, 0].set_title(
        f"Classical TEM\nRange: [{I_classical.min():.3f}, {I_classical.max():.3f}]",
        fontweight="bold",
    )
    axes[1, 0].axis("off")
    plt.colorbar(im3, ax=axes[1, 0])

    im4 = axes[1, 1].imshow(I_quantum, cmap="gray")
    axes[1, 1].set_title(
        f"Quantum TEM (abTEM pot.)\nRange: [{I_quantum.min():.3f}, {I_quantum.max():.3f}]",
        fontweight="bold",
    )
    axes[1, 1].axis("off")
    plt.colorbar(im4, ax=axes[1, 1])

    diff = np.abs(I_quantum - I_classical)
    im5 = axes[1, 2].imshow(diff, cmap="hot")
    axes[1, 2].set_title(
        f"Absolute Difference\nMax: {diff.max():.3f}", fontweight="bold"
    )
    axes[1, 2].axis("off")
    plt.colorbar(im5, ax=axes[1, 2])

    plt.suptitle(
        f"Validation with abTEM Potential @ {voltage/1e3:.0f} kV\n"
        + f"Fidelity: {fidelity:.4f}, RMSE: {rmse:.4f}, SSIM: {ssim:.4f}, Pearson: {pearson:.4f}",
        fontsize=14,
        fontweight="bold",
    )
    plt.tight_layout()

    save_path = "validation_abtem_potential.png"
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    print(f"✓ Saved: {save_path}")

    plt.show()

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    if fidelity > 0.95:
        print("\n✓ EXCELLENT: Quantum propagation method validated!")
        print("  The quantum Hamiltonian approach correctly reproduces")
        print("  classical multislice results when using the same potential.")
    elif fidelity > 0.80:
        print("\n✓ GOOD: Quantum propagation mostly agrees with classical.")
        print("  Minor differences may be due to numerical methods.")
    else:
        print("\n⚠ WARNING: Significant differences between quantum and classical.")
        print("  This suggests an issue with the quantum propagation method.")

    print("\n" + "=" * 70)

    return I_quantum, I_classical, fidelity


if __name__ == "__main__":
    validate_with_abtem_potential()
