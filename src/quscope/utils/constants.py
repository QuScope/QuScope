"""
Physical Constants and Common Calculations for Electron Microscopy

This module contains fundamental physical constants and utility functions
commonly used in electron microscopy simulations.

"""

import numpy as np

class PhysicalConstants:
    """
    Physical constants and utility calculations for electron microscopy.
    """
    
    # Physical constants
    m0c2 = 511.0e3                  # Electron rest energy in eV
    hc = 12.398                     # hc in keV·Å 
    a0 = 0.529177                   # Bohr radius in Angstroms
    e_charge = 1.602176634e-19      # Elementary charge in C
    m_e = 9.1093837015e-31          # Electron mass in kg
    h = 6.62607015e-34              # Planck constant in J·s
    c = 299792458                   # Speed of light in m/s
    
    @staticmethod
    def calculate_wavelength(beam_energy):
        """
        Calculate relativistic electron wavelength.
        
        Parameters:
        -----------
        beam_energy : float
            Electron beam energy in eV.
        
        Returns:
        --------
        wavelength : float
            Electron wavelength in Angstroms.
        """
        # Kirkland's formula (Eq. 5.2)
        # λ = h/√(2m₀eV(1 + eV/(2m₀c²)))
        V = beam_energy
        wavelength = PhysicalConstants.hc / np.sqrt(V + 0.97845e-6 * V**2)
        return wavelength
    
    @staticmethod
    def calculate_sigma(beam_energy):
        """
        Calculate interaction parameter σ for weak phase object.
        
        Parameters:
        -----------
        beam_energy : float
            Electron beam energy in eV.
            
        Returns:
        --------
        sigma : float
            Interaction parameter in rad/eV.
        """
        V = beam_energy
        V_keV = V / 1000.0
        m0c2_eV = PhysicalConstants.m0c2
        
        # Calculate wavelength
        wavelength = PhysicalConstants.calculate_wavelength(beam_energy)
        
        # Relativistic factor
        gamma = (m0c2_eV + V) / (2 * m0c2_eV + V)
        
        # Interaction parameter
        sigma = 0.00335 * gamma / (wavelength * V_keV)
        
        return sigma
    