"""Quantum Machine Learning module for microscopy data."""

# Lazy import to avoid hard dependency on heavy optional libraries (torch, piqture)
import importlib
from types import ModuleType

__all__ = [
    'encode_image_ineqr',
]


def __getattr__(name: str):  # noqa: D401
    """Dynamically resolve optional symbols.

    We expose ``encode_image_ineqr`` only when the optional
    dependencies are available.  This keeps ``import quscope`` fast and
    lightweight for users that are not interested in the QML sub-module.
    """
    if name == 'encode_image_ineqr':
        try:
            module: ModuleType = importlib.import_module('.image_encoding', __name__)
            return getattr(module, name)
        except Exception as import_exc:  # pragma: no cover – forward the original error lazily
            # Capture the exception in the closure
            captured_exc = import_exc
            def _stub(*_args, **_kwargs):  # type: ignore
                raise ImportError(
                    'INEQR encoding requires optional dependencies (torch, piqture).\n'
                    'Install them with:\n\n'
                    '    pip install "quscope[piqture,torch]"\n'
                ) from captured_exc
            return _stub
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
