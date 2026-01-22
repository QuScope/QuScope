"""
Tests for quantum backend abstraction layer.
"""

import numpy as np
import pytest
from qiskit import QuantumCircuit


class TestBackendFactory:
    """Test get_backend factory function."""

    def test_get_simulator_backend(self):
        """Test creating simulator backend."""
        from quscope.quantum_ctem import get_backend

        backend = get_backend("simulator")
        assert backend is not None
        assert "simulator" in backend.name.lower()

    def test_get_statevector_backend(self):
        """Test statevector alias."""
        from quscope.quantum_ctem import get_backend

        backend = get_backend("statevector")
        assert backend is not None

    def test_get_ibm_backend(self):
        """Test creating IBM backend (without credentials)."""
        from quscope.quantum_ctem import get_backend

        backend = get_backend("ibm")
        assert backend is not None
        assert "ibm" in backend.name.lower()

    def test_invalid_backend_raises(self):
        """Test that invalid backend type raises ValueError."""
        from quscope.quantum_ctem import get_backend

        with pytest.raises(ValueError, match="Unknown backend"):
            get_backend("invalid_backend")

    def test_list_available_backends(self):
        """Test listing available backends."""
        from quscope.quantum_ctem import list_available_backends

        backends = list_available_backends()
        assert isinstance(backends, dict)
        assert "simulator" in backends
        assert "ibm" in backends


class TestSimulatorBackend:
    """Test SimulatorBackend class."""

    @pytest.fixture
    def backend(self):
        """Create simulator backend."""
        from quscope.quantum_ctem import SimulatorBackend

        return SimulatorBackend()

    def test_connect(self, backend):
        """Test backend connection."""
        result = backend.connect()
        assert result is True
        assert backend.is_connected is True

    def test_run_simple_circuit(self, backend):
        """Test running a simple circuit."""
        backend.connect()

        # Create simple circuit
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)

        from quscope.quantum_ctem import BackendConfig

        config = BackendConfig(shots=0)  # Statevector
        result = backend.run(qc, config)

        assert result.success is True
        assert result.statevector is not None
        assert len(result.statevector) == 4  # 2^2 states

    def test_run_with_shots(self, backend):
        """Test running with measurement shots."""
        backend.connect()

        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure([0, 1], [0, 1])

        from quscope.quantum_ctem import BackendConfig

        config = BackendConfig(shots=1024)
        result = backend.run(qc, config)

        assert result.success is True
        assert result.shots == 1024
        assert len(result.counts) > 0

    def test_simulate_ctem_wavefunction(self, backend):
        """Test CTEM wavefunction simulation."""
        from quscope.quantum_ctem import QuantumWaveFunction

        backend.connect()

        # Create test wave function (8x8)
        nx, ny = 8, 8
        x = np.linspace(-2, 2, nx)
        y = np.linspace(-2, 2, ny)
        X, Y = np.meshgrid(x, y)
        psi = np.exp(-(X**2 + Y**2) / 2) * np.exp(1j * np.pi / 4)

        # Encode wave function as quantum circuit
        qwf = QuantumWaveFunction(n_qubits_x=3, n_qubits_y=3)  # 2^3 = 8
        circuit = qwf.prepare_arbitrary_wave(psi)

        # Simulate and get wavefunction back
        psi_out = backend.simulate_ctem_wavefunction(circuit, nx, ny)
        assert psi_out is not None
        assert psi_out.shape == (ny, nx)


class TestExecutionResult:
    """Test ExecutionResult dataclass."""

    def test_get_statevector_2d(self):
        """Test reshaping statevector to 2D."""
        from quscope.quantum_ctem import ExecutionResult

        # Create result with 16 element statevector (4x4)
        sv = np.random.randn(16) + 1j * np.random.randn(16)
        sv = sv / np.linalg.norm(sv)

        result = ExecutionResult(statevector=sv)
        psi_2d = result.get_statevector_2d(4, 4)

        assert psi_2d.shape == (4, 4)

    def test_get_intensity(self):
        """Test getting intensity from statevector."""
        from quscope.quantum_ctem import ExecutionResult

        sv = np.array([0.5, 0.5, 0.5, 0.5])
        result = ExecutionResult(statevector=sv)

        intensity = result.get_intensity(2, 2)
        assert intensity.shape == (2, 2)
        assert np.allclose(intensity, 0.25)

    def test_missing_statevector_raises(self):
        """Test error when statevector is missing."""
        from quscope.quantum_ctem import ExecutionResult

        result = ExecutionResult()
        with pytest.raises(ValueError, match="No statevector"):
            result.get_statevector_2d(4, 4)


class TestBackendConfig:
    """Test BackendConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        from quscope.quantum_ctem import BackendConfig

        config = BackendConfig()
        assert config.shots == 1024
        assert config.optimization_level == 3

    def test_custom_values(self):
        """Test custom configuration."""
        from quscope.quantum_ctem import BackendConfig

        config = BackendConfig(shots=4096, optimization_level=1)
        assert config.shots == 4096
        assert config.optimization_level == 1

    def test_to_dict(self):
        """Test conversion to dictionary."""
        from quscope.quantum_ctem import BackendConfig

        config = BackendConfig(shots=2048)
        d = config.to_dict()
        assert isinstance(d, dict)
        assert d["shots"] == 2048
