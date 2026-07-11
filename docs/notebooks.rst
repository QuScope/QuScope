Notebook Gallery
================

QuScope's documentation is built around runnable Jupyter notebooks rather than
hand-written prose — each notebook below imports the real ``quscope.quantum_ctem``
API and produces the figures shown. Start at the top and work down, or jump
straight to the technique you need.

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

:doc:`notebooks/09_quantum_multislice_circuit_test`
   Focused unit-style walkthrough of
   :class:`~quscope.quantum_ctem.QuantumMultisliceCircuit` — circuit
   architecture, gate counts, and a fidelity/RMSE convergence study vs.
   number of slices.

Quantum STEM, Diffraction, and Dynamical Scattering
-----------------------------------------------------

:doc:`notebooks/11_quantum_stem`
   Scanning-probe imaging — one quantum circuit per probe position, HAADF /
   ADF / ABF / BF / iDPC detector channels, frozen-phonon averaging, and the
   qubit-vs-field-of-view tradeoff for matching CTEM's field of view.

:doc:`notebooks/12_quantum_diffraction`
   WPOA, SAED, CBED, and nano-beam diffraction (nBD) patterns, including the
   quantum-multislice nBD variant.

:doc:`notebooks/13_bloch_wave_and_frozen_phonon`
   Dynamical (multiple-scattering) diffraction via the Bloch-wave formalism
   (Bethe eigenvalues through Quantum Phase Estimation), plus thermal diffuse
   scattering — Kikuchi lines and EBSD — from the quantum frozen-phonon
   modules.

:doc:`notebooks/08_fully_quantum_tem_advanced`
   A single-notebook tour across all of the advanced modules above (frozen
   phonon, Bloch wave, diffraction, STEM) on one MoS₂ specimen — useful as a
   quick reference for how the modules compose together.

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
   notebooks/03_material_workflows
   notebooks/10_quantum_ctem
   notebooks/06_quantum_ctf_envelope
   notebooks/07_si3n4_quantum_multislice
   notebooks/09_quantum_multislice_circuit_test
   notebooks/11_quantum_stem
   notebooks/12_quantum_diffraction
   notebooks/13_bloch_wave_and_frozen_phonon
   notebooks/08_fully_quantum_tem_advanced
   notebooks/02_quantum_ctem_advanced.executed
   notebooks/05_fully_quantum_ctem.executed
