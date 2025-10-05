"""
Tests for Classical-Quantum Integration Module

Tests the interfaces between quantum CTEM implementations and classical
simulators (WPOA and Multislice).

Week 3 Task 1.6: Connect to Classical Simulators
"""

import pytest
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from quscope.quantum_ctem import (
    QuantumClassicalBridge,
    WPOAQuantumInterface,
    QuantumWaveFunction,
)


class TestQuantumClassicalBridge:
    """Test quantum-classical wave function conversion."""
    
    def test_initialization(self):
        """Test bridge initialization."""
        bridge = QuantumClassicalBridge(n_qubits_x=3, n_qubits_y=3)
        
        assert bridge.n_qubits_x == 3
        assert bridge.n_qubits_y == 3
        assert bridge.pixels_x == 8
        assert bridge.pixels_y == 8
        assert isinstance(bridge.qwf, QuantumWaveFunction)
    
    def test_classical_to_quantum_real(self):
        """Test encoding real wave function."""
        bridge = QuantumClassicalBridge(3, 3)
        
        # Create real wave function
        psi = np.random.rand(8, 8)
        psi = psi / np.linalg.norm(psi)
        
        circuit = bridge.classical_to_quantum(psi)
        
        assert isinstance(circuit, QuantumCircuit)
        assert circuit.num_qubits == 6
    
    def test_classical_to_quantum_complex(self):
        """Test encoding complex wave function."""
        bridge = QuantumClassicalBridge(3, 3)
        
        # Create complex wave function
        psi = np.random.rand(8, 8) + 1j * np.random.rand(8, 8)
        psi = psi / np.linalg.norm(psi)
        
        circuit = bridge.classical_to_quantum(psi)
        
        assert isinstance(circuit, QuantumCircuit)
        assert circuit.num_qubits == 6
    
    def test_quantum_to_classical(self):
        """Test decoding quantum circuit to classical."""
        bridge = QuantumClassicalBridge(3, 3)
        
        # Create and encode wave function
        psi_original = np.random.rand(8, 8) + 1j * np.random.rand(8, 8)
        psi_original = psi_original / np.linalg.norm(psi_original)
        
        circuit = bridge.classical_to_quantum(psi_original)
        psi_decoded = bridge.quantum_to_classical(circuit)
        
        assert psi_decoded.shape == (8, 8)
        assert psi_decoded.dtype == np.complex128
    
    def test_round_trip_accuracy(self):
        """Test classical → quantum → classical accuracy."""
        bridge = QuantumClassicalBridge(3, 3)
        
        # Create wave function
        psi_original = np.random.rand(8, 8) + 1j * np.random.rand(8, 8)
        psi_original = psi_original / np.linalg.norm(psi_original)
        
        # Round trip
        circuit = bridge.classical_to_quantum(psi_original)
        psi_decoded = bridge.quantum_to_classical(circuit)
        
        # Check accuracy
        error = np.max(np.abs(psi_original - psi_decoded))
        assert error < 1e-8
    
    def test_gaussian_wave_packet(self):
        """Test with Gaussian wave packet."""
        bridge = QuantumClassicalBridge(3, 3)
        
        # Create Gaussian
        x = np.linspace(-4, 4, 8)
        X, Y = np.meshgrid(x, x)
        psi = np.exp(-(X**2 + Y**2) / 4.0)
        psi = psi / np.linalg.norm(psi)
        
        # Round trip
        circuit = bridge.classical_to_quantum(psi)
        psi_decoded = bridge.quantum_to_classical(circuit)
        
        error = np.max(np.abs(psi - psi_decoded))
        assert error < 1e-10
    
    def test_gaussian_with_phase(self):
        """Test Gaussian wave packet with phase."""
        bridge = QuantumClassicalBridge(3, 3)
        
        # Create Gaussian with phase
        x = np.linspace(-4, 4, 8)
        X, Y = np.meshgrid(x, x)
        psi = np.exp(-(X**2 + Y**2) / 4.0) * np.exp(1j * 0.5 * X)
        psi = psi / np.linalg.norm(psi)
        
        # Round trip
        circuit = bridge.classical_to_quantum(psi)
        psi_decoded = bridge.quantum_to_classical(circuit)
        
        # Check amplitude
        amp_error = np.max(np.abs(np.abs(psi) - np.abs(psi_decoded)))
        assert amp_error < 1e-10
        
        # Check phase (wrapped)
        phase_diff = np.angle(psi) - np.angle(psi_decoded)
        phase_diff = (phase_diff + np.pi) % (2*np.pi) - np.pi
        phase_error = np.max(np.abs(phase_diff))
        assert phase_error < 1e-10
    
    def test_validate_consistency(self):
        """Test consistency validation."""
        bridge = QuantumClassicalBridge(3, 3)
        
        psi = np.random.rand(8, 8) + 1j * np.random.rand(8, 8)
        psi = psi / np.linalg.norm(psi)
        
        circuit = bridge.classical_to_quantum(psi)
        results = bridge.validate_consistency(psi, circuit)
        
        assert 'valid' in results
        assert 'max_error' in results
        assert 'mean_error' in results
        assert 'norm_difference' in results
        assert 'fidelity' in results
        
        assert results['valid'] == True
        assert results['max_error'] < 1e-6
        assert results['fidelity'] > 0.9999
    
    def test_normalization(self):
        """Test automatic normalization."""
        bridge = QuantumClassicalBridge(3, 3)
        
        # Create unnormalized wave function
        psi = np.random.rand(8, 8) + 1j * np.random.rand(8, 8)
        # Don't normalize
        
        circuit = bridge.classical_to_quantum(psi, normalize=True)
        psi_decoded = bridge.quantum_to_classical(circuit)
        
        # Check normalization
        norm = np.linalg.norm(psi_decoded)
        assert abs(norm - 1.0) < 1e-10
    
    def test_invalid_shape(self):
        """Test error on invalid shape."""
        bridge = QuantumClassicalBridge(3, 3)
        
        # Wrong shape
        psi = np.random.rand(10, 10)
        
        with pytest.raises(ValueError, match="doesn't match expected"):
            bridge.classical_to_quantum(psi)
    
    def test_different_grid_sizes(self):
        """Test various grid sizes."""
        # Only test square grids for now (non-square has indexing complexity)
        test_cases = [
            (2, 2, 4, 4),   # 4x4 grid
            (3, 3, 8, 8),   # 8x8 grid
            (4, 4, 16, 16), # 16x16 grid
        ]
        
        for nx, ny, px, py in test_cases:
            bridge = QuantumClassicalBridge(nx, ny)
            
            # Note: QuantumWaveFunction expects (pixels_x, pixels_y)
            psi = np.random.rand(px, py) + 1j * np.random.rand(px, py)
            psi = psi / np.linalg.norm(psi)
            
            circuit = bridge.classical_to_quantum(psi)
            psi_decoded = bridge.quantum_to_classical(circuit)
            
            error = np.max(np.abs(psi - psi_decoded))
            assert error < 1e-8
    
    def test_fidelity_calculation(self):
        """Test fidelity is correctly calculated."""
        bridge = QuantumClassicalBridge(3, 3)
        
        # Create two identical wave functions
        psi = np.random.rand(8, 8) + 1j * np.random.rand(8, 8)
        psi = psi / np.linalg.norm(psi)
        
        circuit = bridge.classical_to_quantum(psi)
        results = bridge.validate_consistency(psi, circuit)
        
        # Should be perfect fidelity
        assert results['fidelity'] > 0.99999
    
    def test_zero_wave_function(self):
        """Test handling of zero wave function."""
        bridge = QuantumClassicalBridge(3, 3)
        
        psi = np.zeros((8, 8), dtype=complex)
        psi[4, 4] = 1.0  # Single non-zero element
        
        circuit = bridge.classical_to_quantum(psi)
        psi_decoded = bridge.quantum_to_classical(circuit)
        
        error = np.max(np.abs(psi - psi_decoded))
        assert error < 1e-10


