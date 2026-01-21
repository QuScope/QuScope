"""
Quantum TEM Simulation Integration Module

Bridges the quantum Hamiltonian framework with classical validation,
enabling direct comparison between quantum circuit and classical multislice approaches.

This module provides a high-level interface for running quantum TEM simulations
that can be validated against abTEM classical simulations.

Author: QuScope Team
Date: October 2025
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np

try:
    from ase import Atoms
except ImportError:
    raise ImportError("ASE is required. Install with: conda install -c conda-forge ase")

# Import our quantum modules
try:
    # Try relative imports (when used as package)
    from .hamiltonian import (
        FreeParticleHamiltonian,
        HamiltonianParameters,
        LensHamiltonian,
        SampleHamiltonian,
        TEMHamiltonian,
    )
    from .sample_potential_converter import SamplePotentialConverter
except ImportError:
    # Fall back to absolute imports (when run directly)
    from hamiltonian import (
        FreeParticleHamiltonian,
        HamiltonianParameters,
        LensHamiltonian,
        SampleHamiltonian,
        TEMHamiltonian,
    )
    from sample_potential_converter import SamplePotentialConverter


@dataclass
class QuantumSimulationParameters:
    """Parameters for quantum TEM simulation."""

    # Microscope parameters
    acceleration_voltage: float  # Volts

    # Grid parameters
    grid_size: int  # N for N×N grid
    pixel_size: float  # Angstroms

    # Aberrations (in consistent units)
    defocus: float  # Angstroms (C1)
    cs: float = 0.0  # mm (C3 - spherical aberration)
    c5: float = 0.0  # mm (5th order spherical)

    # 2nd order aberrations
    c12a: float = 0.0  # Angstroms (2-fold astigmatism)
    c12b: float = 0.0

    # 3rd order aberrations
    c21a: float = 0.0  # mm (coma)
    c21b: float = 0.0
    c23a: float = 0.0  # mm (3-fold astigmatism)
    c23b: float = 0.0

    # 4th order aberrations
    c32a: float = 0.0  # mm (star aberration)
    c32b: float = 0.0
    c34a: float = 0.0  # mm (4-fold astigmatism)
    c34b: float = 0.0

    # 5th order aberrations
    c41a: float = 0.0  # mm
    c41b: float = 0.0
    c43a: float = 0.0  # mm
    c43b: float = 0.0
    c45a: float = 0.0  # mm
    c45b: float = 0.0
    c52a: float = 0.0  # mm
    c52b: float = 0.0
    c54a: float = 0.0  # mm
    c54b: float = 0.0
    c56a: float = 0.0  # mm
    c56b: float = 0.0

    # Propagation parameters
    propagation_distance: float = 100.0  # Angstroms (sample to detector)

    def to_aberration_dict(self) -> Dict[str, float]:
        """Convert parameters to aberration dictionary for Hamiltonian.

        Returns:
            Dictionary with aberration coefficients in Angstroms
        """
        # Convert mm to Angstroms for higher-order aberrations
        mm_to_angstrom = 1e7

        return {
            "c1": self.defocus,
            "c12a": self.c12a,
            "c12b": self.c12b,
            "c21a": self.c21a * mm_to_angstrom,
            "c21b": self.c21b * mm_to_angstrom,
            "c23a": self.c23a * mm_to_angstrom,
            "c23b": self.c23b * mm_to_angstrom,
            "c3": self.cs * mm_to_angstrom,
            "c32a": self.c32a * mm_to_angstrom,
            "c32b": self.c32b * mm_to_angstrom,
            "c34a": self.c34a * mm_to_angstrom,
            "c34b": self.c34b * mm_to_angstrom,
            "c41a": self.c41a * mm_to_angstrom,
            "c41b": self.c41b * mm_to_angstrom,
            "c43a": self.c43a * mm_to_angstrom,
            "c43b": self.c43b * mm_to_angstrom,
            "c45a": self.c45a * mm_to_angstrom,
            "c45b": self.c45b * mm_to_angstrom,
            "c5": self.c5 * mm_to_angstrom,
            "c52a": self.c52a * mm_to_angstrom,
            "c52b": self.c52b * mm_to_angstrom,
            "c54a": self.c54a * mm_to_angstrom,
            "c54b": self.c54b * mm_to_angstrom,
            "c56a": self.c56a * mm_to_angstrom,
            "c56b": self.c56b * mm_to_angstrom,
        }


class QuantumTEMSimulator:
    """High-level interface for quantum TEM simulation."""

    def __init__(self, params: QuantumSimulationParameters):
        """Initialize quantum TEM simulator.

        Args:
            params: Simulation parameters
        """
        self.params = params

        # Initialize potential converter
        self.potential_converter = SamplePotentialConverter(
            acceleration_voltage=params.acceleration_voltage, use_scattering_params=True
        )

        # Calculate wavelength
        self.wavelength = self._calculate_wavelength()

        print(f"Quantum TEM Simulator initialized:")
        print(f"  Voltage: {params.acceleration_voltage/1e3:.0f} kV")
        print(f"  Wavelength: {self.wavelength:.5f} Å")
        print(f"  Grid: {params.grid_size}×{params.grid_size}")
        print(f"  Pixel size: {params.pixel_size:.3f} Å")

    def _calculate_wavelength(self) -> float:
        """Calculate relativistic electron wavelength.

        Returns:
            Wavelength in Angstroms
        """
        from scipy.constants import c, e, h, m_e

        V = self.params.acceleration_voltage
        wavelength = h / np.sqrt(2 * m_e * e * V * (1 + e * V / (2 * m_e * c**2)))

        return wavelength * 1e10  # Convert m to Angstroms

    def simulate(self, atoms: Atoms, verbose: bool = True) -> Tuple[np.ndarray, Dict]:
        """Run complete quantum TEM simulation.

        This performs the full quantum simulation workflow:
        1. Convert atomic structure to potential V(x,y)
        2. Create incident plane wave |ψ_in⟩
        3. Propagate through free space (sample to specimen)
        4. Apply sample interaction (WPOA transmission)
        5. Propagate through free space (specimen to lens)
        6. Apply lens aberrations (CTF)
        7. Propagate to detector
        8. Calculate intensity |ψ|²

        Args:
            atoms: ASE Atoms object (sample structure)
            verbose: Print progress information

        Returns:
            Tuple of (intensity_image, simulation_info)
        """
        info = {}

        # Step 1: Convert atoms to potential
        if verbose:
            print("\n[1/7] Converting atomic structure to potential...")

        V = self.potential_converter.atoms_to_potential(
            atoms, self.params.grid_size, self.params.pixel_size
        )

        info["potential_min"] = float(V.min())
        info["potential_max"] = float(V.max())
        info["potential_mean"] = float(V.mean())

        if verbose:
            print(f"  ✓ Potential calculated")
            print(f"    Range: [{V.min():.3e}, {V.max():.3e}] V")

        # Step 2: Create Hamiltonian parameters
        if verbose:
            print("\n[2/7] Setting up Hamiltonian parameters...")

        ham_params = HamiltonianParameters(
            acceleration_voltage=self.params.acceleration_voltage,
            wavelength=self.wavelength,
            grid_size_x=self.params.grid_size,
            grid_size_y=self.params.grid_size,
            pixel_size=self.params.pixel_size,
        )

        if verbose:
            print(f"  ✓ Parameters ready")

        # Step 3: Create incident plane wave
        if verbose:
            print("\n[3/7] Creating incident plane wave...")

        psi_incident = np.ones(
            (self.params.grid_size, self.params.grid_size), dtype=complex
        )

        # Normalize
        psi_incident = psi_incident / np.sqrt(np.sum(np.abs(psi_incident) ** 2))

        info["incident_norm"] = float(np.sum(np.abs(psi_incident) ** 2))

        if verbose:
            print(f"  ✓ Plane wave created")
            print(f"    Norm: {info['incident_norm']:.6f}")

        # Step 4: Use TEMHamiltonian for complete propagation
        if verbose:
            print("\n[4/7] Creating complete TEM Hamiltonian...")

        aberrations = self.params.to_aberration_dict()
        tem_ham = TEMHamiltonian(ham_params, aberrations)

        # Set the sample potential
        tem_ham.set_sample_potential(V)

        if verbose:
            print(f"  ✓ TEM Hamiltonian ready")
            print(f"    Defocus: {self.params.defocus:.1f} Å")
            print(f"    Cs: {self.params.cs:.2f} mm")

        # Step 5: Complete TEM propagation (sample + lens)
        if verbose:
            print("\n[5/7] Propagating through TEM system...")
            print("  - Free propagation to sample")
            print("  - Sample interaction (WPOA)")
            print("  - Lens aberrations (CTF)")

        psi_image = tem_ham.propagate(
            psi_incident, propagation_distance=10.0  # Small distance to sample
        )

        info["image_norm"] = float(np.sum(np.abs(psi_image) ** 2))

        if verbose:
            print(f"  ✓ Propagation complete")
            print(f"    Norm: {info['image_norm']:.6f}")

        # Step 6: Calculate intensity
        if verbose:
            print("\n[6/7] Calculating intensity...")

        intensity = tem_ham.calculate_intensity(psi_image)

        info["intensity_min"] = float(intensity.min())
        info["intensity_max"] = float(intensity.max())
        info["intensity_mean"] = float(intensity.mean())
        info["intensity_std"] = float(intensity.std())

        if verbose:
            print(f"  ✓ Intensity image calculated")
            print(f"    Final norm: {info['image_norm']:.6f}")
            print(
                f"    Intensity range: [{info['intensity_min']:.6f}, {info['intensity_max']:.6f}]"
            )
            print(f"    Mean intensity: {info['intensity_mean']:.6f}")

        return intensity, info

    def simulate_with_potential(
        self, V: np.ndarray, verbose: bool = True
    ) -> np.ndarray:
        """Run quantum TEM simulation with pre-calculated potential.

        This allows using an external potential (e.g., from abTEM) instead of
        calculating it from atoms. Useful for validating the quantum propagation
        method independently of the potential calculation.

        Args:
            V: 2D potential array in V·Å
            verbose: Print progress information

        Returns:
            intensity_image: 2D intensity array
        """
        if verbose:
            print("Running quantum simulation with provided potential...")
            print(f"  Potential: [{V.min():.2f}, {V.max():.2f}] V·Å")

        # Create Hamiltonian parameters
        ham_params = HamiltonianParameters(
            acceleration_voltage=self.params.acceleration_voltage,
            wavelength=self.wavelength,
            grid_size_x=self.params.grid_size,
            grid_size_y=self.params.grid_size,
            pixel_size=self.params.pixel_size,
        )

        # Create incident plane wave
        psi_incident = np.ones(
            (self.params.grid_size, self.params.grid_size), dtype=complex
        )
        psi_incident = psi_incident / np.sqrt(np.sum(np.abs(psi_incident) ** 2))

        # Create TEM Hamiltonian with aberrations
        aberrations = self.params.to_aberration_dict()
        tem_ham = TEMHamiltonian(ham_params, aberrations)

        # Set the provided potential
        tem_ham.set_sample_potential(V)

        # Propagate
        psi_image = tem_ham.propagate(psi_incident, propagation_distance=10.0)

        # Calculate intensity
        intensity = tem_ham.calculate_intensity(psi_image)

        if verbose:
            print(f"  ✓ Intensity: [{intensity.min():.6f}, {intensity.max():.6f}]")

        return intensity


def run_quantum_tem_simulation(
    atoms: Atoms,
    voltage: float,
    grid_size: int,
    pixel_size: float,
    defocus: float,
    cs: float = 0.0,
    c5: float = 0.0,
    verbose: bool = True,
    **additional_aberrations,
) -> np.ndarray:
    """Convenience function to run quantum TEM simulation.

    This is a simplified interface for the most common use case.
    For more control, use QuantumTEMSimulator directly.

    Args:
        atoms: ASE Atoms object (sample structure)
        voltage: Acceleration voltage in Volts
        grid_size: Grid size (N for N×N)
        pixel_size: Pixel size in Angstroms
        defocus: Defocus in Angstroms
        cs: Spherical aberration in mm
        c5: 5th order aberration in mm
        verbose: Print progress
        **additional_aberrations: Additional aberration coefficients

    Returns:
        2D intensity image

    Example:
        >>> from ase.build import graphene_nanoribbon
        >>> atoms = graphene_nanoribbon(6, 6, type='zigzag')
        >>> intensity = run_quantum_tem_simulation(
        ...     atoms,
        ...     voltage=200e3,
        ...     grid_size=256,
        ...     pixel_size=0.1,
        ...     defocus=-659.7,
        ...     cs=1.3
        ... )
    """
    # Create parameters
    params = QuantumSimulationParameters(
        acceleration_voltage=voltage,
        grid_size=grid_size,
        pixel_size=pixel_size,
        defocus=defocus,
        cs=cs,
        c5=c5,
        **additional_aberrations,
    )

    # Create simulator
    simulator = QuantumTEMSimulator(params)

    # Run simulation
    intensity, info = simulator.simulate(atoms, verbose=verbose)

    return intensity


def test_quantum_simulation():
    """Deprecated test function.

    The example quantum simulation test previously used graphene as a
    demonstration structure. Graphene-related examples were removed from
    core modules in order to focus the repository on the MoS2 workflow.

    Please use `quscope.mos2_workflow` and the notebook
    `src/notebooks/MoS2_showcase.ipynb` for canonical examples and visual
    outputs. If you need to run ad-hoc tests, construct ASE structures
    directly in a notebook and call `run_quantum_tem_simulation` or the
    `QuantumTEMSimulator` class.
    """
    raise RuntimeError(
        "test_quantum_simulation() has been removed. Use quscope.mos2_workflow "
        "and src/notebooks/MoS2_showcase.ipynb for canonical examples."
    )


if __name__ == "__main__":
    print("Quantum simulation module (examples removed).")
    print("Use quscope.mos2_workflow and the MoS2 notebook for example runs.")
