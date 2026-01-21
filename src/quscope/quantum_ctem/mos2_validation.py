"""
MoS₂ Validation Example for Quantum CTEM

Following the abTEM tutorial structure for partial coherence:
https://abtem.readthedocs.io/en/latest/user_guide/tutorials/partial_coherence.html

This demonstrates quantum-classical validation using MoS₂ (molybdenum disulfide),
a 2D transition metal dichalcogenide with strong atomic contrast.

Author: QuScope Team
Date: October 2025
"""

from typing import Dict, Tuple

import matplotlib.pyplot as plt
import numpy as np

try:
    from ase import Atoms
    from ase.build import mx2
except ImportError:
    raise ImportError("ASE is required. Install with: conda install -c conda-forge ase")

try:
    import abtem
except ImportError:
    raise ImportError(
        "abTEM is required. Install with: conda install -c conda-forge abtem"
    )

# Import our modules
try:
    from classical_validation import (
        ClassicalTEMSimulator,
        ValidationMetrics,
        ValidationParameters,
        ValidationVisualizer,
    )
    from quantum_simulation import run_quantum_tem_simulation
    from sample_potential_converter import SamplePotentialConverter
except ImportError:
    from .classical_validation import (
        ClassicalTEMSimulator,
        ValidationMetrics,
        ValidationParameters,
        ValidationVisualizer,
    )
    from .quantum_simulation import run_quantum_tem_simulation
    from .sample_potential_converter import SamplePotentialConverter


def create_mos2_sample(
    size: Tuple[int, int] = (3, 2), vacuum: float = 2.0, orthogonalize: bool = True
) -> Atoms:
    """Create MoS₂ sample structure with orthogonal cell.

    Following abTEM tutorial: the structure must have an orthogonal (square/rectangular)
    cell to match the rectangular simulation grid.

    Args:
        size: (nx, ny) supercell size for orthogonalization
        vacuum: Vacuum spacing in Angstroms
        orthogonalize: Whether to create orthogonal cell (required for simulation)

    Returns:
        ASE Atoms object for MoS₂ with orthogonal cell
    """
    # Create primitive MoS₂ structure
    # Note: mx2 function creates a monolayer of transition metal dichalcogenide
    atoms = mx2(
        formula="MoS2",
        kind="2H",  # 2H polytype (most common)
        a=3.18,  # Lattice constant in Angstroms
        thickness=3.19,  # Thickness of the layer
        vacuum=vacuum,
    )

    if orthogonalize:
        # Create orthogonal supercell (critical for rectangular simulation grid)
        # This follows the abTEM tutorial approach
        atoms = abtem.orthogonalize_cell(atoms) * (size[0], size[1], 1)

    return atoms


def visualize_mos2_structure(atoms: Atoms, save_path: str = None):
    """Visualize the MoS₂ atomic structure.

    Args:
        atoms: ASE Atoms object
        save_path: Optional path to save figure
    """
    fig = plt.figure(figsize=(12, 4))

    # 3D view
    ax1 = fig.add_subplot(131, projection="3d")

    # Separate Mo and S atoms
    mo_positions = [atom.position for atom in atoms if atom.symbol == "Mo"]
    s_positions = [atom.position for atom in atoms if atom.symbol == "S"]

    if mo_positions:
        mo_pos = np.array(mo_positions)
        ax1.scatter(
            mo_pos[:, 0],
            mo_pos[:, 1],
            mo_pos[:, 2],
            c="purple",
            s=200,
            label="Mo",
            alpha=0.8,
        )

    if s_positions:
        s_pos = np.array(s_positions)
        ax1.scatter(
            s_pos[:, 0],
            s_pos[:, 1],
            s_pos[:, 2],
            c="yellow",
            s=100,
            label="S",
            alpha=0.8,
        )

    ax1.set_xlabel("x (Å)")
    ax1.set_ylabel("y (Å)")
    ax1.set_zlabel("z (Å)")
    ax1.set_title("MoS₂ Structure (3D)", fontweight="bold")
    ax1.legend()

    # Top view (xy projection)
    ax2 = fig.add_subplot(132)
    if mo_positions:
        ax2.scatter(
            mo_pos[:, 0],
            mo_pos[:, 1],
            c="purple",
            s=200,
            label="Mo",
            alpha=0.8,
            edgecolors="black",
            linewidths=1,
        )
    if s_positions:
        ax2.scatter(
            s_pos[:, 0],
            s_pos[:, 1],
            c="yellow",
            s=100,
            label="S",
            alpha=0.8,
            edgecolors="black",
            linewidths=1,
        )
    ax2.set_xlabel("x (Å)")
    ax2.set_ylabel("y (Å)")
    ax2.set_title("Top View (xy)", fontweight="bold")
    ax2.set_aspect("equal")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Side view (xz projection)
    ax3 = fig.add_subplot(133)
    if mo_positions:
        ax3.scatter(
            mo_pos[:, 0],
            mo_pos[:, 2],
            c="purple",
            s=200,
            label="Mo",
            alpha=0.8,
            edgecolors="black",
            linewidths=1,
        )
    if s_positions:
        ax3.scatter(
            s_pos[:, 0],
            s_pos[:, 2],
            c="yellow",
            s=100,
            label="S",
            alpha=0.8,
            edgecolors="black",
            linewidths=1,
        )
    ax3.set_xlabel("x (Å)")
    ax3.set_ylabel("z (Å)")
    ax3.set_title("Side View (xz)", fontweight="bold")
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    plt.suptitle(
        f"MoS₂ Atomic Structure ({len(atoms)} atoms)", fontsize=14, fontweight="bold"
    )
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"✓ Saved structure visualization: {save_path}")

    plt.show()


