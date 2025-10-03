# Pure Quantum Bloch Wave Simulation - Development Plan

## Project: QuScope Quantum CTEM v2.0
**Goal**: Implement true quantum Bloch wave propagation algorithm  
**Timeline**: 3-6 months  
**Target**: High-impact journal publication (Physical Review A / Quantum / Nature Communications)

---

## Core Principle

**Classical Potential + Quantum Wave Evolution = Pure Quantum Bloch Wave**

✅ **Classical (parameters)**: Kirkland potential V(x,y) from atomic scattering factors  
✅ **Quantum (dynamics)**: Electron wave function ψ(x,y) evolution through potential

This is physically valid! Just like in quantum chemistry:
- Atomic coordinates and charges are classical parameters
- Electronic wave function evolution is quantum

---

## Phase 1: Quantum Wave Function Representation (Weeks 1-4)

### Week 1: Quantum State Encoding Design

**Goal**: Design how to represent ψ(x,y) as quantum state |ψ⟩

#### Task 1.1: Choose Encoding Scheme
Compare three approaches:

**A. Amplitude Encoding** (Most natural)
```python
# ψ(x,y) → |ψ⟩ = Σ ψ(x,y) |x⟩|y⟩
# 
# Pros: Direct representation, natural for wave functions
# Cons: Requires normalization, state preparation overhead
# Qubits: n_x + n_y (e.g., 8 + 8 = 16 qubits for 256×256)

def amplitude_encode_wave(psi_classical):
    """Encode complex wave function into quantum amplitudes"""
    # Flatten 2D wave
    psi_flat = psi_classical.flatten()
    
    # Normalize for quantum state
    norm = np.linalg.norm(psi_flat)
    psi_normalized = psi_flat / norm
    
    # Create quantum circuit
    n_qubits = int(np.log2(len(psi_flat)))
    qc = QuantumCircuit(n_qubits)
    qc.initialize(psi_normalized, range(n_qubits))
    
    return qc, norm  # Store norm for later denormalization
```

**B. Basis Encoding** (Alternative)
```python
# Encode as sum of basis states weighted by amplitudes
# More suitable for sparse wave functions
# Not ideal for CTEM (wave functions are typically dense)
```

**C. FRQI Encoding** (Quantum image processing standard)
```python
# Flexible Representation of Quantum Images
# |I⟩ = 1/2^n Σ (cos(θᵢⱼ)|0⟩ + sin(θᵢⱼ)e^(iφᵢⱼ)|1⟩) ⊗ |ij⟩
# Pros: Efficient for images
# Cons: Extra qubit overhead, complex for wave functions
```

**Decision**: Use **Amplitude Encoding** (most natural for quantum wave mechanics)

#### Task 1.2: Implement State Preparation
```python
class QuantumWaveFunction:
    """Pure quantum representation of electron wave function"""
    
    def __init__(self, n_qubits_x, n_qubits_y):
        self.n_qubits_x = n_qubits_x  # Spatial x dimension
        self.n_qubits_y = n_qubits_y  # Spatial y dimension
        self.n_spatial = n_qubits_x + n_qubits_y
        
        # For momentum space (after QFT)
        self.n_momentum = self.n_spatial
        
        # Total qubits needed
        self.total_qubits = self.n_spatial
        
    def prepare_incident_wave(self):
        """
        Prepare plane wave incident on specimen
        
        For normal incidence: ψ₀(x,y) = 1
        → |ψ₀⟩ = 1/√N Σ |xy⟩  (uniform superposition)
        """
        qc = QuantumCircuit(self.total_qubits, name='incident_wave')
        
        # Hadamard on all qubits → uniform superposition
        qc.h(range(self.total_qubits))
        
        return qc
    
    def prepare_arbitrary_wave(self, psi_classical):
        """
        Prepare arbitrary complex wave function
        
        ψ(x,y) = A(x,y) exp(iφ(x,y))
        → |ψ⟩ = Σ A(x,y) exp(iφ(x,y)) |xy⟩
        """
        qc = QuantumCircuit(self.total_qubits, name='arbitrary_wave')
        
        # Flatten and normalize
        psi_flat = psi_classical.flatten()
        norm = np.linalg.norm(psi_flat)
        
        if norm < 1e-10:
            # Zero wave → uniform superposition
            qc.h(range(self.total_qubits))
            self._stored_norm = 0.0
        else:
            psi_normalized = psi_flat / norm
            qc.initialize(psi_normalized, range(self.total_qubits))
            self._stored_norm = norm
        
        return qc
    
    def extract_wave(self, circuit):
        """
        Extract wave function from quantum circuit
        
        Returns: Complex amplitudes as classical array
        """
        statevector = Statevector.from_instruction(circuit)
        amplitudes = statevector.data
        
        # Denormalize
        amplitudes *= self._stored_norm
        
        # Reshape to 2D
        pixels_x = 2**self.n_qubits_x
        pixels_y = 2**self.n_qubits_y
        psi_2d = amplitudes.reshape(pixels_x, pixels_y)
        
        return psi_2d
```

