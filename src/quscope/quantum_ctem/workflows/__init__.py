"""
Quantum CTEM Workflows.

This module provides end-to-end workflows for quantum CTEM simulation
of different materials. Each workflow handles:
- Structure generation
- Microscope parameter setup
- Quantum circuit construction
- Simulation execution (simulator or IBM hardware)
- Result visualization and validation

Available Workflows:
    - MoS2Workflow: For MoS₂ 2D materials
    - GrapheneWorkflow: For graphene and carbon nanostructures

Usage:
    from quscope.quantum_ctem.workflows import MoS2Workflow, GrapheneWorkflow
    from quscope.quantum_ctem.backends import get_backend

    # Setup backend
    backend = get_backend("simulator")

    # Run MoS2 workflow
    workflow = MoS2Workflow(backend=backend, voltage=200e3)
    results = workflow.run(nx=3, ny=2, grid_size=64)

    # Run Graphene workflow
    workflow = GrapheneWorkflow(backend=backend, voltage=200e3)
    results = workflow.run(nx=5, ny=5, grid_size=64)
"""

from .base import CTEMWorkflow, MicroscopeConfig, SimulationResult
from .mos2 import MoS2Workflow
from .graphene import GrapheneWorkflow

__all__ = [
    "CTEMWorkflow",
    "MicroscopeConfig",
    "SimulationResult",
    "MoS2Workflow",
    "GrapheneWorkflow",
]
