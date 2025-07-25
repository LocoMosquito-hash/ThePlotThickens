#!/usr/bin/env python3
"""
Debug script to investigate nested label flow filtering issues.
"""

import sys
from pathlib import Path

# Add parent directories to path for imports  
app_dir = Path(__file__).parent.parent.parent / "app"
sys.path.insert(0, str(app_dir / "renpy-source-api"))
sys.path.insert(0, str(Path(__file__).parent))

from core import RenpyProject
from renpy_data_adapter import RenpyFlowDataAdapter

def debug_nested_labels():
    """Debug why day01_r_masturbation flows aren't being filtered."""
    
    project_path = r"F:\Bin\Games\SL-1.0-ExtraScenesEdition(PC)\game"
    
    print("=== DEBUGGING NESTED LABEL FILTERING ===")
    print("=" * 50)
    
    # 1. Load project and get parser
    print("1. Loading project...")
    project = RenpyProject(project_path)
    project.analyze()
    
    # 2. Get flow graph using the same method as the adapter
    print("2. Getting flow graph using parser...")
    flow_graph = project.parser.build_flow_graph(project_path)
    
    # 3. Focus on day01_r_bedroom
    target_label = "day01_r_bedroom"
    if target_label in flow_graph:
        label_node = flow_graph[target_label]
        print(f"\n3. Found {target_label}:")
        print(f"   has_menus: {hasattr(label_node, 'menu_nodes')}")
        
        if hasattr(label_node, 'menu_nodes'):
            print(f"   menu_nodes: {label_node.menu_nodes}")
            if label_node.menu_nodes:
                for i, menu_node in enumerate(label_node.menu_nodes):
                    print(f"   Menu {i}: {len(menu_node.choices)} choices")
                    for j, choice in enumerate(menu_node.choices):
                        print(f"     Choice {j}: '{choice.text}'")
                        print(f"       destination: {choice.destination}")
                        print(f"       nested_labels: {choice.nested_labels}")
                        
                        # ADDITIONAL: Check the raw menu parsing directly
                        print(f"       subsequent_lines count: {len(choice.subsequent_lines)}")
                        for k, line in enumerate(choice.subsequent_lines[:5]):  # First 5 lines
                            print(f"         Line {k}: '{line}'")
                        if len(choice.subsequent_lines) > 5:
                            print(f"         ... and {len(choice.subsequent_lines)-5} more lines")
    
    # 4. TEST: Manual parsing of the specific choice
    print("\n4. MANUAL PARSING TEST:")
    print("   Looking for choice containing 'Knock on her door'...")
    
    # Find the specific menu with the nested label
    target_choice_text = "Knock on her door"
    found_choice = None
    
    if target_label in flow_graph and hasattr(flow_graph[target_label], 'menu_nodes'):
        for menu_node in flow_graph[target_label].menu_nodes:
            for choice in menu_node.choices:
                if target_choice_text in choice.text:
                    found_choice = choice
                    break
            if found_choice:
                break
    
    if found_choice:
        print(f"   Found choice: '{found_choice.text}'")
        print(f"   subsequent_lines: {len(found_choice.subsequent_lines)}")
        
        # Look for the nested label manually in subsequent lines
        nested_found = False
        for line in found_choice.subsequent_lines:
            if line.strip().startswith('label day01_r_masturbation'):
                print(f"   FOUND NESTED LABEL LINE: '{line}'")
                nested_found = True
                break
        
        if not nested_found:
            print("   NO NESTED LABEL FOUND in subsequent_lines")
            print("   First 10 subsequent lines:")
            for i, line in enumerate(found_choice.subsequent_lines[:10]):
                print(f"     {i}: '{line}'")
    
    # 5. Test destination detection
    print("\n5. Testing destination detection...")
    adapter = RenpyFlowDataAdapter()
    destinations = adapter._get_menu_choice_destinations(flow_graph)
    
    print(f"   Total destinations found: {len(destinations)}")
    print(f"   day01_r_masturbation in destinations: {'day01_r_masturbation' in destinations}")
    print(f"   All destinations: {sorted(destinations)}")
    
    # 6. Check final flows
    print("\n6. Checking flows from project...")
    flows = project.get_all_flows()
    masturbation_flows = [f for f in flows if f.target_label == "day01_r_masturbation"]
    
    print(f"   Total flows to day01_r_masturbation: {len(masturbation_flows)}")
    for flow in masturbation_flows:
        print(f"     {flow.source_label} -> {flow.target_label} (type: {flow.flow_type})")

if __name__ == "__main__":
    debug_nested_labels() 