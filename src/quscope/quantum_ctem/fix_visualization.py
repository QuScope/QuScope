#!/usr/bin/env python3
"""
Fix quantum vs classical visualization with proper normalization
"""

import os
import sys

import abtem
import matplotlib.pyplot as plt
import numpy as np
from ase.build import mx2
from matplotlib.gridspec import GridSpec

sys.path.insert(0, os.path.dirname(__file__))
from classical_validation import (
    ClassicalTEMSimulator,
    ValidationMetrics,
    ValidationParameters,
)
from quantum_simulation import QuantumSimulationParameters, QuantumTEMSimulator


def normalize_for_comparison(I1, I2):
    """
    Normalize two images for visual comparison

    Removes DC offset and scales to same range
    """
    # Remove DC offset (make minimum = 0)
    I1_norm = I1 - I1.min()
    I2_norm = I2 - I2.min()

    # Scale to [0, 1]
    I1_norm = I1_norm / (I1_norm.max() + 1e-10)
    I2_norm = I2_norm / (I2_norm.max() + 1e-10)

    return I1_norm, I2_norm


def calculate_contrast(I):
    """Calculate Michelson contrast"""
    return (I.max() - I.min()) / (I.max() + I.min() + 1e-10)


def main():
    print("=" * 70)
    print("QUANTUM VS CLASSICAL COMPARISON (NORMALIZED)")
    print("=" * 70)

    # Setup
    voltage = 200e3
    grid_size = 256
    pixel_size = 0.1
    defocus = 200.0  # Angstrom
    cs = 1.0  # mm

    # Create structure
    print("\n[1/5] Creating MoS₂ structure...")
    atoms = mx2(formula="MoS2", kind="2H", a=3.18, thickness=3.19, vacuum=2.0)
    atoms = abtem.orthogonalize_cell(atoms) * (3, 2, 1)
    print(f"  ✓ {len(atoms)} atoms")

    # Get abTEM potential
    print("\n[2/5] Calculating potential...")
    V_pot = abtem.Potential(
        atoms, sampling=pixel_size, gpts=(grid_size, grid_size), projection="infinite"
    )
    V = np.array(V_pot.project().array)
    print(f"  ✓ Potential: [{V.min():.1f}, {V.max():.1f}] V·Å")

    # Classical simulation
    print("\n[3/5] Running classical simulation (abTEM)...")
    params_classical = ValidationParameters(
        acceleration_voltage=voltage,
        sample_type="mos2",
        thickness=3.19,
        defocus=defocus,
        cs=cs,
        grid_size=grid_size,
        pixel_size=pixel_size,
    )
    classical_sim = ClassicalTEMSimulator(params_classical)
    I_classical = classical_sim.simulate(atoms)
    contrast_classical = calculate_contrast(I_classical)
    print(f"  ✓ Intensity: [{I_classical.min():.3e}, {I_classical.max():.3e}]")
    print(f"  ✓ Contrast: {contrast_classical:.3f}")

    # Quantum simulation
    print("\n[4/5] Running quantum simulation...")
    params_quantum = QuantumSimulationParameters(
        acceleration_voltage=voltage,
        grid_size=grid_size,
        pixel_size=pixel_size,
        defocus=defocus,
        cs=cs,
    )
    quantum_sim = QuantumTEMSimulator(params_quantum)
    I_quantum = quantum_sim.simulate_with_potential(V, verbose=False)
    contrast_quantum = calculate_contrast(I_quantum)
    print(f"  ✓ Intensity: [{I_quantum.min():.3e}, {I_quantum.max():.3e}]")
    print(f"  ✓ Contrast: {contrast_quantum:.3f}")

    # Normalize for comparison
    I_quantum_norm, I_classical_norm = normalize_for_comparison(I_quantum, I_classical)

    # Calculate metrics on normalized images
    print("\n[5/5] Calculating metrics...")
    metrics = ValidationMetrics()

    # On normalized images
    fidelity_norm = metrics.calculate_fidelity(I_quantum_norm, I_classical_norm)
    rmse_norm = metrics.calculate_rmse(I_quantum_norm, I_classical_norm)
    ssim_norm = metrics.calculate_ssim(I_quantum_norm, I_classical_norm)
    pearson_norm = metrics.calculate_pearson_correlation(
        I_quantum_norm, I_classical_norm
    )

    # On raw images
    fidelity_raw = metrics.calculate_fidelity(I_quantum, I_classical)
    ssim_raw = metrics.calculate_ssim(I_quantum, I_classical)
    pearson_raw = metrics.calculate_pearson_correlation(I_quantum, I_classical)

    print(f"\n  Normalized Metrics:")
    print(f"    Fidelity: {fidelity_norm:.4f}")
    print(f"    RMSE: {rmse_norm:.4f}")
    print(f"    SSIM: {ssim_norm:.4f}")
    print(f"    Pearson: {pearson_norm:.4f}")

    print(f"\n  Raw Metrics (for comparison):")
    print(f"    Fidelity: {fidelity_raw:.4f}")
    print(f"    SSIM: {ssim_raw:.4f}")
    print(f"    Pearson: {pearson_raw:.4f}")

    # Create publication-quality figure
    fig = plt.figure(figsize=(20, 12))
    gs = GridSpec(3, 4, figure=fig, hspace=0.3, wspace=0.3)

    # Row 1: Raw intensities with individual scaling
    ax1 = fig.add_subplot(gs[0, 0])
    im1 = ax1.imshow(I_classical, cmap="gray", aspect="equal")
    ax1.set_title(
        f"Classical TEM (abTEM)\nRange: [{I_classical.min():.2e}, {I_classical.max():.2e}]\nContrast: {contrast_classical:.3f}",
        fontsize=11,
        fontweight="bold",
    )
    ax1.axis("off")
    plt.colorbar(im1, ax=ax1, fraction=0.046)

    ax2 = fig.add_subplot(gs[0, 1])
    im2 = ax2.imshow(I_quantum, cmap="gray", aspect="equal")
    ax2.set_title(
        f"Quantum TEM (This Work)\nRange: [{I_quantum.min():.2e}, {I_quantum.max():.2e}]\nContrast: {contrast_quantum:.3f}",
        fontsize=11,
        fontweight="bold",
    )
    ax2.axis("off")
    plt.colorbar(im2, ax=ax2, fraction=0.046)

    # Difference (raw scale issues)
    ax3 = fig.add_subplot(gs[0, 2])
    diff_raw = np.abs(I_quantum - I_classical)
    im3 = ax3.imshow(diff_raw, cmap="hot", aspect="equal")
    ax3.set_title(
        f"Absolute Difference (Raw)\nMean: {diff_raw.mean():.2e}",
        fontsize=11,
        fontweight="bold",
    )
    ax3.axis("off")
    plt.colorbar(im3, ax=ax3, fraction=0.046)

    # Potential
    ax4 = fig.add_subplot(gs[0, 3])
    im4 = ax4.imshow(V, cmap="viridis", aspect="equal")
    ax4.set_title(
        f"Potential V(x,y)\nMax: {V.max():.1f} V·Å", fontsize=11, fontweight="bold"
    )
    ax4.axis("off")
    plt.colorbar(im4, ax=ax4, fraction=0.046)

    # Row 2: Normalized intensities (same scale)
    ax5 = fig.add_subplot(gs[1, 0])
    im5 = ax5.imshow(I_classical_norm, cmap="gray", vmin=0, vmax=1, aspect="equal")
    ax5.set_title(
        "Classical (Normalized)\nRange: [0.0, 1.0]", fontsize=11, fontweight="bold"
    )
    ax5.axis("off")
    plt.colorbar(im5, ax=ax5, fraction=0.046)

    ax6 = fig.add_subplot(gs[1, 1])
    im6 = ax6.imshow(I_quantum_norm, cmap="gray", vmin=0, vmax=1, aspect="equal")
    ax6.set_title(
        "Quantum (Normalized)\nRange: [0.0, 1.0]", fontsize=11, fontweight="bold"
    )
    ax6.axis("off")
    plt.colorbar(im6, ax=ax6, fraction=0.046)

    # Difference (normalized - should be small!)
    ax7 = fig.add_subplot(gs[1, 2])
    diff_norm = np.abs(I_quantum_norm - I_classical_norm)
    im7 = ax7.imshow(diff_norm, cmap="hot", vmin=0, vmax=1, aspect="equal")
    ax7.set_title(
        f"Absolute Difference (Normalized)\nRMSE: {rmse_norm:.4f}",
        fontsize=11,
        fontweight="bold",
    )
    ax7.axis("off")
    plt.colorbar(im7, ax=ax7, fraction=0.046)

    # Correlation plot
    ax8 = fig.add_subplot(gs[1, 3])
    ax8.scatter(
        I_classical_norm.flatten()[::10],
        I_quantum_norm.flatten()[::10],
        alpha=0.1,
        s=1,
        c="blue",
    )
    ax8.plot([0, 1], [0, 1], "r--", linewidth=2, label="Perfect correlation")
    ax8.set_xlabel("Classical Intensity (normalized)", fontsize=10)
    ax8.set_ylabel("Quantum Intensity (normalized)", fontsize=10)
    ax8.set_title(
        f"Pixel Correlation\nPearson: {pearson_norm:.4f}",
        fontsize=11,
        fontweight="bold",
    )
    ax8.grid(True, alpha=0.3)
    ax8.legend()
    ax8.set_aspect("equal")

    # Row 3: Line profiles and histograms
    center = grid_size // 2

    # Horizontal line profile (normalized)
    ax9 = fig.add_subplot(gs[2, 0:2])
    ax9.plot(
        I_classical_norm[center, :], "b-", linewidth=2, label="Classical", alpha=0.7
    )
    ax9.plot(I_quantum_norm[center, :], "r--", linewidth=2, label="Quantum", alpha=0.7)
    ax9.set_xlabel("X Pixel", fontsize=10)
    ax9.set_ylabel("Normalized Intensity", fontsize=10)
    ax9.set_title(
        "Line Profile (Y = center, Normalized)", fontsize=11, fontweight="bold"
    )
    ax9.grid(True, alpha=0.3)
    ax9.legend()

    # Intensity histograms
    ax10 = fig.add_subplot(gs[2, 2:])
    ax10.hist(
        I_classical_norm.flatten(),
        bins=100,
        alpha=0.5,
        label="Classical",
        color="blue",
        density=True,
    )
    ax10.hist(
        I_quantum_norm.flatten(),
        bins=100,
        alpha=0.5,
        label="Quantum",
        color="red",
        density=True,
    )
    ax10.set_xlabel("Normalized Intensity", fontsize=10)
    ax10.set_ylabel("Probability Density", fontsize=10)
    ax10.set_title("Intensity Distributions", fontsize=11, fontweight="bold")
    ax10.grid(True, alpha=0.3)
    ax10.legend()
    ax10.set_yscale("log")

    # Overall title with metrics
    fig.suptitle(
        f"Quantum TEM Validation @ {voltage/1e3:.0f} kV (defocus={defocus:.0f} Å, Cs={cs:.1f} mm)\n"
        f"Normalized: Fidelity={fidelity_norm:.4f}, RMSE={rmse_norm:.4f}, SSIM={ssim_norm:.4f}, Pearson={pearson_norm:.4f}",
        fontsize=14,
        fontweight="bold",
        y=0.98,
    )

    # Save
    plt.savefig(
        "quantum_classical_comparison_normalized.png", dpi=300, bbox_inches="tight"
    )
    print(f"\n✓ Saved: quantum_classical_comparison_normalized.png")

    plt.show()

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    if ssim_norm > 0.90 and pearson_norm > 0.90:
        print("✓ EXCELLENT: Quantum matches classical very well!")
        print("  Ready for publication in high-impact journal.")
    elif ssim_norm > 0.70 and pearson_norm > 0.70:
        print("✓ GOOD: Quantum shows reasonable agreement with classical.")
        print("  Suitable for PRA/PRL after minor improvements.")
    elif ssim_norm > 0.50:
        print("⚠ MODERATE: Some agreement but significant differences remain.")
        print("  Need debugging before publication.")
    else:
        print("✗ POOR: Quantum and classical differ significantly.")
        print("  Major issues need resolution.")

    print("\nNext steps:")
    if ssim_norm < 0.90:
        print("  1. Investigate remaining scale mismatch")
        print("  2. Check if WPOA validity (phase > π/2) causes issues")
        print("  3. Consider multi-slice implementation")
    else:
        print("  1. Test on multiple materials (graphene, hBN, WS₂)")
        print("  2. Test at multiple voltages (80, 120, 300 kV)")
        print("  3. Begin Phase 2: True quantum encoding")

    print("=" * 70)


if __name__ == "__main__":
    main()
