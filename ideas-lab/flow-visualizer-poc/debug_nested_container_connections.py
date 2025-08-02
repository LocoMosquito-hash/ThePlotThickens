#!/usr/bin/env python3
"""
Debug Nested Container Connections
==================================

Examine why nested menu containers are appearing as orphans instead of being 
connected to their parent choice buttons.
"""

import sys
import os
from collections import defaultdict

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_nested_container_connections():
    """Debug nested container connection issues."""
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    if not os.path.exists(project_path):
        print(f"ERROR: Project path not found: {project_path}")
        return
    
    print("Debugging nested container connections...")
    print("=" * 60)
    
    try:
        from renpy_data_adapter import RenpyFlowDataAdapter
        
        # Load the project
        adapter = RenpyFlowDataAdapter()
        visualization_data = adapter.analyze_project(project_path)
        
        nodes = visualization_data.nodes
        connections = visualization_data.connections
        
        print(f"✅ Loaded {len(nodes)} nodes, {len(connections)} connections")
        
        # Build connection mapping
        incoming_connections = defaultdict(list)
        outgoing_connections = defaultdict(list)
        
        for conn in connections:
            source = conn.source_node_id
            target = conn.target_node_id
            
            outgoing_connections[source].append(conn)
            incoming_connections[target].append(conn)
        
        # Find nested menu container orphans
        nested_container_orphans = []
        choice_buttons = []
        all_containers = []
        
        for node in nodes:
            if node.node_type == 'menu_container':
                all_containers.append(node)
                if ('nested' in node.node_id or '_menu_1' in node.node_id):
                    # Check if it's an orphan
                    if node.node_id not in incoming_connections:
                        nested_container_orphans.append(node)
            elif node.node_type == 'choice_button':
                choice_buttons.append(node)
        
        print(f"\n📊 NESTED CONTAINER ANALYSIS:")
        print(f"  Total containers: {len(all_containers)}")
        print(f"  Nested container orphans: {len(nested_container_orphans)}")
        print(f"  Choice buttons: {len(choice_buttons)}")
        
        # Analyze first few orphan containers to understand the pattern
        print(f"\n🔍 ANALYZING FIRST 10 ORPHAN NESTED CONTAINERS:")
        print("-" * 60)
        
        for i, container in enumerate(nested_container_orphans[:10]):
            print(f"\n{i+1}. ORPHAN: {container.node_id}")
            
            # Try to find potential parent choice button
            potential_parents = []
            
            # Pattern analysis for parent identification
            container_id = container.node_id
            
            # Common patterns in naming:
            # day01_p_room_action_menu_nested_menu_1_choice_1_menu_1
            # Should connect to: day01_p_room_action_menu_nested_menu_1_choice_1
            
            if '_menu_1' in container_id:
                # Remove the final _menu_1 to get potential parent choice
                potential_parent_choice = container_id.replace('_menu_1', '')
                
                # Look for this choice in our choice buttons
                matching_choices = [c for c in choice_buttons if c.node_id == potential_parent_choice]
                if matching_choices:
                    potential_parents.extend(matching_choices)
                else:
                    print(f"    ❌ No choice found: {potential_parent_choice}")
            
            # Alternative pattern: look for choices that start with similar prefix
            base_pattern = container_id.split('_choice_')[0] if '_choice_' in container_id else ''
            if base_pattern:
                pattern_matches = [c for c in choice_buttons if c.node_id.startswith(base_pattern)]
                potential_parents.extend(pattern_matches[:3])  # Limit to first 3 matches
            
            print(f"    Potential parents found: {len(potential_parents)}")
            for parent in potential_parents[:3]:
                print(f"      - {parent.node_id}")
                
                # Check if there's already a connection
                has_connection = any(
                    conn.source_node_id == parent.node_id and conn.target_node_id == container.node_id
                    for conn in connections
                )
                print(f"        Connection exists: {has_connection}")
                
                # Check outgoing connections from this choice
                outgoing = outgoing_connections.get(parent.node_id, [])
                print(f"        Choice outgoing connections: {len(outgoing)}")
                for conn in outgoing[:2]:
                    print(f"          → {conn.target_node_id} ({conn.connection_type})")
        
        # Look for patterns in how choice-to-menu connections are being made
        print(f"\n🔍 CHOICE-TO-MENU CONNECTION PATTERNS:")
        print("-" * 50)
        
        choice_to_menu_connections = [c for c in connections if c.connection_type == 'choice_to_menu']
        print(f"Total choice_to_menu connections: {len(choice_to_menu_connections)}")
        
        # Group by naming patterns
        connection_patterns = defaultdict(list)
        for conn in choice_to_menu_connections:
            # Check if target is a nested container
            target = conn.target_node_id
            if 'nested' in target or '_menu_1' in target:
                connection_patterns['nested'].append(conn)
            else:
                connection_patterns['normal'].append(conn)
        
        print(f"Connections to nested containers: {len(connection_patterns['nested'])}")
        print(f"Connections to normal containers: {len(connection_patterns['normal'])}")
        
        # Show examples of working nested connections
        if connection_patterns['nested']:
            print(f"\n✅ WORKING NESTED CONNECTIONS (first 5):")
            for i, conn in enumerate(connection_patterns['nested'][:5]):
                print(f"  {i+1}. {conn.source_node_id} → {conn.target_node_id}")
        
        # Check if the issue is in our connection creation logic
        print(f"\n🔍 CONNECTION CREATION LOGIC ANALYSIS:")
        print("-" * 50)
        
        # Look for choice buttons that should connect to orphan containers
        missing_connections = []
        
        for container in nested_container_orphans[:5]:
            container_id = container.node_id
            
            # Try to deduce the expected parent choice
            if '_menu_1' in container_id:
                expected_parent = container_id.replace('_menu_1', '')
                
                # Check if this choice exists
                parent_choice = next((c for c in choice_buttons if c.node_id == expected_parent), None)
                if parent_choice:
                    missing_connections.append((parent_choice.node_id, container_id))
                    print(f"  MISSING: {parent_choice.node_id} → {container_id}")
        
        # Summary
        print(f"\n📋 SUMMARY:")
        print(f"  Nested container orphans: {len(nested_container_orphans)}")
        print(f"  Working nested connections: {len(connection_patterns['nested'])}")
        print(f"  Identified missing connections: {len(missing_connections)}")
        
        return {
            'nested_orphans': len(nested_container_orphans),
            'working_nested': len(connection_patterns['nested']),
            'missing_connections': len(missing_connections)
        }
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    debug_nested_container_connections() 