from typing import Optional

def connect_backend(backend_name: str = 'local'):
    """Return a backend handle. For now, default to local simulator.

    If backend_name == 'ibm', attempt to import qiskit and return provider.
    """
    if backend_name == 'ibm':
        try:
            import qiskit
            return qiskit.Aer.get_backend('aer_simulator')
        except Exception:
            print('IBM backend requested but qiskit not available — falling back to local')
    # Local fallback
    class LocalSim:
        name = 'local_simulator'
        def run(self, *args, **kwargs):
            return None
    return LocalSim()
