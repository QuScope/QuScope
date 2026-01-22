Notebook Examples
=================

This section includes examples from the Jupyter notebooks demonstrating quantum algorithms for microscopy applications.

Example Notebooks
-----------------

Quantum CTEM Demonstration
~~~~~~~~~~~~~~~~~~~~~~~~~~

The **Quantum CTEM** (Conventional Transmission Electron Microscopy) notebook demonstrates quantum circuit-based image processing for electron microscopy simulation:

* Quantum encoding of pixel values (8-bit) into quantum states
* Phase shift operations simulating electron-specimen interactions
* Quantum gate applications for propagation effects and lens aberrations
* Measurement and reconstruction of processed images
* Fourier space analysis and visualization

**Location**: ``examples/quantum_ctem.ipynb``

Complete Quantum Microscopy Examples
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Comprehensive examples showcasing all major functionalities of QuScope:

* IBM Quantum backend integration
* Multiple image encoding methods
* Quantum image segmentation with Grover's algorithm
* Quantum EELS analysis
* Performance benchmarking

**Location**: ``notebooks/complete_quantum_microscopy_examples.ipynb``

.. toctree::
   :maxdepth: 2
   :glob:

   ../examples/*.ipynb
   ../notebooks/*.ipynb
