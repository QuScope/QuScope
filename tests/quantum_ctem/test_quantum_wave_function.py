"""
Tests for Quantum Wave Function Representation

This test suite validates the quantum encoding and decoding of electron
wave functions for pure quantum CTEM simulation (Phase 1).

Test Categories:
1. Initialization and Configuration
2. Incident Plane Wave Preparation
3. Arbitrary Wave Function Encoding
4. Wave Function Extraction
5. Normalization Handling
6. 2D QFT/IQFT Operations
7. Edge Cases and Error Handling
8. Round-Trip Accuracy

Target: >90% code coverage, all tests passing
"""

import numpy as np
import pytest
from qiskit.quantum_info import Statevector

from quscope.quantum_ctem.quantum_wave_function import QuantumWaveFunction


class TestQuantumWaveFunctionInitialization:
    """Test initialization and configuration."""

    def test_basic_initialization(self):
        """Test basic initialization with valid parameters."""
        qwf = QuantumWaveFunction(n_qubits_x=3, n_qubits_y=3)

        assert qwf.n_qubits_x == 3
        assert qwf.n_qubits_y == 3
        assert qwf.pixels_x == 8
        assert qwf.pixels_y == 8
        assert qwf.total_qubits == 6

    def test_asymmetric_initialization(self):
        """Test initialization with different x and y qubit counts."""
        qwf = QuantumWaveFunction(n_qubits_x=2, n_qubits_y=3)

        assert qwf.pixels_x == 4
        assert qwf.pixels_y == 8
        assert qwf.total_qubits == 5

    def test_single_qubit_per_dimension(self):
        """Test minimum case: 1 qubit per dimension."""
        qwf = QuantumWaveFunction(n_qubits_x=1, n_qubits_y=1)

        assert qwf.pixels_x == 2
        assert qwf.pixels_y == 2
        assert qwf.total_qubits == 2

    def test_large_image_size(self):
        """Test large image (256×256)."""
        qwf = QuantumWaveFunction(n_qubits_x=8, n_qubits_y=8)

        assert qwf.pixels_x == 256
        assert qwf.pixels_y == 256
        assert qwf.total_qubits == 16

    def test_invalid_qubit_count_zero(self):
        """Test that zero qubits raises ValueError."""
        with pytest.raises(ValueError, match="Number of qubits must be >= 1"):
            QuantumWaveFunction(n_qubits_x=0, n_qubits_y=3)

    def test_invalid_qubit_count_negative(self):
        """Test that negative qubits raises ValueError."""
        with pytest.raises(ValueError, match="Number of qubits must be >= 1"):
            QuantumWaveFunction(n_qubits_x=3, n_qubits_y=-1)

    def test_qubit_register_assignment(self):
        """Test that qubit registers are properly assigned."""
        qwf = QuantumWaveFunction(n_qubits_x=3, n_qubits_y=2)

        assert qwf.x_qubits == [0, 1, 2]
        assert qwf.y_qubits == [3, 4]

    def test_get_info(self):
        """Test get_info method returns correct configuration."""
        qwf = QuantumWaveFunction(n_qubits_x=3, n_qubits_y=3)
        info = qwf.get_info()

        assert info["n_qubits_x"] == 3
        assert info["n_qubits_y"] == 3
        assert info["total_qubits"] == 6
        assert info["pixels_x"] == 8
        assert info["pixels_y"] == 8
        assert info["total_pixels"] == 64
        assert info["hilbert_space_dimension"] == 64

    def test_repr(self):
        """Test string representation."""
        qwf = QuantumWaveFunction(n_qubits_x=3, n_qubits_y=3)
        repr_str = repr(qwf)

        assert "QuantumWaveFunction" in repr_str
        assert "n_qubits_x=3" in repr_str
        assert "n_qubits_y=3" in repr_str
        assert "8×8" in repr_str


