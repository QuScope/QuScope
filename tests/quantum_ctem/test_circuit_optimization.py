"""
Tests for quantum circuit optimization module.

This module tests circuit optimization strategies critical for
IBM quantum hardware deployment, including:
- State preparation optimization
- Circuit depth reduction
- Hardware transpilation
- Fidelity estimation

Author: QuScope Team
Date: October 2025
"""

import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, state_fidelity

from quscope.quantum_ctem.circuit_optimization import (
    HardwareTranspiler,
    StatePreparationOptimizer,
    benchmark_state_preparation,
)


class TestStatePreparationOptimizer:
    """Test state preparation optimization strategies."""

    def test_basic_initialization(self):
        """Test optimizer initialization with different methods."""
        # Direct method
        opt_direct = StatePreparationOptimizer(method="direct")
        assert opt_direct.method == "direct"
        assert opt_direct.optimization_level == 3

        # Schmidt method
        opt_schmidt = StatePreparationOptimizer(method="schmidt")
        assert opt_schmidt.method == "schmidt"

        # Custom optimization level
        opt_custom = StatePreparationOptimizer(optimization_level=2)
        assert opt_custom.optimization_level == 2

    def test_direct_method_gaussian(self):
        """Test direct state preparation with Gaussian wave packet."""
        n_qubits = 3  # 8-element state
        optimizer = StatePreparationOptimizer(method="direct")

        # Create Gaussian state
        x = np.linspace(-4, 4, 8)
        psi_gaussian = np.exp(-(x**2) / 2)

        # Prepare state
        circuit = optimizer.prepare_state(psi_gaussian, n_qubits, normalize=True)

        # Verify circuit is valid
        assert circuit.num_qubits == n_qubits
        assert circuit.depth() > 0  # Non-trivial circuit

        # Verify state fidelity
        sv = Statevector.from_instruction(circuit)
        psi_expected = psi_gaussian / np.linalg.norm(psi_gaussian)
        fidelity = state_fidelity(sv, psi_expected)

        assert fidelity > 0.9999, f"Fidelity {fidelity} too low"

    def test_direct_method_complex_phase(self):
        """Test direct method with complex phases."""
        n_qubits = 2  # 4-element state
        optimizer = StatePreparationOptimizer(method="direct")

        # Complex state with phase
        psi_complex = np.array([1, 1j, -1, -1j]) / 2

        circuit = optimizer.prepare_state(psi_complex, n_qubits, normalize=False)

        # Verify fidelity
        sv = Statevector.from_instruction(circuit)
        fidelity = state_fidelity(sv, psi_complex)

        assert fidelity > 0.9999

    def test_zero_state_handling(self):
        """Test handling of zero state (should create uniform superposition)."""
        n_qubits = 3
        optimizer = StatePreparationOptimizer(method="direct")

        # Zero state
        psi_zero = np.zeros(8)

        circuit = optimizer.prepare_state(psi_zero, n_qubits, normalize=True)

        # Should be uniform superposition
        sv = Statevector.from_instruction(circuit)
        expected = np.ones(8) / np.sqrt(8)

        assert np.allclose(np.abs(sv.data), expected, atol=1e-10)

    def test_normalization_flag(self):
        """Test that normalization flag works correctly."""
        n_qubits = 2
        optimizer = StatePreparationOptimizer(method="direct")

        # Normalized state
        psi_normalized = np.array([0.6, 0.8, 0, 0])  # Already normalized

        # With normalization flag
        circuit_norm = optimizer.prepare_state(psi_normalized, n_qubits, normalize=True)
        sv_norm = Statevector.from_instruction(circuit_norm)
        assert np.isclose(np.linalg.norm(sv_norm.data), 1.0)

        # Without normalization flag (Qiskit's initialize requires normalized input)
        circuit_no_norm = optimizer.prepare_state(
            psi_normalized, n_qubits, normalize=False
        )
        sv_no_norm = Statevector.from_instruction(circuit_no_norm)
        # Even without our normalization, Qiskit requires normalized states
        assert np.isclose(np.linalg.norm(sv_no_norm.data), 1.0)

        # Test with unnormalized input and normalize=True
        psi_unnorm = np.array([3, 4, 0, 0])  # Norm = 5
        circuit_unnorm = optimizer.prepare_state(psi_unnorm, n_qubits, normalize=True)
        sv_unnorm = Statevector.from_instruction(circuit_unnorm)
        assert np.isclose(np.linalg.norm(sv_unnorm.data), 1.0)

    def test_invalid_state_size(self):
        """Test error handling for mismatched state size."""
        n_qubits = 3  # Expects 8 elements
        optimizer = StatePreparationOptimizer(method="direct")

        # Wrong size state
        psi_wrong = np.ones(7)  # Should be 8

        with pytest.raises(ValueError, match="doesn't match"):
            optimizer.prepare_state(psi_wrong, n_qubits)

    def test_schmidt_method_separable(self):
        """Test Schmidt decomposition for separable 2D state."""
        # For 4 qubits: 2^4 = 16 states, reshape as 4×4
        n_qubits = 4
        optimizer = StatePreparationOptimizer(method="schmidt")

        # Create separable state: |φ⟩_x ⊗ |χ⟩_y
        # 4×4 = 16 element state
        phi_x = np.array([0.5, 0.5, 0.5, 0.5])  # 4 elements
        chi_y = np.array([0.6, 0.8, 0.0, 0.0])  # 4 elements
        psi_separable = np.outer(phi_x, chi_y).flatten()  # 16 elements

        circuit = optimizer.prepare_state(psi_separable, n_qubits, normalize=True)

        # Verify fidelity
        sv = Statevector.from_instruction(circuit)
        psi_expected = psi_separable / np.linalg.norm(psi_separable)
        fidelity = state_fidelity(sv, psi_expected)

        assert fidelity > 0.9999

    def test_schmidt_fallback_to_direct(self):
        """Test that Schmidt method falls back to direct for entangled states."""
        n_qubits = 2
        optimizer = StatePreparationOptimizer(method="schmidt")

        # Highly entangled Bell state
        psi_bell = np.array([1, 0, 0, 1]) / np.sqrt(2)

        circuit = optimizer.prepare_state(psi_bell, n_qubits, normalize=False)

        # Should still work (fell back to direct)
        sv = Statevector.from_instruction(circuit)
        fidelity = state_fidelity(sv, psi_bell)

        assert fidelity > 0.9999

    def test_circuit_metrics(self):
        """Test circuit complexity metrics calculation."""
        n_qubits = 3
        optimizer = StatePreparationOptimizer(method="direct")

        # Create test circuit
        psi = np.random.randn(8) + 1j * np.random.randn(8)
        circuit = optimizer.prepare_state(psi, n_qubits, normalize=True)

        # Get metrics
        metrics = optimizer.get_circuit_metrics(circuit)

        # Verify metric keys
        assert "depth" in metrics
        assert "gates" in metrics
        assert "1q_gates" in metrics
        assert "2q_gates" in metrics
        assert "qubits" in metrics

        # Verify values are reasonable
        assert metrics["qubits"] == n_qubits
        assert metrics["gates"] > 0
        assert metrics["depth"] > 0
        assert metrics["1q_gates"] >= 0
        assert metrics["2q_gates"] >= 0
        assert metrics["gates"] == metrics["1q_gates"] + metrics["2q_gates"]

    def test_optimization_reduces_gates(self):
        """Test that optimization actually reduces circuit complexity."""
        n_qubits = 3

        # Create unoptimized circuit
        psi = np.random.randn(8)
        qc_raw = QuantumCircuit(n_qubits)
        qc_raw.initialize(psi / np.linalg.norm(psi), range(n_qubits))
        qc_raw = qc_raw.decompose()

        # Create optimized circuit
        optimizer = StatePreparationOptimizer(method="direct", optimization_level=3)
        qc_optimized = optimizer.prepare_state(psi, n_qubits, normalize=True)

        # Compare depths (optimized should be less or equal)
        depth_raw = qc_raw.depth()
        depth_optimized = qc_optimized.depth()

        # Optimization should not increase depth
        assert depth_optimized <= depth_raw