#### Task 1.3: Validation Tests
```python
def test_state_preparation():
    """Test quantum wave function preparation"""
    
    # Test 1: Incident plane wave
    qwf = QuantumWaveFunction(n_qubits_x=3, n_qubits_y=3)  # 8×8
    qc = qwf.prepare_incident_wave()
    
    # Should be uniform superposition
    sv = Statevector.from_instruction(qc)
    expected = np.ones(64) / 8  # 1/√64
    assert np.allclose(np.abs(sv.data), expected)
    print("✓ Incident wave test passed")
    
    # Test 2: Gaussian wave packet
    x = np.linspace(-4, 4, 8)
    y = np.linspace(-4, 4, 8)
    X, Y = np.meshgrid(x, y)
    psi_gaussian = np.exp(-(X**2 + Y**2) / 2)
    
    qc = qwf.prepare_arbitrary_wave(psi_gaussian)
    psi_extracted = qwf.extract_wave(qc)
    
    # Should match original (within normalization)
    psi_gaussian_normalized = psi_gaussian / np.linalg.norm(psi_gaussian)
    psi_extracted_normalized = psi_extracted / np.linalg.norm(psi_extracted)
    assert np.allclose(psi_gaussian_normalized, psi_extracted_normalized, atol=1e-10)
    print("✓ Gaussian wave packet test passed")
    
    # Test 3: Complex phase
    psi_complex = psi_gaussian * np.exp(1j * np.pi / 4)
    qc = qwf.prepare_arbitrary_wave(psi_complex)
    psi_extracted = qwf.extract_wave(qc)
    
    # Phase should be preserved
    phase_original = np.angle(psi_complex[4, 4])
    phase_extracted = np.angle(psi_extracted[4, 4])
    assert np.isclose(phase_original, phase_extracted)
    print("✓ Complex phase test passed")
```

---

## Phase 2: Quantum Phase Grating (Weeks 5-8)

### Week 5-6: Design Quantum Transmission Function

**Physical Goal**: Apply t(x,y) = exp(iσV(x,y)Δz) to quantum state |ψ⟩

#### Approach A: Direct Phase Gates (Simple, less efficient)
```python
def quantum_transmission_direct(circuit, wave_qubits, V_classical, sigma, dz):
    """
    Apply transmission function using direct phase gates
    
    For each position (x,y):
        phase = σ * V(x,y) * Δz
        Apply P(phase) gate to |xy⟩ basis state
    
    Pros: Conceptually simple
    Cons: O(N²) gates for N×N image
    """
    pixels_x = 2**len(wave_qubits) // 2
    pixels_y = 2**len(wave_qubits) // 2
    
    for i in range(pixels_x):
        for j in range(pixels_y):
            # Calculate phase for this position
            V_ij = V_classical[i, j]
            phase = sigma * V_ij * dz
            
            # Apply controlled phase gate
            # Control: |ij⟩ basis state
            # Target: Global phase
            
            # Convert (i,j) to binary
            control_state = (i << len(wave_qubits)//2) | j
            
            # Multi-controlled phase gate
            circuit.mcp(phase, 
                       wave_qubits, 
                       None,  # Global phase
                       ctrl_state=control_state)
    
    return circuit
```

#### Approach B: Quantum Oracle (More efficient)
```python
def quantum_transmission_oracle(circuit, wave_qubits, ancilla_qubits, V_classical, sigma, dz):
    """
    Apply transmission function using quantum oracle
    
    Oracle: |x,y⟩|0⟩ → |x,y⟩|V(x,y)⟩
    Then apply phase: |x,y⟩|V⟩ → exp(iσVΔz)|x,y⟩|V⟩
    
    Pros: O(N) gates with proper oracle design
    Cons: Requires ancilla qubits for V(x,y) storage
    """
    
    # Step 1: Compute V(x,y) into ancilla register
    # This can be done with O(log N) depth using binary search tree
    potential_oracle = create_potential_oracle(V_classical, wave_qubits, ancilla_qubits)
    circuit.compose(potential_oracle, inplace=True)
    
    # Step 2: Apply phase proportional to ancilla value
    # phase = σ * V * Δz where V is stored in ancilla
    phase_estimator = create_phase_from_ancilla(ancilla_qubits, sigma, dz)
    circuit.compose(phase_estimator, inplace=True)
    
    # Step 3: Uncompute ancilla (important for garbage collection!)
    circuit.compose(potential_oracle.inverse(), inplace=True)
    
    return circuit

def create_potential_oracle(V_classical, position_qubits, value_qubits):
    """
    Create oracle that computes V(x,y)
    
    |x,y⟩|0⟩ → |x,y⟩|V(x,y)⟩
    
    Implementation: Use QROM (Quantum Read-Only Memory)
    """
    n_pos = len(position_qubits)
    n_val = len(value_qubits)
    
    qc = QuantumCircuit(position_qubits + value_qubits, name='V_oracle')
    
    # Discretize V values to fit in value_qubits
    V_flat = V_classical.flatten()
    V_max = np.max(np.abs(V_flat))
    V_discrete = (V_flat / V_max * (2**n_val - 1)).astype(int)
    
    # Build QROM circuit
    # For each position state |xy⟩, encode corresponding V value
    for idx, V_val in enumerate(V_discrete):
        # Create multi-controlled operation
        # Control: position_qubits in state |idx⟩
        # Target: value_qubits set to |V_val⟩
        
        # Convert V_val to binary and apply X gates
        for bit_idx in range(n_val):
            if (V_val >> bit_idx) & 1:
                # This bit should be |1⟩
                qc.mcx(position_qubits, 
                       value_qubits[bit_idx],
                       ctrl_state=idx)
    
    return qc

def create_phase_from_ancilla(value_qubits, sigma, dz):
    """
    Apply phase rotation based on ancilla register value
    
    |V⟩ → exp(iσVΔz)|V⟩
    
    Use quantum phase estimation or direct controlled rotations
    """
    n_val = len(value_qubits)
    qc = QuantumCircuit(value_qubits, name='phase_from_V')
    
    # For each bit in value register, apply proportional phase
    for k, qubit in enumerate(value_qubits):
        # Bit k contributes 2^k to value
        phase_contribution = sigma * dz * (2**k)
        qc.p(phase_contribution, qubit)
    
    return qc
```

