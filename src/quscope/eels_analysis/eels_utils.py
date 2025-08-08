"""
Additional utilities for EELS analysis
======================================

This module implements a hybrid quantum-classical framework for modeling element
substitution, doping effects, and spatial mapping. The purpose of these additional
utilities is to allow for advanced materials engineering, enabling experimentalists
to test materials design prior to actual experimentation and synthesis.

Key Features
------------
- Element substitution, predicting changes in spectrum, energy, intensity, and other features
- Modeling doping effects, predicting changes in spectrum, energy, intensity, and other features
- Spatial mapping for determining distribution of elements and their chemical states
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy import signal, optimize, integrate, interpolate
from scipy.ndimage import gaussian_filter1d
from scipy.fft import fft, ifft, fftfreq
from scipy.signal import hilbert
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA, FastICA
from sklearn.metrics import silhouette_score
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.manifold import TSNE
from sklearn.neural_network import MLPRegressor
import warnings
warnings.filterwarnings('ignore')

import qiskit
from qiskit import QuantumCircuit, transpile, ClassicalRegister, QuantumRegister
from qiskit.circuit.library import RealAmplitudes, ZZFeatureMap, PauliFeatureMap, EfficientSU2
from qiskit.primitives import Estimator, Sampler
from qiskit.quantum_info import SparsePauliOp, Statevector, DensityMatrix, entropy, partial_trace
from qiskit_algorithms.minimum_eigensolvers import VQE
from qiskit_algorithms.optimizers import SPSA, COBYLA, ADAM
from qiskit_aer import Aer
from qiskit_machine_learning.algorithms.classifiers import VQC
from qiskit_machine_learning.neural_networks import SamplerQNN, EstimatorQNN
from qiskit_machine_learning.kernels import FidelityQuantumKernel

from quscope.eels_analysis.quantum_processing import QuantumCircuitLibrary, QuantumPreprocessor, QuantumFeatureExtractor, QuantumMLProcessor

class ElementSubstitutionEngine:
    """
    Engine for modeling element substitution and doping effects in EELS spectra.
    
    This class provides utilities for simulating how energy-loss spectra change due to
    atomic substitutions or doping in materials. It supports predicting chemical shifts,
    new edge features, intensity changes, and confidence estimates. Useful for modeling
    structural or compositional changes in quantum-enhanced EELS analysis.
    """
    
    def __init__(self, edge_ranges):
        self.edge_ranges = edge_ranges
        self.substitution_history = []
    
    def model_element_substitution(self, spectrum_data, energy_axis, target_element, 
                                  substitute_element, substitution_fraction=1.0):
        """
        Model element substitution effects on an EELS spectrum.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray
            Original EELS intensity values.
        energy_axis : np.ndarray
            Corresponding energy values (eV).
        target_element : str
            Element being replaced.
        substitute_element : str
            Element used as substitute.
        substitution_fraction : float
            Fraction of the target atoms substituted (0 to 1).
            
        Returns:
        --------
        dict :
            Substitution model with predicted spectrum and analysis metadata.
        """
        substitution_model = {
            'predicted_spectrum': None,
            'energy_shifts': {},
            'intensity_changes': {},
            'new_features': [],
            'confidence': 0.0,
            'substitution_fraction': substitution_fraction
        }
        
        # Calculate edge shifts
        substitution_model['energy_shifts'] = self.calculate_edge_shifts(
            target_element, substitute_element
        )
        
        # Apply substitution to spectrum
        modified_spectrum = self.apply_element_substitution(
            spectrum_data.copy(), energy_axis, target_element, 
            substitute_element, substitution_model['energy_shifts'], 
            substitution_fraction
        )
        
        # Predict new features
        substitution_model['new_features'] = self.predict_new_features(
            substitute_element, energy_axis
        )
        
        # Calculate intensity changes
        substitution_model['intensity_changes'] = self.calculate_intensity_changes(
            target_element, substitute_element
        )
        
        substitution_model['predicted_spectrum'] = modified_spectrum
        substitution_model['confidence'] = self.estimate_substitution_confidence(
            target_element, substitute_element
        )
        
        # Store in history
        self.substitution_history.append({
            'target': target_element,
            'substitute': substitute_element,
            'fraction': substitution_fraction,
            'result': substitution_model
        })
        
        return substitution_model
    
    def model_doping(self, spectrum_data, energy_axis, host_elements, 
                    dopant_element, doping_concentration=0.01):
        """
        Model low-concentration doping effects on an EELS spectrum.
        Adds dopant-induced spectral features and simulates perturbations to
        host element edges, such as chemical shifts, broadening, and intensity changes.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray
            Original EELS intensity values.
        energy_axis : np.ndarray
            Energy axis (eV).
        host_elements : list[str]
            List of elements present in the host material.
        dopant_element : str
            The dopant being introduced.
        doping_concentration : float
            Fractional concentration of dopant (e.g., 0.01).
        
        Returns:
        --------
        dict :
            Doping model containing modified spectrum and feature predictions.
        """
        doping_model = {
            'predicted_spectrum': None,
            'dopant_features': [],
            'host_modifications': {},
            'electronic_effects': {},
            'confidence': 0.0
        }
        
        modified_spectrum = spectrum_data.copy()
        
        # Add dopant features with appropriate intensity scaling
        for dopant_feature in self.predict_new_features(dopant_element, energy_axis):
            energy = dopant_feature['energy']
            base_intensity = dopant_feature['intensity_estimate']
            
            # Scale by doping concentration
            scaled_intensity = base_intensity * doping_concentration
            
            # Find closest energy point
            energy_idx = np.argmin(np.abs(energy_axis - energy))
            
            # Add Gaussian peak for dopant
            sigma = 2.0  # eV width
            gaussian_peak = scaled_intensity * np.exp(
                -(energy_axis - energy)**2 / (2 * sigma**2)
            )
            
            modified_spectrum += gaussian_peak
            
            doping_model['dopant_features'].append({
                'element': dopant_element,
                'energy': energy,
                'intensity': scaled_intensity,
                'type': dopant_feature['edge_type']
            })
        
        # Model host modifications due to doping
        for host_element in host_elements:
            host_mods = self.calculate_doping_induced_changes(
                host_element, dopant_element, doping_concentration
            )
            doping_model['host_modifications'][host_element] = host_mods
            
            # Apply host modifications to spectrum
            modified_spectrum = self.apply_host_modifications(
                modified_spectrum, energy_axis, host_element, host_mods
            )
        
        doping_model['predicted_spectrum'] = modified_spectrum
        doping_model['confidence'] = min(0.8, 0.9 - doping_concentration * 10)
        
        return doping_model
    
    def calculate_edge_shifts(self, target_element, substitute_element):
        """
        Compute energy edge shifts between two elements.

        Parameters:
        -----------
        target_element : str
            Original element in the spectrum.
        substitute_element : str
            Substituting element.
        
        Returns:
        --------
        dict :
            Dictionary of energy shifts (in eV) by edge type.
        """
        shifts = {}
        
        edge_types = ['K_edges', 'L2_edges', 'L3_edges', 'M4_edges', 'M5_edges']
        
        for edge_type in edge_types:
            if (target_element in self.edge_ranges[edge_type] and
                substitute_element in self.edge_ranges[edge_type]):
                target_energy = np.mean(self.edge_ranges[edge_type][target_element])
                substitute_energy = np.mean(self.edge_ranges[edge_type][substitute_element])
                
                shifts[edge_type] = substitute_energy - target_energy
        
        return shifts
    
    def apply_element_substitution(self, spectrum, energy_axis, target_element,
                                  substitute_element, energy_shifts, fraction=1.0):
        """
        Apply energy shifts and partial intensity transfers to simulate substitution.
        
        Parameters:
        -----------
        spectrum : np.ndarray
            Original spectrum array.
        energy_axis : np.ndarray
            Energy values (eV).
        target_element : str
            Element being replaced.
        substitute_element : str
            Element substituting the target.
        energy_shifts : dict
            Shift values by edge type.
        fraction : float
            Fraction of atoms substituted (0-1).
            
        Returns:
        --------
        np.ndarray :
            Modified spectrum.
        """
        modified_spectrum = spectrum.copy()
        
        for edge_type, shift in energy_shifts.items():
            if target_element in self.edge_ranges[edge_type]:
                target_range = self.edge_ranges[edge_type][target_element]
                
                # Find peaks in target range
                mask = (energy_axis >= target_range[0] - 10) & (energy_axis <= target_range[1] + 10)
                if np.any(mask):
                    region_spectrum = spectrum[mask]
                    region_energy = energy_axis[mask]
                    
                    peaks, _ = signal.find_peaks(region_spectrum,
                                               prominence=0.1*np.max(region_spectrum))
                    
                    for peak_idx in peaks:
                        peak_energy = region_energy[peak_idx]
                        new_energy = peak_energy + shift
                        
                        old_idx = np.argmin(np.abs(energy_axis - peak_energy))
                        new_idx = np.argmin(np.abs(energy_axis - new_energy))
                        
                        if 0 <= new_idx < len(modified_spectrum):
                            intensity = modified_spectrum[old_idx]
                            
                            # Partial substitution
                            modified_spectrum[old_idx] *= (1 - fraction)
                            modified_spectrum[new_idx] += intensity * fraction
        
        return modified_spectrum
    
    def predict_new_features(self, element, energy_axis):
        """
        Predict potential new edge features from an element.
        
        Parameters:
        -----------
        element : str
            Element of interest.
        energy_axis : np.ndarray
            Spectrum energy axis.
            
        Returns:
        --------
        list[dict] :
            Predicted edge features (energy, intensity, type).
        """
        new_features = []
        
        edge_types = ['K_edges', 'L2_edges', 'L3_edges', 'M4_edges', 'M5_edges']
        
        for edge_type in edge_types:
            if element in self.edge_ranges[edge_type]:
                edge_range = self.edge_ranges[edge_type][element]
                edge_energy = np.mean(edge_range)
                
                if energy_axis[0] <= edge_energy <= energy_axis[-1]:
                    new_features.append({
                        'edge_type': edge_type,
                        'energy': edge_energy,
                        'element': element,
                        'intensity_estimate': self.estimate_edge_intensity(element, edge_type)
                    })
        
        return new_features
    
    def estimate_edge_intensity(self, element, edge_type):
        """
        Estimate relative intensity of an edge based on known cross-sections.
        
        Parameters:
        -----------
        element : str
            Chemical symbol.
        edge_type : str
            One of 'K_edges', 'L2_edges', etc.
            
        Returns:
        --------
        float :
            Estimated normalized intensity.
        """
        intensity_factors = {
            'K_edges': 1.0,
            'L2_edges': 0.3,
            'L3_edges': 0.6,
            'M4_edges': 0.1,
            'M5_edges': 0.15
        }
        
        base_intensity = intensity_factors.get(edge_type, 0.5)
        
        # Heavy elements have higher cross-sections
        heavy_elements = ['Pt', 'Au', 'Hg', 'Tl', 'Pb', 'Bi', 'Th', 'U']
        if element in heavy_elements:
            base_intensity *= 1.5
        
        return base_intensity
    
    def calculate_intensity_changes(self, target_element, substitute_element):
        """
        Estimate overall intensity scaling due to substitution.
        
        Parameters:
        -----------
        target_element : str
            Original element.
        substitute_element : str
            Replacing element.
        
        Returns:
        --------
        dict :
            Scaling factor or intensity modifiers.
        """
        intensity_changes = {}
        
        target_z = self.get_atomic_number(target_element)
        substitute_z = self.get_atomic_number(substitute_element)
        
        if target_z > 0 and substitute_z > 0:
            # Cross-section scaling
            ratio = (substitute_z / target_z) ** 3.5
            intensity_changes['overall_scaling'] = ratio
        
        return intensity_changes
    
    def get_atomic_number(self, element):
        """
        Get the atomic number of an element.
        
        Parameters:
        -----------
        element : str
            Element symbol.
            
        Returns:
        --------
        int :
            Atomic number.
        """
        atomic_numbers = {
            'H': 1, 'He': 2, 'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8, 'F': 9, 'Ne': 10,
            'Na': 11, 'Mg': 12, 'Al': 13, 'Si': 14, 'P': 15, 'S': 16, 'Cl': 17, 'Ar': 18,
            'K': 19, 'Ca': 20, 'Sc': 21, 'Ti': 22, 'V': 23, 'Cr': 24, 'Mn': 25, 'Fe': 26,
            'Co': 27, 'Ni': 28, 'Cu': 29, 'Zn': 30, 'Ga': 31, 'Ge': 32, 'As': 33, 'Se': 34,
            'Br': 35, 'Kr': 36, 'Rb': 37, 'Sr': 38, 'Y': 39, 'Zr': 40, 'Nb': 41, 'Mo': 42,
            'Tc': 43, 'Ru': 44, 'Rh': 45, 'Pd': 46, 'Ag': 47, 'Cd': 48, 'In': 49, 'Sn': 50,
            'Sb': 51, 'Te': 52, 'I': 53, 'Xe': 54, 'Cs': 55, 'Ba': 56, 'La': 57, 'Ce': 58,
            'Pr': 59, 'Nd': 60, 'Pm': 61, 'Sm': 62, 'Eu': 63, 'Gd': 64, 'Tb': 65, 'Dy': 66,
            'Ho': 67, 'Er': 68, 'Tm': 69, 'Yb': 70, 'Lu': 71, 'Hf': 72, 'Ta': 73, 'W': 74,
            'Re': 75, 'Os': 76, 'Ir': 77, 'Pt': 78, 'Au': 79, 'Hg': 80, 'Tl': 81, 'Pb': 82,
            'Bi': 83, 'Po': 84, 'At': 85, 'Rn': 86, 'Fr': 87, 'Ra': 88, 'Ac': 89, 'Th': 90,
            'Pa': 91, 'U': 92
        }
        return atomic_numbers.get(element, 0)
    
    def estimate_substitution_confidence(self, target_element, substitute_element):
        """
        Estimate model confidence based on periodic proximity and atomic number.
        
        Parameters:
        -----------
        target_element : str
            Original atom.
        substitute_element : str
            Replacing atom.
            
        Returns:
        --------
        float :
            Confidence score (0.0 to 1.0).
        """
        confidence = 0.5
        
        target_z = self.get_atomic_number(target_element)
        substitute_z = self.get_atomic_number(substitute_element)
        
        if target_z > 0 and substitute_z > 0:
            z_diff = abs(target_z - substitute_z)
            
            if z_diff <= 2:
                confidence = 0.9
            elif z_diff <= 5:
                confidence = 0.7
            elif z_diff <= 10:
                confidence = 0.6
            else:
                confidence = 0.4
        
        # Check if elements are in same group
        if self.are_same_group(target_element, substitute_element):
            confidence *= 1.2
        
        return min(confidence, 1.0)
    
    def are_same_group(self, element1, element2):
        """
        Determine if two elements are from the same periodic group.
        
        Parameters:
        -----------
        element1 : str
            First element.
        element2 : str
            Second element.
            
        Returns:
        --------
        bool :
            True if same group, else False.
        """
        groups = {
            'alkali': ['Li', 'Na', 'K', 'Rb', 'Cs'],
            'alkaline_earth': ['Be', 'Mg', 'Ca', 'Sr', 'Ba'],
            'transition_metals': ['Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn'],
            'carbon_group': ['C', 'Si', 'Ge', 'Sn', 'Pb'],
            'nitrogen_group': ['N', 'P', 'As', 'Sb', 'Bi'],
            'oxygen_group': ['O', 'S', 'Se', 'Te'],
            'halogens': ['F', 'Cl', 'Br', 'I'],
            'noble_gases': ['He', 'Ne', 'Ar', 'Kr', 'Xe', 'Rn']
        }
        
        for group_elements in groups.values():
            if element1 in group_elements and element2 in group_elements:
                return True
        
        return False
    
    def calculate_doping_induced_changes(self, host_element, dopant_element, concentration):
        """
        Simulate spectral changes in host due to dopant-induced effects.
        Includes energy shifts, intensity changes, and spectral broadening.
        
        Parameters:
        -----------
        host_element : str
            Original atom.
        dopant_element : str
            Dopant species.
        concentration : float
            Dopant concentration (0-1).
            
        Returns:
        --------
        dict :
            Modifications to apply to the host element's spectral signature.
        """
        changes = {
            'chemical_shift': 0.0,
            'intensity_change': 0.0,
            'line_broadening': 0.0
        }
        
        # Chemical shift due to charge transfer
        host_z = self.get_atomic_number(host_element)
        dopant_z = self.get_atomic_number(dopant_element)
        
        if host_z > 0 and dopant_z > 0:
            # Electronegativity difference causes chemical shift
            shift_direction = 1 if dopant_z > host_z else -1
            changes['chemical_shift'] = shift_direction * concentration * 2.0  # eV
            
            # Line broadening due to disorder
            changes['line_broadening'] = concentration * 1.5  # eV
            
            # Intensity change due to charge transfer
            changes['intensity_change'] = -concentration * 0.1  # Slight decrease
        
        return changes
    
    def apply_host_modifications(self, spectrum, energy_axis, host_element, modifications):
        """
        Apply chemical shift, broadening and intensity changes to host edges.
        
        Parameters:
        -----------
        spectrum : np.ndarray
            Spectrum to modify.
        energy_axis : np.ndarray
            Energy axis (eV).
        host_element : str
            Element affected.
        modifications : dict
            Changes from induced doping changes
            
        Returns:
        --------
        np.ndarray :
            Modified spectrum.
        """
        modified_spectrum = spectrum.copy()
        
        # Find host element edges
        for edge_type in ['K_edges', 'L2_edges', 'L3_edges']:
            if host_element in self.edge_ranges[edge_type]:
                edge_range = self.edge_ranges[edge_type][host_element]
                
                # Find region around edge
                mask = (energy_axis >= edge_range[0] - 10) & (energy_axis <= edge_range[1] + 10)
                if np.any(mask):
                    region_indices = np.where(mask)[0]
                    
                    # Apply chemical shift
                    shift = modifications['chemical_shift']
                    if abs(shift) > 0.1:
                        shift_indices = np.round(shift / (energy_axis[1] - energy_axis[0])).astype(int)
                        
                        # Shift the region
                        for i in region_indices:
                            new_i = i + shift_indices
                            if 0 <= new_i < len(modified_spectrum):
                                intensity = modified_spectrum[i] * 0.1  # Partial shift
                                modified_spectrum[i] -= intensity
                                modified_spectrum[new_i] += intensity
                    
                    # Apply line broadening
                    broadening = modifications['line_broadening']
                    if broadening > 0:
                        region_spectrum = modified_spectrum[mask]
                        broadened = gaussian_filter1d(region_spectrum, sigma=broadening)
                        modified_spectrum[mask] = broadened
                    
                    # Apply intensity change
                    intensity_change = modifications['intensity_change']
                    modified_spectrum[mask] *= (1 + intensity_change)
        
        return modified_spectrum


class SpatialMappingEngine:
    """
    This class allows for spatially-resolved EELS analysis with classical
    and quantum-enhanced features. It supports spatial grid creations, storing
    and associating spectra with spatial locations, extracting quantum features,
    detecting elements, generating elemental distribution maps, performing clustering
    and phase boundary detection, and spatial map visualizations.
    """
    
    def __init__(self, n_qubits=6):
        self.n_qubits = n_qubits
        self.backend = Aer.get_backend('qasm_simulator')
        self.spatial_data = {}
        self.maps = {}
    
    def create_spatial_grid(self, x_range, y_range, nx=50, ny=50):
        """
        Create a 2D spatial grid for EELS mapping.
        
        Parameters:
        -----------
        x_range : tuple
            (min_x, max_x) spatial range in x-direction.
        y_range : tuple
            (min_y, max_y) spatial range in y-direction.
        nx : int, optional
            Number of grid points along x-axis. Default is 50.
        ny : int, optional
            Number of grid points along y-axis. Default is 50.
            
        Returns:
        self.spatial_grid : dict
            Dictionary containing 1D and 2D grid arrays and dimensions.
        """
        x = np.linspace(x_range[0], x_range[1], nx)
        y = np.linspace(y_range[0], y_range[1], ny)
        X, Y = np.meshgrid(x, y)
        
        self.spatial_grid = {
            'x': x,
            'y': y,
            'X': X,
            'Y': Y,
            'nx': nx,
            'ny': ny
        }
        
        return self.spatial_grid
    
    def add_spectrum_at_position(self, x, y, spectrum_data, energy_axis):
        """
        Store a spectrum at a specific spatial coordinate.
        
        Parameters:
        -----------
        x : float
            X-coordinate of the measurement.
        y : float
            Y-coordiante of the measurement.
        spectrum_data : np.ndarray
            EELS spectrum.
        energy_axis : np.ndarray
            Energy loss values (eV).
        
        Returns:
        --------
        postion_key : str
            Key corresponding to a (x, y) spatial point.
        """
        position_key = f"{x:.3f}_{y:.3f}"
        
        self.spatial_data[position_key] = {
            'position': (x, y),
            'spectrum': spectrum_data,
            'energy_axis': energy_axis,
            'quantum_features': None,
            'elements': None
        }
        
        return position_key
    
    def analyze_spatial_position(self, position_key, analyzer_instance):
        """
        Analyze a single spatial location using quantum feature extraction
        and elemental detection.
        
        Parameters:
        -----------
        position_key : str
            Key corresponding to a (x, y) spatial point.
        analyzer_instance : object
            Instance of an analyzer class with a method:
            `detect_elements_from_spectrum(spectrum, energy_axis)`.
            
        Returns:
        --------
        dict :
            Dictionary with keys: 'quantum_features', 'elements', and 'position',
            or None if key is invalid.
        """
        if position_key in self.spatial_data:
            data = self.spatial_data[position_key]
            
            # Extract quantum features
            feature_extractor = QuantumFeatureExtractor(self.n_qubits)
            quantum_features = feature_extractor.extract_comprehensive_quantum_features(
                data['spectrum'], data['energy_axis']
            )
            
            # Detect elements
            elements = analyzer_instance.detect_elements_from_spectrum(
                data['spectrum'], data['energy_axis']
            )
            
            # Store results
            self.spatial_data[position_key]['quantum_features'] = quantum_features
            self.spatial_data[position_key]['elements'] = elements
            
            return {
                'quantum_features': quantum_features,
                'elements': elements,
                'position': data['position']
            }
        
        return None
    
    def create_elemental_map(self, element, map_type='intensity'):
        """
        Generate a spatial map for a given element based on spectral analysis.
        
        Parameters:
        -----------
        element : str
            The element symbol to map.
        map_type : str, optional
            Type of map: 'intensity', 'confidence', or 'presence'. Default is 'intensity'.
            
        Returns:
        --------
        tuple :
            2D NumPy array of the interpolated map (elemental_map), and a map ID string (map_id).
        """
        if not hasattr(self, 'spatial_grid'):
            raise ValueError("Spatial grid not created. Call create_spatial_grid() first.")
        
        elemental_map = np.zeros((self.spatial_grid['ny'], self.spatial_grid['nx']))
        
        for position_key, data in self.spatial_data.items():
            if data['elements'] and element in data['elements']:
                x, y = data['position']
                
                # Find grid indices
                x_idx = np.argmin(np.abs(self.spatial_grid['x'] - x))
                y_idx = np.argmin(np.abs(self.spatial_grid['y'] - y))
                
                # Get element data
                element_data = data['elements'][element]
                
                if map_type == 'intensity':
                    value = element_data.get('intensity', 0)
                elif map_type == 'confidence':
                    value = element_data.get('confidence', 0)
                else:
                    value = 1.0  # Presence/absence
                
                elemental_map[y_idx, x_idx] = value
        
        # Interpolate to fill grid
        from scipy.interpolate import griddata
        
        # Get known points
        known_points = []
        known_values = []
        
        for position_key, data in self.spatial_data.items():
            x, y = data['position']
            known_points.append([x, y])
            
            if data['elements'] and element in data['elements']:
                element_data = data['elements'][element]
                if map_type == 'intensity':
                    value = element_data.get('intensity', 0)
                elif map_type == 'confidence':
                    value = element_data.get('confidence', 0)
                else:
                    value = 1.0
            else:
                value = 0.0
            
            known_values.append(value)
        
        if len(known_points) > 3:
            # Interpolate
            grid_points = np.column_stack([
                self.spatial_grid['X'].ravel(),
                self.spatial_grid['Y'].ravel()
            ])
            
            interpolated = griddata(
                known_points, known_values, grid_points,
                method='cubic', fill_value=0.0
            )
            
            elemental_map = interpolated.reshape(self.spatial_grid['ny'], self.spatial_grid['nx'])
        
        # Store map
        map_id = f"{element}_{map_type}"
        self.maps[map_id] = {
            'element': element,
            'type': map_type,
            'data': elemental_map,
            'grid': self.spatial_grid
        }
        
        return elemental_map, map_id
    
    def create_quantum_feature_map(self, feature_type='entanglement'):
        """
        Generate a spatial map of a specific quantum-derived feature.
        
        Parameters:
        -----------
        feature_type : str, optional
            One of 'entanglement', 'coherence', or 'signature'.
        
        Returns:
        --------
        tuple :
            2D array of the quantum feature map (feature_map), and a map ID string (map_id).
        """
        if not hasattr(self, 'spatial_grid'):
            raise ValueError("Spatial grid not created. Call create_spatial_grid() first.")
        
        feature_map = np.zeros((self.spatial_grid['ny'], self.spatial_grid['nx']))
        
        # Get known points and values
        known_points = []
        known_values = []
        
        for position_key, data in self.spatial_data.items():
            if data['quantum_features']:
                x, y = data['position']
                known_points.append([x, y])
                
                # Extract specific quantum feature
                if feature_type == 'entanglement':
                    value = data['quantum_features']['entanglement_features'].get('multipartite_entanglement', 0)
                elif feature_type == 'coherence':
                    value = data['quantum_features']['coherence_features'].get('l1_coherence', 0)
                elif feature_type == 'signature':
                    global_sig = data['quantum_features']['spectral_quantum_signature'].get('global_signature', 0)
                    value = global_sig if isinstance(global_sig, (int, float)) else 0
                else:
                    value = 0.0
                
                known_values.append(value)
        
        if len(known_points) > 3:
            # Interpolate
            from scipy.interpolate import griddata
            
            grid_points = np.column_stack([
                self.spatial_grid['X'].ravel(),
                self.spatial_grid['Y'].ravel()
            ])
            
            interpolated = griddata(
                known_points, known_values, grid_points,
                method='cubic', fill_value=0.0
            )
            
            feature_map = interpolated.reshape(self.spatial_grid['ny'], self.spatial_grid['nx'])
        
        # Store map
        map_id = f"quantum_{feature_type}"
        self.maps[map_id] = {
            'feature': feature_type,
            'type': 'quantum_feature',
            'data': feature_map,
            'grid': self.spatial_grid
        }
        
        return feature_map, map_id
    
    def analyze_spatial_heterogeneity(self):
        """
        Analyze spatial heterogeneity using both classical and quantum measures.
        
        Returns:
        --------
        heterogeneity_analysis : dict
            Dictionary containing variance metrics, clustering results,
            and phase boundary detections.
        """
        heterogeneity_analysis = {
            'variance_maps': {},
            'correlation_maps': {},
            'clustering_results': {},
            'phase_boundaries': []
        }
        
        # Calculate variance maps for each element
        for element in self.get_detected_elements():
            if f"{element}_intensity" in self.maps:
                intensity_map = self.maps[f"{element}_intensity"]['data']
                variance = np.var(intensity_map)
                heterogeneity_analysis['variance_maps'][element] = variance
        
        # Quantum clustering of spatial regions
        heterogeneity_analysis['clustering_results'] = self.quantum_spatial_clustering()
        
        # Detect phase boundaries
        heterogeneity_analysis['phase_boundaries'] = self.detect_phase_boundaries()
        
        return heterogeneity_analysis
    
    def get_detected_elements(self):
        """
        Retrieve list of all chemical elements detected across all spatial positions.
        
        Returns:
        --------
        list[str] :
            List of element symbols detected in the dataset.
        """
        elements = set()
        
        for data in self.spatial_data.values():
            if data['elements']:
                elements.update(data['elements'].keys())
        
        return list(elements)
    
    def quantum_spatial_clustering(self):
        """
        Perform quantum-enhanced clustering of spatial regions using extracted
        quantum features.
        
        Returns:
        --------
        dict :
            Dictionary contains:
            - 'clusters' : list[int]
                Cluster assignment for each spatial point.
            - 'positions' : list[tuple]
                (x, y) coordinates of spatial points.
            - 'feature_vectors' : list[list]
                Quantum feature vectors used for clustering.
            - 'n_clusters' : int
                Number of unique clusters identified.
            
            If fewer than 6 feature vectors are available, returns empty results.
        """
        # Collect quantum features from all positions
        feature_vectors = []
        positions = []
        
        for position_key, data in self.spatial_data.items():
            if data['quantum_features']:
                # Create feature vector from quantum features
                qf = data['quantum_features']
                
                feature_vector = [
                    qf['entanglement_features'].get('multipartite_entanglement', 0),
                    qf['coherence_features'].get('l1_coherence', 0),
                    qf['quantum_correlations'].get('quantum_discord', 0)
                ]
                
                # Add spectral signature if available
                global_sig = qf['spectral_quantum_signature'].get('global_signature', 0)
                if isinstance(global_sig, (int, float)):
                    feature_vector.append(global_sig)
                else:
                    feature_vector.append(0)
                
                feature_vectors.append(feature_vector)
                positions.append(data['position'])
        
        if len(feature_vectors) > 5:
            # Use quantum ML for clustering
            qml_processor = QuantumMLProcessor(self.n_qubits)
            clustering_result = qml_processor.quantum_kernel_prediction(feature_vectors)
            
            return {
                'clusters': clustering_result['clusters'],
                'positions': positions,
                'feature_vectors': feature_vectors,
                'n_clusters': len(set(clustering_result['clusters']))
            }
        
        return {'clusters': [], 'positions': [], 'feature_vectors': []}
    
    def detect_phase_boundaries(self):
        """
        Detect phase boundaries by analyzing spatial gradients in elemental maps.
        
        Returns:
        --------
        list[dict] :
            Each dictionary contains:
            - 'map_id' : str
                ID of the map where the boundary was found.
            - 'coordinates' : list[tuple]
                (x, y) real-space coordinates of detected boundary points.
            - 'strength' : float
                Maximum gradient magnitude at the detected boundary.
        """
        boundaries = []
        
        # Use gradient analysis on elemental maps
        for map_id, map_info in self.maps.items():
            if map_info['type'] in ['intensity', 'confidence']:
                data = map_info['data']
                
                # Calculate gradients
                grad_x = np.gradient(data, axis=1)
                grad_y = np.gradient(data, axis=0)
                grad_magnitude = np.sqrt(grad_x**2 + grad_y**2)
                
                # Find high gradient regions (boundaries)
                threshold = np.mean(grad_magnitude) + 2 * np.std(grad_magnitude)
                boundary_mask = grad_magnitude > threshold
                
                if np.any(boundary_mask):
                    # Get boundary coordinates
                    y_coords, x_coords = np.where(boundary_mask)
                    
                    # Convert to real coordinates
                    real_x = self.spatial_grid['x'][x_coords]
                    real_y = self.spatial_grid['y'][y_coords]
                    
                    boundaries.append({
                        'map_id': map_id,
                        'coordinates': list(zip(real_x, real_y)),
                        'strength': np.max(grad_magnitude)
                    })
        
        return boundaries
    
    def visualize_spatial_maps(self, map_ids=None):
        """
        Plot spatial maps (elemental or quantum).
        
        Parameters:
        -----------
        map_ids : list of str, optional
            List of map IDs to visualize. If None, all stored maps are shown.
            
        Returns:
        --------
        tuple :
            Matplotlib figure and axes containing the visualizations.
        """
        if map_ids is None:
            map_ids = list(self.maps.keys())
        
        n_maps = len(map_ids)
        fig, axes = plt.subplots(
            int(np.ceil(n_maps / 3)), 3, 
            figsize=(15, 5 * int(np.ceil(n_maps / 3)))
        )
        
        if n_maps == 1:
            axes = [axes]
        elif n_maps <= 3:
            axes = axes.flatten()
        else:
            axes = axes.flatten()
        
        for i, map_id in enumerate(map_ids):
            if i < len(axes):
                ax = axes[i]
                map_info = self.maps[map_id]
                
                im = ax.imshow(
                    map_info['data'],
                    extent=[
                        self.spatial_grid['x'][0], self.spatial_grid['x'][-1],
                        self.spatial_grid['y'][0], self.spatial_grid['y'][-1]
                    ],
                    origin='lower',
                    cmap='viridis'
                )
                
                ax.set_title(f"{map_id}")
                ax.set_xlabel('X Position')
                ax.set_ylabel('Y Position')
                
                plt.colorbar(im, ax=ax)
        
        # Hide unused subplots
        for i in range(n_maps, len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        return fig, axes
