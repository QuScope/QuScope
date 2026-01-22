"""
QuScope: Quantum Algorithm Framework for Phase-Contrast CTEM Image Simulation.

This package provides a complete quantum computing framework for simulating
Conventional Transmission Electron Microscopy (CTEM) images using quantum
algorithms on both simulators and IBM Quantum hardware.

Key Features:
- Amplitude encoding of electron wavefunctions into quantum states
- Quantum Fourier Transform (QFT) based propagation
- Weak Phase Object Approximation (WPOA) implementation
- Contrast Transfer Function (CTF) with aberration support
- Material-specific workflows for MoS₂ and Graphene
- Support for both IBM Quantum hardware and local simulators

Quick Start:
    >>> from quscope import get_backend, MoS2Workflow, GrapheneWorkflow

    >>> # Run simulation on local simulator
    >>> backend = get_backend("simulator")
    >>> workflow = MoS2Workflow(backend=backend, voltage=200e3)
    >>> result = workflow.run(nx=3, ny=2, grid_size=64)
    >>> print(result.summary())

    >>> # Run on IBM hardware
    >>> backend = get_backend("ibm", device_name="ibm_kyoto")
    >>> result = workflow.run(nx=3, ny=2, grid_size=64, shots=4096)

For more details, see the quantum_ctem subpackage.

Author: Roberto dos Reis, Sean D. Lam
"""

from importlib.metadata import PackageNotFoundError as _PkgNotFoundError
from importlib.metadata import version as _pkg_version

try:
    __version__ = _pkg_version("quscope")
except _PkgNotFoundError:
    __version__ = "0.1.0+dev"

# =============================================================================
# High-Level API (Recommended for most users)
# =============================================================================

# Re-export key classes from quantum_ctem for convenience
from .quantum_ctem import (
    # Backend management
    get_backend,
    list_available_backends,
    Backend,
    SimulatorBackend,
    IBMBackend,
    # Material definitions
    get_material,
    list_materials,
    MoS2,
    Graphene,
    # Workflows
    MoS2Workflow,
    GrapheneWorkflow,
    CTEMWorkflow,
    MicroscopeConfig,
    SimulationResult,
)

# =============================================================================
# Core Components (For advanced users)
# =============================================================================

from .quantum_ctem import (
    QuantumWaveFunction,
    MomentumSpaceConverter,
    CTFCalculator,
)

# =============================================================================
# Submodules (for direct access to low-level components)
# =============================================================================

from . import quantum_ctem
from . import ctem
from . import simulations
from . import utils

# Legacy support
from . import quantum_backend

# =============================================================================
# Public API
# =============================================================================

__all__ = [
    # Version
    "__version__",
    # High-level API - Backends
    "get_backend",
    "list_available_backends",
    "Backend",
    "SimulatorBackend",
    "IBMBackend",
    # High-level API - Materials
    "get_material",
    "list_materials",
    "MoS2",
    "Graphene",
    # High-level API - Workflows
    "MoS2Workflow",
    "GrapheneWorkflow",
    "CTEMWorkflow",
    "MicroscopeConfig",
    "SimulationResult",
    # Core components
    "QuantumWaveFunction",
    "MomentumSpaceConverter",
    "CTFCalculator",
    # Submodules
    "quantum_ctem",
    "ctem",
    "simulations",
    "utils",
    "quantum_backend",
]
