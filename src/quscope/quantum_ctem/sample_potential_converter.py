"""
Sample Potential Converter: ASE Atoms to Quantum TEM Potential

Converts atomic structures (ASE Atoms) to 2D projected potentials V(x,y)
for quantum TEM simulation using the Weak Phase Object Approximation.

References:
- Kirkland, E. J. (2010). Advanced Computing in Electron Microscopy. Springer.
- Lobato, I., & Van Dyck, D. (2014). Acta Cryst. A70, 636.
The atomic potentials come from abTEM's Kirkland or Lobato parametrization
(quscope.ctem.AtomicPotential); QuScope carries no scattering-factor tables.

Author: QuScope Team
Date: October 2025
"""

from typing import Dict, Optional, Tuple

import numpy as np

from ..ctem.atomic_potential import AtomicPotential
from ..utils.constants import PhysicalConstants

try:
    from ase import Atoms
except ImportError:
    raise ImportError("ASE is required. Install with: conda install -c conda-forge ase")


class SamplePotentialConverter:
    """Convert ASE Atoms to 2D projected potential for quantum TEM."""

    def __init__(self, acceleration_voltage: float = 80e3, parametrization: str = "kirkland"):
        """Initialize converter.

        Args:
            acceleration_voltage: Acceleration voltage in Volts
            parametrization: abTEM atomic potential parametrization, "kirkland" or "lobato"
        """
        self.voltage = acceleration_voltage
        self.atomic_potential = AtomicPotential(parametrization)
        self.wavelength = self._calculate_wavelength()

    def _calculate_wavelength(self) -> float:
        """Calculate relativistic electron wavelength.

        Returns:
            Wavelength in Angstroms
        """
        from scipy.constants import c, e, h, m_e

        V = self.voltage
        # Relativistic correction
        wavelength = h / np.sqrt(2 * m_e * e * V * (1 + e * V / (2 * m_e * c**2)))

        return wavelength * 1e10  # Convert m to Angstroms

    def get_interaction_constant(self) -> float:
        """Return the interaction constant sigma in rad / (V*Angstrom).

        Relativistic, sigma = 2 pi gamma m0 e lambda / h^2 (7.29e-4 at 200 kV).
        """
        return PhysicalConstants.calculate_sigma(self.voltage)

    def atoms_to_potential(
        self,
        atoms: Atoms,
        grid_size: int,
        pixel_size: float,
        projection_method: str = "wpoa",
        tile_to_fill: bool = True,
    ) -> np.ndarray:
        """Convert ASE Atoms to 2D projected potential.

        Args:
            atoms: ASE Atoms object
            grid_size: Number of pixels (N for N×N grid)
            pixel_size: Pixel size in Angstroms
            projection_method: 'wpoa' (weak phase object) or 'full'
            tile_to_fill: If True, tile the structure to fill the grid (like abTEM)

        Returns:
            2D array of projected potential V(x,y) in V*Angstrom
        """
        # Create real-space grid
        extent = grid_size * pixel_size
        x = np.linspace(-extent / 2, extent / 2, grid_size)
        y = np.linspace(-extent / 2, extent / 2, grid_size)
        X, Y = np.meshgrid(x, y)

        # Tile atoms to fill grid if requested (matching abTEM behavior)
        if tile_to_fill:
            cell = atoms.get_cell()
            # Use the actual lattice vector lengths in the xy-plane. Some
            # builders (e.g. ase.build.mx2) produce non-axis-aligned cells
            # where the diagonal cell entries are not sufficient. Using the
            # vector norms projected into xy avoids under-estimating the
            # number of tiles and the resulting empty corner regions.
            a_vec = cell[0]
            b_vec = cell[1]
            cell_x = float(np.linalg.norm(a_vec[:2]))
            cell_y = float(np.linalg.norm(b_vec[:2]))

            # Calculate how many tiles needed (add a small safety margin)
            nx = int(np.ceil(extent / cell_x)) + 2
            ny = int(np.ceil(extent / cell_y)) + 2

            # Tile the structure
            atoms_tiled = atoms.copy()
            atoms_tiled = atoms_tiled.repeat((nx, ny, 1))

            # Center the tiled structure
            atoms_tiled.center()

            atoms_to_use = atoms_tiled
        else:
            atoms_to_use = atoms

        # Sum the projected potentials of all atoms [V*Angstrom]
        V = np.zeros((grid_size, grid_size))
        for atom in atoms_to_use:
            x0, y0, _ = atom.position
            V += self.atomic_potential.calculate_2d(X, Y, x0, y0, int(atom.number))
        return V

    def visualize_potential(
        self,
        atoms: Atoms,
        grid_size: int = 256,
        pixel_size: float = 0.1,
        save_path: Optional[str] = None,
    ) -> None:
        """Visualize the projected potential.

        Args:
            atoms: ASE Atoms object
            grid_size: Grid size
            pixel_size: Pixel size in Angstroms
            save_path: Optional path to save figure
        """
        import matplotlib.pyplot as plt

        # Calculate potential
        V = self.atoms_to_potential(atoms, grid_size, pixel_size)

        # Create figure
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        # Potential map
        extent = grid_size * pixel_size
        im1 = axes[0].imshow(
            V, extent=[-extent / 2, extent / 2, -extent / 2, extent / 2], cmap="viridis"
        )
        axes[0].set_title("Projected Potential V(x,y)", fontweight="bold")
        axes[0].set_xlabel("x (Å)")
        axes[0].set_ylabel("y (Å)")
        plt.colorbar(im1, ax=axes[0], label="Potential (V)")

        # Line profile
        center = grid_size // 2
        profile = V[center, :]
        x_profile = np.linspace(-extent / 2, extent / 2, grid_size)
        axes[1].plot(x_profile, profile, "b-", linewidth=2)
        axes[1].set_xlabel("x (Å)")
        axes[1].set_ylabel("Potential (V)")
        axes[1].set_title("Central Line Profile", fontweight="bold")
        axes[1].grid(True, alpha=0.3)

        # Phase shift (σV)
        # Use consistent interaction constant (rad / (V·Å))
        sigma = self.get_interaction_constant()
        phase = sigma * V

        im2 = axes[2].imshow(
            phase,
            extent=[-extent / 2, extent / 2, -extent / 2, extent / 2],
            cmap="twilight",
        )
        axes[2].set_title("Phase Shift σV (rad)", fontweight="bold")
        axes[2].set_xlabel("x (Å)")
        axes[2].set_ylabel("y (Å)")
        plt.colorbar(im2, ax=axes[2], label="Phase (rad)")

        plt.suptitle(
            f"Sample Potential: {len(atoms)} atoms at {self.voltage/1e3:.0f} kV",
            fontsize=14,
            fontweight="bold",
        )
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"✓ Saved potential visualization: {save_path}")

        plt.show()

    def calculate_sample_statistics(
        self, atoms: Atoms, grid_size: int = 256, pixel_size: float = 0.1
    ) -> Dict[str, float]:
        """Calculate statistics of the sample potential.

        Args:
            atoms: ASE Atoms object
            grid_size: Grid size
            pixel_size: Pixel size in Angstroms

        Returns:
            Dictionary with potential statistics
        """
        V = self.atoms_to_potential(atoms, grid_size, pixel_size)

        sigma = self.get_interaction_constant()
        phase = sigma * V

        stats = {
            "potential_min": float(V.min()),
            "potential_max": float(V.max()),
            "potential_mean": float(V.mean()),
            "potential_std": float(V.std()),
            "phase_shift_max": float(np.abs(phase).max()),
            "phase_shift_mean": float(np.abs(phase).mean()),
            "wpoa_valid": float(np.abs(phase).max()) < 0.5,  # WPOA valid if phase < π/2
        }

        return stats


