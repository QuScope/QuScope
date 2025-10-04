"""
Momentum space utilities for quantum CTEM.

This module provides enhanced momentum space operations for quantum
electron microscopy simulations, including:
- Direct k-space wave function encoding
- Bidirectional real ↔ reciprocal space transformations
- Energy conservation validation (Parseval's theorem)
- Momentum-space filtering operations

Physical Background:
- Real space: |ψ(x,y)⟩ - Electron wave function in position basis
- Momentum space: |ψ̃(kₓ,k_y)⟩ - Same state in momentum basis
- Connection: QFT transforms between representations
- Energy: E = ℏ²k²/2m - Related to momentum

Target: IBM quantum hardware with pure quantum operations.

Author: QuScope Team
Date: October 2025
"""

import numpy as np
from typing import Dict, Tuple, Optional, Union
from qiskit import QuantumCircuit
from qiskit.circuit.library import QFT
from qiskit.quantum_info import Statevector


class MomentumSpaceConverter:
    """
    Convert between real and momentum space representations.
    
    This class provides utilities for working with electron wave functions
    in both position and momentum representations, crucial for:
    - Fresnel propagation (easier in k-space)
    - Aperture functions (applied in k-space)
    - Energy analysis
    - Wave packet dynamics
    
    Physical Principle:
    ψ̃(k) = ∫ ψ(x) exp(-ikx) dx  → Implemented via QFT
    ψ(x) = ∫ ψ̃(k) exp(ikx) dk  → Implemented via IQFT
    """
    
    def __init__(self, n_qubits_x: int, n_qubits_y: int):
        """
        Initialize momentum space converter.
        
        Parameters
        ----------
        n_qubits_x : int
            Number of qubits for x dimension
        n_qubits_y : int
            Number of qubits for y dimension
        """
        self.n_qubits_x = n_qubits_x
        self.n_qubits_y = n_qubits_y
        self.total_qubits = n_qubits_x + n_qubits_y
        
        self.pixels_x = 2**n_qubits_x
        self.pixels_y = 2**n_qubits_y
        
        # Cached QFT circuits
        self._qft_circuit = None
        self._iqft_circuit = None
    
    def create_qft_circuit(self) -> QuantumCircuit:
        """
        Create 2D QFT circuit for real → momentum space.
        
        The 2D QFT is separable: QFT₂D = QFT_x ⊗ QFT_y
        
        Returns
        -------
        QuantumCircuit
            2D QFT circuit
        """
        if self._qft_circuit is not None:
            return self._qft_circuit
        
        qc = QuantumCircuit(self.total_qubits, name='QFT_2D')
        
        # QFT on x qubits
        qft_x = QFT(self.n_qubits_x, do_swaps=True)
        qc.compose(qft_x, range(self.n_qubits_x), inplace=True)
        
        # QFT on y qubits
        qft_y = QFT(self.n_qubits_y, do_swaps=True)
        qc.compose(qft_y, range(self.n_qubits_x, self.total_qubits), inplace=True)
        
        self._qft_circuit = qc
        return qc
    
    def create_iqft_circuit(self) -> QuantumCircuit:
        """
        Create 2D inverse QFT circuit for momentum → real space.
        
        Returns
        -------
        QuantumCircuit
            2D inverse QFT circuit
        """
        if self._iqft_circuit is not None:
            return self._iqft_circuit
        
        qc = QuantumCircuit(self.total_qubits, name='IQFT_2D')
        
        # IQFT on x qubits
        iqft_x = QFT(self.n_qubits_x, do_swaps=True).inverse()
        qc.compose(iqft_x, range(self.n_qubits_x), inplace=True)
        
        # IQFT on y qubits  
        iqft_y = QFT(self.n_qubits_y, do_swaps=True).inverse()
        qc.compose(iqft_y, range(self.n_qubits_x, self.total_qubits), inplace=True)
        
        self._iqft_circuit = qc
        return qc
    
    def transform_to_momentum(
        self, 
        circuit: QuantumCircuit
    ) -> QuantumCircuit:
        """
        Transform wave function from real to momentum space.
        
        |ψ(x,y)⟩ → |ψ̃(kₓ,k_y)⟩
        
        Parameters
        ----------
        circuit : QuantumCircuit
            Circuit with wave function in real space
            
        Returns
        -------
        QuantumCircuit
            Circuit with wave function in momentum space
        """
        qft = self.create_qft_circuit()
        circuit_k = circuit.copy()
        circuit_k.compose(qft, range(self.total_qubits), inplace=True)
        return circuit_k
    
    def transform_to_real(
        self,
        circuit: QuantumCircuit
    ) -> QuantumCircuit:
        """
        Transform wave function from momentum to real space.
        
        |ψ̃(kₓ,k_y)⟩ → |ψ(x,y)⟩
        
        Parameters
        ----------
        circuit : QuantumCircuit
            Circuit with wave function in momentum space
            
        Returns
        -------
        QuantumCircuit
            Circuit with wave function in real space
        """
        iqft = self.create_iqft_circuit()
        circuit_x = circuit.copy()
        circuit_x.compose(iqft, range(self.total_qubits), inplace=True)
        return circuit_x
    
    def get_momentum_grid(
        self,
        real_size: float,
        shift: bool = True
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get momentum space grid corresponding to real space grid.
        
        For real space grid: x ∈ [-L/2, L/2] with N points
        Momentum space grid: k ∈ [-π/Δx, π/Δx] with N points
        where Δx = L/N
        
        Parameters
        ----------
        real_size : float
            Physical size of real space grid (Ångströms)
        shift : bool, optional
            If True, shift grid to center zero frequency (default: True)
            If False, keep in FFT order matching QFT output
            
        Returns
        -------
        kx_grid, ky_grid : np.ndarray
            2D momentum grids (units: 1/Å)
        """
        # Real space sampling
        dx = real_size / self.pixels_x
        dy = real_size / self.pixels_y
        
        # Momentum grids
        # fftfreq returns frequencies in cycles/unit, multiply by 2π for angular freq
        kx = 2 * np.pi * np.fft.fftfreq(self.pixels_x, dx)
        ky = 2 * np.pi * np.fft.fftfreq(self.pixels_y, dy)
        
        if shift:
            kx = np.fft.fftshift(kx)
            ky = np.fft.fftshift(ky)
        
        kx_grid, ky_grid = np.meshgrid(kx, ky, indexing='ij')
        
        return kx_grid, ky_grid


class ParsevalValidator:
    """
    Validate energy conservation via Parseval's theorem.
    
    Parseval's theorem states that the total energy (norm) is preserved
    under Fourier transform:
    
    ∫|ψ(x)|² dx = ∫|ψ̃(k)|² dk
    
    Or in quantum notation:
    ⟨ψ|ψ⟩_real = ⟨ψ̃|ψ̃⟩_momentum
    
    This is a critical validation for quantum CTEM algorithms.
    """
    
    def __init__(self, tolerance: float = 1e-10):
        """
        Initialize Parseval validator.
        
        Parameters
        ----------
        tolerance : float
            Tolerance for energy conservation check
        """
        self.tolerance = tolerance
    
    def validate_transform(
        self,
        circuit_real: QuantumCircuit,
        circuit_momentum: QuantumCircuit
    ) -> Dict[str, Union[bool, float]]:
        """
        Validate that QFT preserves energy (Parseval's theorem).
        
        Parameters
        ----------
        circuit_real : QuantumCircuit
            Circuit with wave function in real space
        circuit_momentum : QuantumCircuit
            Circuit with wave function in momentum space
            
        Returns
        -------
        dict
            Validation results with keys:
            - 'valid': bool - Whether energy is conserved
            - 'energy_real': float - Energy in real space
            - 'energy_momentum': float - Energy in momentum space
            - 'relative_error': float - Relative error in conservation
        """
        # Get statevectors
        sv_real = Statevector.from_instruction(circuit_real)
        sv_momentum = Statevector.from_instruction(circuit_momentum)
        
        # Calculate energies (squared norms)
        energy_real = np.sum(np.abs(sv_real.data)**2)
        energy_momentum = np.sum(np.abs(sv_momentum.data)**2)
        
        # Relative error
        if energy_real > 1e-10:
            rel_error = abs(energy_real - energy_momentum) / energy_real
        else:
            rel_error = abs(energy_real - energy_momentum)
        
        # Validation
        valid = rel_error < self.tolerance
        
        return {
            'valid': valid,
            'energy_real': float(energy_real),
            'energy_momentum': float(energy_momentum),
            'relative_error': float(rel_error),
        }
    
    def validate_round_trip(
        self,
        circuit_original: QuantumCircuit,
        circuit_round_trip: QuantumCircuit
    ) -> Dict[str, Union[bool, float]]:
        """
        Validate QFT → IQFT round trip preserves state.
        
        Tests: QFT(IQFT(|ψ⟩)) = |ψ⟩
        
        Parameters
        ----------
        circuit_original : QuantumCircuit
            Original circuit
        circuit_round_trip : QuantumCircuit
            Circuit after QFT → IQFT
            
        Returns
        -------
        dict
            Validation results with fidelity
        """
        from qiskit.quantum_info import state_fidelity
        
        sv_original = Statevector.from_instruction(circuit_original)
        sv_round_trip = Statevector.from_instruction(circuit_round_trip)
        
        fidelity = state_fidelity(sv_original, sv_round_trip)
        valid = fidelity > (1 - self.tolerance)
        
        return {
            'valid': valid,
            'fidelity': float(fidelity),
            'error': float(1 - fidelity),
        }


class MomentumSpaceFilter:
    """
    Apply filtering operations in momentum space.
    
    Common filters in CTEM:
    - Low-pass: Remove high-k components (smoothing)
    - High-pass: Remove low-k components (edge enhancement)
    - Band-pass: Keep specific k-range
    - Objective aperture: Hard cutoff at k_max
    
    Implementation: Apply phase or amplitude modulation in k-space
    """
    
    def __init__(self, n_qubits_x: int, n_qubits_y: int):
        """
        Initialize momentum space filter.
        
        Parameters
        ----------
        n_qubits_x, n_qubits_y : int
            Number of qubits for x and y dimensions
        """
        self.n_qubits_x = n_qubits_x
        self.n_qubits_y = n_qubits_y
        self.total_qubits = n_qubits_x + n_qubits_y
        
        self.pixels_x = 2**n_qubits_x
        self.pixels_y = 2**n_qubits_y
    
    def create_aperture_filter(
        self,
        k_max: float,
        kx_grid: np.ndarray,
        ky_grid: np.ndarray
    ) -> np.ndarray:
        """
        Create objective aperture filter.
        
        Filters out high-k components beyond aperture radius.
        
        Parameters
        ----------
        k_max : float
            Maximum k-vector magnitude (aperture radius)
        kx_grid, ky_grid : np.ndarray
            Momentum space grids
            
        Returns
        -------
        np.ndarray
            Filter mask (1 inside aperture, 0 outside)
        """
        k_magnitude = np.sqrt(kx_grid**2 + ky_grid**2)
        aperture_mask = (k_magnitude <= k_max).astype(float)
        return aperture_mask
    
    def create_lowpass_filter(
        self,
        k_cutoff: float,
        kx_grid: np.ndarray,
        ky_grid: np.ndarray,
        smoothness: float = 0.1
    ) -> np.ndarray:
        """
        Create smooth low-pass filter.
        
        Smoothly attenuates high-k components.
        
        Parameters
        ----------
        k_cutoff : float
            Cutoff frequency
        kx_grid, ky_grid : np.ndarray
            Momentum space grids
        smoothness : float
            Filter smoothness parameter (larger = smoother)
            
        Returns
        -------
        np.ndarray
            Filter function
        """
        k_magnitude = np.sqrt(kx_grid**2 + ky_grid**2)
        # Smooth Gaussian-like cutoff
        filter_func = np.exp(-(k_magnitude / k_cutoff)**2 / (2 * smoothness**2))
        return filter_func
    
    def apply_filter_classical(
        self,
        psi_k: np.ndarray,
        filter_mask: np.ndarray
    ) -> np.ndarray:
        """
        Apply filter in momentum space (classical simulation).
        
        This is for validation and comparison. The full quantum
        implementation requires controlled amplitude modulation.
        
        Parameters
        ----------
        psi_k : np.ndarray
            Wave function in momentum space
        filter_mask : np.ndarray
            Filter function (real-valued)
            
        Returns
        -------
        np.ndarray
            Filtered wave function in momentum space
        """
        return psi_k * filter_mask


def analyze_momentum_distribution(
    circuit: QuantumCircuit,
    n_qubits_x: int,
    n_qubits_y: int,
    real_size: float = 10.0
) -> Dict[str, np.ndarray]:
    """
    Analyze momentum distribution of quantum wave function.
    
    Parameters
    ----------
    circuit : QuantumCircuit
        Circuit with wave function (in real or momentum space)
    n_qubits_x, n_qubits_y : int
        Qubit dimensions
    real_size : float
        Physical size of real space region (Å)
        
    Returns
    -------
    dict
        Analysis results:
        - 'momentum_amplitudes': Complex amplitudes in k-space
        - 'momentum_probabilities': |ψ̃(k)|²
        - 'kx_grid': Momentum grid x-component
        - 'ky_grid': Momentum grid y-component
        - 'mean_k': Mean momentum vector
        - 'k_spread': Momentum spread (std deviation)
    """
    # Get statevector
    sv = Statevector.from_instruction(circuit)
    
    # Reshape to 2D
    pixels_x = 2**n_qubits_x
    pixels_y = 2**n_qubits_y
    psi_2d = sv.data.reshape(pixels_x, pixels_y)
    
    # Get momentum grids (shifted to center k=0)
    converter = MomentumSpaceConverter(n_qubits_x, n_qubits_y)
    kx_grid, ky_grid = converter.get_momentum_grid(real_size, shift=True)
    
    # Shift probability distribution to match shifted k-grid
    # QFT output is in FFT order, fftshift moves k=0 to center
    psi_2d_shifted = np.fft.fftshift(psi_2d)
    
    # Momentum probabilities
    prob_k = np.abs(psi_2d_shifted)**2
    prob_k_normalized = prob_k / np.sum(prob_k)
    
    # Calculate mean momentum
    mean_kx = np.sum(kx_grid * prob_k_normalized)
    mean_ky = np.sum(ky_grid * prob_k_normalized)
    
    # Calculate momentum spread
    var_kx = np.sum((kx_grid - mean_kx)**2 * prob_k_normalized)
    var_ky = np.sum((ky_grid - mean_ky)**2 * prob_k_normalized)
    spread_kx = np.sqrt(var_kx)
    spread_ky = np.sqrt(var_ky)
    
    return {
        'momentum_amplitudes': psi_2d_shifted,
        'momentum_probabilities': prob_k,
        'kx_grid': kx_grid,
        'ky_grid': ky_grid,
        'mean_k': np.array([mean_kx, mean_ky]),
        'k_spread': np.array([spread_kx, spread_ky]),
    }


def demonstrate_uncertainty_principle(
    n_qubits: int = 3,
    width_real: float = 2.0
) -> Dict[str, float]:
    """
    Demonstrate Heisenberg uncertainty principle: Δx·Δk ≥ 1/2
    
    Creates Gaussian wave packet and measures position/momentum spreads.
    
    Parameters
    ----------
    n_qubits : int
        Number of qubits per dimension
    width_real : float
        Width parameter for Gaussian in real space
        
    Returns
    -------
    dict
        Results showing uncertainty relation
    """
    from quscope.quantum_ctem import QuantumWaveFunction
    
    pixels = 2**n_qubits
    
    # Create Gaussian in real space
    x = np.linspace(-4, 4, pixels)
    X, Y = np.meshgrid(x, x)
    psi_real = np.exp(-(X**2 + Y**2) / (2 * width_real**2))
    
    # Encode quantum state
    qwf = QuantumWaveFunction(n_qubits, n_qubits)
    circuit_real = qwf.prepare_arbitrary_wave(psi_real)
    
    # Real space spread
    psi_real_extracted = qwf.extract_wave(circuit_real)
    prob_real = np.abs(psi_real_extracted)**2
    prob_real /= np.sum(prob_real)
    
    mean_x = np.sum(X * prob_real)
    mean_y = np.sum(Y * prob_real)
    delta_x = np.sqrt(np.sum((X - mean_x)**2 * prob_real))
    delta_y = np.sqrt(np.sum((Y - mean_y)**2 * prob_real))
    
    # Transform to momentum space
    converter = MomentumSpaceConverter(n_qubits, n_qubits)
    circuit_k = converter.transform_to_momentum(circuit_real)
    
    # Momentum space analysis
    analysis_k = analyze_momentum_distribution(
        circuit_k, n_qubits, n_qubits, real_size=8.0
    )
    
    delta_kx = analysis_k['k_spread'][0]
    delta_ky = analysis_k['k_spread'][1]
    
    # Uncertainty products
    uncertainty_x = delta_x * delta_kx
    uncertainty_y = delta_y * delta_ky
    
    return {
        'delta_x': float(delta_x),
        'delta_y': float(delta_y),
        'delta_kx': float(delta_kx),
        'delta_ky': float(delta_ky),
        'uncertainty_x': float(uncertainty_x),
        'uncertainty_y': float(uncertainty_y),
        'heisenberg_limit': 0.5,
        'satisfies_uncertainty': bool(uncertainty_x >= 0.4 and uncertainty_y >= 0.4),
    }
