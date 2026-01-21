"""Base quantum algorithm implementation."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.providers import Backend
from qiskit.result import Result

from ..config import Config
from ..exceptions import QuantumCircuitError, ValidationError

logger = logging.getLogger(__name__)


class BaseQuantumAlgorithm(ABC):
    """Base class for quantum algorithms with improved structure."""

    def __init__(self, config: Config):
        """Initialize quantum algorithm with configuration."""
        self.config = config
        self.circuit: Optional[QuantumCircuit] = None
        self.results: Optional[Result] = None
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate quantum configuration."""
        if self.config.quantum.shots <= 0:
            raise ValidationError("Number of shots must be positive")

        if self.config.quantum.max_qubits <= 0:
            raise ValidationError("Maximum qubits must be positive")

    @abstractmethod
    def build_circuit(self, **kwargs) -> QuantumCircuit:
        """Build the quantum circuit for the algorithm."""
        pass

    @abstractmethod
    def analyze_results(self, results: Result) -> Dict[str, Any]:
        """Analyze quantum execution results."""
        pass

    def validate_parameters(self, **kwargs) -> None:
        """Validate algorithm-specific parameters."""
        pass

    def execute(self, backend: Backend, **kwargs) -> Dict[str, Any]:
        """Execute the quantum algorithm."""
        try:
            # Validate parameters
            self.validate_parameters(**kwargs)

            # Build circuit
            self.circuit = self.build_circuit(**kwargs)

            # Execute circuit
            job = backend.run(
                self.circuit,
                shots=self.config.quantum.shots,
                optimization_level=self.config.quantum.optimization_level,
                seed_simulator=self.config.quantum.seed,
            )

            self.results = job.result()

            # Analyze results
            analysis = self.analyze_results(self.results)

            logger.info(f"Successfully executed {self.__class__.__name__}")
            return analysis

        except Exception as e:
            logger.error(f"Error executing quantum algorithm: {e}")
            raise QuantumCircuitError(f"Failed to execute quantum algorithm: {e}")

    def get_circuit_depth(self) -> int:
        """Get the depth of the quantum circuit."""
        if self.circuit is None:
            raise QuantumCircuitError("Circuit not built yet")
        return self.circuit.depth()

    def get_circuit_size(self) -> int:
        """Get the size (number of gates) of the quantum circuit."""
        if self.circuit is None:
            raise QuantumCircuitError("Circuit not built yet")
        return self.circuit.size()
