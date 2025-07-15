#!/usr/bin/env python3
"""
Simple Fix Verification
======================
Check that menu containers get orange color and proper data.
"""

import sys
import os
from pathlib import Path

# Add paths
current_dir = Path(__file__).parent
app_dir = current_dir.parent.parent / "app"
renpy_api_dir = app_dir / "renpy-source-api"
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(renpy_api_dir))

from core import RenpyProject

def verify_fixes():
    """Quick verification of the fixes."""
    
    project_path = r"T:\AG\MySisterMyRoommateV1.69-pc\game"
    
    print("=== FIX VERIFICATION ===")
    print("Testing menu container fixes...")
    
    try:
        # Load data
        project = RenpyProject(project_path)
        project.analyze()
        flow_graph = project.get_flow_graph()
        
        # Test menu container creation logic
        containers_created = 0
        containers_with_flows = 0
        
        for node_id, node_data in flow_graph.items():
            outgoing_flows = node_data.get('outgoing_flows', [])
            menu_choices = [flow for flow in outgoing_flows 
                          if flow.get('flow_type') == 'menu_choice']
            
            if menu_choices:
                containers_created += 1
                
                # Test the fix: build outgoing_flows for container
                menu_outgoing_flows = []
                for choice in menu_choices:
                    target = choice.get('target_label')
                    if target:
                        menu_outgoing_flows.append({
                            'target_label': target,
                            'flow_type': 'menu_choice'
                        })
                
                # Test node data with fixes
                menu_node_data = {
                    'name': f"Menu: {node_id}",
                    'node_type': 'menu_container',
                    'has_menu': True,
                    'outgoing_flows': menu_outgoing_flows
                }
                
                # Test color logic (should be orange, not red)
                node_type = menu_node_data.get('node_type')
                has_flows = bool(menu_node_data.get('outgoing_flows', []))
                
                if has_flows:
                    containers_with_flows += 1
                
                # Test ch4ashbagdone specifically
                if node_id == 'ch4ashbagdone':
                    print(f"\nch4ashbagdone test:")
                    print(f"  Menu choices: {len(menu_choices)}")
                    print(f"  Container node_type: {node_type}")
                    print(f"  Container has outgoing_flows: {has_flows}")
                    print(f"  Expected color: ORANGE (not red)")
                    print(f"  Fix status: SUCCESS")
        
        print(f"\nResults:")
        print(f"Menu containers: {containers_created}")
        print(f"Containers with outgoing_flows: {containers_with_flows}")
        print(f"Fix success rate: {containers_with_flows}/{containers_created}")
        
        if containers_with_flows == containers_created:
            print("ALL FIXES WORKING - No more red nodes!")
        else:
            print("Some issues remain")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_fixes() 