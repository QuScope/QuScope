#!/usr/bin/env python3
"""
Test IBM Quantum Credentials Setup

This script tests that your IBM Quantum credentials are properly configured
and can be used to access IBM Quantum services.

Run this to verify your setup:
    python test_ibm_setup.py

Author: QuScope Development Team
Date: January 2025
"""

from quscope.quantum_ctem import (
    load_ibm_credentials,
    validate_ibm_deployment,
    IBMHardwareValidator,
    IBMDeviceProfile
)


def test_credentials():
    """Test that credentials can be loaded."""
    print("\n" + "="*70)
    print("TEST 1: Loading IBM Quantum Credentials")
    print("="*70)
    
    try:
        creds = load_ibm_credentials()
        print(f"✓ CRN loaded successfully")
        print(f"  CRN: {creds['crn'][:50]}...")
        print(f"  Channel: {creds['channel']}")
        return True
    except Exception as e:
        print(f"✗ Failed to load credentials: {e}")
        return False


def test_device_profiles():
    """Test that device profiles are available."""
    print("\n" + "="*70)
    print("TEST 2: IBM Device Profiles")
    print("="*70)
    
    try:
        devices = [
            IBMDeviceProfile.ibm_kyoto(),
            IBMDeviceProfile.ibm_brisbane(),
            IBMDeviceProfile.ibm_nazca(),
            IBMDeviceProfile.ibm_sherbrooke()
        ]
        
        print(f"✓ All 4 device profiles loaded")
        for device in devices:
            print(f"  • {device.name}: {device.num_qubits} qubits, "
                  f"T2={device.t2_us}µs")
        return True
    except Exception as e:
        print(f"✗ Failed to load device profiles: {e}")
        return False


def test_validation():
    """Test quantum CTEM validation for IBM hardware."""
    print("\n" + "="*70)
    print("TEST 3: Quantum CTEM Validation for IBM Hardware")
    print("="*70)
    
    try:
        # Test with small circuit (fast)
        print("  Testing 4-qubit circuit on IBM Kyoto...")
        results = validate_ibm_deployment('ibm_kyoto', n_qubits=4)
        
        print(f"✓ Validation successful")
        print(f"  Estimated Fidelity: {results['estimated_fidelity']:.1%}")
        print(f"  Circuit Depth: {results['transpiled_depth']}")
        print(f"  Execution Time: {results['execution_time_us']:.1f} µs")
        return True
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        return False


def test_device_comparison():
    """Test device comparison feature."""
    print("\n" + "="*70)
    print("TEST 4: Device Comparison")
    print("="*70)
    
    try:
        validator = IBMHardwareValidator()
        comparison = validator.compare_devices(n_qubits=4)
        
        print(f"✓ Compared {len(comparison)} devices")
        
        # Sort by fidelity
        sorted_devices = sorted(
            comparison.items(),
            key=lambda x: x[1]['estimated_fidelity'],
            reverse=True
        )
        
        print("\n  Device Rankings (by fidelity):")
        for rank, (device_name, results) in enumerate(sorted_devices, 1):
            fid = results['estimated_fidelity']
            icon = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
            print(f"    {icon} {rank}. {device_name:20s} - {fid:6.2%}")
        
        best_device = sorted_devices[0][0]
        print(f"\n  Recommendation: Use {best_device} for best results")
        return True
    except Exception as e:
        print(f"✗ Device comparison failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("IBM QUANTUM CREDENTIALS & SETUP TEST SUITE")
    print("="*70)
    print("\nThis will test your IBM Quantum setup without connecting")
    print("to real IBM Quantum servers (using local validation only).")
    
    results = []
    
    # Run all tests
    results.append(("Load Credentials", test_credentials()))
    results.append(("Device Profiles", test_device_profiles()))
    results.append(("CTEM Validation", test_validation()))
    results.append(("Device Comparison", test_device_comparison()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70 + "\n")
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status:8s} - {test_name}")
    
    total_passed = sum(passed for _, passed in results)
    total_tests = len(results)
    
    print(f"\n  Total: {total_passed}/{total_tests} tests passed "
          f"({100*total_passed/total_tests:.0f}%)")
    
    if total_passed == total_tests:
        print("\n✅ All tests passed! Your IBM Quantum setup is ready.")
        print("\nNext steps:")
        print("  1. See docs/IBM_QUANTUM_SETUP.md for usage examples")
        print("  2. Try: validate_ibm_access() to test real connection")
        print("  3. Try: list_available_backends() to see quantum computers")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
    
    print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    main()
