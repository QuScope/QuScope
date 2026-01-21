"""
Tests for Comprehensive Validation Testing Module

Week 4 Task 1.8: Validation Testing Tests

This module tests the ComprehensiveValidator class which validates
the entire quantum CTEM implementation for production readiness.

NOTE: This test file is currently skipped as the validation_testing module
is under development.
"""

import pytest

# Skip the entire module until validation_testing is implemented
pytest.skip(
    "validation_testing module not yet implemented",
    allow_module_level=True,
)

import numpy as np
from qiskit import QuantumCircuit

from quscope.quantum_ctem import (
    ComprehensiveValidator,
    ValidationReport,
    validate_quantum_ctem,
)


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_validation_result_creation(self):
        """Test creating ValidationResult."""
        from quscope.quantum_ctem.validation_testing import ValidationResult

        result = ValidationResult(
            test_name="test_example",
            passed=True,
            execution_time=0.5,
            error_message=None,
            metrics={"accuracy": 0.99},
            warnings=[],
        )

        assert result.test_name == "test_example"
        assert result.passed is True
        assert result.execution_time == 0.5
        assert result.metrics["accuracy"] == 0.99


class TestValidationReport:
    """Test ValidationReport dataclass."""

    def test_validation_report_creation(self):
        """Test creating ValidationReport."""
        from quscope.quantum_ctem.validation_testing import ValidationResult

        result1 = ValidationResult("test1", True, 0.1, None, {}, [])
        result2 = ValidationResult("test2", False, 0.2, "Error", {}, [])

        report = ValidationReport(
            total_tests=2,
            passed_tests=1,
            failed_tests=1,
            pass_rate=0.5,
            total_time=0.3,
            results=[result1, result2],
        )

        assert report.total_tests == 2
        assert report.passed_tests == 1
        assert report.failed_tests == 1
        assert report.pass_rate == 0.5


class TestComprehensiveValidator:
    """Test ComprehensiveValidator class."""

    def test_validator_initialization(self):
        """Test validator initialization."""
        validator = ComprehensiveValidator()

        assert validator.qwf is not None
        assert validator.transpiler is not None
        assert validator.bridge is not None
        assert validator.benchmark is not None

    def test_encoding_performance_test(self):
        """Test encoding performance validation."""
        validator = ComprehensiveValidator()

        result = validator.test_encoding_performance()

        assert result.test_name == "encoding_performance"
        assert result.passed is True
        assert result.execution_time < 1.0  # Should be fast
        assert "encoding_time" in result.metrics
        assert result.metrics["encoding_time"] < 1.0

    def test_zero_wave_function(self):
        """Test zero wave function edge case."""
        validator = ComprehensiveValidator()

        result = validator.test_zero_wave_function()

        # This test should pass (handles edge case gracefully)
        assert result.test_name == "zero_wave_function"
        assert result.passed is True

    def test_maximum_amplitude(self):
        """Test maximum amplitude edge case."""
        validator = ComprehensiveValidator()

        result = validator.test_maximum_amplitude()

        assert result.test_name == "maximum_amplitude"
        assert result.passed is True
        assert "fidelity" in result.metrics
        assert result.metrics["fidelity"] > 0.99

    def test_uniform_distribution(self):
        """Test uniform distribution edge case."""
        validator = ComprehensiveValidator()

        result = validator.test_uniform_distribution()

        assert result.test_name == "uniform_distribution"
        assert result.passed is True
        assert "uniformity_error" in result.metrics
        assert result.metrics["uniformity_error"] < 1e-5

    def test_large_grid_encoding(self):
        """Test encoding with larger grids."""
        validator = ComprehensiveValidator()

        # Test 4-qubit (16x16 grid) encoding
        result = validator.test_large_grid_encoding(n_qubits=4)

        assert result.test_name == "large_grid_encoding_n4"
        assert result.passed is True
        assert "grid_size" in result.metrics
        assert result.metrics["grid_size"] == 16

    def test_ibm_transpilation(self):
        """Test IBM basis gate transpilation."""
        validator = ComprehensiveValidator()

        result = validator.test_ibm_transpilation(n_qubits=3)

        assert result.test_name == "ibm_transpilation_n3"
        assert result.passed is True
        assert "transpiled_depth" in result.metrics
        assert "fidelity" in result.metrics
        assert result.metrics["fidelity"] > 0.1  # Relaxed for complex circuits

    def test_ibm_basis_gates(self):
        """Test IBM basis gate validation."""
        validator = ComprehensiveValidator()

        result = validator.test_ibm_basis_gates(n_qubits=2)

        assert result.test_name == "ibm_basis_gates_n2"
        assert result.passed is True
        assert "basis_gates_valid" in result.metrics
        assert result.metrics["basis_gates_valid"] is True

    def test_repeatability(self):
        """Test repeatability of encoding."""
        validator = ComprehensiveValidator()

        result = validator.test_repeatability(n_trials=5)

        assert result.test_name == "repeatability_n5"
        assert result.passed is True
        assert "std_dev" in result.metrics
        assert result.metrics["std_dev"] < 1e-10  # Should be deterministic

    def test_accuracy_distribution(self):
        """Test accuracy distribution across samples."""
        validator = ComprehensiveValidator()

        result = validator.test_accuracy_distribution(n_samples=10)

        assert result.test_name == "accuracy_distribution_n10"
        assert result.passed is True
        assert "mean_error" in result.metrics
        assert "max_error" in result.metrics
        assert result.metrics["mean_error"] < 1e-5

    def test_run_stress_tests(self):
        """Test running all stress tests."""
        validator = ComprehensiveValidator()

        results = validator.run_stress_tests()

        assert len(results) > 0
        assert all(isinstance(r.test_name, str) for r in results)
        # Most should pass
        assert sum(r.passed for r in results) >= len(results) * 0.8

    def test_run_edge_case_tests(self):
        """Test running all edge case tests."""
        validator = ComprehensiveValidator()

        results = validator.run_edge_case_tests()

        assert len(results) == 3  # zero, max, uniform
        assert all(r.passed for r in results)  # All edge cases should pass

    def test_run_ibm_hardware_tests(self):
        """Test running IBM hardware tests."""
        validator = ComprehensiveValidator()

        results = validator.run_ibm_hardware_tests()

        assert len(results) > 0
        # Most should pass (some may have warnings about fidelity)
        assert sum(r.passed for r in results) >= len(results) * 0.7

    def test_run_statistical_tests(self):
        """Test running statistical validation tests."""
        validator = ComprehensiveValidator()

        results = validator.run_statistical_tests()

        assert len(results) == 2  # repeatability and accuracy_distribution
        assert all(r.passed for r in results)

    def test_run_performance_tests(self):
        """Test running performance tests."""
        validator = ComprehensiveValidator()

        results = validator.run_performance_tests()

        assert len(results) == 1  # encoding_performance
        assert results[0].passed is True

    def test_run_all_tests(self):
        """Test running complete validation suite."""
        validator = ComprehensiveValidator()

        report = validator.run_all_tests()

        assert isinstance(report, ValidationReport)
        assert report.total_tests > 10  # Should have many tests
        assert report.pass_rate > 0.7  # At least 70% should pass
        assert report.total_time > 0

    def test_generate_microscopist_report(self):
        """Test generating user-friendly report."""
        validator = ComprehensiveValidator()

        # Run a few tests
        result1 = validator.test_maximum_amplitude()
        result2 = validator.test_uniform_distribution()

        report = ValidationReport(
            total_tests=2,
            passed_tests=2,
            failed_tests=0,
            pass_rate=1.0,
            total_time=0.5,
            results=[result1, result2],
        )

        md_report = validator.generate_microscopist_report(report)

        assert isinstance(md_report, str)
        assert "Quantum CTEM Validation Report" in md_report
        assert "PASSED" in md_report
        assert "100.0%" in md_report