def compare_potentials_mos2(
    atoms: Atoms, grid_size: int = 256, pixel_size: float = 0.1, voltage: float = 200e3
) -> Tuple[np.ndarray, np.ndarray]:
    """Compare quantum and classical projected potentials for MoS₂.

    Args:
        atoms: ASE Atoms object
        grid_size: Grid size
        pixel_size: Pixel size in Angstroms
        voltage: Acceleration voltage in Volts

    Returns:
        Tuple of (quantum_potential, classical_potential)
    """
    # Quantum potential (our implementation)
    print("Calculating quantum potential...")
    converter = SamplePotentialConverter(voltage)
    V_quantum = converter.atoms_to_potential(atoms, grid_size, pixel_size)

    # Classical potential (abTEM)
    print("Calculating classical potential (abTEM)...")
    potential_abtem = abtem.Potential(
        atoms, sampling=pixel_size, gpts=(grid_size, grid_size), projection="infinite"
    )
    V_classical = np.array(potential_abtem.project().array)

    # Visualize comparison
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))

    # Quantum potential
    im1 = axes[0, 0].imshow(V_quantum, cmap="viridis")
    axes[0, 0].set_title("Quantum Potential", fontweight="bold")
    axes[0, 0].axis("off")
    plt.colorbar(im1, ax=axes[0, 0], label="V (V·Å)")

    # Classical potential
    im2 = axes[0, 1].imshow(V_classical, cmap="viridis")
    axes[0, 1].set_title("Classical Potential (abTEM)", fontweight="bold")
    axes[0, 1].axis("off")
    plt.colorbar(im2, ax=axes[0, 1], label="V (V·Å)")

    # Difference
    diff = V_quantum - V_classical
    im3 = axes[0, 2].imshow(diff, cmap="RdBu_r")
    axes[0, 2].set_title("Difference (Quantum - Classical)", fontweight="bold")
    axes[0, 2].axis("off")
    plt.colorbar(im3, ax=axes[0, 2], label="ΔV (V·Å)")

    # Line profiles
    center = grid_size // 2
    profile_q = V_quantum[center, :]
    profile_c = V_classical[center, :]

    axes[1, 0].plot(profile_q, "b-", label="Quantum", linewidth=2)
    axes[1, 0].plot(profile_c, "r--", label="Classical", linewidth=2)
    axes[1, 0].set_xlabel("x (pixels)")
    axes[1, 0].set_ylabel("Potential (V·Å)")
    axes[1, 0].set_title("Central Line Profile", fontweight="bold")
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

    # Correlation plot
    axes[1, 1].hexbin(
        V_quantum.flatten(),
        V_classical.flatten(),
        gridsize=50,
        cmap="viridis",
        mincnt=1,
    )
    axes[1, 1].plot(
        [V_quantum.min(), V_quantum.max()],
        [V_quantum.min(), V_quantum.max()],
        "r--",
        linewidth=2,
        label="Ideal",
    )
    axes[1, 1].set_xlabel("Quantum (V·Å)")
    axes[1, 1].set_ylabel("Classical (V·Å)")
    axes[1, 1].set_title("Potential Correlation", fontweight="bold")
    axes[1, 1].legend()

    # Statistics
    stats_text = (
        f"Statistics\n"
        f"{'='*30}\n\n"
        f"Quantum:\n"
        f"  Min: {V_quantum.min():.2f} V·Å\n"
        f"  Max: {V_quantum.max():.2f} V·Å\n"
        f"  Mean: {V_quantum.mean():.2f} V·Å\n\n"
        f"Classical:\n"
        f"  Min: {V_classical.min():.2f} V·Å\n"
        f"  Max: {V_classical.max():.2f} V·Å\n"
        f"  Mean: {V_classical.mean():.2f} V·Å\n\n"
        f"Difference:\n"
        f"  Max: {np.abs(diff).max():.2f} V·Å\n"
        f"  RMS: {np.sqrt(np.mean(diff**2)):.2f} V·Å\n"
        f"  Correlation: {np.corrcoef(V_quantum.flatten(), V_classical.flatten())[0,1]:.4f}"
    )

    axes[1, 2].axis("off")
    axes[1, 2].text(
        0.1,
        0.5,
        stats_text,
        fontsize=10,
        family="monospace",
        verticalalignment="center",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.3),
    )

    plt.suptitle("MoS₂ Projected Potential Comparison", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig("mos2_potential_comparison.png", dpi=300, bbox_inches="tight")
    print("✓ Saved: mos2_potential_comparison.png")
    plt.show()

    return V_quantum, V_classical


def run_mos2_validation(
    voltage: float = 200e3,
    defocus: float = -659.7,
    cs: float = 1.3,
    grid_size: int = 256,
    size: Tuple[int, int] = (4, 4),
    verbose: bool = True,
) -> Dict:
    """Run complete MoS₂ validation workflow.

    Args:
        voltage: Acceleration voltage in Volts
        defocus: Defocus in Angstroms
        cs: Spherical aberration in mm
        grid_size: Grid size
        size: (nx, ny) supercell size
        verbose: Print progress

    Returns:
        Dictionary with validation results
    """
    print("=" * 70)
    print(f"QUANTUM-CLASSICAL VALIDATION: MoS₂ @ {voltage/1e3:.0f} kV")
    print("=" * 70)

    # Create MoS₂ sample
    if verbose:
        print(f"\n[1/5] Creating MoS₂ structure ({size[0]}×{size[1]} supercell)...")

    atoms = create_mos2_sample(size=size, vacuum=5.0)

    if verbose:
        print(f"  ✓ Created MoS₂ with {len(atoms)} atoms")
        print(f"    Mo atoms: {sum(1 for a in atoms if a.symbol == 'Mo')}")
        print(f"    S atoms: {sum(1 for a in atoms if a.symbol == 'S')}")
        print(f"    Cell: {atoms.cell.lengths()}")

    # Visualize structure
    if verbose:
        print("\n[2/5] Visualizing atomic structure...")
        visualize_mos2_structure(atoms, "mos2_structure.png")

    # Compare potentials
    if verbose:
        print("\n[3/5] Comparing projected potentials...")

    V_quantum, V_classical = compare_potentials_mos2(
        atoms, grid_size, pixel_size=0.1, voltage=voltage
    )

    # Setup parameters
    params = ValidationParameters(
        acceleration_voltage=voltage,
        sample_type="MoS2",
        thickness=3.19,  # Monolayer thickness
        defocus=defocus,
        cs=cs,
        grid_size=grid_size,
        pixel_size=0.1,
    )

    # Classical simulation
    if verbose:
        print("\n[4/5] Running simulations...")
        print("  Classical (abTEM)...")

    classical_sim = ClassicalTEMSimulator(params)
    classical_image = classical_sim.simulate(atoms)

    if verbose:
        print(
            f"    ✓ Classical intensity: [{float(classical_image.min()):.6f}, {float(classical_image.max()):.6f}]"
        )
        print("  Quantum (TEMHamiltonian)...")

    # Quantum simulation
    quantum_image = run_quantum_tem_simulation(
        atoms,
        voltage=voltage,
        grid_size=grid_size,
        pixel_size=0.1,
        defocus=defocus,
        cs=cs,
        verbose=False,
    )

    if verbose:
        print(
            f"    ✓ Quantum intensity: [{float(quantum_image.min()):.6f}, {float(quantum_image.max()):.6f}]"
        )

    # Calculate metrics
    if verbose:
        print("\n[5/5] Calculating validation metrics...")

    metrics = ValidationMetrics.calculate_all_metrics(quantum_image, classical_image)

    # Print results
    print("\n" + "=" * 70)
    print("VALIDATION METRICS")
    print("=" * 70)

    targets = {"fidelity": 0.999, "rmse": 0.01, "ssim": 0.95, "pearson": 0.99}

    for key, value in metrics.items():
        target = targets[key]
        if key == "rmse":
            status = "✓" if value < target else "⚠"
        else:
            status = "✓" if value > target else "⚠"

        print(f"  {status} {key.upper():10s}: {value:.6f}  (target: {target:.3f})")

    print("=" * 70)

    # Generate comparison figure
    if verbose:
        print("\nGenerating validation figure...")

    ValidationVisualizer.plot_comparison(
        quantum_image,
        classical_image,
        metrics,
        params,
        save_path="validation_mos2_200kv.png",
    )

    if verbose:
        print("✓ Saved: validation_mos2_200kv.png")
        print("\n🎉 VALIDATION COMPLETE!")

    return {
        "atoms": atoms,
        "quantum_potential": V_quantum,
        "classical_potential": V_classical,
        "quantum_image": quantum_image,
        "classical_image": classical_image,
        "metrics": metrics,
        "params": params,
    }


def run_multi_voltage_mos2_validation(
    voltages: list = [80e3, 120e3, 200e3, 300e3], grid_size: int = 256
) -> Dict[float, Dict]:
    """Run MoS₂ validation across multiple voltages.

    Args:
        voltages: List of voltages in Volts
        grid_size: Grid size

    Returns:
        Dictionary mapping voltage to results
    """
    print("=" * 70)
    print("MULTI-VOLTAGE VALIDATION: MoS₂")
    print("=" * 70)

    results = {}

    # Create sample once
    atoms = create_mos2_sample(size=(4, 4), vacuum=5.0)

    for voltage in voltages:
        print(f"\n{'='*70}")
        print(f"Testing {voltage/1e3:.0f} kV")
        print(f"{'='*70}")

        # Calculate Scherzer defocus for this voltage
        from scipy.constants import c, e, h, m_e

        wavelength = h / np.sqrt(
            2 * m_e * e * voltage * (1 + e * voltage / (2 * m_e * c**2))
        )
        wavelength *= 1e10  # to Angstroms
        cs_angstrom = 1.3e7  # 1.3 mm to Angstroms
        defocus_scherzer = -1.2 * np.sqrt(cs_angstrom * wavelength)

        result = run_mos2_validation(
            voltage=voltage,
            defocus=defocus_scherzer,
            cs=1.3,
            grid_size=grid_size,
            size=(4, 4),
            verbose=False,
        )

        results[voltage] = result

        metrics = result["metrics"]
        print(f"\nMetrics @ {voltage/1e3:.0f} kV:")
        print(f"  Fidelity: {metrics['fidelity']:.6f}")
        print(f"  RMSE: {metrics['rmse']:.6f}")
        print(f"  SSIM: {metrics['ssim']:.6f}")
        print(f"  Pearson: {metrics['pearson']:.6f}")

    # Generate multi-voltage comparison
    print(f"\n{'='*70}")
    print("Generating multi-voltage comparison figure...")
    ValidationVisualizer.plot_multi_voltage_validation(
        results, save_path="validation_mos2_multi_voltage.png"
    )
    print("✓ Saved: validation_mos2_multi_voltage.png")

    print("\n🎉 MULTI-VOLTAGE VALIDATION COMPLETE!")

    return results


if __name__ == "__main__":
    """Run MoS₂ validation examples."""

    print("MoS₂ Validation for Quantum CTEM")
    print("=" * 70)
    print()

    # Single voltage validation
    print("Running single voltage validation (200 kV)...\n")
    result = run_mos2_validation(
        voltage=200e3, defocus=-659.7, cs=1.3, grid_size=256, size=(4, 4), verbose=True
    )

    # Multi-voltage validation
    print("\n\n")
    input("Press Enter to run multi-voltage validation (80, 120, 200, 300 kV)...")

    results_multi = run_multi_voltage_mos2_validation(
        voltages=[80e3, 120e3, 200e3, 300e3], grid_size=256
    )

    print("\n" + "=" * 70)
    print("ALL VALIDATIONS COMPLETE")
    print("=" * 70)
    print("\nGenerated files:")
    print("  ✓ mos2_structure.png")
    print("  ✓ mos2_potential_comparison.png")
    print("  ✓ validation_mos2_200kv.png")
    print("  ✓ validation_mos2_multi_voltage.png")
