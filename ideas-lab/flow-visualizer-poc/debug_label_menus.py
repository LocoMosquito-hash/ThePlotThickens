#!/usr/bin/env python3
"""
Debug Script for Label Menu Analysis
===================================

This script examines how label menus are detected and processed,
specifically looking for cases like "menu day02_living_room_conversation:"
to understand the current naming and identification issues.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from renpy_data_adapter import RenpyFlowDataAdapter

def analyze_label_menus():
    """Analyze how label menus are currently being processed."""
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    print("🔍 LABEL MENU ANALYSIS")
    print("=" * 50)
    print(f"Project: {project_path}")
    print()
    
    # Get the flow data
    adapter = RenpyFlowDataAdapter(use_hybrid=True)
    
    # Hook into the parser to examine menu structures
    original_analyze = adapter.parser.analyze_project
    
    def logged_analyze_project(path):
        result = original_analyze(path)
        
        # Look at the parsed menu structures
        print("📋 EXAMINING MENU STRUCTURES:")
        print("-" * 30)
        
        day02_menus = []
        label_menus = []
        regular_menus = []
        
        if hasattr(adapter.parser, 'find_all_menus'):
            all_menus = adapter.parser.find_all_menus(path)
            
            for menu in all_menus:
                # Focus on day02 related menus
                if 'day02' in str(menu.label_context) or 'day02' in str(menu.label_name):
                    day02_menus.append(menu)
                
                # Categorize menus
                if menu.label_name:  # This is a label menu
                    label_menus.append(menu)
                else:  # Regular menu
                    regular_menus.append(menu)
        
        print(f"Total menus found: {len(all_menus) if 'all_menus' in locals() else 'Unknown'}")
        print(f"Label menus: {len(label_menus)}")
        print(f"Regular menus: {len(regular_menus)}")
        print(f"Day02 related menus: {len(day02_menus)}")
        print()
        
        # Examine day02 menus in detail
        print("🎯 DAY02 MENU DETAILS:")
        print("-" * 20)
        for i, menu in enumerate(day02_menus):
            print(f"Menu {i+1}:")
            print(f"  - Label Name: {menu.label_name}")
            print(f"  - Label Context: {menu.label_context}")
            print(f"  - File: {os.path.basename(menu.file_path) if menu.file_path else 'Unknown'}")
            print(f"  - Line: {menu.line_number}")
            print(f"  - Prompt: {menu.prompt}")
            print(f"  - Choices: {len(menu.choices)}")
            print(f"  - Nesting Level: {menu.nesting_level}")
            
            # Look for the specific menu we're interested in
            if menu.label_name == "day02_living_room_conversation":
                print(f"  🎯 FOUND TARGET MENU: day02_living_room_conversation")
                print(f"     - Choices:")
                for j, choice in enumerate(menu.choices):
                    print(f"       {j+1}. '{choice.text}'")
                    print(f"          Destination: {choice.destination}")
                    print(f"          Condition: {choice.condition}")
            
            print()
        
        # Look for label menus specifically
        print("📝 LABEL MENU EXAMPLES:")
        print("-" * 25)
        for i, menu in enumerate(label_menus[:10]):  # Show first 10
            print(f"  {i+1}. Label: '{menu.label_name}' in context '{menu.label_context}'")
        print()
        
        return result
    
    adapter.parser.analyze_project = logged_analyze_project
    
    # Hook into the visualization creation to see how menus are named
    original_create_containers = adapter._create_menu_containers
    
    def logged_create_containers(flow_graph):
        print("🏗️ MENU CONTAINER CREATION:")
        print("-" * 30)
        
        container_nodes, choice_connections = original_create_containers(flow_graph)
        
        # Look for day02 related containers
        day02_containers = [node for node in container_nodes 
                          if 'day02' in node.node_id and node.node_type == 'menu_container']
        
        print(f"Day02 menu containers created: {len(day02_containers)}")
        for container in day02_containers:
            print(f"  - ID: {container.node_id}")
            print(f"  - Display: {container.display_name}")
            print(f"  - Color: {container.color_hint}")
            print(f"  - Type: {container.node_type}")
            print(f"  - Metadata: {container.metadata}")
            print()
        
        return container_nodes, choice_connections
    
    adapter._create_menu_containers = logged_create_containers
    
    # Now run the analysis
    try:
        visualization_data = adapter.analyze_project(project_path)
        
        print("✅ ANALYSIS COMPLETE")
        print(f"Total nodes: {len(visualization_data.nodes)}")
        print(f"Total connections: {len(visualization_data.connections)}")
        
        # Look for nodes that might be our target
        living_room_nodes = [node for node in visualization_data.nodes 
                           if 'living_room' in node.node_id.lower()]
        
        print(f"\nNodes containing 'living_room': {len(living_room_nodes)}")
        for node in living_room_nodes:
            print(f"  - {node.node_id} ({node.node_type}) - {node.display_name}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    analyze_label_menus() 