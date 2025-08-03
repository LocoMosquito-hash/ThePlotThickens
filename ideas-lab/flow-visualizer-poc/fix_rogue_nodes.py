#!/usr/bin/env python3
"""
Fix for the rogue node issue in ep2cont5.

The problem is in the orphan container handling logic that creates intermediate
nodes when it should instead connect choices directly to their nested menus.
"""

import sys
from pathlib import Path

# Add renpy-source-api to path
current_dir = Path(__file__).parent
app_dir = current_dir.parent.parent / "app"
sys.path.insert(0, str(app_dir / "renpy-source-api"))

from renpy_data_adapter import RenpyFlowDataAdapter

def apply_fix():
    """Apply the fix to the rogue node issue."""
    
    print("🔧 Applying fix for rogue node issue...")
    
    # Read the current renpy_data_adapter.py
    adapter_file = Path(__file__).parent / "renpy_data_adapter.py"
    
    with open(adapter_file, 'r') as f:
        content = f.read()
    
    # The problematic logic is in the orphan container handling
    # We need to add better filtering to prevent creation of intermediate nodes
    # that are actually legitimate nested menu structures
    
    fix_code = '''
    def _is_legitimate_nested_menu(self, container_id: str, container_nodes: List) -> bool:
        """
        Check if a container ID represents a legitimate nested menu structure
        rather than a missing intermediate node.
        
        Legitimate pattern: {label}_{something}_menu_{index}
        Problematic pattern: {label}_nested_menu_{index} (without proper parent)
        """
        # Check if this follows the standard nested menu naming pattern
        if '_menu_' in container_id and '_choice_' in container_id:
            # This is likely a legitimate nested menu: label_menu_0_choice_1_menu_1
            return True
            
        # Check if there's already a proper nested menu structure for this
        if '_nested_menu_' in container_id and not '_choice_' in container_id:
            # This might be a phantom container like ep2cont5_nested_menu_1
            # Check if there's already a properly named nested menu
            base_pattern = container_id.replace('_nested_menu_', '_menu_0_choice_')
            for node in container_nodes:
                if node.node_id.startswith(base_pattern) and '_menu_' in node.node_id:
                    print(f"[ROGUE FIX] Skipping phantom container {container_id}, legitimate structure exists: {node.node_id}")
                    return False
                    
        return True
'''
    
    # Find the location to insert the fix
    insert_point = content.find("def _create_hierarchy_connections(self, flow_graph: Dict[str, Any], container_nodes: List, choice_connections: List):")
    
    if insert_point == -1:
        print("❌ Could not find insertion point for fix")
        return False
        
    # Insert the fix method before _create_hierarchy_connections
    new_content = content[:insert_point] + fix_code + "\n    " + content[insert_point:]
    
    # Now we need to modify the orphan container processing to use this check
    orphan_fix = '''
        # ROGUE NODE FIX: Skip creating intermediate containers for legitimate nested menus
        orphan_containers = [container for container in container_nodes 
                           if container.node_type == 'menu_container' and 
                           not any(conn.target_node_id == container.node_id for conn in choice_connections) and
                           self._is_legitimate_nested_menu(container.node_id, container_nodes)]
'''
    
    # Replace the orphan container detection
    old_orphan_detection = '''        # Find orphan containers (containers without incoming connections)
        orphan_containers = [container for container in container_nodes 
                           if container.node_type == 'menu_container' and 
                           not any(conn.target_node_id == container.node_id for conn in choice_connections)]'''
    
    new_content = new_content.replace(old_orphan_detection, orphan_fix)
    
    # Write the fixed version
    backup_file = adapter_file.with_suffix('.py.backup')
    
    # Create backup
    with open(backup_file, 'w') as f:
        f.write(content)
    print(f"✅ Created backup: {backup_file}")
    
    # Write the fix
    with open(adapter_file, 'w') as f:
        f.write(new_content)
    print(f"✅ Applied fix to: {adapter_file}")
    
    return True

def test_fix():
    """Test the fix with the Haley game."""
    
    print("🧪 Testing fix with Haley's Story...")
    
    game_path = "F:\\Bin\\Games\\Haley-1.1-alt-pc\\game"
    
    adapter = RenpyFlowDataAdapter(use_hybrid=True)
    visualization_data = adapter.analyze_project(game_path)
    
    # Check ep2cont5 nodes
    ep2cont5_nodes = [node for node in visualization_data.nodes if 'ep2cont5' in node.node_id]
    
    print(f"📊 ep2cont5 nodes after fix: {len(ep2cont5_nodes)}")
    
    # Look for the rogue nodes specifically
    rogue_nodes = [node for node in ep2cont5_nodes 
                   if node.node_id == 'ep2cont5_nested_menu_1' or 
                      node.node_id == 'ep2cont5_nested_menu_1_choice_1']
    
    if rogue_nodes:
        print(f"❌ Fix failed - still found {len(rogue_nodes)} rogue nodes:")
        for node in rogue_nodes:
            print(f"  - {node.node_id}")
    else:
        print("✅ Fix successful - no rogue nodes found!")
        
    # Show the corrected structure
    print("\n📋 Corrected ep2cont5 structure:")
    for node in sorted(ep2cont5_nodes, key=lambda x: x.node_id):
        print(f"  - {node.node_id} ({node.node_type})")

def main():
    """Apply and test the fix."""
    if apply_fix():
        test_fix()
    else:
        print("❌ Fix application failed")

if __name__ == "__main__":
    main()