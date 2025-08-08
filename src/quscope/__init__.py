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

# Import main modules with optional fallbacks
try:
    from . import quantum_backend
    _quantum_backend_available = True
except ImportError:
    _quantum_backend_available = False

try:
    from . import image_processing
    _image_processing_available = True
except ImportError:
    _image_processing_available = False

try:
    from . import qml
    _qml_available = True
except ImportError:
    _qml_available = False

try:
    from . import eels_analysis
    _eels_analysis_available = True
except ImportError:
    eels_analysis = None
    _eels_analysis_available = False

# Import key classes and functions for easy access (with fallbacks)
try:
    from .quantum_backend import QuantumBackendManager
    _backend_manager_available = True
except ImportError:
    _backend_manager_available = False

try:
    from .image_processing.quantum_encoding import (
        encode_image_to_circuit,
        EncodingMethod,
        validate_image_array,
        calculate_required_qubits
    )
    _encoding_available = True
except ImportError:
    _encoding_available = False

try:
    from .image_processing.preprocessing import (
        preprocess_image,
        binarize_image
    )
    _preprocessing_available = True
except ImportError:
    _preprocessing_available = False

try:
    from .qml.image_encoding import QuantumImageEncoder, encode_image_quantum
    _qml_encoding_available = True
except ImportError:
    _qml_encoding_available = False

__all__ = [
    # Version (always available)
    "__version__",
]

# Add modules if available
if _quantum_backend_available:
    __all__.append("quantum_backend")
if _image_processing_available:
    __all__.append("image_processing")
if _qml_available:
    __all__.append("qml")
if _eels_analysis_available:
    __all__.append("eels_analysis")

# Add classes if available
if _backend_manager_available:
    __all__.append("QuantumBackendManager")
if _qml_encoding_available:
    __all__.append("QuantumImageEncoder")

# Add functions if available
if _encoding_available:
    __all__.extend([
        "encode_image_to_circuit",
        "EncodingMethod",
        "validate_image_array",
        "calculate_required_qubits"
    ])
if _preprocessing_available:
    __all__.extend([
        "preprocess_image",
        "binarize_image"
    ])
if _qml_encoding_available:
    __all__.append("encode_image_quantum")
