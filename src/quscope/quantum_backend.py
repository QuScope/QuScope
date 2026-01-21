"""
IBM Quantum backend management module for QuScope.

This module provides utilities for connecting to IBM Quantum backends,
executing quantum circuits, and managing results. It supports both
simulator and real hardware execution with proper error handling.
"""

import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.providers import Backend, JobStatus
from qiskit.providers.exceptions import QiskitBackendNotFoundError
from qiskit.providers.job import JobV1 as Job
from qiskit.result import Result
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel

# Try to import IBM provider - make it optional for compatibility
try:
    from qiskit_ibm_provider import IBMProvider
    from qiskit_ibm_provider.exceptions import (
        IBMAccountError,
        IBMBackendValueError,
        IBMProviderError,
    )
    from qiskit_ibm_provider.job import IBMJob

    IBM_PROVIDER_AVAILABLE = True
except ImportError:
    # Create mock classes for when IBM provider is not available
    class IBMProvider:
        """Mock IBMProvider for when qiskit-ibm-provider is not available."""

        pass

    class IBMJob:
        """Mock IBMJob for when qiskit-ibm-provider is not available."""

        pass

    class IBMAccountError(Exception):
        """Mock IBMAccountError for when qiskit-ibm-provider is not available."""

        pass

    class IBMProviderError(Exception):
        """Mock IBMProviderError for when qiskit-ibm-provider is not available."""

        pass

    class IBMBackendValueError(Exception):
        """Mock IBMBackendValueError for when qiskit-ibm-provider is not available."""

        pass

    IBM_PROVIDER_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_SHOTS = 1024
DEFAULT_OPTIMIZATION_LEVEL = 1
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds


class IBMQuantumError(Exception):
    """Base exception for IBM Quantum related errors."""

    pass


class AuthenticationError(IBMQuantumError):
    """Exception raised for authentication errors."""

    pass


class BackendError(IBMQuantumError):
    """Exception raised for backend errors."""

    pass


class ExecutionError(IBMQuantumError):
    """Exception raised for circuit execution errors."""

    pass


@dataclass
class IBMQConfig:
    """Configuration for IBM Quantum access."""

    token: Optional[str] = None
    hub: str = "ibm-q"
    group: str = "open"
    project: str = "main"

    def get_provider_config(self) -> Dict[str, str]:
        """Get the provider configuration dictionary.

        Returns:
            Dict[str, str]: Provider configuration with hub, group, project.
        """
        return {"hub": self.hub, "group": self.group, "project": self.project}


