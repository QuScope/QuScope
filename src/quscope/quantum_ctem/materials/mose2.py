"""
MoSe₂ (Molybdenum Diselenide) Material Definition.

Same 2H structure as MoS₂ with Se in place of S: a larger lattice constant and a thicker layer,
and a heavier chalcogen (Z=34 against 16), so the Se columns carry more contrast than S does.
"""

from typing import Dict

import numpy as np

from .base import AtomicScatteringParams, MaterialParameters
from .mos2 import MoS2


class MoSe2(MoS2):
    """
    Molybdenum Diselenide (MoSe₂) material for CTEM and STEM simulation.

    - Hexagonal in-plane symmetry, a = 3.29 Å
    - Se-Mo-Se sandwich with a Se-Se vertical distance of about 3.3 Å
    - Z-contrast between Mo (Z=42) and Se (Z=34) columns is weaker than for MoS₂

    The lattice constant and layer thickness are typical literature values for the 2H monolayer; pass
    your own structure to `get_projected_potential` if you need a specific relaxed geometry.

    Examples:
        >>> mose2 = MoSe2()
        >>> atoms = mose2.build_structure(nx=3, ny=2)
        >>> V = mose2.get_projected_potential(atoms, grid_size=256)
    """

    _FORMULA = "MoSe2"
    _LATTICE_A = 3.29
    _THICKNESS = 3.33

    # The projected potential comes from QuScope's full Kirkland table (quscope.ctem.KirklandPotential),
    # which covers Se; there is no separate per-material parameter set here.
    SCATTERING_PARAMS: Dict[str, AtomicScatteringParams] = {}

    def __init__(self, layer_type: str = "2H"):
        super().__init__(layer_type=layer_type)
        self._parameters = MaterialParameters(
            name="Molybdenum Diselenide",
            formula="MoSe₂",
            lattice_constants=(3.29, 3.29, 12.9),  # Å
            lattice_angles=(90.0, 90.0, 120.0),
            space_group="P6_3/mmc" if layer_type == "1H" else "P-3m1",
            elements=["Mo", "Se"],
            typical_thickness=6.9,  # single layer, Å
        )

    def get_scattering_params(self) -> Dict[str, AtomicScatteringParams]:
        """Not used for the potential (see class note); returned empty."""
        return {}

    def get_column_positions(self, atoms) -> Dict[str, np.ndarray]:
        """Projected column positions for Mo and Se, as (N, 2) arrays."""
        positions = atoms.get_positions()
        symbols = np.array(atoms.get_chemical_symbols())
        return {"Mo": positions[symbols == "Mo"][:, :2], "Se": positions[symbols == "Se"][:, :2]}
