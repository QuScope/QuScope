# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
