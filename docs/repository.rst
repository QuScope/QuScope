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
     - The released v0.2.0 package: four validated pipelines (CTEM WPOA,
       CTEM multislice, STEM WPOA, STEM multislice). This site is built from
       ``main``. No top-level ``notebooks/`` directory — only
       ``docs/notebooks/`` (pre-rendered, needed for this documentation
       build).
     - Installing and using QuScope, reporting bugs, contributing fixes to
       the released pipelines.
   * - ``dev``
     - Everything on ``main``, plus work in progress: quantum diffraction
       modes (SAED, CBED, nano-beam diffraction, Kikuchi, EBSD), the
       Bloch-wave QPE eigensolver, frozen-phonon / thermal-diffuse-scattering
       modules, and the full notebook set (including the runnable sources
       and a few additional work-in-progress notebooks).
     - Working on the next release, or trying features that haven't shipped
       yet.
   * - ``v0.2.x``
     - The v0.2.0 release line. Kept in sync with ``dev``'s content.
     - Release-management purposes; most contributors want ``main`` or
       ``dev`` instead.

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
