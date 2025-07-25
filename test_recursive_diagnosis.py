#!/usr/bin/env python3
"""
Diagnostic test for recursive menu parsing issues.
Analyzing v15_mc_evil_robin1 label to understand missing intermediate menu levels.
"""

import sys
from pathlib import Path

# Add the renpy-source-api to the path
sys.path.insert(0, str(Path(__file__).parent / "app" / "renpy-source-api"))
sys.path.insert(0, str(Path(__file__).parent / "ideas-lab" / "flow-visualizer-poc"))

from parser import RenpyParser
from renpy_data_adapter import RenpyFlowDataAdapter

def diagnose_recursive_parsing():
    """Diagnose recursive menu parsing for v15_mc_evil_robin1 label."""
    
    # Define the path to the script file
    script_path = "T:/AG/Savior-0.16c-pc/game/script12.rpy"
    script_file = Path(script_path)
    
    # Check if the file exists, if not use the snippet
    if not script_file.exists():
        print(f"❌ Script file not found at: {script_path}")
        print("📄 Using provided snippet instead...")
        
        # Create a test file from the snippet
        snippet_content = """
label v15_mc_evil_robin1:

    scene v15_day2_morning2_1 with fade
    play music "sounds/slow2.mp3"
    mc "Robin?"
    scene v15_day2_morning2_2
    rb "*Sobbing* Is that *Sobbing* you [mc]?"
    
    menu:
        "Is This Really What You Want":
            scene v15_day2_morning2_22 with dissolve
            mc "Is this really what you want?"
            
            scene v15_day2_robin_good_1 with dissolve
            rb "Yes. I can."
            
            menu:
                "Keep Going":
                    mc "*Panting*"
                    scene v15_day2_robin_evil_4 with dissolve
                    mc "Before we go even further..."
                    
                    menu:
                        "Keep Going":
                            mc "Turn around. I wanna look at your pretty face while fucking you."
                            scene v15_day2_robin_evil_6 with dissolve
                            jump v15_robin_evil_sex_end

                        "Fuck Her Ass":
                            mc "You are gonna let me fuck your ass."
                            scene v15_day2_robin_evil_13 with hpunch
                            jump v15_robin_evil_sex_end

                "Footjob":
                    mc "*Panting*"
                    scene black with fade
                    rb "Why did you stop?"
                    scene v15_day2_robin_good_11 with fade
                    mc "I couldn't take my eyes from your tiny feet."
                    
                    menu:
                        "Keep Going":
                            mc "Turn around. I wanna look at your pretty face while fucking you."
                            scene v15_day2_robin_evil_6 with dissolve
                            jump v15_robin_evil_sex_end

                        "Fuck Her Ass":
                            mc "You are gonna let me fuck your ass."
                            scene v15_day2_robin_evil_13 with hpunch
                            jump v15_robin_evil_sex_end

        "I Don't Think That's A Good Idea":
            mc "I don't think this is a good idea, Robin."
            scene v15_day2_morning2_23 with dissolve
            rb "Oh..."
            jump v16_begin
            
label v15_robin_evil_sex_end:
    "End of scene."
    return
    
label v16_begin:
    "Beginning of next scene."
    return
"""
        
        # Write snippet to temporary file
        test_file = Path("test_v15_snippet.rpy")
        with open(test_file, 'w') as f:
            f.write(snippet_content)
        
        script_dir = "."
        target_file = test_file
    else:
        print(f"✅ Found script file at: {script_path}")
        script_dir = str(script_file.parent)
        target_file = script_file

    try:
        # Parse the content
        parser = RenpyParser()
        flow_graph = parser.build_flow_graph(script_dir)
        
        print("\n" + "="*60)
        print("🔍 RECURSIVE MENU DIAGNOSIS")
        print("="*60)
        
        if 'v15_mc_evil_robin1' not in flow_graph:
            print("❌ Label v15_mc_evil_robin1 not found in flow graph!")
            print("Available labels:", list(flow_graph.keys())[:10], "...")
            return False
            
        label_node = flow_graph['v15_mc_evil_robin1']
        print(f"📊 Label v15_mc_evil_robin1 analysis:")
        print(f"  - Total MenuNodes found: {len(label_node.menu_nodes)}")
        print(f"  - Has menu: {label_node.has_menu}")
        print(f"  - Menu count: {label_node.menu_count}")
        
        # Expected structure analysis
        print(f"\n🎯 EXPECTED STRUCTURE:")
        print(f"  Level 0: Top menu ('Is This Really What You Want', 'I Don't Think That's A Good Idea')")
        print(f"  Level 1: Under 'Is This...' → ('Keep Going', 'Footjob')")
        print(f"  Level 2: Under 'Keep Going' → ('Keep Going', 'Fuck Her Ass')")
        print(f"  Level 2: Under 'Footjob' → ('Keep Going', 'Fuck Her Ass')")
        print(f"  TOTAL EXPECTED: 4 MenuNodes (1 top-level + 3 nested)")
        
        # Analyze actual structure
        print(f"\n📋 ACTUAL PARSED STRUCTURE:")
        top_level_menus = [menu for menu in label_node.menu_nodes if not menu.is_nested]
        nested_menus = [menu for menu in label_node.menu_nodes if menu.is_nested]
        
        print(f"  - Top-level menus: {len(top_level_menus)}")
        print(f"  - Nested menus: {len(nested_menus)}")
        
        # Detailed analysis of each menu
        for i, menu_node in enumerate(label_node.menu_nodes):
            indent = "  " * (menu_node.nesting_level + 1)
            print(f"\n{indent}MenuNode {i}:")
            print(f"{indent}  - ID: {menu_node.node_id}")
            print(f"{indent}  - Name: '{menu_node.name}'")
            print(f"{indent}  - Nested: {menu_node.is_nested}")
            print(f"{indent}  - Level: {menu_node.nesting_level}")
            print(f"{indent}  - Parent: {menu_node.parent_menu_id}")
            print(f"{indent}  - Choices: {len(menu_node.choices)}")
            
            for j, choice in enumerate(menu_node.choices):
                choice_indent = indent + "    "
                print(f"{choice_indent}Choice {j}: '{choice.text}'")
                print(f"{choice_indent}  - Destination: {choice.destination}")
                print(f"{choice_indent}  - Action: {choice.action_type}")
                
                # Check if this choice should have a nested menu
                has_no_destination = not choice.destination or choice.destination == '<return>'
                print(f"{choice_indent}  - No destination: {has_no_destination}")
                print(f"{choice_indent}  - Nested labels: {choice.nested_labels}")
        
        # Test visualization creation
        print(f"\n🎨 VISUALIZATION ANALYSIS:")
        adapter = RenpyFlowDataAdapter()
        container_nodes, choice_connections = adapter._create_menu_containers(flow_graph)
        
        menu_containers = [node for node in container_nodes if node.node_type == 'menu_container']
        choice_buttons = [node for node in container_nodes if node.node_type == 'choice_button']
        
        print(f"  - Menu containers created: {len(menu_containers)}")
        print(f"  - Choice buttons created: {len(choice_buttons)}")
        
        # Analyze containers by nesting level
        containers_by_level = {}
        for container in menu_containers:
            level = container.metadata.get('nesting_level', 0)
            if level not in containers_by_level:
                containers_by_level[level] = []
            containers_by_level[level].append(container)
        
        print(f"\n📊 CONTAINERS BY NESTING LEVEL:")
        for level in sorted(containers_by_level.keys()):
            containers = containers_by_level[level]
            print(f"  Level {level}: {len(containers)} containers")
            for container in containers:
                is_nested = container.metadata.get('is_nested', False)
                parent_id = container.metadata.get('parent_menu_id', 'None')
                print(f"    - {container.node_id}: '{container.display_name}' (nested: {is_nested}, parent: {parent_id})")
        
        # Look for missing menu containers
        print(f"\n🔍 MISSING MENU ANALYSIS:")
        
        # Check if we have all expected choices
        choice_texts = [button.metadata.get('full_text', button.display_name) for button in choice_buttons]
        expected_choices = [
            "Is This Really What You Want",
            "I Don't Think That's A Good Idea", 
            "Keep Going",  # Should appear twice
            "Footjob",
            "Fuck Her Ass"  # Should appear twice
        ]
        
        print(f"  Found choice texts: {choice_texts}")
        print(f"  Expected choices: {expected_choices}")
        
        missing_choices = []
        for expected in expected_choices:
            if expected not in choice_texts:
                missing_choices.append(expected)
        
        if missing_choices:
            print(f"  ❌ MISSING CHOICES: {missing_choices}")
        else:
            print(f"  ✅ All expected choice texts found")
            
        # Check for "Footjob" specifically
        footjob_found = any("Footjob" in text for text in choice_texts)
        print(f"  🦶 'Footjob' choice found: {footjob_found}")
        
        if not footjob_found:
            print(f"  ❌ CRITICAL: 'Footjob' choice is missing!")
            print(f"  This suggests intermediate menu levels are being skipped.")
        
        # Count Keep Going and Fuck Her Ass occurrences
        keep_going_count = sum(1 for text in choice_texts if "Keep Going" in text)
        fuck_her_ass_count = sum(1 for text in choice_texts if "Fuck Her Ass" in text)
        
        print(f"  📊 'Keep Going' occurrences: {keep_going_count} (expected: 3)")
        print(f"  📊 'Fuck Her Ass' occurrences: {fuck_her_ass_count} (expected: 2)")
        
        # Summary
        print(f"\n📋 DIAGNOSIS SUMMARY:")
        if len(menu_containers) < 4:
            print(f"  ❌ ISSUE: Only {len(menu_containers)} menu containers found, expected 4")
        if not footjob_found:
            print(f"  ❌ ISSUE: 'Footjob' choice missing - intermediate menu skipped")
        if keep_going_count < 3:
            print(f"  ❌ ISSUE: 'Keep Going' appears {keep_going_count} times, expected 3")
        if fuck_her_ass_count < 2:
            print(f"  ❌ ISSUE: 'Fuck Her Ass' appears {fuck_her_ass_count} times, expected 2")
            
        return len(menu_containers) == 4 and footjob_found
            
    except Exception as e:
        print(f"❌ ERROR during diagnosis: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up test file if created
        test_file = Path("test_v15_snippet.rpy")
        if test_file.exists():
            test_file.unlink()
            
    return False

if __name__ == "__main__":
    print("🔍 Starting recursive menu parsing diagnosis...")
    success = diagnose_recursive_parsing()
    if success:
        print("\n✅ Recursive parsing appears to be working correctly.")
    else:
        print("\n❌ Recursive parsing issues detected. Further investigation needed.") 