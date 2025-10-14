import numpy as np
from quscope.mos2_workflow import run_comparison


def test_mos2_smoke_fast():
    """Run a very small MoS2 orchestrator job to catch regressions.

    This test is intentionally tiny (32x32 grid) so it runs quickly in CI.
    It relies on the orchestrator's internal fallback so it should pass
    even if abTEM is not available.
    """
    res = run_comparison(nx=1, ny=1, grid_size=32, pixel_size=0.2, voltage=200e3)

    # Basic contract: expected keys
    assert set(["atoms", "V_quantum", "V_abtem", "I_classical", "converter"]).issubset(res.keys())

    Vq = res["V_quantum"]
    I = res["I_classical"]

    # Shapes and simple numeric checks
    assert isinstance(Vq, np.ndarray)
    assert isinstance(I, np.ndarray)
    assert Vq.shape == (32, 32)
    assert I.shape == (32, 32)
    assert np.isfinite(Vq).all()
    assert (I >= 0).all()
