"""
Quantum Transform Utilities for TEM Simulations

This module contains all quantum circuit operations for implementing
Quantum Fourier Transforms (QFT) and Inverse Quantum Fourier Transforms (iQFT).
"""

import numpy as np

# Optional Qiskit imports with graceful fallback
QISKIT_AVAILABLE = True
try:
    from qiskit import QuantumCircuit, QuantumRegister  # type: ignore
    from qiskit.circuit.library import QFT  # type: ignore
    try:
        from qiskit_aer import AerSimulator  # type: ignore
    except Exception:  # Aer may be a separate optional package
        AerSimulator = None  # type: ignore
    # Support both modern and legacy import paths for Statevector
    try:
        from qiskit.quantum_info import Statevector  # type: ignore
    except Exception:
        try:
            from qiskit.quantum.info import Statevector  # type: ignore
        except Exception:
            Statevector = None  # type: ignore
except Exception:
    QISKIT_AVAILABLE = False
    QuantumCircuit = QuantumRegister = QFT = AerSimulator = Statevector = None  # type: ignore


class TEMQFT:
    """
    Class containing quantum transform operations for CTEM simulations.
    """
    
    def __init__(self, n_qubits=8):
        """
        Initialize quantum transforms.
        
        Parameters:
        -----------
        n_qubits : int
            Number of qubits used for the circuit.
        """
        if not QISKIT_AVAILABLE or AerSimulator is None or Statevector is None:
            raise ImportError(
                "Qiskit and qiskit-aer are required for TEMQFT. Install with:"
                " pip install qiskit qiskit-aer"
            )
        self.n_qubits = n_qubits
        self.backend = AerSimulator()
        
    def encode_to_quantum_state(self, data_1d):
        """
        Encode classical 1D array into quantum state amplitudes.
        
        Parameters:
        -----------
        data_1d : np.ndarray
            1D numpy array of length 2^n_qubits to encode.
        
        Returns:
        --------
        circuit : QuantumCircuit
            Quantum circuit with encoded data.
        norm : float
            Normalization factor.
        """
        n = len(data_1d)
        if n != 2**self.n_qubits:
            raise ValueError(f"Data length {n} must equal 2^{self.n_qubits} = {2**self.n_qubits}")
        
        # Calculate norm for later restoration
        norm = np.linalg.norm(data_1d)
        
        # Handle zero or near-zero data
        if norm < 1e-10:
            # Create uniform superposition for zero data
            normalized_data = np.ones(n, dtype=complex) / np.sqrt(n)
            norm = 0.0  # Mark as zero for restoration
        else:
            normalized_data = data_1d / norm
        
        # Create quantum circuit and initialize
        qreg = QuantumRegister(self.n_qubits, 'q')
        circuit = QuantumCircuit(qreg)
        circuit.initialize(normalized_data, qreg)
        
        return circuit, norm
    
    def apply_qft(self, circuit, qubits):
        """
        Apply Quantum Fourier Transform to specified qubits.
        
        Parameters:
        -----------
        circuit : QuantumCircuit
            Quantum circuit.
        qubits : list
            List of qubit indices.
        
        Returns:
        --------
        circuit : QuantumCircuit
            Circuit with QFT applied.
        """
        qft = QFT(num_qubits=len(qubits), do_swaps=True)
        circuit.compose(qft, qubits, inplace=True)
        return circuit
    
    def apply_iqft(self, circuit, qubits):
        """
        Apply Inverse Quantum Fourier Transform to specified qubits.
        
        Parameters:
        -----------
        circuit : QuantumCircuit
            Quantum circuit.
        qubits : list
            List of qubit indices.
        
        Returns:
        --------
        circuit : QuantumCircuit
            Circuit with iQFT applied.
        """
        iqft = QFT(num_qubits=len(qubits), do_swaps=True).inverse()
        circuit.compose(iqft, qubits, inplace=True)
        return circuit
    
    def decode_quantum_state(self, circuit):
        """
        Decode quantum state back to classical data.
        
        Parameters:
        -----------
        circuit : QuantumCircuit
            Quantum circuit to decode.
        
        Returns:
        --------
        amplitudes : np.ndarray
            Complex array of amplitudes.
        """
        statevector = Statevector.from_instruction(circuit)
        amplitudes = statevector.data
        return amplitudes
    
    def qft_1d(self, data_1d):
        """
        Perform 1D QFT on classical data.
        
        Parameters:
        -----------
        data_1d : np.ndarray
            1D complex array.
        
        Returns:
        --------
        transformed_data : np.ndarray
            QFT result with proper normalization.
        """
        # Encode data
        circuit, norm = self.encode_to_quantum_state(data_1d)
        
        # Apply iQFT
        qubits = list(range(self.n_qubits))
        self.apply_qft(circuit, qubits)
        
        # Decode result
        amplitudes = self.decode_quantum_state(circuit)
        
        # Restore normalization (handle zero case)
        if norm == 0.0:
            return np.zeros_like(data_1d)
        else:
            # QFT includes 1/sqrt(N) factor in normalization
            # FFT convention does not have this
            N = len(data_1d)
            return amplitudes * norm * np.sqrt(N)
        
    def iqft_1d(self, data_1d):
        """
        Perform 1D iQFT on classical data.
        
        Parameters:
        -----------
        data_1d : np.ndarray
            1D complex array.
        
        Returns:
        --------
        transformed_data : np.ndarray
            iQFT result with proper normalization.
        """
        # Encode data
        circuit, norm = self.encode_to_quantum_state(data_1d)
        
        # Apply iQFT
        qubits = list(range(self.n_qubits))
        self.apply_iqft(circuit, qubits)
        
        # Decode result
        amplitudes = self.decode_quantum_state(circuit)
        
        # Restore normalization (handle zero case)
        if norm == 0.0:
            return np.zeros_like(data_1d)
        else:
            # QFT includes 1/sqrt(N) factor in normalization
            # FFT convention does not have this
            N = len(data_1d)
            return amplitudes * norm / np.sqrt(N)
        
    def qft_2d(self, data_2d, progress=False):
        """
        Perform 2D QFT using row-column decomposition.
        
        Parameters:
        -----------
        data_2d : np.ndarray
            2D complex array.
        progress : bool
            Print progress messages. Default is False.
        
        Returns:
        --------
        transformed_data : np.ndarray
            2D QFT result.
        """
        result = np.zeros_like(data_2d, dtype=complex)
        
        # QFT on rows
        if progress:
            print(f"  Applying QFT to {data_2d.shape[0]} rows...")
        for i in range(data_2d.shape[0]):
            if progress and i % 32 == 0:
                print(f"    Row {i}/{data_2d.shape[0]}")
            result[i, :] = self.qft_1d(data_2d[i, :])
        
        # QFT on columns
        if progress:
            print(f"  Applying QFT to {data_2d.shape[1]} columns...")
        for j in range(data_2d.shape[1]):
            if progress and j % 32 == 0:
                print(f"    Column {j}/{data_2d.shape[1]}")
            result[:, j] = self.qft_1d(result[:, j])
            
        return result
    
    def iqft_2d(self, data_2d, progress=False):
        """
        Perform 2D iQFT using row-column decomposition.
        
        Parameters:
        -----------
        data_2d : np.ndarray
            2D complex array.
        progress : bool
            Print progress message. Default is False.
        
        Returns:
        --------
        transformed_data : np.ndarray
            2D iQFT result.
        """
        result = np.zeros_like(data_2d, dtype=complex)
        
        # iQFT on rows
        if progress:
            print(f"  Applying iQFT to {data_2d.shape[0]} rows...")
        for i in range(data_2d.shape[0]):
            if progress and i % 32 == 0:
                print(f"    Row {i}/{data_2d.shape[0]}")
            result[i, :] = self.iqft_1d(data_2d[i, :])
        
        # iQFT on columns
        if progress:
            print(f"  Applying iQFT to {data_2d.shape[1]} columns...")
        for j in range(data_2d.shape[1]):
            if progress and j % 32 == 0:
                print(f"    Column {j}/{data_2d.shape[1]}")
            result[:, j] = self.iqft_1d(result[:, j])
            
        return result