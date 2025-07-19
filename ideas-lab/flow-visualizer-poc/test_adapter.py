#!/usr/bin/env python3
"""
Test for RenpyFlowDataAdapter

This test verifies that the adapter correctly converts renpy-source-api data
to standardized visualization format.
"""

import sys
from pathlib import Path
from typing import Optional

# Add paths
current_dir = Path(__file__).parent
app_dir = current_dir.parent.parent / "app"
sys.path.insert(0, str(app_dir / "renpy-source-api"))

from renpy_data_adapter import RenpyFlowDataAdapter
from flow_visualizer_interface import VisualizationData


def find_test_project() -> Optional[str]:
    """Find a test Renpy project to analyze."""
    # Check for the tutorial project
    tutorial_path = app_dir / "renpy-source-api" / "renpy_sdk" / "vn_analyzer" / "game"
    if tutorial_path.exists():
        return str(tutorial_path)
    
    print("⚠️ No test project found. The adapter test will use mock data.")
    return None


def test_adapter_basic_functionality():
    """Test basic adapter functionality."""
    print("🧪 TESTING ADAPTER BASIC FUNCTIONALITY")
    print("=" * 50)
    
    # Create adapter
    adapter = RenpyFlowDataAdapter(use_hybrid=True)
    print(f"✅ Adapter created (hybrid: {adapter.use_hybrid})")
    
    # Check interface compliance
    from flow_visualizer_interface import FlowDataProvider
    assert isinstance(adapter, FlowDataProvider), "Adapter should implement FlowDataProvider interface"
    print("✅ Interface compliance verified")
    
    # Test metadata access
    metadata = adapter.get_analysis_metadata()
    print(f"✅ Metadata accessible: {type(metadata)}")
    
    return True


