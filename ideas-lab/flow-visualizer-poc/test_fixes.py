#!/usr/bin/env python3
"""
Test Script for Flow Visualizer Fixes
=====================================

Test the search functionality and menu container positioning fixes.
"""

import sys
from pathlib import Path

# Add the main app directory to path for renpy-source-api imports
current_dir = Path(__file__).parent
app_dir = current_dir.parent.parent / "app"
renpy_api_dir = app_dir / "renpy-source-api"
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(renpy_api_dir))

from PyQt6.QtWidgets import QApplication
from vn_flow_visualizer import VNFlowVisualizer
from vn_control_panel import VNControlPanel

def test_search_functionality():
    """Test the search functionality with mock data."""
    print("=== TESTING SEARCH FUNCTIONALITY ===")
    
    app = QApplication(sys.argv)
    
    # Create visualizer
    visualizer = VNFlowVisualizer()
    
    # Create some mock data to test search
    from vn_flow_visualizer import VNLabelNode
    
    # Add some test nodes
    test_nodes = [
        ("ch4ashbagdone", {"name": "ch4ashbagdone", "has_menu": True}),
        ("ch4ashbagdone_menu_container", {"name": "Menu: ch4ashbagdone", "node_type": "menu_container"}),
        ("start", {"name": "start", "has_menu": False}),
        ("some_other_node", {"name": "some_other_node", "has_menu": False})
    ]
    
    for node_id, node_data in test_nodes:
        node_item = VNLabelNode(node_id, node_data, "linear")
        visualizer.scene.addItem(node_item)
        visualizer.nodes[node_id] = node_item
        # Position them manually for testing
        x = len(visualizer.nodes) * 100
        node_item.setPos(x, 0)
    
    # Test search functionality
    print(f"Added {len(visualizer.nodes)} test nodes")
    
    # Test 1: Exact match
    result = visualizer.search_and_select_node("ch4ashbagdone")
    print(f"Search for 'ch4ashbagdone': {'PASS' if result else 'FAIL'}")
    
    # Test 2: Partial match
    result = visualizer.search_and_select_node("ashbag")
    print(f"Search for 'ashbag': {'PASS' if result else 'FAIL'}")
    
    # Test 3: Case insensitive
    result = visualizer.search_and_select_node("CH4ASHBAG")
    print(f"Search for 'CH4ASHBAG': {'PASS' if result else 'FAIL'}")
    
    # Test 4: No match
    result = visualizer.search_and_select_node("nonexistent")
    print(f"Search for 'nonexistent': {'PASS' if not result else 'FAIL'}")
    
    app.quit()
    print("✅ Search functionality tests completed\n")

def test_menu_container_positioning():
    """Test the menu container positioning logic."""
    print("=== TESTING MENU CONTAINER POSITIONING ===")
    
    app = QApplication(sys.argv)
    
    # Create visualizer
    visualizer = VNFlowVisualizer()
    
    # Add test nodes with parent-child relationship
    from vn_flow_visualizer import VNLabelNode
    
    # Parent node
    parent_node = VNLabelNode("ch4ashbagdone", {"name": "ch4ashbagdone", "has_menu": True}, "decision_point")
    parent_node.setPos(100, 200)
    visualizer.scene.addItem(parent_node)
    visualizer.nodes["ch4ashbagdone"] = parent_node
    
    # Menu container node
    menu_node = VNLabelNode("ch4ashbagdone_menu_container", {
        "name": "Menu: ch4ashbagdone", 
        "node_type": "menu_container"
    }, "menu_container")
    menu_node.setPos(0, 0)  # Initially at origin
    visualizer.scene.addItem(menu_node)
    visualizer.nodes["ch4ashbagdone_menu_container"] = menu_node
    
    print(f"Parent node position: ({parent_node.pos().x()}, {parent_node.pos().y()})")
    print(f"Menu container initial position: ({menu_node.pos().x()}, {menu_node.pos().y()})")
    
    # Apply menu container positioning fix
    visualizer._position_menu_containers_relative_to_parents()
    
    print(f"Menu container final position: ({menu_node.pos().x()}, {menu_node.pos().y()})")
    
    # Check if menu container is positioned correctly (should be 80 units to the right)
    expected_x = parent_node.pos().x() + 80
    expected_y = parent_node.pos().y()
    
    actual_x = menu_node.pos().x()
    actual_y = menu_node.pos().y()
    
    x_correct = abs(actual_x - expected_x) < 1  # Allow small floating point differences
    y_correct = abs(actual_y - expected_y) < 1
    
    print(f"Expected position: ({expected_x}, {expected_y})")
    print(f"Position X correct: {'PASS' if x_correct else 'FAIL'}")
    print(f"Position Y correct: {'PASS' if y_correct else 'FAIL'}")
    
    app.quit()
    print("✅ Menu container positioning tests completed\n")

def test_control_panel_search():
    """Test the control panel search integration."""
    print("=== TESTING CONTROL PANEL SEARCH INTEGRATION ===")
    
    app = QApplication(sys.argv)
    
    # Create control panel
    control_panel = VNControlPanel()
    
    # Test that search components exist
    has_search_input = hasattr(control_panel, 'search_input')
    has_search_button = hasattr(control_panel, 'search_button')
    has_search_signal = hasattr(control_panel, 'search_node')
    
    print(f"Search input exists: {'PASS' if has_search_input else 'FAIL'}")
    print(f"Search button exists: {'PASS' if has_search_button else 'FAIL'}")
    print(f"Search signal exists: {'PASS' if has_search_signal else 'FAIL'}")
    
    # Test search input functionality
    if has_search_input:
        control_panel.search_input.setText("test_search")
        text = control_panel.search_input.text()
        print(f"Search input text setting: {'PASS' if text == 'test_search' else 'FAIL'}")
    
    app.quit()
    print("✅ Control panel search integration tests completed\n")

if __name__ == "__main__":
    print("🔧 Testing Flow Visualizer Fixes")
    print("=" * 40)
    
    test_search_functionality()
    test_menu_container_positioning()
    test_control_panel_search()
    
    print("✅ All tests completed!")
    print("\nTo test manually:")
    print("1. Run: python renpy_flow_visualizer.py")
    print("2. Load a project with real data")
    print("3. Use the 'Find Node' search box to locate 'ch4ashbagdone'")
    print("4. Check that menu containers appear next to their parent nodes") 