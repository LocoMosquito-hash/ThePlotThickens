#!/usr/bin/env python3
"""
Debug script to understand the actual flow_graph structure.

This will help us fix the AuthoritativeHierarchy implementation.
"""

import sys
from pathlib import Path
import json

# Add renpy-source-api to path
current_dir = Path(__file__).parent
app_dir = current_dir.parent.parent / "app"
sys.path.insert(0, str(app_dir / "renpy-source-api"))

from renpy_data_adapter import RenpyFlowDataAdapter

def debug_flow_graph_structure():
    """Debug the actual flow_graph structure from Haley's Story."""
    
    game_path = "F:\\Bin\\Games\\Haley-1.1-alt-pc\\game"
    
    print("🔍 Debugging Flow Graph Structure")
    print("=" * 50)
    
    # Initialize adapter
    adapter = RenpyFlowDataAdapter(use_hybrid=True)
    
    # Get the flow graph directly without building hierarchy
    flow_graph = adapter.parser.build_flow_graph(game_path)
    
    print(f"📊 Flow graph type: {type(flow_graph)}")
    print(f"📊 Flow graph keys: {list(flow_graph.keys()) if isinstance(flow_graph, dict) else 'Not a dict'}")
    
    # Look specifically at ep2cont5
    if 'labels' in flow_graph:
        ep2cont5_data = flow_graph['labels'].get('ep2cont5')
        if ep2cont5_data:
            print(f"\n🎯 ep2cont5 data:")
            print(f"   Type: {type(ep2cont5_data)}")
            print(f"   Attributes: {dir(ep2cont5_data)}")
            
            if hasattr(ep2cont5_data, 'menu_nodes'):
                print(f"   menu_nodes: {getattr(ep2cont5_data, 'menu_nodes', 'None')}")
                print(f"   menu_nodes type: {type(getattr(ep2cont5_data, 'menu_nodes', None))}")
                
                menu_nodes = getattr(ep2cont5_data, 'menu_nodes', [])
                if menu_nodes:
                    print(f"   Number of menu_nodes: {len(menu_nodes)}")
                    for i, menu in enumerate(menu_nodes):
                        print(f"     Menu {i}: {type(menu)}")
                        print(f"       Attributes: {dir(menu)}")
                        if hasattr(menu, 'choices'):
                            choices = getattr(menu, 'choices', [])
                            print(f"       Choices: {len(choices)}")
                            for j, choice in enumerate(choices):
                                print(f"         Choice {j}: {type(choice)}")
                                print(f"           Text: {getattr(choice, 'text', 'No text')}")
                                print(f"           Has nested: {hasattr(choice, 'nested_menu_structures')}")
                                if hasattr(choice, 'nested_menu_structures'):
                                    nested = getattr(choice, 'nested_menu_structures', [])
                                    print(f"           Nested menus: {len(nested)}")
    else:
        print("⚠️ No 'labels' key in flow_graph")
        print(f"Available keys: {list(flow_graph.keys())}")

if __name__ == "__main__":
    debug_flow_graph_structure()