#!/usr/bin/env python3
"""
Debug Real Hierarchy
====================

Figure out what orphan containers should REALLY connect to instead of 
creating fake auto-generated choice buttons.
"""

import sys
import os

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_real_hierarchy():
    """Figure out what containers should really connect to."""
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    if not os.path.exists(project_path):
        print(f"ERROR: Project path not found: {project_path}")
        return
    
    print("Debugging REAL hierarchy for orphan containers...")
    print("=" * 60)
    
    try:
        from renpy_data_adapter import RenpyFlowDataAdapter
        
        # Load the project WITHOUT the auto-generated fix
        adapter = RenpyFlowDataAdapter()
        result = adapter.analyze_project(project_path)
        
        if not result:
            print("ERROR: Could not analyze project")
            return
        
        print(f"📊 Total nodes: {len(result.nodes)}")
        print(f"📊 Total connections: {len(result.connections)}")
        
        # Find all menu containers and their actual context
        menu_containers = [n for n in result.nodes if n.node_type == 'menu_container']
        print(f"\n📦 Found {len(menu_containers)} menu containers")
        
        # Group containers by their prefix (indicates what label they belong to)
        container_groups = {}
        for container in menu_containers:
            # Extract the label part (everything before _nested_menu or _menu)
            container_id = container.node_id
            
            if '_nested_menu_' in container_id:
                # e.g., day01_p_room_action_menu_nested_menu_1_choice_1_menu_1
                base_label = container_id.split('_nested_menu_')[0]
            elif '_menu_' in container_id:
                # e.g., day01_start_menu_1
                base_label = container_id.split('_menu_')[0]
            else:
                base_label = "unknown"
            
            if base_label not in container_groups:
                container_groups[base_label] = []
            container_groups[base_label].append(container)
        
        print(f"\n🏷️ Container groups by base label:")
        for base_label, containers in container_groups.items():
            print(f"\n  📋 {base_label}: {len(containers)} containers")
            
            # Check if this base label exists as an actual node
            label_nodes = [n for n in result.nodes if n.node_id == base_label]
            print(f"    Label node exists: {'✅ YES' if label_nodes else '❌ NO'}")
            
            if label_nodes:
                label_node = label_nodes[0]
                # Check incoming connections to this label
                incoming = [c for c in result.connections 
                           if hasattr(c, 'target_node_id') and c.target_node_id == base_label]
                print(f"    Label incoming connections: {len(incoming)}")
                
                # Check outgoing connections from this label
                outgoing = [c for c in result.connections 
                           if hasattr(c, 'source_node_id') and c.source_node_id == base_label]
                print(f"    Label outgoing connections: {len(outgoing)}")
                
                # Check if any containers are connected to this label
                connected_containers = [c for c in outgoing 
                                      if any(cont.node_id == getattr(c, 'target_node_id', '') 
                                            for cont in containers)]
                print(f"    Containers connected to label: {len(connected_containers)}")
            
            # Show first few containers for this group
            for i, container in enumerate(containers[:3]):
                incoming_to_container = [c for c in result.connections 
                                       if hasattr(c, 'target_node_id') and c.target_node_id == container.node_id]
                print(f"      Container {i+1}: {container.node_id}")
                print(f"        Incoming: {len(incoming_to_container)}")
                if incoming_to_container:
                    for conn in incoming_to_container:
                        source = getattr(conn, 'source_node_id', 'unknown')
                        print(f"          ← {source}")
        
        # Check for potential real parents that these containers should connect to
        print(f"\n🔍 Looking for REAL potential parents...")
        
        # Find all choice button nodes
        choice_buttons = [n for n in result.nodes if n.node_type == 'choice_button']
        print(f"📋 Found {len(choice_buttons)} choice buttons")
        
        # Check if orphan containers have choice button siblings that might be their real parents
        orphan_containers = []
        connected_containers = set()
        
        for conn in result.connections:
            if hasattr(conn, 'target_node_id'):
                connected_containers.add(conn.target_node_id)
        
        for container in menu_containers:
            if container.node_id not in connected_containers:
                orphan_containers.append(container)
        
        print(f"\n🔍 Analyzing {len(orphan_containers)} orphan containers:")
        
        for i, orphan in enumerate(orphan_containers[:10]):  # Look at first 10
            orphan_id = orphan.node_id
            print(f"\n  {i+1}. {orphan_id}")
            
            # Look for choice buttons that might be the real parent
            # Pattern: remove "_menu_1" from end to find parent choice
            if orphan_id.endswith('_menu_1'):
                potential_parent = orphan_id[:-7]  # Remove "_menu_1"
                
                # Check if this potential parent exists as a choice button
                parent_candidates = [n for n in choice_buttons if n.node_id == potential_parent]
                if parent_candidates:
                    print(f"    ✅ FOUND REAL PARENT: {potential_parent}")
                    
                    # Check if parent is connected
                    parent_incoming = [c for c in result.connections 
                                     if hasattr(c, 'target_node_id') and c.target_node_id == potential_parent]
                    print(f"    Parent incoming connections: {len(parent_incoming)}")
                    
                    if parent_incoming:
                        for conn in parent_incoming:
                            source = getattr(conn, 'source_node_id', 'unknown')
                            print(f"      Parent connected from: {source}")
                else:
                    print(f"    ❌ Parent not found: {potential_parent}")
        
        print(f"\n📊 SUMMARY:")
        print(f"  Total menu containers: {len(menu_containers)}")
        print(f"  Orphan containers: {len(orphan_containers)}")
        print(f"  Container groups: {len(container_groups)}")
        print(f"  Choice buttons: {len(choice_buttons)}")
        
    except Exception as e:
        print(f"ERROR during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_real_hierarchy() 