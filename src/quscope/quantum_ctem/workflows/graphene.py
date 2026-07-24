"""
Graphene Quantum CTEM Workflow.

Complete workflow for quantum simulation of graphene CTEM images,
optimized for weak phase object validation and honeycomb lattice imaging.
"""

from typing import Dict, List, Optional, Tuple

import numpy as np

from ..backends.base import Backend
from ..materials import Graphene
from .base import CTEMWorkflow, MicroscopeConfig, SimulationResult


class GrapheneWorkflow(CTEMWorkflow):
    """
    Quantum CTEM workflow for Graphene.

    Graphene is ideal for quantum CTEM simulation validation because:
    - Light atoms (C, Z=6) give excellent WPOA validity
    - Honeycomb lattice provides clear symmetry tests
    - Well-characterized diffraction pattern for validation
    - Single-atom thickness eliminates multislice complexity

    Examples:
        >>> from quscope.quantum_ctem.backends import get_backend
        >>> from quscope.quantum_ctem.workflows import GrapheneWorkflow

        >>> # Quick simulation with simulator
        >>> backend = get_backend("simulator")
        >>> workflow = GrapheneWorkflow(backend=backend)
        >>> result = workflow.run(nx=5, ny=5, grid_size=64)
        >>> print(result.summary())

        >>> # With IBM hardware
        >>> backend = get_backend("ibm", device_name="ibm_kyoto")
        >>> workflow = GrapheneWorkflow(backend=backend, voltage=80e3)
        >>> result = workflow.run(nx=5, ny=5, grid_size=64, shots=4096)

        >>> # Nanoribbon simulation
        >>> result = workflow.run_nanoribbon(width=10, length=20, edge_type="zigzag")
    """

    def __init__(
        self,
        backend: Backend,
        voltage: float = 80e3,  # Lower voltage better for graphene
        defocus: Optional[float] = None,
        cs: float = 0.001,  # Aberration-corrected for graphene
        edge_type: str = "zigzag",
        **kwargs,
    ):
        """
        Initialize Graphene workflow.

        Args:
            backend: Quantum backend (simulator or IBM)
            voltage: Accelerating voltage in V (default: 80 kV for graphene)
            defocus: Defocus in Å (default: Scherzer defocus)
            cs: Spherical aberration in mm (default: near-zero, corrected)
            edge_type: Edge type for nanoribbons ("zigzag" or "armchair")
        """
        material = Graphene(edge_type=edge_type)

        # Setup microscope - lower voltage, aberration-corrected for graphene
        microscope = MicroscopeConfig(voltage=voltage, cs=cs)
        if defocus is None:
            defocus = microscope.scherzer_defocus
        microscope.defocus = defocus

        super().__init__(material, backend, microscope, **kwargs)
        self.edge_type = edge_type

    def build_structure(
        self,
        nx: int = 5,
        ny: int = 5,
        vacuum: float = 10.0,
        **kwargs,
    ):
        """
        Build graphene supercell.

        Args:
            nx: Unit cells in x direction
            ny: Unit cells in y direction
            vacuum: Vacuum padding in Å

        Returns:
            ASE Atoms object
        """
        return self.material.build_structure(nx=nx, ny=ny, vacuum=vacuum)

    def run(
        self,
        nx: int = 5,
        ny: int = 5,
        grid_size: int = 64,
        pixel_size: float = 0.05,  # Finer for graphene
        shots: int = 0,
        apply_ctf: bool = True,
        compare_classical: bool = False,
        vacuum: float = 10.0,
    ) -> SimulationResult:
        """
        Run graphene quantum CTEM simulation.

        Args:
            nx: Unit cells in x
            ny: Unit cells in y
            grid_size: Grid size (must be power of 2)
            pixel_size: Pixel size in Å (default finer for graphene)
            shots: Measurement shots (0 for statevector)
            apply_ctf: Apply contrast transfer function
            compare_classical: Run classical comparison
            vacuum: Vacuum padding in Å

        Returns:
            SimulationResult with complete simulation data
        """
        result = super().run(
            grid_size=grid_size,
            pixel_size=pixel_size,
            shots=shots,
            apply_ctf=apply_ctf,
            compare_classical=compare_classical,
            nx=nx,
            ny=ny,
            vacuum=vacuum,
        )

        # Update supercell size in result
        result.supercell_size = (nx, ny)

        # Add WPOA validity check
        validity = self.material.wpoa_validity(self.microscope.voltage)
        result.wpoa_valid = validity["wpoa_valid"]
        result.max_phase_shift = validity["max_phase_shift"]

        return result

    def run_nanoribbon(
        self,
        width: int = 10,
        length: int = 20,
        edge_type: Optional[str] = None,
        grid_size: int = 64,
        pixel_size: float = 0.05,
        shots: int = 0,
        apply_ctf: bool = True,
        saturated: bool = False,
    ) -> SimulationResult:
        """
        Run quantum CTEM simulation of graphene nanoribbon.

        Args:
            width: Ribbon width in unit cells
            length: Ribbon length in unit cells
            edge_type: "zigzag" or "armchair" (default: instance setting)
            grid_size: Grid size
            pixel_size: Pixel size in Å
            shots: Measurement shots
            apply_ctf: Apply CTF
            saturated: Saturate edges with hydrogen

        Returns:
            SimulationResult for nanoribbon
        """
        import time

        start_time = time.time()

        # Build nanoribbon
        edge = edge_type or self.edge_type
        atoms = self.material.build_nanoribbon(
            width=width,
            length=length,
            edge_type=edge,
            saturated=saturated,
        )

        # Setup quantum state
        V_proj, transmission = self.setup_quantum_state(
            atoms, grid_size=grid_size, pixel_size=pixel_size
        )

        # Build and run circuit (genuine WPOA -> QFT -> CTF -> IQFT)
        circuit = self.build_quantum_circuit(
            V_proj, grid_size=grid_size, pixel_size=pixel_size, apply_ctf=apply_ctf
        )
        from ..backends.base import BackendConfig

        config = BackendConfig(shots=shots)
        backend_result = self.backend.run(circuit, config)

        # Extract results
        if backend_result.statevector is not None:
            wavefunction = backend_result.get_statevector_2d(grid_size, grid_size)
            intensity = np.abs(wavefunction) ** 2
            intensity = intensity / intensity.mean()
            phase = np.angle(wavefunction)
        else:
            wavefunction = None
            intensity = None
            phase = None

        cell = atoms.get_cell()
        fov = (cell[0, 0], cell[1, 1])

        result = SimulationResult(
            material_name=f"Graphene Nanoribbon ({edge})",
            n_atoms=len(atoms),
            supercell_size=(width, length),
            grid_size=grid_size,
            pixel_size=pixel_size,
            field_of_view=fov,
            wavefunction=wavefunction,
            intensity=intensity,
            phase=phase,
            projected_potential=V_proj,
            transmission_function=transmission,
            microscope_config=self.microscope,
            backend_result=backend_result,
            execution_time=time.time() - start_time,
            circuit_depth=circuit.depth(),
            n_qubits=circuit.num_qubits,
        )

        return result

    def run_with_vacancies(
        self,
        nx: int = 10,
        ny: int = 10,
        vacancy_fraction: float = 0.02,
        grid_size: int = 64,
        pixel_size: float = 0.05,
        shots: int = 0,
        seed: Optional[int] = None,
    ) -> SimulationResult:
        """
        Run simulation of graphene with vacancy defects.

        Args:
            nx, ny: Supercell size
            vacancy_fraction: Fraction of atoms to remove (0-1)
            grid_size: Grid size
            pixel_size: Pixel size in Å
            shots: Measurement shots
            seed: Random seed for vacancy positions

        Returns:
            SimulationResult showing vacancy contrast
        """
        import time

        start_time = time.time()

        # Build defective graphene
        atoms = self.material.build_with_vacancy(
            nx=nx,
            ny=ny,
            vacancy_fraction=vacancy_fraction,
            seed=seed,
        )

        # Setup and run
        V_proj, transmission = self.setup_quantum_state(
            atoms, grid_size=grid_size, pixel_size=pixel_size
        )
        circuit = self.build_quantum_circuit(
            V_proj, grid_size=grid_size, pixel_size=pixel_size, apply_ctf=True
        )

        from ..backends.base import BackendConfig

        config = BackendConfig(shots=shots)
        backend_result = self.backend.run(circuit, config)

        if backend_result.statevector is not None:
            wavefunction = backend_result.get_statevector_2d(grid_size, grid_size)
            intensity = np.abs(wavefunction) ** 2
            intensity = intensity / intensity.mean()
            phase = np.angle(wavefunction)
        else:
            wavefunction = None
            intensity = None
            phase = None

        cell = atoms.get_cell()
        fov = (cell[0, 0], cell[1, 1])

        result = SimulationResult(
            material_name=f"Graphene with {vacancy_fraction*100:.1f}% vacancies",
            n_atoms=len(atoms),
            supercell_size=(nx, ny),
            grid_size=grid_size,
            pixel_size=pixel_size,
            field_of_view=fov,
            wavefunction=wavefunction,
            intensity=intensity,
            phase=phase,
            projected_potential=V_proj,
            transmission_function=transmission,
            microscope_config=self.microscope,
            backend_result=backend_result,
            execution_time=time.time() - start_time,
            circuit_depth=circuit.depth(),
            n_qubits=circuit.num_qubits,
        )

        return result

    def validate_wpoa(self) -> Dict[str, any]:
        """
        Validate WPOA approximation for current settings.

        Returns:
            Dictionary with validity metrics
        """
        return self.material.wpoa_validity(self.microscope.voltage)

    def visualize(
        self,
        result: SimulationResult,
        show_potential: bool = True,
        show_intensity: bool = True,
        show_phase: bool = True,
        show_fft: bool = True,
        figsize: Tuple[int, int] = (14, 4),
        save_path: Optional[str] = None,
    ):
        """
        Visualize graphene simulation results.

        Args:
            result: SimulationResult to visualize
            show_potential: Show projected potential
            show_intensity: Show image intensity
            show_phase: Show phase map
            show_fft: Show FFT (diffraction pattern)
            figsize: Figure size
            save_path: Path to save figure

        Returns:
            matplotlib Figure
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            raise ImportError("matplotlib required")

        n_plots = sum([show_potential, show_intensity, show_phase, show_fft])
        fig, axes = plt.subplots(1, n_plots, figsize=figsize)
        if n_plots == 1:
            axes = [axes]

        idx = 0
        extent = [0, result.field_of_view[0], 0, result.field_of_view[1]]

        if show_potential and result.projected_potential is not None:
            ax = axes[idx]
            im = ax.imshow(result.projected_potential, cmap="viridis", extent=extent)
            ax.set_title("Projected Potential V(x,y)")
            ax.set_xlabel("x (Å)")
            ax.set_ylabel("y (Å)")
            plt.colorbar(im, ax=ax, label="V·Å")
            idx += 1

        if show_intensity and result.intensity is not None:
            ax = axes[idx]
            im = ax.imshow(result.intensity, cmap="gray", extent=extent)
            ax.set_title(f"CTEM Image (Δf={result.microscope_config.defocus:.0f} Å)")
            ax.set_xlabel("x (Å)")
            ax.set_ylabel("y (Å)")
            plt.colorbar(im, ax=ax, label="Intensity")
            idx += 1

        if show_phase and result.phase is not None:
            ax = axes[idx]
            im = ax.imshow(
                result.phase,
                cmap="twilight",
                extent=extent,
                vmin=-np.pi,
                vmax=np.pi,
            )
            ax.set_title("Phase φ(x,y)")
            ax.set_xlabel("x (Å)")
            ax.set_ylabel("y (Å)")
            plt.colorbar(im, ax=ax, label="Phase (rad)")
            idx += 1

        if show_fft and result.wavefunction is not None:
            ax = axes[idx]
            fft = np.fft.fftshift(np.fft.fft2(result.wavefunction))
            fft_intensity = np.abs(fft) ** 2
            # Log scale for better visibility
            fft_log = np.log10(fft_intensity + 1)
            im = ax.imshow(fft_log, cmap="hot")
            ax.set_title("Diffraction Pattern (log)")
            ax.set_xlabel("kx")
            ax.set_ylabel("ky")
            plt.colorbar(im, ax=ax)
            idx += 1

        plt.suptitle(
            f"Graphene Quantum CTEM Simulation "
            f"({result.supercell_size[0]}×{result.supercell_size[1]} supercell, "
            f"{result.microscope_config.voltage/1e3:.0f} kV)",
            fontsize=12,
        )
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")

        return fig

    def visualize_honeycomb(
        self,
        result: SimulationResult,
        zoom_factor: float = 2.0,
        figsize: Tuple[int, int] = (10, 5),
        save_path: Optional[str] = None,
    ):
        """
        Specialized visualization highlighting honeycomb lattice.

        Args:
            result: SimulationResult
            zoom_factor: Zoom into center region
            figsize: Figure size
            save_path: Path to save figure
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            raise ImportError("matplotlib required")

        fig, axes = plt.subplots(1, 2, figsize=figsize)

        # Full view
        extent = [0, result.field_of_view[0], 0, result.field_of_view[1]]
        axes[0].imshow(result.intensity, cmap="gray", extent=extent)
        axes[0].set_title("Full View")
        axes[0].set_xlabel("x (Å)")
        axes[0].set_ylabel("y (Å)")

        # Zoomed center
        ny, nx = result.intensity.shape
        cx, cy = nx // 2, ny // 2
        zoom_size = int(nx / (2 * zoom_factor))
        zoomed = result.intensity[
            cy - zoom_size : cy + zoom_size, cx - zoom_size : cx + zoom_size
        ]
        zoom_extent = [
            result.field_of_view[0] / 2 - result.field_of_view[0] / (2 * zoom_factor),
            result.field_of_view[0] / 2 + result.field_of_view[0] / (2 * zoom_factor),
            result.field_of_view[1] / 2 - result.field_of_view[1] / (2 * zoom_factor),
            result.field_of_view[1] / 2 + result.field_of_view[1] / (2 * zoom_factor),
        ]
        axes[1].imshow(zoomed, cmap="gray", extent=zoom_extent)
        axes[1].set_title(f"Honeycomb Detail ({zoom_factor}x zoom)")
        axes[1].set_xlabel("x (Å)")

        plt.suptitle(
            f"Graphene Honeycomb Lattice at {result.microscope_config.voltage/1e3:.0f} kV"
        )
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")

        return fig
