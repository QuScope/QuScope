"""
Kirkland Atomic Potential Calculations

This module implements the Kirkland atomic potential parameterization
for electron scattering calculations in TEM simulations.

Reference:
E. J. Kirkland, "Advanced Computing in Electron Microscopy", 2nd Edition
Appendix C - Atomic Potentials and Scattering Factors
"""

import numpy as np
import json
from scipy.special import kn

KIRKLAND_SCATTERING_FACTOR = 14.4 # eV⋅Å

class KirklandPotential:
    """
    Calculate atomic potentials using Kirkland parametrization.
    """
    
    def __init__(self, params_file='kirkland.json'):
        """
        Initialize with Kirkland parameters.
        
        Parameters:
        -----------
        params_file : str
            Path to JSON file with Kirkland parameters.
        """
        self.params_file = params_file
        self.parameters = self.load_parameters()
        
    def load_parameters(self):
        """
        Load Kirkland parameters from JSON file
        
        Returns:
        --------
        dict : contains element parameters
        """
        try:
            with open(self.params_file, 'r') as f:
                params = json.load(f)
        except FileNotFoundError:
            print(f"Warning: {params} not found. Using default parameters.")
    
    def kirkland_potential_2d(self, x_grid, y_grid, atom_x, atom_y, Z, element=None):
        """
        Calculate 2D projected atomic potential using Kirkland parametrization.
        
        Parameters:
        -----------
        x_grid, y_grid : np.ndarray
            Coordinate grids.
        atom_x, atom_y : float
            Atom position.
        Z : int
            Atomic number.
        element : str, optional
            Element symbol (if not provided, will try to determine from Z).
            
        Returns:
        --------
        V : np.ndarray
            Projected atomic potential in eV.
        """
        element = self.get_element_symbol(Z)
        if element not in self.load_parameters:
            raise ValueError(f"Element with Z={Z} ({element}) not found in Kirkland parameters")
        
        params = self.load_parameters[element]
        a = np.array(params[0], dtype=float)
        b = np.array(params[1], dtype=float)
        c = np.array(params[2], dtype=float)
        d = np.array(params[3], dtype=float)
        
        r2 = (x_grid - atom_x)**2 + (y_grid - atom_y)**2
        r = np.sqrt(r2 + 1e-16) # Add small value to avoid division by zero
        
        V = np.zeros_like(r, dtype=float)
        
        # Modified Bessel K0 terms
        for i in range(3):
            if b[i] > 0:
                arg = 2 * np.pi * r * np.sqrt(b[i])
                mask_small = arg < 50
                mask_large = arg >= 50
                
                if np.any(mask_small):
                    V[mask_small] += 4 * np.pi**2 * a[i] * kn(0, arg[mask_small])
                if np.any(mask_large):
                    x = arg[mask_large]
                    V[mask_large] += 4 * np.pi**2 * a[i] * np.sqrt(np.pi/(2*x)) * np.exp(-x)
        
        # Gaussian terms
        for i in range(3):
            if d[i] > 0:
                V += 2 * np.pi**(3/2) * c[i] / d[i]**(3/2) * np.exp(-np.pi**2 * r2 / d[i])
        
        # Handle r=0
        center_mask = r < 1e-8
        if np.any(center_mask):
            V_center = 0
            for i in range(3):
                if b[i] > 0:
                    small_arg = 2 * np.pi * 1e-8 * np.sqrt(b[i])
                    V_center += 4 * np.pi**2 * a[i] * (-np.log(small_arg/2) - 0.5772156649)
            for i in range(3):
                if d[i] > 0:
                    V_center += 2 * np.pi**(3/2) * c[i] / d[i]**(3/2)
            V[center_mask] = V_center
        
        V *= KIRKLAND_SCATTERING_FACTOR  # Scaling factor
        return V
        
    def get_element_symbol(self, Z):
        """Get element symbol from atomic number"""
        elements = {1: 'H', 2: 'He', 3: 'Li', 4: 'Be', 5: 'B', 6: 'C', 7: 'N', 8: 'O', 9: 'F', 10: 'Ne',
                   11: 'Na', 12: 'Mg', 13: 'Al', 14: 'Si', 15: 'P', 16: 'S', 17: 'Cl', 18: 'Ar', 19: 'K', 20: 'Ca',
                   21: 'Sc', 22: 'Ti', 23: 'V', 24: 'Cr', 25: 'Mn', 26: 'Fe', 27: 'Co', 28: 'Ni', 29: 'Cu', 30: 'Zn',
                   31: 'Ga', 32: 'Ge', 33: 'As', 34: 'Se', 35: 'Br', 36: 'Kr', 37: 'Rb', 38: 'Sr', 39: 'Y', 40: 'Zr',
                   41: 'Nb', 42: 'Mo', 43: 'Tc', 44: 'Ru', 45: 'Rh', 46: 'Pd', 47: 'Ag', 48: 'Cd', 49: 'In', 50: 'Sn',
                   51: 'Sb', 52: 'Te', 53: 'I', 54: 'Xe', 55: 'Cs', 56: 'Ba', 57: 'La', 58: 'Ce', 59: 'Pr', 60: 'Nd',
                   61: 'Pm', 62: 'Sm', 63: 'Eu', 64: 'Gd', 65: 'Tb', 66: 'Dy', 67: 'Ho', 68: 'Er', 69: 'Tm', 70: 'Yb',
                   71: 'Lu', 72: 'Hf', 73: 'Ta', 74: 'W', 75: 'Re', 76: 'Os', 77: 'Ir', 78: 'Pt', 79: 'Au', 80: 'Hg',
                   81: 'Tl', 82: 'Pb', 83: 'Bi', 84: 'Po', 85: 'At', 86: 'Rn', 87: 'Fr', 88: 'Ra', 89: 'Ac', 90: 'Th',
                   91: 'Pa', 92: 'U', 93: 'Np', 94: 'Pu', 95: 'Am', 96: 'Cm', 97: 'Bk', 98: 'Cf', 99: 'Es', 100: 'Fm'}
        return elements.get(Z, f'Z{Z}')