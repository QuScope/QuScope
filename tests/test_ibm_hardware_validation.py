"""
Tests for IBM Hardware Validation Module

Week 4 Task 1.8: IBM Hardware Validation Tests

This module tests the IBMHardwareValidator class which validates
quantum CTEM circuits for deployment on real IBM Quantum hardware.
"""

import numpy as np
import pytest
from qiskit import QuantumCircuit

from quscope.quantum_ctem import (
    IBMDeviceProfile,
    IBMHardwareValidator,
    validate_ibm_deployment,
)


class TestIBMDeviceProfile:
    """Test IBM device profile configurations."""

    def test_ibm_kyoto_profile(self):
        """Test IBM Kyoto device profile."""
        profile = IBMDeviceProfile.ibm_kyoto()

        assert profile.name == "ibm_kyoto"
        assert profile.num_qubits == 127
        assert "cx" in profile.basis_gates
        assert profile.single_qubit_error > 0
        assert profile.two_qubit_error > profile.single_qubit_error
        assert profile.t1_us > 0
        assert profile.t2_us > 0

    def test_ibm_brisbane_profile(self):
        """Test IBM Brisbane device profile."""
        profile = IBMDeviceProfile.ibm_brisbane()

        assert profile.name == "ibm_brisbane"
        assert profile.num_qubits == 127
        assert profile.t2_us > 0
        # Brisbane has slightly better performance than Kyoto
        assert (
            profile.single_qubit_error
            <= IBMDeviceProfile.ibm_kyoto().single_qubit_error
        )

    def test_ibm_nazca_profile(self):
        """Test IBM Nazca device profile."""
        profile = IBMDeviceProfile.ibm_nazca()

        assert profile.name == "ibm_nazca"
        assert profile.num_qubits == 127
        assert len(profile.basis_gates) > 0

    def test_ibm_sherbrooke_profile(self):
        """Test IBM Sherbrooke device profile."""
        profile = IBMDeviceProfile.ibm_sherbrooke()

        assert profile.name == "ibm_sherbrooke"
        assert profile.num_qubits == 127
        # Sherbrooke has best coherence times
        assert profile.t2_us >= IBMDeviceProfile.ibm_kyoto().t2_us

    def test_create_backend(self):
        """Test backend creation from profile."""
        profile = IBMDeviceProfile.ibm_kyoto()
        backend = profile.create_backend()

        assert backend.num_qubits == 127
        assert hasattr(backend, "operation_names")
        assert "cx" in backend.operation_names

    def test_coupling_map(self):
        """Test coupling map is defined."""
        profile = IBMDeviceProfile.ibm_kyoto()

        assert profile.coupling_map is not None
        assert len(profile.coupling_map) > 0
        # Check it's a list of edges
        assert all(len(edge) == 2 for edge in profile.coupling_map)


class TestFidelityEstimation:
    """Test fidelity estimation functions."""

    def test_estimate_fidelity_simple_circuit(self):
        """Test fidelity estimation for simple circuit."""
        from quscope.quantum_ctem.ibm_hardware_validation import estimate_fidelity

        # Create simple circuit
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)

        device = IBMDeviceProfile.ibm_kyoto()
        fidelity = estimate_fidelity(qc, device)

        assert 0 < fidelity <= 1.0
        # Simple circuit should have high fidelity
        assert fidelity > 0.8

    @pytest.mark.xfail(reason="Pre-existing failure, tracked in issue #21", strict=False)
    def test_estimate_fidelity_complex_circuit(self):
        """Test fidelity estimation for complex circuit."""
        from quscope.quantum_ctem.ibm_hardware_validation import estimate_fidelity

        # Create more complex circuit
        qc = QuantumCircuit(4)
        for i in range(4):
            qc.h(i)
        for i in range(3):
            qc.cx(i, i + 1)
        for i in range(4):
            qc.rz(0.5, i)

        device = IBMDeviceProfile.ibm_kyoto()
        fidelity = estimate_fidelity(qc, device)

        assert 0 < fidelity <= 1.0
        # Complex circuit has lower fidelity
        assert fidelity < 0.9

    def test_fidelity_degrades_with_gates(self):
        """Test that fidelity decreases with more gates."""
        from quscope.quantum_ctem.ibm_hardware_validation import estimate_fidelity

        device = IBMDeviceProfile.ibm_kyoto()

        # Simple circuit
        qc1 = QuantumCircuit(2)
        qc1.h(0)
        fid1 = estimate_fidelity(qc1, device)

        # Same circuit with more gates
        qc2 = QuantumCircuit(2)
        qc2.h(0)
        qc2.cx(0, 1)
        qc2.cx(0, 1)
        fid2 = estimate_fidelity(qc2, device)

        # More gates → lower fidelity
        assert fid2 < fid1