**Decision**: Start with Approach A (direct) for correctness testing, then optimize to Approach B (oracle) for efficiency

#### Task 2.1: Implement and Test
```python
class QuantumPhaseGrating:
    """Quantum implementation of phase grating approximation"""
    
    def __init__(self, sigma, dz, method='direct'):
        self.sigma = sigma
        self.dz = dz
        self.method = method
        
    def apply(self, circuit, wave_qubits, V_classical, ancilla_qubits=None):
        """Apply transmission function quantumly"""
        
        if self.method == 'direct':
            return quantum_transmission_direct(
                circuit, wave_qubits, V_classical, self.sigma, self.dz
            )
        elif self.method == 'oracle':
            if ancilla_qubits is None:
                raise ValueError("Oracle method requires ancilla qubits")
            return quantum_transmission_oracle(
                circuit, wave_qubits, ancilla_qubits, 
                V_classical, self.sigma, self.dz
            )
        else:
            raise ValueError(f"Unknown method: {self.method}")

def test_quantum_phase_grating():
    """Test quantum transmission function"""
    
    # Create simple potential (single atom)
    V = np.zeros((8, 8))
    V[4, 4] = 100.0  # Single atom at center, 100 eV potential
    
    sigma = 0.00729  # Interaction parameter at 200 keV
    dz = 2.0  # 2 Å slice
    
    # Classical transmission function
    phase_classical = sigma * V * dz
    transmission_classical = np.exp(1j * phase_classical)
    
    # Quantum transmission function
    qwf = QuantumWaveFunction(n_qubits_x=3, n_qubits_y=3)
    qc_initial = qwf.prepare_incident_wave()
    
    qpg = QuantumPhaseGrating(sigma, dz, method='direct')
    qc = qc_initial.copy()
    qpg.apply(qc, range(qwf.total_qubits), V)
    
    psi_quantum = qwf.extract_wave(qc)
    
    # Compare: quantum should match classical
    psi_incident = np.ones((8, 8)) / 8  # Normalized plane wave
    psi_classical = transmission_classical * psi_incident
    
    assert np.allclose(psi_quantum, psi_classical, atol=1e-6)
    print("✓ Quantum phase grating test passed")
```

### Week 7-8: Optimize Circuit Depth

**Goal**: Reduce gate count from O(N²) to O(N log N)

#### Techniques:
1. **Gate merging**: Combine adjacent phase gates
2. **Symmetry exploitation**: Use crystal symmetry to reduce unique gates
3. **Approximate gates**: Use Solovay-Kitaev for efficient decomposition
4. **QROM optimization**: Hierarchical addressing for potential lookup

```python
def optimize_phase_grating_circuit(qc, wave_qubits):
    """
    Optimize quantum transmission circuit
    
    Techniques:
    1. Merge consecutive phase gates on same qubit
    2. Use ZZ gates instead of CNOT+P+CNOT
    3. Exploit symmetry in potential
    """
    from qiskit import transpile
    from qiskit.transpiler import PassManager
    from qiskit.transpiler.passes import Optimize1qGates, CommutativeCancellation
    
    # Create optimization pass manager
    pm = PassManager([
        Optimize1qGates(),
        CommutativeCancellation(),
    ])
    
    # Apply optimizations
    qc_optimized = pm.run(qc)
    
    print(f"Original gates: {qc.size()}")
    print(f"Optimized gates: {qc_optimized.size()}")
    print(f"Reduction: {100*(1 - qc_optimized.size()/qc.size()):.1f}%")
    
    return qc_optimized
```

---

## Phase 3: Quantum Propagation (Weeks 9-12)

