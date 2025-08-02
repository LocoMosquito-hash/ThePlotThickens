#!/usr/bin/env python3
"""
Test Script for Label Menu Detection
====================================

This script examines how label menus are detected and what information
is available in MenuStructure objects, specifically looking for the
"menu day02_p_room_choices:" case.
"""

import sys
import os
from pathlib import Path

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to import the adapter we're already using
try:
    from renpy_data_adapter import RenpyFlowDataAdapter
    print("✅ Successfully imported RenpyFlowDataAdapter")
except ImportError as e:
    print(f"Import error with data adapter: {e}")
    sys.exit(1)

def test_sisterly_lust_label_menus():
    """Test label menu detection with SisterlyLust."""
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    if not os.path.exists(project_path):
        print(f"ERROR: Project path not found: {project_path}")
        return
    
    print(f"🔍 Analyzing label menus in: {project_path}")
    print("=" * 60)
    
    # Use the existing data adapter
    adapter = RenpyFlowDataAdapter(use_hybrid=True)
    
    try:
        print(f"\n📊 Analyzing project with data adapter...")
        visualization_data = adapter.analyze_project(project_path)
        
        print(f"Total nodes found: {len(visualization_data.nodes)}")
        print(f"Total connections: {len(visualization_data.connections)}")
        
        # Look for menu containers specifically
        menu_containers = [node for node in visualization_data.nodes if node.node_type == 'menu_container']
        print(f"Menu containers found: {len(menu_containers)}")
        
        # Look for any nodes that might be our target label menu
        target_containers = []
        for container in menu_containers:
            if "day02" in container.node_id.lower():
                print(f"\n🎯 Day02 Menu Container:")
                print(f"   ID: {container.node_id}")
                print(f"   Display Name: {container.display_name}")
                print(f"   Color: {container.color_hint}")
                print(f"   Metadata: {container.metadata}")
                
                if "room" in container.node_id.lower() or "room" in container.display_name.lower():
                    target_containers.append(container)
                    print(f"   ✅ POTENTIAL TARGET (contains 'room')")
        
        # Look for any orphan nodes that might be our missing label menu
        orphan_nodes = []
        connected_node_ids = set()
        for conn in visualization_data.connections:
            connected_node_ids.add(conn.source_node_id)
            connected_node_ids.add(conn.target_node_id)
        
        for node in visualization_data.nodes:
            if node.node_id not in connected_node_ids:
                orphan_nodes.append(node)
        
        print(f"\n🔍 Orphan nodes found: {len(orphan_nodes)}")
        orphan_day02_nodes = [node for node in orphan_nodes if "day02" in node.node_id.lower()]
        print(f"Day02 orphan nodes: {len(orphan_day02_nodes)}")
        
        for node in orphan_day02_nodes:
            print(f"   📋 Orphan: {node.node_id} ({node.display_name})")
            if "room" in node.node_id.lower() or "living" in node.node_id.lower():
                print(f"      🎯 POSSIBLE LABEL MENU!")
    
    except Exception as e:
        print(f"ERROR analyzing project: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sisterly_lust_label_menus() 