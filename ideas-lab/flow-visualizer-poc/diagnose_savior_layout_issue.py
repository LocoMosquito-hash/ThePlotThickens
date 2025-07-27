#!/usr/bin/env python3
"""
Diagnostic script to analyze the Savior game layout issue.

This script will help us understand why nodes with parents are ending up
on the first level when they shouldn't be.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import networkx as nx

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Add renpy-source-api to path
app_dir = current_dir.parent.parent / "app"
sys.path.insert(0, str(app_dir / "renpy-source-api"))

# Import the data adapter and visualizer
from renpy_data_adapter import RenpyFlowDataAdapter
from vn_flow_visualizer import VNFlowVisualizer

def analyze_graph_structure(graph: nx.DiGraph, project_path: str) -> Dict[str, Any]:
    """Analyze the graph structure to understand the layout issue."""
    
    print("=" * 80)
    print("GRAPH STRUCTURE ANALYSIS")
    print("=" * 80)
    
    analysis = {
        'total_nodes': len(graph.nodes()),
        'total_edges': len(graph.edges()),
        'orphan_nodes': [],
        'start_candidates': [],
        'components': [],
        'problematic_nodes': []
    }
    
    # 1. Find truly orphaned nodes (in_degree == 0)
    orphan_nodes = [n for n in graph.nodes() if graph.in_degree(n) == 0]
    analysis['orphan_nodes'] = orphan_nodes
    
    print(f"📊 Total nodes: {analysis['total_nodes']}")
    print(f"📊 Total edges: {analysis['total_edges']}")
    print(f"🏝️  Truly orphaned nodes (in_degree=0): {len(orphan_nodes)}")
    
    if len(orphan_nodes) < 20:  # Only print if manageable number
        for node in orphan_nodes:
            print(f"   - {node}")
    else:
        print(f"   - (Too many to display: {len(orphan_nodes)} nodes)")
        # Show a sample
        for i, node in enumerate(orphan_nodes[:10]):
            print(f"   - {node}")
        print(f"   - ... and {len(orphan_nodes) - 10} more")
    
    # 2. Check connected components
    if graph.is_directed():
        components = list(nx.weakly_connected_components(graph))
    else:
        components = list(nx.connected_components(graph))
    
    analysis['components'] = [(len(comp), list(comp)[:5]) for comp in components]
    
    print(f"\n🔗 Graph connectivity:")
    print(f"   - Number of disconnected components: {len(components)}")
    for i, comp in enumerate(components):
        comp_size = len(comp)
        if comp_size > 1:
            sample_nodes = list(comp)[:5]
            print(f"   - Component {i+1}: {comp_size} nodes (sample: {sample_nodes})")
        else:
            print(f"   - Component {i+1}: 1 node ({list(comp)[0]})")
    
    # 3. Try to detect semantic start using the same logic as the visualizer
    try:
        # Import start label finder
        from control_flow.start_label_finder import StartLabelFinder
        
        finder = StartLabelFinder(project_path)
        start_line = finder.find_start_label()
        semantic_start = start_line.label_name
        
        print(f"\n🎯 Semantic start detection:")
        print(f"   - SDK detected entry point: '{semantic_start}'")
        print(f"   - Entry point in graph: {semantic_start in graph.nodes()}")
        
        if semantic_start in graph.nodes():
            in_deg = graph.in_degree(semantic_start)
            out_deg = graph.out_degree(semantic_start)
            print(f"   - Entry point in_degree: {in_deg}, out_degree: {out_deg}")
            
        analysis['semantic_start'] = semantic_start
        
    except Exception as e:
        print(f"\n⚠️  Could not detect semantic start: {e}")
        analysis['semantic_start'] = None
    
    # 4. Simulate the _find_start_nodes logic from the visualizer
    semantic_start = analysis.get('semantic_start')
    
    print(f"\n🔍 Simulating _find_start_nodes logic:")
    
    # Priority 1: Semantic start
    if semantic_start and semantic_start in graph.nodes():
        start_candidates = [semantic_start]
        print(f"   ✅ Priority 1 - Using semantic start: {start_candidates}")
    else:
        # Priority 2: Heuristic start names
        start_candidates = []
        start_names = ['start', 'main', 'begin', 'intro', 'prologue', 'opening']
        
        for node in graph.nodes():
            node_lower = str(node).lower()
            if any(start_name in node_lower for start_name in start_names):
                start_candidates.append(node)
        
        if start_candidates:
            print(f"   ✅ Priority 2 - Using heuristic start nodes: {start_candidates}")
        else:
            # Priority 3: Fallback to orphans
            start_candidates = orphan_nodes
            print(f"   ⚠️  Priority 3 - Fallback to orphaned nodes: {len(start_candidates)} nodes")
            if len(start_candidates) > 10:
                print(f"      (Showing first 10: {start_candidates[:10]})")
    
    analysis['start_candidates'] = start_candidates
    
    # 5. Analyze nodes that would be problematic
    if len(start_candidates) > 3:  # Arbitrarily flag as problematic if too many start nodes
        print(f"\n🚨 PROBLEM DETECTED: {len(start_candidates)} start candidates found!")
        print(f"   This means {len(start_candidates)} nodes will be placed on the first level.")
        
        # Check if these nodes actually have incoming edges
        nodes_with_parents = []
        for node in start_candidates:
            in_degree = graph.in_degree(node)
            if in_degree > 0:
                predecessors = list(graph.predecessors(node))
                nodes_with_parents.append((node, in_degree, predecessors[:3]))
        
        if nodes_with_parents:
            print(f"\n❌ CRITICAL: {len(nodes_with_parents)} 'start' nodes actually have parents:")
            for node, in_deg, preds in nodes_with_parents[:10]:  # Show first 10
                print(f"   - {node}: in_degree={in_deg}, parents={preds}")
            
            analysis['problematic_nodes'] = nodes_with_parents
    
    return analysis

def simulate_dot_like_layout(graph: nx.DiGraph, semantic_start: Optional[str]) -> Dict[str, Any]:
    """Simulate the dot-like layout logic to see what's happening."""
    
    print("\n" + "=" * 80)
    print("DOT-LIKE LAYOUT SIMULATION")
    print("=" * 80)
    
    # Find disconnected components (same as visualizer)
    if graph.is_directed():
        components = list(nx.weakly_connected_components(graph))
    else:
        components = list(nx.connected_components(graph))
    
    print(f"🔗 Processing {len(components)} disconnected components:")
    
    layout_analysis = {
        'components': [],
        'total_first_level_nodes': 0
    }
    
    for i, component_nodes in enumerate(components):
        print(f"\n📦 Component {i+1}: {len(component_nodes)} nodes")
        
        # Create subgraph for this component
        subgraph = graph.subgraph(component_nodes).copy()
        
        # Simulate _find_start_nodes for this component
        start_nodes = []
        
        # Priority 1: Use semantic start if in this component
        if semantic_start and semantic_start in subgraph.nodes():
            start_nodes = [semantic_start]
            print(f"   ✅ Using semantic start: {start_nodes}")
        else:
            # Priority 2: Look for heuristic start names
            start_names = ['start', 'main', 'begin', 'intro', 'prologue', 'opening']
            for node in subgraph.nodes():
                node_lower = str(node).lower()
                if any(start_name in node_lower for start_name in start_names):
                    start_nodes.append(node)
            
            if start_nodes:
                print(f"   ✅ Using heuristic start nodes: {start_nodes}")
            else:
                # Priority 3: Fallback to orphans in this component
                start_nodes = [n for n in subgraph.nodes() if subgraph.in_degree(n) == 0]
                print(f"   ⚠️  Fallback to orphans: {len(start_nodes)} nodes")
                if len(start_nodes) > 5:
                    print(f"      (Sample: {start_nodes[:5]})")
                else:
                    print(f"      (All: {start_nodes})")
        
        # Check if any start nodes have parents
        problematic_in_component = []
        for node in start_nodes:
            in_degree = subgraph.in_degree(node)
            if in_degree > 0:
                predecessors = list(subgraph.predecessors(node))
                problematic_in_component.append((node, in_degree, predecessors))
        
        if problematic_in_component:
            print(f"   ❌ {len(problematic_in_component)} start nodes have parents in this component!")
            for node, in_deg, preds in problematic_in_component[:3]:
                print(f"      - {node}: in_degree={in_deg}, parents={preds}")
        
        component_analysis = {
            'size': len(component_nodes),
            'start_nodes': start_nodes,
            'problematic_nodes': problematic_in_component
        }
        layout_analysis['components'].append(component_analysis)
        layout_analysis['total_first_level_nodes'] += len(start_nodes)
    
    print(f"\n📊 SUMMARY:")
    print(f"   - Total nodes that will be placed on first level: {layout_analysis['total_first_level_nodes']}")
    problematic_total = sum(len(comp['problematic_nodes']) for comp in layout_analysis['components'])
    print(f"   - Of these, {problematic_total} actually have parents (PROBLEM!)")
    
    return layout_analysis

