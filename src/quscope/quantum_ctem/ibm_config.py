"""
IBM Quantum Account Configuration Utilities

Securely loads IBM Quantum credentials from environment variables.
Credentials are stored in .env file which is NOT committed to version control.

Week 4 Task 1.8: IBM Quantum Integration

Author: QuScope Development Team
Date: January 2025
"""

import os
from pathlib import Path
from typing import Optional


def load_ibm_credentials() -> dict:
    """
    Load IBM Quantum credentials from environment variables.

    Reads credentials from .env file or system environment.
    The .env file should contain:
        IBM_QUANTUM_CRN="crn:v1:bluemix:..."

    Returns:
        Dictionary with IBM Quantum credentials:
        - 'crn': IBM Cloud Resource Name for quantum service
        - 'channel': Quantum channel ('ibm_quantum' or 'ibm_cloud')

    Raises:
        ValueError: If required credentials are not found

    Example:
        >>> creds = load_ibm_credentials()
        >>> print(f"Using CRN: {creds['crn'][:50]}...")
    """
    # Try to load from .env file
    env_file = Path(__file__).parent.parent.parent.parent / ".env"

    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or not line:
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    # Remove quotes if present
                    value = value.strip('"').strip("'")
                    os.environ[key] = value

    # Get CRN from environment
    crn = os.environ.get("IBM_QUANTUM_CRN")

    if not crn:
        raise ValueError(
            "IBM Quantum CRN not found. Please set IBM_QUANTUM_CRN "
            "in .env file or environment variable."
        )

    return {"crn": crn, "channel": "ibm_quantum"}  # Use IBM Quantum channel


def get_ibm_service(backend_name: Optional[str] = None, use_cloud: bool = True):
    """
    Get IBM Quantum service instance with proper authentication.

    Args:
        backend_name: Specific backend to use (e.g., 'ibm_kyoto')
        use_cloud: If True, use IBM Cloud service; if False, use open plan

    Returns:
        QiskitRuntimeService instance configured for your account

    Example:
        >>> service = get_ibm_service()
        >>> backends = service.backends()
        >>> print(f"Available backends: {[b.name for b in backends]}")
    """
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
    except ImportError:
        raise ImportError(
            "qiskit-ibm-runtime not installed. Install with:\n"
            "  pip install qiskit-ibm-runtime"
        )

    creds = load_ibm_credentials()

    if use_cloud:
        # Use IBM Cloud with CRN
        service = QiskitRuntimeService(channel="ibm_cloud", instance=creds["crn"])
    else:
        # Use open plan (requires token instead)
        service = QiskitRuntimeService(channel="ibm_quantum")

    return service


def list_available_backends(show_status: bool = True) -> list:
    """
    List all available IBM Quantum backends for your account.

    Args:
        show_status: If True, print status of each backend

    Returns:
        List of available backend objects

    Example:
        >>> backends = list_available_backends()
        >>> # Use the backend with most qubits
        >>> best = max(backends, key=lambda b: b.num_qubits)
    """
    service = get_ibm_service()
    backends = service.backends()

    if show_status:
        print(f"\n{'='*70}")
        print(f"Available IBM Quantum Backends")
        print(f"{'='*70}\n")

        for backend in backends:
            status = "✓ Online" if backend.status().operational else "✗ Offline"
            pending = backend.status().pending_jobs

            print(
                f"  • {backend.name:25s} | {backend.num_qubits:3d} qubits | "
                f"{status} | {pending:3d} jobs pending"
            )

        print(f"\n{'='*70}\n")

    return backends


def validate_ibm_access() -> bool:
    """
    Validate that IBM Quantum credentials are working.

    Returns:
        True if credentials are valid and can access IBM Quantum

    Example:
        >>> if validate_ibm_access():
        ...     print("✓ IBM Quantum access confirmed!")
    """
    try:
        creds = load_ibm_credentials()
        service = get_ibm_service()
        backends = service.backends()

        print(f"✓ IBM Quantum credentials validated!")
        print(f"  CRN: {creds['crn'][:50]}...")
        print(f"  Available backends: {len(backends)}")

        return True

    except Exception as e:
        print(f"✗ IBM Quantum access failed: {e}")
        return False


# Example usage template for users
def example_usage():
    """
    Example of how to use IBM Quantum credentials in your code.
    """
    print("\n" + "=" * 70)
    print("IBM Quantum Account Configuration - Example Usage")
    print("=" * 70 + "\n")

    # Example 1: Load credentials
    print("1. Loading credentials:")
    print("   from quscope.quantum_ctem.ibm_config import load_ibm_credentials")
    print("   creds = load_ibm_credentials()")
    print("   print(creds['crn'][:50])")

    # Example 2: Get service
    print("\n2. Getting IBM Quantum service:")
    print("   from quscope.quantum_ctem.ibm_config import get_ibm_service")
    print("   service = get_ibm_service()")
    print("   backends = service.backends()")

    # Example 3: List backends
    print("\n3. Listing available backends:")
    print("   from quscope.quantum_ctem.ibm_config import list_available_backends")
    print("   backends = list_available_backends()")

    # Example 4: Submit job
    print("\n4. Submitting a quantum job:")
    print("   from qiskit import QuantumCircuit")
    print("   from qiskit_ibm_runtime import SamplerV2 as Sampler")
    print("   ")
    print("   service = get_ibm_service()")
    print("   backend = service.backend('ibm_kyoto')")
    print("   ")
    print("   # Create circuit")
    print("   qc = QuantumCircuit(2)")
    print("   qc.h(0)")
    print("   qc.cx(0, 1)")
    print("   qc.measure_all()")
    print("   ")
    print("   # Run on real hardware")
    print("   sampler = Sampler(backend)")
    print("   job = sampler.run([qc])")
    print("   result = job.result()")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    """Test IBM Quantum credentials."""
    print("\n🔐 Testing IBM Quantum Credentials...\n")

    if validate_ibm_access():
        print("\n✓ All systems ready for IBM Quantum deployment!")
        print("\nTo use in your code:")
        example_usage()
    else:
        print("\n✗ Please check your IBM Quantum credentials.")
        print("  Make sure .env file exists with IBM_QUANTUM_CRN")
