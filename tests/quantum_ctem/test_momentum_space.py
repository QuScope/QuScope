"""
Tests for momentum space utilities.

This module tests momentum space operations including:
- QFT/IQFT transformations
- Parseval's theorem (energy conservation)
- Momentum space filtering
- Uncertainty principle demonstration

Author: QuScope Team
Date: October 2025
"""

import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, state_fidelity

from quscope.quantum_ctem import QuantumWaveFunction
from quscope.quantum_ctem.momentum_space import (
    MomentumSpaceConverter,
    MomentumSpaceFilter,
    ParsevalValidator,
    analyze_momentum_distribution,
    demonstrate_uncertainty_principle,
)


class TestMomentumSpaceConverter:
    """Test momentum space conversion operations."""

    def test_initialization(self):
        """Test converter initialization."""
        converter = MomentumSpaceConverter(n_qubits_x=3, n_qubits_y=3)

        assert converter.n_qubits_x == 3
        assert converter.n_qubits_y == 3
        assert converter.total_qubits == 6
        assert converter.pixels_x == 8
        assert converter.pixels_y == 8

    def test_qft_circuit_creation(self):
        """Test 2D QFT circuit creation."""
        converter = MomentumSpaceConverter(n_qubits_x=2, n_qubits_y=2)

        qft_circuit = converter.create_qft_circuit()

        assert qft_circuit.num_qubits == 4
        assert qft_circuit.name == "QFT_2D"
        assert qft_circuit.depth() > 0

    def test_iqft_circuit_creation(self):
        """Test 2D inverse QFT circuit creation."""
        converter = MomentumSpaceConverter(n_qubits_x=2, n_qubits_y=2)

        iqft_circuit = converter.create_iqft_circuit()

        assert iqft_circuit.num_qubits == 4
        assert iqft_circuit.name == "IQFT_2D"
        assert iqft_circuit.depth() > 0

    def test_qft_caching(self):
        """Test that QFT circuits are cached."""
        converter = MomentumSpaceConverter(n_qubits_x=2, n_qubits_y=2)

        qft1 = converter.create_qft_circuit()
        qft2 = converter.create_qft_circuit()

        # Should return same object (cached)
        assert qft1 is qft2

    def test_transform_to_momentum(self):
        """Test transformation from real to momentum space."""
        n_qubits = 2
        converter = MomentumSpaceConverter(n_qubits_x=n_qubits, n_qubits_y=n_qubits)

        # Create test state (plane wave)
        qwf = QuantumWaveFunction(n_qubits, n_qubits)
        circuit_real = qwf.prepare_incident_wave()

        # Transform to momentum space
        circuit_k = converter.transform_to_momentum(circuit_real)

        assert circuit_k.num_qubits == 4
        assert circuit_k.depth() > circuit_real.depth()

    def test_transform_to_real(self):
        """Test transformation from momentum to real space."""
        n_qubits = 2
        converter = MomentumSpaceConverter(n_qubits_x=n_qubits, n_qubits_y=n_qubits)

        # Create test state
        qwf = QuantumWaveFunction(n_qubits, n_qubits)
        circuit_k = qwf.prepare_incident_wave()

        # Transform to real space
        circuit_x = converter.transform_to_real(circuit_k)

        assert circuit_x.num_qubits == 4
        assert circuit_x.depth() > circuit_k.depth()

    def test_round_trip_transform(self):
        """Test QFT → IQFT round trip preserves state."""
        n_qubits = 3
        converter = MomentumSpaceConverter(n_qubits_x=n_qubits, n_qubits_y=n_qubits)

        # Create Gaussian state
        x = np.linspace(-4, 4, 8)
        X, Y = np.meshgrid(x, x)
        psi_gauss = np.exp(-(X**2 + Y**2) / 2)

        qwf = QuantumWaveFunction(n_qubits, n_qubits)
        circuit_original = qwf.prepare_arbitrary_wave(psi_gauss)

        # Round trip: real → momentum → real
        circuit_k = converter.transform_to_momentum(circuit_original)
        circuit_back = converter.transform_to_real(circuit_k)

        # Should match original
        sv_original = Statevector.from_instruction(circuit_original)
        sv_back = Statevector.from_instruction(circuit_back)

        fidelity = state_fidelity(sv_original, sv_back)
        assert fidelity > 0.9999

    def test_momentum_grid_generation(self):
        """Test momentum space grid generation."""
        converter = MomentumSpaceConverter(n_qubits_x=3, n_qubits_y=3)

        real_size = 10.0  # Angstroms
        kx_grid, ky_grid = converter.get_momentum_grid(real_size)

        # Check shapes
        assert kx_grid.shape == (8, 8)
        assert ky_grid.shape == (8, 8)

        # Check that grids are centered at k=0
        # (approximately, due to discrete sampling)
        assert abs(np.mean(kx_grid)) < 0.5
        assert abs(np.mean(ky_grid)) < 0.5

        # Check reciprocal relationship
        # Δk ~ 2π / L
        expected_dk = 2 * np.pi / real_size
        actual_dkx = kx_grid[1, 0] - kx_grid[0, 0]
        assert abs(actual_dkx - expected_dk) / expected_dk < 0.1


