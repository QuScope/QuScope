# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# Ensure proper path configuration for quscope package
# Handle both CI environment (PYTHONPATH set) and local development

# Check if we're in a CI environment with PYTHONPATH
pythonpath_env = os.environ.get('PYTHONPATH', '')
if pythonpath_env:
    print(f"Using PYTHONPATH from environment: {pythonpath_env}")
    # Add paths from PYTHONPATH if not already in sys.path
    for path in pythonpath_env.split(os.pathsep):
        if path and path not in sys.path:
            sys.path.insert(0, path)
            print(f"Added from PYTHONPATH: {path}")

# Also set up local paths for development
project_root = os.path.abspath('..')
src_directory = os.path.join(project_root, 'src')

print(f"Project root: {project_root}")
print(f"Source directory: {src_directory}")
print(f"Current working directory: {os.getcwd()}")

# Add source directory to Python path if not already there
if src_directory not in sys.path:
    sys.path.insert(0, src_directory)
    print(f"Added {src_directory} to Python path")

print(f"Current Python path: {sys.path[:3]}...")  # Show first 3 entries

# Verify the quscope module structure
quscope_path = os.path.join(src_directory, 'quscope')
if os.path.exists(quscope_path):
    print(f"Found quscope directory: {quscope_path}")
    print(f"quscope contents: {os.listdir(quscope_path)}")
else:
    print(f"quscope directory not found at: {quscope_path}")

# Try to import quscope
print("=== QuScope Import Attempt ===")
try:
    import quscope
    print(f"✅ Successfully imported quscope")
    if hasattr(quscope, '__version__'):
        print(f"Version: {quscope.__version__}")
    else:
        print("No version attribute found")
    
    # Test submodule imports to ensure they work
    try:
        from quscope import image_processing
        print("✅ image_processing import successful")
    except ImportError as sub_e:
        print(f"⚠️  image_processing import failed: {sub_e}")
        
    try:
        from quscope import qml
        print("✅ qml import successful")
    except ImportError as sub_e:
        print(f"⚠️  qml import failed: {sub_e}")
        
except ImportError as e:
    print(f"❌ Failed to import quscope: {e}")
    print(f"Python path: {sys.path}")
    
    # Debug information
    if os.path.exists(src_directory):
        print(f"Contents of src: {os.listdir(src_directory)}")
    if os.path.exists(quscope_path):
        print(f"Contents of quscope: {os.listdir(quscope_path)}")
        init_file = os.path.join(quscope_path, '__init__.py')
        if os.path.exists(init_file):
            print(f"__init__.py exists: {init_file}")
            # Try to read the first few lines to debug
            try:
                with open(init_file, 'r') as f:
                    first_lines = [f.readline().strip() for _ in range(5)]
                print(f"First lines of __init__.py: {first_lines}")
            except Exception as read_e:
                print(f"Could not read __init__.py: {read_e}")
        else:
            print(f"__init__.py missing: {init_file}")
            
    # Final attempt with explicit import
    print("=== Attempting manual import with error details ===")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("quscope", os.path.join(quscope_path, "__init__.py"))
        if spec and spec.loader:
            quscope_module = importlib.util.module_from_spec(spec)
            sys.modules["quscope"] = quscope_module
            spec.loader.exec_module(quscope_module)
            print("✅ Manual import successful")
        else:
            print("❌ Could not create module spec")
    except Exception as manual_e:
        print(f"❌ Manual import failed: {manual_e}")
        import traceback
        traceback.print_exc()

print("=== End Import Attempt ===\n")

# -- Project information -----------------------------------------------------

project = 'QuScope'
copyright = '2025, Roberto Reis'
author = 'Roberto Reis'

version = '0.1.0'
release = '0.1.0'

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',       # Include documentation from docstrings
    'sphinx.ext.autosummary',   # Generate summary tables for modules/classes/methods
    'sphinx.ext.napoleon',      # Support for Google and NumPy style docstrings
    'sphinx.ext.intersphinx',   # Link to other projects' documentation
    'sphinx.ext.viewcode',      # Add links to source code
    'nbsphinx',               # Include Jupyter notebooks
    'myst_parser',            # Parse Markdown files like README.md
    'sphinx_rtd_theme',      # Read the Docs theme
    'sphinx.ext.githubpages', # Support for GitHub Pages
]

autodoc_member_order = 'bysource'

autosummary_generate = True  # Enable automatic generation of stub files

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

source_suffix = ['.rst', '.md']

templates_path = ['_templates']
exclude_patterns = [
    '_build', 
    'Thumbs.db', 
    '.DS_Store', 
    '**.ipynb_checkpoints',
    'requirements.txt' # Exclude the docs requirements file itself
]

# Mock imports for problematic dependencies - expanded list
autodoc_mock_imports = [
    # Core quantum computing
    "qiskit", 
    "qiskit.circuit",
    "qiskit.quantum_info",
    "qiskit.providers",
    "qiskit.result",
    "qiskit.exceptions",
    "qiskit_aer",
    "qiskit.providers.aer",
    "qiskit.circuit.library",
    "qiskit_ibm_provider",
    "qiskit_algorithms",
    
    # Machine learning and data science
    "torch", 
    "sklearn", 
    "sklearn.cluster",
    "scikit-learn",
    
    # Scientific computing
    "scipy",
    "scipy.ndimage",
    "scipy.signal",
    "scipy.optimize",
    "scipy.stats",
    
    # Image processing
    "PIL",
    "Pillow",
    
    # Plotting
    "matplotlib",
    "matplotlib.pyplot",
    
    # Other optional dependencies
    "pandas",
    "seaborn",
    "plotly",
]

# Additional mock for matplotlib.pyplot specifically
import sys
from unittest.mock import MagicMock

class MockFigure:
    """Mock matplotlib Figure class."""
    def __init__(self, *args, **kwargs):
        pass
    
    def __getattr__(self, name):
        return MagicMock()
    
    def add_subplot(self, *args, **kwargs):
        return MagicMock()
    
    def savefig(self, *args, **kwargs):
        pass
    
    def show(self):
        pass

class MockMatplotlib:
    """Mock matplotlib for documentation building."""
    def __init__(self):
        self.pyplot = MagicMock()
        self.figure = MagicMock()
        self.Figure = MockFigure
        
        # Mock pyplot functions
        self.pyplot.figure = MagicMock(return_value=MockFigure())
        self.pyplot.subplot = MagicMock()
        self.pyplot.show = MagicMock()
        self.pyplot.savefig = MagicMock()
        self.pyplot.imshow = MagicMock()
        self.pyplot.plot = MagicMock()
        self.pyplot.scatter = MagicMock()
    
    def __getattr__(self, name):
        return MagicMock()

# Mock modules that might not be available during docs build
mock_modules = {
    'matplotlib': MockMatplotlib(),
    'matplotlib.pyplot': MockMatplotlib().pyplot,
    'matplotlib.figure': type('MockModule', (), {'Figure': MockFigure})(),
}

for module_name, mock_obj in mock_modules.items():
    if module_name not in sys.modules:
        sys.modules[module_name] = mock_obj

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
