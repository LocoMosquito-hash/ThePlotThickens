#!/usr/bin/env python3
"""
Deep dive debugging specifically for ep2cont5 node ID generation.
Focus on tracing where the rogue nodes come from.
"""

import sys
from pathlib import Path

# Add renpy-source-api to path
current_dir = Path(__file__).parent
app_dir = current_dir.parent.parent / "app"
sys.path.insert(0, str(app_dir / "renpy-source-api"))

try:
    from renpy_data_adapter import RenpyFlowDataAdapter
    from parser import RenpyParser
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

# Monkey patch the adapter to add debugging
original_create_choice_buttons = RenpyFlowDataAdapter._create_choice_buttons_and_connections

def debug_create_choice_buttons_and_connections(self, menu_node, container_id: str, label_name: str, 
                                               container_nodes, choice_connections):
    """Debug wrapper for choice button creation."""
    if 'ep2cont5' in container_id or 'ep2cont5' in label_name:
        print(f"\n🔍 CHOICE BUTTON CREATION DEBUG:")
        print(f"  menu_node type: {type(menu_node)}")
        print(f"  container_id: {container_id}")
        print(f"  label_name: {label_name}")
        print(f"  menu_node.choices: {len(getattr(menu_node, 'choices', []))}")
        
        # Check if menu_node has node_id
        if hasattr(menu_node, 'node_id'):
            print(f"  menu_node.node_id: {menu_node.node_id}")
        
        # Print choice details
        for i, choice in enumerate(getattr(menu_node, 'choices', [])):
            print(f"    Choice {i}: '{choice.text}'")
            if hasattr(choice, 'nested_menu_structures'):
                print(f"      Nested structures: {len(choice.nested_menu_structures)}")
                for j, nested in enumerate(choice.nested_menu_structures):
                    if hasattr(nested, 'node_id'):
                        print(f"        Nested {j} node_id: {nested.node_id}")
    
    return original_create_choice_buttons(self, menu_node, container_id, label_name, container_nodes, choice_connections)

# Apply the monkey patch
RenpyFlowDataAdapter._create_choice_buttons_and_connections = debug_create_choice_buttons_and_connections

# Monkey patch the nested menu creation logic
original_create_menu_containers = RenpyFlowDataAdapter._create_menu_containers

def debug_create_menu_containers(self, flow_graph):
    """Debug wrapper for menu container creation."""
    print(f"\n🔍 MENU CONTAINER CREATION DEBUG:")
    
    # Find all menu nodes in flow graph
    menu_nodes = flow_graph.get('menu_nodes', {})
    ep2cont5_menu_nodes = {k: v for k, v in menu_nodes.items() if 'ep2cont5' in k}
    
    print(f"Total menu nodes in flow_graph: {len(menu_nodes)}")
    print(f"ep2cont5 menu nodes found: {len(ep2cont5_menu_nodes)}")
    
    for node_id, node_data in ep2cont5_menu_nodes.items():
        print(f"  Node ID: {node_id}")
        print(f"    Parent label: {node_data.get('parent_label', 'unknown')}")
        print(f"    Nesting level: {node_data.get('nesting_level', 0)}")
        print(f"    Menu type: {node_data.get('menu_type', 'unknown')}")
        
    result = original_create_menu_containers(self, flow_graph)
    
    # Check what containers were created
    container_nodes, choice_connections = result
    ep2cont5_containers = [node for node in container_nodes if 'ep2cont5' in node.node_id]
    
    print(f"\n🔍 CREATED CONTAINERS:")
    print(f"Total containers created: {len(container_nodes)}")
    print(f"ep2cont5 containers: {len(ep2cont5_containers)}")
    
    for container in ep2cont5_containers:
        print(f"  Container ID: {container.node_id}")
        print(f"    Node type: {container.node_type}")
        print(f"    Display name: {container.display_name}")
        metadata = getattr(container, 'metadata', {})
        print(f"    Parent label: {metadata.get('parent_label', 'unknown')}")
        print(f"    Is nested: {metadata.get('is_nested', False)}")
        print(f"    Nesting level: {metadata.get('nesting_level', 0)}")
        if 'original_node_id' in metadata:
            print(f"    Original node ID: {metadata['original_node_id']}")
    
    return result

# Apply the monkey patch
RenpyFlowDataAdapter._create_menu_containers = debug_create_menu_containers

def main():
    """Run targeted ep2cont5 debugging."""
    
    game_path = "F:\\Bin\\Games\\Haley-1.1-alt-pc\\game"
    
    print("🔍 Route 1 Deep Dive: ep2cont5 Node ID Generation")
    print("=" * 60)
    
    adapter = RenpyFlowDataAdapter(use_hybrid=True)
    
    # This will trigger our debug hooks
    print("Starting analysis with debug hooks...")
    visualization_data = adapter.analyze_project(game_path)
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"Total nodes: {len(visualization_data.nodes)}")
    print(f"Total connections: {len(visualization_data.connections)}")
    
    # Find all ep2cont5 related nodes in final result
    ep2cont5_nodes = [node for node in visualization_data.nodes if 'ep2cont5' in node.node_id]
    print(f"ep2cont5 nodes in final visualization: {len(ep2cont5_nodes)}")
    
    for node in ep2cont5_nodes:
        print(f"  Final Node: {node.node_id}")
        print(f"    Type: {node.node_type}")
        print(f"    Display: {node.display_name}")
        
    # Find connections involving ep2cont5 nodes
    ep2cont5_connections = [conn for conn in visualization_data.connections 
                           if 'ep2cont5' in conn.source_node_id or 'ep2cont5' in conn.target_node_id]
    print(f"\nep2cont5 connections: {len(ep2cont5_connections)}")
    
    for conn in ep2cont5_connections:
        print(f"  Connection: {conn.source_node_id} → {conn.target_node_id}")
        print(f"    Type: {conn.connection_type}")

if __name__ == "__main__":
    main()