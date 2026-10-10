============
Installation
============

QuScope can be installed via pip from PyPI or directly from the source code.

From PyPI (Recommended)
===========================

.. code-block:: bash

   pip install quscope

This will install QuScope and all required dependencies.

Development Installation
============================

For development or to get the latest features:

.. code-block:: bash

   git clone https://github.com/QuScope/QuScope.git
   cd QuScope
   pip install -e ".[dev,docs]"

Requirements
===============

**Python Version**

- Python >= 3.9

**Core Dependencies**

- qiskit >= 2.0.0
- qiskit-aer >= 0.14.0
- qiskit-algorithms >= 0.3.0
- qiskit-machine-learning >= 0.7.0
- numpy >= 1.24.0
- scipy >= 1.10.0
- pillow >= 9.0.0
- scikit-learn >= 1.3.0

**Optional Dependencies**

- matplotlib (for the visualization used throughout the examples)
- jupyter (to run notebooks locally — see `QuScope/examples-applications
  <https://github.com/QuScope/examples-applications>`_)
- ase, abtem (for building real crystal structures)
- qiskit-ibm-runtime, python-dotenv (only needed for the optional IBM Quantum
  hardware sections)

Verify Installation
=======================

Test your installation:

.. code-block:: python

   import quscope
   print(f"QuScope version: {quscope.__version__}")

   # Test basic functionality
   from quscope.quantum_ctem import QuantumCTEMParameters, QuantumCTEMCircuit

   params = QuantumCTEMParameters(acceleration_voltage=200e3, grid_size=8, pixel_size=0.5)
   circuit = QuantumCTEMCircuit(params)
   print("QuScope installed successfully!")

Troubleshooting
==================

**Common Issues:**

1. **Qiskit Installation Problems**

   If you encounter issues with Qiskit:

   .. code-block:: bash

      pip install --upgrade qiskit qiskit-aer

2. **Missing System Dependencies**

   On Ubuntu/Debian:

   .. code-block:: bash

      sudo apt-get update
      sudo apt-get install python3-dev build-essential

   On macOS:

   .. code-block:: bash

      xcode-select --install

3. **Virtual Environment Issues**

   Create a fresh virtual environment:

   .. code-block:: bash

      python -m venv quscope_env
      source quscope_env/bin/activate  # On Windows: quscope_env\Scripts\activate
      pip install quscope
