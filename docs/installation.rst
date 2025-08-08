============
Installation
============

QuScope can be installed via pip from PyPI or directly from the source code.

📦 **From PyPI (Recommended)**
==============================

.. code-block:: bash

   pip install quscope

This will install QuScope and all required dependencies.

🔧 **Development Installation**
===============================

For development or to get the latest features:

.. code-block:: bash

   git clone https://github.com/QuScope/QuScope.git
   cd quscope
   pip install -e ".[dev,docs]"

⚙️ **Requirements**
===================

**Python Version**
- Python >= 3.9

**Core Dependencies**
- qiskit >= 0.45.0
- qiskit-aer >= 0.13.0
- numpy >= 1.21.0
- pillow >= 8.0.0
- scipy >= 1.7.0

**Optional Dependencies**
- matplotlib >= 3.5.0 (for visualization)
- jupyter >= 1.0.0 (for notebook examples)
- pandas >= 1.3.0 (for data analysis)

🧪 **Verify Installation**
==========================

Test your installation:

.. code-block:: python

   import quscope
   print(f"QuScope version: {quscope.__version__}")
   
   # Test basic functionality
   from quscope import EncodingMethod
   print("✅ QuScope installed successfully!")

🐛 **Troubleshooting**
======================

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