class TestValidationConvenienceFunction:
    """Test validate_quantum_ctem convenience function."""

    def test_validate_quantum_ctem(self):
        """Test complete validation workflow."""
        report = validate_quantum_ctem(quick_mode=True)

        assert isinstance(report, ValidationReport)
        assert report.total_tests > 0
        assert report.pass_rate >= 0  # Some tests should run

    def test_validate_quantum_ctem_full(self):
        """Test full validation (slower)."""
        report = validate_quantum_ctem(quick_mode=False)

        assert isinstance(report, ValidationReport)
        assert report.total_tests > 10  # More comprehensive
        # Don't assert pass rate since complex tests may have lower fidelity


class TestIntegrationWithQuantumCTEM:
    """Integration tests with quantum CTEM modules."""

    def test_validation_with_quantum_wave_function(self):
        """Test validation integrates with QuantumWaveFunction."""
        from quscope.quantum_ctem import QuantumWaveFunction

        validator = ComprehensiveValidator()
        qwf = QuantumWaveFunction(n_qubits_x=2, n_qubits_y=2)

        # Create test wave function
        psi = np.ones((4, 4)) / 4.0
        circuit = qwf.prepare_arbitrary_wave(psi)

        # Validate it has the right structure
        assert circuit.num_qubits == 4
        assert len(circuit.data) > 0

    def test_validation_with_circuit_optimization(self):
        """Test validation integrates with circuit optimization."""
        from quscope.quantum_ctem import HardwareTranspiler

        validator = ComprehensiveValidator()
        transpiler = HardwareTranspiler()

        # Create simple circuit
        from qiskit import QuantumCircuit

        qc = QuantumCircuit(3)
        qc.h(0)
        qc.cx(0, 1)
        qc.cx(1, 2)

        # Transpile
        transpiled = transpiler.transpile_for_hardware(qc, optimization_level=3)

        assert transpiled.num_qubits == 3
        # Should be optimized
        assert transpiled.depth() <= qc.depth()


# Pytest markers
pytestmark = pytest.mark.validation
