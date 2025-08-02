#!/usr/bin/env python3
"""
Simple Test for Multiple Parent Label Menu Support
===============================================

Test script to verify that label menus can properly handle multiple
incoming connections from different sources.
"""

import sys
import os

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_multiple_parents():
    """Test multiple parent connections for label menus."""
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    if not os.path.exists(project_path):
        print(f"ERROR: Project path not found: {project_path}")
        return
    
    print("Testing multiple parents for label menus...")
    print("=" * 60)
    
    # Use the existing data adapter
    try:
        from renpy_data_adapter import RenpyFlowDataAdapter
        adapter = RenpyFlowDataAdapter(use_hybrid=True)
        
        print("\nAnalyzing project with data adapter...")
        visualization_data = adapter.analyze_project(project_path)
        
        # Test case: day02_p_room_choices
        target_menu = "day02_p_room_choices"
        target_node = next((node for node in visualization_data.nodes 
                           if node.node_id == target_menu), None)
        
        if not target_node:
            print(f"\nERROR: Target menu '{target_menu}' not found!")
            return
        
        print(f"\nAnalyzing connections for: {target_menu}")
        print(f"   Display: {target_node.display_name}")
        print(f"   Color: {target_node.color_hint}")
        print(f"   Type: {target_node.node_type}")
        
        # Find all incoming connections to this label menu
        incoming_connections = [conn for conn in visualization_data.connections 
                               if conn.target_node_id == target_menu]
        
        print(f"\nIncoming connections ({len(incoming_connections)}):")
        for conn in incoming_connections:
            source_node = next((node for node in visualization_data.nodes 
                               if node.node_id == conn.source_node_id), None)
            source_type = source_node.node_type if source_node else "unknown"
            print(f"   - FROM: {conn.source_node_id} ({source_type})")
            print(f"     Type: {conn.connection_type}")
        
        # Check for the expected connection from day02_l_conversation
        expected_source = "day02_l_conversation"
        has_expected_connection = any(conn.source_node_id == expected_source 
                                     for conn in incoming_connections)
        
        if has_expected_connection:
            print(f"\n✅ SUCCESS: Found expected connection from {expected_source}")
        else:
            print(f"\n❌ MISSING: No connection from {expected_source}")
            
        # Report results
        print(f"\nResults:")
        print(f"   Total incoming connections: {len(incoming_connections)}")
        print(f"   Has multiple parents: {'Yes' if len(incoming_connections) > 1 else 'No'}")
        
    except Exception as e:
        print(f"ERROR during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_multiple_parents() 