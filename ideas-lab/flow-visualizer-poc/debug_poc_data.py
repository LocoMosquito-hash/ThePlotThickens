#!/usr/bin/env python3
"""
Debug POC Flow Graph Data
========================

This diagnostic checks what flow graph data the POC is receiving
to verify our menu container fixes are working.
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

from core import RenpyProject

def debug_poc_flow_data():
    """Debug what flow graph data the POC receives."""
    
    project_path = r"T:\AG\MySisterMyRoommateV1.69-pc\game"
    
    print("=== POC FLOW GRAPH DATA DIAGNOSTIC ===")
    print("=" * 50)
    
    try:
        # Load project (same as POC does)
        print("1. Loading Ren'Py project...")
        project = RenpyProject(project_path)
        project.analyze()
        
        # Get flow graph (same as POC does)
        print("2. Getting flow graph...")
        flow_graph = project.get_flow_graph()
        
        print(f"   Total labels in flow graph: {len(flow_graph)}")
        
        # Check for ch4ashbagdone specifically
        print("\n3. Checking ch4ashbagdone...")
        if 'ch4ashbagdone' in flow_graph:
            ch4_data = flow_graph['ch4ashbagdone']
            print(f"   ✅ Found ch4ashbagdone")
            print(f"   Has menu: {ch4_data.get('has_menu', False)}")
            print(f"   Outgoing flows: {len(ch4_data.get('outgoing_flows', []))}")
            
            # Check outgoing flows
            flows = ch4_data.get('outgoing_flows', [])
            for i, flow in enumerate(flows):
                flow_type = flow.get('flow_type', 'UNKNOWN')
                target = flow.get('target_label', 'UNKNOWN')
                print(f"     Flow {i+1}: {flow_type} → {target}")
        else:
            print("   ❌ ch4ashbagdone not found!")
        
        # Check for menu nodes
        print("\n4. Checking for menu nodes...")
        menu_nodes = [label for label in flow_graph.keys() if '_menu_' in label]
        print(f"   Total menu nodes: {len(menu_nodes)}")
        
        # Check ch4ashbagdone menu node specifically
        ch4_menu_nodes = [label for label in menu_nodes if 'ch4ashbagdone' in label]
        print(f"   ch4ashbagdone menu nodes: {len(ch4_menu_nodes)}")
        for menu_node in ch4_menu_nodes:
            print(f"     - {menu_node}")
            menu_data = flow_graph[menu_node]
            print(f"       Outgoing flows: {len(menu_data.get('outgoing_flows', []))}")
        
        # Check connection types
        print("\n5. Analyzing connection types...")
        connection_types = {}
        for label_data in flow_graph.values():
            flows = label_data.get('outgoing_flows', [])
            for flow in flows:
                flow_type = flow.get('flow_type', 'UNKNOWN')
                connection_types[flow_type] = connection_types.get(flow_type, 0) + 1
        
        for conn_type, count in sorted(connection_types.items()):
            print(f"   {conn_type}: {count}")
        
        # Verify menu choice connections exist
        menu_choice_count = connection_types.get('menu_choice', 0)
        if menu_choice_count > 0:
            print(f"\n✅ SUCCESS: {menu_choice_count} menu_choice connections found!")
        else:
            print(f"\n❌ PROBLEM: No menu_choice connections found!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_poc_flow_data() 