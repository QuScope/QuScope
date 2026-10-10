import numpy as np


def get_interaction_constant(voltage: float) -> float:
    """Return interaction constant σ in 1/(V·Å) using relativistic wavelength from abTEM formula.
    This is a lightweight version for the notebook demo.
    """
    # Use a simple approximation for demo purposes
    # σ ≈ 2π / (λ E) with λ in Å and E in eV; a full relativistic formula is available in other modules
    from scipy.constants import h, m_e, e, c
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


def aberration_transfer_function(nx: int, ny: int, pixel_size: float, defocus: float = 200.0, cs: float = 1.0, wavelength_A=0.0251):
    """Return a 2D complex transfer function for typical TEM aberrations.

    wavelength_A: electron wavelength in Angstroms (default ~200 keV).
    This produces the multiplicative H(kx,ky) used to apply aberrations in Fourier space.
    """
    kx = np.fft.fftfreq(nx, d=pixel_size)
    ky = np.fft.fftfreq(ny, d=pixel_size)
    kxv, kyv = np.meshgrid(kx, ky)
    k2 = kxv**2 + kyv**2
    # Simplified phase aberration: chi = pi * wavelength * (defocus * k^2 + 0.5 * cs * (wavelength**2) * k^4)
    chi = np.pi * wavelength_A * (defocus * k2 + 0.5 * cs * (wavelength_A**2) * (k2**2))
    H = np.exp(-1j * chi)
    return H


def build_quantum_phase_oracle_circuit_from_potential(V: np.ndarray, n_qubits: int = 6):
    """Construct a toy quantum circuit representation that encodes low-frequency phase information.

    This function returns a dictionary describing gates for demonstration (not a full Qiskit circuit).
    """
    # Downsample the potential to a small vector to map into qubits
    small = V.copy()
    # reduce to 2^n elements along a flattened axis
    target_len = 2 ** n_qubits
    flat = small.ravel()
    if flat.size >= target_len:
        vec = flat[:target_len]
    else:
        vec = np.pad(flat, (0, target_len - flat.size))

    # Normalize phases to [-pi, pi]
    phases = (vec - vec.mean())
    phases = (phases / (np.max(np.abs(phases)) + 1e-12)) * np.pi

    # Return a simple dict describing per-qubit phase rotations
    circuit = {
        'n_qubits': n_qubits,
        'rotations': [float(p) for p in phases.tolist()[:n_qubits]]
    }
    return circuit


def run_quantum_simulation_on_ibm(circuit_description: dict, backend_name: str = 'ibm_qystem_127'):
    """Attempt to run the toy circuit description on an IBM backend; falls back to local simulator.

    Note: this is a best-effort helper — real execution requires IBM credentials and a compatible job queue.
    """
    try:
        from qiskit import QuantumCircuit, Aer, transpile, execute
        from qiskit import IBMQ
    except Exception:
        # Qiskit not installed or unavailable
        return {'status': 'qiskit_unavailable', 'result': None}

    n = circuit_description.get('n_qubits', 6)
    qc = QuantumCircuit(n)
    # prepare equal superposition
    for q in range(n):
        qc.h(q)
    # apply Z-rotations as phase oracle
    for q, angle in enumerate(circuit_description.get('rotations', [])):
        qc.rz(angle, q)
    qc.measure_all()

    # Try IBM backend if credentials loaded
    try:
        if IBMQ.active_account() is None:
            IBMQ.load_account()
        provider = IBMQ.get_provider(hub=None)
        backend = provider.get_backend(backend_name)
        tqc = transpile(qc, backend)
        job = backend.run(tqc)
        result = job.result(timeout=120)
        return {'status': 'ibm', 'result': result.get_counts()}
    except Exception:
        # Fallback to Aer simulator
        sim = Aer.get_backend('aer_simulator')
        tqc = transpile(qc, sim)
        job = execute(tqc, sim, shots=1024)
        res = job.result()
        return {'status': 'simulator', 'result': res.get_counts()}
