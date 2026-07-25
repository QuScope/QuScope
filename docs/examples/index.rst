========
Examples
========

Full runnable examples live in a separate repository,
`QuScope/examples-applications <https://github.com/QuScope/examples-applications>`_,
so they can evolve independently of the package release cycle. Clone it and
follow its own setup instructions to run any of them locally.

For a guided, conceptual walkthrough of each technique with short
API-verified snippets, see :doc:`../tutorials/index` instead — this page is
just a quick index by technique:

Quantum CTEM
===============

- Single-slice (WPOA) and multislice CTEM as one quantum circuit
- Contrast Transfer Function and envelope-function analysis
- Multislice on a real crystal structure, validated against a classical reference

Quantum STEM
===============

- HAADF / ADF / ABF / BF / iDPC scanning-probe imaging

Material Workflows
======================

- End-to-end MoS₂ and graphene workflows, from structure to image

Running the Examples
========================

.. code-block:: bash

   pip install quscope jupyter matplotlib
   git clone https://github.com/QuScope/examples-applications.git

See that repository's own README for which optional dependencies (e.g.
``ase``, ``abtem`` for real crystal structures) each example needs.

Pre-rendered Output
=======================

If you just want to see the output of the core pipeline notebooks without
running anything, :doc:`../notebooks` has pre-rendered copies kept in this
repository for reference.
