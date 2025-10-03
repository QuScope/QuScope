"""
Unit tests for Kirkland atomic potential module.
"""

import pytest
import numpy as np
from quscope.ctem.kirkland_potential import KirklandPotential


class TestKirklandPotential:
    """Test suite for KirklandPotential class."""
    
    @pytest.fixture
    def pot(self):
        """Create KirklandPotential instance for testing."""
        return KirklandPotential()
    
    def test_initialization(self, pot):
        """Test initialization with default parameters file."""
        assert pot.params_dict is not None
        assert 'C' in pot.params_dict
        assert 'Si' in pot.params_dict
    
    def test_element_symbol_lookup(self, pot):
        """Test atomic number to element symbol conversion."""
        assert pot.get_element_symbol(6) == 'C'
        assert pot.get_element_symbol(14) == 'Si'
        assert pot.get_element_symbol(29) == 'Cu'
        assert pot.get_element_symbol(79) == 'Au'
        assert pot.get_element_symbol(92) == 'U'
    
    def test_calculate_2d_single_atom_center(self, pot):
        """Test potential calculation at atom center (r=0)."""
        x = np.array([0.0])
        y = np.array([0.0])
        
        V = pot.calculate_2d(x, y, atom_x=0.0, atom_y=0.0, Z=6)
        
        # Potential at center should be large and positive
        # Carbon at r=0 is ~5600 eV based on Kirkland parameters
        assert V[0] > 1000.0
        assert V[0] < 10000.0
        assert np.isfinite(V[0])
    
    def test_calculate_2d_single_atom_decay(self, pot):
        """Test potential decays with distance from atom."""
        r = np.linspace(0, 10, 100)
        x = r
        y = np.zeros_like(r)
        
        V = pot.calculate_2d(x, y, atom_x=0.0, atom_y=0.0, Z=6)
        
        # Potential should decay monotonically
        assert np.all(np.diff(V) < 0)
        
        # Potential should approach zero at large distances
        assert V[-1] < V[0] / 100
    
    def test_calculate_multiple_atoms_superposition(self, pot):
        """Test that multiple atoms use superposition principle."""
        x = np.linspace(-5, 5, 100)
        y = np.zeros_like(x)
        
        # Two carbon atoms
        positions = [(0, 0, 6), (3, 0, 6)]
        
        V_total = pot.calculate_multiple_atoms(x, y, positions)
        
        # Calculate individually
        V1 = pot.calculate_2d(x, y, 0, 0, Z=6)
        V2 = pot.calculate_2d(x, y, 3, 0, Z=6)
        
        # Should match superposition
        np.testing.assert_allclose(V_total, V1 + V2, rtol=1e-10)
    
    def test_potential_symmetry(self, pot):
        """Test that potential is radially symmetric."""
        r = 2.0
        
        # Points at same distance but different angles
        points = [
            (r, 0),
            (0, r),
            (-r, 0),
            (0, -r),
            (r/np.sqrt(2), r/np.sqrt(2)),
        ]
        
        potentials = []
        for px, py in points:
            V = pot.calculate_2d(np.array([px]), np.array([py]), 0, 0, Z=6)
            potentials.append(V[0])
        
        # All should be equal (radial symmetry)
        np.testing.assert_allclose(potentials, potentials[0], rtol=1e-10)
    
    def test_calculate_2d_large_grid(self, pot):
        """Test calculation on realistic grid sizes (256x256)."""
        n = 256
        x = np.linspace(-25, 25, n)
        y = np.linspace(-25, 25, n)
        X, Y = np.meshgrid(x, y, indexing='xy')
        
        V = pot.calculate_2d(X, Y, 0, 0, Z=6)
        
        assert V.shape == (n, n)
        assert np.all(np.isfinite(V))
        assert np.all(V >= 0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
