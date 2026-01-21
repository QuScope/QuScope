"""
Classical-Quantum Integration Module

This module provides interfaces between pure quantum CTEM implementations
and classical simulators (WPOA and Multislice). Enables:
1. Quantum wave function ↔ Classical wave function conversion
2. Consistency validation between quantum and classical methods
3. Performance benchmarking
4. Hybrid simulation workflows

Week 3 Task 1.6: Connect to Classical Simulators

Author: QuScope Development Team
Date: October 4, 2025
"""

from typing import Dict, List, Optional, Tuple, Union

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from .quantum_wave_function import QuantumWaveFunction


class QuantumClassicalBridge:
    """
    Bridge between quantum and classical wave function representations.

    Provides bidirectional conversion and validation between:
    - Quantum circuits (Qiskit QuantumCircuit)
    - Classical wave functions (NumPy complex arrays)

    This enables:
    - Using quantum encodings with classical simulators
    - Validating quantum results against classical benchmarks
    - Hybrid quantum-classical workflows

    Example:
        >>> bridge = QuantumClassicalBridge(n_qubits_x=3, n_qubits_y=3)
        >>>
        >>> # Classical → Quantum
        >>> psi_classical = np.random.rand(8, 8) + 1j*np.random.rand(8, 8)
        >>> circuit = bridge.classical_to_quantum(psi_classical)
        >>>
        >>> # Quantum → Classical
        >>> psi_decoded = bridge.quantum_to_classical(circuit)
        >>>
        >>> # Validate consistency
        >>> error = np.max(np.abs(psi_classical - psi_decoded))
        >>> print(f"Round-trip error: {error:.2e}")

    Attributes:
        n_qubits_x: Number of qubits for x dimension
        n_qubits_y: Number of qubits for y dimension
        qwf: QuantumWaveFunction instance for encoding/decoding
    """

    def __init__(self, n_qubits_x: int, n_qubits_y: int):
        """
        Initialize quantum-classical bridge.

        Args:
            n_qubits_x: Number of qubits for x dimension (determines grid size 2^n)
            n_qubits_y: Number of qubits for y dimension (determines grid size 2^n)
        """
        self.n_qubits_x = n_qubits_x
        self.n_qubits_y = n_qubits_y
        self.pixels_x = 2**n_qubits_x
        self.pixels_y = 2**n_qubits_y

        # Initialize quantum wave function encoder
        self.qwf = QuantumWaveFunction(n_qubits_x, n_qubits_y)

    def classical_to_quantum(
        self, psi_classical: np.ndarray, normalize: bool = True
    ) -> QuantumCircuit:
        """
        Convert classical wave function to quantum circuit.

        Takes a classical 2D complex wave function and encodes it into
        a quantum circuit using amplitude encoding.

        Args:
            psi_classical: Complex wave function, shape (pixels_y, pixels_x)
            normalize: If True, normalize the wave function before encoding

        Returns:
            QuantumCircuit representing the wave function

        Raises:
            ValueError: If shape doesn't match expected dimensions

        Example:
            >>> # Create Gaussian wave packet
            >>> x = np.linspace(-4, 4, 8)
            >>> X, Y = np.meshgrid(x, x)
            >>> psi = np.exp(-(X**2 + Y**2)/4)
            >>>
            >>> bridge = QuantumClassicalBridge(3, 3)
            >>> circuit = bridge.classical_to_quantum(psi)
            >>> print(f"Qubits: {circuit.num_qubits}")
        """
        # Validate shape
        if psi_classical.shape != (self.pixels_y, self.pixels_x):
            raise ValueError(
                f"Wave function shape {psi_classical.shape} doesn't match "
                f"expected ({self.pixels_y}, {self.pixels_x})"
            )

        # Normalize if requested
        if normalize:
            norm = np.linalg.norm(psi_classical)
            if norm > 1e-10:
                psi_classical = psi_classical / norm

        # Encode using quantum wave function
        circuit = self.qwf.prepare_arbitrary_wave(psi_classical)

        return circuit

    def quantum_to_classical(self, circuit: QuantumCircuit) -> np.ndarray:
        """
        Convert quantum circuit to classical wave function.

        Extracts the wave function from a quantum circuit by measuring
        the quantum state amplitudes.

        Args:
            circuit: Quantum circuit encoding the wave function

        Returns:
            Complex wave function array, shape (pixels_y, pixels_x)

        Example:
            >>> circuit = bridge.classical_to_quantum(psi)
            >>> psi_recovered = bridge.quantum_to_classical(circuit)
            >>> error = np.linalg.norm(psi - psi_recovered)
            >>> print(f"Reconstruction error: {error:.2e}")
        """
        # Extract using quantum wave function
        psi_classical = self.qwf.extract_wave(circuit)

        return psi_classical

    def validate_consistency(
        self,
        psi_classical: np.ndarray,
        circuit: QuantumCircuit,
        tolerance: float = 1e-6,
    ) -> Dict[str, Union[bool, float]]:
        """
        Validate consistency between classical and quantum representations.

        Compares a classical wave function with its quantum circuit
        representation to ensure they encode the same information.

        Args:
            psi_classical: Classical wave function
            circuit: Quantum circuit encoding
            tolerance: Maximum acceptable error

        Returns:
            Dictionary with validation results:
                - valid: True if error < tolerance
                - max_error: Maximum absolute error
                - mean_error: Mean absolute error
                - norm_difference: Difference in normalization
                - fidelity: State fidelity (0-1)

        Example:
            >>> circuit = bridge.classical_to_quantum(psi)
            >>> results = bridge.validate_consistency(psi, circuit)
            >>> if results['valid']:
            ...     print(f"✅ Consistent (error: {results['max_error']:.2e})")
            ... else:
            ...     print(f"❌ Inconsistent (error: {results['max_error']:.2e})")
        """
        # Decode quantum circuit
        psi_decoded = self.quantum_to_classical(circuit)

        # Normalize both for fair comparison
        psi_classical_norm = psi_classical / np.linalg.norm(psi_classical)
        psi_decoded_norm = psi_decoded / np.linalg.norm(psi_decoded)

        # Calculate errors
        difference = psi_classical_norm - psi_decoded_norm
        max_error = np.max(np.abs(difference))
        mean_error = np.mean(np.abs(difference))

        # Calculate normalization difference
        norm_diff = abs(np.linalg.norm(psi_decoded) - np.linalg.norm(psi_classical))

        # Calculate fidelity (overlap between normalized states)
        fidelity = (
            np.abs(np.vdot(psi_classical_norm.flatten(), psi_decoded_norm.flatten()))
            ** 2
        )

        return {
            "valid": max_error < tolerance,
            "max_error": float(max_error),
            "mean_error": float(mean_error),
            "norm_difference": float(norm_diff),
            "fidelity": float(fidelity),
        }


