"""Regression tests for the iDPC reconstruction in the quantum STEM modules."""

import numpy as np

from quscope.quantum_ctem.quantum_stem import integrate_dpc


def _phase(n, step):
    """Smooth periodic test phase [rad] on an n x n grid."""
    x = np.arange(n) * step
    X, Y = np.meshgrid(x, x, indexing="ij")
    L = n * step
    return (np.sin(2 * np.pi * 2 * X / L) * np.cos(2 * np.pi * 3 * Y / L)
            + 0.5 * np.cos(2 * np.pi * Y / L))


def test_integrate_dpc_recovers_phase():
    n, step = 64, 0.25
    phi = _phase(n, step)
    # centre of mass = grad(phi) / (2 pi), computed spectrally
    q = np.fft.fftfreq(n, d=step)
    ph = np.fft.fft2(phi)
    com_x = np.real(np.fft.ifft2(1j * q[:, None] * ph))
    com_y = np.real(np.fft.ifft2(1j * q[None, :] * ph))
    rec = integrate_dpc(com_x, com_y, step)
    assert np.allclose(rec, phi - phi.mean(), atol=1e-10)


def test_integrate_dpc_is_zero_mean_and_sign_follows_phase():
    n, step = 32, 0.3
    phi = _phase(n, step)
    q = np.fft.fftfreq(n, d=step)
    ph = np.fft.fft2(phi)
    rec = integrate_dpc(np.real(np.fft.ifft2(1j * q[:, None] * ph)),
                        np.real(np.fft.ifft2(1j * q[None, :] * ph)), step)
    assert abs(rec.mean()) < 1e-12
    assert np.corrcoef(rec.ravel(), phi.ravel())[0, 1] > 0.999



def test_stem_scan_is_registered_with_the_potential():
    """Scan index (i, j) puts the probe at pixel (i*step, j*step) of V, so the
    HAADF maximum of a single atom lands on the atom."""
    from quscope.quantum_ctem.quantum_stem import STEMDetectors
    from quscope.quantum_ctem.quantum_stem_multislice import run_stem_multislice

    n, px, step = 32, 0.15, 2
    x = np.arange(n) * px
    X, Y = np.meshgrid(x, x, indexing="ij")
    cx, cy = 8 * px, 20 * px                      # atom at pixel (8, 20)
    V = 1000.0 * np.exp(-((X - cx) ** 2 + (Y - cy) ** 2) / (2 * 0.3 ** 2))
    det = STEMDetectors(haadf_inner=30, haadf_outer=70, adf_inner=15,
                        adf_outer=30, abf_inner=5, abf_outer=10, bf_outer=10)
    res = run_stem_multislice(V, px, 200e3, n_slices=1, convergence_mrad=15,
                              detectors=det, scan_step_px=step)
    i, j = np.unravel_index(np.argmax(res["HAADF"]), res["HAADF"].shape)
    assert (i * step, j * step) == (8, 20)


def test_stem_detector_signals_are_beam_fractions():
    """With no specimen the probe is fully collected: detector fractions sum to <= 1
    and the bright-field disc holds almost all of it."""
    from quscope.quantum_ctem.quantum_stem import STEMDetectors
    from quscope.quantum_ctem.quantum_stem_multislice import run_stem_multislice

    n, px = 32, 0.15
    det = STEMDetectors(haadf_inner=30, haadf_outer=70, adf_inner=15,
                        adf_outer=30, abf_inner=5, abf_outer=10, bf_outer=10)
    res = run_stem_multislice(np.zeros((n, n)), px, 200e3, n_slices=1,
                              convergence_mrad=10, detectors=det, scan_step_px=16)
    assert np.all(res["BF"] <= 1.0 + 1e-9)
    assert res["BF"].min() > 0.95


def test_multislice_metadata_reports_actual_slice_count():
    """A 3D potential defines the slices; the default n_slices must not leak into the result."""
    from quscope.quantum_ctem.quantum_stem_multislice import run_stem_multislice

    V = np.zeros((3, 16, 16))
    res = run_stem_multislice(V, 0.2, 200e3, convergence_mrad=10, scan_step_px=8)
    assert res["metadata"]["n_slices"] == 3
    assert "3 slices" in res["metrics"]["approach"]