### Week 9-10: Quantum Fresnel Propagator

**Physical Goal**: Apply P(k) = exp(-iπλk²Δz) in momentum space

#### Challenge: Need k² quantum mechanically

**Solution**: QFT + Quantum arithmetic

```python
class QuantumPropagator:
    """Quantum implementation of Fresnel propagation"""
    
    def __init__(self, wavelength, dz):
        self.wavelength = wavelength
        self.dz = dz
        
    def propagate(self, circuit, wave_qubits):
        """
        Propagate wave function through free space
        
        Steps:
        1. QFT: |ψ(x,y)⟩ → |ψ(kₓ,k_y)⟩
        2. Apply phase: exp(-iπλk²Δz)
        3. IQFT: |ψ(kₓ,k_y)⟩ → |ψ(x,y)⟩
        
        Key challenge: Step 2 requires k² = kₓ² + k_y²
        """
        n_qubits = len(wave_qubits)
        n_x = n_y = n_qubits // 2
        
        kx_qubits = wave_qubits[:n_x]
        ky_qubits = wave_qubits[n_x:]
        
        # Step 1: QFT to momentum space
        qft_2d = self._create_2d_qft(n_x, n_y)
        circuit.compose(qft_2d, wave_qubits, inplace=True)
        
        # Step 2: Apply propagator phase
        # This is the hard part - need quantum k² calculation
        propagator_phase = self._create_propagator_phase(n_x, n_y)
        circuit.compose(propagator_phase, wave_qubits, inplace=True)
        
        # Step 3: IQFT back to real space
        iqft_2d = qft_2d.inverse()
        circuit.compose(iqft_2d, wave_qubits, inplace=True)
        
        return circuit
    
    def _create_2d_qft(self, n_x, n_y):
        """Create 2D QFT circuit"""
        qc = QuantumCircuit(n_x + n_y, name='QFT_2D')
        
        # QFT on x qubits
        qft_x = QFT(n_x, do_swaps=True)
        qc.compose(qft_x, range(n_x), inplace=True)
        
        # QFT on y qubits
        qft_y = QFT(n_y, do_swaps=True)
        qc.compose(qft_y, range(n_x, n_x + n_y), inplace=True)
        
        return qc
    
    def _create_propagator_phase(self, n_x, n_y):
        """
        Apply phase exp(-iπλk²Δz) where k² = kₓ² + k_y²
        
        This requires quantum arithmetic!
        """
        kx_qubits = list(range(n_x))
        ky_qubits = list(range(n_x, n_x + n_y))
        
        qc = QuantumCircuit(n_x + n_y + 2*n_x + 2*n_y,  # Wave + ancillas for kₓ², k_y²
                           name='propagator')
        
        kx_squared_qubits = list(range(n_x + n_y, n_x + n_y + 2*n_x))
        ky_squared_qubits = list(range(n_x + n_y + 2*n_x, n_x + n_y + 2*n_x + 2*n_y))
        
        # Step 1: Calculate kₓ² (quantum squaring)
        qc.compose(
            quantum_square(kx_qubits, kx_squared_qubits),
            kx_qubits + kx_squared_qubits,
            inplace=True
        )
        
        # Step 2: Calculate k_y² (quantum squaring)
        qc.compose(
            quantum_square(ky_qubits, ky_squared_qubits),
            ky_qubits + ky_squared_qubits,
            inplace=True
        )
        
        # Step 3: Add kₓ² + k_y² (quantum addition)
        k_squared_qubits = kx_squared_qubits  # Result stored here
        qc.compose(
            quantum_add(kx_squared_qubits, ky_squared_qubits),
            kx_squared_qubits + ky_squared_qubits,
            inplace=True
        )
        
        # Step 4: Apply phase -πλk²Δz
        phase_factor = -np.pi * self.wavelength * self.dz
        qc.compose(
            apply_phase_from_register(k_squared_qubits, phase_factor),
            k_squared_qubits + kx_qubits + ky_qubits,
            inplace=True
        )
        
        # Step 5: Uncompute ancillas (garbage collection)
        qc.compose(
            quantum_add(kx_squared_qubits, ky_squared_qubits).inverse(),
            kx_squared_qubits + ky_squared_qubits,
            inplace=True
        )
        qc.compose(
            quantum_square(ky_qubits, ky_squared_qubits).inverse(),
            ky_qubits + ky_squared_qubits,
            inplace=True
        )
        qc.compose(
            quantum_square(kx_qubits, kx_squared_qubits).inverse(),
            kx_qubits + kx_squared_qubits,
            inplace=True
        )
        
        return qc
```

#### Week 11: Implement Quantum Arithmetic

**Critical component**: Need quantum circuits for arithmetic operations

