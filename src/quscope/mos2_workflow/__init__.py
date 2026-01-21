"""MoS2 workflow package - focused utilities for MoS2 simulations and visualization.

NOTE: This module requires optional dependencies:
- ase (Atomic Simulation Environment)
- matplotlib

Install with: pip install quscope[microscopy,viz]
"""

from .backend import connect_backend
from .hamiltonian import get_interaction_constant, render_quantum_circuit
from .microscope import MicroscopeParams
from .orchestrator import run_comparison

# Visualization functions require matplotlib and ase
try:
    from .viz import build_mos2, compare_projected_potentials, plot_structure_caxis

    _VIZ_AVAILABLE = True
except ImportError:
    _VIZ_AVAILABLE = False

    def _missing_dep_error(*args, **kwargs):
        raise ImportError(
            "Visualization functions require 'ase' and 'matplotlib'. "
            "Install with: pip install quscope[microscopy,viz]"
        )

    build_mos2 = _missing_dep_error
    plot_structure_caxis = _missing_dep_error
    compare_projected_potentials = _missing_dep_error

__all__ = [
    "build_mos2",
    "plot_structure_caxis",
    "compare_projected_potentials",
    "MicroscopeParams",
    "get_interaction_constant",
    "render_quantum_circuit",
    "connect_backend",
    "run_comparison",
]
