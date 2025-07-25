#!/usr/bin/env python3
"""
Test to verify the hierarchy connection fix using the actual v15_mc_evil_robin1 structure.
"""

import sys
from pathlib import Path

# Add the renpy-source-api to the path
sys.path.insert(0, str(Path(__file__).parent / "app" / "renpy-source-api"))
sys.path.insert(0, str(Path(__file__).parent / "ideas-lab" / "flow-visualizer-poc"))

def test_hierarchy_fix_verification():
    """Test that the hierarchy connection fix works with the actual nested structure."""
    
    # Use the exact content from the user's file
    test_content = """
label v15_mc_evil_robin1:
    scene v15_day2_morning2_1 with fade
    play music "sounds/slow2.mp3"
    mc "Robin?"
    
    menu:
        "Is This Really What You Want":
            scene v15_day2_morning2_22 with dissolve
            mc "Is this really what you want?"
            
            menu:
                "Keep Going":
                    mc "*Panting*"
                    scene v15_day2_robin_evil_4 with dissolve
                    mc "Before we go even further..."
                    
                    menu:
                        "Keep Going":
                            mc "Turn around. I wanna look at your pretty face while fucking you."
                            jump v15_robin_evil_sex_end

                        "Fuck Her Ass":
                            mc "Very well then."
                            jump v15_robin_evil_sex_end

                "Footjob":
                    mc "*Panting*"
                    scene black with fade
                    rb "Why did you stop?"
                    
                    menu:
                        "Keep Going":
                            mc "Turn around. I wanna look at your pretty face while fucking you."
                            jump v15_robin_evil_sex_end

                        "Fuck Her Ass":
                            mc "Very well then."
                            jump v15_robin_evil_sex_end

        "I Don't Think That's A Good Idea":
            mc "I don't think this is a good idea, Robin."
            jump v16_begin
"""

    # Write test file
    test_file = Path("test_v15_structure.rpy")
    test_file.write_text(test_content)
    
    try:
        print("=== HIERARCHY FIX VERIFICATION TEST ===")
        
        # Test the full pipeline: Parser -> Adapter -> Visualization
        from parser import RenpyParser
        from renpy_data_adapter import RenpyFlowDataAdapter
        
        # Step 1: Parse with RenpyParser
        parser = RenpyParser()
        graph = parser.build_flow_graph(str(test_file.parent))
        
        # Get the v15_mc_evil_robin1 label
        label_node = graph.get('v15_mc_evil_robin1')
        if not label_node:
            print("[ERROR] v15_mc_evil_robin1 label not found")
            return
            
        print(f"Found {len(label_node.menu_nodes)} MenuNodes in v15_mc_evil_robin1")
        
        # Show MenuNode hierarchy
        for i, menu_node in enumerate(label_node.menu_nodes):
            level_indent = "  " * menu_node.nesting_level
            print(f"{level_indent}MenuNode {i}: Level {menu_node.nesting_level}, ID: {menu_node.node_id}")
            print(f"{level_indent}  Choices: {[choice.text for choice in menu_node.choices]}")
        
        # Step 2: Test the visualization adapter
        adapter = RenpyFlowDataAdapter()
        nodes, connections = adapter.create_visualization_graph(graph, str(test_file.parent))
        
        # Analyze the results
        menu_containers = [n for n in nodes if n.node_type == 'menu_container']
        choice_buttons = [n for n in nodes if n.node_type == 'choice_button'] 
        hierarchy_connections = [c for c in connections if c.connection_type == 'choice_to_nested_menu']
        
        print(f"\n=== VISUALIZATION RESULTS ===")
        print(f"Menu containers: {len(menu_containers)}")
        print(f"Choice buttons: {len(choice_buttons)}")
        print(f"Hierarchy connections: {len(hierarchy_connections)}")
        
        # Show menu containers
        print(f"\n=== MENU CONTAINERS ===")
        for container in menu_containers:
            nesting_info = "nested" if "nested" in container.node_id else "top-level"
            print(f"  {container.node_id} ({nesting_info})")
            print(f"    Display: {container.display_name}")
        
        # Show hierarchy connections  
        print(f"\n=== HIERARCHY CONNECTIONS ===")
        for conn in hierarchy_connections:
            print(f"  {conn.source_node_id} -> {conn.target_node_id}")
            
        # Check if all expected connections exist
        expected_connections = [
            # Top-level choice to first nested menu
            ("v15_mc_evil_robin1_menu_0_choice_0", "v15_mc_evil_robin1_nested_menu_1_choice_0_menu_1"),
            # First nested choices to second nested menus  
            ("v15_mc_evil_robin1_nested_menu_1_choice_0_menu_1_choice_0", "v15_mc_evil_robin1_nested_menu_1_choice_0_menu_1_choice_0_menu_1"),
            ("v15_mc_evil_robin1_nested_menu_1_choice_0_menu_1_choice_1", "v15_mc_evil_robin1_nested_menu_1_choice_0_menu_1_choice_1_menu_1")
        ]
        
        actual_connections = [(c.source_node_id, c.target_node_id) for c in hierarchy_connections]
        
        print(f"\n=== CONNECTION VERIFICATION ===")
        missing_connections = []
        for expected in expected_connections:
            if expected in actual_connections:
                print(f"  ✅ {expected[0]} -> {expected[1]}")
            else:
                print(f"  ❌ MISSING: {expected[0]} -> {expected[1]}")
                missing_connections.append(expected)
        
        if missing_connections:
            print(f"\n❌ TEST FAILED: {len(missing_connections)} missing connections")
            print("Available choice buttons:")
            for choice in choice_buttons:
                print(f"  - {choice.node_id}")
            print("Available containers:")
            for container in menu_containers:
                print(f"  - {container.node_id}")
        else:
            print(f"\n✅ TEST PASSED: All hierarchy connections found!")
            
    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()

if __name__ == "__main__":
    test_hierarchy_fix_verification() 