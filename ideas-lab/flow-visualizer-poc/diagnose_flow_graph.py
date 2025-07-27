#!/usr/bin/env python3
"""
Diagnostic script to check flow graph menu detection for Last Call game.
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Add renpy-source-api to path
app_dir = current_dir.parent.parent / "app"
sys.path.insert(0, str(app_dir / "renpy-source-api"))

# Import the core components
from sdk_integration import HybridRenpyParser

def diagnose_flow_graph():
    """Diagnose flow graph for Last Call game."""
    
    print("🔍 DIAGNOSING FLOW GRAPH - LAST CALL")
    print("=" * 60)
    
    # Load Last Call game
    game_path = "T:/AG/LastCall-0.4-pc/game"
    print(f"📂 Loading game: {game_path}")
    
    try:
        parser = HybridRenpyParser()
        flow_graph = parser.build_flow_graph(game_path)
        
        print(f"✅ Flow graph built successfully")
        print(f"📊 Total labels in flow graph: {len(flow_graph)}")
        
        # Check ch1mckellycar specifically
        if 'ch1mckellycar' in flow_graph:
            label_node = flow_graph['ch1mckellycar']
            print(f"\n🎯 CH1MCKELLYCAR ANALYSIS:")
            print(f"  Has menu: {label_node.has_menu}")
            if hasattr(label_node, 'menu_nodes'):
                print(f"  Menu nodes: {len(label_node.menu_nodes)}")
                for i, menu in enumerate(label_node.menu_nodes):
                    print(f"    Menu {i}: {menu.name}")
                    print(f"      Prompt: {menu.prompt}")
                    print(f"      Choices: {len(menu.choices)}")
                    for j, choice in enumerate(menu.choices):
                        print(f"        Choice {j}: {choice.text} → {choice.destination}")
            else:
                print(f"  No menu_nodes attribute")
        else:
            print(f"❌ ch1mckellycar not found in flow graph")
            
        # List all labels with menus
        labels_with_menus = [name for name, label in flow_graph.items() if label.has_menu]
        print(f"\n📋 LABELS WITH MENUS ({len(labels_with_menus)}):")
        for label_name in labels_with_menus[:10]:  # Show first 10
            label_node = flow_graph[label_name]
            menu_count = len(label_node.menu_nodes) if hasattr(label_node, 'menu_nodes') else 0
            print(f"  {label_name}: {menu_count} menus")
            
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose_flow_graph() 