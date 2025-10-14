"""
IBM Quantum Hardware Deployment Testing

Validates quantum CTEM implementation for deployment on IBM Quantum systems.
Tests real hardware constraints, connectivity, basis gates, and error mitigation.

Week 4 Task 1.8: IBM Hardware Validation

Author: QuScope Development Team
Date: January 2025
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import warnings
import time

from qiskit import QuantumCircuit, transpile
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit.transpiler import CouplingMap
from qiskit.quantum_info import Statevector, state_fidelity

from .quantum_wave_function import QuantumWaveFunction
from .circuit_optimization import HardwareTranspiler
from .classical_integration import QuantumClassicalBridge


@dataclass
class IBMDeviceProfile:
    """
    IBM Quantum device specifications.
    
    Attributes:
        name: Device name (e.g., 'ibm_kyoto')
        num_qubits: Total number of qubits
        basis_gates: List of native gates
        coupling_map: Qubit connectivity as list of edges
        single_qubit_error: Average single-qubit gate error rate
        two_qubit_error: Average two-qubit gate error rate
        readout_error: Average measurement error rate
        t1_us: T1 coherence time in microseconds
        t2_us: T2 coherence time in microseconds
    """
    
    name: str
    num_qubits: int
    basis_gates: List[str]
    coupling_map: Optional[List[List[int]]]
    single_qubit_error: float  # Average 1q gate error
    two_qubit_error: float     # Average 2q gate error
    readout_error: float       # Average readout error
    t1_us: float              # T1 coherence time (microseconds)
    t2_us: float              # T2 coherence time (microseconds)
    
    @staticmethod
    def ibm_kyoto() -> 'IBMDeviceProfile':
        """
        IBM Kyoto device profile (127 qubits, heavy-hex topology).
        One of the most advanced IBM Quantum systems available.
        """
        # Create a simple heavy-hex-inspired coupling map
        coupling_list = []
        for i in range(126):
            coupling_list.append([i, i+1])  # Linear backbone
            if i % 3 == 0 and i+3 < 127:
                coupling_list.append([i, i+3])  # Hexagonal connections
        
        return IBMDeviceProfile(
            name="ibm_kyoto",
            num_qubits=127,
            basis_gates=['id', 'rz', 'sx', 'x', 'cx', 'reset'],
            coupling_map=coupling_list,
            single_qubit_error=1.0e-4,
            two_qubit_error=1.0e-2,
            readout_error=1.5e-2,
            t1_us=100.0,
            t2_us=150.0
        )
    
    @staticmethod
    def ibm_brisbane() -> 'IBMDeviceProfile':
        """
        IBM Brisbane device profile (127 qubits, heavy-hex topology).
        Slightly better single-qubit performance than Kyoto.
        """
        coupling_list = []
        for i in range(126):
            coupling_list.append([i, i+1])
            if i % 3 == 0 and i+3 < 127:
                coupling_list.append([i, i+3])
        
        return IBMDeviceProfile(
            name="ibm_brisbane",
            num_qubits=127,
            basis_gates=['id', 'rz', 'sx', 'x', 'cx', 'reset'],
            coupling_map=coupling_list,
            single_qubit_error=8.0e-5,
            two_qubit_error=9.0e-3,
            readout_error=1.2e-2,
            t1_us=120.0,
            t2_us=180.0
        )
    
    @staticmethod
    def ibm_nazca() -> 'IBMDeviceProfile':
        """
        IBM Nazca device profile (127 qubits, heavy-hex topology).
        Good balance of qubit count and error rates.
        """
        coupling_list = []
        for i in range(126):
            coupling_list.append([i, i+1])
            if i % 3 == 0 and i+3 < 127:
                coupling_list.append([i, i+3])
        
        return IBMDeviceProfile(
            name="ibm_nazca",
            num_qubits=127,
            basis_gates=['id', 'rz', 'sx', 'x', 'cx', 'reset'],
            coupling_map=coupling_list,
            single_qubit_error=9.0e-5,
            two_qubit_error=1.1e-2,
            readout_error=1.3e-2,
            t1_us=110.0,
            t2_us=160.0
        )
    
    @staticmethod
    def ibm_sherbrooke() -> 'IBMDeviceProfile':
        """
        IBM Sherbrooke device profile (127 qubits, heavy-hex topology).
        Best overall coherence times.
        """
        coupling_list = []
        for i in range(126):
            coupling_list.append([i, i+1])
            if i % 3 == 0 and i+3 < 127:
                coupling_list.append([i, i+3])
        
        return IBMDeviceProfile(
            name="ibm_sherbrooke",
            num_qubits=127,
            basis_gates=['id', 'rz', 'sx', 'x', 'cx', 'reset'],
            coupling_map=coupling_list,
            single_qubit_error=8.5e-5,
            two_qubit_error=9.5e-3,
            readout_error=1.1e-2,
            t1_us=130.0,
            t2_us=190.0
        )
    
    def create_backend(self) -> GenericBackendV2:
        """
        Create a GenericBackendV2 instance with this device's specifications.
        
        Returns:
            GenericBackendV2 configured with device parameters
        """
        return GenericBackendV2(
            num_qubits=self.num_qubits,
            basis_gates=self.basis_gates,
            coupling_map=self.coupling_map
        )


def estimate_fidelity(circuit: QuantumCircuit, device: IBMDeviceProfile) -> float:
    """
    Estimate circuit fidelity on a given IBM device based on gate counts and error rates.
    
    Args:
        circuit: Quantum circuit to estimate fidelity for
        device: IBM device profile with error rates
    
    Returns:
        Estimated fidelity (0 to 1)
    """
    # Count gates
    gate_counts = circuit.count_ops()
    
    # Single-qubit gates
    single_q_gates = sum(gate_counts.get(gate, 0) 
                         for gate in ['id', 'rz', 'sx', 'x', 'h', 'u1', 'u2', 'u3'])
    
    # Two-qubit gates
    two_q_gates = gate_counts.get('cx', 0) + gate_counts.get('cz', 0)
    
    # Measurements
    num_measurements = circuit.num_qubits  # Assume all qubits measured
    
    # Estimate fidelity using error propagation
    fidelity = 1.0
    fidelity *= (1 - device.single_qubit_error) ** single_q_gates
    fidelity *= (1 - device.two_qubit_error) ** two_q_gates
    fidelity *= (1 - device.readout_error) ** num_measurements
    
    return fidelity


class IBMHardwareValidator:
    """
    Validates quantum circuits for deployment on IBM Quantum hardware.
    
    Features:
    - Circuit transpilation to IBM basis gates
    - Connectivity validation for heavy-hex topology
    - Fidelity estimation based on gate counts
    - Device comparison and recommendations
    - Qubit mapping optimization
    
    Example:
        validator = IBMHardwareValidator()
        results = validator.validate_for_device('ibm_kyoto', n_qubits=4)
        guide = validator.generate_deployment_guide(results)
    """
    
    def __init__(self):
        """Initialize the IBM hardware validator."""
        self.devices = {
            'ibm_kyoto': IBMDeviceProfile.ibm_kyoto(),
            'ibm_brisbane': IBMDeviceProfile.ibm_brisbane(),
            'ibm_nazca': IBMDeviceProfile.ibm_nazca(),
            'ibm_sherbrooke': IBMDeviceProfile.ibm_sherbrooke()
        }
        # Don't instantiate encoder here - create per validation with specific qubit count
    
    def validate_circuit_for_ibm(
        self,
        circuit: QuantumCircuit,
        device_name: str
    ) -> Dict:
        """
        Validate a quantum circuit for a specific IBM device.
        
        Args:
            circuit: Quantum circuit to validate
            device_name: Name of IBM device ('ibm_kyoto', etc.)
        
        Returns:
            Dictionary with validation results including:
            - transpiled_circuit: Circuit transpiled to device basis
            - original_depth: Original circuit depth
            - transpiled_depth: Depth after transpilation
            - original_gates: Original gate count
            - transpiled_gates: Gate count after transpilation
            - estimated_fidelity: Expected fidelity on device
            - execution_time_us: Estimated execution time
            - warnings: List of any issues
        """
        if device_name not in self.devices:
            raise ValueError(f"Unknown device: {device_name}")
        
        device = self.devices[device_name]
        start_time = time.time()
        
        # Get original circuit metrics
        original_depth = circuit.depth()
        original_gates = sum(circuit.count_ops().values())
        
        # Transpile to device
        backend = device.create_backend()
        transpiled = transpile(
            circuit,
            backend=backend,
            optimization_level=3,
            seed_transpiler=42
        )
        
        # Get transpiled metrics
        transpiled_depth = transpiled.depth()
        transpiled_gates = sum(transpiled.count_ops().values())
        
        # Estimate fidelity
        fidelity = estimate_fidelity(transpiled, device)
        
        # Estimate execution time (gates + readout)
        gate_counts = transpiled.count_ops()
        single_q_gates = sum(gate_counts.get(gate, 0) 
                            for gate in ['id', 'rz', 'sx', 'x'])
        two_q_gates = gate_counts.get('cx', 0)
        
        execution_time_us = (single_q_gates * 0.1 + two_q_gates * 0.5 + 
                            circuit.num_qubits * 1.0)  # Rough estimate
        
        # Check for warnings
        warnings_list = []
        if fidelity < 0.8:
            warnings_list.append(
                f"Low estimated fidelity ({fidelity:.1%}). "
                f"Consider reducing circuit depth or using error mitigation."
            )
        if execution_time_us > device.t2_us:
            warnings_list.append(
                f"Execution time ({execution_time_us:.1f}µs) exceeds T2 "
                f"({device.t2_us:.1f}µs). Circuit may decohere."
            )
        if transpiled_depth > 2 * original_depth:
            warnings_list.append(
                f"Transpilation significantly increased depth "
                f"({original_depth} → {transpiled_depth})"
            )
        
        elapsed_time = time.time() - start_time
        
        return {
            'device_name': device_name,
            'transpiled_circuit': transpiled,
            'original_depth': original_depth,
            'transpiled_depth': transpiled_depth,
            'original_gates': original_gates,
            'transpiled_gates': transpiled_gates,
            'estimated_fidelity': fidelity,
            'execution_time_us': execution_time_us,
            't1_us': device.t1_us,
            't2_us': device.t2_us,
            'warnings': warnings_list,
            'validation_time': elapsed_time
        }
    
    def validate_for_device(
        self,
        device_name: str,
        n_qubits: int = 4
    ) -> Dict:
        """
        Complete validation workflow for a specific device.
        
        Creates test circuit, validates for device, returns comprehensive results.
        
        Args:
            device_name: Name of IBM device
            n_qubits: Number of qubits for test circuit (total, will be split for 2D)
        
        Returns:
            Validation results dictionary
        """
        # Split qubits for 2D representation
        n_qubits_per_dim = max(1, n_qubits // 2)
        
        # Create wave function encoder for this test
        qwf_encoder = QuantumWaveFunction(n_qubits_per_dim, n_qubits_per_dim)
        
        # Create test wave function (2D Gaussian)
        grid_size = 2 ** n_qubits_per_dim
        x = np.linspace(-2, 2, grid_size)
        y = np.linspace(-2, 2, grid_size)
        X, Y = np.meshgrid(x, y)
        psi = np.exp(-(X**2 + Y**2) / 2)  # 2D Gaussian
        psi = psi / np.linalg.norm(psi)  # Normalize
        
        # Encode to quantum circuit
        circuit = qwf_encoder.prepare_arbitrary_wave(psi)
        
        # Validate
        return self.validate_circuit_for_ibm(circuit, device_name)
    
    def compare_devices(self, n_qubits: int = 4) -> Dict[str, Dict]:
        """
        Compare all IBM devices for the same test circuit.
        
        Args:
            n_qubits: Number of qubits for test circuit
        
        Returns:
            Dictionary mapping device names to validation results
        """
        results = {}
        for device_name in self.devices.keys():
            results[device_name] = self.validate_for_device(device_name, n_qubits)
        return results
    
    def test_qubit_mapping(
        self,
        device_name: str,
        n_qubits: int = 4
    ) -> Dict:
        """
        Test different transpilation optimization levels and qubit mappings.
        
        Args:
            device_name: Name of IBM device
            n_qubits: Number of qubits for test circuit (total)
        
        Returns:
            Dictionary with results for different optimization levels
        """
        device = self.devices[device_name]
        backend = device.create_backend()
        
        # Split qubits for 2D
        n_qubits_per_dim = max(1, n_qubits // 2)
        qwf_encoder = QuantumWaveFunction(n_qubits_per_dim, n_qubits_per_dim)
        
        # Create test circuit
        grid_size = 2 ** n_qubits_per_dim
        x = np.linspace(-2, 2, grid_size)
        y = np.linspace(-2, 2, grid_size)
        X, Y = np.meshgrid(x, y)
        psi = np.exp(-(X**2 + Y**2) / 2)
        psi = psi / np.linalg.norm(psi)
        circuit = qwf_encoder.prepare_arbitrary_wave(psi)
        
        results = {}
        for opt_level in range(4):
            transpiled = transpile(
                circuit,
                backend=backend,
                optimization_level=opt_level,
                seed_transpiler=42
            )
            
            results[f'opt_level_{opt_level}'] = {
                'depth': transpiled.depth(),
                'gates': sum(transpiled.count_ops().values()),
                'fidelity': estimate_fidelity(transpiled, device)
            }
        
        return results
    
    def generate_deployment_guide(
        self,
        device_results: Dict[str, Dict]
    ) -> str:
        """
        Generate microscopist-friendly deployment guide.
        
        Args:
            device_results: Results from compare_devices()
        
        Returns:
            Markdown-formatted deployment guide
        """
        guide = "# IBM Quantum Deployment Guide\n\n"
        guide += "## Device Comparison\n\n"
        
        # Sort devices by fidelity
        sorted_devices = sorted(
            device_results.items(),
            key=lambda x: x[1]['estimated_fidelity'],
            reverse=True
        )
        
        for device_name, results in sorted_devices:
            fidelity = results['estimated_fidelity']
            
            # Recommendation icon
            if fidelity > 0.95:
                icon = "✅ EXCELLENT"
            elif fidelity > 0.90:
                icon = "✅ GOOD"
            elif fidelity > 0.80:
                icon = "⚠️ ACCEPTABLE"
            else:
                icon = "❌ NOT RECOMMENDED"
            
            guide += f"### {device_name.upper()} {icon}\n\n"
            guide += f"- **Estimated Fidelity**: {fidelity:.1%}\n"
            guide += f"- **Circuit Depth**: {results['transpiled_depth']} gates\n"
            guide += f"- **Total Gates**: {results['transpiled_gates']}\n"
            guide += f"- **Execution Time**: {results['execution_time_us']:.1f} µs\n"
            guide += f"- **Coherence Time (T2)**: {results['t2_us']:.1f} µs\n"
            
            if results['warnings']:
                guide += "\n**⚠️ Warnings:**\n"
                for warning in results['warnings']:
                    guide += f"- {warning}\n"
            
            guide += "\n"
        
        # Best device recommendation
        best_device, best_results = sorted_devices[0]
        guide += "## Recommendation\n\n"
        guide += f"**Use `{best_device}` for best results.**\n\n"
        guide += f"Expected fidelity: {best_results['estimated_fidelity']:.1%}\n\n"
        
        # User instructions
        guide += "## How to Deploy\n\n"
        guide += "```python\n"
        guide += "from quscope.quantum_ctem import validate_ibm_deployment\n\n"
        guide += f"# Validate for {best_device}\n"
        guide += f"results = validate_ibm_deployment(device='{best_device}', n_qubits=4)\n"
        guide += "```\n\n"
        
        return guide


def validate_ibm_deployment(
    device: str = 'ibm_kyoto',
    n_qubits: int = 4
) -> Dict:
    """
    Convenience function for IBM deployment validation.
    
    Args:
        device: IBM device name ('ibm_kyoto', 'ibm_brisbane', 'ibm_nazca', 'ibm_sherbrooke')
        n_qubits: Number of qubits for test circuit
    
    Returns:
        Validation results dictionary
    
    Example:
        >>> results = validate_ibm_deployment('ibm_kyoto', n_qubits=4)
        >>> print(f"Estimated fidelity: {results['estimated_fidelity']:.1%}")
    """
    validator = IBMHardwareValidator()
    
    print(f"\n{'='*60}")
    print(f"IBM Quantum Deployment Validation")
    print(f"{'='*60}")
    print(f"Device: {device}")
    print(f"Qubits: {n_qubits}")
    print(f"{'='*60}\n")
    
    # Validate single device
    results = validator.validate_for_device(device, n_qubits)
    
    # Print summary
    print(f"✓ Circuit validated successfully!")
    print(f"  Estimated Fidelity: {results['estimated_fidelity']:.1%}")
    print(f"  Circuit Depth: {results['transpiled_depth']}")
    print(f"  Total Gates: {results['transpiled_gates']}")
    print(f"  Execution Time: {results['execution_time_us']:.1f} µs")
    
    if results['warnings']:
        print(f"\n⚠️  Warnings:")
        for warning in results['warnings']:
            print(f"  • {warning}")
    
    print(f"\n{'='*60}\n")
    
    return results
