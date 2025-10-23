"""
QuScope: Quantum algorithms for microscopy image processing and EELS analysis.

This package provides quantum computing tools for:
- Quantum image processing and encoding
- EELS (Electron Energy Loss Spectroscopy) analysis  
- Quantum machine learning for microscopy data
- Quantum backend management and circuit execution
"""

from importlib.metadata import version as _pkg_version, PackageNotFoundError as _PkgNotFoundError

try:
    __version__ = _pkg_version("quscope")
except _PkgNotFoundError:
    __version__ = "0.1.0+dev"

# Import main modules
from . import quantum_backend
from . import image_processing
from . import qml
from . import eels_analysis

# Import key classes and functions for easy access
from .quantum_backend import QuantumBackendManager
from .image_processing.quantum_encoding import (
    encode_image_to_circuit,
    EncodingMethod,
    validate_image_array,
    calculate_required_qubits
)
from .image_processing.preprocessing import (
    preprocess_image,
    binarize_image
)
from .qml.image_encoding import QuantumImageEncoder, encode_image_quantum

__all__ = [
    # Version
    "__version__",
    
    # Modules
    "quantum_backend",
    "image_processing", 
    "qml",
    "eels_analysis",
    
    # Key classes
    "QuantumBackendManager",
    "QuantumImageEncoder",
    
    # Key functions
    "encode_image_to_circuit",
    "EncodingMethod",
    "validate_image_array",
    "calculate_required_qubits",
    "preprocess_image",
    "binarize_image",
    "encode_image_quantum",
]
