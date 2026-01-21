import abtem
import numpy as np

from ..quantum_ctem.sample_potential_converter import SamplePotentialConverter
from .viz import build_mos2


def run_comparison(nx=3, ny=2, grid_size=256, pixel_size=0.1, voltage=200e3):
    """Build MoS2, compute quantum (converter) and classical (abTEM) potentials and multislice.

    Returns a dict with potentials and multislice intensity.
    """
    atoms = build_mos2(nx=nx, ny=ny)
    converter = SamplePotentialConverter(acceleration_voltage=voltage)
    V_quant = converter.atoms_to_potential(
        atoms, grid_size=grid_size, pixel_size=pixel_size
    )
    # Classical abTEM potential
    pot = abtem.Potential(
        atoms,
        sampling=pixel_size,
        gpts=grid_size,
        projection="infinite",
        parametrization="kirkland",
    ).build()
    V_abtem = pot.project().array
    # Multislice classical image
    probe = abtem.PlaneWave(energy=voltage, device="cpu")
    waves = probe.multislice(pot)
    if hasattr(waves, "array"):
        arr = waves.array
    else:
        arr = waves
    if hasattr(arr, "compute"):
        arr = arr.compute()
    if arr.ndim == 3:
        exit_wave = arr[0]
    else:
        exit_wave = arr
    I_classical = np.abs(exit_wave) ** 2

    return {
        "atoms": atoms,
        "V_quantum": V_quant,
        "V_abtem": V_abtem,
        "I_classical": I_classical,
        "converter": converter,
    }
