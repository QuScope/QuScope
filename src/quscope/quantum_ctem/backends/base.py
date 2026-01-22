"""
Abstract Base Classes for Quantum Backends.

Defines the interface that all quantum backends must implement,
ensuring consistent behavior across simulators and real hardware.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

import numpy as np
from qiskit import QuantumCircuit
from qiskit.result import Result


@dataclass
class BackendConfig:
    """Configuration for quantum backend execution."""

    shots: int = 1024
    optimization_level: int = 3
    seed_simulator: Optional[int] = None
    memory: bool = False
    init_qubits: bool = True

    # Hardware-specific options
    dynamic_decoupling: bool = False
    resilience_level: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for backend options."""
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class ExecutionResult:
    """Standardized result from quantum circuit execution."""

    # Core results
    counts: Dict[str, int] = field(default_factory=dict)
    statevector: Optional[np.ndarray] = None
    probabilities: Optional[np.ndarray] = None

    # Metadata
    shots: int = 0
    success: bool = True
    backend_name: str = ""
    execution_time: float = 0.0
    job_id: Optional[str] = None

    # Circuit info
    num_qubits: int = 0
    depth: int = 0
    gate_counts: Dict[str, int] = field(default_factory=dict)

    # Error information
    error_message: Optional[str] = None

    def get_statevector_2d(self, nx: int, ny: int) -> np.ndarray:
        """
        Reshape statevector to 2D grid for CTEM wavefunction.

        Args:
            nx: Number of pixels in x direction
            ny: Number of pixels in y direction

        Returns:
            Complex 2D array of shape (ny, nx) representing the wavefunction
        """
        if self.statevector is None:
            raise ValueError("No statevector available. Run with statevector simulator.")

        expected_size = nx * ny
        if len(self.statevector) != expected_size:
            raise ValueError(
                f"Statevector size {len(self.statevector)} doesn't match "
                f"grid size {nx}x{ny}={expected_size}"
            )

        return self.statevector.reshape((ny, nx))

    def get_intensity(self, nx: int, ny: int) -> np.ndarray:
        """
        Get intensity (|ψ|²) as 2D array.

        Args:
            nx: Number of pixels in x direction
            ny: Number of pixels in y direction

        Returns:
            Real 2D array of intensity values
        """
        psi = self.get_statevector_2d(nx, ny)
        return np.abs(psi) ** 2


class Backend(ABC):
    """
    Abstract base class for quantum backends.

    All backends (simulator, IBM hardware, etc.) must implement this interface
    to ensure consistent behavior across the quantum CTEM package.
    """

    def __init__(self, name: str = "base"):
        self.name = name
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        """Check if backend is ready for execution."""
        return self._is_connected

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the backend.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def run(
        self,
        circuit: QuantumCircuit,
        config: Optional[BackendConfig] = None,
    ) -> ExecutionResult:
        """
        Execute a quantum circuit on this backend.

        Args:
            circuit: Qiskit QuantumCircuit to execute
            config: Execution configuration options

        Returns:
            ExecutionResult with counts, statevector (if available), and metadata
        """
        pass

    @abstractmethod
    def run_batch(
        self,
        circuits: List[QuantumCircuit],
        config: Optional[BackendConfig] = None,
    ) -> List[ExecutionResult]:
        """
        Execute multiple circuits in a batch.

        Args:
            circuits: List of QuantumCircuit objects
            config: Execution configuration options

        Returns:
            List of ExecutionResult objects
        """
        pass

    def transpile(
        self,
        circuit: QuantumCircuit,
        optimization_level: int = 3,
    ) -> QuantumCircuit:
        """
        Transpile circuit for this backend.

        Args:
            circuit: Circuit to transpile
            optimization_level: Qiskit optimization level (0-3)

        Returns:
            Transpiled circuit
        """
        from qiskit import transpile

        return transpile(
            circuit,
            backend=self._get_qiskit_backend(),
            optimization_level=optimization_level,
        )

    @abstractmethod
    def _get_qiskit_backend(self):
        """Get the underlying Qiskit backend object."""
        pass

    def get_circuit_metrics(self, circuit: QuantumCircuit) -> Dict[str, Any]:
        """
        Get metrics for a circuit on this backend.

        Args:
            circuit: Circuit to analyze

        Returns:
            Dictionary with depth, gate counts, etc.
        """
        transpiled = self.transpile(circuit)
        return {
            "original_depth": circuit.depth(),
            "transpiled_depth": transpiled.depth(),
            "num_qubits": circuit.num_qubits,
            "gate_counts": dict(transpiled.count_ops()),
            "two_qubit_gates": sum(
                count
                for gate, count in transpiled.count_ops().items()
                if gate in ["cx", "cz", "ecr", "rzz"]
            ),
        }

    def __repr__(self) -> str:
        status = "connected" if self.is_connected else "disconnected"
        return f"{self.__class__.__name__}(name='{self.name}', status='{status}')"