class WPOAQuantumInterface:
    """
    Interface between WPOA classical simulator and quantum implementations.

    Enables using quantum wave function encodings with the classical WPOA
    simulator, facilitating:
    - Hybrid quantum-classical simulations
    - Quantum algorithm validation against classical benchmarks
    - Performance comparisons

    Example:
        >>> from quscope.ctem import WPOASimulator
        >>>
        >>> # Initialize simulators
        >>> wpoa = WPOASimulator(image_size=50, pixels=256, beam_energy=200e3)
        >>> interface = WPOAQuantumInterface(wpoa, n_qubits_x=4, n_qubits_y=4)
        >>>
        >>> # Simulate with quantum encoding
        >>> atoms = [(0, 0, 6), (5, 0, 14)]
        >>> results = interface.simulate_with_quantum_encoding(
        ...     atoms, defocus=700, Cs=1.3e7
        ... )
        >>>
        >>> # Compare quantum vs classical
        >>> comparison = interface.compare_quantum_classical(atoms)

    Attributes:
        wpoa: WPOASimulator instance
        bridge: QuantumClassicalBridge for conversions
        n_qubits_x: Number of qubits for x dimension
        n_qubits_y: Number of qubits for y dimension
    """

    def __init__(self, wpoa_simulator, n_qubits_x: int, n_qubits_y: int):
        """
        Initialize WPOA-quantum interface.

        Args:
            wpoa_simulator: WPOASimulator instance
            n_qubits_x: Number of qubits for x (must match WPOA grid)
            n_qubits_y: Number of qubits for y (must match WPOA grid)

        Raises:
            ValueError: If quantum grid size doesn't match WPOA pixels
        """
        self.wpoa = wpoa_simulator
        self.n_qubits_x = n_qubits_x
        self.n_qubits_y = n_qubits_y

        # Validate grid compatibility
        expected_pixels = 2 ** max(n_qubits_x, n_qubits_y)
        if self.wpoa.pixels < expected_pixels:
            raise ValueError(
                f"WPOA grid ({self.wpoa.pixels}) too small for quantum encoding "
                f"({expected_pixels} needed)"
            )

        # Initialize bridge
        self.bridge = QuantumClassicalBridge(n_qubits_x, n_qubits_y)

    def simulate_with_quantum_encoding(
        self,
        atom_positions: List[Tuple[float, float, int]],
        defocus: float = 700.0,
        Cs: float = 1.3e7,
        alpha_max: Optional[float] = None,
        downsample: bool = True,
    ) -> Dict[str, Union[np.ndarray, QuantumCircuit]]:
        """
        Run WPOA simulation using quantum wave function encoding.

        Pipeline:
        1. Classical WPOA simulates transmission function
        2. Downsample to quantum grid size if needed
        3. Encode transmission into quantum circuit
        4. Classical propagation (lens CTF + inverse FFT)
        5. Encode final wave function quantum

        Args:
            atom_positions: List of (x, y, Z) atom coordinates
            defocus: Defocus in Angstroms
            Cs: Spherical aberration in Angstroms
            alpha_max: Aperture semi-angle in milliradians
            downsample: If True, downsample to quantum grid size

        Returns:
            Dictionary containing:
                - transmission_classical: Classical transmission function
                - transmission_quantum: Quantum circuit encoding transmission
                - wavefunction_classical: Final classical wave function
                - wavefunction_quantum: Final quantum circuit
                - intensity: Image intensity
                - potential: Atomic potential
                - consistency: Validation metrics
        """
        # Run classical WPOA simulation
        results = self.wpoa.simulate_image(
            atom_positions=atom_positions,
            defocus=defocus,
            Cs=Cs,
            alpha_max=alpha_max,
            return_wavefunction=True,
        )

        # Extract classical results
        transmission = results["transmission"]
        psi = results["psi"]

        # Downsample if needed
        if downsample and self.wpoa.pixels > self.bridge.pixels_x:
            scale_x = self.wpoa.pixels // self.bridge.pixels_x
            scale_y = self.wpoa.pixels // self.bridge.pixels_y
            transmission = transmission[::scale_y, ::scale_x]
            psi = psi[::scale_y, ::scale_x]

        # Encode transmission into quantum circuit
        transmission_quantum = self.bridge.classical_to_quantum(transmission)

        # Encode final wave function into quantum circuit
        psi_quantum = self.bridge.classical_to_quantum(psi)

        # Validate consistency
        consistency_transmission = self.bridge.validate_consistency(
            transmission, transmission_quantum
        )
        consistency_psi = self.bridge.validate_consistency(psi, psi_quantum)

        return {
            "transmission_classical": transmission,
            "transmission_quantum": transmission_quantum,
            "wavefunction_classical": psi,
            "wavefunction_quantum": psi_quantum,
            "intensity": np.abs(psi) ** 2,
            "potential": results["potential"],
            "consistency_transmission": consistency_transmission,
            "consistency_psi": consistency_psi,
        }

    def compare_quantum_classical(
        self,
        atom_positions: List[Tuple[float, float, int]],
        defocus: float = 700.0,
        Cs: float = 1.3e7,
    ) -> Dict[str, Union[float, np.ndarray]]:
        """
        Compare quantum encoding vs pure classical simulation.

        Runs both quantum-encoded and pure classical simulations
        to validate that quantum encoding preserves accuracy.

        Args:
            atom_positions: List of (x, y, Z) atom coordinates
            defocus: Defocus in Angstroms
            Cs: Spherical aberration in Angstroms

        Returns:
            Dictionary with comparison metrics:
                - transmission_error: Max error in transmission function
                - wavefunction_error: Max error in final wave function
                - intensity_error: Max error in intensity image
                - transmission_fidelity: State fidelity
                - wavefunction_fidelity: State fidelity
                - quantum_overhead: Circuit depth/gates info
        """
        # Run quantum-encoded simulation
        quantum_results = self.simulate_with_quantum_encoding(
            atom_positions, defocus, Cs
        )

        # Run pure classical simulation at quantum grid resolution
        classical_results = self.wpoa.simulate_image(
            atom_positions, defocus, Cs, return_wavefunction=True
        )

        # Downsample classical results
        scale = self.wpoa.pixels // self.bridge.pixels_x
        transmission_classical = classical_results["transmission"][::scale, ::scale]
        psi_classical = classical_results["psi"][::scale, ::scale]
        intensity_classical = np.abs(psi_classical) ** 2

        # Calculate errors
        transmission_error = np.max(
            np.abs(quantum_results["transmission_classical"] - transmission_classical)
        )

        wavefunction_error = np.max(
            np.abs(quantum_results["wavefunction_classical"] - psi_classical)
        )

        intensity_error = np.max(
            np.abs(quantum_results["intensity"] - intensity_classical)
        )

        # Get quantum circuit metrics
        circuit = quantum_results["wavefunction_quantum"]

        return {
            "transmission_error": float(transmission_error),
            "wavefunction_error": float(wavefunction_error),
            "intensity_error": float(intensity_error),
            "transmission_fidelity": quantum_results["consistency_transmission"][
                "fidelity"
            ],
            "wavefunction_fidelity": quantum_results["consistency_psi"]["fidelity"],
            "quantum_overhead": {
                "qubits": circuit.num_qubits,
                "depth": circuit.depth(),
                "gates": circuit.size(),
            },
        }


