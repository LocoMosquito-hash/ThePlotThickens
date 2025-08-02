#!/usr/bin/env python3
"""
Debug Remaining Orphans
=======================

Analyze the remaining 182 orphan containers to understand what patterns
they have and why they weren't fixed.
"""

import sys
import os

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_remaining_orphans():
    """Analyze remaining orphan containers."""
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    if not os.path.exists(project_path):
        print(f"ERROR: Project path not found: {project_path}")
        return
    
    print("Debugging remaining orphan containers...")
    print("=" * 60)
    
    try:
        from renpy_data_adapter import RenpyFlowDataAdapter
        
        adapter = RenpyFlowDataAdapter()
        result = adapter.analyze_project(project_path)
        
        if not result:
            print("ERROR: Could not analyze project")
            return
        
        # Find orphan containers
        container_targets = set()
        for conn in result.connections:
            if hasattr(conn, 'target_node_id'):
                container_targets.add(conn.target_node_id)
        
        orphan_containers = []
        for node in result.nodes:
            if (node.node_type == 'menu_container' and 
                node.node_id not in container_targets):
                orphan_containers.append(node)
        
        print(f"📊 Found {len(orphan_containers)} remaining orphan containers")
        
        # Analyze patterns in remaining orphans
        patterns = {}
        
        for orphan in orphan_containers:
            orphan_id = orphan.node_id
            
            # Categorize by pattern
            if '_nested_menu_' in orphan_id and orphan_id.endswith('_menu_1'):
                pattern = "nested_menu_1"
            elif '_nested_menu_' in orphan_id and orphan_id.endswith('_menu_2'):
                pattern = "nested_menu_2"
            elif '_nested_menu_' in orphan_id:
                pattern = "other_nested_menu"
            elif orphan_id.endswith('_menu_0'):
                pattern = "top_level_menu_0"
            else:
                pattern = "other_pattern"
            
            if pattern not in patterns:
                patterns[pattern] = []
            patterns[pattern].append(orphan_id)
        
        print(f"\n📋 Pattern analysis:")
        for pattern, orphan_ids in patterns.items():
            print(f"\n  🔸 {pattern}: {len(orphan_ids)} orphans")
            
            # Show first few examples
            for i, orphan_id in enumerate(orphan_ids[:5]):
                print(f"    {i+1}. {orphan_id}")
                
                # For nested_menu_1 pattern, check why it wasn't fixed
                if pattern == "nested_menu_1":
                    # Extract expected parent choice
                    if orphan_id.endswith('_menu_1'):
                        expected_parent_choice = orphan_id[:-7]  # Remove "_menu_1"
                        
                        # Check if choice exists
                        choice_exists = any(n.node_id == expected_parent_choice 
                                          for n in result.nodes if n.node_type == 'choice_button')
                        print(f"       Expected parent: {expected_parent_choice}")
                        print(f"       Parent exists: {'✅' if choice_exists else '❌'}")
                        
                        if not choice_exists:
                            # Check why parent container might not exist
                            if '_choice_' in expected_parent_choice:
                                parent_container = expected_parent_choice.rsplit('_choice_', 1)[0]
                                container_exists = any(n.node_id == parent_container 
                                                     for n in result.nodes if n.node_type == 'menu_container')
                                print(f"       Expected container: {parent_container}")
                                print(f"       Container exists: {'✅' if container_exists else '❌'}")
            
            if len(orphan_ids) > 5:
                print(f"    ... and {len(orphan_ids) - 5} more")
        
        # Look for specific issues with top-level menu_0 orphans
        if "top_level_menu_0" in patterns:
            print(f"\n🔍 Analyzing top-level menu_0 orphans:")
            menu_0_orphans = patterns["top_level_menu_0"]
            
            for orphan_id in menu_0_orphans[:10]:
                # These should be connected to their label
                expected_label = orphan_id.replace('_menu_0', '')
                
                # Check if label exists
                label_exists = any(n.node_id == expected_label 
                                 for n in result.nodes if n.node_type not in ['menu_container', 'choice_button'])
                print(f"    {orphan_id}")
                print(f"      Expected label: {expected_label}")
                print(f"      Label exists: {'✅' if label_exists else '❌'}")
                
                if label_exists:
                    # Check if there's supposed to be a connection
                    label_connections = [c for c in result.connections 
                                       if hasattr(c, 'source_node_id') and c.source_node_id == expected_label]
                    print(f"      Label outgoing connections: {len(label_connections)}")
                    
                    # Check if any go to this container
                    to_this_container = [c for c in label_connections 
                                       if hasattr(c, 'target_node_id') and c.target_node_id == orphan_id]
                    print(f"      Connections to this container: {len(to_this_container)}")
        
        print(f"\n📊 SUMMARY:")
        print(f"  Remaining orphan containers: {len(orphan_containers)}")
        print(f"  Main patterns:")
        for pattern, orphan_ids in sorted(patterns.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"    - {pattern}: {len(orphan_ids)}")
        
    except Exception as e:
        print(f"ERROR during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_remaining_orphans() 