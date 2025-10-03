# Classical Bloch Wave Implementation Comparison - abTEM vs QuScope

## Date: October 3, 2025
## Purpose: Step-by-step validation of classical implementation before quantum development

---

## Overview: abTEM Bloch Wave Method

**Key Points from Documentation:**

1. **Bloch Wave Method** - Alternative to multislice, efficient for small unit cells
2. **Structure Factor Approach** - Uses Fourier representation for crystal potential
3. **Lobato Parametrization** - Modern atomic scattering factors (alternative to Kirkland)
4. **Thermal Motion** - Includes Debye-Waller factors (thermal_sigma parameter)
5. **Arbitrary Rotations** - Can handle non-orthogonal unit cells

### abTEM Implementation Structure:

```python
# 1. Define structure and structure factor
atoms = ase.build.bulk("Si", cubic=True)
structure_factor = StructureFactor(
    atoms,
    k_max=12,
    parametrization="lobato",  # or "kirkland"
)

# 2. Create Bloch waves object
bloch_waves = BlochWaves(
    structure_factor=structure_factor,
    energy=200e3,
    sg_max=0.1,  # Max scattering angle
)

# 3. Calculate diffraction or exit waves
diffraction = bloch_waves.calculate_diffraction_patterns(thicknesses)
exit_waves = bloch_waves.calculate_exit_wave(thickness, gpts, extent)
```

---

## Current QuScope Implementation (Kirkland-based)

### What You Have:

**File**: `notebooks/sean's testing notebooks/quantum CTEM development.ipynb`

#### Cell 1: Classical WPOA (Weak Phase Object Approximation)
```python
class CTEMSimulator:
    """Classical CTEM using Kirkland parameterization"""
    
    def __init__(self, image_size=50.0, pixels=512, beam_energy=200e3):
        # Kirkland parameters for V(x,y)
        # Relativistic wavelength calculation
        # Interaction parameter sigma
        
    def kirkland_potential_2d(self, x_grid, y_grid, atom_x, atom_y, Z):
        """
        2D projected potential using Kirkland Eq. 5.8-5.10
        - Modified Bessel K0 terms (Yukawa-like)
        - Gaussian terms
        """
        
    def calculate_transmission_function(self):
        """t(x,y) = exp(iσV(x,y))"""
        
    def simulate_image(self, defocus, Cs, alpha_max):
        """
        Full image simulation:
        1. Transmission function
        2. FFT to reciprocal space
        3. Apply objective lens CTF
        4. IFFT back to real space
        5. Calculate intensity
        """
```

**Validation**: Reproduces Kirkland Fig 5.11 and 5.12 ✅

#### Cell 3: Classical Multislice (Full Dynamic Diffraction)
```python
class QuantumGaAsMultislice:
    """Multislice with GaAs crystal structure"""
    
    def create_gaas_structure(self):
        """Generate GaAs [110] atomic positions"""
        
    def get_atoms_in_slice(self, z_start, z_end):
        """Atoms within z-range"""
        
    def calculate_slice_transmission(self, atoms_in_slice, slice_thickness):
        """Transmission for thin slice"""
        
    def calculate_propagator(self, slice_thickness):
        """Fresnel propagator P(k) = exp(-iπλk²Δz)"""
        
    def simulate_thickness_series(self, thicknesses, defocus):
        """
        Multislice algorithm:
        For each slice:
            1. Multiply by transmission function
            2. FFT
            3. Multiply by propagator
            4. IFFT
        """
```

**Validation**: Reproduces Kirkland Fig 7.2, 7.3, 7.4 ✅

---

## Comparison: abTEM vs QuScope

### Similarities ✅

| Feature | abTEM | QuScope |
|---------|-------|---------|
| **Physical Model** | Kirkland/Lobato scattering | Kirkland scattering |
| **Multislice** | ✓ Supported | ✓ Implemented |
| **Weak Phase Object** | ✓ Optional | ✓ Implemented (Fig 5.11-5.12) |
| **CTF Application** | ✓ Defocus, Cs aberrations | ✓ Defocus, Cs aberrations |
| **Beam Energy** | ✓ Configurable (200 keV) | ✓ Configurable (200 keV) |
| **Validation** | ✓ Against multislice | ✓ Against Kirkland figures |

