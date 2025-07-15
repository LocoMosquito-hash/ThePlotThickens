#!/usr/bin/env python3
"""
Test Menu Containers in POC
===========================

Test the menu container logic implementation in the POC.
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
import networkx as nx

def test_menu_container_logic():
    """Test menu container creation logic without GUI."""
    
    project_path = r"T:\AG\MySisterMyRoommateV1.69-pc\game"
    
    print("=== MENU CONTAINER LOGIC TEST ===")
    print("=" * 40)
    
    try:
        # Load flow graph data
        project = RenpyProject(project_path)
        project.analyze()
        flow_graph = project.get_flow_graph()
        
        # Create NetworkX graph from flow graph data
        graph = nx.DiGraph()
        
        # Add nodes
        for node_id, node_data in flow_graph.items():
            graph.add_node(node_id, **node_data)
        
        # Add edges
        for node_id, node_data in flow_graph.items():
            outgoing_flows = node_data.get('outgoing_flows', [])
            for flow in outgoing_flows:
                target = flow.get('target_label')
                if target:
                    graph.add_edge(node_id, target, **flow)
        
        print(f"Original graph: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
        
        # Simulate menu container creation
        menu_containers = {}
        menu_choice_edges = set()
        nodes_created = 0
        
        # Find menu containers needed
        for node_id, node_data in graph.nodes.items():
            outgoing_flows = node_data.get('outgoing_flows', [])
            menu_choices = [flow for flow in outgoing_flows 
                          if flow.get('flow_type') == 'menu_choice']
            
            if menu_choices:
                menu_node_id = f"{node_id}_menu_container"
                menu_containers[node_id] = menu_node_id
                nodes_created += 1
                
                # Track which edges should go through menu containers
                for choice in menu_choices:
                    target = choice.get('target_label')
                    if target:
                        menu_choice_edges.add((node_id, target))
        
        print(f"Menu containers to create: {nodes_created}")
        print(f"Menu choice edges to reroute: {len(menu_choice_edges)}")
        
        # Test specific case: ch4ashbagdone
        if 'ch4ashbagdone' in menu_containers:
            print(f"\n✅ ch4ashbagdone will have menu container: {menu_containers['ch4ashbagdone']}")
            
            # Count how many edges will be rerouted
            ch4_edges = [edge for edge in menu_choice_edges if edge[0] == 'ch4ashbagdone']
            print(f"   Edges to reroute: {len(ch4_edges)}")
            for edge in ch4_edges[:5]:  # Show first 5
                print(f"     {edge[0]} -> {edge[1]}")
            if len(ch4_edges) > 5:
                print(f"     ... and {len(ch4_edges) - 5} more")
        else:
            print(f"\n❌ ch4ashbagdone will NOT have menu container")
        
        # Count edge changes
        original_edges = len(graph.edges)
        direct_edges = len([e for e in graph.edges if e not in menu_choice_edges])
        rerouted_edges = len(menu_choice_edges)
        new_edges = direct_edges + (rerouted_edges * 2)  # Each rerouted edge becomes 2
        
        print(f"\nEdge analysis:")
        print(f"  Original edges: {original_edges}")
        print(f"  Direct edges (unchanged): {direct_edges}")
        print(f"  Rerouted edges: {rerouted_edges}")
        print(f"  New total edges: {new_edges}")
        print(f"  Edge reduction: {original_edges - new_edges}")
        
        if new_edges < original_edges:
            print("✅ Menu containers will reduce visual clutter!")
        else:
            print("❌ No edge reduction achieved")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_menu_container_logic() 