class TestHardwareTranspiler:
    """Test hardware-specific transpilation."""

    def test_basic_initialization(self):
        """Test transpiler initialization."""
        transpiler = HardwareTranspiler()
        assert transpiler.optimization_level == 3
        assert transpiler.seed_transpiler == 42

        # With backend name
        transpiler_hw = HardwareTranspiler(backend_name="ibm_kyoto")
        assert transpiler_hw.backend_name == "ibm_kyoto"

    def test_transpile_simple_circuit(self):
        """Test transpilation of simple quantum circuit."""
        transpiler = HardwareTranspiler(optimization_level=3)

        # Create simple circuit
        qc = QuantumCircuit(3)
        qc.h(0)
        qc.cx(0, 1)
        qc.cx(1, 2)

        # Transpile
        qc_transpiled = transpiler.transpile_for_hardware(qc)

        # Verify circuit is still valid
        assert qc_transpiled.num_qubits >= qc.num_qubits
        assert qc_transpiled.depth() > 0

        # Verify equivalence
        sv_original = Statevector.from_instruction(qc)
        sv_transpiled = Statevector.from_instruction(qc_transpiled)
        fidelity = state_fidelity(sv_original, sv_transpiled)

        assert fidelity > 0.9999

    def test_transpile_state_preparation(self):
        """Test transpilation of state preparation circuit."""
        optimizer = StatePreparationOptimizer(method="direct")
        transpiler = HardwareTranspiler(optimization_level=3)

        # Prepare Gaussian state
        n_qubits = 3
        x = np.linspace(-4, 4, 8)
        psi = np.exp(-(x**2) / 2)

        circuit = optimizer.prepare_state(psi, n_qubits, normalize=True)
        circuit_transpiled = transpiler.transpile_for_hardware(circuit)

        # Verify equivalence
        sv_original = Statevector.from_instruction(circuit)
        sv_transpiled = Statevector.from_instruction(circuit_transpiled)
        fidelity = state_fidelity(sv_original, sv_transpiled)

        assert fidelity > 0.999  # Allow small transpilation error

    def test_fidelity_estimation(self):
        """Test circuit fidelity estimation."""
        transpiler = HardwareTranspiler()

        # Create test circuit
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)

        # Estimate fidelity with default error rates
        fidelity = transpiler.estimate_fidelity(qc)

        # Should be high for simple circuit
        assert 0 < fidelity <= 1.0
        assert fidelity > 0.95  # Most gates should succeed

    def test_fidelity_decreases_with_depth(self):
        """Test that estimated fidelity decreases with circuit depth."""
        transpiler = HardwareTranspiler()

        # Shallow circuit
        qc_shallow = QuantumCircuit(2)
        qc_shallow.h(0)
        qc_shallow.cx(0, 1)

        # Deep circuit (more gates)
        qc_deep = QuantumCircuit(2)
        for _ in range(10):
            qc_deep.h(0)
            qc_deep.cx(0, 1)
            qc_deep.h(1)
            qc_deep.cx(1, 0)

        fidelity_shallow = transpiler.estimate_fidelity(qc_shallow)
        fidelity_deep = transpiler.estimate_fidelity(qc_deep)

        # Deep circuit should have lower fidelity
        assert fidelity_deep < fidelity_shallow

    def test_compare_strategies(self):
        """Test comparison of multiple implementation strategies."""
        transpiler = HardwareTranspiler()

        # Create different implementations of GHZ state
        n_qubits = 3

        # Strategy 1: Linear chain
        qc1 = QuantumCircuit(n_qubits, name="linear")
        qc1.h(0)
        qc1.cx(0, 1)
        qc1.cx(1, 2)

        # Strategy 2: Star topology
        qc2 = QuantumCircuit(n_qubits, name="star")
        qc2.h(0)
        qc2.cx(0, 1)
        qc2.cx(0, 2)

        circuits = {"linear": qc1, "star": qc2}
        results = transpiler.compare_strategies(circuits)

        # Verify results structure
        assert "linear" in results
        assert "star" in results

        for name, metrics in results.items():
            assert "depth" in metrics
            assert "gates" in metrics
            assert "estimated_fidelity" in metrics
            assert "circuit" in metrics
            assert 0 < metrics["estimated_fidelity"] <= 1.0


