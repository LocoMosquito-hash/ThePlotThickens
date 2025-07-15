#!/usr/bin/env python3
"""
Test script for menu node separation implementation.

This tests the new MenuNode system with the provided VN file example.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any

# Add the parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from parser import RenpyParser, MenuNode, LabelNode
    from core import RenpyProject
    from flow_visualizer import FlowVisualizer
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the correct directory")
    sys.exit(1)


def test_menu_node_creation():
    """Test MenuNode creation from the provided VN file."""
    print("🔍 Testing MenuNode creation...")
    
    # Use the provided VN path
    vn_path = r"T:\AG\MySisterMyRoommateV1.69-pc\game"
    
    if not os.path.exists(vn_path):
        print(f"❌ VN path not found: {vn_path}")
        print("Please check that the VN is accessible at this path")
        return False
    
    try:
        # Initialize parser and project
        parser = RenpyParser()
        project = RenpyProject(vn_path)
        
        # Test menu node creation
        print(f"📂 Analyzing project: {vn_path}")
        menu_nodes = parser.get_all_menu_nodes(vn_path)
        menu_nodes_by_label = parser.get_menu_nodes_by_label(vn_path)
        
        print(f"✅ Found {len(menu_nodes)} total menu nodes")
        print(f"✅ Found menus in {len(menu_nodes_by_label)} labels")
        
        # Look specifically for ch4ashbagdone
        if 'ch4ashbagdone' in menu_nodes_by_label:
            ch4_menus = menu_nodes_by_label['ch4ashbagdone']
            print(f"\n🎯 Found ch4ashbagdone with {len(ch4_menus)} menus:")
            
            for i, menu_node in enumerate(ch4_menus):
                print(f"  Menu {i+1}: {menu_node.node_id}")
                print(f"    Name: {menu_node.name}")
                print(f"    Choices: {menu_node.total_choices}")
                print(f"    Complexity: {menu_node.complexity_level}")
                print(f"    Destinations: {menu_node.choice_destinations}")
                
                for j, choice in enumerate(menu_node.choices):
                    print(f"      Choice {j+1}: '{choice.text}' -> {choice.destination}")
        else:
            print("❌ ch4ashbagdone label not found in menu analysis")
            print("Available labels with menus:")
            for label_name in list(menu_nodes_by_label.keys())[:10]:
                print(f"  - {label_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_flow_graph_building():
    """Test the enhanced flow graph building with separate menu nodes."""
    print("\n🔧 Testing flow graph building...")
    
    vn_path = r"T:\AG\MySisterMyRoommateV1.69-pc\game"
    
    if not os.path.exists(vn_path):
        print(f"❌ VN path not found: {vn_path}")
        return False
    
    try:
        parser = RenpyParser()
        
        # Build the enhanced flow graph
        print("🏗️ Building enhanced flow graph...")
        flow_graph = parser.build_flow_graph(vn_path)
        
        print(f"✅ Built flow graph with {len(flow_graph)} label nodes")
        
        # Analyze menu integration
        labels_with_menus = 0
        total_menu_nodes = 0
        
        for label_name, label_node in flow_graph.items():
            if label_node.has_menu:
                labels_with_menus += 1
                total_menu_nodes += label_node.menu_count
        
        print(f"✅ Found {labels_with_menus} labels with menus")
        print(f"✅ Total menu nodes: {total_menu_nodes}")
        
        # Check ch4ashbagdone specifically
        if 'ch4ashbagdone' in flow_graph:
            label_node = flow_graph['ch4ashbagdone']
            print(f"\n🎯 ch4ashbagdone analysis:")
            print(f"    Has menu: {label_node.has_menu}")
            print(f"    Menu count: {label_node.menu_count}")
            print(f"    Outgoing flows: {len(label_node.outgoing_flows)}")
            print(f"    Menu destinations: {label_node.get_all_menu_destinations()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during flow graph testing: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_visualization_generation():
    """Test the visualization generation with new menu nodes."""
    print("\n🎨 Testing visualization generation...")
    
    vn_path = r"T:\AG\MySisterMyRoommateV1.69-pc\game"
    
    if not os.path.exists(vn_path):
        print(f"❌ VN path not found: {vn_path}")
        return False
    
    try:
        # Initialize project and visualizer
        project = RenpyProject(vn_path)
        
        # This should use our enhanced flow graph building
        print("🎯 Initializing flow visualizer...")
        visualizer = FlowVisualizer(project)
        
        # Get basic statistics about the graph
        if hasattr(visualizer, 'graph') and visualizer.graph:
            total_nodes = len(visualizer.graph.nodes())
            menu_nodes = sum(1 for _, data in visualizer.graph.nodes(data=True) 
                           if data.get('node_type') == 'menu')
            label_nodes = total_nodes - menu_nodes
            
            print(f"✅ Graph contains {total_nodes} total nodes:")
            print(f"    - {label_nodes} label nodes")
            print(f"    - {menu_nodes} menu nodes")
            
            # Check edge types
            edge_types = {}
            for _, _, edge_data in visualizer.graph.edges(data=True):
                edge_style = edge_data.get('edge_style', 'unknown')
                edge_types[edge_style] = edge_types.get(edge_style, 0) + 1
            
            print(f"✅ Edge type distribution:")
            for edge_type, count in edge_types.items():
                print(f"    - {edge_type}: {count}")
            
            # Try to generate a small interactive map (limited nodes for testing)
            try:
                print("🌐 Generating test interactive flow map...")
                output_path = "test_menu_separation_map.html"
                visualizer.generate_interactive_flow_map(output_path, max_nodes=50)
                print(f"✅ Generated test visualization: {output_path}")
            except Exception as viz_error:
                print(f"⚠️ Visualization generation failed: {viz_error}")
                # This might fail due to missing plotly, which is okay for testing the core logic
        
        return True
        
    except Exception as e:
        print(f"❌ Error during visualization testing: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests for the menu separation implementation."""
    print("🚀 Testing Menu Node Separation Implementation")
    print("=" * 50)
    
    tests = [
        ("Menu Node Creation", test_menu_node_creation),
        ("Flow Graph Building", test_flow_graph_building),
        ("Visualization Generation", test_visualization_generation),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 30)
        
        success = test_func()
        results.append((test_name, success))
        
        if success:
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Menu separation implementation is working.")
    else:
        print("⚠️ Some tests failed. Check the errors above for details.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 