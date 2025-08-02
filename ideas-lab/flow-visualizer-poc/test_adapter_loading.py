#!/usr/bin/env python3
"""
Test Data Adapter Loading
=========================

Simple test to verify our data adapter is being loaded correctly.
"""

import sys
import os

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_adapter_loading():
    """Test if our data adapter modifications are loaded."""
    print("Testing data adapter loading...")
    
    try:
        from renpy_data_adapter import RenpyFlowDataAdapter
        
        # Create adapter 
        adapter = RenpyFlowDataAdapter(use_hybrid=True)
        
        # Check if our method exists
        if hasattr(adapter, '_convert_flows_to_connections'):
            print("SUCCESS: _convert_flows_to_connections method found")
            
            # Try to read the method source to see if our debug code is there
            import inspect
            source = inspect.getsource(adapter._convert_flows_to_connections)
            if "DEBUG CONVERT" in source:
                print("SUCCESS: Our debug modifications are loaded")
            else:
                print("FAILURE: Debug modifications NOT found in loaded method")
                print("Method source preview:")
                print(source[:200] + "...")
        else:
            print("FAILURE: _convert_flows_to_connections method NOT found")
            
        print(f"Adapter class: {adapter.__class__}")
        print(f"Module: {adapter.__class__.__module__}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_adapter_loading() 