def test_potential_converter():
    """Light smoke-test for the potential converter using a small MoS2 cell.

    This replaces the previous graphene-focused example to align with the
    repository's MoS2-centered workflow.
    """
    try:
        from quscope.quantum_ctem.mos2_workflow.viz import build_mos2
    except Exception:
        # Fallback: construct a minimal MoS2 cell manually using ASE
        from ase import Atoms

        # Minimal MoS2-like triatomic cell (not physically accurate; smoke-test only)
        atoms = Atoms(
            ["Mo", "S", "S"], positions=[(0, 0, 0), (1.6, 0, 0), (-1.6, 0, 0)]
        )
    else:
        atoms = build_mos2(nx=1, ny=1, vacuum=5.0)

    atoms.center()

    print("Testing Sample Potential Converter (MoS2 smoke-test)")
    print("=" * 60)

    print("\n[1/3] Initializing potential converter...")
    converter = SamplePotentialConverter(acceleration_voltage=200e3)
    print("✓ Converter initialized")

    print("\n[2/3] Converting atoms to potential...")
    V = converter.atoms_to_potential(atoms, grid_size=128, pixel_size=0.1)
    print(f"✓ Potential calculated — shape: {V.shape}")

    print("\n[3/3] Calculating sample statistics...")
    stats = converter.calculate_sample_statistics(atoms, grid_size=128, pixel_size=0.1)
    for key, value in stats.items():
        if isinstance(value, bool):
            print(f"  {key}: {value}")
        else:
            print(f"  {key}: {value:.6e}")

    print("\nSmoke-test complete — potential visualization disabled in smoke-test")
    print("Next steps: integrate with quscope.quantum_ctem and run the MoS2 workflow")


if __name__ == "__main__":
    """Run test suite."""
    test_potential_converter()
