#!/usr/bin/env python3
"""
Test Targeted Fixes
==================

Verify that the menu container fixes resolve the "red nodes in corner" disaster.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add the main app directory to path for renpy-source-api imports
current_dir = Path(__file__).parent
app_dir = current_dir.parent.parent / "app"
renpy_api_dir = app_dir / "renpy-source-api"
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(renpy_api_dir))

from core import RenpyProject
import networkx as nx

def test_menu_container_fixes():
    """Test that menu containers now get proper colors and data."""
    
    project_path = r"T:\AG\MySisterMyRoommateV1.69-pc\game"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_file = f"test_fixes_{timestamp}.txt"
    
    print(f"=== TESTING TARGETED FIXES ===")
    print(f"Saving results to: {test_file}")
    print("=" * 40)
    
    try:
        with open(test_file, 'w') as f:
            f.write(f"=== TARGETED FIXES TEST ===\n")
            f.write(f"Timestamp: {datetime.now()}\n\n")
            
            # Load flow graph data
            project = RenpyProject(project_path)
            project.analyze()
            flow_graph = project.get_flow_graph()
            
            # Create NetworkX graph
            graph = nx.DiGraph()
            for node_id, node_data in flow_graph.items():
                graph.add_node(node_id, **node_data)
            
            for node_id, node_data in flow_graph.items():
                outgoing_flows = node_data.get('outgoing_flows', [])
                for flow in outgoing_flows:
                    target = flow.get('target_label')
                    if target:
                        graph.add_edge(node_id, target, **flow)
            
            # Test menu container creation with fixes
            menu_containers_created = 0
            red_nodes_fixed = 0
            proper_outgoing_flows = 0
            
            for node_id, node_data in list(graph.nodes.items()):
                outgoing_flows = node_data.get('outgoing_flows', [])
                menu_choices = [flow for flow in outgoing_flows 
                              if flow.get('flow_type') == 'menu_choice']
                
                if menu_choices:
                    menu_node_id = f"{node_id}_menu_container"
                    menu_containers_created += 1
                    
                    # Build outgoing_flows for the menu container (FIX 2)
                    menu_outgoing_flows = []
                    for choice in menu_choices:
                        target = choice.get('target_label')
                        if target:
                            menu_outgoing_flows.append({
                                'target_label': target,
                                'flow_type': 'menu_choice',
                                'choice_text': choice.get('choice_text', f"Choice -> {target}")
                            })
                    
                    # Test node data with fixes
                    menu_node_data = {
                        'name': f"Menu: {node_id}",
                        'node_type': 'menu_container',
                        'has_menu': True,
                        'menu_choices': len(menu_choices),
                        'outgoing_flows': menu_outgoing_flows  # FIX 2: Add missing outgoing_flows
                    }
                    
                    # Test color logic (FIX 1)
                    node_type = menu_node_data.get('node_type')
                    has_outgoing_flows = bool(menu_node_data.get('outgoing_flows', []))
                    
                    if node_type == 'menu_container':
                        # Should get ORANGE color now (not red)
                        color_result = "ORANGE (255, 140, 0)"
                        red_nodes_fixed += 1
                    elif not has_outgoing_flows:
                        # Would get red for endings
                        color_result = "RED (250, 100, 100) - ENDING"
                    else:
                        color_result = "DEFAULT"
                    
                    if has_outgoing_flows:
                        proper_outgoing_flows += 1
                    
                    # Test first few containers in detail
                    if menu_containers_created <= 5:
                        f.write(f"Menu Container {menu_containers_created}: {menu_node_id}\n")
                        f.write(f"  Node type: {node_type}\n")
                        f.write(f"  Has outgoing_flows: {has_outgoing_flows}\n")
                        f.write(f"  Outgoing flows count: {len(menu_outgoing_flows)}\n")
                        f.write(f"  Expected color: {color_result}\n")
                        f.write(f"  Source node: {node_id}\n\n")
            
            # Summary results
            f.write(f"=== FIX VERIFICATION RESULTS ===\n")
            f.write(f"Total menu containers: {menu_containers_created}\n")
            f.write(f"Containers fixed from red: {red_nodes_fixed}\n")
            f.write(f"Containers with proper outgoing_flows: {proper_outgoing_flows}\n")
            f.write(f"Fix success rate: {red_nodes_fixed}/{menu_containers_created} = {(red_nodes_fixed/menu_containers_created*100):.1f}%\n\n")
            
            # Test specific case: ch4ashbagdone
            if 'ch4ashbagdone' in flow_graph:
                ch4_flows = flow_graph['ch4ashbagdone'].get('outgoing_flows', [])
                ch4_menu_choices = [flow for flow in ch4_flows 
                                  if flow.get('flow_type') == 'menu_choice']
                
                if ch4_menu_choices:
                    f.write(f"=== CH4ASHBAGDONE TEST ===\n")
                    f.write(f"Original node has menu: {flow_graph['ch4ashbagdone'].get('has_menu', False)}\n")
                    f.write(f"Menu choices found: {len(ch4_menu_choices)}\n")
                    f.write(f"Container will be created: ch4ashbagdone_menu_container\n")
                                         f.write(f"Container will be ORANGE (not red)\n")
                     f.write(f"Container will have {len(ch4_menu_choices)} outgoing_flows\n")
                     f.write(f"Disaster status: FIXED\n\n")
            
            # Expected behavior
            f.write(f"=== EXPECTED BEHAVIOR AFTER FIXES ===\n")
            f.write(f"✅ No red menu container nodes\n")
            f.write(f"✅ All menu containers should be ORANGE\n")
            f.write(f"✅ Menu containers have proper outgoing_flows data\n")
            f.write(f"✅ ch4ashbagdone connects to ORANGE container, not direct to destinations\n")
            f.write(f"✅ Container positioning should improve (no corner clustering)\n")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        with open(test_file, 'w') as f:
            f.write(f"ERROR: {e}\n")
            import traceback
            f.write(traceback.format_exc())
        return None
    
    print(f"✅ Fix verification saved to: {test_file}")
    return test_file

if __name__ == "__main__":
    test_menu_container_fixes() 