"""Paper-ready runner for MoS2 quantum vs classical CTEM comparison.

Saves high-resolution images and a metadata file with parameters and git commit.
"""
from pathlib import Path
import json
import os
import sys

# Ensure site-packages first, then our src
repo_root = Path(__file__).resolve().parents[1]
src_dir = repo_root / 'src'
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir))

from quscope.mos2_workflow import run_comparison
import numpy as np
import matplotlib.pyplot as plt


def save_image(arr, path, cmap='gray'):
    plt.figure(figsize=(6, 6))
    plt.imshow(arr, cmap=cmap)
    plt.axis('off')
    plt.tight_layout(pad=0)
    plt.savefig(path, dpi=300, bbox_inches='tight', pad_inches=0)
    plt.close()


def write_metadata(path, params):
    with open(path, 'w') as f:
        json.dump(params, f, indent=2)


def main(nx=3, ny=2, grid_size=512, pixel_size=0.05, voltage=200e3, outdir='outputs/paper'):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)

    print('Running classical + quantum comparator')
    res = run_comparison(nx=nx, ny=ny, grid_size=grid_size, pixel_size=pixel_size, voltage=voltage)

    # Save images
    vq = res['V_quantum']
    vab = res.get('V_abtem', vq)
    I = res['I_classical']

    save_image(vq, out / f'V_quantum_{grid_size}.png')
    save_image(vab, out / f'V_abtem_{grid_size}.png')
    save_image(I, out / f'I_classical_{grid_size}.png')

    # Write metadata
    params = {
        'nx': nx,
        'ny': ny,
        'grid_size': grid_size,
        'pixel_size': pixel_size,
        'voltage': voltage,
        'abtem_used': 'V_abtem' in res and res['V_abtem'] is not None,
    }
    # Add git commit if available
    try:
        import subprocess
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
        params['git_commit'] = commit
    except Exception:
        params['git_commit'] = None

    write_metadata(out / f'metadata_{grid_size}.json', params)
    print('Saved outputs to', out)


if __name__ == '__main__':
    main()
