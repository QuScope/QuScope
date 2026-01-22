"""Test import resilience and defensive import patterns."""

import pytest


def test_quscope_imports_without_error():
    """Test that quscope can be imported without raising errors."""
    import quscope
    
    assert hasattr(quscope, "__version__")
    assert isinstance(quscope.__all__, list)
    assert "__version__" in quscope.__all__


def test_image_processing_imports_without_error():
    """Test that image_processing subpackage can be imported."""
    from quscope import image_processing
    
    assert isinstance(image_processing.__all__, list)


def test_qml_imports_without_error():
    """Test that qml subpackage can be imported."""
    from quscope import qml
    
    assert isinstance(qml.__all__, list)


def test_core_functions_available_when_dependencies_present():
    """Test that core functions are available when dependencies are present."""
    import quscope
    
    # These should be available when numpy and qiskit are installed
    assert hasattr(quscope, "encode_image_to_circuit")
    assert hasattr(quscope, "EncodingMethod")
    assert hasattr(quscope, "validate_image_array")
    assert hasattr(quscope, "calculate_required_qubits")
    assert hasattr(quscope, "preprocess_image")
    assert hasattr(quscope, "binarize_image")


def test_lazy_backend_import():
    """Test that quantum backend is accessible via lazy import."""
    import quscope
    
    # Test lazy module access
    qb = quscope.quantum_backend
    assert hasattr(qb, "QuantumBackendManager")
    
    # Test lazy class access
    backend_manager_class = quscope.QuantumBackendManager
    assert backend_manager_class.__name__ == "QuantumBackendManager"


def test_image_processing_all_reflects_available_modules():
    """Test that __all__ in image_processing only contains successfully imported symbols."""
    from quscope import image_processing
    
    # All items in __all__ should be importable
    for name in image_processing.__all__:
        assert hasattr(image_processing, name), f"{name} not available in image_processing"


def test_quscope_all_reflects_available_modules():
    """Test that __all__ in quscope only contains successfully imported symbols."""
    import quscope
    
    # All items in __all__ should be accessible
    for name in quscope.__all__:
        assert hasattr(quscope, name), f"{name} not available in quscope"


def test_qml_lazy_import_pattern():
    """Test that qml uses lazy imports correctly."""
    from quscope import qml
    
    # qml should have an empty __all__ since it uses lazy loading
    assert qml.__all__ == []
    
    # But it should have __getattr__ for lazy loading
    assert hasattr(qml, "__getattr__")
