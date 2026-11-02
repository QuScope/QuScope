"""MoSe2 material."""

import numpy as np
import pytest

from quscope.ctem import AtomicPotential
from quscope.quantum_ctem.materials import MoS2, MoSe2, get_material, list_materials


def test_mose2_structure_and_registry():
    m = get_material("MoSe2")
    assert isinstance(m, MoSe2) and "mose2" in list_materials()
    atoms = m.build_structure(nx=3, ny=2)
    assert atoms.get_chemical_formula() == "Mo6Se12"
    assert abs(atoms.cell.lengths()[0] - 3 * 3.29) < 1e-6
    z = atoms.positions[:, 2]
    assert abs((z.max() - z.min()) - 3.33) < 1e-6
    cols = m.get_column_positions(atoms)
    assert cols["Mo"].shape == (6, 2) and cols["Se"].shape == (12, 2)


def test_mos2_is_unchanged_by_the_subclassing():
    atoms = MoS2().build_structure(nx=2, ny=2)
    assert atoms.get_chemical_formula() == "Mo4S8"
    assert abs(atoms.cell.lengths()[0] - 2 * 3.16) < 1e-6
    z = atoms.positions[:, 2]
    assert abs((z.max() - z.min()) - 3.19) < 1e-6   # ASE default layer thickness


def test_selenium_scatters_between_sulfur_and_molybdenum_near_the_core():
    r = np.array([0.2, 0.5])
    pot = AtomicPotential()
    s, se, mo = (pot.projected_potential(e, r) for e in ("S", "Se", "Mo"))
    assert np.all(s < se) and np.all(se < mo)


@pytest.mark.parametrize("parametrization", ["kirkland", "lobato"])
def test_mose2_potential_is_finite_and_positive(parametrization):
    m = MoSe2()
    V = m.get_projected_potential(m.build_structure(nx=2, ny=2), grid_size=32, pixel_size=0.4,
                                  parametrization=parametrization)
    assert np.isfinite(V).all() and V.max() > 0 and V.min() >= 0
