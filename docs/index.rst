.. QuScope documentation master file

============================
QuScope v0.2.0 Documentation
============================

**QuScope** is a Python package for applying quantum computing algorithms to
Transmission Electron Microscopy (TEM) simulation. Built on Qiskit, it
expresses the TEM image-formation pipeline as quantum circuits — the electron
wavefunction is amplitude-encoded on qubits, and every optical element (phase
grating, Fresnel propagation, objective lens) is a diagonal unitary conjugated
by quantum Fourier transforms — validated against classical reference
implementations to unit fidelity.

v0.2.0 provides four fully-quantum imaging pipelines: CTEM (WPOA), CTEM
multislice, STEM (WPOA), and STEM multislice. New to the project? Start with
:doc:`quickstart`, or see :doc:`repository` for a map of the branches, related
repositories, and package layout.

Documentation Structure
========================

.. toctree::
   :maxdepth: 2
   :caption: User Guide:

   installation
   quickstart
   tutorials/index
   examples/index

.. toctree::
   :maxdepth: 1
   :caption: Project:

   repository

.. toctree::
   :maxdepth: 2
   :caption: API Reference:

   api
   notebooks

.. toctree::
   :maxdepth: 1
   :caption: Development:

   contributing
   changelog
   license

Links
=====

- **Repository**: https://github.com/QuScope/QuScope
- **Examples & applications**: https://github.com/QuScope/examples-applications
- **Issues**: https://github.com/QuScope/QuScope/issues
- **PyPI**: https://pypi.org/project/quscope/

Indices and Tables
===================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. include:: ../README.md
   :parser: myst_parser.sphinx_
