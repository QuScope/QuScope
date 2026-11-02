"""
Projected atomic potentials from abTEM's parametrizations.

QuScope does not carry its own scattering-factor tables. Projected potentials come from abTEM
(https://abtem.readthedocs.io), using one of two parametrizations:

* ``"kirkland"``: Kirkland, *Advanced Computing in Electron Microscopy* (2nd ed., 2010), Appendix C
* ``"lobato"``: Lobato and Van Dyck, Acta Cryst. A70, 636 (2014)

Both return the electron-optical projected potential of a neutral atom in V*Angstrom (numerically eV*Angstrom
for a unit charge), which is what the phase grating ``exp(i sigma V)`` needs with sigma in rad/(V*Angstrom).

abTEM is a dependency of QuScope for this reason; there is no fallback table.

Example:
    >>> from quscope.ctem import AtomicPotential
    >>> pot = AtomicPotential("lobato")
    >>> x = np.linspace(-5, 5, 200)
    >>> V = pot.calculate_2d(x, np.zeros_like(x), atom_x=0.0, atom_y=0.0, Z=6)
"""

from typing import Iterable, Tuple

import numpy as np

PARAMETRIZATIONS = ("kirkland", "lobato")

# The projected potential diverges logarithmically at the nucleus; abTEM returns inf (Kirkland) or nan (Lobato)
# at r = 0. Distances are floored here so a grid point on top of an atom gets a large, finite value.
R_MIN = 1e-3  # Angstrom


def _load(name: str):
    try:
        from abtem import parametrizations as P
    except ImportError as exc:  # pragma: no cover - abtem is a declared dependency
        raise ImportError(
            "QuScope takes atomic potentials from abTEM. Install it with `pip install abtem`."
        ) from exc
    if name == "kirkland":
        return P.KirklandParametrization()
    if name == "lobato":
        return P.LobatoParametrization()
    raise ValueError(f"Unknown parametrization {name!r}; choose one of {PARAMETRIZATIONS}.")


def element_symbol(Z: int) -> str:
    """Element symbol for atomic number Z (1 to 118)."""
    from ase.data import chemical_symbols

    if not 1 <= int(Z) < len(chemical_symbols):
        raise ValueError(f"Atomic number {Z} is out of range (1 to {len(chemical_symbols) - 1}).")
    return chemical_symbols[int(Z)]


class AtomicPotential:
    """Projected atomic potentials V(r) in V*Angstrom from abTEM's Kirkland or Lobato parametrization.

    Args:
        parametrization: ``"kirkland"`` (default) or ``"lobato"``.
    """

    def __init__(self, parametrization: str = "kirkland"):
        self.parametrization = str(parametrization).lower()
        self._p = _load(self.parametrization)
        self._cache = {}

    def get_element_symbol(self, Z: int) -> str:
        """Element symbol for atomic number Z."""
        return element_symbol(Z)

    def _function(self, element):
        symbol = element if isinstance(element, str) else element_symbol(element)
        if symbol not in self._cache:
            self._cache[symbol] = self._p.projected_potential(symbol)
        return self._cache[symbol]

    def projected_potential(self, element, r) -> np.ndarray:
        """V(r) [V*Angstrom] of a single atom at distance r [Angstrom]; element is a symbol or atomic number."""
        r = np.maximum(np.asarray(r, dtype=float), R_MIN)
        # abTEM's Lobato function only takes 1D input, so evaluate on a flat array for any shape
        flat = self._function(element)(r.ravel())
        return np.asarray(flat, dtype=float).reshape(r.shape)

    def calculate_2d(self, x_grid, y_grid, atom_x: float, atom_y: float, Z: int) -> np.ndarray:
        """Projected potential of one atom on a grid [V*Angstrom], same shape as ``x_grid``.

        Args:
            x_grid, y_grid: coordinates in Angstrom, same shape
            atom_x, atom_y: atom position in Angstrom
            Z: atomic number
        """
        x_grid, y_grid = np.asarray(x_grid, dtype=float), np.asarray(y_grid, dtype=float)
        if x_grid.shape != y_grid.shape:
            raise ValueError(f"Grid shape mismatch: x_grid {x_grid.shape} vs y_grid {y_grid.shape}")
        r = np.hypot(x_grid - atom_x, y_grid - atom_y)
        return self.projected_potential(Z, r)

    def calculate_multiple_atoms(self, x_grid, y_grid, atom_positions: Iterable[Tuple[float, float, int]]) -> np.ndarray:
        """Sum of the projected potentials of atoms given as (x, y, Z) tuples [V*Angstrom]."""
        V = np.zeros(np.shape(x_grid), dtype=float)
        for x, y, Z in atom_positions:
            V += self.calculate_2d(x_grid, y_grid, x, y, Z)
        return V
