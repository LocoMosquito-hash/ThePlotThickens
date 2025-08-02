#!/usr/bin/env python3
"""
Debug Label Menu Integration
============================

This script checks if our label menu detection and coloring logic
is actually being executed in the data adapter.
"""

import sys
import os

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_label_menu_integration():
    """Debug label menu integration in the data adapter."""
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    if not os.path.exists(project_path):
        print(f"ERROR: Project path not found: {project_path}")
        return
    
    print(f"🔍 Debugging label menu integration for: {project_path}")
    print("=" * 60)
    
    try:
        from renpy_data_adapter import RenpyFlowDataAdapter
        
        # Create adapter and analyze
        adapter = RenpyFlowDataAdapter(use_hybrid=True)
        visualization_data = adapter.analyze_project(project_path)
        
        print(f"\n📊 Total nodes: {len(visualization_data.nodes)}")
        print(f"📊 Total connections: {len(visualization_data.connections)}")
        
        # Look specifically for day02_p_room_choices
        target_node = None
        for node in visualization_data.nodes:
            if node.node_id == "day02_p_room_choices":
                target_node = node
                break
        
        if target_node:
            print(f"\n🎯 FOUND day02_p_room_choices:")
            print(f"   Node ID: {target_node.node_id}")
            print(f"   Display Name: {target_node.display_name}")
            print(f"   Node Type: {target_node.node_type}")
            print(f"   Color Hint: {target_node.color_hint}")
            print(f"   Metadata: {target_node.metadata}")
            
            # Check if it's detected as a label menu
            is_label_menu = target_node.metadata.get('is_label_menu', False)
            label_name = target_node.metadata.get('label_name', 'None')
            print(f"   Is Label Menu: {is_label_menu}")
            print(f"   Label Name: {label_name}")
            
            if target_node.color_hint != '#FFD700':
                print(f"   ❌ ISSUE: Expected goldish color #FFD700, got {target_node.color_hint}")
            else:
                print(f"   ✅ Color is correct: {target_node.color_hint}")
        else:
            print(f"\n❌ day02_p_room_choices NOT FOUND in visualization nodes")
            
            # Check if it exists with a different name
            print(f"\n🔍 All nodes containing 'day02_p_room':")
            matching_nodes = [n for n in visualization_data.nodes if 'day02_p_room' in n.node_id]
            for node in matching_nodes:
                print(f"   - {node.node_id} (type: {node.node_type}, color: {node.color_hint})")
        
        # Check connections TO day02_p_room_choices
        print(f"\n🔗 Connections TO day02_p_room_choices:")
        incoming_connections = [c for c in visualization_data.connections if c.target_node_id == "day02_p_room_choices"]
        if incoming_connections:
            for conn in incoming_connections:
                print(f"   {conn.source_node_id} -> {conn.target_node_id} (type: {conn.connection_type})")
        else:
            print(f"   ❌ No incoming connections found (explains orphan status)")
        
        # Check connections FROM day02_l_conversation
        print(f"\n🔗 Connections FROM day02_l_conversation:")
        outgoing_connections = [c for c in visualization_data.connections if c.source_node_id == "day02_l_conversation"]
        if outgoing_connections:
            for conn in outgoing_connections:
                print(f"   {conn.source_node_id} -> {conn.target_node_id} (type: {conn.connection_type})")
        else:
            print(f"   ❌ No outgoing connections from day02_l_conversation")
        
        print(f"\n📋 Summary:")
        print(f"   - Label menu naming: {'✅ Working' if target_node else '❌ Not found'}")
        print(f"   - Goldish color: {'✅ Working' if target_node and target_node.color_hint == '#FFD700' else '❌ Not working'}")
        print(f"   - Parent connection: {'✅ Working' if incoming_connections else '❌ Missing'}")
        
    except Exception as e:
        print(f"ERROR during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_label_menu_integration() 