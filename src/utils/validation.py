"""Validation utilities for quantum microscopy system."""

from typing import Any, Dict, List, Optional, Union

import numpy as np

from ..exceptions import ValidationError


def validate_positive_integer(value: Any, name: str) -> int:
    """Validate that value is a positive integer."""
    if not isinstance(value, int):
        raise ValidationError(f"{name} must be an integer, got {type(value)}")
    if value <= 0:
        raise ValidationError(f"{name} must be positive, got {value}")
    return value


def validate_probability_distribution(probs: Dict[str, float]) -> Dict[str, float]:
    """Validate probability distribution."""
    if not isinstance(probs, dict):
        raise ValidationError("Probabilities must be a dictionary")

    if not probs:
        raise ValidationError("Probability distribution cannot be empty")

    total = sum(probs.values())
    if not np.isclose(total, 1.0, rtol=1e-10):
        raise ValidationError(f"Probabilities must sum to 1.0, got {total}")

    for state, prob in probs.items():
        if not isinstance(prob, (int, float)):
            raise ValidationError(f"Probability for state {state} must be numeric")
        if prob < 0:
            raise ValidationError(f"Probability for state {state} cannot be negative")

    return probs


def validate_quantum_state(state: str, num_qubits: int) -> str:
    """Validate quantum state string."""
    if not isinstance(state, str):
        raise ValidationError("Quantum state must be a string")

    if len(state) != num_qubits:
        raise ValidationError(
            f"State length {len(state)} doesn't match qubits {num_qubits}"
        )

    if not all(bit in "01" for bit in state):
        raise ValidationError("State must contain only '0' and '1' characters")

    return state


def validate_range(
    value: Union[int, float],
    min_val: Union[int, float],
    max_val: Union[int, float],
    name: str,
) -> Union[int, float]:
    """Validate that value is within specified range."""
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{name} must be numeric")

    if value < min_val or value > max_val:
        raise ValidationError(
            f"{name} must be between {min_val} and {max_val}, got {value}"
        )

    return value
