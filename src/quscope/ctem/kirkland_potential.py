"""
Kirkland Atomic Potential Module

Implements the 2D projected atomic potential from Earl J. Kirkland's
"Advanced Computing in Electron Microscopy", 2nd Edition, Appendix C.

The potential is parameterized as:
    V(r) = Σᵢ[4π²aᵢ·K₀(2πr√bᵢ)] + Σᵢ[2π^(3/2)·cᵢ/dᵢ^(3/2)·exp(-π²r²/dᵢ)]

where K₀ is the modified Bessel function of the second kind.

Parameters (aᵢ, bᵢ, cᵢ, dᵢ) are tabulated in Kirkland Appendix C for each element.
The potential is scaled by 14.4 to convert to electron volts (eV).

Reference:
    Kirkland, E. J. (2010). Advanced Computing in Electron Microscopy (2nd ed.).
    Springer. ISBN 978-1-4419-6532-5
"""

import json
from pathlib import Path
from typing import Dict, Tuple, Union

import numpy as np
from scipy.special import kn


class KirklandPotential:
    """
    Calculate 2D projected atomic potential using Kirkland parameterization.

    This class provides methods to compute the electrostatic potential of atoms
    projected along the beam direction (z-axis) at 2D positions (x, y).

    Attributes:
        params_dict: Dictionary of Kirkland parameters {element: [[a], [b], [c], [d]]}
        V_scaling: Scaling factor to convert potential to eV (default 14.4)

    Example:
        >>> from quscope.ctem import KirklandPotential
        >>> pot = KirklandPotential()
        >>>
        >>> # Calculate potential for a single carbon atom
        >>> x = np.linspace(-5, 5, 100)
        >>> y = np.zeros_like(x)
        >>> V = pot.calculate_2d(x, y, atom_x=0, atom_y=0, Z=6)
        >>>
        >>> # Calculate potential for multiple atoms
        >>> positions = [(0, 0, 6), (5, 0, 14), (10, 0, 29)]  # (x, y, Z)
        >>> V_total = pot.calculate_multiple_atoms(x_grid, y_grid, positions)
    """

    # Default Kirkland parameters file location
    # Packaged copy (ships in wheels); the repo root holds the same file for
    # backwards compatibility with source checkouts.
    DEFAULT_PARAMS_FILE = Path(__file__).parent / "kirkland.json"

    # Physical constant: scaling factor for potential (eV)
    V_SCALING = 14.4

    def __init__(self, params_file: Union[str, Path, None] = None):
        """
        Initialize Kirkland potential calculator.

        Args:
            params_file: Path to JSON file with Kirkland parameters.
                        If None, uses default kirkland.json in project root.

        Raises:
            FileNotFoundError: If params file doesn't exist
            ValueError: If params file has invalid format
        """
        if params_file is None:
            params_file = self.DEFAULT_PARAMS_FILE

        params_file = Path(params_file)
        if not params_file.exists():
            raise FileNotFoundError(
                f"Kirkland parameters file not found: {params_file}\n"
                f"Expected location: {self.DEFAULT_PARAMS_FILE}"
            )

        with open(params_file, "r") as f:
            self.params_dict = json.load(f)

        self._validate_params()

    def _validate_params(self):
        """Validate that parameters file has correct structure."""
        for element, params in self.params_dict.items():
            if len(params) != 4:
                raise ValueError(
                    f"Invalid parameters for {element}: expected 4 arrays [a, b, c, d], "
                    f"got {len(params)}"
                )
            for i, param_name in enumerate(["a", "b", "c", "d"]):
                if len(params[i]) != 3:
                    raise ValueError(
                        f"Invalid {param_name} parameters for {element}: expected 3 values, "
                        f"got {len(params[i])}"
                    )

    def get_element_symbol(self, Z: int) -> str:
        """
        Convert atomic number to element symbol.

        Args:
            Z: Atomic number

        Returns:
            Element symbol (e.g., 'C' for Z=6)

        Raises:
            ValueError: If element not in parameters dictionary
        """
        # Common elements used in Kirkland examples
        Z_TO_SYMBOL = {
            1: "H",
            6: "C",
            7: "N",
            8: "O",
            13: "Al",
            14: "Si",
            16: "S",
            22: "Ti",
            26: "Fe",
            29: "Cu",
            31: "Ga",
            33: "As",
            38: "Sr",
            42: "Mo",
            47: "Ag",
            56: "Ba",
            57: "La",
            79: "Au",
            82: "Pb",
            92: "U",
        }

        symbol = Z_TO_SYMBOL.get(Z)
        if symbol is None or symbol not in self.params_dict:
            raise ValueError(
                f"Element with Z={Z} not found in parameters.\n"
                f"Available elements: {list(self.params_dict.keys())}"
            )
        return symbol

    def calculate_2d(
        self,
        x_grid: np.ndarray,
        y_grid: np.ndarray,
        atom_x: float,
        atom_y: float,
        Z: int,
    ) -> np.ndarray:
        """
        Calculate 2D projected atomic potential at grid points.

        This implements Kirkland's parameterization (Appendix C, Equations 5.8-5.10):

        V(r) = Σᵢ[4π²aᵢ·K₀(2πr√bᵢ)] + Σᵢ[2π^(3/2)·cᵢ/dᵢ^(3/2)·exp(-π²r²/dᵢ)]

        where:
        - r = √[(x-x_atom)² + (y-y_atom)²] is distance from atom center
        - K₀ is modified Bessel function of second kind, order 0
        - aᵢ, bᵢ, cᵢ, dᵢ are element-specific parameters from Kirkland Appendix C

        Args:
            x_grid: X coordinates (Angstroms), shape (M,) or (M, N)
            y_grid: Y coordinates (Angstroms), shape (M,) or (M, N)
            atom_x: X position of atom center (Angstroms)
            atom_y: Y position of atom center (Angstroms)
            Z: Atomic number

        Returns:
            Potential values in eV, same shape as x_grid

        Raises:
            ValueError: If element not available or grid shapes don't match

        Notes:
            - For r → 0, uses limiting form: K₀(x) ≈ -ln(x/2) - γ where γ = 0.5772156649
            - For large arguments (x > 50), uses asymptotic form: K₀(x) ≈ √(π/2x)·exp(-x)
            - Final potential is scaled by 14.4 to convert to eV
        """
        if x_grid.shape != y_grid.shape:
            raise ValueError(
                f"Grid shape mismatch: x_grid {x_grid.shape} vs y_grid {y_grid.shape}"
            )

        # Get element parameters
        element = self.get_element_symbol(Z)
        params = self.params_dict[element]
        a = np.array(params[0], dtype=float)
        b = np.array(params[1], dtype=float)
        c = np.array(params[2], dtype=float)
        d = np.array(params[3], dtype=float)

        # Calculate distance from atom center
        r2 = (x_grid - atom_x) ** 2 + (y_grid - atom_y) ** 2
        r = np.sqrt(r2)

        V = np.zeros_like(r, dtype=float)

        # Modified Bessel K₀ terms
        for i in range(3):
            if b[i] > 0:
                arg = 2 * np.pi * r * np.sqrt(b[i])

                # Handle different regimes for numerical stability
                mask_small = arg < 50
                mask_large = arg >= 50

                if np.any(mask_small):
                    V[mask_small] += 4 * np.pi**2 * a[i] * kn(0, arg[mask_small])

                if np.any(mask_large):
                    # Asymptotic form for large arguments
                    x = arg[mask_large]
                    V[mask_large] += (
                        4 * np.pi**2 * a[i] * np.sqrt(np.pi / (2 * x)) * np.exp(-x)
                    )

        # Gaussian terms
        for i in range(3):
            if d[i] > 0:
                V += (
                    2
                    * np.pi ** (3 / 2)
                    * c[i]
                    / d[i] ** (3 / 2)
                    * np.exp(-np.pi**2 * r2 / d[i])
                )

        # Handle r = 0 (atom center) using limiting form
        center_mask = r < 1e-8
        if np.any(center_mask):
            V_center = 0.0

            # K₀ limiting form: K₀(x) ≈ -ln(x/2) - γ for x → 0
            euler_gamma = 0.5772156649
            for i in range(3):
                if b[i] > 0:
                    small_arg = 2 * np.pi * 1e-8 * np.sqrt(b[i])
                    V_center += (
                        4 * np.pi**2 * a[i] * (-np.log(small_arg / 2) - euler_gamma)
                    )

            # Gaussian terms at r = 0
            for i in range(3):
                if d[i] > 0:
                    V_center += 2 * np.pi ** (3 / 2) * c[i] / d[i] ** (3 / 2)

            V[center_mask] = V_center

        # Apply scaling factor to convert to eV
        V *= self.V_SCALING

        return V

    def calculate_multiple_atoms(
        self,
        x_grid: np.ndarray,
        y_grid: np.ndarray,
        atom_positions: list[Tuple[float, float, int]],
    ) -> np.ndarray:
        """
        Calculate total potential from multiple atoms.

        Superposition principle: total potential is sum of individual atomic potentials.

        Args:
            x_grid: X coordinates (Angstroms)
            y_grid: Y coordinates (Angstroms)
            atom_positions: List of (x, y, Z) tuples for each atom

        Returns:
            Total potential in eV

        Example:
            >>> positions = [(0, 0, 6), (5, 0, 14), (10, 0, 29)]  # C, Si, Cu
            >>> V_total = pot.calculate_multiple_atoms(X, Y, positions)
        """
        V_total = np.zeros_like(x_grid, dtype=float)

        for atom_x, atom_y, Z in atom_positions:
            V_atom = self.calculate_2d(x_grid, y_grid, atom_x, atom_y, Z)
            V_total += V_atom

        return V_total

    def get_parameters(self, Z: int) -> Dict[str, np.ndarray]:
        """
        Get Kirkland parameters for an element.

        Args:
            Z: Atomic number

        Returns:
            Dictionary with keys 'a', 'b', 'c', 'd' containing parameter arrays

        Example:
            >>> params = pot.get_parameters(6)  # Carbon
            >>> print(f"a parameters: {params['a']}")
        """
        element = self.get_element_symbol(Z)
        params = self.params_dict[element]

        return {
            "a": np.array(params[0], dtype=float),
            "b": np.array(params[1], dtype=float),
            "c": np.array(params[2], dtype=float),
            "d": np.array(params[3], dtype=float),
        }
