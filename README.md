# 🔬 QuScope v0.1.0: Quantum Algorithms for Microscopy

[![PyPI version](https://badge.fury.io/py/quscope.svg)](https://badge.fury.io/py/quscope)
[![Documentation Status](https://readthedocs.org/projects/quscope/badge/?version=latest)](https://quscope.readthedocs.io/en/latest/?badge=latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

**QuScope** is a comprehensive Python package for applying quantum computing algorithms to electron microscopy image processing and Electron Energy Loss Spectroscopy (EELS) analysis. Built on Qiskit, QuScope provides robust quantum circuit design and execution capabilities with seamless integration to quantum simulators and real quantum hardware.

## 🚀 **Quick Start**

```bash
pip install quscope
```

```python
import quscope
from quscope import EncodingMethod, encode_image_to_circuit
import numpy as np

# Create a sample image
image = np.random.rand(4, 4)

# Encode into quantum circuit
circuit = encode_image_to_circuit(image, method=EncodingMethod.AMPLITUDE)
print(f"Encoded into {circuit.num_qubits} qubits")
```

## ✨ **Key Features**

*   **IBM Quantum Integration**:
    *   Seamless connection to IBM Quantum backends using `QuantumBackendManager`.
    *   Support for API token authentication (via environment variable `IBMQ_TOKEN` or direct input).
    *   Execution on simulators (e.g., `aer_simulator`) and real quantum hardware.
    *   Selection of least busy backends and retrieval of backend properties.
    *   Noise model integration for realistic simulations.
*   **Advanced Quantum Image Encoding**:
    *   Multiple encoding methods: Amplitude, Basis, Angle, Flexible, and FRQI (Flexible Representation of Quantum Images).
    *   Integration with PiQture for INEQR (Improved Novel Enhanced Quantum Representation) encoding.
    *   Support for grayscale and multi-channel images.
    *   Utilities for analyzing encoding resource requirements (qubits, depth, gates).
*   **Quantum Image Segmentation**:
    *   Implementation of Grover's algorithm for various segmentation tasks.
    *   Customizable oracles for:
        *   Threshold-based segmentation.
        *   Edge-based segmentation (placeholder for quantum edge detection).
        *   Region-based segmentation (e.g., quantum region growing).
        *   Pattern-based segmentation.
    *   Automatic calculation of optimal Grover iterations.
    *   Comprehensive `SegmentationResult` class for easy analysis and visualization.
*   **Quantum EELS Analysis**:
    *   Preprocessing utilities for EELS spectra (background subtraction, normalization).
    *   Quantum Fourier Transform (QFT) for frequency analysis and peak detection in EELS data.
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
quantum_algo_microscopy/
├── notebooks/                      # Jupyter notebooks with examples
│   └── complete_quantum_microscopy_examples.ipynb  # Comprehensive examples
├── src/
│   └── quscope/                    # Main package source
│       ├── __init__.py
│       ├── quantum_backend.py      # IBM Quantum backend management
│       ├── image_processing/       # Quantum image processing modules
│       │   ├── __init__.py
│       │   ├── preprocessing.py
│       │   ├── quantum_encoding.py
│       │   ├── quantum_segmentation.py
│       │   └── filtering.py        # (Placeholder for quantum filters)
│       ├── eels_analysis/          # EELS analysis modules
│       │   ├── __init__.py
│       │   ├── preprocessing.py
│       │   └── quantum_processing.py
│       └── qml/                    # Quantum Machine Learning modules
│           ├── __init__.py
│           └── image_encoding.py   # (Integrates PiQture/INEQR)
├── README.md                       # This file
├── requirements.txt                # Project dependencies
├── setup.py                        # Setup script for installation
└── docs/                           # (Sphinx documentation - to be generated)
```

## Installation

### Prerequisites

*   Python 3.8 or higher
*   Qiskit (core, aer, ibm-provider) - see `requirements.txt` for specific versions.
*   NumPy, SciPy, Matplotlib, Pillow, Pandas, Scikit-image, PiQture, etc. (see `requirements.txt`)

### Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/rmsreis/quantum_algo_microscopy.git
    cd quantum_algo_microscopy
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install the QuScope package in editable mode:**
    ```bash
    pip install -e .
    ```

5.  **Set up IBM Quantum Access (Optional, for running on IBM backends):**
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

## API Documentation

Detailed API documentation for all modules and functions can be generated using Sphinx.
(TODO: Add instructions on how to build Sphinx docs or link to hosted documentation).

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

This package is developed to support research in quantum algorithms for electron microscopy. If you are using QuScope for your research, please consider citing our work.
(TODO: Add placeholder for an associated scientific paper citation and link once available.)

```
@software{quscope_reis_2025,
  author = {Reis, Roberto},
  title = {{QuScope: Quantum Algorithms for Advanced Electron Microscopy}},
  year = {2025},
  publisher = {GitHub},
  journal = {GitHub repository},
  url = {https://github.com/rmsreis/quantum_algo_microscopy}
}
```

## Contributing

Contributions to QuScope are welcome! If you'd like to contribute, please follow these steps:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix (`git checkout -b feature/your-feature-name`).
3.  Make your changes and commit them with clear, descriptive messages.
4.  Ensure your code adheres to PEP 8 style guidelines and includes docstrings.
5.  Add or update unit tests for your changes.
6.  Push your branch to your fork (`git push origin feature/your-feature-name`).
7.  Open a Pull Request to the `main` branch of the original repository.

Please make sure to update tests as appropriate.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details (if one exists, otherwise assume standard MIT terms).

---

For questions, issues, or suggestions, please open an issue on the GitHub repository.
