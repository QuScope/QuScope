"""
Quantum-Enhanced Weak Phase Object Simulations
======================================

This module implements a hybrid quantum-classical framework for simulating
CTEM and STEM images of thin specimen based on weak phase object approximation. 
This leverages QFTs and inverse QFTs, replacing various FFTs and iFFTs to reduce
computational overhead.
"""

import numpy as np
import matplotlib.pyplot as plt
from quscope.simulations.quantum_utils import TEMQFT
from quscope.utils.constants import PhysicalConstants
from quscope.utils.kirkland import KirklandPotential

class ThinCTEM:
    """
    Quantum CTEM simulation for thin specimens using weak phase object approximation.
    
    This class implements:
    - Weak phase object approximation for thin specimens
    - QFT replacing classical FFT
    - Support for abritrary atomic structures
    - For CTEM at the moment
    """
    
    def __init__(self, image_size=50.0, n_qubits=8, beam_energy=200e3, kirkland_params_file='kirkland.json'):
        """
        Initialize thin specimen simulator.
        
        Parameters:
        -----------
        image_size : float
            Lateral size of the image in Angstroms.
        n_qubits : int
            Number of qubits per dimension (n_qubits=8 gives 256x256 pixels)
        beam_energy : float
            Electron beam energy in eV.
        """
        
        self.image_size = image_size
        self.n_qubits = n_qubits
        self.pixels = 2**n_qubits
        self.beam_energy = beam_energy
        
        # Calculate beam parameters
        self.wavelength = PhysicalConstants.calculate_wavelength(beam_energy)
        self.sigma = PhysicalConstants.calculate_sigma(beam_energy)
        
        # Load Kirkland parameters
        self.params = KirklandPotential(kirkland_params_file)
        
        # Set up QFTs
        self.qfts = TEMQFT(n_qubits)
        
        # Create coordinate grids (real space)
        self.dx = self.image_size / self.pixels
        x = (np.arange(self.pixels) - self.pixels/2 + 0.5) * self.dx
        self.x = x
        self.y = x
        self.X, self.Y = np.meshgrid(x, x, indexing='xy')
    
    def calculate_transmission_function(self, atom_positions, atom_z_values):
        """
        Calculate transmission function for weak phase object.
        
        Parameters:
        -----------
        atom_positions : list
            List of (x,y) positions in Angstroms.
        atom_z_values : list
            List of atomic numbers corresponding to positions
        
        Returns:
        --------
        transmission : np.ndarray
            Complex transmission function.
        """
        # Get projected potential
        V_total = np.zeros((self.pixels, self.pixels))
        
        print("\nAtomic potential peaks:")
        for (x_atom, y_atom), Z in zip(atom_positions, atom_z_values):
            V_atom = self.params.kirkland_potential_2d(
                self.X, self.Y, x_atom, y_atom, Z
            )
            V_total += V_atom
            
            idx_x = np.argmin(np.abs(self.x - x_atom))
            idx_y = np.argmin(np.abs(self.y - y_atom))
            V_peak = V_atom[idx_y, idx_x]
            element = self.params.get_element_symbol(Z)
            print(f"{element} (Z={Z}): V_peak = {V_peak:.2f} eV")
        
        phase = self.sigma * V_total
        print(f"\nPhase range: [{np.min(phase):.4f}, {np.max(phase):.4f}] radians")
        
        transmission = np.exp(1j * phase)
        
        return transmission, V_total
    
    def objective_lens_transfer_function(self, kx, ky, defocus, Cs, alpha_max=None):
        """
        Apply objective lens transfer function in reciprocal space.
        
        Parameters:
        -----------
        kx, ky : float
            Spatial components in the x and y directions in space.
        defocus : float
            Defocus in Angstroms.
        Cs : float
            Spherical aberration coefficient in Angstroms.
        alpha_max : float, optional
            Objective aperture semi-angle in mrad.
            
        Returns:
        --------
        H : np.ndarray
            Transfer function.
        """
        k2 = kx**2 + ky**2
        k = np.sqrt(k2)
        
        chi = np.pi * self.wavelength * k2 * (0.5 * Cs * self.wavelength**2 * k2 - defocus)
        
        H = np.exp(-1j * chi)
        
        if alpha_max is not None:
            k_max = alpha_max / self.wavelength
            aperture = k <= k_max
            H *= aperture
        
        return H
    
    def simulate_image(self, atom_positions, atom_z_values, defocus=700, Cs=1.3e7, alpha_max=None):
        """
        Simulate CTEM image using quantum algorithms.
        
        Parameters:
        -----------
        atom_positions : list
            List of (x,y) positions in Angstroms.
        atom_z_values : list
            List of atomic numbers.
        defocus : float
            Defocus in Angstroms.
        Cs : float
            Spherical aberration in Angstroms.
        alpha_max : float, optional
            Objective aperture in mrad.
        
        Returns:
        --------
        results : Dict
            Dictionary containing:
            - 'intensity': Final image intensity.
            - 'transmission': Complex transmission function.
            - 'psi': Exit wave function.
            - 'potential': Projected potential.
        """
        if alpha_max is not None:
            alpha_max = alpha_max * 1e-3  # mrad to rad
            
        # Get transmission function
        transmission, potential = self.calculate_transmission_function(atom_positions, atom_z_values)
        
        print("\nApplying QFT...")
        # QFT
        psi_k = self.qfts.qft_2d(transmission)
        psi_k = np.fft.fftshift(psi_k)  # Classical postprocessing
        
        # Get frequency coordinates
        kx = np.fft.fftshift(np.fft.fftfreq(self.pixels, d=self.dx))
        ky = np.fft.fftshift(np.fft.fftfreq(self.pixels, d=self.dx))
        KX, KY = np.meshgrid(kx, ky, indexing='xy')
        
        # Apply objective lens transfer function
        H = self.objective_lens_transfer_function(KX, KY, defocus, Cs, alpha_max)
        psi_k *= H
        
        print("Apply Inverse QFT...")
        # iQFT
        psi_k_shifted = np.fft.ifftshift(psi_k)
        psi = self.qfts.iqft_2d(psi_k_shifted)
        
        # Calculate intensity
        intensity = np.abs(psi)**2
        
        return {
            'transmission': transmission,
            'intensity': intensity,
            'potential': potential,
            'psi': psi,
            'atom_positions': atom_positions,
            'atom_z_values': atom_z_values
        }
        
    def plot_transmission_function(self, atom_positions, atom_z_values):
        """Plot transmission function line scan (reproduces Figure 5.11)"""
        transmission, _ = self.calculate_transmission_function(atom_positions, atom_z_values)
        
        center_idx = self.pixels // 2
        line_real = np.real(transmission[center_idx, :])
        line_imag = np.imag(transmission[center_idx, :])
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 10))
        
        # Real part
        ax1.plot(self.x, line_real, 'b-', linewidth=1.5, label='Quantum')
        ax1.set_xlim(-25, 25)
        ax1.set_ylim(0, 1.2)
        ax1.set_ylabel('Real Part')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        elements = [self.params.get_element_symbol(Z) for Z in atom_z_values]
        for (x, y), elem in zip(atom_positions, elements):
            ax1.text(x, 1.15, elem, ha='center', va='bottom', fontsize=10)
            ax1.axvline(x, color='gray', linestyle=':', alpha=0.5)
        
        ax1.set_title('Line scan of the complex transmission function\n' + 
                      f'for {len(atom_positions)} atoms ({self.beam_energy/1e3:.0f} keV)', fontsize=12)
        
        # Imaginary part
        ax2.plot(self.x, line_imag, 'b-', linewidth=1.5, label='Quantum')
        ax2.set_xlim(-25, 25)
        ax2.set_ylim(0, 1.0)
        ax2.set_xlabel('position x (in Ang)')
        ax2.set_ylabel('Imag Part')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        for (x, y), elem in zip(atom_positions, elements):
            ax2.axvline(x, color='gray', linestyle=':', alpha=0.5)
        
        plt.tight_layout()
        plt.show()
        
        return fig
    
    def plot_phase_contrast_image(self, results, title_suffix=""):
        """Plot phase contrast image and line scan (reproduces Figure 5.12)"""
        intensity = results['intensity']
        atom_positions = results['atom_positions']
        atom_z_values = results['atom_z_values']
        elements = [self.params.get_element_symbol(Z) for Z in atom_z_values]
        
        # 2D image
        fig, ax = plt.subplots(1, 1, figsize=(8, 8))
        extent = [-self.image_size/2, self.image_size/2,
                  -self.image_size/2, self.image_size/2]
        
        print(f"\nIntensity range: [{np.min(intensity):.3f}, {np.max(intensity):.3f}]")
        
        im = ax.imshow(intensity, extent=extent, cmap='gray', origin='lower',
                       interpolation='bilinear', vmin=0.7, vmax=1.1)
        
        for (x, y) in atom_positions:
            circle = plt.Circle((x, y), 2.0, fill=False, edgecolor='red', linewidth=1.5)
            ax.add_patch(circle)
        
        ax.set_xlabel('x (Å)')
        ax.set_ylabel('y (Å)')
        ax.set_title(f'Coherent bright field phase contrast image{title_suffix}', fontsize=12)
        ax.set_xlim(-25, 25)
        ax.set_ylim(-25, 25)
        
        plt.colorbar(im, ax=ax, label='Intensity')
        plt.tight_layout()
        plt.show()
        
        # Line scan through atoms
        fig2, ax2 = plt.subplots(1, 1, figsize=(8, 5))
        center_idx = self.pixels // 2
        line_intensity = intensity[center_idx, :]
        
        ax2.plot(self.x, line_intensity, 'b-', linewidth=1.5, label='Quantum')
        ax2.set_xlabel('position x (in Ang)')
        ax2.set_ylabel('Image Intensity')
        ax2.set_title('Line scan through the center of the atoms', fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim(-25, 25)
        ax2.set_ylim(0.5, 1.1)
        ax2.legend()
        
        for (x_pos, y_pos), elem in zip(atom_positions, elements):
            ax2.axvline(x_pos, color='gray', linestyle=':', alpha=0.5)
            ax2.text(x_pos, 1.08, elem, ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        plt.show()
        
        return fig, fig2

# Kirkland example structure
def create_five_atoms_example():
    """Create the classic 5-atom example from Kirkland Figure 5.11"""
    elements = ['C', 'Si', 'Cu', 'Au', 'U']
    z_values = [6, 14, 29, 79, 92]
    positions = []
    for i in range(5):
        x_pos = (i - 2) * 10.0
        positions.append([x_pos, 0.0])
    return positions, z_values, elements