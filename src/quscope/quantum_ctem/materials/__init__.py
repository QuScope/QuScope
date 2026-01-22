"""
Material Definitions for Quantum CTEM Simulation.

This module provides material-specific parameters and structure builders
for quantum CTEM simulations. Currently supports:
- MoS₂ (Molybdenum disulfide) - 2D transition metal dichalcogenide
- Graphene - 2D carbon allotrope

Usage:
    from quscope.quantum_ctem.materials import get_material, MoS2, Graphene

    # Get material by name
    material = get_material("mos2")
    atoms = material.build_structure(nx=3, ny=2)
    potential = material.get_projected_potential(atoms, grid_size=256)

    # Or use directly
    graphene = Graphene()
    atoms = graphene.build_supercell(nx=5, ny=5)
"""

from .base import Material, MaterialParameters, AtomicScatteringParams
from .mos2 import MoS2
from .graphene import Graphene

# Material registry
_MATERIAL_REGISTRY = {
    "mos2": MoS2,
    "MoS2": MoS2,
    "molybdenum_disulfide": MoS2,
    "graphene": Graphene,
    "Graphene": Graphene,
    "carbon": Graphene,
}


def get_material(name: str, **kwargs) -> Material:
    """
    Factory function to get a material instance.

    Args:
        name: Material name (e.g., "mos2", "graphene")
        **kwargs: Material-specific parameters

    Returns:
        Configured Material instance

    Examples:
        >>> material = get_material("mos2")
        >>> material = get_material("graphene", edge_type="zigzag")
    """
    name_lower = name.lower().replace("-", "_").replace(" ", "_")

    if name_lower not in _MATERIAL_REGISTRY:
        available = ", ".join(set(k.lower() for k in _MATERIAL_REGISTRY.keys()))
        raise ValueError(
            f"Unknown material: {name}. Available: {available}"
        )

    material_class = _MATERIAL_REGISTRY[name_lower]
    return material_class(**kwargs)


def list_materials() -> dict:
    """List all available materials with descriptions."""
    return {
        "mos2": "Molybdenum disulfide (MoS₂) - 2D TMD semiconductor",
        "graphene": "Graphene - 2D carbon with honeycomb lattice",
    }


__all__ = [
    "Material",
    "MaterialParameters",
    "AtomicScatteringParams",
    "MoS2",
    "Graphene",
    "get_material",
    "list_materials",
]
