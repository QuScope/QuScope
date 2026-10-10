"""MoSe2 material and the full Z -> symbol table of the Kirkland potential."""

import json
from pathlib import Path

import numpy as np
import pytest

from quscope.ctem.kirkland_potential import ELEMENT_SYMBOLS, KirklandPotential
from quscope.quantum_ctem.materials import MoS2, MoSe2, get_material, list_materials


def test_symbol_table_matches_the_parameter_file():
    path = Path(__import__("quscope.ctem", fromlist=["x"]).__file__).parent / "kirkland.json"
    assert list(json.load(open(path))) == list(ELEMENT_SYMBOLS)
    assert len(ELEMENT_SYMBOLS) == 103


@pytest.mark.parametrize("Z, symbol", [(1, "H"), (16, "S"), (34, "Se"), (42, "Mo"), (74, "W"), (103, "Lr")])
def test_every_tabulated_element_resolves(Z, symbol):
    assert KirklandPotential().get_element_symbol(Z) == symbol


def test_unknown_atomic_number_raises():
    with pytest.raises(ValueError):
        KirklandPotential().get_element_symbol(104)


def test_selenium_potential_lies_between_sulfur_and_molybdenum():
    k = KirklandPotential()
    r = np.array([[0.2, 0.4, 0.8]])
    v = {Z: k.calculate_2d(r, np.zeros_like(r), 0.0, 0.0, Z)[0] for Z in (16, 34, 42)}
    assert np.all(v[16] < v[34]) and np.all(v[34] < v[42])


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


def test_mos2_is_unchanged_by_the_refactor():
    atoms = MoS2().build_structure(nx=2, ny=2)
    assert atoms.get_chemical_formula() == "Mo4S8"
    assert abs(atoms.cell.lengths()[0] - 2 * 3.16) < 1e-6
    z = atoms.positions[:, 2]
    assert abs((z.max() - z.min()) - 3.19) < 1e-6   # ASE default layer thickness


def test_mose2_potential_is_finite_and_positive():
    m = MoSe2()
    V = m.get_projected_potential(m.build_structure(nx=2, ny=2), grid_size=32, pixel_size=0.4)
    assert np.isfinite(V).all() and V.max() > 0 and V.min() >= 0
