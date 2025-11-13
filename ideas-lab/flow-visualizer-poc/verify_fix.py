#!/usr/bin/env python3
"""
Verify that the fix resolved the shared parenthood issue.
"""
import sys
sys.path.insert(0, r'C:\Users\juanc\PycharmProjects\TPT3\ThePlotThickens\app\renpy-source-api')
sys.path.insert(0, r'C:\Users\juanc\PycharmProjects\TPT3\ThePlotThickens\ideas-lab\flow-visualizer-poc')

def verify():
    """Verify the label-menu hierarchy is correct."""
    
    print("=" * 70)
    print("VERIFICATION: Shared Parenthood Fix")
    print("=" * 70)
    
    from parser import RenpyParser
    from renpy_data_adapter import RenpyFlowDataAdapter
    
    game_path = r'T:\AG\TheUnbroken-Pt.5-pc'
    
    print(f"\n[1] Building flow graph...")
    parser = RenpyParser()
    flow_graph = parser.build_flow_graph(game_path)
    
    # Get the label node
    if 'fightnightnumberonebranch' not in flow_graph:
        print("❌ Label not found in flow graph")
        return 1
    
    label_node = flow_graph['fightnightnumberonebranch']
    
    print(f"\n[2] Label's Outgoing Flows (should be 0):")
    print(f"   Count: {len(label_node.outgoing_flows)}")
    for flow in label_node.outgoing_flows:
        print(f"      ❌ → {flow.target_label} ({flow.flow_type})")
    
    if len(label_node.outgoing_flows) == 0:
        print("   ✅ No explicit flows (correct!)")
    
    print(f"\n[3] Building visualization data...")
    adapter = RenpyFlowDataAdapter(flow_graph, game_path)
    vis_data = adapter.prepare_visualization_data()
    
    # Find the label node in visualization data
    label_vis_node = None
    for node_id, node_data in vis_data['nodes'].items():
        if node_data['data'].get('name') == 'fightnightnumberonebranch' and node_data['data'].get('type') == 'label':
            label_vis_node = (node_id, node_data)
            break
    
    if not label_vis_node:
        print("❌ Label not found in visualization data")
        return 1
    
    label_id, label_data = label_vis_node
    
    # Find all edges from this label
    label_children = []
    for edge in vis_data['edges']:
        if edge['source'] == label_id:
            target_node = vis_data['nodes'][edge['target']]
            label_children.append({
                'type': target_node['data']['type'],
                'name': target_node['data'].get('name', target_node['data'].get('label', 'unknown')),
                'edge_type': edge.get('type', 'unknown')
            })
    
    print(f"\n[4] Label's Children in Hierarchy:")
    print(f"   Count: {len(label_children)}")
    
    menu_children = [c for c in label_children if 'menu' in c['type'].lower() or 'container' in c['type'].lower()]
    label_children_non_menu = [c for c in label_children if 'menu' not in c['type'].lower() and 'container' not in c['type'].lower()]
    
    print(f"\n   Menu children (expected 1): {len(menu_children)}")
    for child in menu_children:
        print(f"      ✅ {child['type']}: {child['name']}")
    
    print(f"\n   Non-menu children (expected 0): {len(label_children_non_menu)}")
    for child in label_children_non_menu:
        print(f"      ❌ {child['type']}: {child['name']} (SHOULD NOT BE HERE!)")
    
    print(f"\n{'=' * 70}")
    if len(label_children_non_menu) == 0 and len(menu_children) == 1:
        print("✅ FIX VERIFIED: Label only has menu as child, no stolen connections!")
        return 0
    else:
        print("❌ FIX INCOMPLETE: Label still has non-menu children")
        return 1

if __name__ == "__main__":
    sys.exit(verify())

