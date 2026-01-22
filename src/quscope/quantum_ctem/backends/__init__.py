"""
Quantum Backend Abstraction Layer.

This module provides a unified interface for running quantum circuits on
different backends: IBM Quantum hardware, local simulators, and fake devices.

Usage:
    from quscope.quantum_ctem.backends import get_backend, SimulatorBackend, IBMBackend

    # For development/testing - use simulator
    backend = get_backend("simulator")

    # For production - use IBM hardware
    backend = get_backend("ibm", device_name="ibm_kyoto")

    # Run a circuit
    result = backend.run(circuit, shots=1024)
"""

from .base import Backend, BackendConfig, ExecutionResult
from .simulator import SimulatorBackend
from .ibm import IBMBackend

# Backend registry
_BACKEND_REGISTRY = {
    "simulator": SimulatorBackend,
    "statevector": SimulatorBackend,
    "ibm": IBMBackend,
    "ibm_quantum": IBMBackend,
}


def get_backend(backend_type: str, **kwargs) -> Backend:
    """
    Factory function to get a quantum backend.

    Args:
        backend_type: One of "simulator", "statevector", "ibm", "ibm_quantum"
        **kwargs: Backend-specific configuration options

    Returns:
        Configured Backend instance

    Examples:
        >>> backend = get_backend("simulator")
        >>> backend = get_backend("ibm", device_name="ibm_kyoto")
    """
    backend_type = backend_type.lower()

    if backend_type not in _BACKEND_REGISTRY:
        available = ", ".join(_BACKEND_REGISTRY.keys())
        raise ValueError(
            f"Unknown backend type: {backend_type}. Available: {available}"
        )

    backend_class = _BACKEND_REGISTRY[backend_type]
    return backend_class(**kwargs)


def list_available_backends() -> dict:
    """List all available backend types and their descriptions."""
    return {
        "simulator": "Local Qiskit Aer statevector simulator (fast, exact)",
        "statevector": "Alias for simulator",
        "ibm": "IBM Quantum hardware (requires credentials)",
        "ibm_quantum": "Alias for ibm",
    }


__all__ = [
    "Backend",
    "BackendConfig",
    "ExecutionResult",
    "SimulatorBackend",
    "IBMBackend",
    "get_backend",
    "list_available_backends",
]
