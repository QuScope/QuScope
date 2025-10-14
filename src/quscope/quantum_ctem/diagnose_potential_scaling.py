#!/usr/bin/env python3
"""
Diagnostic script to analyze potential scaling between quantum and classical methods.
"""

import numpy as np
import matplotlib.pyplot as plt
from ase.build import mx2
import abtem

try:
    from .sample_potential_converter import SamplePotentialConverter
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from sample_potential_converter import SamplePotentialConverter


def diagnose_potential_scaling():
    """Diagnose potential scaling issues."""
    
    print("=" * 70)
    print("POTENTIAL SCALING DIAGNOSTIC")
    print("=" * 70)
    
    # Create MoS₂ structure with orthogonal cell (critical!)
    print("\n[1/5] Creating MoS₂ structure...")
    atoms = mx2(formula='MoS2', kind='2H', a=3.18, thickness=3.19, vacuum=2.0)
    atoms = abtem.orthogonalize_cell(atoms) * (3, 2, 1)
    
    n_mo = len([a for a in atoms if a.symbol == 'Mo'])
    n_s = len([a for a in atoms if a.symbol == 'S'])
    print(f"  ✓ Created: {len(atoms)} atoms (Mo: {n_mo}, S: {n_s})")
    
    # Parameters
    voltage = 200e3  # V
    grid_size = 256
    pixel_size = 0.1  # Angstrom
    
    # Calculate quantum potential
    print("\n[2/5] Calculating quantum potential (Kirkland)...")
    converter = SamplePotentialConverter(voltage)
    V_quantum = converter.atoms_to_potential(atoms, grid_size, pixel_size)
    
    print(f"  Quantum potential:")
    print(f"    Min: {V_quantum.min():.6e} V·Å")
    print(f"    Max: {V_quantum.max():.6e} V·Å")
    print(f"    Mean: {V_quantum.mean():.6e} V·Å")
    print(f"    Std: {V_quantum.std():.6e} V·Å")
    
    # Calculate phase shift manually
    from scipy.constants import h, m_e, e
    wavelength = converter.wavelength
    sigma = (2 * np.pi * m_e * e * wavelength * 1e-10) / h**2
    phase_quantum = sigma * V_quantum / (1e20)
    
    print(f"\n  Phase shift (quantum):")
    print(f"    Max: {np.abs(phase_quantum).max():.6e} rad")
    print(f"    Mean: {np.abs(phase_quantum).mean():.6e} rad")
    print(f"    WPOA valid: {np.abs(phase_quantum).max() < 0.5}")
    print(f"    Interaction parameter σ: {sigma:.6e} rad/(V·Å)")
    
    stats = {'phase_shift_max': np.abs(phase_quantum).max(), 
             'phase_shift_mean': np.abs(phase_quantum).mean(),
             'wpoa_valid': np.abs(phase_quantum).max() < 0.5,
             'sigma': sigma}
    
    # Calculate classical potential (abTEM)
    print("\n[3/5] Calculating classical potential (abTEM)...")
    potential_abtem = abtem.Potential(
        atoms,
        sampling=pixel_size,
        gpts=(grid_size, grid_size),
        projection='infinite'
    )
    V_classical = np.array(potential_abtem.project().array)
    
    print(f"  Classical potential:")
    print(f"    Min: {V_classical.min():.6e} V·Å")
    print(f"    Max: {V_classical.max():.6e} V·Å")
    print(f"    Mean: {V_classical.mean():.6e} V·Å")
    print(f"    Std: {V_classical.std():.6e} V·Å")
    
    # Calculate ratio
    print("\n[4/5] Analyzing scaling ratio...")
    
    # Find ratio in non-zero regions
    mask = V_classical > 0.01 * V_classical.max()
    ratio = V_quantum[mask] / V_classical[mask]
    
    print(f"  Scaling ratio (quantum/classical):")
    print(f"    Min: {ratio.min():.6e}")
    print(f"    Max: {ratio.max():.6e}")
    print(f"    Mean: {ratio.mean():.6e}")
    print(f"    Median: {np.median(ratio):.6e}")
    print(f"    Std: {ratio.std():.6e}")
    
    # Expected values
    print("\n  Expected phase shifts for MoS₂:")
    print(f"    Typical phase shift: 0.5-2.0 rad")
    print(f"    For WPOA validity: phase < π/2 = 1.571 rad")
    
    # Scaling factor needed
    target_phase = 1.0  # rad
    current_phase = stats['phase_shift_max']
    needed_scaling = target_phase / current_phase if current_phase > 0 else np.inf
    
    print(f"\n  Scaling correction needed:")
    print(f"    Current max phase: {current_phase:.6e} rad")
    print(f"    Target phase: {target_phase:.3f} rad")
    print(f"    Scaling factor: {needed_scaling:.6e}")
    
    # Check if it's reasonable
    if needed_scaling > 1e10:
        print(f"    ⚠ WARNING: Scaling factor too large (> 10^10)")
        print(f"    This suggests fundamental issue in potential calculation")
    elif needed_scaling > 100:
        print(f"    ⚠ WARNING: Scaling factor > 100")
        print(f"    Consider reviewing Kirkland parametrization")
    else:
        print(f"    ✓ Scaling factor seems reasonable")
    
    # Visualize
    print("\n[5/5] Generating diagnostic plots...")
    
    fig = plt.figure(figsize=(18, 12))
    
    # Row 1: Potentials
    ax1 = plt.subplot(3, 3, 1)
    im1 = ax1.imshow(V_quantum, cmap='viridis')
    ax1.set_title(f'Quantum Potential\nMax: {V_quantum.max():.2e} V·Å', fontweight='bold')
    ax1.axis('off')
    plt.colorbar(im1, ax=ax1, label='V·Å')
    
    ax2 = plt.subplot(3, 3, 2)
    im2 = ax2.imshow(V_classical, cmap='viridis')
    ax2.set_title(f'Classical Potential (abTEM)\nMax: {V_classical.max():.2e} V·Å', fontweight='bold')
    ax2.axis('off')
    plt.colorbar(im2, ax=ax2, label='V·Å')
    
    ax3 = plt.subplot(3, 3, 3)
    ratio_2d = np.zeros_like(V_quantum)
    ratio_2d[mask] = ratio
    im3 = ax3.imshow(np.log10(ratio_2d + 1e-30), cmap='RdBu_r', vmin=-12, vmax=-6)
    ax3.set_title(f'Log10 Ratio (Q/C)\nMedian: {np.median(ratio):.2e}', fontweight='bold')
    ax3.axis('off')
    plt.colorbar(im3, ax=ax3, label='log10(ratio)')
    
    # Row 2: Line profiles
    center = grid_size // 2
    
    ax4 = plt.subplot(3, 3, 4)
    ax4.plot(V_quantum[center, :], 'b-', label='Quantum', linewidth=2)
    ax4.plot(V_classical[center, :], 'r-', label='Classical', linewidth=2)
    ax4.set_xlabel('X pixel')
    ax4.set_ylabel('Potential (V·Å)')
    ax4.set_title('Line Profile (Y = center)', fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    ax5 = plt.subplot(3, 3, 5)
    ax5.semilogy(V_quantum[center, :], 'b-', label='Quantum', linewidth=2)
    ax5.semilogy(V_classical[center, :], 'r-', label='Classical', linewidth=2)
    ax5.set_xlabel('X pixel')
    ax5.set_ylabel('Potential (V·Å)')
    ax5.set_title('Line Profile (log scale)', fontweight='bold')
    ax5.legend()
    ax5.grid(True, alpha=0.3, which='both')
    
    ax6 = plt.subplot(3, 3, 6)
    valid_idx = (V_classical[center, :] > 0) & (V_quantum[center, :] > 0)
    x_valid = np.arange(grid_size)[valid_idx]
    ratio_line = V_quantum[center, valid_idx] / V_classical[center, valid_idx]
    ax6.semilogy(x_valid, ratio_line, 'g-', linewidth=2)
    ax6.axhline(np.median(ratio), color='k', linestyle='--', label=f'Median: {np.median(ratio):.2e}')
    ax6.set_xlabel('X pixel')
    ax6.set_ylabel('Ratio (Q/C)')
    ax6.set_title('Scaling Ratio (log scale)', fontweight='bold')
    ax6.legend()
    ax6.grid(True, alpha=0.3, which='both')
    
    # Row 3: Histograms and statistics
    ax7 = plt.subplot(3, 3, 7)
    ax7.hist(V_quantum.flatten(), bins=100, alpha=0.7, label='Quantum', color='blue')
    ax7.hist(V_classical.flatten(), bins=100, alpha=0.7, label='Classical', color='red')
    ax7.set_xlabel('Potential (V·Å)')
    ax7.set_ylabel('Count')
    ax7.set_title('Potential Distributions', fontweight='bold')
    ax7.legend()
    ax7.set_yscale('log')
    ax7.grid(True, alpha=0.3)
    
    ax8 = plt.subplot(3, 3, 8)
    ax8.hist(np.log10(ratio + 1e-30), bins=50, color='green', alpha=0.7)
    ax8.axvline(np.log10(np.median(ratio)), color='k', linestyle='--', linewidth=2,
                label=f'Median: {np.median(ratio):.2e}')
    ax8.set_xlabel('Log10(Ratio)')
    ax8.set_ylabel('Count')
    ax8.set_title('Ratio Distribution', fontweight='bold')
    ax8.legend()
    ax8.grid(True, alpha=0.3)
    
    # Summary text
    ax9 = plt.subplot(3, 3, 9)
    ax9.axis('off')
    
    summary_text = f"""
SCALING ANALYSIS SUMMARY
{'=' * 35}

Quantum Potential:
  Max: {V_quantum.max():.3e} V·Å
  Mean: {V_quantum.mean():.3e} V·Å

Classical Potential:
  Max: {V_classical.max():.3e} V·Å
  Mean: {V_classical.mean():.3e} V·Å

Ratio (Q/C):
  Median: {np.median(ratio):.3e}
  Mean: {ratio.mean():.3e}

Phase Shift:
  Max: {stats['phase_shift_max']:.3e} rad
  Target: 1.0 rad
  
Scaling Factor Needed:
  {needed_scaling:.3e}
  
Status:
"""
    
    if stats['wpoa_valid']:
        summary_text += "  ✓ WPOA valid"
    else:
        summary_text += "  ✗ WPOA invalid"
    
    if abs(np.log10(needed_scaling)) < 2:
        summary_text += "\n  ✓ Scaling reasonable"
    else:
        summary_text += "\n  ⚠ Scaling problematic"
    
    ax9.text(0.1, 0.5, summary_text, fontsize=10, family='monospace',
             verticalalignment='center')
    
    plt.suptitle('MoS₂ Potential Scaling Diagnostic (200 kV)', 
                 fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    save_path = 'potential_scaling_diagnostic.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {save_path}")
    
    plt.show()
    
    # Recommendations
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    
    if needed_scaling > 1e6:
        print("\n⚠ CRITICAL: Potential scaling off by > 6 orders of magnitude")
        print("\nLikely causes:")
        print("  1. Missing unit conversion in Kirkland formula")
        print("  2. Incorrect parametrization (a_i, b_i values)")
        print("  3. Wrong formula for projected potential")
        print("\nSuggested fixes:")
        print("  1. Verify Kirkland parameters against original paper")
        print("  2. Check unit conversions (eV vs V, Å vs nm)")
        print("  3. Compare single-atom potential with literature")
        print("  4. Consider using abTEM potential directly in quantum sim")
    
    elif needed_scaling > 100:
        print("\n⚠ WARNING: Potential scaling off by 2-6 orders of magnitude")
        print("\nSuggested actions:")
        print("  1. Review normalization factors")
        print("  2. Verify grid spacing usage")
        print("  3. Compare with single-atom test case")
    
    else:
        print("\n✓ Potential scaling appears reasonable")
        print("\nNext steps:")
        print("  1. Apply scaling factor to quantum potential")
        print("  2. Re-run validation")
        print("  3. Check metrics improvement")
    
    print("\n" + "=" * 70)
    
    return V_quantum, V_classical, ratio


if __name__ == '__main__':
    V_quantum, V_classical, ratio = diagnose_potential_scaling()
