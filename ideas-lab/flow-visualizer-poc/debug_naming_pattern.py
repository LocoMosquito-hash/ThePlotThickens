#!/usr/bin/env python3
"""
Debug Naming Pattern
====================

Check if the expected parent choice buttons exist for orphan containers.
"""

import sys
import os

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_naming_pattern():
    """Check specific examples of orphan containers and their expected parents."""
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    if not os.path.exists(project_path):
        print(f"ERROR: Project path not found: {project_path}")
        return
    
    print("🔍 DEBUGGING NAMING PATTERN")
    print("=" * 50)
    
    try:
        # Add the control_flow path
        control_flow_path = os.path.join(project_root, "app", "renpy-source-api", "control_flow")
        sys.path.insert(0, control_flow_path)
        
        from renpy_data_adapter import RenpyFlowDataAdapter
        
        # Load the project
        print("1. Loading project data...")
        adapter = RenpyFlowDataAdapter()
        result = adapter.analyze_project(project_path)
        
        nodes = result.nodes
        
        # Get orphan containers and choice buttons
        orphan_containers = []
        choice_buttons = []
        
        for node in nodes:
            if node.node_type == 'menu_container':
                # Check if it's an orphan (simplified check)
                if '_nested_menu_' in node.node_id and node.node_id.endswith('_menu_1'):
                    orphan_containers.append(node)
            elif node.node_type == 'choice_button':
                choice_buttons.append(node)
        
        print(f"Found {len(orphan_containers)} potential orphan containers")
        print(f"Found {len(choice_buttons)} choice buttons")
        
        # Test first 5 orphans
        print(f"\n2. TESTING FIRST 5 ORPHANS:")
        print("-" * 40)
        
        choice_button_ids = {cb.node_id for cb in choice_buttons}
        
        for i, orphan in enumerate(orphan_containers[:5]):
            orphan_id = orphan.node_id
            print(f"\n{i+1}. ORPHAN: {orphan_id}")
            
            # Strategy 1: Remove _menu_1 suffix
            if orphan_id.endswith('_menu_1'):
                expected_parent = orphan_id[:-7]  # Remove "_menu_1"
                exists = expected_parent in choice_button_ids
                print(f"   Expected parent: {expected_parent}")
                print(f"   Parent exists: {'✅' if exists else '❌'}")
                
                if not exists:
                    # Look for similar choice buttons
                    similar = [cb for cb in choice_button_ids if expected_parent in cb or cb in expected_parent]
                    print(f"   Similar choices: {similar[:3]}")
        
        print(f"\n3. SAMPLE CHOICE BUTTON NAMES:")
        print("-" * 40)
        for i, choice in enumerate(choice_buttons[:10]):
            print(f"   {i+1}. {choice.node_id}")
        
        print(f"\n4. ANALYSIS - Looking for '_nested_' pattern in choice buttons:")
        print("-" * 60)
        nested_choices = [cb for cb in choice_buttons if '_nested_' in cb.node_id]
        print(f"Found {len(nested_choices)} choice buttons with '_nested_' pattern")
        
        for i, choice in enumerate(nested_choices[:10]):
            print(f"   {i+1}. {choice.node_id}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_naming_pattern() 