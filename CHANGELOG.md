# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
