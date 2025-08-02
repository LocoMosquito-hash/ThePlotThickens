#!/usr/bin/env python3
"""
Debug Target Validation
=======================

Check why day02_p_room_choices isn't recognized as a valid flow target.
"""

import sys
import os

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_target_validation():
    """Check flow target validation."""
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    if not os.path.exists(project_path):
        print(f"ERROR: Project path not found: {project_path}")
        return
    
    print("Debugging target validation...")
    print("=" * 50)
    
    try:
        from renpy_data_adapter import RenpyFlowDataAdapter
        
        # Create adapter
        adapter = RenpyFlowDataAdapter(use_hybrid=True)
        
        # Analyze project to get visualization data (which triggers flow graph creation)
        print("Analyzing project...")
        visualization_data = adapter.analyze_project(project_path)
        
        # Access the stored flow graph
        flow_graph = adapter._last_flow_graph
        
        if not flow_graph:
            print("ERROR: Flow graph not found")
            return
            
        print(f"Flow graph has {len(flow_graph)} labels")
        
        # Check if day02_p_room_choices exists in flow graph
        target_label = 'day02_p_room_choices'
        print(f"\nChecking target '{target_label}':")
        print(f"   Exists in flow_graph: {target_label in flow_graph}")
        
        if target_label in flow_graph:
            label_node = flow_graph[target_label]
            print(f"   Type: {type(label_node)}")
            print(f"   Has menu_nodes: {hasattr(label_node, 'menu_nodes')}")
            if hasattr(label_node, 'menu_nodes'):
                print(f"   Menu nodes: {len(label_node.menu_nodes)}")
        
        # Check what labels contain day02_p_room_choices
        print(f"\nLabels containing '{target_label}' as substring:")
        matching_labels = [label for label in flow_graph.keys() if target_label in label]
        for label in matching_labels:
            print(f"   {label}")
        
        # Check day02_l_conversation flows
        source_label = 'day02_l_conversation'
        print(f"\nChecking flows FROM '{source_label}':")
        if source_label in flow_graph:
            source_node = flow_graph[source_label]
            if hasattr(source_node, 'outgoing_flows'):
                target_flows = [f for f in source_node.outgoing_flows if f.target_label == target_label]
                print(f"   Flows to {target_label}: {len(target_flows)}")
                for flow in target_flows:
                    print(f"     Flow: {flow.source_label} -> {flow.target_label} (Type: {flow.flow_type})")
                    print(f"     Context: {getattr(flow, 'context', 'None')}")
            else:
                print(f"   No outgoing_flows attribute")
        else:
            print(f"   {source_label} not found in flow graph")
        
        # Check menu analysis directly
        print(f"\nChecking menu analysis...")
        try:
            from control_flow.analyze_vn_menus import MenuAnalyzer
            analyzer = MenuAnalyzer()
            menu_analysis = analyzer.analyze_vn_menus(project_path)
            
            target_menus = [
                menu for menu in menu_analysis.get('menu_structures', [])
                if menu.label_name == target_label
            ]
            print(f"   Label menus named '{target_label}': {len(target_menus)}")
            for menu in target_menus:
                print(f"     File: {menu.file_path}")
                print(f"     Line: {menu.line_number}")
                print(f"     Label: {menu.label_name}")
        except Exception as e:
            print(f"   Menu analysis error: {e}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_target_validation() 