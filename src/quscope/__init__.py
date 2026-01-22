"""
QuScope: Quantum algorithms for microscopy image processing and EELS analysis.

This top-level package keeps imports lightweight: optional heavy submodules are
imported lazily or wrapped to avoid raising on a plain `import quscope`.
"""

from importlib.metadata import version as _pkg_version, PackageNotFoundError as _PkgNotFoundError

try:
    __version__ = _pkg_version("quscope")
except _PkgNotFoundError:
    __version__ = "0.1.0+dev"

# Avoid unconditional imports of subpackages here to keep `import quscope`
# light and robust in minimal environments. Consumers can import subpackages
# explicitly (e.g., `from quscope.image_processing import ...`).

# Provide convenient access to frequently used functions if available.
# Wrap imports to avoid raising at import time if optional dependencies are missing.
try:
    from .image_processing.quantum_encoding import (  # type: ignore
        encode_image_to_circuit,
        EncodingMethod,
        validate_image_array,
        calculate_required_qubits,
    )
    _encoding_available = True
except Exception:
    # These names will not be present if the import failed; callers should import
    # directly from submodules if needed.
    _encoding_available = False
    encode_image_to_circuit = None
    EncodingMethod = None
    validate_image_array = None
    calculate_required_qubits = None

try:
    from .image_processing.preprocessing import preprocess_image, binarize_image  # type: ignore
    _preprocessing_available = True
except Exception:
    _preprocessing_available = False
    preprocess_image = None
    binarize_image = None

# Do not import heavy optional subpackages (qml, eels_analysis) eagerly.
# Leave them for explicit import by the user or lazy access via __getattr__.

__all__ = [
    "__version__",
]

# Add core symbols conditionally
if _encoding_available:
    __all__.extend(
        [
            "encode_image_to_circuit",
            "EncodingMethod",
            "validate_image_array",
            "calculate_required_qubits",
        ]
    )
if _preprocessing_available:
    __all__.extend(["preprocess_image", "binarize_image"])

# Lazy access for backend to avoid import-time side effects (keep existing behavior)
def __getattr__(name):
    if name == "QuantumBackendManager" or name == "quantum_backend":
        import importlib
        _qb = importlib.import_module(".quantum_backend", __name__)
        if name == "QuantumBackendManager":
            return _qb.QuantumBackendManager
        return _qb
    raise AttributeError(f"module 'quscope' has no attribute {name!r}")
