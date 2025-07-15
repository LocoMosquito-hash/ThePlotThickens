"""
Debug script to check why menu nodes aren't being associated with labels properly.
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from parser import RenpyParser
except ImportError as e:
    print(f"❌ Could not import required modules: {e}")
    sys.exit(1)


def debug_menu_association():
    """Debug the menu node association with labels."""
    print("🐛 Debugging Menu Node Association")
    print("="*50)
    
    # VN file path
    vn_path = r"T:\AG\MySisterMyRoommateV1.69-pc\game"
    parser = RenpyParser()
    
    print("🔍 Step 1: Building flow graph...")
    flow_graph = parser.build_flow_graph(vn_path)
    print(f"✅ Built flow graph with {len(flow_graph)} labels")
    
    if 'ch4ashbagdone' in flow_graph:
        node = flow_graph['ch4ashbagdone']
        print(f"\n🎯 ch4ashbagdone LabelNode inspection:")
        print(f"    Name: {node.name}")
        print(f"    Menu structures: {len(node.menu_structures)}")
        print(f"    Menu nodes: {len(node.menu_nodes)}")
        print(f"    Menu count: {node.menu_count}")
        print(f"    Has menu: {node.has_menu}")
        
        if node.menu_structures:
            print(f"    Menu structure details:")
            for i, menu_struct in enumerate(node.menu_structures):
                print(f"      {i+1}. Label context: {menu_struct.label_context}")
                print(f"         Choices: {[choice.text for choice in menu_struct.choices]}")
        
        if node.menu_nodes:
            print(f"    Menu node details:")
            for i, menu_node in enumerate(node.menu_nodes):
                print(f"      {i+1}. Node ID: {menu_node.node_id}")
                print(f"         Parent label: {menu_node.parent_label}")
                print(f"         Choices: {len(menu_node.choices)}")
        
        print(f"\n🔍 Outgoing flows count: {len(node.outgoing_flows)}")
        if len(node.outgoing_flows) > 10:
            print(f"    First 10 destinations: {[flow.target_label for flow in node.outgoing_flows[:10]]}")
            # Check for duplicates
            destinations = [flow.target_label for flow in node.outgoing_flows]
            unique_destinations = list(set(destinations))
            print(f"    Unique destinations: {len(unique_destinations)} out of {len(destinations)}")
            if len(unique_destinations) < len(destinations):
                print(f"    ⚠️  WARNING: Duplicate flows detected!")
                from collections import Counter
                counts = Counter(destinations)
                duplicates = {dest: count for dest, count in counts.items() if count > 1}
                print(f"    Duplicates: {duplicates}")
        else:
            print(f"    Destinations: {[flow.target_label for flow in node.outgoing_flows]}")
    else:
        print("❌ ch4ashbagdone not found in flow graph")
    
    print("\n🔍 Step 2: Testing menu association directly...")
    
    # Get menus and see if they have the right label context
    menus = parser.find_all_menus(vn_path)
    ch4_menus = [menu for menu in menus if menu.label_context == 'ch4ashbagdone']
    
    print(f"✅ Found {len(ch4_menus)} menus with ch4ashbagdone context")
    for i, menu in enumerate(ch4_menus):
        print(f"  Menu {i+1}:")
        print(f"    Label context: {menu.label_context}")
        print(f"    Choices: {[choice.text for choice in menu.choices]}")
        print(f"    Choice destinations: {[choice.destination for choice in menu.choices]}")


if __name__ == "__main__":
    debug_menu_association() 