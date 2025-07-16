#!/usr/bin/env python3
"""
Temporary investigation script to analyze menu choice filtering issue
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path('../../app').resolve()))
sys.path.insert(0, str(Path('../../app/renpy-source-api').resolve()))

from core import RenpyProject

def investigate_savior_menus():
    # Load Savior VN data
    project_path = r'T:\AG\Savior-0.16c-pc\game'
    project = RenpyProject(project_path)
    project.analyze()
    
    flow_graph = project.get_flow_graph()
    
    print('=== INVESTIGATING SELF-LOOP PATTERNS ===')
    print()
    
    # Check the problematic menus
    target_menus = ['dinnertalk', 'olivia']
    
    for label_id in target_menus:
        if label_id in flow_graph:
            node_data = flow_graph[label_id]
            outgoing_flows = node_data.get('outgoing_flows', [])
            menu_choices = [flow for flow in outgoing_flows if flow.get('flow_type') == 'menu_choice']
            
            print(f'LABEL: {label_id} - {len(menu_choices)} menu choices detected')
            
            self_loops = 0
            non_self_loops = 0
            
            # Check each choice destination
            for i, choice in enumerate(menu_choices):
                source = choice.get('source_label')
                target = choice.get('target_label') 
                context = choice.get('context', 'No context')
                print(f'  Choice {i+1}: "{context}" -> {source} to {target}')
                
                # Check if it's a self-loop
                if source == target:
                    print(f'    ⚠️  SELF-LOOP: {source} loops back to itself')
                    self_loops += 1
                else:
                    print(f'    ✅ EXTERNAL: {source} -> {target}')
                    non_self_loops += 1
            
            print(f'  Summary: {self_loops} self-loops, {non_self_loops} external targets')
            print()

if __name__ == "__main__":
    investigate_savior_menus() 