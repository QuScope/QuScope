"""Run a quick smoke test for the QuScope MoS2 workflow.

This script imports the orchestrator and runs a small grid to verify
that the package can execute end-to-end (build atoms, compute potentials,
classical multislice). Use it after activating the conda environment.

It also contains a small NumPy compatibility shim to restore the
`ndarray.itemset` API that older versions of abTEM rely on (NumPy 2.0
removed ndarray.itemset). This shim assigns via __setitem__ which is
functionally equivalent for the use-cases in abTEM.
"""

import numpy as _np

# Compatibility shim: abTEM expects ndarray.itemset; NumPy 2.0 removed it.
def _ensure_abtem_compat():
    if not hasattr(_np.ndarray, 'itemset'):
        def _itemset(self, idx, val):
            # emulate the old itemset behavior using __setitem__
            self[idx] = val

        try:
            setattr(_np.ndarray, 'itemset', _itemset)
        except Exception:
            # If we cannot patch the ndarray type, continue.
            pass

    # Try to monkeypatch abtem ensemble helper if abtem is importable
    try:
        import abtem.core.ensemble as _ab_ensemble
        def _safe_wrap_with_array(x, n):
            arr = _np.empty(n, dtype=object)
            arr[0] = x
            return arr

        if getattr(_ab_ensemble, '_wrap_with_array', None) is not None:
            _ab_ensemble._wrap_with_array = _safe_wrap_with_array
    except Exception:
        pass


# Ensure compatibility adjustments are attempted before importing abtem-dependent modules
_ensure_abtem_compat()

from quscope.mos2_workflow import run_comparison


def main():
    print('Running QuScope MoS2 smoke test...')
    res = run_comparison(nx=2, ny=1, grid_size=128, pixel_size=0.1, voltage=200e3)
    print('Returned keys:', list(res.keys()))
    print('Atoms:', len(res['atoms']))
    print('V_quantum shape:', res['V_quantum'].shape)
    print('V_abtem shape:', res['V_abtem'].shape)
    print('I_classical shape:', res['I_classical'].shape)


if __name__ == '__main__':
    main()
