"""
Classical Validation Module for Quantum CTEM

This module implements classical multislice TEM simulation using abTEM
and provides validation metrics comparing quantum and classical approaches.

For publication in Nature Computational Science or Physical Review Applied,
demonstrating agreement between quantum circuit implementation and
established classical TEM simulation methods.

Author: QuScope Team
Date: October 2025
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage
from skimage.metrics import structural_similarity as ssim

try:
    import abtem
    from ase import Atoms
    from ase.build import mx2
except ImportError as e:
    raise ImportError(
        "abTEM and ASE are required for classical validation. "
        "Install with: conda install -c conda-forge abtem ase"
    ) from e


@dataclass
class ValidationParameters:
    """Parameters for classical-quantum validation comparison."""

    # Microscope parameters
    acceleration_voltage: float  # Volts (e.g., 200e3)

    # Sample parameters
    sample_type: str  # 'graphene', 'mos2', 'silicon'
    thickness: float  # Angstroms

    # Imaging parameters
    defocus: float  # Angstroms
    cs: float  # mm (spherical aberration)
    c5: float = 0.0  # mm (5th order spherical)

    # Aberrations (up to 5th order)
    c12a: float = 0.0  # Angstroms (2-fold astigmatism)
    c12b: float = 0.0
    c21a: float = 0.0  # mm (coma)
    c21b: float = 0.0
    c23a: float = 0.0  # mm (3-fold astigmatism)
    c23b: float = 0.0
    c32a: float = 0.0  # mm (star aberration)
    c32b: float = 0.0
    c34a: float = 0.0  # mm (4-fold astigmatism)
    c34b: float = 0.0
    c41a: float = 0.0  # mm (4-fold coma)
    c41b: float = 0.0
    c43a: float = 0.0  # mm (5-fold astigmatism)
    c43b: float = 0.0
    c45a: float = 0.0  # mm (6-fold astigmatism)
    c45b: float = 0.0
    c52a: float = 0.0  # mm (5th order terms)
    c52b: float = 0.0
    c54a: float = 0.0
    c54b: float = 0.0
    c56a: float = 0.0
    c56b: float = 0.0

    # Simulation parameters
    grid_size: int = 512  # Grid points
    pixel_size: float = 0.05  # Angstroms

    # Coherence parameters
    convergence_semiangle: float = 0.01  # mrad
    defocus_spread: float = 30.0  # Angstroms

    def to_abtem_aberrations(self) -> Dict[str, float]:
        """Convert aberration parameters to abTEM format.

        abTEM uses notation: C10 (defocus), C12 (2-fold astigmatism),
        C21 (coma), C23 (3-fold astigmatism), C30 (spherical), etc.

        Returns:
            Dictionary of aberration coefficients in abTEM format.
        """
        aberrations = {
            "C10": self.defocus,  # Angstroms
            "C12a": self.c12a,  # Angstroms
            "C12b": self.c12b,
            "C21a": self.c21a * 1e7,  # Convert mm to Angstroms
            "C21b": self.c21b * 1e7,
            "C23a": self.c23a * 1e7,
            "C23b": self.c23b * 1e7,
            "C30": self.cs * 1e7,  # Convert mm to Angstroms (spherical)
            "C32a": self.c32a * 1e7,
            "C32b": self.c32b * 1e7,
            "C34a": self.c34a * 1e7,
            "C34b": self.c34b * 1e7,
            "C41a": self.c41a * 1e7,
            "C41b": self.c41b * 1e7,
            "C43a": self.c43a * 1e7,
            "C43b": self.c43b * 1e7,
            "C45a": self.c45a * 1e7,
            "C45b": self.c45b * 1e7,
            "C50": self.c5 * 1e7,  # Convert mm to Angstroms (5th order)
            "C52a": self.c52a * 1e7,
            "C52b": self.c52b * 1e7,
            "C54a": self.c54a * 1e7,
            "C54b": self.c54b * 1e7,
            "C56a": self.c56a * 1e7,
            "C56b": self.c56b * 1e7,
        }

        # Remove zero-valued aberrations for cleaner output
        return {k: v for k, v in aberrations.items() if abs(v) > 1e-10}


# Graphene sample builders and example runners have been removed from
# the core validation module to keep the codebase focused on the
# MoS2-centered workflow. If you need to build a graphene sample for
# ad-hoc tests, use ASE directly in a notebook or script. For the
# canonical MoS2 workflow and examples, see `quscope.mos2_workflow`.


class _GrapheneDeprecated:
    @staticmethod
    def create_graphene_sheet(*args, **kwargs):
        raise RuntimeError(
            "Graphene sample builders have been removed from the core "
            "validation module. Use quscope.mos2_workflow for the supported "
            "MoS2 workflows or construct ASE graphene samples directly in "
            "your notebook/script."
        )


# Backwards-compatible alias to make accidental imports fail loudly.
GrapheneSampleBuilder = _GrapheneDeprecated


class ClassicalTEMSimulator:
    """Classical TEM simulation using abTEM multislice algorithm."""

    def __init__(self, params: ValidationParameters):
        """Initialize classical TEM simulator.

        Args:
            params: Validation parameters including microscope settings
        """
        self.params = params
        self.wavelength = self._calculate_wavelength()

    def _calculate_wavelength(self) -> float:
        """Calculate relativistic electron wavelength.

        Returns:
            Wavelength in Angstroms
        """
        from scipy.constants import c, e, h, m_e

        V = self.params.acceleration_voltage
        # Relativistic correction
        wavelength = h / np.sqrt(2 * m_e * e * V * (1 + e * V / (2 * m_e * c**2)))

        return wavelength * 1e10  # Convert m to Angstroms

    def simulate(self, atoms: Atoms) -> np.ndarray:
        """Run classical multislice TEM simulation.

        Args:
            atoms: ASE Atoms object representing the sample

        Returns:
            2D array of exit wave intensity
        """
        # Create probe (plane wave for CTEM)
        plane_wave = abtem.PlaneWave(
            energy=self.params.acceleration_voltage / 1000,  # Convert to keV
            sampling=self.params.pixel_size,
        )

        # Create potential
        potential = abtem.Potential(
            atoms=atoms,
            sampling=self.params.pixel_size,
            gpts=(self.params.grid_size, self.params.grid_size),
            slice_thickness=2.0,  # Angstroms
            projection="infinite",  # Projection for 2D materials
        )

        # Propagate through sample (multislice)
        exit_wave = plane_wave.multislice(potential)

        # Apply CTF (lens aberrations)
        ctf = abtem.CTF(
            energy=self.params.acceleration_voltage / 1000,  # keV
            defocus=self.params.defocus,
            Cs=self.params.cs * 1e7,  # Convert mm to Angstroms
            **self.params.to_abtem_aberrations(),
        )

        # Apply CTF to exit wave
        image_wave = exit_wave.apply_ctf(ctf)

        # Calculate intensity
        intensity = np.abs(image_wave.array) ** 2

        # Ensure we return a regular numpy array
        if hasattr(intensity, "compute"):
            intensity = intensity.compute()

        return np.array(intensity)

    def simulate_with_coherence(
        self, atoms: Atoms, temporal: bool = True, spatial: bool = False
    ) -> np.ndarray:
        """Simulate with partial coherence effects.

        Args:
            atoms: ASE Atoms object
            temporal: Include temporal coherence (defocus spread)
            spatial: Include spatial coherence (convergence angle)

        Returns:
            2D array of intensity with coherence effects
        """
        if not temporal and not spatial:
            return self.simulate(atoms)

        # Create probe
        plane_wave = abtem.PlaneWave(
            energy=self.params.acceleration_voltage / 1000,
            sampling=self.params.pixel_size,
        )

        # Create potential
        potential = abtem.Potential(
            atoms=atoms,
            sampling=self.params.pixel_size,
            gpts=(self.params.grid_size, self.params.grid_size),
            slice_thickness=2.0,
        )

        # Apply multislice
        exit_wave = plane_wave.multislice(potential)

        # Create CTF with partial coherence
        ctf = abtem.CTF(
            energy=self.params.acceleration_voltage / 1000,
            defocus=self.params.defocus,
            Cs=self.params.cs * 1e7,
            **self.params.to_abtem_aberrations(),
        )

        # Add temporal coherence envelope if requested
        if temporal:
            ctf = ctf.add_temporal_envelope(focal_spread=self.params.defocus_spread)

        # Add spatial coherence envelope if requested
        if spatial:
            ctf = ctf.add_spatial_envelope(
                semiangle_cutoff=self.params.convergence_semiangle
            )

        # Apply CTF
        image_wave = exit_wave.apply_ctf(ctf)

        # Calculate intensity and ensure numpy array
        intensity = np.abs(image_wave.array) ** 2
        if hasattr(intensity, "compute"):
            intensity = intensity.compute()

        return np.array(intensity)


class ValidationMetrics:
    """Calculate validation metrics comparing quantum and classical results."""

    @staticmethod
    def calculate_fidelity(
        quantum_image: np.ndarray, classical_image: np.ndarray
    ) -> float:
        """Calculate quantum state fidelity.

        Fidelity F = |⟨ψ_q|ψ_c⟩|² for normalized states

        Args:
            quantum_image: Quantum simulation intensity
            classical_image: Classical simulation intensity

        Returns:
            Fidelity value in [0, 1]
        """
        # Ensure non-negative values (intensities should be positive)
        img_q = np.maximum(quantum_image.flatten(), 0)
        img_c = np.maximum(classical_image.flatten(), 0)

        # Normalize to unit norm (treat as probability amplitudes)
        psi_q = np.sqrt(img_q)
        psi_c = np.sqrt(img_c)

        psi_q = psi_q / np.linalg.norm(psi_q)
        psi_c = psi_c / np.linalg.norm(psi_c)

        # Calculate fidelity
        fidelity = np.abs(np.vdot(psi_q, psi_c)) ** 2

        return float(fidelity)

    @staticmethod
    def calculate_rmse(
        quantum_image: np.ndarray, classical_image: np.ndarray, normalized: bool = True
    ) -> float:
        """Calculate Root Mean Square Error.

        Args:
            quantum_image: Quantum simulation intensity
            classical_image: Classical simulation intensity
            normalized: Normalize images before comparison

        Returns:
            RMSE value
        """
        img_q = quantum_image.copy()
        img_c = classical_image.copy()

        if normalized:
            img_q = (img_q - img_q.min()) / (img_q.max() - img_q.min())
            img_c = (img_c - img_c.min()) / (img_c.max() - img_c.min())

        rmse = np.sqrt(np.mean((img_q - img_c) ** 2))

        return float(rmse)

    @staticmethod
    def calculate_ssim(quantum_image: np.ndarray, classical_image: np.ndarray) -> float:
        """Calculate Structural Similarity Index.

        Args:
            quantum_image: Quantum simulation intensity
            classical_image: Classical simulation intensity

        Returns:
            SSIM value in [-1, 1], typically [0, 1]
        """
        # Normalize images
        img_q = (quantum_image - quantum_image.min()) / (
            quantum_image.max() - quantum_image.min()
        )
        img_c = (classical_image - classical_image.min()) / (
            classical_image.max() - classical_image.min()
        )

        # Calculate SSIM
        ssim_value = ssim(img_q, img_c, data_range=1.0)

        return float(ssim_value)

    @staticmethod
    def calculate_pearson_correlation(
        quantum_image: np.ndarray, classical_image: np.ndarray
    ) -> float:
        """Calculate Pearson correlation coefficient.

        Args:
            quantum_image: Quantum simulation intensity
            classical_image: Classical simulation intensity

        Returns:
            Pearson correlation in [-1, 1]
        """
        img_q = quantum_image.flatten()
        img_c = classical_image.flatten()

        correlation = np.corrcoef(img_q, img_c)[0, 1]

        return float(correlation)

    @staticmethod
    def calculate_all_metrics(
        quantum_image: np.ndarray, classical_image: np.ndarray
    ) -> Dict[str, float]:
        """Calculate all validation metrics.

        Args:
            quantum_image: Quantum simulation intensity
            classical_image: Classical simulation intensity

        Returns:
            Dictionary with all metrics
        """
        return {
            "fidelity": ValidationMetrics.calculate_fidelity(
                quantum_image, classical_image
            ),
            "rmse": ValidationMetrics.calculate_rmse(quantum_image, classical_image),
            "ssim": ValidationMetrics.calculate_ssim(quantum_image, classical_image),
            "pearson": ValidationMetrics.calculate_pearson_correlation(
                quantum_image, classical_image
            ),
        }


class ValidationVisualizer:
    """Create publication-quality validation figures."""

    @staticmethod
    def plot_comparison(
        quantum_image: np.ndarray,
        classical_image: np.ndarray,
        metrics: Dict[str, float],
        params: ValidationParameters,
        save_path: Optional[str] = None,
    ) -> None:
        """Create side-by-side comparison figure.

        Args:
            quantum_image: Quantum simulation result
            classical_image: Classical simulation result
            metrics: Validation metrics dictionary
            params: Validation parameters
            save_path: Optional path to save figure
        """
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))

        # Quantum image
        im1 = axes[0, 0].imshow(quantum_image, cmap="gray")
        axes[0, 0].set_title(
            "Quantum Circuit Simulation", fontsize=12, fontweight="bold"
        )
        axes[0, 0].axis("off")
        plt.colorbar(im1, ax=axes[0, 0], fraction=0.046)

        # Classical image
        im2 = axes[0, 1].imshow(classical_image, cmap="gray")
        axes[0, 1].set_title(
            "Classical Multislice (abTEM)", fontsize=12, fontweight="bold"
        )
        axes[0, 1].axis("off")
        plt.colorbar(im2, ax=axes[0, 1], fraction=0.046)

        # Difference map
        diff = np.abs(quantum_image - classical_image)
        im3 = axes[0, 2].imshow(diff, cmap="hot")
        axes[0, 2].set_title("Absolute Difference", fontsize=12, fontweight="bold")
        axes[0, 2].axis("off")
        plt.colorbar(im3, ax=axes[0, 2], fraction=0.046)

        # Line profiles
        center_y = quantum_image.shape[0] // 2
        profile_q = quantum_image[center_y, :]
        profile_c = classical_image[center_y, :]

        axes[1, 0].plot(profile_q, "b-", label="Quantum", linewidth=2)
        axes[1, 0].plot(profile_c, "r--", label="Classical", linewidth=2)
        axes[1, 0].set_xlabel("Pixel position", fontsize=10)
        axes[1, 0].set_ylabel("Intensity", fontsize=10)
        axes[1, 0].set_title("Central Line Profile", fontsize=12, fontweight="bold")
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)

        # 2D histogram
        axes[1, 1].hexbin(
            quantum_image.flatten(),
            classical_image.flatten(),
            gridsize=50,
            cmap="viridis",
            mincnt=1,
        )
        axes[1, 1].set_xlabel("Quantum intensity", fontsize=10)
        axes[1, 1].set_ylabel("Classical intensity", fontsize=10)
        axes[1, 1].set_title("Correlation Plot", fontsize=12, fontweight="bold")

        # Add ideal line
        min_val = min(quantum_image.min(), classical_image.min())
        max_val = max(quantum_image.max(), classical_image.max())
        axes[1, 1].plot(
            [min_val, max_val], [min_val, max_val], "r--", linewidth=2, label="Ideal"
        )
        axes[1, 1].legend()

        # Metrics text
        axes[1, 2].axis("off")
        metrics_text = (
            f"Validation Metrics\n"
            f"{'=' * 30}\n\n"
            f"Fidelity: {metrics['fidelity']:.6f}\n"
            f"RMSE: {metrics['rmse']:.6f}\n"
            f"SSIM: {metrics['ssim']:.6f}\n"
            f"Pearson: {metrics['pearson']:.6f}\n\n"
            f"Parameters\n"
            f"{'=' * 30}\n\n"
            f"Voltage: {params.acceleration_voltage/1e3:.0f} kV\n"
            f"Defocus: {params.defocus:.1f} Å\n"
            f"Cs: {params.cs:.2f} mm\n"
            f"Sample: {params.sample_type}\n"
            f"Grid: {params.grid_size}×{params.grid_size}\n"
            f"Pixel: {params.pixel_size:.3f} Å"
        )

        axes[1, 2].text(
            0.1,
            0.5,
            metrics_text,
            fontsize=11,
            family="monospace",
            verticalalignment="center",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.3),
        )

        plt.suptitle(
            f"Quantum vs Classical TEM Validation: {params.sample_type.capitalize()}",
            fontsize=14,
            fontweight="bold",
        )
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"✓ Saved validation figure: {save_path}")

        plt.show()

    @staticmethod
    def plot_multi_voltage_validation(
        results: Dict[float, Dict[str, any]], save_path: Optional[str] = None
    ) -> None:
        """Plot validation metrics across multiple voltages.

        Args:
            results: Dictionary mapping voltage to results dict
            save_path: Optional save path
        """
        voltages = sorted(results.keys())
        fidelities = [results[v]["metrics"]["fidelity"] for v in voltages]
        rmses = [results[v]["metrics"]["rmse"] for v in voltages]
        ssims = [results[v]["metrics"]["ssim"] for v in voltages]
        pearsons = [results[v]["metrics"]["pearson"] for v in voltages]

        fig, axes = plt.subplots(2, 2, figsize=(12, 10))

        # Fidelity
        axes[0, 0].plot(
            np.array(voltages) / 1e3, fidelities, "o-", linewidth=2, markersize=8
        )
        axes[0, 0].set_xlabel("Acceleration Voltage (kV)", fontsize=10)
        axes[0, 0].set_ylabel("Fidelity", fontsize=10)
        axes[0, 0].set_title(
            "Quantum Fidelity vs Voltage", fontsize=12, fontweight="bold"
        )
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].set_ylim([0.995, 1.001])

        # RMSE
        axes[0, 1].plot(
            np.array(voltages) / 1e3,
            rmses,
            "o-",
            linewidth=2,
            markersize=8,
            color="orange",
        )
        axes[0, 1].set_xlabel("Acceleration Voltage (kV)", fontsize=10)
        axes[0, 1].set_ylabel("RMSE", fontsize=10)
        axes[0, 1].set_title(
            "Root Mean Square Error vs Voltage", fontsize=12, fontweight="bold"
        )
        axes[0, 1].grid(True, alpha=0.3)

        # SSIM
        axes[1, 0].plot(
            np.array(voltages) / 1e3,
            ssims,
            "o-",
            linewidth=2,
            markersize=8,
            color="green",
        )
        axes[1, 0].set_xlabel("Acceleration Voltage (kV)", fontsize=10)
        axes[1, 0].set_ylabel("SSIM", fontsize=10)
        axes[1, 0].set_title(
            "Structural Similarity vs Voltage", fontsize=12, fontweight="bold"
        )
        axes[1, 0].grid(True, alpha=0.3)

        # Pearson
        axes[1, 1].plot(
            np.array(voltages) / 1e3,
            pearsons,
            "o-",
            linewidth=2,
            markersize=8,
            color="red",
        )
        axes[1, 1].set_xlabel("Acceleration Voltage (kV)", fontsize=10)
        axes[1, 1].set_ylabel("Pearson Correlation", fontsize=10)
        axes[1, 1].set_title(
            "Pearson Correlation vs Voltage", fontsize=12, fontweight="bold"
        )
        axes[1, 1].grid(True, alpha=0.3)

        plt.suptitle("Multi-Voltage Validation Metrics", fontsize=14, fontweight="bold")
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"✓ Saved multi-voltage figure: {save_path}")

        plt.show()


def run_graphene_validation(*args, **kwargs):
    """Deprecated: graphene validation removed from core module.

    This function previously ran an end-to-end graphene validation.
    It has been removed to keep the core codebase focused on the
    MoS2 workflow. Please use `quscope.mos2_workflow.orchestrator.run_comparison`
    and the notebook `src/notebooks/MoS2_showcase.ipynb` for canonical
    examples and publication-quality figures.
    """
    raise RuntimeError(
        "run_graphene_validation() has been removed. Use quscope.mos2_workflow "
        "and the MoS2 notebook (src/notebooks/MoS2_showcase.ipynb) instead."
    )


if __name__ == "__main__":
    print("Classical Validation Module for Quantum CTEM")
    print("=" * 60)
    print("This module no longer includes a graphene example runner.")
    print("Use the MoS2-focused workflow: quscope.mos2_workflow and the notebook")
    print("src/notebooks/MoS2_showcase.ipynb for canonical examples and figures.")
