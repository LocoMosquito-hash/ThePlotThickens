#!/usr/bin/env python3
"""
Debug Real Orphan Fix
=====================

Apply the correct fix for orphan menu containers by creating missing
higher-level choice buttons and connecting them properly.
"""

import sys
import os

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def apply_real_orphan_fix():
    """Apply the correct fix for orphan containers."""
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    if not os.path.exists(project_path):
        print(f"ERROR: Project path not found: {project_path}")
        return
    
    print("🔧 APPLYING REAL ORPHAN FIX")
    print("=" * 50)
    print("Creating missing higher-level choice buttons for orphan containers")
    
    try:
        # Add the control_flow path
        control_flow_path = os.path.join(project_root, "app", "renpy-source-api", "control_flow")
        sys.path.insert(0, control_flow_path)
        
        from renpy_data_adapter import RenpyFlowDataAdapter
        from vn_flow_visualizer import VisualizationNode, VisualizationConnection
        
        # Load the project
        print("\n1. Loading project data...")
        adapter = RenpyFlowDataAdapter()
        result = adapter.analyze_project(project_path)
        
        nodes = result.nodes
        connections = result.connections
        
        # Find orphan containers
        print("\n2. Finding orphan containers...")
        incoming_connections = {}
        for conn in connections:
            target_attr = getattr(conn, 'target_node_id', getattr(conn, 'target', 'unknown'))
            if target_attr not in incoming_connections:
                incoming_connections[target_attr] = []
            incoming_connections[target_attr].append(conn)
        
        orphan_containers = []
        for node in nodes:
            if node.node_type == 'menu_container':
                incoming_count = len(incoming_connections.get(node.node_id, []))
                if incoming_count == 0 and '_nested_menu_' in node.node_id and node.node_id.endswith('_menu_1'):
                    orphan_containers.append(node)
        
        print(f"Found {len(orphan_containers)} orphan containers")
        
        # Create missing choice buttons and connections
        print(f"\n3. Creating missing choice buttons and connections...")
        new_choice_buttons = []
        new_connections = []
        
        for orphan in orphan_containers:
            orphan_id = orphan.node_id
            
            # Extract the expected parent choice button name
            if orphan_id.endswith('_menu_1'):
                expected_choice_id = orphan_id[:-7]  # Remove "_menu_1"
                
                # Create the missing choice button
                new_choice_button = VisualizationNode(
                    node_id=expected_choice_id,
                    node_type='choice_button',
                    label=f"Choice for {expected_choice_id.split('_')[-1]}",
                    color='#90EE90',  # Light green for new nodes
                    position=(0, 0)  # Will be positioned by layout
                )
                
                # Create connection: choice -> menu container
                new_connection = VisualizationConnection(
                    connection_id=f"{expected_choice_id}_to_{orphan_id}",
                    source_node_id=expected_choice_id,
                    target_node_id=orphan_id,
                    connection_type='choice_to_menu',
                    color_hint='orange',
                    weight_hint=1.5,
                    label="creates"
                )
                
                new_choice_buttons.append(new_choice_button)
                new_connections.append(new_connection)
                
                print(f"✅ Created: {expected_choice_id} → {orphan_id}")
        
        # Add new nodes and connections to the result
        nodes.extend(new_choice_buttons)
        connections.extend(new_connections)
        
        print(f"\n4. RESULTS:")
        print(f"✅ Created {len(new_choice_buttons)} missing choice buttons")
        print(f"✅ Created {len(new_connections)} new connections")
        print(f"✅ Total nodes now: {len(nodes)}")
        print(f"✅ Total connections now: {len(connections)}")
        
        # Verify orphan reduction
        print(f"\n5. Verifying orphan reduction...")
        incoming_connections_after = {}
        for conn in connections:
            target_attr = getattr(conn, 'target_node_id', getattr(conn, 'target', 'unknown'))
            if target_attr not in incoming_connections_after:
                incoming_connections_after[target_attr] = []
            incoming_connections_after[target_attr].append(conn)
        
        remaining_orphan_containers = []
        for node in nodes:
            if node.node_type == 'menu_container':
                incoming_count = len(incoming_connections_after.get(node.node_id, []))
                if incoming_count == 0:
                    remaining_orphan_containers.append(node)
        
        print(f"❌ Remaining orphan containers: {len(remaining_orphan_containers)}")
        reduction = len(orphan_containers) - len(remaining_orphan_containers)
        print(f"🎉 Orphans eliminated: {reduction}")
        
        if reduction > 0:
            print(f"\n🎉 SUCCESS! Reduced orphans by {reduction} containers!")
            print(f"This should significantly clean up the top-level layout.")
        else:
            print(f"\n⚠️  No orphans eliminated - fix needs refinement")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    apply_real_orphan_fix() 