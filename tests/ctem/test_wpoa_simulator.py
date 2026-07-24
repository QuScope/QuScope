"""
Unit tests for WPOA (Weak Phase Object Approximation) simulator.

Tests validate:
1. Initialization and parameter calculation
2. Wavelength and sigma calculations
3. Transmission function calculation
4. Objective lens transfer function
5. Full image simulation pipeline
6. Validation against Kirkland reference values

Reference:
- Kirkland Figure 5.11: Transmission function for 5 atoms
- Kirkland Figure 5.12: Coherent BF image (200 keV, Cs=1.3mm, Δf=700Å)
"""

import numpy as np
import pytest

from quscope.ctem.wpoa_simulator import WPOASimulator


class TestWPOASimulator:
    """Test suite for WPOASimulator class."""

    @pytest.fixture
    def sim_200kev(self):
        """Create standard 200 keV simulator for testing."""
        return WPOASimulator(image_size=50.0, pixels=512, beam_energy=200e3)

    def test_initialization(self, sim_200kev):
        """Test simulator initialization."""
        assert sim_200kev.image_size == 50.0
        assert sim_200kev.pixels == 512
        assert sim_200kev.beam_energy == 200e3
        assert sim_200kev.potential_calculator is not None

    def test_wavelength_calculation_200kev(self, sim_200kev):
        """
        Test relativistic wavelength calculation for 200 keV.

        Expected: λ ≈ 0.02508 Å (from Kirkland)
        """
        wavelength = sim_200kev.wavelength

        # Should be close to 0.025 Angstroms for 200 keV
        assert 0.024 < wavelength < 0.026

        # More precise check
        assert abs(wavelength - 0.02508) < 0.0001

    def test_wavelength_calculation_100kev(self):
        """Test wavelength for 100 keV (different energy)."""
        sim = WPOASimulator(beam_energy=100e3)

        # 100 keV should give longer wavelength than 200 keV
        assert sim.wavelength > 0.035
        assert sim.wavelength < 0.04

    def test_sigma_calculation_200kev(self, sim_200kev):
        """
        Test interaction parameter σ for 200 keV.

        Expected: σ ≈ 0.000389 rad/eV (empirically calibrated to match Kirkland figures)
        For 5600 eV potential (C at origin) → phase ≈ 2.18 radians
        """
        sigma = sim_200kev.sigma

        # Should be in correct order of magnitude
        # (empirically determined from Kirkland Fig 5.11 output)
        assert 0.0003 < sigma < 0.0005

        # Verify this matches expected behavior:
        # For C atom at origin (V ≈ 5600 eV), phase ≈ 2.18 radians
        expected_phase = sigma * 5600
        assert 2.0 < expected_phase < 2.4  # Matches notebook output

    def test_coordinate_grid_setup(self, sim_200kev):
        """Test that coordinate grids are correctly set up."""
        # Check pixel size
        expected_dx = 50.0 / 512
        assert abs(sim_200kev.dx - expected_dx) < 1e-10

        # Check grid shapes
        assert sim_200kev.X.shape == (512, 512)
        assert sim_200kev.Y.shape == (512, 512)

        # Check grid ranges
        assert np.min(sim_200kev.X) < -24
        assert np.max(sim_200kev.X) > 24
        assert np.min(sim_200kev.Y) < -24
        assert np.max(sim_200kev.Y) > 24

        # Check symmetry (grid centered at origin)
        assert abs(np.mean(sim_200kev.X)) < 0.1
        assert abs(np.mean(sim_200kev.Y)) < 0.1

    def test_transmission_function_single_atom(self, sim_200kev):
        """Test transmission function for a single carbon atom."""
        # Single carbon atom at origin
        atoms = [(0, 0, 6)]

        transmission, potential = sim_200kev.calculate_transmission_function(atoms)

        # Check shapes
        assert transmission.shape == (512, 512)
        assert potential.shape == (512, 512)

        # Transmission should be complex
        assert transmission.dtype == np.complex128

        # Magnitude should be 1 everywhere (weak phase object)
        magnitudes = np.abs(transmission)
        np.testing.assert_allclose(magnitudes, 1.0, rtol=1e-10)

        # Phase should be non-zero near atom center
        center_idx = 512 // 2
        phase_center = np.angle(transmission[center_idx, center_idx])
        assert abs(phase_center) > 0.1  # Significant phase shift

    def test_transmission_function_five_atoms_kirkland_fig_5_11(self, sim_200kev):
        """
        Test five-atom configuration from Kirkland Figure 5.11.

        Configuration: C, Si, Cu, Au, U at -20, -10, 0, 10, 20 Angstroms
        """
        # Five atoms as in Kirkland Figure 5.11
        atoms = [
            (-20, 0, 6),  # C
            (-10, 0, 14),  # Si
            (0, 0, 29),  # Cu
            (10, 0, 79),  # Au
            (20, 0, 92),  # U
        ]

        transmission, potential = sim_200kev.calculate_transmission_function(atoms)

        # Extract line scan through center (y=0)
        center_idx = 512 // 2
        line_real = np.real(transmission[center_idx, :])
        line_imag = np.imag(transmission[center_idx, :])

        # Check that real part dips at atom positions (phase contrast)
        x = sim_200kev.x
        for atom_x, _, Z in atoms:
            idx = np.argmin(np.abs(x - atom_x))
            real_at_atom = line_real[idx]

            # Real part should be less than 1.0 at atom positions
            assert real_at_atom < 1.0

            # Higher Z should give more phase shift (lower real part)
            if Z == 92:  # Uranium
                assert real_at_atom < 0.5

    def test_objective_lens_transfer_function(self, sim_200kev):
        """Test objective lens CTF calculation."""
        # Create frequency grids
        kx = np.fft.fftfreq(128, d=sim_200kev.dx)
        ky = np.fft.fftfreq(128, d=sim_200kev.dx)
        KX, KY = np.meshgrid(kx, ky, indexing="xy")

        # Calculate CTF
        H = sim_200kev.objective_lens_transfer_function(
            KX, KY, defocus=700.0, Cs=1.3e7, alpha_max=None
        )

        # Check shape
        assert H.shape == (128, 128)

        # Should be complex
        assert H.dtype == np.complex128

        # Magnitude should be 1 (no aperture)
        magnitudes = np.abs(H)
        np.testing.assert_allclose(magnitudes, 1.0, rtol=1e-10)

    def test_objective_lens_with_aperture(self, sim_200kev):
        """Test CTF with aperture cutoff."""
        kx = np.fft.fftfreq(128, d=sim_200kev.dx)
        ky = np.fft.fftfreq(128, d=sim_200kev.dx)
        KX, KY = np.meshgrid(kx, ky, indexing="xy")

        alpha_max = 0.01  # 10 mrad in radians

        H = sim_200kev.objective_lens_transfer_function(
            KX, KY, defocus=700.0, Cs=1.3e7, alpha_max=alpha_max
        )

        # Some high frequencies should be cut off
        k = np.sqrt(KX**2 + KY**2)
        k_max = alpha_max / sim_200kev.wavelength

        # Check that frequencies beyond aperture are zero
        high_freq_mask = k > k_max
        if np.any(high_freq_mask):
            assert np.all(np.abs(H[high_freq_mask]) < 1e-10)

    def test_simulate_image_single_atom(self, sim_200kev):
        """Test full image simulation for single atom."""
        atoms = [(0, 0, 6)]  # Carbon at origin

        results = sim_200kev.simulate_image(
            atom_positions=atoms, defocus=700.0, Cs=1.3e7, alpha_max=10.37
        )

        # Check result keys
        assert "intensity" in results
        assert "transmission" in results
        assert "potential" in results
        assert "positions" in results

        # Check shapes
        assert results["intensity"].shape == (512, 512)

        # Intensity should be real and positive
        assert results["intensity"].dtype == np.float64
        assert np.all(results["intensity"] >= 0)

    def test_simulate_image_kirkland_fig_5_12(self, sim_200kev):
        """
        Test full simulation reproducing Kirkland Figure 5.12.

        Parameters from Kirkland:
        - 200 keV electrons
        - Cs = 1.3 mm = 1.3e7 Angstroms
        - Defocus = 700 Angstroms (underfocus)
        - Aperture = 10.37 mrad
        - Expected intensity range: 0.72 to 1.03
        """
        # Five atoms
        atoms = [
            (-20, 0, 6),  # C
            (-10, 0, 14),  # Si
            (0, 0, 29),  # Cu
            (10, 0, 79),  # Au
            (20, 0, 92),  # U
        ]

        results = sim_200kev.simulate_image(
            atom_positions=atoms, defocus=700.0, Cs=1.3e7, alpha_max=10.37
        )

        intensity = results["intensity"]

        # Check intensity range (Kirkland reports 0.72 to 1.03)
        I_min = np.min(intensity)
        I_max = np.max(intensity)

        print(f"\nIntensity range: [{I_min:.3f}, {I_max:.3f}]")
        print(f"Expected (Kirkland): [0.72, 1.03]")

        # Should be close to Kirkland values (within 10% tolerance)
        assert 0.65 < I_min < 0.80  # Min around 0.72
        assert 0.95 < I_max < 1.10  # Max around 1.03

        # Line profile through atoms should show contrast
        center_idx = 512 // 2
        line_intensity = intensity[center_idx, :]

        # Check contrast at atom positions
        x = sim_200kev.x
        for atom_x, _, Z in atoms:
            idx = np.argmin(np.abs(x - atom_x))
            I_atom = line_intensity[idx]

            # Atoms should appear dark (I < 1.0) in phase contrast
            assert I_atom < 1.0

    def test_simulate_image_with_wavefunction(self, sim_200kev):
        """Test simulation with wavefunction return."""
        atoms = [(0, 0, 6)]

        results = sim_200kev.simulate_image(
            atom_positions=atoms, defocus=700.0, Cs=1.3e7, return_wavefunction=True
        )

        # Should include wavefunction
        assert "psi" in results

        # Wavefunction should be complex
        assert results["psi"].dtype == np.complex128

        # Intensity should match |ψ|²
        intensity_from_psi = np.abs(results["psi"]) ** 2
        np.testing.assert_allclose(results["intensity"], intensity_from_psi, rtol=1e-10)

    def test_get_simulation_parameters(self, sim_200kev):
        """Test parameter retrieval."""
        params = sim_200kev.get_simulation_parameters()

        assert "beam_energy" in params
        assert "wavelength" in params
        assert "sigma" in params
        assert "pixel_size" in params
        assert "image_size" in params
        assert "pixels" in params

        assert params["beam_energy"] == 200e3
        assert params["pixels"] == 512
        assert params["image_size"] == 50.0

    def test_different_beam_energies(self):
        """Test that different beam energies give different results."""
        atoms = [(0, 0, 6)]

        # 100 keV
        sim_100 = WPOASimulator(beam_energy=100e3, pixels=256)
        results_100 = sim_100.simulate_image(atoms, defocus=700, Cs=1.3e7)

        # 200 keV
        sim_200 = WPOASimulator(beam_energy=200e3, pixels=256)
        results_200 = sim_200.simulate_image(atoms, defocus=700, Cs=1.3e7)

        # Results should differ
        assert not np.allclose(results_100["intensity"], results_200["intensity"])

        # 100 keV should have longer wavelength, different sigma
        assert sim_100.wavelength > sim_200.wavelength

    def test_numerical_stability(self, sim_200kev):
        """Test numerical stability with various configurations."""
        # Test with many atoms
        atoms = [(i * 2, 0, 6) for i in range(-10, 11)]  # 21 carbon atoms

        results = sim_200kev.simulate_image(
            atom_positions=atoms, defocus=700.0, Cs=1.3e7
        )

        # Should complete without errors
        assert np.all(np.isfinite(results["intensity"]))
        assert np.all(results["intensity"] >= 0)


