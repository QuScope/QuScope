# Quantum CTEM Bloch Wave Simulation Roadmap

## Current Status (v0.1.0 Development)

### What We Have:
- ✅ Classical multislice CTEM simulation (working reference implementation)
- ✅ Hybrid quantum-classical CTEM using QFT for Fourier transforms
- ✅ Proper Kirkland potential parameterization
- ✅ GaAs [110] crystal structure generation
- ⚠️ Quantum Fourier transforms (QFT/IQFT) implemented but not fully integrated

### What's Missing for Pure Quantum Bloch Wave:
- ❌ Quantum representation of electron wave function as quantum state
- ❌ Quantum evolution of Bloch waves through crystal potential
- ❌ Quantum implementation of phase grating approximation
- ❌ Quantum version of fftshift operation
- ❌ Quantum accumulation of phase from slice propagation

---

## Path to Pure Quantum Bloch Wave Simulation

### Phase 1: Foundation (Current Priority)
**Goal**: Establish correct quantum state representation

#### 1.1 Quantum Bloch Wave State Encoding
```python
class QuantumBlochWave:
    """
    Represent electron wave as pure quantum state
    
    Key Insight:
    - Electron wavefunction ψ(x,y) → |ψ⟩ quantum state
    - Amplitude encoding: |ψ⟩ = Σ ψ(x,y)|x,y⟩
    - Phase information preserved in complex amplitudes
    """
    
    def __init__(self, n_qubits_x, n_qubits_y):
        self.n_qubits_x = n_qubits_x
        self.n_qubits_y = n_qubits_y
        self.total_qubits = n_qubits_x + n_qubits_y
        
    def encode_incident_wave(self):
        """
        Encode plane wave as quantum state
        
        For normal incidence: ψ₀(x,y) = 1
        → Uniform superposition: |ψ⟩ = (1/√N) Σ|x,y⟩
        """
        pass
        
    def encode_complex_wave(self, amplitude, phase):
        """
        Encode arbitrary complex wavefunction
        
        ψ(x,y) = A(x,y) exp(iφ(x,y))
        → |ψ⟩ = Σ A(x,y) exp(iφ(x,y)) |x,y⟩
        """
        pass
```

#### 1.2 Quantum Phase Grating
```python
def quantum_phase_grating(qc, potential_qubits, wave_qubits, sigma, dz):
    """
    Apply transmission function quantumly
    
    t(x,y) = exp(iσV(x,y)Δz)
    
    Approaches:
    1. Hamiltonian evolution: exp(-iHt) where H ∝ V(x,y)
    2. Controlled phase gates based on potential values
    3. Quantum phase estimation for precise phase accumulation
    """
    pass
```

#### 1.3 Pure Quantum Propagation
```python
def quantum_propagate(qc, wave_qubits, wavelength, dz):
    """
    Fresnel propagator in quantum domain
    
    P(k) = exp(-iπλk²Δz)
    
    Steps:
    1. Apply QFT to go to reciprocal space
    2. Apply phase based on k² (quantum arithmetic)
    3. Apply IQFT to return to real space
    
    Challenge: Quantum implementation of k² calculation
    """
    pass
```

---

### Phase 2: Quantum Arithmetic for Physics

#### 2.1 Quantum k-space Operations
**Problem**: Need to calculate k² for each k-vector quantum mechanically

**Solution**: Quantum arithmetic circuits
```python
def quantum_k_squared(k_qubits, k2_qubits):
    """
    Compute k² = kₓ² + k_y² quantumly
    
    Use quantum adder and multiplier circuits:
    - Quantum multiplier: kₓ × kₓ → kₓ²
    - Quantum multiplier: k_y × k_y → k_y²
    - Quantum adder: kₓ² + k_y² → k²
    """
    pass
```

#### 2.2 Quantum Phase Accumulation
```python
def quantum_phase_from_potential(potential_qubits, phase_qubits, sigma, dz):
    """
    Calculate φ = σV(x,y)Δz quantumly
    
    Requires:
    - Quantum fixed-point multiplication
    - Controlled rotation gates based on result
    """
    pass
```

---

### Phase 3: Full Quantum Multislice Algorithm

