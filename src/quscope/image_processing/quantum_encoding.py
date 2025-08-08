"""
Quantum encoding methods for image processing.

This module provides various methods for encoding classical image data into quantum
circuits, including amplitude encoding, basis encoding, angle encoding, and flexible
encoding. It supports both grayscale and multi-channel images with proper validation
and error handling.
"""

import logging
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union, Any, Callable

import numpy as np

# Optional heavy imports with fallbacks
try:
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
    from qiskit.circuit import Parameter
    from qiskit.exceptions import QiskitError
    from qiskit.quantum_info import Statevector
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False
    QuantumCircuit = None
    QiskitError = Exception

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

# Configure logging
logger = logging.getLogger(__name__)


class EncodingMethod(Enum):
    """Enumeration of supported quantum image encoding methods."""
    AMPLITUDE = "amplitude"
    BASIS = "basis"
    ANGLE = "angle"
    FLEXIBLE = "flexible"
    FRQI = "frqi"  # Flexible Representation of Quantum Images


class EncodingError(Exception):
    """Base exception for encoding errors."""
    pass


class InvalidImageError(EncodingError):
    """Exception raised for invalid image inputs."""
    pass


class EncodingDimensionError(EncodingError):
    """Exception raised when image dimensions are incompatible with encoding."""
    pass


def validate_image_array(
    img_array: np.ndarray, 
    allow_multichannel: bool = True
) -> Tuple[np.ndarray, bool]:
    """Validate and normalize an image array for quantum encoding.
    
    Args:
        img_array: Input image array.
        allow_multichannel: Whether to allow multi-channel images.
    
    Returns:
        Tuple containing:
            - Validated and normalized image array
            - Boolean indicating if the image is multi-channel
    
    Raises:
        InvalidImageError: If the image array is invalid.
    """
    # Check if array is valid
    if not isinstance(img_array, np.ndarray):
        raise InvalidImageError("Input must be a numpy array")
    
    if img_array.size == 0:
        raise InvalidImageError("Input array is empty")
    
    # Check dimensions
    if img_array.ndim not in [2, 3]:
        raise InvalidImageError(
            f"Image array must be 2D (grayscale) or 3D (multi-channel), got {img_array.ndim}D"
        )
    
    # Handle multi-channel images
    is_multichannel = img_array.ndim == 3
    if is_multichannel and not allow_multichannel:
        raise InvalidImageError(
            "Multi-channel images are not supported for this encoding method. "
            "Convert to grayscale first."
        )
    
    # Check if values are in valid range [0, 1]
    if np.min(img_array) < 0 or np.max(img_array) > 1:
        logger.warning(
            "Image values outside [0, 1] range. Normalizing to [0, 1]."
        )
        # Normalize to [0, 1]
        img_array = (img_array - np.min(img_array)) / (np.max(img_array) - np.min(img_array))
    
    return img_array, is_multichannel


def calculate_required_qubits(
    data_size: int, 
    encoding: EncodingMethod
) -> int:
    """Calculate the number of qubits required for encoding.
    
    Args:
        data_size: Number of data points to encode.
        encoding: Encoding method to use.
    
    Returns:
        Number of qubits required.
    
    Raises:
        EncodingDimensionError: If the encoding method is incompatible with the data size.
    """
    if encoding == EncodingMethod.AMPLITUDE:
        # For amplitude encoding, we need log2(data_size) qubits
        return int(np.ceil(np.log2(data_size)))
    
    elif encoding == EncodingMethod.BASIS:
        # For basis encoding, we need one qubit per data point
        return data_size
    
    elif encoding == EncodingMethod.ANGLE:
        # For angle encoding, we need one qubit per data point
        return data_size
    
    elif encoding == EncodingMethod.FLEXIBLE:
        # For flexible encoding, we need one qubit per data point
        return data_size
    
    elif encoding == EncodingMethod.FRQI:
        # For FRQI, we need log2(width*height) + 1 qubits
        position_qubits = int(np.ceil(np.log2(data_size)))
        color_qubits = 1  # One qubit for color information
        return position_qubits + color_qubits
    
    else:
        raise ValueError(f"Unsupported encoding method: {encoding}")


