Notebook Gallery
================

This page indexes pre-rendered output copies of QuScope's core pipeline
notebooks, kept in this repository so their results are visible without
running anything. For the full, runnable example set (and anything not
listed here), see `QuScope/examples-applications
<https://github.com/QuScope/examples-applications>`_.

Getting Started
----------------

:doc:`notebooks/01_getting_started`
   Install check, backend basics (:func:`~quscope.quantum_ctem.get_backend`),
   loading built-in materials (MoS₂, graphene), and a first quantum amplitude
   encoding of a small wavefunction.

:doc:`notebooks/03_material_workflows`
   End-to-end :class:`~quscope.quantum_ctem.MoS2Workflow` and
   :class:`~quscope.quantum_ctem.GrapheneWorkflow` runs — structure
   visualization, simulation configuration, and CTEM image formation for two
   real 2D materials.

:doc:`notebooks/02_quantum_ctem_advanced`
   Wavefunction encoding, QFT to momentum space, WPOA, and CTF modeling
   walked through step by step on a real abTEM-built graphene structure,
   using :class:`~quscope.quantum_ctem.QuantumWaveFunction` directly.

Fully Quantum CTEM
-------------------

:doc:`notebooks/10_quantum_ctem`
   The core CTEM pipeline: a single quantum circuit (state prep → QFT →
   phase-grating/lens diagonal gates → IQFT) implementing both single-slice
   WPOA and multislice CTEM, compared side by side.

:doc:`notebooks/06_quantum_ctf_envelope`
   Deep dive on the Contrast Transfer Function — spatial/temporal coherence
   envelopes, multi-voltage comparisons, aperture effects, and resolution
   metrics, with publication-quality figure export.

:doc:`notebooks/07_si3n4_quantum_multislice`
   A realistic multislice simulation of hexagonal Si₃N₄ built from an ASE
   structure via abTEM, validated against a classical multislice reference,
   including an optional IBM Quantum hardware deployment section.

Quantum STEM
------------

:doc:`notebooks/11_quantum_stem`
   Scanning-probe imaging — one quantum circuit per probe position, HAADF /
   ADF / ABF / BF / iDPC detector channels, and the qubit-vs-field-of-view
   tradeoff for matching CTEM's field of view.

.. note::
   Quantum diffraction modes, frozen-phonon/thermal-diffuse-scattering
   channels, and the Bloch-wave QPE eigensolver are under development on the
   ``dev`` branch and not yet part of a release.

Executed Reference Copies
---------------------------

A couple of notebooks are long-running (multislice on a real crystal
structure, IBM hardware calls) and are also kept with outputs pre-executed so
readers can see results without re-running them:
:doc:`notebooks/02_quantum_ctem_advanced.executed`,
:doc:`notebooks/05_fully_quantum_ctem.executed`.

.. toctree::
   :hidden:
   :maxdepth: 1

   notebooks/01_getting_started
   notebooks/02_quantum_ctem_advanced
   notebooks/02_quantum_ctem_advanced.executed
   notebooks/03_material_workflows
   notebooks/05_fully_quantum_ctem.executed
   notebooks/06_quantum_ctf_envelope
   notebooks/07_si3n4_quantum_multislice
   notebooks/10_quantum_ctem
   notebooks/11_quantum_stem
