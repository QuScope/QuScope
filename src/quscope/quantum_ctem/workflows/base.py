"""
Base Workflow Classes for Quantum CTEM Simulation.

Provides the abstract workflow template that all material-specific
workflows inherit from, ensuring consistent interfaces and behavior.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from ..backends.base import Backend, BackendConfig, ExecutionResult
from ..materials.base import Material


@dataclass
class MicroscopeConfig:
    """
    CTEM microscope configuration parameters.

    Based on typical parameters for modern 200-300 kV instruments.

    Attributes:
        voltage: Accelerating voltage in Volts
        defocus: Defocus value in Ångströms (positive = underfocus)
        cs: Spherical aberration coefficient in mm
        aperture: Objective aperture semi-angle in mrad
        convergence: Beam convergence semi-angle in mrad
        energy_spread: Energy spread in eV (for partial coherence)
    """

    voltage: float = 200e3  # 200 kV
    defocus: float = -500.0  # -50 nm underfocus (Scherzer-like)
    cs: float = 1.3  # mm, typical uncorrected
    c5: float = 0.0  # mm, 5th order
    aperture: float = 10.0  # mrad
    convergence: float = 0.5  # mrad
    energy_spread: float = 0.7  # eV

    @property
    def wavelength(self) -> float:
        """Calculate relativistic electron wavelength in Ångströms."""
        m0 = 9.10938e-31
        e = 1.60218e-19
        h = 6.62607e-34
        c = 2.99792e8

        E = self.voltage * e
        E0 = m0 * c**2
        wavelength = h / np.sqrt(2 * m0 * E * (1 + E / (2 * E0)))
        return wavelength * 1e10  # Convert to Å

    @property
    def scherzer_defocus(self) -> float:
        """Calculate Scherzer defocus for optimal phase contrast."""
        lambda_A = self.wavelength
        Cs_A = self.cs * 1e7  # Convert mm to Å
        return -1.2 * np.sqrt(Cs_A * lambda_A)

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "voltage": self.voltage,
            "defocus": self.defocus,
            "cs": self.cs,
            "c5": self.c5,
            "aperture": self.aperture,
            "convergence": self.convergence,
            "energy_spread": self.energy_spread,
            "wavelength": self.wavelength,
        }


@dataclass
class SimulationResult:
    """
    Complete result from a quantum CTEM simulation.

    Contains the wavefunction, image intensity, and all metadata
    needed for analysis and visualization.
    """

    # Structure info
    material_name: str = ""
    n_atoms: int = 0
    supercell_size: Tuple[int, int] = (0, 0)

    # Grid parameters
    grid_size: int = 0
    pixel_size: float = 0.0
    field_of_view: Tuple[float, float] = (0.0, 0.0)  # Å

    # Quantum results
    wavefunction: Optional[np.ndarray] = None  # Complex 2D
    intensity: Optional[np.ndarray] = None  # |ψ|² 2D
    phase: Optional[np.ndarray] = None  # arg(ψ) 2D

    # Potentials
    projected_potential: Optional[np.ndarray] = None  # V(x,y)
    transmission_function: Optional[np.ndarray] = None  # t(x,y)

    # Microscope
    microscope_config: Optional[MicroscopeConfig] = None

    # Backend execution
    backend_result: Optional[ExecutionResult] = None
    execution_time: float = 0.0
    circuit_depth: int = 0
    n_qubits: int = 0

    # Classical comparison (if available)
    classical_intensity: Optional[np.ndarray] = None
    correlation_coefficient: Optional[float] = None

    def get_contrast(self) -> Optional[np.ndarray]:
        """Calculate image contrast: (I - mean) / mean."""
        if self.intensity is None:
            return None
        mean_I = np.mean(self.intensity)
        if mean_I == 0:
            return np.zeros_like(self.intensity)
        return (self.intensity - mean_I) / mean_I

    def summary(self) -> str:
        """Generate text summary of results."""
        lines = [
            f"=== Quantum CTEM Simulation Result ===",
            f"Material: {self.material_name}",
            f"Supercell: {self.supercell_size[0]}×{self.supercell_size[1]} ({self.n_atoms} atoms)",
            f"Grid: {self.grid_size}×{self.grid_size} px ({self.pixel_size:.3f} Å/px)",
            f"Field of view: {self.field_of_view[0]:.1f}×{self.field_of_view[1]:.1f} Å",
            f"",
            f"Quantum Circuit:",
            f"  Qubits: {self.n_qubits}",
            f"  Depth: {self.circuit_depth}",
            f"  Execution time: {self.execution_time:.3f} s",
        ]

        if self.microscope_config:
            lines.extend([
                f"",
                f"Microscope:",
                f"  Voltage: {self.microscope_config.voltage/1e3:.0f} kV",
                f"  Defocus: {self.microscope_config.defocus:.1f} Å",
                f"  Cs: {self.microscope_config.cs:.1f} mm",
            ])

        if self.correlation_coefficient is not None:
            lines.extend([
                f"",
                f"Validation:",
                f"  Correlation with classical: {self.correlation_coefficient:.4f}",
            ])

        return "\n".join(lines)


class CTEMWorkflow(ABC):
    """
    Abstract base class for quantum CTEM simulation workflows.

    Provides the template method pattern for running CTEM simulations.
    Subclasses implement material-specific structure building and visualization.

    Attributes:
        material: Material instance for the simulation
        backend: Quantum backend (simulator or IBM hardware)
        microscope: Microscope configuration
    """

    def __init__(
        self,
        material: Material,
        backend: Backend,
        microscope: Optional[MicroscopeConfig] = None,
        **kwargs,
    ):
        """
        Initialize workflow.

        Args:
            material: Material instance
            backend: Quantum backend
            microscope: Microscope config (uses defaults if None)
            **kwargs: Additional configuration
        """
        self.material = material
        self.backend = backend
        self.microscope = microscope or MicroscopeConfig()

        # Connect backend if not already connected
        if not backend.is_connected:
            backend.connect()

    @abstractmethod
    def build_structure(self, **kwargs):
        """Build atomic structure for simulation."""
        pass

    def setup_quantum_state(
        self,
        atoms,
        grid_size: int = 64,
        pixel_size: float = 0.1,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Setup quantum state from atomic structure.

        Args:
            atoms: ASE Atoms object
            grid_size: Number of grid points per dimension
            pixel_size: Pixel size in Å

        Returns:
            Tuple of (projected_potential, transmission_function)
        """
        # Get projected potential
        V_proj = self.material.get_projected_potential(
            atoms, grid_size=grid_size, pixel_size=pixel_size
        )

        # Calculate transmission function under WPOA
        sigma = self.material.get_interaction_constant(self.microscope.voltage)
        t = np.exp(1j * sigma * V_proj)

        return V_proj, t

    def build_quantum_circuit(
        self,
        transmission_function: np.ndarray,
        apply_ctf: bool = True,
    ):
        """
        Build quantum circuit for CTEM simulation.

        The quantum circuit encodes the exit wave function, which is the
        product of the incident plane wave and the transmission function.
        For WPOA with unit incident wave: exit_wave ≈ transmission_function

        If CTF is applied, it modifies the wave in momentum space.

        Args:
            transmission_function: Complex 2D transmission function
            apply_ctf: Whether to apply contrast transfer function

        Returns:
            Qiskit QuantumCircuit
        """
        from ..quantum_wave_function import QuantumWaveFunction

        ny, nx = transmission_function.shape
        n_qubits_x = int(np.ceil(np.log2(nx)))
        n_qubits_y = int(np.ceil(np.log2(ny)))

        # Pad to power of 2 if needed
        padded_nx = 2**n_qubits_x
        padded_ny = 2**n_qubits_y

        # Exit wave = incident wave * transmission function
        # For unit incident plane wave: exit_wave = transmission_function
        exit_wave = transmission_function.copy()

        # Pad if needed
        if exit_wave.shape != (padded_ny, padded_nx):
            padded_wave = np.ones((padded_ny, padded_nx), dtype=complex)
            padded_wave[:ny, :nx] = exit_wave
            exit_wave = padded_wave

        # Apply CTF if requested (in momentum space)
        if apply_ctf:
            exit_wave = self._apply_ctf_classical(exit_wave)

        # Initialize quantum wave function encoder
        qwf = QuantumWaveFunction(n_qubits_x, n_qubits_y)

        # Encode exit wave as quantum state using amplitude encoding
        circuit = qwf.prepare_arbitrary_wave(exit_wave)

        # Store the QWF for later extraction
        self._last_qwf = qwf

        return circuit

    def _apply_ctf_classical(self, wave: np.ndarray) -> np.ndarray:
        """
        Apply Contrast Transfer Function in momentum space.

        CTF operation: wave_ctf = IFFT(CTF * FFT(wave))

        Args:
            wave: Complex wave function in real space

        Returns:
            Wave function after CTF application
        """
        ny, nx = wave.shape

        # Transform to momentum space
        wave_k = np.fft.fft2(wave)
        wave_k = np.fft.fftshift(wave_k)

        # Compute CTF
        ctf = self._compute_ctf(nx, ny)

        # Apply CTF
        wave_k_ctf = wave_k * ctf

        # Transform back to real space
        wave_k_ctf = np.fft.ifftshift(wave_k_ctf)
        wave_ctf = np.fft.ifft2(wave_k_ctf)

        return wave_ctf

    def _compute_ctf(self, nx: int, ny: int) -> np.ndarray:
        """
        Compute the Contrast Transfer Function.

        CTF(k) = sin(χ(k)) for phase contrast
        χ(k) = π λ Δf k² + 0.5 π λ³ Cs k⁴

        Args:
            nx, ny: Grid dimensions

        Returns:
            2D CTF array
        """
        # Create frequency grid (centered)
        kx = np.fft.fftfreq(nx)
        ky = np.fft.fftfreq(ny)
        KX, KY = np.meshgrid(kx, ky)
        KX = np.fft.fftshift(KX)
        KY = np.fft.fftshift(KY)
        K2 = KX**2 + KY**2

        # Microscope parameters
        lambda_e = self.microscope.wavelength  # Å
        df = self.microscope.defocus  # Å
        Cs = self.microscope.cs * 1e7  # mm to Å

        # CTF phase aberration function
        chi = np.pi * lambda_e * df * K2 + 0.5 * np.pi * lambda_e**3 * Cs * K2**2

        # CTF = sin(χ) for phase contrast
        ctf = np.sin(chi)

        return ctf

    def run(
        self,
        grid_size: int = 64,
        pixel_size: float = 0.1,
        shots: int = 0,
        apply_ctf: bool = True,
        compare_classical: bool = False,
        **structure_kwargs,
    ) -> SimulationResult:
        """
        Run complete quantum CTEM simulation.

        Args:
            grid_size: Number of grid points per dimension (must be power of 2)
            pixel_size: Pixel size in Ångströms
            shots: Number of measurement shots (0 for statevector only)
            apply_ctf: Whether to apply contrast transfer function
            compare_classical: Whether to run classical comparison
            **structure_kwargs: Arguments passed to build_structure()

        Returns:
            SimulationResult with all simulation data
        """
        import time

        # Validate grid size
        if grid_size & (grid_size - 1) != 0:
            raise ValueError(f"grid_size must be power of 2, got {grid_size}")

        start_time = time.time()

        # 1. Build structure
        atoms = self.build_structure(**structure_kwargs)
        self.material.validate_structure(atoms)

        # 2. Setup quantum state
        V_proj, transmission = self.setup_quantum_state(
            atoms, grid_size=grid_size, pixel_size=pixel_size
        )

        # 3. Build quantum circuit
        circuit = self.build_quantum_circuit(transmission, apply_ctf=apply_ctf)

        # 4. Execute on backend
        config = BackendConfig(shots=shots)
        backend_result = self.backend.run(circuit, config)

        # 5. Extract wavefunction
        if backend_result.statevector is not None:
            wavefunction = backend_result.get_statevector_2d(grid_size, grid_size)
            intensity = np.abs(wavefunction) ** 2
            phase = np.angle(wavefunction)
        else:
            wavefunction = None
            intensity = None
            phase = None

        # 6. Classical comparison if requested
        classical_intensity = None
        correlation = None
        if compare_classical and intensity is not None:
            classical_intensity = self._run_classical(atoms, grid_size, pixel_size)
            if classical_intensity is not None:
                correlation = np.corrcoef(
                    intensity.flatten(), classical_intensity.flatten()
                )[0, 1]

        # Build result
        cell = atoms.get_cell()
        fov = (cell[0, 0], cell[1, 1])

        result = SimulationResult(
            material_name=self.material.name,
            n_atoms=len(atoms),
            supercell_size=(structure_kwargs.get("nx", 1), structure_kwargs.get("ny", 1)),
            grid_size=grid_size,
            pixel_size=pixel_size,
            field_of_view=fov,
            wavefunction=wavefunction,
            intensity=intensity,
            phase=phase,
            projected_potential=V_proj,
            transmission_function=transmission,
            microscope_config=self.microscope,
            backend_result=backend_result,
            execution_time=time.time() - start_time,
            circuit_depth=circuit.depth(),
            n_qubits=circuit.num_qubits,
            classical_intensity=classical_intensity,
            correlation_coefficient=correlation,
        )

        return result

    def _run_classical(
        self,
        atoms,
        grid_size: int,
        pixel_size: float,
    ) -> Optional[np.ndarray]:
        """Run classical WPOA simulation for comparison."""
        try:
            from ..classical_integration import WPOAQuantumInterface

            interface = WPOAQuantumInterface(
                voltage=self.microscope.voltage,
                defocus=self.microscope.defocus,
                cs=self.microscope.cs,
            )
            return interface.simulate(atoms, grid_size, pixel_size)
        except Exception:
            return None

    def run_defocus_series(
        self,
        defocus_values: List[float],
        grid_size: int = 64,
        pixel_size: float = 0.1,
        **structure_kwargs,
    ) -> List[SimulationResult]:
        """
        Run simulation at multiple defocus values.

        Args:
            defocus_values: List of defocus values in Å
            grid_size: Grid size
            pixel_size: Pixel size in Å
            **structure_kwargs: Structure parameters

        Returns:
            List of SimulationResult for each defocus
        """
        results = []
        original_defocus = self.microscope.defocus

        for df in defocus_values:
            self.microscope.defocus = df
            result = self.run(
                grid_size=grid_size,
                pixel_size=pixel_size,
                **structure_kwargs,
            )
            results.append(result)

        # Restore original
        self.microscope.defocus = original_defocus
        return results

    @abstractmethod
    def visualize(self, result: SimulationResult, **kwargs):
        """Create visualization of simulation results."""
        pass
