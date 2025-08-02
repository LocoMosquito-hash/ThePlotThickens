#!/usr/bin/env python3
"""
Debug Hierarchy Method
======================

Test the _create_hierarchy_connections method directly to see if there are exceptions.
"""

import sys
import os

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_hierarchy_method():
    """Test the hierarchy connections method directly."""
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    if not os.path.exists(project_path):
        print(f"ERROR: Project path not found: {project_path}")
        return
    
    print("Testing hierarchy connections method...")
    print("=" * 50)
    
    try:
        from renpy_data_adapter import RenpyFlowDataAdapter
        
        # Load the project
        adapter = RenpyFlowDataAdapter()
        
        # Monkey patch the method to add debugging
        original_method = adapter._create_hierarchy_connections
        
        def debug_hierarchy_method(flow_graph, container_nodes, choice_connections):
            print(f"🔄 DEBUG: _create_hierarchy_connections called")
            print(f"🔄 DEBUG: container_nodes count: {len(container_nodes)}")
            print(f"🔄 DEBUG: choice_connections count before: {len(choice_connections)}")
            
            try:
                # Call original method
                result = original_method(flow_graph, container_nodes, choice_connections)
                print(f"🔄 DEBUG: choice_connections count after: {len(choice_connections)}")
                print(f"✅ DEBUG: Method completed successfully")
                return result
            except Exception as e:
                print(f"❌ DEBUG: Exception in hierarchy method: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        # Replace the method
        adapter._create_hierarchy_connections = debug_hierarchy_method
        
        print("🔄 Starting project analysis...")
        visualization_data = adapter.analyze_project(project_path)
        
        print(f"✅ Analysis complete")
        print(f"   Nodes: {len(visualization_data.nodes)}")
        print(f"   Connections: {len(visualization_data.connections)}")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_hierarchy_method() 