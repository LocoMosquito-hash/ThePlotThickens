#!/usr/bin/env python3
"""
Test script to isolate the visualizer integration error
"""

import sys
import traceback
from PyQt6.QtWidgets import QApplication
from renpy_data_adapter import RenpyFlowDataAdapter
from vn_flow_visualizer_v2_simple import VNFlowVisualizerV2Simple

def test_visualizer_with_data():
    """Test the visualizer with actual data loading."""
    
    print("Testing visualizer with data loading...")
    
    try:
        # First get the data
        adapter = RenpyFlowDataAdapter(use_hybrid=True)
        print("✅ Data adapter created")
        
        question_path = r"C:\Users\juanc\PycharmProjects\TPT3\ThePlotThickens\app\renpy-source-api\renpy_sdk\renpy-8.4.0-sdk\the_question\game"
        
        print(f"🔍 Analyzing project: {question_path}")
        visualization_data = adapter.analyze_project(question_path, use_sdk=True)
        print("✅ Analysis completed")
        
        # Now test the visualizer
        app = QApplication(sys.argv)
        print("✅ QApplication created")
        
        visualizer = VNFlowVisualizerV2Simple()
        print("✅ Visualizer created")
        
        print("🔍 Loading data into visualizer...")
        visualizer.load_flow_data(visualization_data)
        print("✅ Data loaded into visualizer successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during visualizer integration: {e}")
        print(f"❌ Exception type: {type(e)}")
        print("❌ Full traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_visualizer_with_data()
    print(f"\nResult: {'✅ PASSED' if success else '❌ FAILED'}") 