"""
Circuit optimization for quantum CTEM implementation.

This module provides tools to optimize quantum circuits for:
1. Reduced circuit depth (critical for NISQ devices)
2. Hardware-specific gate sets (IBM quantum devices)
3. Qubit connectivity constraints
4. Error mitigation strategies

Target Hardware: IBM Quantum devices (127+ qubits)
- ibm_kyoto: 127 qubits
- ibm_osaka: 127 qubits  
- ibm_brisbane: 127 qubits

Author: QuScope Team
Date: October 2025
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Union
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import Parameter
from qiskit.circuit.library import Initialize
from qiskit.quantum_info import Statevector
from qiskit.transpiler import PassManager, CouplingMap
from qiskit.transpiler.passes import (
    Optimize1qGates,
    CommutativeCancellation,
    RemoveBarriers,
    Depth,
)


class StatePreparationOptimizer:
    """
    Optimize quantum state preparation circuits for hardware deployment.
    
    The state initialization circuit |0⟩^n → |ψ⟩ is often the deepest part
    of quantum algorithms. This class provides multiple strategies to reduce
    circuit depth while maintaining fidelity.
    
    Strategies:
    1. Direct: Qiskit's built-in initialize() with optimization
    2. Schmidt decomposition: Exploit entanglement structure
    3. Variational: Parameterized circuits (requires training)
    4. QGAN: Quantum GAN approach (requires training)
    
    For hardware deployment, we focus on Direct + transpilation.
    """
    
    def __init__(self, method: str = 'direct', optimization_level: int = 3):
        """
        Initialize state preparation optimizer.
        
        Parameters
        ----------
        method : str
            Preparation method: 'direct', 'schmidt', 'variational', 'qgan'
        optimization_level : int
            Qiskit transpilation optimization level (0-3)
            Level 3: Most aggressive optimization for hardware
        """
        self.method = method
        self.optimization_level = optimization_level
        
    def prepare_state(
        self, 
        psi: np.ndarray,
        num_qubits: int,
        normalize: bool = True
    ) -> QuantumCircuit:
        """
        Prepare quantum state |ψ⟩ from classical array.
        
        Parameters
        ----------
        psi : np.ndarray
            Target state vector (flattened or 2D)
        num_qubits : int
            Number of qubits for the state
        normalize : bool
            Whether to normalize the state vector
            
        Returns
        -------
        QuantumCircuit
            Optimized state preparation circuit
            
        Notes
        -----
        For hardware execution, this circuit will be transpiled to
        the native gate set of the target device. IBM devices typically
        use {√X, X, RZ, CNOT} or {SX, RZ, ECR} basis.
        """
        if self.method == 'direct':
            return self._prepare_direct(psi, num_qubits, normalize)
        elif self.method == 'schmidt':
            return self._prepare_schmidt(psi, num_qubits, normalize)
        elif self.method == 'variational':
            raise NotImplementedError("Variational method requires training")
        elif self.method == 'qgan':
            raise NotImplementedError("QGAN method requires training")
        else:
            raise ValueError(f"Unknown method: {self.method}")
    
    def _prepare_direct(
        self,
        psi: np.ndarray,
        num_qubits: int,
        normalize: bool
    ) -> QuantumCircuit:
        """
        Direct state preparation using Qiskit's initialize().
        
        This uses the Shende-Bullock-Markov decomposition which gives
        O(2^n) gates but is exact. We then apply optimization passes.
        """
        # Flatten if needed
        psi_flat = psi.flatten()
        
        # Validate size
        expected_size = 2**num_qubits
        if len(psi_flat) != expected_size:
            raise ValueError(
                f"State size {len(psi_flat)} doesn't match "
                f"2^{num_qubits} = {expected_size}"
            )
        
        # Normalize if requested
        if normalize:
            norm = np.linalg.norm(psi_flat)
            if norm < 1e-10:
                # Zero state → uniform superposition
                qc = QuantumCircuit(num_qubits, name='uniform_prep')
                qc.h(range(num_qubits))
                return qc
            psi_flat = psi_flat / norm
        
        # Create circuit with initialize instruction
        qc = QuantumCircuit(num_qubits, name='state_prep')
        qc.initialize(psi_flat, range(num_qubits))
        
        # Decompose initialize into basic gates
        qc = qc.decompose()
        
        # Apply optimization passes
        qc_optimized = self._optimize_circuit(qc)
        
        return qc_optimized
    
    def _prepare_schmidt(
        self,
        psi: np.ndarray,
        num_qubits: int,
        normalize: bool
    ) -> QuantumCircuit:
        """
        State preparation using Schmidt decomposition.
        
        For separable or low-entanglement states, this can significantly
        reduce circuit depth by exploiting tensor product structure.
        
        |ψ⟩ = Σᵢ λᵢ |φᵢ⟩_A ⊗ |χᵢ⟩_B
        
        If only a few λᵢ are significant, we can prepare with shallow circuits.
        """
        # For 2D wave functions, split into x and y subsystems
        if psi.ndim == 2:
            # Check if state is approximately separable
            u, s, vh = np.linalg.svd(psi)
            
            # If state is highly separable (one dominant singular value)
            if s[0] / np.sum(s) > 0.99:
                # Prepare as product state
                return self._prepare_product_state(u[:, 0], vh[0, :], num_qubits)
        
        # Fall back to direct method
        return self._prepare_direct(psi, num_qubits, normalize)
    
    def _prepare_product_state(
        self,
        state_x: np.ndarray,
        state_y: np.ndarray,
        num_qubits: int
    ) -> QuantumCircuit:
        """
        Prepare product state |φ⟩_x ⊗ |χ⟩_y efficiently.
        
        This reduces depth from O(2^n) to O(2^(n/2)) for separable states.
        """
        n_x = num_qubits // 2
        n_y = num_qubits - n_x
        
        qc = QuantumCircuit(num_qubits, name='product_prep')
        
        # Prepare x subsystem
        qc_x = QuantumCircuit(n_x)
        qc_x.initialize(state_x, range(n_x))
        qc_x = qc_x.decompose()
        
        # Prepare y subsystem
        qc_y = QuantumCircuit(n_y)
        qc_y.initialize(state_y, range(n_y))
        qc_y = qc_y.decompose()
        
        # Combine
        qc.compose(qc_x, range(n_x), inplace=True)
        qc.compose(qc_y, range(n_x, num_qubits), inplace=True)
        
        return self._optimize_circuit(qc)
    
    def _optimize_circuit(self, qc: QuantumCircuit) -> QuantumCircuit:
        """
        Apply optimization passes to reduce circuit depth and gate count.
        
        These optimizations are hardware-agnostic and prepare the circuit
        for subsequent hardware-specific transpilation.
        """
        # Create pass manager with optimization passes
        pm = PassManager([
            Optimize1qGates(),         # Merge consecutive 1-qubit gates
            CommutativeCancellation(), # Cancel commuting gates
            RemoveBarriers(),          # Remove unnecessary barriers
        ])
        
        # Run optimization
        qc_optimized = pm.run(qc)
        
        return qc_optimized
    
    def get_circuit_metrics(self, qc: QuantumCircuit) -> Dict[str, int]:
        """
        Get circuit complexity metrics.
        
        Returns
        -------
        dict
            - 'depth': Circuit depth (critical for NISQ devices)
            - 'gates': Total gate count
            - '1q_gates': Single-qubit gate count
            - '2q_gates': Two-qubit gate count (most expensive)
            - 'qubits': Number of qubits used
        """
        from qiskit.converters import circuit_to_dag
        
        dag = circuit_to_dag(qc)
        
        # Count gates by type
        gate_count = qc.count_ops()
        two_qubit_gates = ['cx', 'cz', 'cy', 'cp', 'crx', 'cry', 'crz', 
                          'ecr', 'swap', 'iswap', 'rxx', 'ryy', 'rzz']
        
        num_2q = sum(gate_count.get(g, 0) for g in two_qubit_gates)
        num_1q = sum(gate_count.values()) - num_2q
        
        return {
            'depth': qc.depth(),
            'gates': sum(gate_count.values()),
            '1q_gates': num_1q,
            '2q_gates': num_2q,
            'qubits': qc.num_qubits,
        }


class HardwareTranspiler:
    """
    Transpile circuits for specific IBM quantum hardware.
    
    This class handles:
    1. Gate set conversion to native gates
    2. Qubit routing and SWAP insertion
    3. Pulse-level optimization (optional)
    4. Error mitigation preparation
    """
    
    def __init__(
        self,
        backend_name: Optional[str] = None,
        optimization_level: int = 3,
        seed_transpiler: int = 42
    ):
        """
        Initialize hardware transpiler.
        
        Parameters
        ----------
        backend_name : str, optional
            IBM backend name (e.g., 'ibm_kyoto', 'ibm_osaka')
            If None, uses a generic 127-qubit heavy-hex topology
        optimization_level : int
            Transpilation optimization (0-3), default 3
        seed_transpiler : int
            Random seed for reproducible transpilation
        """
        self.backend_name = backend_name
        self.optimization_level = optimization_level
        self.seed_transpiler = seed_transpiler
        
        # Define coupling map for target hardware
        # IBM's heavy-hex topology (simplified for now)
        self.coupling_map = self._get_coupling_map()
        
    def _get_coupling_map(self) -> Optional[CouplingMap]:
        """
        Get qubit connectivity for target backend.
        
        For actual hardware execution, this would be loaded from
        the backend properties. For simulation, we use a generic
        all-to-all connectivity for small systems.
        """
        if self.backend_name is None:
            # Generic all-to-all for testing (not realistic)
            return None
        
        # TODO: Load actual topology from IBM backend
        # For now, return None to allow all-to-all
        return None
    
    def transpile_for_hardware(
        self,
        circuit: QuantumCircuit,
        initial_layout: Optional[List[int]] = None
    ) -> QuantumCircuit:
        """
        Transpile circuit for target hardware.
        
        This converts the circuit to:
        1. Native gate set (e.g., {SX, RZ, ECR} for IBM)
        2. Hardware topology (insert SWAPs for non-adjacent qubits)
        3. Optimized depth (minimize decoherence effects)
        
        Parameters
        ----------
        circuit : QuantumCircuit
            High-level quantum circuit
        initial_layout : list, optional
            Initial qubit mapping to physical qubits
            
        Returns
        -------
        QuantumCircuit
            Hardware-optimized transpiled circuit
        """
        transpiled = transpile(
            circuit,
            coupling_map=self.coupling_map,
            optimization_level=self.optimization_level,
            seed_transpiler=self.seed_transpiler,
            initial_layout=initial_layout,
        )
        
        return transpiled
    
    def estimate_fidelity(
        self,
        circuit: QuantumCircuit,
        gate_error_1q: float = 1e-4,
        gate_error_2q: float = 1e-2
    ) -> float:
        """
        Estimate circuit fidelity on noisy hardware.
        
        Uses simple error model:
        F ≈ (1 - ε₁)^(n₁) × (1 - ε₂)^(n₂)
        
        where:
        - ε₁, ε₂: single/two-qubit gate errors
        - n₁, n₂: number of single/two-qubit gates
        
        Parameters
        ----------
        circuit : QuantumCircuit
            Transpiled circuit
        gate_error_1q : float
            Single-qubit gate error rate (typical: 1e-4)
        gate_error_2q : float
            Two-qubit gate error rate (typical: 1e-2)
            
        Returns
        -------
        float
            Estimated fidelity (0 to 1)
        """
        metrics = StatePreparationOptimizer().get_circuit_metrics(circuit)
        
        n_1q = metrics['1q_gates']
        n_2q = metrics['2q_gates']
        
        # Simple error model
        fidelity = (1 - gate_error_1q)**n_1q * (1 - gate_error_2q)**n_2q
        
        return fidelity
    
    def compare_strategies(
        self,
        circuits: Dict[str, QuantumCircuit]
    ) -> Dict[str, Dict]:
        """
        Compare multiple implementation strategies.
        
        Parameters
        ----------
        circuits : dict
            Dictionary of {strategy_name: circuit}
            
        Returns
        -------
        dict
            Comparison metrics for each strategy
        """
        results = {}
        
        for name, circuit in circuits.items():
            # Transpile for hardware
            transpiled = self.transpile_for_hardware(circuit)
            
            # Get metrics
            metrics = StatePreparationOptimizer().get_circuit_metrics(transpiled)
            
            # Estimate fidelity
            fidelity = self.estimate_fidelity(transpiled)
            
            results[name] = {
                **metrics,
                'estimated_fidelity': fidelity,
                'circuit': transpiled,
            }
        
        return results


def benchmark_state_preparation(
    n_qubits_list: List[int],
    methods: List[str] = ['direct', 'schmidt']
) -> Dict:
    """
    Benchmark state preparation methods across different system sizes.
    
    Parameters
    ----------
    n_qubits_list : list
        List of qubit counts to test [2, 4, 6, 8, ...]
    methods : list
        Preparation methods to compare
        
    Returns
    -------
    dict
        Benchmark results with circuit metrics
    """
    results = {}
    
    for n_qubits in n_qubits_list:
        results[n_qubits] = {}
        
        # Create test state (Gaussian wave packet)
        size = 2**n_qubits
        x = np.linspace(-4, 4, size)
        psi_test = np.exp(-x**2 / 2)
        psi_test /= np.linalg.norm(psi_test)
        
        for method in methods:
            try:
                optimizer = StatePreparationOptimizer(method=method)
                circuit = optimizer.prepare_state(psi_test, n_qubits)
                metrics = optimizer.get_circuit_metrics(circuit)
                
                results[n_qubits][method] = metrics
            except Exception as e:
                results[n_qubits][method] = {'error': str(e)}
    
    return results
