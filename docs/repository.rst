==================
Repository Guide
==================

QuScope's work is split across a few branches and a companion repository.
This page explains what lives where, so you land in the right place the
first time.

Branches
========

.. list-table::
   :header-rows: 1
   :widths: 15 55 30

   * - Branch
     - What it has
     - Use it for
   * - ``main``
     - The released v0.2 package (v0.2.1 fixes included): four validated pipelines (CTEM WPOA,
       CTEM multislice, STEM WPOA, STEM multislice). This site is built from
       ``main``. No top-level ``notebooks/`` directory — only
       ``docs/notebooks/`` (pre-rendered, needed for this documentation
       build).
     - Installing and using QuScope, reporting bugs, contributing fixes to
       the released pipelines.
   * - ``v0.2.x``
     - The v0.2 maintenance line. Fixes are made here and merged into
       ``main``.
     - Release management; most contributors want ``main``.

Work towards v0.3 (CBED, and frozen-phonon / thermal-diffuse-scattering
options through the multislice stack) happens on feature branches, starting
from the experimental ``quantum_diffraction`` and ``quantum_frozen_phonon``
modules already in the source tree. The Bloch-wave eigensolver is planned for
the version after that.

Related repositories
=====================

`QuScope/examples-applications <https://github.com/QuScope/examples-applications>`_
holds runnable example notebooks and end-to-end applications built on
QuScope. If you want to *run* something rather than read API docs, start
there.

Package layout
==============

The full directory tree is in the
`README <https://github.com/QuScope/QuScope#repository-structure>`_. At the
module level:

.. list-table::
   :header-rows: 1
   :widths: 25 45 30

   * - Module
     - What it's for
     - API docs
   * - ``quscope.quantum_ctem``
     - The main module — quantum circuits for CTEM/STEM imaging, materials,
       workflows, backends.
     - :doc:`api/quscope.quantum_ctem`
   * - ``quscope.ctem``
     - Classical reference implementations (Kirkland potentials, multislice,
       WPOA) used to validate the quantum circuits.
     - :doc:`api/quscope.ctem`
   * - ``quscope.simulations``
     - Lower-level classical simulation helpers shared by ``ctem`` and
       ``quantum_ctem``.
     - :doc:`api/quscope.simulations`
   * - ``quscope.utils``
     - Physical constants and Kirkland scattering-factor tables.
     - :doc:`api/quscope.utils`

I want to...
============

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Goal
     - Where to go
   * - Run a simulation for the first time
     - :doc:`quickstart`
   * - See a full worked example
     - `QuScope/examples-applications <https://github.com/QuScope/examples-applications>`_
   * - Understand a specific pipeline in depth
     - :doc:`tutorials/index`
   * - Look up a function or class
     - :doc:`api`
   * - Report a bug or contribute a fix
     - :doc:`contributing`
   * - Work on diffraction, Bloch-wave, or frozen-phonon features
     - The ``dev`` branch (not yet released)