def encode_image_to_circuit(
    img_array: np.ndarray,
    method: Union[str, EncodingMethod] = EncodingMethod.AMPLITUDE,
    num_qubits: Optional[int] = None,
    add_measurements: bool = False,
    normalize: bool = True
) -> QuantumCircuit:
    """Encode an image into a quantum circuit using the specified method.
    
    Args:
        img_array: Input image array (normalized to [0, 1]).
        method: Encoding method to use.
        num_qubits: Number of qubits to use. If None, determined automatically.
        add_measurements: Whether to add measurement operations to the circuit.
        normalize: Whether to normalize the image array before encoding.
    
    Returns:
        Quantum circuit with encoded image.
    
    Raises:
        EncodingError: If encoding fails.
        InvalidImageError: If the image array is invalid.
        EncodingDimensionError: If the image dimensions are incompatible with the encoding.
    """
    # Convert string method to enum if needed
    if isinstance(method, str):
        try:
            method = EncodingMethod(method)
        except ValueError:
            raise ValueError(
                f"Invalid encoding method: {method}. "
                f"Supported methods: {[m.value for m in EncodingMethod]}"
            )
    
    # Validate image array
    try:
        img_array, is_multichannel = validate_image_array(
            img_array, 
            allow_multichannel=(method != EncodingMethod.BASIS)
        )
    except InvalidImageError as e:
        raise InvalidImageError(f"Image validation failed: {str(e)}")
    
    # Handle different encoding methods
    try:
        if method == EncodingMethod.AMPLITUDE:
            return _amplitude_encode_image(
                img_array, num_qubits, add_measurements, normalize
            )
        elif method == EncodingMethod.BASIS:
            if is_multichannel:
                raise InvalidImageError(
                    "Basis encoding only supports grayscale images. Convert to grayscale first."
                )
            return _basis_encode_image(
                img_array, add_measurements
            )
        elif method == EncodingMethod.ANGLE:
            return _angle_encode_image(
                img_array, num_qubits, add_measurements
            )
        elif method == EncodingMethod.FLEXIBLE:
            return _flexible_encode_image(
                img_array, num_qubits, add_measurements
            )
        elif method == EncodingMethod.FRQI:
            if is_multichannel:
                raise InvalidImageError(
                    "FRQI encoding currently only supports grayscale images. Convert to grayscale first."
                )
            return _frqi_encode_image(
                img_array, add_measurements
            )
        else:
            raise ValueError(f"Unsupported encoding method: {method}")
    except Exception as e:
        logger.error(f"Encoding failed: {str(e)}")
        raise EncodingError(f"Failed to encode image: {str(e)}")


def _amplitude_encode_image(
    img_array: np.ndarray,
    num_qubits: Optional[int] = None,
    add_measurements: bool = False,
    normalize: bool = True
) -> QuantumCircuit:
    """Encode an image into a quantum circuit using amplitude encoding.
    
    Args:
        img_array: Input image array (normalized to [0, 1]).
        num_qubits: Number of qubits to use. If None, determined automatically.
        add_measurements: Whether to add measurement operations to the circuit.
        normalize: Whether to normalize the image array before encoding.
    
    Returns:
        Quantum circuit with amplitude-encoded image.
    """
    # Flatten the image
    img_flat = img_array.flatten()
    
    # Normalize if requested
    if normalize:
        # Avoid division by zero
        norm = np.linalg.norm(img_flat)
        if norm < 1e-10:
            logger.warning("Image norm is close to zero. Using uniform amplitudes.")
            img_norm = np.ones_like(img_flat) / np.sqrt(len(img_flat))
        else:
            img_norm = img_flat / norm
    else:
        img_norm = img_flat
    
    # Calculate number of qubits needed if not specified
    if num_qubits is None:
        num_qubits = calculate_required_qubits(
            len(img_norm), EncodingMethod.AMPLITUDE
        )
    
    # Pad the vector if needed
    padded_length = 2**num_qubits
    if len(img_norm) < padded_length:
        logger.debug(
            f"Padding image vector from {len(img_norm)} to {padded_length} elements"
        )
        img_norm = np.pad(img_norm, (0, padded_length - len(img_norm)))
        
        # Renormalize after padding
        if normalize:
            norm = np.linalg.norm(img_norm)
            if norm > 1e-10:  # Avoid division by zero
                img_norm = img_norm / norm
    
    # Create quantum circuit
    qr = QuantumRegister(num_qubits, 'q')
    if add_measurements:
        cr = ClassicalRegister(num_qubits, 'c')
        circuit = QuantumCircuit(qr, cr)
    else:
        circuit = QuantumCircuit(qr)
    
    # Initialize with amplitude encoding
    try:
        circuit.initialize(img_norm, qr)
    except QiskitError as e:
        logger.error(f"Qiskit initialization error: {str(e)}")
        raise EncodingError(f"Failed to initialize quantum state: {str(e)}")
    
    # Add measurements if requested
    if add_measurements:
        circuit.measure(qr, cr)
    
    return circuit