```python
class PureQuantumMultislice:
    """
    Complete quantum multislice simulation
    
    All operations performed on quantum computer:
    1. Wave state stored as quantum state |ψ⟩
    2. Transmission via quantum phase gates
    3. Propagation via QFT + quantum phase estimation
    4. No classical intermediate steps
    """
    
    def simulate_slice_propagation(self, circuit, n_slices):
        """
        For each slice z:
            1. |ψ⟩ → Apply quantum phase grating
            2. QFT: |ψ⟩_real → |ψ⟩_k
            3. Apply quantum propagator (k² calculation)
            4. IQFT: |ψ⟩_k → |ψ⟩_real
        """
        for slice_idx in range(n_slices):
            # Quantum phase grating
            self.apply_transmission_quantum(circuit, slice_idx)
            
            # QFT
            qft = QFT(self.total_qubits, do_swaps=True)
            circuit.compose(qft, inplace=True)
            
            # Quantum propagator (requires quantum k² calculation)
            self.apply_propagator_quantum(circuit)
            
            # IQFT
            iqft = qft.inverse()
            circuit.compose(iqft, inplace=True)
        
        return circuit
    
    def apply_transmission_quantum(self, circuit, slice_idx):
        """
        Pure quantum phase grating
        
        No classical potential calculation!
        Potential encoded in quantum register.
        """
        # Get potential from quantum memory
        potential_state = self.get_slice_potential_quantum(slice_idx)
        
        # Apply controlled phase rotations
        # phase = sigma * V * dz
        # Implemented as quantum multiplication + rotation
        pass
    
    def apply_propagator_quantum(self, circuit):
        """
        Pure quantum Fresnel propagator
        
        No classical k² calculation!
        k-vectors in quantum superposition.
        """
        # k² calculation using quantum arithmetic
        k_squared_register = self.compute_k_squared_quantum()
        
        # Apply phase: exp(-iπλk²Δz)
        # Using quantum phase estimation
        pass
```

---

## Technical Challenges & Solutions

### Challenge 1: Quantum vs Classical Shift Operations
**Problem**: `np.fft.fftshift` is classical array manipulation

**Solution**: Quantum bit-reversal circuit
```python
def quantum_fftshift(circuit, qubits):
    """
    Quantum implementation of fftshift
    
    Reorder qubits to achieve frequency centering
    Uses SWAP gates in specific pattern
    """
    n = len(qubits)
    # Pattern of SWAPs to center zero frequency
    for i in range(n//2):
        circuit.swap(qubits[i], qubits[i + n//2])
```

### Challenge 2: Storing Crystal Potential Quantumly
**Problem**: Kirkland potential is computed classically

**Solution**: Quantum RAM (QRAM) or quantum state preparation
```python
def prepare_potential_quantum(circuit, potential_classical):
    """
    Encode crystal potential into quantum state
    
    Options:
    1. QRAM: Store V(x,y) in quantum accessible memory
    2. Oracle: Quantum circuit that computes V(x,y)
    3. Amplitude encoding: |V⟩ = Σ V(x,y)|x,y⟩
    """
    # Normalize potential for quantum state
    V_normalized = potential_classical / np.linalg.norm(potential_classical)
    
    # Initialize quantum state with potential values
    circuit.initialize(V_normalized.flatten(), potential_qubits)
```

### Challenge 3: Quantum Measurement of Final Image
**Problem**: Need intensity I(x,y) = |ψ(x,y)|² from quantum state

**Solution**: Quantum amplitude estimation or sampling
```python
def measure_intensity_quantum(circuit, wave_qubits):
    """
    Extract intensity from quantum state
    
    Methods:
    1. Amplitude estimation algorithm (quantum)
    2. Tomography for full state reconstruction
    3. Direct measurement + histogram (semi-classical)
    """
    # Create ancilla for amplitude estimation
    ancilla = QuantumRegister(1, 'anc')
    circuit.add_register(ancilla)
    
    # Amplitude estimation circuit
    # Gives |ψ(x,y)|² without collapsing state
    pass
```

---

## Implementation Priority

### Immediate Goals (Next 2-4 Weeks):
1. ✅ **Fix hybrid implementation**
   - Remove classical postprocessing steps
   - Implement quantum fftshift
   - Verify QFT correctness against FFT

2. 🔄 **Quantum k² arithmetic**
   - Implement quantum multiplier for k²
   - Test on small examples (4-8 qubits)
   - Integrate into propagator

3. 🔄 **Quantum phase grating**
   - Design controlled phase rotation circuit
   - Encode potential in quantum register
   - Apply transmission function quantumly

### Medium-term Goals (1-3 Months):
4. 📋 **Full quantum multislice**
   - Integrate all quantum components
   - Test on single slice propagation
   - Validate against classical reference

5. 📋 **Optimization**
   - Circuit depth reduction
   - Error mitigation strategies
   - Resource estimation for real quantum hardware

### Long-term Vision (3-6 Months):
6. 🎯 **Quantum advantage demonstration**
   - Identify regimes where quantum is superior
   - Benchmark against classical multislice
   - Publish results

