=========
Tutorials
=========

QuScope doesn't maintain separate hand-written tutorial pages — the notebooks
themselves *are* the tutorials, kept in sync with the code because they
import and run the real ``quscope.quantum_ctem`` API. This page is a short
guided path through them; the full gallery (with every notebook) lives at
:doc:`../notebooks`.

🎯 **1. Start Here**
=====================

- :doc:`../notebooks/01_getting_started` — install check, backends, materials, and a first quantum amplitude encoding
- :doc:`../notebooks/03_material_workflows` — full MoS₂/graphene workflows from structure to CTEM image

🚀 **2. Core Quantum CTEM**
=============================

- :doc:`../notebooks/10_quantum_ctem` — the single-circuit WPOA/multislice CTEM pipeline
- :doc:`../notebooks/06_quantum_ctf_envelope` — Contrast Transfer Function and envelope functions in depth
- :doc:`../notebooks/07_si3n4_quantum_multislice` — multislice on a real crystal structure, validated classically

🌀 **3. STEM, Diffraction, and Dynamical Scattering**
========================================================

- :doc:`../notebooks/11_quantum_stem` — scanning-probe imaging with multi-detector channels
- :doc:`../notebooks/12_quantum_diffraction` — WPOA, SAED, CBED, and nano-beam diffraction
- :doc:`../notebooks/13_bloch_wave_and_frozen_phonon` — dynamical diffraction (Bloch wave / QPE) and thermal diffuse scattering

📚 **Prerequisites**
=====================

Before starting these notebooks, you should have:

- Basic understanding of Python and NumPy
- Basic knowledge of TEM/STEM imaging concepts (helpful but not required — each notebook explains the physics it uses)
- QuScope installed (see :doc:`../installation`), plus ``jupyter`` to run the notebooks locally

🔗 **Additional Resources**
=============================

- :doc:`../notebooks` — the full notebook gallery, including advanced and reference-copy notebooks
- :doc:`../api` — complete API reference
- `Qiskit documentation <https://docs.quantum.ibm.com/api/qiskit/>`_ — for the underlying quantum circuit primitives