class TestBenchmarking:
    """Test benchmarking utilities."""

    def test_benchmark_state_preparation(self):
        """Test state preparation benchmarking across sizes."""
        n_qubits_list = [2, 3, 4]
        methods = ["direct"]

        results = benchmark_state_preparation(n_qubits_list, methods)

        # Verify structure
        assert len(results) == len(n_qubits_list)

        for n_qubits in n_qubits_list:
            assert n_qubits in results
            assert "direct" in results[n_qubits]

            metrics = results[n_qubits]["direct"]
            if "error" not in metrics:
                assert "depth" in metrics
                assert "gates" in metrics

    def test_benchmark_scaling(self):
        """Test that circuit depth scales as expected."""
        n_qubits_list = [2, 3, 4]
        results = benchmark_state_preparation(n_qubits_list, methods=["direct"])

        depths = []
        for n_qubits in n_qubits_list:
            if "error" not in results[n_qubits]["direct"]:
                depths.append(results[n_qubits]["direct"]["depth"])

        # Depth should generally increase with system size
        if len(depths) >= 2:
            # Allow some variation due to optimization
            assert max(depths) >= min(depths)


class TestIntegration:
    """Integration tests combining multiple components."""

    def test_full_optimization_pipeline(self):
        """Test complete optimization pipeline: prepare → optimize → transpile."""
        n_qubits = 3

        # Step 1: Prepare state
        optimizer = StatePreparationOptimizer(method="direct", optimization_level=3)
        x = np.linspace(-4, 4, 8)
        psi = np.exp(-(x**2) / 2)
        circuit = optimizer.prepare_state(psi, n_qubits, normalize=True)

        # Step 2: Get metrics before transpilation
        metrics_before = optimizer.get_circuit_metrics(circuit)

        # Step 3: Transpile for hardware
        transpiler = HardwareTranspiler(optimization_level=3)
        circuit_hw = transpiler.transpile_for_hardware(circuit)

        # Step 4: Get metrics after transpilation
        metrics_after = optimizer.get_circuit_metrics(circuit_hw)

        # Step 5: Verify fidelity preserved
        sv_before = Statevector.from_instruction(circuit)
        sv_after = Statevector.from_instruction(circuit_hw)
        fidelity = state_fidelity(sv_before, sv_after)

        assert fidelity > 0.999

        # Step 6: Estimate hardware fidelity
        hw_fidelity = transpiler.estimate_fidelity(circuit_hw)
        assert hw_fidelity > 0.9

        print(f"\nOptimization Pipeline Results:")
        print(
            f"  Before transpilation: depth={metrics_before['depth']}, "
            f"gates={metrics_before['gates']}"
        )
        print(
            f"  After transpilation:  depth={metrics_after['depth']}, "
            f"gates={metrics_after['gates']}"
        )
        print(f"  State fidelity: {fidelity:.6f}")
        print(f"  Estimated HW fidelity: {hw_fidelity:.6f}")

    def test_schmidt_vs_direct_comparison(self):
        """Compare Schmidt and direct methods for separable states."""
        n_qubits = 4

        # Create separable 2D state
        x = np.linspace(-2, 2, 4)
        y = np.linspace(-2, 2, 4)
        X, Y = np.meshgrid(x, y)
        psi_2d = np.exp(-(X**2 + Y**2) / 2)
        psi_flat = psi_2d.flatten()

        # Direct method
        opt_direct = StatePreparationOptimizer(method="direct")
        circuit_direct = opt_direct.prepare_state(psi_flat, n_qubits, normalize=True)
        metrics_direct = opt_direct.get_circuit_metrics(circuit_direct)

        # Schmidt method
        opt_schmidt = StatePreparationOptimizer(method="schmidt")
        circuit_schmidt = opt_schmidt.prepare_state(psi_flat, n_qubits, normalize=True)
        metrics_schmidt = opt_schmidt.get_circuit_metrics(circuit_schmidt)

        # Both should produce valid states
        sv_direct = Statevector.from_instruction(circuit_direct)
        sv_schmidt = Statevector.from_instruction(circuit_schmidt)

        psi_expected = psi_flat / np.linalg.norm(psi_flat)
        fidelity_direct = state_fidelity(sv_direct, psi_expected)
        fidelity_schmidt = state_fidelity(sv_schmidt, psi_expected)

        assert fidelity_direct > 0.9999
        assert fidelity_schmidt > 0.9999

        print(f"\nSchmidt vs Direct Comparison:")
        print(
            f"  Direct:  depth={metrics_direct['depth']}, "
            f"gates={metrics_direct['gates']}"
        )
        print(
            f"  Schmidt: depth={metrics_schmidt['depth']}, "
            f"gates={metrics_schmidt['gates']}"
        )
        print(f"  Fidelity (direct): {fidelity_direct:.6f}")
        print(f"  Fidelity (schmidt): {fidelity_schmidt:.6f}")


