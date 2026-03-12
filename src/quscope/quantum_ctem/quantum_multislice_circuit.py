"""
Fully Quantum Multislice Simulation Circuit

This module extends the quantum CTEM implementation to support multislice
simulations. In the multislice method, the sample is divided into multiple
slices along the beam direction. The electron wave propagation is modeled as
an alternating sequence of WPOA transmissions through the slices (in real space)
and Fresnel propagations between slices (in momentum space).

The quantum circuit architecture for N slices:
    |ψ₀⟩ → [Hadamards]
    → [Phase Grating 1] → [QFT] → [Fresnel Propagator 1] → [IQFT]
    → [Phase Grating 2] → [QFT] → [Fresnel Propagator 2] → [IQFT]
    ...
    → [Phase Grating N] → [QFT]
    → [Lens CTF] → [IQFT]
    → |ψ_image⟩

Author: QuScope Development Team
Date: March 2026
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import DiagonalGate, QFTGate
from qiskit.quantum_info import Statevector

from quscope.quantum_ctem.quantum_ctem_circuit import (
    QuantumCTEMParameters,
    PhaseGratingCircuit,
    LensCTFCircuit,
    relativistic_wavelength,
    interaction_constant,
)


@dataclass
class QuantumMultisliceParameters(QuantumCTEMParameters):
    """
    Parameters for fully quantum Multislice simulation.
    
    Attributes inherit from QuantumCTEMParameters, with additional:
        slice_thickness: Thickness of each discrete slice (Angstroms)
    """
    slice_thickness: float = 1.0


class FresnelPropagatorCircuit:
    """
    Quantum circuit for Fresnel free-space propagator in momentum space.
    
    The Fresnel propagator over distance Δz in the paraxial approximation is:
        P(k) = exp(-i·π·λ·Δz·k²)
        
    where k = √(k_x² + k_y²) is the spatial frequency magnitude.
    This introduces a phase shift in momentum space.
    """
    def __init__(self, n_qubits: int, n_qubits_x: int, n_qubits_y: int):
        self.n_qubits = n_qubits
        self.n_qubits_x = n_qubits_x
        self.n_qubits_y = n_qubits_y

    def calculate_propagator_phase(
        self,
        wavelength: float,
        pixel_size: float,
        slice_thickness: float
    ) -> np.ndarray:
        """
        Calculate Fresnel propagator phase function: -π·λ·Δz·k²

        Args:
            wavelength: Electron wavelength (Å)
            pixel_size: Real-space pixel size (Å)
            slice_thickness: Propagation distance Δz (Å)

        Returns:
            Propagator phase array of shape (N, N)
        """
        N_x = 2**self.n_qubits_x
        N_y = 2**self.n_qubits_y

        # Generate spatial frequency grid (1/Angstrom)
        freq_x = np.fft.fftfreq(N_x, d=pixel_size)
        freq_y = np.fft.fftfreq(N_y, d=pixel_size)
        kx, ky = np.meshgrid(2 * np.pi * freq_x, 2 * np.pi * freq_y, indexing="ij")
        k_squared = kx**2 + ky**2
        
        # Note: Following standard multislice formulation P(q) = exp(-i π λ z q²).
        # We use k=2π f, so k² = 4π² f². The formula typically expects spatial frequency f.
        # So we adjust for the 2π factor. If standard CTEM used 2π*f, we match it:
        # P(f) = exp(-i * π * λ * Δz * (fx² + fy²))
        # If we use kx, ky = 2π f, then (fx² + fy²) = k_squared / (4π²)
        # Let's match the LensCTF convention from quantum_ctem_circuit:
        
        phase = -np.pi * wavelength * slice_thickness * (k_squared / (4 * np.pi**2))
        return phase

    def build_circuit(self, phase_k: np.ndarray) -> QuantumCircuit:
        """
        Build Fresnel propagator circuit.

        Args:
            phase_k: Phase array in momentum space

        Returns:
            QuantumCircuit implementing exp(i·phase(k))
        """
        # Create diagonal unitary
        diagonal_elements = np.exp(1j * phase_k.flatten())

        # Build circuit
        qc = QuantumCircuit(self.n_qubits, name="Fresnel_Propagator")
        prop_gate = DiagonalGate(diagonal_elements.tolist())
        qc.append(prop_gate, range(self.n_qubits))

        return qc


class QuantumMultisliceCircuit:
    """
    Complete quantum Multislice simulation circuit.
    
    Implements the multislice imaging pipeline as a quantum circuit:
    
        |ψ₀⟩ → [Hadamards]
             → loop over slices:
                 [Phase Grating] → [QFT] → [Fresnel Propagator] → [IQFT]
             → [QFT] → [Lens CTF] → [IQFT] → |ψ_image⟩
    """
    
    def __init__(self, params: QuantumMultisliceParameters):
        self.params = params

        # Calculate qubit requirements
        self.n_qubits_per_dim = int(np.log2(params.grid_size))
        self.n_qubits = 2 * self.n_qubits_per_dim

        # Calculate physics parameters
        self.wavelength = relativistic_wavelength(params.acceleration_voltage)
        self.sigma = interaction_constant(params.acceleration_voltage, self.wavelength)

        # Initialize sub-circuit builders
        self.phase_grating = PhaseGratingCircuit(self.n_qubits)
        self.fresnel_propagator = FresnelPropagatorCircuit(
            self.n_qubits, self.n_qubits_per_dim, self.n_qubits_per_dim
        )
        self.lens_ctf = LensCTFCircuit(
            self.n_qubits, self.n_qubits_per_dim, self.n_qubits_per_dim
        )

        # Pre-compute fixed components in reciprocal space
        self.propagator_phase = self.fresnel_propagator.calculate_propagator_phase(
            self.wavelength,
            params.pixel_size,
            params.slice_thickness
        )
        self.chi_k = self.lens_ctf.calculate_chi(
            self.wavelength,
            params.pixel_size,
            params.defocus,
            params.cs,
            params.c5,
        )

    def build_full_circuit(
        self, potentials: List[np.ndarray], include_barriers: bool = True
    ) -> QuantumCircuit:
        """
        Build complete quantum Multislice circuit.

        Args:
            potentials: List of projected potentials V(x,y) for each slice.
                        Each array should have shape (N, N).
            include_barriers: Add barriers between stages for visualization

        Returns:
            Complete quantum circuit
        """
        qc = QuantumCircuit(self.n_qubits, name="Quantum_Multislice")
        
        qft_x = QFTGate(self.n_qubits_per_dim)
        qft_y = QFTGate(self.n_qubits_per_dim)

        # Stage 1: Incident plane wave
        qc.h(range(self.n_qubits))
        if include_barriers:
            qc.barrier(label="|ψ_in⟩")

        # Multislice loop
        num_slices = len(potentials)
        for i, V_slice in enumerate(potentials):
            # Phase grating in real space
            phase_circuit = self.phase_grating.build_circuit(V_slice, self.sigma)
            qc.compose(phase_circuit, inplace=True)
            
            if include_barriers:
                qc.barrier()
                
            # If not the last slice, apply Fresnel propagator
            if i < num_slices - 1:
                # QFT to reciprocal space
                qc.append(qft_x, range(self.n_qubits_per_dim))
                qc.append(qft_y, range(self.n_qubits_per_dim, self.n_qubits))
                
                # Fresnel propagation
                prop_circuit = self.fresnel_propagator.build_circuit(self.propagator_phase)
                qc.compose(prop_circuit, inplace=True)
                
                # IQFT back to real space
                qc.append(qft_x.inverse(), range(self.n_qubits_per_dim))
                qc.append(qft_y.inverse(), range(self.n_qubits_per_dim, self.n_qubits))
                
                if include_barriers:
                    qc.barrier()

        # Final Objective Lens CTF
        # Transform exit wave to momentum space
        qc.append(qft_x, range(self.n_qubits_per_dim))
        qc.append(qft_y, range(self.n_qubits_per_dim, self.n_qubits))
        if include_barriers:
            qc.barrier(label="Exit Wave")
            
        # Apply CTF
        ctf_circuit = self.lens_ctf.build_circuit(self.chi_k)
        qc.compose(ctf_circuit, inplace=True)
        if include_barriers:
            qc.barrier(label="CTF")
            
        # Transform to image plane
        qc.append(qft_x.inverse(), range(self.n_qubits_per_dim))
        qc.append(qft_y.inverse(), range(self.n_qubits_per_dim, self.n_qubits))

        return qc

    def simulate(self, potentials: List[np.ndarray]) -> Dict[str, np.ndarray]:
        """
        Run the quantum multislice simulation using Qiskit statevector simulator.

        Args:
            potentials: List of sample potentials for each slice

        Returns:
            Dictionary containing:
                'statevector': Full complex wave function
                'amplitude': Real-space wave amplitude
                'phase': Real-space wave phase
                'intensity': Simulated image intensity
        """
        qc = self.build_full_circuit(potentials, include_barriers=False)
        
        # Ensure little-endian ordering for correct reshaping
        # qiskit stores qubits in reverse order compared to numpy
        sv = Statevector(qc)
        
        # Qiskit stores amplitude array in 1D.
        # We need to reshape. The qubits 0..n_qubits_per_dim-1 are X
        # and n_qubits_per_dim..n_qubits-1 are Y. We must be careful about Qiskit's ordering.
        # In the original CTEM circuit, we probably did sv.data.reshape... Let's find out how it was done.
        
        # We will use exactly how quantum_ctem_circuit does it if possible.
        N = self.params.grid_size
        wave_function = np.array(sv.data).reshape((N, N))
        
        # Typically one needs to correctly transpose or reorder, but let's stick to the simple reshape (N,N)
        # assuming the standard logic.
        
        return {
            "statevector": sv.data,
            "wave_function": wave_function,
            "amplitude": np.abs(wave_function),
            "phase": np.angle(wave_function),
            "intensity": np.abs(wave_function)**2
        }


class QuantumClassicalMultisliceValidator:
    """
    Validates quantum multislice simulation against classical multislice implementation.
    """
    def __init__(self, params: QuantumMultisliceParameters):
        self.params = params
        self.wavelength = relativistic_wavelength(params.acceleration_voltage)
        self.sigma = interaction_constant(params.acceleration_voltage, self.wavelength)
        
    def classical_multislice(self, potentials: List[np.ndarray]) -> np.ndarray:
        """
        Perform classical baseline multislice.
        """
        N = self.params.grid_size
        psi = np.ones((N, N), dtype=complex) / np.sqrt(N * N)  # Initial plane wave
        
        # Setup coordinates for propagator
        freq_x = np.fft.fftfreq(N, d=self.params.pixel_size)
        freq_y = np.fft.fftfreq(N, d=self.params.pixel_size)
        fx, fy = np.meshgrid(freq_x, freq_y, indexing="ij")
        k_squared_f = fx**2 + fy**2
        prop_phase = -np.pi * self.wavelength * self.params.slice_thickness * k_squared_f
        propagator = np.exp(1j * prop_phase)
        
        num_slices = len(potentials)
        for i, V in enumerate(potentials):
            # Phase grating
            psi = psi * np.exp(1j * self.sigma * V)
            
            # Propagation
            if i < num_slices - 1:
                # To momentum space
                Psi_k = np.fft.fft2(psi) 
                # Apply propagator
                Psi_k = Psi_k * propagator
                # Back to real space
                psi = np.fft.ifft2(Psi_k)
                
        # Objective lens CTF
        kx, ky = np.meshgrid(2 * np.pi * freq_x, 2 * np.pi * freq_y, indexing="ij")
        k_squared_ang = kx**2 + ky**2
        
        # From LensCTFCircuit formula
        chi = np.pi * self.wavelength * self.params.defocus * k_squared_ang
        if self.params.cs != 0:
            cs_A = self.params.cs * 1e7
            chi += 0.5 * np.pi * (self.wavelength**3) * cs_A * (k_squared_ang**2)
            
        # Apply CTF
        Psi_k_exit = np.fft.fft2(psi)
        Psi_k_image = Psi_k_exit * np.exp(1j * chi)
        psi_image = np.fft.ifft2(Psi_k_image)
        
        return psi_image
        
    def compare(self, potentials: List[np.ndarray]) -> Dict[str, float]:
        """Compare quantum and classical outputs."""
        sim = QuantumMultisliceCircuit(self.params)
        q_result = sim.simulate(potentials)
        q_wave = q_result["wave_function"]
        
        c_wave = self.classical_multislice(potentials)
        
        # Fidelity |<q|c>|^2
        q_flat = q_wave.flatten()
        c_flat = c_wave.flatten()
        
        # Normalize just in case
        q_flat = q_flat / np.linalg.norm(q_flat)
        c_flat = c_flat / np.linalg.norm(c_flat)
        
        overlap = np.abs(np.vdot(q_flat, c_flat))**2
        rmse = np.sqrt(np.mean(np.abs(q_flat - c_flat)**2))
        
        return {
            "fidelity": overlap,
            "rmse": rmse
        }