### Differences ⚠️

| Feature | abTEM | QuScope |
|---------|-------|---------|
| **Parametrization** | Lobato (default) or Kirkland | Kirkland only |
| **Structure Factor** | ✓ Fourier space approach | ✗ Direct real space |
| **Bloch Waves** | ✓ Full implementation | ✗ Not implemented |
| **Thermal Motion** | ✓ Debye-Waller factors | ✗ Static atoms |
| **Arbitrary Rotations** | ✓ Euler angles | Limited (requires manual setup) |
| **Periodic Boundaries** | ✓ Automatic | Manual wrapping |
| **Diffraction Patterns** | ✓ Indexed by hkl | ✗ k-space only |

---

## Action Plan: Step-by-Step Implementation

### Phase 0: Validation & Cleanup (This Week)

#### Task 0.1: Extract Classical Code to Module ✅ Priority 1
**Goal**: Clean separation of classical reference implementation

```bash
src/quscope/ctem/
├── classical/
│   ├── __init__.py
│   ├── kirkland_potential.py    # Potential calculation
│   ├── wpoa_simulator.py        # Weak phase object (Fig 5.11-5.12)
│   ├── multislice_simulator.py  # Full multislice (Fig 7.2-7.4)
│   └── structures.py            # Crystal structure generation
```

**Files to Create**:

1. **`kirkland_potential.py`**:
```python
"""
Kirkland atomic potential parameterization (Appendix C)

References:
- Kirkland (2010) "Advanced Computing in Electron Microscopy"
- Eqs. 5.8-5.10 for 2D projected potential
"""

import numpy as np
from scipy.special import kn
import json

class KirklandPotential:
    """
    Calculate atomic potentials using Kirkland parameterization
    """
    
    def __init__(self, kirkland_params_file='kirkland.json'):
        with open(kirkland_params_file, 'r') as f:
            self.params = json.load(f)
    
    def potential_2d(self, x_grid, y_grid, atom_x, atom_y, Z):
        """
        2D projected atomic potential
        
        V(x,y) = Σᵢ 4π²aᵢK₀(2π√bᵢ r) + Σᵢ 2π^(3/2) cᵢ/dᵢ^(3/2) exp(-π²r²/dᵢ)
        
        Parameters:
        -----------
        x_grid, y_grid : ndarray
            Coordinate grids
        atom_x, atom_y : float
            Atom position
        Z : int
            Atomic number
            
        Returns:
        --------
        V : ndarray
            Potential in eV
        """
        element = self._get_element_symbol(Z)
        if element not in self.params:
            raise ValueError(f"Element Z={Z} not in Kirkland parameters")
        
        a, b, c, d = [np.array(self.params[element][i], dtype=float) 
                      for i in range(4)]
        
        r2 = (x_grid - atom_x)**2 + (y_grid - atom_y)**2
        r = np.sqrt(r2 + 1e-16)  # Avoid singularity
        
        V = np.zeros_like(r, dtype=float)
        
        # Modified Bessel K₀ terms
        for i in range(3):
            if b[i] > 0:
                arg = 2 * np.pi * r * np.sqrt(b[i])
                
                # Use different approximations for different ranges
                mask_small = arg < 50
                if np.any(mask_small):
                    V[mask_small] += 4 * np.pi**2 * a[i] * kn(0, arg[mask_small])
                
                mask_large = arg >= 50
                if np.any(mask_large):
                    V[mask_large] += 4 * np.pi**2 * a[i] * np.sqrt(np.pi/(2*arg[mask_large])) * np.exp(-arg[mask_large])
        
        # Gaussian terms
        for i in range(3):
            if d[i] > 0:
                V += 2 * np.pi**(3/2) * c[i] / d[i]**(3/2) * np.exp(-np.pi**2 * r2 / d[i])
        
        # Kirkland scaling factor (Appendix C)
        V *= 14.4  # eV·Å to eV conversion
        
        return V
    
    def _get_element_symbol(self, Z):
        """Map atomic number to element symbol"""
        elements = {
            6: 'C', 14: 'Si', 29: 'Cu', 79: 'Au', 92: 'U',
            31: 'Ga', 33: 'As'  # For GaAs
        }
        return elements.get(Z, None)
```

