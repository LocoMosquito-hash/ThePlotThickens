#!/usr/bin/env python3
"""
Debug Day02 Actual Structure
============================

Check the actual structure of day02_p_room_choices and its choices.
"""

import sys
import os

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_day02_structure():
    """Check actual day02_p_room_choices structure."""
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    if not os.path.exists(project_path):
        print(f"ERROR: Project path not found: {project_path}")
        return
    
    print("Debugging day02_p_room_choices actual structure...")
    print("=" * 60)
    
    try:
        # Add the control_flow path
        control_flow_path = os.path.join(project_root, "app", "renpy-source-api", "control_flow")
        sys.path.insert(0, control_flow_path)
        
        from analyze_vn_menus import MenuAnalyzer
        
        # 1. Get the actual menu structure for day02_p_room_choices
        print("1. DAY02_P_ROOM_CHOICES MENU STRUCTURE:")
        print("-" * 50)
        
        analyzer = MenuAnalyzer()
        menu_analysis = analyzer.analyze_vn_menus(project_path)
        menus = menu_analysis.get('menu_structures', [])
        
        day02_menu = None
        for menu in menus:
            if menu.label_name == 'day02_p_room_choices':
                day02_menu = menu
                break
        
        if day02_menu:
            print(f"Found day02_p_room_choices menu:")
            print(f"  - Label: {day02_menu.label_name}")
            print(f"  - Choices: {len(day02_menu.choices)}")
            
            for i, choice in enumerate(day02_menu.choices):
                print(f"\n  Choice {i}: '{choice.text}'")
                
                # Check all attributes of choice
                print(f"    - Attributes: {[attr for attr in dir(choice) if not attr.startswith('_')]}")
                
                # Try to get target info
                if hasattr(choice, 'target'):
                    print(f"    - Target: {choice.target}")
                if hasattr(choice, 'action'):
                    print(f"    - Action: {choice.action}")
                if hasattr(choice, 'jump_to'):
                    print(f"    - Jump to: {choice.jump_to}")
                
                # Check if this choice has nested menus
                if hasattr(choice, 'nested_menus') and choice.nested_menus:
                    print(f"    - Has nested menus: {len(choice.nested_menus)}")
                    for j, nested in enumerate(choice.nested_menus):
                        print(f"      Nested {j}: {nested.label_name if hasattr(nested, 'label_name') else 'unnamed'}")
        else:
            print("❌ day02_p_room_choices not found in menu analysis!")
        
        # 2. Check what labels actually exist starting with day02
        print(f"\n2. ALL DAY02 LABELS IN SOURCE:")
        print("-" * 50)
        
        import pathlib
        game_dir = pathlib.Path(project_path)
        rpy_files = list(game_dir.rglob('*.rpy'))
        
        day02_labels = set()
        for rpy_file in rpy_files:
            try:
                with open(rpy_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line.startswith('label day02') and ':' in line:
                            label_name = line.split(':')[0].replace('label ', '').strip()
                            day02_labels.add(label_name)
            except Exception as e:
                pass
        
        print(f"Found {len(day02_labels)} day02 labels:")
        for label in sorted(day02_labels):
            print(f"  - {label}")
        
        # 3. Check visualization data for day02 patterns
        print(f"\n3. VISUALIZATION NODES - DAY02 PATTERNS:")
        print("-" * 50)
        
        from renpy_data_adapter import RenpyFlowDataAdapter
        adapter = RenpyFlowDataAdapter(use_hybrid=True)
        visualization_data = adapter.analyze_project(project_path)
        
        day02_nodes = [n for n in visualization_data.nodes if 'day02' in n.node_id]
        
        # Group by type
        by_type = {}
        for node in day02_nodes:
            if node.node_type not in by_type:
                by_type[node.node_type] = []
            by_type[node.node_type].append(node.node_id)
        
        for node_type, nodes in by_type.items():
            print(f"\n{node_type} ({len(nodes)}):")
            for node_id in sorted(nodes)[:5]:  # Show first 5
                print(f"  - {node_id}")
            if len(nodes) > 5:
                print(f"  ... and {len(nodes) - 5} more")
        
        # 4. Check specific choice connections
        print(f"\n4. CHOICE CONNECTIONS:")
        print("-" * 50)
        
        connections = visualization_data.connections
        choice_connections = [c for c in connections if 'day02_p_room_choices_choice' in c.source]
        
        print(f"Connections from day02_p_room_choices choices: {len(choice_connections)}")
        for conn in choice_connections[:10]:  # Show first 10
            print(f"  {conn.source} → {conn.target} ({conn.connection_type})")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_day02_structure() 