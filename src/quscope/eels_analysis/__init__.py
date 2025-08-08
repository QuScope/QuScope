"""Quantum EELS (Electron Energy Loss Spectroscopy) analysis module."""

from quscope.eels_analysis.preprocessing import preprocess_eels_data, extract_eels_features
from quscope.eels_analysis.quantum_processing import QuantumCircuitLibrary, QuantumPreprocessor, QuantumFeatureExtractor, QuantumMLProcessor
from quscope.eels_analysis.eels_utils import ElementSubstitutionEngine, SpatialMappingEngine
from quscope.eels_analysis.analysis import EELSAnalyzer

__version__ = "0.1.0"
__all__ = [
    preprocess_eels_data,
    extract_eels_features,
    QuantumCircuitLibrary,
    QuantumPreprocessor,
    QuantumFeatureExtractor,
    QuantumMLProcessor,
    ElementSubstitutionEngine,
    SpatialMappingEngine,
    EELSAnalyzer
]
