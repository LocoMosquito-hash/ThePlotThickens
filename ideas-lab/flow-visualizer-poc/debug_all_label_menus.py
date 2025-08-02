#!/usr/bin/env python3
"""
Debug All Label Menus
=====================

Check which label menus are being detected and processed correctly.
"""

import sys
import os

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_all_label_menus():
    """Check all label menus in the game."""
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    if not os.path.exists(project_path):
        print(f"ERROR: Project path not found: {project_path}")
        return
    
    print("Debugging ALL label menus...")
    print("=" * 60)
    
    try:
        # Get menu analysis first
        print("\n1. MENU ANALYSIS - All detected label menus:")
        print("-" * 50)
        
        # Add the control_flow path
        control_flow_path = os.path.join(project_root, "app", "renpy-source-api", "control_flow")
        sys.path.insert(0, control_flow_path)
        
        from analyze_vn_menus import MenuAnalyzer
        analyzer = MenuAnalyzer()
        menu_analysis = analyzer.analyze_vn_menus(project_path)
        menus = menu_analysis.get('menu_structures', [])
        
        label_menus = [m for m in menus if m.label_name]
        print(f"Total label menus detected: {len(label_menus)}")
        
        for i, menu in enumerate(label_menus[:10]):  # Show first 10
            print(f"  {i+1}. {menu.label_name}")
            
        # Get flow graph
        print("\n2. FLOW GRAPH - Which label menus are in flow graph:")
        print("-" * 50)
        from renpy_data_adapter import RenpyFlowDataAdapter
        adapter = RenpyFlowDataAdapter(use_hybrid=True)
        visualization_data = adapter.analyze_project(project_path)
        flow_graph = adapter._last_flow_graph
        
        in_flow_graph = []
        missing_from_flow_graph = []
        
        for menu in label_menus[:10]:  # Check first 10
            if menu.label_name in flow_graph:
                in_flow_graph.append(menu.label_name)
            else:
                missing_from_flow_graph.append(menu.label_name)
        
        print(f"In flow graph: {len(in_flow_graph)}")
        for name in in_flow_graph:
            print(f"  ✅ {name}")
            
        print(f"Missing from flow graph: {len(missing_from_flow_graph)}")
        for name in missing_from_flow_graph:
            print(f"  ❌ {name}")
        
        # Check visualization data
        print("\n3. VISUALIZATION DATA - How label menus appear:")
        print("-" * 50)
        nodes = visualization_data.nodes
        
        label_menu_nodes = [n for n in nodes if 'day02' in n.node_id and ('living_room' in n.node_id or 'p_room_choices' in n.node_id)]
        
        print("Nodes containing 'day02' and relevant patterns:")
        for node in label_menu_nodes:
            # Handle different node types and color attributes
            if hasattr(node, 'color'):
                color_val = node.color
            elif hasattr(node, 'style') and hasattr(node.style, 'fill'):
                color_val = node.style.fill
            else:
                color_val = "unknown"
            
            color = "🟠" if "#FFA500" in str(color_val) else "🔵" if "#ADD8E6" in str(color_val) else "🟡" if "#FFFF00" in str(color_val) else "⚫"
            print(f"  {color} {node.node_id} (type: {node.node_type}, color: {color_val})")
        
        # Check specific problematic nodes
        print("\n4. SPECIFIC CHECKS:")
        print("-" * 50)
        
        target_names = ['day02_p_room_choices', 'day02_living_room_conversation']
        for target in target_names:
            print(f"\nChecking {target}:")
            
            # In menu analysis?
            found_in_menus = any(m.label_name == target for m in label_menus)
            print(f"  Found in menu analysis: {found_in_menus}")
            
            # In flow graph?
            in_fg = target in flow_graph if flow_graph else False
            print(f"  In flow graph: {in_fg}")
            
            # In visualization nodes?
            viz_nodes = [n for n in nodes if target in n.node_id]
            print(f"  Visualization nodes: {len(viz_nodes)}")
            for vn in viz_nodes:
                # Safe color access
                if hasattr(vn, 'color'):
                    color_val = vn.color
                elif hasattr(vn, 'style') and hasattr(vn.style, 'fill'):
                    color_val = vn.style.fill
                else:
                    color_val = "unknown"
                print(f"    - {vn.node_id} (type: {vn.node_type}, color: {color_val})")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_all_label_menus() 