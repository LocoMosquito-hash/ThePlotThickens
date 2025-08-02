#!/usr/bin/env python3
"""
Debug Choice Connections
========================

Check why choice nodes aren't connecting to their child menus.
"""

import sys
import os

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_choice_connections():
    """Check choice-to-menu connections."""
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    if not os.path.exists(project_path):
        print(f"ERROR: Project path not found: {project_path}")
        return
    
    print("Debugging choice connections...")
    print("=" * 60)
    
    try:
        from renpy_data_adapter import RenpyFlowDataAdapter
        
        # Load the project
        adapter = RenpyFlowDataAdapter()
        print(f"Analyzing project: {project_path}")
        
        result = adapter.analyze_project(project_path)
        if not result or not hasattr(result, 'nodes'):
            print("❌ Failed to analyze project")
            return
        
        nodes = result.nodes
        connections = result.connections if hasattr(result, 'connections') else []
        
        print(f"\n✅ Loaded {len(nodes)} nodes, {len(connections)} connections")
        
        # Focus on day02_p_room_choices area
        print("\n🔍 DAY02_P_ROOM_CHOICES AREA:")
        print("-" * 50)
        
        # Find all nodes related to day02_p_room_choices
        related_nodes = [n for n in nodes if 'day02_p_room_choices' in n.node_id]
        print(f"Found {len(related_nodes)} related nodes:")
        
        choice_nodes = []
        menu_container_nodes = []
        
        for node in related_nodes:
            # Safe color access
            if hasattr(node, 'color'):
                color_val = node.color
            elif hasattr(node, 'style') and hasattr(node.style, 'fill'):
                color_val = node.style.fill
            else:
                color_val = "unknown"
            
            color_emoji = "🟠" if "#FFA500" in str(color_val) else "🔵" if "#ADD8E6" in str(color_val) else "🟡"
            
            print(f"  {color_emoji} {node.node_id}")
            print(f"    Type: {node.node_type}")
            print(f"    Color: {color_val}")
            
            if node.node_type == 'choice_button':
                choice_nodes.append(node)
            elif node.node_type == 'menu_container':
                menu_container_nodes.append(node)
        
        print(f"\n📊 Summary:")
        print(f"  Choice nodes: {len(choice_nodes)}")
        print(f"  Menu container nodes: {len(menu_container_nodes)}")
        
        # Check connections involving these nodes
        print(f"\n🔗 CONNECTIONS ANALYSIS:")
        print("-" * 50)
        
        # First, check what attributes connections have
        if connections:
            print(f"Connection attributes: {dir(connections[0])}")
            print(f"Sample connection: {connections[0]}")
            
            # DEBUG: Print first 10 connections to see their structure
            print(f"\nFirst 10 connections:")
            for i, conn in enumerate(connections[:10]):
                source_attr = getattr(conn, 'source_node_id', 'NO_SOURCE')
                target_attr = getattr(conn, 'target_node_id', 'NO_TARGET')
                conn_type = getattr(conn, 'connection_type', 'NO_TYPE')
                print(f"  {i}: {source_attr} → {target_attr} ({conn_type})")
        
        related_connections = []
        for conn in connections:
            # Check what attributes this connection has
            source_attr = getattr(conn, 'source', getattr(conn, 'source_id', getattr(conn, 'source_node_id', getattr(conn, 'from_node', None))))
            target_attr = getattr(conn, 'target', getattr(conn, 'target_id', getattr(conn, 'target_node_id', getattr(conn, 'to_node', None))))
            
            if (source_attr and 'day02_p_room_choices' in str(source_attr)) or \
               (target_attr and 'day02_p_room_choices' in str(target_attr)):
                related_connections.append(conn)
        
        print(f"Found {len(related_connections)} related connections:")
        
        choice_to_menu_connections = []
        container_to_choice_connections = []
        other_connections = []
        
        for conn in related_connections:
            # Safe attribute access
            source_attr = getattr(conn, 'source', getattr(conn, 'source_id', getattr(conn, 'source_node_id', getattr(conn, 'from_node', 'unknown_source'))))
            target_attr = getattr(conn, 'target', getattr(conn, 'target_id', getattr(conn, 'target_node_id', getattr(conn, 'to_node', 'unknown_target'))))
            conn_type = getattr(conn, 'connection_type', getattr(conn, 'type', 'unknown_type'))
            
            print(f"  {source_attr} → {target_attr} ({conn_type})")
            
            if conn_type == 'choice_to_menu':
                choice_to_menu_connections.append(conn)
            elif conn_type == 'container_to_choice':
                container_to_choice_connections.append(conn)
            else:
                other_connections.append(conn)
        
        print(f"\n📈 Connection Types:")
        print(f"  Choice-to-menu: {len(choice_to_menu_connections)}")
        print(f"  Container-to-choice: {len(container_to_choice_connections)}")
        print(f"  Other: {len(other_connections)}")
        
        # Check for missing choice-to-menu connections
        print(f"\n🔍 MISSING CONNECTIONS CHECK:")
        print("-" * 50)
        
        print(f"Choice nodes that should have children:")
        for choice in choice_nodes:
            print(f"  {choice.node_id}")
            
            # Look for outgoing connections from this choice
            outgoing = []
            for c in connections:
                source_attr = getattr(c, 'source', getattr(c, 'source_id', getattr(c, 'source_node_id', getattr(c, 'from_node', None))))
                if source_attr == choice.node_id:
                    outgoing.append(c)
            
            print(f"    Outgoing connections: {len(outgoing)}")
            
            for out_conn in outgoing:
                target_attr = getattr(out_conn, 'target', getattr(out_conn, 'target_id', getattr(out_conn, 'target_node_id', getattr(out_conn, 'to_node', 'unknown_target'))))
                conn_type = getattr(out_conn, 'connection_type', getattr(out_conn, 'type', 'unknown_type'))
                print(f"      → {target_attr} ({conn_type})")
            
            # Look for potential child menu containers
            potential_children = [n for n in nodes if n.node_id.startswith(choice.node_id + '_menu')]
            print(f"    Potential child containers: {len(potential_children)}")
            
            for child in potential_children:
                print(f"      Potential: {child.node_id} ({child.node_type})")
                
                # Check if there's a connection to this potential child
                has_connection = False
                for c in connections:
                    source_attr = getattr(c, 'source', getattr(c, 'source_id', getattr(c, 'source_node_id', getattr(c, 'from_node', None))))
                    target_attr = getattr(c, 'target', getattr(c, 'target_id', getattr(c, 'target_node_id', getattr(c, 'to_node', None))))
                    if source_attr == choice.node_id and target_attr == child.node_id:
                        has_connection = True
                        break
                print(f"        Has connection: {has_connection}")
        
        # Summary
        print(f"\n📝 SUMMARY:")
        print("-" * 50)
        print(f"- Total nodes in day02_p_room_choices area: {len(related_nodes)}")
        print(f"- Choice nodes: {len(choice_nodes)}")
        print(f"- Menu container nodes: {len(menu_container_nodes)}")
        print(f"- Total connections: {len(related_connections)}")
        print(f"- Choice-to-menu connections: {len(choice_to_menu_connections)}")
        
        if len(choice_nodes) > 0 and len(choice_to_menu_connections) == 0:
            print("🚨 ISSUE: We have choice nodes but NO choice-to-menu connections!")
            print("   This is likely why choices aren't showing their children.")
        
    except Exception as e:
        import traceback
        print(f"❌ Error during analysis: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    debug_choice_connections() 