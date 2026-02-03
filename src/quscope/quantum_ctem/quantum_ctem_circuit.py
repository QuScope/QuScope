"""
Fully Quantum CTEM Simulation Circuit

This module implements a complete quantum TEM simulation pipeline using Qiskit
quantum circuits. Unlike classical FFT-based approaches, this implementation
uses true quantum gates for all operations:

    |ψ₀⟩ → [Phase Grating] → [QFT] → [CTF] → [IQFT] → |ψ_image⟩

Physical Framework:
    1. Incident plane wave: Uniform superposition via Hadamard gates
    2. Phase grating: exp(iσV) via DiagonalGate (WPOA transmission)
    3. QFT: Transform to momentum space (2D separable QFT)
    4. Lens CTF: exp(iχ(k)) via DiagonalGate (aberration function)
    5. IQFT: Transform back to real space

This is a TRUE quantum implementation suitable for publication-quality
demonstrations of quantum advantage in electron microscopy simulation.

References:
    - Kirkland, E. J. (2010). Advanced Computing in Electron Microscopy.
    - Nielsen & Chuang (2010). Quantum Computation and Quantum Information.

Author: QuScope Development Team
Date: January 2026
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Union

import numpy as np
from qiskit import QuantumCircuit, QuantumRegister
from qiskit.circuit.library import DiagonalGate, QFTGate
from qiskit.quantum_info import Statevector
import scipy.constants as const


@dataclass
class QuantumCTEMParameters:
    """
    Parameters for fully quantum CTEM simulation.

    Attributes:
        acceleration_voltage: Electron acceleration voltage (V)
        grid_size: Image size N for N×N grid (must be power of 2)
        pixel_size: Real-space pixel size (Angstroms)
        defocus: Defocus value C₁ (Angstroms, negative = underfocus)
        cs: Spherical aberration C₃ (mm)
        c5: 5th order spherical aberration (mm)
    """

    acceleration_voltage: float
    grid_size: int
    pixel_size: float
    defocus: float = 0.0
    cs: float = 0.0
    c5: float = 0.0

    def __post_init__(self):
        """Validate parameters."""
        if not (self.grid_size & (self.grid_size - 1) == 0):
            raise ValueError(f"grid_size must be power of 2, got {self.grid_size}")
        if self.grid_size < 4:
            raise ValueError(f"grid_size must be >= 4, got {self.grid_size}")


def relativistic_wavelength(voltage: float) -> float:
    """
    Calculate relativistic electron wavelength.

    λ = h / √(2·m₀·e·V·(1 + e·V/(2·m₀·c²)))

    Args:
        voltage: Acceleration voltage (V)

    Returns:
        Wavelength in Angstroms
    """
    m0 = const.electron_mass
    e = const.elementary_charge
    h = const.Planck
    c = const.speed_of_light

    gamma = 1 + e * voltage / (m0 * c**2)
    lambda_m = h / np.sqrt(2 * m0 * e * voltage * gamma)

    return lambda_m * 1e10  # Convert to Angstroms


def interaction_constant(voltage: float, wavelength: float) -> float:
    """
    Calculate interaction constant σ for WPOA.

    σ = 0.00335 × γ / (λ × V_keV)

    where γ is the relativistic correction factor.

    Args:
        voltage: Acceleration voltage (V)
        wavelength: Electron wavelength (Angstroms)

    Returns:
        Interaction constant σ in rad/(V·Å)
    """
    M0C2 = 511.0e3  # Electron rest mass energy in eV
    gamma = (M0C2 + voltage) / (2 * M0C2 + voltage)
    V_keV = voltage / 1000.0
    return 0.00335 * gamma / (wavelength * V_keV)


class PhaseGratingCircuit:
    """
    Quantum circuit for phase grating exp(iσV).

    Implements the Weak Phase Object Approximation (WPOA) transmission
    function as a quantum diagonal unitary gate.

    The transmission function t(x,y) = exp(iσV(x,y)) applies a position-
    dependent phase shift based on the projected atomic potential.
    """

    def __init__(self, n_qubits: int):
        """
        Initialize phase grating circuit builder.

        Args:
            n_qubits: Total number of qubits (log₂(N²) for N×N grid)
        """
        self.n_qubits = n_qubits

    def build_circuit(self, V: np.ndarray, sigma: float) -> QuantumCircuit:
        """
        Build phase grating circuit from potential array.

        Args:
            V: Projected potential V(x,y) in V·Å, shape (N, N)
            sigma: Interaction constant in rad/(V·Å)

        Returns:
            QuantumCircuit implementing exp(iσV)
        """
        # Calculate phase shifts for each pixel
        phases = sigma * V.flatten()

        # Create diagonal unitary: diag(exp(iσV₀), exp(iσV₁), ...)
        diagonal_elements = np.exp(1j * phases)

        # Build circuit with DiagonalGate
        qc = QuantumCircuit(self.n_qubits, name="Phase_Grating")
        diag_gate = DiagonalGate(diagonal_elements.tolist())
        qc.append(diag_gate, range(self.n_qubits))

        return qc

    def get_transmission_function(
        self, V: np.ndarray, sigma: float
    ) -> np.ndarray:
        """
        Get classical transmission function for validation.

        Args:
            V: Projected potential
            sigma: Interaction constant

        Returns:
            Transmission function t(x,y) = exp(iσV)
        """
        return np.exp(1j * sigma * V)


class LensCTFCircuit:
    """
    Quantum circuit for lens aberration exp(iχ(k)).

    Implements the Contrast Transfer Function (CTF) as a quantum diagonal
    unitary in momentum space. The aberration function χ(k) includes:

        χ(k) = π·λ·Δf·k² + 0.5·π·λ³·Cs·k⁴ + ...

    This must be applied AFTER the QFT transforms to momentum space.
    """

    def __init__(self, n_qubits: int, n_qubits_x: int, n_qubits_y: int):
        """
        Initialize lens CTF circuit builder.

        Args:
            n_qubits: Total number of qubits
            n_qubits_x: Qubits for x dimension
            n_qubits_y: Qubits for y dimension
        """
        self.n_qubits = n_qubits
        self.n_qubits_x = n_qubits_x
        self.n_qubits_y = n_qubits_y

    def calculate_chi(
        self,
        wavelength: float,
        pixel_size: float,
        defocus: float,
        cs: float = 0.0,
        c5: float = 0.0,
    ) -> np.ndarray:
        """
        Calculate aberration function χ(k).

        χ(k) = π·λ·Δf·k² + 0.5·π·λ³·Cs·k⁴ + (π/3)·λ⁵·C₅·k⁶

        Args:
            wavelength: Electron wavelength (Å)
            pixel_size: Real-space pixel size (Å)
            defocus: Defocus C₁ (Å)
            cs: Spherical aberration C₃ (mm)
            c5: 5th order aberration (mm)

        Returns:
            χ(k) array of shape (N, N)
        """
        N_x = 2**self.n_qubits_x
        N_y = 2**self.n_qubits_y

        # Generate k-space grid
        # k = 2π × frequency, frequency = index / (N × pixel_size)
        freq_x = np.fft.fftfreq(N_x, d=pixel_size)
        freq_y = np.fft.fftfreq(N_y, d=pixel_size)
        kx, ky = np.meshgrid(2 * np.pi * freq_x, 2 * np.pi * freq_y, indexing="ij")
        k_squared = kx**2 + ky**2

        # Convert Cs from mm to Angstroms
        Cs_A = cs * 1e7
        C5_A = c5 * 1e7

        # Aberration function
        chi = np.zeros_like(k_squared)

        # Defocus term: π·λ·Δf·k²
        chi += np.pi * wavelength * defocus * k_squared

        # Spherical aberration: 0.5·π·λ³·Cs·k⁴
        if cs != 0:
            chi += 0.5 * np.pi * (wavelength**3) * Cs_A * (k_squared**2)

        # 5th order: (π/3)·λ⁵·C₅·k⁶
        if c5 != 0:
            chi += (np.pi / 3) * (wavelength**5) * C5_A * (k_squared**3)

        return chi

    def build_circuit(self, chi_k: np.ndarray) -> QuantumCircuit:
        """
        Build CTF circuit from aberration function.

        Args:
            chi_k: Aberration function χ(k), shape (N, N)

        Returns:
            QuantumCircuit implementing exp(iχ(k))
        """
        # Create diagonal unitary: diag(exp(iχ₀), exp(iχ₁), ...)
        diagonal_elements = np.exp(1j * chi_k.flatten())

        # Build circuit
        qc = QuantumCircuit(self.n_qubits, name="Lens_CTF")
        ctf_gate = DiagonalGate(diagonal_elements.tolist())
        qc.append(ctf_gate, range(self.n_qubits))

        return qc


class QuantumCTEMCircuit:
    """
    Complete quantum CTEM simulation circuit.

    Implements the full TEM imaging pipeline as a quantum circuit:

        |ψ₀⟩ → [Hadamards] → [Phase Grating] → [QFT] → [CTF] → [IQFT] → |ψ_image⟩

    This is a TRUE quantum implementation where all operations are
    performed using quantum gates, not classical FFT.

    Example:
        >>> params = QuantumCTEMParameters(
        ...     acceleration_voltage=200e3,
        ...     grid_size=8,
        ...     pixel_size=0.5,
        ...     defocus=-500.0,
        ...     cs=1.3
        ... )
        >>> sim = QuantumCTEMCircuit(params)
        >>> V = np.random.rand(8, 8) * 100  # Test potential
        >>> result = sim.simulate(V)
        >>> print(result['intensity'].shape)
        (8, 8)
    """

    def __init__(self, params: QuantumCTEMParameters):
        """
        Initialize quantum CTEM simulator.

        Args:
            params: Simulation parameters
        """
        self.params = params

        # Calculate qubit requirements
        self.n_qubits_per_dim = int(np.log2(params.grid_size))
        self.n_qubits = 2 * self.n_qubits_per_dim

        # Calculate physics parameters
        self.wavelength = relativistic_wavelength(params.acceleration_voltage)
        self.sigma = interaction_constant(params.acceleration_voltage, self.wavelength)

        # Initialize sub-circuit builders
        self.phase_grating = PhaseGratingCircuit(self.n_qubits)
        self.lens_ctf = LensCTFCircuit(
            self.n_qubits, self.n_qubits_per_dim, self.n_qubits_per_dim
        )

        # Pre-compute aberration function
        self.chi_k = self.lens_ctf.calculate_chi(
            self.wavelength,
            params.pixel_size,
            params.defocus,
            params.cs,
            params.c5,
        )

    def build_full_circuit(
        self, V: np.ndarray, include_barriers: bool = True
    ) -> QuantumCircuit:
        """
        Build complete quantum CTEM circuit.

        Args:
            V: Projected potential V(x,y) in V·Å, shape (N, N)
            include_barriers: Add barriers between stages for visualization

        Returns:
            Complete quantum circuit for TEM simulation
        """
        qc = QuantumCircuit(self.n_qubits, name="Quantum_CTEM")

        # Stage 1: Incident plane wave (uniform superposition)
        qc.h(range(self.n_qubits))
        if include_barriers:
            qc.barrier(label="|ψ₀⟩")

        # Stage 2: Phase grating exp(iσV) in real space
        phase_circuit = self.phase_grating.build_circuit(V, self.sigma)
        qc.compose(phase_circuit, inplace=True)
        if include_barriers:
            qc.barrier(label="exp(iσV)")

        # Stage 3: 2D QFT (separable: QFT_x ⊗ QFT_y)
        qft_x = QFTGate(self.n_qubits_per_dim)
        qft_y = QFTGate(self.n_qubits_per_dim)
        qc.append(qft_x, range(self.n_qubits_per_dim))
        qc.append(qft_y, range(self.n_qubits_per_dim, self.n_qubits))
        if include_barriers:
            qc.barrier(label="QFT")

        # Stage 4: Lens CTF exp(iχ(k)) in momentum space
        ctf_circuit = self.lens_ctf.build_circuit(self.chi_k)
        qc.compose(ctf_circuit, inplace=True)
        if include_barriers:
            qc.barrier(label="exp(iχ)")

        # Stage 5: 2D IQFT (inverse QFT)
        qc.append(qft_x.inverse(), range(self.n_qubits_per_dim))
        qc.append(qft_y.inverse(), range(self.n_qubits_per_dim, self.n_qubits))
        if include_barriers:
            qc.barrier(label="IQFT")

        return qc

    def simulate(self, V: np.ndarray) -> Dict:
        """
        Run complete quantum simulation and extract results.

        Uses statevector simulation to extract the final wave function
        and intensity image.

        Args:
            V: Projected potential V(x,y) in V·Å, shape (N, N)

        Returns:
            Dictionary containing:
            - 'circuit': The quantum circuit
            - 'psi_image': Complex wave function ψ(x,y)
            - 'intensity': Image intensity |ψ|²
            - 'metrics': Circuit complexity metrics
            - 'parameters': Physics parameters used
        """
        # Build circuit
        circuit = self.build_full_circuit(V, include_barriers=False)

        # Execute via statevector simulation
        sv = Statevector.from_instruction(circuit)
        psi_flat = sv.data

        # Reshape to 2D image
        N = self.params.grid_size
        psi_image = psi_flat.reshape(N, N)

        # Calculate intensity
        intensity = np.abs(psi_image) ** 2

        # Normalize intensity (plane wave should give ~1)
        intensity = intensity / intensity.mean()

        return {
            "circuit": circuit,
            "psi_image": psi_image,
            "intensity": intensity,
            "metrics": self._get_circuit_metrics(circuit),
            "parameters": {
                "wavelength": self.wavelength,
                "sigma": self.sigma,
                "defocus": self.params.defocus,
                "cs": self.params.cs,
                "grid_size": N,
                "n_qubits": self.n_qubits,
            },
        }

    def _get_circuit_metrics(self, qc: QuantumCircuit) -> Dict:
        """Get circuit complexity metrics."""
        ops = qc.count_ops()
        return {
            "depth": qc.depth(),
            "total_gates": sum(ops.values()),
            "gate_counts": dict(ops),
            "qubits": qc.num_qubits,
        }

    def get_ctf(self) -> np.ndarray:
        """
        Get the Contrast Transfer Function sin(χ(k)).

        Returns:
            CTF array of shape (N, N)
        """
        return np.sin(self.chi_k)

    def get_info(self) -> str:
        """Get simulation information string."""
        return (
            f"Quantum CTEM Simulator\n"
            f"  Voltage: {self.params.acceleration_voltage/1e3:.0f} kV\n"
            f"  Wavelength: {self.wavelength:.5f} Å\n"
            f"  Grid: {self.params.grid_size}×{self.params.grid_size}\n"
            f"  Qubits: {self.n_qubits}\n"
            f"  Defocus: {self.params.defocus:.1f} Å\n"
            f"  Cs: {self.params.cs:.2f} mm\n"
            f"  σ: {self.sigma:.4e} rad/(V·Å)"
        )


class QuantumClassicalValidator:
    """
    Validate quantum CTEM against classical FFT simulation.

    Computes fidelity and error metrics between quantum circuit
    simulation and classical numpy FFT-based simulation.
    """

    def __init__(self, params: QuantumCTEMParameters):
        """
        Initialize validator.

        Args:
            params: Simulation parameters
        """
        self.params = params
        self.quantum_sim = QuantumCTEMCircuit(params)

    def classical_simulation(self, V: np.ndarray) -> Dict:
        """
        Run classical FFT-based CTEM simulation.

        Args:
            V: Projected potential V(x,y) in V·Å

        Returns:
            Dictionary with classical results
        """
        # Get parameters from quantum simulator
        sigma = self.quantum_sim.sigma
        chi_k = self.quantum_sim.chi_k

        # Incident plane wave (normalized)
        N = self.params.grid_size
        psi_in = np.ones((N, N), dtype=complex) / N

        # Phase grating (WPOA transmission)
        t = np.exp(1j * sigma * V)
        psi_exit = psi_in * t

        # FFT to momentum space
        psi_k = np.fft.fft2(psi_exit)

        # Apply CTF
        H_k = np.exp(1j * chi_k)
        psi_k_ctf = psi_k * H_k

        # IFFT back to real space
        psi_image = np.fft.ifft2(psi_k_ctf)

        # Intensity
        intensity = np.abs(psi_image) ** 2
        intensity = intensity / intensity.mean()

        return {
            "psi_image": psi_image,
            "intensity": intensity,
            "transmission": t,
        }

    def compare(self, V: np.ndarray) -> Dict:
        """
        Compare quantum and classical simulations.

        Args:
            V: Projected potential

        Returns:
            Dictionary with comparison metrics:
            - 'fidelity': State fidelity |⟨ψ_c|ψ_q⟩|²
            - 'intensity_mse': Mean squared error of intensities
            - 'quantum': Quantum simulation results
            - 'classical': Classical simulation results
        """
        # Run both simulations
        quantum_result = self.quantum_sim.simulate(V)
        classical_result = self.classical_simulation(V)

        # Calculate fidelity
        psi_q = quantum_result["psi_image"].flatten()
        psi_c = classical_result["psi_image"].flatten()

        # Normalize for fidelity calculation
        psi_q_norm = psi_q / np.linalg.norm(psi_q)
        psi_c_norm = psi_c / np.linalg.norm(psi_c)

        fidelity = np.abs(np.vdot(psi_c_norm, psi_q_norm)) ** 2

        # Intensity MSE
        I_q = quantum_result["intensity"]
        I_c = classical_result["intensity"]
        intensity_mse = np.mean((I_q - I_c) ** 2)

        # Correlation
        correlation = np.corrcoef(I_q.flatten(), I_c.flatten())[0, 1]

        return {
            "fidelity": fidelity,
            "intensity_mse": intensity_mse,
            "correlation": correlation,
            "quantum": quantum_result,
            "classical": classical_result,
        }


def demo_quantum_ctem():
    """Demonstrate fully quantum CTEM simulation."""

    print("=" * 70)
    print("FULLY QUANTUM CTEM SIMULATION DEMONSTRATION")
    print("=" * 70)

    # Parameters
    params = QuantumCTEMParameters(
        acceleration_voltage=200e3,
        grid_size=8,  # 8×8 grid = 6 qubits
        pixel_size=0.5,
        defocus=-500.0,  # Scherzer-like underfocus
        cs=1.3,  # mm
    )

    # Create simulator
    sim = QuantumCTEMCircuit(params)
    print("\n" + sim.get_info())

    # Create test potential (single atom at center)
    N = params.grid_size
    x = np.linspace(-2, 2, N)
    X, Y = np.meshgrid(x, x)
    V = 100 * np.exp(-(X**2 + Y**2) / 0.5)  # Gaussian atom

    print(f"\nTest potential: Gaussian atom")
    print(f"  V range: [{V.min():.2f}, {V.max():.2f}] V·Å")

    # Run quantum simulation
    print("\nRunning quantum simulation...")
    result = sim.simulate(V)

    print(f"\nCircuit metrics:")
    for key, value in result["metrics"].items():
        print(f"  {key}: {value}")

    # Validate against classical
    print("\nValidating against classical FFT simulation...")
    validator = QuantumClassicalValidator(params)
    comparison = validator.compare(V)

    print(f"\nValidation results:")
    print(f"  Fidelity: {comparison['fidelity']:.10f}")
    print(f"  Intensity MSE: {comparison['intensity_mse']:.2e}")
    print(f"  Correlation: {comparison['correlation']:.10f}")

    print("\n" + "=" * 70)
    print("QUANTUM CTEM SIMULATION COMPLETE")
    print("=" * 70)

    return result, comparison


if __name__ == "__main__":
    demo_quantum_ctem()
