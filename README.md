# 🔬 QuScope v0.2.0: Quantum Algorithms for Electron Microscopy

[![PyPI version](https://badge.fury.io/py/quscope.svg)](https://badge.fury.io/py/quscope)
[![Documentation Status](https://readthedocs.org/projects/quscope/badge/?version=latest)](https://quscope.readthedocs.io/en/latest/?badge=latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Qiskit 2.x](https://img.shields.io/badge/Qiskit-2.x-purple.svg)](https://qiskit.org/)

**QuScope** is a Python package for applying quantum computing algorithms to Transmission Electron Microscopy (TEM) simulation. Built on Qiskit, it provides fully-quantum circuit implementations of every stage of the TEM imaging pipeline — from specimen interaction to detector readout — validated against classical reference implementations with fidelity ≥ 0.9999.

v0.2.0 adds five new fully-quantum modules (multislice, diffraction, STEM, frozen phonon, Bloch wave) expanding the coverage from CTEM to the complete TEM technique suite.

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
print("Wave function shape:", result["wave_function"].shape)   # (8, 8)
print("Intensity range   :", result["intensity"].min(), "–", result["intensity"].max())

# Validate against classical implementation
validator = QuantumClassicalValidator(params)
comparison = validator.compare(V)
print(f"Quantum–classical fidelity: {comparison['fidelity']:.6f}")   # → 1.000000
```

---

## ✨ Key Features

| Module | Technique | Quantum Engine |
|--------|-----------|----------------|
| `quantum_ctem_circuit` | Bright-field CTEM (WPOA + CTF) | QFT on amplitude-encoded wavefunction |
| `quantum_multislice_circuit` | Multislice propagation | Fresnel DiagonalGate + QFT |
| `quantum_diffraction` | WPOA / SAED / CBED / Kikuchi / nBD / EBSD | Phase grating + diffraction QFT |
| `quantum_stem` | HAADF / ADF / ABF / BF / iDPC STEM | Angular-range annular detectors |
| `quantum_frozen_phonon` | Thermal diffuse scattering | QTPC & QPS phonon superposition + Lindblad |
| `quantum_bloch_wave` | Bloch wave diagonalisation | Quantum Phase Estimation (QPE) |
| `ctf_calculator` | CTF / aberration function | Analytical + GPU-ready |

### Diffraction Modes
| Mode | Description |
|------|-------------|
| `simulate_wpoa` | Weak Phase Object approximation — amplitude contrast image |
| `simulate_saed` | Selected Area Electron Diffraction pattern |
| `simulate_cbed` | Convergent Beam Electron Diffraction disk pattern |
| `simulate_kikuchi` | Kikuchi band map via quantum interference |
| `simulate_nbd` | Nano Beam Diffraction |
| `simulate_ebsd` | Electron Back-Scatter Diffraction pattern |

### STEM Channels
| Channel | Inner (mrad) | Outer (mrad) | Contrast |
|---------|:---:|:---:|---------|
| HAADF | 70 | 200 | Z-contrast |
| ADF | 40 | 70 | Mixed |
| ABF | 11 | 22 | Light elements |
| BF | 0 | 11 | Phase |
| iDPC | 0 | 22 | Integrated DPC |

### Frozen Phonon Descriptions
- **QTPC** (`QuantumThermalPhaseCode`) — random phase kicks via parameterised Rz gates
- **QPS** (`QuantumPhononSuperposition`) — coherent phonon superposition with Debye–Waller weighting
- **Lindblad** (`LindbladFrozenPhonon`) — open-quantum-system thermal channel

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
│   ├── quantum_ctem/
│   │   ├── __init__.py                      # 25+ public exports
│   │   ├── quantum_ctem_circuit.py          # CTEM: QFT + CTF DiagonalGate
│   │   ├── quantum_multislice_circuit.py    # Multislice: Fresnel + QFT
│   │   ├── quantum_diffraction.py           # 6 diffraction modes
│   │   ├── quantum_stem.py                  # 5-channel STEM detectors
│   │   ├── quantum_frozen_phonon.py         # QTPC / QPS / Lindblad phonons
│   │   ├── quantum_bloch_wave.py            # QPE-based Bloch wave
│   │   ├── ctf_calculator.py                # CTF + aberration function
│   │   ├── hamiltonian.py                   # Full TEM Hamiltonian
│   │   ├── materials/                       # MoS₂, Graphene structure factors
│   │   ├── mos2_workflow/                   # End-to-end MoS₂ workflow
│   │   └── backends/                        # IBM / Aer backend wrappers
│   ├── image_processing/                    # Quantum image encoding / segmentation
│   ├── eels_analysis/                       # QFT-based EELS processing
│   └── qml/                                 # Quantum machine learning (INEQR)
├── notebooks/
│   ├── 01_getting_started.ipynb
│   ├── 02_quantum_ctem_advanced.ipynb
│   ├── 03_material_workflows.ipynb
│   ├── 05_fully_quantum_ctem.ipynb          # Quantum CTEM circuit showcase
│   ├── 06_quantum_ctf_envelope.ipynb
│   ├── 07_si3n4_quantum_multislice.ipynb
│   ├── 08_fully_quantum_tem_advanced.ipynb  # All 6 quantum modules
│   └── 09_quantum_multislice_circuit_test.ipynb
├── kirkland.json                            # Kirkland potential parameters (20 elements)
├── pyproject.toml
└── docs/
```

---

## 💡 Usage Examples

### 1. Quantum CTEM (bright-field imaging)

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
# result keys: wave_function, amplitude, phase, intensity
```

### 2. Quantum Multislice

```python
from quscope.quantum_ctem import QuantumMultisliceCircuit, QuantumMultisliceParameters

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
```

### 3. Quantum Diffraction (6 modes)

```python
from quscope.quantum_ctem import QuantumDiffractionSimulator, QuantumCTEMParameters

params = QuantumCTEMParameters(acceleration_voltage=200e3, grid_size=8, pixel_size=0.5)
sim = QuantumDiffractionSimulator(params)
V = np.random.rand(8, 8) * 100

saed  = sim.simulate_saed(V)        # Selected Area ED
cbed  = sim.simulate_cbed(V)        # Convergent Beam ED
kiku  = sim.simulate_kikuchi(V)     # Kikuchi bands
```

### 4. Quantum STEM

```python
from quscope.quantum_ctem import QuantumSTEMSimulator, STEMDetectors, QuantumCTEMParameters

params  = QuantumCTEMParameters(acceleration_voltage=200e3, grid_size=8, pixel_size=0.5)
dets    = STEMDetectors()            # default angular ranges
sim     = QuantumSTEMSimulator(params, dets)
V_scan  = np.random.rand(4, 4, 8, 8) * 50   # (nx, ny, Nx, Ny)

result = sim.run_stem(V_scan)
# result["HAADF"], result["ABF"], result["iDPC"], ...
```

### 5. Frozen Phonon (thermal diffuse scattering)

```python
from quscope.quantum_ctem import (
    QuantumPhononSuperposition,
    DebyeWaller,
)
import numpy as np

dw = DebyeWaller(B_iso=0.5)         # Debye–Waller factor (Å²)
N, px = 8, 0.5
V = np.random.rand(N, N) * 100

qps = QuantumPhononSuperposition(N, px, V, dw, n_phonon_qubits=2)
result = qps.simulate(V)            # thermally averaged intensity
```

### 6. Bloch Wave (quantum phase estimation)

```python
from quscope.quantum_ctem import BlochWaveMatrix, QuantumBlochWave
from quscope.quantum_ctem.materials import MoS2StructureFactors

sf  = MoS2StructureFactors(acceleration_voltage=200e3, g_max=0.5)
bwm = BlochWaveMatrix(sf, g_max=0.5)

qbw = QuantumBlochWave(bwm, n_precision=4)
result = qbw.simulate_qpe()
# result keys: eigenvalues_quantum, eigenvalues_classical, fidelity
```

---

## ✅ Validated Results

All modules are smoke-tested and validated against classical reference implementations:

| Module | Grid | Qubits | Fidelity | RMSE |
|--------|------|--------|----------|------|
| `QuantumCTEMCircuit` | 8×8 | 6 | 1.000000 | < 1 × 10⁻¹³ |
| `QuantumMultisliceCircuit` | 8×8 | 6 | 1.000000 | 3.6 × 10⁻¹⁴ |
| `QuantumDiffractionSimulator` (WPOA) | 8×8 | 6 | 1.000000 | < 1 × 10⁻¹³ |
| `QuantumSTEMSimulator` (HAADF) | 8×8 | 6 | ≥ 0.9999 | < 1 × 10⁻⁶ |
| `QuantumPhononSuperposition` | 8×8 | 8 | ≥ 0.9999 | < 1 × 10⁻⁶ |
| `QuantumBlochWave` (QPE) | N/A | 6+4 | ≥ 0.9999 | < 1 × 10⁻³ |

All simulations run on `StatevectorSimulator` (exact) and are ready for transpilation to IBM hardware.

---

## 📓 Notebooks

| Notebook | Description |
|----------|-------------|
| [01_getting_started](notebooks/01_getting_started.ipynb) | Package overview, CTEM basics, Scherzer defocus |
| [02_quantum_ctem_advanced](notebooks/02_quantum_ctem_advanced.ipynb) | Advanced CTEM: aberrations, CTF envelopes |
| [03_material_workflows](notebooks/03_material_workflows.ipynb) | MoS₂ and Graphene end-to-end workflows |
| [05_fully_quantum_ctem](notebooks/05_fully_quantum_ctem.ipynb) | Quantum circuit CTEM showcase |
| [06_quantum_ctf_envelope](notebooks/06_quantum_ctf_envelope.ipynb) | CTF envelope & damping functions |
| [07_si3n4_quantum_multislice](notebooks/07_si3n4_quantum_multislice.ipynb) | Si₃N₄ multislice quantum simulation |
| [08_fully_quantum_tem_advanced](notebooks/08_fully_quantum_tem_advanced.ipynb) | **All 6 quantum modules** — full demonstration |
| [09_quantum_multislice_circuit_test](notebooks/09_quantum_multislice_circuit_test.ipynb) | Fresnel propagator circuit validation |

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

### Bloch Wave (Quantum Phase Estimation)
```
|0⟩⊗p (precision) ─[H⊗p]─ ─────── control-U^k ─────── [QFT†]─ |phase⟩
|0⟩⊗b (eigenvec)  ──────── [prepare_eigenstate] ────────────── |eigenvec⟩
```

---

## 📋 API Reference

```python
from quscope.quantum_ctem import (
    # CTEM
    QuantumCTEMCircuit, QuantumCTEMParameters, QuantumClassicalValidator,
    # Multislice
    QuantumMultisliceCircuit, QuantumMultisliceParameters,
    FresnelPropagatorCircuit, QuantumClassicalMultisliceValidator,
    # Diffraction
    QuantumDiffractionSimulator,
    # STEM
    QuantumSTEMSimulator, STEMDetectors,
    # Frozen phonon
    QuantumThermalPhaseCode, QuantumPhononSuperposition,
    DebyeWaller, LindbladFrozenPhonon,
    # Bloch wave
    BlochWaveMatrix, QuantumBlochWave,
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

```bibtex
@software{quscope_reis_2026,
  author    = {Reis, Roberto},
  title     = {{QuScope: Fully-Quantum Algorithms for Transmission Electron Microscopy}},
  year      = {2026},
  version   = {0.2.0},
  publisher = {GitHub},
  url       = {https://github.com/QuScope/QuScope}
}
```

---

*For questions, issues, or suggestions, please open an issue on the [GitHub repository](https://github.com/QuScope/QuScope).*
