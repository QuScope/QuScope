"""Quantum image encoding methods for quantum machine learning."""

import math

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import RYGate


class QuantumImageEncoder:
    """Quantum image encoder for machine learning applications."""

    def __init__(self, image_size=(4, 4)):
        """Initialize the quantum image encoder.

        Args:
            image_size (tuple): Size of the image to encode (height, width).
        """
        self.image_size = image_size
        self.num_qubits = int(math.log2(image_size[0] * image_size[1]))

    def encode_amplitude_encoding(self, img_array):
        """Encode image using amplitude encoding.

        Args:
            img_array (np.ndarray): Normalized image array (0-1).

        Returns:
            QuantumCircuit: Quantum circuit with amplitude-encoded image.
        """
        if img_array.shape != self.image_size:
            raise ValueError(
                f"Image shape {img_array.shape} doesn't match expected {self.image_size}"
            )

        # Flatten and normalize the image
        flat_image = img_array.flatten()
        norm = np.linalg.norm(flat_image)
        if norm > 0:
            normalized_amplitudes = flat_image / norm
        else:
            normalized_amplitudes = flat_image

        # Create quantum circuit
        circuit = QuantumCircuit(self.num_qubits)

        # Initialize state vector (simplified amplitude encoding)
        circuit.initialize(normalized_amplitudes, range(self.num_qubits))

        return circuit

    def encode_angle_encoding(self, img_array):
        """Encode image using angle encoding.

        Args:
            img_array (np.ndarray): Normalized image array (0-1).

        Returns:
            QuantumCircuit: Quantum circuit with angle-encoded image.
        """
        if img_array.shape != self.image_size:
            raise ValueError(
                f"Image shape {img_array.shape} doesn't match expected {self.image_size}"
            )

        # Flatten the image
        flat_image = img_array.flatten()

        # Create quantum circuit
        num_pixels = len(flat_image)
        num_qubits = max(1, int(math.ceil(math.log2(num_pixels))))
        circuit = QuantumCircuit(num_qubits)

        # Encode each pixel value as rotation angles
        for i, pixel_val in enumerate(flat_image[: 2**num_qubits]):
            if i < 2**num_qubits:
                # Map pixel value (0-1) to rotation angle (0-π)
                angle = pixel_val * math.pi
                if i < num_qubits:
                    circuit.ry(angle, i)

        return circuit


def encode_image_quantum(img_array, method="amplitude"):
    """Encode an image using quantum encoding methods.

    Args:
        img_array (np.ndarray): Input image array (normalized 0-1).
        method (str): Encoding method ('amplitude' or 'angle').

    Returns:
        QuantumCircuit: The quantum encoded circuit.
    """
    # Ensure image is 2D
    if img_array.ndim != 2:
        raise ValueError("Input image array must be 2D.")

    # Create encoder
    encoder = QuantumImageEncoder(img_array.shape)

    if method == "amplitude":
        return encoder.encode_amplitude_encoding(img_array)
    elif method == "angle":
        return encoder.encode_angle_encoding(img_array)
    else:
        raise ValueError(f"Unknown encoding method: {method}")
