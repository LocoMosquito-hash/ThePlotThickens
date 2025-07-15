#!/usr/bin/env python3
"""
Debug Menu Choice Connections
============================

Focused diagnostic to understand why menu choice connections aren't being created.
ROOT CAUSE IDENTIFIED: Labels have menus (112) but menu_choice connections = 0
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core import RenpyProject
import json

def analyze_menu_connections(project_path: str):
    """Analyze why menu choice connections aren't being created"""
    
    print("=== DEBUGGING MENU CHOICE CONNECTIONS ===")
    print("=" * 50)
    
    # Load project
    print("1. Loading project...")
    project = RenpyProject(project_path)
    project.analyze()
    
    # Get flow data
    flow_data = project.get_flow_graph()
    print(f"   Flow data: {len(flow_data)} labels")
    
    # Focus on labels with menus
    print("2. Analyzing labels with menus...")
    menu_labels = []
    for label_name, label_data in flow_data.items():
        if label_data.get('has_menu', False):
            menu_labels.append((label_name, label_data))
    
    print(f"   Found {len(menu_labels)} labels with menus")
    
    # Examine a few menu labels in detail
    print("3. Detailed analysis of menu labels...")
    for i, (label_name, label_data) in enumerate(menu_labels[:5]):
        print(f"\n   Label {i+1}: {label_name}")
        print(f"     has_menu: {label_data.get('has_menu')}")
        print(f"     outgoing_flows: {len(label_data.get('outgoing_flows', []))}")
        
        # Check each outgoing flow
        flows = label_data.get('outgoing_flows', [])
        for j, flow in enumerate(flows):
            flow_type = flow.get('flow_type', 'UNKNOWN')
            target = flow.get('target_label', 'UNKNOWN')
            print(f"       Flow {j+1}: type='{flow_type}' → {target}")
            
            # If this should be a menu choice, why isn't it marked as such?
            if flow_type != 'menu_choice':
                print(f"         ❌ Expected menu_choice, got '{flow_type}'")
        
        # Check if there are menu structures
        menu_structure = label_data.get('menu_structure')
        if menu_structure:
            print(f"     menu_structure: {len(menu_structure)} choices")
            for k, choice in enumerate(menu_structure[:3]):
                choice_text = choice.get('text', 'NO_TEXT')
                choice_target = choice.get('target', 'NO_TARGET')
                print(f"       Choice {k+1}: '{choice_text[:30]}' → {choice_target}")
        else:
            print(f"     ❌ No menu_structure found!")
    
    # Focus on our test case
    print(f"\n4. Deep dive on ch4ashbagdone...")
    test_label = 'ch4ashbagdone'
    if test_label in flow_data:
        test_data = flow_data[test_label]
        print(f"   has_menu: {test_data.get('has_menu')}")
        print(f"   Raw data keys: {list(test_data.keys())}")
        
        # Check all the data
        for key, value in test_data.items():
            if key == 'outgoing_flows':
                print(f"   {key}: {len(value)} flows")
                for i, flow in enumerate(value):
                    print(f"     Flow {i+1}: {flow}")
            elif key == 'menu_structure':
                print(f"   {key}: {len(value) if value else 'None'} choices")
                if value:
                    for i, choice in enumerate(value):
                        print(f"     Choice {i+1}: {choice}")
            else:
                print(f"   {key}: {value}")
    else:
        print(f"   ❌ {test_label} not found!")
    
    # Check if the issue is in the flow generation
    print(f"\n5. Checking connection type distribution...")
    connection_types = {}
    total_connections = 0
    
    for label_name, label_data in flow_data.items():
        flows = label_data.get('outgoing_flows', [])
        total_connections += len(flows)
        
        for flow in flows:
            flow_type = flow.get('flow_type', 'UNKNOWN')
            connection_types[flow_type] = connection_types.get(flow_type, 0) + 1
    
    print(f"   Total connections: {total_connections}")
    print(f"   Connection types:")
    for conn_type, count in sorted(connection_types.items()):
        print(f"     {conn_type}: {count}")
    
    # The critical question: Are menu choices being processed at all?
    print(f"\n6. CRITICAL ANALYSIS:")
    if connection_types.get('menu_choice', 0) == 0:
        print("   ❌ NO menu_choice connections found!")
        print("   🔍 This means menu choices aren't being processed as separate connections")
        print("   💡 The issue is likely in the flow analysis phase")
    else:
        print(f"   ✅ Found {connection_types.get('menu_choice', 0)} menu_choice connections")

def main():
    project_path = r"T:\AG\MySisterMyRoommateV1.69-pc\game"
    
    try:
        analyze_menu_connections(project_path)
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main() 