class QuantumBackendManager:
    """Manager for IBM Quantum backends.

    This class provides methods for authenticating with IBM Quantum,
    selecting backends, executing circuits, and monitoring jobs.

    Attributes:
        config (IBMQConfig): IBM Quantum configuration.
        provider (Optional[IBMProvider]): IBM Quantum provider instance.
        current_backend (Optional[Backend]): Currently selected backend.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        load_account: bool = True,
        config: Optional[IBMQConfig] = None,
    ) -> None:
        """Initialize the Quantum Backend Manager.

        Args:
            token (Optional[str]): IBM Quantum API token. If None, will try to
                load from environment variable IBMQ_TOKEN.
            load_account (bool): Whether to load the account on initialization.
            config (Optional[IBMQConfig]): IBM Quantum configuration.
                If None, default configuration will be used.

        Raises:
            AuthenticationError: If authentication fails.
        """
        self.config = config if config else IBMQConfig(token=token)
        self.provider = None
        self.current_backend = None

        # Try to get token from environment if not provided
        if not self.config.token and "IBMQ_TOKEN" in os.environ:
            self.config.token = os.environ["IBMQ_TOKEN"]

        if load_account and self.config.token:
            try:
                self.authenticate()
            except IBMAccountError as e:
                logger.warning(f"Authentication failed: {str(e)}")
                logger.info(
                    "Continuing without authentication. "
                    "Only local simulators will be available."
                )

    def authenticate(self) -> None:
        """Authenticate with IBM Quantum.

        Raises:
            AuthenticationError: If authentication fails.
        """
        if not self.config.token:
            raise AuthenticationError(
                "No IBM Quantum token provided. Set the token in the config or "
                "use the IBMQ_TOKEN environment variable."
            )

        try:
            # Save account for future use
            IBMProvider.save_account(token=self.config.token, overwrite=True)

            # Load the account - newer versions don't accept hub/group/project in constructor
            self.provider = IBMProvider()
            logger.info("Successfully authenticated with IBM Quantum.")
        except IBMAccountError as e:
            raise AuthenticationError(f"Failed to authenticate: {str(e)}")
        except Exception as e:
            # Handle other potential errors
            logger.warning(f"Error initializing IBM Quantum backend: {str(e)}")
            logger.info("Continuing with local simulator only.")
            self.provider = None

    def get_available_backends(
        self, simulator_only: bool = False, operational: bool = True
    ) -> List[str]:
        """Get a list of available backend names.

        Args:
            simulator_only (bool): If True, only return simulator backends.
            operational (bool): If True, only return operational backends.

        Returns:
            List[str]: List of available backend names.

        Raises:
            BackendError: If failed to retrieve backends.
        """
        backends = []

        # Always include local simulators
        backends.append("aer_simulator")

        # Return only local simulator if requested or no provider
        if simulator_only or not self.provider:
            return backends

        try:
            # Get remote backends
            remote_backends = self.provider.backends(
                operational=operational, simulator=False
            )
            backends.extend([b.name for b in remote_backends])

            # Get remote simulators
            if not simulator_only:
                remote_simulators = self.provider.backends(
                    operational=operational, simulator=True
                )
                backends.extend([b.name for b in remote_simulators])

            return backends
        except IBMProviderError as e:
            raise BackendError(f"Failed to get backends: {str(e)}")

    def get_backend(self, name: str) -> Backend:
        """Get a specific backend by name.

        Args:
            name (str): Name of the backend.

        Returns:
            Backend: The requested backend.

        Raises:
            BackendError: If the backend is not found.
        """
        # For local simulator
        if name == "aer_simulator":
            return AerSimulator()

        # For IBM Quantum backends
        if not self.provider:
            raise BackendError(
                "No IBM Quantum provider available. "
                "Authenticate first using authenticate()."
            )

        try:
            backend = self.provider.get_backend(name)
            return backend
        except QiskitBackendNotFoundError:
            raise BackendError(f"Backend '{name}' not found.")

    def select_backend(self, name: str) -> None:
        """Select a backend to use for circuit execution.

        Args:
            name (str): Name of the backend.

        Raises:
            BackendError: If the backend is not found.
        """
        self.current_backend = self.get_backend(name)
        logger.info(f"Selected backend: {name}")

    def select_least_busy_backend(
        self, min_qubits: int = 5, simulator: bool = False
    ) -> None:
        """Select the least busy backend with at least the specified qubits.

        Args:
            min_qubits (int): Minimum number of qubits required.
            simulator (bool): Whether to consider simulator backends.

        Raises:
            BackendError: If no suitable backend is found.
        """
        if not self.provider:
            if simulator:
                self.select_backend("aer_simulator")
                return
            else:
                raise BackendError(
                    "No IBM Quantum provider available. "
                    "Authenticate first using authenticate()."
                )

        try:
            # Filter backends by criteria
            backends = self.provider.backends(
                filters=lambda b: (
                    b.configuration().n_qubits >= min_qubits
                    and b.status().operational
                    and (simulator == b.configuration().simulator)
                )
            )

            if not backends:
                raise BackendError(
                    f"No backends found with at least {min_qubits} qubits "
                    f"and simulator={simulator}."
                )

            # Select the least busy backend
            least_busy = min(backends, key=lambda b: b.status().pending_jobs)
            self.current_backend = least_busy
            logger.info(f"Selected least busy backend: {least_busy.name}")
        except IBMProviderError as e:
            raise BackendError(f"Failed to select backend: {str(e)}")

    def get_backend_properties(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Get properties of a backend.

        Args:
            name (Optional[str]): Name of the backend. If None, uses current backend.

        Returns:
            Dict[str, Any]: Backend properties.

        Raises:
            BackendError: If the backend is not found or has no properties.
        """
        backend = self.current_backend
        if name:
            backend = self.get_backend(name)

        if not backend:
            raise BackendError("No backend selected.")

        try:
            if hasattr(backend, "properties") and callable(backend.properties):
                props = backend.properties()
                if props:
                    return props.to_dict()

            # For simulators or backends without properties
            return {
                "name": backend.name,
                "description": (
                    "Simulator" if backend.configuration().simulator else "QPU"
                ),
                "n_qubits": backend.configuration().n_qubits,
                "simulator": backend.configuration().simulator,
            }
        except Exception as e:
            raise BackendError(f"Failed to get backend properties: {str(e)}")

    def get_noise_model(self, backend_name: Optional[str] = None) -> NoiseModel:
        """Get a noise model based on a real backend's properties.

        Args:
            backend_name (Optional[str]): Name of the backend to base noise model on.
                If None, uses current backend.

        Returns:
            NoiseModel: Noise model based on backend properties.

        Raises:
            BackendError: If failed to create noise model.
        """
        try:
            if backend_name:
                backend = self.get_backend(backend_name)
            else:
                backend = self.current_backend
                if not backend:
                    raise BackendError("No backend selected.")

            # Can't get noise model from a simulator
            if backend.configuration().simulator:
                # Try to get a real backend for noise model
                try:
                    if self.provider:
                        real_backends = self.provider.backends(
                            simulator=False, operational=True
                        )
                        if real_backends:
                            backend = real_backends[0]
                    else:
                        logger.warning(
                            "No real backend available for noise model. Using default noise."
                        )
                        return NoiseModel()
                except Exception:
                    logger.warning(
                        "Error getting real backend for noise model. Using default noise."
                    )
                    return NoiseModel()

            # Create noise model from backend properties
            properties = backend.properties()
            noise_model = NoiseModel.from_backend(properties)
            return noise_model
        except Exception as e:
            logger.warning(
                f"Failed to create noise model: {str(e)}. Using default noise."
            )
            return NoiseModel()

    def execute_circuit(
        self,
        circuit: QuantumCircuit,
        shots: int = DEFAULT_SHOTS,
        optimization_level: int = DEFAULT_OPTIMIZATION_LEVEL,
        noise_model: Optional[NoiseModel] = None,
        use_real_backend: bool = False,
        backend_name: Optional[str] = None,
        wait: bool = True,
        timeout: Optional[float] = None,
    ) -> Result:
        """Execute a quantum circuit on the selected backend.

        Args:
            circuit (QuantumCircuit): The quantum circuit to execute.
            shots (int): Number of shots for the execution.
            optimization_level (int): Transpiler optimization level (0-3).
            noise_model (Optional[NoiseModel]): Noise model for simulation.
                Only used with simulators.
            use_real_backend (bool): If True, use a real backend even if a
                simulator is selected.
            backend_name (Optional[str]): Name of the backend to use.
                If None, uses current backend.
            wait (bool): Whether to wait for the job to complete.
            timeout (Optional[float]): Maximum time to wait for job completion in seconds.
                If None, wait indefinitely.

        Returns:
            Result: Execution result.

        Raises:
            ExecutionError: If execution fails.
            BackendError: If no backend is selected.
        """
        # Select backend if specified
        backend = self.current_backend
        if backend_name:
            backend = self.get_backend(backend_name)

        if not backend:
            raise BackendError("No backend selected. Call select_backend() first.")

        # If real backend is requested but current is simulator
        if use_real_backend and backend.configuration().simulator and self.provider:
            try:
                real_backends = self.provider.backends(
                    simulator=False, operational=True
                )
                if real_backends:
                    backend = real_backends[0]
                    logger.info(f"Using real backend: {backend.name}")
                else:
                    logger.warning("No real backends available. Using simulator.")
            except Exception as e:
                logger.warning(
                    f"Failed to get real backend: {str(e)}. Using simulator."
                )

        # Transpile circuit for the target backend
        try:
            transpiled_circuit = transpile(
                circuit, backend=backend, optimization_level=optimization_level
            )
        except Exception as e:
            raise ExecutionError(f"Failed to transpile circuit: {str(e)}")

        # Set up execution parameters
        run_kwargs = {"shots": shots}

        # Add noise model for simulators
        is_simulator = backend.configuration().simulator
        if is_simulator and noise_model:
            run_kwargs["noise_model"] = noise_model

        # Execute circuit
        try:
            job = backend.run(transpiled_circuit, **run_kwargs)
            logger.info(f"Job {job.job_id()} submitted to {backend.name}")

            if wait:
                result = self._wait_for_job(job, timeout=timeout)
                return result
            else:
                return job
        except Exception as e:
            raise ExecutionError(f"Failed to execute circuit: {str(e)}")

    def _wait_for_job(self, job: Job, timeout: Optional[float] = None) -> Result:
        """Wait for a job to complete and return the result.

        Args:
            job (Job): The job to wait for.
            timeout (Optional[float]): Maximum time to wait in seconds.
                If None, wait indefinitely.

        Returns:
            Result: Job result.

        Raises:
            ExecutionError: If job fails or times out.
        """
        start_time = time.time()
        status = job.status()

        # Wait for job to complete
        while status not in [JobStatus.DONE, JobStatus.ERROR, JobStatus.CANCELLED]:
            if timeout and (time.time() - start_time > timeout):
                raise ExecutionError(
                    f"Job {job.job_id()} timed out after {timeout} seconds"
                )

            # Print status update
            queue_position = self._get_queue_position(job)
            if queue_position:
                logger.info(
                    f"Job {job.job_id()} is queued at position {queue_position}"
                )
            else:
                logger.info(f"Job {job.job_id()} status: {status.name}")

            # Wait before checking again
            time.sleep(RETRY_DELAY)
            status = job.status()

        # Check if job completed successfully
        if status is JobStatus.ERROR:
            raise ExecutionError(f"Job {job.job_id()} failed: {job.error_message()}")

        if status is JobStatus.CANCELLED:
            raise ExecutionError(f"Job {job.job_id()} was cancelled")

        # Get results
        try:
            result = job.result()
            logger.info(f"Job {job.job_id()} completed successfully")
            return result
        except Exception as e:
            raise ExecutionError(f"Failed to get job result: {str(e)}")

    def _get_queue_position(self, job: Job) -> Optional[int]:
        """Get the queue position of a job.

        Args:
            job (Job): The job to check.

        Returns:
            Optional[int]: Queue position or None if not available/applicable.
        """
        try:
            if isinstance(job, IBMJob):
                queue_info = job.queue_info()
                if queue_info:
                    return queue_info.position
        except Exception:
            pass
        return None

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job.

        Args:
            job_id (str): ID of the job to cancel.

        Returns:
            bool: True if job was cancelled successfully, False otherwise.
        """
        if not self.provider:
            logger.warning("No IBM Quantum provider available.")
            return False

        try:
            job = self.provider.retrieve_job(job_id)
            job.cancel()
            return True
        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {str(e)}")
            return False

    def get_job_status(self, job_id: str) -> Optional[str]:
        """Get the status of a job.

        Args:
            job_id (str): ID of the job to check.

        Returns:
            Optional[str]: Job status as string or None if job not found.
        """
        if not self.provider:
            logger.warning("No IBM Quantum provider available.")
            return None

        try:
            job = self.provider.retrieve_job(job_id)
            return job.status().name
        except Exception as e:
            logger.error(f"Failed to get job status for {job_id}: {str(e)}")
            return None

    def get_backend_status(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Get the status of a backend.

        Args:
            name (Optional[str]): Name of the backend. If None, uses current backend.

        Returns:
            Dict[str, Any]: Backend status information.

        Raises:
            BackendError: If the backend is not found.
        """
        backend = self.current_backend
        if name:
            backend = self.get_backend(name)

        if not backend:
            raise BackendError("No backend selected.")

        try:
            status = backend.status()
            return {
                "operational": status.operational,
                "pending_jobs": status.pending_jobs,
                "status_msg": status.status_msg,
            }
        except Exception as e:
            raise BackendError(f"Failed to get backend status: {str(e)}")


# Convenience function to get a backend manager with default settings
def get_backend_manager(
    token: Optional[str] = None, load_account: bool = True
) -> QuantumBackendManager:
    """Get a quantum backend manager with default settings.

    Args:
        token (Optional[str]): IBM Quantum API token.
        load_account (bool): Whether to load the account on initialization.

    Returns:
        QuantumBackendManager: Configured backend manager.
    """
    return QuantumBackendManager(token=token, load_account=load_account)
