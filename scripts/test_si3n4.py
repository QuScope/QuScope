"""Quick validation of Si3N4 quantum multislice pipeline."""
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import ase
import abtem

from quscope.quantum_ctem import (
    QuantumMultisliceParameters,
    QuantumMultisliceCircuit,
    QuantumClassicalMultisliceValidator,
)
from quscope.ctem.kirkland_potential import KirklandPotential
from quscope.quantum_ctem.quantum_ctem_circuit import relativistic_wavelength, interaction_constant

# --- Structure ---
structure = ase.Atoms(
    "Si6N8",
    positions=[
        (4.015308131006949,  3.9110253242355126,  2.1788993100000003),
        (2.422878997737693, -1.15285715796029,    0.72629977),
        (5.3947013511357,   -1.5218461833564767,  0.72629977),
        (2.2098430845971873, 1.521846183356477,   2.1788993100000003),
        (5.181665437995193,  1.1528571579602902,  2.1788993100000003),
        (3.5892363047259375,-3.9110253242355126,  0.72629977),
        (3.8022722178664434, 2.195242888517426,   2.1788993100000003),
        (3.802272217866444, -2.1952428885174267,  0.72629977),
        (6.2321062558996125,-1.9713791971906662,  2.1788993100000003),
        (4.8233175932090955, 4.411472738097657,   0.72629977),
        (5.211060880556961,  0.20287673026395847, 0.72629977),
        (2.3934835551759255,-0.20287673026395803, 2.1788993100000003),
        (1.3724381798332734, 1.9713791971906653,  0.72629977),
        (2.781226842523792, -4.411472738097657,   2.1788993100000003),
    ],
    cell=[7.6045, 7.6045, 2.9052, 90, 90, 120],
)

structure_orth = abtem.orthogonalize_cell(structure)
print(f"Orthogonal cell: {structure_orth.cell.cellpar()[:3].round(4)} A")
print(f"Formula: {structure_orth.get_chemical_formula()}  ({len(structure_orth)} atoms)")

# --- Parameters ---
GRID_SIZE  = 16
PIXEL_SIZE = 0.5

params = QuantumMultisliceParameters(
    acceleration_voltage=200e3,
    grid_size=GRID_SIZE,
    pixel_size=PIXEL_SIZE,
    defocus=-659.7,
    cs=1.3,
    slice_thickness=2.9052,
)
wl    = relativistic_wavelength(200e3)
sigma = interaction_constant(200e3, wl)
print(f"lambda={wl:.4f} A  sigma={sigma:.4f} V-1A-1")

# --- Kirkland slice potentials ---
kirk     = KirklandPotential()
SYMBOL_Z = {"Si": 14, "N": 7}
N_SLICES = 4
extent   = GRID_SIZE * PIXEL_SIZE

x_lin = np.linspace(0, extent, GRID_SIZE, endpoint=False)
y_lin = np.linspace(0, extent, GRID_SIZE, endpoint=False)
X, Y  = np.meshgrid(x_lin, y_lin, indexing="ij")

Z_total  = structure_orth.cell[2, 2]
z_bounds = np.linspace(0, Z_total, N_SLICES + 1)
positions = structure_orth.get_positions()
symbols   = structure_orth.get_chemical_symbols()
cell_x    = structure_orth.cell[0, 0]
cell_y    = structure_orth.cell[1, 1]

slice_pots = []
for s in range(N_SLICES):
    z_lo, z_hi = z_bounds[s], z_bounds[s + 1]
    V = np.zeros((GRID_SIZE, GRID_SIZE))
    for pos, sym in zip(positions, symbols):
        if z_lo <= pos[2] < z_hi and sym in SYMBOL_Z:
            ax = pos[0] % cell_x
            ay = pos[1] % cell_y
            for nx in range(int(np.ceil(extent / cell_x)) + 1):
                for ny in range(int(np.ceil(extent / cell_y)) + 1):
                    apx = ax + nx * cell_x
                    apy = ay + ny * cell_y
                    if -3 < apx < extent + 3 and -3 < apy < extent + 3:
                        V += kirk.calculate_2d(X, Y, apx, apy, SYMBOL_Z[sym])
    slice_pots.append(V)
    print(f"  Slice {s+1}: V in [{V.min():.1f}, {V.max():.1f}] eV")

# --- Quantum simulation ---
print("Running quantum multislice...")
sim    = QuantumMultisliceCircuit(params)
result = sim.simulate(slice_pots)
I_q    = result["intensity"]
print(f"Quantum intensity: [{I_q.min():.4e}, {I_q.max():.4e}]  norm={np.sum(I_q):.6f}")

# --- Fidelity ---
print("Computing quantum-classical fidelity...")
validator  = QuantumClassicalMultisliceValidator(params)
comparison = validator.compare(slice_pots)
print(f"Fidelity: {comparison['fidelity']:.6f}  RMSE: {comparison['rmse']:.2e}")

if comparison["fidelity"] > 0.99:
    print("ALL OK - Quantum multislice Si3N4 validated successfully!")
else:
    print(f"WARNING: fidelity = {comparison['fidelity']:.4f} < 0.99")