class TestParsevalValidator:
    """Test Parseval's theorem validation."""

    def test_initialization(self):
        """Test validator initialization."""
        validator = ParsevalValidator(tolerance=1e-8)
        assert validator.tolerance == 1e-8

    def test_energy_conservation(self):
        """Test that QFT preserves energy (Parseval)."""
        n_qubits = 3
        converter = MomentumSpaceConverter(n_qubits_x=n_qubits, n_qubits_y=n_qubits)
        validator = ParsevalValidator(tolerance=1e-10)

        # Create Gaussian state
        x = np.linspace(-4, 4, 8)
        X, Y = np.meshgrid(x, x)
        psi = np.exp(-(X**2 + Y**2) / 2)

        qwf = QuantumWaveFunction(n_qubits, n_qubits)
        circuit_real = qwf.prepare_arbitrary_wave(psi)
        circuit_k = converter.transform_to_momentum(circuit_real)

        # Validate energy conservation
        result = validator.validate_transform(circuit_real, circuit_k)

        assert result["valid"]
        assert result["relative_error"] < 1e-10
        assert abs(result["energy_real"] - 1.0) < 1e-10  # Normalized state
        assert abs(result["energy_momentum"] - 1.0) < 1e-10

    def test_round_trip_validation(self):
        """Test round trip QFT → IQFT validation."""
        n_qubits = 2
        converter = MomentumSpaceConverter(n_qubits_x=n_qubits, n_qubits_y=n_qubits)
        validator = ParsevalValidator(tolerance=1e-10)

        # Create test state
        qwf = QuantumWaveFunction(n_qubits, n_qubits)
        psi = np.random.randn(4, 4) + 1j * np.random.randn(4, 4)
        circuit_original = qwf.prepare_arbitrary_wave(psi)

        # Round trip
        circuit_k = converter.transform_to_momentum(circuit_original)
        circuit_back = converter.transform_to_real(circuit_k)

        # Validate
        result = validator.validate_round_trip(circuit_original, circuit_back)

        assert result["valid"]
        assert result["fidelity"] > 0.9999
        assert result["error"] < 1e-10

    def test_multiple_states_conservation(self):
        """Test energy conservation for various states."""
        n_qubits = 3
        converter = MomentumSpaceConverter(n_qubits_x=n_qubits, n_qubits_y=n_qubits)
        validator = ParsevalValidator(tolerance=1e-10)

        test_states = []

        # Plane wave
        test_states.append(np.ones((8, 8)))

        # Gaussian
        x = np.linspace(-4, 4, 8)
        X, Y = np.meshgrid(x, x)
        test_states.append(np.exp(-(X**2 + Y**2) / 2))

        # Random state
        test_states.append(np.random.randn(8, 8) + 1j * np.random.randn(8, 8))

        qwf = QuantumWaveFunction(n_qubits, n_qubits)

        for psi in test_states:
            circuit_real = qwf.prepare_arbitrary_wave(psi)
            circuit_k = converter.transform_to_momentum(circuit_real)

            result = validator.validate_transform(circuit_real, circuit_k)
            assert result["valid"], f"Failed for state shape {psi.shape}"


