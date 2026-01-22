"""
MoS₂ Quantum CTEM Workflow.

Complete workflow for quantum simulation of MoS₂ CTEM images,
from structure generation to result visualization.
"""

from typing import Dict, List, Optional, Tuple

import numpy as np

from ..backends.base import Backend
from ..materials import MoS2
from .base import CTEMWorkflow, MicroscopeConfig, SimulationResult


class MoS2Workflow(CTEMWorkflow):
    """
    Quantum CTEM workflow for MoS₂ (Molybdenum Disulfide).

    Provides end-to-end simulation capabilities including:
    - MoS₂ supercell generation
    - Quantum circuit construction for WPOA
    - Execution on simulators or IBM hardware
    - Comparison with classical multislice
    - Publication-quality visualization

    Examples:
        >>> from quscope.quantum_ctem.backends import get_backend
        >>> from quscope.quantum_ctem.workflows import MoS2Workflow

        >>> # Quick simulation with simulator
        >>> backend = get_backend("simulator")
        >>> workflow = MoS2Workflow(backend=backend)
        >>> result = workflow.run(nx=3, ny=2, grid_size=64)
        >>> print(result.summary())

        >>> # Production run on IBM hardware
        >>> backend = get_backend("ibm", device_name="ibm_kyoto")
        >>> workflow = MoS2Workflow(backend=backend, voltage=200e3)
        >>> result = workflow.run(nx=3, ny=2, grid_size=64, shots=4096)
    """

    def __init__(
        self,
        backend: Backend,
        voltage: float = 200e3,
        defocus: Optional[float] = None,
        cs: float = 1.3,
        layer_type: str = "1H",
        **kwargs,
    ):
        """
        Initialize MoS₂ workflow.

        Args:
            backend: Quantum backend (simulator or IBM)
            voltage: Accelerating voltage in V (default: 200 kV)
            defocus: Defocus in Å (default: Scherzer defocus)
            cs: Spherical aberration in mm (default: 1.3 mm)
            layer_type: MoS₂ structure type ("1H" or "1T")
        """
        material = MoS2(layer_type=layer_type)

        # Setup microscope with Scherzer defocus if not specified
        microscope = MicroscopeConfig(voltage=voltage, cs=cs)
        if defocus is None:
            defocus = microscope.scherzer_defocus
        microscope.defocus = defocus

        super().__init__(material, backend, microscope, **kwargs)

    def build_structure(
        self,
        nx: int = 3,
        ny: int = 2,
        vacuum: float = 10.0,
        **kwargs,
    ):
        """
        Build MoS₂ supercell.

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
        nx: int = 3,
        ny: int = 2,
        grid_size: int = 64,
        pixel_size: float = 0.1,
        shots: int = 0,
        apply_ctf: bool = True,
        compare_classical: bool = False,
        vacuum: float = 10.0,
    ) -> SimulationResult:
        """
        Run MoS₂ quantum CTEM simulation.

        Args:
            nx: Unit cells in x
            ny: Unit cells in y
            grid_size: Grid size (must be power of 2)
            pixel_size: Pixel size in Å
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

        return result

    def run_voltage_series(
        self,
        voltages: List[float] = [80e3, 120e3, 200e3, 300e3],
        nx: int = 3,
        ny: int = 2,
        grid_size: int = 64,
        pixel_size: float = 0.1,
    ) -> Dict[float, SimulationResult]:
        """
        Run simulations at multiple accelerating voltages.

        Useful for studying voltage-dependent contrast and WPOA validity.

        Args:
            voltages: List of voltages in V
            nx, ny: Supercell dimensions
            grid_size: Grid size
            pixel_size: Pixel size in Å

        Returns:
            Dictionary mapping voltage to SimulationResult
        """
        results = {}
        original_voltage = self.microscope.voltage

        for voltage in voltages:
            self.microscope.voltage = voltage
            # Update defocus to Scherzer for each voltage
            self.microscope.defocus = self.microscope.scherzer_defocus

            result = self.run(
                nx=nx, ny=ny, grid_size=grid_size, pixel_size=pixel_size
            )
            results[voltage] = result

        self.microscope.voltage = original_voltage
        return results

    def run_cs_series(
        self,
        cs_values: List[float] = [0.0, 0.5, 1.0, 1.3, 2.0],
        nx: int = 3,
        ny: int = 2,
        grid_size: int = 64,
        pixel_size: float = 0.1,
    ) -> Dict[float, SimulationResult]:
        """
        Run simulations at multiple spherical aberration values.

        Useful for comparing aberration-corrected vs uncorrected imaging.

        Args:
            cs_values: List of Cs values in mm
            nx, ny: Supercell dimensions
            grid_size: Grid size
            pixel_size: Pixel size in Å

        Returns:
            Dictionary mapping Cs to SimulationResult
        """
        results = {}
        original_cs = self.microscope.cs

        for cs in cs_values:
            self.microscope.cs = cs
            # Update defocus to Scherzer for each Cs
            self.microscope.defocus = self.microscope.scherzer_defocus

            result = self.run(
                nx=nx, ny=ny, grid_size=grid_size, pixel_size=pixel_size
            )
            results[cs] = result

        self.microscope.cs = original_cs
        return results

    def visualize(
        self,
        result: SimulationResult,
        show_potential: bool = True,
        show_intensity: bool = True,
        show_phase: bool = True,
        show_ctf: bool = False,
        figsize: Tuple[int, int] = (12, 4),
        save_path: Optional[str] = None,
    ):
        """
        Visualize MoS₂ simulation results.

        Args:
            result: SimulationResult to visualize
            show_potential: Show projected potential
            show_intensity: Show image intensity
            show_phase: Show phase map
            show_ctf: Show CTF curve
            figsize: Figure size
            save_path: Path to save figure (optional)

        Returns:
            matplotlib Figure
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            raise ImportError(
                "matplotlib required for visualization. "
                "Install with: pip install matplotlib"
            )

        n_plots = sum([show_potential, show_intensity, show_phase, show_ctf])
        fig, axes = plt.subplots(1, n_plots, figsize=figsize)
        if n_plots == 1:
            axes = [axes]

        idx = 0

        if show_potential and result.projected_potential is not None:
            ax = axes[idx]
            im = ax.imshow(
                result.projected_potential,
                cmap="viridis",
                extent=[0, result.field_of_view[0], 0, result.field_of_view[1]],
            )
            ax.set_title("Projected Potential V(x,y)")
            ax.set_xlabel("x (Å)")
            ax.set_ylabel("y (Å)")
            plt.colorbar(im, ax=ax, label="V·Å")
            idx += 1

        if show_intensity and result.intensity is not None:
            ax = axes[idx]
            im = ax.imshow(
                result.intensity,
                cmap="gray",
                extent=[0, result.field_of_view[0], 0, result.field_of_view[1]],
            )
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
                extent=[0, result.field_of_view[0], 0, result.field_of_view[1]],
                vmin=-np.pi,
                vmax=np.pi,
            )
            ax.set_title("Phase φ(x,y)")
            ax.set_xlabel("x (Å)")
            ax.set_ylabel("y (Å)")
            plt.colorbar(im, ax=ax, label="Phase (rad)")
            idx += 1

        if show_ctf:
            ax = axes[idx]
            self._plot_ctf(ax, result)
            idx += 1

        plt.suptitle(
            f"MoS₂ Quantum CTEM Simulation "
            f"({result.supercell_size[0]}×{result.supercell_size[1]} supercell, "
            f"{result.microscope_config.voltage/1e3:.0f} kV)",
            fontsize=12,
        )
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")

        return fig

    def _plot_ctf(self, ax, result: SimulationResult):
        """Plot contrast transfer function."""
        config = result.microscope_config
        k = np.linspace(0, 5, 1000)  # 1/Å

        lambda_A = config.wavelength
        df = config.defocus
        Cs = config.cs * 1e7  # mm to Å

        chi = np.pi * lambda_A * df * k**2 + 0.5 * np.pi * lambda_A**3 * Cs * k**4
        ctf = np.sin(chi)

        ax.plot(k, ctf, "b-", linewidth=1.5)
        ax.axhline(y=0, color="k", linestyle="--", alpha=0.3)
        ax.set_xlabel("Spatial frequency k (1/Å)")
        ax.set_ylabel("CTF")
        ax.set_title(f"CTF (Δf={df:.0f} Å, Cs={config.cs:.1f} mm)")
        ax.set_xlim(0, 5)
        ax.set_ylim(-1.1, 1.1)
        ax.grid(True, alpha=0.3)

    def compare_with_classical(
        self,
        result: SimulationResult,
        figsize: Tuple[int, int] = (15, 5),
        save_path: Optional[str] = None,
    ):
        """
        Create comparison plot between quantum and classical results.

        Args:
            result: SimulationResult (must have classical_intensity)
            figsize: Figure size
            save_path: Path to save figure
        """
        if result.classical_intensity is None:
            raise ValueError(
                "No classical comparison available. "
                "Run with compare_classical=True"
            )

        try:
            import matplotlib.pyplot as plt
        except ImportError:
            raise ImportError("matplotlib required")

        fig, axes = plt.subplots(1, 3, figsize=figsize)

        extent = [0, result.field_of_view[0], 0, result.field_of_view[1]]

        # Quantum result
        im0 = axes[0].imshow(result.intensity, cmap="gray", extent=extent)
        axes[0].set_title("Quantum CTEM")
        axes[0].set_xlabel("x (Å)")
        axes[0].set_ylabel("y (Å)")
        plt.colorbar(im0, ax=axes[0])

        # Classical result
        im1 = axes[1].imshow(result.classical_intensity, cmap="gray", extent=extent)
        axes[1].set_title("Classical WPOA")
        axes[1].set_xlabel("x (Å)")
        plt.colorbar(im1, ax=axes[1])

        # Difference
        diff = result.intensity - result.classical_intensity
        max_diff = np.max(np.abs(diff))
        im2 = axes[2].imshow(
            diff, cmap="RdBu", extent=extent, vmin=-max_diff, vmax=max_diff
        )
        axes[2].set_title(f"Difference (corr: {result.correlation_coefficient:.4f})")
        axes[2].set_xlabel("x (Å)")
        plt.colorbar(im2, ax=axes[2])

        plt.suptitle(
            f"MoS₂ Quantum vs Classical Comparison "
            f"({result.microscope_config.voltage/1e3:.0f} kV)",
            fontsize=12,
        )
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")

        return fig
