Integration Examples
====================

This section shows how to integrate QuScope with other tools and frameworks.

Integration with Matplotlib
----------------------------

Visualizing quantum circuits and results:

.. code-block:: python

   import quscope
   import numpy as np
   import matplotlib.pyplot as plt
   
   # Create and encode image
   image_data = np.random.rand(8, 8)
   encoder = quscope.QuantumImageEncoder(image_size=(8, 8))
   circuit = encoder.encode_amplitude_encoding(image_data)
   
   # Visualize original image
   plt.figure(figsize=(12, 4))
   plt.subplot(1, 2, 1)
   plt.imshow(image_data, cmap='viridis')
   plt.title('Original Image')
   plt.colorbar()
   
   # Print circuit information
   plt.subplot(1, 2, 2)
   plt.text(0.1, 0.5, f'Quantum Circuit:\\n{circuit.num_qubits} qubits\\n{circuit.size()} gates')
   plt.axis('off')
   plt.show()

Integration with Jupyter Notebooks
-----------------------------------

Using QuScope in interactive Jupyter environments:

.. code-block:: python

   # Install in Jupyter
   # !pip install quscope[viz]
   
   import quscope
   import numpy as np
   from IPython.display import display, HTML
   
   # Interactive workflow
   def interactive_analysis(image_size=(4, 4)):
       # Generate sample data
       image_data = np.random.rand(*image_size)
       
       # Process with QuScope
       encoder = quscope.QuantumImageEncoder(image_size=image_size)
       circuit = encoder.encode_amplitude_encoding(image_data)
       
       # Display results
       print(f"Image size: {image_size}")
       print(f"⚛️  Quantum circuit: {circuit.num_qubits} qubits")
       print(f"🔧 Gates: {circuit.size()}")
       
       return circuit
   
   # Run interactive analysis
   result = interactive_analysis()

Integration with NumPy and SciPy
---------------------------------

Leveraging scientific Python ecosystem:

.. code-block:: python

   import quscope
   import numpy as np
   from scipy import ndimage
   from scipy.fft import fft2
   
   # Complex image processing workflow
   def quantum_enhanced_analysis(image_data):
       # Classical preprocessing with SciPy
       filtered_image = ndimage.gaussian_filter(image_data, sigma=1.0)
       
       # Fourier analysis
       fft_image = fft2(filtered_image)
       magnitude = np.abs(fft_image)
       
       # Quantum encoding
       encoder = quscope.QuantumImageEncoder(image_size=filtered_image.shape)
       circuit = encoder.encode_amplitude_encoding(filtered_image)
       
       return {
           'filtered': filtered_image,
           'fft_magnitude': magnitude,
           'quantum_circuit': circuit
       }
   
   # Example usage
   image_data = np.random.rand(8, 8)
   results = quantum_enhanced_analysis(image_data)
