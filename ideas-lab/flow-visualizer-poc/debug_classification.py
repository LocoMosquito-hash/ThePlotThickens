#!/usr/bin/env python3
"""
Debug POC Classification
=======================

Test if the POC's semantic classification correctly identifies ch4ashbagdone as a decision point.
"""

import sys
import os
from pathlib import Path

# Add the main app directory to path for renpy-source-api imports
current_dir = Path(__file__).parent
app_dir = current_dir.parent.parent / "app"
renpy_api_dir = app_dir / "renpy-source-api"
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(renpy_api_dir))

# Import the VNFlowVisualizer to test its classification
from vn_flow_visualizer import VNFlowVisualizer
from core import RenpyProject

def test_classification():
    """Test semantic classification of menu nodes."""
    
    project_path = r"T:\AG\MySisterMyRoommateV1.69-pc\game"
    
    print("=== POC CLASSIFICATION TEST ===")
    print("=" * 40)
    
    try:
        # Create visualizer instance
        visualizer = VNFlowVisualizer()
        
        # Load flow graph data
        project = RenpyProject(project_path)
        project.analyze()
        flow_graph = project.get_flow_graph()
        
        # Set up visualizer with flow graph
        visualizer.set_flow_graph_data({
            'flow_graph': flow_graph,
            'project_path': project_path
        })
        
        # Check classification of ch4ashbagdone
        classifications = visualizer.semantic_classifications
        ch4_classification = classifications.get('ch4ashbagdone', 'NOT_FOUND')
        
        print(f"ch4ashbagdone classification: '{ch4_classification}'")
        
        # Check if it's classified as decision_point
        if ch4_classification == 'decision_point':
            print("✅ SUCCESS: ch4ashbagdone should appear GOLD!")
        elif ch4_classification == 'linear':
            print("❌ PROBLEM: ch4ashbagdone classified as linear (blue)")
        else:
            print(f"⚠️  UNKNOWN: Unexpected classification '{ch4_classification}'")
        
        # Show all decision_point nodes
        decision_points = [node for node, cls in classifications.items() if cls == 'decision_point']
        print(f"\nTotal decision_point nodes: {len(decision_points)}")
        
        # Show some examples
        for i, node in enumerate(decision_points[:10]):
            print(f"  {i+1}. {node}")
        
        if len(decision_points) > 10:
            print(f"  ... and {len(decision_points) - 10} more")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_classification() 