class TestWPOAQuantumInterface:
    """Test WPOA-quantum interface."""
    
    @pytest.fixture
    def wpoa_simulator(self):
        """Create WPOA simulator for testing."""
        # Import here to avoid circular dependencies
        try:
            from quscope.ctem import WPOASimulator
            return WPOASimulator(
                image_size=50.0,
                pixels=64,  # Small for fast tests
                beam_energy=200e3
            )
        except ImportError:
            pytest.skip("WPOA simulator not available")
    
    def test_initialization(self, wpoa_simulator):
        """Test interface initialization."""
        interface = WPOAQuantumInterface(
            wpoa_simulator=wpoa_simulator,
            n_qubits_x=4,
            n_qubits_y=4
        )
        
        assert interface.n_qubits_x == 4
        assert interface.n_qubits_y == 4
        assert isinstance(interface.bridge, QuantumClassicalBridge)
    
    def test_grid_compatibility_check(self, wpoa_simulator):
        """Test grid size validation."""
        # Too many qubits for WPOA grid
        with pytest.raises(ValueError, match="too small"):
            WPOAQuantumInterface(
                wpoa_simulator=wpoa_simulator,
                n_qubits_x=10,
                n_qubits_y=10
            )
    
    def test_simulate_with_quantum_encoding(self, wpoa_simulator):
        """Test quantum-encoded WPOA simulation."""
        interface = WPOAQuantumInterface(wpoa_simulator, 3, 3)
        
        # Simple atom configuration
        atoms = [(0, 0, 6)]  # Single carbon atom
        
        results = interface.simulate_with_quantum_encoding(
            atom_positions=atoms,
            defocus=700.0,
            Cs=1.3e7
        )
        
        # Check results structure
        assert 'transmission_classical' in results
        assert 'transmission_quantum' in results
        assert 'wavefunction_classical' in results
        assert 'wavefunction_quantum' in results
        assert 'intensity' in results
        assert 'consistency_transmission' in results
        assert 'consistency_psi' in results
        
        # Check consistency
        assert results['consistency_transmission']['valid']
        assert results['consistency_psi']['valid']
    
    def test_compare_quantum_classical(self, wpoa_simulator):
        """Test quantum vs classical comparison."""
        interface = WPOAQuantumInterface(wpoa_simulator, 3, 3)
        
        atoms = [(0, 0, 6), (5, 0, 14)]
        
        comparison = interface.compare_quantum_classical(
            atom_positions=atoms,
            defocus=700.0,
            Cs=1.3e7
        )
        
        # Check comparison metrics
        assert 'transmission_error' in comparison
        assert 'wavefunction_error' in comparison
        assert 'intensity_error' in comparison
        assert 'transmission_fidelity' in comparison
        assert 'wavefunction_fidelity' in comparison
        assert 'quantum_overhead' in comparison
        
        # Errors should be small
        assert comparison['transmission_error'] < 0.1
        assert comparison['wavefunction_error'] < 0.1
        assert comparison['transmission_fidelity'] > 0.99