def _basis_encode_image(
    img_array: np.ndarray,
    add_measurements: bool = False,
    threshold: float = 0.5
) -> QuantumCircuit:
    """Encode a binary image into a quantum circuit using basis states.
    
    Args:
        img_array: Binary image array with values in [0, 1].
        add_measurements: Whether to add measurement operations to the circuit.
        threshold: Threshold for binarization (if image is not already binary).
    
    Returns:
        Quantum circuit with basis-encoded binary image.
    """
    # Flatten and binarize the image
    img_flat = img_array.flatten()
    binary_img = (img_flat > threshold).astype(int)
    
    # Calculate number of qubits needed (one per pixel)
    n_qubits = len(binary_img)
    
    # Create quantum circuit
    qr = QuantumRegister(n_qubits, 'q')
    if add_measurements:
        cr = ClassicalRegister(n_qubits, 'c')
        circuit = QuantumCircuit(qr, cr)
    else:
        circuit = QuantumCircuit(qr)
    
    # Apply X gates where pixel value is 1
    for i, pixel in enumerate(binary_img):
        if pixel == 1:
            circuit.x(qr[i])
    
    # Add measurements if requested
    if add_measurements:
        circuit.measure(qr, cr)
    
    return circuit


def _angle_encode_image(
    img_array: np.ndarray,
    num_qubits: Optional[int] = None,
    add_measurements: bool = False
) -> QuantumCircuit:
    """Encode an image into a quantum circuit using angle encoding.
    
    In angle encoding, each pixel value is encoded as a rotation angle of a qubit.
    
    Args:
        img_array: Input image array (normalized to [0, 1]).
        num_qubits: Number of qubits to use. If None, uses one qubit per pixel.
        add_measurements: Whether to add measurement operations to the circuit.
    
    Returns:
        Quantum circuit with angle-encoded image.
    """
    # Flatten the image
    img_flat = img_array.flatten()
    
    # Determine number of qubits
    if num_qubits is None:
        num_qubits = len(img_flat)
    elif num_qubits < len(img_flat):
        logger.warning(
            f"Requested {num_qubits} qubits is less than the number of pixels ({len(img_flat)}). "
            "Some pixels will be omitted."
        )
        img_flat = img_flat[:num_qubits]
    elif num_qubits > len(img_flat):
        logger.warning(
            f"Requested {num_qubits} qubits is more than the number of pixels ({len(img_flat)}). "
            "Padding with zeros."
        )
        img_flat = np.pad(img_flat, (0, num_qubits - len(img_flat)))
    
    # Create quantum circuit
    qr = QuantumRegister(num_qubits, 'q')
    if add_measurements:
        cr = ClassicalRegister(num_qubits, 'c')
        circuit = QuantumCircuit(qr, cr)
    else:
        circuit = QuantumCircuit(qr)
    
    # Apply Hadamard gates to create superposition
    circuit.h(qr)
    
    # Apply rotation gates based on pixel values
    # Scale pixel values from [0, 1] to [0, π]
    for i, pixel in enumerate(img_flat):
        theta = pixel * np.pi
        circuit.ry(theta, qr[i])
    
    # Add measurements if requested
    if add_measurements:
        circuit.measure(qr, cr)
    
    return circuit


