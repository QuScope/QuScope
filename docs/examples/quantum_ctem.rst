==========================
Quantum CTEM Demonstration
==========================

This example demonstrates quantum circuit-based simulation of Conventional Transmission Electron Microscopy (CTEM).

Overview
========

The quantum CTEM demonstration shows how quantum circuits can be used to simulate electron-specimen interactions in transmission electron microscopy. The approach encodes pixel values as quantum states and applies quantum gates to simulate physical processes like phase shifts, propagation effects, and lens aberrations.

Key Concepts
============

Electron-Specimen Interaction
------------------------------

In conventional TEM, electrons interact with the specimen through electromagnetic potentials. This interaction can be modeled using:

* **Phase Shifts**: Simulated with rotation gates (Rz) representing electron-specimen potential interaction
* **Coherent Superposition**: Hadamard gates (H) create quantum superposition states for interference effects
* **Electron Correlation**: Controlled-NOT gates (CX) model entanglement and correlation between electron states

Quantum Circuit Design
----------------------

Each pixel is processed through an 8-qubit quantum circuit:

1. **State Preparation**: Encode 8-bit pixel value into quantum state using X gates
2. **Phase Shifts**: Apply Rz rotations to all qubits (∝ to interaction potential)
3. **Propagation**: Use Hadamard and controlled gates for coherent evolution
4. **Lens Effects**: Controlled rotations (CRY, CRZ) simulate aberrations
5. **Measurement**: Measure all qubits to collapse to classical output

Implementation
==============

The quantum CTEM workflow consists of:

Image Encoding
--------------

.. code-block:: python

    # Encode pixel value in quantum state
    binary_pixel = format(pixel_value, '08b')
    for i, bit in enumerate(binary_pixel):
        if bit == '1':
            qc.x(i)

Quantum Operations
------------------

.. code-block:: python

    # Phase shifts (electron-specimen interaction)
    for i in range(8):
        qc.rz(np.pi/8, i)
    
    # Propagation effects
    qc.h(0)  # Superposition for interference
    qc.cx(0, 1)  # Entanglement for correlation
    qc.cx(1, 2)  # Chain entanglement
    
    # Lens aberrations
    qc.cry(np.pi/6, 0, 4)
    qc.crz(np.pi/8, 1, 5)

Circuit Execution
-----------------

.. code-block:: python

    # Execute on quantum simulator
    simulator = Aer.get_backend('qasm_simulator')
    job = simulator.run(transpile(qc, simulator), shots=100)
    result = job.result()
    counts = result.get_counts(qc)
    
    # Extract most probable measurement
    most_probable = max(counts, key=counts.get)
    processed_value = int(most_probable, 2)

Analysis Features
=================

The demonstration includes several analysis tools:

Image Comparison
----------------

* **Original Specimen**: Input synthetic microscopy image
* **Quantum Processed**: Output after quantum circuit processing
* **Phase Difference Map**: Visualization of intensity changes

Fourier Space Analysis
----------------------

* **FFT of Original**: Reciprocal space representation of input
* **FFT of Processed**: Reciprocal space after quantum processing
* Comparison reveals how quantum operations affect spatial frequencies

Statistical Analysis
--------------------

* Histogram comparison of intensity distributions
* Mean intensity before/after processing
* Phase shift statistics

Performance Metrics
===================

Quantum Advantage Characteristics
----------------------------------

* **Gate Depth**: ~20 gates per pixel (polylogarithmic scaling)
* **Qubit Requirements**: 8 qubits for 8-bit encoding
* **Parallelization**: Multiple pixels can be processed in parallel on larger quantum computers
* **Classical Comparison**: Classical operations scale as O(N² log N²) for N×N images

Notebook Location
=================

The complete interactive demonstration is available at:

``examples/quantum_ctem.ipynb``

The notebook includes:

* Full implementation with visualization
* Circuit diagrams
* Statistical analysis
* Fourier space comparisons
* Performance metrics
* Extensible framework for custom quantum operations

Running the Example
===================

Prerequisites
-------------

.. code-block:: bash

    pip install qiskit qiskit-aer numpy matplotlib pillow

Execute Notebook
----------------

.. code-block:: bash

    jupyter notebook examples/quantum_ctem.ipynb

Or run the Python script:

.. code-block:: bash

    python examples/quantum_ctem_demonstration.py

Expected Output
===============

The example generates several visualization files:

* ``quantum_ctem_simulation.png`` - Side-by-side image comparison
* ``quantum_ctem_stats.png`` - Statistical analysis plots
* ``quantum_ctem_circuit.png`` - Quantum circuit diagram
* ``quantum_ctem_fourier.png`` - Fourier space analysis

Future Extensions
=================

This example can be extended to:

* **Real Hardware Execution**: Deploy on IBM Quantum devices
* **Noise Analysis**: Study effects of quantum noise on image quality
* **Advanced Encoding**: Test different quantum encoding schemes
* **Multi-slice Simulation**: Extend to 3D specimen reconstruction
* **Error Mitigation**: Implement error correction techniques
* **Hybrid Algorithms**: Combine with classical pre/post-processing

References
==========

* Quantum Image Processing: FRQI, NEQR encoding methods
* Quantum Simulation of Physical Systems
* Transmission Electron Microscopy theory
* Qiskit documentation and tutorials

See Also
========

* :doc:`basic_examples` - Introduction to quantum image encoding
* :doc:`advanced_examples` - More complex quantum algorithms
* :doc:`../api` - Full API reference
