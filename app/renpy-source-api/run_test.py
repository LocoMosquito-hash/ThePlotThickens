#!/usr/bin/env python3
"""
Alternative test runner for the Ren'Py Source API.

This script handles imports more robustly for different execution contexts.
"""

import os
import sys
from pathlib import Path

# Ensure proper imports regardless of execution context
script_dir = Path(__file__).parent.absolute()
parent_dir = script_dir.parent.parent
sys.path.insert(0, str(parent_dir))
sys.path.insert(0, str(script_dir))

def main():
    """Main test execution."""
    print("🚀 Starting Ren'Py API tests (alternative runner)...")
    
    try:
        # Import and run the main test
        from test_renpy_api import test_basic_functionality, export_sample_data
        
        # Run the tests
        success = test_basic_functionality()
        
        if success:
            # Ask if user wants to export sample data
            try:
                response = input("\n❓ Export sample analysis data to JSON? (y/n): ").lower().strip()
                if response in ['y', 'yes']:
                    export_sample_data()
            except KeyboardInterrupt:
                print("\n\n👋 Test completed!")
        
        return success
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Tests completed successfully!")
    else:
        print("\n❌ Tests failed - check the error messages above.") 