```python
def quantum_square(input_qubits, output_qubits):
    """
    Quantum circuit to compute x² 
    
    |x⟩|0⟩ → |x⟩|x²⟩
    
    Using quantum multiplication: x * x = x²
    """
    n_in = len(input_qubits)
    n_out = len(output_qubits)
    
    qc = QuantumCircuit(n_in + n_out, name='x_squared')
    
    # Use quantum multiplier with both inputs = x
    multiplier = create_quantum_multiplier(n_in, n_in, n_out)
    qc.compose(multiplier, 
               input_qubits + input_qubits + output_qubits,
               inplace=True)
    
    return qc

def create_quantum_multiplier(n_a, n_b, n_out):
    """
    Quantum multiplier: |a⟩|b⟩|0⟩ → |a⟩|b⟩|a×b⟩
    
    Methods:
    1. Peasant multiplication (sequential, O(n²) gates)
    2. Karatsuba (recursive, O(n^1.58) gates)
    3. Using QFT (O(n log n) but approximate)
    """
    # For CTEM, use QFT-based approximate multiplication
    # Good enough for physical simulation (errors << quantum noise)
    
    from qiskit.circuit.library import DraperQFTAdder
    
    qc = QuantumCircuit(n_a + n_b + n_out, name='multiply')
    
    # Multiply using repeated addition with QFT adder
    # a × b = b + b + ... + b (a times)
    # Implemented with controlled additions
    
    for i in range(n_a):
        # If bit i of a is 1, add b * 2^i to result
        controlled_add = DraperQFTAdder(n_b).control(1)
        qc.compose(controlled_add,
                   [i] + list(range(n_a, n_a + n_b)) + list(range(n_a + n_b, n_a + n_b + n_out)),
                   inplace=True)
    
    return qc

def quantum_add(a_qubits, b_qubits):
    """
    Quantum adder: |a⟩|b⟩ → |a⟩|a+b⟩
    
    Using Draper QFT adder (most efficient)
    """
    from qiskit.circuit.library import DraperQFTAdder
    
    n_a = len(a_qubits)
    adder = DraperQFTAdder(n_a)
    
    qc = QuantumCircuit(2 * n_a, name='add')
    qc.compose(adder, a_qubits + b_qubits, inplace=True)
    
    return qc

def apply_phase_from_register(value_qubits, scale_factor):
    """
    Apply phase proportional to value in register
    
    |v⟩ → exp(i * scale_factor * v)|v⟩
    """
    n_val = len(value_qubits)
    qc = QuantumCircuit(n_val, name='phase_from_register')
    
    # Each bit contributes weighted phase
    for k, qubit in enumerate(value_qubits):
        phase = scale_factor * (2**k)
        qc.p(phase, qubit)
    
    return qc
```

#### Week 12: Test and Validate

```python
def test_quantum_propagator():
    """Test quantum Fresnel propagation"""
    
    # Create Gaussian wave packet
    x = np.linspace(-4, 4, 8)
    y = np.linspace(-4, 4, 8)
    X, Y = np.meshgrid(x, y)
    psi_initial = np.exp(-(X**2 + Y**2) / 2)
    
    # Classical propagation (using FFT)
    wavelength = 0.0251  # 200 keV electrons
    dz = 10.0  # 10 Å propagation
    
    psi_k_classical = np.fft.fft2(psi_initial)
    kx = np.fft.fftfreq(8, d=1.0)
    ky = np.fft.fftfreq(8, d=1.0)
    KX, KY = np.meshgrid(kx, ky)
    k_squared = KX**2 + KY**2
    propagator = np.exp(-1j * np.pi * wavelength * k_squared * dz)
    psi_k_classical *= propagator
    psi_final_classical = np.fft.ifft2(psi_k_classical)
    
    # Quantum propagation (using QFT)
    qwf = QuantumWaveFunction(n_qubits_x=3, n_qubits_y=3)
    qc = qwf.prepare_arbitrary_wave(psi_initial)
    
    qp = QuantumPropagator(wavelength, dz)
    qp.propagate(qc, range(qwf.total_qubits))
    
    psi_final_quantum = qwf.extract_wave(qc)
    
    # Compare
    error = np.linalg.norm(psi_final_quantum - psi_final_classical) / np.linalg.norm(psi_final_classical)
    print(f"Propagation error: {error:.6f}")
    assert error < 0.01, "Quantum propagation error too large!"
    print("✓ Quantum propagator test passed")
```

---

## Phase 4: Full Quantum Multislice (Weeks 13-16)

### Week 13-14: Integrate All Components

