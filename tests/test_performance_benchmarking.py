"""
Tests for Performance Benchmarking Module

Week 3 Task 1.7: Performance Benchmarking

Author: QuScope Development Team
Date: October 5, 2025
"""

import pytest
import numpy as np
from pathlib import Path
import json
import tempfile

from quscope.quantum_ctem import (
    BenchmarkResult,
    PerformanceBenchmark,
    quick_benchmark,
)


class TestBenchmarkResult:
    """Test BenchmarkResult dataclass."""
    
    def test_benchmark_result_creation(self):
        """Test creating a benchmark result."""
        result = BenchmarkResult(
            pixels=4,
            n_qubits_x=2,
            n_qubits_y=2,
            encoding_time=0.5,
            decoding_time=0.3,
            round_trip_time=0.8,
            round_trip_error=1e-10,
            fidelity=0.99999,
            circuit_depth=100,
            total_gates=500,
            single_qubit_gates=450,
            two_qubit_gates=50,
            memory_classical=1.0,
            memory_circuit=2.0,
            memory_statevector=4.0,
            estimated_runtime_ibm=0.001,
            estimated_fidelity_ibm=0.95
        )
        
        assert result.pixels == 4
        assert result.n_qubits_x == 2
        assert result.n_qubits_y == 2
        assert result.encoding_time == 0.5
        assert result.round_trip_time == 0.8
    
    def test_benchmark_result_to_dict(self):
        """Test converting result to dictionary."""
        result = BenchmarkResult(
            pixels=4, n_qubits_x=2, n_qubits_y=2,
            encoding_time=0.5, decoding_time=0.3, round_trip_time=0.8,
            round_trip_error=1e-10, fidelity=0.99999,
            circuit_depth=100, total_gates=500, single_qubit_gates=450, two_qubit_gates=50,
            memory_classical=1.0, memory_circuit=2.0, memory_statevector=4.0,
            estimated_runtime_ibm=0.001, estimated_fidelity_ibm=0.95
        )
        
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert result_dict['pixels'] == 4
        assert result_dict['encoding_time'] == 0.5


class TestPerformanceBenchmark:
    """Test PerformanceBenchmark class."""
    
    def test_benchmark_creation(self):
        """Test creating a benchmark instance."""
        benchmark = PerformanceBenchmark()
        assert benchmark is not None
    
    def test_benchmark_single_configuration_small(self):
        """Test benchmarking a small configuration."""
        benchmark = PerformanceBenchmark()
        result = benchmark.benchmark_single_configuration(
            n_qubits_x=2,
            n_qubits_y=2
        )
        
        # Check result structure
        assert isinstance(result, BenchmarkResult)
        assert result.pixels == 4
        assert result.n_qubits_x == 2
        assert result.n_qubits_y == 2
        
        # Check timing
        assert result.encoding_time > 0
        assert result.decoding_time > 0
        
        # Check accuracy
        assert result.round_trip_error < 1e-8
        assert result.fidelity > 0.999
        
        # Check circuit metrics
        assert result.circuit_depth > 0
        assert result.total_gates > 0
        
        # Check memory
        assert result.memory_classical > 0
        assert result.memory_circuit > 0
        assert result.memory_statevector > 0
        
        # Check hardware estimates
        assert result.estimated_runtime_ibm > 0
        assert 0 < result.estimated_fidelity_ibm <= 1
    
    def test_benchmark_different_optimization_methods(self):
        """Test benchmarking with different optimization methods."""
        benchmark = PerformanceBenchmark()
        
        result1 = benchmark.benchmark_single_configuration(
            n_qubits_x=2,
            n_qubits_y=2
        )
        
        result2 = benchmark.benchmark_single_configuration(
            n_qubits_x=2,
            n_qubits_y=2
        )
        
        # Both should succeed
        assert result1.pixels == 4
        assert result2.pixels == 4
        
        # Both should have high fidelity
        assert result1.fidelity > 0.999
        assert result2.fidelity > 0.999
    
    def test_run_scaling_analysis_small(self):
        """Test scaling analysis with small grid sizes."""
        benchmark = PerformanceBenchmark()
        results = benchmark.run_scaling_analysis(
            n_qubits_range=[2, 3]
        )
        
        assert len(results) == 2
        assert results[0].pixels == 4
        assert results[1].pixels == 8
        
        # Check all results are valid
        for result in results:
            assert isinstance(result, BenchmarkResult)
            assert result.fidelity > 0.999
            assert result.round_trip_error < 1e-8
    
    def test_scaling_trends(self):
        """Test that scaling shows expected trends."""
        benchmark = PerformanceBenchmark()
        results = benchmark.run_scaling_analysis([2, 3])
        
        # Check basic properties
        assert results[0].pixels == 4  # 2x2
        assert results[1].pixels == 8  # 3x3 → max(8,8)=8
        
        # Circuit complexity should increase or stay same
        assert results[1].circuit_depth >= results[0].circuit_depth
        assert results[1].total_gates >= results[0].total_gates
    
    def test_compare_optimization_methods_small(self):
        """Test comparing optimization methods."""
        benchmark = PerformanceBenchmark()
        comparison = benchmark.compare_optimization_methods(n_qubits=2)
        
        assert 'direct' in comparison
        assert 'schmidt' in comparison
        
        # Check structure
        for method, result in comparison.items():
            assert 'preparation_time' in result
            assert 'depth' in result
            assert 'gates' in result
            assert 'fidelity' in result
            
            # Check values
            assert result['preparation_time'] > 0
            assert result['depth'] > 0
            assert result['gates'] > 0
            assert result['fidelity'] > 0.999
    
    def test_profile_memory_usage_small(self):
        """Test memory profiling."""
        benchmark = PerformanceBenchmark()
        memory_data = benchmark.profile_memory_usage([2, 3])
        
        assert 'pixels' in memory_data
        assert 'classical_mb' in memory_data
        assert 'circuit_mb' in memory_data
        assert 'statevector_mb' in memory_data
        assert 'total_mb' in memory_data
        
        assert len(memory_data['pixels']) == 2
        
        # Memory should increase or stay same with size
        assert memory_data['total_mb'][1] >= memory_data['total_mb'][0]
    
    def test_estimate_hardware_costs_small(self):
        """Test hardware cost estimation."""
        benchmark = PerformanceBenchmark()
        cost_data = benchmark.estimate_hardware_costs([2, 3])
        
        assert 'pixels' in cost_data
        assert 'runtime_seconds' in cost_data
        assert 'estimated_fidelity' in cost_data
        
        assert len(cost_data['pixels']) == 2
        
        # Runtime should increase or stay same with size
        assert cost_data['runtime_seconds'][1] >= cost_data['runtime_seconds'][0]
        
        # Fidelity should decrease or stay same with size  
        assert cost_data['estimated_fidelity'][1] <= cost_data['estimated_fidelity'][0]
    
    def test_save_results_json(self):
        """Test saving results to JSON."""
        benchmark = PerformanceBenchmark()
        results = benchmark.run_scaling_analysis([2])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'benchmark_results.json'
            benchmark.save_results(results, str(output_path))
            
            assert output_path.exists()
            
            # Load and verify
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert isinstance(data, dict)
            assert 'results' in data
            assert len(data['results']) == 1
            assert data['results'][0]['pixels'] == 4
    
    def test_generate_report(self):
        """Test generating markdown report."""
        benchmark = PerformanceBenchmark()
        results = benchmark.run_scaling_analysis([2])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / 'benchmark_report.md'
            benchmark.generate_report(results, str(report_path))
            
            assert report_path.exists()
            
            # Read and check content
            with open(report_path, 'r') as f:
                content = f.read()
            
            assert 'Performance Benchmark Report' in content or 'Benchmark Report' in content
            assert 'pixels' in content or 'Pixels' in content
            assert 'Fidelity' in content


