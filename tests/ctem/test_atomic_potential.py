"""AtomicPotential: abTEM's Kirkland and Lobato projected potentials behind a QuScope interface."""

import numpy as np
import pytest

from quscope.ctem import AtomicPotential
from quscope.ctem.atomic_potential import R_MIN, element_symbol

abtem_param = pytest.importorskip("abtem.parametrizations")


@pytest.mark.parametrize("name, cls", [("kirkland", "KirklandParametrization"), ("lobato", "LobatoParametrization")])
@pytest.mark.parametrize("symbol", ["H", "C", "S", "Se", "Mo", "W", "Au"])
def test_matches_abtem_exactly(name, cls, symbol):
    r = np.array([0.05, 0.2, 0.5, 1.0, 2.0, 4.0])
    ref = getattr(abtem_param, cls)().projected_potential(symbol)(r)
    assert np.array_equal(AtomicPotential(name).projected_potential(symbol, r), ref)


def test_atomic_number_and_symbol_agree():
    pot = AtomicPotential()
    r = np.array([0.1, 0.5, 1.5])
    for Z in (6, 34, 42, 79):
        assert np.array_equal(pot.projected_potential(Z, r), pot.projected_potential(element_symbol(Z), r))


def test_element_symbols():
    assert [element_symbol(Z) for Z in (1, 16, 34, 74, 92, 103)] == ["H", "S", "Se", "W", "U", "Lr"]
    for bad in (0, 119):
        with pytest.raises(ValueError):
            element_symbol(bad)


@pytest.mark.parametrize("name", ["kirkland", "lobato"])
def test_finite_at_the_nucleus_and_monotonic(name):
    pot = AtomicPotential(name)
    r = np.array([0.0, R_MIN, 0.01, 0.1, 0.5, 1.0, 2.0, 3.0])
    v = pot.projected_potential("Au", r)
    assert np.isfinite(v).all()
    assert v[0] == v[1]  # r = 0 is floored at R_MIN
    assert np.all(np.diff(v[1:]) < 0)


def test_heavier_atoms_scatter_more_in_the_core_region():
    # inside 0.5 A; further out the order can change (Au falls below Mo near 1 A in abTEM's tables)
    r = np.array([0.2, 0.5])
    v = {Z: AtomicPotential().projected_potential(Z, r) for Z in (6, 16, 34, 42, 79)}
    for lo, hi in [(6, 16), (16, 34), (34, 42), (42, 79)]:
        assert np.all(v[lo] < v[hi])


def test_calculate_2d_is_radial_and_additive():
    pot = AtomicPotential()
    x = np.linspace(-3, 3, 61)
    X, Y = np.meshgrid(x, x)
    one = pot.calculate_2d(X, Y, 0.5, -0.5, 14)
    assert one.shape == X.shape
    two = pot.calculate_multiple_atoms(X, Y, [(0.5, -0.5, 14), (-1.0, 1.0, 8)])
    assert np.allclose(two, one + pot.calculate_2d(X, Y, -1.0, 1.0, 8))
    assert np.allclose(pot.calculate_2d(X, Y, 0.0, 0.0, 6), pot.calculate_2d(Y, X, 0.0, 0.0, 6))
    with pytest.raises(ValueError):
        pot.calculate_2d(X, Y[:-1], 0, 0, 6)


def test_unknown_parametrization_is_rejected():
    with pytest.raises(ValueError):
        AtomicPotential("peng")


@pytest.mark.parametrize("name", ["kirkland", "lobato"])
def test_accepts_arrays_of_any_shape(name):
    pot = AtomicPotential(name)
    r1 = np.linspace(0.1, 3.0, 12)
    r2 = r1.reshape(3, 4)
    r3 = np.stack([r2, r2 * 1.5])
    assert np.array_equal(pot.projected_potential("Mo", r2), pot.projected_potential("Mo", r1).reshape(3, 4))
    assert pot.projected_potential("Mo", r3).shape == r3.shape
    assert pot.projected_potential("Mo", 0.7).shape == ()
