"""
Multislice CTEM Simulator - Classical Implementation

This module implements the multislice algorithm for thick specimen CTEM simulation
following Kirkland's "Advanced Computing in Electron Microscopy" 2nd Edition, Chapter 7.

The multislice method divides the specimen into thin slices and alternately applies:
1. Transmission function: t_n(x,y) = exp(iσV_n(x,y))
2. Propagation function: P(k) = exp(-iπλk²Δz)

This is the classical implementation using standard FFT (not quantum QFT).

References:
    Kirkland, E.J. (2010). Advanced Computing in Electron Microscopy (2nd ed.).
    Springer. Chapter 7: Multislice.
    - Figure 7.2: Magnitude of wave function at different thicknesses
    - Figure 7.3: Intensity and phase vs thickness curves
    - Figure 7.4: BF phase contrast images
    - Table 7.2: Mean intensity validation values
"""

from typing import Dict, List, Optional, Tuple

import numpy as np

from ..utils.constants import PhysicalConstants
from .atomic_potential import AtomicPotential


class MultisliceSimulator:
    """
    Classical multislice CTEM simulator for thick specimens.

    The multislice algorithm simulates electron scattering through thick specimens
    by alternating between transmission (phase grating approximation) and
    propagation (Fresnel diffraction) through thin slices.

    Attributes:
        image_size (float): Real-space image size in Angstroms
        pixels (int): Number of pixels (must be power of 2)
        beam_energy (float): Electron beam energy in eV
        slice_thickness (float): Thickness of each slice in Angstroms
        wavelength (float): Relativistic electron wavelength (Å)
        sigma (float): Interaction parameter σ (rad/(eV·Å))
        dx (float): Pixel size in real space (Å)

    Example:
        >>> sim = MultisliceSimulator(
        ...     image_size=40.0,
        ...     pixels=256,
        ...     beam_energy=200e3,
        ...     slice_thickness=2.0
        ... )
        >>> results = sim.simulate_thickness_series(
        ...     atoms,
        ...     thicknesses=[40, 80, 200],
        ...     defocus=0
        ... )
    """

    def __init__(
        self,
        image_size: float,
        pixels: int,
        beam_energy: float,
        slice_thickness: float = 2.0,
        parametrization: str = "kirkland",
    ):
        """
        Initialize multislice simulator.

        Parameters:
            image_size: Real-space image size in Angstroms
            pixels: Number of pixels (must be power of 2 for efficient FFT)
            beam_energy: Electron beam energy in eV (e.g., 200e3 for 200 keV)
            slice_thickness: Thickness of each slice in Angstroms (default: 2.0)
            parametrization: Atomic potential parametrization from abTEM, "kirkland" or "lobato"

        Raises:
            ValueError: If pixels is not a power of 2
            ValueError: If the parametrization is unknown
        """
        # Check power of 2
        if pixels & (pixels - 1) != 0:
            raise ValueError(f"pixels must be power of 2, got {pixels}")

        self.image_size = image_size
        self.pixels = pixels
        self.beam_energy = beam_energy
        self.slice_thickness = slice_thickness

        # Physical constants
        self.m0c2 = 511.0e3  # Electron rest mass energy in eV

        # Calculate wavelength and interaction parameter
        self.wavelength = self._calculate_wavelength()
        self.sigma = self._calculate_sigma()

        # Real-space grid
        self.dx = self.image_size / self.pixels
        x = np.linspace(0, self.image_size, self.pixels, endpoint=False)
        self.x = x - self.image_size / 2  # Center at origin
        self.X, self.Y = np.meshgrid(self.x, self.x, indexing="xy")

        # Reciprocal-space grid
        kx = np.fft.fftfreq(self.pixels, d=self.dx)
        self.kx = np.fft.fftshift(kx)
        self.KX, self.KY = np.meshgrid(self.kx, self.kx, indexing="xy")
        self.k_squared = self.KX**2 + self.KY**2

        # Projected atomic potentials from abTEM
        self.potential_calculator = AtomicPotential(parametrization)

    def _calculate_wavelength(self) -> float:
        """
        Calculate relativistic electron wavelength using Kirkland Eq. 5.2.

        λ = 12.2639 / √(V + 0.97845×10⁻⁶ V²)

        where V is the beam energy in volts.

        Returns:
            Wavelength in Angstroms
        """
        V = self.beam_energy
        wavelength = 12.2639 / np.sqrt(V + 0.97845e-6 * V**2)
        return wavelength

    def _calculate_sigma(self) -> float:
        """
        Interaction parameter sigma = 2 pi gamma m0 e lambda / h^2 (Kirkland Eq. 5.6) in rad/(V*Angstrom).

        Applied to the projected potential in V*Angstrom; 7.29e-4 rad/(V*Angstrom) at 200 keV.
        """
        return PhysicalConstants.calculate_sigma(self.beam_energy)

    def kirkland_potential_2d(
        self,
        x_grid: np.ndarray,
        y_grid: np.ndarray,
        atom_x: float,
        atom_y: float,
        Z: int,
    ) -> np.ndarray:
        """
        Projected atomic potential of one atom on a grid, in V*Angstrom.

        Delegates to abTEM's parametrization chosen at construction (the method name is kept for
        compatibility; the parametrization can also be "lobato").
        """
        return self.potential_calculator.calculate_2d(x_grid, y_grid, atom_x, atom_y, Z)

    def get_atoms_in_slice(
        self, atoms: List[Dict], z_min: float, z_max: float
    ) -> List[Dict]:
        """
        Get atoms within a z-range [z_min, z_max).

        Parameters:
            atoms: List of atom dictionaries with keys:
                   - 'position': [x, y, z] in Angstroms
                   - 'Z': Atomic number
                   - 'element': Element symbol (optional)
            z_min: Minimum z coordinate (Å)
            z_max: Maximum z coordinate (Å)

        Returns:
            List of atoms within the z-range
        """
        atoms_in_slice = []

        for atom in atoms:
            x, y, z = atom["position"]

            # Check if atom is in this slice
            if z_min <= z < z_max:
                # Wrap coordinates with periodic boundary conditions
                x_wrapped = x % self.image_size
                y_wrapped = y % self.image_size

                # Center in image
                x_centered = x_wrapped - self.image_size / 2
                y_centered = y_wrapped - self.image_size / 2

                atoms_in_slice.append(
                    {
                        "position": [x_centered, y_centered, z],
                        "Z": atom["Z"],
                        "element": atom.get("element", ""),
                    }
                )

        return atoms_in_slice

    def calculate_slice_transmission(
        self, atoms_in_slice: List[Dict], slice_thickness: float
    ) -> np.ndarray:
        """
        Calculate transmission function for a slice.

        t_n(x,y) = exp(iσ v_n(x,y))

        where v_n is the projected potential of the atoms in slice n [V*Angstrom]. The atomic
        potentials are already integrated along z, so there is no extra factor of the slice thickness.

        Parameters:
            atoms_in_slice: List of atoms in this slice
            slice_thickness: Thickness of slice in Angstroms

        Returns:
            Complex transmission function array
        """
        V_slice = np.zeros((self.pixels, self.pixels))

        for atom in atoms_in_slice:
            x, y, z = atom["position"]
            Z = atom["Z"]

            # Add potential from this atom
            V_atom = self.kirkland_potential_2d(self.X, self.Y, x, y, Z)
            V_slice += V_atom

            # Add periodic images if atom is near boundary
            # This ensures continuity at edges
            if abs(x) > self.image_size / 2 - 5:  # Near x boundary
                x_periodic = x - np.sign(x) * self.image_size
                V_atom = self.kirkland_potential_2d(self.X, self.Y, x_periodic, y, Z)
                V_slice += V_atom

            if abs(y) > self.image_size / 2 - 5:  # Near y boundary
                y_periodic = y - np.sign(y) * self.image_size
                V_atom = self.kirkland_potential_2d(self.X, self.Y, x, y_periodic, Z)
                V_slice += V_atom

        # Transmission function: phase is proportional to V·Δz
        phase = self.sigma * V_slice
        transmission = np.exp(1j * phase)

        return transmission

    def calculate_propagator(self, dz: float) -> np.ndarray:
        """
        Calculate Fresnel free-space propagator.

        P(k) = exp(-iπλk²Δz)

        where k² = k_x² + k_y² is the squared spatial frequency.

        Parameters:
            dz: Propagation distance (slice thickness) in Angstroms

        Returns:
            Complex propagator array in reciprocal space

        References:
            Kirkland Eq. 7.2: Fresnel propagation
        """
        phase = -np.pi * self.wavelength * self.k_squared * dz
        propagator = np.exp(1j * phase)
        return propagator

    def simulate_thickness(
        self, atoms: List[Dict], thickness: float, defocus: float = 0, Cs: float = 0
    ) -> Dict[str, np.ndarray]:
        """
        Simulate CTEM image for a single specimen thickness.

        Algorithm:
        1. Initialize ψ = 1 (plane wave)
        2. For each slice:
           a. Apply transmission: ψ → t_n(x,y) × ψ
           b. FFT: ψ → ψ_k
           c. Apply propagator: ψ_k → P(k) × ψ_k
           d. IFFT: ψ_k → ψ
        3. Apply CTF (objective lens aberrations)
        4. Calculate intensity: I = |ψ|²

        Parameters:
            atoms: List of atom dictionaries
            thickness: Total specimen thickness in Angstroms
            defocus: Defocus value in Angstroms (default: 0)
            Cs: Spherical aberration coefficient in Angstroms (default: 0)

        Returns:
            Dictionary with keys:
                - 'intensity_image': 2D intensity array
                - 'exit_wave': Complex exit wave function
                - 'mean_intensity': Mean intensity value
                - 'n_slices': Number of slices used
        """
        # Calculate number of slices
        n_slices = max(1, int(np.ceil(thickness / self.slice_thickness)))
        actual_slice_thickness = thickness / n_slices

        # Initialize incident wave (plane wave)
        psi = np.ones((self.pixels, self.pixels), dtype=complex)

        # Calculate propagator for this slice thickness
        propagator = self.calculate_propagator(actual_slice_thickness)

        # Propagate through slices
        for i in range(n_slices):
            z_start = i * actual_slice_thickness
            z_end = (i + 1) * actual_slice_thickness

            # Get atoms in this slice
            atoms_in_slice = self.get_atoms_in_slice(atoms, z_start, z_end)

            # Apply transmission function
            transmission = self.calculate_slice_transmission(
                atoms_in_slice, actual_slice_thickness
            )
            psi *= transmission

            # Propagate to next slice (except for last slice)
            if i < n_slices - 1:
                # FFT to reciprocal space
                psi_k = np.fft.fft2(psi)
                psi_k = np.fft.fftshift(psi_k)

                # Apply propagator
                psi_k *= propagator

                # IFFT back to real space
                psi_k = np.fft.ifftshift(psi_k)
                psi = np.fft.ifft2(psi_k)

        # Apply objective lens transfer function (CTF)
        if defocus != 0 or Cs != 0:
            psi_k = np.fft.fft2(psi)
            psi_k = np.fft.fftshift(psi_k)

            # Aberration function χ(k)
            # χ = π λ k² Δf + π/2 Cs λ³ k⁴
            chi = -np.pi * self.wavelength * self.k_squared * defocus
            if Cs != 0:
                chi += 0.5 * np.pi * Cs * self.wavelength**3 * self.k_squared**2

            # Apply CTF: exp(iχ)
            psi_k *= np.exp(1j * chi)

            psi_k = np.fft.ifftshift(psi_k)
            psi = np.fft.ifft2(psi_k)

        # Calculate intensity
        intensity = np.abs(psi) ** 2

        return {
            "intensity_image": intensity,
            "exit_wave": psi,
            "mean_intensity": np.mean(intensity),
            "n_slices": n_slices,
        }

    def simulate_thickness_series(
        self,
        atoms: List[Dict],
        thicknesses: List[float],
        defocus: float = 0,
        Cs: float = 0,
        verbose: bool = True,
    ) -> Dict[float, Dict[str, np.ndarray]]:
        """
        Simulate CTEM images for multiple specimen thicknesses.

        This is useful for generating thickness series plots like Kirkland
        Figures 7.2-7.4 and validating against Table 7.2.

        Parameters:
            atoms: List of atom dictionaries
            thicknesses: List of thickness values in Angstroms
            defocus: Defocus value in Angstroms (default: 0)
            Cs: Spherical aberration coefficient in Angstroms (default: 0)
            verbose: Print progress messages (default: True)

        Returns:
            Dictionary mapping thickness → simulation results

        Example:
            >>> results = sim.simulate_thickness_series(
            ...     atoms,
            ...     thicknesses=[40, 80, 128, 200, 256, 400, 512],
            ...     defocus=0
            ... )
            >>> for t, res in results.items():
            ...     print(f"{t:.1f} Å: I_mean = {res['mean_intensity']:.3f}")
        """
        results = {}

        for thickness in thicknesses:
            if verbose:
                print(f"Simulating thickness: {thickness:.1f} Å")

            result = self.simulate_thickness(atoms, thickness, defocus, Cs)
            results[thickness] = result

        return results
