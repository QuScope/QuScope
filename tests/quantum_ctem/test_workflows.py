"""
Tests for quantum CTEM workflows.
"""

import numpy as np
import pytest


# Skip all tests if ASE is not available
pytest.importorskip("ase")


class TestMoS2Workflow:
    """Test MoS2Workflow class."""

    @pytest.fixture
    def workflow(self):
        """Create MoS2 workflow with simulator backend."""
        from quscope.quantum_ctem import MoS2Workflow, get_backend

        backend = get_backend("simulator")
        backend.connect()
        return MoS2Workflow(backend=backend, voltage=200e3)

    def test_workflow_creation(self, workflow):
        """Test workflow is created correctly."""
        assert workflow is not None
        assert workflow.microscope.voltage == 200e3

    def test_run_simulation(self, workflow):
        """Test running a simulation."""
        result = workflow.run(nx=2, ny=2, grid_size=16, pixel_size=0.1)

        assert result is not None
        assert result.material_name == "Molybdenum Disulfide"
        assert result.grid_size == 16
        assert result.intensity is not None
        assert result.intensity.shape == (16, 16)

    def test_run_with_ctf(self, workflow):
        """Test running with CTF enabled."""
        result = workflow.run(nx=2, ny=2, grid_size=16, apply_ctf=True)
        assert result.intensity is not None

    def test_run_without_ctf(self, workflow):
        """Test running without CTF."""
        result = workflow.run(nx=2, ny=2, grid_size=16, apply_ctf=False)
        assert result.intensity is not None

    def test_result_summary(self, workflow):
        """Test result summary method."""
        result = workflow.run(nx=2, ny=2, grid_size=16)
        summary = result.summary()

        assert isinstance(summary, str)
        assert "MoS" in summary or "Molybdenum" in summary
        assert str(result.n_atoms) in summary

    def test_invalid_grid_size_raises(self, workflow):
        """Test that non-power-of-2 grid size raises error."""
        with pytest.raises(ValueError, match="power of 2"):
            workflow.run(nx=2, ny=2, grid_size=17)


class TestGrapheneWorkflow:
    """Test GrapheneWorkflow class."""

    @pytest.fixture
    def workflow(self):
        """Create Graphene workflow with simulator backend."""
        from quscope.quantum_ctem import GrapheneWorkflow, get_backend

        backend = get_backend("simulator")
        backend.connect()
        return GrapheneWorkflow(backend=backend, voltage=80e3)

    def test_workflow_creation(self, workflow):
        """Test workflow is created correctly."""
        assert workflow is not None
        assert workflow.microscope.voltage == 80e3

    def test_run_simulation(self, workflow):
        """Test running a graphene simulation."""
        result = workflow.run(nx=2, ny=2, grid_size=16, pixel_size=0.1)

        assert result is not None
        assert "Graphene" in result.material_name
        assert result.grid_size == 16
        assert result.intensity is not None
        assert result.intensity.shape == (16, 16)

    def test_wpoa_validity_check(self, workflow):
        """Test WPOA validity is checked."""
        result = workflow.run(nx=2, ny=2, grid_size=16)
        assert hasattr(result, "wpoa_valid")
        assert result.wpoa_valid == True  # Graphene at 80kV should be WPOA valid

    def test_run_nanoribbon(self, workflow):
        """Test nanoribbon simulation."""
        result = workflow.run_nanoribbon(
            width=3, length=5, edge_type="zigzag", grid_size=16
        )
        assert result is not None
        assert "Nanoribbon" in result.material_name

    def test_run_with_vacancies(self, workflow):
        """Test simulation with vacancy defects."""
        result = workflow.run_with_vacancies(
            nx=3, ny=3, vacancy_fraction=0.05, grid_size=16, seed=42
        )
        assert result is not None
        assert "vacanc" in result.material_name.lower()

    def test_validate_wpoa(self, workflow):
        """Test WPOA validation method."""
        validity = workflow.validate_wpoa()
        assert "wpoa_valid" in validity
        assert "max_phase_shift" in validity


class TestMicroscopeConfig:
    """Test MicroscopeConfig class."""

    def test_default_values(self):
        """Test default microscope configuration."""
        from quscope.quantum_ctem import MicroscopeConfig

        config = MicroscopeConfig(voltage=200e3)
        assert config.voltage == 200e3
        assert config.wavelength > 0
        assert config.cs >= 0

    def test_wavelength_calculation(self):
        """Test electron wavelength calculation."""
        from quscope.quantum_ctem import MicroscopeConfig

        config_200kV = MicroscopeConfig(voltage=200e3)
        config_80kV = MicroscopeConfig(voltage=80e3)

        # Higher voltage → shorter wavelength
        assert config_200kV.wavelength < config_80kV.wavelength

        # 200 kV wavelength should be ~0.025 Å
        assert 0.02 < config_200kV.wavelength < 0.03

    def test_scherzer_defocus(self):
        """Test Scherzer defocus calculation."""
        from quscope.quantum_ctem import MicroscopeConfig

        config = MicroscopeConfig(voltage=200e3, cs=1.0)  # 1 mm Cs
        scherzer = config.scherzer_defocus

        # Scherzer defocus should be negative (underfocus)
        assert scherzer < 0


class TestSimulationResult:
    """Test SimulationResult dataclass."""

    def test_result_attributes(self):
        """Test result has expected attributes."""
        from quscope.quantum_ctem import SimulationResult, MicroscopeConfig

        config = MicroscopeConfig(voltage=200e3)
        result = SimulationResult(
            material_name="Test",
            n_atoms=10,
            supercell_size=(2, 2),
            grid_size=16,
            pixel_size=0.1,
            field_of_view=(5.0, 5.0),
            wavefunction=np.ones((16, 16), dtype=complex),
            intensity=np.ones((16, 16)),
            phase=np.zeros((16, 16)),
            projected_potential=np.ones((16, 16)),
            transmission_function=np.ones((16, 16), dtype=complex),
            microscope_config=config,
            backend_result=None,
            execution_time=0.1,
            circuit_depth=10,
            n_qubits=8,
        )

        assert result.material_name == "Test"
        assert result.n_atoms == 10
        assert result.grid_size == 16

    def test_summary_method(self):
        """Test summary method returns string."""
        from quscope.quantum_ctem import SimulationResult, MicroscopeConfig

        config = MicroscopeConfig(voltage=200e3)
        result = SimulationResult(
            material_name="Test",
            n_atoms=10,
            supercell_size=(2, 2),
            grid_size=16,
            pixel_size=0.1,
            field_of_view=(5.0, 5.0),
            wavefunction=None,
            intensity=np.ones((16, 16)),
            phase=None,
            projected_potential=None,
            transmission_function=None,
            microscope_config=config,
            backend_result=None,
            execution_time=0.1,
            circuit_depth=10,
            n_qubits=8,
        )

        summary = result.summary()
        assert isinstance(summary, str)
        assert "Test" in summary


class TestDefocusSeries:
    """Test defocus series functionality."""

    def test_run_defocus_series(self):
        """Test running defocus series."""
        from quscope.quantum_ctem import MoS2Workflow, get_backend

        backend = get_backend("simulator")
        backend.connect()
        workflow = MoS2Workflow(backend=backend)

        defoci = [-50, 0, 50]  # Å
        results = workflow.run_defocus_series(
            defocus_values=defoci, nx=2, ny=2, grid_size=16, pixel_size=0.1
        )

        assert len(results) == 3
        for result in results:
            assert result.intensity is not None
