Basic Examples
==============

This section contains introductory examples for getting started with QuScope.

Image Preprocessing
-------------------

Learn how to preprocess microscopy images for quantum analysis:

.. code-block:: python

   import quscope
   import numpy as np
   
   # Create sample image data
   image_data = np.random.rand(8, 8)
   
   # Binarize the image
   binary_image = quscope.binarize_image(image_data, threshold=0.5)
   print(f"Binary image shape: {binary_image.shape}")

Quantum Image Encoding
-----------------------

Basic quantum encoding of image data:

.. code-block:: python

   import quscope
   import numpy as np
   
   # Create sample image
   image_data = np.random.rand(4, 4)
   
   # Create quantum encoder
   encoder = quscope.QuantumImageEncoder(image_size=(4, 4))
   
   # Encode using amplitude encoding
   circuit = encoder.encode_amplitude_encoding(image_data)
   print(f"Quantum circuit: {circuit.num_qubits} qubits")

Backend Management
------------------

Working with quantum backends:

.. code-block:: python

   import quscope
   
   # Initialize backend manager
   backend_manager = quscope.QuantumBackendManager()
   
   # Get available backends
   backends = backend_manager.get_available_backends()
   print(f"Available backends: {backends}")
