# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

STEM fixes found while validating the quantum STEM pipelines against abTEM on SrTiO3 [001]
(HAADF, ADF, ABF, BF and iDPC agree with abTEM to a correlation of 0.997-0.9994; see
`examples-applications`).

### Added
- `MoSe2` material (`get_material("mose2")`): 2H MoSe2 with a = 3.29 A and a Se-Se distance of 3.33 A.

### Changed (breaking)
- Python >= 3.11 (was 3.9). abTEM requires it and now provides the atomic potentials; 3.9 is end-of-life and 3.10 reaches it in October 2026.
- Atomic potentials now come from abTEM only, through the new `quscope.ctem.AtomicPotential`
  (`"kirkland"` or `"lobato"` parametrization, in V*Angstrom). QuScope no longer carries scattering-factor tables.
  abTEM and ASE are core dependencies now (`quscope[microscopy]` is kept as an empty extra).
- `WPOASimulator`, `MultisliceSimulator`, `simulations.WPO`, `simulations.Multislice`:
  the `params_file` / `kirkland_params_path` / `kirkland_params_file` arguments are replaced by
  `parametrization="kirkland"`.
- `SamplePotentialConverter(acceleration_voltage, parametrization="kirkland")`: `use_scattering_params`
  is gone. Potentials are in V*Angstrom (the old per-element `ELEMENT_SCALE` factors are gone).
- `Material.get_projected_potential(..., parametrization=None)`; materials carry a `parametrization` attribute.

### Removed
- `quscope.ctem.KirklandPotential`, `quscope.utils.kirkland` (`KirklandPotential`,
  `KIRKLAND_SCATTERING_FACTOR`), `kirkland.json`, the hand-typed `AtomicScatteringParams` /
  `SCATTERING_PARAMS` tables and `Material.get_scattering_params`, and the copy of the formula in
  `MultisliceSimulator`.

### Fixed
- Atomic potentials were 1.2 to 1.9 times larger than abTEM's Kirkland potentials for every element, with a
  different shape: the prefactor was a bare 14.4 instead of 4 pi^2 a0 e (the Bohr radius a0 was missing) and
  the Gaussian terms used the 3D form. Other constants were tuned to compensate, which is why the following
  changed together with the potentials:
  - `WPOASimulator` and `MultisliceSimulator` used an "empirically calibrated" sigma of 3.9e-4 at 200 kV; they now use
    the physical 7.29e-4 rad/(V*Angstrom).
  - `MultisliceSimulator` and `simulations.Multislice` multiplied the already z-projected potential by the slice
    thickness again; removed.
  - `SamplePotentialConverter` used the non-relativistic electron mass in sigma (5.24e-4 at 200 kV, 0.72x too small);
    it is relativistic now.
- `MultisliceSimulator.kirkland_potential_2d` silently used carbon for every element except Ga, As, Si and C
  (gold became carbon). All elements are supported.
- `run_stem`, `run_stem_multislice`: the `iDPC` image was the divergence of the centre-of-mass
  field (the Laplacian of the phase), not its integral. It is now the Fourier-space integral
  (`quantum_stem.integrate_dpc`), a phase image in radians. The centre-of-mass field is also
  returned as `DPC_x` / `DPC_y` [1/A].
- `run_stem`, `run_stem_multislice`: scan index `(i, j)` placed the probe at pixel
  `(i*step - N/2, j*step - N/2)`, so every image was displaced by half the field of view from
  the potential. The probe is now at `(i*step, j*step)`.
- STEM detector signals are fractions of the incident beam (unitary FFT); they were scaled by N^2.
- `run_stem_multislice`: with a 3D potential the result reported the default `n_slices` (4) in its
  metadata and description instead of the actual slice count.

## [0.2.1] - 2026-10-09

