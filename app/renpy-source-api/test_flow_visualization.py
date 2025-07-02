"""
Test script for Flow Graph Visualization Engine

This script demonstrates the comprehensive flow visualization capabilities
we've built for Ren'Py narrative analysis.
"""

import os
from flow_visualizer import FlowGraphVisualizer, quick_visualize
from core import RenpyProject

def test_flow_visualization():
    """Test the flow visualization with our known test VN."""
    print("🚀 Testing Flow Graph Visualization Engine")
    print("=" * 60)
    
    # Use our test VN path
    test_vn_path = "T:/AG/Savior-0.16c-pc/game"
    
    if not os.path.exists(test_vn_path):
        print("❌ Test VN not found. Please update the path.")
        return False
    
    try:
        print(f"📁 Analyzing VN: {test_vn_path}")
        print("-" * 40)
        
        # Quick visualization test
        output_dir = quick_visualize(test_vn_path, "demo_flow_visualization")
        
        print(f"\n✅ Flow visualization complete!")
        print(f"📂 Output directory: {output_dir}")
        
        # List generated files
        files = os.listdir(output_dir)
        print(f"\n📋 Generated files:")
        for file in files:
            file_path = os.path.join(output_dir, file)
            file_size = os.path.getsize(file_path)
            size_mb = file_size / (1024 * 1024)
            
            if file.endswith('.png'):
                print(f"   📊 {file} ({size_mb:.1f}MB) - Static flow charts")
            elif file.endswith('.html') and 'interactive' in file:
                print(f"   🌐 {file} ({size_mb:.1f}MB) - Interactive flow map")
            elif file.endswith('.html') and 'branching' in file:
                print(f"   📈 {file} ({size_mb:.1f}MB) - Branching analysis")
            elif file.endswith('.html') and 'index' in file:
                print(f"   🏠 {file} - Main report page")
            elif file.endswith('.json'):
                print(f"   📄 {file} ({size_mb:.1f}MB) - Raw flow data")
            else:
                print(f"   📁 {file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during visualization: {e}")
        import traceback
        traceback.print_exc()
        return False

def demonstrate_individual_features():
    """Demonstrate individual visualization features."""
    print("\n🎨 Demonstrating Individual Features")
    print("=" * 60)
    
    test_vn_path = "T:/AG/Savior-0.16c-pc/game"
    
    if not os.path.exists(test_vn_path):
        print("❌ Test VN not found.")
        return
    
    # Create project and visualizer
    project = RenpyProject(test_vn_path)
    project.analyze()
    
    visualizer = FlowGraphVisualizer(project)
    
    print(f"📊 Flow Analysis Summary:")
    print(f"   🏷️ Total Labels: {visualizer.flow_data.get('total_labels', 0)}")
    print(f"   🌊 Total Flows: {visualizer.flow_data.get('total_flows', 0):,}")
    print(f"   🎯 Reachability: {visualizer.flow_data.get('reachability_ratio', 0):.1%}")
    print(f"   ⭐ Quality Score: {project.get_scene_connectivity().get('narrative_flow_quality', {}).get('overall_score', 0):.0f}/100")
    
    # Generate individual visualizations
    output_dir = "individual_demos"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n🖼️ Generating individual visualizations...")
    
    # 1. Summary visualization
    summary_path = visualizer.generate_summary_visualization(
        os.path.join(output_dir, "summary_demo.png")
    )
    
    # 2. Interactive flow map
    interactive_path = visualizer.generate_interactive_flow_map(
        os.path.join(output_dir, "interactive_demo.html"),
        max_nodes=50  # Smaller for demo
    )
    
    print(f"✅ Individual demos generated in: {output_dir}")

if __name__ == "__main__":
    print("🎮 Flow Graph Visualization Test Suite")
    print("=" * 70)
    
    # Test 1: Full visualization
    success = test_flow_visualization()
    
    if success:
        print("\n" + "=" * 70)
        print("🎉 FLOW VISUALIZATION TESTS PASSED!")
        print("=" * 70)
        
        # Test 2: Individual features  
        demonstrate_individual_features()
        
        print("\n🌟 Phase 3.1A: Graph Visualization Engine - COMPLETE!")
        print("\n📋 What we've achieved:")
        print("   ✅ NetworkX graph conversion")
        print("   ✅ Static flow charts (matplotlib)")
        print("   ✅ Interactive flow maps (plotly)")  
        print("   ✅ Branching complexity analysis")
        print("   ✅ HTML report generation")
        print("   ✅ JSON data export")
        print("   ✅ Comprehensive visualization suite")
        
        print("\n🚀 Ready for Phase 3.1B: Enhanced Metrics!")
    else:
        print("\n❌ Tests failed. Check the error messages above.") 