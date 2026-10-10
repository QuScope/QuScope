"""Full paper runner: classical vs quantum CTEM comparison for MoSe2.

Saves:
- outputs/paper/full/V_quantum.png
- outputs/paper/full/V_abtem.png
- outputs/paper/full/V_diff.png
- outputs/paper/full/phase.png
- outputs/paper/full/I_classical.png
- outputs/paper/full/circuit.txt
- outputs/paper/full/circuit.svg (if qiskit + matplotlib available)
- outputs/paper/full/quantum_result.json

This script will attempt to pick an IBM backend with >=127 qubits if
available in your IBMQ account; otherwise it will run on the Aer simulator.
"""
from pathlib import Path
import sys, os, json

# ensure repo src is importable after site-packages
sys.path.append(os.path.abspath('src'))

from quscope.mos2_workflow import run_comparison
from quscope.mos2_workflow.hamiltonian import build_quantum_phase_oracle_circuit_from_potential
import matplotlib.pyplot as plt
import numpy as np


def save_im(arr, path, cmap='viridis'):
    plt.figure(figsize=(6,6))
    plt.imshow(arr, origin='lower', cmap=cmap)
    plt.axis('off')
    plt.tight_layout(pad=0)
    plt.savefig(path, dpi=300, bbox_inches='tight', pad_inches=0)
    plt.close()


def pick_ibm_backend_name():
    try:
        from qiskit import IBMQ
        if IBMQ.active_account() is None:
            IBMQ.load_account()
        provider = IBMQ.get_provider()
        # find operational backends with >=127 qubits
        candidates = []
        for b in provider.backends():
            try:
                cfg = b.configuration()
                if getattr(cfg, 'n_qubits', 0) >= 127 and getattr(b, 'status', lambda: None)() is not None and b.status().operational:
                    return b.name()
            except Exception:
                continue
    except Exception:
        return None
    return None


def render_and_save_qiskit_circuit(circuit_desc, outdir: Path):
    # Save textual description
    with open(outdir / 'circuit.txt', 'w') as f:
        f.write(json.dumps(circuit_desc, indent=2))

    # Try to build a Qiskit circuit for visualization
    try:
        from qiskit import QuantumCircuit
        n = circuit_desc.get('n_qubits', 6)
        qc = QuantumCircuit(n)
        for q in range(n):
            qc.h(q)
        for q, angle in enumerate(circuit_desc.get('rotations', [])):
            qc.rz(angle, q)
        qc.measure_all()

        # textual
        with open(outdir / 'circuit_qasm.txt', 'w') as f:
            f.write(qc.qasm())

        # draw via matplotlib if available
        try:
            fig = qc.draw(output='mpl')
            fig.savefig(outdir / 'circuit.svg')
            plt.close(fig)
        except Exception:
            # fallback: save ASCII
            with open(outdir / 'circuit_ascii.txt', 'w') as f:
                f.write(qc.draw(output='text'))
    except Exception:
        # qiskit not available
        pass


def main():
    out = Path('outputs/paper/full')
    out.mkdir(parents=True, exist_ok=True)

    print('Building MoSe2 and running comparison...')
    res = run_comparison(nx=3, ny=2, grid_size=512, pixel_size=0.05, voltage=200e3, material='MoSe2', apply_aberration=True)

    Vq = res['V_quantum']
    Va = res['V_abtem']
    I = res['I_classical']

    # Save images
    save_im(Vq, out / 'V_quantum.png')
    save_im(Va, out / 'V_abtem.png')
    save_im(np.abs(Vq - Va), out / 'V_diff.png', cmap='inferno')

    # Save phase map
    sigma = res['converter'].get_interaction_constant()
    phase = sigma * Vq
    save_im(phase, out / 'phase.png', cmap='twilight')

    save_im(I, out / 'I_classical.png', cmap='gray')

    # Circuit description and Qiskit drawing
    circ = res.get('circuit_description') or build_quantum_phase_oracle_circuit_from_potential(Vq)
    render_and_save_qiskit_circuit(circ, out)

    # Try to pick IBM backend with >=127 qubits
    backend_name = pick_ibm_backend_name()
    from quscope.mos2_workflow.hamiltonian import run_quantum_simulation_on_ibm
    if backend_name:
        print('Attempting IBM backend:', backend_name)
        qres = run_quantum_simulation_on_ibm(circ, backend_name=backend_name)
    else:
        print('No suitable IBM backend found; running on local simulator')
        qres = run_quantum_simulation_on_ibm(circ, backend_name=None)

    with open(out / 'quantum_result.json', 'w') as f:
        json.dump(qres, f, indent=2)

    print('Saved outputs in', out)


if __name__ == '__main__':
    main()
