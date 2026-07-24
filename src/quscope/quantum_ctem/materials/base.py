"""
Abstract Base Classes for Materials.

Defines the interface that all material classes must implement,
ensuring consistent handling of structure generation and potential calculation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ...ctem.kirkland_potential import KirklandPotential


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
        supersample: int = 4,
        thermal_sigma: float = 0.08,
    ) -> np.ndarray:
        """
        Calculate 2D projected potential for the structure.

        Uses QuScope's own Kirkland scattering-factor tables
        (quscope.ctem.KirklandPotential, Kirkland Appendix C, full
        Bessel-K0-plus-Gaussian parametrization) rather than an ad hoc
        per-material approximation, so results are consistent with the
        rest of the package (quantum_ctem_circuit, the paper figures, etc).

        Args:
            atoms: ASE Atoms object
            grid_size: Number of pixels (grid_size × grid_size)
            pixel_size: Pixel size in Ångströms -- this fixes the field of
                view to grid_size * pixel_size; it does not depend on the
                ASE cell size, so the physical sampling here always matches
                what any downstream CTF/QFT frequency grid assumes.
            padding: unused (kept for backward-compatible signature);
                atoms outside the field of view are still included via a
                one-cell periodic margin so their potential tails aren't
                abruptly clipped at the boundary.
            supersample: evaluate the (near-singular, log-divergent at the
                atom core) potential on a supersample*grid_size grid and
                average-pool down to grid_size, so peak heights don't alias
                depending on exactly where an atom center falls relative to
                a pixel. supersample=1 disables this (raw point sampling).
            thermal_sigma: Gaussian (Debye-Waller-like) smearing width in
                Angstrom, representing thermal atomic vibration -- a real
                specimen at finite temperature, not a mathematical point
                charge. Without this the Kirkland potential's log-divergent
                core makes sigma*V wrap through many multiples of 2*pi
                within a single pixel step, aliasing the WPOA transmission
                function into speckle. 0.08 A is a typical light/mid-Z RMS
                thermal displacement; set to 0 to disable.

        Returns:
            2D numpy array of projected potential in V·Å
        """
        positions = atoms.get_positions()
        atomic_numbers = atoms.get_atomic_numbers()
        kirkland = KirklandPotential()

        # Pixel-center coordinates (Angstrom) at the supersampled resolution
        # -- grid_size * pixel_size is the actual field of view, matching
        # QuantumCTEMCircuit's convention.
        Ns = grid_size * supersample
        coords = (np.arange(Ns) + 0.5) * (pixel_size / supersample)
        X, Y = np.meshgrid(coords, coords, indexing="ij")
        L = grid_size * pixel_size

        V_super = np.zeros((Ns, Ns))
        margin = 3.0  # A; Kirkland potentials fall off quickly beyond a few A
        for pos, Z in zip(positions, atomic_numbers):
            if not (-margin <= pos[0] < L + margin and -margin <= pos[1] < L + margin):
                continue
            V_super += kirkland.calculate_2d(X, Y, atom_x=pos[0], atom_y=pos[1], Z=int(Z))

        if thermal_sigma > 0:
            from scipy.ndimage import gaussian_filter

            V_super = gaussian_filter(V_super, sigma=thermal_sigma / (pixel_size / supersample))

        if supersample > 1:
            V_super = V_super.reshape(
                grid_size, supersample, grid_size, supersample
            ).mean(axis=(1, 3))

        return V_super

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
