#!/usr/bin/env python3
"""
Analyze Complex Menu Flows in Savior VN
========================================

Investigate why menu connections are bypassing choice containers.
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path('../../app').resolve()))
sys.path.insert(0, str(Path('../../app/renpy-source-api').resolve()))

from core import RenpyProject

def analyze_complex_menu():
    # Analyze Savior VN's complex dinnertalk menu
    project_path = r'T:\AG\Savior-0.16c-pc\game'
    project = RenpyProject(project_path)
    project.analyze()

    flow_graph = project.get_flow_graph()

    print('=== DINNERTALK COMPLEX MENU ANALYSIS ===')
    print()

    if 'dinnertalk' in flow_graph:
        node_data = flow_graph['dinnertalk']
        outgoing_flows = node_data.get('outgoing_flows', [])
        
        print(f'DINNERTALK LABEL - Total outgoing flows: {len(outgoing_flows)}')
        print()
        
        # Separate menu choices from other flows
        menu_choices = [flow for flow in outgoing_flows if flow.get('flow_type') == 'menu_choice']
        other_flows = [flow for flow in outgoing_flows if flow.get('flow_type') != 'menu_choice']
        
        print(f'Menu choices detected: {len(menu_choices)}')
        for i, choice in enumerate(menu_choices):
            context = choice.get('context', 'No context')
            target = choice.get('target_label', 'No target')
            condition = choice.get('condition', 'No condition')
            print(f'  Choice {i+1}: "{context}" -> {target}')
            if condition and condition != 'No condition':
                print(f'    Condition: {condition}')
        
        print(f'\nOther flows detected: {len(other_flows)}')
        for i, flow in enumerate(other_flows):
            flow_type = flow.get('flow_type', 'unknown')
            target = flow.get('target_label', 'No target')
            context = flow.get('context', 'No context')
            print(f'  Flow {i+1}: {flow_type} -> {target}')
            if context != 'No context':
                print(f'    Context: {context}')
            
        print()
        print('POTENTIAL ISSUE: Are there direct flows bypassing menu structure?')
        direct_targets = set()
        for flow in other_flows:
            if flow.get('target_label'):
                direct_targets.add(flow.get('target_label'))
        
        if direct_targets:
            print(f'Direct flow targets: {direct_targets}')
            
            # Check if these match expected menu destinations
            expected_destinations = {'olivia', 'daisy', 'vanessa', 'dinner'}
            overlap = direct_targets.intersection(expected_destinations)
            if overlap:
                print(f'⚠️  PROBLEM FOUND: Direct flows to menu destinations: {overlap}')
            else:
                print('✅ No direct flows to expected menu destinations')
        else:
            print('✅ No direct flows detected')
            
    else:
        print('ERROR: dinnertalk label not found in flow graph')

    print('\n' + '='*60)
    print('VISUALIZER CONNECTION ANALYSIS')
    print('='*60)
    
    # Now let's see how the visualizer processes these flows
    import networkx as nx
    
    # Create NetworkX graph from flow graph data (simulating visualizer logic)
    graph = nx.DiGraph()
    
    # Add nodes
    for node_id, node_data in flow_graph.items():
        graph.add_node(node_id, **node_data)
    
    # Add edges based on outgoing flows
    for node_id, node_data in flow_graph.items():
        outgoing_flows = node_data.get('outgoing_flows', [])
        for flow in outgoing_flows:
            target = flow.get('target_label')
            if target:
                graph.add_edge(node_id, target, **flow)
    
    print(f'Graph created: {len(graph.nodes)} nodes, {len(graph.edges)} edges')
    
    # Check what edges exist for dinnertalk
    if 'dinnertalk' in graph.nodes:
        dinnertalk_edges = list(graph.edges('dinnertalk', data=True))
        print(f'\nDINNERTALK outgoing edges: {len(dinnertalk_edges)}')
        
        for source, target, data in dinnertalk_edges:
            flow_type = data.get('flow_type', 'unknown')
            context = data.get('context', 'No context')
            print(f'  {source} -> {target} ({flow_type})')
            if context != 'No context':
                print(f'    Context: "{context}"')
    
    # Check if the problematic direct connections exist
    problematic_connections = [
        ('dinnertalk', 'olivia'),
        ('dinnertalk', 'daisy'), 
        ('dinnertalk', 'vanessa'),
        ('dinnertalk', 'dinner')
    ]
    
    print(f'\nChecking for problematic direct connections:')
    for source, target in problematic_connections:
        if graph.has_edge(source, target):
            edge_data = graph.edges[source, target]
            flow_type = edge_data.get('flow_type', 'unknown')
            print(f'⚠️  FOUND: {source} -> {target} ({flow_type})')
        else:
            print(f'✅ OK: No direct {source} -> {target} connection')

if __name__ == "__main__":
    analyze_complex_menu() 