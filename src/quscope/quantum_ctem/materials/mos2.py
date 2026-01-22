"""
MoS₂ (Molybdenum Disulfide) Material Definition.

MoS₂ is a 2D transition metal dichalcogenide with hexagonal structure,
commonly used as a test case for CTEM simulations due to its clear
Mo and S column contrast.
"""

from typing import Dict, Optional

import numpy as np

from .base import AtomicScatteringParams, Material, MaterialParameters


class MoS2(Material):
    """
    Molybdenum Disulfide (MoS₂) material for CTEM simulation.

    MoS₂ has a layered structure with:
    - Hexagonal in-plane symmetry (a ≈ 3.16 Å)
    - S-Mo-S sandwich structure
    - Clear Z-contrast between Mo (Z=42) and S (Z=16) columns

    Attributes:
        layer_type: "1H" (trigonal prismatic) or "1T" (octahedral)

    Examples:
        >>> mos2 = MoS2()
        >>> atoms = mos2.build_structure(nx=3, ny=2)
        >>> V = mos2.get_projected_potential(atoms, grid_size=256)
    """

    # Kirkland scattering parameters for Mo and S
    # From Kirkland, "Advanced Computing in Electron Microscopy", Appendix C
    SCATTERING_PARAMS = {
        "Mo": AtomicScatteringParams(
            symbol="Mo",
            atomic_number=42,
            a_coefficients=[2.5460, 2.6963, 1.8027, 0.5960],
            b_coefficients=[0.0667, 0.5717, 3.1346, 12.313],
        ),
        "S": AtomicScatteringParams(
            symbol="S",
            atomic_number=16,
            a_coefficients=[1.2052, 1.1717, 0.4403, 0.2037],
            b_coefficients=[0.0331, 0.2636, 1.0096, 4.1210],
        ),
    }

    # Map layer types to ASE mx2 kind parameter
    _ASE_KIND_MAP = {"1H": "2H", "2H": "2H", "1T": "1T"}

    def __init__(self, layer_type: str = "2H"):
        """
        Initialize MoS₂ material.

        Args:
            layer_type: "2H" for trigonal prismatic (semiconductor, default),
                       "1T" for octahedral (metallic)
        """
        super().__init__()
        if layer_type not in self._ASE_KIND_MAP:
            raise ValueError(f"layer_type must be '2H' or '1T', got {layer_type}")
        self.layer_type = layer_type
        self._ase_kind = self._ASE_KIND_MAP[layer_type]

        self._parameters = MaterialParameters(
            name="Molybdenum Disulfide",
            formula="MoS₂",
            lattice_constants=(3.16, 3.16, 12.29),  # Å
            lattice_angles=(90.0, 90.0, 120.0),
            space_group="P6_3/mmc" if layer_type == "1H" else "P-3m1",
            elements=["Mo", "S"],
            typical_thickness=6.5,  # Single layer ~6.5 Å
        )

    @property
    def parameters(self) -> MaterialParameters:
        return self._parameters

    def build_structure(
        self,
        nx: int = 3,
        ny: int = 2,
        vacuum: float = 10.0,
        **kwargs,
    ):
        """
        Build MoS₂ supercell using ASE.

        Args:
            nx: Number of unit cells in x direction
            ny: Number of unit cells in y direction
            vacuum: Vacuum padding in z direction (Å)

        Returns:
            ASE Atoms object
        """
        try:
            from ase.build import mx2
        except ImportError:
            raise ImportError(
                "ASE is required for structure building. "
                "Install with: pip install ase"
            )

        # Build MoS₂ using ASE's mx2 builder
        atoms = mx2(
            formula="MoS2",
            kind=self._ase_kind,
            a=self.parameters.a,
            vacuum=vacuum,
        )

        # Create supercell
        atoms = atoms.repeat((nx, ny, 1))
        atoms.center()

        return atoms

    def build_supercell(
        self,
        nx: int = 3,
        ny: int = 2,
        vacuum: float = 10.0,
    ):
        """Alias for build_structure for API consistency."""
        return self.build_structure(nx=nx, ny=ny, vacuum=vacuum)

    def get_scattering_params(self) -> Dict[str, AtomicScatteringParams]:
        """Get Kirkland scattering parameters for Mo and S."""
        return self.SCATTERING_PARAMS.copy()

    def get_column_positions(self, atoms) -> Dict[str, np.ndarray]:
        """
        Get projected column positions for Mo and S.

        Useful for analyzing image contrast at column locations.

        Args:
            atoms: ASE Atoms object

        Returns:
            Dictionary with "Mo" and "S" keys containing (N, 2) position arrays
        """
        positions = atoms.get_positions()
        symbols = atoms.get_chemical_symbols()

        mo_pos = positions[np.array(symbols) == "Mo"][:, :2]
        s_pos = positions[np.array(symbols) == "S"][:, :2]

        return {"Mo": mo_pos, "S": s_pos}

    def expected_contrast(self, voltage: float = 200e3) -> str:
        """
        Describe expected CTEM contrast for MoS₂.

        Args:
            voltage: Accelerating voltage in V

        Returns:
            Description of expected contrast
        """
        return (
            f"At {voltage/1e3:.0f} kV:\n"
            "- Mo columns appear as bright spots (high Z, strong scattering)\n"
            "- S columns appear dimmer (lower Z)\n"
            "- Hexagonal pattern with Mo at corners, S in trigonal positions\n"
            "- With underfocus: bright atom contrast\n"
            "- With overfocus: dark atom contrast (inverted)"
        )
