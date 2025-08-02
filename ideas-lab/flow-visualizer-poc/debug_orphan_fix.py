#!/usr/bin/env python3
"""
Debug Orphan Fix
================

Based on industry research, implement proper parent-child connections 
for nested menu containers to eliminate 189 orphan nodes.

Research insights:
1. Use Closure Table pattern for hierarchical connections
2. Create explicit choice-to-nested-menu connections 
3. Use consistent connection types (avoid mixed patterns)
4. Early exit when target is found
"""

import sys
import os

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def fix_orphan_connections():
    """Apply the orphan connection fix using industry best practices."""
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    if not os.path.exists(project_path):
        print(f"ERROR: Project path not found: {project_path}")
        return
    
    print("🔧 IMPLEMENTING ORPHAN FIX")
    print("=" * 60)
    print("Research-backed approach: Closure Table pattern with explicit choice-to-menu connections")
    
    try:
        # Add the control_flow path
        control_flow_path = os.path.join(project_root, "app", "renpy-source-api", "control_flow")
        sys.path.insert(0, control_flow_path)
        
        from renpy_data_adapter import RenpyFlowDataAdapter
        
        # Load the project
        print("\n1. Loading project data...")
        adapter = RenpyFlowDataAdapter()
        result = adapter.analyze_project(project_path)
        
        if not result or not hasattr(result, 'nodes') or not hasattr(result, 'connections'):
            print("ERROR: Failed to load project data")
            return
            
        nodes = result.nodes
        connections = result.connections
        
        print(f"✅ Loaded {len(nodes)} nodes and {len(connections)} connections")
        
        # Analyze orphans before fix
        print("\n2. BEFORE FIX - Orphan Analysis:")
        print("-" * 40)
        
        # Find orphan containers (connections pointing TO each node)
        incoming_connections = {}
        for conn in connections:
            target_attr = getattr(conn, 'target_node_id', getattr(conn, 'target', 'unknown'))
            if target_attr not in incoming_connections:
                incoming_connections[target_attr] = []
            incoming_connections[target_attr].append(conn)
        
        orphan_containers = []
        choice_buttons = []
        
        for node in nodes:
            if node.node_type == 'menu_container':
                incoming_count = len(incoming_connections.get(node.node_id, []))
                if incoming_count == 0:
                    orphan_containers.append(node)
            elif node.node_type == 'choice_button':
                choice_buttons.append(node)
        
        print(f"❌ Orphan containers found: {len(orphan_containers)}")
        print(f"✅ Choice buttons available: {len(choice_buttons)}")
        
        # Apply the fix: Create missing choice-to-menu connections
        print("\n3. APPLYING FIX - Creating Choice-to-Menu Connections:")
        print("-" * 50)
        
        new_connections_created = 0
        fixed_orphans = []
        
        for orphan in orphan_containers:
            # Find the parent choice button for this orphan menu container
            # Pattern: menu container should be {choice_id}_menu_{number}
            orphan_id = orphan.node_id
            
            # Try to find the parent choice button
            parent_choice = None
            
            # Strategy 1: Direct parent pattern {choice_id}_menu_1
            if '_menu_' in orphan_id:
                potential_parent = orphan_id.rsplit('_menu_', 1)[0]
                parent_choice = next((c for c in choice_buttons if c.node_id == potential_parent), None)
            
            # Strategy 2: Look for choice buttons that this container should belong to
            if not parent_choice:
                # Check if this container belongs to any choice based on naming pattern
                for choice in choice_buttons:
                    if orphan_id.startswith(choice.node_id + '_menu_'):
                        parent_choice = choice
                        break
            
            if parent_choice:
                # Create the missing connection using industry best practice pattern
                from vn_flow_visualizer import VisualizationConnection
                
                connection_id = f"{parent_choice.node_id}_to_nested_{orphan.node_id}"
                
                new_connection = VisualizationConnection(
                    connection_id=connection_id,
                    source_node_id=parent_choice.node_id,
                    target_node_id=orphan.node_id,
                    connection_type='choice_to_menu',  # Consistent type
                    color_hint='orange',  # Visual consistency
                    weight_hint=1.5,
                    label="nested menu"
                )
                
                connections.append(new_connection)
                new_connections_created += 1
                fixed_orphans.append(orphan.node_id)
                
                print(f"✅ Connected: {parent_choice.node_id} → {orphan.node_id}")
            else:
                print(f"❌ No parent found for: {orphan.node_id}")
        
        # Verify the fix
        print(f"\n4. FIX RESULTS:")
        print("-" * 30)
        print(f"✅ New connections created: {new_connections_created}")
        print(f"✅ Orphans fixed: {len(fixed_orphans)}")
        print(f"✅ Total connections now: {len(connections)}")
        
        # Recheck orphan status after fix
        print("\n5. AFTER FIX - Orphan Verification:")
        print("-" * 40)
        
        # Rebuild incoming connections map
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
        
        if len(remaining_orphan_containers) < len(orphan_containers):
            print("\n🎉 SUCCESS! Orphan reduction achieved!")
            print(f"Orphan reduction: {reduction} containers now properly connected")
        else:
            print("\n⚠️  Fix needs refinement - analyzing remaining orphans...")
            
            # Show first 5 remaining orphans for analysis
            print("\nFirst 5 remaining orphans:")
            for i, orphan in enumerate(remaining_orphan_containers[:5]):
                print(f"  {i+1}. {orphan.node_id}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_orphan_connections() 