class TestIncidentPlaneWave:
    """Test incident plane wave preparation."""

    def test_plane_wave_circuit_creation(self):
        """Test that plane wave circuit is created correctly."""
        qwf = QuantumWaveFunction(n_qubits_x=3, n_qubits_y=3)
        circuit = qwf.prepare_incident_wave()

        assert circuit is not None
        assert circuit.num_qubits == 6
        assert circuit.name == "incident_wave"

    def test_plane_wave_uniform_superposition(self):
        """Test that plane wave creates uniform superposition."""
        qwf = QuantumWaveFunction(n_qubits_x=3, n_qubits_y=3)
        circuit = qwf.prepare_incident_wave()

        # Get statevector
        sv = Statevector.from_instruction(circuit)
        amplitudes = np.abs(sv.data)

        # All amplitudes should be equal (uniform superposition)
        expected_amplitude = 1.0 / np.sqrt(64)
        assert np.allclose(amplitudes, expected_amplitude)

    def test_plane_wave_normalization_stored(self):
        """Test that normalization factor is stored correctly."""
        qwf = QuantumWaveFunction(n_qubits_x=3, n_qubits_y=3)
        circuit = qwf.prepare_incident_wave()

        assert qwf.get_normalization_factor() == 1.0

    def test_plane_wave_extraction(self):
        """Test extracting plane wave as classical array."""
        qwf = QuantumWaveFunction(n_qubits_x=3, n_qubits_y=3)
        circuit = qwf.prepare_incident_wave()
        psi = qwf.extract_wave(circuit)

        # Shape should match pixels
        assert psi.shape == (8, 8)

        # All values should be equal (uniform)
        assert np.allclose(np.abs(psi), np.abs(psi[0, 0]))

        # Value should be 1/√64 (normalized)
        expected_value = 1.0 / np.sqrt(64)
        assert np.isclose(np.abs(psi[0, 0]), expected_value)

    def test_plane_wave_phase(self):
        """Test that plane wave has zero relative phase."""
        qwf = QuantumWaveFunction(n_qubits_x=2, n_qubits_y=2)
        circuit = qwf.prepare_incident_wave()
        psi = qwf.extract_wave(circuit)

        # All phases should be equal (up to global phase)
        phases = np.angle(psi)
        phase_differences = phases - phases[0, 0]
        assert np.allclose(phase_differences, 0, atol=1e-10)


