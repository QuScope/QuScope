.. QuScope documentation master file

============================
QuScope v0.1.0 Documentation
============================

**QuScope** (Quantum Algorithm Microscopy) is a Python framework integrating quantum computing algorithms with electron microscopy data processing and analysis. Version 0.1.0 provides foundational quantum-classical hybrid capabilities for image processing and EELS analysis.

**Key Features (v0.1.0)**
==========================

- **Quantum Image Encoding**: Multiple encoding methods (Amplitude, Basis, Angle, FRQI) for converting images to quantum states
- **Quantum-Classical Denoising**: Hybrid approach using Grover's algorithm and quantum features to guide adaptive classical filtering (4×4 patches, 16 qubits)
- **Image Segmentation**: Grover's algorithm with customizable oracles for threshold, edge, and region-based segmentation
- **EELS Analysis Framework**: 
  - Classical preprocessing (Richardson-Lucy, Kramers-Kronig)
  - Quantum feature extraction via parameterized circuits (4-8 qubits)
  - Element identification (~20 common elements)
  - Basic property lookup from reference database
- **Backend Management**: IBM Quantum integration with simulator and hardware support
- **Documentation & Examples**: Working Jupyter notebooks, API reference, and tutorials

**Current Scope**
==================

QuScope v0.1.0 is a **foundational release** demonstrating quantum-classical integration patterns:

✅ **Implemented**: Image encoding, quantum-guided denoising, EELS framework, backend management

⚠️ **Limited**: EELS uses classical preprocessing + quantum features; element database covers ~20 elements

🔮 **Planned**: Electron diffraction, advanced QML, quantum-enhanced preprocessing, expanded databases

**Quick Start**
==================

Install QuScope via pip:

.. code-block:: bash

   pip install quscope

Basic usage:

.. code-block:: python

   import quscope
   from quscope import QuantumImageEncoder, EncodingMethod
   
   # Create a quantum image encoder
   encoder = QuantumImageEncoder()
   
   # Encode an image using amplitude encoding
   circuit = encoder.encode_image(image_array, method=EncodingMethod.AMPLITUDE)
   
   print(f"QuScope version: {quscope.__version__}")

**Documentation Structure**
==============================

.. toctree::
   :maxdepth: 2
   :caption: User Guide:
   
   installation
   quickstart
   tutorials/index
   examples/index

.. toctree::
   :maxdepth: 2
   :caption: API Reference:
   
   api

.. toctree::
   :maxdepth: 1
   :caption: Notebooks & Examples:
   
   notebooks

.. toctree::
   :maxdepth: 1
   :caption: Development:
   
   contributing
   changelog
   license

**Links**
============

- **Repository**: https://github.com/QuScope/QuScope
- **Issues**: https://github.com/QuScope/QuScope/issues
- **PyPI**: https://pypi.org/project/quscope/

📖 **Indices and Tables**
=========================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. include:: ../README.md
   :parser: myst_parser.sphinx_
