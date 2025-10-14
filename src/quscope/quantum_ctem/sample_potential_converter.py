"""
Sample Potential Converter: ASE Atoms to Quantum TEM Potential

Converts atomic structures (ASE Atoms) to 2D projected potentials V(x,y)
for quantum TEM simulation using the Weak Phase Object Approximation.

References:
- Kirkland, E. J. (2010). Advanced Computing in Electron Microscopy. 
  Springer. Chapter 6: Simulation of Projected Potentials.
- Weickenmeier, A., & Kohl, H. (1991). Computation of absorptive form 
  factors for high-energy electron diffraction. Acta Cryst. A47, 590-597.

Author: QuScope Team
Date: October 2025
"""

import numpy as np
from typing import Tuple, Optional, Dict
from dataclasses import dataclass

try:
    from ase import Atoms
except ImportError:
    raise ImportError("ASE is required. Install with: conda install -c conda-forge ase")


@dataclass
class AtomicScatteringParameters:
    """Kirkland parametrization for atomic scattering factors.
    
    The atomic potential is represented as:
    V(r) = Σᵢ aᵢ·exp(-πr²/bᵢ) / r
    
    Parameters from:
    Kirkland, E. J. (2010). Advanced Computing in Electron Microscopy.
    Appendix C: Atomic Scattering Factors.
    """
    
    # Element symbol
    symbol: str
    
    # Atomic number
    Z: int
    
    # Kirkland parameters
    # a coefficients (Å)
    a: np.ndarray
    
    # b coefficients (Å²)
    b: np.ndarray
    
    # c, d parameters for higher accuracy (optional)
    c: Optional[np.ndarray] = None
    d: Optional[np.ndarray] = None


# Kirkland parameters for common elements
KIRKLAND_PARAMS = {
    'C': AtomicScatteringParameters(
        symbol='C',
        Z=6,
        a=np.array([0.2149, 1.0181, 3.5026]),
        b=np.array([0.2615, 1.0186, 4.3415])
    ),
    'Si': AtomicScatteringParameters(
        symbol='Si',
        Z=14,
        a=np.array([0.3247, 1.1931, 4.2288]),
        b=np.array([0.3187, 0.9636, 3.4739])
    ),
    'Mo': AtomicScatteringParameters(
        symbol='Mo',
        Z=42,
        a=np.array([1.9842, 6.9768, 14.7635]),
        b=np.array([0.4836, 1.5905, 9.7448])
    ),
    'S': AtomicScatteringParameters(
        symbol='S',
        Z=16,
        a=np.array([0.3831, 1.3533, 4.5397]),
        b=np.array([0.3216, 0.9622, 3.3763])
    ),
    'Au': AtomicScatteringParameters(
        symbol='Au',
        Z=79,
        a=np.array([4.0791, 14.3491, 27.9881]),
        b=np.array([0.5203, 1.6627, 9.9729])
    ),
}


