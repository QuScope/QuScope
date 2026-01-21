#!/usr/bin/env python3
"""Run a quick MoS2 potential conversion test using the SamplePotentialConverter.

This script mirrors the quick workflow shown in the screenshot: it calls
ase.build.mx2(...) to create a MoS2 monolayer, tiles it, then converts the
structure to a 2D projected potential and saves a visualization.
"""

from __future__ import annotations

import os

from ase import build
from sample_potential_converter import SamplePotentialConverter


def main():
    print("MoS2 potential conversion test")
    print("=" * 60)

    # Build a MoS2 monolayer using ASE's mx2 builder (matches the notebook)
    print("[1/4] Building MoS2 unit and tiling...")
    atoms = build.mx2(vacuum=5.0)
    # Do NOT pre-repeat the cell here. The converter's tile_to_fill=True
    # behavior will tile the unit cell to fill the requested field-of-view.
    # Pre-repeating can interact with the tiling math and create partial
    # coverage or offsets (observed as an empty corner). If you already
    # want to supply a repeated supercell, pass tile_to_fill=False below.
    atoms.center()
    print(f"✓ Created MoS2 with {len(atoms)} atoms")

    # Initialize converter
    print("[2/4] Initializing SamplePotentialConverter...")
    converter = SamplePotentialConverter(acceleration_voltage=200e3)
    print(f"✓ Converter initialized — wavelength: {converter.wavelength:.5f} Å")

    # Convert to potential
    print("[3/4] Converting atoms to projected potential (256×256, 0.05 Å pix)...")
    grid_size = 256
    pixel_size = 0.05
    V = converter.atoms_to_potential(atoms, grid_size=grid_size, pixel_size=pixel_size)
    print(
        f"✓ Potential calculated — shape: {V.shape}, range: [{V.min():.4e}, {V.max():.4e}] V"
    )

    # Calculate stats
    print("[4/4] Calculating statistics and saving visualization...")
    stats = converter.calculate_sample_statistics(
        atoms, grid_size=grid_size, pixel_size=pixel_size
    )
    for k, v in stats.items():
        print(f"  {k}: {v}")

    out_png = os.path.join(os.getcwd(), "sample_potential_mos2.png")
    converter.visualize_potential(
        atoms, grid_size=grid_size, pixel_size=pixel_size, save_path=out_png
    )

    print("\nDone.")


if __name__ == "__main__":
    main()
