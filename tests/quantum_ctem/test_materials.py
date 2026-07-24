"""
Tests for material definitions.
"""

import numpy as np
import pytest


# Skip all tests if ASE is not available
pytest.importorskip("ase")


class TestMaterialFactory:
    """Test get_material factory function."""

    def test_get_mos2(self):
        """Test creating MoS2 material."""
        from quscope.quantum_ctem import get_material

        mat = get_material("mos2")
        assert mat is not None
        assert "molybdenum" in mat.name.lower()

    def test_get_graphene(self):
        """Test creating graphene material."""
        from quscope.quantum_ctem import get_material

        mat = get_material("graphene")
        assert mat is not None
        assert "graphene" in mat.name.lower()

    def test_invalid_material_raises(self):
        """Test invalid material type raises error."""
        from quscope.quantum_ctem import get_material

        with pytest.raises(ValueError, match="Unknown material"):
            get_material("invalid_material")

    def test_list_materials(self):
        """Test listing available materials."""
        from quscope.quantum_ctem import list_materials

        materials = list_materials()
        assert isinstance(materials, dict)
        assert "mos2" in materials
        assert "graphene" in materials


class TestMoS2Material:
    """Test MoS2 material class."""

    @pytest.fixture
    def mos2(self):
        """Create MoS2 material instance."""
        from quscope.quantum_ctem import MoS2

        return MoS2()

    def test_parameters(self, mos2):
        """Test MoS2 parameters."""
        assert mos2.name == "Molybdenum Disulfide"
        assert "Mo" in mos2.parameters.elements
        assert "S" in mos2.parameters.elements
        assert mos2.parameters.a == pytest.approx(3.16, rel=0.01)

    def test_build_structure(self, mos2):
        """Test building MoS2 structure."""
        atoms = mos2.build_structure(nx=2, ny=2)
        assert len(atoms) > 0
        symbols = set(atoms.get_chemical_symbols())
        assert "Mo" in symbols
        assert "S" in symbols

    def test_build_supercell(self, mos2):
        """Test building supercell."""
        atoms = mos2.build_supercell(nx=3, ny=3)
        assert len(atoms) > 0

    def test_get_scattering_params(self, mos2):
        """Test getting Kirkland scattering parameters."""
        params = mos2.get_scattering_params()
        assert "Mo" in params
        assert "S" in params
        assert len(params["Mo"].a_coefficients) == 4
        assert len(params["Mo"].b_coefficients) == 4

    def test_projected_potential(self, mos2):
        """Test computing projected potential."""
        atoms = mos2.build_structure(nx=2, ny=2)
        V = mos2.get_projected_potential(atoms, grid_size=32, pixel_size=0.2)
        assert V.shape == (32, 32)
        assert np.all(np.isreal(V))
        assert np.max(V) > 0  # Should have positive values at atom positions

    def test_get_column_positions(self, mos2):
        """Test getting atomic column positions."""
        atoms = mos2.build_structure(nx=2, ny=2)
        columns = mos2.get_column_positions(atoms)
        assert "Mo" in columns
        assert "S" in columns


class TestGrapheneMaterial:
    """Test Graphene material class."""

    @pytest.fixture
    def graphene(self):
        """Create graphene material instance."""
        from quscope.quantum_ctem import Graphene

        return Graphene()

    def test_parameters(self, graphene):
        """Test graphene parameters."""
        assert graphene.name == "Graphene"
        assert "C" in graphene.parameters.elements
        assert graphene.parameters.a == pytest.approx(2.46, rel=0.01)

    def test_build_structure(self, graphene):
        """Test building graphene structure."""
        atoms = graphene.build_structure(nx=3, ny=3)
        assert len(atoms) > 0
        symbols = set(atoms.get_chemical_symbols())
        assert "C" in symbols

    def test_build_nanoribbon(self, graphene):
        """Test building graphene nanoribbon."""
        atoms = graphene.build_nanoribbon(width=5, length=10, edge_type="zigzag")
        assert len(atoms) > 0

    def test_build_with_vacancy(self, graphene):
        """Test building graphene with vacancies."""
        atoms_pristine = graphene.build_structure(nx=5, ny=5)
        atoms_defect = graphene.build_with_vacancy(nx=5, ny=5, vacancy_fraction=0.1)
        assert len(atoms_defect) < len(atoms_pristine)

    def test_wpoa_validity(self, graphene):
        """Test WPOA validity assessment."""
        validity = graphene.wpoa_validity(voltage=200e3)
        assert "wpoa_valid" in validity
        assert "max_phase_shift" in validity
        # max_phase_shift is evaluated essentially at the atom center (r=0.01 A),
        # where the Kirkland projected potential is log-divergent (Bessel K0
        # term); even for light carbon this exceeds the 0.3 rad rule-of-thumb,
        # so WPOA is only marginally valid right at the core -- it remains a
        # good approximation over the bulk of the image away from atom centers.
        assert validity["max_phase_shift"] > 0.3
        assert validity["wpoa_valid"] == False

    def test_get_sublattice_positions(self, graphene):
        """Test getting sublattice positions."""
        atoms = graphene.build_structure(nx=3, ny=3)
        sublattices = graphene.get_sublattice_positions(atoms)
        assert "A" in sublattices
        assert "B" in sublattices

    def test_get_diffraction_spots(self, graphene):
        """Test getting expected diffraction spots."""
        spots = graphene.get_diffraction_spots()
        assert "b1" in spots
        assert "b2" in spots
        assert "first_order" in spots


class TestMaterialInterface:
    """Test the Material base class interface."""

    def test_interaction_constant(self):
        """Test interaction constant calculation."""
        from quscope.quantum_ctem import MoS2

        mat = MoS2()
        sigma_200kV = mat.get_interaction_constant(200e3)
        sigma_80kV = mat.get_interaction_constant(80e3)

        # Higher voltage → smaller interaction constant
        assert sigma_80kV > sigma_200kV
        # Typical values are around 0.0005-0.002 rad/V·Å at 200kV
        # (relativistic correction factor affects the value)
        assert 0.0001 < sigma_200kV < 0.005

    def test_transmission_function(self):
        """Test computing transmission function via WPOA."""
        from quscope.quantum_ctem import MoS2

        mat = MoS2()
        atoms = mat.build_structure(nx=2, ny=2)
        V_proj = mat.get_projected_potential(atoms, grid_size=32, pixel_size=0.2)

        # Compute transmission function using WPOA: T = exp(i σ V)
        sigma = mat.get_interaction_constant(200e3)
        T = np.exp(1j * sigma * V_proj)

        # Transmission function should be complex with |T| ≈ 1 for weak phase objects
        assert T.shape == V_proj.shape
        assert T.dtype == complex
        assert np.allclose(np.abs(T), 1.0)  # Pure phase modulation
