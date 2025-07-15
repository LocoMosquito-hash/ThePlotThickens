#!/usr/bin/env python3
"""
Simple Diagnostics for Menu Container Issue
==========================================

A simplified diagnostic tool to trace why menu nodes aren't appearing.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core import RenpyProject
from menu_container_visualizer import MenuContainerVisualizer
import json

def main():
    project_path = r"T:\AG\MySisterMyRoommateV1.69-pc\game"
    
    print("=== SIMPLE MENU CONTAINER DIAGNOSTICS ===")
    print("=" * 50)
    
    try:
        # Step 1: Load and analyze project
        print("1. Loading Ren'Py project...")
        project = RenpyProject(project_path)
        project.analyze()
        
        # Step 2: Get flow data
        print("2. Getting flow graph data...")
        flow_data = project.get_flow_graph()
        print(f"   Flow data contains {len(flow_data)} labels")
        
        # Step 3: Analyze raw data
        print("3. Analyzing raw flow data...")
        labels_with_menus = 0
        menu_choice_connections = 0
        sample_menu_labels = []
        
        for label_name, label_data in flow_data.items():
            if label_data.get('has_menu', False):
                labels_with_menus += 1
                sample_menu_labels.append(label_name)
                
            connections = label_data.get('outgoing_flows', [])
            for conn in connections:
                if conn.get('type') == 'menu_choice':
                    menu_choice_connections += 1
                    
        print(f"   Labels with menus: {labels_with_menus}")
        print(f"   Menu choice connections: {menu_choice_connections}")
        print(f"   Sample menu labels: {sample_menu_labels[:10]}")
        
        # Step 4: Test menu container visualizer
        print("4. Testing MenuContainerVisualizer...")
        visualizer = MenuContainerVisualizer(project)  # Pass project, not flow_data
        
        # Check flow data format in visualizer
        print(f"   Visualizer flow_data type: {type(visualizer.flow_data)}")
        
        # Try to create graph
        print("5. Creating NetworkX graph...")
        graph = visualizer.graph  # Use the existing graph property
        
        all_nodes = list(graph.nodes())
        menu_nodes = [n for n in all_nodes if '_menu_' in n]
        label_nodes = [n for n in all_nodes if '_menu_' not in n and not n.startswith('_')]
        
        print(f"   Total nodes: {len(all_nodes)}")
        print(f"   Menu nodes: {len(menu_nodes)}")
        print(f"   Label nodes: {len(label_nodes)}")
        print(f"   Sample menu nodes: {menu_nodes[:10]}")
        
        # Check specific test case
        test_node = 'ch4ashbagdone'
        if test_node in flow_data:
            test_data = flow_data[test_node]
            print(f"6. Testing specific node: {test_node}")
            print(f"   Has menu: {test_data.get('has_menu', False)}")
            print(f"   Outgoing flows: {len(test_data.get('outgoing_flows', []))}")
            
            if test_node in graph:
                successors = list(graph.successors(test_node))
                print(f"   Graph successors: {successors}")
                menu_successors = [s for s in successors if '_menu_' in s]
                print(f"   Menu successors: {menu_successors}")
            else:
                print(f"   ❌ {test_node} not found in graph!")
        else:
            print(f"6. ❌ {test_node} not found in flow data!")
            
        # Check edges
        print("7. Analyzing edges...")
        all_edges = list(graph.edges(data=True))
        menu_choice_edges = [e for e in all_edges if e[2].get('type') == 'menu_choice']
        label_to_menu_edges = [e for e in all_edges if e[2].get('type') == 'label_to_menu']
        
        print(f"   Total edges: {len(all_edges)}")
        print(f"   Menu choice edges: {len(menu_choice_edges)}")
        print(f"   Label to menu edges: {len(label_to_menu_edges)}")
        
        # Summary
        print("\n=== SUMMARY ===")
        if labels_with_menus > 0:
            print(f"✅ Raw data has {labels_with_menus} labels with menus")
        else:
            print("❌ No labels with menus in raw data!")
            
        if len(menu_nodes) > 0:
            print(f"✅ Graph has {len(menu_nodes)} menu nodes")
        else:
            print("❌ No menu nodes in graph!")
            
        if len(menu_choice_edges) > 0:
            print(f"✅ Graph has {len(menu_choice_edges)} menu choice edges")
        else:
            print("❌ No menu choice edges in graph!")
            
        # Try to get menu choices for a test node
        test_menu_node = f"{test_node}_menu_1"
        if test_menu_node in menu_nodes:
            print(f"8. Testing menu choices for {test_menu_node}...")
            choices = visualizer.get_menu_choices(test_menu_node)
            print(f"   Menu choices found: {len(choices) if choices else 0}")
            if choices:
                print(f"   Sample choices: {[c.get('text', 'NO_TEXT')[:20] for c in choices[:3]]}")
        
        return True
        
    except Exception as e:
        print(f"❌ DIAGNOSTIC FAILED: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    main() 