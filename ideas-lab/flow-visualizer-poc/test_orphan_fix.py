#!/usr/bin/env python3
"""
Test Orphan Fix
===============

Test if the orphan fix is working without import errors.
"""

from renpy_data_adapter import RenpyFlowDataAdapter

def test_orphan_fix():
    """Test the orphan fix."""
    print("Starting orphan fix test...")
    
    adapter = RenpyFlowDataAdapter()
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    try:
        result = adapter.analyze_project(project_path)
        
        if result:
            print(f"✅ SUCCESS! Total nodes: {len(result.nodes)}")
            print(f"✅ SUCCESS! Total connections: {len(result.connections)}")
            
            # Count orphan containers
            orphan_containers = 0
            for node in result.nodes:
                if (node.node_type == 'menu_container' and 
                    '_nested_menu_' in node.node_id and 
                    node.node_id.endswith('_menu_1')):
                    
                    # Check if this container has incoming connections
                    has_incoming = any(conn.target_node_id == node.node_id 
                                     for conn in result.connections)
                    if not has_incoming:
                        orphan_containers += 1
            
            print(f"📊 Remaining orphan containers: {orphan_containers}")
            
            # Count auto-generated choices
            auto_choices = sum(1 for node in result.nodes 
                             if node.node_type == 'choice_button' and 
                             'Auto-generated' in node.display_name)
            
            print(f"🔧 Auto-generated choice buttons: {auto_choices}")
            
        else:
            print("❌ FAILED - No result returned")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_orphan_fix() 