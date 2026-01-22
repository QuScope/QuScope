"""Quantum Machine Learning module for microscopy data (lightweight lazy imports)."""

import importlib
from types import ModuleType

__all__ = []

def __getattr__(name: str):  # noqa: D401
    if name == "encode_image_ineqr":  # adjust this name to the real exported symbol if different
        try:
            module: ModuleType = importlib.import_module(".image_encoding", __name__)
            return getattr(module, name)
        except Exception as import_exc:  # pragma: no cover – forward the original error lazily
            captured_exc = import_exc
            def _stub(*_args, **_kwargs):  # type: ignore
                raise ImportError(
                    'Requested QML functionality requires optional dependencies.\n'
                    'Install extras with:\n\n'
                    '    pip install "quscope[piqture,torch]"\n'
                ) from captured_exc
            return _stub
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
