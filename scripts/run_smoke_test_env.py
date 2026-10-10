"""Run the MoS2 smoke test robustly from any shell.

This wrapper ensures that the environment site-packages are searched
before the repo's `src` directory so installed packages (ASE, abTEM)
are used, then it imports the orchestrator and saves outputs to disk.
"""
import os
import sys
from pathlib import Path
# Ensure the site's packages are searched before src by appending src
repo_root = Path(__file__).resolve().parents[1]
src_dir = repo_root / 'src'
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir))

import site
import sysconfig

# Ensure the conda environment's site-packages directory (if any) is
# inserted before the repo src so installed packages (ase, abtem)
# take precedence when this script is launched via `conda run`.
def _ensure_site_packages_first():
    # Try to determine the site-packages path for the active interpreter
    try:
        sp = site.getsitepackages()
    except Exception:
        sp = []
    # Also include sysconfig's purelib location
    try:
        sp.append(sysconfig.get_paths().get('purelib'))
    except Exception:
        pass
    for p in sp:
        if p and p not in sys.path:
            sys.path.insert(0, p)


_ensure_site_packages_first()

from quscope.mos2_workflow import run_comparison
import matplotlib.pyplot as plt


def save_array_as_image(arr, path):
    plt.figure(figsize=(4, 4))
    plt.imshow(arr, cmap='gray')
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def main():
    out_dir = repo_root / 'outputs'
    out_dir.mkdir(parents=True, exist_ok=True)

    # Default run (script-equivalent)
    res = run_comparison(nx=2, ny=1, grid_size=128, pixel_size=0.1, voltage=200e3)
    save_array_as_image(res['I_classical'], out_dir / 'I_classical_128.png')

    # Larger run to generate higher-res images
    res_large = run_comparison(nx=3, ny=2, grid_size=512, pixel_size=0.05, voltage=200e3)
    save_array_as_image(res_large['I_classical'], out_dir / 'I_classical_512.png')

    print('Saved images to', out_dir)


if __name__ == '__main__':
    main()
