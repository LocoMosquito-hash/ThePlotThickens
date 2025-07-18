#!/usr/bin/env python3
"""
SDK Test Runner

Run this script to test Ren'Py SDK integration.
Usage: python run_tests.py
"""

import sys
import os
from pathlib import Path

def main():
    """Run the SDK integration tests."""
    # Add the tests directory to the path
    current_dir = Path(__file__).parent
    tests_dir = current_dir / "tests"
    
    if not tests_dir.exists():
        print("❌ Tests directory not found!")
        return False
    
    sys.path.insert(0, str(tests_dir))
    
    try:
        # Import and run the basic test
        import test_basic_sdk
        success = test_basic_sdk.main()
        return success
    except ImportError as e:
        print(f"❌ Could not import test module: {e}")
        return False
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False

if __name__ == "__main__":
    print("Ren'Py SDK Integration Test Runner")
    print("="*50)
    success = main()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        exit(0)
    else:
        print("\n💥 Tests failed!")
        exit(1) 