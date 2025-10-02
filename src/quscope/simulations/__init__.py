"""
Quantum TEM Simulations Module

This module provides quantum implementations of Transmission Electron Microscopy
simulations using Qiskit for quantum algorithms (i.e. QFT).

Classes:
- ThinCTEM: Weak Phase Object approximation for thin specimens.
- ThickCTEM: Multislice method for thick specimens.
- TEMQFT: Necessary quantum transformations and algorithms for TEM simulations.
"""

try:
    from quscope.simulations.wpo import ThinCTEM  # type: ignore
    from quscope.simulations.multislice import ThickCTEM  # type: ignore
    from quscope.simulations.quantum_utils import TEMQFT  # type: ignore
except Exception:
    # Optional dependency or import issues should not break package import
    ThinCTEM = None  # type: ignore
    ThickCTEM = None  # type: ignore
    TEMQFT = None  # type: ignore

__version__ = "0.1.0"
__author__ = "Roberto dos Reis and Sean Lam"
__all__ = [
    name for name in ("ThinCTEM", "ThickCTEM", "TEMQFT") if globals().get(name) is not None
]