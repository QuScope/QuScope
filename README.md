# QuScope v0.1.0: Quantum Algorithms for Microscopy

[![GitHub release](https://img.shields.io/github/v/release/QuScope/QuScope?include_prereleases&label=version)](https://github.com/QuScope/QuScope/releases)
[![Documentation Status](https://readthedocs.org/projects/quscope/badge/?version=latest)](https://quscope.readthedocs.io/en/latest/?badge=latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests](https://github.com/QuScope/QuScope/workflows/Tests/badge.svg)](https://github.com/QuScope/QuScope/actions)

Developers: Roberto dos Reis and Sean Lam

**QuScope** is a Python framework integrating quantum computing algorithms with electron microscopy analysis. Built on Qiskit, QuScope provides quantum circuit implementations for image processing and EELS feature extraction, establishing a foundation for quantum-enhanced materials characterization.

> **v0.1.0 Status**: Published on PyPI - This is a foundational release demonstrating quantum-classical integration patterns. See [Current Capabilities](#current-capabilities-v010) for details.

## Installation

QuScope v0.1.0 is available on PyPI:

```bash
pip install quscope
```

For development installation:

```bash
git clone https://github.com/QuScope/QuScope.git
cd QuScope
pip install -e .
```

```python
import quscope
from quscope.image_processing.quantum_encoding import encode_image_to_circuit, EncodingMethod
import numpy as np

# Create a sample image
image = np.random.rand(4, 4)

# Encode into quantum circuit
circuit = encode_image_to_circuit(image, method=EncodingMethod.AMPLITUDE)
print(f"Encoded into {circuit.num_qubits} qubits")
```

## Current Capabilities (v0.1.0)

QuScope v0.1.0 provides a **foundational framework** for quantum-classical microscopy analysis:

### ✅ Implemented Features

**Image Processing**:
- Multiple quantum encoding methods (Amplitude, Basis, Angle, FRQI, INEQR)
- Grover's algorithm for image segmentation
- Quantum-guided classical denoising (4×4 patches, 16 qubits)
- Classical preprocessing utilities

**EELS Analysis**:
- Classical preprocessing (Richardson-Lucy, Kramers-Kronig)
- Quantum feature extraction (parameterized circuits, 4-8 qubits)
- Element identification (~20 common elements)
- Property lookup from reference database

**Backend Management**:
- IBM Quantum integration
- Simulator support (Aer, statevector)
- Noise model capabilities

### ⚠️ Important Notes

**Current Limitations**:
- EELS preprocessing is classical (quantum enhancement planned)
- Element database covers ~20 elements (expansion ongoing)
- Property predictions use reference lookup (not quantum-derived)
- Image processing limited by NISQ constraints (small patches)
- Most workflows use classical simulation

**Not Yet Implemented** (Planned for Future):
- Electron diffraction analysis (placeholder in v0.1.0)
- Advanced QML models
- Comprehensive materials database
- Many-body effects analysis
- Magnetic characterization

## Key Features (Detailed)

*   **IBM Quantum Integration**:
    *   Connection to IBM Quantum backends via `QuantumBackendManager`
    *   API token authentication (environment variable or direct input)
    *   Execution on simulators (Aer) and real quantum hardware
    *   Backend selection and noise model integration
    
*   **Quantum Image Encoding**:
    *   Multiple encoding methods: Amplitude, Basis, Angle, FRQI
    *   Optional INEQR encoding (requires PiQture)
    *   Support for grayscale images
    *   Resource analysis utilities (qubits, depth, gates)
    
*   **Quantum-Classical Image Denoising**:
    *   Grover's algorithm for noise candidate identification
    *   Quantum feature extraction (entropy, confidence, correlation)
    *   Adaptive classical filtering guided by quantum features
    *   Patch-based processing (4×4 patches, 16 qubits)
    *   Performance metrics (SNR improvement, edge preservation)
    
*   **Image Segmentation**:
    *   Grover's algorithm with customizable oracles
    *   Threshold-based, edge-based, region-based segmentation
    *   Automatic Grover iteration optimization
    *   Visualization and analysis tools
    
*   **EELS Analysis Framework**:
    *   **Classical preprocessing**: Background subtraction, normalization, Richardson-Lucy deconvolution, Kramers-Kronig analysis
    *   **Quantum feature extraction**: Parameterized circuits (4-8 qubits) for spectral signatures
    *   **Element identification**: Peak detection and database matching (~20 elements: C, N, O, Si, Fe, Cu, Al, Ti, Cr, Ni, B, Mg, Ca, Na, K, S, Cl, P, Mn, Co)
    *   **Property lookup**: Reference-based material classification and properties
*   **Synthetic Data Generation**:
    *   Functions to generate synthetic electron microscopy images with particles and noise.
    *   Functions to generate synthetic EELS spectra with customizable peaks and background.
*   **Professional Code Structure**:
    *   Modular design with clear separation of concerns (image processing, EELS analysis, QML, backend management).
    *   Comprehensive docstrings and type hinting.
    *   Robust error handling and logging.
*   **Jupyter Notebook Examples**:
    *   A detailed example notebook (`notebooks/complete_quantum_microscopy_examples.ipynb`) showcasing all major functionalities, suitable for educational purposes and as a basis for scientific publications.
*   **Resource Analysis and Optimization**:
    *   Tools to analyze circuit resources (qubits, depth, gate counts).
    *   Demonstration of circuit optimization using Qiskit's transpiler.

## Repository Structure

```
QuScope/
├── notebooks/                      # Jupyter notebooks with examples
│   ├── complete_quantum_microscopy_examples.ipynb  # Comprehensive examples
│   ├── image_denoising.ipynb       # Image denoising examples
│   └── qml_image_encoding_example.ipynb  # QML examples
├── src/
│   └── quscope/                    # Main package source
│       ├── eels_analysis/          # EELS analysis modules
│       │   ├── __init__.py
│       │   ├── preprocessing.py
│       │   └── quantum_processing.py
│       ├── electron_diffraction/   # Electron Diffraction analysis modules
│       ├── image_processing/       # Quantum image processing modules
│       │   ├── __init__.py
│       │   ├── preprocessing.py
│       │   ├── quantum_encoding.py
│       │   ├── quantum_segmentation.py
│       │   ├── filtering.py
│       │   └── image_denoising.py  # Quantum-classical hybrid denoising
│       ├── qml/                    # Quantum Machine Learning modules
│       │   ├── __init__.py
│       │   └── image_encoding.py
│       ├── simulations/            # Simulation modules
│       │   ├── __init__.py
│       │   ├── multislice.py       # Multislice methods
│       │   ├── quantum_utils.py    # Quantum algorithms for simulations
│       │   └── wpo.py              # Weak phase object approximation calculations
│       ├── utils/                  # Utility modules
│       │   ├── __init__.py
│       │   ├── constants.py        # Physical constants
│       │   ├── kirkland.json       # Kirkland parameters
│       │   └── kirkland.py         # Atomic potential calculations
│       ├── __init__.py
│       └── quantum_backend.py      # IBM Quantum backend management
├── docs/                           # Sphinx documentation
│   ├── conf.py
│   ├── index.rst
│   └── notebooks/                  # Documentation notebooks
├── tests/                          # Test suite
├── README.md                       # This file
├── pyproject.toml                  # Modern Python packaging configuration
├── requirements.txt                # Project dependencies
└── .readthedocs.yaml              # Read the Docs configuration
```

## Installation

### From PyPI (Coming Soon)

> Status: QuScope v0.1.0 will be available on PyPI after the first official release is created on GitHub.

```bash
pip install quscope  # Available after v0.1.0 release
```

### Development Installation (Current)

```bash
git clone https://github.com/QuScope/QuScope.git
cd QuScope
pip install -e .
```

### Prerequisites

*   Python 3.9 or higher
*   Qiskit (core, aer, ibm-provider) - see `requirements.txt` for specific versions.
*   NumPy, SciPy, Matplotlib, Pillow, Pandas, Scikit-image, PiQture, etc. (see `requirements.txt`)

### Development Setup

Conda environment (recommended)
-------------------------------

We provide an example `environment.yml` tailored to this project. It creates a reproducible conda environment named `quantum` with abTEM, ASE and common scientific packages.

Create and activate the environment:

```bash
conda env create -f environment.yml
conda activate quantum
```

Install the project in editable mode:

```bash
pip install -e .
# (Optional) Install extras for development
pip install -e .[dev]
```

Run the MoS2 smoke test (small grid) to verify the environment is working:

```bash
python scripts/run_smoke_test.py
```

Notes and troubleshooting:

- abTEM is distributed on conda-forge; if you run into GPU-related issues, ensure you have a compatible CUDA runtime and the correct abTEM build for your platform.
- If you only need CPU execution, the conda-forge abTEM package will run on CPU by default.
- If you prefer a pip-only setup, you can recreate a virtualenv and install the same pip packages listed in `environment.yml` (abTEM is recommended via conda-forge).

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/QuScope/QuScope.git
    cd QuScope
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install in development mode:**
    ```bash
    pip install -e .[docs,dev]
    ```

4.  **Set up IBM Quantum Access (Optional, for running on IBM backends):**
    *   Obtain an API token from your [IBM Quantum account](https://quantum.ibm.com/).
    *   Set the `IBMQ_TOKEN` environment variable:
        ```bash
        export IBMQ_TOKEN="YOUR_API_TOKEN_HERE"
        ```
        Alternatively, the token can be provided directly when initializing `QuantumBackendManager`.

## Usage

The `quscope` package provides a range of functionalities accessible through its modules. Below are some basic usage examples. For detailed demonstrations, please refer to the `notebooks/complete_quantum_microscopy_examples.ipynb` notebook.

### 1. IBM Quantum Backend Management

```python
from quscope.quantum_backend import get_backend_manager, IBMQConfig

# Initialize with default config (tries to load token from IBMQ_TOKEN env var)
manager = get_backend_manager()

# Or, provide token and custom config
# config = IBMQConfig(token="YOUR_TOKEN", hub="your-hub", group="your-group", project="your-project")
# manager = get_backend_manager(config=config)

# List available backends
print(manager.get_available_backends())

# Select a backend (e.g., a simulator)
manager.select_backend("aer_simulator")
# To use a real device (if you have access and have authenticated):
# manager.select_least_busy_backend(min_qubits=5, simulator=False)

# Get noise model (optional, for noisy simulation)
# noise_model = manager.get_noise_model()

# Execute a quantum circuit (qc is a QuantumCircuit object)
# result = manager.execute_circuit(qc, shots=1024, noise_model=noise_model)
# counts = result.get_counts()
# print(counts)
```

### 2. Image Preprocessing

```python
from quscope.image_processing.preprocessing import preprocess_image
from PIL import Image
import numpy as np

# Create a dummy image file for example
dummy_image = Image.fromarray((np.random.rand(64, 64) * 255).astype(np.uint8))
dummy_image_path = "dummy_image.png"
dummy_image.save(dummy_image_path)

# Preprocess an image (resize to 8x8, convert to grayscale, normalize)
img_array_normalized = preprocess_image(dummy_image_path, size=(8, 8))
print(f"Preprocessed image shape: {img_array_normalized.shape}")

# Clean up dummy image
import os
os.remove(dummy_image_path)
```

### 3. Quantum Image Encoding

```python
from quscope.image_processing.quantum_encoding import encode_image_to_circuit, EncodingMethod

# Assuming img_array_normalized from previous step (e.g., 8x8)
# Encode using Amplitude Encoding
amplitude_encoded_circuit = encode_image_to_circuit(
    img_array_normalized,
    method=EncodingMethod.AMPLITUDE
)
print(f"Amplitude encoded circuit: {amplitude_encoded_circuit.num_qubits} qubits, depth {amplitude_encoded_circuit.depth()}")

# Encode using FRQI
frqi_encoded_circuit = encode_image_to_circuit(
    img_array_normalized,
    method=EncodingMethod.FRQI
)
print(f"FRQI encoded circuit: {frqi_encoded_circuit.num_qubits} qubits, depth {frqi_encoded_circuit.depth()}")
```

### 4. Quantum Image Segmentation (Grover's Algorithm)

```python
from quscope.image_processing.quantum_segmentation import segment_image, interpret_results, SegmentationMethod
# Assuming img_array_normalized (8x8) and backend_manager are defined

# Define segmentation parameters for threshold-based segmentation
segmentation_params = {
    "threshold": 0.5,
    "comparison": "greater"
}

# Create the segmentation circuit
segmentation_circuit, params = segment_image(
    img_array_normalized,
    method=SegmentationMethod.THRESHOLD,
    encoding_method=EncodingMethod.AMPLITUDE,
    parameters=segmentation_params,
    iterations=2 # Number of Grover iterations
)
print(f"Segmentation circuit: {segmentation_circuit.num_qubits} qubits, depth {segmentation_circuit.depth()}")

# Execute the circuit (using the selected backend_manager)
# result = backend_manager.execute_circuit(segmentation_circuit, shots=1024)
# counts = result.get_counts()

# Interpret results (assuming 'counts' are obtained)
# segmentation_result_obj = interpret_results(
#     counts,
#     img_array_normalized.shape,
#     method=SegmentationMethod.THRESHOLD,
#     parameters=params
# )
# segmented_image_mask = segmentation_result_obj.get_segmentation_mask()
# print(f"Segmented image mask shape: {segmented_image_mask.shape}")
# segmentation_result_obj.visualize(original_image=img_array_normalized)
```

### 5. Quantum EELS Analysis (QFT)

```python
from quscope.eels_analysis.preprocessing import preprocess_eels_data
from quscope.eels_analysis.quantum_processing import create_eels_circuit, apply_qft_to_eels
import numpy as np

# Generate synthetic EELS data for example
energy_axis = np.linspace(0, 1000, 256)
spectrum = 100 * np.exp(-((energy_axis - 500) / 50)**2) + np.random.rand(256) * 10

# Preprocess EELS data (e.g., select range, normalize)
# This is a simplified version; refer to the notebook for detailed preprocessing
preprocessed_eels_data = spectrum / np.max(spectrum)
eels_subset = preprocessed_eels_data[:32] # Use 32 points for 5 qubits

# Create quantum circuit for EELS data (amplitude encoding)
eels_qc = create_eels_circuit(eels_subset)
print(f"EELS circuit: {eels_qc.num_qubits} qubits, depth {eels_qc.depth()}")

# Apply QFT
qft_eels_qc = apply_qft_to_eels(eels_qc)
print(f"QFT EELS circuit: {qft_eels_qc.num_qubits} qubits, depth {qft_eels_qc.depth()}")

# Execute and analyze (similar to image segmentation)
# result = backend_manager.execute_circuit(qft_eels_qc, shots=2048)
# counts = result.get_counts()
# print(counts) # These counts represent the frequency components
```

### 6. INEQR Encoding (using PiQture via QML module)

```python
from quscope.qml.image_encoding import encode_image_ineqr
# Assuming img_array_normalized (e.g., 8x8)

try:
    ineqr_circuit = encode_image_ineqr(img_array_normalized)
    print(f"INEQR circuit: {ineqr_circuit.num_qubits} qubits, depth {ineqr_circuit.depth()}")
except ImportError:
    print("PiQture library not found. Skipping INEQR example.")
except Exception as e:
    print(f"Error during INEQR encoding: {e}")

```

For more detailed examples, including data generation, visualization, and advanced usage, please see the Jupyter Notebook: `notebooks/complete_quantum_microscopy_examples.ipynb`.

## Documentation

Full documentation is available at **[quscope.readthedocs.io](https://quscope.readthedocs.io)**

The documentation includes:
- **API Reference**: Complete documentation of all modules and functions
- **Tutorials**: Step-by-step guides for common tasks
- **Examples**: Jupyter notebook examples demonstrating key features
- **Installation Guide**: Detailed setup instructions

You can also build the documentation locally:
```bash
cd docs
make html
```

## Performance and Benchmarking

The `QuantumBackendManager` and the example notebook facilitate performance comparisons:
*   **Ideal vs. Noisy Simulation**: Execute circuits on `aer_simulator` with and without a `NoiseModel` derived from real IBM hardware.
*   **Simulator vs. Real Hardware**: Compare execution times, results, and fidelity between simulators and actual IBM Quantum devices (requires IBM Quantum access).
*   **Resource Analysis**: Utilities are provided to analyze circuit depth, qubit count, and gate operations, aiding in algorithm optimization.

The `notebooks/complete_quantum_microscopy_examples.ipynb` includes sections on performance comparison and resource analysis.

## Real-world Applications

QuScope aims to bridge the gap between theoretical quantum algorithms and practical applications in materials science and biology through electron microscopy. Potential applications include:
*   **Enhanced Image Segmentation**: Identifying nanoparticles, defects, or biological structures with potentially higher accuracy or efficiency.
*   **Advanced EELS Analysis**: Quantum-enhanced feature extraction from EELS spectra for material identification and chemical state analysis.
*   **Quantum Machine Learning for Microscopy**: Classifying images, detecting anomalies, or predicting material properties from microscopy data.
*   **Noise Reduction and Image Restoration**: Exploring quantum algorithms for denoising and improving the quality of microscopy images.

## Scientific Publication

This package is developed to support research in quantum algorithms for electron microscopy. If you use QuScope in your research, please cite:

```bibtex
@software{quscope_2025,
  author = {Reis, Roberto and Lam, Sean},
  title = {{QuScope: Quantum Algorithms for Advanced Electron Microscopy}},
  version = {0.1.0},
  year = {2025},
  publisher = {GitHub},
  journal = {GitHub repository},
  url = {https://github.com/QuScope/QuScope},
  doi = {10.5281/zenodo.XXXXXXX}
}
```

## Contributing

Contributions to QuScope are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- **GitHub Repository**: [https://github.com/QuScope/QuScope](https://github.com/QuScope/QuScope)
- **Documentation**: [https://quscope.readthedocs.io](https://quscope.readthedocs.io)
- **PyPI Package**: [https://pypi.org/project/quscope/](https://pypi.org/project/quscope/)
- **Issues**: [https://github.com/QuScope/QuScope/issues](https://github.com/QuScope/QuScope/issues)

## Support

If you encounter any issues or have questions:
1. Check the [documentation](https://quscope.readthedocs.io)
2. Look through existing [issues](https://github.com/QuScope/QuScope/issues)
3. Create a new issue with details about your problem

---

## Contributions

To contribute to QuScope:
1.  Make your changes and commit them with clear, descriptive messages.
2.  Ensure your code adheres to PEP 8 style guidelines and includes docstrings.
3.  Add or update unit tests for your changes.
4.  Push your branch to your fork (`git push origin feature/your-feature-name`).
5.  Open a Pull Request to the `main` branch of the original repository.

Please make sure to update tests as appropriate.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details (if one exists, otherwise assume standard MIT terms).

---

For questions, issues, or suggestions, please open an issue on the GitHub repository.
