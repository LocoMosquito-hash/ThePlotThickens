#!/usr/bin/env python3
"""
Simple Fix Test
===============

Test if our missing _convert_flows_to_connections fix works.
"""

import sys
import os

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_fix():
    """Simple test without Unicode symbols."""
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    if not os.path.exists(project_path):
        print(f"ERROR: Project path not found: {project_path}")
        return
    
    print("Testing fix...")
    print("=" * 50)
    
    try:
        from renpy_data_adapter import RenpyFlowDataAdapter
        
        # Create adapter
        adapter = RenpyFlowDataAdapter(use_hybrid=True)
        
        # Clear debug log
        try:
            os.remove("debug_adapter.log")
        except:
            pass
        
        # Analyze project
        print("Starting analysis...")
        visualization_data = adapter.analyze_project(project_path)
        
        print(f"Analysis complete!")
        print(f"Nodes: {len(visualization_data.nodes)}")
        print(f"Connections: {len(visualization_data.connections)}")
        
        # Check for day02_p_room_choices connections
        day02_connections = [
            conn for conn in visualization_data.connections 
            if conn.target_node_id == 'day02_p_room_choices'
        ]
        
        print(f"Connections TO day02_p_room_choices: {len(day02_connections)}")
        for conn in day02_connections:
            print(f"   {conn.source_node_id} -> {conn.target_node_id}")
        
        # Check debug log
        if os.path.exists("debug_adapter.log"):
            print("\nDebug log contents:")
            with open("debug_adapter.log", "r") as f:
                for line in f:
                    if "DEBUG" in line:
                        print(f"   {line.strip()}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fix() 