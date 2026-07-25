=========
Tutorials
=========

Full runnable walkthroughs live as Jupyter notebooks in
`QuScope/examples-applications <https://github.com/QuScope/examples-applications>`_.
This page is a guided path through the concepts, with short API-verified code
snippets for each stage — for the complete worked examples, follow the links
into that repository.

1. Start Here
================

- **Backends and materials** — ``get_backend``, ``get_material``, and
  QuScope's built-in MoS₂/graphene structures. See the *Material Workflows*
  section of :doc:`../quickstart`.
- **Material workflows end to end** — ``MoS2Workflow`` and
  ``GrapheneWorkflow`` take a structure from build to CTEM image in one
  ``.run()`` call. See :doc:`../quickstart` and
  :doc:`../api/quscope.quantum_ctem`.

2. Core Quantum CTEM
========================

- **The CTEM pipeline** — a single quantum circuit (state prep → QFT →
  phase-grating/lens diagonal gates → IQFT) implementing both single-slice
  WPOA and multislice CTEM. See *Quantum CTEM in Five Lines* in
  :doc:`../quickstart` and :class:`~quscope.quantum_ctem.QuantumCTEMCircuit`.
- **Contrast Transfer Function** — spatial/temporal coherence envelopes,
  multi-voltage comparisons, and aperture effects. See
  :class:`~quscope.quantum_ctem.CTFCalculator`.
- **Multislice on a real crystal structure** — building a specimen from an
  ASE structure via abTEM and validating the quantum multislice circuit
  against a classical reference. See
  :class:`~quscope.quantum_ctem.QuantumMultisliceCircuit`.

3. Quantum STEM
==================

- **Scanning-probe imaging** — one quantum circuit per probe position, with
  HAADF / ADF / ABF / BF / iDPC detector channels. See *Beyond CTEM: Quantum
  STEM* in :doc:`../quickstart` and :func:`~quscope.quantum_ctem.run_stem`.

Prerequisites
================

Before working through these, you should have:

- Basic understanding of Python and NumPy
- Basic knowledge of TEM/STEM imaging concepts (helpful but not required —
  each pipeline is explained as it's introduced)
- QuScope installed (see :doc:`../installation`)

Additional Resources
========================

- `QuScope/examples-applications <https://github.com/QuScope/examples-applications>`_ — full runnable notebooks
- :doc:`../repository` — how the codebase and branches are organized
- :doc:`../notebooks` — pre-rendered output copies of the pipeline notebooks
- :doc:`../api` — complete API reference
- `Qiskit documentation <https://docs.quantum.ibm.com/api/qiskit/>`_ — for the underlying quantum circuit primitives