def _flexible_encode_image(
    img_array: np.ndarray,
    num_qubits: Optional[int] = None,
    add_measurements: bool = False
) -> QuantumCircuit:
    """Encode an image using a flexible encoding scheme with parameterized circuits.
    
    This encoding uses a combination of Hadamard and rotation gates with parameters
    that can be adjusted based on the image data.
    
    Args:
        img_array: Input image array (normalized to [0, 1]).
        num_qubits: Number of qubits to use. If None, uses one qubit per pixel.
        add_measurements: Whether to add measurement operations to the circuit.
    
    Returns:
        Quantum circuit with flexible encoding of the image.
    """
    # Flatten the image
    img_flat = img_array.flatten()
    
    # Determine number of qubits
    if num_qubits is None:
        num_qubits = len(img_flat)
    elif num_qubits < len(img_flat):
        logger.warning(
            f"Requested {num_qubits} qubits is less than the number of pixels ({len(img_flat)}). "
            "Some pixels will be omitted."
        )
        img_flat = img_flat[:num_qubits]
    elif num_qubits > len(img_flat):
        logger.warning(
            f"Requested {num_qubits} qubits is more than the number of pixels ({len(img_flat)}). "
            "Padding with zeros."
        )
        img_flat = np.pad(img_flat, (0, num_qubits - len(img_flat)))
    
    # Create quantum circuit
    qr = QuantumRegister(num_qubits, 'q')
    if add_measurements:
        cr = ClassicalRegister(num_qubits, 'c')
        circuit = QuantumCircuit(qr, cr)
    else:
        circuit = QuantumCircuit(qr)
    
    # Create parameters for the circuit
    params = [Parameter(f"θ_{i}") for i in range(len(img_flat))]
    
    # Apply Hadamard gates to create superposition
    circuit.h(qr)
    
    # Apply parameterized rotation gates
    for i, param in enumerate(params):
        circuit.ry(param, qr[i])
    
    # Bind parameters to pixel values (scaled to [0, π])
    param_dict = {param: pixel * np.pi for param, pixel in zip(params, img_flat)}
    bound_circuit = circuit.bind_parameters(param_dict)
    
    # Add measurements if requested
    if add_measurements:
        bound_circuit.measure(qr, cr)
    
    return bound_circuit


def _frqi_encode_image(
    img_array: np.ndarray,
    add_measurements: bool = False
) -> QuantumCircuit:
    """Encode an image using Flexible Representation of Quantum Images (FRQI).
    
    FRQI encodes both position and color information of an image into a quantum state.
    
    Args:
        img_array: Input grayscale image array (normalized to [0, 1]).
        add_measurements: Whether to add measurement operations to the circuit.
    
    Returns:
        Quantum circuit with FRQI encoding of the image.
    
    Raises:
        EncodingDimensionError: If the image dimensions are not powers of 2.
    """
    # Check if dimensions are powers of 2
    height, width = img_array.shape
    
    # Calculate required qubits for position encoding
    position_qubits = int(np.ceil(np.log2(height * width)))
    
    # Create quantum circuit
    qr_pos = QuantumRegister(position_qubits, 'pos')
    qr_color = QuantumRegister(1, 'color')
    
    if add_measurements:
        cr_pos = ClassicalRegister(position_qubits, 'c_pos')
        cr_color = ClassicalRegister(1, 'c_color')
        circuit = QuantumCircuit(qr_pos, qr_color, cr_pos, cr_color)
    else:
        circuit = QuantumCircuit(qr_pos, qr_color)
    
    # Create equal superposition of all position states
    circuit.h(qr_pos)
    
    # Encode color information
    img_flat = img_array.flatten()
    
    # Pad if necessary
    padded_length = 2**position_qubits
    if len(img_flat) < padded_length:
        img_flat = np.pad(img_flat, (0, padded_length - len(img_flat)))
    
    # Apply controlled rotations for each pixel
    for i, pixel_value in enumerate(img_flat):
        # Convert index to binary for control qubits
        bin_i = format(i, f'0{position_qubits}b')
        
        # Calculate rotation angle based on pixel value
        theta = 2 * np.arcsin(np.sqrt(pixel_value))
        
        # Create controlled rotation
        # We need to apply X gates to control qubits that should be |0⟩
        for j, bit in enumerate(bin_i):
            if bit == '0':
                circuit.x(qr_pos[j])
        
        # Apply controlled rotation
        circuit.cry(theta, qr_pos, qr_color[0])
        
        # Undo X gates
        for j, bit in enumerate(bin_i):
            if bit == '0':
                circuit.x(qr_pos[j])
    
    # Add measurements if requested
    if add_measurements:
        circuit.measure(qr_pos, cr_pos)
        circuit.measure(qr_color, cr_color)
    
    return circuit


