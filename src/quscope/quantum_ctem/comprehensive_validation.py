#!/usr/bin/env python3
"""
Comprehensive Validation Suite for Quantum TEM
Tests multiple materials and voltages to demonstrate generality
"""

import os
import sys
from typing import Dict, List, Tuple

import abtem
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from ase import Atoms
from ase.build import mx2
from matplotlib.gridspec import GridSpec

sys.path.insert(0, os.path.dirname(__file__))
from classical_validation import (
    ClassicalTEMSimulator,
    ValidationMetrics,
    ValidationParameters,
)
from quantum_simulation import QuantumSimulationParameters, QuantumTEMSimulator


def create_test_structures() -> Dict[str, Atoms]:
    """Create multiple test structures for validation."""
    structures = {}

    # 1. MoS₂ monolayer (our main test case)
    mos2 = mx2(formula="MoS2", kind="2H", a=3.18, thickness=3.19, vacuum=2.0)
    structures["MoS2"] = abtem.orthogonalize_cell(mos2) * (3, 2, 1)

    # 2. WS₂ monolayer (similar but heavier W)
    ws2 = mx2(formula="WS2", kind="2H", a=3.15, thickness=3.18, vacuum=2.0)
    structures["WS2"] = abtem.orthogonalize_cell(ws2) * (3, 2, 1)

    # 3. Graphene removed from the canonical test set. If needed, build
    # graphene ad-hoc in a notebook or script using ASE directly.

    # 4. hBN (insulator, similar mass to graphene)
    # Create hBN manually
    a = 2.504  # Angstrom
    c = 6.661
    cell = [[a, 0, 0], [-a / 2, a * np.sqrt(3) / 2, 0], [0, 0, c]]
    positions = [[0, 0, 0], [2 / 3, 1 / 3, 0]]  # B  # N
    hbn = Atoms("BN", positions=positions, cell=cell, pbc=True)
    structures["hBN"] = abtem.orthogonalize_cell(hbn) * (4, 4, 1)

    return structures


def test_voltage_dependence(
    atoms: Atoms,
    voltages: List[float],
    material_name: str,
    grid_size: int = 256,
    pixel_size: float = 0.1,
) -> pd.DataFrame:
    """Test quantum vs classical at multiple voltages."""

    results = []

    for voltage in voltages:
        print(f"\n  Testing {material_name} at {voltage/1e3:.0f} kV...")

        # Calculate Scherzer defocus for this voltage
        wavelength = 12.398 / np.sqrt(voltage * (1 + voltage / 1.022e6))  # Angstrom
        # Scherzer defocus: Δf = -1.2 * sqrt(Cs * λ)
        Cs = 1.0e7  # 1 mm in Angstrom
        defocus_scherzer = -1.2 * np.sqrt(Cs * wavelength)

        # Use fixed defocus for consistency
        defocus = 200.0  # Angstrom

        # Classical simulation
        params_classical = ValidationParameters(
            acceleration_voltage=voltage,
            sample_type=material_name.lower(),
            thickness=atoms.cell[2, 2],
            defocus=defocus,
            cs=1.0,
            grid_size=grid_size,
            pixel_size=pixel_size,
        )
        classical_sim = ClassicalTEMSimulator(params_classical)
        I_classical = classical_sim.simulate(atoms)

        # Quantum simulation
        params_quantum = QuantumSimulationParameters(
            acceleration_voltage=voltage,
            grid_size=grid_size,
            pixel_size=pixel_size,
            defocus=defocus,
            cs=1.0,
        )

        # Get potential
        V_pot = abtem.Potential(
            atoms,
            sampling=pixel_size,
            gpts=(grid_size, grid_size),
            projection="infinite",
        )
        V = np.array(V_pot.project().array)

        quantum_sim = QuantumTEMSimulator(params_quantum)
        I_quantum = quantum_sim.simulate_with_potential(V, verbose=False)

        # Calculate metrics
        metrics = ValidationMetrics()

        # Normalize for fair comparison
        I_q_norm = (I_quantum - I_quantum.min()) / (
            I_quantum.max() - I_quantum.min() + 1e-10
        )
        I_c_norm = (I_classical - I_classical.min()) / (
            I_classical.max() - I_classical.min() + 1e-10
        )

        fidelity = metrics.calculate_fidelity(I_q_norm, I_c_norm)
        rmse = metrics.calculate_rmse(I_q_norm, I_c_norm)
        ssim = metrics.calculate_ssim(I_q_norm, I_c_norm)
        pearson = metrics.calculate_pearson_correlation(I_q_norm, I_c_norm)

        # Contrast
        contrast_q = (I_quantum.max() - I_quantum.min()) / (
            I_quantum.max() + I_quantum.min()
        )
        contrast_c = (I_classical.max() - I_classical.min()) / (
            I_classical.max() + I_classical.min()
        )

        # Interaction constant at this voltage
        h = 6.626e-34
        m_e = 9.109e-31
        e = 1.602e-19
        c = 3.0e8
        wavelength_m = h / np.sqrt(
            2 * m_e * e * voltage * (1 + e * voltage / (2 * m_e * c**2))
        )
        hbar = h / (2 * np.pi)
        sigma = (m_e * e * wavelength_m) / (2 * np.pi * hbar**2) * 1e-10

        # WPOA validity
        phase_max = sigma * V.max()
        wpoa_valid = phase_max < np.pi / 2

        results.append(
            {
                "Material": material_name,
                "Voltage_kV": voltage / 1e3,
                "Wavelength_A": wavelength,
                "Defocus_A": defocus,
                "Sigma": sigma,
                "Phase_max_rad": phase_max,
                "WPOA_valid": wpoa_valid,
                "Contrast_Quantum": contrast_q,
                "Contrast_Classical": contrast_c,
                "Fidelity": fidelity,
                "RMSE": rmse,
                "SSIM": ssim,
                "Pearson": pearson,
                "Intensity_Q_min": I_quantum.min(),
                "Intensity_Q_max": I_quantum.max(),
                "Intensity_C_min": I_classical.min(),
                "Intensity_C_max": I_classical.max(),
            }
        )

        print(f"    σ = {sigma:.3e} rad/(V·Å), Phase_max = {phase_max:.3f} rad")
        print(f"    Pearson = {pearson:.4f}, SSIM = {ssim:.4f}")

    return pd.DataFrame(results)