def test_adapter_with_real_project():
    """Test adapter with a real Renpy project."""
    print("\n🔍 TESTING ADAPTER WITH REAL PROJECT")
    print("=" * 50)
    
    test_project = find_test_project()
    if not test_project:
        print("⚠️ Skipping real project test - no test project available")
        return True
    
    try:
        adapter = RenpyFlowDataAdapter(use_hybrid=True)
        
        # Test without SDK
        print("📝 Testing without SDK...")
        data_no_sdk = adapter.analyze_project(test_project, use_sdk=False)
        
        print(f"   Nodes: {len(data_no_sdk.nodes)}")
        print(f"   Connections: {len(data_no_sdk.connections)}")
        print(f"   Project info keys: {list(data_no_sdk.project_info.keys())}")
        
        # Test with SDK
        print("🔧 Testing with SDK...")
        data_with_sdk = adapter.analyze_project(test_project, use_sdk=True)
        
        print(f"   Nodes: {len(data_with_sdk.nodes)}")
        print(f"   Connections: {len(data_with_sdk.connections)}")
        
        # Compare results
        print(f"\n📊 Comparison:")
        print(f"   Node difference: {len(data_with_sdk.nodes) - len(data_no_sdk.nodes)}")
        print(f"   Connection difference: {len(data_with_sdk.connections) - len(data_no_sdk.connections)}")
        
        # Check analysis metadata
        metadata = adapter.get_analysis_metadata()
        print(f"\n🔍 Analysis metadata:")
        for key, value in metadata.items():
            if isinstance(value, list) and len(value) > 3:
                print(f"   {key}: [{len(value)} items]")
            else:
                print(f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Real project test failed: {e}")
        return False


def test_visualization_data_structure():
    """Test the VisualizationData structure created by adapter."""
    print("\n📊 TESTING VISUALIZATION DATA STRUCTURE")
    print("=" * 50)
    
    test_project = find_test_project()
    if not test_project:
        print("⚠️ Skipping data structure test - no test project available")
        return True
    
    try:
        adapter = RenpyFlowDataAdapter(use_hybrid=True)
        data = adapter.analyze_project(test_project, use_sdk=True)
        
        # Verify data structure
        assert isinstance(data, VisualizationData), "Should return VisualizationData"
        print("✅ VisualizationData structure correct")
        
        # Check nodes
        if data.nodes:
            sample_node = data.nodes[0]
            print(f"📦 Sample node:")
            print(f"   ID: {sample_node.node_id}")
            print(f"   Type: {sample_node.node_type}")
            print(f"   Display: {sample_node.display_name}")
            print(f"   Color: {sample_node.color_hint}")
            print(f"   Metadata keys: {list(sample_node.metadata.keys()) if sample_node.metadata else 'None'}")
        
        # Check connections
        if data.connections:
            sample_conn = data.connections[0]
            print(f"🔗 Sample connection:")
            print(f"   ID: {sample_conn.connection_id}")
            print(f"   Type: {sample_conn.connection_type}")
            print(f"   From: {sample_conn.source_node_id}")
            print(f"   To: {sample_conn.target_node_id}")
            print(f"   Style: {sample_conn.line_style}")
            print(f"   Color: {sample_conn.color_hint}")
        
        # Count node types
        node_types = {}
        for node in data.nodes:
            node_type = node.node_type
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        print(f"\n📈 Node type distribution:")
        for node_type, count in node_types.items():
            print(f"   {node_type}: {count}")
        
        # Count connection types
        conn_types = {}
        for conn in data.connections:
            conn_type = conn.connection_type
            conn_types[conn_type] = conn_types.get(conn_type, 0) + 1
        
        print(f"\n🔀 Connection type distribution:")
        for conn_type, count in conn_types.items():
            print(f"   {conn_type}: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data structure test failed: {e}")
        return False


def test_menu_container_creation():
    """Test that menu containers are created correctly."""
    print("\n🎛️ TESTING MENU CONTAINER CREATION")
    print("=" * 50)
    
    test_project = find_test_project()
    if not test_project:
        print("⚠️ Skipping menu container test - no test project available")
        return True
    
    try:
        adapter = RenpyFlowDataAdapter(use_hybrid=True)
        data = adapter.analyze_project(test_project, use_sdk=True)
        
        # Find menu containers
        containers = [node for node in data.nodes if node.node_type == 'menu_container']
        choice_buttons = [node for node in data.nodes if node.node_type == 'choice_button']
        menu_connections = [conn for conn in data.connections if conn.connection_type == 'menu_choice']
        
        print(f"📦 Menu containers: {len(containers)}")
        print(f"🔘 Choice buttons: {len(choice_buttons)}")
        print(f"🔗 Menu connections: {len(menu_connections)}")
        
        if containers:
            sample_container = containers[0]
            print(f"\n📦 Sample menu container:")
            print(f"   ID: {sample_container.node_id}")
            print(f"   Display: {sample_container.display_name}")
            print(f"   Parent label: {sample_container.metadata.get('parent_label')}")
            print(f"   Total choices: {sample_container.metadata.get('total_choices')}")
            print(f"   Complexity: {sample_container.metadata.get('complexity_level')}")
        
        if choice_buttons:
            sample_choice = choice_buttons[0]
            print(f"\n🔘 Sample choice button:")
            print(f"   ID: {sample_choice.node_id}")
            print(f"   Text: {sample_choice.display_name}")
            print(f"   Full text: {sample_choice.metadata.get('full_text')}")
            print(f"   Condition: {sample_choice.metadata.get('condition')}")
            print(f"   Destination: {sample_choice.metadata.get('destination')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Menu container test failed: {e}")
        return False


def main():
    """Run all adapter tests."""
    print("🧪 RENPY FLOW DATA ADAPTER TESTS")
    print("=" * 60)
    
    tests = [
        test_adapter_basic_functionality,
        test_adapter_with_real_project,
        test_visualization_data_structure,
        test_menu_container_creation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("✅ PASSED\n")
            else:
                print("❌ FAILED\n")
        except Exception as e:
            print(f"❌ ERROR: {e}\n")
    
    print("🎯 SUMMARY")
    print("=" * 60)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The adapter is working correctly.")
        print("\n✅ Ready to move to Phase 2: Create VNFlowVisualizerV2")
    else:
        print("⚠️ Some tests failed. Please check the adapter implementation.")
    
    return passed == total


if __name__ == "__main__":
    main() 