2. **`wpoa_simulator.py`**:
```python
"""
Weak Phase Object Approximation (WPOA) CTEM simulator

Reproduces Kirkland Fig 5.11 and 5.12
"""

import numpy as np
import matplotlib.pyplot as plt
from .kirkland_potential import KirklandPotential

class WPOASimulator:
    """
    Classical CTEM using weak phase object approximation
    
    Valid for thin specimens where phase ≪ π
    """
    
    def __init__(self, image_size, pixels, beam_energy, 
                 kirkland_params='kirkland.json'):
        self.image_size = image_size  # Å
        self.pixels = pixels
        self.beam_energy = beam_energy  # eV
        
        # Physical constants
        self.m0c2 = 511.0e3  # eV
        self.hc = 12.398  # keV·Å
        
        # Relativistic wavelength (Eq. 5.2)
        self.wavelength = self._calculate_wavelength()
        
        # Interaction parameter (Eq. 5.6)
        self.sigma = self._calculate_sigma()
        
        # Real space grid
        self.dx = self.image_size / self.pixels
        x = (np.arange(self.pixels) - self.pixels/2 + 0.5) * self.dx
        self.x, self.y = x, x
        self.X, self.Y = np.meshgrid(x, x, indexing='xy')
        
        # Reciprocal space grid
        kx = np.fft.fftfreq(self.pixels, d=self.dx)
        self.kx = np.fft.fftshift(kx)
        self.KX, self.KY = np.meshgrid(self.kx, self.kx, indexing='xy')
        
        # Potential calculator
        self.potential = KirklandPotential(kirkland_params)
    
    def _calculate_wavelength(self):
        """Relativistic electron wavelength (Kirkland Eq. 5.2)"""
        V = self.beam_energy
        return self.hc / np.sqrt(V + 0.97845e-6 * V**2)
    
    def _calculate_sigma(self):
        """Interaction parameter (Kirkland Eq. 5.6)"""
        V = self.beam_energy
        V_keV = V / 1000.0
        gamma = (self.m0c2 + V) / (2 * self.m0c2 + V)
        return 0.00335 * gamma / (self.wavelength * V_keV)
    
    def calculate_transmission(self, atom_positions, atom_Zs):
        """
        Transmission function t(x,y) = exp(iσV(x,y))
        
        Parameters:
        -----------
        atom_positions : list of [x, y]
            Atomic positions in Å
        atom_Zs : list of int
            Atomic numbers
            
        Returns:
        --------
        transmission : ndarray (complex)
            Complex transmission function
        V_total : ndarray (float)
            Total projected potential
        """
        V_total = np.zeros((self.pixels, self.pixels))
        
        for (x_atom, y_atom), Z in zip(atom_positions, atom_Zs):
            V_atom = self.potential.potential_2d(
                self.X, self.Y, x_atom, y_atom, Z
            )
            V_total += V_atom
        
        # Phase = σ * V(x,y) for weak phase object
        phase = self.sigma * V_total
        transmission = np.exp(1j * phase)
        
        return transmission, V_total
    
    def objective_lens_ctf(self, defocus, Cs=0, alpha_max=None):
        """
        Contrast Transfer Function H(k) = exp(-iχ(k))
        
        χ(k) = πλk²(CsλK²/2 - Δf)  [Eq. 5.27]
        """
        k2 = self.KX**2 + self.KY**2
        k = np.sqrt(k2)
        
        chi = np.pi * self.wavelength * k2 * (
            0.5 * Cs * self.wavelength**2 * k2 - defocus
        )
        
        H = np.exp(-1j * chi)
        
        if alpha_max is not None:
            k_max = alpha_max / self.wavelength
            H *= (k <= k_max)
        
        return H
    
    def simulate_image(self, atom_positions, atom_Zs, 
                      defocus=0, Cs=0, alpha_max=None):
        """
        Full WPOA image simulation
        
        Steps:
        1. Calculate transmission function
        2. FFT to reciprocal space
        3. Apply objective lens CTF
        4. IFFT to real space
        5. Calculate intensity I = |ψ|²
        """
        # Step 1: Transmission
        transmission, V = self.calculate_transmission(atom_positions, atom_Zs)
        
        # Step 2: Fourier transform
        psi_k = np.fft.fftshift(np.fft.fft2(transmission))
        
        # Step 3: Apply CTF
        H = self.objective_lens_ctf(defocus, Cs, alpha_max)
        psi_k *= H
        
        # Step 4: Inverse Fourier transform
        psi = np.fft.ifft2(np.fft.ifftshift(psi_k))
        
        # Step 5: Intensity
        intensity = np.abs(psi)**2
        
        return {
            'transmission': transmission,
            'potential': V,
            'exit_wave': psi,
            'intensity': intensity
        }
```

