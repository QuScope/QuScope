===========
Quick Start
===========

This guide will get you up and running with QuScope in just a few minutes.

🎯 **Basic Quantum Image Encoding**
===================================

Let's start with a simple example of encoding an image into a quantum circuit:

.. code-block:: python

   import numpy as np
   from quscope.image_processing.quantum_encoding import encode_image_to_circuit, EncodingMethod
   
   # Create a simple 4x4 test image
   test_image = np.array([
       [0.8, 0.6, 0.4, 0.2],
       [0.7, 0.9, 0.3, 0.1], 
       [0.5, 0.8, 0.6, 0.4],
       [0.3, 0.2, 0.7, 0.9]
   ])
   
   # Encode the image using amplitude encoding
   circuit = encode_image_to_circuit(test_image, method=EncodingMethod.AMPLITUDE)
   
   print(f"Circuit has {circuit.num_qubits} qubits")
   print(f"Circuit depth: {circuit.depth()}")

🔧 **Quantum Backend Setup**
============================

Set up a quantum backend for circuit execution:

.. code-block:: python

   from quscope.quantum_backend import QuantumBackendManager
   from qiskit_aer import AerSimulator
   
   # Initialize backend manager
   backend_manager = QuantumBackendManager()
   
   # Use local simulator
   simulator = AerSimulator()
   result = backend_manager.execute_circuit(circuit, simulator, shots=1024)
   
   print("Measurement results:", result.get_counts())

**Quantum Machine Learning Example**
=======================================

Use QuScope for quantum machine learning on image data:

.. code-block:: python

   from quscope.qml.image_encoding import QuantumImageEncoder
   
   # Create encoder
   encoder = QuantumImageEncoder(encoding_method=EncodingMethod.ANGLE)
   
   # Encode multiple image patches
   image_patches = [test_image, test_image * 0.5, test_image * 1.5]
   
   encoded_circuits = []
   for patch in image_patches:
       circuit = encoder.encode(patch)
       encoded_circuits.append(circuit)
   
   print(f"Encoded {len(encoded_circuits)} image patches")

**EELS Analysis Example**
============================

Process electron energy loss spectroscopy data:

.. code-block:: python

   from quscope.eels_analysis.quantum_processing import quantum_eels_filter
   from quscope.eels_analysis.preprocessing import normalize_spectrum
   
   # Simulate EELS spectrum data
   energy_range = np.linspace(0, 1000, 256)  # eV
   spectrum = np.exp(-energy_range/100) + 0.1*np.random.normal(size=256)
   
   # Preprocess the spectrum
   normalized_spectrum = normalize_spectrum(spectrum)
   
   # Apply quantum filtering (this would create a quantum circuit for processing)
   filtered_circuit = quantum_eels_filter(normalized_spectrum)
   
   print(f"EELS quantum filter circuit depth: {filtered_circuit.depth()}")

📈 **Visualization and Analysis**
=================================

QuScope includes tools for visualizing quantum circuits and results:

.. code-block:: python

   import matplotlib.pyplot as plt
   from quscope.image_processing.preprocessing import normalize_image
   
   # Visualize original and processed images
   fig, axes = plt.subplots(1, 2, figsize=(10, 4))
   
   # Original image
   axes[0].imshow(test_image, cmap='gray')
   axes[0].set_title('Original Image')
   axes[0].axis('off')
   
   # Normalized image
   normalized = normalize_image(test_image)
   axes[1].imshow(normalized, cmap='gray') 
   axes[1].set_title('Normalized Image')
   axes[1].axis('off')
   
   plt.tight_layout()
   plt.show()

**Next Steps**
=================

- Explore the :doc:`tutorials/index` for detailed guides
- Check out the :doc:`notebooks` for interactive examples
- Read the :doc:`api` reference for complete documentation
- Visit our `GitHub repository <https://github.com/robertoreis/quantum_algo_microscopy>`_ for the latest updates

🆘 **Need Help?**
=================

- Check the :doc:`api` for detailed function documentation
- Browse the example notebooks in :doc:`notebooks`
- Open an issue on `GitHub <https://github.com/robertoreis/quantum_algo_microscopy/issues>`_