class TestArbitraryWaveEncoding:
    """Test encoding of arbitrary wave functions."""

    def test_gaussian_wave_packet(self):
        """Test encoding Gaussian wave packet."""
        qwf = QuantumWaveFunction(n_qubits_x=3, n_qubits_y=3)

        # Create Gaussian
        x = np.linspace(-4, 4, 8)
        y = np.linspace(-4, 4, 8)
        X, Y = np.meshgrid(x, y)
        psi_gaussian = np.exp(-(X**2 + Y**2) / 2)

        # Encode
        circuit = qwf.prepare_arbitrary_wave(psi_gaussian)

        assert circuit is not None
        assert circuit.num_qubits == 6

    def test_complex_phase_preservation(self):
        """Test that complex phases are preserved."""
        qwf = QuantumWaveFunction(n_qubits_x=3, n_qubits_y=3)

        # Create wave with definite phase
        x = np.linspace(-4, 4, 8)
        X, Y = np.meshgrid(x, x)
        phase = np.pi / 4
        psi_complex = np.exp(-(X**2 + Y**2) / 2) * np.exp(1j * phase)

        # Encode and extract
        circuit = qwf.prepare_arbitrary_wave(psi_complex)
        psi_extracted = qwf.extract_wave(circuit)

        # Check phase at center (where amplitude is highest)
        phase_original = np.angle(psi_complex[4, 4])
        phase_extracted = np.angle(psi_extracted[4, 4])

        assert np.isclose(phase_original, phase_extracted, atol=1e-10)

    def test_spatially_varying_phase(self):
        """Test wave with spatially varying phase (momentum kick)."""
        qwf = QuantumWaveFunction(n_qubits_x=3, n_qubits_y=3)

        # Create wave with linear phase (plane wave with momentum)
        x = np.linspace(0, 8, 8)
        X, Y = np.meshgrid(x, x)
        kx, ky = 0.5, 0.3  # Wave vector
        psi_momentum = np.exp(1j * (kx * X + ky * Y))

        # Encode and extract
        circuit = qwf.prepare_arbitrary_wave(psi_momentum)
        psi_extracted = qwf.extract_wave(circuit)

        # Phases should match (up to normalization and global phase)
        phase_original = np.angle(psi_momentum)
        phase_extracted = np.angle(psi_extracted)

        # Remove global phase
        phase_diff = phase_original - phase_extracted
        phase_diff -= phase_diff[0, 0]

        assert np.allclose(phase_diff, 0, atol=1e-6)

    def test_zero_wave_function(self):
        """Test encoding zero wave function."""
        qwf = QuantumWaveFunction(n_qubits_x=3, n_qubits_y=3)

        # Zero wave
        psi_zero = np.zeros((8, 8), dtype=complex)

        # Should create uniform superposition as fallback
        circuit = qwf.prepare_arbitrary_wave(psi_zero)
        psi_extracted = qwf.extract_wave(circuit)

        # Should be zeros (norm was stored as 0)
        assert np.allclose(psi_extracted, 0)
        assert qwf.get_normalization_factor() == 0.0

    def test_single_pixel_nonzero(self):
        """Test wave with single nonzero pixel."""
        qwf = QuantumWaveFunction(n_qubits_x=2, n_qubits_y=2)

        # Single pixel wave
        psi_single = np.zeros((4, 4), dtype=complex)
        psi_single[2, 2] = 1.0 + 0.5j

        # Encode and extract
        circuit = qwf.prepare_arbitrary_wave(psi_single)
        psi_extracted = qwf.extract_wave(circuit)

        # Normalize both for comparison
        psi_single_norm = psi_single / np.linalg.norm(psi_single)
        psi_extracted_norm = psi_extracted / np.linalg.norm(psi_extracted)

        assert np.allclose(psi_single_norm, psi_extracted_norm, atol=1e-10)

    def test_invalid_shape_raises_error(self):
        """Test that wrong shape raises ValueError."""
        qwf = QuantumWaveFunction(n_qubits_x=3, n_qubits_y=3)

        # Wrong shape
        psi_wrong = np.ones((4, 4), dtype=complex)

        with pytest.raises(ValueError, match="doesn't match expected"):
            qwf.prepare_arbitrary_wave(psi_wrong, validate_shape=True)

    def test_shape_validation_can_be_disabled(self):
        """Test that shape validation can be disabled.

        Note: Even with validate_shape=False, Qiskit's initialize()
        may still raise errors for incompatible array sizes. This test
        verifies that OUR ValueError is not raised.
        """
        qwf = QuantumWaveFunction(n_qubits_x=3, n_qubits_y=3)

        # Wrong shape, but validation disabled
        psi_wrong = np.ones((4, 4), dtype=complex)

        # Should not raise OUR ValueError, but may raise Qiskit errors
        from qiskit.exceptions import QiskitError

        try:
            circuit = qwf.prepare_arbitrary_wave(psi_wrong, validate_shape=False)
            # If Qiskit doesn't complain, that's fine
        except ValueError as e:
            # OUR validation should be disabled
            if "doesn't match expected" in str(e):
                pytest.fail("Shape validation was not disabled")
            # But other ValueErrors are fine
        except QiskitError:
            # Qiskit's own validation is expected and acceptable
            pass


