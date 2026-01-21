"""Custom exceptions for quantum microscopy system."""


class QuantumMicroscopyError(Exception):
    """Base exception for quantum microscopy errors."""

    pass


class QuantumCircuitError(QuantumMicroscopyError):
    """Raised when quantum circuit operations fail."""

    pass


class ProcessingError(QuantumMicroscopyError):
    """Raised when classical processing fails."""

    pass


class VisualizationError(QuantumMicroscopyError):
    """Raised when visualization operations fail."""

    pass


class ConfigurationError(QuantumMicroscopyError):
    """Raised when configuration is invalid."""

    pass


class ValidationError(QuantumMicroscopyError):
    """Raised when input validation fails."""

    pass
