"""
Quantum TEM Simulations Module

This module provides quantum implementations of Transmission Electron Microscopy
simulations using Qiskit for quantum algorithms (i.e. QFT).

Classes:
- ThinCTEM: Weak Phase Object approximation for thin specimens.
- ThickCTEM: Multislice method for thick specimens.
- TEMQFT: Necessary quantum transformations and algorithms for TEM simulations.
"""

from quscope.simulations.wpo import ThinCTEM
from quscope.simulations.multislice import ThickCTEM
from quscope.simulations.quantum_utils import TEMQFT

__version__ = "0.1.0"
__author__ = "Roberto dos Reis and Sean D. Lam"
__all__ = [
    ThinCTEM,
    ThickCTEM,
    TEMQFT
]