class TestIBMHardwareValidator:
    """Test IBM hardware validator class."""

    def test_validator_initialization(self):
        """Test validator initialization."""
        validator = IBMHardwareValidator()

        assert len(validator.devices) == 4
        assert "ibm_kyoto" in validator.devices
        assert "ibm_brisbane" in validator.devices
        assert "ibm_nazca" in validator.devices
        assert "ibm_sherbrooke" in validator.devices

    def test_validate_circuit_for_ibm(self):
        """Test circuit validation for IBM device."""
        validator = IBMHardwareValidator()

        # Create test circuit
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)

        results = validator.validate_circuit_for_ibm(qc, "ibm_kyoto")

        assert "transpiled_circuit" in results
        assert "original_depth" in results
        assert "transpiled_depth" in results
        assert "estimated_fidelity" in results
        assert "warnings" in results
        assert results["device_name"] == "ibm_kyoto"

    def test_validate_circuit_invalid_device(self):
        """Test validation with invalid device name."""
        validator = IBMHardwareValidator()

        qc = QuantumCircuit(2)
        qc.h(0)

        with pytest.raises(ValueError, match="Unknown device"):
            validator.validate_circuit_for_ibm(qc, "invalid_device")

    def test_validate_for_device(self):
        """Test complete validation workflow."""
        validator = IBMHardwareValidator()

        results = validator.validate_for_device("ibm_kyoto", n_qubits=4)

        assert results["device_name"] == "ibm_kyoto"
        assert "estimated_fidelity" in results
        assert "transpiled_depth" in results
        assert "execution_time_us" in results
        assert results["estimated_fidelity"] > 0

    def test_validate_different_qubit_counts(self):
        """Test validation with different qubit counts."""
        validator = IBMHardwareValidator()

        # Test with 2, 4, 6 qubits
        for n_qubits in [2, 4, 6]:
            results = validator.validate_for_device("ibm_kyoto", n_qubits=n_qubits)
            assert results["transpiled_circuit"].num_qubits >= n_qubits // 2

    def test_compare_devices(self):
        """Test device comparison functionality."""
        validator = IBMHardwareValidator()

        comparison = validator.compare_devices(n_qubits=4)

        assert len(comparison) == 4
        assert all(
            device in comparison
            for device in ["ibm_kyoto", "ibm_brisbane", "ibm_nazca", "ibm_sherbrooke"]
        )

        # All should have fidelity estimates
        assert all("estimated_fidelity" in results for results in comparison.values())

    def test_test_qubit_mapping(self):
        """Test qubit mapping optimization."""
        validator = IBMHardwareValidator()

        results = validator.test_qubit_mapping("ibm_kyoto", n_qubits=4)

        # Should test 4 optimization levels (0-3)
        assert len(results) == 4
        assert all(f"opt_level_{i}" in results for i in range(4))

        # Higher optimization should generally give better fidelity
        fid_opt0 = results["opt_level_0"]["fidelity"]
        fid_opt3 = results["opt_level_3"]["fidelity"]
        # Optimization level 3 should be at least as good as level 0
        assert fid_opt3 >= fid_opt0 * 0.9  # Allow some variation

    @pytest.mark.xfail(reason="Pre-existing failure, tracked in issue #21", strict=False)
    def test_generate_deployment_guide(self):
        """Test deployment guide generation."""
        validator = IBMHardwareValidator()

        # Get comparison results
        comparison = validator.compare_devices(n_qubits=4)

        # Generate guide
        guide = validator.generate_deployment_guide(comparison)

        assert isinstance(guide, str)
        assert "IBM Quantum Deployment Guide" in guide
        assert "Device Comparison" in guide
        assert "Recommendation" in guide
        # Should mention all devices
        for device in ["ibm_kyoto", "ibm_brisbane", "ibm_nazca", "ibm_sherbrooke"]:
            assert device in guide


class TestValidationWarnings:
    """Test warning generation for problematic circuits."""

    def test_low_fidelity_warning(self):
        """Test warning for low estimated fidelity."""
        validator = IBMHardwareValidator()

        # Create very deep circuit that will have low fidelity
        qc = QuantumCircuit(4)
        for _ in range(20):  # Many layers
            for i in range(4):
                qc.h(i)
            for i in range(3):
                qc.cx(i, i + 1)

        results = validator.validate_circuit_for_ibm(qc, "ibm_kyoto")

        # Should have low fidelity warning
        assert len(results["warnings"]) > 0
        assert any("fidelity" in warning.lower() for warning in results["warnings"])

    def test_depth_increase_warning(self):
        """Test warning for significant depth increase during transpilation."""
        validator = IBMHardwareValidator()

        # Circuit that transpiles poorly
        qc = QuantumCircuit(3)
        qc.h(0)
        qc.t(1)
        qc.s(2)
        qc.cx(0, 1)
        qc.cx(1, 2)

        results = validator.validate_circuit_for_ibm(qc, "ibm_kyoto")

        # May have depth warning if transpilation increases depth significantly
        if results["transpiled_depth"] > 2 * results["original_depth"]:
            assert any("depth" in warning.lower() for warning in results["warnings"])