```python
class PureQuantumMultisliceCTEM:
    """
    Complete pure quantum multislice CTEM simulation
    
    All wave evolution happens quantumly:
    - Wave function stored as quantum state
    - Phase grating applied via quantum gates
    - Propagation via QFT + quantum arithmetic
    - No classical intermediate steps
    """
    
    def __init__(self, n_qubits_x, n_qubits_y, beam_energy, slice_thickness):
        self.n_qubits_x = n_qubits_x
        self.n_qubits_y = n_qubits_y
        self.total_qubits = n_qubits_x + n_qubits_y
        
        # Physical parameters
        self.beam_energy = beam_energy
        self.wavelength = self._calculate_wavelength()
        self.sigma = self._calculate_sigma()
        self.slice_thickness = slice_thickness
        
        # Quantum components
        self.qwf = QuantumWaveFunction(n_qubits_x, n_qubits_y)
        self.qpg = QuantumPhaseGrating(self.sigma, slice_thickness)
        self.qp = QuantumPropagator(self.wavelength, slice_thickness)
        
    def simulate_multislice(self, potential_slices):
        """
        Full quantum multislice simulation
        
        Args:
            potential_slices: List of 2D arrays, V(x,y) for each slice (classical)
        
        Returns:
            final_circuit: Quantum circuit representing full simulation
        """
        n_slices = len(potential_slices)
        
        # Initialize with incident plane wave
        circuit = self.qwf.prepare_incident_wave()
        
        print(f"Simulating {n_slices} slices quantumly...")
        
        for i, V_slice in enumerate(potential_slices):
            print(f"  Slice {i+1}/{n_slices}")
            
            # Step 1: Phase grating (transmission function)
            self.qpg.apply(circuit, range(self.total_qubits), V_slice)
            
            # Step 2: Propagate to next slice (if not last)
            if i < n_slices - 1:
                self.qp.propagate(circuit, range(self.total_qubits))
        
        return circuit
    
    def get_exit_wave(self, circuit):
        """Extract exit wave function from final quantum state"""
        return self.qwf.extract_wave(circuit)
    
    def get_intensity(self, circuit):
        """
        Calculate intensity from quantum state
        
        Option 1: Extract full wave function (simulation only)
        Option 2: Quantum amplitude estimation (real hardware)
        """
        psi = self.get_exit_wave(circuit)
        intensity = np.abs(psi)**2
        return intensity
    
    def apply_objective_lens(self, circuit, defocus, Cs=0):
        """
        Apply objective lens transfer function
        
        Similar to propagator but with aberration phase
        χ(k) = πλk²(CsλK²/2 - Δf)
        """
        # QFT to momentum space
        qft_2d = QFT(self.total_qubits, do_swaps=True)
        circuit.compose(qft_2d, inplace=True)
        
        # Apply CTF phase (requires k² calculation)
        ctf_phase = self._create_ctf_phase(defocus, Cs)
        circuit.compose(ctf_phase, inplace=True)
        
        # IQFT back to real space
        circuit.compose(qft_2d.inverse(), inplace=True)
        
        return circuit
    
    def _calculate_wavelength(self):
        V = self.beam_energy
        return 12.2639 / np.sqrt(V + 0.97845e-6 * V**2)
    
    def _calculate_sigma(self):
        V = self.beam_energy
        V_keV = V / 1000.0
        m0c2 = 511.0e3
        gamma = (m0c2 + V) / (2 * m0c2 + V)
        return 0.00335 * gamma / (self.wavelength * V_keV)
    
    def _create_ctf_phase(self, defocus, Cs):
        """Create CTF phase circuit (similar to propagator)"""
        # Implementation similar to QuantumPropagator._create_propagator_phase
        # But with different phase formula
        pass
```

### Week 15: Full System Test

```python
def test_full_quantum_multislice():
    """Test complete quantum multislice simulation"""
    
    # Create simple test case: 2 slices, single atom per slice
    n_qubits_x = n_qubits_y = 3  # 8×8 pixels
    
    # Slice 1: Carbon atom at center
    V1 = np.zeros((8, 8))
    V1[4, 4] = 50.0  # eV
    
    # Slice 2: Carbon atom at center (same position)
    V2 = np.zeros((8, 8))
    V2[4, 4] = 50.0
    
    # Run quantum simulation
    qms = PureQuantumMultisliceCTEM(
        n_qubits_x=3, n_qubits_y=3,
        beam_energy=200e3,
        slice_thickness=2.0
    )
    
    circuit = qms.simulate_multislice([V1, V2])
    intensity_quantum = qms.get_intensity(circuit)
    
    # Run classical simulation for comparison
    from classical_multislice import ClassicalMultislice
    cms = ClassicalMultislice(pixels=8, beam_energy=200e3, slice_thickness=2.0)
    intensity_classical = cms.simulate([V1, V2])
    
    # Compare
    error = np.linalg.norm(intensity_quantum - intensity_classical) / np.linalg.norm(intensity_classical)
    print(f"Quantum vs Classical error: {error:.6f}")
    
    # Plot comparison
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    axes[0].imshow(intensity_classical, cmap='gray')
    axes[0].set_title('Classical')
    axes[1].imshow(intensity_quantum, cmap='gray')
    axes[1].set_title('Quantum')
    axes[2].imshow(np.abs(intensity_quantum - intensity_classical), cmap='hot')
    axes[2].set_title(f'|Difference| (error={error:.4f})')
    plt.show()
    
    assert error < 0.05, "Quantum multislice error too large!"
    print("✓ Full quantum multislice test passed")
```

### Week 16: GaAs [110] Validation

