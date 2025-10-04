"""
Quantum Wave Function Representation for Pure Quantum CTEM

This module implements quantum encoding of electron wave functions for
pure quantum Bloch wave simulation. The wave function ψ(x,y) is represented
as a quantum state |ψ⟩ using amplitude encoding.

Physical Principle:
    Classical wave function: ψ(x,y) = A(x,y) exp(iφ(x,y))
    Quantum encoding: |ψ⟩ = Σ_{x,y} ψ(x,y)|x⟩|y⟩
    
This is the foundation for Phase 1 of the pure quantum CTEM development.

References:
    - Le, P. Q., et al. (2011). "Quantum image processing." 
      Quantum Information Processing, 10(1), 63-89.
    - Schuld, M., & Petruccione, F. (2021). "Machine Learning with Quantum Computers."
      Chapter 3: Quantum Feature Maps and Kernels.

Author: QuScope Development Team
Date: October 3, 2025
Phase: 1.1 - Quantum State Encoding
"""

import numpy as np
from typing import Tuple, Optional, Dict
from qiskit import QuantumCircuit, QuantumRegister
from qiskit.quantum_info import Statevector
from qiskit.circuit.library import QFT


class QuantumWaveFunction:
    """
    Pure quantum representation of electron wave function.
    
    This class provides methods to encode classical wave functions ψ(x,y)
    as quantum states and decode quantum states back to classical arrays.
    
    The encoding uses amplitude encoding where the complex values of ψ(x,y)
    directly become the amplitudes of quantum basis states |xy⟩.
    
    Attributes:
        n_qubits_x (int): Number of qubits for x dimension
        n_qubits_y (int): Number of qubits for y dimension
        pixels_x (int): Number of pixels in x (2^n_qubits_x)
        pixels_y (int): Number of pixels in y (2^n_qubits_y)
        total_qubits (int): Total qubits needed (n_qubits_x + n_qubits_y)
        
    Example:
        >>> # Create quantum wave function for 8×8 image
        >>> qwf = QuantumWaveFunction(n_qubits_x=3, n_qubits_y=3)
        >>> 
        >>> # Prepare incident plane wave
        >>> circuit = qwf.prepare_incident_wave()
        >>> 
        >>> # Extract wave function
        >>> psi = qwf.extract_wave(circuit)
        >>> print(psi.shape)  # (8, 8)
    """
    
    def __init__(self, n_qubits_x: int, n_qubits_y: int):
        """
        Initialize quantum wave function representation.
        
        Parameters:
            n_qubits_x: Number of qubits for x spatial dimension
            n_qubits_y: Number of qubits for y spatial dimension
        
        Raises:
            ValueError: If n_qubits_x or n_qubits_y < 1
        """
        if n_qubits_x < 1 or n_qubits_y < 1:
            raise ValueError(f"Number of qubits must be >= 1, got x={n_qubits_x}, y={n_qubits_y}")
        
        self.n_qubits_x = n_qubits_x
        self.n_qubits_y = n_qubits_y
        self.pixels_x = 2**n_qubits_x
        self.pixels_y = 2**n_qubits_y
        self.total_qubits = n_qubits_x + n_qubits_y
        
        # Storage for normalization factor (used during encoding/decoding)
        self._stored_norm = 1.0
        
        # Qubit registers for clarity
        self.x_qubits = list(range(n_qubits_x))
        self.y_qubits = list(range(n_qubits_x, self.total_qubits))
    
    def prepare_incident_wave(self) -> QuantumCircuit:
        """
        Prepare incident plane wave state.
        
        For normal incidence CTEM, the incident wave is a plane wave:
        ψ₀(x,y) = 1 (constant everywhere)
        
        In quantum representation:
        |ψ₀⟩ = 1/√N Σ_{x,y} |xy⟩
        
        This is a uniform superposition over all spatial positions,
        created by applying Hadamard gates to all qubits.
        
        Returns:
            QuantumCircuit with incident plane wave prepared
            
        Example:
            >>> qwf = QuantumWaveFunction(3, 3)
            >>> circuit = qwf.prepare_incident_wave()
            >>> psi = qwf.extract_wave(circuit)
            >>> # psi should be uniform with value 1/√64
        """
        qc = QuantumCircuit(self.total_qubits, name='incident_wave')
        
        # Apply Hadamard to all qubits → uniform superposition
        # H|0⟩ = 1/√2(|0⟩ + |1⟩)
        # H^⊗n|0⟩^⊗n = 1/√(2^n) Σ|x⟩
        qc.h(range(self.total_qubits))
        
        # Store normalization (uniform plane wave has amplitude 1)
        self._stored_norm = 1.0
        
        return qc
    
    def prepare_arbitrary_wave(
        self, 
        psi_classical: np.ndarray,
        validate_shape: bool = True
    ) -> QuantumCircuit:
        """
        Prepare arbitrary complex wave function.
        
        Encodes a classical wave function ψ(x,y) into quantum state:
        |ψ⟩ = Σ_{x,y} ψ(x,y)|xy⟩
        
        The wave function is automatically normalized for quantum encoding,
        and the normalization factor is stored for later reconstruction.
        
        Parameters:
            psi_classical: Complex 2D array of shape (pixels_x, pixels_y)
            validate_shape: Check if input shape matches expected dimensions
        
        Returns:
            QuantumCircuit with wave function prepared
            
        Raises:
            ValueError: If shape doesn't match (pixels_x, pixels_y)
            
        Example:
            >>> # Gaussian wave packet
            >>> x = np.linspace(-4, 4, 8)
            >>> X, Y = np.meshgrid(x, x)
            >>> psi = np.exp(-(X**2 + Y**2)/2) * np.exp(1j * np.pi/4)
            >>> 
            >>> qwf = QuantumWaveFunction(3, 3)
            >>> circuit = qwf.prepare_arbitrary_wave(psi)
            >>> psi_decoded = qwf.extract_wave(circuit)
            >>> # psi_decoded should match psi (up to global phase)
        """
        # Validate input shape
        if validate_shape:
            expected_shape = (self.pixels_x, self.pixels_y)
            if psi_classical.shape != expected_shape:
                raise ValueError(
                    f"Wave function shape {psi_classical.shape} doesn't match "
                    f"expected {expected_shape}"
                )
        
        # Flatten to 1D for quantum encoding
        psi_flat = psi_classical.flatten()
        
        # Calculate norm
        norm = np.linalg.norm(psi_flat)
        
        # Create circuit
        qc = QuantumCircuit(self.total_qubits, name='arbitrary_wave')
        
        if norm < 1e-10:
            # Zero wave function → prepare uniform superposition as default
            qc.h(range(self.total_qubits))
            self._stored_norm = 0.0
        else:
            # Normalize for quantum state (amplitudes must have norm 1)
            psi_normalized = psi_flat / norm
            
            # Initialize quantum state with these amplitudes
            # This uses Qiskit's initialize() which finds an efficient
            # gate decomposition to prepare the desired state
            qc.initialize(psi_normalized, range(self.total_qubits))
            
            # Store normalization for later reconstruction
            self._stored_norm = norm
        
        return qc
    
    def extract_wave(self, circuit: QuantumCircuit) -> np.ndarray:
        """
        Extract classical wave function from quantum circuit.
        
        Decodes the quantum state back into a classical complex array.
        This uses statevector simulation to get the amplitudes, then
        reshapes and denormalizes to recover the original wave function.
        
        Note: This operation requires a quantum statevector simulator
        and is exponentially expensive. In real quantum hardware, this
        would be replaced by tomography or other measurement protocols.
        
        Parameters:
            circuit: QuantumCircuit containing the quantum state
        
        Returns:
            Complex 2D array of shape (pixels_x, pixels_y)
            
        Example:
            >>> qwf = QuantumWaveFunction(3, 3)
            >>> circuit = qwf.prepare_incident_wave()
            >>> psi = qwf.extract_wave(circuit)
            >>> assert psi.shape == (8, 8)
            >>> # For plane wave, all values should be equal
            >>> assert np.allclose(np.abs(psi), np.abs(psi[0, 0]))
        """
        # Get statevector (quantum state amplitudes)
        statevector = Statevector.from_instruction(circuit)
        amplitudes = statevector.data
        
        # Denormalize (multiply by stored norm)
        amplitudes *= self._stored_norm
        
        # Reshape to 2D image
        psi_2d = amplitudes.reshape(self.pixels_x, self.pixels_y)
        
        return psi_2d
    
    def get_normalization_factor(self) -> float:
        """
        Get the stored normalization factor.
        
        Returns:
            Normalization factor from last encoding operation
        """
        return self._stored_norm
    
    def create_2d_qft_circuit(self) -> QuantumCircuit:
        """
        Create 2D Quantum Fourier Transform circuit.
        
        Applies QFT separately to x and y dimensions:
        QFT₂D = QFT_x ⊗ QFT_y
        
        This transforms real-space wave function to momentum space:
        |ψ(x,y)⟩ → |ψ(kₓ,k_y)⟩
        
        Returns:
            QuantumCircuit implementing 2D QFT
            
        Example:
            >>> qwf = QuantumWaveFunction(3, 3)
            >>> qft_circuit = qwf.create_2d_qft_circuit()
            >>> 
            >>> # Apply to plane wave
            >>> psi_circuit = qwf.prepare_incident_wave()
            >>> psi_circuit.compose(qft_circuit, inplace=True)
            >>> 
            >>> # Extract momentum space wave function
            >>> psi_k = qwf.extract_wave(psi_circuit)
        """
        qc = QuantumCircuit(self.total_qubits, name='QFT_2D')
        
        # QFT on x qubits
        qft_x = QFT(self.n_qubits_x, do_swaps=True)
        qc.compose(qft_x, self.x_qubits, inplace=True)
        
        # QFT on y qubits
        qft_y = QFT(self.n_qubits_y, do_swaps=True)
        qc.compose(qft_y, self.y_qubits, inplace=True)
        
        return qc
    
    def create_2d_iqft_circuit(self) -> QuantumCircuit:
        """
        Create 2D Inverse Quantum Fourier Transform circuit.
        
        Inverse of QFT₂D, transforms momentum space back to real space:
        |ψ(kₓ,k_y)⟩ → |ψ(x,y)⟩
        
        Returns:
            QuantumCircuit implementing 2D IQFT
        """
        qft_2d = self.create_2d_qft_circuit()
        iqft_2d = qft_2d.inverse()
        iqft_2d.name = 'IQFT_2D'
        return iqft_2d
    
    def get_info(self) -> Dict[str, any]:
        """
        Get information about the quantum wave function configuration.
        
        Returns:
            Dictionary with configuration parameters
        """
        return {
            'n_qubits_x': self.n_qubits_x,
            'n_qubits_y': self.n_qubits_y,
            'total_qubits': self.total_qubits,
            'pixels_x': self.pixels_x,
            'pixels_y': self.pixels_y,
            'total_pixels': self.pixels_x * self.pixels_y,
            'hilbert_space_dimension': 2**self.total_qubits,
            'stored_norm': self._stored_norm,
        }
    
    def __repr__(self) -> str:
        """String representation of the quantum wave function."""
        return (
            f"QuantumWaveFunction("
            f"n_qubits_x={self.n_qubits_x}, "
            f"n_qubits_y={self.n_qubits_y}, "
            f"pixels={self.pixels_x}×{self.pixels_y}, "
            f"total_qubits={self.total_qubits})"
        )
