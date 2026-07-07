"""
QuScope Quantum CTEM Module
===========================

Pure quantum algorithms for Conventional Transmission Electron Microscopy
(CTEM) image simulation. This module provides a complete framework for
simulating CTEM image formation on quantum computers.

Key Features:
- Amplitude encoding of electron wavefunctions into quantum states
- Quantum Fourier Transform (QFT) based propagation
- Weak Phase Object Approximation (WPOA) implementation
- Contrast Transfer Function (CTF) with aberration support
- Support for both IBM Quantum hardware and local simulators
- Material-specific workflows for MoS₂ and Graphene

Quick Start:
    >>> from quscope.quantum_ctem import get_backend, MoS2Workflow

    >>> # Run simulation on local simulator
    >>> backend = get_backend("simulator")
    >>> workflow = MoS2Workflow(backend=backend, voltage=200e3)
    >>> result = workflow.run(nx=3, ny=2, grid_size=64)
    >>> print(result.summary())

    >>> # Run on IBM hardware
    >>> backend = get_backend("ibm", device_name="ibm_kyoto")
    >>> result = workflow.run(nx=3, ny=2, grid_size=64, shots=4096)

Architecture:
    backends/     - Quantum backend abstraction (simulator, IBM)
    materials/    - Material definitions (MoS2, Graphene)
    workflows/    - End-to-end simulation workflows

Core Classes:
    QuantumWaveFunction    - Amplitude encoding of 2D wavefunctions
    MomentumSpaceConverter - QFT-based real/momentum space transforms
    CTFCalculator          - Contrast transfer function implementation
"""

__version__ = "0.2.0"
__author__ = "Roberto dos Reis, Sean D. Lam"

# =============================================================================
# High-Level API (Recommended for most users)
# =============================================================================

# Backends
from .backends import (
    Backend,
    BackendConfig,
    ExecutionResult,
    SimulatorBackend,
    IBMBackend,
    get_backend,
    list_available_backends,
)

# Materials
from .materials import (
    Material,
    MoS2,
    Graphene,
    get_material,
    list_materials,
)

# Workflows
from .workflows import (
    CTEMWorkflow,
    MicroscopeConfig,
    SimulationResult,
    MoS2Workflow,
    GrapheneWorkflow,
)

# =============================================================================
# Core Components (For advanced users and custom implementations)
# =============================================================================

# Quantum wave function encoding
from .quantum_wave_function import QuantumWaveFunction

# Momentum space operations (QFT-based)
from .momentum_space import (
    MomentumSpaceConverter,
    MomentumSpaceFilter,
    ParsevalValidator,
    analyze_momentum_distribution,
)

# Circuit optimization for hardware
from .circuit_optimization import (
    StatePreparationOptimizer,
    HardwareTranspiler,
    benchmark_state_preparation,
)

# Classical integration (for validation)
from .classical_integration import (
    QuantumClassicalBridge,
    WPOAQuantumInterface,
    MultisliceQuantumInterface,
)

# CTF calculator
from .ctf_calculator import CTFCalculator

# Fully Quantum CTEM Circuit (TRUE quantum implementation)
from .quantum_ctem_circuit import (
    QuantumCTEMParameters,
    QuantumCTEMCircuit,
    PhaseGratingCircuit,
    LensCTFCircuit,
    QuantumClassicalValidator,
    relativistic_wavelength,
    interaction_constant,
)

# Fully Quantum Multislice Circuit
from .quantum_multislice_circuit import (
    QuantumMultisliceParameters,
    QuantumMultisliceCircuit,
    FresnelPropagatorCircuit,
    QuantumClassicalMultisliceValidator,
)

# Hamiltonian components
from .hamiltonian import (
    TEMHamiltonian,
    FreeParticleHamiltonian,
    SampleHamiltonian,
    LensHamiltonian,
    HamiltonianParameters,
)

# =============================================================================
# IBM Hardware Integration
# =============================================================================

from .ibm_hardware_validation import (
    IBMHardwareValidator,
    IBMDeviceProfile,
    validate_ibm_deployment,
)

# Legacy IBM config (use get_backend("ibm") instead)
from .ibm_config import (
    load_ibm_credentials,
    get_ibm_service,
    validate_ibm_access,
)

# =============================================================================
# Fully Quantum TEM Advanced Modules
# =============================================================================

