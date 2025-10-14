"""
Visualization Tools for Performance Benchmarking

Creates publication-quality plots and visualizations for benchmark results.

Week 3 Task 1.7: Performance Benchmarking

Author: QuScope Development Team
Date: October 5, 2025
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from typing import List, Dict, Optional
from pathlib import Path

from .performance_benchmarking import BenchmarkResult


class BenchmarkVisualizer:
    """
    Create visualizations for benchmark results.
    
    Example:
        >>> from quscope.quantum_ctem import PerformanceBenchmark, BenchmarkVisualizer
        >>> 
        >>> # Run benchmarks
        >>> benchmark = PerformanceBenchmark()
        >>> results = benchmark.run_scaling_analysis([2, 3, 4, 5])
        >>> 
        >>> # Visualize
        >>> visualizer = BenchmarkVisualizer()
        >>> visualizer.plot_all(results, save_path='benchmarks.png')
    """
    
    def __init__(self, style: str = 'seaborn-v0_8-darkgrid'):
        """
        Initialize visualizer.
        
        Args:
            style: Matplotlib style to use
        """
        self.style = style
        try:
            plt.style.use(style)
        except:
            plt.style.use('default')
    
    def plot_scaling_analysis(
        self,
        results: List[BenchmarkResult],
        save_path: Optional[str] = None
    ):
        """
        Plot comprehensive scaling analysis.
        
        Creates 4-panel figure:
        1. Timing scaling
        2. Circuit complexity scaling
        3. Memory scaling
        4. Hardware estimates
        """
        fig = plt.figure(figsize=(16, 12))
        gs = GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.3)
        
        # Extract data
        pixels = [r.pixels for r in results]
        n_qubits = [r.n_qubits_x + r.n_qubits_y for r in results]
        
        # Panel 1: Timing
        ax1 = fig.add_subplot(gs[0, 0])
        encoding_times = [r.encoding_time * 1000 for r in results]
        decoding_times = [r.decoding_time * 1000 for r in results]
        
        ax1.plot(pixels, encoding_times, 'o-', linewidth=2, markersize=8, label='Encoding')
        ax1.plot(pixels, decoding_times, 's-', linewidth=2, markersize=8, label='Decoding')
        ax1.set_xlabel('Grid Size (pixels)', fontsize=12)
        ax1.set_ylabel('Time (ms)', fontsize=12)
        ax1.set_title('Encoding/Decoding Performance', fontsize=14, fontweight='bold')
        ax1.legend(fontsize=11)
        ax1.grid(alpha=0.3)
        ax1.set_xscale('log', base=2)
        ax1.set_yscale('log')
        
        # Panel 2: Circuit Complexity
        ax2 = fig.add_subplot(gs[0, 1])
        depths = [r.circuit_depth for r in results]
        gates = [r.total_gates for r in results]
        
        ax2_twin = ax2.twinx()
        l1 = ax2.plot(pixels, depths, 'o-', color='C2', linewidth=2, markersize=8, label='Depth')
        l2 = ax2_twin.plot(pixels, gates, 's-', color='C3', linewidth=2, markersize=8, label='Gates')
        
        ax2.set_xlabel('Grid Size (pixels)', fontsize=12)
        ax2.set_ylabel('Circuit Depth', fontsize=12, color='C2')
        ax2_twin.set_ylabel('Total Gates', fontsize=12, color='C3')
        ax2.set_title('Circuit Complexity Scaling', fontsize=14, fontweight='bold')
        ax2.tick_params(axis='y', labelcolor='C2')
        ax2_twin.tick_params(axis='y', labelcolor='C3')
        ax2.grid(alpha=0.3)
        ax2.set_xscale('log', base=2)
        
        # Combine legends
        lns = l1 + l2
        labs = [l.get_label() for l in lns]
        ax2.legend(lns, labs, fontsize=11, loc='upper left')
        
        # Panel 3: Memory Usage
        ax3 = fig.add_subplot(gs[1, 0])
        mem_classical = [r.memory_classical for r in results]
        mem_circuit = [r.memory_circuit for r in results]
        mem_statevector = [r.memory_statevector for r in results]
        
        ax3.plot(pixels, mem_classical, 'o-', linewidth=2, markersize=8, label='Classical')
        ax3.plot(pixels, mem_circuit, 's-', linewidth=2, markersize=8, label='Circuit')
        ax3.plot(pixels, mem_statevector, '^-', linewidth=2, markersize=8, label='Statevector')
        ax3.set_xlabel('Grid Size (pixels)', fontsize=12)
        ax3.set_ylabel('Memory (MB)', fontsize=12)
        ax3.set_title('Memory Usage', fontsize=14, fontweight='bold')
        ax3.legend(fontsize=11)
        ax3.grid(alpha=0.3)
        ax3.set_xscale('log', base=2)
        ax3.set_yscale('log')
        
        # Panel 4: Hardware Estimates
        ax4 = fig.add_subplot(gs[1, 1])
        runtime_us = [r.estimated_runtime_ibm * 1e6 for r in results]
        fidelity = [r.estimated_fidelity_ibm * 100 for r in results]
        
        ax4_twin = ax4.twinx()
        l1 = ax4.plot(pixels, runtime_us, 'o-', color='C4', linewidth=2, markersize=8, label='Runtime')
        l2 = ax4_twin.plot(pixels, fidelity, 's-', color='C5', linewidth=2, markersize=8, label='Fidelity')
        
        ax4.set_xlabel('Grid Size (pixels)', fontsize=12)
        ax4.set_ylabel('Est. Runtime (µs)', fontsize=12, color='C4')
        ax4_twin.set_ylabel('Est. Fidelity (%)', fontsize=12, color='C5')
        ax4.set_title('IBM Hardware Estimates', fontsize=14, fontweight='bold')
        ax4.tick_params(axis='y', labelcolor='C4')
        ax4_twin.tick_params(axis='y', labelcolor='C5')
        ax4.grid(alpha=0.3)
        ax4.set_xscale('log', base=2)
        
        # Combine legends
        lns = l1 + l2
        labs = [l.get_label() for l in lns]
        ax4.legend(lns, labs, fontsize=11, loc='upper left')
        
        plt.suptitle('Quantum CTEM Performance Scaling Analysis', 
                     fontsize=16, fontweight='bold', y=0.995)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📊 Scaling plot saved: {save_path}")
        
        plt.show()
    
    def plot_accuracy_analysis(
        self,
        results: List[BenchmarkResult],
        save_path: Optional[str] = None
    ):
        """Plot accuracy metrics across grid sizes."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        pixels = [r.pixels for r in results]
        errors = [r.round_trip_error for r in results]
        fidelities = [r.fidelity for r in results]
        
        # Error plot
        ax1.semilogy(pixels, errors, 'o-', linewidth=2, markersize=10, color='C0')
        ax1.axhline(y=1e-8, color='red', linestyle='--', alpha=0.5, label='Target (1e-8)')
        ax1.set_xlabel('Grid Size (pixels)', fontsize=12)
        ax1.set_ylabel('Round-trip Error', fontsize=12)
        ax1.set_title('Encoding Accuracy', fontsize=14, fontweight='bold')
        ax1.legend(fontsize=11)
        ax1.grid(alpha=0.3)
        ax1.set_xscale('log', base=2)
        
        # Fidelity plot
        ax2.plot(pixels, fidelities, 's-', linewidth=2, markersize=10, color='C1')
        ax2.axhline(y=0.999, color='red', linestyle='--', alpha=0.5, label='Target (0.999)')
        ax2.set_xlabel('Grid Size (pixels)', fontsize=12)
        ax2.set_ylabel('State Fidelity', fontsize=12)
        ax2.set_title('State Preservation', fontsize=14, fontweight='bold')
        ax2.legend(fontsize=11)
        ax2.grid(alpha=0.3)
        ax2.set_xscale('log', base=2)
        ax2.set_ylim([0.9999, 1.0001])
        
        plt.suptitle('Accuracy Analysis', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📊 Accuracy plot saved: {save_path}")
        
        plt.show()
    
    def plot_optimization_comparison(
        self,
        comparison_results: Dict[str, Dict],
        save_path: Optional[str] = None
    ):
        """Plot comparison of optimization methods."""
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        
        methods = list(comparison_results.keys())
        
        # Preparation time
        times = [comparison_results[m]['preparation_time'] * 1000 for m in methods]
        axes[0].bar(methods, times, color=['C0', 'C1'], alpha=0.7, edgecolor='black', linewidth=1.5)
        axes[0].set_ylabel('Time (ms)', fontsize=12)
        axes[0].set_title('Preparation Time', fontsize=13, fontweight='bold')
        axes[0].grid(axis='y', alpha=0.3)
        
        # Circuit depth
        depths = [comparison_results[m]['depth'] for m in methods]
        axes[1].bar(methods, depths, color=['C2', 'C3'], alpha=0.7, edgecolor='black', linewidth=1.5)
        axes[1].set_ylabel('Depth', fontsize=12)
        axes[1].set_title('Circuit Depth', fontsize=13, fontweight='bold')
        axes[1].grid(axis='y', alpha=0.3)
        
        # Fidelity
        fidelities = [comparison_results[m]['fidelity'] for m in methods]
        axes[2].bar(methods, fidelities, color=['C4', 'C5'], alpha=0.7, edgecolor='black', linewidth=1.5)
        axes[2].set_ylabel('Fidelity', fontsize=12)
        axes[2].set_title('State Fidelity', fontsize=13, fontweight='bold')
        axes[2].set_ylim([0.9999, 1.0001])
        axes[2].grid(axis='y', alpha=0.3)
        
        plt.suptitle('Optimization Method Comparison', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📊 Comparison plot saved: {save_path}")
        
        plt.show()
    
    def plot_memory_profile(
        self,
        memory_data: Dict[str, List],
        save_path: Optional[str] = None
    ):
        """Plot memory usage profile."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        pixels = memory_data['pixels']
        
        # Stacked bar chart
        width = 0.6
        x = np.arange(len(pixels))
        
        ax1.bar(x, memory_data['classical_mb'], width, label='Classical', alpha=0.8)
        ax1.bar(x, memory_data['circuit_mb'], width, bottom=memory_data['classical_mb'],
               label='Circuit', alpha=0.8)
        ax1.bar(x, memory_data['statevector_mb'], width,
               bottom=np.array(memory_data['classical_mb']) + np.array(memory_data['circuit_mb']),
               label='Statevector', alpha=0.8)
        
        ax1.set_xlabel('Grid Size', fontsize=12)
        ax1.set_ylabel('Memory (MB)', fontsize=12)
        ax1.set_title('Memory Breakdown', fontsize=14, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels([f'{p}×{p}' for p in pixels])
        ax1.legend(fontsize=11)
        ax1.grid(axis='y', alpha=0.3)
        
        # Scaling plot
        ax2.loglog(pixels, memory_data['total_mb'], 'o-', linewidth=2, markersize=10,
                  label='Total Memory')
        ax2.loglog(pixels, memory_data['statevector_mb'], 's-', linewidth=2, markersize=8,
                  alpha=0.7, label='Statevector Only')
        
        ax2.set_xlabel('Grid Size (pixels)', fontsize=12)
        ax2.set_ylabel('Memory (MB)', fontsize=12)
        ax2.set_title('Memory Scaling', fontsize=14, fontweight='bold')
        ax2.legend(fontsize=11)
        ax2.grid(alpha=0.3)
        
        plt.suptitle('Memory Usage Analysis', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📊 Memory plot saved: {save_path}")
        
        plt.show()
    
    def plot_hardware_costs(
        self,
        cost_data: Dict[str, List],
        save_path: Optional[str] = None
    ):
        """Plot hardware deployment cost estimates."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        pixels = cost_data['pixels']
        
        # Runtime plot
        ax1.semilogy(pixels, cost_data['runtime_seconds'], 'o-', linewidth=2, 
                    markersize=10, color='C0', label='Per-shot runtime')
        ax1.set_xlabel('Grid Size (pixels)', fontsize=12)
        ax1.set_ylabel('Runtime per Shot (seconds)', fontsize=12)
        ax1.set_title('IBM Hardware Runtime', fontsize=14, fontweight='bold')
        ax1.grid(alpha=0.3)
        ax1.set_xscale('log', base=2)
        
        # Add text annotations
        for p, r in zip(pixels, cost_data['runtime_seconds']):
            ax1.text(p, r*1.3, f'{r*1e6:.1f}µs', ha='center', fontsize=9)
        
        # Fidelity plot
        fidelity_pct = [f * 100 for f in cost_data['estimated_fidelity']]
        ax2.plot(pixels, fidelity_pct, 's-', linewidth=2, markersize=10, color='C1')
        ax2.axhline(y=90, color='red', linestyle='--', alpha=0.5, label='90% threshold')
        ax2.set_xlabel('Grid Size (pixels)', fontsize=12)
        ax2.set_ylabel('Estimated Fidelity (%)', fontsize=12)
        ax2.set_title('Expected Fidelity on IBM Hardware', fontsize=14, fontweight='bold')
        ax2.legend(fontsize=11)
        ax2.grid(alpha=0.3)
        ax2.set_xscale('log', base=2)
        
        # Add text annotations
        for p, f in zip(pixels, fidelity_pct):
            ax2.text(p, f-5, f'{f:.2f}%', ha='center', fontsize=9)
        
        plt.suptitle('Hardware Deployment Estimates', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📊 Hardware cost plot saved: {save_path}")
        
        plt.show()
    
    def plot_all(
        self,
        results: List[BenchmarkResult],
        save_dir: Optional[str] = None
    ):
        """
        Create all visualization plots.
        
        Args:
            results: List of benchmark results
            save_dir: Directory to save plots (if None, only display)
        """
        if save_dir:
            save_dir = Path(save_dir)
            save_dir.mkdir(parents=True, exist_ok=True)
        
        # Scaling analysis
        self.plot_scaling_analysis(
            results,
            save_path=save_dir / 'scaling_analysis.png' if save_dir else None
        )
        
        # Accuracy analysis
        self.plot_accuracy_analysis(
            results,
            save_path=save_dir / 'accuracy_analysis.png' if save_dir else None
        )


def create_summary_figure(
    results: List[BenchmarkResult],
    save_path: str = 'benchmark_summary.png'
):
    """
    Create single summary figure with key metrics.
    
    Args:
        results: List of benchmark results
        save_path: Path to save figure
    """
    visualizer = BenchmarkVisualizer()
    visualizer.plot_scaling_analysis(results, save_path=save_path)
