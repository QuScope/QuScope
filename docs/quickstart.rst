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

**Image Denoising Example**
=============================

Use quantum-guided classical denoising on microscopy images:

.. code-block:: python

   from quscope.image_processing.image_denoising import ImageDenoiser
   import numpy as np
   
   # Create a noisy test image or load one
   # For this example, create synthetic noisy image
   clean_image = np.random.rand(64, 64)
   noisy_image = clean_image + 0.3 * np.random.randn(64, 64)
   
   # Initialize denoiser (4x4 patches = 16 qubits each)
   denoiser = ImageDenoiser(patch_size=4, threshold=0.5)
   
   # Process the image
   results = denoiser.process_image_array(noisy_image)
   
   # Results include denoised image and quantum features
   print(f"SNR Improvement: {results['snr_improvement']:.2f} dB")
   print(f"Edge Preservation: {results['edge_preservation']:.3f}")
   print(f"Mean Quantum Entropy: {results['mean_entropy']:.3f}")
   
   # Visualize results (shows original, denoised, difference, quantum features)
   denoiser.visualize_results(results)

**EELS Analysis Example**
============================

Process electron energy loss spectroscopy data with quantum feature extraction:

.. code-block:: python

   from quscope.eels_analysis.analysis import EELSAnalyzer
   from quscope.eels_analysis.preprocessing import normalize_spectrum
   import numpy as np
   
   # Simulate EELS spectrum data
   energy_range = np.linspace(0, 1000, 256)  # eV
   spectrum = np.exp(-energy_range/100) + 0.1*np.random.normal(size=256)
   
   # Create analyzer with 6-qubit quantum circuits
   analyzer = EELSAnalyzer(n_qubits=6)
   
   # Option 1: Analyze from array
   results = analyzer.comprehensive_analysis_from_array(spectrum, energy_range)
   
   # Option 2: Analyze from MSA file
   # results = analyzer.comprehensive_analysis('sample.msa')
   
   # Access results
   print(f"Detected elements: {results['elements']}")
   print(f"Quantum entropy: {results['quantum_features']['entropy']:.3f}")
   print(f"Material type: {results['material_classification']}")
   
   # Visualize results
   analyzer.visualize_results(results)

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
