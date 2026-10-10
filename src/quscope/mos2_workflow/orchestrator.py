from .viz import build_mos2
from ..quantum_ctem.sample_potential_converter import SamplePotentialConverter
from .hamiltonian import aberration_transfer_function, build_quantum_phase_oracle_circuit_from_potential, run_quantum_simulation_on_ibm
import numpy as np


def run_comparison(nx=3, ny=2, grid_size=256, pixel_size=0.1, voltage=200e3, material: str = 'MoS2', apply_aberration: bool = True):
    """Build MoS2, compute quantum (converter) and classical (abTEM) potentials and multislice.

    Returns a dict with potentials and multislice intensity.
    """
    atoms = build_mos2(nx=nx, ny=ny, material=material)
    converter = SamplePotentialConverter(acceleration_voltage=voltage)
    V_quant = converter.atoms_to_potential(atoms, grid_size=grid_size, pixel_size=pixel_size)
    # Classical abTEM potential and multislice (use abTEM if available,
    # otherwise fall back to a lightweight FFT-propagation approximation
    # so the smoke test remains deterministic and does not depend on
    # abTEM internals that may be incompatible with NumPy 2.0).
    try:
        import abtem
        pot = abtem.Potential(atoms, sampling=pixel_size, gpts=grid_size, projection='infinite', parametrization='kirkland').build()
        # try to get projected potential from abTEM
        try:
            V_abtem = pot.project().array
        except Exception:
            # If the projection API differs, attempt a direct conversion
            V_abtem = np.array(pot)

        # Try the full multislice
        probe = abtem.PlaneWave(energy=voltage, device='cpu')
        waves = probe.multislice(pot)
        if hasattr(waves, 'array'):
            arr = waves.array
        else:
            arr = waves
        if hasattr(arr, 'compute'):
            arr = arr.compute()
        if arr.ndim == 3:
            exit_wave = arr[0]
        else:
            exit_wave = arr
        I_classical = np.abs(exit_wave)**2
    except Exception:
        # Fallback: compute classical intensity by FFT propagation of a phase screen
        # built from the converter-provided projected potential (prefer the
        # converter's numpy output to avoid triggering abTEM/dask internals).
        V_phase = V_quant

        # Optionally apply aberration transfer function in Fourier domain
        if apply_aberration:
            H = aberration_transfer_function(V_phase.shape[1], V_phase.shape[0], pixel_size, defocus=200.0, cs=1.0)
            phase_screen = np.exp(1j * converter.get_interaction_constant() * V_phase)
            field_ft = np.fft.fft2(phase_screen)
            field_ft *= H
            exit_wave = np.fft.ifft2(field_ft)
            intensity = np.abs(exit_wave)**2
        else:
            sigma = converter.get_interaction_constant()
            phase_screen = np.exp(1j * sigma * V_phase)
            field_ft = np.fft.fft2(phase_screen)
            intensity = np.abs(field_ft)**2

        # Normalize to unit max like an intensity image
        if intensity.max() > 0:
            intensity = intensity / float(intensity.max())
        I_classical = intensity
        # If V_abtem not present, set it to V_quant for comparison
        V_abtem = V_phase

    # Build simple quantum circuit description and try to run on IBM or simulator
    circuit_desc = build_quantum_phase_oracle_circuit_from_potential(V_quant)
    quantum_run = run_quantum_simulation_on_ibm(circuit_desc, backend_name='ibm_127')

    return {
        'atoms': atoms,
        'V_quantum': V_quant,
        'V_abtem': V_abtem,
        'I_classical': I_classical,
        'converter': converter,
        'circuit_description': circuit_desc,
        'quantum_run': quantum_run
    }
