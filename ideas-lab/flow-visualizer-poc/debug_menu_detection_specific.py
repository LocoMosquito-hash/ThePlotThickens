#!/usr/bin/env python3
"""
Debug Menu Detection - Specific
===============================

Check why day02_living_room_conversation is not detected by MenuAnalyzer.
"""

import sys
import os

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_specific_label_menu():
    """Check why day02_living_room_conversation is missing."""
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    if not os.path.exists(project_path):
        print(f"ERROR: Project path not found: {project_path}")
        return
    
    print("Debugging specific label menu detection...")
    print("=" * 60)
    
    try:
        # Add the control_flow path
        control_flow_path = os.path.join(project_root, "app", "renpy-source-api", "control_flow")
        sys.path.insert(0, control_flow_path)
        
        from analyze_vn_menus import MenuAnalyzer
        
        # 1. Check if day02_living_room_conversation exists in .rpy files
        print("1. SEARCHING FOR 'day02_living_room_conversation' in files:")
        print("-" * 50)
        
        import pathlib
        game_dir = pathlib.Path(project_path)
        rpy_files = list(game_dir.rglob('*.rpy'))
        
        found_files = []
        for rpy_file in rpy_files:
            try:
                with open(rpy_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if 'day02_living_room_conversation' in content:
                        found_files.append(rpy_file)
                        print(f"  ✅ Found in: {rpy_file}")
                        
                        # Show relevant lines
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if 'day02_living_room_conversation' in line:
                                start = max(0, i-2)
                                end = min(len(lines), i+3)
                                print(f"    Lines {start+1}-{end}:")
                                for j in range(start, end):
                                    marker = " >>> " if j == i else "     "
                                    print(f"    {marker}{j+1}: {lines[j]}")
                                print()
            except Exception as e:
                print(f"  ❌ Error reading {rpy_file}: {e}")
        
        if not found_files:
            print("  ❌ NOT FOUND in any .rpy files!")
        
        # 2. Check MenuAnalyzer detection
        print("\n2. MENU ANALYZER DETECTION:")
        print("-" * 50)
        
        analyzer = MenuAnalyzer()
        menu_analysis = analyzer.analyze_vn_menus(project_path)
        menus = menu_analysis.get('menu_structures', [])
        
        print(f"Total menus detected: {len(menus)}")
        
        # Look for any menus with similar names
        day02_menus = [m for m in menus if 'day02' in str(m.label_name) and 'living_room' in str(m.label_name)]
        print(f"Day02 living_room menus: {len(day02_menus)}")
        
        for menu in day02_menus:
            print(f"  - {menu.label_name}")
            
        # Check all day02 menus
        all_day02_menus = [m for m in menus if 'day02' in str(m.label_name)]
        print(f"\nAll day02 menus ({len(all_day02_menus)}):")
        for menu in all_day02_menus:
            print(f"  - {menu.label_name}")
        
        # 3. Check flow graph detection
        print("\n3. CHECKING FLOW GRAPH FOR REFERENCES:")
        print("-" * 50)
        
        from renpy_data_adapter import RenpyFlowDataAdapter
        adapter = RenpyFlowDataAdapter(use_hybrid=True)
        visualization_data = adapter.analyze_project(project_path)
        flow_graph = adapter._last_flow_graph
        
        # Look for any flows that reference day02_living_room_conversation
        flows_to_target = []
        flows_from_target = []
        
        for label_name, label_node in flow_graph.items():
            for flow in label_node.flows:
                if flow.target == 'day02_living_room_conversation':
                    flows_to_target.append(f"{label_name} → {flow.target}")
                if label_name == 'day02_living_room_conversation':
                    flows_from_target.append(f"{label_name} → {flow.target}")
        
        print(f"Flows TO day02_living_room_conversation: {len(flows_to_target)}")
        for flow in flows_to_target:
            print(f"  - {flow}")
        
        print(f"Flows FROM day02_living_room_conversation: {len(flows_from_target)}")
        for flow in flows_from_target:
            print(f"  - {flow}")
        
        # 4. Check if it exists as a label (non-menu)
        print(f"\n4. LABEL EXISTENCE CHECK:")
        print("-" * 50)
        
        if 'day02_living_room_conversation' in flow_graph:
            label_node = flow_graph['day02_living_room_conversation']
            print(f"  ✅ Exists as label in flow graph")
            print(f"  - Total flows: {len(label_node.flows)}")
            print(f"  - Properties: {label_node.properties}")
        else:
            print(f"  ❌ Does NOT exist in flow graph")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_specific_label_menu() 