# Quantum Frozen Phonon / Thermal Diffuse Scattering (3 approaches)
from .quantum_frozen_phonon import (
    DebyeWaller,
    apply_frozen_phonon_to_potential,
    QuantumThermalPhaseChannel,
    QuantumPhononSuperposition,
    QuantumLindbladChannel,
    k_grid,
    fresnel_propagator,
)

# Quantum Bloch Wave via QPE
from .quantum_bloch_wave import (
    MoS2StructureFactors,
    BlochWaveMatrix,
    ClassicalBlochWave,
    QuantumBlochWave,
    BlochWaveExitWave,
)

# Quantum Diffraction Modes (SAED, CBED, Kikuchi, nBD, EBSD, WPOA)
from .quantum_diffraction import (
    simulate_saed,
    simulate_cbed,
    simulate_kikuchi,
    simulate_nbd,
    simulate_ebsd,
    simulate_wpoa,
)

# Quantum STEM
from .quantum_stem import (
    STEMDetectors,
    run_stem,
)

# Quantum STEM Multislice
from .quantum_stem_multislice import (
    fresnel_propagator_phase,
    build_probe_circuit,
    run_stem_multislice
)

# =============================================================================
# Benchmarking and Visualization
# =============================================================================

from .performance_benchmarking import (
    BenchmarkResult,
    PerformanceBenchmark,
    quick_benchmark,
)

from .benchmark_visualization import (
    BenchmarkVisualizer,
    create_summary_figure,
)

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
    "BackendConfig",
    "ExecutionResult",
    "SimulatorBackend",
    "IBMBackend",
    # High-level API - Materials
    "get_material",
    "list_materials",
    "Material",
    "MoS2",
    "Graphene",
    # High-level API - Workflows
    "MoS2Workflow",
    "GrapheneWorkflow",
    "CTEMWorkflow",
    "MicroscopeConfig",
    "SimulationResult",
    # Core - Quantum encoding
    "QuantumWaveFunction",
    # Core - Momentum space
    "MomentumSpaceConverter",
    "MomentumSpaceFilter",
    "ParsevalValidator",
    "analyze_momentum_distribution",
    # Core - Circuit optimization
    "StatePreparationOptimizer",
    "HardwareTranspiler",
    "benchmark_state_preparation",
    # Core - Classical integration
    "QuantumClassicalBridge",
    "WPOAQuantumInterface",
    "MultisliceQuantumInterface",
    # Core - CTF
    "CTFCalculator",
    # Core - Fully Quantum CTEM Circuit
    "QuantumCTEMParameters",
    "QuantumCTEMCircuit",
    "PhaseGratingCircuit",
    "LensCTFCircuit",
    "QuantumClassicalValidator",
    "relativistic_wavelength",
    "interaction_constant",
    # Core - Fully Quantum Multislice Circuit
    "QuantumMultisliceParameters",
    "QuantumMultisliceCircuit",
    "FresnelPropagatorCircuit",
    "QuantumClassicalMultisliceValidator",
    # Core - Hamiltonian
    "TEMHamiltonian",
    "FreeParticleHamiltonian",
    "SampleHamiltonian",
    "LensHamiltonian",
    "HamiltonianParameters",
    # IBM Hardware
    "IBMHardwareValidator",
    "IBMDeviceProfile",
    "validate_ibm_deployment",
    "load_ibm_credentials",
    "get_ibm_service",
    "validate_ibm_access",
    # Benchmarking
    "BenchmarkResult",
    "PerformanceBenchmark",
    "quick_benchmark",
    "BenchmarkVisualizer",
    "create_summary_figure",
    # Quantum Frozen Phonon
    "DebyeWaller",
    "apply_frozen_phonon_to_potential",
    "QuantumThermalPhaseChannel",
    "QuantumPhononSuperposition",
    "QuantumLindbladChannel",
    "k_grid",
    "fresnel_propagator",
    # Quantum Bloch Wave
    "MoS2StructureFactors",
    "BlochWaveMatrix",
    "ClassicalBlochWave",
    "QuantumBlochWave",
    "BlochWaveExitWave",
    # Quantum Diffraction
    "simulate_saed",
    "simulate_cbed",
    "simulate_kikuchi",
    "simulate_nbd",
    "simulate_ebsd",
    "simulate_wpoa",
    # Quantum STEM
    "STEMDetectors",
    "run_stem",
    # STEM Multislice
    "fresnel_propagator_phase",
    "build_probe_circuit",
    "run_stem_multislice",
]
