#!/usr/bin/env python3
"""
Real-Time Graph State Capture
=============================

Captures the exact graph state when POC switches to dot-like layout.
This helps diagnose the "red nodes in corner" disaster.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add the main app directory to path for renpy-source-api imports
current_dir = Path(__file__).parent
app_dir = current_dir.parent.parent / "app"
renpy_api_dir = app_dir / "renpy-source-api"
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(renpy_api_dir))

from core import RenpyProject
import networkx as nx

def capture_real_time_state():
    """Capture real-time graph state like the POC does."""
    
    project_path = r"T:\AG\MySisterMyRoommateV1.69-pc\game"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    capture_file = f"graph_state_capture_{timestamp}.txt"
    
    print(f"=== REAL-TIME GRAPH STATE CAPTURE ===")
    print(f"Saving to: {capture_file}")
    print("=" * 50)
    
    try:
        with open(capture_file, 'w') as f:
            f.write(f"=== REAL-TIME GRAPH STATE CAPTURE ===\n")
            f.write(f"Timestamp: {datetime.now()}\n")
            f.write(f"Project: {project_path}\n\n")
            
            # Load flow graph data (exactly as POC does)
            project = RenpyProject(project_path)
            project.analyze()
            flow_graph = project.get_flow_graph()
            
            # Create NetworkX graph (exactly as POC does)
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
            
            f.write(f"ORIGINAL GRAPH STATE:\n")
            f.write(f"  Nodes: {len(graph.nodes)}\n")
            f.write(f"  Edges: {len(graph.edges)}\n\n")
            
            # SIMULATE MENU CONTAINER CREATION (POC logic)
            f.write("=== MENU CONTAINER CREATION SIMULATION ===\n")
            
            nodes_before = list(graph.nodes())
            edges_before = list(graph.edges())
            
            menu_containers = {}
            menu_choice_edges = set()
            container_nodes_created = []
            
            # Step 1: Create menu container nodes
            for node_id, node_data in list(graph.nodes.items()):  # Use list() to avoid modification during iteration
                outgoing_flows = node_data.get('outgoing_flows', [])
                menu_choices = [flow for flow in outgoing_flows 
                              if flow.get('flow_type') == 'menu_choice']
                
                if menu_choices:
                    # Create menu container node
                    menu_node_id = f"{node_id}_menu_container"
                    menu_containers[node_id] = menu_node_id
                    container_nodes_created.append(menu_node_id)
                    
                    # Add to graph
                    graph.add_node(menu_node_id, **{
                        'name': f"Menu: {node_id}",
                        'node_type': 'menu_container',
                        'has_menu': True,
                        'menu_choices': len(menu_choices)
                    })
                    
                    # Track which edges should go through menu containers
                    for choice in menu_choices:
                        target = choice.get('target_label')
                        if target:
                            menu_choice_edges.add((node_id, target))
            
            f.write(f"Menu containers created: {len(container_nodes_created)}\n")
            f.write(f"Menu choice edges to reroute: {len(menu_choice_edges)}\n")
            
            # Step 2: Reroute edges through menu containers
            edges_to_remove = []
            edges_to_add = []
            
            for source_id, target_id in list(graph.edges()):
                edge_key = (source_id, target_id)
                if edge_key in menu_choice_edges and source_id in menu_containers:
                    menu_container_id = menu_containers[source_id]
                    
                    # Mark original edge for removal
                    edges_to_remove.append((source_id, target_id))
                    
                    # Add new edges through menu container
                    edges_to_add.append((source_id, menu_container_id, {'flow_type': 'to_menu'}))
                    edges_to_add.append((menu_container_id, target_id, {'flow_type': 'menu_choice'}))
            
            # Apply edge changes
            for edge in edges_to_remove:
                if graph.has_edge(edge[0], edge[1]):
                    graph.remove_edge(edge[0], edge[1])
            
            for edge_data in edges_to_add:
                graph.add_edge(edge_data[0], edge_data[1], **edge_data[2])
            
            f.write(f"Edges removed: {len(edges_to_remove)}\n")
            f.write(f"Edges added: {len(edges_to_add)}\n\n")
            
            # FINAL GRAPH STATE
            f.write("=== FINAL GRAPH STATE ===\n")
            f.write(f"  Total nodes: {len(graph.nodes)}\n")
            f.write(f"  Total edges: {len(graph.edges)}\n")
            f.write(f"  Original nodes: {len(nodes_before)}\n")
            f.write(f"  Container nodes: {len(container_nodes_created)}\n\n")
            
            # DISASTER ANALYSIS - Find the "red nodes in corner"
            f.write("=== DISASTER ANALYSIS ===\n")
            
            # Check ch4ashbagdone specifically
            if 'ch4ashbagdone' in graph.nodes:
                ch4_data = graph.nodes['ch4ashbagdone']
                f.write(f"ch4ashbagdone status:\n")
                f.write(f"  Exists: True\n")
                f.write(f"  Has menu: {ch4_data.get('has_menu', False)}\n")
                f.write(f"  In-degree: {graph.in_degree('ch4ashbagdone')}\n")
                f.write(f"  Out-degree: {graph.out_degree('ch4ashbagdone')}\n")
                f.write(f"  Successors: {list(graph.successors('ch4ashbagdone'))}\n\n")
            
            # Check menu container nodes
            f.write("Menu container nodes:\n")
            for container_node in container_nodes_created[:10]:  # Show first 10
                if container_node in graph.nodes:
                    container_data = graph.nodes[container_node]
                    f.write(f"  {container_node}:\n")
                    f.write(f"    Type: {container_data.get('node_type', 'unknown')}\n")
                    f.write(f"    In-degree: {graph.in_degree(container_node)}\n")
                    f.write(f"    Out-degree: {graph.out_degree(container_node)}\n")
                    f.write(f"    Predecessors: {list(graph.predecessors(container_node))}\n")
                    f.write(f"    Successors: {list(graph.successors(container_node))[:5]}...\n\n")  # Limit output
            
            if len(container_nodes_created) > 10:
                f.write(f"  ... and {len(container_nodes_created) - 10} more container nodes\n\n")
            
            # Check for problematic patterns
            f.write("PROBLEM PATTERNS:\n")
            
            # Nodes with many outgoing edges (visual clutter)
            high_out_degree = [(node, graph.out_degree(node)) for node in graph.nodes 
                             if graph.out_degree(node) > 10]
            high_out_degree.sort(key=lambda x: x[1], reverse=True)
            
            f.write(f"Nodes with >10 outgoing edges: {len(high_out_degree)}\n")
            for node, degree in high_out_degree[:5]:
                f.write(f"  {node}: {degree} edges\n")
            
            # Isolated container nodes
            isolated_containers = [node for node in container_nodes_created 
                                 if graph.in_degree(node) == 0 or graph.out_degree(node) == 0]
            f.write(f"Isolated container nodes: {len(isolated_containers)}\n")
            for node in isolated_containers[:5]:
                f.write(f"  {node} (in: {graph.in_degree(node)}, out: {graph.out_degree(node)})\n")
            
    except Exception as e:
        with open(capture_file, 'w') as f:
            f.write(f"ERROR during capture: {e}\n")
            import traceback
            f.write(traceback.format_exc())
        print(f"❌ Error: {e}")
        return None
    
    print(f"✅ Graph state captured to: {capture_file}")
    return capture_file

if __name__ == "__main__":
    capture_real_time_state() 