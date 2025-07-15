"""
Debug script to investigate menu detection issues with ch4ashbagdone.
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


def debug_menu_detection_step_by_step():
    """Debug menu detection step by step."""
    print("🔍 DEBUGGING MENU DETECTION FOR ch4ashbagdone")
    print("="*60)
    
    vn_path = r"T:\AG\MySisterMyRoommateV1.69-pc\game"
    parser = RenpyParser()
    
    print("📂 Step 1: Check if parser can find menus...")
    try:
        all_menus = parser.find_all_menus(vn_path)
        print(f"✅ Found {len(all_menus)} total menus")
        
        # Look for ch4ashbagdone specifically
        ch4_menus = [menu for menu in all_menus if 
                    'ch4ashbagdone' in menu.parent_label.lower() or
                    any('Fashion' in choice.text for choice in menu.choices)]
        
        print(f"🎯 Found {len(ch4_menus)} menus related to ch4ashbagdone")
        
        for i, menu in enumerate(ch4_menus):
            print(f"\n  Menu {i+1}:")
            print(f"    Parent Label: {menu.parent_label}")
            print(f"    File: {os.path.basename(menu.file_path)}")
            print(f"    Line: {menu.line_number}")
            print(f"    Choices: {[choice.text for choice in menu.choices]}")
            
    except Exception as e:
        print(f"❌ Error finding menus: {e}")
        return
    
    print(f"\n📊 Step 2: Check flow graph creation...")
    try:
        flow_graph = parser.build_flow_graph(vn_path)
        print(f"✅ Built flow graph with {len(flow_graph)} labels")
        
        if 'ch4ashbagdone' in flow_graph:
            node = flow_graph['ch4ashbagdone']
            print(f"\n🎯 ch4ashbagdone node details:")
            print(f"    Has menu: {node.has_menu}")
            print(f"    Menu structures: {len(node.menu_structures) if hasattr(node, 'menu_structures') else 'None'}")
            print(f"    Menu nodes: {len(node.menu_nodes) if hasattr(node, 'menu_nodes') else 'None'}")
            print(f"    Successors: {node.successors}")
            
            if hasattr(node, 'menu_structures') and node.menu_structures:
                print(f"    Menu structure details:")
                for i, menu_struct in enumerate(node.menu_structures):
                    print(f"      Menu {i}: {[choice.text for choice in menu_struct.choices]}")
        else:
            print(f"❌ ch4ashbagdone not found in flow graph!")
            
    except Exception as e:
        print(f"❌ Error building flow graph: {e}")
        return
    
    print(f"\n🔧 Step 3: Check menu association process...")
    try:
        # Get menus by label
        menus_by_label = parser.get_menu_nodes_by_label(vn_path)
        print(f"✅ Got menus for {len(menus_by_label)} labels")
        
        if 'ch4ashbagdone' in menus_by_label:
            menus = menus_by_label['ch4ashbagdone']
            print(f"🎯 ch4ashbagdone has {len(menus)} menu(s):")
            for i, menu in enumerate(menus):
                print(f"    Menu {i}: {[choice.text for choice in menu.choices]}")
        else:
            print(f"❌ ch4ashbagdone not found in menus_by_label!")
            print(f"Available labels: {list(menus_by_label.keys())[:10]}...")
            
    except Exception as e:
        print(f"❌ Error getting menu nodes by label: {e}")
        return


def debug_has_menu_computation():
    """Debug the has_menu computation specifically."""
    print(f"\n🔍 DEBUGGING has_menu COMPUTATION")
    print("="*40)
    
    vn_path = r"T:\AG\MySisterMyRoommateV1.69-pc\game"
    parser = RenpyParser()
    
    try:
        flow_graph = parser.build_flow_graph(vn_path)
        
        if 'ch4ashbagdone' in flow_graph:
            node = flow_graph['ch4ashbagdone']
            
            print(f"📊 Node attributes:")
            print(f"    hasattr(node, 'menu_structures'): {hasattr(node, 'menu_structures')}")
            print(f"    hasattr(node, 'menu_nodes'): {hasattr(node, 'menu_nodes')}")
            
            if hasattr(node, 'menu_structures'):
                print(f"    len(menu_structures): {len(node.menu_structures)}")
                print(f"    menu_structures type: {type(node.menu_structures)}")
                print(f"    menu_structures: {node.menu_structures}")
                
            if hasattr(node, 'menu_nodes'):
                print(f"    len(menu_nodes): {len(node.menu_nodes)}")
                print(f"    menu_nodes type: {type(node.menu_nodes)}")
                print(f"    menu_nodes: {node.menu_nodes}")
                
            # Check how has_menu is computed
            if hasattr(node, 'menu_structures'):
                computed_has_menu = len(node.menu_structures) > 0
                print(f"    Computed has_menu: {computed_has_menu}")
                
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    debug_menu_detection_step_by_step()
    debug_has_menu_computation() 