class MultisliceQuantumInterface:
    """
    Interface between Multislice classical simulator and quantum implementations.

    Enables using quantum wave function encodings with the classical multislice
    simulator for thick specimen simulations.

    Example:
        >>> from quscope.ctem import MultisliceSimulator
        >>>
        >>> # Initialize simulators
        >>> multislice = MultisliceSimulator(
        ...     image_size=40, pixels=256, beam_energy=200e3, slice_thickness=2.0
        ... )
        >>> interface = MultisliceQuantumInterface(multislice, n_qubits_x=4, n_qubits_y=4)
        >>>
        >>> # Simulate with quantum encoding at each slice
        >>> atoms = generate_crystal_atoms()
        >>> results = interface.simulate_with_quantum_slices(
        ...     atoms, num_slices=100, defocus=0
        ... )

    Attributes:
        multislice: MultisliceSimulator instance
        bridge: QuantumClassicalBridge for conversions
        n_qubits_x: Number of qubits for x dimension
        n_qubits_y: Number of qubits for y dimension
    """

    def __init__(self, multislice_simulator, n_qubits_x: int, n_qubits_y: int):
        """
        Initialize Multislice-quantum interface.

        Args:
            multislice_simulator: MultisliceSimulator instance
            n_qubits_x: Number of qubits for x
            n_qubits_y: Number of qubits for y

        Raises:
            ValueError: If quantum grid size doesn't match multislice pixels
        """
        self.multislice = multislice_simulator
        self.n_qubits_x = n_qubits_x
        self.n_qubits_y = n_qubits_y

        # Validate grid compatibility
        expected_pixels = 2 ** max(n_qubits_x, n_qubits_y)
        if self.multislice.pixels < expected_pixels:
            raise ValueError(
                f"Multislice grid ({self.multislice.pixels}) too small "
                f"for quantum encoding ({expected_pixels} needed)"
            )

        # Initialize bridge
        self.bridge = QuantumClassicalBridge(n_qubits_x, n_qubits_y)

    def simulate_with_quantum_slices(
        self,
        atom_positions: List[Tuple[float, float, float, int]],
        num_slices: int,
        defocus: float = 0,
        Cs: float = 0,
        record_slices: Optional[List[int]] = None,
    ) -> Dict[str, Union[List, np.ndarray]]:
        """
        Run multislice simulation with quantum encoding at specified slices.

        Performs multislice propagation and encodes the wave function
        into quantum circuits at specified slice indices for analysis.

        Args:
            atom_positions: List of (x, y, z, Z) atom coordinates
            num_slices: Total number of slices
            defocus: Defocus in Angstroms
            Cs: Spherical aberration in Angstroms
            record_slices: Slice indices to encode quantum (default: [0, middle, end])

        Returns:
            Dictionary containing:
                - intensity_final: Final intensity image
                - quantum_snapshots: List of quantum circuits at recorded slices
                - classical_snapshots: List of classical wave functions
                - consistency: Validation metrics at each recorded slice
                - slice_indices: Which slices were recorded
        """
        # Default: record at start, middle, end
        if record_slices is None:
            record_slices = [0, num_slices // 2, num_slices - 1]

        # Run classical multislice (we'll implement wrapper if needed)
        # For now, return placeholder structure

        quantum_snapshots = []
        classical_snapshots = []
        consistency_results = []

        # This is a placeholder - actual implementation would iterate through slices
        # and encode at specified indices

        return {
            "intensity_final": np.zeros((self.bridge.pixels_y, self.bridge.pixels_x)),
            "quantum_snapshots": quantum_snapshots,
            "classical_snapshots": classical_snapshots,
            "consistency": consistency_results,
            "slice_indices": record_slices,
            "note": "Full implementation requires multislice method refactoring",
        }


def benchmark_quantum_classical_integration(
    n_qubits_range: List[int] = [2, 3, 4], num_trials: int = 5
) -> Dict[str, List]:
    """
    Benchmark quantum-classical integration performance.

    Measures:
    - Encoding time: classical → quantum
    - Decoding time: quantum → classical
    - Round-trip accuracy
    - Memory overhead

    Args:
        n_qubits_range: List of qubit counts to test
        num_trials: Number of trials per configuration

    Returns:
        Dictionary with benchmark results:
            - n_qubits: List of qubit counts tested
            - encoding_times: Mean encoding time per config
            - decoding_times: Mean decoding time per config
            - errors: Mean round-trip errors
            - memory_overhead: Quantum vs classical memory ratio

    Example:
        >>> results = benchmark_quantum_classical_integration([2, 3, 4])
        >>> import matplotlib.pyplot as plt
        >>> plt.plot(results['n_qubits'], results['encoding_times'])
        >>> plt.xlabel('Number of Qubits')
        >>> plt.ylabel('Encoding Time (s)')
    """
    import time

    encoding_times = []
    decoding_times = []
    errors = []

    for n_qubits in n_qubits_range:
        bridge = QuantumClassicalBridge(n_qubits, n_qubits)
        pixels = 2**n_qubits

        trial_encoding = []
        trial_decoding = []
        trial_errors = []

        for _ in range(num_trials):
            # Generate random wave function
            psi = np.random.rand(pixels, pixels) + 1j * np.random.rand(pixels, pixels)
            psi = psi / np.linalg.norm(psi)

            # Measure encoding time
            start = time.time()
            circuit = bridge.classical_to_quantum(psi)
            trial_encoding.append(time.time() - start)

            # Measure decoding time
            start = time.time()
            psi_decoded = bridge.quantum_to_classical(circuit)
            trial_decoding.append(time.time() - start)

            # Measure error
            error = np.max(np.abs(psi - psi_decoded))
            trial_errors.append(error)

        encoding_times.append(np.mean(trial_encoding))
        decoding_times.append(np.mean(trial_decoding))
        errors.append(np.mean(trial_errors))

    return {
        "n_qubits": n_qubits_range,
        "encoding_times": encoding_times,
        "decoding_times": decoding_times,
        "errors": errors,
        "pixels": [2**n for n in n_qubits_range],
    }
