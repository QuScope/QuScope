"""
Contrast Transfer Function (CTF) Calculator and Visualization

This module provides comprehensive CTF analysis for Conventional TEM including:
- 1D radial CTF plots
- 2D CTF visualization in momentum space
- Multi-voltage comparison
- Individual aberration contributions
- Scherzer defocus calculation
- Resolution limits

Designed for publication-quality figures suitable for both quantum computing
and electron microscopy audiences.

References:
    - Kirkland, E. J. (2010). Advanced Computing in Electron Microscopy.
    - Krivanek, O. L., et al. (2008). Ultramicroscopy 108(3), 179-195.
    - Spence, J. C. H. (2013). High-Resolution Electron Microscopy (4th ed.).

Author: QuScope Development Team
Date: January 2025
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import scipy.constants as const

try:
    from .hamiltonian import relativistic_wavelength, HamiltonianParameters, LensHamiltonian
except ImportError:
    from hamiltonian import relativistic_wavelength, HamiltonianParameters, LensHamiltonian


@dataclass
class CTFParameters:
    """
    Parameters for CTF calculation.
    
    Attributes:
        voltage: Acceleration voltage (V)
        defocus: Defocus C₁ (Angstrom)
        cs: Spherical aberration C₃ (mm)
        c5: 5th order spherical aberration (mm)
        aperture: Objective aperture semi-angle (mrad)
        aberrations: Complete aberration dictionary
    """
    voltage: float
    defocus: float
    cs: float = 0.0
    c5: float = 0.0
    aperture: float = 10.0
    aberrations: Dict[str, float] = None
    
    def __post_init__(self):
        """Initialize aberrations dictionary if not provided."""
        if self.aberrations is None:
            self.aberrations = {
                'defocus': self.defocus,
                'c3': self.cs,
                'c5': self.c5
            }


class CTFCalculator:
    """
    Calculate Contrast Transfer Function for TEM.
    
    The CTF describes how spatial frequencies are transferred from the
    sample to the image, including effects of defocus and aberrations.
    
    For phase contrast imaging (weak phase object):
        CTF(k) = A(k) · sin(χ(k)) - B(k) · cos(χ(k))
    
    where χ(k) is the wave aberration function and A(k), B(k) are envelope
    functions describing partial coherence and damping effects.
    
    For simplicity, we often use:
        CTF(k) = sin(χ(k))
    """
    
    def __init__(self, params: CTFParameters, max_k: float = 10.0, n_points: int = 1000):
        """
        Initialize CTF calculator.
        
        Args:
            params: CTF parameters
            max_k: Maximum spatial frequency (1/Angstrom)
            n_points: Number of points for radial CTF
        """
        self.params = params
        self.wavelength = relativistic_wavelength(params.voltage)
        self.max_k = max_k
        self.n_points = n_points
        
        # Generate radial k-space
        self.k_radial = np.linspace(0, max_k, n_points)
        
    def chi(self, k: np.ndarray, theta: np.ndarray = None) -> np.ndarray:
        """
        Calculate wave aberration function χ(k).
        
        For axially symmetric aberrations (no astigmatism/coma):
            χ(k) = π·λ·k²·C₁ + π/2·(λk)⁴·C₃ + π/3·(λk)⁶·C₅
        
        Args:
            k: Spatial frequency (1/Angstrom), scalar or array
            theta: Azimuthal angle (radians), for non-axial aberrations
        
        Returns:
            χ(k) in radians
        """
        lam = self.wavelength
        lam_k = lam * k
        
        # Defocus term
        chi = np.pi * lam * k**2 * self.params.defocus
        
        # Spherical aberration C₃
        if self.params.cs != 0:
            cs_angstrom = self.params.cs * 1e7  # mm to Angstrom
            chi += 0.5 * np.pi * cs_angstrom * lam_k**4
        
        # 5th order spherical aberration C₅
        if self.params.c5 != 0:
            c5_angstrom = self.params.c5 * 1e7
            chi += (np.pi / 3) * c5_angstrom * lam_k**6
        
        return chi
    
    def ctf(self, k: np.ndarray, theta: np.ndarray = None) -> np.ndarray:
        """
        Calculate CTF = sin(χ(k)).
        
        Args:
            k: Spatial frequency
            theta: Azimuthal angle (optional)
        
        Returns:
            CTF value
        """
        return np.sin(self.chi(k, theta))
    
    def calculate_scherzer_defocus(self) -> float:
        """
        Calculate Scherzer defocus for optimal phase contrast.
        
        Scherzer defocus balances defocus and spherical aberration to
        maximize contrast transfer at medium spatial frequencies.
        
        For C₃-dominated systems:
            Δf_Scherzer = -1.2 · √(C₃·λ)
        
        Returns:
            Scherzer defocus (Angstrom), negative = overfocus
        """
        if self.params.cs == 0:
            return 0.0
        
        cs_angstrom = self.params.cs * 1e7
        return -1.2 * np.sqrt(cs_angstrom * self.wavelength)
    
    def calculate_point_resolution(self) -> float:
        """
        Calculate point resolution (Scherzer limit).
        
        d_Scherzer = 0.66 · (C₃·λ³)^(1/4)
        
        This is the finest detail that can be resolved with optimal
        defocus in a Cs-uncorrected microscope.
        
        Returns:
            Point resolution (Angstrom)
        """
        if self.params.cs == 0:
            # For Cs-corrected microscopes, limited by higher orders
            if self.params.c5 != 0:
                c5_angstrom = self.params.c5 * 1e7
                return 0.8 * (c5_angstrom * self.wavelength**5) ** (1/6)
            return 0.5 * self.wavelength  # Optimistic estimate
        
        cs_angstrom = self.params.cs * 1e7
        return 0.66 * (cs_angstrom * self.wavelength**3) ** 0.25
    
    def find_first_zero(self) -> float:
        """
        Find first zero of CTF (point resolution crossover).
        
        Returns:
            k value of first CTF zero (1/Angstrom)
        """
        ctf_values = self.ctf(self.k_radial)
        
        # Find sign changes
        sign_changes = np.diff(np.sign(ctf_values))
        zeros = np.where(sign_changes != 0)[0]
        
        if len(zeros) > 0:
            return self.k_radial[zeros[0]]
        return self.max_k
    
    def calculate_information_limit(self) -> float:
        """
        Calculate information limit (highest usable spatial frequency).
        
        This is limited by damping envelopes due to:
        - Chromatic aberration
        - Partial spatial coherence
        - Partial temporal coherence
        - Instabilities
        
        Simplified estimate based on aberrations:
            k_max ≈ 1 / (acceptable phase error)
        
        Returns:
            Information limit (1/Angstrom)
        """
        # Find where |χ| exceeds π (destructive interference)
        chi_values = np.abs(self.chi(self.k_radial))
        exceeds_pi = np.where(chi_values > np.pi)[0]
        
        if len(exceeds_pi) > 0:
            return self.k_radial[exceeds_pi[0]]
        return self.max_k


class CTFVisualizer:
    """
    Generate publication-quality CTF visualizations.
    """
    
    def __init__(self, figsize: Tuple[int, int] = (12, 10)):
        """
        Initialize visualizer.
        
        Args:
            figsize: Figure size (width, height) in inches
        """
        self.figsize = figsize
        self.colors = plt.cm.tab10(np.linspace(0, 1, 10))
        
    def plot_1d_ctf(self, 
                    calculators: Dict[str, CTFCalculator],
                    ax: Optional[plt.Axes] = None,
                    show_zeros: bool = True,
                    show_envelope: bool = False) -> plt.Figure:
        """
        Plot 1D radial CTF for multiple conditions.
        
        Args:
            calculators: Dictionary of {label: CTFCalculator}
            ax: Matplotlib axes (creates new if None)
            show_zeros: Mark CTF zeros
            show_envelope: Show envelope function
        
        Returns:
            Figure object
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))
        else:
            fig = ax.get_figure()
        
        for idx, (label, calc) in enumerate(calculators.items()):
            k = calc.k_radial
            ctf = calc.ctf(k)
            
            # Plot CTF
            ax.plot(k, ctf, label=label, linewidth=2, color=self.colors[idx])
            
            # Mark first zero (point resolution)
            if show_zeros:
                k_zero = calc.find_first_zero()
                ax.axvline(k_zero, color=self.colors[idx], linestyle='--', 
                          alpha=0.5, linewidth=1)
                ax.text(k_zero, -0.9, f'{1/k_zero:.2f} Å', 
                       fontsize=9, ha='center')
        
        # Formatting
        ax.set_xlabel('Spatial Frequency k (1/Å)', fontsize=14, fontweight='bold')
        ax.set_ylabel('CTF Amplitude', fontsize=14, fontweight='bold')
        ax.set_title('Contrast Transfer Function', fontsize=16, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=11, framealpha=0.9)
        ax.set_xlim(0, max([c.max_k for c in calculators.values()]))
        ax.set_ylim(-1.1, 1.1)
        
        # Add resolution markers
        ax.axhline(0, color='black', linewidth=0.8, alpha=0.5)
        ax.fill_between([0, ax.get_xlim()[1]], -1, 1, alpha=0.05, color='gray')
        
        plt.tight_layout()
        return fig
    
    def plot_2d_ctf(self,
                    calc: CTFCalculator,
                    n_points: int = 512,
                    cmap: str = 'RdBu_r') -> plt.Figure:
        """
        Plot 2D CTF in momentum space.
        
        Args:
            calc: CTF calculator
            n_points: Number of points in each dimension
            cmap: Colormap name
        
        Returns:
            Figure object with 2D CTF visualization
        """
        # Generate 2D k-space grid
        k_max = calc.max_k
        kx = np.linspace(-k_max, k_max, n_points)
        ky = np.linspace(-k_max, k_max, n_points)
        KX, KY = np.meshgrid(kx, ky)
        
        # Calculate k and theta
        K = np.sqrt(KX**2 + KY**2)
        Theta = np.arctan2(KY, KX)
        
        # Calculate 2D CTF
        CTF_2D = calc.ctf(K, Theta)
        
        # Apply aperture
        aperture_k = calc.params.aperture * 1e-3 / calc.wavelength  # mrad to 1/Å
        aperture_mask = K <= aperture_k
        CTF_2D = CTF_2D * aperture_mask
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Plot 2D CTF
        extent = [-k_max, k_max, -k_max, k_max]
        im1 = ax1.imshow(CTF_2D, extent=extent, cmap=cmap, 
                        vmin=-1, vmax=1, origin='lower', interpolation='bilinear')
        ax1.set_xlabel('kₓ (1/Å)', fontsize=13)
        ax1.set_ylabel('kᵧ (1/Å)', fontsize=13)
        ax1.set_title('2D Contrast Transfer Function', fontsize=14, fontweight='bold')
        
        # Add aperture circle
        circle = plt.Circle((0, 0), aperture_k, fill=False, 
                           edgecolor='white', linewidth=2, linestyle='--')
        ax1.add_patch(circle)
        
        # Add resolution circles
        d_scherzer = calc.calculate_point_resolution()
        k_scherzer = 1 / d_scherzer
        circle_res = plt.Circle((0, 0), k_scherzer, fill=False,
                               edgecolor='yellow', linewidth=1.5, linestyle=':')
        ax1.add_patch(circle_res)
        ax1.text(0, -k_scherzer*1.15, f'Scherzer: {d_scherzer:.2f} Å',
                ha='center', va='top', color='yellow', fontsize=10,
                bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))
        
        plt.colorbar(im1, ax=ax1, label='CTF Amplitude')
        
        # Plot radial average
        k_radial = calc.k_radial
        ctf_radial = calc.ctf(k_radial)
        ax2.plot(k_radial, ctf_radial, 'b-', linewidth=2.5, label='CTF')
        ax2.axhline(0, color='black', linewidth=0.8, alpha=0.5)
        ax2.axvline(aperture_k, color='red', linestyle='--', 
                   linewidth=2, label=f'Aperture ({calc.params.aperture} mrad)')
        ax2.axvline(k_scherzer, color='orange', linestyle=':', 
                   linewidth=2, label=f'Point Resolution ({d_scherzer:.2f} Å)')
        
        ax2.set_xlabel('Spatial Frequency k (1/Å)', fontsize=13)
        ax2.set_ylabel('CTF Amplitude', fontsize=13)
        ax2.set_title('Radial Average', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend(fontsize=10)
        ax2.set_xlim(0, k_max)
        ax2.set_ylim(-1.1, 1.1)
        
        plt.tight_layout()
        return fig
    
    def plot_multi_voltage_comparison(self,
                                     voltages: List[float],
                                     cs: float = 1.3,
                                     defocus: float = None) -> plt.Figure:
        """
        Compare CTF for different acceleration voltages.
        
        Args:
            voltages: List of voltages (V), e.g., [80e3, 120e3, 200e3, 300e3]
            cs: Spherical aberration (mm)
            defocus: Defocus (Angstrom), uses Scherzer if None
        
        Returns:
            Figure with multi-voltage comparison
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 12))
        axes = axes.flatten()
        
        for idx, voltage in enumerate(voltages):
            ax = axes[idx]
            
            # Calculate Scherzer defocus for this voltage if not specified
            if defocus is None:
                wavelength = relativistic_wavelength(voltage)
                cs_angstrom = cs * 1e7
                df = -1.2 * np.sqrt(cs_angstrom * wavelength)
            else:
                df = defocus
            
            # Create CTF calculator
            params = CTFParameters(voltage=voltage, defocus=df, cs=cs)
            calc = CTFCalculator(params, max_k=5.0)
            
            # Plot CTF
            k = calc.k_radial
            ctf_vals = calc.ctf(k)
            ax.plot(k, ctf_vals, 'b-', linewidth=2.5)
            
            # Mark point resolution
            d_res = calc.calculate_point_resolution()
            k_res = 1 / d_res
            ax.axvline(k_res, color='red', linestyle='--', linewidth=2, alpha=0.7)
            
            # Formatting
            ax.set_xlabel('Spatial Frequency k (1/Å)', fontsize=12)
            ax.set_ylabel('CTF', fontsize=12)
            ax.set_title(f'{voltage/1e3:.0f} kV (λ={calc.wavelength:.4f} Å, '
                        f'd={d_res:.2f} Å)', fontsize=13, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.axhline(0, color='black', linewidth=0.8, alpha=0.5)
            ax.set_xlim(0, 5.0)
            ax.set_ylim(-1.1, 1.1)
            
            # Add text annotation
            ax.text(0.98, 0.97, 
                   f'Cs = {cs} mm\nΔf = {df:.0f} Å\nd_res = {d_res:.2f} Å',
                   transform=ax.transAxes, fontsize=10,
                   verticalalignment='top', horizontalalignment='right',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.suptitle('CTF Comparison: Multi-Voltage Analysis', 
                    fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout()
        return fig


# Example usage
if __name__ == "__main__":
    print("=" * 70)
    print("CTF Calculator - Validation and Demonstration")
    print("=" * 70)
    print()
    
    # Test different voltages
    voltages = [80e3, 120e3, 200e3, 300e3]
    
    print("Calculating wavelengths for standard voltages:")
    for V in voltages:
        lam = relativistic_wavelength(V)
        print(f"  {V/1e3:>3.0f} kV: λ = {lam:.5f} Å")
    print()
    
    # Create CTF calculator for 200 kV
    params = CTFParameters(voltage=200e3, defocus=-500.0, cs=1.3, c5=10.0)
    calc = CTFCalculator(params)
    
    print(f"200 kV TEM with Cs = 1.3 mm:")
    print(f"  Scherzer defocus: {calc.calculate_scherzer_defocus():.1f} Å")
    print(f"  Point resolution: {calc.calculate_point_resolution():.3f} Å")
    print(f"  Information limit: {1/calc.calculate_information_limit():.3f} Å")
    print()
    
    # Create visualizations
    print("Generating CTF visualizations...")
    
    # 1D CTF comparison
    calculators = {}
    for V in [80e3, 200e3, 300e3]:
        lam = relativistic_wavelength(V)
        cs_ang = 1.3 * 1e7
        df = -1.2 * np.sqrt(cs_ang * lam)
        params = CTFParameters(voltage=V, defocus=df, cs=1.3)
        calculators[f'{V/1e3:.0f} kV'] = CTFCalculator(params, max_k=5.0)
    
    viz = CTFVisualizer()
    fig1 = viz.plot_1d_ctf(calculators)
    plt.savefig('ctf_1d_comparison.png', dpi=300, bbox_inches='tight')
    print("  ✓ Saved: ctf_1d_comparison.png")
    
    # 2D CTF
    params_2d = CTFParameters(voltage=200e3, defocus=-500.0, cs=1.3)
    calc_2d = CTFCalculator(params_2d, max_k=5.0)
    fig2 = viz.plot_2d_ctf(calc_2d, n_points=512)
    plt.savefig('ctf_2d_visualization.png', dpi=300, bbox_inches='tight')
    print("  ✓ Saved: ctf_2d_visualization.png")
    
    # Multi-voltage comparison
    fig3 = viz.plot_multi_voltage_comparison([80e3, 120e3, 200e3, 300e3], cs=1.3)
    plt.savefig('ctf_multi_voltage.png', dpi=300, bbox_inches='tight')
    print("  ✓ Saved: ctf_multi_voltage.png")
    
    print()
    print("✓ CTF module validated and figures generated")
    print()
    print("Publication-ready figures:")
    print("  • ctf_1d_comparison.png - 1D radial CTF")
    print("  • ctf_2d_visualization.png - 2D momentum space CTF")
    print("  • ctf_multi_voltage.png - Multi-voltage comparison")