def create_summary_figure(
    df: pd.DataFrame, output_file: str = "validation_summary.png"
):
    """Create comprehensive summary figure."""

    fig = plt.figure(figsize=(20, 12))
    gs = GridSpec(3, 3, figure=fig, hspace=0.35, wspace=0.3)

    materials = df["Material"].unique()
    colors = plt.cm.Set2(np.linspace(0, 1, len(materials)))

    # 1. Wavelength vs Voltage
    ax1 = fig.add_subplot(gs[0, 0])
    for mat, color in zip(materials, colors):
        df_mat = df[df["Material"] == mat]
        ax1.plot(
            df_mat["Voltage_kV"],
            df_mat["Wavelength_A"],
            "o-",
            label=mat,
            color=color,
            linewidth=2,
            markersize=8,
        )
    ax1.set_xlabel("Voltage (kV)", fontsize=11)
    ax1.set_ylabel("Wavelength (Å)", fontsize=11)
    ax1.set_title("Electron Wavelength vs Voltage", fontweight="bold")
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # 2. Interaction constant vs Voltage
    ax2 = fig.add_subplot(gs[0, 1])
    for mat, color in zip(materials, colors):
        df_mat = df[df["Material"] == mat]
        ax2.plot(
            df_mat["Voltage_kV"],
            df_mat["Sigma"],
            "o-",
            label=mat,
            color=color,
            linewidth=2,
            markersize=8,
        )
    ax2.set_xlabel("Voltage (kV)", fontsize=11)
    ax2.set_ylabel("σ [rad/(V·Å)]", fontsize=11)
    ax2.set_title("Interaction Constant vs Voltage", fontweight="bold")
    ax2.grid(True, alpha=0.3)
    ax2.set_yscale("log")
    ax2.legend()

    # 3. WPOA Validity (Phase shift)
    ax3 = fig.add_subplot(gs[0, 2])
    for mat, color in zip(materials, colors):
        df_mat = df[df["Material"] == mat]
        ax3.plot(
            df_mat["Voltage_kV"],
            df_mat["Phase_max_rad"],
            "o-",
            label=mat,
            color=color,
            linewidth=2,
            markersize=8,
        )
    ax3.axhline(
        np.pi / 2, color="red", linestyle="--", linewidth=2, label="WPOA limit (π/2)"
    )
    ax3.set_xlabel("Voltage (kV)", fontsize=11)
    ax3.set_ylabel("Max Phase Shift (rad)", fontsize=11)
    ax3.set_title("WPOA Validity Check", fontweight="bold")
    ax3.grid(True, alpha=0.3)
    ax3.legend()

    # 4. Contrast comparison
    ax4 = fig.add_subplot(gs[1, 0])
    x = np.arange(len(df))
    width = 0.35
    ax4.bar(x - width / 2, df["Contrast_Quantum"], width, label="Quantum", alpha=0.8)
    ax4.bar(
        x + width / 2, df["Contrast_Classical"], width, label="Classical", alpha=0.8
    )
    ax4.set_xlabel("Test Case", fontsize=11)
    ax4.set_ylabel("Contrast", fontsize=11)
    ax4.set_title("Quantum vs Classical Contrast", fontweight="bold")
    ax4.set_xticks(x)
    ax4.set_xticklabels(
        [f"{row['Material']}\n{row['Voltage_kV']:.0f}kV" for _, row in df.iterrows()],
        rotation=45,
        ha="right",
        fontsize=8,
    )
    ax4.legend()
    ax4.grid(True, alpha=0.3, axis="y")

    # 5. Fidelity across tests
    ax5 = fig.add_subplot(gs[1, 1])
    for mat, color in zip(materials, colors):
        df_mat = df[df["Material"] == mat]
        ax5.plot(
            df_mat["Voltage_kV"],
            df_mat["Fidelity"],
            "o-",
            label=mat,
            color=color,
            linewidth=2,
            markersize=8,
        )
    ax5.axhline(
        0.99,
        color="green",
        linestyle="--",
        linewidth=1,
        alpha=0.5,
        label="Target (0.99)",
    )
    ax5.set_xlabel("Voltage (kV)", fontsize=11)
    ax5.set_ylabel("Fidelity", fontsize=11)
    ax5.set_title("Quantum-Classical Fidelity", fontweight="bold")
    ax5.grid(True, alpha=0.3)
    ax5.legend()

    # 6. SSIM across tests
    ax6 = fig.add_subplot(gs[1, 2])
    for mat, color in zip(materials, colors):
        df_mat = df[df["Material"] == mat]
        ax6.plot(
            df_mat["Voltage_kV"],
            df_mat["SSIM"],
            "o-",
            label=mat,
            color=color,
            linewidth=2,
            markersize=8,
        )
    ax6.axhline(
        0.95,
        color="green",
        linestyle="--",
        linewidth=1,
        alpha=0.5,
        label="Target (0.95)",
    )
    ax6.set_xlabel("Voltage (kV)", fontsize=11)
    ax6.set_ylabel("SSIM", fontsize=11)
    ax6.set_title("Structural Similarity Index", fontweight="bold")
    ax6.grid(True, alpha=0.3)
    ax6.legend()

    # 7. Pearson correlation
    ax7 = fig.add_subplot(gs[2, 0])
    for mat, color in zip(materials, colors):
        df_mat = df[df["Material"] == mat]
        ax7.plot(
            df_mat["Voltage_kV"],
            df_mat["Pearson"],
            "o-",
            label=mat,
            color=color,
            linewidth=2,
            markersize=8,
        )
    ax7.axhline(
        0.99,
        color="green",
        linestyle="--",
        linewidth=1,
        alpha=0.5,
        label="Target (0.99)",
    )
    ax7.axhline(0.0, color="red", linestyle="-", linewidth=1, alpha=0.3)
    ax7.set_xlabel("Voltage (kV)", fontsize=11)
    ax7.set_ylabel("Pearson Correlation", fontsize=11)
    ax7.set_title("Pixel Correlation", fontweight="bold")
    ax7.grid(True, alpha=0.3)
    ax7.legend()

    # 8. RMSE across tests
    ax8 = fig.add_subplot(gs[2, 1])
    for mat, color in zip(materials, colors):
        df_mat = df[df["Material"] == mat]
        ax8.plot(
            df_mat["Voltage_kV"],
            df_mat["RMSE"],
            "o-",
            label=mat,
            color=color,
            linewidth=2,
            markersize=8,
        )
    ax8.axhline(
        0.01,
        color="green",
        linestyle="--",
        linewidth=1,
        alpha=0.5,
        label="Target (0.01)",
    )
    ax8.set_xlabel("Voltage (kV)", fontsize=11)
    ax8.set_ylabel("RMSE (normalized)", fontsize=11)
    ax8.set_title("Root Mean Square Error", fontweight="bold")
    ax8.grid(True, alpha=0.3)
    ax8.set_yscale("log")
    ax8.legend()

    # 9. Summary table
    ax9 = fig.add_subplot(gs[2, 2])
    ax9.axis("off")

    # Calculate summary statistics
    summary_text = "VALIDATION SUMMARY\n" + "=" * 40 + "\n\n"
    summary_text += f"Materials tested: {len(materials)}\n"
    summary_text += f"Total test cases: {len(df)}\n\n"

    summary_text += "Average Metrics:\n"
    summary_text += (
        f"  Fidelity:  {df['Fidelity'].mean():.4f} ± {df['Fidelity'].std():.4f}\n"
    )
    summary_text += f"  SSIM:      {df['SSIM'].mean():.4f} ± {df['SSIM'].std():.4f}\n"
    summary_text += (
        f"  Pearson:   {df['Pearson'].mean():.4f} ± {df['Pearson'].std():.4f}\n"
    )
    summary_text += f"  RMSE:      {df['RMSE'].mean():.4f} ± {df['RMSE'].std():.4f}\n\n"

    summary_text += "WPOA Validity:\n"
    valid_count = df["WPOA_valid"].sum()
    summary_text += f"  Valid cases: {valid_count}/{len(df)}\n"
    summary_text += f"  Percentage:  {100*valid_count/len(df):.1f}%\n\n"

    if df["Pearson"].mean() < -0.2:
        summary_text += "⚠ WARNING: Negative correlation!\n"
        summary_text += "  Sign inversion in quantum output.\n"
        summary_text += "  Needs debugging before publication.\n"
    elif df["SSIM"].mean() > 0.90:
        summary_text += "✓ EXCELLENT: Ready for publication!\n"
        summary_text += "  High structural similarity achieved.\n"
    elif df["SSIM"].mean() > 0.70:
        summary_text += "✓ GOOD: Suitable for PRA/PRQ.\n"
        summary_text += "  Minor improvements recommended.\n"
    else:
        summary_text += "⚠ MODERATE: More work needed.\n"
        summary_text += "  Check normalization and scaling.\n"

    ax9.text(
        0.1,
        0.95,
        summary_text,
        transform=ax9.transAxes,
        fontsize=10,
        verticalalignment="top",
        fontfamily="monospace",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.3),
    )

    fig.suptitle(
        "Comprehensive Quantum TEM Validation Suite",
        fontsize=16,
        fontweight="bold",
        y=0.995,
    )

    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"\n✓ Saved: {output_file}")