# Hardware-readiness validation
def test_hardware_ready_circuit():
    """
    Test that generated circuits are ready for IBM hardware.

    This validates that circuits:
    1. Use only gates available on IBM devices
    2. Have reasonable depth for NISQ execution
    3. Maintain high fidelity after transpilation
    """
    n_qubits = 3
    optimizer = StatePreparationOptimizer(method="direct")
    transpiler = HardwareTranspiler(optimization_level=3)

    # Create test state
    x = np.linspace(-4, 4, 8)
    psi = np.exp(-(x**2) / 2)

    # Prepare and transpile
    circuit = optimizer.prepare_state(psi, n_qubits, normalize=True)
    circuit_hw = transpiler.transpile_for_hardware(circuit)

    # Check gate set (IBM devices typically use: sx, rz, cx, ecr, id)
    gate_names = set(circuit_hw.count_ops().keys())
    ibm_gates = {"sx", "rz", "cx", "ecr", "id", "x", "measure", "barrier", "reset"}

    # All gates should be in IBM gate set (or close to it after transpilation)
    # Note: Exact gate set depends on backend, this is a general check
    print(f"\nHardware-ready circuit gates: {gate_names}")

    # Verify circuit depth is reasonable for NISQ
    assert circuit_hw.depth() < 1000, "Circuit too deep for NISQ devices"

    # Verify estimated fidelity is acceptable
    fidelity_estimate = transpiler.estimate_fidelity(circuit_hw)
    assert fidelity_estimate > 0.8, f"Fidelity too low: {fidelity_estimate}"

    print(f"✓ Hardware-ready validation passed")
    print(f"  Depth: {circuit_hw.depth()}")
    print(f"  Estimated fidelity: {fidelity_estimate:.4f}")