class TestValidationConvenienceFunction:
    """Test validate_ibm_deployment convenience function."""

    def test_validate_ibm_deployment(self):
        """Test IBM deployment validation."""
        results = validate_ibm_deployment("ibm_kyoto", n_qubits=4)

        assert "estimated_fidelity" in results
        assert "transpiled_depth" in results
        assert "warnings" in results
        assert results["device_name"] == "ibm_kyoto"

    def test_validate_all_devices(self):
        """Test validation for all devices."""
        devices = ["ibm_kyoto", "ibm_brisbane", "ibm_nazca", "ibm_sherbrooke"]

        for device in devices:
            results = validate_ibm_deployment(device, n_qubits=4)
            assert results["device_name"] == device
            assert results["estimated_fidelity"] > 0


class TestDeviceRecommendation:
    """Test device recommendation logic."""

    def test_sherbrooke_best_coherence(self):
        """Test that Sherbrooke has best coherence times."""
        devices = [
            IBMDeviceProfile.ibm_kyoto(),
            IBMDeviceProfile.ibm_brisbane(),
            IBMDeviceProfile.ibm_nazca(),
            IBMDeviceProfile.ibm_sherbrooke(),
        ]

        sherbrooke = IBMDeviceProfile.ibm_sherbrooke()

        # Sherbrooke should have highest or tied T2
        assert all(sherbrooke.t2_us >= d.t2_us for d in devices)

    def test_device_ranking(self):
        """Test that devices can be ranked by fidelity."""
        validator = IBMHardwareValidator()
        comparison = validator.compare_devices(n_qubits=4)

        # Sort by fidelity
        ranked = sorted(
            comparison.items(), key=lambda x: x[1]["estimated_fidelity"], reverse=True
        )

        # Should have 4 devices ranked
        assert len(ranked) == 4

        # Fidelities should be in descending order
        fidelities = [r[1]["estimated_fidelity"] for r in ranked]
        assert fidelities == sorted(fidelities, reverse=True)


class TestIntegrationWithQuantumCTEM:
    """Integration tests with quantum CTEM modules."""

    @pytest.mark.xfail(reason="Pre-existing failure, tracked in issue #21", strict=False)
    def test_validation_with_quantum_wave_function(self):
        """Test validation with real quantum wave function."""
        from quscope.quantum_ctem import QuantumWaveFunction

        validator = IBMHardwareValidator()
        qwf = QuantumWaveFunction(n_qubits_x=2, n_qubits_y=2)

        # Create test wave function
        psi = np.ones((4, 4)) / 4.0
        circuit = qwf.prepare_arbitrary_wave(psi)

        # Validate for IBM
        results = validator.validate_circuit_for_ibm(circuit, "ibm_kyoto")

        assert results["estimated_fidelity"] > 0
        assert results["transpiled_circuit"].num_qubits == 4

    @pytest.mark.xfail(reason="Pre-existing failure, tracked in issue #21", strict=False)
    def test_validation_preserves_circuit_functionality(self):
        """Test that transpilation preserves circuit behavior."""
        from quscope.quantum_ctem import QuantumWaveFunction

        validator = IBMHardwareValidator()
        qwf = QuantumWaveFunction(n_qubits_x=2, n_qubits_y=2)

        # Simple uniform state
        psi = np.ones((4, 4)) / 4.0
        circuit = qwf.prepare_arbitrary_wave(psi)

        # Validate
        results = validator.validate_circuit_for_ibm(circuit, "ibm_kyoto")

        # Transpiled circuit should still work
        transpiled = results["transpiled_circuit"]
        assert transpiled.num_qubits == circuit.num_qubits


class TestPerformanceMetrics:
    """Test performance tracking and metrics."""

    def test_validation_time_tracking(self):
        """Test that validation time is tracked."""
        validator = IBMHardwareValidator()

        results = validator.validate_for_device("ibm_kyoto", n_qubits=4)

        assert "validation_time" in results
        assert results["validation_time"] > 0
        assert results["validation_time"] < 10  # Should be reasonably fast

    def test_execution_time_estimation(self):
        """Test circuit execution time estimation."""
        validator = IBMHardwareValidator()

        results = validator.validate_for_device("ibm_kyoto", n_qubits=4)

        assert "execution_time_us" in results
        assert results["execution_time_us"] > 0
        # Should be less than coherence time for valid circuits
        # (though may exceed for complex circuits with warnings)


# Pytest markers
pytestmark = pytest.mark.ibm_validation
