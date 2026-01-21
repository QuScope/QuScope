"""Quantum EELS (Electron Energy Loss Spectroscopy) analysis module."""

from quscope.eels_analysis.analysis import EELSAnalyzer
from quscope.eels_analysis.eels_utils import (
    ElementSubstitutionEngine,
    SpatialMappingEngine,
)
from quscope.eels_analysis.preprocessing import (
    extract_eels_features,
    preprocess_eels_data,
)
from quscope.eels_analysis.quantum_processing import (
    QuantumCircuitLibrary,
    QuantumFeatureExtractor,
    QuantumMLProcessor,
    QuantumPreprocessor,
)

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
    EELSAnalyzer,
]
