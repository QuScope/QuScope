"""
Abstract Base Classes for Materials.

Defines the interface that all material classes must implement,
ensuring consistent handling of structure generation and potential calculation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class AtomicScatteringParams:
    """
    Kirkland parameterization for atomic scattering factors.

    Based on: Kirkland, "Advanced Computing in Electron Microscopy", Appendix C.
    The projected potential is computed as a sum of Gaussians:
        V(r) = Σ a_i * exp(-π * r² / b_i)

    Attributes:
        symbol: Element symbol (e.g., "C", "Mo", "S")
        atomic_number: Z
        a_coefficients: Gaussian amplitudes [Å²·V]
        b_coefficients: Gaussian widths [Å²]
    """

    symbol: str
    atomic_number: int
    a_coefficients: List[float] = field(default_factory=list)
    b_coefficients: List[float] = field(default_factory=list)

    def projected_potential(self, r: np.ndarray) -> np.ndarray:
        """
        Calculate projected potential at distance r from atom center.

        Args:
            r: Distance array in Ångströms

        Returns:
            Projected potential in V·Å
        """
        V = np.zeros_like(r)
        for a, b in zip(self.a_coefficients, self.b_coefficients):
            V += a * np.exp(-np.pi * r**2 / b)
        return V


@dataclass
class MaterialParameters:
    """
    Physical parameters for a material.

    Attributes:
        name: Material name
        formula: Chemical formula
        lattice_constants: (a, b, c) in Ångströms
        lattice_angles: (α, β, γ) in degrees
        space_group: Crystallographic space group
        elements: List of element symbols
        typical_thickness: Typical specimen thickness in Å
    """

    name: str
    formula: str
    lattice_constants: Tuple[float, float, float]
    lattice_angles: Tuple[float, float, float] = (90.0, 90.0, 90.0)
    space_group: str = "P1"
    elements: List[str] = field(default_factory=list)
    typical_thickness: float = 10.0  # Å

    @property
    def a(self) -> float:
        return self.lattice_constants[0]

    @property
    def b(self) -> float:
        return self.lattice_constants[1]

    @property
    def c(self) -> float:
        return self.lattice_constants[2]


class Material(ABC):
    """
    Abstract base class for materials in quantum CTEM simulations.

    Subclasses must implement:
    - build_structure(): Generate atomic structure
    - get_scattering_params(): Return Kirkland parameters for all elements
    """

    def __init__(self):
        self._parameters: Optional[MaterialParameters] = None
        self._scattering_params: Dict[str, AtomicScatteringParams] = {}

    @property
    @abstractmethod
    def parameters(self) -> MaterialParameters:
        """Get material parameters."""
        pass

    @property
    def name(self) -> str:
        return self.parameters.name

    @property
    def formula(self) -> str:
        return self.parameters.formula

    @abstractmethod
    def build_structure(self, **kwargs):
        """
        Build atomic structure for this material.

        Returns:
            ASE Atoms object representing the structure
        """
        pass

    @abstractmethod
    def get_scattering_params(self) -> Dict[str, AtomicScatteringParams]:
        """
        Get Kirkland scattering parameters for all elements.

        Returns:
            Dictionary mapping element symbol to AtomicScatteringParams
        """
        pass

    def get_projected_potential(
        self,
        atoms,
        grid_size: int = 256,
        pixel_size: float = 0.1,
        padding: float = 2.0,
    ) -> np.ndarray:
        """
        Calculate 2D projected potential for the structure.

        Args:
            atoms: ASE Atoms object
            grid_size: Number of pixels (grid_size × grid_size)
            pixel_size: Pixel size in Ångströms
            padding: Padding around structure in Å

        Returns:
            2D numpy array of projected potential in V·Å
        """
        positions = atoms.get_positions()
        symbols = atoms.get_chemical_symbols()
        scattering = self.get_scattering_params()

        # Determine grid bounds
        cell = atoms.get_cell()
        Lx = cell[0, 0] if cell[0, 0] > 0 else positions[:, 0].max() + padding
        Ly = cell[1, 1] if cell[1, 1] > 0 else positions[:, 1].max() + padding

        # Create coordinate grids
        x = np.linspace(0, Lx, grid_size)
        y = np.linspace(0, Ly, grid_size)
        X, Y = np.meshgrid(x, y)

        # Calculate projected potential
        V_proj = np.zeros((grid_size, grid_size))

        for pos, symbol in zip(positions, symbols):
            if symbol not in scattering:
                raise ValueError(f"No scattering parameters for element: {symbol}")

            params = scattering[symbol]
            r = np.sqrt((X - pos[0]) ** 2 + (Y - pos[1]) ** 2)
            V_proj += params.projected_potential(r)

        return V_proj

    def get_interaction_constant(self, voltage: float) -> float:
        """
        Calculate relativistic interaction constant σ.

        Args:
            voltage: Accelerating voltage in Volts

        Returns:
            Interaction constant in rad/(V·Å)
        """
        # Physical constants
        m0 = 9.10938e-31  # electron rest mass [kg]
        e = 1.60218e-19  # electron charge [C]
        h = 6.62607e-34  # Planck constant [J·s]
        c = 2.99792e8  # speed of light [m/s]

        # Relativistic wavelength
        E = voltage * e  # kinetic energy [J]
        E0 = m0 * c**2  # rest energy [J]
        wavelength = h / np.sqrt(2 * m0 * E * (1 + E / (2 * E0)))  # [m]
        wavelength_A = wavelength * 1e10  # [Å]

        # Relativistic factor
        gamma = 1 + E / E0

        # Interaction constant: σ = 2π * m * e * λ / h²
        # With relativistic correction
        sigma = (2 * np.pi * gamma * m0 * e * wavelength) / (h**2)
        sigma_A = sigma * 1e-10  # Convert to rad/(V·Å)

        return sigma_A

    def validate_structure(self, atoms) -> bool:
        """
        Validate that the structure is suitable for CTEM simulation.

        Args:
            atoms: ASE Atoms object

        Returns:
            True if valid, raises ValueError otherwise
        """
        # Check for required elements
        symbols = set(atoms.get_chemical_symbols())
        expected = set(self.parameters.elements)

        if not symbols.issubset(expected):
            unexpected = symbols - expected
            raise ValueError(
                f"Unexpected elements in structure: {unexpected}. "
                f"Expected: {expected}"
            )

        # Check for reasonable size
        if len(atoms) == 0:
            raise ValueError("Structure contains no atoms")

        if len(atoms) > 100000:
            raise ValueError(
                f"Structure too large ({len(atoms)} atoms). "
                "Consider using a smaller supercell."
            )

        return True

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(formula='{self.formula}')"