```python
def validate_gaas_quantum():
    """
    Validate against Kirkland's GaAs [110] results
    
    Reproduce Figures 7.2, 7.3, 7.4 with pure quantum algorithm
    """
    # Create GaAs structure (classical - this is OK!)
    from create_gaas_structure import GaAsStructure
    gaas = GaAsStructure(supercell=(4, 4, 20), orientation='110')
    
    # Get potential slices (classical - this is OK!)
    potential_slices = gaas.get_potential_slices(slice_thickness=2.0)
    
    # Quantum simulation
    qms = PureQuantumMultisliceCTEM(
        n_qubits_x=4, n_qubits_y=4,  # 16×16 pixels (small for testing)
        beam_energy=200e3,
        slice_thickness=2.0
    )
    
    # Simulate different thicknesses
    thicknesses = [50, 100, 200, 400]
    
    for thickness in thicknesses:
        n_slices = int(thickness / 2.0)
        circuit = qms.simulate_multislice(potential_slices[:n_slices])
        
        # Apply objective lens
        qms.apply_objective_lens(circuit, defocus=0, Cs=1.3e7)
        
        # Get intensity
        intensity = qms.get_intensity(circuit)
        
        # Compare with Kirkland Table 7.2
        mean_intensity = np.mean(intensity)
        print(f"Thickness {thickness} Å: Mean intensity = {mean_intensity:.3f}")
        
        # Plot
        plt.imshow(intensity, cmap='gray')
        plt.title(f'Quantum CTEM: GaAs [110], {thickness} Å')
        plt.colorbar()
        plt.show()
```

---

## Phase 5: Optimization & Hardware (Weeks 17-20)

### Week 17-18: Circuit Optimization

**Goal**: Reduce circuit depth for real quantum hardware

```python
def optimize_quantum_ctem_circuit(circuit, optimization_level=3):
    """
    Optimize full quantum CTEM circuit
    
    Targets:
    - Gate count: < 100,000
    - Circuit depth: < 10,000
    - Qubit count: < 20
    """
    from qiskit import transpile
    from qiskit.transpiler import CouplingMap
    
    # Transpile for specific backend
    backend = AerSimulator()
    
    circuit_optimized = transpile(
        circuit,
        backend=backend,
        optimization_level=optimization_level,
        seed_transpiler=42
    )
    
    print(f"Original: {circuit.size()} gates, depth {circuit.depth()}")
    print(f"Optimized: {circuit_optimized.size()} gates, depth {circuit_optimized.depth()}")
    
    return circuit_optimized

def estimate_hardware_requirements():
    """
    Estimate resources for real quantum computer
    
    For N×N image (N = 2^n qubits):
    - Wave function: 2n qubits
    - Arithmetic ancillas: ~4n qubits (for k² calculation)
    - Total: ~6n qubits
    
    Example:
    - 16×16 image: n=4, total ~24 qubits
    - 32×32 image: n=5, total ~30 qubits
    - 64×64 image: n=6, total ~36 qubits
    """
    for n in range(3, 8):
        N = 2**n
        wave_qubits = 2*n
        arithmetic_qubits = 4*n
        total_qubits = wave_qubits + arithmetic_qubits
        
        print(f"{N}×{N} image: {wave_qubits} wave + {arithmetic_qubits} arithmetic = {total_qubits} total qubits")
```

### Week 19-20: Run on Real Hardware

```python
def run_on_ibm_quantum(circuit, shots=1024):
    """
    Execute circuit on IBM Quantum hardware
    
    Available systems (as of 2025):
    - ibm_kyoto: 127 qubits
    - ibm_osaka: 127 qubits
    - ibm_brisbane: 127 qubits
    """
    from qiskit_ibm_runtime import QiskitRuntimeService, Sampler
    
    # Load IBM Quantum account
    service = QiskitRuntimeService(channel="ibm_quantum")
    
    # Select backend
    backend = service.backend("ibm_kyoto")
    
    # Transpile for hardware
    circuit_hw = transpile(circuit, backend, optimization_level=3)
    
    print(f"Running on {backend.name}...")
    print(f"Circuit depth: {circuit_hw.depth()}")
    print(f"Circuit gates: {circuit_hw.size()}")
    
    # Execute
    sampler = Sampler(backend)
    job = sampler.run(circuit_hw, shots=shots)
    
    result = job.result()
    
    return result

def benchmark_quantum_vs_classical():
    """
    Comprehensive benchmark: Quantum vs Classical
    
    Metrics:
    1. Accuracy: How close to classical?
    2. Time: Quantum faster? (probably not initially)
    3. Scaling: How does performance scale with N?
    4. Hardware noise: Impact on results?
    """
    results = {}
    
    for n_qubits in [3, 4, 5]:  # 8×8, 16×16, 32×32
        N = 2**n_qubits
        print(f"\nBenchmarking {N}×{N} image...")
        
        # Create test potential
        V = create_test_potential(N, N)
        
        # Classical simulation
        import time
        t0 = time.time()
        intensity_classical = simulate_classical(V)
        time_classical = time.time() - t0
        
        # Quantum simulation
        t0 = time.time()
        intensity_quantum = simulate_quantum(V, n_qubits)
        time_quantum = time.time() - t0
        
        # Compare
        error = np.linalg.norm(intensity_quantum - intensity_classical) / np.linalg.norm(intensity_classical)
        
        results[N] = {
            'error': error,
            'time_classical': time_classical,
            'time_quantum': time_quantum,
            'speedup': time_classical / time_quantum
        }
        
        print(f"  Error: {error:.6f}")
        print(f"  Time (classical): {time_classical:.3f} s")
        print(f"  Time (quantum): {time_quantum:.3f} s")
        print(f"  Speedup: {results[N]['speedup']:.2f}x")
    
    return results
```