class SamplePotentialConverter:
    """Convert ASE Atoms to 2D projected potential for quantum TEM."""
    
    def __init__(
        self,
        acceleration_voltage: float = 80e3,
        use_scattering_params: bool = True
    ):
        """Initialize converter.
        
        Args:
            acceleration_voltage: Acceleration voltage in Volts
            use_scattering_params: Use Kirkland scattering factors (True)
                                   or simple Gaussian approximation (False)
        """
        self.voltage = acceleration_voltage
        self.use_scattering_params = use_scattering_params
        self.wavelength = self._calculate_wavelength()
        
    def _calculate_wavelength(self) -> float:
        """Calculate relativistic electron wavelength.
        
        Returns:
            Wavelength in Angstroms
        """
        from scipy.constants import h, m_e, e, c
        
        V = self.voltage
        # Relativistic correction
        wavelength = h / np.sqrt(2 * m_e * e * V * (1 + e * V / (2 * m_e * c**2)))
        
        return wavelength * 1e10  # Convert m to Angstroms

    def get_interaction_constant(self) -> float:
        """Return interaction constant σ in units of rad / (V·Å).

        Uses the same formula as HamiltonianParameters for consistency:
        σ = (m_e * e * λ) / (2π ℏ²) converted to per Angstrom (×1e-10)
        """
        from scipy.constants import electron_mass as m_e, elementary_charge as e, Planck as h
        hbar = h / (2 * np.pi)
        lambda_m = self.wavelength * 1e-10  # Å -> m

        sigma = (m_e * e * lambda_m) / (2 * np.pi * hbar**2)
        # convert from 1/(V·m) to 1/(V·Å)
        sigma *= 1e-10
        return sigma
    
    def atoms_to_potential(
        self,
        atoms: Atoms,
        grid_size: int,
        pixel_size: float,
        projection_method: str = 'wpoa',
        tile_to_fill: bool = True
    ) -> np.ndarray:
        """Convert ASE Atoms to 2D projected potential.
        
        Args:
            atoms: ASE Atoms object
            grid_size: Number of pixels (N for N×N grid)
            pixel_size: Pixel size in Angstroms
            projection_method: 'wpoa' (weak phase object) or 'full'
            tile_to_fill: If True, tile the structure to fill the grid (like abTEM)
            
        Returns:
            2D array of projected potential V(x,y) in Volts
        """
        # Create real-space grid
        extent = grid_size * pixel_size
        x = np.linspace(-extent/2, extent/2, grid_size)
        y = np.linspace(-extent/2, extent/2, grid_size)
        X, Y = np.meshgrid(x, y)
        
        # Tile atoms to fill grid if requested (matching abTEM behavior)
        if tile_to_fill:
            cell = atoms.get_cell()
            # Use the actual lattice vector lengths in the xy-plane. Some
            # builders (e.g. ase.build.mx2) produce non-axis-aligned cells
            # where the diagonal cell entries are not sufficient. Using the
            # vector norms projected into xy avoids under-estimating the
            # number of tiles and the resulting empty corner regions.
            a_vec = cell[0]
            b_vec = cell[1]
            cell_x = float(np.linalg.norm(a_vec[:2]))
            cell_y = float(np.linalg.norm(b_vec[:2]))

            # Calculate how many tiles needed (add a small safety margin)
            nx = int(np.ceil(extent / cell_x)) + 2
            ny = int(np.ceil(extent / cell_y)) + 2
            
            # Tile the structure
            atoms_tiled = atoms.copy()
            atoms_tiled = atoms_tiled.repeat((nx, ny, 1))
            
            # Center the tiled structure
            atoms_tiled.center()
            
            atoms_to_use = atoms_tiled
        else:
            atoms_to_use = atoms
        
        # Initialize potential
        V = np.zeros((grid_size, grid_size))
        
        # Project each atom onto grid
        for atom in atoms_to_use:
            x0, y0, z0 = atom.position
            
            # Get scattering parameters for this element
            symbol = atom.symbol
            if symbol not in KIRKLAND_PARAMS:
                print(f"Warning: No Kirkland parameters for {symbol}, using Carbon as fallback")
                symbol = 'C'
            
            params = KIRKLAND_PARAMS[symbol]
            
            # Distance from atom to each grid point (in xy plane)
            r = np.sqrt((X - x0)**2 + (Y - y0)**2)
            
            if self.use_scattering_params:
                # Use Kirkland parametrization
                atom_potential = self._kirkland_potential(r, params)
            else:
                # Simple Gaussian approximation
                sigma = 1.0  # Angstroms (width parameter)
                atom_potential = params.Z * np.exp(-r**2 / (2 * sigma**2))
            
            V += atom_potential
        
    # The Kirkland parametrization gives dimensionless values that represent
    # the shape of the atomic potential. We need to scale these to physical
    # units of Volt-Angstroms for the projected potential.
    #
    # The Kirkland formula Σᵢ aᵢ·exp(-π·r²/bᵢ) is in Ångstroms but needs
    # proper physical units. Empirical calibration against abTEM is used
    # to set per-element scaling factors for representative materials.
        #
        # Universal scaling approach: Scale ≈ Z^1.3 / 10
        # This accounts for atomic number dependence of scattering strength
        
        # Per-element empirical scaling factors (calibrated vs abTEM)
        ELEMENT_SCALE = {
            'C': 5.4,
            'S': 20.0,
            'Mo': 90.0,
            'Si': 8.0,
            'Au': 300.0
        }

        # Recompute V with per-atom scaling applied (better fidelity across materials)
        V_scaled = np.zeros_like(V)
        idx = 0
        for atom in atoms_to_use:
            symbol = atom.symbol if atom.symbol in KIRKLAND_PARAMS else 'C'
            # extract same potential contribution as before
            x0, y0, z0 = atom.position
            r = np.sqrt((X - x0)**2 + (Y - y0)**2)
            if self.use_scattering_params:
                atom_potential = self._kirkland_potential(r, KIRKLAND_PARAMS[symbol])
            else:
                sigma_g = 1.0
                atom_potential = KIRKLAND_PARAMS[symbol].Z * np.exp(-r**2 / (2 * sigma_g**2))

            # Apply element-specific empirical scale (fallback to Z^1.3/10)
            scale = ELEMENT_SCALE.get(symbol, (KIRKLAND_PARAMS[symbol].Z ** 1.3) / 10.0)
            V_scaled += atom_potential * scale
            idx += 1

        return V_scaled
    
    def _kirkland_potential(
        self,
        r: np.ndarray,
        params: AtomicScatteringParameters
    ) -> np.ndarray:
        """Calculate atomic potential using Kirkland parametrization.
        
        The projected potential (integrated along z) is:
        V_proj(r) = 2π Σᵢ aᵢ·bᵢ·K₀(2π·r/√bᵢ)
        
        Where K₀ is the modified Bessel function of the second kind.
        
        For computational efficiency, we use the Gaussian approximation:
        V_proj(r) ≈ Σᵢ aᵢ·exp(-π·r²/bᵢ)
        
        Args:
            r: Distance array in Angstroms
            params: Atomic scattering parameters
            
        Returns:
            Projected potential array
        """
        V = np.zeros_like(r)
        
        # Sum over parametrized terms
        for ai, bi in zip(params.a, params.b):
            # Gaussian approximation to projected potential
            V += ai * np.exp(-np.pi * r**2 / bi)
        
        return V
    
    def visualize_potential(
        self,
        atoms: Atoms,
        grid_size: int = 256,
        pixel_size: float = 0.1,
        save_path: Optional[str] = None
    ) -> None:
        """Visualize the projected potential.
        
        Args:
            atoms: ASE Atoms object
            grid_size: Grid size
            pixel_size: Pixel size in Angstroms
            save_path: Optional path to save figure
        """
        import matplotlib.pyplot as plt
        
        # Calculate potential
        V = self.atoms_to_potential(atoms, grid_size, pixel_size)
        
        # Create figure
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        
        # Potential map
        extent = grid_size * pixel_size
        im1 = axes[0].imshow(
            V,
            extent=[-extent/2, extent/2, -extent/2, extent/2],
            cmap='viridis'
        )
        axes[0].set_title('Projected Potential V(x,y)', fontweight='bold')
        axes[0].set_xlabel('x (Å)')
        axes[0].set_ylabel('y (Å)')
        plt.colorbar(im1, ax=axes[0], label='Potential (V)')
        
        # Line profile
        center = grid_size // 2
        profile = V[center, :]
        x_profile = np.linspace(-extent/2, extent/2, grid_size)
        axes[1].plot(x_profile, profile, 'b-', linewidth=2)
        axes[1].set_xlabel('x (Å)')
        axes[1].set_ylabel('Potential (V)')
        axes[1].set_title('Central Line Profile', fontweight='bold')
        axes[1].grid(True, alpha=0.3)
        
        # Phase shift (σV)
        # Use consistent interaction constant (rad / (V·Å))
        sigma = self.get_interaction_constant()
        phase = sigma * V
        
        im2 = axes[2].imshow(
            phase,
            extent=[-extent/2, extent/2, -extent/2, extent/2],
            cmap='twilight'
        )
        axes[2].set_title('Phase Shift σV (rad)', fontweight='bold')
        axes[2].set_xlabel('x (Å)')
        axes[2].set_ylabel('y (Å)')
        plt.colorbar(im2, ax=axes[2], label='Phase (rad)')
        
        plt.suptitle(
            f'Sample Potential: {len(atoms)} atoms at {self.voltage/1e3:.0f} kV',
            fontsize=14,
            fontweight='bold'
        )
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved potential visualization: {save_path}")
        
        plt.show()
    
    def calculate_sample_statistics(
        self,
        atoms: Atoms,
        grid_size: int = 256,
        pixel_size: float = 0.1
    ) -> Dict[str, float]:
        """Calculate statistics of the sample potential.
        
        Args:
            atoms: ASE Atoms object
            grid_size: Grid size
            pixel_size: Pixel size in Angstroms
            
        Returns:
            Dictionary with potential statistics
        """
        V = self.atoms_to_potential(atoms, grid_size, pixel_size)

        sigma = self.get_interaction_constant()
        phase = sigma * V
        
        stats = {
            'potential_min': float(V.min()),
            'potential_max': float(V.max()),
            'potential_mean': float(V.mean()),
            'potential_std': float(V.std()),
            'phase_shift_max': float(np.abs(phase).max()),
            'phase_shift_mean': float(np.abs(phase).mean()),
            'wpoa_valid': float(np.abs(phase).max()) < 0.5,  # WPOA valid if phase < π/2
        }
        
        return stats