3. **`multislice_simulator.py`**:
```python
"""
Multislice CTEM simulator for thick specimens

Reproduces Kirkland Fig 7.2, 7.3, 7.4 (GaAs [110])
"""

import numpy as np
from .kirkland_potential import KirklandPotential
from .wpoa_simulator import WPOASimulator

class MultisliceSimulator(WPOASimulator):
    """
    Multislice algorithm for thick specimens
    
    Divides specimen into thin slices and propagates wave through each:
    ψ(z+Δz) = P(Δz) ⊗ [t(z) · ψ(z)]
    
    where:
    - t(z) = exp(iσV(x,y,z)Δz) is transmission function
    - P(Δz) = F⁻¹{exp(-iπλk²Δz)F{·}} is propagator
    """
    
    def __init__(self, image_size, pixels, beam_energy, slice_thickness,
                 kirkland_params='kirkland.json'):
        super().__init__(image_size, pixels, beam_energy, kirkland_params)
        self.slice_thickness = slice_thickness
        
        # Precompute propagator in k-space
        self.propagator_k = self._compute_propagator()
    
    def _compute_propagator(self):
        """
        Fresnel propagator in reciprocal space
        P(k) = exp(-iπλk²Δz)
        """
        k2 = self.KX**2 + self.KY**2
        phase = -np.pi * self.wavelength * k2 * self.slice_thickness
        return np.exp(1j * phase)
    
    def get_atoms_in_slice(self, atoms_3d, z_start, z_end):
        """
        Extract atoms within z-range
        
        Parameters:
        -----------
        atoms_3d : list of dicts
            Each with 'position' [x,y,z] and 'Z'
        z_start, z_end : float
            Slice boundaries
            
        Returns:
        --------
        atoms_in_slice : list
            Atoms with z_start ≤ z < z_end
        """
        atoms_in_slice = []
        for atom in atoms_3d:
            x, y, z = atom['position']
            if z_start <= z < z_end:
                # Apply periodic boundary conditions
                x_wrapped = x % self.image_size
                y_wrapped = y % self.image_size
                
                atoms_in_slice.append({
                    'position': [x_wrapped - self.image_size/2, 
                                y_wrapped - self.image_size/2],
                    'Z': atom['Z']
                })
        
        return atoms_in_slice
    
    def propagate_slice(self, psi):
        """
        Propagate wave through free space by Δz
        
        ψ_out = F⁻¹{P(k) · F{ψ_in}}
        """
        # FFT to k-space
        psi_k = np.fft.fftshift(np.fft.fft2(psi))
        
        # Apply propagator
        psi_k *= self.propagator_k
        
        # IFFT back to real space
        psi_out = np.fft.ifft2(np.fft.ifftshift(psi_k))
        
        return psi_out
    
    def simulate_thickness(self, atoms_3d, thickness):
        """
        Simulate image at specific thickness
        
        Parameters:
        -----------
        atoms_3d : list of dicts
            3D atomic structure
        thickness : float
            Specimen thickness in Å
            
        Returns:
        --------
        result : dict
            exit_wave, intensity, etc.
        """
        n_slices = int(thickness / self.slice_thickness)
        
        # Initialize with incident plane wave
        psi = np.ones((self.pixels, self.pixels), dtype=complex)
        
        for i in range(n_slices):
            z_start = i * self.slice_thickness
            z_end = (i + 1) * self.slice_thickness
            
            # Get atoms in this slice
            atoms_slice = self.get_atoms_in_slice(atoms_3d, z_start, z_end)
            
            if len(atoms_slice) > 0:
                # Calculate transmission for this slice
                positions = [atom['position'] for atom in atoms_slice]
                Zs = [atom['Z'] for atom in atoms_slice]
                
                transmission, _ = self.calculate_transmission(positions, Zs)
                
                # Apply transmission
                psi *= transmission
            
            # Propagate to next slice (if not last)
            if i < n_slices - 1:
                psi = self.propagate_slice(psi)
        
        intensity = np.abs(psi)**2
        
        return {
            'exit_wave': psi,
            'intensity': intensity,
            'n_slices': n_slices
        }
```

