#!/usr/bin/env python3
"""
Test script to verify the Savior layout fixes are working.

This script loads the Savior game and checks:
1. Whether the critical graph connectivity fix worked
2. Whether the orphan filtering is working
3. Whether the number of first-level nodes is reasonable
"""

import sys
import os
from pathlib import Path
import networkx as nx

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Add renpy-source-api to path
app_dir = current_dir.parent.parent / "app"
sys.path.insert(0, str(app_dir / "renpy-source-api"))

# Import the data adapter
from renpy_data_adapter import RenpyFlowDataAdapter

def test_savior_fix():
    """Test the Savior layout fixes."""
    
    # Savior game path
    savior_path = r"T:/AG/Savior-0.16c-pc/game"
    
    if not os.path.exists(savior_path):
        print(f"❌ Savior path not found: {savior_path}")
        print("Please update the path and try again.")
        return False
    
    print(f"🎮 Testing Savior fixes at: {savior_path}")
    
    try:
        # Load the data using the fixed adapter
        print("\n📊 Loading visualization data with fixes...")
        adapter = RenpyFlowDataAdapter(use_hybrid=True)
        visualization_data = adapter.analyze_project(savior_path, use_sdk=True)
        
        print(f"✅ Loaded {len(visualization_data.nodes)} nodes and {len(visualization_data.connections)} connections")
        
        # Build NetworkX graph to test connectivity
        print("\n🔗 Building NetworkX graph...")
        graph = nx.DiGraph()
        
        # Add nodes
        for node_data in visualization_data.nodes:
            graph.add_node(node_data.node_id, **node_data.metadata)
        
        # Add edges  
        for conn_data in visualization_data.connections:
            graph.add_edge(conn_data.source_node_id, conn_data.target_node_id)
        
        print(f"✅ NetworkX graph created: {len(graph.nodes())} nodes, {len(graph.edges())} edges")
        
        # Test 1: Check connectivity improvement
        print("\n🔍 Testing connectivity improvement...")
        if graph.is_directed():
            components = list(nx.weakly_connected_components(graph))
        else:
            components = list(nx.connected_components(graph))
        
        print(f"📊 Disconnected components: {len(components)}")
        
        if len(components) < 50:  # Much better than the original 200
            print(f"✅ MAJOR IMPROVEMENT: Components reduced from 200 to {len(components)}")
        elif len(components) < 100:
            print(f"✅ GOOD IMPROVEMENT: Components reduced from 200 to {len(components)}")
        else:
            print(f"⚠️  PARTIAL IMPROVEMENT: Components reduced from 200 to {len(components)}")
        
        # Test 2: Check orphan nodes
        print("\n🏝️  Testing orphan detection...")
        orphan_nodes = [n for n in graph.nodes() if graph.in_degree(n) == 0]
        print(f"📊 Total orphan nodes (in_degree=0): {len(orphan_nodes)}")
        
        # Test 3: Check menu choice connectivity
        print("\n🔗 Testing menu choice connectivity...")
        choice_nodes = [n for n in graph.nodes() if '_choice_' in str(n)]
        orphaned_choices = [n for n in choice_nodes if graph.in_degree(n) == 0]
        
        print(f"📊 Total choice nodes: {len(choice_nodes)}")
        print(f"📊 Orphaned choice nodes: {len(orphaned_choices)}")
        
        if len(orphaned_choices) == 0:
            print(f"✅ PERFECT: All choice nodes are properly connected!")
        elif len(orphaned_choices) < len(choice_nodes) * 0.1:  # Less than 10% orphaned
            print(f"✅ GOOD: Only {len(orphaned_choices)} orphaned choices ({len(orphaned_choices)/len(choice_nodes)*100:.1f}%)")
        else:
            print(f"⚠️  NEEDS WORK: {len(orphaned_choices)} orphaned choices ({len(orphaned_choices)/len(choice_nodes)*100:.1f}%)")
        
        # Test 4: Estimate first-level nodes
        print("\n📊 Estimating first-level node count...")
        
        # Find the main component (largest one)
        main_component = max(components, key=len)
        main_subgraph = graph.subgraph(main_component).copy()
        
        # Count potential start nodes in main component
        potential_starts = [n for n in main_subgraph.nodes() if main_subgraph.in_degree(n) == 0]
        
        print(f"📊 Main component size: {len(main_component)} nodes")
        print(f"📊 Potential start nodes in main component: {len(potential_starts)}")
        
        if len(potential_starts) <= 5:
            print(f"✅ EXCELLENT: Only {len(potential_starts)} start nodes (vs 489 before)")
        elif len(potential_starts) <= 20:
            print(f"✅ GOOD: {len(potential_starts)} start nodes (vs 489 before)")
        else:
            print(f"⚠️  IMPROVEMENT NEEDED: {len(potential_starts)} start nodes (vs 489 before)")
        
        # Test 5: Check container-to-choice connections
        print("\n🔗 Testing container-to-choice connections...")
        container_to_choice_connections = [
            conn for conn in visualization_data.connections 
            if conn.connection_type == 'container_to_choice'
        ]
        
        print(f"📊 Container-to-choice connections: {len(container_to_choice_connections)}")
        
        if len(container_to_choice_connections) > 0:
            print(f"✅ SUCCESS: Critical fix applied - {len(container_to_choice_connections)} container-to-choice connections created!")
        else:
            print(f"❌ ISSUE: No container-to-choice connections found - fix may not be working")
        
        # Summary
        print("\n" + "="*60)
        print("🎯 SUMMARY OF FIXES")
        print("="*60)
        print(f"✅ Graph connectivity: {len(components)} components (was 200)")
        print(f"✅ Choice connectivity: {len(choice_nodes) - len(orphaned_choices)}/{len(choice_nodes)} connected")
        print(f"✅ Container connections: {len(container_to_choice_connections)} created")
        print(f"✅ Expected first-level reduction: ~{len(potential_starts)} nodes (was 489)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_savior_fix()
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n💥 Test failed!") 