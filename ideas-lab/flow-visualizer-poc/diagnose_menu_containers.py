#!/usr/bin/env python3
"""
Diagnostic script to analyze menu container creation in Last Call game.

This script will help us understand why menu containers are disappearing
in simpler games after our Savior fix.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import networkx as nx

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Add renpy-source-api to path
app_dir = current_dir.parent.parent / "app"
sys.path.insert(0, str(app_dir / "renpy-source-api"))

# Import the data adapter
from renpy_data_adapter import RenpyFlowDataAdapter

def diagnose_last_call_menus():
    """Diagnose menu container creation for Last Call game."""
    
    print("🔍 DIAGNOSING MENU CONTAINER CREATION - LAST CALL")
    print("=" * 60)
    
    # Load Last Call game
    game_path = "T:/AG/LastCall-0.4-pc/game"
    print(f"📂 Loading game: {game_path}")
    
    try:
        adapter = RenpyFlowDataAdapter()
        viz_data = adapter.analyze_project(game_path, use_sdk=True)
        
        if not viz_data:
            print("❌ Failed to analyze project")
            return
            
        print(f"✅ Project analyzed successfully")
        
        # Test adapter processing
        print(f"\n🔧 ANALYZING VISUALIZATION DATA:")
        print("-" * 40)
        
        print(f"📦 Visualization data created:")
        print(f"  Nodes: {len(viz_data.nodes)}")
        print(f"  Connections: {len(viz_data.connections)}")
        
        # Analyze nodes for menu containers
        nodes = viz_data.nodes
        menu_containers = [n for n in nodes if n.node_type == 'menu_container']
        choice_nodes = [n for n in nodes if n.node_type == 'choice']
        label_nodes = [n for n in nodes if n.node_type == 'label']
        
        print(f"\n📊 NODE TYPE ANALYSIS:")
        print(f"  Menu containers: {len(menu_containers)}")
        print(f"  Choice nodes: {len(choice_nodes)}")
        print(f"  Label nodes: {len(label_nodes)}")
        
        # Find ch1mckellycar related nodes
        target_nodes = [n for n in nodes if 'ch1mckellycar' in n.node_id]
        print(f"\n🎯 CH1MCKELLYCAR RELATED NODES:")
        for node in target_nodes:
            print(f"  {node.node_type}: {node.node_id}")
            
        # Check for expected menu container
        expected_container = f"ch1mckellycar_menu_0"
        container_exists = any(n.node_id == expected_container for n in nodes)
        print(f"\n🔍 Expected container '{expected_container}': {'✅ EXISTS' if container_exists else '❌ MISSING'}")
        
        # Analyze connections
        connections = viz_data.connections
        ch1_connections = [c for c in connections if 'ch1mckellycar' in c.source or 'ch1mckellycar' in c.target]
        
        print(f"\n🔗 CH1MCKELLYCAR CONNECTIONS:")
        for conn in ch1_connections:
            print(f"  {conn.source} → {conn.target}")
            
        # Check for direct jumps (problematic)
        direct_jumps = [c for c in connections 
                       if c.source == 'ch1mckellycar' 
                       and c.target in ['turnkellydown', 'acceptedkjproposal']]
                       
        if direct_jumps:
            print(f"\n⚠️  FOUND PROBLEMATIC DIRECT JUMPS:")
            for jump in direct_jumps:
                print(f"  {jump.source} → {jump.target}")
        else:
            print(f"\n✅ No problematic direct jumps found")
            
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose_last_call_menus() 