4. **`structures.py`**:
```python
"""
Crystal structure generation for CTEM simulations
"""

import numpy as np

class GaAsStructure:
    """Generate GaAs crystal in [110] orientation"""
    
    def __init__(self, supercell_size=(6, 6, 20)):
        self.supercell_size = supercell_size
        self.a = 5.65  # GaAs lattice constant (Å)
        
        # Unit cell dimensions for [110] projection
        self.unit_cell_x = self.a / np.sqrt(2)
        self.unit_cell_y = self.a
        self.unit_cell_z = self.a * np.sqrt(2)
        
        self.atoms_3d = self._generate_atoms()
    
    def _generate_atoms(self):
        """Generate all atomic positions"""
        nx, ny, nz = self.supercell_size
        
        # Unit cell atomic positions (fractional coordinates)
        unit_positions = [
            {'x': 0, 'y': 0, 'z': 0, 'Z': 31},  # Ga
            {'x': 0.5, 'y': 0.5, 'z': 0.25, 'Z': 31},  # Ga
            {'x': 0, 'y': 0.25, 'z': 0.125, 'Z': 33},  # As
            {'x': 0.5, 'y': 0.75, 'z': 0.375, 'Z': 33},  # As
        ]
        
        atoms = []
        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    for atom in unit_positions:
                        x = (i + atom['x']) * self.unit_cell_x
                        y = (j + atom['y']) * self.unit_cell_y
                        z = (k + atom['z']) * self.unit_cell_z
                        
                        atoms.append({
                            'position': [x, y, z],
                            'Z': atom['Z']
                        })
        
        return atoms
    
    def get_image_size(self):
        """Get image dimensions"""
        nx, ny, _ = self.supercell_size
        return nx * self.unit_cell_x, ny * self.unit_cell_y
    
    def get_total_thickness(self):
        """Get total specimen thickness"""
        _, _, nz = self.supercell_size
        return nz * self.unit_cell_z
```

**Action**: Extract code from notebook cells into these modules

---

#### Task 0.2: Create Unit Tests ✅ Priority 1

**File**: `tests/test_classical_ctem.py`