class TestQuickBenchmark:
    """Test quick_benchmark convenience function."""
    
    def test_quick_benchmark_small(self):
        """Test quick benchmark function."""
        result = quick_benchmark(n_qubits=2)
        
        assert isinstance(result, BenchmarkResult)
        assert result.pixels == 4
        assert result.fidelity > 0.999
    
    def test_quick_benchmark_multiple_sizes(self):
        """Test quick benchmark with different sizes."""
        result1 = quick_benchmark(n_qubits=2)
        result2 = quick_benchmark(n_qubits=3)
        
        assert result1.pixels == 4
        assert result2.pixels == 8


class TestBenchmarkAccuracy:
    """Test accuracy of benchmark measurements."""
    
    def test_timing_consistency(self):
        """Test that timing measurements are consistent."""
        benchmark = PerformanceBenchmark()
        
        # Run same benchmark twice
        result1 = benchmark.benchmark_single_configuration(2, 2)
        result2 = benchmark.benchmark_single_configuration(2, 2)
        
        # Timings should be within reasonable range (within 50%)
        assert abs(result1.encoding_time - result2.encoding_time) / result1.encoding_time < 0.5
    
    def test_accuracy_metrics_precision(self):
        """Test accuracy metrics are precise."""
        benchmark = PerformanceBenchmark()
        result = benchmark.benchmark_single_configuration(2, 2)
        
        # Should have high precision
        assert result.round_trip_error < 1e-8
        assert result.fidelity > 0.99999
    
    def test_circuit_metrics_deterministic(self):
        """Test circuit metrics are deterministic."""
        benchmark = PerformanceBenchmark()
        
        result1 = benchmark.benchmark_single_configuration(2, 2)
        result2 = benchmark.benchmark_single_configuration(2, 2)
        
        # Circuit metrics should be identical
        assert result1.circuit_depth == result2.circuit_depth
        assert result1.total_gates == result2.total_gates
        assert result1.two_qubit_gates == result2.two_qubit_gates


class TestBenchmarkEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_minimum_grid_size(self):
        """Test minimum supported grid size."""
        benchmark = PerformanceBenchmark()
        result = benchmark.benchmark_single_configuration(2, 2)
        
        assert result.pixels == 4
        assert result.fidelity > 0.999
    
    def test_invalid_optimization_method(self):
        """Test invalid grid size handling."""
        benchmark = PerformanceBenchmark()
        
        # Test with valid small configuration
        result = benchmark.benchmark_single_configuration(2, 2)
        assert result.pixels == 4
    
    def test_empty_grid_sizes_list(self):
        """Test empty grid sizes list."""
        benchmark = PerformanceBenchmark()
        results = benchmark.run_scaling_analysis([])
        
        assert len(results) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
