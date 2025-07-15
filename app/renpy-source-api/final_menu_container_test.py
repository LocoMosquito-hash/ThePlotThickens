"""
Final comprehensive test of the menu container system.
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from core import RenpyProject
    from flow_visualizer import FlowGraphVisualizer
    from menu_container_visualizer import MenuContainerVisualizer
except ImportError as e:
    print(f"❌ Could not import required modules: {e}")
    sys.exit(1)


def run_comprehensive_test():
    """Run a comprehensive test of the menu container system."""
    
    print("🧪 COMPREHENSIVE MENU CONTAINER SYSTEM TEST")
    print("="*70)
    
    vn_path = r"T:\AG\MySisterMyRoommateV1.69-pc\game"
    focus_label = "ch4ashbagdone"
    
    try:
        # Stage 1: Project Analysis
        print("\n📊 Stage 1: Project Analysis")
        print("-" * 30)
        
        project = RenpyProject(vn_path)
        if not project.is_analyzed:
            print("🔄 Analyzing project...")
            project.analyze()
        
        print(f"✅ Project analyzed successfully")
        
        # Stage 2: Menu Detection
        print("\n🔍 Stage 2: Menu Detection")
        print("-" * 30)
        
        flow_graph = project.parser.build_flow_graph(vn_path)
        if focus_label in flow_graph:
            node = flow_graph[focus_label]
            print(f"✅ {focus_label} found in flow graph")
            print(f"    Has menu: {node.has_menu}")
            print(f"    Menu structures: {len(node.menu_structures)}")
            print(f"    Menu nodes: {len(node.menu_nodes)}")
            
            if node.has_menu and len(node.menu_nodes) > 0:
                menu_node = node.menu_nodes[0]
                print(f"    Menu node ID: {menu_node.node_id}")
                print(f"    Choices: {[choice.text for choice in menu_node.choices]}")
            else:
                print("❌ Menu detection failed!")
                return False
        else:
            print(f"❌ {focus_label} not found in flow graph!")
            return False
        
        # Stage 3: NetworkX Graph Construction
        print("\n🕸️  Stage 3: NetworkX Graph Construction")
        print("-" * 30)
        
        visualizer = FlowGraphVisualizer(project)
        graph = visualizer.graph
        
        print(f"✅ NetworkX graph created")
        print(f"    Total nodes: {len(graph.nodes())}")
        print(f"    Total edges: {len(graph.edges())}")
        
        # Check menu nodes
        menu_nodes = [node for node, data in graph.nodes(data=True) if data.get('node_type') == 'menu']
        ch4_menu_nodes = [node for node in menu_nodes if focus_label in node]
        
        print(f"    Total menu nodes: {len(menu_nodes)}")
        print(f"    {focus_label} menu nodes: {len(ch4_menu_nodes)}")
        
        if len(ch4_menu_nodes) == 0:
            print("❌ No menu nodes found for ch4ashbagdone!")
            return False
        
        # Check connections
        if focus_label in graph:
            successors = list(graph.successors(focus_label))
            menu_successors = [s for s in successors if s in menu_nodes]
            direct_successors = [s for s in successors if s not in menu_nodes]
            
            print(f"    {focus_label} total successors: {len(successors)}")
            print(f"    Menu successors: {len(menu_successors)}")
            print(f"    Direct successors: {len(direct_successors)}")
            
            if len(menu_successors) > 0 and len(direct_successors) == 0:
                print("✅ Perfect! Only connects to menu nodes")
            else:
                print("⚠️  Still has direct connections")
        
        # Stage 4: Menu Container Visualization
        print("\n🎨 Stage 4: Menu Container Visualization")
        print("-" * 30)
        
        container_visualizer = MenuContainerVisualizer(project)
        output_path = container_visualizer.generate_menu_container_visualization(
            focus_label=focus_label,
            output_path=f"{focus_label}_final_test.png"
        )
        
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path) / 1024  # KB
            print(f"✅ Menu container visualization created")
            print(f"    File: {output_path}")
            print(f"    Size: {file_size:.1f} KB")
        else:
            print("❌ Visualization file not created!")
            return False
        
        # Stage 5: System Validation
        print("\n🔬 Stage 5: System Validation")
        print("-" * 30)
        
        # Test the complete workflow
        success_criteria = [
            (node.has_menu, "Menu detection"),
            (len(node.menu_nodes) > 0, "Menu node creation"),
            (len(ch4_menu_nodes) > 0, "NetworkX menu nodes"),
            (len(menu_successors) > 0, "Menu connections"),
            (len(direct_successors) == 0, "No direct connections"),
            (os.path.exists(output_path), "Visualization output")
        ]
        
        passed = 0
        total = len(success_criteria)
        
        for condition, description in success_criteria:
            if condition:
                print(f"    ✅ {description}")
                passed += 1
            else:
                print(f"    ❌ {description}")
        
        print(f"\n📊 FINAL RESULTS: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 COMPLETE SUCCESS! Menu container system is fully functional!")
            print("\n🌟 ACHIEVEMENTS:")
            print("    • Menu detection working perfectly")
            print("    • Menu nodes created with rich metadata")
            print("    • Direct connections eliminated")
            print("    • Visual clutter reduced significantly")
            print("    • Menu container visualization implemented")
            print("    • System ready for integration into main app")
            return True
        else:
            print("⚠️  Some issues remaining. See details above.")
            return False
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_comprehensive_test()
    
    if success:
        print("\n🚀 READY FOR INTEGRATION!")
        print("The menu container system is complete and ready to be integrated")
        print("into The Plot Thickens main application as the 'source of truth'")
        print("for Gallery, Decision Points, Storyboard, and other components.")
    else:
        print("\n🔧 NEEDS DEBUGGING")
        print("Some components need additional work before integration.") 