class TestMomentumSpaceFilter:
    """Test momentum space filtering operations."""

    def test_initialization(self):
        """Test filter initialization."""
        filter_obj = MomentumSpaceFilter(n_qubits_x=3, n_qubits_y=3)

        assert filter_obj.n_qubits_x == 3
        assert filter_obj.n_qubits_y == 3
        assert filter_obj.total_qubits == 6
        assert filter_obj.pixels_x == 8
        assert filter_obj.pixels_y == 8

    def test_aperture_filter_creation(self):
        """Test objective aperture filter creation."""
        filter_obj = MomentumSpaceFilter(n_qubits_x=3, n_qubits_y=3)

        # Create momentum grids
        converter = MomentumSpaceConverter(3, 3)
        kx_grid, ky_grid = converter.get_momentum_grid(real_size=10.0)

        # Create aperture
        k_max = 0.5
        aperture = filter_obj.create_aperture_filter(k_max, kx_grid, ky_grid)

        # Check shape
        assert aperture.shape == (8, 8)

        # Check that center is included
        center_idx = 4
        assert aperture[center_idx, center_idx] == 1.0

        # Check that values are binary (0 or 1)
        assert np.all((aperture == 0) | (aperture == 1))

    def test_lowpass_filter_creation(self):
        """Test low-pass filter creation."""
        filter_obj = MomentumSpaceFilter(n_qubits_x=3, n_qubits_y=3)

        # Create momentum grids
        converter = MomentumSpaceConverter(3, 3)
        kx_grid, ky_grid = converter.get_momentum_grid(real_size=10.0)

        # Create low-pass filter
        k_cutoff = 0.5
        lowpass = filter_obj.create_lowpass_filter(k_cutoff, kx_grid, ky_grid)

        # Check shape
        assert lowpass.shape == (8, 8)

        # Check that center has maximum value
        center_idx = 4
        assert lowpass[center_idx, center_idx] > 0.9

        # Check that values decrease with k
        assert np.all(lowpass >= 0.0)
        assert np.all(lowpass <= 1.0)

    def test_classical_filter_application(self):
        """Test classical filter application."""
        filter_obj = MomentumSpaceFilter(n_qubits_x=2, n_qubits_y=2)

        # Create test wave function in k-space
        psi_k = np.random.randn(4, 4) + 1j * np.random.randn(4, 4)

        # Create filter
        filter_mask = np.ones((4, 4))
        filter_mask[0, 0] = 0.0  # Block one k-mode

        # Apply filter
        psi_k_filtered = filter_obj.apply_filter_classical(psi_k, filter_mask)

        # Check that blocked mode is zero
        assert abs(psi_k_filtered[0, 0]) < 1e-10

        # Check that other modes are preserved
        assert np.allclose(psi_k_filtered[1:, 1:], psi_k[1:, 1:])


class TestMomentumAnalysis:
    """Test momentum distribution analysis."""

    def test_plane_wave_momentum(self):
        """Test that plane wave has sharp momentum peak."""
        n_qubits = 3

        # Create plane wave (k=0)
        qwf = QuantumWaveFunction(n_qubits, n_qubits)
        circuit = qwf.prepare_incident_wave()

        # Transform to momentum space
        converter = MomentumSpaceConverter(n_qubits, n_qubits)
        circuit_k = converter.transform_to_momentum(circuit)

        # Analyze
        analysis = analyze_momentum_distribution(circuit_k, n_qubits, n_qubits)

        # Mean momentum should be near zero
        assert np.abs(analysis["mean_k"][0]) < 0.1
        assert np.abs(analysis["mean_k"][1]) < 0.1

        # Check that all required keys are present
        assert "momentum_amplitudes" in analysis
        assert "momentum_probabilities" in analysis
        assert "kx_grid" in analysis
        assert "ky_grid" in analysis
        assert "mean_k" in analysis
        assert "k_spread" in analysis

    def test_gaussian_momentum_spread(self):
        """Test Gaussian wave packet momentum analysis."""
        n_qubits = 3

        # Create Gaussian wave packet
        x = np.linspace(-4, 4, 8)
        X, Y = np.meshgrid(x, x)
        psi_gauss = np.exp(-(X**2 + Y**2) / 2)

        qwf = QuantumWaveFunction(n_qubits, n_qubits)
        circuit = qwf.prepare_arbitrary_wave(psi_gauss)

        # Transform to momentum space
        converter = MomentumSpaceConverter(n_qubits, n_qubits)
        circuit_k = converter.transform_to_momentum(circuit)

        # Analyze
        analysis = analyze_momentum_distribution(circuit_k, n_qubits, n_qubits)

        # Gaussian should have finite momentum spread
        assert analysis["k_spread"][0] > 0
        assert analysis["k_spread"][1] > 0

        # Mean should be near zero (centered Gaussian)
        assert abs(analysis["mean_k"][0]) < 0.5
        assert abs(analysis["mean_k"][1]) < 0.5


