#!/usr/bin/env python3
"""
Minimal test to isolate the QGraphicsScene callable error
"""

import sys
import traceback
from PyQt6.QtWidgets import QApplication
from renpy_flow_visualizer_v2_main import RenpyFlowMapperV2

def test_basic_ui():
    """Test basic UI functionality to isolate the error."""
    
    print("Testing basic UI functionality...")
    
    try:
        app = QApplication(sys.argv)
        
        print("✅ QApplication created successfully")
        
        # Create main window
        window = RenpyFlowMapperV2()
        print("✅ Main window created successfully")
        
        # Show the window
        window.show()
        print("✅ Window shown successfully")
        
        # Try to trigger the load project functionality
        print("\n🔍 Attempting to trigger load project...")
        
        # Just return here to test if basic creation works
        print("✅ Basic UI test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error during basic UI test: {e}")
        print(f"❌ Exception type: {type(e)}")
        print("❌ Full traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_basic_ui() 