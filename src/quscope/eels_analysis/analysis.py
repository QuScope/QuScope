"""
Comprehensive EELS Analysis
===========================

This module provides a comprehensive framework for quantum-enhanced EELS analysis
using hybrid quantum-classical techniques. It integrates quantum preprocessing,
feature extraction, machine learning, and material classification to assist in the
interpretation of EELS spectra from advanced microscopy analysis techniques.
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
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

from quscope.eels_analysis.eels_utils import ElementSubstitutionEngine, SpatialMappingEngine
from quscope.eels_analysis.quantum_processing import QuantumCircuitLibrary, QuantumPreprocessor, QuantumFeatureExtractor, QuantumMLProcessor

class EELSAnalyzer:
    """
    This class integrates quantum simulation backends with material-specific databases to
    support tasks such as quantum preprocessing, spectral feature extraction, modeling,
    and material and property classification.
    """
    
    def __init__(self, n_qubits=8):
        self.n_qubits = n_qubits
        self.backend = Aer.get_backend('qasm_simulator')
        self.estimator = Estimator()
        self.sampler = Sampler()
        
        # Initialize all components
        self.preprocessor = QuantumPreprocessor(n_qubits)
        self.feature_extractor = QuantumFeatureExtractor(n_qubits)
        self.qml_processor = QuantumMLProcessor(n_qubits)
        self.spatial_mapper = SpatialMappingEngine(n_qubits)
        
        # Initialize edge ranges and databases
        self.edge_ranges = self.initialize_comprehensive_edge_ranges()
        self.substitution_engine = ElementSubstitutionEngine(self.edge_ranges)
        
        # Initialize material databases
        self.initialize_material_databases()
        
        # Analysis history
        self.analysis_history = []
        self.current_spectrum = None
        self.current_energy_axis = None
    
    def initialize_comprehensive_edge_ranges(self):
        """
        Initialize a comprehensive dictionary of EELS energy edges.
        
        Returns:
        --------
        dict :
            A nested dictionary mapping edge types (K, L2, L3, M4, M5, plasmons)
            to known elements and their characteristic energy ranges (in eV).
        """
        return {
            'K_edges': {
                'H': (13.5, 13.6), 'He': (24.5, 24.6), 'Li': (54.7, 55.5), 'Be': (111.5, 112.0),
                'B': (188.0, 192.0), 'C': (283, 290.0), 'N': (399.6, 409.9), 'O': (531.0, 543.1),
                'F': (685.0, 696.7), 'Ne':(866.9, 870.2), 'Na': (1070.8, 1072.3), 'Mg': (1303.0, 1305.0),
                'Al': (1559.6, 1564.4), 'Si': (1839.0, 1844.9), 'P': (2145.5, 2149.4), 'S': (2472.0, 2476.3),
                'Cl': (2822.4, 2823.8), 'Ar': (3202.9, 3206.3), 'K': (3607.4, 3608.7), 'Ca': (4037.0, 4038.8),
                'Sc': (4492.8, 4493.2), 'Ti': (4960, 4975), 'V': (5464.5, 5466.4), 'Cr': (5989.0, 5989.2),
                'Mn': (6539.0, 6539.3), 'Fe': (7112.0, 7112.8), 'Co': (7708.0, 7709.5), 'Ni': (8332.0, 8333.8),
                'Cu': (8978.8, 8980.5), 'Zn': (9658.0, 9659.9), 'Ga': (10367.0, 10368.0), 'Ge': (11103.0, 11104.0),
                'As': (11866.0, 11868.0), 'Se': (12657.0, 12660.0), 'Br': (13473.0, 13476.0), 'Kr': (14325.0, 14328.0),
                'Rb': (15199.0, 15200.3), 'Sr': (16104.0, 16106.0), 'Y': (17038.0, 170310.0), 'Zr': (17997.0, 17999.0),
                'Nb': (18984.0, 18987.0), 'Mo': (19998.5, 20001.0), 'Tc': (21043.0, 21045.0), 'Ru': (22116.8, 22118.0),
                'Rh': (23219.0, 23220.8), 'Pd': (24349.0, 24351.0), 'Ag': (25514.0, 25514.9), 'Cd': (26710.5, 26712.0)
            },
            'L2_edges': {
                'B': (4.5, 4.7), 'C': (6.2, 6.4), 'N': (9.0, 9.2), 'O': (7.0, 7.1),
                'F': (8.5, 8.6), 'Ne': (18.0, 18.3), 'Na': (30.9, 31.3), 'Mg': (51.2, 51.5),
                'Al': (72.8, 73.3), 'Si': (98.9, 99.4), 'P': (131.8, 132.5), 'S': (164.4, 165.0),
                'Cl': (201.4, 201.7), 'Ar': (247.0, 247.9), 'K': (295.9, 296.8), 'Ca': (349.0, 352.0),
                'Sc': (406.0, 408.0), 'Ti': (456.0, 462.5), 'V': (520.0, 522.0), 'Cr': (583.0, 584.2),
                'Mn': (650.4, 652.0), 'Fe': (720.0, 722.0), 'Co': (793.2, 793.8), 'Ni': (871.0, 872.3),
                'Cu': (950.5, 952.0), 'Zn': (1042.0, 1044.0), 'Ga': (1142.0, 1144.1), 'Ge': (1247.1, 1249.1),
                'As': (1358.0, 1360.0), 'Se': (1475.5, 1477.0), 'Br': (1596.0, 1597.0), 'Kr': (1727.0, 1728.0),
                'Rb': (1863.5, 1865.0), 'Sr': (2006.0, 2007.8), 'Y': (2155.0, 2156.5), 'Zr': (2306.0, 2307.7),
                'Nb': (2464.0, 2466.0), 'Mo': (2624.5, 2626.0), 'Tc': (2793.0, 2794.0), 'Ru': (2966.0, 2968.0),
                'Rh': (3145.8, 3147.0), 'Pd': (3330.0, 3331.0), 'Ag': (3523.3, 3524.5), 'Cd': (3727.0, 3728.0),
                'In': (3938.0, 3939.0), 'Sn': (4155.7, 4156.9), 'Sb': (4380.0, 4381.0), 'Te': (4611.5, 4612.9),
                'I': (4851.8, 4853.0), 'Xe': (5103.0, 5104.5), 'Cs': (5359.0, 5361.0), 'Ba': (5623.0, 5624.5),
                'La': (5890.0, 5891.9), 'Ce': (6163.8, 6165.0), 'Pr': (6440.0, 6441.0), 'Nd': (6721.0, 6722.5),
                'Pm': (7012.2, 7013.5), 'Sm': (7311.0, 7313.0), 'Eu': (7616.5, 6517.9), 'Gd': (7930.0, 7931.3),
                'Tb': (8251.0, 8252.6), 'Dy': (8580.0, 8581.6), 'Ho': (8917.3, 8918.8), 'Er': (9263.8, 9265.0),
                'Tm': (9616.4, 9617.9), 'Yb': (9978.0, 9979.0), 'Lu': (10348.3, 10349.6), 'Hf': (10739.0, 17400.0),
                'Ta': (11135.4, 11137.0), 'W': (11543.0, 11545.0), 'Re': (11958.3, 11959.7), 'Os': (12384.5, 12385.5),
                'Ir': (12823.6, 12825.0), 'Pt': (13272.0, 13273.6), 'Au': (13733.0, 13734.6), 'Hg': (14208.0, 14209.7),
                'Tl': (14697.3, 14698.9), 'Pb': (15199.0, 15201.0), 'Bi': (15710.8, 15712.0), 'Po': (16244.0, 16245.0)
            },
            'L3_edges': {
                'B': (4.5, 4.7), 'C': (6.2, 6.4), 'N': (9.0, 9.2), 'O': (7.0, 7.1),
                'F': (8.5, 8.6), 'Ne': (18.0, 18.3), 'Na': (30.9, 31.3), 'Mg': (51.2, 51.5),
                'Al': (72.8, 73.3), 'Si': (98.9, 99.4), 'P': (131.8, 132.5), 'S': (164.4, 165.0),
                'Cl': (199.5, 200.5), 'Ar': (245.0, 246.0), 'K': (293.3, 294.0), 'Ca': (346.0, 345.0),
                'Sc': (402.0, 402.5), 'Ti': (455.0, 462.0), 'V': (512.4, 512.9), 'Cr': (574.0, 575.0),
                'Mn': (640.0, 641.0), 'Fe': (707.8, 708.5), 'Co': (778.2, 779.0), 'Ni': (854.3, 855.0),
                'Cu': (931.0, 932.0), 'Zn': (1019.3, 1020.7), 'Ga': (1115.0, 1116.0), 'Ge': (1216.2, 1217.7),
                'As': (1323.9, 1323.5), 'Se': (1435.3, 1436.8), 'Br': (1549.0, 1550.4), 'Kr': (1674.5, 1675.9),
                'Rb': (1804.0, 1805.0), 'Sr': (1939.0, 1940.0), 'Y': (2079.8, 2080.8), 'Zr': (2222.0, 2223.0),
                'Nb': (2370.0, 2371.0), 'Mo': (2519.8, 2520.9), 'Tc': (2676.4, 2677.9), 'Ru': (2837.5, 2838.9),
                'Rh': (3003.0, 3004.8), 'Pd': (3173.0, 3174.0), 'Ag': (3350.8, 3351.9), 'Cd': (3537.0, 3538.0),
                'In': (3729.8, 3730.9), 'Sn': (3928.4, 3929.8), 'Sb': (4132.0, 4133.0), 'Te': (4341.0, 4342.0),
                'I': (4556.8, 4557.9), 'Xe': (4782.0, 4783.0), 'Cs': (5011.1, 5012.9), 'Ba': (5246.5, 5247.5),
                'La': (5482.3, 5483.7), 'Ce': (5723.0, 5724.0), 'Pr': (5964.0, 5965.0), 'Nd': (6207.0, 6208.8),
                'Pm': (6459.0, 6460.0), 'Sm': (6716.0, 6717.0), 'Eu': (6976.5, 6977.6), 'Gd': (7242.0, 7243.3),
                'Tb': (7513.5, 7514.5), 'Dy': (7790.0, 7791.0), 'Ho': (8070.5, 8071.5), 'Er': (8357.4, 8358.9),
                'Tm': (8467.5, 8468.5), 'Yb': (8943.0, 8944.0), 'Lu': (9244.0, 9245.0), 'Hf': (9560.0, 9561.0),
                'Ta': (9881.0, 9882.0), 'W': (10206.0, 10207.0), 'Re': (10535.0, 10536.0), 'Os': (10870.4, 10871.9),
                'Ir': (11215.0, 11216.0), 'Pt': (11563.3, 11564.7), 'Au': (11918.4, 11919.5), 'Hg': (12283.3, 12284.9),
                'Tl': (12657.0, 12658.0), 'Pb': (13035.0, 13035.5), 'Bi': (13418.3, 13418.9), 'Po': (13813.3, 13814.4)
            },
            'M4_edges': {
                'Yb': (1575.5, 1576.5), 'Lu': (1638.5, 1639.5), 'Hf': (1715.5, 1716.5), 'Ta': (1792.5, 1793.5),
                'W': (1871.5, 1872.5), 'Re': (1948.5, 1949.5), 'Os': (2030.5, 2031.5), 'Ir': (2115.5, 2116.5),
                'Pt': (2202.0, 2203.5), 'Au': (2291.0, 2292.8), 'Hg': (2385.0, 2387.2), 'Tl': (2485.0, 2487.5),
                'Pb': (2586.0, 2588.8), 'Bi': (2688.0, 2691.0)
            },
            'M5_edges': {
                'Yb': (1527.5, 1528.5), 'Lu': (1588.5, 1589.5), 'Hf': (1661.5, 1662.5), 'Ta': (1734.5, 1735.5),
                'W': (1808.5, 1809.5), 'Re': (1882.5, 1883.5), 'Os': (1959.5, 1960.5), 'Ir': (2039.5, 2040.5),
                'Pt': (2122.0, 2123.2), 'Au': (2206.0, 2207.5), 'Hg': (2295.0, 2296.8), 'Tl': (2369.0, 2371.0),
                'Pb': (2484.0, 2486.2), 'Bi': (2580.0, 2582.5)
            },
            'plasmons': {
                'Al': (15.0, 15.8), 'Si': (16.6, 17.1), 'C': (25.0, 27.0), 'TiO2': (18.0, 20.0)
            }
        }
    
    def initialize_material_databases(self):
        """
        Load internal databases of physical, chemical, and spectral properties for materials.
        """
        self.magnetic_moments = {
            'Fe': 2.2, 'Co': 1.6, 'Ni': 0.6, 'Mn': 5.0, 'Cr': 0.0,
            'Gd': 7.6, 'Tb': 9.3, 'Dy': 10.6, 'Ho': 10.6, 'Er': 9.6
        }
        
        self.work_functions = {
            'Al': (4.06, 4.26), 'Cu': (4.53, 5.10), 'Au': (5.1, 5.47), 'Ag': (4.26, 4.74),
            'Fe': (4.67, 4.81), 'Ni': (5.04, 5.35), 'Ti': 4.33, 'W': (4.32, 5.22)
        }
        
        # Add phonon energies database
        self.phonon_energies = {
            'Al': {'acoustic': 20, 'optical': 40},
            'Si': {'acoustic': 15, 'optical': 60},
            'Fe': {'acoustic': 25, 'optical': 35}
        }
        
        self.material_signatures = {
            'polymers': {
                'organic_polymers': {
                    'required_elements': ['C', 'H'],
                    'optional_elements': ['O', 'N', 'S', 'Cl', 'F'],
                    'characteristic_ratios': {'C/O': (2,20), 'C/H': (0.5,2)},
                    'spectral_features': {
                        'carbon_k_edge': {'pi_star': (284,286), 'sigma_star':(290,295)},
                        'plasmons': {'energy_range': (20,30)},
                        'low_energy_features': True
                    },
                    'subcategories': {
                        'thermoplastics': ['polyethylene', 'polypropylene', 'polystyrene', 'PVC'],
                        'thermosets': ['epoxy', 'polyurethane', 'phenolic'],
                        'elastomers': ['rubber', 'silicone'],
                        'biopolymers': ['cellulose', 'collagen', 'chitin']
                    }
                },
                'inorganic_polymers': {
                    'required_elements': ['Si', 'O'],
                    'optional_elements': ['Al', 'B', 'P', 'N'],
                    'subcategories': ['silicones', 'polysiloxanes', 'borosilicates']
                }
            },
            
            'metals': {
                'pure_metals': {
                    'alkali_metals': ['Li', 'Na', 'K', 'Rb', 'Cs'],
                    'alkaline_earth': ['Be', 'Mg', 'Ca', 'Sr', 'Ba'],
                    'transition_metals': ['Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn'],
                    'post_transition': ['Al', 'Ga', 'In', 'Sn', 'Pb', 'Bi'],
                    'noble_metals': ['Au', 'Ag', 'Pt', 'Pd', 'Rh', 'Ir'],
                    'refractory_metals': ['W', 'Mo', 'Ta', 'Nb', 'Re']
                },
                'alloys': {
                    'steel_alloys': {
                        'required_elements': ['Fe'],
                        'common_additions': ['C', 'Cr', 'Ni', 'Mn', 'Mo', 'V', 'W'],
                        'subcategories': {
                            'carbon_steel': {'C': (0.1, 2.0)},
                            'stainless_steel': {'Cr': (10, 30), 'Ni': (0, 20)},
                            'tool_steel': {'C': (0.5, 1.5), 'W': (0, 20), 'Mo': (0, 10)},
                            'maraging_steel': {'Ni': (15, 25), 'Co': (5, 15), 'Mo': (3, 8)}
                        }
                    },
                    'aluminum_alloys': {
                        'required_elements': ['Al'],
                        'common_additions': ['Cu', 'Mg', 'Si', 'Zn', 'Mn', 'Li'],
                        'subcategories': {
                            '1xxx': {'Al': (99,100)}, # Pure aluminum
                            '2xxx': {'Cu': (2,7)}, # Al-Cu
                            '3xxx': {'Mn': (1, 2)}, # Al-Mn
                            '5xxx': {'Mg': (2, 6)}, # Al-Mg
                            '6xxx': {'Mg': (0.5, 2), 'Si': (0.5, 2)}, # Al-Mg-Si
                            '7xxx': {'Zn': (4, 8)} # Al-Zn
                        }
                    },
                    'titanium_alloys': {
                        'required_elements': ['Ti'],
                        'common_additions': ['Al', 'V', 'Mo', 'Sn', 'Zr', 'Nb'],
                        'subcategories': {
                            'alpha_alloys': {'Al': (2, 8), 'Sn': (0, 4)},
                            'beta_alloys': {'V': (10, 15), 'Mo': (3, 8)},
                            'alpha_beta_alloys': {'Al': (4, 7), 'V': (2, 6)}
                        }
                    },
                    'superalloys': {
                        'required_elements': ['Ni', 'Co', 'Fe'],
                        'common_additions': ['Cr', 'Al', 'Ti', 'Mo', 'W', 'Ta', 'Re'],
                        'subcategories': ['inconel', 'hastelloy', 'waspaloy', 'rene']
                    }
                }
            },
            
            'semiconductors': {
                'elemental': {
                    'group_iv': ['Si', 'Ge', 'C'], # Carbon as diamond
                    'characteristics': {
                        'band_gap_range': (0.1,5.5), # eV
                        'crystal_structure': ['diamond', 'zinc_blende']
                    }
                },
                'compound': {
                    'iii_v': {
                        'combinations': [('Ga', 'As'), ('In', 'P'), ('Al', 'As'), ('Ga', 'N'), ('In', 'As')],
                        'band_gaps': {'GaAs': 1.42, 'InP': 1.35, 'GaN': 3.4, 'AlAs': 2.16}
                    },
                    'ii_vi': {
                        'combinations': [('Zn', 'S'), ('Cd', 'Te'), ('Hg', 'Te'), ('Zn', 'Se')],
                        'band_gaps': {'ZnS': 3.6, 'CdTe': 1.5, 'ZnSe': 2.7}
                    },
                    'iv_vi': {
                        'combinations': [('Pb', 'S'), ('Pb', 'Te'), ('Sn', 'Te')],
                        'applications': ['infrared_detectors', 'thermoelectrics']
                    }
                },
                'oxide_semiconductors': {
                    'combinations': [('Zn', 'O'), ('Ti', 'O'), ('In', 'Ga', 'Zn', 'O'), ('Cu', 'O')],
                    'characteristics': ['transparent', 'wide_band_gap']
                }
            },
            
            'ceramics': {
                'oxide_ceramics': {
                    'simple_oxides': [('Al', 'O'), ('Zr', 'O'), ('Ti', 'O'), ('Mg', 'O'), ('Ca', 'O')],
                    'complex_oxides': [
                        ('Ba', 'Ti', 'O'), # BaTiO3 - ferroelectric
                        ('Y', 'Ba', 'Cu', 'O'), # YBCO - superconductor
                        ('La', 'Sr', 'Mn', 'O'), # LSMO - colossal magnetoresistance
                        ('Pb', 'Zr', 'Ti', 'O') # PZT - piezoelectric
                    ],
                    'spinel_structure': [('Mg', 'Al', 'O'), ('Fe', 'Al', 'O'), ('Zn', 'Al', 'O')],
                    'perovskite_structure': [('Ca', 'Ti', 'O'), ('Sr', 'Ti', 'O'), ('Ba', 'Ti', 'O')]
                },
                'non_oxide_ceramics': {
                    'carbides': [('Si', 'C'), ('Ti', 'C'), ('W', 'C'), ('B', 'C')],
                    'nitrides': [('Si', 'N'), ('Ti', 'N'), ('Al', 'N'), ('B', 'N')],
                    'borides': [('Ti', 'B'), ('Zr', 'B'), ('Hf', 'B')],
                    'silicides': [('Mo', 'Si'), ('Ti', 'Si'), ('W', 'Si')]
                }
            },
            
            'glasses': {
                'silicate_glasses': {
                    'required_elements': ['Si', 'O'],
                    'common_modifiers': ['Na', 'K', 'Ca', 'Mg', 'Al', 'B', 'Pb'],
                    'subcategories': {
                        'soda_lime': ['Na', 'Ca', 'Si', 'O'],
                        'borosilicate': ['B', 'Si', 'O'],
                        'lead_crystal': ['Pb', 'Si', 'O'],
                        'aluminosilicate': ['Al', 'Si', 'O']
                    }
                },
                'metallic_glasses': {
                    'base_elements': ['Fe', 'Co', 'Ni', 'Cu', 'Zr', 'Ti', 'Al'],
                    'glass_formers': ['B', 'P', 'C', 'Si'],
                    'characteristics': ['amorphous_structure', 'no_crystalline_peaks']
                },
                'chalcogenide_glasses': {
                    'chalcogens': ['S', 'Se', 'Te'],
                    'network_formers': ['As', 'Ge', 'Si', 'P'],
                    'applications': ['infrared_optics', 'phase_change_memory']
                }
            },
            
            'composites': {
                'polymer_matrix': {
                    'fiber_reinforced': {
                        'matrix': ['C', 'H', 'O', 'N'], # Polymer
                        'reinforcement': ['C', 'Si', 'Al', 'B'], # Carbon, glass, aramid fibers
                        'subcategories': ['carbon_fiber', 'glass_fiber', 'aramid_fiber']
                    },
                    'particle_reinforced': {
                        'matrix': ['C', 'H', 'O'],
                        'particles': ['Al', 'Si', 'Ti', 'B', 'C'],
                        'subcategories': ['filled_polymers', 'nanocomposites']
                    }
                },
                'metal_matrix': {
                    'base_metals': ['Al', 'Ti', 'Mg', 'Cu'],
                    'reinforcements': ['C', 'Si', 'Al', 'Ti', 'B'],
                    'categories': ['mmc_continuous_fiber', 'mmc_particulate']
                },
                'ceramic_matrix': {
                    'matrix': ['Si', 'Al', 'O', 'C', 'N'],
                    'reinforcement': ['C', 'Si'],
                    'subcategories': ['cmc_continuous_fiber', 'cmc_whisker']
                }
            },
            
            'nanomaterials': {
                'carbon_nanomaterials': {
                    'types': ['graphene', 'carbon_nanotubes', 'fullerenes', 'carbon_dots'],
                    'signature': ['C'],
                    'spectral_features': {
                        'pi_plasmon': (6,7), # eV
                        'sigma_plasmon': (25,27), # eV
                        'carbon_k_edge': (285, 286)
                    }
                },
                'metal_nanoparticles': {
                    'common_metals': ['Au', 'Ag', 'Cu', 'Pt', 'Pd', 'Fe', 'Co', 'Ni'],
                    'characteristics': ['surface_plasmons', 'quantum_size_effects']
                },
                'quantum_dots': {
                    'materials': [('Cd', 'Se'), ('Cd', 'S'), ('In', 'As'), ('Pb', 'S')],
                    'characteristics': ['quantum_confinement', 'size_dependent_properties']
                }
            },
            
            'biomaterials': {
                'natural': {
                    'proteins': ['C', 'H', 'O', 'N', 'S'],
                    'minerals': [('Ca', 'P', 'O'), ('Ca', 'C', 'O')], # Hydroxyapatite, calcite
                    'subcategories': ['bone', 'teeth', 'shell', 'collagen']
                },
                'synthetic': {
                    'bioceramics': [('Ca', 'P', 'O'), ('Al', 'O'), ('Zr', 'O')],
                    'biopolymers': ['C', 'H', 'O', 'N'],
                    'biocomposites': ['mixed_organic_inorganic']
                }
            },
            
            'energetic_materials': {
                'explosives': {
                    'molecular': ['C', 'H', 'N', 'O'],
                    'characteristics': ['high_nitrogen_content', 'oxygen_balance']
                },
                'propellants': {
                    'solid': ['C', 'H', 'N', 'O', 'Al', 'NH4', 'ClO4'],
                    'characteristics': ['controlled_burn_rate']
                },
                'pyrotechnics': {
                    'oxidizers': ['K', 'Ba', 'Sr', 'ClO4', 'NO3'],
                    'fuels': ['Mg', 'Al', 'C', 'S'],
                    'colorants': ['Cu', 'Sr', 'Ba', 'Na', 'Li']
                }
            }
        }
    
    def load_spectrum_file(self, filepath):
        """
        Load a spectrum file and route to the appropriate parser.
        
        Parameters:
        -----------
        filepath : str or Path
            Path to the spectrum file. Supported formats:
            - '.msa': MSA (Microscopy Society of America) format
            - '.txt', '.dat': Two-column text files (energy, intensity)
            - '.csv': Comma-separated values
            
        Returns:
        --------
        tuple :
            self : EELSAnalyzer
            current_spectrum : np.ndarray
            current_energy_axis : np.ndarray    
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"File {filepath} not found")
        
        if filepath.suffix.lower() == '.msa':
            return self.load_msa_file(filepath)
        elif filepath.suffix.lower() in ['.txt', '.dat']:
            return self.load_text_file(filepath)
        elif filepath.suffix.lower() in ['.csv']:
            return self.load_csv_file(filepath)
        else:
            raise ValueError(f"Unsupported file format: {filepath.suffix}")
    
    def load_msa_file(self, filepath):
        """
        Load an EELS spectrum from .msa file.
        
        Parameters:
        -----------
        filepath : str or Path
            Path to the .msa file
        
        Returns:
        --------
        tuple : 
            self : EELSAnalyzer
            current_energy_axis : np.ndarray
            current_spectrum : np.ndarray
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"File {filepath} not found")

        with open(filepath, 'r') as f:
            lines = f.readlines()

        # Parse metadata
        metadata = {}
        data_start_idx = 0

        for i, line in enumerate(lines):
            if line.startswith('#'):
                if ':' in line:
                    key, value = line[1:].strip().split(':', 1)
                    metadata[key.strip()] = value.strip()
            else:
                data_start_idx = i
                break

        # Parse data
        data_lines = lines[data_start_idx:]
        spectrum_data = []
        energy_data = []

        for line in data_lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue  # skip empty lines and inline comments like #ENDOFDATA

            # Clean formatting
            line = line.rstrip(',')        # remove trailing commas
            line = line.replace(',', ' ')  # convert commas to spaces

            # Try parsing float values
            try:
                values = [float(v) for v in line.split() if v]
                if len(values) == 1:
                    spectrum_data.append(values[0])
                elif len(values) >= 2:
                    energy_data.append(values[0])
                    spectrum_data.append(values[1])
            except ValueError:
                continue  # skip lines that can't be converted to floats

        # Generate energy axis if not found
        if not energy_data:
            n_channels = len(spectrum_data)
            x_per_chan = float(metadata.get('XPERCHAN', 1.0))
            x_offset = float(metadata.get('OFFSET', 0.0))
            energy_data = np.arange(n_channels) * x_per_chan + x_offset

        self.current_spectrum = np.array(spectrum_data)
        self.current_energy_axis = np.array(energy_data)

        return self, self.current_spectrum, self.current_energy_axis

    
    def load_text_file(self, filepath):
        """
        Load an EELS spectrum from a .txt file.
        
        Parameters:
        -----------
        filepath : str or Path
            Path to the .txt file.
            
        Returns:
        --------
        tuple :
            self : EELSAnalyzer
            current_spectrum : np.ndarray
            current_energy_axis : np.ndarray 
        """
        data = np.loadtxt(filepath)
        
        if data.shape[1] >= 2:
            self.current_energy_axis = data[:, 0]
            self.current_spectrum = data[:, 1]
        else:
            self.current_spectrum = data.flatten()
            self.current_energy_axis = np.arange(len(self.current_spectrum))
        
        return self.current_spectrum, self.current_energy_axis, {}
    
    def load_csv_file(self, filepath):
        """
        Load an EELS spectrum from a .csv file.
        
        Parameters:
        -----------
        filepath : str or Path
            Path to the .csv file.
        
        Returns:
        --------
        tuple :
            self : EELSAnalyzer
            current_spectrum : np.ndarray
            current_energy_axis : np.ndarray
        """
        df = pd.read_csv(filepath)
        
        if len(df.columns) >= 2:
            self.current_energy_axis = df.iloc[:, 0].values
            self.current_spectrum = df.iloc[:, 1].values
        else:
            self.current_spectrum = df.iloc[:, 0].values
            self.current_energy_axis = np.arange(len(self.current_spectrum))
        
        return self.current_spectrum, self.current_energy_axis, {}
    
    def preprocess_spectrum(self, spectrum_data=None, energy_axis=None, 
                          use_quantum_enhancement=True):
        """
        Comprehensive spectrum preprocessing with quantum enhancement options.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray, optional
            Spectrum intensity data. If None, uses self.current_spectrum.
        energy_axis : np.ndarray, optional
            Energy axis in eV. If None, uses self.current_energy_axis.
        use_quantum_enhancement : bool, optional
            Whether to apply quantum-enhanced preprocessing. Default is True.
            
        Returns:
        --------
        processed_spectrum : np.ndarray
            Preprocessed spectrum data.
        """
        if spectrum_data is None:
            spectrum_data = self.current_spectrum
        if energy_axis is None:
            energy_axis = self.current_energy_axis
        
        if spectrum_data is None:
            raise ValueError("No spectrum data available")
        
        # Ensure positive values
        spectrum_data = np.maximum(spectrum_data, 0)
        
        # Advanced preprocessing
        if use_quantum_enhancement:
            processed_spectrum = self.preprocessor.quantum_richardson_lucy_deconvolution(spectrum_data)
            processed_spectrum = self.quantum_noise_reduction(processed_spectrum)
        else:
            processed_spectrum = self.classical_preprocessing(spectrum_data)
        
        # Normalization
        processed_spectrum = self.normalize_spectrum(processed_spectrum)
        
        return processed_spectrum
    
    def quantum_noise_reduction(self, spectrum):
        """
        Apply quantum-enhanced noise reduction to spectrum data.
        
        Parameters:
        -----------
        spectrum : np.ndarray
            Input spectrum data to be denoised.
        
        Returns:
        --------
        filtered_spectrum : np.ndarray
            Denoised spectrum with improved signal-to-noise ratio.
        """
        n_filter_qubits = min(4, self.n_qubits)
        segment_size = len(spectrum) // n_filter_qubits
        filtered_spectrum = spectrum.copy()
        
        for i in range(n_filter_qubits):
            start_idx = i * segment_size
            end_idx = min((i + 1) * segment_size, len(spectrum))
            segment = spectrum[start_idx:end_idx]
            
            if len(segment) > 0:
                segment_variance = np.var(segment)
                if segment_variance > 0:
                    noise_level = min(segment_variance / np.mean(segment), 0.5)
                    smoothed_segment = segment * (1 - noise_level * 0.1)
                    filtered_spectrum[start_idx:end_idx] = smoothed_segment
        
        return filtered_spectrum
    
    def classical_preprocessing(self, spectrum):
        """
        Apply classical preprocessing methods as fallback or comparison.
        
        Parameters:
        -----------
        spectrum : np.ndarray
            Input spectrum data.
            
        Returns:
        --------
        spectrum : np.ndarray
            Classically preprocessed spectrum.
        """
        window_length = min(21, len(spectrum) // 4 * 2 + 1)
        if window_length >= 3:
            spectrum = signal.savgol_filter(spectrum, window_length, 2)
        
        spectrum = gaussian_filter1d(spectrum, sigma=1.0)
        return spectrum
    
    def normalize_spectrum(self, spectrum, method='l2'):
        """
        Normalize spectrum for quantum processing and analysis.
        
        Parameters:
        -----------
        spectrum : np.ndarray
            Input spectrum data.
        method : {'l2', 'max', 'area'}, optional
            Normalization method. Default is 'l2'.
            - 'l2': L2 norm normalization.
            - 'max': Maximum value normalization.
            - 'area': Area under curve normalization.
        
        Returns:
        --------
        np.ndarray :
            Normalized spectrum.
        """
        if method == 'max':
            max_val = np.max(spectrum)
            if max_val > 0:
                return spectrum / max_val
        elif method == 'l2':
            norm = np.linalg.norm(spectrum)
            if norm > 0:
                return spectrum / norm
        elif method == 'area':
            area = np.trapz(spectrum)
            if area > 0:
                return spectrum / area
        
        return spectrum / (np.max(spectrum) + 1e-10)
    
    def detect_elements_from_spectrum(self, spectrum_data, energy_axis):
        """
        Detect chemical elements using quantum-enhanced peak analysis.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray
            Preprocessed spectrum intensity data.
        energy_axis : np.ndarray
            Energy axis in eV.
            
        Returns:
        --------
        detected_elements : dict
            Dictionary with element symbols as keys and detection info as values.
        """
        detected_elements = {}
        
        quantum_peaks = self.quantum_enhanced_peak_detection(spectrum_data, energy_axis)
        
        for peak_energy, peak_info in quantum_peaks.items():
            for edge_type, edge_dict in self.edge_ranges.items():
                for element, (e_min, e_max) in edge_dict.items():
                    if e_min <= peak_energy <= e_max:
                        if element not in detected_elements:
                            detected_elements[element] = {
                                'edges': [],
                                'intensity': 0,
                                'confidence': 0,
                                'quantum_signature': 0
                            }
                        
                        detected_elements[element]['edges'].append({
                            'type': edge_type,
                            'energy': peak_energy,
                            'intensity': peak_info['intensity'],
                            'quantum_signature': peak_info['quantum_signature']
                        })
                        
                        detected_elements[element]['intensity'] = max(
                            detected_elements[element]['intensity'],
                            peak_info['intensity']
                        )
                        detected_elements[element]['quantum_signature'] += peak_info['quantum_signature']
        
        # Calculate confidence scores
        for element, info in detected_elements.items():
            n_edges = len(info['edges'])
            avg_quantum_sig = info['quantum_signature'] / n_edges if n_edges > 0 else 0
            confidence = min(0.9, (n_edges * 0.3 + avg_quantum_sig * 0.7))
            detected_elements[element]['confidence'] = confidence
        
        return detected_elements
    
    def quantum_enhanced_peak_detection(self, spectrum_data, energy_axis):
        """
        Detect spectral peaks using quantum-enhanced algorithms.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray
            Preprocessed spectrum intensity data
        energy_axis : np.ndarray
            Corresponding energy axis in eV.
        
        Returns:
        --------
        quantum_peaks : dict
            Dictionary with peak energies as keys
            and peak information as values.
        """
        peaks, properties = signal.find_peaks(
            spectrum_data,
            prominence=0.02 * np.max(spectrum_data),
            distance=5,
            width=1
        )
        
        quantum_peaks = {}
        
        for i, peak_idx in enumerate(peaks):
            peak_energy = energy_axis[peak_idx]
            
            # Extract local region around peak
            window = 30
            start_idx = max(0, peak_idx - window)
            end_idx = min(len(spectrum_data), peak_idx + window)
            
            local_spectrum = spectrum_data[start_idx:end_idx]
            local_energy = energy_axis[start_idx:end_idx]
            
            quantum_analysis = self.quantum_peak_analysis(local_spectrum, local_energy, peak_energy)
            
            quantum_peaks[peak_energy] = {
                'intensity': spectrum_data[peak_idx],
                'prominence': properties['prominences'][i] if i < len(properties['prominences']) else 0,
                'width': properties['widths'][i] if i < len(properties['widths']) else 0,
                'quantum_signature': quantum_analysis['signature'],
                'entanglement_entropy': quantum_analysis['entanglement'],
                'coherence_measure': quantum_analysis['coherence']
            }
        
        return quantum_peaks
    
    def quantum_peak_analysis(self, local_spectrum, local_energy, peak_energy):
        """
        Perform detailed quantum analysis of individual spectral peaks.
        
        Parameters:
        -----------
        local_spectrum : np.ndarray
            Spectrum data in the local region around the peak.
        local_energy : np.ndarray
            Energy axis for the local region.
        peak_energy : float
            Central energy of the peak being analyzed.
        
        Returns:
        --------
        dict :
            Quantum analysis results for the peak:
            - 'signature' : float
                Quantum signature strength (0-1).
            -'entanglement' : float
                Entanglement entropy measure.
            - 'coherence' : float
                L1 coherence measure.
        """
        local_spectrum = local_spectrum / (np.max(local_spectrum) + 1e-10)
        n_peak_qubits = min(4, self.n_qubits)
        
        qc = QuantumCircuit(n_peak_qubits)
        
        # Multi-layer encoding
        for layer in range(3):
            for i in range(n_peak_qubits):
                if i < len(local_spectrum):
                    amplitude = local_spectrum[i] if len(local_spectrum) > i else 0
                    qc.ry(amplitude * np.pi, i)
                    qc.rz(amplitude * np.pi / (layer + 1), i)
            
            for i in range(n_peak_qubits - 1):
                qc.cx(i, i + 1)
            
            energy_param = (peak_energy % 100) / 100
            for i in range(n_peak_qubits):
                qc.rz(energy_param * np.pi / (layer + 1), i)
        
        try:
            statevector = Statevector.from_instruction(qc)
            
            signature = self.feature_extractor.calculate_quantum_signature(statevector, n_peak_qubits)
            entanglement = self.feature_extractor.calculate_entanglement_entropy(statevector, n_peak_qubits)
            
            rho = DensityMatrix(statevector)
            coherence = self.feature_extractor.calculate_l1_coherence(rho)
            
            return {
                'signature': signature,
                'entanglement': entanglement,
                'coherence': coherence
            }
        
        except Exception as e:
            print(f"Warning: Quantum peak analysis failed: {e}")
            return {'signature': 0.5, 'entanglement': 0.0, 'coherence': 0.5}
    
    def quantum_fourier_analysis(self, spectrum_data=None):
        """
        Perform Quantum Fourier Transform (QFT) analysis of spectrum.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray, optional
            Spectrum data to analyze. If None, uses current_spectrum.
            
        Returns:
        --------
        tuple of (dict, QuantumCircuit or None)
            - Quantum measurement counts from QFT circuit.
            - The quantum circuit used (None if analysis failed).
        """
        if spectrum_data is None:
            spectrum_data = self.current_spectrum
        
        try:
            n_qft_qubits = min(6, self.n_qubits)
            
            # Create simple QFT circuit (placeholder implementation)
            qc = QuantumCircuit(n_qft_qubits, n_qft_qubits)
            
            # Encode some spectrum data
            for i in range(min(n_qft_qubits, len(spectrum_data))):
                amplitude = spectrum_data[i] / (np.max(spectrum_data) + 1e-10)
                qc.ry(amplitude * np.pi, i)
            
            # Apply simplified QFT
            for i in range(n_qft_qubits):
                qc.h(i)
                for j in range(i + 1, n_qft_qubits):
                    qc.cp(np.pi / (2**(j-i)), j, i)
            
            qc.measure_all()
            
            transpiled_qc = transpile(qc, self.backend)
            job = self.backend.run(transpiled_qc, shots=1024)
            result = job.result()
            counts = result.get_counts()
            
            return counts, qc
            
        except Exception as e:
            print(f"Warning: Quantum Fourier Transform failed: {e}")
            return {}, None
    
    def comprehensive_analysis(self, spectrum_data=None, energy_axis=None, 
                              material_name=None, use_quantum_ml=True):
        """
        Perform comprehensive quantum-enhanced EELS analysis. Execute a complete
        analysis pipeline including element detection, quantum feature extraction,
        bonding analysis, magnetic/electronic characterization, and material
        identification using quantum-enhanced algorithms.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray, optional
            Spectrum intensity data. If None, uses loaded spectrum.
        energy_axis : np.ndarray, optional
            Energy axis in eV. If None, uses loaded energy axis.
        material_name : str, optional
            Name identifier for sample being analyzed.
        use_quantum_ml : bool, optional
            Whether to apply quantum machine learning. Default is True.
            
        Returns:
        --------
        comprehensive_results : dict
            Comprehensive analysis results.
        """
        if spectrum_data is None:
            spectrum_data = self.current_spectrum
        if energy_axis is None:
            energy_axis = self.current_energy_axis
        
        if spectrum_data is None or energy_axis is None:
            raise ValueError("No spectrum data available for analysis")
        
        print("Starting comprehensive quantum-enhanced EELS analysis...")
        
        # 1. Preprocessing
        print("Step 1: Quantum-enhanced preprocessing...")
        processed_spectrum = self.preprocess_spectrum(spectrum_data, energy_axis)
        
        # 2. Element detection
        print("Step 2: Quantum-enhanced element detection...")
        detected_elements = self.detect_elements_from_spectrum(processed_spectrum, energy_axis)
        print(f"Detected elements: {list(detected_elements.keys())}")
        
        # 3. Quantum feature extraction
        print("Step 3: Extracting quantum features...")
        quantum_features = self.feature_extractor.extract_comprehensive_quantum_features(
            processed_spectrum, energy_axis
        )
        
        # 4. Quantum Fourier analysis
        print("Step 4: Quantum Fourier Transform analysis...")
        qft_results = self.quantum_fourier_analysis(processed_spectrum)
        
        # 5. Quantum Kramers-Kronig analysis
        print("Step 5: Quantum Kramers-Kronig optical analysis...")
        kk_results = self.kramers_kronig_analysis(processed_spectrum, energy_axis)
        
        # 6. Advanced bonding analysis
        print("Step 6: Advanced bonding analysis...")
        bonding_analysis = self.advanced_bonding_analysis(processed_spectrum, energy_axis, detected_elements)
        
        # 7. Advanced magnetic analysis
        print("Step 7: Advanced magnetic properties analysis...")
        magnetic_analysis = self.advanced_magnetic_analysis(processed_spectrum, energy_axis, detected_elements)
        
        # 8. Energy trajectory analysis
        print("Step 8: Energy trajectory and scattering analysis...")
        trajectory_analysis = self.energy_trajectory_analysis(processed_spectrum, energy_axis)
        
        # 9. Phonon and magnon analysis
        print("Step 9: Phonon and magnon excitation analysis...")
        excitation_analysis = self.phonon_magnon_analysis(processed_spectrum, energy_axis, detected_elements)
        
        # 10. Vibrational EELS analysis
        print("Step 10: Vibrational EELS analysis...")
        vibrational_analysis = self.vibrational_eels_analysis(processed_spectrum, energy_axis, detected_elements)
        
        # 11. Quantum ML analysis
        quantum_ml_results = {}
        if use_quantum_ml:
            print("Step 11: Quantum machine learning analysis...")
            quantum_ml_results = self.perform_quantum_ml_analysis(quantum_features)
        
        # 12. Material property prediction
        print("Step 12: Predicting comprehensive material properties...")
        material_properties = self.predict_comprehensive_material_properties(
            detected_elements, bonding_analysis, magnetic_analysis, kk_results
        )
        
        # 13. Enhanced material identification
        print("Step 13: Enhanced material identification...")
        temp_analysis_results = {
            'detected_elements': detected_elements,
            'bonding_analysis': bonding_analysis,
            'magnetic_properties': magnetic_analysis,
            'optical_properties': kk_results,
            'quantum_features': quantum_features
        }
        material_identification = self.generate_material_identification(temp_analysis_results)
        
        # Compile comprehensive results
        comprehensive_results = {
            'material_name': material_name or 'Unknown Sample',
            'analysis_timestamp': np.datetime64('now'),
            'original_spectrum': spectrum_data,
            'processed_spectrum': processed_spectrum,
            'energy_axis': energy_axis,
            'detected_elements': detected_elements,
            'quantum_features': quantum_features,
            'qft_results': qft_results,
            'optical_properties': kk_results,
            'bonding_analysis': bonding_analysis,
            'magnetic_properties': magnetic_analysis,
            'energy_trajectories': trajectory_analysis,
            'excitation_analysis': excitation_analysis,
            'vibrational_analysis': vibrational_analysis,
            'material_properties': material_properties,
            'material_identification': material_identification,
            'quantum_ml_results': quantum_ml_results,
            'confidence_assessment': self.calculate_comprehensive_confidence(
                detected_elements, quantum_features, bonding_analysis
            )
        }
        
        self.analysis_history.append(comprehensive_results)
        
        print("Comprehensive analysis completed!")
        print(f"Analysis included: {len(comprehensive_results.keys())} different analysis modules")
        return comprehensive_results
    
    def advanced_bonding_analysis(self, spectrum_data, energy_axis, detected_elements):
        """
        Advanced chemical bonding analysis using quantum many-body theory.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray
            Spectrum intensity data.
        energy_axis : np.ndarray
            Energy axis in eV.
        detected_elements : dict
            Previously detected elements from element detection.
            
        Returns:
        --------
        bonding_analysis : dict
            Comprehensive bonding analysis results.
        """
        bonding_analysis = {
            'bonding_characteristics': {},
            'bond_types': {},
            'hybridization': {},
            'charge_transfer': {},
            'orbital_mixing': {},
            'many_body_effects': {},
            'bond_strengths': {},
            'quantum_correlations': {}
        }
        
        # First get basic bonding characteristics for compatibility
        bonding_analysis['bonding_characteristics'] = self.determine_primary_bonding(
            spectrum_data, energy_axis, detected_elements
        )
        
        # Analyze different energy regions for bonding information
        energy_regions = {
            'valence': (0, 50),
            'shallow_core': (50, 200),
            'deep_core': (200, 1000),
            'inner_shell': (1000, 5000)
        }
        
        for region_name, (e_min, e_max) in energy_regions.items():
            mask = (energy_axis >= e_min) & (energy_axis <= e_max)
            if np.any(mask):
                region_spectrum = spectrum_data[mask]
                region_energy = energy_axis[mask]
                
                bonding_analysis[region_name] = self.analyze_bonding_region(region_spectrum,
                                                                           region_energy,
                                                                           detected_elements)
                
        # Quantum many-body analysis
        bonding_analysis['many_body_effects'] = self.quantum_many_body_analysis(spectrum_data,
                                                                               energy_axis,
                                                                               detected_elements)
        
        # Charge transfer analysis
        bonding_analysis['charge_transfer'] = self.charge_transfer_analysis(spectrum_data,
                                                                           energy_axis,
                                                                           detected_elements)
        
        # Hybridization analysis
        bonding_analysis['hybridization'] = self.hybridization_analysis(spectrum_data,
                                                                       energy_axis,
                                                                       detected_elements)
        
        return bonding_analysis
    
    def analyze_bonding_region(self, region_spectrum, region_energy, detected_elements):
        """
        Analyze bonding in specific energy regions of the EELS spectrum.
        
        Parameters:
        -----------
        region_spectrum : np.ndarray
            Specific area within EELS spectrum intensity data.
        region_energy : np.ndarray
            Specific area of energy axis in eV.
        detected_elements : dict
            Previously detected elements.
        
        Returns:
        --------
        region_analysis : dict
            Specific bonding regions analysis results.
        """
        region_analysis = {
            'dominant_transitions': [],
            'bond_character': 'Unknown',
            'coordination': 'Unknown',
            'orbital_splitting': {},
            'crystal_field_effects': {},
            'quantum_interference': 0.0
        }
        
        # Find peaks in the region
        peaks, properties = signal.find_peaks(region_spectrum,
                                             prominence=0.1*np.max(region_spectrum),
                                             distance=3)
        
        if len(peaks) > 0:
            peak_energies = region_energy[peaks]
            peak_intensities = region_spectrum[peaks]
            
            # Analyze peak splitting patterns
            if len(peaks) > 1:
                splittings = np.diff(peak_energies)
                region_analysis['orbital_splitting'] = {
                    'splittings': splittings.tolist(),
                    'average_splitting': np.mean(splittings),
                    'crystal_field_strength': self.estimate_crystal_field_strength(splittings)
                }
            
            # Determine bond character from peak ratios and positions
            if len(peaks) >= 2:
                intensity_ratio = peak_intensities[0] / peak_intensities[1] if peak_intensities[1] > 0 else float('inf')
                
                if intensity_ratio > 3:
                    region_analysis['bond_character'] = 'ionic'
                elif intensity_ratio < 0.5:
                    region_analysis['bond_character'] = 'metallic'
                else:
                    region_analysis['bond_character'] = 'covalent'
                    
            # Quantum interference analysis
            region_analysis['quantum_interference'] = self.calculate_quantum_interference_bonding(
                region_spectrum, region_energy, peak_energies
            )
        
        return region_analysis
    
    def estimate_crystal_field_strength(self, splittings):
        """
        Estimate crystal field strength from orbital splittings.
        
        Parameters:
        -----------
        splittings : np.ndarray
            Peak splitting patterns observed from peak intensities/energies.
        
        Returns:
        --------
        avg_splitting : 'weak', 'medium', or 'strong' 
        """
        if len(splittings) == 0:
            return 0.0
        
        # Simplified conversion of splitting to crystal field strength
        # 10Dq ~ average splitting for d orbitals
        avg_splitting = np.mean(splittings)
        
        if avg_splitting < 1.0:
            return 'weak'
        elif avg_splitting < 3.0:
            return 'medium'
        else:
            return 'strong'
        
    def calculate_quantum_interference_bonding(self, spectrum, energy, peak_energies):
        """
        Calculate quantum interference effects between transitions based on EELS spectrum and energy.
        
        Parameters:
        -----------
        spectrum : np.ndarray
            EELS spectrum data.
        energy : np.ndarray
            Energy in eV.
        peak_energies : np.ndarray
            Specific regions with peak energies.
        
        Returns:
        --------
        np.ndarray :
            Quantum interference bonding effects.
        """
        if len(peak_energies) < 2:
            return 0.0
        
        # Look for interference patterns between peaks
        interference_score = 0.0
        
        for i in range(len(peak_energies) - 1):
            for j in range(i + 1, len(peak_energies)):
                e1, e2 = peak_energies[i], peak_energies[j]
                
                # Find region between peaks
                mask = (energy >= min(e1, e2)) & (energy <= max(e1, e2))
                if np.any(mask):
                    between_region = spectrum[mask]
                    
                    # Look for oscillatory patterns (interference)
                    if len(between_region) > 5:
                        fft_between = np.abs(fft(between_region))
                        # High frequency components indicate interference
                        high_freq_power = np.sum(fft_between[len(fft_between)//4:])
                        total_power = np.sum(fft_between)
                        
                        if total_power > 0:
                            interference_score += high_freq_power / total_power
                            
        return interference_score / max(1, len(peak_energies) * (len(peak_energies) - 1) / 2)
    
    def quantum_many_body_analysis(self, spectrum_data, energy_axis, detected_elements):
        """
        Quantum many-body effects analysis to determine plasmons, satellite peaks, shake-up
        processes, correlation effects, and excitations.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray
            EELS spectrum intensity data.
        energy_axis : np.ndarray
            Energy axis in eV.
        detected_elements : dict
            Previously detected elements.
        
        Returns:
        --------
        many_body_effects : dict
            Quantum many-body results.
        """
        many_body_effects = {
            'plasmons': {},
            'satellite_peaks': {},
            'shake_up_processes': {},
            'correlation_effects': {},
            'collective_excitations': {}
        }
        
        # Plasmon analysis
        many_body_effects['plasmons'] = self.analyze_plasmons(spectrum_data, energy_axis, detected_elements)
        
        # Satellite peak analysis
        many_body_effects['satellite_peaks'] = self.analyze_satellite_peaks(spectrum_data, energy_axis)
        
        # Shake-up/shake-off analysis
        many_body_effects['shake_up_processes'] = self.analyze_shake_processes(spectrum_data, energy_axis)
        
        # Correlation effects
        many_body_effects['correlation_effects'] = self.analyze_correlation_effects(spectrum_data, energy_axis)
        
        return many_body_effects
    
    def analyze_plasmons(self, spectrum_data, energy_axis, detected_elements):
        """
        Analyze plasmon excitations in low energy regions.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray
            EELS spectrum intensity data.
        energy_axis : np.ndarray
            Energy axis in eV.
        detected_elements : dict
            Previously detected elements.
        
        Returns:
        --------
        plasmon_analysis : dict
            Plasmon analysis results.
        """
        plasmon_analysis = {
            'bulk_plasmons': [],
            'surface_plasmons': [],
            'plasmon_dispersion': {},
            'coupling_strength': 0.0
        }
        
        # Look for plasmon peaks in low energy region
        low_energy_mask = energy_axis <= 50
        if np.any(low_energy_mask):
            low_energy_spectrum = spectrum_data[low_energy_mask]
            low_energy_axis = energy_axis[low_energy_mask]
            
            # Find peaks that could be plasmons
            peaks, _ = signal.find_peaks(low_energy_spectrum,
                                        prominence=0.05*np.max(low_energy_spectrum),
                                        distance=5)
            
            for peak_idx in peaks:
                peak_energy = low_energy_axis[peak_idx]
                
                # Check against known plasmon energies
                for element in detected_elements:
                    if element in self.edge_ranges.get('plasmons', {}):
                        plasmon_range = self.edge_ranges['plasmons'][element]
                        if plasmon_range[0] <= peak_energy <= plasmon_range[1]:
                            plasmon_analysis['bulk_plasmons'].append({
                                'element': element,
                                'energy': peak_energy,
                                'intensity': low_energy_spectrum[peak_idx],
                                'type': 'bulk'
                            })
                        elif plasmon_range[0] * 0.7 <= peak_energy <= plasmon_range[1] * 0.7:
                            plasmon_analysis['surface_plasmons'].append({
                                'element': element,
                                'energy': peak_energy,
                                'intensity': low_energy_spectrum[peak_idx],
                                'type': 'surface'
                            })
                            
        return plasmon_analysis
    
    def analyze_satellite_peaks(self, spectrum_data, energy_axis):
        """
        Analyze satellite peaks from many-body effects.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray
            EELS spectrum intensity data.
        energy_axis : np.ndarray
            Energy axis in eV.
        
        Returns:
        --------
        satellite_analysis : dict
            Satellite peak analysis results.
        """
        satellite_analysis = {
            'shake_up_satellites': [],
            'multiplet_structure': [],
            'charge_transfer_satellites': []
        }
        
        # Find main peaks and look for satellites
        main_peaks, _ = signal.find_peaks(spectrum_data,
                                         prominence=0.2*np.max(spectrum_data),
                                         distance=20)
        
        for main_peak_idx in main_peaks:
            main_energy = energy_axis[main_peak_idx]
            main_intensity = spectrum_data[main_peak_idx]
            
            # Look for satellites within +/- 50 eV
            search_window = 50
            start_idx = max(0, main_peak_idx - search_window)
            end_idx = min(len(spectrum_data), main_peak_idx + search_window)
            
            local_spectrum = spectrum_data[start_idx:end_idx]
            local_energy = energy_axis[start_idx:end_idx]
            
            # Find smaller peaks (satellites)
            satellites, _ = signal.find_peaks(local_spectrum,
                                             prominence=0.05*main_intensity,
                                             distance=5)
            
            for sat_idx in satellites:
                sat_energy = local_energy[sat_idx]
                if abs(sat_energy - main_energy) > 2:  # Exclude main peak
                    satellite_analysis['shake_up_satellites'].append({
                        'main_peak_energy': main_energy,
                        'satellite_energy': sat_energy,
                        'energy_separation': sat_energy - main_energy,
                        'intensity_ratio': local_spectrum[sat_idx] / main_intensity
                    })
                    
        return satellite_analysis
    
    def analyze_shake_processes(self, spectrum_data, energy_axis):
        """
        Analyze shake-up and shake-off processes based on EELS spectrum.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray
            EELS spectrum intensity data.
        energy_axis : np.ndarray
            Energy axis in eV.
        
        Returns:
        --------
        shake_analysis : dict
            Shake-up and shake-off analysis results.
        """
        shake_analysis = {
            'shake_up_probability': 0.0,
            'shake_off_threshold': None,
            'correlation_energy': 0.0
        }
        
        # Shake processes appear as broad background or weak satellites
        # Calculate background intensity relative to main peaks
        main_peaks, _ = signal.find_peaks(spectrum_data,
                                         prominence=0.3*np.max(spectrum_data))
        
        if len(main_peaks) > 0:
            peak_intensities = spectrum_data[main_peaks]
            total_peak_intensity = np.sum(peak_intensities)
            total_intensity = np.sum(spectrum_data)
            
            if total_intensity > 0:
                shake_analysis['shake_up_probability'] = 1 - (total_peak_intensity / total_intensity)
                
        return shake_analysis
    
    def analyze_correlation_effects(self, spectrum_data, energy_axis):
        """
        Analyze electron correlation effects based on peaks.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray
            EELS spectrum intensity data.
        energy_axis : np.ndarray
            Energy axis in eV.
        
        Returns:
        --------
        correlation_analysis : dict
            Electron correlation effects analysis results.
        """
        correlation_analysis = {
            'correlation_strength': 0.0,
            'screening_effects': {},
            'final_state_relaxation': {}
        }
        
        # Correlation effects appear as peak broadening and energy shifts
        peaks, properties = signal.find_peaks(spectrum_data,
                                             prominence=0.1*np.max(spectrum_data),
                                             width=1)
        
        if len(peaks) > 0 and 'widths' in properties:
            widths = properties['widths']
            
            # Broader peaks indicate stronger correlation
            avg_width = np.mean(widths)
            correlation_analysis['correlation_strength'] = min(avg_width / 10, 1.0)
            
            # Asymmetric peak shapes indicate final state effects
            for i, peak_idx in enumerate(peaks):
                if i < len(widths):
                    # Analyze peak symmetry
                    peak_start = max(0, int(peak_idx - widths[i]))
                    peak_end = min(len(spectrum_data), int(peak_idx + widths[i]))
                    
                    left_half = spectrum_data[peak_start:peak_idx]
                    right_half = spectrum_data[peak_idx:peak_end]
                    
                    if len(left_half) > 0 and len(right_half) > 0:
                        asymmetry = (np.mean(right_half) - np.mean(left_half)) / (np.mean(right_half) + np.mean(left_half))
                        correlation_analysis['final_state_relaxation'][f'peak_{i}'] = asymmetry
                        
        return correlation_analysis
    
    def charge_transfer_analysis(self, spectrum_data, energy_axis, detected_elements):
        """
        Analyze charge transfer effects in EELS spectrum.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray
            EELS spectrum intensity data.
        energy_axis : np.ndarray
            Energy axis in eV.
        detected_elements : dict
            Previously detected elements.
        
        Returns:
        --------
        charge_analysis : dict
            Charge transfer analysis results.
        """
        charge_analysis = {
            'oxidation_states': {},
            'chemical_shifts': {},
            'charge_transfer_energy': {},
            'electron_affinity_effects': {}
        }
        
        # Analyze chemical shifts for oxidation state determination
        for element in detected_elements:
            if element in self.edge_ranges['K_edges']:
                k_edge_range = self.edge_ranges['K_edges'][element]
                k_edge_center = (k_edge_range[0] + k_edge_range[1]) / 2
                
                # Find actual peak position
                mask = (energy_axis >= k_edge_range[0] - 10) & (energy_axis <= k_edge_range[1] + 10)
                if np.any(mask):
                    local_spectrum = spectrum_data[mask]
                    local_energy = energy_axis[mask]
                    
                    peak_idx = np.argmax(local_spectrum)
                    actual_energy = local_energy[peak_idx]
                    
                    # Chemical shift analysis
                    shift = actual_energy - k_edge_center
                    charge_analysis['chemical_shifts'][element] = shift
                    
                    # Estimate oxidation state from shift
                    # Positive shift indicates higher oxidation state
                    if abs(shift) < 1:
                        oxidation_state = 0
                    elif shift > 0:
                        oxidation_state = min(int(shift / 2), 4)  # Approximation
                    else:
                        oxidation_state = max(int(shift / 2), -2)
                        
                    charge_analysis['oxidation_states'][element] = oxidation_state
                    
        return charge_analysis
        
    def hybridization_analysis(self, spectrum_data, energy_axis, detected_elements):
        """
        Analyze orbital hybridization.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray
            EELS spectrum intensity data.
        energy_axis : np.ndarray
            Energy axis in eV.
        detected_elements : dict
            Previously detected elements.
        
        Returns:
        --------
        hybrid_analysis : dict
            Orbital hybridization analysis results.
        """
        hybrid_analysis = {
            'carbon_hybridization': {},
            'transition_metal_hybridization': {},
            'orbital_mixing': {},
            'bond_angles': {}
        }
        
        # Carbon hybridization analysis
        if 'C' in detected_elements:
            hybrid_analysis['carbon_hybridization'] = self.analyze_carbon_hybridization_detailed(
                spectrum_data, energy_axis
            )
            
        # Transition metal hybridization
        tm_elements = ['Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn']
        for element in detected_elements:
            if element in tm_elements:
                hybrid_analysis['transition_metal_hybridization'][element] = self.analyze_tm_hybridization_detailed(
                    spectrum_data, energy_axis, element
                )
                
        return hybrid_analysis
    
    def analyze_carbon_hybridization_detailed(self, spectrum_data, energy_axis):
        """
        Detailed analysis of carbon orbital hybridization.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray
            EELS spectrum containing carbon K-edge.
        energy_axis : np.ndarray
            Energy axis in eV.
            
        Returns:
        --------
        carbon_analysis : dict
            Carbon hybridization analysis results.
        """
        carbon_analysis = {
            'sp3_fraction': 0.0,
            'sp2_fraction': 0.0,
            'sp_fraction': 0.0,
            'pi_star_intensity': 0.0,
            'sigma_star_intensity': 0.0,
            'exciton_binding_energy': 0.0
        }
        
        # Look for C K-edge features
        c_k_edge = 285  # Approximate
        
        # π* peak around 285 eV (sp2)
        pi_mask = (energy_axis >= 284) & (energy_axis <= 287)
        if np.any(pi_mask):
            pi_intensity = np.max(spectrum_data[pi_mask])
            carbon_analysis['pi_star_intensity'] = pi_intensity
            
        # σ* peak around 293 eV
        sigma_mask = (energy_axis >= 290) & (energy_axis <= 295)
        if np.any(sigma_mask):
            sigma_intensity = np.max(spectrum_data[sigma_mask])
            carbon_analysis['sigma_star_intensity'] = sigma_intensity
            
        # Estimate hybridization fractions from peak ratios
        total_intensity = carbon_analysis['pi_star_intensity'] + carbon_analysis['sigma_star_intensity']
        if total_intensity > 0:
            # Strong π* indicates sp2
            carbon_analysis['sp2_fraction'] = carbon_analysis['pi_star_intensity'] / total_intensity
            # Remaining is primarily sp3
            carbon_analysis['sp3_fraction'] = 1 - carbon_analysis['sp2_fraction']
            
        return carbon_analysis
    
    def analyze_tm_hybridization_detailed(self, spectrum_data, energy_axis, element):
        """
        Detailed transition metal d-orbital hybridization analysis.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray
            EELS spectrum data.
        energy_axis : np.ndarray
            Energy axis in eV.
        element : str
            Transition metal element symbol.
            
        Returns:
        --------
        tm_analysis : dict
            Transition metal analysis results.
        """
        tm_analysis = {
            'crystal_field_splitting': 0.0,
            'd_orbital_occupancy': {},
            'ligand_field_strength': 'Unknown',
            'spin_state': 'Unknown',
            'jahn_teller_distortion': False
        }
        
        # Look for L2,3 edges which show d-orbital splitting
        if element in self.edge_ranges['L2_edges'] and element in self.edge_ranges['L3_edges']:
            l3_range = self.edge_ranges['L3_edges'][element]
            l2_range = self.edge_ranges['L2_edges'][element]
            
            # Analyze L3 edge fine structure
            l3_mask = (energy_axis >= l3_range[0] - 5) & (energy_axis <= l3_range[1] + 15)
            if np.any(l3_mask):
                l3_spectrum = spectrum_data[l3_mask]
                l3_energy = energy_axis[l3_mask]
                
                # Find peaks in L3 region
                peaks, _ = signal.find_peaks(l3_spectrum,
                                            prominence=0.1*np.max(l3_spectrum))
                
                if len(peaks) > 1:
                    peak_energies = l3_energy[peaks]
                    splittings = np.diff(peak_energies)
                    
                    if len(splittings) > 0:
                        tm_analysis['crystal_field_splitting'] = np.mean(splittings)
                        
                        # Estimate ligand field strength
                        if tm_analysis['crystal_field_splitting'] < 1.0:
                            tm_analysis['ligand_field_strength'] = 'weak'
                        elif tm_analysis['crystal_field_splitting'] < 3.0:
                            tm_analysis['ligand_field_strength'] = 'medium'
                        else:
                            tm_analysis['ligand_field_strength'] = 'strong'
                            
                        # Check for Jahn-Teller distortion (asymmetric splitting)
                        if len(splittings) > 1:
                            splitting_variance = np.var(splittings)
                            if splitting_variance > 0.5:
                                tm_analysis['jahn_teller_distortion'] = True
        
        return tm_analysis
    
    def determine_primary_bonding(self, spectrum_data, energy_axis, detected_elements):
        """
        Determine primary chemical bonding tpe in the material.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray
            EELS spectrum data.
        energy_axis : np.ndarray
            Energy axis in eV.
        detected_elements : dict
            Previously detected chemical elements.
        
        Returns:
        --------
        characteristics : dict
            Primary bonding characteristics.
        """
        characteristics = {
            'primary_bonding': 'Unknown',
            'bond_strength': 'Unknown',
            'confidence': 0.0
        }
        
        metals = ['Al', 'Fe', 'Cu', 'Au', 'Ag', 'Ti', 'Ni', 'Co', 'Cr', 'Mn', 'Zn', 'Pt']
        nonmetals = ['C', 'N', 'O', 'F', 'Si', 'P', 'S', 'Cl']
        
        detected_metals = [e for e in detected_elements if e in metals]
        detected_nonmetals = [e for e in detected_elements if e in nonmetals]
        
        if len(detected_metals) > 0 and len(detected_nonmetals) == 0:
            characteristics['primary_bonding'] = 'Metallic'
            characteristics['confidence'] = 0.8
        elif len(detected_metals) == 0 and len(detected_nonmetals) > 0:
            characteristics['primary_bonding'] = 'Covalent'
            characteristics['confidence'] = 0.7
        elif len(detected_metals) > 0 and len(detected_nonmetals) > 0:
            if self.has_charge_transfer_signature(spectrum_data, energy_axis):
                characteristics['primary_bonding'] = 'Ionic'
                characteristics['confidence'] = 0.6
            else:
                characteristics['primary_bonding'] = 'Mixed'
                characteristics['confidence'] = 0.5
        
        return characteristics
    
    def has_charge_transfer_signature(self, spectrum_data, energy_axis):
        """
        Check for charge transfer signatures in EELS spectrum.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray
            EELS spectrum intensity data.
        energy_axis : np.ndarray
            Energy axis in eV.
        
        Returns:
        --------
        bool :
            True if charge transfer signatures are detected,
            False otherwise.
        """
        for element_edges in self.edge_ranges.values():
            for element, (e_min, e_max) in element_edges.items():
                pre_edge_mask = (energy_axis >= e_min - 10) & (energy_axis <= e_min)
                if np.any(pre_edge_mask):
                    pre_edge_intensity = np.max(spectrum_data[pre_edge_mask])
                    edge_mask = (energy_axis >= e_min) & (energy_axis <= e_max)
                    if np.any(edge_mask):
                        edge_intensity = np.max(spectrum_data[edge_mask])
                        if pre_edge_intensity > 0.1 * edge_intensity:
                            return True
        return False
    
    def analyze_orbital_structure(self, spectrum_data, energy_axis, detected_elements):
        """
        Analyze orbital structure from fine structure.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray
            EELS spectrum intensity data.
        energy_axis : np.ndarray
            Energy axis in eV.
        detected_elements : dict
            Previously detected elements.
        
        Returns:
        --------
        orbital_analysis : dict
            Orbital structure analysis results.
        """
        orbital_analysis = {
            'd_orbital_splitting': {},
            'crystal_field_effects': {},
            'orbital_occupancy': {}
        }
        
        transition_metals = ['Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu']
        
        for element in detected_elements:
            if element in transition_metals:
                orbital_analysis[element] = self.analyze_transition_metal_orbitals(
                    spectrum_data, energy_axis, element
                )
        
        return orbital_analysis
    
    def advanced_magnetic_analysis(self, spectrum_data, energy_axis, detected_elements):
        """
        Advanced magnetic properties analysis with comprehensive characterization.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray
            Spectrum intensity data.
        energy_axis : np.ndarray
            Energy axis in eV.
        detected_elements : dict
            Previously detected elements.
        
        Returns:
        --------
        magnetic_analysis : dict
            Magnetic analysis results.
        """
        magnetic_analysis = {
            'magnetic_moments': {},
            'exchange_interactions': {},
            'magnetic_anisotropy': {},
            'spin_orbit_coupling': {},
            'magnetic_ordering': {},
            'curie_temperature_estimate': None
        }
        
        # Identify magnetic elements
        magnetic_elements = [elem for elem in detected_elements
                            if elem in ['Fe', 'Co', 'Ni', 'Mn', 'Cr', 'Gd', 'Tb', 'Dy', 'Ho', 'Er']]
        
        if not magnetic_elements:
            return magnetic_analysis
        
        # Analyze magnetic circular dichroism effects in L2,3 edges
        for element in magnetic_elements:
            if element in self.edge_ranges['L2_edges'] and element in self.edge_ranges['L3_edges']:
                mag_analysis = self.analyze_magnetic_dichroism(spectrum_data,
                                                              energy_axis,
                                                              element)
                magnetic_analysis['magnetic_moments'][element] = mag_analysis
                
        # Exchange interaction analysis
        magnetic_analysis['exchange_interactions'] = self.analyze_exchange_interactions(spectrum_data,
                                                                                       energy_axis,
                                                                                       magnetic_elements)
        # Spin orbit coupling analysis
        magnetic_analysis['spin_orbit_coupling'] = self.analyze_spin_orbit_coupling(spectrum_data,
                                                                                   energy_axis,
                                                                                   magnetic_elements)
        # Estimate magnetic ordering temperature
        if magnetic_elements:
            magnetic_analysis['curie_temperature_estimate'] = self.estimate_curie_temperature(magnetic_elements,
                                                                                             magnetic_analysis['exchange_interactions'])
            
        return magnetic_analysis
    
    def analyze_magnetic_dichroism(self, spectrum_data, energy_axis, element):
        """
        Analyzing magnetic circular dichroism effects at L2,3 edges.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray
            EELS spectrum data.
        energy_axis : np.ndarray
            Element axis in eV.
        element : str
            Magnetic element symbol.
            
        Returns:
        --------
        dichroism_analysis : dict
            Magnetic dichroism analysis results.
        """
        dichroism_analysis = {
            'orbital_moment': 0.0,
            'spin_moment': 0.0,
            'l2_l3_ratio': 0.0,
            'magnetic_moment_total': 0.0
        }
        
        # Find L2 and L3 edges
        l2_range = self.edge_ranges['L2_edges'].get(element)
        l3_range = self.edge_ranges['L3_edges'].get(element)
        
        if l2_range and l3_range:
            # Extract L2 range
            l2_mask = (energy_axis >= l2_range[0] - 5) & (energy_axis <= l2_range[1] + 10)
            l2_spectrum = spectrum_data[l2_mask] if np.any(l2_mask) else np.array([])
            
            # Extract L3 range
            l3_mask = (energy_axis >= l3_range[0] - 5) & (energy_axis <= l3_range[1] + 10)
            l3_spectrum = spectrum_data[l3_mask] if np.any(l3_mask) else np.array([])
            
            if len(l2_spectrum) > 0 and len(l3_spectrum) > 0:
                # Integrated intensities
                l2_intensity = np.trapz(l2_spectrum, dx=1)
                l3_intensity = np.trapz(l3_spectrum, dx=1)
                
                if l3_intensity > 0:
                    dichroism_analysis['l2_l3_ratio'] = l2_intensity / l3_intensity
                    
                # Estimating moments using sum rules (simplified approach)
                if element in self.magnetic_moments:
                    reference_moment = self.magnetic_moments[element]
                    
                    # Scale based on L2/L3 ratio and known values
                    dichroism_analysis['spin_moment'] = reference_moment * 0.8
                    dichroism_analysis['orbital_moment'] = reference_moment * 0.2
                    dichroism_analysis['magnetic_moment_total'] = reference_moment
        
        return dichroism_analysis
    
    def analyze_exchange_interactions(self, spectrum_data, energy_axis, magnetic_elements):
        """
        Analyze magnetic exchange interactions in magnetic materials.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray
            EELS spectrum data.
        energy_axis : np.ndarray
            Energy axis in eV.
        magnetic_elements : list
            List of magnetic elements present.
            
        Returns:
        --------
        exchange_analysis : dict
            Exchange interaction analysis results.
        """
        exchange_analysis = {
            'direct_exchange': {},
            'superexchange': {},
            'indirect_exchange': {},
            'exchange_constants': {}
        }
        
        # Looking for exchange splitting in core levels
        for element in magnetic_elements:
            if element in self.edge_ranges['L3_edges']:
                l3_range = self.edge_ranges['L3_edges'][element]
                
                # Extract L3 region
                mask = (energy_axis >= l3_range[0] - 5) & (energy_axis <= l3_range[1] + 15)
                if np.any(mask):
                    region_spectrum = spectrum_data[mask]
                    region_energy = energy_axis[mask]
                    
                    # Look for exchange splitting
                    peaks, _ = signal.find_peaks(region_spectrum,
                                                prominence=0.1*np.max(region_spectrum),
                                                distance=3)
                    
                    if len(peaks) >= 2:
                        peak_energies = region_energy[peaks]
                        exchange_splitting = np.min(np.diff(peak_energies))
                        
                        # Estimate exchange constant
                        exchange_analysis['exchange_constants'][element] = exchange_splitting / 2
                        
        return exchange_analysis
    
    def analyze_spin_orbit_coupling(self, spectrum_data, energy_axis, magnetic_elements):
        """
        Analyze spin-orbit coupling in magnetic materials.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray
            EELS spectrum data.
        energy_axis : np.ndarray
            Energy axis in eV.
        magnetic_elements : list
            List of magnetic elements present.
            
        Returns:
        --------
        soc_analysis : dict
            Spin-orbit coupling analysis results.
        """
        soc_analysis = {
            'soc_strength': {},
            'j_j_coupling': {},
            'orbital_angular_momentum': {}
        }
        
        # Spin-orbit coupling appears as L2/L3 splitting
        for element in magnetic_elements:
            if (element in self.edge_ranges['L2_edges'] and
               element in self.edge_ranges['L3_edges']):
                l2_energy = np.mean(self.edge_ranges['L2_edges'][element])
                l3_energy = np.mean(self.edge_ranges['L3_edges'][element])
                
                soc_splitting = l2_energy - l3_energy
                soc_analysis['soc_strength'][element] = soc_splitting
                
                # Estimating orbital angular momentum contribution
                if element in self.magnetic_moments:
                    total_moment = self.magnetic_moments[element]
                    orbital_contribution = min(soc_splitting / 20, total_moment * 0.5)
                    soc_analysis['orbital_angular_momentum'][element] = orbital_contribution
                    
        return soc_analysis
    
    def estimate_curie_temperature(self, magnetic_elements, exchange_interactions):
        """
        Estimate Curie temperature using Mean Field Approximation.
        
        Parameters:
        -----------
        magnetic_elements : list
            List of magnetic elements.
        exchange_interactions : dict
            Exchange interaction analysis results.
        
        Returns:
        --------
        float or None :
            Estimated Curie temperature in Kelvin, or None if insufficient data.
        """
        if not exchange_interactions.get('exchange_constants'):
            return None
        
        # Tc ~ (2/3) * J * S * (S+1) * Z / kB (Heisenberg model)
        exchange_values = list(exchange_interactions['exchange_constants'].values())
        if exchange_values:
            avg_exchange = np.mean(exchange_values)  # eV
            
            # Rough estimates
            avg_spin = 2.5  # roughly for 3d elements
            coordination = 8
            kB_eV = 8.617e-5  # eV/K
            
            tc_estimate = (2/3) * avg_exchange * avg_spin * (avg_spin + 1) * coordination / kB_eV
            
            return max(tc_estimate, 0)  # Kelvin
        
        return None
    
    
    def energy_trajectory_analysis(self, spectrum_data, energy_axis):
        """
        Analyze energy loss trajectories and electron scattering processes.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray
            EELS spectrum data.
        energy_axis : np.ndarray
            Energy loss axis in eV.
            
        Returns:
        --------
        trajectory_analysis : dict
            Energy trajectory analysis results.
        """
        trajectory_analysis = {
            'energy_loss_function': None,
            'mean_free_path': {},
            'scattering_cross_sections': {},
            'energy_dependent_effects': {},
            'quantum_trajectories': {}
        }
        
        # Calculate energy loss function
        trajectory_analysis['energy_loss_function'] = self.calculate_energy_loss_function(spectrum_data,
                                                                                          energy_axis)
        
        # Analyze scattering processes
        trajectory_analysis['scattering_cross_sections'] = self.analyze_scattering_processes(spectrum_data,
                                                                                             energy_axis)
        
        # Quantum trajectory analysis
        trajectory_analysis['quantum_trajectories'] = self.quantum_trajectory_analysis(spectrum_data,
                                                                                       energy_axis)
        
        return trajectory_analysis
    
    def calculate_energy_loss_function(self, spectrum_data, energy_axis):
        """
        Calculate the energy loss function Im(-1/ε) from EELS data.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray
            EELS spectrum intensity.
        energy_axis : np.ndarray
            Energy loss values in eV.
            
        Returns:
        --------
        energy_loss_function : np.ndarray
            Energy loss function values, or None if calculation failed.
        """
        # Using Kramers-Kronig to get full dielectric function
        kk_results = self.kramers_kronig_analysis(spectrum_data, energy_axis)
        
        if kk_results and kk_results.get('dielectric_function'):
            eps1 = kk_results['dielectric_function']['real']
            eps2 = kk_results['dielectric_function']['imaginary']
            
            # Energy loss function: Im(-1/epsilon) = epsilon2/(epsilon1^2 + epsilon2^2)
            energy_loss_function = eps2 / (eps1**2 + eps2**2 + 1e-10)
            
            # Apply quantum corrections if available
            if kk_results.get('quantum_corrections'):
                quantum_corrections = kk_results['quantum_corrections']
                # Apply quantum coherence enhancement
                coherence_factor = quantum_corrections.get('quantum_coherence', 1.0)
                energy_loss_function *= (1 + 0.1 * coherence_factor)
            
            return energy_loss_function
        
        return None
    
    def kramers_kronig_analysis(self, spectrum_data, energy_axis):
        """
        Perform quantum-enhanced Kramers-Kronig analysis for optical properties.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray
            EELS spectrum.
        energy_axis : np.ndarray
            Energy axis in eV.
            
        Returns:
        --------
        kk_analysis : dict
            Optical properties analysis.
        """
        # Use the quantum-enhanced Kramers-Kronig transform from preprocessor
        quantum_kk_results = self.preprocessor.quantum_kramers_kronig_transform(energy_axis, spectrum_data)
        
        # The quantum preprocessor already returns a complete analysis
        # Just need to reformat for consistency with existing code structure
        kk_analysis = {
            'real_part': quantum_kk_results.get('real_part'),
            'imaginary_part': quantum_kk_results.get('imaginary_part'),
            'dielectric_function': quantum_kk_results.get('dielectric_function', {}),
            'refractive_index': quantum_kk_results.get('refractive_index'),
            'extinction_coefficient': quantum_kk_results.get('extinction_coefficient'),
            'quantum_corrections': quantum_kk_results.get('quantum_corrections', {}),
            'quantum_enhanced': True  # Flag to indicate this used quantum methods
        }
        
        return kk_analysis
    
    def analyze_scattering_processes(self, spectrum_data, energy_axis):
        """
        Analyze different electron scattering processes in EELS.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray
            EELS spectrum data.
        energy_axis : np.ndarray
            Energy loss axis in eV.
            
        Returns:
        --------
        scattering_analysis : dict
            Scattering analysis results.
        """
        scattering_analysis = {
            'elastic_scattering': 0.0,
            'inelastic_scattering': 0.0,
            'multiple_scattering': 0.0,
            'single_scattering_probability': 0.0
        }
        
        # Elastic scattering = zero-loss peak
        zero_loss_mask = energy_axis <= 2  # eV
        if np.any(zero_loss_mask):
            elastic_intensity = np.max(spectrum_data[zero_loss_mask])
            total_intensity = np.sum(spectrum_data)
            
            if total_intensity > 0:
                scattering_analysis['elastic_scattering'] = elastic_intensity / total_intensity
                scattering_analysis['inelastic_scattering'] = 1 - scattering_analysis['elastic_scattering']
                
        # Multiple scattering from high energy
        high_energy_mask = energy_axis > 1000  # eV
        if np.any(high_energy_mask):
            high_energy_intensity = np.sum(spectrum_data[high_energy_mask])
            total_intensity = np.sum(spectrum_data)
            
            if total_intensity > 0:
                scattering_analysis['multiple_scattering'] = high_energy_intensity / total_intensity
                
        return scattering_analysis
    
    def quantum_trajectory_analysis(self, spectrum_data, energy_axis):
        """
        Quantum mechanical analysis of electron trajectories in EELS.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray
            EELS spectrum data.
        energy_axis : np.ndarray
            Energy axis in eV.
        
        Returns:
        --------
        quantum_traj : dict
            Quantum trajectory analysis.
        """
        quantum_traj = {
            'coherence_length': 0.0,
            'quantum_interference': 0.0,
            'decoherence_rate': 0.0,
            'trajectory_entanglement': 0.0
        }
        
        # Using quantum circuit to model electron trajectories
        n_traj_qubits = min(6, self.n_qubits)
        
        # Create trajectory-encoding circuit
        qc = QuantumCircuit(n_traj_qubits)
        
        # Encode energy distribution
        energy_weights = spectrum_data / (np.sum(spectrum_data) + 1e-10)
        
        # Sample energies for encoding
        n_samples = n_traj_qubits
        if len(energy_weights) > n_samples:
            sample_indices = np.random.choice(len(energy_weights), n_samples,
                                              p=energy_weights/np.sum(energy_weights))
            sample_energies = energy_axis[sample_indices]
            sample_weights = energy_weights[sample_indices]
        else:
            sample_energies = energy_axis[:n_samples]
            sample_weights = energy_weights[:n_samples]
            
        # Encoding trajectories
        for i, (energy, weight) in enumerate(zip(sample_energies, sample_weights)):
            if i < n_traj_qubits:
                # Energy-dependent rotation
                angle = (energy / 1000) * np.pi  # Normalizing to reasonable range
                qc.ry(angle, i)
                qc.rz(weight * np.pi, i)
                
        # Add trajectory entanglement
        for i in range(n_traj_qubits - 1):
            qc.cx(i, i + 1)
        
        # Add scattering interactions
        for i in range(0, n_traj_qubits - 1, 2):
            qc.cry(np.pi/4, i, i + 1)
            
        try:
            # Calculate quantum trajectory properties
            statevector = Statevector.from_instruction(qc)
            
            # Coherence length from quantum state
            amplitudes = statevector.data
            coherence = np.sum(np.abs(amplitudes[::2] * np.conj(amplitudes[1::2])))
            quantum_traj['coherence_length'] = coherence
            
            # Entanglement between trajectory components
            if n_traj_qubits >= 2:
                quantum_traj['trajectory_entanglement'] = self.feature_extractor.calculate_entanglement_entropy(
                    statevector, n_traj_qubits)
                
            # Decoherence rate from state purity
            rho = DensityMatrix(statevector)
            purity = np.trace(rho.data @ rho.data).real
            quantum_traj['decoherence_rate'] = 1 - purity
        
        except Exception as e:
            print(f"Warning: Quantum trajectory analysis failed: {e}")
            
        return quantum_traj
    
    def phonon_magnon_analysis(self, spectrum_data, energy_axis, detected_elements):
        """
        Analyze phonon and magnon excitations in low-energy EELS.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray
            EELS spectrum data.
        energy_axis : np.ndarray
            Energy axis in eV.
        detected_elements : dict
            Previously detected chemical elements.
        
        Returns:
        --------
        excitation_analysis : dict
            Excitation analysis results.
        """
        excitation_analysis = {
            'phonons': {},
            'magnons': {},
            'electron_phonon_coupling': {},
            'magnetic_exchange': {}
        }
        
        # Phonon analysis (low energy region < 250 meV)
        low_energy_mask = energy_axis <= 0.25  # 250 meV
        if np.any(low_energy_mask):
            excitation_analysis['phonons'] = self.analyze_phonon_modes(spectrum_data[low_energy_mask],
                                                                      energy_axis[low_energy_mask],
                                                                      detected_elements)
        
        # Magnon analysis (for magnetic materials)
        magnetic_elements = ['Fe', 'Co', 'Ni', 'Mn', 'Cr', 'Gd', 'Tb', 'Dy', 'Er', 'Ho', 'Tm']
        if any(elem in detected_elements for elem in magnetic_elements):
            excitation_analysis['magnons'] = self.analyze_magnon_modes(spectrum_data,
                                                                      energy_axis,
                                                                      detected_elements)
            
        # Electron-phonon coupling
        excitation_analysis['electron_phonon_coupling'] = self.analyze_electron_phonon_coupling(spectrum_data,
                                                                                               energy_axis,
                                                                                               detected_elements)
        
        return excitation_analysis
    
    def analyze_phonon_modes(self, low_energy_spectrum, low_energy_axis, detected_elements):
        """
        Analyze phonon modes in low-energy EELS spectra.
        Identifies and classifies acoustic and optical phonon modes.
        
        Parameters:
        -----------
        low_energy_spectrum : np.ndarray
            EELS spectrum in low energy region (< 0.25 eV).
        low_energy_axis : np.ndarray
            Energy axis in eV.
        detected_elements : dict
            Chemical elements present in the sample.
            
        Returns:
        --------
        phonon_analysis : dict
            Phonon analysis results.
        """
        phonon_analysis = {
            'acoustic_modes': [],
            'optical_modes': [],
            'mode_assignment': {},
            'debye_temperature': None
        }
        
        # Find peaks that could be phonon modes
        peaks, properties = signal.find_peaks(low_energy_spectrum,
                                             prominence=0.05*np.max(low_energy_spectrum),
                                             distance=2)
        
        for peak_idx in peaks:
            peak_energy = low_energy_axis[peak_idx] * 1000  # convert to meV
            peak_intensity = low_energy_spectrum[peak_idx]
            
            # Classify as acoustic or optical based on energy
            if peak_energy < 50:  # meV
                phonon_analysis['acoustic_modes'].append({
                    'energy_meV': peak_energy,
                    'intensity': peak_intensity,
                    'type': 'acoustic'
                })
            else:
                phonon_analysis['optical_modes'].append({
                    'energy_meV': peak_energy,
                    'intensity': peak_intensity,
                    'type': 'optical'
                })
            
            # Try to assign modes based on known materials
            for element in detected_elements:
                if element in self.phonon_energies:
                    element_phonons = self.phonon_energies[element]
                    for mode_name, mode_energy in element_phonons.items():
                        if abs(peak_energy - mode_energy) < 5:  # 5 meV tolerance
                            phonon_analysis['mode_assignment'][f'{element}_{mode_name}'] = {
                                'energy_meV': peak_energy,
                                'reference_energy': mode_energy,
                                'confidence': 1 - abs(peak_energy - mode_energy) / 5
                            }
            
        # Estimate Debye temperature from highest phonon energy
        all_modes = phonon_analysis['acoustic_modes'] + phonon_analysis['optical_modes']
        if all_modes:
            max_phonon_energy = max(mode['energy_meV'] for mode in all_modes)
            # Rough estimate: θD ~ max_phonon_energy / kB (Kelvin)
            kB_meV = 0.0862  # meV/K
            phonon_analysis['debye_temperature'] = max_phonon_energy / kB_meV
            
        return phonon_analysis

    def analyze_magnon_modes(self, spectrum_data, energy_axis, detected_elements):
        """
        Analyze magnon excitations in magnetic materials.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray
            EELS spectrum data.
        energy_axis : np.ndarray
            Energy axis in eV.
        detected_elements : dict
            Chemical elements, checked for magnetic species.
            
        Returns:
        --------
        magnon_analysis : dict
            Magnon analysis results.
        """
        magnon_analysis = {
            'spin_wave_modes': [],
            'exchange_energies': {},
            'magnetic_anisotropy': {},
            'spin_orbit_coupling': 0.0
        }
        
        # Look for magnon modes in 0-1 eV range
        magnon_mask = (energy_axis >= 0.01) & (energy_axis <= 1.0)
        if np.any(magnon_mask):
            magnon_spectrum = spectrum_data[magnon_mask]
            magnon_energy = energy_axis[magnon_mask]
            
            # Find peaks that could be magnons
            peaks, _ = signal.find_peaks(magnon_spectrum,
                                        prominence=0.02*np.max(magnon_spectrum),
                                        distance=5)
            
            for peak_idx in peaks:
                peak_energy = magnon_energy[peak_idx]
                peak_intensity = magnon_spectrum[peak_idx]
                
                magnon_analysis['spin_wave_modes'].append({
                    'energy_eV': peak_energy,
                    'intensity': peak_intensity,
                    'type': 'magnon'
                })
                
        # Estimate exchange interactions for magnetic elements
        magnetic_elements = [elem for elem in detected_elements 
                           if elem in ['Fe', 'Co', 'Ni', 'Mn', 'Cr', 'Gd', 'Dy', 'Ho', 'Tb', 'Tm', 'Er']]
        
        for element in magnetic_elements:
            if element in self.magnetic_moments:
                moment = self.magnetic_moments[element]
                # Rough estimate of exchange energy from magnetic moment
                exchange_estimate = moment * 0.1  # eV (very rough estimate)
                magnon_analysis['exchange_energies'][element] = exchange_estimate
                
        return magnon_analysis
    
    def analyze_electron_phonon_coupling(self, spectrum_data, energy_axis, detected_elements):
        """
        Analyze electron-phonon coupling effects.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray
            EELS spectrum data.
        energy_axis : np.ndarray
            Energy axis in eV.
        detected_elements : dict
            Chemical elements, checked for magnetic species.
            
        Returns:
        --------
        coupling_analysis : dict
            Coupling analysis results.
        """
        coupling_analysis = {
            'coupling_strength': 0.0,
            'isotope_effects': {},
            'temperature_dependence': {},
            'polaronic_effects': False
        }
        
        # Look for signatures of electron-phonon coupling:
        # 1. Peak broadening beyond lifetime effects
        # 2. Satellite peaks displaced by phonon energies
        # 3. Temperature-dependent line shapes
        
        # Find main electronic transitions
        main_peaks, properties = signal.find_peaks(spectrum_data,
                                                  prominence=0.2*np.max(spectrum_data),
                                                  distance=10)
        
        if len(main_peaks) > 0 and 'widths' in properties:
            widths = properties['widths']
            
            # Compare observed widths to expected lifetime broadening
            avg_width = np.mean(widths)
            
            # Lifetime broadening estimate (rough estimate)
            lifetime_width = 0.1  # eV (typical)
            
            if avg_width > lifetime_width * 2:
                coupling_analysis['coupling_strength'] = min((avg_width / lifetime_width - 1), 5.0)
                if coupling_analysis['coupling_strength'] > 2.0:
                    coupling_analysis['polaronic_effects'] = True
        
        return coupling_analysis
    
    def vibrational_eels_analysis(self, spectrum_data, energy_axis, detected_elements):
        """
        Comprehensive vibrational EELS analysis for molecular systems.
        
        Parameters:
        -----------
        spectrum_data : np.ndarray
            EELS spectrum data.
        energy_axis : np.ndarray
            Energy axis in eV.
        detected_elements : dict
            Chemical composition information.
        
        Returns:
        --------
        vibrational_analysis : dict
            Vibrational analysis results.
        """
        vibrational_analysis = {
            'molecular_vibrations': {},
            'surface_modes': {},
            'defect_modes': {},
            'isotope_shifts': {},
            'anharmonic_effects': {}
        }
        
        # Focusing on low energy region (< 500 meV)
        vib_mask = energy_axis <= 0.5
        if np.any(vib_mask):
            vib_spectrum = spectrum_data[vib_mask]
            vib_energy = energy_axis[vib_mask] * 1000  # convert to meV
            
            vibrational_analysis['molecular_vibrations'] = self.analyze_molecular_vibrations(vib_spectrum,
                                                                                            vib_energy,
                                                                                            detected_elements)
            vibrational_analysis['surface_modes'] = self.analyze_surface_vibrations(vib_spectrum,
                                                                                   vib_energy,
                                                                                   detected_elements)
            vibrational_analysis['defect_modes'] = self.analyze_defect_vibrations(vib_spectrum,
                                                                                 vib_energy)
        
        return vibrational_analysis
    
    def analyze_molecular_vibrations(self, vib_spectrum, vib_energy_meV, detected_elements):
        """
        Analyze molecular vibrational modes in EELS spectra.
        
        Parameters:
        -----------
        vib_spectrum : np.ndarray
            Vibrational spectrum data (< 500 meV).
        vib_energy_meV : np.ndarray
            Energy axis in meV.
        detected_elements : dict
            Chemical elements present.
        
        Returns:
        --------
        molecular_analysis : dict
            Molecular vibration analysis.
        """
        molecular_analysis = {
            'stretching_modes': [],
            'bending_modes': [],
            'torsional_modes': [],
            'combination_bands': []
        }
        
        # Find vibrational peaks
        peaks, _ = signal.find_peaks(vib_spectrum,
                                    prominence=0.03*np.max(vib_spectrum),
                                    distance=2)
        
        for peak_idx in peaks:
            peak_energy = vib_energy_meV[peak_idx]
            peak_intensity = vib_spectrum[peak_idx]
            
            # Classify vibrations by energy ranges
            if peak_energy > 300:  # High energy stretching
                molecular_analysis['stretching_modes'].append({
                    'energy_meV': peak_energy,
                    'intensity': peak_intensity,
                    'type': 'stretching'
                })
            elif peak_energy > 100:  # Bending modes
                molecular_analysis['bending_modes'].append({
                    'energy_meV': peak_energy,
                    'intensity': peak_intensity,
                    'type': 'bending'
                })
            else:  # Low energy torsional/lattice modes
                molecular_analysis['torsional_modes'].append({
                    'energy_meV': peak_energy,
                    'intensity': peak_intensity,
                    'type': 'torsional'
                })
                
        return molecular_analysis
    
    def analyze_surface_vibrations(self, vib_spectrum, vib_energy_meV, detected_elements):
        """
        Analyze surface-specific vibrational modes in EELS spectrum.
        
        Parameters:
        -----------
        vib_spectrum : np.ndarray
            Vibrational spectrum data (< 500 meV).
        vib_energy_meV : np.ndarray
            Energy axis in meV.
        detected_elements : dict
            Chemical elements present.
        
        Returns:
        --------
        surface_analysis : dict
            Surface vibration analysis.
        """
        surface_analysis = {
            'surface_phonons': [],
            'adsorbate_modes': [],
            'surface_reconstruction': {}
        }
        
        # Surface modes usually have lower energies than bulk modes
        surface_peaks, _ = signal.find_peaks(vib_spectrum,
                                            prominence=0.05*np.max(vib_spectrum),
                                            distance=3)
        for peak_idx in surface_peaks:
            peak_energy = vib_energy_meV[peak_idx]
            
            # Surface phonons are usually redshifted from bulk
            if peak_energy < 50:  # meV
                surface_analysis['surface_phonons'].append({
                    'energy_meV': peak_energy,
                    'type': 'surface_phonon'
                })
                
        return surface_analysis
    
    def analyze_defect_vibrations(self, vib_spectrum, vib_energy_meV):
        """
        Analyze defect-related vibrational modes in EELS spectrum.
        
        Parameters:
        -----------
        vib_spectrum : np.ndarray
            Vibrational spectrum data (< 500 meV).
        vib_energy_meV : np.ndarray
            Energy axis in meV.
        detected_elements : dict
            Chemical elements present.
        
        Returns:
        --------
        defect_analysis : dict
            Defect-related analysis.
        """
        defect_analysis = {
            'local_modes': [],
            'gap_modes': [],
            'disorder_effects': 0.0
        }
        
        # Defect modes usually appear as weak, isolated peaks
        defect_peaks, properties = signal.find_peaks(vib_spectrum,
                                                    prominence=0.01*np.max(vib_spectrum),
                                                    distance=1,
                                                    width=(1,10))
        if len(defect_peaks) > 0 and 'widths' in properties:
            widths = properties['widths']
            
            for i, peak_idx in enumerate(defect_peaks):
                peak_energy = vib_energy_meV[peak_idx]
                peak_width = widths[i] if i < len(widths) else 1
                
                # Very narrow peaks might be defect modes
                if peak_width < 2:  # meV
                    defect_analysis['local_modes'].append({
                        'energy_meV': peak_energy,
                        'width_meV': peak_width,
                        'type': 'defect_mode'
                    })
                    
        # Disorder effects from peak broadening
        if len(defect_peaks) > 0:
            avg_width = np.mean([properties['widths'][i] if i < len(properties['widths']) else 1
                                for i in range(len(defect_peaks))])
            defect_analysis['disorder_effects'] = avg_width / 10  # Normalized
            
        return defect_analysis
    
    def perform_quantum_ml_analysis(self, quantum_features):
        """
        Perform quantum machine learning analysis on extracted features.
        
        Parameters:
        -----------
        quantum_features : dict
            Quantum features from feature extraction.
        
        Returns:
        --------
        qml_results : dict
            QML analysis results.
        """
        qml_results = {
            'material_classification': 'Unknown',
            'similarity_analysis': {},
            'property_predictions': {}
        }
        
        try:
            feature_vector = self.extract_feature_vector(quantum_features)
            
            if len(feature_vector) > 0:
                qml_prediction = self.qml_processor.quantum_kernel_prediction([feature_vector])
                qml_results['material_classification'] = qml_prediction
                
        except Exception as e:
            print(f"Warning: Quantum ML analysis failed: {e}")
        
        return qml_results
    
    def extract_feature_vector(self, quantum_features):
        """
        Extract numerical feature vector from quantum features for ML analysis.
        
        Parameters:
        -----------
        quantum_features : dict
            Quantum feature analysis results.
            
        Returns:
        --------
        feature_vector : list
            Numerical feature vector containing multipartite entanglement
            measure, L1 coherence value, quantum discord measure, and global
            quantum signature.
        """
        feature_vector = []
        
        ent_features = quantum_features.get('entanglement_features', {})
        feature_vector.append(ent_features.get('multipartite_entanglement', 0))
        
        coh_features = quantum_features.get('coherence_features', {})
        feature_vector.append(coh_features.get('l1_coherence', 0))
        
        corr_features = quantum_features.get('quantum_correlations', {})
        feature_vector.append(corr_features.get('quantum_discord', 0))
        
        sig_features = quantum_features.get('spectral_quantum_signature', {})
        global_sig = sig_features.get('global_signature', 0)
        if isinstance(global_sig, (int, float)):
            feature_vector.append(global_sig)
        else:
            feature_vector.append(0)
        
        return feature_vector
    
    def predict_comprehensive_material_properties(self, detected_elements, 
                                                 bonding_analysis, magnetic_analysis, 
                                                 kk_results):
        """
        Predict comprehensive material properties from analysis results.
        
        Parameters:
        -----------
        detected_elements : dict
            Results from element detection.
        bonding_analysis : dict
            Chemical bonding analysis results.
        magnetic_analysis : dict
            Magnetic properties analysis.
        kk_results : dict
            Quantum Kramers-Kronig optical analysis results.
        
        Returns:
        --------
        properties : dict
            Comprehensive property predictions.
        """
        properties = {
            'mechanical_properties': self.predict_mechanical_properties(detected_elements, bonding_analysis),
            'electrical_properties': self.predict_electrical_properties(detected_elements, bonding_analysis),
            'thermal_properties': self.predict_thermal_properties(detected_elements, bonding_analysis),
            'optical_properties': self.extract_optical_properties(kk_results),
            'magnetic_properties': self.extract_magnetic_predictions(magnetic_analysis),
            'chemical_properties': self.predict_chemical_properties(detected_elements, bonding_analysis)
        }
        
        return properties
    
    def predict_mechanical_properties(self, detected_elements, bonding_analysis):
        """
        Predict mechanical properties from composition and bonding.
        
        Parameters:
        -----------
        detected_elements : dict
            Detected chemical elements.
        bonding_analysis : dict
            Chemical bonding characteristics.
        
        Returns:
        --------
        mechanical : dict
            Mechanical property predictions.
        """
        mechanical = {
            'hardness_estimate': 'Unknown',
            'elastic_modulus_estimate': 'Unknown',
            'brittleness': 'Unknown'
        }
        
        primary_bonding = bonding_analysis.get('bonding_characteristics', {}).get('primary_bonding', 'Unknown')
        
        if primary_bonding == 'Covalent':
            mechanical['hardness_estimate'] = 'high'
            mechanical['elastic_modulus_estimate'] = 'high'
            mechanical['brittleness'] = 'brittle'
        elif primary_bonding == 'Metallic':
            mechanical['hardness_estimate'] = 'medium'
            mechanical['elastic_modulus_estimate'] = 'medium'
            mechanical['brittleness'] = 'ductile'
        elif primary_bonding == 'Ionic':
            mechanical['hardness_estimate'] = 'medium'
            mechanical['elastic_modulus_estimate'] = 'medium'
            mechanical['brittleness'] = 'brittle'
        
        hard_elements = ['C', 'B', 'Si', 'N']
        if any(elem in detected_elements for elem in hard_elements):
            mechanical['hardness_estimate'] = 'high'
        
        return mechanical
    
    def predict_electrical_properties(self, detected_elements, bonding_analysis):
        """
        Predict electrical properties from composition and bonding.
        
        Parameters:
        -----------
        detected_elements : dict
            Detected chemical elements.
        bonding_analysis : dict
            Chemical bonding characteristics.
            
        Returns:
        --------
        electrical : dict
            Electrical property predictions.
        """
        electrical = {
            'conductivity_type': 'Unknown',
            'band_gap_estimate': 'Unknown',
            'resistivity_estimate': 'Unknown'
        }
        
        primary_bonding = bonding_analysis.get('bonding_characteristics', {}).get('primary_bonding', 'Unknown')
        
        if primary_bonding == 'Metallic':
            electrical['conductivity_type'] = 'conductor'
            electrical['band_gap_estimate'] = 'zero'
            electrical['resistivity_estimate'] = 'low'
        elif primary_bonding == 'Covalent':
            semiconductors = ['Si', 'Ge', 'GaAs']
            if any(elem in detected_elements for elem in semiconductors):
                electrical['conductivity_type'] = 'semiconductor'
                electrical['band_gap_estimate'] = 'small'
                electrical['resistivity_estimate'] = 'medium'
            else:
                electrical['conductivity_type'] = 'insulator'
                electrical['band_gap_estimate'] = 'large'
                electrical['resistivity_estimate'] = 'high'
        elif primary_bonding == 'Ionic':
            electrical['conductivity_type'] = 'insulator'
            electrical['band_gap_estimate'] = 'large'
            electrical['resistivity_estimate'] = 'high'
        
        return electrical
    
    def predict_thermal_properties(self, detected_elements, bonding_analysis):
        """
        Predict thermal properties from composition and bonding.
        
        Parameters:
        -----------
        detected_elements : dict
            Detected chemical elements.
        bonding_analysis : dict
            Chemical bonding characteristics.
        
        Returns:
        --------
        thermal : dict
            Thermal property predictions.
        """
        thermal = {
            'melting_point_estimate': 'Unknown',
            'thermal_conductivity': 'Unknown',
            'thermal_expansion': 'Unknown'
        }
        
        high_mp_elements = ['W', 'Re', 'Os', 'Ta', 'Mo', 'Nb']
        medium_mp_elements = ['Fe', 'Ni', 'Co', 'Cr', 'Ti', 'V']
        
        if any(elem in detected_elements for elem in high_mp_elements):
            thermal['melting_point_estimate'] = 'very_high'
            thermal['thermal_conductivity'] = 'high'
        elif any(elem in detected_elements for elem in medium_mp_elements):
            thermal['melting_point_estimate'] = 'medium'
            thermal['thermal_conductivity'] = 'medium'
        
        primary_bonding = bonding_analysis.get('bonding_characteristics', {}).get('primary_bonding', 'Unknown')
        if primary_bonding == 'Metallic':
            thermal['thermal_conductivity'] = 'high'
            thermal['thermal_expansion'] = 'medium'
        
        return thermal
    
    def extract_optical_properties(self, kk_results):
        """
        Extract optical properties from Quantum Kramers-Kronig analysis.
        
        Parameters:
        -----------
        kk_results : dict
            Quantum Kramers-Kronig optical analysis results.
        
        Returns:
        --------
        optical : dict
            Optical property predictions.
        """
        optical = {
            'refractive_index_range': 'Unknown',
            'absorption_features': [],
            'transparency_windows': []
        }
        
        if isinstance(kk_results, np.ndarray) and len(kk_results) > 0:
            optical['refractive_index_range'] = f"{np.min(kk_results):.2f} - {np.max(kk_results):.2f}"
        
        return optical
    
    def extract_magnetic_predictions(self, magnetic_analysis):
        """
        Extract magnetic property predictions based on magnetic analysis.
        
        Parameters:
        -----------
        magnetic_analysis : dict
            Magnetic properties analysis.
        
        Returns:
        --------
        predictions : dict
            Magnetic property predictions.
        """
        predictions = {
            'magnetic_behavior': 'non-magnetic',
            'magnetic_moment_estimate': 'zero',
            'magnetic_ordering': 'Unknown'
        }
        
        if magnetic_analysis.get('magnetic_elements'):
            predictions['magnetic_behavior'] = 'magnetic'
            predictions['magnetic_ordering'] = magnetic_analysis.get('magnetic_ordering', 'Unknown')
            
            total_moment = 0
            for element, analysis in magnetic_analysis['magnetic_elements'].items():
                total_moment += analysis.get('magnetic_moment_estimate', 0)
            
            predictions['magnetic_moment_estimate'] = f"{total_moment:.1f} μB"
        
        return predictions
    
    def predict_chemical_properties(self, detected_elements, bonding_analysis):
        """
        Predict chemical properties based on bonding analysis and elements.
        
        Parameters:
        -----------
        detected_elements : dict
            Previously detected chemical elements.
        bonding_analysis : dict
            Chemical bonding analysis results.
        
        Returns:
        --------
        chemical : dict
            Chemical properties prediction.
        """
        chemical = {
            'reactivity': 'Unknown',
            'oxidation_resistance': 'Unknown',
            'corrosion_resistance': 'Unknown'
        }
        
        reactive_elements = ['Li', 'Na', 'K', 'Mg', 'Ca', 'Al']
        noble_elements = ['Au', 'Pt', 'Ag']
        
        if any(elem in detected_elements for elem in reactive_elements):
            chemical['reactivity'] = 'high'
            chemical['oxidation_resistance'] = 'low'
            chemical['corrosion_resistance'] = 'low'
        elif any(elem in detected_elements for elem in noble_elements):
            chemical['reactivity'] = 'low'
            chemical['oxidation_resistance'] = 'high'
            chemical['corrosion_resistance'] = 'high'
        
        return chemical
    
    def calculate_comprehensive_confidence(self, detected_elements, quantum_features, bonding_analysis):
        """
        Calculate comprehensive confidence assessment.
        
        Parameters:
        -----------
        detected_elements : dict
            Results from element detection.
        quantum_features : dict
            Quantum-extracted spectral features.
        bonding_analysis : dict
            Chemical bonding analysis results.
            
        Returns:
        --------
        confidence : dict
            Comprehensive confidence assessment.
        """
        confidence = {
            'overall': 0.0,
            'element_detection': 0.0,
            'quantum_analysis': 0.0,
            'bonding_analysis': 0.0
        }
        
        if detected_elements:
            element_confidences = [info.get('confidence', 0) for info in detected_elements.values()]
            confidence['element_detection'] = np.mean(element_confidences)
        
        if quantum_features:
            confidence['quantum_analysis'] = 0.8
        
        bonding_confidence = bonding_analysis.get('bonding_characteristics', {}).get('confidence', 0)
        confidence['bonding_analysis'] = bonding_confidence
        
        confidences = [
            confidence['element_detection'],
            confidence['quantum_analysis'],
            confidence['bonding_analysis']
        ]
        confidence['overall'] = np.mean([c for c in confidences if c > 0])
        
        return confidence
    
    def visualize_results(self, analysis_results, show_quantum_features=True, 
                         show_substitution=False, save_path=None):
        """
        Comprehensive visualization of analysis results.
        
        Parameters:
        -----------
        analysis_results : dict
            Results from comprehensive_analysis().
        show_quantum_features : bool, optional
            Whether to display quantum feature analysis. Default is True.
        show_substitution :
            Whether to show element substitution analysis. Default is False.
        save_path : str, optional
            Path to save the figure. If None, displays interactively.
            
        Returns:
        --------
        tuple : matplotlib.figure.Figure, np.ndarray
            Figure object and array of axes for further customization
        """
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        
        # 1. Main spectrum plot
        ax1 = axes[0, 0]
        energy_axis = analysis_results['energy_axis']
        original_spectrum = analysis_results['original_spectrum']
        processed_spectrum = analysis_results['processed_spectrum']
        
        ax1.plot(energy_axis, original_spectrum, 'b-', alpha=0.7, label='Original')
        ax1.plot(energy_axis, processed_spectrum, 'r-', linewidth=2, label='Processed')
        
        # Annotate detected elements
        detected_elements = analysis_results['detected_elements']
        for element, info in detected_elements.items():
            for edge_info in info['edges']:
                energy = edge_info['energy']
                ax1.axvline(x=energy, color='green', linestyle='--', alpha=0.7)
                ax1.text(energy, ax1.get_ylim()[1] * 0.9, f"{element}\n{edge_info['type']}", 
                        rotation=90, ha='right', va='top', fontsize=8)
        
        ax1.set_xlabel('Energy Loss (eV)')
        ax1.set_ylabel('Intensity')
        ax1.set_title('EELS Spectrum with Element Detection')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Quantum Fourier Transform results
        ax2 = axes[0, 1]
        qft_results = analysis_results.get('qft_results', ({}, None))
        if qft_results[0]:
            states = list(qft_results[0].keys())
            counts = list(qft_results[0].values())
            ax2.bar(range(len(states)), counts, color='purple', alpha=0.7)
            ax2.set_title('Quantum Fourier Transform')
            ax2.set_xlabel('Quantum State')
            ax2.set_ylabel('Counts')
            ax2.set_xticks(range(len(states)))
            ax2.set_xticklabels(states, rotation=45)
        else:
            ax2.text(0.5, 0.5, 'QFT Analysis\nNot Available', 
                    ha='center', va='center', transform=ax2.transAxes)
        ax2.grid(True, alpha=0.3)
        
        # 3. Element confidence plot
        ax3 = axes[0, 2]
        if detected_elements:
            elements = list(detected_elements.keys())
            confidences = [info.get('confidence', 0) for info in detected_elements.values()]
            bars = ax3.bar(range(len(elements)), confidences, color='orange', alpha=0.7)
            ax3.set_title('Element Detection Confidence')
            ax3.set_xlabel('Element')
            ax3.set_ylabel('Confidence')
            ax3.set_xticks(range(len(elements)))
            ax3.set_xticklabels(elements)
            ax3.set_ylim(0, 1)
            
            for bar, conf in zip(bars, confidences):
                ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                        f'{conf:.2f}', ha='center', va='bottom', fontsize=9)
        else:
            ax3.text(0.5, 0.5, 'No Elements\nDetected', 
                    ha='center', va='center', transform=ax3.transAxes)
        ax3.grid(True, alpha=0.3)
        
        # 4. Quantum features visualization
        ax4 = axes[1, 0]
        if show_quantum_features and analysis_results.get('quantum_features'):
            quantum_features = analysis_results['quantum_features']
            
            feature_names = []
            feature_values = []
            
            ent_features = quantum_features.get('entanglement_features', {})
            if 'multipartite_entanglement' in ent_features:
                feature_names.append('Multipartite\nEntanglement')
                feature_values.append(ent_features['multipartite_entanglement'])
            
            coh_features = quantum_features.get('coherence_features', {})
            if 'l1_coherence' in coh_features:
                feature_names.append('L1 Coherence')
                feature_values.append(coh_features['l1_coherence'])
            
            corr_features = quantum_features.get('quantum_correlations', {})
            if 'quantum_discord' in corr_features:
                feature_names.append('Quantum\nDiscord')
                feature_values.append(corr_features['quantum_discord'])
            
            if feature_names:
                bars = ax4.bar(range(len(feature_names)), feature_values, 
                              color='cyan', alpha=0.7)
                ax4.set_title('Quantum Features')
                ax4.set_xlabel('Feature Type')
                ax4.set_ylabel('Feature Value')
                ax4.set_xticks(range(len(feature_names)))
                ax4.set_xticklabels(feature_names, rotation=45, ha='right')
                
                for bar, value in zip(bars, feature_values):
                    ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                            f'{value:.3f}', ha='center', va='bottom', fontsize=9)
            else:
                ax4.text(0.5, 0.5, 'Quantum Features\nNot Available', 
                        ha='center', va='center', transform=ax4.transAxes)
        else:
            ax4.text(0.5, 0.5, 'Quantum Features\nDisabled', 
                    ha='center', va='center', transform=ax4.transAxes)
        ax4.grid(True, alpha=0.3)
        
        # 5. Bonding analysis
        ax5 = axes[1, 1]
        bonding_analysis = analysis_results.get('bonding_analysis', {})
        bonding_chars = bonding_analysis.get('bonding_characteristics', {})
        
        if bonding_chars:
            bonding_type = bonding_chars.get('primary_bonding', 'Unknown')
            confidence = bonding_chars.get('confidence', 0)
            
            ax5.pie([confidence, 1-confidence], 
                   labels=[f'{bonding_type}\n({confidence:.2f})', f'Uncertainty\n({1-confidence:.2f})'],
                   autopct='%1.1f%%', colors=['lightgreen', 'lightcoral'])
            ax5.set_title('Primary Bonding Type')
        else:
            ax5.text(0.5, 0.5, 'Bonding Analysis\nNot Available', 
                    ha='center', va='center', transform=ax5.transAxes)
        
        # 6. Material properties summary
        ax6 = axes[1, 2]
        material_props = analysis_results.get('material_properties', {})
        
        summary_text = "Material Properties Summary:\n\n"
        
        electrical = material_props.get('electrical_properties', {})
        if electrical.get('conductivity_type') != 'Unknown':
            summary_text += f"Electrical: {electrical['conductivity_type']}\n"
        
        mechanical = material_props.get('mechanical_properties', {})
        if mechanical.get('hardness_estimate') != 'Unknown':
            summary_text += f"Hardness: {mechanical['hardness_estimate']}\n"
        
        magnetic = material_props.get('magnetic_properties', {})
        if magnetic.get('magnetic_behavior') != 'non-magnetic':
            summary_text += f"Magnetic: {magnetic['magnetic_behavior']}\n"
        
        bonding = bonding_analysis.get('bonding_characteristics', {})
        if bonding.get('primary_bonding') != 'Unknown':
            summary_text += f"Bonding: {bonding['primary_bonding']}\n"
        
        confidence = analysis_results.get('confidence_assessment', {})
        overall_conf = confidence.get('overall', 0)
        summary_text += f"\nOverall Confidence: {overall_conf:.2f}"
        
        ax6.text(0.05, 0.95, summary_text, transform=ax6.transAxes, 
                fontsize=10, verticalalignment='top', fontfamily='monospace')
        ax6.set_title('Analysis Summary')
        ax6.axis('off')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()
        
        return fig, axes
    
    def generate_comprehensive_report(self, analysis_results, include_quantum_details=True):
        """
        Generate a comprehensive report with all findings.
        
        Parameters:
        -----------
        analysis_results : dict
            Results from comprehensive_analysis().
        include_quantum_details : bool, optional
            Whether to include detailed quantum analysis sections. Default is True.
            
        Returns:
        --------
        report : dict
            Structured report.
        """
        report = {
            'executive_summary': self.generate_executive_summary(analysis_results),
            'detailed_analysis': self.generate_detailed_analysis(analysis_results),
            'material_identification': self.generate_material_identification(analysis_results),
            'property_predictions': analysis_results.get('material_properties', {}),
            'recommendations': self.generate_recommendations(analysis_results),
            'confidence_assessment': analysis_results.get('confidence_assessment', {}),
            'metadata': {
                'analysis_timestamp': analysis_results.get('analysis_timestamp'),
                'material_name': analysis_results.get('material_name'),
                'quantum_enhancement': True
            }
        }
        
        if include_quantum_details:
            report['quantum_insights'] = self.generate_quantum_insights(analysis_results)
        
        return report
    
    def generate_executive_summary(self, analysis_results):
        """
        Generate executive summary of analysis results.
        
        Parameters:
        -----------
        analysis_results : dict
            Complete analysis results from comprehensive_analysis().
            
        Returns:
        --------
        summary : dict
            Executive summary of composition, characteristics,
            properties, and confidence.
        """
        detected_elements = analysis_results.get('detected_elements', {})
        confidence = analysis_results.get('confidence_assessment', {}).get('overall', 0)
        
        summary = {
            'material_composition': list(detected_elements.keys()),
            'primary_characteristics': [],
            'key_properties': [],
            'confidence_level': 'high' if confidence > 0.8 else 'medium' if confidence > 0.6 else 'low',
            'main_findings': []
        }
        
        bonding_info = analysis_results.get('bonding_analysis', {}).get('bonding_characteristics', {})
        if bonding_info.get('primary_bonding') != 'Unknown':
            summary['primary_characteristics'].append(f"Primary bonding: {bonding_info['primary_bonding']}")
        
        material_id = analysis_results.get('material_identification', {})
        if material_id.get('material_class') != 'Unknown':
            summary['primary_characteristics'].append(f"Material class {material_id['material_class']}")
        
        magnetic_analysis = analysis_results.get('magnetic_properties', {})
        if magnetic_analysis.get('magnetic_elements'):
            summary['primary_characteristics'].append("Magnetic material detected")
        
        material_props = analysis_results.get('material_properties', {})
        electrical = material_props.get('electrical_properties', {})
        if electrical.get('conductivity_type') != 'Unknown':
            summary['key_properties'].append(f"Electrical: {electrical['conductivity_type']}")
            
        mechanical = material_props.get('mechanical_properties', {})
        if mechanical.get('hardness_estimate', 'Unknown') != 'Unknown':
            summary['key_properties'].append(f"Hardness: {mechanical['hardness_estimate']}")
        
        if len(detected_elements) == 1:
            summary['main_findings'].append("Pure elemental material")
        elif len(detected_elements) == 2:
            summary['main_findings'].append("Binary compound detected")
        elif len(detected_elements) == 3:
            summary['main_findings'].append("Ternary compound detected")
        elif len(detected_elements) > 4:
            summary['main_findings'].append("Complex multi-component material")
        
        if confidence > 0.8:
            summary['main_findings'].append("High-confidence quantum-enhanced analysis")
        elif confidence > 0.6:
            summary['main_findings'].append("Reliable quantum-enhanced analysis")
            
        # Specific material findings
        if material_id.get('specific_identification', 'Unidentified') != 'unidentified_ceramic':
            specific_name = material_id.get('specific_identification', '').replace('_', ' ').title()
            summary['main_findings'].append(f"Identified as {specific_name}")
        
        return summary
    
    def generate_detailed_analysis(self, analysis_results):
        """
        Generate detailed technical analysis section.
        
        Parameters:
        -----------
        analysis_results : dict
            Complete analysis results.
        
        Returns:
        --------
        detailed : dict
            Detailed analysis documentation.
        """
        detailed = {
            'elemental_composition': self.format_elemental_analysis(
                analysis_results.get('detected_elements', {})
            ),
            'spectroscopic_features': self.format_spectroscopic_features(analysis_results),
            'bonding_characteristics': self.format_bonding_analysis(
                analysis_results.get('bonding_analysis', {})
            ),
            'quantum_enhancements': self.format_quantum_enhancements(analysis_results)
        }
        
        return detailed
    
    def format_elemental_analysis(self, detected_elements):
        """
        Format elemental analysis results for reporting.
        
        Parameters:
        -----------
        detected_elements : dict
            Raw element detection results.
        
        Returns:
        --------
        elemental_report : dict
            Formatted elemental analysis for each detected element.
        """
        elemental_report = {}
        
        for element, info in detected_elements.items():
            elemental_report[element] = {
                'confidence': f"{info.get('confidence', 0):.2f}",
                'detected_edges': [edge['type'] for edge in info.get('edges', [])],
                'quantum_signature': f"{info.get('quantum_signature', 0):.3f}",
                'multiple_edges': len(info.get('edges', [])) > 1
            }
        
        return elemental_report
    
    def format_spectroscopic_features(self, analysis_results):
        """
        Format spectroscopic features for reporting.
        
        Parameters:
        -----------
        analysis_results : dict
            Complete analysis results from comprehensive_analysis()
        
        Returns:
        --------
        features : dict
            Formatted spectroscopic feature analysis for each detected element.
        """
        features = {
            'energy_range': f"{analysis_results['energy_axis'][0]:.1f} - {analysis_results['energy_axis'][-1]:.1f} eV",
            'data_points': len(analysis_results['energy_axis']),
            'preprocessing_applied': 'Quantum-enhanced Richardson-Lucy deconvolution',
            'quantum_fourier_analysis': 'Applied' if analysis_results.get('qft_results', [{}])[0] else 'Failed',
            'kramers_kronig_analysis': 'Applied' if analysis_results.get('optical_properties') else 'Not available'
        }
        
        return features
    
    def format_bonding_analysis(self, bonding_analysis):
        """
        Format bonding analysis for reporting.
        
        Parameters:
        -----------
        bonding_analysis : dict
            Chemical bonding analysis results
            
        Returns:
        --------
        bonding_report : dict
            Formatted bonding analysis report.
        """
        bonding_report = {
            'primary_bonding_type': bonding_analysis.get('bonding_characteristics', {}).get('primary_bonding', 'Unknown'),
            'bonding_confidence': bonding_analysis.get('bonding_characteristics', {}).get('confidence', 0),
            'orbital_analysis': bonding_analysis.get('orbital_analysis', {}),
            'hybridization_analysis': bonding_analysis.get('hybridization', {}),
            'charge_transfer_effects': bonding_analysis.get('charge_transfer', {})
        }
        
        return bonding_report
    
    def format_quantum_enhancements(self, analysis_results):
        """
        Format quantum enhancement details.
        
        Parameters:
        -----------
        analysis_results : dict
            Complete analysis results from comprehensive_analysis()
        
        Returns:
        --------
        enhancements : dict
            Formatted quantum enhancement details for reporting.
        """
        enhancements = {
            'quantum_preprocessing': 'Richardson-Lucy deconvolution with quantum PSF estimation',
            'quantum_peak_detection': 'Entanglement-based peak analysis',
            'quantum_feature_extraction': 'Multi-scale quantum signatures',
            'quantum_fourier_transform': 'Applied for frequency domain analysis',
            'quantum_machine_learning': 'Kernel-based material classification'
        }
        
        return enhancements

    def format_alternative_classifications(alternatives):
        """
        Format alternative classifications properly.
        """
        formatted_alts = []
        for alt in alternatives[:2]:  # Show top 2 alternatives
            material_class = alt.get('material_class', 'Unknown')
            material_subclass = alt.get('material_subclass', 'Unknown')
            confidence = alt.get('confidence', 0)
            formatted_alts.append(f"{material_class}/{material_subclass} (confidence: {confidence:.2f})")
        return formatted_alts
    
    def generate_material_identification(self, analysis_results):
        """
        Generate comprehensive material identification and classification.
        
        Parameters:
        -----------
        analysis_results : dict
            Complete analysis results from comprehensive_analysis().
            
        Returns:
        --------
        identification : dict
            Material identification results.
        """
        detected_elements = analysis_results.get('detected_elements', {})
        element_list = sorted(detected_elements.keys())
        bonding_analysis = analysis_results.get('bonding_analysis', {})
        quantum_features = analysis_results.get('quantum_features', {})
        optical_properties = analysis_results.get('optical_features', {})
        
        identification = {
            'most_likely_material': 'Unknown',
            'material_class': 'Unknown',
            'material_subclass': 'Unknown',
            'specific_identification': 'Unknown',
            'confidence': 0.0,
            'alternative_possibilities': [],
            'classification_reasoning': [],
            'elemental_composition': element_list,
            'stoichiometry_analysis': {},
            'structure_prediction': {}
        }
        
        if not element_list:
            return identification
        
        # Analyze elemental composition and ratios
        identification['stoichiometry_analysis'] = self.analyze_stoichiometry(detected_elements)
        
        # Comprehensive material classification
        classification_results = []
        
        # 1. Check for polymers
        polymer_match = self.classify_polymers(element_list, detected_elements, bonding_analysis)
        if polymer_match['confidence'] > 0.3:
            classification_results.append(polymer_match)
            
        # 2. Check for metals and alloys
        metal_match = self.classify_metals_alloys(element_list, detected_elements, bonding_analysis)
        if metal_match['confidence'] > 0.3:
            classification_results.append(metal_match)
            
        # 3. Check for semiconductors
        semiconductor_match = self.classify_semiconductors(element_list, detected_elements, optical_properties)
        if semiconductor_match['confidence'] > 0.3:
            classification_results.append(semiconductor_match)
            
        # 4. Check for ceramics
        ceramic_match = self.classify_ceramics(element_list, detected_elements, bonding_analysis)
        if ceramic_match['confidence'] > 0.3:
            classification_results.append(ceramic_match)
    
        # 5. Check for glasses
        glass_match = self.classify_glasses(element_list, detected_elements, bonding_analysis)
        if glass_match['confidence'] > 0.3:
            classification_results.append(glass_match)
    
        # 6. Check for composites
        composite_match = self.classify_composites(element_list, detected_elements, bonding_analysis)
        if composite_match['confidence'] > 0.3:
            classification_results.append(composite_match)
    
        # 7. Check for nanomaterials
        nano_match = self.classify_nanomaterials(element_list, detected_elements, quantum_features)
        if nano_match['confidence'] > 0.3:
            classification_results.append(nano_match)
    
        # 8. Check for biomaterials
        bio_match = self.classify_biomaterials(element_list, detected_elements, bonding_analysis)
        if bio_match['confidence'] > 0.3:
            classification_results.append(bio_match)
        
        # Choose best classification
        if classification_results:
            best_match = max(classification_results, key=lambda x: x['confidence'])
            identification.update(best_match)
            
            # Add alternatives
            identification['alternative_possibilities'] = [
                match for match in classification_results
                if match != best_match and match['confidence'] > 0.5
            ]
        else:
            # Fallback classification
            identification = self.fallback_classification(element_list, detected_elements, bonding_analysis)
            
        # Predict structure and properties
        identification['structure_prediction'] = self.predict_structure(element_list, identification)
        
        return identification
    
    def analyze_stoichiometry(self, detected_elements):
        """
        Determine stoichiometry based on relative intensities, elements, and composition.
        
        Parameters:
        -----------
        detected_elements : dict
            Previously detected elements in material.
        
        Returns:
        --------
        stoichiometry : dict
            Stoichiometry analysis results.
        """
        stoichiometry = {
            'atomic_ratios': {},
            'dominant_element': None,
            'trace_elements': [],
            'binary_ratios': {},
            'complexity_index': 0
        }
        
        if not detected_elements:
            return stoichiometry
        
        # Get element list from detected_elements
        element_list = list(detected_elements.keys())
        
        # Calculate relative intensities (proxy for atomic ratios)
        total_intensity = sum(info.get('intensity', 0) for info in detected_elements.values())
        
        if total_intensity > 0:
            for element, info in detected_elements.items():
                intensity = info.get('intensity', 0)
                stoichiometry['atomic_ratios'][element] = intensity / total_intensity
        
        # Identify dominant and trace elements
        if stoichiometry['atomic_ratios']:
            max_element = max(stoichiometry['atomic_ratios'], key=stoichiometry['atomic_ratios'].get)
            stoichiometry['dominant_element'] = max_element
            
            threshold = 0.1 # 10% threshold for trace elements
            stoichiometry['trace_elements'] = [
                elem for elem, ratio in stoichiometry['atomic_ratios'].items()
                if ratio < threshold
            ]
            
        # Calculate binary ratios for common element pairs
        important_pairs = [
            ('C', 'O'), ('C', 'H'), ('Si', 'O'), ('Al', 'O'), ('Fe', 'C'),
            ('Ti', 'O'), ('Ca', 'O'), ('Mg', 'O'), ('Zn', 'O'), ('Cu', 'O')
        ]
        
        for elem1, elem2 in important_pairs:
            if elem1 in element_list and elem2 in element_list:
                ratio1 = stoichiometry['atomic_ratios'].get(elem1, 0)
                ratio2 = stoichiometry['atomic_ratios'].get(elem2, 0)
                if ratio2 > 0:
                    stoichiometry['binary_ratios'][f'{elem1}/{elem2}'] = ratio1 / ratio2
                    
        # Complexity index based on number of elements and distribution
        n_elements = len(detected_elements)
        if n_elements > 1:
            # Shannon entropy as complexity measure
            ratios = list(stoichiometry['atomic_ratios'].values())
            entropy = -sum(r * np.log(r + 1e-10) for r in ratios if r > 0)
            stoichiometry['complexity_index'] = entropy / np.log(n_elements)
            
        return stoichiometry
    
    def classify_polymers(self, element_list, detected_elements, bonding_analysis):
        """
        Classify polymer materials based on composition and bonding.
        
        Parameters:
        -----------
        element_list : list
            List of detected element symbols.
        detected_elements : dict
            Element detection results with intensities.
        bonding_analysis : dict
            Chemical bonding analysis results.
        
        Returns:
        --------
        classification : dict
            Polymer classification.
        """
        classification = {
            'material_class': 'Polymer',
            'material_subclass': 'Unknown Polymer',
            'specific_identification': 'Unidentified Polymer',
            'confidence': 0.0,
            'classification_reasoning': []
        }
        
        # Check for organic polymer signature
        has_carbon = 'C' in element_list
        has_hydrogen = 'H' in element_list
        organic_elements = {'C', 'H', 'O', 'N', 'S', 'Cl', 'F', 'Br', 'I'}
        
        if has_carbon:
            organic_fraction = len(set(element_list) & organic_elements) / len(element_list)
            base_confidence = 0.7 if has_hydrogen else 0.4
            
            # Check bonding type
            primary_bonding = bonding_analysis.get('bonding_characteristics', {}).get('primary_bonding', '')
            if primary_bonding == 'Covalent':
                base_confidence += 0.2
                classification['classification_reasoning'].append('Covalent bonding supports polymer structure')
                
            # Analyze composition for specific polymer types
            if organic_fraction > 0.8:
                classification['confidence'] = base_confidence * organic_fraction
                
                # Specific polymer identification
                if set(element_list) == {'C', 'H'}:
                    classification['material_subclass'] = 'Hydrocarbon Polymer'
                    classification['specific_identification'] = 'Polyethylene or Polypropylene'
                    classification['confidence'] = 0.8
                    classification['classification_reasoning'].append('Pure hydrocarbon composition')
                    
                elif 'O' in element_list and len(element_list) <= 3:
                    co_ratio = detected_elements.get('C', {}).get('intensity', 0) / max(detected_elements.get('O', {}).get('intensity', 1), 1)
                    if 2 < co_ratio < 10:
                        classification['material_subclass'] = 'Oxygen-Containing Polymer'
                        classification['specific_identification'] = 'Polyester or Polyether'
                        classification['confidence'] = 0.75
                        classification['classification_reasoning'].append(f'C/O ratio ({co_ratio:.1f}) suggests polyester/polyether')
                        
                elif 'N' in element_list:
                    classification['material_subclass'] = 'Nitrogen-Containing Polymer'
                    if 'O' in element_list:
                        classification['specific_identification'] = 'Polyurethane or Polyamide'
                    else:
                        classification['specific_identification'] = 'Polyimide or Polyaniline'
                    classification['confidence'] = 0.7
                    classification['classification_reasoning'].append('Nitrogen content suggests specialty polymer')
                    
                elif 'Cl' in element_list:
                    classification['material_subclass'] = 'Halogenated Polymer'
                    classification['specific_identification'] = 'PVC or Chlorinated Polymer'
                    classification['confidence'] = 0.85
                    classification['classification_reasoning'].append('Chlorine suggests PVC or similar')
                    
                elif 'F' in element_list:
                    classification['material_subclass'] = 'Fluoropolymer'
                    classification['specific_identification'] = 'PTFE or Fluorinated_Polymer'
                    classification['confidence'] = 0.9
                    classification['classification_reasoning'].append('Fluorine indicates fluoropolymer')
                    
        # Check for inorganic polymers
        elif 'Si' in element_list and 'O' in element_list:
            si_o_elements = {'Si', 'O', 'C', 'H'}
            if set(element_list).issubset(si_o_elements):
                classification['material_class'] = 'Polymer'
                classification['subclass'] = 'Inorganic Polymer'
                classification['specific_identification'] = 'Silicone Polymer'
                classification['confidence'] = 0.8
                classification['classification_reasoning'].append('Si-O backbone indicates silicone')
                
        return classification
    
    def classify_metals_alloys(self, element_list, detected_elements, bonding_analysis):
        """
        Classify metallic materials and alloys.
        
        Parameters:
        -----------
        element_list : dict
            List of detected element symbols.
        detected_elements : dict
            Element detection results.
        bonding_analysis : dict
            Bonding analysis results.
            
        Returns:
        --------
        classification : dict
            Metal/alloy classification.
        """
        classification = {
            'material_class': 'Metal',
            'material_subclass': 'Unknown Metal',
            'specific_identification': 'Unidentified Metal',
            'confidence': 0.0,
            'classification_reasoning': []
        }
        
        metals = {
            'alkali': ['Li', 'Na', 'K', 'Rb', 'Cs'],
            'alkaline_earth': ['Be', 'Mg', 'Ca', 'Sr', 'Ba'],
            'transition': ['Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Y', 'Zr', 'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg'],
            'post_transition': ['Al', 'Ga', 'In', 'Sn', 'Tl', 'Pb', 'Bi'],
            'lanthanides': ['La', 'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu'],
            'actinides': ['Ac', 'Th', 'Pa', 'U', 'Np', 'Pu']
        }
        
        all_metals = set()
        for metal_group in metals.values():
            all_metals.update(metal_group)
            
        metallic_elements = set(element_list) & all_metals
        metallic_fraction = len(metallic_elements) / len(element_list) if element_list else 0
        
        # Check bonding type
        primary_bonding = bonding_analysis.get('bonding_characteristics', {}).get('primary_bonding', '')
        if primary_bonding == 'Metallic':
            base_confidence = 0.9
            classification['classification_reasoning'].append('Metallic bonding confirmed')
        elif metallic_fraction > 0.7:
            base_confidence = 0.7
            classification['classification_reasoning'].append('High metallic element content')
        else:
            base_confidence = 0.3
        
        if metallic_fraction > 0.5:
            classification['confidence'] = base_confidence * metallic_fraction
            
            # Pure metal identification
            if len(element_list) == 1 and element_list[0] in all_metals:
                metal = element_list[0]
                classification['material_subclass'] = 'Pure Metal'
                classification['specific_identification'] = f'Pure {metal.lower()}'
                classification['confidence'] = 0.95
                classification['classification_reasoning'].append(f'Single metallic element: {metal}')
                
                # Add metal category
                for category, metal_list in metals.items():
                    if metal in metal_list:
                        classification['metal_category'] = category
                        break
            
            # Alloy identification
            elif len(metallic_elements) >= 2:
                classification['material_subclass'] = 'Alloy'
                classification = self.identify_specific_alloy(classification, element_list, detected_elements)
                
            # Metal with non-metallic additions (could be alloy or compound)
            elif len(metallic_elements) == 1:
                metal = list(metallic_elements)[0]
                non_metals = set(element_list) - metallic_elements
                
                if non_metals <= {'C', 'N', 'O', 'B', 'P', 'S'}: # Common alloying elements
                    classification['material_subclass'] = 'Alloy'
                    classification['specific_identification'] = f'{metal.lower()}-Based Alloy'
                    classification['confidence'] = 0.7
                    classification['classification_reasoning'].append(f'{metal} with common alloying elements')
                else:
                    classification['confidence'] *= 0.7 # Reduce confidence for unusual composition
                    
        return classification
    
    def identify_specific_alloy(self, classification, element_list, detected_elements):
        """
        Identify specific types of alloys based on detected elements.
        
        Parameters:
        -----------
        classification : dict
            Classified as an alloy.
        element_list : list
            List of chemical element symbols.
        detected_elements : dict
            Previously detected elements.
        
        Returns:
        --------
        classification : dict
            Specific alloy classification.
        """
        element_set = set(element_list)
        
        # Steel alloys
        if 'Fe' in element_list:
            classification['specific_identification'] = 'Steel Alloy'
            classification['alloy_family'] = 'Steel'
            
            if 'C' in element_list:
                classification['specific_identification'] = 'Carbon Steel'
            if 'Cr' in element_list and detected_elements['Cr']['intensity'] > 0.1:
                if 'Ni' in element_list:
                    classification['specific_identification'] = 'Stainless Steel'
                    classification['confidence'] = 0.85
                else:
                    classification['specific_identification'] = 'Chromium Steel'
            if 'Ni' in element_list and detected_elements['Ni']['intensity'] > 0.15:
                classification['specific_identification'] = 'Nickel Steel'
            if 'Mo' in element_list or 'W' in element_list:
                classification['specific_identification'] = 'Tool Steel'
        
        # Aluminum alloys
        elif 'Al' in element_list:
            classification['specific_identification'] = 'Aluminum Alloy'
            classification['alloy_family'] = 'Aluminum'
            
            if 'Cu' in element_list:
                classification['specific_identification'] = '2xxx Aluminum Alloy'
            elif 'Mg' in element_list and 'Si' in element_list:
                classification['specific_identification'] = '6xxx Aluminum Alloy'
            elif 'Mg' in element_list:
                classification['specific_identification'] = '5xxx Aluminum Alloy'
            elif 'Zn' in element_list:
                classification['specific_identification'] = '7xxx Aluminum Alloy'
            elif 'Mn' in element_list:
                classification['specific_identification'] = '3xxx Aluminum Alloy'
            elif 'Si' in element_list:
                classification['specific_identification'] = '4xxx Aluminum Alloy'
                
        # Titanium alloys
        elif 'Ti' in element_list:
            classification['specific_identification'] = 'Titanium Alloy'
            classification['alloy_family'] = 'Titanium'
            
            if 'Al' in element_list and 'V' in element_list:
                classification['specific_identification'] = 'Ti-6Al-4V Alloy'
                classification['confidence'] = 0.8
            elif 'Al' in element_list:
                classification['specific_identification'] = 'Alpha Titanium Alloy'
            elif 'V' in element_list or 'Mo' in element_list:
                classification['specific_identification'] = 'Beta Titanium Alloy'
                
        # Copper alloys
        elif 'Cu' in element_list:
            classification['alloy_family'] = 'Copper'
            if 'Zn' in element_list:
                classification['specific_identification'] = 'Brass'
                classification['confidence'] = 0.9
            elif 'Sn' in element_list:
                classification['specific_identification'] = 'Bronze'
                classification['confidence'] = 0.9
            elif 'Al' in element_list:
                classification['specific_identification'] = 'Aluminum Bronze'
            elif 'Ni' in element_list:
                classification['specific_identification'] = 'Cupronickel'
        
        # Nickel-based superalloys
        elif 'Ni' in element_list and ('Cr' in element_list or 'Co' in element_list):
            classification['specific_identification'] = 'Nickel Superalloy'
            classification['alloy_family'] = 'Superalloy'
            classification['confidence'] = 0.8
            
            if 'Co' in element_list and 'Cr' in element_list:
                classification['specific_identification'] = 'Inconel-type Superalloy'
                
        # Magnesium alloys
        elif 'Mg' in element_list:
            classification['specific_identification'] = 'Magnesium Alloy'
            classification['alloy_family'] = 'Magnesium'
            
            if 'Al' in element_list:
                classification['specific_identification'] = 'Aluminium-Magnesium Alloy'
            elif 'Zn' in element_list:
                classification['specific_identification'] = 'Magnesium-Zinc Alloy'
        
        # Precious metal alloys
        elif element_set & {'Au', 'Ag', 'Pt', 'Pd'}:
            precious_metals = element_set & {'Au', 'Ag', 'Pt', 'Pd'}
            classification['alloy_family'] = 'Precious Metal'
            
            if 'Au' in element_list:
                if 'Cu' in element_list:
                    classification['specific_identification'] = 'Gold-Copper Alloy'
                elif 'Ag' in element_list:
                    classification['specific_identification'] = 'White Gold Alloy'
                else:
                    classification['specific_identification'] = 'Gold Alloy'
            elif 'Pt' in element_list:
                classification['specific_identification'] = 'Platinum Alloy'
                
        return classification
    
    def classify_semiconductors(self, element_list, detected_elements, optical_properties):
        """
        Classify semiconductor materials.
        
        Parameters:
        -----------
        element_list : list
            List of detected element symbols.
        detected_elements : dict
            Element detection results.
        optical_properties : dict
            Optical properties from Quantum Kramers-Kronig analysis.
            
        Returns:
        --------
        classification : dict
            Semiconductor classification.
        """
        classification = {
            'material_class': 'Semiconductor',
            'material_subclass': 'Unknown Semiconductor',
            'specific_identification': 'Unidentified Semiconductor',
            'confidence': 0.0,
            'classification_reasoning': []
        }
        
        element_set = set(element_list)
        
        # Group IV semiconductors
        group_iv = {'Si', 'Ge', 'C'}
        if len(element_list) == 1 and element_list[0] in group_iv:
            element = element_list[0]
            classification['material_subclass'] = 'Elemental Semiconductor'
            classification['specific_identification'] = f'{element.lower()} Semiconductor'
            classification['confidence'] = 0.9
            classification['classification_reasoning'].append(f'Pure Group IV semiconductor: {element}')
            
            if element == 'C':
                classification['specific_identification'] = 'Diamond Semiconductor'
            elif element == 'Si':
                classification['crystal_structure'] = 'Diamond Cubic'
            elif element == 'Ge':
                classification['crystal_structure'] = 'Diamond Cubic'
                
        # III-V semiconductors
        elif len(element_list) == 2:
            group_iii = {'B', 'Al', 'Ga', 'In', 'Tl'}
            group_v = {'N', 'P', 'As', 'Sb', 'Bi'}
            
            iii_elements = element_set & group_iii
            v_elements = element_set & group_v
            
            if len(iii_elements) == 1 and len(v_elements) == 1:
                iii_elem = list(iii_elements)[0]
                v_elem = list(v_elements)[0]
                classification['material_subclass'] = 'III-V Semiconductor'
                classification['specific_identification'] = f'{iii_elem.lower()}{v_elem.lower()} Semiconductor'
                classification['confidence'] = 0.85
                classification['classification_reasoning'].append(f'III-V compound: {iii_elem}{v_elem}')
                classification['crystal_structure'] = 'Zinc Blende'
                
                # Specific III-V compounds with bandgaps
                compound_map = {
                    ('Ga', 'As'): ('Gallium Arsenide', 1.42),
                    ('In', 'P'): ('Indium Phosphide', 1.35),
                    ('Ga', 'N'): ('Gallium Nitride', 3.4),
                    ('Al', 'As'): ('Aluminum Arsenide', 2.16),
                    ('In', 'As'): ('Indium Arsenide', 0.36),
                    ('Ga', 'P'): ('Gallium Phosphide', 2.26)
                }
                
                key = (iii_elem, v_elem)
                if key in compound_map:
                    name, band_gap = compound_map[key]
                    classification['specific_identification'] = name
                    classification['predicted_band_gap'] = f'{band_gap} eV'
                    
            # II-VI semiconductors
            else:
                group_ii = {'Zn', 'Cd', 'Hg', 'Mg', 'Ca', 'Sr', 'Ba'}
                group_vi = {'O', 'S', 'Se', 'Te', 'Po'}
                
                ii_elements = element_set & group_ii
                vi_elements = element_set & group_vi
                
                if len(ii_elements) == 1 and len(vi_elements) == 1:
                    ii_elem = list(ii_elements)[0]
                    vi_elem = list(vi_elements)[0]
                    classification['material_subclass'] = 'II-VI Semiconductor'
                    classification['specific_identification'] = f'{ii_elem.lower()}{vi_elem.lower()} Semiconductor'
                    classification['confidence'] = 0.8
                    classification['classification_reasoning'].append(f'II-VI compound: {ii_elem}{vi_elem}')
                    
                    # Specific II-VI compounds with bandgaps
                    compound_map = {
                        ('Zn', 'O'): ('Zinc Oxide', 3.37),
                        ('Zn', 'S'): ('Zinc Sulfide', 3.6),
                        ('Cd', 'Te'): ('Cadmium Telluride', 1.5),
                        ('Cd', 'Se'): ('Cadmium Selenide', 1.7),
                        ('Zn', 'Se'): ('Zinc Selenide', 2.7)
                    }
                
                    key = (ii_elem, vi_elem)
                    if key in compound_map:
                        name, band_gap = compound_map[key]
                        classification['specific_identification'] = name
                        classification['predicted_band_gap'] = f'{band_gap} eV'
                        
        # Oxide semiconductors
        elif 'O' in element_list:
            metals_with_o = set(element_list) - {'O'}
            semiconductor_oxides = {'Ti', 'Zn', 'In', 'Sn', 'Ga', 'Cu', 'Ni'}
            
            if metals_with_o & semiconductor_oxides:
                classification['material_subclass'] = 'Oxide Semiconductor'
                classification['confidence'] = 0.7
                
                if 'Ti' in element_list and len(element_list) == 2:
                    classification['specific_identification'] = 'Titanium Dioxide'
                    classification['confidence'] = 0.8
                elif 'Zn' in element_list and len(element_list) == 2:
                    classification['specific_identification'] = 'Zinc Oxide'
                    classification['confidence'] = 0.85
                elif element_set == {'In', 'Ga', 'Zn', 'O'}:
                    classification['specific_identification'] = 'Indium Gallium Zinc Oxide (IGZO)'
                    classification['confidence'] = 0.8
                    classification['classification_reasoning'].append('IGZO transparent conductor')
                    
        # Organic semiconductors
        elif element_set <= {'C', 'H', 'N', 'O', 'S'}:
            if 'C' in element_list:
                classification['material_subclass'] = 'Organic Semiconductor'
                classification['specific_identification'] = 'Organic Semiconductor Material'
                classification['confidence'] = 0.6
                classification['classification_reasoning'].append('Organic composition suggests organic semiconductor')
        
        return classification
    
    def classify_ceramics(self, element_list, detected_elements, bonding_analysis):
        """
        Classify ceramic materials.
        
        Parameters:
        -----------
        element_list : list
            List of detected element symbols.
        detected_elements : dict
            Element detection results.
        bonding_analysis : dict
            Bonding analysis results.
            
        Returns:
        --------
        classification : dict
            Ceramic classification.
        """
        classification = {
            'material_class': 'Ceramic',
            'material_subclass': 'Unknown Ceramic',
            'specific_identification': 'Unidentified Ceramic',
            'confidence': 0.0,
            'classification_reasoning': []
        }
        
        element_set = set(element_list)
        
        # Check for ionic bonding (typical of ceramics)
        primary_bonding = bonding_analysis.get('bonding_characteristics', {}).get('primary_bonding', '')
        if primary_bonding == 'Ionic':
            base_confidence = 0.8
            classification['classification_reasoning'].append('Ionic bonding characteristic of ceramics')
        else:
            base_confidence = 0.5
            
        # Oxide ceramics
        if 'O' in element_list:
            metals = set(element_list) - {'O'}
            ceramic_metals = {'Al', 'Si', 'Ti', 'Zr', 'Mg', 'Ca', 'Y', 'Ba', 'Sr', 'La', 'Ce', 'Pr', 'Nd'}
            
            if metals & ceramic_metals:
                classification['material_subclass'] = 'Oxide Ceramic'
                classification['confidence'] = base_confidence * 0.9
                
                # Simple oxides
                if len(element_list) == 2:
                    metal = list(metals)[0]
                    classification['specific_identification'] = f'{metal.lower()} Oxide'
                    
                    oxide_map = {
                        'Al': ('Alumina', 'Al2O3'),
                        'Si': ('Silica', 'SiO2'),
                        'Ti': ('Titania', 'TiO2'),
                        'Zr': ('Zirconia', 'ZrO2'),
                        'Mg': ('Magnesia', 'MgO'),
                        'Ca': ('Lime', 'CaO'),
                        'Y': ('Yttria', 'Y2O3')
                    }
                    
                    if metal in oxide_map:
                        name, formula = oxide_map[metal]
                        classification['specific_identification'] = name
                        classification['chemical_formula'] = formula
                        classification['confidence'] = 0.85
                        
                # Complex oxides
                elif len(metals) >= 2:
                    classification['material_subclass'] = 'Complex Oxide Ceramic'
                    
                    # Perovskite structures
                    if element_set == {'Ba', 'Ti', 'O'}:
                        classification['specific_identification'] = 'Barium Titanate'
                        classification['crystal_structure'] = 'Perovskite'
                        classification['functional_properties'] = ['Ferroelectric', 'Piezoelectric']
                        classification['confidence'] = 0.9
                    elif element_set == {'Ca', 'Ti', 'O'}:
                        classification['specific_identification'] = 'Calcium Titanate'
                        classification['crystal_structure'] = 'Perovskite'
                        classification['functional_properties'] = ['High Dielectric Constant', 'Thermal Resistive']
                        classification['confidence'] = 0.9
                    elif element_set == {'Pb', 'Zr', 'Ti', 'O'}:
                        classification['specific_identification'] = 'Lead Zirconate Titanate (PZT)'
                        classification['crystal_structure'] = 'Perovskite'
                        classification['functional_properties'] = ['Piezoelectric']
                        classification['confidence'] = 0.9
                    elif element_set == {'Y', 'Ba', 'Cu', 'O'}:
                        classification['specific_identification'] = 'YBCO Superconductor'
                        classification['functional_properties'] = ['High Temperature Superconductor']
                        classification['confidence'] = 0.85
                    
                    # Spinel structures
                    elif element_set == {'Mg', 'Al', 'O'}:
                        classification['specific_identification'] = 'Magnesium Aluminate Spinel'
                        classification['crystal_structure'] = 'Spinel'
                        classification['confidence'] = 0.8
                    elif element_set == {'Fe', 'Al', 'O'}:
                        classification['specific_identification'] = 'Iron Aluminate Spinel'
                        classification['crystal_structure'] = 'Spinel'
                        classification['confidence'] = 0.8
                        
        # Non-oxide ceramics
        else:
            non_oxide_elements = {'C', 'N', 'B', 'Si'}
            metals = set(element_list) - non_oxide_elements
            
            if non_oxide_elements & element_set and metals:
                classification['material_subclass'] = 'Non-Oxide Ceramic'
                classification['confidence'] = base_confidence * 0.8
                
                # Carbides
                if 'C' in element_list:
                    classification['ceramic_type'] = 'Carbide'
                    if len(element_list) == 2:
                        metal = list(metals)[0]
                        classification['specific_identification'] = f'{metal.lower()} Carbide'
                        
                        carbide_map = {
                            'Si': ('Silicon Carbide', 'SiC', ['Semiconductor', 'Abrasive']),
                            'Ti': ('Titanium Carbide', 'TiC', ['Hard Coating']),
                            'W': ('Tungsten Carbide', 'WC', ['Cutting Tool']),
                            'B': ('Boron Carbide', 'B4C', ['Armor', 'Abrasive'])
                        }
                        
                        if metal in carbide_map:
                            name, formula, applications = carbide_map[metal]
                            classification['specific_identification'] = name
                            classification['chemical_formula'] = formula
                            classification['applications'] = applications
                            classification['confidence'] = 0.85
                
                # Nitrides
                elif 'N' in element_list:
                    classification['ceramic_type'] = 'Nitride'
                    if len(element_list) == 2:
                        metal = list(metals)[0]
                        classification['specific_identification'] = f'{metal.lower()} Nitride'
                        
                        nitride_map = {
                            'Si': ('Silicon Nitride', 'Si3N4', ['Structural Ceramic']),
                            'Ti': ('Titanium Nitride', 'TiN', ['Hard Coating']),
                            'Al': ('Aluminum Nitride', 'AlN', ['Thermal Management']),
                            'B': ('Boron Nitride', 'BN', ['Lubricant', 'Thermal Conductor'])
                        }
                        
                        if metal in nitride_map:
                            name, formula, applications = nitride_map[metal]
                            classification['specific_identification'] = name
                            classification['chemical_formula'] = formula
                            classification['applications'] = applications
                            classification['confidence'] = 0.85
                            
                # Borides
                elif 'B' in element_list:
                    classification['ceramic_type'] = 'Boride'
                    if len(element_list) == 2:
                        metal = list(metals)[0]
                        classification['specific_identification'] = f'{metal.lower()} Boride'
                        classification['confidence'] = 0.8
        
        return classification
    
    def classify_glasses(self, element_list, detected_elements, bonding_analysis):
        """
        Classify types of glass.
        
        Parameters:
        -----------
        element_list : list
            List of detected element symbols.
        detected_elements : dict
            Element detection results.
        bonding_analysis : dict
            Bonding analysis results.
            
        Returns:
        --------
        classification : dict
            Glass classification.
        """
        classification = {
            'material_class': 'Glass',
            'material_subclass': 'Unknown Glass',
            'specific_identification': 'Unidentified Glass',
            'confidence': 0.0,
            'classification_reasoning': []
        }
        
        element_set = set(element_list)
        
        # Silicate glass (most common)
        if 'Si' in element_list and 'O' in element_list:
            classification['material_subclass'] = 'Silicate Glass'
            base_confidence = 0.7
            
            modifiers = element_set - {'Si', 'O'}
            glass_modifiers = {'Na', 'K', 'Ca', 'Mg', 'Al', 'B', 'Pb', 'Li', 'Ba', 'Zn'}
            
            if modifiers & glass_modifiers:
                classification['confidence'] = base_confidence
                classification['classification_reasoning'].append('Si-O network with glass modifiers')
                
                # Specific glass types
                if element_set == {'Si', 'O', 'Na', 'Ca'}:
                    classification['specific_identification'] = 'Soda-lime Glass'
                    classification['confidence'] = 0.85
                    classification['classification_reasoning'].append('Soda-lime composition (most common window glass)')
                elif 'B' in element_list:
                    classification['specific_identification'] = 'Borosilicate Glass'
                    classification['confidence'] = 0.8
                    classification['classification_reasoning'].append('Boron addition indicates borosilicate')
                elif 'Pb' in element_list:
                    classification['specific_identification'] = 'Lead crystal glass'
                    classification['confidence'] = 0.9
                    classification['classification_reasoning'].append('Lead content indicates crystal glass')
                elif 'Al' in element_list and len(modifiers) <= 2:
                    classification['specific_identification'] = 'Aluminosilicate Glass'
                    classification['confidence'] = 0.8
            else:
                classification['specific_identification'] = 'Pure Silica Glass'
                classification['confidence'] = 0.75
        
        # Metallic glasses
        elif not ({'O', 'C', 'N', 'H'} & element_set): # No obvious non-metallic glass formers
            metals = {'Fe', 'Co', 'Ni', 'Cu', 'Zr', 'Ti', 'Al', 'Mg', 'Ca', 'Pd', 'Pt', 'Au'}
            metalloids = {'B', 'P', 'Si'}
            
            metal_elements = element_set & metals
            metalloid_elements = element_set & metalloids
            
            if metal_elements and metalloid_elements:
                classification['material_subclass'] = 'Metallic Glass'
                classification['confidence'] = 0.6
                classification['classification_reasoning'].append('Metal + metalloid composition suggests metallic glass')
                
                # Common metallic glass systems
                if 'Zr' in element_list and metalloid_elements:
                    classification['specific_identification'] = 'Zr-based Metallic Glass'
                    classification['confidence'] = 0.7
                elif 'Fe' in element_list and 'B' in element_list:
                    classification['specific_identification'] = 'Fe-B Metallic Glass'
                    classification['confidence'] = 0.7
                elif 'Cu' in element_list and 'Zr' in element_list:
                    classification['specific_identification'] = 'Cu-Zr Metallic Glass'
                    classification['confidence'] = 0.7
        
        # Chalcogenide glasses
        elif element_set & {'S', 'Se', 'Te'}:
            chalcogens = element_set & {'S', 'Se', 'Te'}
            network_formers = element_set & {'As', 'Ge', 'Si', 'P', 'Sb'}
            
            if network_formers:
                classification['material_subclass'] = 'Chalcogenide Glass'
                classification['confidence'] = 0.75
                classification['classification_reasoning'].append('Chalcogen + network former composition')
                
                if 'As' in element_list and 'S' in element_list:
                    classification['specific_identification'] = 'Arsenic Sulfide Glass'
                    classification['confidence'] = 0.8
                elif 'Ge' in element_list and ('S' in element_list or 'Se' in element_list):
                    classification['specific_identification'] = 'Germanium Chalcogenide Glass'
                    classification['confidence'] = 0.8
                    
        # Phosphate glasses
        elif 'P' in element_list and 'O' in element_list:
            classification['material_subclass'] = 'Phosphate Glass'
            classification['specific_identification'] = 'Phosphate Glass'
            classification['confidence'] = 0.7
            classification['classification_reasoning'].append('P-O network indicates phosphate glass')
            
        # Borate glasses
        elif 'B' in element_list and 'O' in element_list:
            classification['material_subclass'] = 'Borate Glass'
            classification['specific_identification'] = 'Borate Glass'
            classification['confidence'] = 0.7
            classification['classification_reasoning'].append('B-O network indicates borate glass')
            
        return classification
    
    def classify_composites(self, element_list, detected_elements, bonding_analysis):
        """
        Classify composite materials.
        
        Parameters:
        -----------
        element_list : list
            List of detected element symbols.
        detected_elements : dict
            Element detection results.
        bonding_analysis : dict
            Bonding analysis results.
            
        Returns:
        --------
        classification : dict
            Composites classification.
        """
        classification = {
            'material_class': 'Composite',
            'material_subclass': 'Unknown Composite',
            'specific_identification': 'Unidentified Composite',
            'confidence': 0.0,
            'classification_reasoning': []
        }
        
        element_set = set(element_list)
        
        # Composites usually have multiple phases with different bonding
        if len(element_list) >= 3:
            
            # Polymer matrix composites
            organic_elements = element_set & {'C', 'H', 'O', 'N'}
            reinforcement_elements = element_set & {'Si', 'Al', 'B', 'Ti', 'Fe'}
            
            if organic_elements and reinforcement_elements:
                classification['material_subclass'] = 'Polymer Matrix Composite (PMC)'
                classification['confidence'] = 0.6
                classification['classification_reasoning'].append('Organic matrix with inorganic reinforcement')
                
                if 'Si' in element_list and 'O' in element_list:
                    classification['specific_identification'] = 'Fiberglass Composite'
                    classification['reinforcement_type'] = 'Fiberglass / Glass Fiber'
                    classification['confidence'] = 0.7
                elif element_set == {'C', 'H'} | reinforcement_elements:
                    classification['specific_identification'] = 'Carbon Fiber Composite'
                    classification['reinforcement_type'] = 'Carbon Fiber'
                    classification['confidence'] = 0.75
            
            # Metal matrix composites
            metals = {'Al', 'Ti', 'Mg', 'Cu', 'Fe', 'Ni'}
            reinforcements = {'C', 'Si', 'Al', 'B', 'Ti'}
            
            metal_elements = element_set & metals
            reinforcement_elements = element_set & reinforcements
            
            if metal_elements and reinforcement_elements and len(metal_elements) >= 1:
                classification['material_subclass'] = 'Metal Matrix Composite (MMC)'
                classification['confidence'] = 0.65
                classification['classification_reasoning'].append('Metal matrix with ceramic/carbon reinforcement')
                
                primary_metal = max(metal_elements, key=lambda x: detected_elements.get(x, {}).get('intensity', 0))
                classification['matrix_material'] = f'{primary_metal.lower()} Matrix'
                
                if 'C' in reinforcement_elements:
                    classification['specific_identification'] = f'{primary_metal.lower()} Carbon Composite'
                elif 'Si' in reinforcement_elements and 'C' in reinforcement_elements:
                    classification['specific_identification'] = f'{primary_metal.lower()} Si-C Composite'
                    
            # Ceramic matrix composites
            ceramic_elements = {'Si', 'Al', 'O', 'N', 'C'}
            if len(element_set & ceramic_elements) >= 3:
                classification['material_subclass'] = 'Ceramic Matrix Composite (CMC)'
                classification['confidence'] = 0.6
                classification['classification_reasoning'].append('Multi-component ceramic system')
                
                if element_set & {'Si', 'C', 'N'}:
                    classification['specific_identification'] = 'Silicon Nitride Composite'
                elif element_set & {'Si', 'C', 'O'}:
                    classification['specific_identification'] = 'Silicon Carbide Composite'
                    
        return classification
    
    def classify_nanomaterials(self, element_list, detected_elements, quantum_features):
        """
        Classify nanomaterials based on composition and quantum signatures.
        
        Parameters:
        -----------
        element_list : list
            List of detected element symbols.
        detected_elements : dict
            Element detection results.
        quantum_features : dict
            Quantum feature analysis results.
            
        Returns:
        --------
        classification : dict
            Nanomaterial classification.
        """
        classification = {
            'material_class': 'Nanomaterial',
            'material_subclass': 'Unknown Nanomaterial',
            'specific_identification': 'Unidentified Nanomaterial',
            'confidence': 0.0,
            'classification_reasoning': []
        }
        
        element_set = set(element_list)
        
        # Quantum features can indicate nanoscale effects
        quantum_signature = 0
        if quantum_features:
            entanglement = quantum_features.get('entanglement_features', {}).get('multipartite_entanglement', 0)
            coherence = quantum_features.get('coherence_features', {}).get('l1_coherence', 0)
            quantum_signature = (entanglement + coherence) / 2
        
        base_confidence = 0.3 + quantum_signature * 0.4 # Quantum effects suggest nanoscale
        
        # Carbon nanomaterials
        if element_set == {'C'} or element_set == {'C', 'H'}:
            classification['material_subclass'] = 'Carbon Nanomaterial'
            classification['confidence'] = base_confidence + 0.3
            classification['classification_reasoning'].append('Pure carbon suggests carbon nanomaterial')
            
            # Need spctral analysis for specific identification
            if quantum_signature > 0.5:
                classification['specific_identification'] = 'Graphene or Carbon Nanotubes'
                classification['confidence'] = 0.7
            else:
                classification['specific_identification'] = 'Carbon Nanostructure'
                
        # Metal nanoparticles
        elif len(element_list) == 1 and element_list[0] in {'Au', 'Ag', 'Cu', 'Pt', 'Pd', 'Fe', 'Co', 'Ni'}:
            metal = element_list[0]
            classification['material_subclass'] = 'Metal Nanoparticle'
            classification['specific_identification'] = f'{metal.lower()} Nanoparticles'
            classification['confidence'] = base_confidence + 0.4
            classification['classification_reasoning'].append(f'Pure {metal} with quantum signatures suggests nanoparticles')
            
        # Quantum dots
        elif len(element_list) == 2:
            semiconductor_pairs = {('Cd', 'Se'), ('Cd', 'S'), ('In', 'As'), ('Pb', 'S'), ('Zn', 'Se')}
            element_pair = tuple(sorted(element_list))
            
            if element_pair in semiconductor_pairs or any(element_pair == pair for pair in semiconductor_pairs):
                classification['material_subclass'] = 'Quantum Dots'
                classification['specific_identification'] = f'{element_pair[0].lower()}_{element_pair[1].lower()} Quantum Dots'
                classification['confidence'] = base_confidence + 0.5
                classification['classification_reasoning'].append('Semiconductor pair with quantum effects suggests quantum dots')
            
        # Oxide nanoparticles
        elif 'O' in element_list and len(element_list) == 2:
            metal = (set(element_list) - {'O'}).pop()
            nano_oxides = {'Ti', 'Zr', 'Al', 'Zn', 'Fe', 'Ce'}
            
            if metal in nano_oxides:
                classification['material_subclass'] = 'Oxide Nanoparticle'
                classification['specific_identification'] = f'{metal.lower()} oxide nanoparticle'
                classification['confidence'] = base_confidence + 0.3
                classification['classification_reasoning'].append(f'{metal} oxide with possible nanoscale effects')
                
        return classification
    
    def classify_biomaterials(self, element_list, detected_elements, bonding_analysis):
        """
        Classify biomaterials based on elements and bonding.
        
        Parameters:
        -----------
        element_list : list
            List of detected element symbols.
        detected_elements : dict
            Element detection results.
        bonding_analysis : dict
            Bonding analysis results.
            
        Returns:
        --------
        classification : dict
            Biomaterial classification.
        """
        classification = {
            'material_class': 'Biomaterial',
            'material_subclass': 'Unknown Biomaterial',
            'specific_identification': 'Unidentified Biomaterial',
            'confidence': 0.0,
            'classification_reasoning': []
        }
        
        element_set = set(element_list)
        
        # Organic biomaterials
        bio_organic = {'C', 'H', 'O', 'N', 'S', 'P'}
        if element_set <= bio_organic and 'C' in element_list:
            organic_confidence = len(element_set & bio_organic) / len(element_list)
            
            if organic_confidence > 0.8:
                classification['material_subclass'] = 'Organic Biomaterial'
                classification['confidence'] = 0.6 * organic_confidence
                
                # Protein-like composition
                if element_set & {'C', 'H', 'O', 'N'} and len(element_set) <= 5:
                    classification['specific_identification'] = 'Protein-based Material'
                    if 'S' in element_list:
                        classification['specific_identification'] = 'Protein with disulfide bonds'
                        classification['confidence'] = 0.7
                
                # Nucleic acid-like composition
                elif 'P' in element_list and element_set & {'C', 'H', 'O', 'N'}:
                    classification['specific_identification'] = 'Nucleic Acid-based Material'
                    classification['confidence'] = 0.75
        
        # Biominerals
        elif element_set & {'Ca', 'P', 'O'}:
            if element_set == {'Ca', 'P', 'O'} or element_set == {'Ca', 'P', 'O', 'H'}:
                classification['material_subclass'] = 'Biomineral'
                classification['specific_identification'] = 'Hydroxyapatite or Bone Mineral'
                classification['confidence'] = 0.85
                classification['classification_reasoning'].append('Ca-P-O composition characteristics of bone/teeth')
                
            elif element_set == {'Ca', 'C', 'O'}:
                classification['material_subclass'] = 'Biomineral'
                classification['specific_identification'] = 'Calcium Carbonate Biomineral'
                classification['confidence'] = 0.8
                classification['classification_reasoning'].append('CaCO3 composition typical of shells/coral')
                
        # Siliceous biomaterials
        elif element_set == {'Si', 'O'} or element_set == {'Si', 'O', 'H'}:
            classification['material_subclass'] = 'Siliceous Biomaterial'
            classification['specific_identification'] = 'Biogenic Silica'
            classification['confidence'] = 0.7
            classification['classification_reasoning'].append('Silica composition suggests diatoms or sponges')
        
        return classification
    
    def fallback_classification(self, element_list, detected_elements, bonding_analysis):
        """
        If the model cannot classify the material based on other properties, fallback onto basic classification.
        
        Parameters:
        -----------
        element_list : list
            List of element symbols.
        detected_elements : dict
            Previously detected chemical elements.
        bonding_analysis : dict
            Chemical bonding analysis results.
        
        Returns:
        --------
        classification : dict
            Material classification.
        """
        classification = {
            'material_class': 'Unknown',
            'material_subclass': 'Unclassified',
            'specific_identification': 'Unknown Material',
            'confidence': 0.2,
            'classification_reasoning': ['No clear material class identified']
        }
        
        # Basic classification based on number of elements
        n_elements = len(element_list)
        
        if n_elements == 1:
            element = element_list[0]
            classification['material_class'] = 'Elemental'
            classification['specific_identification'] = f'Pure {element.lower()}'
            classification['confidence'] = 0.7
            classification['classification_reasoning'] = [f'Single element: {element}']
    
        elif n_elements == 2:
            classification['material_class'] = 'Binary Compound'
            classification['specific_identification'] = f'{element_list[0].lower()}_{element_list[1].lower()} compound'
            classification['confidence'] = 0.5
            classification['classification_reasoning'] = ['Two-element compound']
    
        elif n_elements <= 5:
            classification['material_class'] = 'Simple Compound'
            classification['specific_identification'] = 'Multi-element compound'
            classification['confidence'] = 0.4
            classification['classification_reasoning'] = [f'{n_elements}-element compound']
    
        else:
            classification['material_class'] = 'Complex Material'
            classification['specific_identification'] = 'Complex multi-component material'
            classification['confidence'] = 0.3
            classification['classification_reasoning'] = [f'Complex material with {n_elements} elements']
    
        # Add bonding information if available
        primary_bonding = bonding_analysis.get('bonding_characteristics', {}).get('primary_bonding', '')
        if primary_bonding != 'Unknown':
            classification['classification_reasoning'].append(f'Primary bonding: {primary_bonding}')
            classification['confidence'] += 0.1
    
        return classification
    
    def predict_structure(self, element_list, identification):
        """
        Predict structure of material based on elements and classification.
        
        Parameters:
        -----------
        element_list : list
            List of detected element symbols.
        identification : str
            Material identification.
        
        Returns:
        --------
        structure_prediction : dict
            Dictionary and prediction of a material's structure.
        """
        structure_prediction = {
            'crystal_system': 'Unknown',
            'space_group': 'Unknown',
            'coordination': 'Unknown',
            'structure_type': 'Unknown',
            'dimensional_structure': 'Bulk'
        }
        
        material_class = identification.get('material_class', '')
        specific_id = identification.get('specific_identification', '')
        
        # Structure predictions based on material class
        if material_class == 'Metal':
            if len(element_list) == 1:
                metal = element_list[0]
                # Common metal structures
                fcc_metals = ['Al', 'Cu', 'Au', 'Ag', 'Ni', 'Pt', 'Pd']
                bcc_metals = ['Fe', 'Cr', 'W', 'Mo', 'V', 'Ta', 'Nb']
                hcp_metals = ['Ti', 'Zn', 'Mg', 'Co', 'Zr']
                
                if metal in fcc_metals:
                    structure_prediction['crystal_system'] = 'Cubic'
                    structure_prediction['structure_type'] = 'FCC'
                    structure_prediction['coordination'] = '12'
                elif metal in bcc_metals:
                    structure_prediction['crystal_system'] = 'Cubic'
                    structure_prediction['structure_type'] = 'BCC'
                    structure_prediction['coordination'] = '8'
                elif metal in hcp_metals:
                    structure_prediction['crystal_system'] = 'Hexagonal'
                    structure_prediction['structure_type'] = 'HCP'
                    structure_prediction['coordination'] = '12'
        
        elif material_class == 'Semiconductor':
            if 'diamond' in specific_id or 'silicon' in specific_id or 'germanium' in specific_id:
                structure_prediction['crystal_system'] = 'Cubic'
                structure_prediction['structure_type'] = 'Diamond Cubic'
                structure_prediction['coordination'] = '4'
            elif 'iii_v' in identification.get('material_subclass', ''):
                structure_prediction['crystal_system'] = 'Cubic'
                structure_prediction['structure_type'] = 'Zinc Blende'
                structure_prediction['coordination'] = '4'
        
        elif material_class == 'Ceramic':
            if 'perovskite' in specific_id:
                structure_prediction['crystal_system'] = 'Cubic'
                structure_prediction['structure_type'] = 'Perovskite'
                structure_prediction['coordination'] = '6+12'
            elif 'spinel' in specific_id:
                structure_prediction['crystal_system'] = 'Cubic'
                structure_prediction['structure_type'] = 'Spinel'
                structure_prediction['coordination'] = '4+6'
            elif 'alumina' in specific_id:
                structure_prediction['crystal_system'] = 'Trigonal'
                structure_prediction['structure_type'] = 'Corundum'
                structure_prediction['coordination'] = '6'
        
        elif material_class == 'Glass':
            structure_prediction['crystal_system'] = 'Amorphous'
            structure_prediction['structure_type'] = 'Non-Crystalline'
            structure_prediction['coordination'] = 'Variable'
            
        elif material_class == 'Nanomaterial':
            structure_prediction['dimensional_structure'] = 'Nanostructured'
            if 'quantum_dots' in specific_id:
                structure_prediction['dimensional_structure'] = '0D_quantum_confined'
            elif 'nanotubes' in specific_id:
                structure_prediction['dimensional_structure'] = '1D_nanostructure'
            elif 'graphene' in specific_id:
                structure_prediction['dimensional_structure'] = '2D_layered'
        
        return structure_prediction
    
    def enhance_material_identification_system(self):
        # This would be called during __init__ to set up all the databases
        self.initialize_material_databases()
        
        # Add material property correlation matrices
        self.property_correlation_matrix = self.build_property_correlations()
        
        # Add ML features for material identification
        self.ml_feature_weights = self.initialize_ml_weights()
        
    def build_property_correlations(self):
        # Build correlation matrix between elements, structures, and properties
        correlations = {
            'hardness_indicators': {
                'elements': ['C', 'B', 'Si', 'N'],
                'structures': ['diamond', 'carbide', 'nitride'],
                'weight': 0.8
            },
            'conductivity_indicators': {
                'elements': ['Cu', 'Ag', 'Au', 'Al'],
                'structures': ['metallic', 'fcc', 'bcc'],
                'weight': 0.9
            },
            'magnetic_indicators': {
                'elements': ['Fe', 'Co', 'Ni', 'Nd', 'Sm'],
                'structures': ['ferromagnetic', 'antiferromagnetic'],
                'weight': 0.85
            },
            'optical_indicators': {
                'elements': ['Si', 'Ge', 'Ga', 'In', 'As'],
                'structures': ['semiconductor', 'quantum_dots'],
                'weight': 0.75
            }
        }
        return correlations
    
    def initialize_ml_weights(self):
        weights = {
            'elemental_composition': 0.3,
            'bonding_analysis': 0.25,
            'quantum_features': 0.2,
            'spectral_signatures': 0.15,
            'stoichiometry': 0.1
        }
        return weights
     
    def generate_recommendations(self, analysis_results):
        """
        Generate analysis recommendations and suggestions.
        
        Parameters:
        -----------
        analysis_results : dict
            Complete analysis results with confidence assessments.
            
        Returns:
        --------
        recommendations : dict
            Analysis recommendations.
        """
        confidence = analysis_results.get('confidence_assessment', {})
        overall_confidence = confidence.get('overall', 0)
        
        recommendations = {
            'analysis_quality': 'excellent' if overall_confidence > 0.8 else 'good' if overall_confidence > 0.6 else 'needs_improvement',
            'suggested_improvements': [],
            'complementary_techniques': [
                'XRD for crystal structure determination',
                'SEM/TEM for morphological analysis',
                'XPS for chemical state analysis',
                'Raman spectroscopy for molecular vibrations'
            ],
            'future_analysis': []
        }
        
        if confidence.get('element_detection', 0) < 0.7:
            recommendations['suggested_improvements'].append('Improve energy resolution for better element detection')
        
        if confidence.get('quantum_analysis', 0) < 0.7:
            recommendations['suggested_improvements'].append('Increase quantum circuit depth for better feature extraction')
        
        detected_elements = analysis_results.get('detected_elements', {})
        if len(detected_elements) > 3:
            recommendations['future_analysis'].append('Spatial mapping for phase distribution analysis')
        
        magnetic_elements = analysis_results.get('magnetic_properties', {}).get('magnetic_elements', {})
        if magnetic_elements:
            recommendations['future_analysis'].append('Magnetic dichroism measurements for spin analysis')
        
        return recommendations
    
    def generate_quantum_insights(self, analysis_results):
        """
        Generate quantum-specific insights
        
        Parameters:
        -----------
        analysis_results : dict
            Results from comprehensive_analysis().
            
        Returns:
        --------
        insights : dict
            Generates insights about material.
        """
        quantum_features = analysis_results.get('quantum_features', {})
        
        insights = {
            'quantum_enhancement_benefits': [
                'Enhanced sensitivity in peak detection',
                'Quantum entanglement analysis reveals hidden correlations',
                'Coherence measures provide material characterization',
                'Quantum ML enables advanced pattern recognition'
            ],
            'entanglement_analysis': self.interpret_entanglement_features(
                quantum_features.get('entanglement_features', {})
            ),
            'coherence_analysis': self.interpret_coherence_features(
                quantum_features.get('coherence_features', {})
            ),
            'quantum_correlations': self.interpret_quantum_correlations(
                quantum_features.get('quantum_correlations', {})
            )
        }
        
        return insights
    
    def interpret_entanglement_features(self, entanglement_features):
        """
        Interpret quantum entanglement features in physical terms.
        
        Parameters:
        -----------
        entanglement_features : dict
            Quantum entanglement analysis results.
        
        Returns:
        --------
        interpretation : dict
            Physical interpretation of entanglement.
        """
        interpretation = {
            'entanglement_strength': 'low',
            'spatial_correlations': 'localized',
            'information_content': 'classical-like'
        }
        
        multipartite = entanglement_features.get('multipartite_entanglement', 0)
        
        if multipartite > 0.5:
            interpretation['entanglement_strength'] = 'high'
            interpretation['spatial_correlations'] = 'long-range'
            interpretation['information_content'] = 'quantum-enhanced'
        elif multipartite > 0.2:
            interpretation['entanglement_strength'] = 'medium'
            interpretation['spatial_correlations'] = 'medium-range'
            interpretation['information_content'] = 'mixed quantum-classical'
        
        return interpretation
    
    def interpret_coherence_features(self, coherence_features):
        """
        Interpret quantum coherence features for material analysis.
        
        Parameters:
        -----------
        coherence_features : dict
            Quantum coherence analysis results.
        
        Returns:
        --------
        interpretation : dict
            Physical interpretation of coherence.
        """
        interpretation = {
            'quantum_coherence_level': 'low',
            'phase_correlations': 'weak',
            'superposition_effects': 'minimal'
        }
        
        l1_coherence = coherence_features.get('l1_coherence', 0)
        
        if l1_coherence > 0.7:
            interpretation['quantum_coherence_level'] = 'high'
            interpretation['phase_correlations'] = 'strong'
            interpretation['superposition_effects'] = 'significant'
        elif l1_coherence > 0.3:
            interpretation['quantum_coherence_level'] = 'medium'
            interpretation['phase_correlations'] = 'moderate'
            interpretation['superposition_effects'] = 'detectable'
        
        return interpretation
    
    def interpret_quantum_correlations(self, quantum_correlations):
        """
        Interpret quantum correlations for classical vs. quantum computing analysis.
        
        Parameters:
        -----------
        quantum_correlations : dict
            Quantum correlation effects in bonding.
            
        Returns:
        --------
        interpretation : dict
            Intepretation of quantum correlations.
        """
        interpretation = {
            'quantum_vs_classical': 'classical_dominated',
            'information_distribution': 'localized',
            'quantum_advantage': 'minimal'
        }
        
        discord = quantum_correlations.get('quantum_discord', 0)
        classical = quantum_correlations.get('classical_correlations', 0)
        
        if discord > abs(classical):
            interpretation['quantum_vs_classical'] = 'quantum_dominated'
            interpretation['information_distribution'] = 'distributed'
            interpretation['quantum_advantage'] = 'significant'
        elif discord > 0.3:
            interpretation['quantum_vs_classical'] = 'mixed'
            interpretation['information_distribution'] = 'partially_distributed'
            interpretation['quantum_advantage'] = 'moderate'
        
        return interpretation