def main():
    """Main diagnostic function."""
    
    # Savior game path (update this path as needed)
    savior_path = r"T:/AG/Savior-0.16c-pc/game"
    
    if not os.path.exists(savior_path):
        print(f"❌ Savior path not found: {savior_path}")
        print("Please update the path in the script and try again.")
        return
    
    print(f"🎮 Analyzing Savior game at: {savior_path}")
    
    try:
        # 1. Load the data using the same adapter as the visualizer
        print("\n📊 Loading visualization data...")
        adapter = RenpyFlowDataAdapter(use_hybrid=True)
        visualization_data = adapter.analyze_project(savior_path, use_sdk=True)
        
        print(f"✅ Loaded {len(visualization_data.nodes)} nodes and {len(visualization_data.connections)} connections")
        
        # 2. Convert to NetworkX graph (same as visualizer does)
        print("\n🔗 Building NetworkX graph...")
        graph = nx.DiGraph()
        
        # Add nodes
        for node_data in visualization_data.nodes:
            graph.add_node(node_data.node_id, **node_data.metadata)
        
        # Add edges  
        for conn_data in visualization_data.connections:
            graph.add_edge(conn_data.source_node_id, conn_data.target_node_id)
        
        print(f"✅ NetworkX graph created: {len(graph.nodes())} nodes, {len(graph.edges())} edges")
        
        # 3. Analyze the graph structure
        graph_analysis = analyze_graph_structure(graph, savior_path)
        
        # 4. Simulate the dot-like layout logic
        semantic_start = graph_analysis.get('semantic_start')
        layout_analysis = simulate_dot_like_layout(graph, semantic_start)
        
        # 5. Final diagnosis
        print("\n" + "=" * 80)
        print("FINAL DIAGNOSIS")
        print("=" * 80)
        
        total_problematic = sum(len(comp['problematic_nodes']) for comp in layout_analysis['components'])
        
        if total_problematic > 0:
            print(f"🚨 ISSUE CONFIRMED: {total_problematic} nodes have parents but will be placed on first level!")
            print(f"\nPossible causes:")
            print(f"   1. Too many disconnected components ({len(layout_analysis['components'])} components)")
            print(f"   2. Semantic start detection failing")
            print(f"   3. Too many nodes matching heuristic start patterns")
            print(f"   4. Graph connectivity issues")
            
            # Recommendations
            print(f"\nRecommended fixes:")
            print(f"   1. Improve start node detection to be more selective")
            print(f"   2. Add validation to detect nodes with parents being treated as starts")
            print(f"   3. Limit the number of start nodes per component")
            print(f"   4. Investigate why so many components exist")
        else:
            print("✅ No obvious issues detected in graph structure.")
            print("The problem might be elsewhere in the layout pipeline.")
            
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 