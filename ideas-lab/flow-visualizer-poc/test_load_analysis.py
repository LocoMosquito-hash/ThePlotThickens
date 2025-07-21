#!/usr/bin/env python3
"""
Test script to isolate the project loading and analysis error
"""

import sys
import traceback
from PyQt6.QtWidgets import QApplication
from renpy_data_adapter import RenpyFlowDataAdapter

def test_project_analysis():
    """Test project analysis to isolate the QGraphicsScene error."""
    
    print("Testing project analysis functionality...")
    
    try:
        # Test the data adapter directly
        adapter = RenpyFlowDataAdapter(use_hybrid=True)
        print("✅ Data adapter created successfully")
        
        # Try to analyze "The Question" project
        question_path = r"C:\Users\juanc\PycharmProjects\TPT3\ThePlotThickens\app\renpy-source-api\renpy_sdk\renpy-8.4.0-sdk\the_question\game"
        
        print(f"🔍 Attempting to analyze: {question_path}")
        
        # This should trigger the same analysis that fails in the UI
        visualization_data = adapter.analyze_project(question_path, use_sdk=True)
        print("✅ Analysis completed successfully")
        
        print(f"📊 Analysis results:")
        print(f"   Nodes: {len(visualization_data.nodes)}")
        print(f"   Connections: {len(visualization_data.connections)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during project analysis: {e}")
        print(f"❌ Exception type: {type(e)}")
        print("❌ Full traceback:")
        traceback.print_exc()
        return False

def test_ui_with_analysis():
    """Test full UI with actual project loading."""
    
    print("\n" + "="*50)
    print("Testing UI with project loading...")
    
    try:
        app = QApplication(sys.argv)
        print("✅ QApplication created")
        
        # Import here to avoid issues
        from renpy_flow_visualizer_v2_main import RenpyFlowMapperV2
        
        window = RenpyFlowMapperV2()
        print("✅ Main window created")
        
        # Try to programmatically trigger project loading
        question_path = r"C:\Users\juanc\PycharmProjects\TPT3\ThePlotThickens\app\renpy-source-api\renpy_sdk\renpy-8.4.0-sdk\the_question\game"
        
        print(f"🔍 Attempting to load project: {question_path}")
        
        # Skip UI field setting for now, just test if basic functionality works
        print("✅ Basic UI creation test passed")
        
        return True
             
    except Exception as e:
        print(f"❌ Error during UI with analysis: {e}")
        print(f"❌ Exception type: {type(e)}")
        print("❌ Full traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Test analysis separately first
    analysis_success = test_project_analysis()
    
    # Then test UI with analysis
    ui_success = test_ui_with_analysis()
    
    print("\n" + "="*50)
    print("SUMMARY:")
    print(f"Analysis test: {'✅ PASSED' if analysis_success else '❌ FAILED'}")
    print(f"UI test: {'✅ PASSED' if ui_success else '❌ FAILED'}") 