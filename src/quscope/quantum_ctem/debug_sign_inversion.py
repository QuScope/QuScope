#!/usr/bin/env python3
"""
Debug Sign Inversion in Quantum TEM

Tests all possible sign combinations in:
1. Phase grating: exp(±iσV)
2. CTF: exp(±iχ)
3. Fresnel propagator: exp(±iπλz k²)

Goal: Find which sign(s) cause anti-correlation at specific voltages
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from quscope.quantum_ctem.quantum_simulation import QuantumTEMSimulator
from ase.build import mx2

def test_sign_combinations(voltage_kv=200.0, defocus_A=200.0):
    """
    Test all 8 combinations of signs (+/-) for:
    - Phase grating
    - CTF
    - Fresnel propagator
    
    Returns correlation with classical for each combination.
    """
    print(f"\n{'='*70}")
    print(f"TESTING SIGN COMBINATIONS at {voltage_kv} kV, defocus {defocus_A} Å")
    print(f"{'='*70}\n")
    
    # Create MoS2 structure
    atoms = mx2(formula='MoS2', kind='2H', a=3.18, thickness=3.19, 
                size=(3, 3, 1), vacuum=7.5)
    
    # Classical reference (abTEM)
    try:
        import abtem
        pot_classical = abtem.Potential(
            atoms,
            gpts=256,
            sampling=0.1,
            device='cpu',
            projection='infinite'
        ).build()
        
        probe_classical = abtem.PlaneWave(
            energy=voltage_kv * 1000,
            device='cpu'
        )
        
        waves_classical = probe_classical.multislice(pot_classical)
        
        # abTEM may return an object with .array or a dask array
        if hasattr(waves_classical, 'array'):
            arr = waves_classical.array
        else:
            arr = waves_classical

        if hasattr(arr, 'compute'):
            arr = arr.compute()

        # Ensure 2D
        if arr.ndim == 3:
            arr = arr[0]

        intensity_classical = np.abs(arr)**2
        print(f"✓ Classical reference computed")
        print(f"  Range: [{intensity_classical.min():.6e}, {intensity_classical.max():.6e}]")
        
    except ImportError:
        print("⚠ abTEM not available, using synthetic classical data")
        intensity_classical = None
    
    # Test all 8 combinations
    results = []
    
    sign_combinations = [
        ('+', '+', '+'),  # 0: all positive
        ('+', '+', '-'),  # 1: phase+, CTF+, fresnel-
        ('+', '-', '+'),  # 2: phase+, CTF-, fresnel+
        ('+', '-', '-'),  # 3: phase+, CTF-, fresnel-
        ('-', '+', '+'),  # 4: phase-, CTF+, fresnel+
        ('-', '+', '-'),  # 5: phase-, CTF+, fresnel-
        ('-', '-', '+'),  # 6: phase-, CTF-, fresnel+
        ('-', '-', '-'),  # 7: all negative
    ]
    
    print(f"\nTesting {len(sign_combinations)} combinations...")
    print(f"{'Combo':<8} {'Phase':<7} {'CTF':<7} {'Fresnel':<9} {'Pearson':<10} {'SSIM':<10}")
    print(f"{'-'*70}")
    
    for idx, (sign_phase, sign_ctf, sign_fresnel) in enumerate(sign_combinations):
        
        # Create simulator (we'll modify signs in the calculation)
        # Build simulation parameters dataclass
        from quscope.quantum_ctem.quantum_simulation import QuantumSimulationParameters

        params = QuantumSimulationParameters(
            acceleration_voltage=voltage_kv * 1000,
            grid_size=256,
            pixel_size=0.1,
            defocus=defocus_A,
            cs=1.0
        )

        sim = QuantumTEMSimulator(params)
        
        # Get potential and interaction constant
        V = sim.potential_converter.atoms_to_potential(
            atoms,
            params.grid_size,
            params.pixel_size
        )

        # Normalize potential to unit scale for sign testing
        V_norm = (V - V.min()) / (V.max() - V.min() + 1e-12)
        # Use normalized potential as unitless phase proxy (sign flips still meaningful)
        phase_proxy = V_norm
        
        # Apply phase grating with chosen sign
        psi_in = np.ones((256, 256), dtype=complex)
        if sign_phase == '+':
            phase_grating = np.exp(1j * phase_proxy)
        else:
            phase_grating = np.exp(-1j * phase_proxy)
        
        psi_after_phase = psi_in * phase_grating
        
        # Propagate to detector with Fresnel propagator
        psi_fft = np.fft.fft2(psi_after_phase)
        psi_fft_shifted = np.fft.fftshift(psi_fft)
        
        # Create k-space grid
        kx = np.fft.fftfreq(256, d=0.1)
        ky = np.fft.fftfreq(256, d=0.1)
        Kx, Ky = np.meshgrid(kx, ky)
        k2 = Kx**2 + Ky**2
        
        # Apply Fresnel propagator with chosen sign
        lam = sim.wavelength
        z = 0.0  # WPOA: no propagation distance
        if sign_fresnel == '+':
            fresnel = np.exp(1j * np.pi * lam * z * k2)
        else:
            fresnel = np.exp(-1j * np.pi * lam * z * k2)
        
        psi_fft_shifted = psi_fft_shifted * fresnel
        
        # Apply CTF (aberration function)
        # Build HamiltonianParameters and LensHamiltonian to compute chi
        from quscope.quantum_ctem.hamiltonian import HamiltonianParameters, LensHamiltonian

        ham_params = HamiltonianParameters(
            acceleration_voltage=params.acceleration_voltage,
            wavelength=sim.wavelength,
            grid_size_x=params.grid_size,
            grid_size_y=params.grid_size,
            pixel_size=params.pixel_size
        )

        aberrations = {'defocus': params.defocus, 'cs': params.cs}
        lens = LensHamiltonian(ham_params, aberrations)
        chi = lens.chi
        if sign_ctf == '+':
            ctf = np.exp(1j * chi)
        else:
            ctf = np.exp(-1j * chi)
        
        psi_fft_shifted = psi_fft_shifted * ctf
        
        # Transform back
        psi_fft = np.fft.ifftshift(psi_fft_shifted)
        psi_out = np.fft.ifft2(psi_fft)
        
        # Calculate intensity
        intensity_quantum = np.abs(psi_out)**2
        
        # Compare with classical
        if intensity_classical is not None:
            # Normalize both to [0, 1]
            def normalize(I):
                return (I - I.min()) / (I.max() - I.min() + 1e-10)
            
            I_q_norm = normalize(intensity_quantum)
            I_c_norm = normalize(intensity_classical)
            
            # Calculate metrics
            pearson = np.corrcoef(I_q_norm.flat, I_c_norm.flat)[0, 1]
            
            # SSIM (simplified)
            mean_q = I_q_norm.mean()
            mean_c = I_c_norm.mean()
            std_q = I_q_norm.std()
            std_c = I_c_norm.std()
            cov = np.mean((I_q_norm - mean_q) * (I_c_norm - mean_c))
            
            C1 = (0.01)**2
            C2 = (0.03)**2
            ssim = ((2*mean_q*mean_c + C1) * (2*cov + C2)) / \
                   ((mean_q**2 + mean_c**2 + C1) * (std_q**2 + std_c**2 + C2))
            
            results.append({
                'combo': idx,
                'sign_phase': sign_phase,
                'sign_ctf': sign_ctf,
                'sign_fresnel': sign_fresnel,
                'pearson': pearson,
                'ssim': ssim,
                'intensity_range': (intensity_quantum.min(), intensity_quantum.max())
            })
            
            # Print result
            status = "✓" if pearson > 0.5 else ("~" if pearson > 0 else "✗")
            print(f"{status} {idx:<6} {sign_phase:<7} {sign_ctf:<7} {sign_fresnel:<9} "
                  f"{pearson:>9.4f} {ssim:>9.4f}")
        else:
            print(f"  {idx:<6} {sign_phase:<7} {sign_ctf:<7} {sign_fresnel:<9} "
                  f"[no classical reference]")
    
    # Find best combination
    if results:
        print(f"\n{'='*70}")
        best = max(results, key=lambda x: x['pearson'])
        print(f"BEST COMBINATION:")
        print(f"  Combo {best['combo']}: "
              f"Phase={best['sign_phase']}, CTF={best['sign_ctf']}, Fresnel={best['sign_fresnel']}")
        print(f"  Pearson: {best['pearson']:.4f}")
        print(f"  SSIM: {best['ssim']:.4f}")
        
        # Check if current implementation matches best
        current = results[0]  # Combo 0 is all positive (current)
        if best['combo'] != 0:
            print(f"\n⚠ CURRENT IMPLEMENTATION (all +) is NOT optimal!")
            print(f"  Current Pearson: {current['pearson']:.4f}")
            print(f"  Best Pearson: {best['pearson']:.4f}")
            print(f"  Improvement: {best['pearson'] - current['pearson']:.4f}")
            
            print(f"\n🔧 RECOMMENDED FIX:")
            if best['sign_phase'] == '-':
                print(f"  1. Change phase grating: exp(-iσV) instead of exp(+iσV)")
            if best['sign_ctf'] == '-':
                print(f"  2. Change CTF: exp(-iχ) instead of exp(+iχ)")
            if best['sign_fresnel'] == '-':
                print(f"  3. Change Fresnel: exp(-iπλzk²) instead of exp(+iπλzk²)")
        else:
            print(f"\n✓ Current implementation uses optimal signs!")
    
    return results


def visualize_sign_test(voltage_kv=200.0, defocus_A=200.0):
    """
    Create visualization of best vs worst sign combinations.
    """
    print(f"\nGenerating visualization...")
    
    results = test_sign_combinations(voltage_kv, defocus_A)
    
    if not results:
        print("⚠ No results to visualize")
        return
    
    # Find best and worst
    best = max(results, key=lambda x: x['pearson'])
    worst = min(results, key=lambda x: x['pearson'])
    
    # Create summary plot
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle(f'Sign Combination Analysis\n{voltage_kv} kV, defocus={defocus_A} Å', 
                 fontsize=14, fontweight='bold')
    
    # Plot 1: Pearson correlation for all combinations
    ax = axes[0, 0]
    combos = [r['combo'] for r in results]
    pearsons = [r['pearson'] for r in results]
    colors = ['green' if p > 0.5 else ('orange' if p > 0 else 'red') for p in pearsons]
    ax.bar(combos, pearsons, color=colors, alpha=0.7, edgecolor='black')
    ax.axhline(y=0, color='black', linestyle='--', linewidth=1)
    ax.axhline(y=0.5, color='green', linestyle='--', linewidth=1, alpha=0.5)
    ax.set_xlabel('Sign Combination')
    ax.set_ylabel('Pearson Correlation')
    ax.set_title('Correlation vs Sign Combination')
    ax.grid(axis='y', alpha=0.3)
    
    # Annotate best and worst
    best_idx = best['combo']
    worst_idx = worst['combo']
    ax.annotate('BEST', xy=(best_idx, best['pearson']), 
                xytext=(best_idx, best['pearson'] + 0.2),
                ha='center', fontweight='bold', color='green',
                arrowprops=dict(arrowstyle='->', color='green'))
    ax.annotate('WORST', xy=(worst_idx, worst['pearson']), 
                xytext=(worst_idx, worst['pearson'] - 0.2),
                ha='center', fontweight='bold', color='red',
                arrowprops=dict(arrowstyle='->', color='red'))
    
    # Plot 2: SSIM for all combinations
    ax = axes[0, 1]
    ssims = [r['ssim'] for r in results]
    ax.bar(combos, ssims, color='steelblue', alpha=0.7, edgecolor='black')
    ax.axhline(y=0, color='black', linestyle='--', linewidth=1)
    ax.set_xlabel('Sign Combination')
    ax.set_ylabel('SSIM')
    ax.set_title('SSIM vs Sign Combination')
    ax.grid(axis='y', alpha=0.3)
    
    # Plot 3: Sign pattern of best combination
    ax = axes[1, 0]
    ax.text(0.5, 0.8, f"Best Combination (#{best['combo']})", 
            ha='center', fontsize=12, fontweight='bold')
    ax.text(0.5, 0.6, f"Phase grating: exp({best['sign_phase']}iσV)", 
            ha='center', fontsize=11, family='monospace')
    ax.text(0.5, 0.45, f"CTF: exp({best['sign_ctf']}iχ)", 
            ha='center', fontsize=11, family='monospace')
    ax.text(0.5, 0.3, f"Fresnel: exp({best['sign_fresnel']}iπλzk²)", 
            ha='center', fontsize=11, family='monospace')
    ax.text(0.5, 0.1, f"Pearson: {best['pearson']:.4f}", 
            ha='center', fontsize=11, fontweight='bold', color='green')
    ax.axis('off')
    
    # Plot 4: Sign pattern of current implementation
    ax = axes[1, 1]
    current = results[0]  # Combo 0 is all positive
    status = "✓ OPTIMAL" if current['combo'] == best['combo'] else "⚠ SUBOPTIMAL"
    color = 'green' if current['combo'] == best['combo'] else 'red'
    
    ax.text(0.5, 0.8, f"Current Implementation ({status})", 
            ha='center', fontsize=12, fontweight='bold', color=color)
    ax.text(0.5, 0.6, f"Phase grating: exp(+iσV)", 
            ha='center', fontsize=11, family='monospace')
    ax.text(0.5, 0.45, f"CTF: exp(+iχ)", 
            ha='center', fontsize=11, family='monospace')
    ax.text(0.5, 0.3, f"Fresnel: exp(+iπλzk²)", 
            ha='center', fontsize=11, family='monospace')
    ax.text(0.5, 0.1, f"Pearson: {current['pearson']:.4f}", 
            ha='center', fontsize=11, fontweight='bold', color=color)
    ax.axis('off')
    
    plt.tight_layout()
    
    # Save figure
    output_path = Path(__file__).parent.parent.parent.parent / 'sign_inversion_analysis.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    
    plt.show()


def main():
    """
    Main execution: test at problematic voltages.
    """
    print("="*70)
    print("SIGN INVERSION DEBUGGING")
    print("="*70)
    
    # Test at voltages where we saw issues
    print("\n" + "="*70)
    print("TEST 1: MoS₂ at 200 kV (Pearson = -0.32)")
    print("="*70)
    results_200kv = test_sign_combinations(voltage_kv=200.0, defocus_A=200.0)
    
    print("\n" + "="*70)
    print("TEST 2: hBN at 300 kV (Pearson = -0.50)")
    print("="*70)
    results_300kv = test_sign_combinations(voltage_kv=300.0, defocus_A=200.0)
    
    # Visualize
    visualize_sign_test(voltage_kv=200.0, defocus_A=200.0)
    
    print("\n" + "="*70)
    print("DEBUGGING COMPLETE")
    print("="*70)


if __name__ == '__main__':
    main()
