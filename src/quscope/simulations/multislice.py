"""
Multislice method for thick specimen CTEM simulations.
Uses quantum algorithms (QFT/iQFT) for wave propagation between slices.
"""

import numpy as np
import matplotlib.pyplot as plt
from quscope.simulations.quantum_utils import TEMQFT
from quscope.utils.kirkland import KirklandPotential
from quscope.utils.constants import PhysicalConstants

class ThickCTEM:
    """
    Quantum multislice CTEM simulation for thick specimens.
    
    This class implements:
    - Multislice algorithm for thick specimens
    - QFT for propagation between slices
    - Support for arbitrary crystal structures
    - Dynamical scattering effects
    """
    
    def __init__(self, image_size=50.0, n_qubits=8, beam_energy=200e3, kirkland_params_file='kirkland.json'):
        """
        Initialize thick specimen simulator.
        
        Parameters:
        -----------
        image_size : float
            Lateral size of the image in Angstroms.
        n_qubits : int
            Number of qubits per dimension.
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
        
        # Setup real and reciprocal space coordinate grids
        # Real space
        self.dx = self.image_size / self.pixels
        x = (np.arange(self.pixels) - self.pixels/2 + 0.5) * self.dx
        self.x = x
        self.y = x
        self.X, self.Y = np.meshgrid(x, x, indexing='xy')
        
        # Reciprocal space
        kx = np.fft.fftfreq(self.pixels, d=self.dx)
        self.kx = np.fft.fftshift(kx)
        self.KX, self.KY = np.meshgrid(self.kx, self.kx, indexing='xy')
        self.k_squared = self.KX**2 + self.KY**2
        
    def get_atoms_in_slice(self, atoms_3d, z_start, z_end):
        """Get atoms within a z-range, with periodic boundary conditions"""
        atoms_in_slice = []
        for atom in atoms_3d:
            x, y, z = atom['position']
            # Check if atom is in this slice
            if z_start <= z <= z_end:
                # Apply periodic boundary conditions for x, y
                x_wrapped = x % self.image_size
                y_wrapped = y % self.image_size
                
                # Center in image
                x_centered = x_wrapped - self.image_size/2
                y_centered = y_wrapped - self.image_size/2
                
                atoms_in_slice.append({
                    'position': [x_centered, y_centered, z],
                    'Z': atom['Z'],
                    'element': atom['element']
                })
        return atoms_in_slice
    
    def calculate_slice_transmission(self, atoms_in_slice, slice_thickness):
        """Calculate transmission function for a slice"""
        V_slice = np.zeros((self.pixels, self.pixels))
        
        for atom in atoms_in_slice:
            x, y, z = atom['position']
            Z = atom['Z']
            
            # Add potential from this atom
            V_atom = self.params.kirkland_potential_2d(self.X, self.Y, x, y, Z)
            V_slice += V_atom
            
            # Also add periodic images if atom is near boundary
            # This ensures continuity at edges
            if abs(x) > self.image_size/2 - 5:  # Near x boundary
                x_periodic = x - np.sign(x) * self.image_size
                V_atom = self.params.kirkland_potential_2d(self.X, self.Y, x_periodic, y, Z)
                V_slice += V_atom
                
            if abs(y) > self.image_size/2 - 5:  # Near y boundary
                y_periodic = y - np.sign(y) * self.image_size
                V_atom = self.params.kirkland_potential_2d(self.X, self.Y, x, y_periodic, Z)
                V_slice += V_atom
        
        # Transmission function with correct normalization
        # Phase should be proportional to projected potential and slice thickness
        phase = self.sigma * V_slice * slice_thickness
        transmission = np.exp(1j * phase)
        
        return transmission
        
    def calculate_propagator(self, slice_thickness):
        """
        Calculate Fresnel propagator.
        
        Parameters:
        -----------
        slice_thickness : float
            Thickness of each slice in Angstroms.
            
        Returns:
        --------
        propagator : np.ndarray
            Fresnel propagator.
        """
        phase = -np.pi * self.wavelength * self.k_squared * slice_thickness
        propagator = np.exp(1j * phase)
        return propagator
    
    def simulate_multislice(self, atoms_3d, total_thickness, slice_thickness=2.0, defocus=0):
        """
        Simulate multislice propagation through a specimen.
        
        Parameters:
        -----------
        atoms_3d : list
            List of atom dictionaries with 'position' [x,y,z] and 'Z' keys.
        total_thickness : float
            Total specimen thickness in Angstroms.
        slice_thickness : float
            Thickness of each slice in Angstroms.
        defocus : float
            Objective lens defocus in Angstroms.            
        
        Returns:
        --------
        Dictionary with simulation results.
        """
        print(f"\nMultislice simulation: {total_thickness:.1f} Å thick specimen")
        
        # Calculate number of slices
        n_slices = max(1, int(total_thickness / slice_thickness))
        actual_slice_thickness = total_thickness / n_slices
        
        print(f"Using {n_slices} slices of {actual_slice_thickness:.2f} Å each")
        
        # Initialize incident wave
        psi = np.ones((self.pixels, self.pixels), dtype=complex)
        
        # Propagator for this slice thickness
        propagator = self.calculate_propagator(actual_slice_thickness)
        
        # Store intermediate results
        intermediate_waves = []
        
        # Propagate through slices
        for i in range(n_slices):
            z_start = i * actual_slice_thickness
            z_end = (i+1) * actual_slice_thickness
            
            print(f"  Slice {i+1}/{n_slices}: z = {z_start:.1f} - {z_end:.1f} Å")
            
            # Get atoms in slice
            atoms_in_slice = self.get_atoms_in_slice(atoms_3d, z_start, z_end)
            
            # Transmission function
            transmission = self.calculate_slice_transmission(atoms_in_slice, actual_slice_thickness)
            psi *= transmission
            
            # Store wave after every few slices
            if i % max(1, n_slices // 4) == 0:
                intermediate_waves.append({
                    'slice': i,
                    'thickness': z_end,
                    'wave': psi.copy(),
                    'intensity': np.abs(psi)**2
                })
                
            # Propagate to next slice
            if i < n_slices - 1:
                # QFT
                psi_k = self.qfts.qft_2d(psi)
                psi_k = np.fft.fftshift(psi_k)
                
                # Propagate
                psi_k *= propagator
                
                # iQFT
                psi_k = np.fft.ifftshift(psi_k)
                psi = self.qfts.iqft_2d(psi_k)
        
        # Apply objective lens defocus if specified
        if defocus != 0:
            psi_k = self.qfts.qft_2d(psi)
            psi_k = np.fft.fftshift(psi_k)
            
            # Defocus phase shift
            chi = -np.pi * self.wavelength * self.k_squared * defocus
            psi_k *= np.exp(1j * chi)
            
            psi_k = np.fft.ifftshift(psi_k)
            psi = self.qfts.iqft_2d(psi_k)
            
        # Final intensity
        intensity = np.abs(psi)**2
        
        return {
            'exit_wave': psi,
            'intensity': intensity,
            'mean_intensity': np.mean(intensity),
            'n_slices': n_slices,
            'slice_thickness': actual_slice_thickness,
            'total_thickness': total_thickness,
            'intermediate_waves': intermediate_waves,
            'atoms_3d': atoms_3d
        }
        
    def simulate_thickness_series(self, atoms_3d, thicknesses, slice_thickness=2.0, defocus=0):
        """
        Simulate images at different specimen thicknesses.
        
        Parameters:
        -----------
        atoms_3d : list
            List of atom dictionaries.
        thicknesses : list
            List of thicknesses to simulate.
        slice_thickness : float
            Thickness per slice in Angstroms.
        defocus : float
            Objective lens defocus.
            
        Returns:
        --------
        Dictionary with results for each thickness.
        """
        results = {}
        
        for thickness in thicknesses:
            # Filter atoms up to this thickness
            atoms_filtered = [atom for atom in atoms_3d if atom['position'][2] < thickness]
            
            # Simulate this thickness
            result = self.simulate_multislice(atoms_filtered, thickness, slice_thickness, defocus)
            results[thickness] = result
            
        return results
    
    def plot_wave_magnitude(self, results, thicknesses=None):
        """Plot magnitude of electron wave function at different thicknesses (Figure 7.2)"""
        if thicknesses is None:
            thicknesses = sorted(list(results.keys()))[:4]  # Show first 4
        
        fig, axes = plt.subplots(2, 2, figsize=(10, 10))
        axes = axes.ravel()
        
        for i, thickness in enumerate(thicknesses[:4]):
            if thickness in results:
                ax = axes[i]
                
                # Get magnitude of wave function
                psi = results[thickness]['exit_wave']
                magnitude = np.abs(psi)
                
                # Show central region
                center = self.pixels // 2
                size = self.pixels // 4
                region = magnitude[center-size:center+size, center-size:center+size]
                
                im = ax.imshow(region, cmap='gray', interpolation='nearest')
                ax.set_title(f'{thickness} Å')
                ax.axis('off')
        
        plt.suptitle('Magnitude of electron wave function |ψ(x,y)|', fontsize=14)
        plt.tight_layout()
        plt.show()
        return fig
    
    def plot_intensity_vs_thickness(self, results):
        """Plot intensity and phase vs thickness (Figure 7.3)"""
        thicknesses = sorted(results.keys())
        intensities = [results[t]['mean_intensity'] for t in thicknesses]
        
        # Also calculate phase at center
        phases = []
        for t in thicknesses:
            psi = results[t]['exit_wave']
            center = self.pixels // 2
            phase_center = np.angle(psi[center, center])
            phases.append(phase_center)
        
        fig, ax = plt.subplots(1, 1, figsize=(8, 6))
        
        # Plot intensity
        ax.plot(thicknesses, intensities, 'b-', linewidth=2, label='Intensity')
        
        # Plot phase (normalized)
        phases_norm = (np.array(phases) + np.pi) / (2 * np.pi)  # Normalize to [0,1]
        ax.plot(thicknesses, phases_norm, 'r--', linewidth=2, label='Phase (normalized)')
        
        ax.set_xlabel('Thickness z (in Angstroms)')
        ax.set_ylabel('Intensity / Phase')
        ax.set_title('Intensity and phase vs thickness')
        ax.grid(True, alpha=0.3)
        ax.legend()
        ax.set_xlim(0, max(thicknesses))
        ax.set_ylim(0, 1.1)
        
        plt.tight_layout()
        plt.show()
        return fig
    
    def plot_phase_contrast_series(self, results, thicknesses=None):
        """Plot simulated bright field phase contrast images (Figure 7.4)"""
        if thicknesses is None:
            available = sorted(results.keys())
            # Select 3 representative thicknesses
            thicknesses = [available[len(available)//4], available[len(available)//2], available[-1]]
        
        fig, axes = plt.subplots(1, len(thicknesses), figsize=(4*len(thicknesses), 4))
        if len(thicknesses) == 1:
            axes = [axes]
        
        labels = ['a', 'b', 'c', 'd', 'e'][:len(thicknesses)]
        
        for i, (thickness, label) in enumerate(zip(thicknesses, labels)):
            # Find closest available thickness
            available = sorted(results.keys())
            closest = min(available, key=lambda x: abs(x - thickness))
            
            ax = axes[i]
            intensity = results[closest]['intensity']
            
            # Show central region with contrast adjustment
            center = self.pixels // 2
            size = self.pixels // 4
            region = intensity[center-size:center+size, center-size:center+size]
            
            # Enhance contrast
            vmin = np.percentile(region, 5)
            vmax = np.percentile(region, 95)
            
            im = ax.imshow(region, cmap='gray', vmin=vmin, vmax=vmax, interpolation='bilinear')
            ax.set_title(f'({label}) {closest:.0f} Å')
            ax.axis('off')
            
            # Add scale bar
            pixels_per_nm = size * 2 * self.dx / 10  # pixels per nm
            bar_length = int(pixels_per_nm)  # 1 nm scale bar
            if bar_length > 0:
                ax.plot([10, 10 + bar_length], [region.shape[0]-10, region.shape[0]-10], 
                        'w-', linewidth=3)
                ax.text(10 + bar_length/2, region.shape[0]-20, '1 nm', 
                        ha='center', va='top', color='white', fontsize=10)
        
        plt.suptitle('Simulated bright field phase contrast images', fontsize=14)
        plt.tight_layout()
        plt.show()
        return fig
    
    def print_intensity_table(self, results):
        """Print intensity vs thickness comparison table"""
        print("\nIntensity vs Thickness Results")
        print("Thickness (Å) | Mean Intensity | Slices Used")
        print("-" * 45)
        
        for thickness in sorted(results.keys()):
            if thickness < 600:  # Only show relevant range
                intensity = results[thickness]['mean_intensity']
                n_slices = results[thickness]['n_slices']
                print(f"{thickness:8.1f}     | {intensity:12.4f}   | {n_slices:8d}")
                
# Kirkland example structure
def create_gaas_structure(supercell_size=(6, 6, 20), a_gaas=5.65):
    """
    Create GaAs crystal structure oriented for [110] projection
    
    Parameters:
    - supercell_size: (nx, ny, nz) repetitions of unit cell
    - a_gaas: GaAs lattice constant in Angstroms
    
    Returns:
    - List of atom dictionaries with 'position' and 'Z' keys
    - Dictionary with structural information
    """
    nx, ny, nz = supercell_size
    
    # For [110] projection, unit cell dimensions:
    unit_cell_x = a_gaas / np.sqrt(2)  # along [1-10]
    unit_cell_y = a_gaas  # along [001]
    unit_cell_z = a_gaas * np.sqrt(2)  # along [110]
    
    # Atomic positions in unit cell for [110] projection
    unit_positions = [
        # Ga atoms
        {'x': 0, 'y': 0, 'z': 0, 'element': 'Ga', 'Z': 31},
        {'x': 0.5, 'y': 0.5, 'z': 0.25, 'element': 'Ga', 'Z': 31},
        # As atoms  
        {'x': 0, 'y': 0.25, 'z': 0.125, 'element': 'As', 'Z': 33},
        {'x': 0.5, 'y': 0.75, 'z': 0.375, 'element': 'As', 'Z': 33},
    ]
    
    atoms_3d = []
    
    # Generate supercell
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                for atom in unit_positions:
                    x_pos = (i + atom['x']) * unit_cell_x
                    y_pos = (j + atom['y']) * unit_cell_y
                    z_pos = (k + atom['z']) * unit_cell_z
                    
                    atoms_3d.append({
                        'position': [x_pos, y_pos, z_pos],
                        'Z': atom['Z'],
                        'element': atom['element']
                    })
    
    structure_info = {
        'unit_cell_dimensions': (unit_cell_x, unit_cell_y, unit_cell_z),
        'supercell_size': supercell_size,
        'total_atoms': len(atoms_3d),
        'image_size_x': nx * unit_cell_x,
        'image_size_y': ny * unit_cell_y,
        'specimen_thickness': nz * unit_cell_z
    }
    
    return atoms_3d, structure_info