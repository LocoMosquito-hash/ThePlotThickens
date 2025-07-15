"""
Simple test to verify the menu node fix without heavy dependencies.
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


def test_menu_fix():
    """Test if menu nodes are properly integrated into flow graph."""
    print("🔧 Testing Menu Node Fix")
    print("="*40)
    
    # VN file path
    vn_path = r"T:\AG\MySisterMyRoommateV1.69-pc\game"
    
    try:
        project = RenpyProject(vn_path)
        
        if not project.is_analyzed:
            print("🔄 Running project analysis...")
            project.analyze()
        
        # Test the fixed method
        print("🔍 Testing get_flow_graph()...")
        flow_graph = project.get_flow_graph()
        print(f"✅ get_flow_graph returned {len(flow_graph)} labels")
        
        if 'ch4ashbagdone' in flow_graph:
            label_data = flow_graph['ch4ashbagdone']
            print(f"🎯 ch4ashbagdone flow graph data:")
            print(f"    Name: {label_data.get('name')}")
            print(f"    Has menu: {label_data.get('has_menu')}")
            print(f"    Incoming flows: {len(label_data.get('incoming_flows', []))}")
            print(f"    Outgoing flows: {len(label_data.get('outgoing_flows', []))}")
            
            # Check outgoing flow destinations
            outgoing = label_data.get('outgoing_flows', [])
            if outgoing:
                print(f"    Outgoing destinations: {[flow['target_label'] for flow in outgoing]}")
        else:
            print("❌ ch4ashbagdone not found in flow graph")
        
        # Test menu nodes separately
        print("\n🔍 Testing get_menu_nodes_by_label()...")
        menu_nodes_by_label = project.parser.get_menu_nodes_by_label(vn_path)
        
        if 'ch4ashbagdone' in menu_nodes_by_label:
            menu_nodes = menu_nodes_by_label['ch4ashbagdone']
            print(f"✅ ch4ashbagdone has {len(menu_nodes)} menu nodes")
            
            for menu_node in menu_nodes:
                print(f"    Menu: {menu_node.node_id}")
                print(f"      Choices: {[choice.destination for choice in menu_node.choices]}")
        else:
            print("❌ ch4ashbagdone not found in menu nodes")
        
        print("\n🎯 Summary:")
        print(f"    Flow graph labels: {len(flow_graph)}")
        print(f"    Menu node labels: {len(menu_nodes_by_label)}")
        
        # The key test: check if both have ch4ashbagdone
        has_flow = 'ch4ashbagdone' in flow_graph
        has_menu = 'ch4ashbagdone' in menu_nodes_by_label
        
        print(f"    ch4ashbagdone in flow graph: {has_flow}")
        print(f"    ch4ashbagdone has menu nodes: {has_menu}")
        
        if has_flow and has_menu:
            print("✅ SUCCESS: Both flow graph and menu nodes contain ch4ashbagdone")
            print("✅ Menu nodes should now appear in visualizations!")
        else:
            print("❌ ISSUE: Missing data for proper menu node integration")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_menu_fix() 