7. 🎯 **Hardware implementation**
   - Transpile for IBM/IonQ/Rigetti hardware
   - Run on real quantum computers
   - Compare noisy vs ideal results

---

## Code Structure Recommendations

```
src/quscope/
├── ctem/
│   ├── __init__.py
│   ├── classical/
│   │   ├── multislice.py          # Current working code
│   │   ├── potential.py            # Kirkland parameterization
│   │   └── structures.py           # Crystal structures
│   ├── hybrid/
│   │   ├── qft_multislice.py      # Current QFT implementation
│   │   └── quantum_transforms.py   # QFT/IQFT utilities
│   └── pure_quantum/
│       ├── quantum_bloch.py        # Pure quantum Bloch wave
│       ├── quantum_arithmetic.py   # k² calculation, etc.
│       ├── quantum_propagator.py   # Fresnel propagator
│       └── quantum_measurement.py  # Intensity extraction
├── quantum_backend.py
└── utils/
    ├── validation.py
    └── benchmarking.py
```

---

## Validation Strategy

### Test 1: Single Atom
- **Classical**: Known analytical solution for single atom scattering
- **Hybrid QFT**: Should match classical exactly
- **Pure Quantum**: Should match within quantum sampling error

### Test 2: Thin Specimen (WPO)
- **Classical**: GaAs [110], thickness < 50 Å
- **Verify**: Transmission function correctness
- **Compare**: Intensity profiles line-by-line

### Test 3: Thick Specimen (Multislice)
- **Classical**: GaAs [110], thickness 100-500 Å
- **Verify**: Slice-by-slice propagation
- **Compare**: Final image intensity vs Kirkland results

### Test 4: Defocus Series
- **Classical**: Images at various defocus values
- **Verify**: CTF application correctness
- **Compare**: Contrast transfer across methods

---

## Open Questions for Discussion

1. **Qubit Requirements**: 
   - Current: 8 qubits → 256×256 image
   - Realistic: Can we handle 512×512 (9 qubits)?
   - With k² arithmetic: Need ~16-20 qubits total

2. **Hybrid vs Pure Quantum**:
   - Is pure quantum necessary for scientific validity?
   - Or is demonstrating QFT speedup sufficient?
   - What's the publication strategy?

3. **Hardware Access**:
   - Target IBM Quantum (up to 127 qubits available)
   - Consider IonQ for higher fidelity
   - Timeline for hardware experiments?

4. **Validation Criteria**:
   - What error threshold is acceptable vs classical?
   - How to handle quantum sampling noise?
   - Need experimental CTEM data for comparison?

---

## Next Steps

### This Week:
1. Review this roadmap and prioritize goals
2. Decide: Hybrid QFT or Pure Quantum approach?
3. Set up `src/quscope/ctem/` directory structure
4. Extract working classical code into `classical/` module

### Next Week:
1. Implement quantum fftshift to remove `np.fft.fftshift`
2. Design quantum k² arithmetic circuit
3. Write unit tests for QFT correctness
4. Benchmark QFT vs FFT performance

### This Month:
1. Complete hybrid implementation (all quantum transforms)
2. Begin pure quantum phase grating design
3. Write documentation and theory section
4. Prepare for paper submission (target: arxiv + journal)

---

## Success Metrics

- ✅ **Code Quality**: All tests pass, documentation complete
- ✅ **Scientific Rigor**: Results match Kirkland within 1%
- ✅ **Quantum Validation**: QFT verified against FFT
- ✅ **Performance**: Circuit depth < 10,000 for 8-qubit system
- ✅ **Reproducibility**: Other groups can replicate results
- ✅ **Publication**: Accepted in peer-reviewed journal

---

## Resources & References

### Key Papers:
1. Kirkland (2010) - Advanced Computing in Electron Microscopy (Bible)
2. Quantum Image Processing reviews (quantum encoding methods)
3. Variational quantum eigensolver for materials (quantum chemistry context)
4. Quantum simulation of electron diffraction (if exists)

### Code References:
- Current notebook: `notebooks/sean's testing notebooks/quantum CTEM development.ipynb`
- Classical reference: Working implementation in cell #1
- Hybrid QFT: Implementation in cell #2
- Multislice: Implementation in cell #3

### Qiskit Documentation:
- QFT: https://qiskit.org/documentation/stubs/qiskit.circuit.library.QFT.html
- Quantum arithmetic: https://qiskit.org/documentation/apidoc/circuit_library.html
- Amplitude estimation: https://qiskit.org/documentation/stubs/qiskit.algorithms.AmplitudeEstimation.html

---

*Last Updated: October 2, 2025*
*Author: QuScope Development Team*
*Status: Active Development - v0.2.0 Planning*
