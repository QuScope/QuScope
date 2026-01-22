"""Quantum image processing package for QuScope.

This package exposes core, lightweight helpers (preprocessing, encoding).
Optional components (segmentation, filtering, denoising) are imported
lazily / wrapped so importing the package remains safe in minimal
environments (no heavy optional dependencies installed).
"""

__all__ = []

# Core (lightweight) API
try:
    from .preprocessing import preprocess_image, binarize_image  # type: ignore
    _preprocessing_available = True
except Exception:
    _preprocessing_available = False

try:
    from .quantum_encoding import (
        encode_image_to_circuit,
        EncodingMethod,
        validate_image_array,
        calculate_required_qubits,
    )  # type: ignore
    _encoding_available = True
except Exception:
    _encoding_available = False

# Optional features (may depend on heavy libs). Wrap imports to avoid raising
# on package import when optional dependencies are absent.
try:
    from .quantum_segmentation import apply_grovers_algorithm, interpret_results  # type: ignore
    _segmentation_available = True
except Exception:
    _segmentation_available = False

try:
    from .filtering import quantum_edge_detection  # type: ignore
    _filtering_available = True
except Exception:
    _filtering_available = False

try:
    from . import image_denoising  # type: ignore
    _denoising_available = True
except Exception:
    _denoising_available = False

# Build __all__ only from symbols that were successfully imported
if _preprocessing_available:
    __all__.extend(["preprocess_image", "binarize_image"])
if _encoding_available:
    __all__.extend(
        [
            "encode_image_to_circuit",
            "EncodingMethod",
            "validate_image_array",
            "calculate_required_qubits",
        ]
    )
if _segmentation_available:
    __all__.extend(["apply_grovers_algorithm", "interpret_results"])
if _filtering_available:
    __all__.append("quantum_edge_detection")
if _denoising_available:
    __all__.append("image_denoising")