Physics fixes found while building the sister project [ptyqo](https://github.com/QuScope/ptyqo)
(quantum electron ptychography) on QuScope. Reference values: Kirkland, *Advanced Computing in
Electron Microscopy* (lambda = 0.02508 A, sigma = 7.288e-4 rad/(V A) at 200 kV).

### Fixed
- `QuantumWaveFunction`: x/y qubit labels now match the C-order flattening of `psi[x, y]`
  (y on the low qubits, x on the high qubits); the 2D QFT was applied to the wrong axis for
  non-square grids or single-axis gates.
- `HamiltonianParameters.interaction_constant`: relativistic mass (was the rest mass,
  5.24e-4 instead of 7.29e-4 rad/(V A) at 200 kV); now consistent with
  `quantum_ctem_circuit.interaction_constant`.
- `LensHamiltonian` and `FreeParticleHamiltonian`: spatial frequencies in 1/A as their formulas
  require (aberration phases and the Fresnel propagator were 4 pi^2 too large);
  `FreeParticleHamiltonian.energy` values unchanged. Affects `ctf_calculator`, `quantum_simulation`
  and the end-to-end workflows that use these classes.
- `QuantumPhaseGrating.apply`: applies exp(i sigma V) exactly as one `DiagonalGate` (was a
  barrier-only placeholder).
- `utils.constants.PhysicalConstants`: Kirkland wavelength (12.2643 / sqrt(V (1 + 0.97845e-6 V)),
  was 1.1% long) and interaction constant (was 0.53x); used by `simulations/wpo.py` and
  `simulations/multislice.py`.
- Notebook 08: `simulate_multislice(..., slice_thickness=...)` (was `dz=`), from the `dev-2` branch.
- Package version fallback string.

### Added
- `tests/quantum_ctem/test_v021_physics_fixes.py`: regression tests for the fixes above.
- README: papers, and the sister module ptyqo.

## [0.2.0] - 2026-07-15

v0.2.0 focuses on four validated quantum imaging pipelines: CTEM (WPOA),
CTEM multislice, STEM (WPOA), and STEM multislice.

### Added
- Quantum STEM Multislice implementation (`run_stem_multislice`, `build_probe_circuit`)
- Demonstration notebooks 10 (quantum CTEM) and 11 (quantum STEM)

### Changed
- Scope: quantum diffraction modes, frozen-phonon/TDS channels, and the
  Bloch-wave QPE eigensolver moved to the `dev` branch for a future release
- Rewrote README around the four available pipelines with verified examples
- Bump versions in packaging files to v0.2.0 and add quantum STEM imports
- Update authors, qiskit version (>= 2.0), dependencies, and installation instructions

### Fixed
- Relativistic wavelength: corrected gamma factor to 1 + eV/(2·m0·c²)
  (was off by −4% to −10% at 100–300 kV); interaction constant now matches
  literature values to <0.1%
- Fresnel propagator phase: corrected to −π·λ·Δz·k² with spatial-frequency
  grid (quantum vs classical multislice fidelity now 1.000000)
- Corrected formulas, DiagonalGate usage, and documentation for quantum CTEM circuit
- Fixed frequency grid usage (raw spatial frequencies, Kirkland convention)
  in CTF and propagator
- Fixed repository clone commands

### Documentation
- Major documentation restructuring for v0.2.0: quantum_ctem-focused API and notebook gallery
- Removed deprecated analysis, processing, and QML docs (will be reimplemented in future versions)
- Notebook sources ship without outputs; pre-executed reference copies retained
- Updated tutorials, notebooks, guides, and API docs

## [0.2.0] - 2026-03-12

### Added
- Quantum Bloch Wave implementation implementation using QPE
- Quantum Diffraction (WPOA, SAED, CBED, Kikuchi, nBD, EBSD modes)
- Quantum Frozen Phonons experimental implementation with 3 different executions
- Quantum STEM with HAADF/ADF/BF/iDPC multi-detectors
- Quantum Multislice Circuit using Fresnel propagator gates
- Demonstration notebooks 05-09 for new quantum implementations
- Test script for Si3N4

### Changed
- Updated quantum_ctem/__init__.py for all new modules
- Updated README.md to reflect v0.2.0 in title, documentation, developer credits, and arXiv paper

### Fixed
- Qiskit 2.x partial_trace API (standalone qiskit.quantum_info.partial_trace)
- QPE beam-count guard (MAX_SV_BEAMS=16) to prevent UnitaryGate hang
- ClassicalBlochWave.amplitude() returns complex (eliminates ComplexWarning)

## [0.1.2] - 2026-01-22

### Changed
- Updated README.md to reflect v0.1.1 in title and documentation

## [0.1.1] - 2026-01-22

### Added
- Quantum CTEM demonstration notebook (`examples/quantum_ctem.ipynb`)
- Quantum CTEM simulation modules with backends, materials, and workflows
- Comprehensive documentation for quantum CTEM methodology
- Backend abstraction layer (SimulatorBackend, IBMBackend)
- Material definitions (MoS2, Graphene) with atomic structure builders
- Quantum wavefunction encoding with amplitude encoding
- Momentum space operations using Quantum Fourier Transform
- Circuit optimization for IBM quantum hardware
- Performance benchmarking tools

### Changed
- Modernized package structure to use `pyproject.toml`
- Updated repository URLs to QuScope/QuScope organization
- Enhanced documentation with quantum CTEM examples
- Improved README with comprehensive examples and usage guide

### Fixed
- Package installation in editable mode
- Module import paths for quantum_ctem subpackages

### Documentation
- Added `docs/examples/quantum_ctem.rst` with detailed methodology
- Updated `docs/notebooks.rst` with quantum CTEM notebook description
- Enhanced quickstart guide with featured quantum CTEM example
- Updated repository structure documentation

## [0.1.0] - 2025-07-09

### Added
- Initial release of QuScope - Quantum Algorithm Microscopy package
- Quantum image processing capabilities with quantum encoding, segmentation, and filtering
- EELS (Electron Energy Loss Spectroscopy) analysis with quantum preprocessing and processing
- Quantum machine learning module with image encoding functionality
- Comprehensive documentation with Sphinx and Read the Docs integration
- Full pip installability with proper package structure
- Example notebooks demonstrating quantum microscopy workflows
- Unit tests and CI/CD pipeline with GitHub Actions

### Features
- Quantum state preparation and manipulation for image processing
- Advanced quantum algorithms for microscopy analysis
- Integration with Qiskit for quantum computing operations
- Modular architecture for extensibility
- Professional documentation and API reference

### Documentation
- Complete API documentation
- Installation and quickstart guides
- Tutorial notebooks with practical examples
- Read the Docs integration for online documentation

### Package Structure
- Source layout with proper Python packaging
- PyPI-ready configuration
- Comprehensive testing suite
- Development tools and pre-commit hooks