def test_potential_converter():
    """Light smoke-test for the potential converter using a small MoS2 cell.

    This replaces the previous graphene-focused example to align with the
    repository's MoS2-centered workflow.
    """
    try:
        from quscope.quantum_ctem.mos2_workflow.viz import build_mos2
    except Exception:
        # Fallback: construct a minimal MoS2 cell manually using ASE
        from ase import Atoms
        # Minimal MoS2-like triatomic cell (not physically accurate; smoke-test only)
        atoms = Atoms(['Mo', 'S', 'S'], positions=[(0,0,0), (1.6,0,0), (-1.6,0,0)])
    else:
        atoms = build_mos2(nx=1, ny=1, vacuum=5.0)

    atoms.center()

    print("Testing Sample Potential Converter (MoS2 smoke-test)")
    print("=" * 60)

    print("\n[1/3] Initializing potential converter...")
    converter = SamplePotentialConverter(acceleration_voltage=200e3)
    print("✓ Converter initialized")

    print("\n[2/3] Converting atoms to potential...")
    V = converter.atoms_to_potential(atoms, grid_size=128, pixel_size=0.1)
    print(f"✓ Potential calculated — shape: {V.shape}")

    print("\n[3/3] Calculating sample statistics...")
    stats = converter.calculate_sample_statistics(atoms, grid_size=128, pixel_size=0.1)
    for key, value in stats.items():
        if isinstance(value, bool):
            print(f"  {key}: {value}")
        else:
            print(f"  {key}: {value:.6e}")

    print("\nSmoke-test complete — potential visualization disabled in smoke-test")
    print("Next steps: integrate with quscope.quantum_ctem and run the MoS2 workflow")


if __name__ == '__main__':
    """Run test suite."""
    test_potential_converter()
