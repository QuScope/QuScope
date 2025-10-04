"""
Test WPOA simulator with realistic graphene structure.

Uses ASE to generate graphene supercell and validates that it behaves as
a weak phase object (small phase shifts, intensity variations).
"""

import pytest
import numpy as np
from ase.build import graphene

from quscope.ctem import WPOASimulator


@pytest.fixture
def graphene_atoms():
    """
    Create a graphene supercell using ASE.
    
    Returns graphene structure suitable for weak phase object approximation:
    - Single layer (truly 2D)
    - Small supercell (5x3) for computational efficiency
    - Carbon atoms (Z=6) - light element, ideal for WPOA
    """
    # Create graphene unit cell with 2 Å vacuum
    atoms = graphene(vacuum=2.0)
    
    # Create 5x3 supercell (30 carbon atoms)
    atoms *= (5, 3, 1)
    
    return atoms


@pytest.fixture
def graphene_positions(graphene_atoms):
    """
    Extract atomic positions from ASE Atoms object.
    
    Returns list of (x, y, Z) tuples for WPOA simulator.
    """
    positions = []
    for atom in graphene_atoms:
        x, y, z = atom.position
        Z = atom.number  # Atomic number (6 for carbon)
        positions.append((x, y, Z))
    
    return positions


class TestGrapheneWPOA:
    """Test WPOA simulator with realistic graphene structure."""
    
    def test_graphene_structure_generation(self, graphene_atoms):
        """Verify graphene structure is correctly generated."""
        # Should have 30 carbon atoms (5x3 supercell, 2 atoms per unit cell)
        assert len(graphene_atoms) == 30
        
        # All atoms should be carbon (Z=6)
        assert all(atom.number == 6 for atom in graphene_atoms)
        
        # Check approximate cell dimensions
        # Graphene lattice constant: ~2.46 Å
        # 5x3 supercell: ~12.3 x 6.4 Å
        cell = graphene_atoms.get_cell()
        assert 12.0 < cell[0, 0] < 13.0  # x dimension
        assert 6.0 < cell[1, 1] < 7.0    # y dimension
        
    def test_graphene_positions_format(self, graphene_positions):
        """Verify positions are in correct format for simulator."""
        assert len(graphene_positions) == 30
        
        # Each position should be (x, y, Z) tuple
        for pos in graphene_positions:
            assert len(pos) == 3
            x, y, Z = pos
            assert isinstance(x, (int, float))
            assert isinstance(y, (int, float))
            assert Z == 6  # Carbon
    
    def test_graphene_transmission_function(self, graphene_positions):
        """
        Test transmission function calculation for graphene.
        
        Graphene should exhibit weak phase object behavior:
        - Small phase shifts (WPOA valid for φ << π)
        - All phases positive (no negative potentials)
        """
        # Use smaller image size to encompass graphene structure
        # Graphene supercell is ~12 x 7 Å, add margin
        sim = WPOASimulator(
            image_size=20.0,  # 20 Å x 20 Å
            pixels=256,        # 256 x 256 pixels
            beam_energy=200e3  # 200 keV
        )
        
        transmission, potential = sim.calculate_transmission_function(graphene_positions)
        
        # Extract phases
        phases = np.angle(transmission)
        
        # Phases should be small (weak phase object condition)
        # For carbon monolayer, expect max phase < 0.6 radians
        # (overlapping atoms in honeycomb can give slightly higher values)
        max_phase = np.max(phases)
        min_phase = np.min(phases)
        
        print(f"\nGraphene phase range: [{min_phase:.4f}, {max_phase:.4f}] radians")
        
        # Verify weak phase object condition (φ << π)
        # Using π/3 ≈ 1.05 rad as validity limit
        assert max_phase < 0.7, f"Phase too large for WPOA: {max_phase:.4f} rad"
        assert min_phase >= 0.0, "Negative phases indicate potential calculation error"
        
        # Verify potential is positive (attractive)
        assert np.min(potential) >= 0.0
        assert np.max(potential) > 0.0
        
    def test_graphene_image_simulation(self, graphene_positions):
        """
        Test full image simulation of graphene.
        
        Expected behavior:
        - Intensity variations from carbon atoms
        - Honeycomb pattern should be visible (qualitatively)
        - Intensity range close to 1.0 (weak contrast for single layer)
        """
        sim = WPOASimulator(
            image_size=20.0,
            pixels=256,
            beam_energy=200e3
        )
        
        # Simulate with typical HRTEM parameters
        results = sim.simulate_image(
            atom_positions=graphene_positions,
            defocus=500.0,       # 500 Å underfocus (Scherzer-ish)
            Cs=1.3e7,            # 1.3 mm Cs
            alpha_max=10.0       # 10 mrad aperture
        )
        
        intensity = results['intensity']
        
        # Check intensity statistics
        I_mean = np.mean(intensity)
        I_std = np.std(intensity)
        I_min = np.min(intensity)
        I_max = np.max(intensity)
        
        print(f"\nGraphene intensity statistics:")
        print(f"  Mean: {I_mean:.4f}")
        print(f"  Std:  {I_std:.4f}")
        print(f"  Min:  {I_min:.4f}")
        print(f"  Max:  {I_max:.4f}")
        print(f"  Range: [{I_min:.4f}, {I_max:.4f}]")
        
        # Single layer graphene should have weak contrast
        # Intensity should be close to 1.0 with small variations
        assert 0.90 < I_mean < 1.05, f"Mean intensity unexpected: {I_mean:.4f}"
        assert I_std < 0.10, f"Contrast too high for single layer: {I_std:.4f}"
        
        # Verify some contrast is present (not completely flat)
        assert I_max > I_min, "No contrast detected"
        assert (I_max - I_min) > 0.01, "Contrast too weak to detect atoms"
        
    def test_graphene_vs_kirkland_single_atom(self, graphene_positions):
        """
        Compare graphene simulation with single carbon atom.
        
        Validates that:
        - Graphene phases are superposition of individual carbon atoms
        - Multiple atoms increase total phase shift
        - Simulator handles both single atoms and complex structures
        """
        sim = WPOASimulator(
            image_size=20.0,
            pixels=256,
            beam_energy=200e3
        )
        
        # Simulate graphene (30 atoms)
        trans_graphene, pot_graphene = sim.calculate_transmission_function(graphene_positions)
        phase_graphene = np.angle(trans_graphene)
        
        # Simulate single carbon atom at origin
        single_carbon = [(0.0, 0.0, 6)]
        trans_single, pot_single = sim.calculate_transmission_function(single_carbon)
        phase_single = np.angle(trans_single)
        
        # Graphene max phase should be larger than single atom
        # (due to overlapping potentials from nearby atoms)
        assert np.max(phase_graphene) > np.max(phase_single)
        
        # But still should be reasonable for WPOA
        assert np.max(phase_graphene) < 1.0, "Phase too large for WPOA"
        
        print(f"\nPhase comparison:")
        print(f"  Single carbon: {np.max(phase_single):.4f} rad")
        print(f"  Graphene:      {np.max(phase_graphene):.4f} rad")
        print(f"  Ratio:         {np.max(phase_graphene) / np.max(phase_single):.2f}x")


