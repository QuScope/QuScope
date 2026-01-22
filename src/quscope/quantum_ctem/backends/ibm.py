"""
IBM Quantum Backend for Quantum CTEM.

Provides integration with IBM Quantum hardware for running
quantum CTEM simulations on real quantum processors.
"""

import os
import time
from typing import Any, Dict, List, Optional

import numpy as np
from qiskit import QuantumCircuit, transpile

from .base import Backend, BackendConfig, ExecutionResult


class IBMBackend(Backend):
    """
    IBM Quantum hardware backend.

    Connects to IBM Quantum services and executes circuits on real
    quantum processors or IBM's cloud simulators.

    Attributes:
        device_name: Name of the IBM device (e.g., "ibm_kyoto", "ibm_osaka")
        channel: "ibm_quantum" for open access, "ibm_cloud" for premium

    Examples:
        >>> backend = IBMBackend(device_name="ibm_kyoto")
        >>> backend.connect()
        >>> result = backend.run(circuit, BackendConfig(shots=4096))

        >>> # List available devices
        >>> devices = backend.list_devices()
    """

    # Default device profiles with qubit counts and typical error rates
    DEVICE_PROFILES = {
        "ibm_kyoto": {"qubits": 127, "topology": "heavy_hex"},
        "ibm_osaka": {"qubits": 127, "topology": "heavy_hex"},
        "ibm_brisbane": {"qubits": 127, "topology": "heavy_hex"},
        "ibm_sherbrooke": {"qubits": 127, "topology": "heavy_hex"},
        "ibm_nazca": {"qubits": 127, "topology": "heavy_hex"},
    }

    def __init__(
        self,
        device_name: str = "ibm_kyoto",
        channel: str = "ibm_quantum",
        instance: Optional[str] = None,
        token: Optional[str] = None,
    ):
        """
        Initialize IBM backend.

        Args:
            device_name: IBM device name (e.g., "ibm_kyoto")
            channel: "ibm_quantum" (open) or "ibm_cloud" (premium)
            instance: IBM Cloud instance CRN (required for ibm_cloud channel)
            token: IBM Quantum API token (reads from IBM_QUANTUM_TOKEN env if not provided)
        """
        super().__init__(name=device_name)
        self.device_name = device_name
        self.channel = channel
        self.instance = instance
        self.token = token or os.environ.get("IBM_QUANTUM_TOKEN")

        self._service = None
        self._backend = None

    def connect(self) -> bool:
        """
        Connect to IBM Quantum service.

        Returns:
            True if connection successful

        Raises:
            RuntimeError: If connection fails or credentials invalid
        """
        try:
            from qiskit_ibm_runtime import QiskitRuntimeService

            # Try to use saved credentials first
            try:
                self._service = QiskitRuntimeService(channel=self.channel)
            except Exception:
                # Fall back to explicit token
                if not self.token:
                    raise RuntimeError(
                        "IBM Quantum token not found. Set IBM_QUANTUM_TOKEN "
                        "environment variable or pass token parameter."
                    )

                self._service = QiskitRuntimeService(
                    channel=self.channel,
                    token=self.token,
                    instance=self.instance,
                )

            # Get the specific backend
            self._backend = self._service.backend(self.device_name)
            self._is_connected = True
            return True

        except ImportError:
            raise RuntimeError(
                "qiskit-ibm-runtime not installed. "
                "Install with: pip install qiskit-ibm-runtime"
            )
        except Exception as e:
            self._is_connected = False
            raise RuntimeError(f"Failed to connect to IBM Quantum: {e}")

    def run(
        self,
        circuit: QuantumCircuit,
        config: Optional[BackendConfig] = None,
    ) -> ExecutionResult:
        """
        Execute circuit on IBM hardware.

        Args:
            circuit: QuantumCircuit to execute
            config: Execution configuration

        Returns:
            ExecutionResult with counts and metadata
        """
        if not self.is_connected:
            self.connect()

        config = config or BackendConfig(shots=4096)
        start_time = time.time()

        result = ExecutionResult(
            backend_name=self.device_name,
            num_qubits=circuit.num_qubits,
            depth=circuit.depth(),
            gate_counts=dict(circuit.count_ops()),
        )

        try:
            from qiskit_ibm_runtime import SamplerV2 as Sampler

            # Transpile for hardware
            transpiled = transpile(
                circuit,
                backend=self._backend,
                optimization_level=config.optimization_level,
            )

            # Add measurements if needed
            if not any(
                instr.operation.name == "measure" for instr in transpiled.data
            ):
                transpiled.measure_all()

            # Run with Sampler primitive
            sampler = Sampler(self._backend)
            job = sampler.run([transpiled], shots=config.shots)
            result.job_id = job.job_id()

            # Wait for results
            pub_result = job.result()[0]
            counts_dict = {}
            for bitstring, count in pub_result.data.meas.get_counts().items():
                counts_dict[bitstring] = count

            result.counts = counts_dict
            result.shots = config.shots
            result.success = True
            result.execution_time = time.time() - start_time

            # Update gate counts after transpilation
            result.gate_counts = dict(transpiled.count_ops())
            result.depth = transpiled.depth()

        except Exception as e:
            result.success = False
            result.error_message = str(e)

        return result

    def run_batch(
        self,
        circuits: List[QuantumCircuit],
        config: Optional[BackendConfig] = None,
    ) -> List[ExecutionResult]:
        """
        Execute multiple circuits as a batch job.

        More efficient than individual runs for parameter sweeps.
        """
        if not self.is_connected:
            self.connect()

        config = config or BackendConfig(shots=4096)
        results = []

        try:
            from qiskit_ibm_runtime import SamplerV2 as Sampler

            # Transpile all circuits
            transpiled_circuits = transpile(
                circuits,
                backend=self._backend,
                optimization_level=config.optimization_level,
            )

            # Add measurements
            for tc in transpiled_circuits:
                if not any(
                    instr.operation.name == "measure" for instr in tc.data
                ):
                    tc.measure_all()

            # Submit batch job
            sampler = Sampler(self._backend)
            job = sampler.run(transpiled_circuits, shots=config.shots)
            job_id = job.job_id()

            # Collect results
            pub_results = job.result()
            for i, (circuit, pub_result) in enumerate(
                zip(circuits, pub_results)
            ):
                counts_dict = {}
                for bitstring, count in pub_result.data.meas.get_counts().items():
                    counts_dict[bitstring] = count

                result = ExecutionResult(
                    counts=counts_dict,
                    shots=config.shots,
                    success=True,
                    backend_name=self.device_name,
                    job_id=job_id,
                    num_qubits=circuit.num_qubits,
                    depth=transpiled_circuits[i].depth(),
                    gate_counts=dict(transpiled_circuits[i].count_ops()),
                )
                results.append(result)

        except Exception as e:
            # Return error results for all circuits
            for circuit in circuits:
                results.append(
                    ExecutionResult(
                        success=False,
                        error_message=str(e),
                        backend_name=self.device_name,
                        num_qubits=circuit.num_qubits,
                    )
                )

        return results

    def _get_qiskit_backend(self):
        """Get underlying Qiskit backend."""
        if not self.is_connected:
            self.connect()
        return self._backend

    def list_devices(self) -> List[Dict[str, Any]]:
        """
        List available IBM Quantum devices.

        Returns:
            List of device info dictionaries
        """
        if self._service is None:
            try:
                from qiskit_ibm_runtime import QiskitRuntimeService

                self._service = QiskitRuntimeService(channel=self.channel)
            except Exception as e:
                raise RuntimeError(f"Cannot list devices: {e}")

        devices = []
        for backend in self._service.backends():
            devices.append(
                {
                    "name": backend.name,
                    "qubits": backend.num_qubits,
                    "status": backend.status().status_msg,
                    "operational": backend.status().operational,
                    "pending_jobs": backend.status().pending_jobs,
                }
            )
        return devices

    def get_device_info(self) -> Dict[str, Any]:
        """Get detailed info about the current device."""
        if not self.is_connected:
            self.connect()

        return {
            "name": self._backend.name,
            "num_qubits": self._backend.num_qubits,
            "basis_gates": list(self._backend.operation_names),
            "coupling_map": list(self._backend.coupling_map.get_edges()),
            "status": self._backend.status().status_msg,
        }

    @staticmethod
    def save_credentials(token: str, channel: str = "ibm_quantum") -> None:
        """
        Save IBM Quantum credentials for future use.

        Args:
            token: IBM Quantum API token
            channel: Service channel
        """
        from qiskit_ibm_runtime import QiskitRuntimeService

        QiskitRuntimeService.save_account(
            channel=channel,
            token=token,
            overwrite=True,
        )
