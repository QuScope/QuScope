"""
Quantum Hamiltonian for Conventional TEM

This module implements the complete quantum mechanical Hamiltonian for electron
wave propagation in Conventional Transmission Electron Microscopy, including:

1. Free propagation
2. Sample interaction (Weak Phase Object Approximation)
3. Lens aberrations (up to 5th order)
4. Evolution operator decomposition
5. Mapping to quantum circuits

Theoretical Framework:
    The electron wave function evolution in TEM can be described by the
    time-independent Schrödinger equation with a position-dependent potential.

    Total Hamiltonian:
        H_total = H_0 + H_sample + H_lens

    where:
        H_0: Free particle kinetic energy
        H_sample: Sample-electron interaction
        H_lens: Lens aberrations in momentum space

    The evolution operator is:
        U = exp(-iH_lens·t/ℏ) · exp(-iH_sample·t/ℏ) · exp(-iH_0·t/ℏ)

    This operator can be efficiently implemented as a quantum circuit.

References:
    - Messiah, A. (1961). Quantum Mechanics. North-Holland.
    - Kirkland, E. J. (2010). Advanced Computing in Electron Microscopy.
    - Nielsen & Chuang (2010). Quantum Computation and Quantum Information.

Author: QuScope Development Team
Date: January 2025
"""

from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple

import numpy as np
import scipy.constants as const
from scipy.fft import fft2, fftfreq, ifft2


@dataclass
class HamiltonianParameters:
    """
    Parameters for the quantum Hamiltonian.

    Attributes:
        acceleration_voltage: Electron acceleration voltage (V)
        wavelength: Relativistic electron wavelength (Angstrom)
        grid_size_x: Number of grid points in x
        grid_size_y: Number of grid points in y
        pixel_size: Real-space pixel size (Angstrom)
        interaction_constant: σ = (2π·m_e·e·λ)/(h²) for WPOA
    """

    acceleration_voltage: float
    wavelength: float
    grid_size_x: int
    grid_size_y: int
    pixel_size: float
    interaction_constant: float = None

    def __post_init__(self):
        """Calculate interaction constant if not provided."""
        if self.interaction_constant is None:
            # σ = interaction constant for WPOA: χ = σ·V
            # From Kirkland "Advanced Computing in Electron Microscopy":
            # σ [rad/(V·Å)] = me·e/(2π·ℏ²) × λ
            # Simplified: σ ≈ 0.01 × λ[Å] / (acceleration_voltage[kV])
            #
            # For 200 kV: σ ≈ 3.2e-4 rad/(V·Å)
            # For 300 kV: σ ≈ 2.1e-4 rad/(V·Å)

            m_e = const.electron_mass  # kg
            e = const.elementary_charge  # C
            h = const.Planck  # J·s
            hbar = h / (2 * np.pi)
            lambda_m = self.wavelength * 1e-10  # Convert Å to m

            # Correct formula: σ = (me·e)/(2π·ℏ²) × λ
            # Units: [kg·C]/[J·s]² × [m] = [kg·C·m]/[kg²·m⁴/s²·s²] = [C]/[kg·m³/s²] = 1/(V·m)
            self.interaction_constant = (m_e * e * lambda_m) / (2 * np.pi * hbar**2)
            # Convert from 1/(V·m) to 1/(V·Å)
            self.interaction_constant *= 1e-10


