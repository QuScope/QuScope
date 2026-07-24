# 🔬 QuScope v0.2.0: Quantum Algorithms for Electron Microscopy

[![PyPI version](https://badge.fury.io/py/quscope.svg)](https://badge.fury.io/py/quscope)
[![Documentation Status](https://readthedocs.org/projects/quscope/badge/?version=latest)](https://quscope.readthedocs.io/en/latest/?badge=latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Qiskit 2.x](https://img.shields.io/badge/Qiskit-2.x-purple.svg)](https://qiskit.org/)

**QuScope** is a Python package for applying quantum computing algorithms to Transmission Electron Microscopy (TEM) simulation. Built on Qiskit, it expresses the TEM image-formation pipeline as quantum circuits — the electron wavefunction is amplitude-encoded on qubits, and every optical element (phase grating, Fresnel propagation, objective lens) is a diagonal unitary conjugated by quantum Fourier transforms — validated against classical reference implementations to unit fidelity.

v0.2.0 provides four fully-quantum imaging pipelines: **CTEM (WPOA)**, **CTEM multislice**, **STEM (WPOA)**, and **STEM multislice**.

**Developed by** [Sean D. Lam](https://arxiv.org/search/quant-ph?searchtype=author&query=Lam,+S+D) and [Roberto dos Reis](https://arxiv.org/search/quant-ph?searchtype=author&query=Reis,+R+d) · Northwestern University

> 📄 **Paper**: [*Quantum Algorithm Framework for Phase-Contrast Transmission Electron Microscopy Image Simulation*](https://arxiv.org/abs/2602.13438) — arXiv:2602.13438 [quant-ph], Feb 2026

---

## 🚀 Quick Start

```bash
pip install quscope
```

```python
from quscope.quantum_ctem import (
    QuantumCTEMCircuit,
    QuantumCTEMParameters,
    QuantumClassicalValidator,
)
import numpy as np

# 8×8 grid (6 qubits), 200 kV, Scherzer condition
params = QuantumCTEMParameters(
    acceleration_voltage=200e3,
    grid_size=8,
    pixel_size=0.5,       # Å/pixel
    defocus=-659.7,       # Å  (Scherzer defocus)
    cs=1.3,               # mm
)
sim = QuantumCTEMCircuit(params)

# Simulate a random projected potential
V = np.random.rand(8, 8) * 100          # projected potential in V·Å

result = sim.simulate(V)
print("Image shape    :", result["intensity"].shape)   # (8, 8)
print("Intensity range:", result["intensity"].min(), "–", result["intensity"].max())

# Validate against classical implementation
validator = QuantumClassicalValidator(params)
comparison = validator.compare(V)
print(f"Quantum–classical fidelity: {comparison['fidelity']:.6f}")   # → 1.000000
```

---

## ✨ Available Modules (v0.2.0)

| Module | Technique | Quantum Engine |
|--------|-----------|----------------|
| `quantum_ctem_circuit` | CTEM bright-field imaging (WPOA + CTF) | Phase-grating DiagonalGate → QFT → CTF DiagonalGate → IQFT |
| `quantum_multislice_circuit` | CTEM multislice propagation | Alternating phase grating / Fresnel-propagator DiagonalGates + QFT |
| `quantum_stem` | STEM imaging (single-slice WPOA) | One quantum circuit per probe position |
| `quantum_stem_multislice` | STEM multislice propagation | Probe state through the multislice circuit per scan position |

Supporting infrastructure: `ctf_calculator` (aberration function), `hamiltonian` (TEM Hamiltonian), `momentum_space`, `quantum_encoding`, classical reference implementations (`classical_validation`, `ctem/`, `simulations/`), Kirkland scattering-factor tables (`utils/`), materials workflows (MoS₂, graphene), circuit optimization, and IBM Quantum backend wrappers.

### STEM Detector Channels
| Channel | Inner (mrad) | Outer (mrad) | Contrast |
|---------|:---:|:---:|---------|
| HAADF | 60 | 200 | Z-contrast |
| ADF | 25 | 60 | Mixed |
| ABF | 10 | 25 | Light elements |
| BF | 0 | 10 | Phase |
| iDPC | — | — | From BF centre-of-mass |

### 🛣 Roadmap
Quantum diffraction modes (SAED, CBED, nBD, Kikuchi, EBSD), frozen-phonon /
thermal-diffuse-scattering channels, and the Bloch-wave QPE eigensolver are
under development on the [`dev`](https://github.com/QuScope/QuScope/tree/dev)
branch and planned for a future release.

---

## 📦 Installation

### From PyPI (recommended)
```bash
pip install quscope
```

### Development install
```bash
git clone https://github.com/QuScope/QuScope.git
cd QuScope
pip install -e ".[all]"
```

### IBM Quantum access (optional — for real hardware)
```bash
export IBMQ_TOKEN="YOUR_API_TOKEN"
```

---

## 🗂 Repository Structure

```
quantum_algo_microscopy/
├── src/quscope/
│   ├── quantum_ctem/                        # Core quantum TEM modules
│   │   ├── quantum_ctem_circuit.py          # CTEM WPOA: QFT + CTF DiagonalGate
│   │   ├── quantum_multislice_circuit.py    # CTEM multislice: Fresnel + QFT
│   │   ├── quantum_stem.py                  # STEM WPOA (HAADF/ADF/ABF/BF/iDPC)
│   │   ├── quantum_stem_multislice.py       # STEM multislice
│   │   ├── quantum_encoding.py              # Amplitude encoding utilities
│   │   ├── quantum_simulation.py            # High-level simulation runner
│   │   ├── quantum_wave_function.py         # Wavefunction helper
│   │   ├── quantum_tomography.py            # Quantum state tomography
│   │   ├── ctf_calculator.py                # CTF + aberration function
│   │   ├── hamiltonian.py                   # Full TEM Hamiltonian
│   │   ├── momentum_space.py                # Reciprocal-space utilities
│   │   ├── classical_integration.py         # abTEM / Kirkland bridge
│   │   ├── classical_validation.py          # Classical reference implementations
│   │   ├── circuit_optimization.py          # Gate cancellation & transpilation
│   │   ├── performance_benchmarking.py      # Benchmark suite
│   │   ├── materials/                       # MoS₂, Graphene structure factors
│   │   ├── mos2_workflow/                   # End-to-end MoS₂ orchestration
│   │   ├── workflows/                       # Reusable workflow base classes
│   │   └── backends/                        # IBM Quantum / Aer backend wrappers
│   ├── ctem/                                # Classical CTEM (reference)
│   ├── simulations/                         # Shared simulation utilities
│   ├── utils/                               # Constants, Kirkland parameters
│   └── quantum_backend.py                   # IBM Quantum session manager
├── notebooks/                               # Executable documentation
├── pyproject.toml
└── docs/                                    # Sphinx documentation source
```

---

## 💡 Usage Examples

### 1. Quantum CTEM (bright-field imaging, WPOA)

```python
from quscope.quantum_ctem import QuantumCTEMCircuit, QuantumCTEMParameters
import numpy as np

params = QuantumCTEMParameters(
    acceleration_voltage=200e3,
    grid_size=16,
    pixel_size=0.25,
    defocus=-659.7,
    cs=1.3,
)
result = QuantumCTEMCircuit(params).simulate(np.random.rand(16, 16) * 50)
# result keys: circuit, psi_image, intensity, metrics, parameters
```

### 2. Quantum CTEM Multislice

```python
from quscope.quantum_ctem import (
    QuantumMultisliceCircuit,
    QuantumMultisliceParameters,
    QuantumClassicalMultisliceValidator,
)

params = QuantumMultisliceParameters(
    acceleration_voltage=200e3,
    grid_size=8,
    pixel_size=0.5,
    defocus=-500.0,
    cs=1.3,
    slice_thickness=2.0,   # Å per slice
)
potentials = [np.random.rand(8, 8) * 30 for _ in range(4)]   # 4-slice specimen
result = QuantumMultisliceCircuit(params).simulate(potentials)

# Validate against the classical multislice reference
cmp = QuantumClassicalMultisliceValidator(params).compare(potentials)
print(f"fidelity: {cmp['fidelity']:.6f}")   # → 1.000000
```

### 3. Quantum STEM (single-slice WPOA)

```python
from quscope.quantum_ctem import run_stem, STEMDetectors
import numpy as np

N, px = 16, 0.12                     # Nyquist must exceed detector angles:
V = np.random.rand(N, N) * 100       # k_max = 1/(2·px) vs θ/λ

result = run_stem(
    V, pixel_size=px, voltage=200e3,
    convergence_mrad=20.0,
    detectors=STEMDetectors(),       # default angular ranges
    scan_step_px=1,
)
# result["HAADF"], result["ADF"], result["ABF"], result["BF"], result["iDPC"]
```

### 4. Quantum STEM Multislice

```python
from quscope.quantum_ctem import run_stem_multislice

result = run_stem_multislice(
    V, pixel_size=px, voltage=200e3,
    n_slices=4, slice_thickness=6.5,   # or pass a (n_slices, N, N) array
    convergence_mrad=20.0,
)
# Same detector channels as run_stem; per-position quantum multislice circuit
```

---

## ✅ Validated Results

Every quantum pipeline is validated against a classical twin implementation:

| Check | Result |
|-------|--------|
| Relativistic wavelength vs literature (100/200/300 kV) | exact (0.037014 / 0.025079 / 0.019687 Å) |
| Interaction constant σ vs literature | exact (e.g. 0.72884×10⁻³ rad V⁻¹Å⁻¹ at 200 kV) |
| CTF χ(k) and Fresnel propagator vs Kirkland closed forms | machine precision |
| Quantum vs classical multislice exit wave | fidelity 1.000000 |
| STEM multislice single-slice limit vs `run_stem` | correlation 1.0000 |

All simulations run on Qiskit `Statevector` (exact) and are ready for transpilation to IBM hardware.

---

## 📓 Notebooks

| Notebook | Description |
|----------|-------------|
| [01_getting_started](notebooks/01_getting_started.ipynb) | Package overview, CTEM basics, Scherzer defocus |
| [02_quantum_ctem_advanced](notebooks/02_quantum_ctem_advanced.ipynb) | Advanced CTEM: aberrations, CTF envelopes |
| [03_material_workflows](notebooks/03_material_workflows.ipynb) | MoS₂ and Graphene end-to-end workflows |
| [05_fully_quantum_ctem](notebooks/05_fully_quantum_ctem.executed.ipynb) | Quantum circuit CTEM showcase (pre-executed) |
| [06_quantum_ctf_envelope](notebooks/06_quantum_ctf_envelope.ipynb) | CTF envelope & damping functions |
| [07_si3n4_quantum_multislice](notebooks/07_si3n4_quantum_multislice.ipynb) | Si₃N₄ multislice quantum simulation |
| [10_quantum_ctem](notebooks/10_quantum_ctem.ipynb) | Quantum circuit CTEM demonstration — WPOA & multislice |
| [11_quantum_stem](notebooks/11_quantum_stem.ipynb) | Quantum circuit STEM demonstration — WPOA & multislice |

---

## ⚙️ Circuit Architectures

### CTEM (WPOA)
```
|0⟩⊗n ─[H⊗n]─[DiagGate(exp(iσV))]─[QFT]─[DiagGate(exp(iχ))]─[QFT†]─ |ψ_image⟩
              phase grating           k-sp  lens CTF              image
```

### Multislice (Fresnel propagation)
```
|0⟩⊗n ─[H⊗n]─( [PhaseGrating(V_j)] ─ [QFT] ─ [FresnelProp(dz)] ─ [QFT†] )×N_slices─ |ψ⟩
```

### STEM (per probe position)
```
|probe(r_s)⟩ ─( [PhaseGrating(V_j)] ─ [QFT] ─ [FresnelProp(dz)] ─ [QFT†] )×N_slices─ → detector integrals
```

---

## 📋 API Reference

```python
from quscope.quantum_ctem import (
    # CTEM (WPOA)
    QuantumCTEMCircuit, QuantumCTEMParameters, QuantumClassicalValidator,
    # CTEM multislice
    QuantumMultisliceCircuit, QuantumMultisliceParameters,
    FresnelPropagatorCircuit, QuantumClassicalMultisliceValidator,
    # STEM
    STEMDetectors, run_stem,
    # STEM multislice
    run_stem_multislice, build_probe_circuit, fresnel_propagator_phase,
    # CTF
    CTFCalculator,
    # Hamiltonian
    TEMHamiltonian,
)
```

Full Sphinx documentation: [quscope.readthedocs.io](https://quscope.readthedocs.io)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit with descriptive messages
4. Ensure `pytest` passes and coverage remains ≥ 80 %
5. Open a Pull Request to `main`

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 📜 Citation

If you use QuScope in your research, please cite the companion paper:

```bibtex
@article{lam2026quantum,
  title     = {{Quantum Algorithm Framework for Phase-Contrast Transmission
               Electron Microscopy Image Simulation}},
  author    = {Lam, Sean D. and dos Reis, Roberto},
  journal   = {arXiv preprint},
  volume    = {arXiv:2602.13438},
  year      = {2026},
  url       = {https://arxiv.org/abs/2602.13438},
  doi       = {10.48550/arXiv.2602.13438}
}
```
