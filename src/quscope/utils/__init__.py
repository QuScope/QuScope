"""
Utility module for TEM simulations

This module contains utility functions and constants for electron microscopy
simulations, including physical constants, Kirkland atomic potentials, and
common calculations.

Modules:
- constants: Physical constants and common TEM calculations
- kirkland: Kirkland atomic potential parameterization
"""

from quscope.utils.constants import (
    PhysicalConstants
)

from quscope.utils.kirkland import (
    KirklandPotential,
    KIRKLAND_SCATTERING_FACTOR
)

__version__ = "0.1.0"
__all__ = [
    # Classes
    PhysicalConstants,
    KirklandPotential,
    
    # Constants
    KIRKLAND_SCATTERING_FACTOR
]