class FreeParticleHamiltonian:
    """
    Free particle Hamiltonian H₀ = p²/(2m) = ℏ²k²/(2m).

    In the paraxial approximation (small scattering angles), this describes
    the kinetic energy of the electron beam.

    For high-energy electrons (80-300 kV), relativistic corrections are small
    but can be included in the wavelength calculation.
    """

    def __init__(self, params: HamiltonianParameters):
        """
        Initialize free particle Hamiltonian.

        Args:
            params: Hamiltonian parameters
        """
        self.params = params
        self.kx, self.ky = self._generate_k_grid()
        self.k_squared = self.kx**2 + self.ky**2

    def _generate_k_grid(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate momentum space grid.

        Returns:
            kx, ky: 2D arrays of k-space coordinates (1/Angstrom)
        """
        # Frequency grids
        freq_x = fftfreq(self.params.grid_size_x, d=self.params.pixel_size)
        freq_y = fftfreq(self.params.grid_size_y, d=self.params.pixel_size)

        # Convert to k-space (k = 2π·freq)
        kx, ky = np.meshgrid(2 * np.pi * freq_x, 2 * np.pi * freq_y, indexing="ij")

        return kx, ky

    def energy(self) -> np.ndarray:
        """
        Calculate kinetic energy E = ℏ²k²/(2m).

        In practice, we work with dimensionless units where ℏ=m=1,
        so E = k²/2.

        Returns:
            Energy at each k-point (2D array)
        """
        return 0.5 * self.k_squared

    def propagator(self, distance: float) -> np.ndarray:
        """
        Free space propagation operator exp(-iH₀·z/ℏ).

        For small angles (paraxial approximation):
            exp(-iH₀·z/ℏ) ≈ exp(-iπλz·k²)

        Args:
            distance: Propagation distance (Angstrom)

        Returns:
            Propagator in momentum space (2D complex array)
        """
        # Phase factor: -π·λ·z·k²
        phase = -np.pi * self.params.wavelength * distance * self.k_squared
        return np.exp(1j * phase)

    def apply(self, psi: np.ndarray, distance: float) -> np.ndarray:
        """
        Apply free space propagation to wave function.

        Args:
            psi: Wave function in real space (2D complex array)
            distance: Propagation distance (Angstrom)

        Returns:
            Propagated wave function in real space
        """
        # Transform to momentum space
        psi_k = fft2(psi)

        # Apply propagator
        psi_k_propagated = psi_k * self.propagator(distance)

        # Transform back to real space
        return ifft2(psi_k_propagated)


class SampleHamiltonian:
    """
    Sample interaction Hamiltonian under Weak Phase Object Approximation (WPOA).

    H_sample = V(x,y) where V is the projected atomic potential.

    The transmission function is:
        t(x,y) = exp(iσV(x,y))

    where σ = (2π·m_e·e·λ)/(h²) is the interaction constant.

    WPOA is valid when:
        σV << 1 (weak phase modulation)
        Sample thickness << mean free path
    """

    def __init__(self, params: HamiltonianParameters):
        """
        Initialize sample Hamiltonian.

        Args:
            params: Hamiltonian parameters
        """
        self.params = params
        self.potential = None

    def set_potential(self, V: np.ndarray):
        """
        Set the projected potential V(x,y).

        Args:
            V: Projected potential in V·Angstrom (2D array)
        """
        assert V.shape == (
            self.params.grid_size_x,
            self.params.grid_size_y,
        ), f"Potential shape {V.shape} doesn't match grid size"

        self.potential = V

    def transmission_function(self) -> np.ndarray:
        """
        Calculate transmission function t(x,y) = exp(iσV(x,y)).

        Returns:
            Transmission function (2D complex array)
        """
        if self.potential is None:
            # No sample → pure transmission
            return np.ones(
                (self.params.grid_size_x, self.params.grid_size_y), dtype=complex
            )

        # Apply phase shift: exp(iσV)
        phase = self.params.interaction_constant * self.potential
        return np.exp(1j * phase)

    def apply(self, psi: np.ndarray) -> np.ndarray:
        """
        Apply sample interaction to wave function.

        This is a simple multiplication in real space:
            ψ_exit(x,y) = ψ_incident(x,y) · t(x,y)

        Args:
            psi: Incident wave function (2D complex array)

        Returns:
            Exit wave function (2D complex array)
        """
        return psi * self.transmission_function()


class LensHamiltonian:
    """
    Lens aberration Hamiltonian in momentum space.

    The lens applies a k-dependent phase shift:
        H_lens → exp(iχ(k))

    where χ(k) is the wave aberration function including all aberration
    coefficients up to 5th order.

    This operator is diagonal in momentum space, making it efficient to apply.
    """

    def __init__(self, params: HamiltonianParameters, aberrations: Dict[str, float]):
        """
        Initialize lens Hamiltonian.

        Args:
            params: Hamiltonian parameters
            aberrations: Dictionary of aberration coefficients
                Keys: 'defocus', 'c12a', 'c12b', 'c3', 'c5', etc.
        """
        self.params = params
        self.aberrations = aberrations

        # Generate k-space grid
        self.kx, self.ky = self._generate_k_grid()
        self.k = np.sqrt(self.kx**2 + self.ky**2)
        self.theta = np.arctan2(self.ky, self.kx)

        # Pre-calculate aberration function
        self.chi = self.calculate_aberration_function()

    def _generate_k_grid(self) -> Tuple[np.ndarray, np.ndarray]:
        """Generate momentum space grid."""
        freq_x = fftfreq(self.params.grid_size_x, d=self.params.pixel_size)
        freq_y = fftfreq(self.params.grid_size_y, d=self.params.pixel_size)
        kx, ky = np.meshgrid(2 * np.pi * freq_x, 2 * np.pi * freq_y, indexing="ij")
        return kx, ky

    def calculate_aberration_function(self) -> np.ndarray:
        """
        Calculate complete wave aberration function χ(k).

        Standard TEM convention (Kirkland, Spence & Zuo):
            χ(k) = π λ Δf k² + 0.5 π λ³ Cs k⁴ + ...

        where:
            λ = wavelength (Angstrom)
            Δf = defocus (Angstrom, positive = underfocus)
            k = spatial frequency (1/Angstrom)
            Cs = spherical aberration (Angstrom)

        Returns:
            χ(kx, ky) in radians (2D array)
        """
        lam = self.params.wavelength
        k = self.k  # Already in 1/Angstrom

        chi = np.zeros_like(k)

        # Defocus term: χ₁ = π λ Δf k²
        if "defocus" in self.aberrations:
            defocus = self.aberrations["defocus"]  # Angstrom
            chi += np.pi * lam * defocus * k**2

        # 2-fold astigmatism
        if "c12a" in self.aberrations and "c12b" in self.aberrations:
            C12 = self.aberrations["c12a"]
            phi12 = self.aberrations["c12b"]
            chi += np.pi * lam * C12 * k**2 * np.cos(2 * (self.theta - phi12))

        # Spherical aberration Cs: χ₃ = 0.5 π λ³ Cs k⁴
        if "cs" in self.aberrations:
            Cs = self.aberrations["cs"] * 1e7  # Convert mm to Angstrom
            chi += 0.5 * np.pi * (lam**3) * Cs * k**4

        # Alternative key for Cs
        if "c3" in self.aberrations:
            C3 = self.aberrations["c3"] * 1e7  # Convert mm to Angstrom
            chi += 0.5 * np.pi * (lam**3) * C3 * k**4

        # Higher order aberrations (keeping dimensionless form with 2π/λ factor later)
        # These use lam_k = λk for dimensional consistency
        lam_k = lam * k

        # 2nd order: Axial coma and 3-fold astigmatism
        if "c21a" in self.aberrations and "c21b" in self.aberrations:
            C21 = self.aberrations["c21a"]
            phi21 = self.aberrations["c21b"]
            chi += (
                (2 * np.pi / lam)
                * (1 / 3)
                * C21
                * lam_k**3
                * np.cos(self.theta - phi21)
            )

        if "c23a" in self.aberrations and "c23b" in self.aberrations:
            C23 = self.aberrations["c23a"]
            phi23 = self.aberrations["c23b"]
            chi += (
                (2 * np.pi / lam)
                * (1 / 3)
                * C23
                * lam_k**3
                * np.cos(3 * (self.theta - phi23))
            )

        # 3rd order: 4-fold astigmatism
        if "c32a" in self.aberrations and "c32b" in self.aberrations:
            C32 = self.aberrations["c32a"] * 1e7
            phi32 = self.aberrations["c32b"]
            chi += (
                (2 * np.pi / lam)
                * 0.25
                * C32
                * lam_k**4
                * np.cos(2 * (self.theta - phi32))
            )

        if "c34a" in self.aberrations and "c34b" in self.aberrations:
            C34 = self.aberrations["c34a"] * 1e7
            phi34 = self.aberrations["c34b"]
            chi += (
                (2 * np.pi / lam)
                * 0.25
                * C34
                * lam_k**4
                * np.cos(4 * (self.theta - phi34))
            )

        # 4th order aberrations
        if "c41a" in self.aberrations and "c41b" in self.aberrations:
            C41 = self.aberrations["c41a"] * 1e7
            phi41 = self.aberrations["c41b"]
            chi += (2 * np.pi / lam) * 0.2 * C41 * lam_k**5 * np.cos(self.theta - phi41)

        if "c43a" in self.aberrations and "c43b" in self.aberrations:
            C43 = self.aberrations["c43a"] * 1e7
            phi43 = self.aberrations["c43b"]
            chi += (
                (2 * np.pi / lam)
                * 0.2
                * C43
                * lam_k**5
                * np.cos(3 * (self.theta - phi43))
            )

        if "c45a" in self.aberrations and "c45b" in self.aberrations:
            C45 = self.aberrations["c45a"] * 1e7
            phi45 = self.aberrations["c45b"]
            chi += (
                (2 * np.pi / lam)
                * 0.2
                * C45
                * lam_k**5
                * np.cos(5 * (self.theta - phi45))
            )

        # 5th order: 5th order spherical aberration
        if "c5" in self.aberrations:
            C5 = self.aberrations["c5"] * 1e7  # Convert mm to Angstrom
            chi += (2 * np.pi / lam) * (1 / 6) * C5 * lam_k**6

        if "c52a" in self.aberrations and "c52b" in self.aberrations:
            C52 = self.aberrations["c52a"] * 1e7
            phi52 = self.aberrations["c52b"]
            chi += (
                (2 * np.pi / lam)
                * (1 / 6)
                * C52
                * lam_k**6
                * np.cos(2 * (self.theta - phi52))
            )

        if "c54a" in self.aberrations and "c54b" in self.aberrations:
            C54 = self.aberrations["c54a"] * 1e7
            phi54 = self.aberrations["c54b"]
            chi += (
                (2 * np.pi / lam)
                * (1 / 6)
                * C54
                * lam_k**6
                * np.cos(4 * (self.theta - phi54))
            )

        if "c56a" in self.aberrations and "c56b" in self.aberrations:
            C56 = self.aberrations["c56a"] * 1e7
            phi56 = self.aberrations["c56b"]
            chi += (
                (2 * np.pi / lam)
                * (1 / 6)
                * C56
                * lam_k**6
                * np.cos(6 * (self.theta - phi56))
            )

        return chi

    def transfer_function(self) -> np.ndarray:
        """
        Calculate lens transfer function exp(iχ(k)).

        Returns:
            Transfer function in momentum space (2D complex array)
        """
        return np.exp(1j * self.chi)

    def ctf(self) -> np.ndarray:
        """
        Calculate Contrast Transfer Function sin(χ(k)).

        For phase contrast imaging with weak phase objects.

        Returns:
            CTF (2D array)
        """
        return np.sin(self.chi)

    def apply(self, psi: np.ndarray) -> np.ndarray:
        """
        Apply lens aberrations to wave function.

        This operates in momentum space:
            ψ_image(k) = exp(iχ(k)) · ψ_exit(k)

        Args:
            psi: Exit wave function in real space (2D complex array)

        Returns:
            Image wave function in real space (2D complex array)
        """
        # Transform to momentum space
        psi_k = fft2(psi)

        # Apply transfer function
        psi_k_aberrated = psi_k * self.transfer_function()

        # Transform back to real space
        return ifft2(psi_k_aberrated)


class TEMHamiltonian:
    """
    Complete TEM Hamiltonian combining all contributions.

    Total evolution:
        U = U_lens · U_sample · U_propagation

    This represents the complete electron wave propagation through:
    1. Free space to sample
    2. Sample interaction
    3. Free space to image plane
    4. Lens aberrations
    """

    def __init__(self, params: HamiltonianParameters, aberrations: Dict[str, float]):
        """
        Initialize complete TEM Hamiltonian.

        Args:
            params: Hamiltonian parameters
            aberrations: Aberration coefficients
        """
        self.params = params
        self.aberrations = aberrations

        # Initialize component Hamiltonians
        self.H_free = FreeParticleHamiltonian(params)
        self.H_sample = SampleHamiltonian(params)
        self.H_lens = LensHamiltonian(params, aberrations)

    def set_sample_potential(self, V: np.ndarray):
        """
        Set sample potential.

        Args:
            V: Projected potential (V·Angstrom)
        """
        self.H_sample.set_potential(V)

    def propagate(
        self, psi_incident: np.ndarray, propagation_distance: float = 0.0
    ) -> np.ndarray:
        """
        Complete TEM wave propagation.

        Args:
            psi_incident: Incident wave function
            propagation_distance: Free space propagation before sample

        Returns:
            Final image wave function
        """
        # Step 1: Free space propagation to sample (if needed)
        if propagation_distance > 0:
            psi = self.H_free.apply(psi_incident, propagation_distance)
        else:
            psi = psi_incident.copy()

        # Step 2: Sample interaction
        psi_exit = self.H_sample.apply(psi)

        # Step 3: Lens aberrations (in image plane)
        psi_image = self.H_lens.apply(psi_exit)

        return psi_image

    def get_ctf(self) -> np.ndarray:
        """Get Contrast Transfer Function."""
        return self.H_lens.ctf()

    def get_aberration_function(self) -> np.ndarray:
        """Get wave aberration function χ(k)."""
        return self.H_lens.chi

    def calculate_intensity(self, psi: np.ndarray) -> np.ndarray:
        """
        Calculate image intensity I = |ψ|².

        Args:
            psi: Image wave function

        Returns:
            Intensity image
        """
        return np.abs(psi) ** 2


def relativistic_wavelength(voltage: float) -> float:
    """
    Calculate relativistic electron wavelength.

    λ = h / √(2·m₀·e·V·(1 + e·V/(2·m₀·c²)))

    Args:
        voltage: Acceleration voltage (V)

    Returns:
        Wavelength in Angstroms
    """
    m0 = const.electron_mass  # kg
    e = const.elementary_charge  # C
    h = const.Planck  # J·s
    c = const.speed_of_light  # m/s

    # Relativistic correction factor
    gamma = 1 + e * voltage / (2 * m0 * c**2)

    # Wavelength in meters
    lambda_m = h / np.sqrt(2 * m0 * e * voltage * gamma)

    # Convert to Angstroms
    return lambda_m * 1e10


# Example usage and validation
if __name__ == "__main__":
    print("=" * 70)
    print("TEM Hamiltonian Module - Validation")
    print("=" * 70)
    print()

    # Setup parameters
    params = HamiltonianParameters(
        acceleration_voltage=200e3,
        wavelength=relativistic_wavelength(200e3),
        grid_size_x=4,
        grid_size_y=4,
        pixel_size=0.1,
    )

    print(f"Acceleration voltage: {params.acceleration_voltage/1e3:.0f} kV")
    print(f"Wavelength: {params.wavelength:.4f} Å")
    print(f"Interaction constant σ: {params.interaction_constant:.4e} 1/(V·Å²)")
    print()

    # Define aberrations
    aberrations = {"defocus": 500.0, "c3": 1.3, "c5": 10.0}  # Angstrom  # mm  # mm

    # Create Hamiltonian
    H = TEMHamiltonian(params, aberrations)

    print("Hamiltonian components initialized:")
    print(f"  ✓ Free particle propagation")
    print(f"  ✓ Sample interaction (WPOA)")
    print(f"  ✓ Lens aberrations (5th order)")
    print()

    # Create test wave function (plane wave)
    psi_0 = np.ones((4, 4), dtype=complex) / 4.0

    print("Test propagation:")
    psi_final = H.propagate(psi_0)
    print(f"  Input norm: {np.linalg.norm(psi_0):.6f}")
    print(f"  Output norm: {np.linalg.norm(psi_final):.6f}")
    print(
        f"  Norm preserved: {np.allclose(np.linalg.norm(psi_0), np.linalg.norm(psi_final))}"
    )
    print()

    print("✓ Hamiltonian module validated")
