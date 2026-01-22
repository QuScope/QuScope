# 🔬 QuScope v0.1.1: Quantum Algorithms for Microscopy

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
from quscope.quantum_ctem.backends import get_backend
from quscope.quantum_ctem.materials import get_material
import numpy as np

# Get a quantum simulator backend
backend = get_backend('simulator')
print(f"QuScope v{quscope.__version__}")

# Load a material (e.g., MoS2)
material = get_material('mos2')
print(f"Loaded material: {material.name}")
```

## ✨ **Key Features**

*   **Quantum CTEM Simulation**:
    *   Full quantum circuit simulation of Conventional Transmission Electron Microscopy
    *   Amplitude encoding of electron wavefunctions into quantum states
    *   Quantum Fourier Transform (QFT) based momentum space operations
    *   Weak Phase Object Approximation (WPOA) implementation
    *   Support for multiple materials (MoS₂, Graphene)
    *   Contrast Transfer Function (CTF) with aberration modeling
*   **Quantum Backend Integration**:
    *   Unified backend abstraction for simulators and IBM Quantum hardware
    *   Seamless execution on local `AerSimulator` or IBM quantum devices
    *   Circuit optimization and transpilation for hardware deployment
    *   Performance benchmarking tools
*   **Classical-Quantum Integration**:
    *   Bridge between classical multislice simulations and quantum encoding
    *   Validation against established microscopy simulators (abTEM)
    *   Quantum tomography for wavefunction reconstruction
*   **Material-Specific Workflows**:
    *   Pre-configured workflows for MoS₂ and Graphene
    *   Automatic atomic structure generation from lattice parameters
    *   Kirkland potential calculation for electron scattering
*   **Professional Code Structure**:
    *   Modular design with clear separation of backends, materials, and workflows
    *   Comprehensive test suite (200+ tests)
    *   Type hints and detailed docstrings
    *   Continuous integration with GitHub Actions
*   **Jupyter Notebook Examples**:
    *   Interactive quantum CTEM demonstration (`examples/quantum_ctem.ipynb`)
    *   Complete visualization and analysis tools
    *   Reproducible scientific workflows

## Repository Structure

```
quantum_algo_microscopy/
├── examples/                       # Example scripts and notebooks
│   ├── quantum_ctem.ipynb         # Quantum CTEM demonstration notebook
│   └── quantum_ctem_demonstration.py  # Quantum CTEM Python script
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
│       ├── qml/                    # Quantum Machine Learning modules
│       │   ├── __init__.py
│       │   └── image_encoding.py   # (Integrates PiQture/INEQR)
│       └── quantum_ctem/           # Quantum CTEM simulation modules
│           ├── __init__.py
│           ├── hamiltonian.py
│           ├── quantum_simulation.py
│           └── microscope.py
├── README.md                       # This file
├── requirements.txt                # Project dependencies
├── pyproject.toml                  # Modern Python project configuration
└── docs/                           # Sphinx documentation
```

## Installation

### Prerequisites

*   Python 3.8 or higher
*   Qiskit (core, aer, ibm-provider) - see `requirements.txt` for specific versions.
*   NumPy, SciPy, Matplotlib, Pillow, Pandas, Scikit-image, PiQture, etc. (see `requirements.txt`)

### Setup

1.  **Install from PyPI (recommended):**
    ```bash
    pip install quscope
    ```

2.  **Or clone the repository for development:**
    ```bash
    git clone https://github.com/QuScope/QuScope.git
    cd QuScope
    ```

3.  **Create and activate a virtual environment (for development):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

4.  **Install in editable mode (for development):**
    ```bash
    pip install -e ".[all]"  # Install with all optional dependencies
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

### 7. Quantum CTEM (Conventional Transmission Electron Microscopy) Simulation

```python
from qiskit import QuantumCircuit, transpile
from qiskit_aer import Aer
import numpy as np

# Create a synthetic microscopy image
image_size = 64  # 64x64 image
synthetic_image = np.random.randint(0, 256, (image_size, image_size), dtype=np.uint8)

# Process pixels through quantum circuits
def quantum_process_pixels(pixel_chunk):
    """Process pixels using quantum circuits for CTEM simulation"""
    processed_pixels = []
    
    for pixel_value in pixel_chunk:
        # Create quantum circuit with 8 qubits (for 8-bit pixel values)
        qc = QuantumCircuit(8, 8)
        
        # Encode pixel value in quantum state
        binary_pixel = format(pixel_value, '08b')
        for i, bit in enumerate(binary_pixel):
            if bit == '1':
                qc.x(i)
        
        # Apply quantum operations for CTEM-inspired transformations
        for i in range(8):
            qc.rz(np.pi/8, i)  # Phase shifts (electron-specimen interaction)
        
        # Simulate propagation effects
        qc.h(0)  # Superposition for interference
        qc.cx(0, 1)  # Entanglement for correlation
        qc.measure_all()
        
        # Execute circuit
        simulator = Aer.get_backend('qasm_simulator')
        job = simulator.run(transpile(qc, simulator), shots=100)
        result = job.result()
        counts = result.get_counts(qc)
        
        # Extract most probable measurement
        most_probable = max(counts, key=counts.get)
        processed_value = int(most_probable.replace(' ', ''), 2)
        processed_pixels.append(processed_value)
    
    return np.array(processed_pixels)

# Process the image and visualize results
processed_image = quantum_process_pixels(synthetic_image.flatten())
processed_image = processed_image.reshape(image_size, image_size)
```

For a complete quantum CTEM demonstration with visualizations and analysis, see the notebook: `examples/quantum_ctem.ipynb`.

For more detailed examples, including data generation, visualization, and advanced usage, please see the Jupyter Notebooks:
- `examples/quantum_ctem.ipynb` - Quantum CTEM demonstration
- `notebooks/complete_quantum_microscopy_examples.ipynb` - Comprehensive examples

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