def main():
    """Run comprehensive validation suite."""

    print("=" * 70)
    print("COMPREHENSIVE QUANTUM TEM VALIDATION")
    print("=" * 70)

    # Test parameters
    voltages = [80e3, 120e3, 200e3, 300e3]  # 80, 120, 200, 300 kV
    grid_size = 256
    pixel_size = 0.1

    # Create structures
    print("\n[1/3] Creating test structures...")
    structures = create_test_structures()
    print(f"  ✓ Created {len(structures)} structures: {', '.join(structures.keys())}")

    # Run tests
    print("\n[2/3] Running validation tests...")
    all_results = []

    for material_name, atoms in structures.items():
        print(f"\nTesting {material_name}:")
        print(f"  Atoms: {len(atoms)}, Cell: {atoms.cell.lengths()}")

        df_material = test_voltage_dependence(
            atoms, voltages, material_name, grid_size, pixel_size
        )
        all_results.append(df_material)

    # Combine results
    df_all = pd.concat(all_results, ignore_index=True)

    # Save to CSV
    csv_file = "validation_results.csv"
    df_all.to_csv(csv_file, index=False)
    print(f"\n✓ Saved results to: {csv_file}")

    # Create summary figure
    print("\n[3/3] Generating summary figure...")
    create_summary_figure(df_all)

    # Print detailed results
    print("\n" + "=" * 70)
    print("DETAILED RESULTS")
    print("=" * 70)
    print(df_all.to_string(index=False))

    print("\n" + "=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)

    # Publication readiness assessment
    print("\nPUBLICATION READINESS:")
    avg_ssim = df_all["SSIM"].mean()
    avg_pearson = df_all["Pearson"].mean()

    if avg_pearson < -0.2:
        print("  Status: ⚠ BLOCKED")
        print("  Issue: Negative correlation (sign inversion)")
        print("  Action: Fix sign error before proceeding")
        print("\n  Next step: Debug phase grating or CTF sign convention")
    elif avg_ssim > 0.90 and avg_pearson > 0.90:
        print("  Status: ✓ READY for high-impact venue (Nature/PRL)")
        print("  Quality: Excellent agreement across all tests")
        print("\n  Next steps:")
        print("    1. Write manuscript")
        print("    2. Generate publication figures")
        print("    3. Add error analysis")
    elif avg_ssim > 0.70:
        print("  Status: ✓ READY for PRA/Quantum")
        print("  Quality: Good agreement with room for improvement")
        print("\n  Next steps:")
        print("    1. Optional: Improve normalization")
        print("    2. Write manuscript")
        print("    3. Add convergence tests")
    else:
        print("  Status: ⚠ NOT READY")
        print("  Quality: Moderate agreement, needs work")
        print("\n  Next steps:")
        print("    1. Debug systematic differences")
        print("    2. Check potential calculation")
        print("    3. Verify propagation method")


if __name__ == "__main__":
    main()
