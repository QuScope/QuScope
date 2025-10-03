Advanced Examples
=================

This section contains advanced examples for experienced users.

Custom Quantum Encoding
------------------------

Implementing custom quantum encoding methods:

.. code-block:: python

   from quscope.image_processing.quantum_encoding import encode_image_to_circuit, EncodingMethod
   import numpy as np
   from qiskit import QuantumCircuit
   from qiskit.circuit.library import RYGate, CXGate
   
   def custom_phase_encoding(image_data):
       """Custom encoding using phase rotations."""
       flat_data = image_data.flatten()
       n_qubits = int(np.ceil(np.log2(len(flat_data))))
       circuit = QuantumCircuit(n_qubits)
       
       # Apply Hadamard to create superposition
       circuit.h(range(n_qubits))
       
       # Apply phase rotations based on pixel values
       for i, pixel in enumerate(flat_data[:2**n_qubits]):
           if i < 2**n_qubits:
               circuit.p(pixel * np.pi, i % n_qubits)
       
       return circuit
   
   # Use custom encoder
   image_data = np.random.rand(4, 4)
   circuit = custom_phase_encoding(image_data)
   print(f"Custom circuit: {circuit.num_qubits} qubits, depth {circuit.depth()}")

EELS Analysis Workflow
----------------------

Complete electron energy loss spectroscopy analysis:

.. code-block:: python

   from quscope.eels_analysis.analysis import EELSAnalyzer
   from quscope.eels_analysis.preprocessing import normalize_spectrum
   import numpy as np
   
   # Simulate EELS spectrum
   energy_axis = np.linspace(0, 1000, 256)  # Energy in eV
   # Create spectrum with peaks at 284 eV (C K-edge) and 532 eV (O K-edge)
   spectrum = (
       100 * np.exp(-((energy_axis - 284) / 30)**2) +  # C peak
       80 * np.exp(-((energy_axis - 532) / 40)**2) +   # O peak
       np.random.normal(0, 5, len(energy_axis))  # Noise
   )
   
   # Normalize spectrum
   spectrum_normalized = normalize_spectrum(spectrum)
   
   # Create analyzer with 6-qubit circuits
   analyzer = EELSAnalyzer(n_qubits=6)
   
   # Comprehensive analysis
   results = analyzer.comprehensive_analysis_from_array(
       spectrum_normalized, 
       energy_axis
   )
   
   # Display results
   print(f"Detected elements: {results['elements']}")
   print(f"Quantum entropy: {results['quantum_features']['entropy']:.3f}")
   print(f"Material classification: {results['material_classification']}")
   
   # Visualize
   analyzer.visualize_results(results)

Performance Optimization
------------------------

Optimizing quantum circuits for better performance:

.. code-block:: python

   from quscope.image_processing.quantum_encoding import encode_image_to_circuit, EncodingMethod
   from qiskit.transpiler import PassManager, transpile
   from qiskit.transpiler.passes import Optimize1qGates, CXCancellation
   from qiskit_aer import AerSimulator
   import numpy as np
   
   # Create circuit
   image_data = np.random.rand(4, 4)
   circuit = encode_image_to_circuit(image_data, method=EncodingMethod.AMPLITUDE)
   
   print(f"Original circuit - Gates: {circuit.size()}, Depth: {circuit.depth()}")
   
   # Optimize the circuit
   pass_manager = PassManager([
       Optimize1qGates(),
       CXCancellation()
   ])
   optimized_circuit = pass_manager.run(circuit)
   
   print(f"Optimized circuit - Gates: {optimized_circuit.size()}, Depth: {optimized_circuit.depth()}")
   
   # Transpile for specific backend
   backend = AerSimulator()
   transpiled_circuit = transpile(circuit, backend=backend, optimization_level=3)
   
   print(f"Transpiled circuit - Gates: {transpiled_circuit.size()}, Depth: {transpiled_circuit.depth()}")
