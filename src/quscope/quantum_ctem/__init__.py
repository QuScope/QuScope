"""
QuScope Quantum CTEM Module

This module implements pure quantum algorithms for Conventional Transmission
Electron Microscopy (CTEM) image simulation. Unlike hybrid quantum-classical
approaches, this is a fully quantum implementation where the electron wave
function evolution happens entirely on a quantum computer.

Phases:
- Phase 1: Quantum Wave Function Representation (Weeks 1-4)
- Phase 2: Quantum Phase Grating (Weeks 5-8)
- Phase 3: Quantum Propagation (Weeks 9-12)
- Phase 4: Full Quantum Multislice (Weeks 13-16)
- Phase 5: Optimization & Hardware (Weeks 17-20)
- Phase 6: Publication (Weeks 21-24)

Current Status: Phase 1 - Week 3

Modules:
- quantum_wave_function: Quantum encoding of electron wave functions ✅
- circuit_optimization: Hardware-ready circuit optimization ✅
- momentum_space: Enhanced momentum space operations ✅
- classical_integration: Quantum-classical bridge interfaces 🔄
- [TO BE ADDED] quantum_phase_grating: Quantum transmission function
- [TO BE ADDED] quantum_propagator: Quantum Fresnel propagation
- [TO BE ADDED] quantum_multislice: Full quantum multislice simulation
"""

from .quantum_wave_function import QuantumWaveFunction
from .circuit_optimization import (
    StatePreparationOptimizer,
    HardwareTranspiler,
    benchmark_state_preparation,
)
from .momentum_space import (
    MomentumSpaceConverter,
    ParsevalValidator,
    MomentumSpaceFilter,
    analyze_momentum_distribution,
    demonstrate_uncertainty_principle,
)
from .classical_integration import (
    QuantumClassicalBridge,
    WPOAQuantumInterface,
    MultisliceQuantumInterface,
    benchmark_quantum_classical_integration,
)

__all__ = [
    'QuantumWaveFunction',
    'StatePreparationOptimizer',
    'HardwareTranspiler',
    'benchmark_state_preparation',
    'MomentumSpaceConverter',
    'ParsevalValidator',
    'MomentumSpaceFilter',
    'analyze_momentum_distribution',
    'demonstrate_uncertainty_principle',
    'QuantumClassicalBridge',
    'WPOAQuantumInterface',
    'MultisliceQuantumInterface',
    'benchmark_quantum_classical_integration',
]

__version__ = '0.1.0'
__phase__ = 'Phase 1 Week 3: Classical-Quantum Integration'
__status__ = 'Active Development'
