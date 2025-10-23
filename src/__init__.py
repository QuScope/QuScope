"""
QuScope - Quantum Algorithm Microscopy Package

A comprehensive toolkit for quantum algorithm analysis, quantum image processing,
and quantum machine learning with microscopy applications.
"""

__version__ = "0.1.0"
__author__ = "Roberto Reis"
__email__ = "roberto@example.com"
__description__ = "Quantum Algorithm Microscopy - Advanced quantum computing analysis tools"

# Core imports
try:
    from .quantum.microscopy import QuantumMicroscopy
    from .config import Config
except ImportError:
    # Graceful fallback if optional dependencies are missing
    QuantumMicroscopy = None
    Config = None

# QuScope modules - the main package components
from .quscope import *

__all__ = [
    # Core classes
    "QuantumMicroscopy",
    "Config",
    # QuScope modules (imported via *)
    # These are defined in quscope/__init__.py
]
