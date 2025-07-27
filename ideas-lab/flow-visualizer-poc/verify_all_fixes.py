#!/usr/bin/env python3
"""
Verification script for all Flow Visualizer POC fixes.

This script tests the critical fixes to ensure the architecture is working correctly:
1. Container-to-choice connection fix
2. Recursive directory search fix  
3. Smart orphan detection

Run this script after any changes to verify the fixes still work.
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Add renpy-source-api to path
app_dir = current_dir.parent.parent / "app"
sys.path.insert(0, str(app_dir / "renpy-source-api"))

from renpy_data_adapter import RenpyFlowDataAdapter
from control_flow.analyze_vn_menus import MenuAnalyzer

def test_recursive_directory_search():
    """Test Fix #2: Recursive directory search"""
    print("🔍 TESTING FIX #2: Recursive Directory Search")
    print("-" * 50)
    
    game_path = "T:/AG/LastCall-0.4-pc/game"
    if not os.path.exists(game_path):
        print("❌ Test game not found - skipping test")
        return False
        
    analyzer = MenuAnalyzer()
    analysis = analyzer.analyze_vn_menus(game_path)
    
    total_menus = analysis.get('total_menus', 0)
    print(f"📊 Menus detected: {total_menus}")
    
    # Look for our known test menu
    menu_structures = analysis.get('menu_structures', [])
    ch1_menu_found = any(menu.label_context == 'ch1mckellycar' for menu in menu_structures)
    
    if ch1_menu_found and total_menus > 50:  # LastCall has 92+ menus
        print("✅ PASS: Recursive search working - found menus in subdirectories")
        return True
    else:
        print("❌ FAIL: Recursive search not working properly")
        return False

def test_container_choice_connections():
    """Test Fix #1: Container-to-choice connections"""
    print("\n🔗 TESTING FIX #1: Container-to-Choice Connections")
    print("-" * 50)
    
    game_path = "T:/AG/LastCall-0.4-pc/game"
    if not os.path.exists(game_path):
        print("❌ Test game not found - skipping test")
        return False
        
    adapter = RenpyFlowDataAdapter()
    viz_data = adapter.analyze_project(game_path, use_sdk=True)
    
    # Count node types
    menu_containers = [n for n in viz_data.nodes if n.node_type == 'menu_container']
    choice_nodes = [n for n in viz_data.nodes if n.node_type == 'choice']
    
    print(f"📊 Menu containers: {len(menu_containers)}")
    print(f"📊 Choice nodes: {len(choice_nodes)}")
    
    # Check for container-to-choice connections
    container_choice_connections = [
        c for c in viz_data.connections 
        if c.connection_type == 'container_to_choice'
    ]
    
    print(f"📊 Container-to-choice connections: {len(container_choice_connections)}")
    
    if len(menu_containers) > 80 and len(choice_nodes) > 150 and len(container_choice_connections) > 150:
        print("✅ PASS: Container-choice connections working")
        return True
    else:
        print("❌ FAIL: Container-choice connections not working properly")
        return False

def test_orphan_detection():
    """Test Fix #3: Smart orphan detection"""
    print("\n🧠 TESTING FIX #3: Smart Orphan Detection")
    print("-" * 50)
    
    # Test with Savior if available
    savior_path = "T:/AG/Savior-0.16c-pc/game"
    if not os.path.exists(savior_path):
        print("❌ Savior test game not found - skipping test")
        return False
        
    adapter = RenpyFlowDataAdapter()
    viz_data = adapter.analyze_project(savior_path, use_sdk=True)
    
    # Build a simple graph to count potential start nodes
    import networkx as nx
    G = nx.DiGraph()
    
    for node in viz_data.nodes:
        G.add_node(node.node_id)
        
    for conn in viz_data.connections:
        G.add_edge(conn.source, conn.target)
        
    # Count nodes with in_degree == 0 (potential start nodes)
    orphan_candidates = [n for n in G.nodes() if G.in_degree(n) == 0]
    
    print(f"📊 Total nodes: {len(viz_data.nodes)}")
    print(f"📊 Potential start nodes (in_degree=0): {len(orphan_candidates)}")
    
    # Should be much less than the old "489 nodes on first level"
    if len(orphan_candidates) < 20:  # Much better than 489!
        print("✅ PASS: Smart orphan detection working - reasonable start node count")
        return True
    else:
        print("❌ FAIL: Too many potential start nodes - orphan detection may be broken")
        return False

def main():
    """Run all verification tests"""
    print("🧪 FLOW VISUALIZER POC - FIX VERIFICATION")
    print("=" * 60)
    print("📖 Testing critical fixes documented in FLOW_VISUALIZER_ARCHITECTURE.md")
    print()
    
    results = []
    
    # Test all fixes
    results.append(test_recursive_directory_search())
    results.append(test_container_choice_connections())
    results.append(test_orphan_detection())
    
    # Summary
    print("\n📋 VERIFICATION SUMMARY")
    print("=" * 30)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 ALL TESTS PASSED ({passed}/{total})")
        print("✅ Flow Visualizer POC architecture is working correctly!")
    else:
        print(f"⚠️  SOME TESTS FAILED ({passed}/{total})")
        print("❌ Check the failed tests and refer to FLOW_VISUALIZER_ARCHITECTURE.md")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 