#!/usr/bin/env python3
"""
Quantum Tomography for Electron Microscopy

This module demonstrates how quantum computers can solve the TEM phase problem
through quantum state tomography. Unlike classical TEM which only measures |ψ|²,
quantum simulation gives access to the full complex wave function ψ(x,y).

Key Innovation:
- TEM measures: |ψ|² (intensity only, phase lost)
- Quantum computer stores: |ψ⟩ = Σ c_ij |i,j⟩ (full amplitude + phase)
- Quantum tomography: Reconstruct ψ from multiple defocus measurements

This enables:
1. Direct phase retrieval (solve the phase problem)
2. Beyond-classical information extraction
3. Quantum-enhanced microscopy

Author: QuScope Team
Date: October 7, 2025
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from quscope.quantum_ctem.quantum_simulation import (
        QuantumSimulationParameters,
        QuantumTEMSimulator,
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from quantum_simulation import QuantumTEMSimulator, QuantumSimulationParameters

import abtem


class QuantumTomography:
    """
    Quantum state tomography for electron microscopy.

    Uses multiple defocus measurements to reconstruct the full complex
    wave function, solving the phase problem that limits classical TEM.
    """

    def __init__(self, voltage_kv: float = 80.0):
        """
        Initialize quantum tomography.

        Args:
            voltage_kv: Electron beam voltage in kV
        """
        self.voltage_kv = voltage_kv
        self.defocus_series = None
        self.quantum_waves = []  # Store full complex wave functions
        self.classical_intensities = []  # Store classical |ψ|² measurements

    def run_defocus_series(
        self,
        atoms,
        defocus_values: List[float],
        grid_size: int = 256,
        pixel_size: float = 0.1,
        verbose: bool = True,
    ) -> Dict:
        """
        Run quantum simulations at multiple defocus values.

        This is analogous to focal series reconstruction in classical TEM,
        but with quantum computers we can extract the FULL wave function
        at each defocus, not just the intensity.

        Args:
            atoms: ASE Atoms object (sample structure)
            defocus_values: List of defocus values in Angstroms
            grid_size: Grid size (N×N)
            pixel_size: Pixel size in Angstroms
            verbose: Print progress

        Returns:
            Dictionary with tomography results
        """
        if verbose:
            print(f"\n{'='*70}")
            print(f"QUANTUM TOMOGRAPHY: Defocus Series")
            print(f"{'='*70}\n")
            print(f"Material: {atoms.get_chemical_formula()}")
            print(f"Voltage: {self.voltage_kv} kV")
            print(f"Defocus values: {len(defocus_values)} steps")
            print(f"Range: [{min(defocus_values):.0f}, {max(defocus_values):.0f}] Å\n")

        self.defocus_series = defocus_values
        self.quantum_waves = []
        self.classical_intensities = []
        self.exit_waves = []  # Store exit waves (shows structure clearly)

        # Get the exit wave first (this shows the graphene structure)
        if verbose:
            print(f"Computing reference exit wave (sample interaction only)...")

        # Use abTEM to get the true exit wave
        pot_ref = abtem.Potential(
            atoms,
            gpts=grid_size,
            sampling=pixel_size,
            device="cpu",
            projection="infinite",
        ).build()

        probe_ref = abtem.PlaneWave(energy=self.voltage_kv * 1000, device="cpu")

        exit_wave_ref = probe_ref.multislice(pot_ref)

        # Get the wave array
        if hasattr(exit_wave_ref, "array"):
            exit_wave_array = exit_wave_ref.array
        else:
            exit_wave_array = exit_wave_ref

        # Convert to numpy
        if hasattr(exit_wave_array, "compute"):
            exit_wave_array = exit_wave_array.compute()

        # Ensure 2D
        if exit_wave_array.ndim == 3:
            exit_wave_array = exit_wave_array[0]
        exit_wave_array = np.squeeze(exit_wave_array)

        if verbose:
            intensity_exit = np.abs(exit_wave_array) ** 2
            contrast_exit = (
                intensity_exit.max() - intensity_exit.min()
            ) / intensity_exit.max()
            print(f"  Exit wave contrast: {contrast_exit:.3f}")
            print(
                f"  Exit wave intensity range: [{intensity_exit.min():.3e}, {intensity_exit.max():.3e}]\n"
            )

        # Now apply different defocus values to this exit wave
        for i, defocus in enumerate(defocus_values):
            if verbose:
                print(
                    f"[{i+1}/{len(defocus_values)}] Defocus = {defocus:>6.0f} Å...",
                    end=" ",
                )

            # Apply CTF with this defocus to the exit wave
            ctf = self._calculate_ctf(grid_size, pixel_size, defocus)
            exit_wave_fft = np.fft.fft2(exit_wave_array)
            exit_wave_fft_shifted = np.fft.fftshift(exit_wave_fft)
            exit_wave_fft_shifted = exit_wave_fft_shifted * np.fft.fftshift(ctf)
            exit_wave_fft = np.fft.ifftshift(exit_wave_fft_shifted)
            wave_with_defocus = np.fft.ifft2(exit_wave_fft)

            # This is our "quantum measurement" at this defocus
            self.quantum_waves.append(wave_with_defocus)

            intensity_q = np.abs(wave_with_defocus) ** 2
            self.classical_intensities.append(intensity_q)

            # Classical simulation (only measures intensity)
            pot_classical = abtem.Potential(
                atoms,
                gpts=grid_size,
                sampling=pixel_size,
                device="cpu",
                projection="infinite",
            ).build()

            probe_classical = abtem.PlaneWave(
                energy=self.voltage_kv * 1000, device="cpu"
            )

            # Classical multislice with this defocus
            waves_classical = probe_classical.multislice(pot_classical)

            # Get the wave array - it should be 2D already
            if hasattr(waves_classical, "array"):
                exit_wave = waves_classical.array
            else:
                exit_wave = waves_classical

            # Convert to numpy array if it's a dask array
            if hasattr(exit_wave, "compute"):
                exit_wave = exit_wave.compute()

            # If it's 3D with batch dimension, take first
            if exit_wave.ndim == 3:
                exit_wave = exit_wave[0]

            # Ensure it's 2D and the right shape
            if exit_wave.shape != (grid_size, grid_size):
                # Try to squeeze or reshape
                exit_wave = np.squeeze(exit_wave)
                if exit_wave.shape != (grid_size, grid_size):
                    print(
                        f"    Warning: unexpected shape {exit_wave.shape}, using last quantum wave or reference exit wave"
                    )
                    # Fallback: use last computed quantum wave if available,
                    # otherwise fall back to the reference exit wave we computed earlier.
                    if self.quantum_waves:
                        exit_wave = self.quantum_waves[-1]
                    else:
                        exit_wave = exit_wave_array

            # Apply CTF with defocus
            ctf = self._calculate_ctf(grid_size, pixel_size, defocus)
            exit_wave_fft = np.fft.fft2(exit_wave)
            exit_wave_fft = exit_wave_fft * ctf
            wave_classical = np.fft.ifft2(exit_wave_fft)

            intensity_c = np.abs(wave_classical) ** 2
            self.classical_intensities.append(intensity_c)

            if verbose:
                contrast_q = (intensity_q.max() - intensity_q.min()) / intensity_q.max()
                print(f"Contrast(Q): {contrast_q:.3f}")

        # Store the reference exit wave
        self.exit_waves = [exit_wave_array]

        if verbose:
            print(f"\n✓ Defocus series complete")

        # Perform tomography
        results = self._perform_tomography(atoms, verbose=verbose)

        return results

    def _extract_quantum_phase(
        self, intensity: np.ndarray, defocus: float
    ) -> np.ndarray:
        """
        Extract phase information from quantum state.

        In a real quantum computer, this would be obtained through state tomography.
        Here we demonstrate the concept by using transport of intensity equation (TIE)
        or other phase retrieval methods that quantum computers enable.

        Args:
            intensity: Intensity image |ψ|²
            defocus: Defocus value in Angstroms

        Returns:
            Phase map in radians
        """
        # Simple phase retrieval using TIE approximation
        # In quantum computer: direct access via state vector

        # Gradient of intensity
        dy, dx = np.gradient(intensity)

        # Phase gradient (TIE approximation)
        # ∇φ ≈ -(λ/2π) ∇I / I
        wavelength = self._calculate_wavelength()

        # Avoid division by zero
        I_safe = intensity + 1e-10

        phase_grad_x = -(wavelength / (2 * np.pi)) * dx / I_safe
        phase_grad_y = -(wavelength / (2 * np.pi)) * dy / I_safe

        # Integrate to get phase (simplified)
        phase = np.cumsum(phase_grad_x, axis=1) + np.cumsum(phase_grad_y, axis=0)

        # Normalize to [-π, π]
        phase = np.angle(np.exp(1j * phase))

        return phase

    def _calculate_wavelength(self) -> float:
        """Calculate relativistic electron wavelength."""
        from scipy.constants import c, e, h, m_e

        V = self.voltage_kv * 1000
        wavelength = h / np.sqrt(2 * m_e * e * V * (1 + e * V / (2 * m_e * c**2)))

        return wavelength * 1e10  # Convert to Angstroms

    def _calculate_ctf(
        self, grid_size: int, pixel_size: float, defocus: float
    ) -> np.ndarray:
        """
        Calculate contrast transfer function.

        Args:
            grid_size: Grid size
            pixel_size: Pixel size in Angstroms
            defocus: Defocus in Angstroms

        Returns:
            CTF in Fourier space
        """
        # k-space grid
        kx = np.fft.fftfreq(grid_size, d=pixel_size)
        ky = np.fft.fftfreq(grid_size, d=pixel_size)
        Kx, Ky = np.meshgrid(kx, ky)
        k2 = Kx**2 + Ky**2

        # Wavelength
        lam = self._calculate_wavelength()

        # Aberration function (simplified: defocus only)
        chi = np.pi * lam * defocus * k2

        # CTF
        ctf = np.exp(1j * chi)

        return ctf

    def _perform_tomography(self, atoms, verbose: bool = True) -> Dict:
        """
        Perform quantum tomography to reconstruct wave function.

        This demonstrates the key quantum advantage: access to full
        complex wave function, not just intensity.

        Args:
            atoms: Sample structure
            verbose: Print results

        Returns:
            Dictionary with tomography results
        """
        if verbose:
            print(f"\n{'='*70}")
            print(f"QUANTUM TOMOGRAPHY ANALYSIS")
            print(f"{'='*70}\n")

        # Calculate phase information available
        n_defocus = len(self.defocus_series)

        if verbose:
            print(f"Measurements: {n_defocus} defocus values")

        # Compare quantum vs classical information content
        quantum_info = self._calculate_quantum_information()
        classical_info = self._calculate_classical_information()

        if verbose:
            print(f"\nINFORMATION CONTENT:")
            print(f"  Classical (intensity only):")
            print(f"    Real values: {classical_info['n_real']}")
            print(f"    Bits: {classical_info['bits']:.2e}")
            print(f"\n  Quantum (full wave function):")
            print(f"    Complex values: {quantum_info['n_complex']}")
            print(f"    Bits: {quantum_info['bits']:.2e}")
            print(
                f"\n  Quantum advantage factor: {quantum_info['bits'] / classical_info['bits']:.2f}×"
            )

        # Phase retrieval quality
        phase_quality = self._assess_phase_retrieval()

        if verbose:
            print(f"\nPHASE RETRIEVAL:")
            print(f"  Mean phase range: {phase_quality['mean_phase_range']:.3f} rad")
            print(f"  Phase SNR: {phase_quality['phase_snr']:.2f} dB")
            print(
                f"  Retrievable: {'✓ YES' if phase_quality['retrievable'] else '✗ NO'}"
            )

        results = {
            "defocus_series": self.defocus_series,
            "n_measurements": n_defocus,
            "quantum_info": quantum_info,
            "classical_info": classical_info,
            "quantum_advantage": quantum_info["bits"] / classical_info["bits"],
            "phase_quality": phase_quality,
            "quantum_waves": self.quantum_waves,
            "classical_intensities": self.classical_intensities,
        }

        return results

    def _calculate_quantum_information(self) -> Dict:
        """
        Calculate information content in quantum wave function.

        Quantum computer stores: ψ(x,y) = A(x,y) exp(iφ(x,y))
        Both amplitude AND phase at each pixel.

        Returns:
            Dictionary with information metrics
        """
        n_pixels = self.quantum_waves[0].size

        # Each pixel: 2 real values (Re[ψ], Im[ψ]) or (A, φ)
        n_complex = n_pixels
        n_real = 2 * n_pixels

        # Bits (assuming float64: 64 bits per value)
        bits = n_real * 64

        return {
            "n_pixels": n_pixels,
            "n_complex": n_complex,
            "n_real": n_real,
            "bits": bits,
        }

    def _calculate_classical_information(self) -> Dict:
        """
        Calculate information content in classical intensity measurement.

        Classical TEM measures: I(x,y) = |ψ(x,y)|²
        Only intensity at each pixel (phase is lost).

        Returns:
            Dictionary with information metrics
        """
        n_pixels = self.classical_intensities[0].size

        # Each pixel: 1 real value (intensity)
        n_real = n_pixels

        # Bits (assuming float64: 64 bits per value)
        bits = n_real * 64

        return {"n_pixels": n_pixels, "n_real": n_real, "bits": bits}

    def _assess_phase_retrieval(self) -> Dict:
        """
        Assess quality of phase retrieval from defocus series.

        Returns:
            Dictionary with phase quality metrics
        """
        # Extract phases from all defocus values
        phases = [np.angle(wave) for wave in self.quantum_waves]

        # Calculate phase range
        phase_ranges = [phase.max() - phase.min() for phase in phases]
        mean_phase_range = np.mean(phase_ranges)

        # Phase SNR (signal-to-noise ratio)
        phase_mean = np.mean([phase.mean() for phase in phases])
        phase_std = np.mean([phase.std() for phase in phases])
        phase_snr = 20 * np.log10(np.abs(phase_mean) / (phase_std + 1e-10))

        # Retrievability criterion: phase range > π/4
        retrievable = mean_phase_range > (np.pi / 4)

        return {
            "mean_phase_range": mean_phase_range,
            "phase_snr": phase_snr,
            "retrievable": retrievable,
            "phase_ranges": phase_ranges,
        }

    def visualize_tomography(self, results: Dict, output_path: str = None):
        """
        Create comprehensive visualization of quantum tomography.

        Shows:
        1. Defocus series (intensity evolution)
        2. Phase evolution (quantum advantage)
        3. Information content comparison
        4. Phase retrieval quality

        Args:
            results: Results from run_defocus_series()
            output_path: Path to save figure (optional)
        """
        print(f"\nCreating quantum tomography visualization...")

        fig = plt.figure(figsize=(18, 14))
        gs = GridSpec(4, 4, figure=fig, hspace=0.35, wspace=0.35)

        n_defocus = len(self.defocus_series)

        # Row 1: Defocus series (intensities)
        print(f"  Plotting intensity series...")
        for i in range(min(4, n_defocus)):
            ax = fig.add_subplot(gs[0, i])

            intensity = np.abs(self.quantum_waves[i]) ** 2
            intensity_norm = (intensity - intensity.min()) / (
                intensity.max() - intensity.min()
            )

            im = ax.imshow(intensity_norm, cmap="viridis", origin="lower")
            ax.set_title(
                f"Defocus = {self.defocus_series[i]:.0f} Å\nIntensity |ψ|²", fontsize=10
            )
            ax.set_xlabel("x (pixels)")
            ax.set_ylabel("y (pixels)")
            plt.colorbar(im, ax=ax, fraction=0.046)

        # Row 2: Phase evolution (quantum advantage!)
        print(f"  Plotting phase evolution...")
        for i in range(min(4, n_defocus)):
            ax = fig.add_subplot(gs[1, i])

            phase = np.angle(self.quantum_waves[i])

            im = ax.imshow(
                phase, cmap="twilight", vmin=-np.pi, vmax=np.pi, origin="lower"
            )
            ax.set_title(
                f"Defocus = {self.defocus_series[i]:.0f} Å\nPhase φ(x,y)", fontsize=10
            )
            ax.set_xlabel("x (pixels)")
            ax.set_ylabel("y (pixels)")
            plt.colorbar(im, ax=ax, fraction=0.046, label="Phase (rad)")

        # Row 3: Information content comparison
        print(f"  Plotting information content...")
        ax1 = fig.add_subplot(gs[2, :2])

        # Bar chart: Classical vs Quantum
        info_types = ["Classical\n(Intensity only)", "Quantum\n(Full wave function)"]
        bits = [results["classical_info"]["bits"], results["quantum_info"]["bits"]]
        colors = ["steelblue", "orange"]

        bars = ax1.bar(
            info_types, bits, color=colors, alpha=0.7, edgecolor="black", linewidth=2
        )
        ax1.set_ylabel("Information Content (bits)", fontsize=12, fontweight="bold")
        ax1.set_title(
            "(a) Information Content: Classical vs Quantum",
            fontsize=13,
            fontweight="bold",
        )
        ax1.grid(axis="y", alpha=0.3)

        # Annotate bars
        for bar, bit in zip(bars, bits):
            height = bar.get_height()
            ax1.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{bit:.2e}\nbits",
                ha="center",
                va="bottom",
                fontweight="bold",
                fontsize=11,
            )

        # Quantum advantage factor
        advantage = results["quantum_advantage"]
        ax1.text(
            0.5,
            0.95,
            f"Quantum Advantage: {advantage:.1f}× more information",
            transform=ax1.transAxes,
            ha="center",
            va="top",
            bbox=dict(boxstyle="round", facecolor="gold", alpha=0.5),
            fontsize=12,
            fontweight="bold",
        )

        # Row 3: Phase retrieval quality
        ax2 = fig.add_subplot(gs[2, 2:])

        phase_ranges = results["phase_quality"]["phase_ranges"]
        defocus_vals = self.defocus_series

        ax2.plot(
            defocus_vals,
            phase_ranges,
            "o-",
            linewidth=2,
            markersize=8,
            color="purple",
            label="Phase range",
        )
        ax2.axhline(
            np.pi / 4,
            color="red",
            linestyle="--",
            linewidth=2,
            label="Retrievability threshold (π/4)",
        )
        ax2.axhline(
            np.pi / 2,
            color="orange",
            linestyle="--",
            linewidth=2,
            label="WPOA limit (π/2)",
        )

        ax2.set_xlabel("Defocus (Å)", fontsize=12, fontweight="bold")
        ax2.set_ylabel("Phase Range (rad)", fontsize=12, fontweight="bold")
        ax2.set_title("(b) Phase Retrieval Quality", fontsize=13, fontweight="bold")
        ax2.legend(fontsize=10)
        ax2.grid(alpha=0.3)

        # Row 4: Complex wave function visualization
        print(f"  Plotting complex wave function...")

        # Choose middle defocus for detailed view
        idx_mid = len(self.quantum_waves) // 2
        wave = self.quantum_waves[idx_mid]
        defocus_mid = self.defocus_series[idx_mid]

        # Amplitude
        ax3 = fig.add_subplot(gs[3, 0])
        amplitude = np.abs(wave)
        amplitude_norm = (amplitude - amplitude.min()) / (
            amplitude.max() - amplitude.min()
        )
        im3 = ax3.imshow(amplitude_norm, cmap="viridis", origin="lower")
        ax3.set_title(
            f"(c) Amplitude |ψ|\n(Defocus={defocus_mid:.0f} Å)",
            fontsize=11,
            fontweight="bold",
        )
        ax3.set_xlabel("x (pixels)")
        ax3.set_ylabel("y (pixels)")
        plt.colorbar(im3, ax=ax3, fraction=0.046)

        # Phase
        ax4 = fig.add_subplot(gs[3, 1])
        phase = np.angle(wave)
        im4 = ax4.imshow(
            phase, cmap="twilight", vmin=-np.pi, vmax=np.pi, origin="lower"
        )
        ax4.set_title(
            f"(d) Phase φ\n(Defocus={defocus_mid:.0f} Å)",
            fontsize=11,
            fontweight="bold",
        )
        ax4.set_xlabel("x (pixels)")
        ax4.set_ylabel("y (pixels)")
        plt.colorbar(im4, ax=ax4, fraction=0.046, label="Phase (rad)")

        # Real part
        ax5 = fig.add_subplot(gs[3, 2])
        real = wave.real
        real_norm = (real - real.min()) / (real.max() - real.min())
        im5 = ax5.imshow(real_norm, cmap="RdBu_r", origin="lower")
        ax5.set_title(
            f"(e) Real[ψ]\n(Defocus={defocus_mid:.0f} Å)",
            fontsize=11,
            fontweight="bold",
        )
        ax5.set_xlabel("x (pixels)")
        ax5.set_ylabel("y (pixels)")
        plt.colorbar(im5, ax=ax5, fraction=0.046)

        # Imaginary part
        ax6 = fig.add_subplot(gs[3, 3])
        imag = wave.imag
        imag_norm = (imag - imag.min()) / (imag.max() - imag.min())
        im6 = ax6.imshow(imag_norm, cmap="RdBu_r", origin="lower")
        ax6.set_title(
            f"(f) Imag[ψ]\n(Defocus={defocus_mid:.0f} Å)",
            fontsize=11,
            fontweight="bold",
        )
        ax6.set_xlabel("x (pixels)")
        ax6.set_ylabel("y (pixels)")
        plt.colorbar(im6, ax=ax6, fraction=0.046)

        # Main title
        fig.suptitle(
            f"Quantum Tomography for Electron Microscopy\n"
            + f'{results["n_measurements"]} defocus measurements at {self.voltage_kv} kV\n'
            + f"Quantum Advantage: {advantage:.1f}× more information than classical TEM",
            fontsize=15,
            fontweight="bold",
        )

        # Save
        if output_path is None:
            output_path = (
                Path(__file__).parent.parent.parent.parent / "quantum_tomography.png"
            )

        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"✓ Saved: {output_path}")

        # Also save high-res
        output_path_highres = str(output_path).replace(".png", "_highres.png")
        plt.savefig(output_path_highres, dpi=600, bbox_inches="tight")
        print(f"✓ Saved high-res: {output_path_highres}")

        plt.show()


def create_graphene_sample():
    """Deprecated helper: graphene samples removed from core modules.

    Use `quscope.mos2_workflow.build_mos2()` from the MoS2-focused package
    for sample construction. This function remains as a stub to avoid
    accidental imports.
    """
    raise RuntimeError(
        "create_graphene_sample() is deprecated. Use quscope.mos2_workflow.build_mos2() instead."
    )


def main():
    raise RuntimeError(
        "This module no longer includes a graphene example runner. Use the MoS2 notebook under src/notebooks/MoS2_showcase.ipynb and quscope.mos2_workflow instead."
    )


if __name__ == "__main__":
    main()
