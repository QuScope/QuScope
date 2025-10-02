.. QuScope documentation master file

============================
QuScope v0.1.0 Documentation
============================

**QuScope** (Quantum Algorithm Microscopy) is a comprehensive Python package for applying quantum computing algorithms to electron microscopy data processing and analysis.

**Key Features**
===================

- **Quantum Image Processing**: Encode and process microscopy images using quantum circuits
- **EELS Analysis**: Quantum algorithms for Electron Energy Loss Spectroscopy data
- **Electron Diffraction Analysis**: Quantum algorithms for Electron Diffraction analysis
- **Quantum Machine Learning**: ML algorithms optimized for microscopy applications  
- **Backend Management**: Seamless integration with quantum simulators and hardware
- **Ready-to-Use Examples**: Comprehensive Jupyter notebooks and tutorials

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