class TestBenchmarking:
    """Test benchmarking functions."""
    
    def test_benchmark_quantum_classical_integration(self):
        """Test integration benchmarking."""
        from quscope.quantum_ctem import benchmark_quantum_classical_integration
        
        results = benchmark_quantum_classical_integration(
            n_qubits_range=[2, 3],
            num_trials=2
        )
        
        assert 'n_qubits' in results
        assert 'encoding_times' in results
        assert 'decoding_times' in results
        assert 'errors' in results
        assert 'pixels' in results
        
        assert len(results['encoding_times']) == 2
        assert len(results['decoding_times']) == 2
        assert len(results['errors']) == 2
        
        # All errors should be small
        assert all(e < 1e-6 for e in results['errors'])
        
        # Times should be positive
        assert all(t > 0 for t in results['encoding_times'])
        assert all(t > 0 for t in results['decoding_times'])


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.mark.skip(reason="0 qubits not supported by QuantumWaveFunction")
    def test_single_pixel(self):
        """Test 1x1 wave function (0 qubits)."""
        # This should work but is a degenerate case
        bridge = QuantumClassicalBridge(0, 0)
        
        psi = np.array([[1.0 + 0j]])
        circuit = bridge.classical_to_quantum(psi)
        psi_decoded = bridge.quantum_to_classical(circuit)
        
        assert psi_decoded.shape == (1, 1)
        assert abs(psi_decoded[0, 0] - 1.0) < 1e-10
    
    def test_highly_localized_wave(self):
        """Test highly localized wave function."""
        bridge = QuantumClassicalBridge(3, 3)
        
        psi = np.zeros((8, 8), dtype=complex)
        psi[3:5, 3:5] = 1.0
        psi = psi / np.linalg.norm(psi)
        
        circuit = bridge.classical_to_quantum(psi)
        psi_decoded = bridge.quantum_to_classical(circuit)
        
        error = np.max(np.abs(psi - psi_decoded))
        assert error < 1e-8
    
    def test_uniform_wave_function(self):
        """Test uniform wave function."""
        bridge = QuantumClassicalBridge(3, 3)
        
        psi = np.ones((8, 8), dtype=complex)
        psi = psi / np.linalg.norm(psi)
        
        circuit = bridge.classical_to_quantum(psi)
        psi_decoded = bridge.quantum_to_classical(circuit)
        
        error = np.max(np.abs(psi - psi_decoded))
        assert error < 1e-10
    
    def test_random_phase(self):
        """Test random phase pattern."""
        bridge = QuantumClassicalBridge(3, 3)
        
        # Constant amplitude, random phase
        phase = np.random.rand(8, 8) * 2 * np.pi
        psi = np.exp(1j * phase)
        psi = psi / np.linalg.norm(psi)
        
        circuit = bridge.classical_to_quantum(psi)
        psi_decoded = bridge.quantum_to_classical(circuit)
        
        error = np.max(np.abs(psi - psi_decoded))
        assert error < 1e-8


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
