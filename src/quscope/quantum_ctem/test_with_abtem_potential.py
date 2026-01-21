#!/usr/bin/env python3
"""
Direct test: Use abTEM potential in quantum simulation.
This isolates the quantum propagation testing from potential calculation issues.
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


def test_quantum_with_abtem_potential():
    """Test quantum simulation using abTEM's potential directly."""

    print("=" * 70)
    print("QUANTUM VALIDATION USING ABTEM POTENTIAL")
    print("=" * 70)
    print("\nThis test uses the SAME potential for both quantum and classical")
    print("to isolate whether the quantum propagation method is correct.\n")

    # Parameters
    voltage = 200e3
    grid_size = 256
    pixel_size = 0.1

    # Create MoS₂ with orthogonal cell
    print("[1/5] Creating MoS₂ structure...")
    atoms = mx2(formula="MoS2", kind="2H", a=3.18, thickness=3.19, vacuum=2.0)
    atoms = abtem.orthogonalize_cell(atoms) * (3, 2, 1)
    print(f"  ✓ {len(atoms)} atoms, cell: {atoms.cell.lengths()}")

    # Get abTEM potential
    print("\n[2/5] Calculating abTEM potential...")
    potential_abtem = abtem.Potential(
        atoms, sampling=pixel_size, gpts=(grid_size, grid_size), projection="infinite"
    )
    V_abtem = np.array(potential_abtem.project().array)
    print(f"  ✓ Potential: [{V_abtem.min():.1f}, {V_abtem.max():.1f}] V·Å")

    # Classical simulation (abTEM)
    print("\n[3/5] Running classical simulation...")
    params_classical = ValidationParameters(
        acceleration_voltage=voltage,
        sample_type="mos2",
        thickness=3.19,
        defocus=0.0,
        cs=0.0,
        grid_size=grid_size,
        pixel_size=pixel_size,
    )

    classical_sim = ClassicalTEMSimulator(params_classical)
    I_classical = classical_sim.simulate(atoms)
    print(f"  ✓ Classical: [{I_classical.min():.6f}, {I_classical.max():.6f}]")

    # Quantum simulation with abTEM potential
    print("\n[4/5] Running quantum simulation (using abTEM potential)...")
    params_quantum = QuantumSimulationParameters(
        acceleration_voltage=voltage,
        grid_size=grid_size,
        pixel_size=pixel_size,
        defocus=0.0,
    )

    quantum_sim = QuantumTEMSimulator(params_quantum)
    I_quantum = quantum_sim.simulate_with_potential(V_abtem, verbose=False)
    print(f"  ✓ Quantum: [{I_quantum.min():.6f}, {I_quantum.max():.6f}]")

    # Calculate metrics
    print("\n[5/5] Calculating metrics...")
    metrics = ValidationMetrics()

    fidelity = metrics.calculate_fidelity(I_quantum, I_classical)
    rmse = metrics.calculate_rmse(I_quantum, I_classical)
    ssim = metrics.calculate_ssim(I_quantum, I_classical)
    pearson = metrics.calculate_pearson_correlation(I_quantum, I_classical)

    print("\n" + "=" * 70)
    print("VALIDATION METRICS (Same Potential)")
    print("=" * 70)
    print(f"  Fidelity:  {fidelity:.6f}  (target: > 0.999)")
    print(f"  RMSE:      {rmse:.6f}  (target: < 0.010)")
    print(f"  SSIM:      {ssim:.6f}  (target: > 0.950)")
    print(f"  Pearson:   {pearson:.6f}  (target: > 0.990)")
    print("=" * 70)

    # Visualize
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))

    # Row 1: Potential and phase
    im1 = axes[0, 0].imshow(V_abtem, cmap="viridis")
    axes[0, 0].set_title(
        f"abTEM Potential\nMax: {V_abtem.max():.0f} V·Å", fontweight="bold"
    )
    axes[0, 0].axis("off")
    plt.colorbar(im1, ax=axes[0, 0])

    # Phase shift
    from scipy.constants import c, e, h, m_e

    wavelength_m = h / np.sqrt(
        2 * m_e * e * voltage * (1 + e * voltage / (2 * m_e * c**2))
    )
    sigma_SI = (2 * np.pi * m_e * wavelength_m) / h**2
    sigma = sigma_SI * e * 1e10
    phase = sigma * V_abtem

    im2 = axes[0, 1].imshow(phase, cmap="RdBu_r")
    axes[0, 1].set_title(
        f"Phase Shift\nMax: {np.abs(phase).max():.3f} rad", fontweight="bold"
    )
    axes[0, 1].axis("off")
    plt.colorbar(im2, ax=axes[0, 1], label="rad")

    # Histogram
    axes[0, 2].hist(V_abtem.flatten(), bins=50, alpha=0.7, color="blue")
    axes[0, 2].set_xlabel("Potential (V·Å)")
    axes[0, 2].set_ylabel("Count")
    axes[0, 2].set_title("Potential Distribution", fontweight="bold")
    axes[0, 2].set_yscale("log")
    axes[0, 2].grid(True, alpha=0.3)

    # Row 2: Intensities
    im3 = axes[1, 0].imshow(I_classical, cmap="gray")
    axes[1, 0].set_title(
        f"Classical\n[{I_classical.min():.3f}, {I_classical.max():.3f}]",
        fontweight="bold",
    )
    axes[1, 0].axis("off")
    plt.colorbar(im3, ax=axes[1, 0])

    im4 = axes[1, 1].imshow(I_quantum, cmap="gray")
    axes[1, 1].set_title(
        f"Quantum (abTEM pot.)\n[{I_quantum.min():.3f}, {I_quantum.max():.3f}]",
        fontweight="bold",
    )
    axes[1, 1].axis("off")
    plt.colorbar(im4, ax=axes[1, 1])

    diff = np.abs(I_quantum - I_classical)
    im5 = axes[1, 2].imshow(diff, cmap="hot")
    axes[1, 2].set_title(f"|Difference|\nMax: {diff.max():.3f}", fontweight="bold")
    axes[1, 2].axis("off")
    plt.colorbar(im5, ax=axes[1, 2])

    plt.suptitle(
        f"Quantum Validation with abTEM Potential @ {voltage/1e3:.0f} kV\n"
        + f"Fidelity: {fidelity:.4f}, RMSE: {rmse:.4f}, SSIM: {ssim:.4f}, Pearson: {pearson:.4f}",
        fontsize=14,
        fontweight="bold",
    )
    plt.tight_layout()

    save_path = "test_quantum_abtem_potential.png"
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    print(f"\n✓ Saved: {save_path}")

    plt.show()

    # Analysis
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)

    if fidelity > 0.95 and ssim > 0.80:
        print("\n✅ SUCCESS: Quantum propagation is correct!")
        print("   The quantum Hamiltonian method accurately reproduces")
        print("   classical multislice when using the same potential.")
        print("\n   Next step: Fix the Kirkland potential calculation")
        print("   by calibrating against abTEM for each element.")
    elif fidelity > 0.70:
        print("\n⚠️  PARTIAL: Quantum propagation mostly works")
        print(f"   Fidelity {fidelity:.3f} suggests general agreement")
        print("   but numerical differences remain.")
        print("\n   Possible issues:")
        print("   - Discretization differences")
        print("   - CTF application method")
        print("   - Boundary conditions")
    else:
        print("\n❌ FAILURE: Significant discrepancy")
        print("   Even with the same potential, results differ greatly.")
        print("\n   This suggests a fundamental problem with:")
        print("   - Quantum propagation implementation")
        print("   - Phase shift calculation (interaction constant)")
        print("   - CTF application")
        print("   - Grid normalization")

    print("\n" + "=" * 70)

    return I_quantum, I_classical, fidelity


if __name__ == "__main__":
    test_quantum_with_abtem_potential()