---

## Phase 6: Publication (Weeks 21-24)

### Week 21-22: Write Paper

**Title**: "Pure Quantum Algorithm for Multislice Electron Microscopy Image Simulation"

**Structure**:

1. **Abstract**
   - First pure quantum Bloch wave simulation
   - All wave evolution on quantum computer
   - Validated against classical multislice
   - Demonstrated on real quantum hardware

2. **Introduction**
   - CTEM imaging principles
   - Multislice method review
   - Why quantum computing?
   - Our contribution

3. **Methods**
   - Quantum wave function representation
   - Quantum phase grating
   - Quantum Fresnel propagation
   - Circuit architecture

4. **Results**
   - Validation: Single atom, thin specimen
   - GaAs [110] comparison with Kirkland
   - Hardware experiments
   - Benchmarking

5. **Discussion**
   - Quantum advantage analysis
   - Limitations
   - Future directions

6. **Conclusion**

### Week 23: Prepare Supplementary Materials

- **Code repository**: GitHub with full implementation
- **Quantum circuits**: Export to OpenQASM
- **Data**: All simulation results + raw data
- **Videos**: Animations of wave propagation

### Week 24: Submit and Present

**Target Journals** (in order of preference):
1. **Physical Review A** - Atomic, Molecular, and Optical Physics
2. **Quantum** - Open access, high impact in quantum computing
3. **npj Quantum Information** - Nature partner journal
4. **Physical Review Applied** - Applications of quantum computing
5. **Journal of Applied Physics** - Electron microscopy audience

**Conference Presentations**:
- Microscopy & Microanalysis (M&M)
- Quantum Information Processing (QIP)
- APS March Meeting

---

## Success Metrics

### Technical Milestones:
- [ ] Quantum wave function encoding working (Week 4)
- [ ] Quantum phase grating validated (Week 8)
- [ ] Quantum propagator tested (Week 12)
- [ ] Full multislice simulation complete (Week 16)
- [ ] Hardware execution successful (Week 20)
- [ ] Paper submitted (Week 24)

### Scientific Validation:
- [ ] Matches classical for single atom (error < 0.1%)
- [ ] Matches classical for thin specimen (error < 1%)
- [ ] Matches Kirkland GaAs results (error < 5%)
- [ ] Stable on hardware (with error mitigation)

### Publication Impact:
- [ ] Submitted to high-impact journal (IF > 5)
- [ ] Positive peer reviews
- [ ] Accepted and published
- [ ] Follow-up citations and interest

---

## Resources Needed

### Computational:
- **Qiskit 1.1+**: Quantum circuit framework
- **IBM Quantum**: Access to 127-qubit systems
- **HPC cluster**: For large-scale classical validation

### Human:
- **Your time**: ~20 hrs/week for 6 months
- **Quantum computing expert**: Consultation for optimization
- **Microscopy expert**: Validation and interpretation

### Financial:
- **IBM Quantum Premium**: ~$5,000/year for hardware access
- **Publication fees**: $1,500-3,000 (if open access)
- **Conference travel**: $2,000-5,000

---

## Risk Mitigation

### Risk 1: Circuit too deep for hardware
**Mitigation**: 
- Start with small images (16×16)
- Use error mitigation techniques
- Publish simulation results first

### Risk 2: Quantum advantage not achieved
**Mitigation**:
- Focus on proof-of-concept value
- Emphasize novel algorithm, not speedup
- Compare against future projections

### Risk 3: Validation fails
**Mitigation**:
- Extensive unit testing at each phase
- Multiple validation cases
- Classical co-simulation throughout

### Risk 4: Scooped by competitors
**Mitigation**:
- Move quickly through phases
- arXiv preprint early (Month 4)
- Secure preliminary results ASAP

---

## Next Actions (This Week)

1. **Review this plan** - Discuss with team, adjust timeline
2. **Set up infrastructure** - GitHub repo, Qiskit environment
3. **Start Phase 1** - Begin quantum wave function encoding
4. **Order resources** - IBM Quantum access, HPC allocation
5. **Literature review** - Recent quantum algorithms for PDEs

**Let's get started! 🚀**

---

*Created: October 2, 2025*
*Target completion: April 2, 2026*
*High-impact publication target: June 2026*
