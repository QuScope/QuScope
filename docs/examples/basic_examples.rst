Basic Examples
==============

This section contains introductory examples for getting started with QuScope.

Image Preprocessing
-------------------

Learn how to preprocess microscopy images for quantum analysis:

.. code-block:: python

   from quscope.image_processing.preprocessing import binarize_image, normalize_image
   import numpy as np
   
   # Create sample image data
   image_data = np.random.rand(8, 8)
   
   # Normalize the image
   normalized_image = normalize_image(image_data)
   print(f"Normalized range: [{normalized_image.min():.3f}, {normalized_image.max():.3f}]")
   
   # Binarize the image
   binary_image = binarize_image(image_data, threshold=0.5)
   print(f"Binary image shape: {binary_image.shape}")
   print(f"Unique values: {np.unique(binary_image)}")

Quantum Image Encoding
-----------------------

Basic quantum encoding of image data:

.. code-block:: python

   from quscope.image_processing.quantum_encoding import encode_image_to_circuit, EncodingMethod
   import numpy as np
   
   # Create sample image
   image_data = np.random.rand(4, 4)
   
   # Encode using amplitude encoding
   circuit = encode_image_to_circuit(image_data, method=EncodingMethod.AMPLITUDE)
   print(f"Quantum circuit: {circuit.num_qubits} qubits")
   print(f"Circuit depth: {circuit.depth()}")
   
   # Try different encoding methods
   circuit_frqi = encode_image_to_circuit(image_data, method=EncodingMethod.FRQI)
   print(f"FRQI encoding: {circuit_frqi.num_qubits} qubits, depth {circuit_frqi.depth()}")

Backend Management
------------------

Working with quantum backends:

.. code-block:: python

   from quscope.quantum_backend import QuantumBackendManager
   
   # Initialize backend manager (uses IBMQ_TOKEN env var if set)
   backend_manager = QuantumBackendManager()
   
   # Get available backends
   backends = backend_manager.get_available_backends()
   print(f"Available backends: {backends}")
   
   # Select a simulator
   backend_manager.select_backend('aer_simulator')
   print(f"Selected backend: {backend_manager.backend}")
