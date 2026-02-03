"""Visualization utilities for MoS2 workflow.

This module provides abTEM-compatible structure building and visualization
for MoS2 and other 2D materials.

Example:
    >>> atoms = build_mos2(nx=5, ny=3, orthogonalize=True)
    >>> show_atoms(atoms, legend=True)
"""

from typing import Tuple, Optional, List, Union
from dataclasses import dataclass

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
import numpy as np
from ase.build import mx2
from ase import Atoms


def orthogonalize_cell(atoms: Atoms) -> Atoms:
    """
    Convert hexagonal cell to orthogonal (rectangular) cell.

    This is equivalent to abTEM's orthogonalize_cell function.
    For hexagonal cells, creates a rectangular supercell that
    preserves periodicity.

    Args:
        atoms: ASE Atoms object with hexagonal cell

    Returns:
        ASE Atoms object with orthogonal cell
    """
    cell = atoms.get_cell()

    # Check if already orthogonal
    angles = atoms.cell.angles()
    if np.allclose(angles, [90, 90, 90], atol=1):
        return atoms.copy()

    # For hexagonal cell (gamma = 120°), create orthogonal supercell
    # The transformation is: new_b = a + 2*b for 120° angle
    a = cell[0]
    b = cell[1]
    c = cell[2]

    # New orthogonal cell vectors
    new_a = a
    new_b = a + 2 * b  # This makes it orthogonal
    new_c = c

    # Create new cell
    new_cell = np.array([new_a, new_b, new_c])

    # We need to replicate atoms to fill the new cell
    # For the hexagonal -> orthogonal transformation, we need 2x in b direction
    atoms_ortho = atoms.repeat((1, 2, 1))
    atoms_ortho.set_cell(new_cell)
    atoms_ortho.wrap()

    return atoms_ortho


def build_mos2(
    nx: int = 3,
    ny: int = 2,
    vacuum: float = 2.0,
    orthogonalize: bool = True,
    kind: str = "2H"
) -> Atoms:
    """
    Build a MoS2 structure using ASE's mx2 helper.

    This function mimics abTEM's approach:
        atoms = ase.build.mx2(vacuum=2)
        atoms = abtem.orthogonalize_cell(atoms)
        atoms = atoms * (5, 3, 1)

    Args:
        nx: Number of unit cells in x direction
        ny: Number of unit cells in y direction
        vacuum: Vacuum padding in z direction (Å)
        orthogonalize: Convert hexagonal cell to orthogonal
        kind: Crystal structure type ("2H" or "1T")

    Returns:
        ASE Atoms object

    Example:
        >>> atoms = build_mos2(nx=5, ny=3, orthogonalize=True)
        >>> print(f"Cell: {atoms.cell.lengths()[:2].round(2)} Å")
        >>> print(f"Atoms: {len(atoms)}")
    """
    # Build base MoS2 unit cell
    atoms = mx2(formula="MoS2", kind=kind, vacuum=vacuum)

    # Orthogonalize if requested (like abTEM)
    if orthogonalize:
        atoms = orthogonalize_cell(atoms)

    # Create supercell
    atoms = atoms * (nx, ny, 1)

    return atoms


# Element colors matching abTEM style
ELEMENT_COLORS = {
    "Mo": "#20B2AA",  # Teal/Light sea green
    "S": "#FFD700",   # Gold/Yellow
    "C": "#808080",   # Gray
    "N": "#0000FF",   # Blue
    "O": "#FF0000",   # Red
    "H": "#FFFFFF",   # White
    "Si": "#A0522D",  # Sienna
    "Au": "#FFD700",  # Gold
    "Ag": "#C0C0C0",  # Silver
    "Cu": "#B87333",  # Copper
    "Fe": "#A52A2A",  # Brown
}

# Covalent radii for atom sizes (Å)
COVALENT_RADII = {
    "Mo": 1.54,
    "S": 1.05,
    "C": 0.77,
    "N": 0.75,
    "O": 0.73,
    "H": 0.31,
    "Si": 1.11,
    "Au": 1.36,
    "Ag": 1.45,
    "Cu": 1.32,
    "Fe": 1.26,
}