class TestUncertaintyPrinciple:
    """Test Heisenberg uncertainty principle demonstration."""

    def test_uncertainty_relation(self):
        """Test that Δx·Δk ≥ 1/2 is satisfied."""
        result = demonstrate_uncertainty_principle(n_qubits=3, width_real=2.0)

        # Check all required keys
        assert "delta_x" in result
        assert "delta_y" in result
        assert "delta_kx" in result
        assert "delta_ky" in result
        assert "uncertainty_x" in result
        assert "uncertainty_y" in result
        assert "heisenberg_limit" in result
        assert "satisfies_uncertainty" in result

        # Check that uncertainty principle is satisfied
        assert result["satisfies_uncertainty"]
        assert result["uncertainty_x"] >= 0.4  # Close to Heisenberg limit
        assert result["uncertainty_y"] >= 0.4

    def test_narrow_real_space_wide_momentum(self):
        """Test that narrow real space → wide momentum space."""
        # Narrow in real space
        result_narrow = demonstrate_uncertainty_principle(n_qubits=3, width_real=0.5)

        # Wide in real space
        result_wide = demonstrate_uncertainty_principle(n_qubits=3, width_real=3.0)

        # Narrower real space should have wider momentum spread
        assert result_narrow["delta_kx"] > result_wide["delta_kx"]


class TestIntegration:
    """Integration tests for momentum space operations."""

    def test_complete_momentum_pipeline(self):
        """Test complete pipeline: prepare → transform → analyze → validate."""
        n_qubits = 3

        # Step 1: Prepare Gaussian wave packet
        x = np.linspace(-4, 4, 8)
        X, Y = np.meshgrid(x, x)
        psi_gauss = np.exp(-(X**2 + Y**2) / 2)

        qwf = QuantumWaveFunction(n_qubits, n_qubits)
        circuit_real = qwf.prepare_arbitrary_wave(psi_gauss)

        # Step 2: Transform to momentum space
        converter = MomentumSpaceConverter(n_qubits, n_qubits)
        circuit_k = converter.transform_to_momentum(circuit_real)

        # Step 3: Validate energy conservation
        validator = ParsevalValidator(tolerance=1e-10)
        parseval_result = validator.validate_transform(circuit_real, circuit_k)
        assert parseval_result["valid"]

        # Step 4: Analyze momentum distribution
        analysis = analyze_momentum_distribution(circuit_k, n_qubits, n_qubits)
        assert analysis["k_spread"][0] > 0

        # Step 5: Transform back to real space
        circuit_back = converter.transform_to_real(circuit_k)

        # Step 6: Validate round trip
        round_trip_result = validator.validate_round_trip(circuit_real, circuit_back)
        assert round_trip_result["valid"]
        assert round_trip_result["fidelity"] > 0.9999

        print("\n✓ Complete momentum space pipeline validated!")
        print(f"  Energy conservation: {parseval_result['relative_error']:.2e}")
        print(f"  Round-trip fidelity: {round_trip_result['fidelity']:.6f}")
        print(
            f"  Momentum spread: Δkx={analysis['k_spread'][0]:.3f}, "
            f"Δky={analysis['k_spread'][1]:.3f}"
        )
