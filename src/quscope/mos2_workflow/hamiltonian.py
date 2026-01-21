import numpy as np


def get_interaction_constant(voltage: float) -> float:
    """Return interaction constant σ in 1/(V·Å) using relativistic wavelength from abTEM formula.
    This is a lightweight version for the notebook demo.
    """
    # Use a simple approximation for demo purposes
    # σ ≈ 2π / (λ E) with λ in Å and E in eV; a full relativistic formula is available in other modules
    from scipy.constants import c, e, h, m_e

    V = voltage
    wavelength_m = h / (np.sqrt(2 * m_e * e * V * (1 + e * V / (2 * m_e * c**2))))
    wavelength_A = wavelength_m * 1e10
    sigma = 2 * np.pi / (wavelength_A * V)
    return sigma


def render_quantum_circuit(n_qubits: int = 6):
    """Return a simple ASCII representation of a toy phase-oracle circuit for the notebook."""
    lines = [f"Quantum phase oracle circuit (n_qubits={n_qubits})"]
    lines.append("[ |0> ] -- H -- Oracle(phase) -- QFT^{-1} -- Measure")
    return "\n".join(lines)