def show_atoms(
    atoms: Atoms,
    plane: str = "xy",
    ax: Optional[plt.Axes] = None,
    title: Optional[str] = None,
    legend: bool = False,
    show_cell: bool = True,
    scale: float = 0.5,
    figsize: Tuple[float, float] = (8, 6),
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Visualize atomic structure similar to abTEM's show_atoms.

    Args:
        atoms: ASE Atoms object
        plane: Projection plane ("xy" for beam view, "xz" for side view)
        ax: Matplotlib axes (creates new figure if None)
        title: Plot title
        legend: Show element legend
        show_cell: Show unit cell box
        scale: Atom size scaling factor
        figsize: Figure size if creating new figure

    Returns:
        Tuple of (figure, axes)

    Example:
        >>> atoms = build_mos2(nx=5, ny=3)
        >>> fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        >>> show_atoms(atoms, plane="xy", ax=ax1, title="Beam view")
        >>> show_atoms(atoms, plane="xz", ax=ax2, title="Side view", legend=True)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()

    positions = atoms.get_positions()
    symbols = atoms.get_chemical_symbols()
    cell = atoms.get_cell()

    # Determine axis indices based on plane
    plane_map = {
        "xy": (0, 1, "x", "y"),
        "xz": (0, 2, "x", "z"),
        "yz": (1, 2, "y", "z"),
    }

    if plane not in plane_map:
        raise ValueError(f"plane must be one of {list(plane_map.keys())}")

    idx1, idx2, xlabel, ylabel = plane_map[plane]

    # Get unique elements for consistent ordering
    unique_elements = list(dict.fromkeys(symbols))

    # Plot atoms by element (for proper z-ordering and legend)
    legend_handles = []

    for element in unique_elements:
        mask = np.array(symbols) == element
        pos = positions[mask]

        color = ELEMENT_COLORS.get(element, "#888888")
        radius = COVALENT_RADII.get(element, 1.0) * scale

        # Plot atoms
        scatter = ax.scatter(
            pos[:, idx1],
            pos[:, idx2],
            s=radius * 500,  # Scale for visibility
            c=color,
            edgecolors="black",
            linewidths=0.5,
            zorder=2,
            label=element,
        )

        if legend:
            legend_handles.append(
                plt.scatter([], [], s=100, c=color, edgecolors="black",
                           linewidths=0.5, label=element)
            )

    # Show unit cell box
    if show_cell:
        # Get cell vectors for the projection plane
        cell_vec1 = cell[idx1]
        cell_vec2 = cell[idx2] if idx2 < 3 else np.zeros(3)

        # Create cell rectangle
        cell_corners = np.array([
            [0, 0],
            [cell[0, idx1], cell[0, idx2]],
            [cell[0, idx1] + cell[1, idx1], cell[0, idx2] + cell[1, idx2]],
            [cell[1, idx1], cell[1, idx2]],
            [0, 0],  # Close the box
        ])

        ax.plot(cell_corners[:, 0], cell_corners[:, 1],
                'k-', linewidth=1.5, zorder=1)

    # Set labels and appearance
    ax.set_xlabel(f"{xlabel} [Å]")
    ax.set_ylabel(f"{ylabel} [Å]")
    ax.set_aspect("equal")

    if title:
        ax.set_title(title)

    if legend:
        ax.legend(loc="upper right", framealpha=0.9)

    # Set axis limits with padding
    extent = cell.lengths()
    padding = 0.1 * max(extent[idx1], extent[idx2])
    ax.set_xlim(-padding, extent[idx1] + padding)
    ax.set_ylim(-padding, extent[idx2] + padding)

    return fig, ax


def show_atoms_dual_view(
    atoms: Atoms,
    figsize: Tuple[float, float] = (12, 5),
    save_path: Optional[str] = None,
) -> Tuple[plt.Figure, Tuple[plt.Axes, plt.Axes]]:
    """
    Show beam view and side view of atoms (like abTEM).

    Args:
        atoms: ASE Atoms object
        figsize: Figure size
        save_path: Path to save figure

    Returns:
        Tuple of (figure, (ax_beam, ax_side))

    Example:
        >>> atoms = build_mos2(nx=5, ny=3)
        >>> fig, (ax1, ax2) = show_atoms_dual_view(atoms)
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    show_atoms(atoms, plane="xy", ax=ax1, title="Beam view")
    show_atoms(atoms, plane="xz", ax=ax2, title="Side view", legend=True)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig, (ax1, ax2)


# ============================================================================
# Scan Types (similar to abTEM)
# ============================================================================

@dataclass
class GridScan:
    """
    Uniformly spaced 2D grid of probe positions.

    Similar to abTEM's GridScan.

    Attributes:
        start: Start position (x, y) in Å or as fraction of extent
        end: End position (x, y) in Å or as fraction of extent
        gpts: Number of grid points (nx, ny) or single int for square
        fractional: If True, start/end are fractions of extent
        endpoint: Include endpoint in scan

    Example:
        >>> scan = GridScan(start=(0, 0), end=(10, 10), gpts=(50, 50))
        >>> positions = scan.get_positions()
    """
    start: Tuple[float, float] = (0.0, 0.0)
    end: Tuple[float, float] = (1.0, 1.0)
    gpts: Union[int, Tuple[int, int]] = 50
    fractional: bool = False
    endpoint: bool = True

    def get_positions(self, extent: Optional[Tuple[float, float]] = None) -> np.ndarray:
        """
        Get scan positions as (N, 2) array.

        Args:
            extent: Field of view (x, y) if using fractional coordinates

        Returns:
            Array of shape (n_positions, 2)
        """
        if isinstance(self.gpts, int):
            nx, ny = self.gpts, self.gpts
        else:
            nx, ny = self.gpts

        start = np.array(self.start)
        end = np.array(self.end)

        if self.fractional and extent is not None:
            start = start * np.array(extent)
            end = end * np.array(extent)

        x = np.linspace(start[0], end[0], nx, endpoint=self.endpoint)
        y = np.linspace(start[1], end[1], ny, endpoint=self.endpoint)

        xx, yy = np.meshgrid(x, y)
        positions = np.column_stack([xx.ravel(), yy.ravel()])

        return positions

    def add_to_axes(
        self,
        ax: plt.Axes,
        extent: Optional[Tuple[float, float]] = None,
        color: str = "red",
        marker: str = ".",
        markersize: float = 2,
        alpha: float = 0.5,
    ):
        """Add scan positions to existing axes."""
        positions = self.get_positions(extent)
        ax.scatter(positions[:, 0], positions[:, 1],
                  c=color, s=markersize, alpha=alpha, marker=marker)


@dataclass
class LineScan:
    """
    Uniformly spaced probe positions along a line.

    Similar to abTEM's LineScan.

    Attributes:
        start: Start position (x, y)
        end: End position (x, y)
        gpts: Number of points along line
        fractional: If True, coordinates are fractions of extent
        endpoint: Include endpoint

    Example:
        >>> line_scan = LineScan(
        ...     start=(0.2, 0.0),
        ...     end=(0.2, 1.0),
        ...     gpts=50,
        ...     fractional=True,
        ...     endpoint=False
        ... )
    """
    start: Tuple[float, float]
    end: Tuple[float, float]
    gpts: int = 50
    fractional: bool = False
    endpoint: bool = True

    def get_positions(self, extent: Optional[Tuple[float, float]] = None) -> np.ndarray:
        """Get scan positions as (N, 2) array."""
        start = np.array(self.start)
        end = np.array(self.end)

        if self.fractional and extent is not None:
            start = start * np.array(extent)
            end = end * np.array(extent)

        t = np.linspace(0, 1, self.gpts, endpoint=self.endpoint)
        positions = start + np.outer(t, end - start)

        return positions

    def add_to_axes(
        self,
        ax: plt.Axes,
        extent: Optional[Tuple[float, float]] = None,
        color: str = "red",
        linewidth: float = 2,
        linestyle: str = "-",
    ):
        """Add scan line to existing axes."""
        positions = self.get_positions(extent)
        ax.plot(positions[:, 0], positions[:, 1],
               color=color, linewidth=linewidth, linestyle=linestyle)
        # Mark start and end
        ax.scatter(positions[0, 0], positions[0, 1],
                  c=color, s=50, marker="o", zorder=10)
        ax.scatter(positions[-1, 0], positions[-1, 1],
                  c=color, s=50, marker="s", zorder=10)


@dataclass
class CustomScan:
    """
    Arbitrary probe positions.

    Attributes:
        positions: Array of shape (N, 2) with (x, y) positions
    """
    positions: np.ndarray

    def get_positions(self, extent: Optional[Tuple[float, float]] = None) -> np.ndarray:
        return self.positions

    def add_to_axes(
        self,
        ax: plt.Axes,
        extent: Optional[Tuple[float, float]] = None,
        color: str = "red",
        marker: str = "x",
        markersize: float = 20,
    ):
        """Add custom scan positions to axes."""
        ax.scatter(self.positions[:, 0], self.positions[:, 1],
                  c=color, s=markersize, marker=marker, zorder=10)


def plot_structure_caxis(atoms, show=True, save_path: str = None):
    """Simple top-down plot of atomic positions (c-axis view).

    DEPRECATED: Use show_atoms(atoms, plane="xy") instead.
    """
    return show_atoms(atoms, plane="xy", title="MoS2 top-down (c-axis)")


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
