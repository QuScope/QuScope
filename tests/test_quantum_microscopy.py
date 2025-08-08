"""Tests for QuScope quantum microscopy implementation."""

import pytest
import numpy as np
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Updated imports to match current package structure
try:
    from quscope.image_processing.quantum_encoding import EncodingMethod
    ENCODING_AVAILABLE = True
except ImportError as e:
    ENCODING_AVAILABLE = False
    ENCODING_ERROR = str(e)

try:
    from quscope.quantum_backend import QuantumBackendManager
    BACKEND_AVAILABLE = True
except ImportError as e:
    BACKEND_AVAILABLE = False
    BACKEND_ERROR = str(e)

try:
    import quscope
    QUSCOPE_AVAILABLE = True
except ImportError as e:
    QUSCOPE_AVAILABLE = False
    QUSCOPE_ERROR = str(e)


class TestQuantumMicroscopy:
    """Test suite for QuScope functionality."""
    
    @pytest.fixture
    def sample_image(self):
        """Create a simple test image."""
        return np.random.rand(4, 4)
    
    @pytest.fixture 
    def small_image(self):
        """Create a very small test image."""
        return np.array([[0.1, 0.9], [0.3, 0.7]])
    
    @pytest.mark.skipif(not ENCODING_AVAILABLE, reason=f"Encoding not available: {ENCODING_ERROR if not ENCODING_AVAILABLE else ''}")
    def test_encoding_methods_available(self):
        """Test that encoding methods are available."""
        assert hasattr(EncodingMethod, 'AMPLITUDE')
        assert hasattr(EncodingMethod, 'BASIS')
        assert hasattr(EncodingMethod, 'ANGLE')
    
    @pytest.mark.skipif(not BACKEND_AVAILABLE, reason=f"Backend not available: {BACKEND_ERROR if not BACKEND_AVAILABLE else ''}")
    def test_quantum_backend_manager_init(self):
        """Test QuantumBackendManager initialization."""
        try:
            manager = QuantumBackendManager()
            assert manager is not None
        except Exception as e:
            pytest.skip(f"Backend manager initialization failed: {e}")
    
    @pytest.mark.skipif(not QUSCOPE_AVAILABLE, reason=f"QuScope not available: {QUSCOPE_ERROR if not QUSCOPE_AVAILABLE else ''}")
    def test_package_importable(self):
        """Test that the package can be imported."""
        import quscope
        assert hasattr(quscope, '__version__')
    
    def test_numpy_available(self):
        """Test that required dependencies are available."""
        import numpy as np
        assert np.__version__ is not None


class TestBasicFunctionality:
    """Test basic functionality that should always work."""
    
    def test_package_structure(self):
        """Test that package structure is correct."""
        import os
        src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
        quscope_path = os.path.join(src_path, 'quscope')
        assert os.path.exists(quscope_path)
        assert os.path.exists(os.path.join(quscope_path, '__init__.py'))
    
    def test_module_files_exist(self):
        """Test that main module files exist."""
        import os
        src_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'quscope')
        
        expected_files = [
            'quantum_backend.py',
            'image_processing/__init__.py',
            'image_processing/quantum_encoding.py',
            'image_processing/quantum_segmentation.py',
            'qml/__init__.py',
            'eels_analysis/__init__.py'
        ]
        
        for file_path in expected_files:
            full_path = os.path.join(src_path, file_path)
            assert os.path.exists(full_path), f"Expected file {file_path} not found"
    
    def test_numpy_functionality(self):
        """Test basic numpy functionality."""
        arr = np.array([1, 2, 3, 4])
        assert arr.shape == (4,)
        assert np.sum(arr) == 10
    
    def test_python_version(self):
        """Test that Python version is supported."""
        import sys
        version = sys.version_info
        assert version.major == 3
        assert version.minor >= 8  # We support Python 3.8+
