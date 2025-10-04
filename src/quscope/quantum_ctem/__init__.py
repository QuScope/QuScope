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

Current Status: Phase 1 - Week 1

Modules:
- quantum_wave_function: Quantum encoding of electron wave functions
- [TO BE ADDED] quantum_phase_grating: Quantum transmission function
- [TO BE ADDED] quantum_propagator: Quantum Fresnel propagation
- [TO BE ADDED] quantum_multislice: Full quantum multislice simulation
"""

from .quantum_wave_function import QuantumWaveFunction

__all__ = [
    'QuantumWaveFunction',
]

__version__ = '0.1.0'
__phase__ = 'Phase 1: Quantum Wave Function Representation'
__status__ = 'Active Development'
