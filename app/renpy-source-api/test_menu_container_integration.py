"""
Test script to verify menu container integration is working.
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from core import RenpyProject
    from flow_visualizer import FlowGraphVisualizer
except ImportError as e:
    print(f"❌ Could not import required modules: {e}")
    sys.exit(1)


def test_menu_container_integration():
    """Test if menu nodes are being created in the flow visualization."""
    print("🧪 TESTING MENU CONTAINER INTEGRATION")
    print("="*60)
    
    vn_path = r"T:\AG\MySisterMyRoommateV1.69-pc\game"
    
    try:
        # Create project and visualizer
        project = RenpyProject(vn_path)
        if not project.is_analyzed:
            print("🔄 Analyzing project...")
            project.analyze()
        
        visualizer = FlowGraphVisualizer(project)
        
        # Check the NetworkX graph
        print("📊 Checking NetworkX graph construction...")
        graph = visualizer.graph
        
        print(f"✅ Graph created with {len(graph.nodes())} nodes and {len(graph.edges())} edges")
        
        # Look for menu nodes
        menu_nodes = [node for node, data in graph.nodes(data=True) if data.get('node_type') == 'menu']
        print(f"🎯 Found {len(menu_nodes)} menu nodes")
        
        # Check for ch4ashbagdone specifically
        ch4_menu_nodes = [node for node in menu_nodes if 'ch4ashbagdone' in node]
        print(f"🎯 Found {len(ch4_menu_nodes)} menu nodes for ch4ashbagdone")
        
        for menu_node in ch4_menu_nodes:
            print(f"    Menu node: {menu_node}")
            node_data = graph.nodes[menu_node]
            print(f"    Choice count: {node_data.get('choice_count', 'N/A')}")
            print(f"    Parent label: {node_data.get('parent_label', 'N/A')}")
        
        # Check ch4ashbagdone connections
        if 'ch4ashbagdone' in graph:
            ch4_successors = list(graph.successors('ch4ashbagdone'))
            print(f"\n📊 ch4ashbagdone successors: {ch4_successors}")
            print(f"    Count: {len(ch4_successors)}")
            
            # Check if any successors are menu nodes
            menu_successors = [s for s in ch4_successors if s in menu_nodes]
            direct_successors = [s for s in ch4_successors if s not in menu_nodes]
            
            print(f"    Menu successors: {menu_successors}")
            print(f"    Direct successors: {direct_successors}")
            
            if len(menu_successors) > 0 and len(direct_successors) == 0:
                print("🎉 SUCCESS: ch4ashbagdone connects only to menu nodes!")
            elif len(direct_successors) > 0:
                print("⚠️  ISSUE: ch4ashbagdone still has direct connections to destination labels")
        else:
            print("❌ ch4ashbagdone not found in graph")
            
        # Check menu node connections
        for menu_node in ch4_menu_nodes:
            menu_successors = list(graph.successors(menu_node))
            print(f"\n📊 {menu_node} successors: {menu_successors}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_menu_container_integration() 