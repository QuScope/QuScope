===========
Quick Start
===========

This guide gets you running QuScope's fully-quantum TEM pipeline in a few
minutes. For deeper, runnable walkthroughs of every technique below, see the
:doc:`notebooks`.

🎯 **Quantum CTEM in Five Lines**
==================================

.. code-block:: python

   import numpy as np
   from quscope.quantum_ctem import QuantumCTEMParameters, QuantumCTEMCircuit

   params = QuantumCTEMParameters(
       acceleration_voltage=200e3,   # 200 kV
       grid_size=8,                  # 8x8 grid -> 6 qubits
       pixel_size=0.5,               # Angstrom/pixel
       defocus=-659.7,               # Scherzer defocus at 200 kV, Cs=1.3 mm
       cs=1.3,                       # mm
   )
   sim = QuantumCTEMCircuit(params)

   V = np.random.rand(8, 8) * 100    # toy projected potential (V*Angstrom)
   result = sim.simulate(V)

   print("qubits:", result["circuit_info"]["n_qubits"] if "circuit_info" in result else sim.qc.num_qubits)
   print("intensity range:", result["intensity"].min(), "-", result["intensity"].max())

Every quantity here — grid size, voltage, defocus, Cs — maps directly onto
real microscope parameters, and the same ``simulate()`` call works whether
``sim`` is backed by a statevector simulator or (via ``qiskit-ibm-runtime``)
real IBM Quantum hardware.

🔧 **Validating Against a Classical Reference**
=================================================

Every quantum module in QuScope ships with a classical validator so you can
check fidelity before trusting a quantum-hardware run:

.. code-block:: python

   from quscope.quantum_ctem import QuantumClassicalValidator

   validator = QuantumClassicalValidator(params)
   comparison = validator.compare(V)
   print(f"fidelity: {comparison['fidelity']:.6f}")   # -> 1.000000 for statevector sim

🧬 **Material Workflows**
==========================

QuScope ships built-in structures for MoS₂ and graphene, plus a backend
abstraction so the same workflow runs on a simulator or IBM hardware:

.. code-block:: python

   from quscope.quantum_ctem import get_backend, get_material, MoS2Workflow

   backend = get_backend("simulator")
   mos2 = get_material("mos2")

   workflow = MoS2Workflow(backend=backend)
   result = workflow.run_simulation({
       "grid_size": 64,
       "pixel_size": 0.1,
       "voltage": 200e3,
       "defocus": -659.7,
       "Cs": 1.3e-3,
       "supercell": (3, 3, 1),
   })
   print("circuit qubits:", result["circuit_info"]["n_qubits"])

🌀 **Beyond CTEM: Quantum STEM**
==================================

.. code-block:: python

   from quscope.quantum_ctem import run_stem, run_stem_multislice, STEMDetectors

   # Quantum STEM with HAADF/ADF/ABF/BF/iDPC detectors (single-slice WPOA)
   stem_result = run_stem(V, pixel_size=0.5, voltage=200e3, detectors=STEMDetectors())

   # Full multislice STEM (thick specimens)
   stem_ms = run_stem_multislice(V, pixel_size=0.5, voltage=200e3,
                                 n_slices=4, slice_thickness=6.5)

Quantum diffraction modes, frozen-phonon/thermal-diffuse scattering, and the
Bloch-wave QPE eigensolver are under development on the ``dev`` branch and
planned for a future release.

🚀 **Next Steps**
=================

- Work through :doc:`notebooks/01_getting_started` for backends, materials, and basic encoding
- Browse the full :doc:`notebooks` gallery for CTEM, STEM, diffraction, and Bloch-wave demonstrations
- Read the :doc:`api` reference for complete class and function documentation
- Visit the `GitHub repository <https://github.com/QuScope/QuScope>`_ for the latest updates

🆘 **Need Help?**
=================

- Check the :doc:`api` for detailed function documentation
- Browse the notebook gallery in :doc:`notebooks`
- Open an issue on `GitHub <https://github.com/QuScope/QuScope/issues>`_
