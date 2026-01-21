"""
QuScope Classical CTEM Module

This module contains validated classical CTEM (Conventional Transmission Electron Microscopy)
implementations based on Earl J. Kirkland's "Advanced Computing in Electron Microscopy" 2nd Edition.

The classical implementations serve as:
1. Reference baseline for quantum algorithm validation
2. Tested and validated physics implementations
3. Comparison benchmarks for quantum advantage demonstrations

Modules:
- kirkland_potential: Atomic potential calculations (Kirkland Appendix C)
- wpoa_simulator: Weak Phase Object Approximation simulator (Kirkland Chapter 5)
- multislice_simulator: Full multislice algorithm (Kirkland Chapter 7)
- structures: Crystal structure generation utilities [TO BE ADDED]
"""

from .kirkland_potential import KirklandPotential
from .multislice_simulator import MultisliceSimulator
from .wpoa_simulator import WPOASimulator

# TODO: Add these modules as we extract them from notebooks
# from .structures import create_gaas_structure, create_silicon_structure

__all__ = [
    "KirklandPotential",
    "WPOASimulator",
    "MultisliceSimulator",
    # 'create_gaas_structure',
    # 'create_silicon_structure',
]
