========
Examples
========

QuScope's examples live as runnable Jupyter notebooks in
``docs/notebooks/`` rather than as standalone scripts — each one imports the
real ``quscope.quantum_ctem`` API and reproduces the figures shown. This page
groups the notebook gallery by technique; see :doc:`../notebooks` for the
complete, ordered list.

🧪 **Quantum CTEM**
=====================

- :doc:`../notebooks/10_quantum_ctem` — single-slice (WPOA) and multislice CTEM as one quantum circuit
- :doc:`../notebooks/06_quantum_ctf_envelope` — Contrast Transfer Function and envelope-function analysis
- :doc:`../notebooks/07_si3n4_quantum_multislice` — multislice on a real Si₃N₄ crystal structure, with an optional IBM hardware section

🚀 **Quantum STEM**
=====================

- :doc:`../notebooks/11_quantum_stem` — HAADF / ADF / ABF / BF / iDPC scanning-probe imaging

🔧 **Running the Notebooks**
==============================

.. code-block:: bash

   pip install quscope jupyter matplotlib

   # optional, for the Si3N4 multislice notebook's classical reference
   pip install ase abtem

   jupyter notebook docs/notebooks/10_quantum_ctem.ipynb

📥 **Source**
==============

All notebooks are tracked in the `GitHub repository <https://github.com/QuScope/QuScope/tree/main/docs/notebooks>`_:

.. code-block:: bash

   git clone https://github.com/QuScope/QuScope.git
   cd QuScope/docs/notebooks