class TestRoundTripAccuracy:
    """Test round-trip encoding and decoding accuracy."""

    def test_gaussian_round_trip(self):
        """Test Gaussian wave packet round-trip accuracy."""
        qwf = QuantumWaveFunction(n_qubits_x=3, n_qubits_y=3)

        # Create Gaussian
        x = np.linspace(-4, 4, 8)
        X, Y = np.meshgrid(x, x)
        psi_original = np.exp(-(X**2 + Y**2) / 2)

        # Encode and decode
        circuit = qwf.prepare_arbitrary_wave(psi_original)
        psi_reconstructed = qwf.extract_wave(circuit)

        # Should match within numerical precision
        assert np.allclose(psi_original, psi_reconstructed, atol=1e-10)

    def test_complex_gaussian_round_trip(self):
        """Test complex Gaussian round-trip."""
        qwf = QuantumWaveFunction(n_qubits_x=3, n_qubits_y=3)

        # Complex Gaussian with phase
        x = np.linspace(-4, 4, 8)
        X, Y = np.meshgrid(x, x)
        psi_original = np.exp(-(X**2 + Y**2) / 2) * np.exp(1j * X)

        # Round-trip
        circuit = qwf.prepare_arbitrary_wave(psi_original)
        psi_reconstructed = qwf.extract_wave(circuit)

        assert np.allclose(psi_original, psi_reconstructed, atol=1e-10)

    def test_random_wave_round_trip(self):
        """Test random wave function round-trip."""
        qwf = QuantumWaveFunction(n_qubits_x=2, n_qubits_y=2)

        # Random complex wave
        np.random.seed(42)
        psi_original = np.random.randn(4, 4) + 1j * np.random.randn(4, 4)

        # Round-trip
        circuit = qwf.prepare_arbitrary_wave(psi_original)
        psi_reconstructed = qwf.extract_wave(circuit)

        assert np.allclose(psi_original, psi_reconstructed, atol=1e-10)

    def test_normalization_preservation(self):
        """Test that normalization is correctly preserved."""
        qwf = QuantumWaveFunction(n_qubits_x=3, n_qubits_y=3)

        # Wave with known norm
        x = np.linspace(-4, 4, 8)
        X, Y = np.meshgrid(x, x)
        psi_original = 2.5 * np.exp(-(X**2 + Y**2) / 2)  # Norm ≠ 1

        original_norm = np.linalg.norm(psi_original)

        # Round-trip
        circuit = qwf.prepare_arbitrary_wave(psi_original)
        psi_reconstructed = qwf.extract_wave(circuit)

        reconstructed_norm = np.linalg.norm(psi_reconstructed)

        # Norms should match
        assert np.isclose(original_norm, reconstructed_norm, rtol=1e-10)
        assert np.isclose(qwf.get_normalization_factor(), original_norm, rtol=1e-10)


