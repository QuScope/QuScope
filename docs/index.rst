.. QuScope documentation master file

============================
QuScope v0.2.0 Documentation
============================

**QuScope** is a Python package for applying quantum computing algorithms to
Transmission Electron Microscopy (TEM) simulation. Built on Qiskit, it
provides fully-quantum circuit implementations of every stage of the TEM
imaging pipeline — from specimen interaction to detector readout — validated
against classical reference implementations with fidelity ≥ 0.9999.

🔬 **Key Features**
===================

- **Quantum CTEM**: Single-slice (WPOA) and multislice conventional TEM image simulation as one quantum circuit (state prep -> QFT -> diagonal-gate phase grating/lens CTF -> IQFT)
- **Quantum STEM**: Per-probe-position quantum circuits with HAADF / ADF / ABF / BF / iDPC detector channels
- **Quantum Diffraction**: WPOA, SAED, CBED, nano-beam diffraction (nBD), Kikuchi, and EBSD patterns
- **Dynamical Scattering**: Bloch-wave formalism with eigenvalues extracted via Quantum Phase Estimation
- **Thermal Diffuse Scattering**: Quantum frozen-phonon modules (QTPC, QPS, Lindblad channel) for Debye-Waller-parameterized thermal effects
- **Backend Management**: Local Qiskit Aer simulators and real IBM Quantum hardware via Qiskit Runtime
- **Ready-to-Use Notebooks**: A full notebook gallery demonstrating every module above on real materials (MoS₂, graphene, Si₃N₄)

🚀 **Quick Start**
==================

Install QuScope via pip:

.. code-block:: bash

   pip install quscope

Basic usage — simulate a quantum CTEM image and validate it against a classical reference:

.. code-block:: python

   from quscope.quantum_ctem import (
       QuantumCTEMCircuit,
       QuantumCTEMParameters,
       QuantumClassicalValidator,
   )
   import numpy as np

   # 8x8 grid (6 qubits), 200 kV, Scherzer condition
   params = QuantumCTEMParameters(
       acceleration_voltage=200e3,
       grid_size=8,
       pixel_size=0.5,       # Angstrom/pixel
       defocus=-659.7,       # Angstrom (Scherzer defocus)
       cs=1.3,               # mm
   )
   sim = QuantumCTEMCircuit(params)

   # Simulate a random projected potential
   V = np.random.rand(8, 8) * 100          # projected potential in V*Angstrom

   result = sim.simulate(V)
   print("Wave function shape:", result["wave_function"].shape)   # (8, 8)
   print("Intensity range   :", result["intensity"].min(), "-", result["intensity"].max())

   # Validate against classical implementation
   validator = QuantumClassicalValidator(params)
   comparison = validator.compare(V)
   print(f"Quantum-classical fidelity: {comparison['fidelity']:.6f}")   # -> 1.000000

See the :doc:`notebooks` for the full set of runnable demonstrations (CTEM,
STEM, diffraction, Bloch wave, and frozen phonons).

📚 **Documentation Structure**
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

🔗 **Links**
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
