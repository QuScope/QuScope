"""Visualization utilities for MoS2 workflow."""

from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
from ase.build import mx2


def build_mos2(nx: int = 3, ny: int = 2, vacuum: float = 10.0):
    """Build a MoS2 patch using ASE's mx2 helper."""
    atoms = mx2(vacuum=vacuum)
    atoms = atoms.repeat((nx, ny, 1))
    atoms.center()
    return atoms


def plot_structure_caxis(atoms, show=True, save_path: str = None):
    """Simple top-down plot of atomic positions (c-axis view)."""
    pos = atoms.get_positions()
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(pos[:, 0], pos[:, 1], s=40, c="tab:orange", edgecolor="k")
    ax.set_xlabel("x (Å)")
    ax.set_ylabel("y (Å)")
    ax.set_aspect("equal")
    ax.set_title("MoS2 top-down (c-axis)")
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
    if show:
        plt.show()
    return fig, ax


def compare_projected_potentials(
    V_quantum: np.ndarray,
    V_classical: np.ndarray,
    sampling: float = 0.1,
    save_path=None,
):
    """Quick comparison plot of two projected potentials."""
    import numpy as np

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    extent = [0, V_quantum.shape[1] * sampling, 0, V_quantum.shape[0] * sampling]
    im0 = axes[0].imshow(V_quantum, origin="lower", extent=extent, cmap="viridis")
    axes[0].set_title("Quantum potential")
    plt.colorbar(im0, ax=axes[0], fraction=0.046)
    im1 = axes[1].imshow(V_classical, origin="lower", extent=extent, cmap="viridis")
    axes[1].set_title("Classical potential")
    plt.colorbar(im1, ax=axes[1], fraction=0.046)
    im2 = axes[2].imshow(
        np.abs(V_quantum - V_classical), origin="lower", extent=extent, cmap="inferno"
    )
    axes[2].set_title("Absolute difference")
    plt.colorbar(im2, ax=axes[2], fraction=0.046)
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.show()
    return fig