class TestGrapheneWPOAValidation:
    """Validation tests comparing graphene simulation to expected behavior."""
    
    def test_graphene_weak_phase_condition(self, graphene_positions):
        """
        Validate that graphene satisfies weak phase object approximation.
        
        WPOA requires: φ(x,y) << π
        For validity: typically φ < π/3 (~1 radian)
        """
        sim = WPOASimulator(
            image_size=20.0,
            pixels=256,
            beam_energy=200e3
        )
        
        transmission, _ = sim.calculate_transmission_function(graphene_positions)
        phases = np.angle(transmission)
        
        # Calculate phase statistics
        max_phase = np.max(phases)
        mean_phase = np.mean(phases[phases > 0])  # Exclude zero background
        
        # WPOA validity criterion
        WPOA_LIMIT = np.pi / 3.0  # Conservative limit (~1 radian)
        
        assert max_phase < WPOA_LIMIT, \
            f"WPOA not valid: max phase {max_phase:.3f} rad > {WPOA_LIMIT:.3f} rad"
        
        print(f"\nWPOA validity check:")
        print(f"  Max phase:  {max_phase:.4f} rad")
        print(f"  Mean phase: {mean_phase:.4f} rad")
        print(f"  Limit (π/3): {WPOA_LIMIT:.4f} rad")
        print(f"  WPOA valid: {max_phase < WPOA_LIMIT}")
    
    def test_graphene_different_beam_energies(self, graphene_positions):
        """
        Test graphene simulation at different beam energies.
        
        Higher energy → shorter wavelength → smaller phase shifts
        """
        energies = [80e3, 200e3, 300e3]  # 80, 200, 300 keV
        max_phases = []
        
        for energy in energies:
            sim = WPOASimulator(
                image_size=20.0,
                pixels=256,
                beam_energy=energy
            )
            
            transmission, _ = sim.calculate_transmission_function(graphene_positions)
            phases = np.angle(transmission)
            max_phase = np.max(phases)
            max_phases.append(max_phase)
            
            print(f"\n{energy/1000:.0f} keV: max phase = {max_phase:.4f} rad")
        
        # Higher energy should give smaller phases
        # (due to shorter wavelength and smaller sigma)
        assert max_phases[0] > max_phases[1] > max_phases[2], \
            "Phase should decrease with increasing beam energy"
        
        # All should still satisfy WPOA
        for energy, phase in zip(energies, max_phases):
            assert phase < np.pi / 3.0, \
                f"WPOA invalid at {energy/1000:.0f} keV: phase = {phase:.3f} rad"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