class TestWPOAValidation:
    """Validation tests against Kirkland reference values."""

    @pytest.fixture
    def sim_kirkland(self):
        """Simulator with exact Kirkland parameters."""
        return WPOASimulator(image_size=50.0, pixels=512, beam_energy=200e3)

    def test_wavelength_matches_kirkland(self, sim_kirkland):
        """
        Validate wavelength calculation against Kirkland.

        Kirkland Eq. 5.2 for 200 keV: λ ≈ 0.02508 Å
        """
        wavelength = sim_kirkland.wavelength
        expected = 0.02508  # From Kirkland

        # Should match within 0.1%
        relative_error = abs(wavelength - expected) / expected
        assert relative_error < 0.001

    def test_transmission_function_phase_range(self, sim_kirkland):
        """Validate phase shifts are in expected range."""
        atoms = [(-20, 0, 6), (-10, 0, 14), (0, 0, 29), (10, 0, 79), (20, 0, 92)]

        transmission, _ = sim_kirkland.calculate_transmission_function(atoms)

        # Extract phases
        phases = np.angle(transmission)

        # Phases should be in reasonable range
        # Based on notebook output: Phase range [0.0000, 2.1821] radians
        # Carbon gives smallest phase (near 0), Uranium largest (≈2.18)
        assert np.min(phases) >= 0.0
        assert np.max(phases) < 2.3  # Based on Kirkland Fig 5.11 and notebook output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
