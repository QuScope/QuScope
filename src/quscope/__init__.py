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

# Import main modules (avoid importing quantum_backend eagerly to prevent
# optional qiskit_ibm_provider dependency during docs build)
from . import image_processing
from . import qml
from . import eels_analysis

# Optional: simulations (may depend on qiskit)
try:
    from . import simulations  # type: ignore
except Exception:
    simulations = None  # type: ignore

# Import key classes and functions for easy access (lazy import for backend)
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
    # Version (always available)
    "__version__",
    
    # Modules
    "image_processing", 
    "qml",
    "eels_analysis",
]

# Conditionally expose simulations when available
if simulations is not None:
    __all__.append("simulations")

# Add key classes and functions
__all__ += [
    # Key classes
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

# Provide lazy access to QuantumBackendManager to avoid import-time side effects
def __getattr__(name):
    if name == "QuantumBackendManager" or name == "quantum_backend":
        from . import quantum_backend as _qb
        if name == "QuantumBackendManager":
            return _qb.QuantumBackendManager
        return _qb
    raise AttributeError(f"module 'quscope' has no attribute {name!r}")