class TestQuantumFourierTransform:
    """Test 2D QFT and IQFT operations."""

    def test_2d_qft_circuit_creation(self):
        """Test that 2D QFT circuit is created correctly."""
        qwf = QuantumWaveFunction(n_qubits_x=3, n_qubits_y=3)
        qft_circuit = qwf.create_2d_qft_circuit()

        assert qft_circuit is not None
        assert qft_circuit.num_qubits == 6
        assert qft_circuit.name == "QFT_2D"

    def test_2d_iqft_circuit_creation(self):
        """Test that 2D IQFT circuit is created correctly."""
        qwf = QuantumWaveFunction(n_qubits_x=3, n_qubits_y=3)
        iqft_circuit = qwf.create_2d_iqft_circuit()

        assert iqft_circuit is not None
        assert iqft_circuit.num_qubits == 6
        assert iqft_circuit.name == "IQFT_2D"

    def test_qft_iqft_round_trip(self):
        """Test that QFT followed by IQFT returns original state."""
        qwf = QuantumWaveFunction(n_qubits_x=2, n_qubits_y=2)

        # Create arbitrary wave
        x = np.linspace(-2, 2, 4)
        X, Y = np.meshgrid(x, x)
        psi_original = np.exp(-(X**2 + Y**2))

        # Encode
        circuit = qwf.prepare_arbitrary_wave(psi_original)

        # Apply QFT then IQFT
        qft = qwf.create_2d_qft_circuit()
        iqft = qwf.create_2d_iqft_circuit()
        circuit.compose(qft, inplace=True)
        circuit.compose(iqft, inplace=True)

        # Extract
        psi_final = qwf.extract_wave(circuit)

        # Should match original (QFT and IQFT cancel)
        assert np.allclose(psi_original, psi_final, atol=1e-10)

    def test_qft_transforms_to_momentum_space(self):
        """Test that QFT transforms plane wave correctly."""
        qwf = QuantumWaveFunction(n_qubits_x=3, n_qubits_y=3)

        # Incident plane wave (k=0)
        circuit = qwf.prepare_incident_wave()

        # Apply QFT
        qft = qwf.create_2d_qft_circuit()
        circuit.compose(qft, inplace=True)

        # Extract momentum space
        psi_k = qwf.extract_wave(circuit)

        # For uniform plane wave, momentum space should be peaked at k=0
        # (first element after QFT with swaps)
        assert np.abs(psi_k[0, 0]) > 0.9 * np.max(np.abs(psi_k))


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_minimum_image_size(self):
        """Test minimum possible image (2×2)."""
        qwf = QuantumWaveFunction(n_qubits_x=1, n_qubits_y=1)

        psi = np.ones((2, 2), dtype=complex)
        circuit = qwf.prepare_arbitrary_wave(psi)
        psi_extracted = qwf.extract_wave(circuit)

        assert psi_extracted.shape == (2, 2)
        assert np.allclose(psi, psi_extracted, atol=1e-10)

    def test_maximum_amplitude_values(self):
        """Test wave with very large amplitude values."""
        qwf = QuantumWaveFunction(n_qubits_x=2, n_qubits_y=2)

        # Very large amplitude
        psi_large = 1e10 * np.ones((4, 4), dtype=complex)

        circuit = qwf.prepare_arbitrary_wave(psi_large)
        psi_extracted = qwf.extract_wave(circuit)

        # Should preserve the large norm
        assert np.isclose(
            np.linalg.norm(psi_large), np.linalg.norm(psi_extracted), rtol=1e-10
        )

    def test_very_small_amplitude_values(self):
        """Test wave with very small amplitude values."""
        qwf = QuantumWaveFunction(n_qubits_x=2, n_qubits_y=2)

        # Very small amplitude
        psi_small = 1e-10 * np.ones((4, 4), dtype=complex)

        circuit = qwf.prepare_arbitrary_wave(psi_small)
        psi_extracted = qwf.extract_wave(circuit)

        # Should preserve the small norm
        assert np.isclose(
            np.linalg.norm(psi_small), np.linalg.norm(psi_extracted), rtol=1e-6
        )


def test_integration_with_classical_plane_wave():
    """
    Integration test: Compare quantum plane wave with classical expectation.

    This test validates that the quantum encoding produces results consistent
    with classical wave mechanics.
    """
    qwf = QuantumWaveFunction(n_qubits_x=3, n_qubits_y=3)

    # Quantum plane wave
    circuit = qwf.prepare_incident_wave()
    psi_quantum = qwf.extract_wave(circuit)

    # Classical expectation: uniform with value 1/√N
    N = 64
    psi_classical = np.ones((8, 8), dtype=complex) / np.sqrt(N)

    # Should match
    assert np.allclose(psi_quantum, psi_classical, atol=1e-10)

    # Intensity should be uniform and sum to 1
    intensity = np.abs(psi_quantum) ** 2
    assert np.allclose(intensity, 1.0 / N)
    assert np.isclose(np.sum(intensity), 1.0)


def test_quantum_state_normalization():
    """
    Test that quantum states are properly normalized.

    This is a critical property for valid quantum mechanics:
    The sum of squared amplitudes must equal 1.
    """
    qwf = QuantumWaveFunction(n_qubits_x=3, n_qubits_y=3)

    # Create arbitrary wave
    x = np.linspace(-4, 4, 8)
    X, Y = np.meshgrid(x, x)
    psi_original = 5.0 * np.exp(-(X**2 + Y**2) / 2)  # Unnormalized

    # Encode
    circuit = qwf.prepare_arbitrary_wave(psi_original)

    # Check quantum state is normalized
    sv = Statevector.from_instruction(circuit)
    quantum_norm = np.linalg.norm(sv.data)

    assert np.isclose(quantum_norm, 1.0, atol=1e-10)