```python
"""
Unit tests for classical CTEM implementations
"""

import numpy as np
import pytest
from quscope.ctem.classical import (
    KirklandPotential,
    WPOASimulator,
    MultisliceSimulator,
    GaAsStructure
)

class TestKirklandPotential:
    """Test Kirkland potential calculation"""
    
    def test_carbon_potential(self):
        """Test C atom potential matches Kirkland values"""
        pot = KirklandPotential()
        
        # Create small grid around origin
        x = y = np.linspace(-5, 5, 100)
        X, Y = np.meshgrid(x, y)
        
        V = pot.potential_2d(X, Y, atom_x=0, atom_y=0, Z=6)
        
        # Check peak at center (from Kirkland Fig 5.11)
        V_peak = V[50, 50]
        assert 100 < V_peak < 200, f"C potential peak {V_peak:.1f} eV not in expected range"
    
    def test_potential_decay(self):
        """Test potential decays with distance"""
        pot = KirklandPotential()
        
        x = np.array([0, 0.5, 1.0, 2.0, 5.0])
        y = np.zeros_like(x)
        
        V = pot.potential_2d(x, y, atom_x=0, atom_y=0, Z=14)
        
        # Potential should decrease monotonically
        assert np.all(np.diff(V) < 0), "Potential doesn't decay with distance"

class TestWPOASimulator:
    """Test weak phase object approximation"""
    
    def test_incident_wave(self):
        """Test incident plane wave is uniform"""
        sim = WPOASimulator(image_size=10, pixels=64, beam_energy=200e3)
        
        # No atoms → no potential → t(x,y) = 1
        transmission, V = sim.calculate_transmission([], [])
        
        assert np.allclose(V, 0), "Potential should be zero with no atoms"
        assert np.allclose(transmission, 1), "Transmission should be 1 with no atoms"
    
    def test_wavelength(self):
        """Test relativistic wavelength calculation"""
        sim = WPOASimulator(image_size=10, pixels=64, beam_energy=200e3)
        
        # At 200 keV, λ ≈ 0.0251 Å (Kirkland Table 5.1)
        assert 0.024 < sim.wavelength < 0.026, f"Wavelength {sim.wavelength} not correct"
    
    def test_single_atom_image(self):
        """Test image simulation with single atom"""
        sim = WPOASimulator(image_size=20, pixels=128, beam_energy=200e3)
        
        # Single C atom at center
        result = sim.simulate_image(
            atom_positions=[[0, 0]],
            atom_Zs=[6],
            defocus=700,  # Å
            Cs=1.3e7,     # Å
            alpha_max=10.37e-3  # rad
        )
        
        # Check intensity has dip at center (phase contrast)
        center = result['intensity'][64, 64]
        edge = np.mean(result['intensity'][0:10, 0:10])
        
        assert center < edge, "Should see dark contrast at atom position"

class TestMultisliceSimulator:
    """Test multislice algorithm"""
    
    def test_propagator(self):
        """Test free-space propagation conserves norm"""
        sim = MultisliceSimulator(
            image_size=20, pixels=64, 
            beam_energy=200e3, slice_thickness=2.0
        )
        
        # Start with Gaussian wave packet
        x = np.linspace(-10, 10, 64)
        X, Y = np.meshgrid(x, x)
        psi_in = np.exp(-(X**2 + Y**2) / 4)
        
        # Propagate
        psi_out = sim.propagate_slice(psi_in)
        
        # Norm should be conserved
        norm_in = np.sum(np.abs(psi_in)**2)
        norm_out = np.sum(np.abs(psi_out)**2)
        
        assert np.isclose(norm_in, norm_out, rtol=1e-6), "Propagator doesn't conserve norm"
    
    def test_zero_thickness(self):
        """Test zero thickness gives incident wave"""
        gaas = GaAsStructure(supercell_size=(2, 2, 1))
        
        sim = MultisliceSimulator(
            image_size=gaas.get_image_size()[0],
            pixels=32,
            beam_energy=200e3,
            slice_thickness=2.0
        )
        
        # Simulate with thickness = 0 (no slices)
        result = sim.simulate_thickness(gaas.atoms_3d, thickness=0)
        
        # Should get uniform intensity = 1
        assert np.allclose(result['intensity'], 1, atol=0.01)

class TestGaAsStructure:
    """Test GaAs structure generation"""
    
    def test_atom_count(self):
        """Test correct number of atoms"""
        gaas = GaAsStructure(supercell_size=(2, 2, 3))
        
        # 4 atoms per unit cell × 2×2×3 = 48 atoms
        assert len(gaas.atoms_3d) == 48
    
    def test_lattice_constant(self):
        """Test lattice constant is correct"""
        gaas = GaAsStructure(supercell_size=(1, 1, 1))
        
        assert gaas.a == 5.65, "GaAs lattice constant incorrect"
    
    def test_unit_cell_dimensions(self):
        """Test [110] unit cell dimensions"""
        gaas = GaAsStructure()
        
        # [110] projection
        expected_x = 5.65 / np.sqrt(2)
        expected_y = 5.65
        expected_z = 5.65 * np.sqrt(2)
        
        assert np.isclose(gaas.unit_cell_x, expected_x)
        assert np.isclose(gaas.unit_cell_y, expected_y)
        assert np.isclose(gaas.unit_cell_z, expected_z)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

#### Task 0.3: Validation Against Kirkland ✅ Priority 2

**File**: `notebooks/validation/validate_kirkland_figures.ipynb`

Create notebook that reproduces:
- **Figure 5.11**: Transmission function line scan (5 atoms)
- **Figure 5.12**: Phase contrast image (5 atoms)
- **Figure 7.2**: Wave function magnitude vs thickness (GaAs)
- **Figure 7.3**: Intensity vs thickness (GaAs)
- **Figure 7.4**: Phase contrast images at different thicknesses

**Acceptance Criteria**:
- Visual match to published figures
- Quantitative values within 5% of Kirkland
- Document any discrepancies

---

### Phase 0.5: Compare with abTEM (Optional but Recommended)

#### Task 0.4: Install and Test abTEM

```bash
pip install abtem[all]
```

#### Task 0.5: Cross-Validation

Create comparison notebook that runs:
1. **Same structure** (e.g., Si bulk) in both abTEM and QuScope
2. **Same beam energy** (200 keV)
3. **Same thicknesses** (e.g., 100, 200, 500 Å)
4. **Compare outputs**:
   - Exit wave functions
   - Diffraction patterns
   - Image intensities

**Expected**: Should match within numerical precision (~1%)

---

## Summary of This Week's Tasks

### Must Do (Critical Path):
1. ✅ Extract classical code to `src/quscope/ctem/classical/`
2. ✅ Write unit tests in `tests/test_classical_ctem.py`
3. ✅ Create validation notebook reproducing Kirkland figures
4. ✅ Run all tests and ensure they pass
5. ✅ Commit to dev branch

### Should Do (Recommended):
6. ⏳ Install abTEM and run examples
7. ⏳ Cross-validate with abTEM on simple case
8. ⏳ Document any discrepancies

### Nice to Have (Future):
9. ⏸️ Implement Lobato parametrization (alternative to Kirkland)
10. ⏸️ Add thermal motion (Debye-Waller factors)
11. ⏸️ Structure factor approach (Fourier space potential)

---

## Checklist for Completion

- [ ] `kirkland_potential.py` created and tested
- [ ] `wpoa_simulator.py` created and tested
- [ ] `multislice_simulator.py` created and tested
- [ ] `structures.py` created and tested
- [ ] All unit tests pass
- [ ] Kirkland Fig 5.11 reproduced (within 5%)
- [ ] Kirkland Fig 5.12 reproduced (within 5%)
- [ ] Kirkland Fig 7.2 reproduced (within 5%)
- [ ] Kirkland Fig 7.3 reproduced (within 5%)
- [ ] Kirkland Fig 7.4 reproduced (within 5%)
- [ ] Code committed to dev branch
- [ ] Documentation updated

---

## Next Steps After Validation

Once classical implementation is validated and cleaned up:

1. **Phase 1 can begin**: Quantum wave function encoding
2. Use validated classical code as reference for comparison
3. Every quantum component tested against classical counterpart

---

*Document Status: Active Development*  
*Last Updated: October 3, 2025*  
*Next Review: After Task 0.3 completion*
