"""
Performance Benchmarking Suite for Quantum CTEM

Comprehensive performance analysis tools for quantum CTEM implementations:
- Encoding/decoding timing analysis
- Circuit complexity scaling (depth, gates, qubits)
- Memory profiling
- Hardware execution time estimates
- Quantum vs classical comparison

Week 3 Task 1.7: Performance Benchmarking

Author: QuScope Development Team
Date: October 5, 2025
"""

import time
import numpy as np
import psutil
import os
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, asdict
import json
from pathlib import Path

from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector

from .quantum_wave_function import QuantumWaveFunction
from .circuit_optimization import StatePreparationOptimizer, HardwareTranspiler
from .classical_integration import QuantumClassicalBridge


@dataclass
class BenchmarkResult:
    """Container for benchmark results."""
    
    # Configuration
    n_qubits_x: int
    n_qubits_y: int
    pixels: int
    
    # Timing (seconds)
    encoding_time: float
    decoding_time: float
    round_trip_time: float
    
    # Circuit metrics
    circuit_depth: int
    total_gates: int
    single_qubit_gates: int
    two_qubit_gates: int
    
    # Memory (MB)
    memory_classical: float
    memory_circuit: float
    memory_statevector: float
    
    # Accuracy
    round_trip_error: float
    fidelity: float
    
    # Hardware estimates
    estimated_runtime_ibm: float  # seconds
    estimated_fidelity_ibm: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class PerformanceBenchmark:
    """
    Comprehensive performance benchmarking for quantum CTEM.
    
    Measures:
    - Encoding/decoding speed
    - Circuit complexity scaling
    - Memory usage
    - Hardware deployment estimates
    - Quantum vs classical overhead
    
    Example:
        >>> benchmark = PerformanceBenchmark()
        >>> 
        >>> # Run scaling analysis
        >>> results = benchmark.run_scaling_analysis(
        ...     n_qubits_range=[2, 3, 4, 5],
        ...     num_trials=10
        ... )
        >>> 
        >>> # Visualize results
        >>> benchmark.plot_scaling_results(results)
        >>> 
        >>> # Generate report
        >>> benchmark.generate_report(results, output_file='benchmark_report.md')
    """
    
    def __init__(self, random_seed: Optional[int] = 42):
        """
        Initialize benchmark suite.
        
        Args:
            random_seed: Random seed for reproducibility
        """
        self.random_seed = random_seed
        if random_seed is not None:
            np.random.seed(random_seed)
        
        # Process for memory profiling
        self.process = psutil.Process(os.getpid())
    
    def _get_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024
    
    def _create_test_wave_function(self, pixels: int) -> np.ndarray:
        """Create test wave function (Gaussian)."""
        x = np.linspace(-4, 4, pixels)
        X, Y = np.meshgrid(x, x)
        psi = np.exp(-(X**2 + Y**2) / 4.0) * np.exp(1j * 0.5 * X)
        psi = psi / np.linalg.norm(psi)
        return psi
    
    def benchmark_single_configuration(
        self,
        n_qubits_x: int,
        n_qubits_y: int,
        num_trials: int = 5
    ) -> BenchmarkResult:
        """
        Benchmark a single grid configuration.
        
        Args:
            n_qubits_x: Number of qubits for x dimension
            n_qubits_y: Number of qubits for y dimension
            num_trials: Number of trials to average
        
        Returns:
            BenchmarkResult with all metrics
        """
        pixels_x = 2**n_qubits_x
        pixels_y = 2**n_qubits_y
        pixels = max(pixels_x, pixels_y)
        
        # Initialize components
        qwf = QuantumWaveFunction(n_qubits_x, n_qubits_y)
        bridge = QuantumClassicalBridge(n_qubits_x, n_qubits_y)
        
        # Create test wave function
        psi = self._create_test_wave_function(pixels)
        if pixels_x != pixels or pixels_y != pixels:
            psi = psi[:pixels_x, :pixels_y]
        
        # Measure classical memory
        mem_before = self._get_memory_mb()
        psi_copy = psi.copy()
        mem_classical = self._get_memory_mb() - mem_before
        
        # Timing arrays
        encoding_times = []
        decoding_times = []
        errors = []
        
        for _ in range(num_trials):
            # Measure encoding time
            start = time.perf_counter()
            circuit = bridge.classical_to_quantum(psi)
            encoding_time = time.perf_counter() - start
            encoding_times.append(encoding_time)
            
            # Measure decoding time
            start = time.perf_counter()
            psi_decoded = bridge.quantum_to_classical(circuit)
            decoding_time = time.perf_counter() - start
            decoding_times.append(decoding_time)
            
            # Measure error
            error = np.max(np.abs(psi - psi_decoded))
            errors.append(error)
        
        # Average results
        encoding_time = np.mean(encoding_times)
        decoding_time = np.mean(decoding_times)
        round_trip_time = encoding_time + decoding_time
        round_trip_error = np.mean(errors)
        
        # Calculate fidelity
        psi_norm = psi / np.linalg.norm(psi)
        psi_decoded_norm = psi_decoded / np.linalg.norm(psi_decoded)
        fidelity = np.abs(np.vdot(psi_norm.flatten(), psi_decoded_norm.flatten()))**2
        
        # Circuit metrics
        circuit_depth = circuit.depth()
        total_gates = circuit.size()
        
        # Count gate types
        gate_counts = circuit.count_ops()
        single_qubit_gates = sum(
            count for gate, count in gate_counts.items()
            if gate in ['u3', 'u2', 'u1', 'u', 'rx', 'ry', 'rz', 'x', 'y', 'z', 'h', 's', 't']
        )
        two_qubit_gates = sum(
            count for gate, count in gate_counts.items()
            if gate in ['cx', 'cy', 'cz', 'swap', 'cswap']
        )
        
        # Memory measurements
        mem_before = self._get_memory_mb()
        circuit_copy = circuit.copy()
        mem_circuit = self._get_memory_mb() - mem_before
        
        mem_before = self._get_memory_mb()
        sv = Statevector.from_instruction(circuit)
        mem_statevector = self._get_memory_mb() - mem_before
        
        # Hardware estimates (IBM quantum devices)
        estimated_runtime_ibm = self._estimate_hardware_runtime(circuit)
        estimated_fidelity_ibm = self._estimate_hardware_fidelity(
            circuit_depth, single_qubit_gates, two_qubit_gates
        )
        
        return BenchmarkResult(
            n_qubits_x=n_qubits_x,
            n_qubits_y=n_qubits_y,
            pixels=pixels,
            encoding_time=encoding_time,
            decoding_time=decoding_time,
            round_trip_time=round_trip_time,
            circuit_depth=circuit_depth,
            total_gates=total_gates,
            single_qubit_gates=single_qubit_gates,
            two_qubit_gates=two_qubit_gates,
            memory_classical=mem_classical,
            memory_circuit=mem_circuit,
            memory_statevector=mem_statevector,
            round_trip_error=round_trip_error,
            fidelity=fidelity,
            estimated_runtime_ibm=estimated_runtime_ibm,
            estimated_fidelity_ibm=estimated_fidelity_ibm,
        )
    
    def _estimate_hardware_runtime(self, circuit: QuantumCircuit) -> float:
        """
        Estimate runtime on IBM quantum hardware.
        
        Assumptions:
        - Single-qubit gate: 100 ns
        - Two-qubit gate: 500 ns
        - Measurement: 1 µs
        - Overhead: 10% per operation
        """
        gate_counts = circuit.count_ops()
        
        # Gate times (seconds)
        single_qubit_time = 100e-9
        two_qubit_time = 500e-9
        measurement_time = 1e-6
        
        # Count gates
        single_q = sum(
            count for gate, count in gate_counts.items()
            if gate in ['u3', 'u2', 'u1', 'u', 'rx', 'ry', 'rz', 'x', 'y', 'z', 'h', 's', 't']
        )
        two_q = sum(
            count for gate, count in gate_counts.items()
            if gate in ['cx', 'cy', 'cz', 'swap']
        )
        
        # Calculate time
        total_time = (
            single_q * single_qubit_time +
            two_q * two_qubit_time +
            circuit.num_qubits * measurement_time
        )
        
        # Add overhead
        total_time *= 1.1
        
        return total_time
    
    def _estimate_hardware_fidelity(
        self,
        depth: int,
        single_qubit_gates: int,
        two_qubit_gates: int
    ) -> float:
        """
        Estimate fidelity on IBM quantum hardware.
        
        Typical IBM error rates:
        - Single-qubit gate: 1e-4
        - Two-qubit gate: 1e-2
        - Measurement: 1e-2
        """
        error_1q = 1e-4
        error_2q = 1e-2
        error_meas = 1e-2
        
        # Calculate total fidelity (multiplicative)
        fidelity = (
            (1 - error_1q) ** single_qubit_gates *
            (1 - error_2q) ** two_qubit_gates *
            (1 - error_meas)
        )
        
        return fidelity
    
    def run_scaling_analysis(
        self,
        n_qubits_range: List[int] = [2, 3, 4, 5, 6],
        num_trials: int = 5
    ) -> List[BenchmarkResult]:
        """
        Run scaling analysis across multiple grid sizes.
        
        Args:
            n_qubits_range: List of qubit counts to test
            num_trials: Number of trials per configuration
        
        Returns:
            List of BenchmarkResult objects
        """
        results = []
        
        print("🔍 Running scaling analysis...")
        print(f"   Grid sizes: {[f'{2**n}×{2**n}' for n in n_qubits_range]}")
        print(f"   Trials per size: {num_trials}\n")
        
        for i, n_qubits in enumerate(n_qubits_range):
            pixels = 2**n_qubits
            print(f"[{i+1}/{len(n_qubits_range)}] Testing {pixels}×{pixels} grid ({n_qubits} qubits)...", end=" ")
            
            start = time.time()
            result = self.benchmark_single_configuration(
                n_qubits, n_qubits, num_trials
            )
            elapsed = time.time() - start
            
            results.append(result)
            print(f"✓ ({elapsed:.1f}s)")
            print(f"       Encoding: {result.encoding_time*1000:.2f}ms, "
                  f"Depth: {result.circuit_depth}, "
                  f"Gates: {result.total_gates}")
        
        print("\n✅ Scaling analysis complete!")
        return results
    
    def compare_optimization_methods(
        self,
        n_qubits: int = 4,
        num_trials: int = 5
    ) -> Dict[str, Dict]:
        """
        Compare different circuit optimization methods.
        
        Args:
            n_qubits: Number of qubits per dimension
            num_trials: Number of trials per method
        
        Returns:
            Dictionary with results for each method
        """
        pixels = 2**n_qubits
        psi = self._create_test_wave_function(pixels)
        
        methods = ['direct', 'schmidt']
        results = {}
        
        print(f"🔧 Comparing optimization methods ({pixels}×{pixels} grid)...\n")
        
        for method in methods:
            print(f"   Testing '{method}' method...", end=" ")
            
            optimizer = StatePreparationOptimizer(method=method)
            
            times = []
            depths = []
            gates = []
            fidelities = []
            
            for _ in range(num_trials):
                start = time.perf_counter()
                circuit = optimizer.prepare_state(psi.flatten(), num_qubits=2*n_qubits)
                elapsed = time.perf_counter() - start
                
                times.append(elapsed)
                depths.append(circuit.depth())
                
                metrics = optimizer.get_circuit_metrics(circuit)
                gates.append(metrics['gates'])
                
                # Calculate fidelity
                sv = Statevector.from_instruction(circuit)
                psi_decoded = sv.data.reshape(pixels, pixels)
                fid = np.abs(np.vdot(psi.flatten(), psi_decoded.flatten()))**2
                fidelities.append(fid)
            
            results[method] = {
                'preparation_time': np.mean(times),
                'depth': int(np.mean(depths)),
                'gates': int(np.mean(gates)),
                'fidelity': np.mean(fidelities),
                'std_time': np.std(times),
                'std_depth': np.std(depths),
            }
            
            print(f"✓ Time: {results[method]['preparation_time']*1000:.2f}ms, "
                  f"Depth: {results[method]['depth']}")
        
        print("\n✅ Optimization comparison complete!")
        return results
    
    def profile_memory_usage(
        self,
        n_qubits_range: List[int] = [2, 3, 4, 5]
    ) -> Dict[str, List]:
        """
        Profile memory usage across grid sizes.
        
        Args:
            n_qubits_range: List of qubit counts to test
        
        Returns:
            Dictionary with memory profiles
        """
        memory_data = {
            'n_qubits': [],
            'pixels': [],
            'classical_mb': [],
            'circuit_mb': [],
            'statevector_mb': [],
            'total_mb': [],
        }
        
        print("💾 Profiling memory usage...\n")
        
        for n_qubits in n_qubits_range:
            pixels = 2**n_qubits
            print(f"   {pixels}×{pixels} grid...", end=" ")
            
            result = self.benchmark_single_configuration(n_qubits, n_qubits, num_trials=1)
            
            memory_data['n_qubits'].append(n_qubits)
            memory_data['pixels'].append(pixels)
            memory_data['classical_mb'].append(result.memory_classical)
            memory_data['circuit_mb'].append(result.memory_circuit)
            memory_data['statevector_mb'].append(result.memory_statevector)
            memory_data['total_mb'].append(
                result.memory_classical + result.memory_circuit + result.memory_statevector
            )
            
            print(f"✓ Total: {memory_data['total_mb'][-1]:.2f} MB")
        
        print("\n✅ Memory profiling complete!")
        return memory_data
    
    def estimate_hardware_costs(
        self,
        n_qubits_range: List[int] = [2, 3, 4, 5],
        shots_per_run: int = 1024
    ) -> Dict[str, List]:
        """
        Estimate costs for running on IBM quantum hardware.
        
        Args:
            n_qubits_range: List of qubit counts to test
            shots_per_run: Number of shots per execution
        
        Returns:
            Dictionary with cost estimates
        """
        cost_data = {
            'n_qubits': [],
            'pixels': [],
            'runtime_seconds': [],
            'estimated_fidelity': [],
            'shots_required': [],
            'total_time_hours': [],
        }
        
        print("💰 Estimating hardware deployment costs...\n")
        
        for n_qubits in n_qubits_range:
            pixels = 2**n_qubits
            print(f"   {pixels}×{pixels} grid...", end=" ")
            
            result = self.benchmark_single_configuration(n_qubits, n_qubits, num_trials=1)
            
            # Calculate total runtime
            runtime_per_shot = result.estimated_runtime_ibm
            total_runtime = runtime_per_shot * shots_per_run
            
            cost_data['n_qubits'].append(n_qubits)
            cost_data['pixels'].append(pixels)
            cost_data['runtime_seconds'].append(runtime_per_shot)
            cost_data['estimated_fidelity'].append(result.estimated_fidelity_ibm)
            cost_data['shots_required'].append(shots_per_run)
            cost_data['total_time_hours'].append(total_runtime / 3600)
            
            print(f"✓ Runtime: {runtime_per_shot*1e6:.2f}µs, "
                  f"Fidelity: {result.estimated_fidelity_ibm:.4f}")
        
        print("\n✅ Cost estimation complete!")
        return cost_data
    
    def save_results(
        self,
        results: List[BenchmarkResult],
        output_file: str = 'benchmark_results.json'
    ):
        """
        Save benchmark results to JSON file.
        
        Args:
            results: List of BenchmarkResult objects
            output_file: Output file path
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'metadata': {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'num_configurations': len(results),
                'random_seed': self.random_seed,
            },
            'results': [result.to_dict() for result in results]
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 Results saved to: {output_path}")
    
    def generate_report(
        self,
        results: List[BenchmarkResult],
        output_file: str = 'benchmark_report.md'
    ):
        """
        Generate markdown report from benchmark results.
        
        Args:
            results: List of BenchmarkResult objects
            output_file: Output markdown file path
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write("# Quantum CTEM Performance Benchmark Report\n\n")
            f.write(f"**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Configurations tested**: {len(results)}\n\n")
            
            f.write("## Summary Table\n\n")
            f.write("| Grid Size | Qubits | Encoding (ms) | Depth | Gates | Error | Fidelity |\n")
            f.write("|-----------|--------|---------------|-------|-------|-------|----------|\n")
            
            for r in results:
                f.write(f"| {r.pixels}×{r.pixels} | {r.n_qubits_x + r.n_qubits_y} | "
                       f"{r.encoding_time*1000:.2f} | {r.circuit_depth} | {r.total_gates} | "
                       f"{r.round_trip_error:.2e} | {r.fidelity:.6f} |\n")
            
            f.write("\n## Detailed Results\n\n")
            for i, r in enumerate(results, 1):
                f.write(f"### Configuration {i}: {r.pixels}×{r.pixels} Grid\n\n")
                f.write(f"- **Qubits**: {r.n_qubits_x + r.n_qubits_y} "
                       f"({r.n_qubits_x} × {r.n_qubits_y})\n")
                f.write(f"- **Encoding time**: {r.encoding_time*1000:.3f} ms\n")
                f.write(f"- **Decoding time**: {r.decoding_time*1000:.3f} ms\n")
                f.write(f"- **Round-trip time**: {r.round_trip_time*1000:.3f} ms\n")
                f.write(f"- **Circuit depth**: {r.circuit_depth}\n")
                f.write(f"- **Total gates**: {r.total_gates}\n")
                f.write(f"- **Round-trip error**: {r.round_trip_error:.2e}\n")
                f.write(f"- **Fidelity**: {r.fidelity:.8f}\n")
                f.write(f"- **Est. IBM runtime**: {r.estimated_runtime_ibm*1e6:.2f} µs\n")
                f.write(f"- **Est. IBM fidelity**: {r.estimated_fidelity_ibm:.6f}\n\n")
        
        print(f"📄 Report generated: {output_path}")


def quick_benchmark(n_qubits: int = 3) -> BenchmarkResult:
    """
    Run a quick benchmark for a single configuration.
    
    Args:
        n_qubits: Number of qubits per dimension
    
    Returns:
        BenchmarkResult
    
    Example:
        >>> result = quick_benchmark(n_qubits=4)
        >>> print(f"Encoding: {result.encoding_time*1000:.2f}ms")
        >>> print(f"Depth: {result.circuit_depth}")
    """
    benchmark = PerformanceBenchmark()
    return benchmark.benchmark_single_configuration(n_qubits, n_qubits, num_trials=3)
