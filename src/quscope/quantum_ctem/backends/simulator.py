"""
Local Simulator Backend for Quantum CTEM.

Provides fast, exact simulation using Qiskit Aer for development,
testing, and validation of quantum circuits before hardware deployment.
"""

import time
from typing import List, Optional

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator, StatevectorSimulator

from .base import Backend, BackendConfig, ExecutionResult


class SimulatorBackend(Backend):
    """
    Local quantum simulator backend using Qiskit Aer.

    Supports both statevector (exact) and sampling (shot-based) simulation.
    Ideal for development, testing, and validating quantum CTEM circuits.

    Attributes:
        simulation_method: "statevector" for exact simulation, "automatic" for sampling
        device: Optional device to mimic (e.g., "ibm_kyoto" for noise model)

    Examples:
        >>> backend = SimulatorBackend()
        >>> result = backend.run(circuit)
        >>> psi = result.get_statevector_2d(nx=32, ny=32)

        >>> # With noise model mimicking IBM hardware
        >>> backend = SimulatorBackend(device="ibm_kyoto")
    """

    def __init__(
        self,
        simulation_method: str = "statevector",
        device: Optional[str] = None,
        seed: Optional[int] = None,
    ):
        """
        Initialize simulator backend.

        Args:
            simulation_method: "statevector" for exact, "automatic" for sampling
            device: Optional IBM device name to mimic with noise model
            seed: Random seed for reproducibility
        """
        super().__init__(name=f"simulator_{simulation_method}")
        self.simulation_method = simulation_method
        self.device = device
        self.seed = seed

        self._simulator = None
        self._statevector_sim = None

    def connect(self) -> bool:
        """Initialize the simulator backends."""
        try:
            # Main simulator for shots-based execution
            if self.device:
                # Create fake backend with noise model
                from qiskit_aer.noise import NoiseModel
                from qiskit.providers.fake_provider import GenericBackendV2

                fake_backend = GenericBackendV2(num_qubits=127)
                noise_model = NoiseModel.from_backend(fake_backend)
                self._simulator = AerSimulator(
                    method=self.simulation_method,
                    noise_model=noise_model,
                )
            else:
                self._simulator = AerSimulator(method=self.simulation_method)

            # Statevector simulator for exact state extraction
            self._statevector_sim = StatevectorSimulator()

            self._is_connected = True
            return True

        except Exception as e:
            self._is_connected = False
            raise RuntimeError(f"Failed to initialize simulator: {e}")

    def run(
        self,
        circuit: QuantumCircuit,
        config: Optional[BackendConfig] = None,
    ) -> ExecutionResult:
        """
        Execute circuit on simulator.

        Args:
            circuit: QuantumCircuit to execute
            config: Execution configuration

        Returns:
            ExecutionResult with statevector and/or counts
        """
        if not self.is_connected:
            self.connect()

        config = config or BackendConfig()
        start_time = time.time()

        result = ExecutionResult(
            backend_name=self.name,
            num_qubits=circuit.num_qubits,
            depth=circuit.depth(),
            gate_counts=dict(circuit.count_ops()),
        )

        try:
            # Get statevector (exact state)
            if self.simulation_method == "statevector":
                # Use statevector simulator for exact results
                sv_circuit = circuit.copy()
                sv_circuit.save_statevector()

                job = self._simulator.run(
                    sv_circuit,
                    seed_simulator=config.seed_simulator or self.seed,
                )
                qiskit_result = job.result()
                statevector = qiskit_result.get_statevector()
                result.statevector = np.array(statevector.data)
                result.probabilities = np.abs(result.statevector) ** 2

            # Also get counts if shots > 0
            if config.shots > 0:
                # Add measurements if not present
                meas_circuit = circuit.copy()
                if not any(
                    instr.operation.name == "measure"
                    for instr in meas_circuit.data
                ):
                    meas_circuit.measure_all()

                job = self._simulator.run(
                    meas_circuit,
                    shots=config.shots,
                    seed_simulator=config.seed_simulator or self.seed,
                )
                qiskit_result = job.result()
                result.counts = qiskit_result.get_counts()
                result.shots = config.shots

            result.success = True
            result.execution_time = time.time() - start_time

        except Exception as e:
            result.success = False
            result.error_message = str(e)

        return result

    def run_batch(
        self,
        circuits: List[QuantumCircuit],
        config: Optional[BackendConfig] = None,
    ) -> List[ExecutionResult]:
        """Execute multiple circuits."""
        return [self.run(circuit, config) for circuit in circuits]

    def _get_qiskit_backend(self):
        """Get underlying Qiskit backend for transpilation."""
        if not self.is_connected:
            self.connect()
        return self._simulator

    def get_statevector(self, circuit: QuantumCircuit) -> np.ndarray:
        """
        Convenience method to get statevector directly.

        Args:
            circuit: Circuit to simulate

        Returns:
            Complex numpy array of state amplitudes
        """
        result = self.run(circuit, BackendConfig(shots=0))
        if result.statevector is None:
            raise RuntimeError("Failed to get statevector")
        return result.statevector

    def simulate_ctem_wavefunction(
        self,
        circuit: QuantumCircuit,
        nx: int,
        ny: int,
    ) -> np.ndarray:
        """
        Simulate circuit and return CTEM wavefunction as 2D array.

        Args:
            circuit: Quantum circuit encoding the electron wavefunction
            nx: Number of pixels in x
            ny: Number of pixels in y

        Returns:
            Complex 2D array (ny, nx) representing ψ(x, y)
        """
        result = self.run(circuit, BackendConfig(shots=0))
        return result.get_statevector_2d(nx, ny)
