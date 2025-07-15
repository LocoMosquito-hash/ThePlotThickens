"""
Debug script to check flow graph creation and menu node integration.
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from parser import RenpyParser
    from core import RenpyProject
except ImportError as e:
    print(f"❌ Could not import required modules: {e}")
    sys.exit(1)


def debug_flow_graph():
    """Debug the flow graph creation and menu node integration."""
    print("🐛 Debugging Flow Graph & Menu Node Integration")
    print("="*60)
    
    # VN file path
    vn_path = r"T:\AG\MySisterMyRoommateV1.69-pc\game"
    
    print("🔍 Step 1: Testing parser.get_menu_nodes_by_label()...")
    parser = RenpyParser()
    
    try:
        menu_nodes_by_label = parser.get_menu_nodes_by_label(vn_path)
        print(f"✅ get_menu_nodes_by_label returned {len(menu_nodes_by_label)} labels with menus")
        
        if 'ch4ashbagdone' in menu_nodes_by_label:
            menu_nodes = menu_nodes_by_label['ch4ashbagdone']
            print(f"🎯 ch4ashbagdone has {len(menu_nodes)} menu nodes:")
            for i, menu_node in enumerate(menu_nodes):
                print(f"    Menu {i+1}: {menu_node.node_id}")
                print(f"      Name: {menu_node.name}")
                print(f"      Choices: {len(menu_node.choices)}")
                print(f"      Destinations: {[choice.destination for choice in menu_node.choices]}")
        else:
            print("❌ ch4ashbagdone not found in menu_nodes_by_label")
            print(f"Available labels: {list(menu_nodes_by_label.keys())[:10]}...")
    
    except Exception as e:
        print(f"❌ Error in get_menu_nodes_by_label: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🔍 Step 2: Testing RenpyProject creation...")
    
    try:
        project = RenpyProject(vn_path)
        print(f"✅ Created RenpyProject")
        
        if not project.is_analyzed:
            print("🔄 Running project analysis...")
            project.analyze()
            print("✅ Project analysis complete")
        
        flow_data = project.get_label_flow_analysis()
        print(f"✅ Got flow data with {len(flow_data.get('labels', {}))} labels")
        
        if 'ch4ashbagdone' in flow_data.get('labels', {}):
            label_data = flow_data['labels']['ch4ashbagdone']
            print(f"🎯 ch4ashbagdone flow data:")
            print(f"    Incoming: {len(label_data.get('incoming_connections', []))}")
            print(f"    Outgoing: {len(label_data.get('outgoing_connections', []))}")
            print(f"    Reachable: {label_data.get('reachable', 'unknown')}")
        else:
            print("❌ ch4ashbagdone not found in flow data")
    
    except Exception as e:
        print(f"❌ Error in RenpyProject: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🔍 Step 3: Testing Flow Visualizer...")
    
    try:
        from flow_visualizer import FlowGraphVisualizer
        
        visualizer = FlowGraphVisualizer(project)
        print(f"✅ Created FlowGraphVisualizer")
        
        # Check the built graph
        G = visualizer.graph
        print(f"✅ Built NetworkX graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
        
        # Check for menu nodes
        menu_nodes = [node for node in G.nodes() if G.nodes[node].get('node_type') == 'menu']
        print(f"🎯 Found {len(menu_nodes)} menu nodes in graph:")
        
        ch4_menu_nodes = [node for node in menu_nodes if 'ch4ashbagdone' in node]
        if ch4_menu_nodes:
            for menu_node_id in ch4_menu_nodes:
                node_data = G.nodes[menu_node_id]
                print(f"    {menu_node_id}:")
                print(f"      Parent: {node_data.get('parent_label')}")
                print(f"      Choices: {node_data.get('choice_count')}")
                print(f"      Type: {node_data.get('node_type')}")
        else:
            print("❌ No ch4ashbagdone menu nodes found in graph")
        
        # Check if ch4ashbagdone label exists
        if 'ch4ashbagdone' in G.nodes():
            node_data = G.nodes['ch4ashbagdone']
            print(f"🎯 ch4ashbagdone label node:")
            print(f"    Has menu: {node_data.get('has_menu')}")
            print(f"    Outgoing edges: {len(list(G.successors('ch4ashbagdone')))}")
            print(f"    Successors: {list(G.successors('ch4ashbagdone'))}")
        else:
            print("❌ ch4ashbagdone label not found in graph")
    
    except Exception as e:
        print(f"❌ Error in FlowGraphVisualizer: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎯 Debug Summary:")
    print("    Check the outputs above to identify where menu nodes are lost")


if __name__ == "__main__":
    debug_flow_graph() 