def encode_binary_image(
    binary_img: np.ndarray,
    add_measurements: bool = False
) -> QuantumCircuit:
    """Encode a binary image into a quantum circuit using basis states.
    
    This is a wrapper around _basis_encode_image for backward compatibility.
    
    Args:
        binary_img: Binary image array with values 0 and 1.
        add_measurements: Whether to add measurement operations to the circuit.
        
    Returns:
        Quantum circuit with encoded binary image.
    """
    return _basis_encode_image(binary_img, add_measurements)


def analyze_encoding_resources(
    img_array: np.ndarray,
    methods: List[EncodingMethod] = None
) -> Dict[str, Dict[str, Any]]:
    """Analyze the resources required for different encoding methods.
    
    Args:
        img_array: Input image array.
        methods: List of encoding methods to analyze. If None, analyzes all methods.
        
    Returns:
        Dictionary with resource analysis for each encoding method.
    """
    if methods is None:
        methods = list(EncodingMethod)
    
    results = {}
    img_size = img_array.size
    
    for method in methods:
        try:
            # Calculate required qubits
            n_qubits = calculate_required_qubits(img_size, method)
            
            # Create a small test circuit to analyze
            circuit = encode_image_to_circuit(
                img_array, method=method, add_measurements=False
            )
            
            results[method.value] = {
                "qubits": n_qubits,
                "circuit_depth": circuit.depth(),
                "gate_counts": circuit.count_ops(),
                "total_gates": sum(circuit.count_ops().values()),
                "state_vector_size": 2**n_qubits,
                "classical_bits": n_qubits if method != EncodingMethod.FRQI else n_qubits + 1
            }
        except Exception as e:
            results[method.value] = {
                "error": str(e)
            }
    
    return results


def encode_multichannel_image(
    img_array: np.ndarray,
    method: Union[str, EncodingMethod] = EncodingMethod.AMPLITUDE,
    combine_channels: bool = False
) -> Union[QuantumCircuit, List[QuantumCircuit]]:
    """Encode a multi-channel image into quantum circuits.
    
    Args:
        img_array: Multi-channel image array (normalized to [0, 1]).
        method: Encoding method to use.
        combine_channels: Whether to combine all channels into a single circuit.
            If False, returns a list of circuits, one for each channel.
            
    Returns:
        Either a single quantum circuit (if combine_channels=True) or
        a list of quantum circuits, one for each channel.
    
    Raises:
        InvalidImageError: If the image is not multi-channel.
    """
    # Validate image is multi-channel
    if img_array.ndim != 3:
        raise InvalidImageError(
            "Input must be a multi-channel image (3D array)"
        )
    
    # Get number of channels
    height, width, channels = img_array.shape
    
    if combine_channels:
        # Reshape to single 2D array
        combined_img = img_array.reshape(height * width * channels)
        return encode_image_to_circuit(combined_img, method=method)
    else:
        # Encode each channel separately
        circuits = []
        for c in range(channels):
            channel_img = img_array[:, :, c]
            circuits.append(encode_image_to_circuit(channel_img, method=method))
        return circuits


def get_encoding_statevector(circuit: QuantumCircuit) -> np.ndarray:
    """Get the statevector representation of an encoded image.
    
    Args:
        circuit: Quantum circuit with encoded image.
        
    Returns:
        Numpy array containing the statevector.
    """
    # Remove measurements if present
    circuit_no_measure = circuit.copy()
    circuit_no_measure.remove_final_measurements()
    
    # Get statevector
    statevector = Statevector.from_instruction(circuit_no_measure)
    return statevector.data


def get_encoding_probabilities(circuit: QuantumCircuit) -> np.ndarray:
    """Get the measurement probabilities of an encoded image.
    
    Args:
        circuit: Quantum circuit with encoded image.
        
    Returns:
        Numpy array containing the measurement probabilities.
    """
    # Get statevector
    statevector = get_encoding_statevector(circuit)
    
    # Calculate probabilities
    probabilities = np.abs(statevector)**2
    return probabilities
