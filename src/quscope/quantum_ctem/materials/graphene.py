"""
Graphene Material Definition.

Graphene is a 2D carbon allotrope with a honeycomb lattice structure.
As a weak phase object with light atoms (Z=6), it's ideal for testing
WPOA validity and quantum simulation accuracy.
"""

from typing import Dict, Optional

import numpy as np

from .base import AtomicScatteringParams, Material, MaterialParameters


class Graphene(Material):
    """
    Graphene material for CTEM simulation.

    Graphene has:
    - Honeycomb lattice with a ≈ 2.46 Å
    - Single atomic layer of carbon (Z=6)
    - Excellent WPOA validity due to weak scattering
    - Six-fold symmetry in diffraction pattern

    Attributes:
        edge_type: "zigzag" or "armchair" for nanoribbons

    Examples:
        >>> graphene = Graphene()
        >>> atoms = graphene.build_structure(nx=5, ny=5)
        >>> V = graphene.get_projected_potential(atoms, grid_size=256)

        >>> # Build nanoribbon
        >>> ribbon = graphene.build_nanoribbon(width=10, length=50)
    """

    # Kirkland scattering parameters for Carbon
    # From Kirkland, "Advanced Computing in Electron Microscopy", Appendix C
    SCATTERING_PARAMS = {
        "C": AtomicScatteringParams(
            symbol="C",
            atomic_number=6,
            a_coefficients=[0.7307, 0.6166, 0.2098, 0.1058],
            b_coefficients=[0.0207, 0.1813, 0.7028, 2.8454],
        ),
    }

    # Graphene lattice parameters
    LATTICE_CONSTANT = 2.46  # Å (in-plane)
    BOND_LENGTH = 1.42  # Å (C-C bond)
    LAYER_SPACING = 3.35  # Å (for multilayer)

    def __init__(self, edge_type: str = "zigzag"):
        """
        Initialize Graphene material.

        Args:
            edge_type: "zigzag" or "armchair" (affects nanoribbon edges)
        """
        super().__init__()
        self.edge_type = edge_type

        self._parameters = MaterialParameters(
            name="Graphene",
            formula="C",
            lattice_constants=(2.46, 2.46, 3.35),  # Å
            lattice_angles=(90.0, 90.0, 120.0),
            space_group="P6/mmm",
            elements=["C"],
            typical_thickness=3.35,  # Single layer
        )

    @property
    def parameters(self) -> MaterialParameters:
        return self._parameters

    def build_structure(
        self,
        nx: int = 5,
        ny: int = 5,
        vacuum: float = 10.0,
        **kwargs,
    ):
        """
        Build graphene supercell using ASE.

        Args:
            nx: Number of unit cells in x direction
            ny: Number of unit cells in y direction
            vacuum: Vacuum padding in z direction (Å)

        Returns:
            ASE Atoms object
        """
        try:
            from ase.build import graphene as ase_graphene
        except ImportError:
            raise ImportError(
                "ASE is required for structure building. "
                "Install with: pip install ase"
            )

        # Build graphene using ASE
        atoms = ase_graphene(
            a=self.LATTICE_CONSTANT,
            size=(nx, ny, 1),
            vacuum=vacuum,
        )
        atoms.center()

        return atoms

    def build_supercell(
        self,
        nx: int = 5,
        ny: int = 5,
        vacuum: float = 10.0,
    ):
        """Alias for build_structure for API consistency."""
        return self.build_structure(nx=nx, ny=ny, vacuum=vacuum)

    def build_nanoribbon(
        self,
        width: int = 10,
        length: int = 20,
        edge_type: Optional[str] = None,
        vacuum: float = 10.0,
        saturated: bool = False,
    ):
        """
        Build graphene nanoribbon.

        Args:
            width: Width in unit cells (perpendicular to ribbon axis)
            length: Length in unit cells (along ribbon axis)
            edge_type: "zigzag" or "armchair" (defaults to instance setting)
            vacuum: Vacuum padding (Å)
            saturated: If True, saturate edges with hydrogen

        Returns:
            ASE Atoms object
        """
        try:
            from ase.build import graphene_nanoribbon
        except ImportError:
            raise ImportError(
                "ASE is required for structure building. "
                "Install with: pip install ase"
            )

        edge = edge_type or self.edge_type
        if edge not in ["zigzag", "armchair"]:
            raise ValueError(f"edge_type must be 'zigzag' or 'armchair', got {edge}")

        atoms = graphene_nanoribbon(
            n=width,
            m=length,
            type=edge,
            saturated=saturated,
            vacuum=vacuum,
        )
        atoms.center()

        return atoms

    def build_with_vacancy(
        self,
        nx: int = 5,
        ny: int = 5,
        vacancy_fraction: float = 0.01,
        vacuum: float = 10.0,
        seed: Optional[int] = None,
    ):
        """
        Build graphene with random vacancies.

        Args:
            nx, ny: Supercell size
            vacancy_fraction: Fraction of atoms to remove (0-1)
            vacuum: Vacuum padding (Å)
            seed: Random seed for reproducibility

        Returns:
            ASE Atoms object with vacancies
        """
        atoms = self.build_structure(nx=nx, ny=ny, vacuum=vacuum)

        if seed is not None:
            np.random.seed(seed)

        n_atoms = len(atoms)
        n_remove = int(n_atoms * vacancy_fraction)

        if n_remove > 0:
            remove_indices = np.random.choice(n_atoms, n_remove, replace=False)
            # Remove atoms in reverse order to preserve indices
            for idx in sorted(remove_indices, reverse=True):
                del atoms[idx]

        return atoms

    def get_scattering_params(self) -> Dict[str, AtomicScatteringParams]:
        """Get Kirkland scattering parameters for Carbon."""
        return self.SCATTERING_PARAMS.copy()

    def get_sublattice_positions(self, atoms) -> Dict[str, np.ndarray]:
        """
        Get positions of A and B sublattice atoms.

        In graphene, the honeycomb lattice has two sublattices.
        This is useful for analyzing sublattice-resolved contrast.

        Args:
            atoms: ASE Atoms object

        Returns:
            Dictionary with "A" and "B" sublattice positions
        """
        positions = atoms.get_positions()[:, :2]

        # Determine sublattice based on fractional coordinates
        cell = atoms.get_cell()[:2, :2]

        # Simple heuristic: classify by y-coordinate modulo unit cell
        a = self.LATTICE_CONSTANT
        y_mod = positions[:, 1] % (a * np.sqrt(3) / 2)
        threshold = a * np.sqrt(3) / 4

        a_mask = y_mod < threshold
        b_mask = ~a_mask

        return {
            "A": positions[a_mask],
            "B": positions[b_mask],
        }

    def wpoa_validity(self, voltage: float = 200e3) -> Dict[str, float]:
        """
        Assess WPOA validity for graphene at given voltage.

        The WPOA is valid when σ·V_proj << 1.

        Args:
            voltage: Accelerating voltage in V

        Returns:
            Dictionary with validity metrics
        """
        sigma = self.get_interaction_constant(voltage)

        # Approximate maximum projected potential for C atom
        # Using peak value from Kirkland parameterization
        V_max_approx = sum(self.SCATTERING_PARAMS["C"].a_coefficients)

        phase_shift = sigma * V_max_approx

        return {
            "interaction_constant": sigma,
            "max_projected_potential": V_max_approx,
            "max_phase_shift": phase_shift,
            "wpoa_valid": phase_shift < 0.3,  # Rule of thumb: < 0.3 rad
            "validity_ratio": phase_shift / 0.3,
        }

    def expected_contrast(self, voltage: float = 200e3) -> str:
        """
        Describe expected CTEM contrast for graphene.

        Args:
            voltage: Accelerating voltage in V

        Returns:
            Description of expected contrast
        """
        validity = self.wpoa_validity(voltage)
        valid_str = "valid" if validity["wpoa_valid"] else "marginally valid"

        return (
            f"At {voltage/1e3:.0f} kV:\n"
            f"- WPOA is {valid_str} (phase shift: {validity['max_phase_shift']:.3f} rad)\n"
            "- Carbon atoms appear as weak spots in honeycomb pattern\n"
            "- Six-fold symmetry in diffraction\n"
            "- Very weak contrast compared to heavy elements\n"
            "- Ideal for validating quantum simulation accuracy"
        )

    def get_diffraction_spots(self) -> Dict[str, np.ndarray]:
        """
        Get expected diffraction spot positions for graphene.

        Returns:
            Dictionary with reciprocal lattice vectors and spot positions
        """
        a = self.LATTICE_CONSTANT
        # Reciprocal lattice vectors for hexagonal lattice
        b1 = 2 * np.pi / a * np.array([1, 1 / np.sqrt(3)])
        b2 = 2 * np.pi / a * np.array([0, 2 / np.sqrt(3)])

        return {
            "b1": b1,
            "b2": b2,
            "first_order": [b1, b2, b1 + b2, -b1, -b2, -(b1 + b2)],
            "lattice_constant": a,
        }
