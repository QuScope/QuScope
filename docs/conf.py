# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# Ensure the src/ directory is on sys.path for src-layout projects
_THIS_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, '..'))
_SRC_DIR = os.path.join(_PROJECT_ROOT, 'src')
if os.path.isdir(_SRC_DIR) and _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

# -- Project information -----------------------------------------------------

project = 'QuScope'
copyright = '2025, Roberto dos Reis and Sean Lam'
author = 'Roberto dos Reis and Sean Lam'

version = '0.1.0'
release = '0.1.0'

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',       # Include documentation from docstrings
    'sphinx.ext.autosummary',   # Generate summary tables for modules/classes/methods
    'sphinx.ext.napoleon',      # Support for Google and NumPy style docstrings
    'sphinx.ext.intersphinx',   # Link to other projects' documentation
    'sphinx.ext.viewcode',      # Add links to source code
    # 'nbsphinx',               # Made optional below
    'myst_parser',            # Parse Markdown files like README.md
    'sphinx_rtd_theme',      # Read the Docs theme
    'sphinx.ext.githubpages', # Support for GitHub Pages
]

# Try to enable nbsphinx if environment supports it
try:
    import nbsphinx  # noqa: F401
    extensions.append('nbsphinx')
    NBS_PHINX_AVAILABLE = True
except Exception:
    NBS_PHINX_AVAILABLE = False

autodoc_member_order = 'bysource'

autosummary_generate = False  # Disable auto stub generation to avoid import-time issues

napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'scipy': ('https://docs.scipy.org/doc/scipy/', None), # Corrected URL
    'matplotlib': ('https://matplotlib.org/stable/', None),
    'qiskit': ('https://docs.quantum.ibm.com/api/qiskit/', None),
    'pillow': ('https://pillow.readthedocs.io/en/stable/', None),
    'pandas': ('https://pandas.pydata.org/pandas-docs/stable/', None),
}

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}
if NBS_PHINX_AVAILABLE:
    # Only register ipynb when nbsphinx is available
    source_suffix['.ipynb'] = 'nbsphinx'

templates_path = ['_templates']
exclude_patterns = [
    '_build', 
    'Thumbs.db', 
    '.DS_Store', 
    '**.ipynb_checkpoints',
    'requirements.txt' # Exclude the docs requirements file itself
]

# If nbsphinx is not available, exclude notebooks from the build
if not NBS_PHINX_AVAILABLE:
    exclude_patterns += ['**/*.ipynb', 'notebooks/**']

# Mock imports for problematic/optional dependencies
autodoc_mock_imports = [
    'torch',
    'qiskit',
    'qiskit_aer',
    'qiskit_ibm_provider',
    'qiskit.quantum_info',
    'qiskit.quantum.info',
    'quscope.simulations',
    'quscope.simulations.quantum_utils',
    'quscope.simulations.multislice',
    'quscope.simulations.wpo',
]

# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Add logo (optional)
# html_logo = "_static/logo.png"

# Add custom CSS (optional)
def setup(app):
    # Check if the file exists before adding
    css_file = os.path.join(os.path.dirname(__file__), '_static', 'custom.css')
    if os.path.exists(css_file):
        app.add_css_file('custom.css') # create docs/_static/custom.css

# -- Options for nbsphinx ----------------------------------------------------

# Execute notebooks before processing?
# 'always' means always execute
# 'never' means never execute
# 'auto' means execute if no output files are present (good for CI)
nbsphinx_execute = 'auto'

# Allow errors during notebook execution? (Set to True to debug)
nbsphinx_allow_errors = True

# Timeout for notebook execution in seconds
# nbsphinx_timeout = 180 # Increase if notebooks take longer
