MoS2 CTEM Simulation Methods

This document summarizes methods used to generate the MoS2 CTEM simulations for the paper.

References
- Kirkland, EA. Advanced Computing in Electron Microscopy. (Use the appropriate edition and section for WPOA/multislice).

Overview
- Classical CTEM: We use abTEM's Potential and multislice to compute the multislice exit wave and intensity. The abTEM potential is constructed from ASE Atoms produced by `quscope.mos2_workflow.build_mos2`.
- Quantum mapping: The projected potential V(x,y) from `SamplePotentialConverter.atoms_to_potential` is used as the input to our quantum encoding and simulation pathway.

Reproducibility
- Use the provided `environment.yml` to create a reproducible conda environment named `quantum`. Note: NumPy is pinned to `<2` to remain compatible with abTEM (avoid runtime monkeypatches).

Commands
```bash
# create the environment (recommended: mamba)
mamba env create -f environment.yml -n quantum
conda activate quantum

# generate publication figures at 512px resolution
conda run -n quantum python scripts/run_paper_mos2.py
```

Notes
- abTEM may emit warnings about grid sampling if the provided grid parameters are overspecified; these do not affect correctness but can be silenced by matching sampling parameters.
- The code contains a fallback FFT-propagation if abTEM is unavailable; for publication we recommend using the abTEM multislice path with NumPy 1.x for exact reproducibility.
