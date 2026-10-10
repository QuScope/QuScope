#!/usr/bin/env python
"""Generate the data figures for the QuScope paper from the released code.

All quantum results in these figures come from COMPLETE quantum-circuit
executions (state preparation + DiagonalGate + QFTGate via Statevector);
no diagonal-as-array shortcuts are used.

Figures (saved to paper/figures/ as PDF + PNG preview):
  fig_ctem_wpoa    potential | quantum CTEM intensity | classical reference
  fig_stem         Z-contrast: O/Ti/Sr/Au columns (Kirkland potentials),
                   HAADF + ABF + HAADF-peak-vs-Z scaling panel
  fig_multislice   SrTiO3 [100], 10 unit cells (20 slices): quantum vs
                   classical exit wave + difference
  fig_propagation  on-column intensity vs depth through the 20 slices,
                   quantum circuit vs classical multislice

Conventions: image intensities use grayscale (sequential magnitude,
microscopy convention); potentials use a single-hue sequential map.

Usage: python generate_figures.py [--src ../src]
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--src", default=str(HERE.parent / "src"))
parser.add_argument("--fast", action="store_true",
                    help="coarser STEM scan for quick iteration")
parser.add_argument("--only", default="all", choices=["all", "ctf", "ctem", "stem", "sto"],
                    help="generate only one figure group")
parser.add_argument("--stem-step", type=int, default=2,
                    help="scan step (pixels) for the 2D STEM image")
args = parser.parse_args()
sys.path.insert(0, args.src)

from qiskit import QuantumCircuit                                   # noqa: E402
from qiskit.quantum_info import Statevector                         # noqa: E402
from quscope.quantum_ctem import (                                  # noqa: E402
    QuantumCTEMParameters, QuantumCTEMCircuit, QuantumClassicalValidator,
    QuantumMultisliceParameters, QuantumMultisliceCircuit,
    QuantumClassicalMultisliceValidator, STEMDetectors,
    build_probe_circuit, fresnel_propagator_phase,
)
from quscope.quantum_ctem.quantum_ctem_circuit import (             # noqa: E402
    relativistic_wavelength, interaction_constant,
)
from quscope.quantum_ctem.quantum_stem import (                     # noqa: E402
    _focused_probe_k, _probe_real, _propagate_to_detector,
)
from quscope.ctem.kirkland_potential import KirklandPotential       # noqa: E402

FIGDIR = HERE / "figures"
FIGDIR.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 9, "axes.labelsize": 9,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
    "figure.dpi": 200, "savefig.bbox": "tight",
})

CM_INT = "gray"     # image intensities (sequential magnitude)
CM_POT = "magma"    # projected potential (sequential magnitude)

VOLTAGE = 200e3
LAM = relativistic_wavelength(VOLTAGE)
SIGMA = interaction_constant(VOLTAGE, LAM)
KP = KirklandPotential()


def kirkland_grid(N, px, atoms, origin=0.0, supersample=1):
    """Projected potential (V*A) on an N x N grid from (x, y, Z) atoms,
    including one ring of periodic images so column tails wrap correctly.
    supersample > 1 integrates the near-singular core over each pixel
    (evaluate on a finer grid, average-pool) so peak heights are uniform
    regardless of where atoms fall relative to pixel centres."""
    L = N * px
    Ns = N * supersample
    coords = (np.arange(Ns) + 0.5) * (px / supersample) + origin
    X, Y = np.meshgrid(coords, coords, indexing="ij")
    V = np.zeros((Ns, Ns))
    for (ax, ay, Z) in atoms:
        for mx in (-1, 0, 1):
            for my in (-1, 0, 1):
                V += KP.calculate_2d(X, Y, atom_x=ax + mx * L, atom_y=ay + my * L, Z=Z)
    if supersample > 1:
        V = V.reshape(N, supersample, N, supersample).mean(axis=(1, 3))
    return V


def panel(ax, img, title, cmap, extent, vmin=None, vmax=None):
    im = ax.imshow(img.T, origin="lower", cmap=cmap, extent=extent,
                   vmin=vmin, vmax=vmax, interpolation="nearest")
    ax.set_title(title)
    ax.set_xlabel(r"$x$ (Å)")
    return im


def save(fig, name):
    fig.savefig(FIGDIR / f"{name}.pdf")
    fig.savefig(FIGDIR / f"{name}.png")
    plt.close(fig)
    print(f"wrote figures/{name}.pdf")


# ================================================================ Fig: CTF / probes
if args.only in ('all', 'ctf'):
    from quscope.quantum_ctem import CTFCalculator
    from quscope.quantum_ctem.ctf_calculator import CTFParameters

    k = np.linspace(0, 1.5, 800)
    # Scherzer defocus depends only on (voltage, cs), not on the defocus
    # field itself, so compute it from a zero-defocus calculator first and
    # feed the result back into the CTFParameters used for the plot -- this
    # keeps both cases on the same convention as calculate_scherzer_defocus()
    # (the extended/Lentzen factor 1.2) instead of a hand-typed number that
    # can drift out of sync with the formula.
    cs_cases = [("$C_s$ = 1.3 mm (Scherzer)", 1.3, "0.15", "-"),
                ("$C_s$ = 0.05 mm (corrected)", 0.05, "0.55", "--")]
    cases = []
    for label, cs, col, ls in cs_cases:
        df = CTFCalculator(CTFParameters(voltage=VOLTAGE, defocus=0.0, cs=cs)).calculate_scherzer_defocus()
        cases.append((label, CTFParameters(voltage=VOLTAGE, defocus=df, cs=cs), col, ls))

    fig, (axa, axb) = plt.subplots(1, 2, figsize=(7.0, 2.3), constrained_layout=True)
    for label, p, col, ls in cases:
        calc = CTFCalculator(p, max_k=1.5)
        axa.plot(k, calc.ctf(k), ls, color=col, lw=1.2, label=label)
        res = calc.calculate_point_resolution()
        axa.axvline(1.0 / res, color=col, lw=0.8, ls="--", alpha=0.6)
        # axa.annotate(f"{res:.2f} Å", (1.0 / res, 1.02), ha="center", va="bottom",
        #              fontsize=6.5, color=col, annotation_clip=False)
        print(f"CTF {label}: Scherzer={calc.calculate_scherzer_defocus():.1f} A, "
              f"point resolution={res:.2f} A")
    axa.axhline(0, color="0.8", lw=0.6)
    axa.set_xlabel(r"spatial frequency $k$ (Å$^{-1}$)")
    axa.set_ylabel(r"CTF $\sin\chi(k)$")
    axa.set_title("TEM phase-contrast transfer (200 kV)", pad=10)
    leg = axa.legend(fontsize=6.5, loc="lower right", framealpha=0.95,
                     edgecolor="none", fancybox=False)
    axa.set_xlim(0, 1.2); axa.set_ylim(-1.05, 1.05)

    # STEM probes for the two apertures used in this paper (aberration-free)
    Np, pxp = 256, 0.05
    r = (np.arange(Np) - Np // 2) * pxp
    for alpha_mrad, col, ls in ((18.0, "0.15", "-"), (30.0, "0.55", "--")):
        pk = _focused_probe_k(Np, pxp, LAM, convergence_mrad=alpha_mrad,
                              defocus_ang=0.0, cs_mm=0.0)
        pr = _probe_real(pk, shift_x=Np // 2, shift_y=Np // 2)
        prof = np.abs(pr[:, Np // 2]) ** 2
        prof = prof / prof.max()
        half = np.where(prof >= 0.5)[0]
        fwhm = (half[-1] - half[0]) * pxp
        axb.plot(r, prof, ls, color=col, lw=1.3,
                 label=rf"$\alpha$ = {alpha_mrad:.0f} mrad")
        print(f"probe alpha={alpha_mrad} mrad: FWHM = {fwhm:.2f} A")
    axb.set_xlabel(r"$r$ (Å)")
    axb.set_ylabel("probe intensity (norm.)")
    axb.set_title("STEM probe profiles (200 kV)")
    axb.legend(frameon=False, fontsize=6.5, loc="upper left")
    axb.set_xlim(-2.5, 2.5)
    save(fig, "fig_ctf")

# ================================================================ Fig: CTEM WPOA
if args.only in ('all', 'ctem'):
    # Periodic graphene sheet, ~5x5 hexagonal unit cells (12.3 A field of
    # view), aberration-corrected Scherzer imaging so the bonds are resolved.
    # A commensurate square supercell needs a slight (<4%) y-strain: 5
    # rectangular cells (2.46 A) x 3 rectangular cells (4.26 -> 4.10 A).
    N = 128
    L = 5 * 2.46                                 # 12.30 A field of view
    px = L / N                                   # 0.0961 A
    ext = [0, L, 0, L]
    cy = L / 3                                   # strained rect-cell height
    sy = cy / 4.26                               # y-strain factor 0.9624
    basis = [(0.0, 0.0), (0.0, 1.42 * sy), (1.23, 2.13 * sy), (1.23, 3.55 * sy)]
    atoms = []
    for m in range(5):
        for n in range(3):
            for (bx, by) in basis:
                atoms.append(((m * 2.46 + bx) % L, (n * cy + by) % L, 6))
    from scipy.ndimage import gaussian_filter
    V = kirkland_grid(N, px, atoms, supersample=4)
    V = gaussian_filter(V, sigma=0.25 / px, mode="wrap")   # Debye-Waller thermal smearing
    print(f"graphene sheet: {len(atoms)} C atoms, {N}x{N} grid "
          f"({2*int(np.log2(N))} qubits), max sigma*V = {SIGMA * V.max():.3f} rad")

    cs_mm = 0.05                                  # aberration-corrected
    scherzer = -1.2 * np.sqrt(cs_mm * 1e7 * LAM)  # ~ -134 A
    params = QuantumCTEMParameters(
        acceleration_voltage=VOLTAGE, grid_size=N, pixel_size=px,
        defocus=scherzer, cs=cs_mm,
    )
    q = QuantumCTEMCircuit(params).simulate(V)
    cmp = QuantumClassicalValidator(params).compare(V)
    I_q = q["intensity"]
    t = np.exp(1j * SIGMA * V)
    psi0 = np.ones((N, N)) / N
    f = np.fft.fftfreq(N, d=px)
    fx, fy = np.meshgrid(f, f, indexing="ij")
    k2 = fx ** 2 + fy ** 2
    chi = np.pi * LAM * params.defocus * k2 + 0.5 * np.pi * (cs_mm * 1e7) * LAM ** 3 * k2 ** 2
    psi_c = np.fft.ifft2(np.fft.fft2(t * psi0) * np.exp(1j * chi))
    I_c = np.abs(psi_c) ** 2
    I_c = I_c / I_c.sum() * I_q.sum()

    # abTEM reference: same graphene geometry, same voltage and CTF parameters
    try:
        from ase import Atoms as AseAtoms
        import abtem

        ase_atoms = AseAtoms(
            'C' * len(atoms),
            positions=[(x, y, 0.0) for (x, y, _Z) in atoms],
            cell=[L, L, 3.0],
            pbc=True,
        )
        potential_abtem = abtem.Potential(
            ase_atoms, gpts=(N, N), slice_thickness=3.0,
        )
        pw = abtem.PlaneWave(energy=VOLTAGE)
        exit_wave = pw.multislice(potential_abtem)
        ctf_abtem = abtem.CTF(
            energy=VOLTAGE,
            aberration_coefficients={"C10": params.defocus, "C30": cs_mm * 1e7},
        )
        I_abtem_raw = np.array(exit_wave.apply_ctf(ctf_abtem).intensity().array)
        I_abtem = I_abtem_raw / I_abtem_raw.sum() * I_q.sum()
        have_abtem = True
        print(f"abTEM CTEM computed (version {abtem.__version__})")
    except Exception as _e:
        have_abtem = False
        print(f"abTEM not available or failed ({_e}); skipping 4th panel")

    ncols = 4 if have_abtem else 3
    fw = 9.2 if have_abtem else 7.0
    fig, axes = plt.subplots(1, ncols, figsize=(fw, 2.35), constrained_layout=True)
    im0 = panel(axes[0], V, r"graphene $V_z$", CM_POT, ext)
    axes[0].set_ylabel(r"$y$ (Å)")
    fig.colorbar(im0, ax=axes[0], label=r"V·Å", shrink=0.85)
    all_I = [I_q, I_c] + ([I_abtem] if have_abtem else [])
    vmax = max(x.max() for x in all_I); vmin = min(x.min() for x in all_I)
    panel(axes[1], I_q, "quantum circuit", CM_INT, ext, vmin=vmin, vmax=vmax)
    im2 = panel(axes[2], I_c, "classical (FFT)", CM_INT, ext, vmin=vmin, vmax=vmax)
    if have_abtem:
        im_last = panel(axes[3], I_abtem, "abTEM", CM_INT, ext, vmin=vmin, vmax=vmax)
        fig.colorbar(im_last, ax=axes[3], label="intensity", shrink=0.85)
    else:
        fig.colorbar(im2, ax=axes[2], label="intensity", shrink=0.85)
    fid = cmp.get("fidelity", cmp.get("overlap", float("nan")))
    print(f"CTEM (graphene) fidelity: {fid:.6f}")
    save(fig, "fig_ctem_wpoa")

# ================================================================ Fig: STEM Z-contrast
if args.only in ('all', 'stem'):
    # Quantum multislice STEM of SrTiO3 [100], ten unit cells thick.
    # One unit cell scanned at full resolution (periodic boundaries);
    # every scan pixel is one complete 20-slice quantum circuit.
    A0 = 3.905
    N = 32
    px = A0 / N                                    # 0.1220 A
    NUC = 10
    DZ = A0 / 2
    sro = [(0.0, 0.0, 38), (A0 / 2, A0 / 2, 8)]
    tio2 = [(A0 / 2, A0 / 2, 22), (A0 / 2, 0.0, 8), (0.0, A0 / 2, 8)]
    V_sro = kirkland_grid(N, px, sro)
    V_tio2 = kirkland_grid(N, px, tio2)
    gratings = [np.exp(1j * SIGMA * (V_sro if s % 2 == 0 else V_tio2)).flatten()
                for s in range(2 * NUC)]
    prop = fresnel_propagator_phase(N, px, LAM, DZ)
    print(f"STEM STO: 1 UC field of view, {2*NUC} slices, "
          f"max sigma*V = {SIGMA * max(V_sro.max(), V_tio2.max()):.3f} rad")

    n_q = 2 * int(np.log2(N))
    det = STEMDetectors()
    masks = det.masks(N, px, LAM)
    probe_k = _focused_probe_k(N, px, LAM, convergence_mrad=30.0,
                               defocus_ang=0.0, cs_mm=0.0)

    step = 4 if args.fast else 1
    scan = list(range(0, N, step))
    imgs = {name: np.zeros((len(scan), len(scan))) for name in masks}
    t0 = time.time()
    for si, ix in enumerate(scan):
        for sj, iy in enumerate(scan):
            probe_r = _probe_real(probe_k, shift_x=ix, shift_y=iy)
            amps = probe_r.flatten()
            amps = amps / (np.linalg.norm(amps) + 1e-20)
            qc = QuantumCircuit(n_q)
            qc.initialize(amps.tolist(), range(n_q))
            qc.compose(build_probe_circuit(n_q, gratings, prop), inplace=True)
            psi_exit = Statevector.from_instruction(qc).data.reshape(N, N)
            sigs, _, _ = _propagate_to_detector(psi_exit, masks)
            for name in masks:
                imgs[name][si, sj] = sigs[name]
        print(f"  scan row {si + 1}/{len(scan)} ({time.time() - t0:.0f}s)", flush=True)
    print(f"STEM STO scan: {len(scan) ** 2} complete 20-slice quantum circuits "
          f"in {time.time() - t0:.0f}s")

    def tile(img):
        return np.tile(img, (2, 2))

    ext2 = [0, 2 * A0, 0, 2 * A0]
    V_proj = V_sro + V_tio2
    fig, axes = plt.subplots(1, 4, figsize=(7.05, 1.95), constrained_layout=True)
    im0 = panel(axes[0], tile(V_proj), "STO [100] potential", CM_POT, ext2)
    axes[0].set_ylabel(r"$y$ (Å)")
    axes[0].annotate("Sr", (A0, A0 + 0.5), color="white", ha="center", fontsize=6.5)
    axes[0].annotate("Ti+O", (A0 / 2, A0 / 2 + 0.5), color="white", ha="center", fontsize=6.5)
    panel(axes[1], tile(imgs["HAADF"]), "HAADF", CM_INT, ext2)
    panel(axes[2], tile(imgs["ABF"]), "ABF", CM_INT, ext2)
    panel(axes[3], tile(imgs["BF"]), "BF", CM_INT, ext2)
    save(fig, "fig_stem")

# ================================================================ SrTiO3 [100] multislice
if args.only in ('all', 'sto'):

    A0 = 3.905                       # SrTiO3 lattice parameter (A)
    NCELLS, NUC = 2, 10              # 2x2 cells in-plane, 10 unit cells thick
    N = 64
    px = NCELLS * A0 / N             # 0.1220 A
    L = N * px
    ext = [0, L, 0, L]
    DZ = A0 / 2                      # SrO / TiO2 alternation

    sro_atoms, tio2_atoms = [], []
    for mx in range(NCELLS):
        for my in range(NCELLS):
            ox, oy = mx * A0, my * A0
            sro_atoms += [(ox + 0.0, oy + 0.0, 38), (ox + A0/2, oy + A0/2, 8)]
            tio2_atoms += [(ox + A0/2, oy + A0/2, 22),
                           (ox + A0/2, oy + 0.0, 8), (ox + 0.0, oy + A0/2, 8)]
    V_sro = kirkland_grid(N, px, sro_atoms)
    V_tio2 = kirkland_grid(N, px, tio2_atoms)
    pots = [V_sro if s % 2 == 0 else V_tio2 for s in range(2 * NUC)]
    print(f"STO: {len(pots)} slices, sigma*V max per slice = "
          f"{SIGMA * max(V_sro.max(), V_tio2.max()):.3f} rad")

    msp = QuantumMultisliceParameters(
        acceleration_voltage=VOLTAGE, grid_size=N, pixel_size=px,
        defocus=0.0, cs=0.0, slice_thickness=DZ,
    )
    t0 = time.time()
    res = QuantumMultisliceCircuit(msp).simulate(pots)
    print(f"STO quantum multislice circuit ({2*NUC} slices, {2*int(np.log2(N))} qubits): "
          f"{time.time() - t0:.0f}s")
    q_wave = np.asarray(res.get("wave_function", res.get("statevector"))).reshape(N, N)
    c_wave = QuantumClassicalMultisliceValidator(msp).classical_multislice(pots)
    q_flat = q_wave.flatten() / np.linalg.norm(q_wave)
    c_flat = c_wave.flatten() / np.linalg.norm(c_wave)
    fid = float(np.abs(np.vdot(q_flat, c_flat)) ** 2)
    print(f"STO multislice fidelity: {fid:.6f}")

    Iq = np.abs(q_flat.reshape(N, N)) ** 2
    Ic = np.abs(c_flat.reshape(N, N)) ** 2
    phase = np.vdot(c_flat, q_flat); phase /= abs(phase)
    diff = np.abs(q_flat.reshape(N, N) - phase * c_flat.reshape(N, N))

    fig, axes = plt.subplots(1, 4, figsize=(7.0, 1.95), constrained_layout=True)
    im0 = panel(axes[0], V_sro + V_tio2, r"STO [100] potential", CM_POT, ext)
    axes[0].set_ylabel(r"$y$ (Å)")
    vmax = max(Iq.max(), Ic.max())
    panel(axes[1], Iq, "quantum exit wave", CM_INT, ext, vmin=0, vmax=vmax)
    im2 = panel(axes[2], Ic, "classical exit wave", CM_INT, ext, vmin=0, vmax=vmax)
    fig.colorbar(im2, ax=axes[2], label=r"$|\psi|^2$", shrink=0.85)
    expo = int(np.ceil(-np.log10(diff.max() + 1e-300)))
    im3 = panel(axes[3], diff * 10.0 ** expo,
                rf"$|\psi_q-\psi_c|\times10^{{{expo}}}$", "viridis", ext)
    fig.colorbar(im3, ax=axes[3], shrink=0.85)
    print(f"STO max |psi_q - psi_c| = {diff.max():.2e}")
    save(fig, "fig_multislice")

    # ================================================================ Beam propagation
    # x-z maps of a focused probe channeling through the crystal, in the
    # style of classical beam-propagation figures: beam enters at the top,
    # one column records |psi(x, y_row, z)|^2 after every slice subcircuit.
    from qiskit.circuit.library import DiagonalGate, QFTGate
    n_q = 2 * int(np.log2(N))
    n_half = n_q // 2
    prop = fresnel_propagator_phase(N, px, LAM, DZ)

    def slice_subcircuit(V_s, with_prop=True):
        qc = QuantumCircuit(n_q)
        qc.append(DiagonalGate(np.exp(1j * SIGMA * V_s).flatten().tolist()), range(n_q))
        if with_prop:
            qc.append(QFTGate(n_half), range(n_half))
            qc.append(QFTGate(n_half), range(n_half, n_q))
            qc.append(DiagonalGate(prop.tolist()), range(n_q))
            qc.append(QFTGate(n_half).inverse(), range(n_half))
            qc.append(QFTGate(n_half).inverse(), range(n_half, n_q))
        return qc

    def pix(coord):
        return int(round(coord / px - 0.5)) % N

    probe_k = _focused_probe_k(N, px, LAM, convergence_mrad=18.0,
                               defocus_ang=0.0, cs_mm=0.0)
    fprop = prop.reshape(N, N)
    cases = [("Sr column", (A0, A0)), ("Ti–O column", (A0 / 2, A0 / 2))]
    maps, fmins = [], []
    t0 = time.time()
    for label, (cx, cy) in cases:
        ix, iy = pix(cx), pix(cy)
        probe_r = _probe_real(probe_k, shift_x=ix, shift_y=iy)
        amps = probe_r.flatten() / (np.linalg.norm(probe_r.flatten()) + 1e-20)
        qc0 = QuantumCircuit(n_q)
        qc0.initialize(amps.tolist(), range(n_q))
        sv = Statevector.from_instruction(qc0)
        psi_cl = amps.reshape(N, N).copy()
        rows = [np.abs(sv.data.reshape(N, N)[:, iy]) ** 2]
        fid_min = 1.0
        for s, V_s in enumerate(pots):
            sv = sv.evolve(slice_subcircuit(V_s, with_prop=s < len(pots) - 1))
            psi_cl = psi_cl * np.exp(1j * SIGMA * V_s)
            if s < len(pots) - 1:
                psi_cl = np.fft.ifft2(np.fft.fft2(psi_cl) * fprop)
            qs = sv.data.reshape(N, N)
            rows.append(np.abs(qs[:, iy]) ** 2)
            cf = psi_cl.flatten() / np.linalg.norm(psi_cl)
            fid_min = min(fid_min, float(np.abs(np.vdot(qs.flatten(), cf)) ** 2))
        maps.append((label, np.array(rows)))
        fmins.append(fid_min)
        print(f"  {label}: {len(pots)} slice circuits, min fidelity {fid_min:.6f} "
              f"({time.time() - t0:.0f}s)")

    Zmax = len(pots) * DZ
    fig, axes = plt.subplots(1, 2, figsize=(4.6, 3.1), constrained_layout=True,
                             sharey=True)
    vmax = max(m.max() for _, m in maps)
    from matplotlib.colors import PowerNorm
    for ax, (label, m) in zip(axes, maps):
        im = ax.imshow(m, origin="upper", aspect="auto", cmap="inferno",
                       extent=[0, N * px, Zmax, 0],
                       norm=PowerNorm(0.45, vmin=0, vmax=vmax),
                       interpolation="bilinear")
        ax.set_title(f"probe on {label}")
        ax.set_xlabel(r"$x$ (Å)")
    axes[0].set_ylabel(r"depth $z$ (Å)")
    fig.colorbar(im, ax=axes, label=r"$|\psi|^2$", shrink=0.9, pad=0.02)
    print(f"propagation maps: min per-depth fidelity = {min(fmins):.6f}")
    save(fig, "fig_propagation")

print("all figures written to", FIGDIR)
