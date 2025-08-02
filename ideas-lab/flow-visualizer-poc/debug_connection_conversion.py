#!/usr/bin/env python3
"""
Debug Connection Conversion
============================

This script traces why flows from day02_l_conversation to day02_p_room_choices
aren't being converted to proper VisualizationConnections.
"""

import sys
import os

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_connection_conversion():
    """Debug connection conversion for day02_l_conversation -> day02_p_room_choices."""
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    if not os.path.exists(project_path):
        print(f"ERROR: Project path not found: {project_path}")
        return
    
    print(f"Debugging connection conversion for: {project_path}")
    print("=" * 60)
    
    try:
        from renpy_data_adapter import RenpyFlowDataAdapter
        
        # Create adapter
        adapter = RenpyFlowDataAdapter(use_hybrid=True)
        
        # Check if we can access the internal flow graph
        if hasattr(adapter, '_last_flow_graph'):
            print("Using stored flow graph...")
        else:
            print("Building fresh flow graph...")
            adapter.analyze_project(project_path)
            
        # Access the internal flow graph if available
        flow_graph = getattr(adapter, '_last_flow_graph', None)
        if not flow_graph:
            print("ERROR: No flow graph available")
            return
            
        print(f"Flow graph contains {len(flow_graph)} labels")
        
        # Check day02_l_conversation specifically
        if 'day02_l_conversation' in flow_graph:
            label_node = flow_graph['day02_l_conversation']
            print(f"\nday02_l_conversation flows:")
            
            flows = getattr(label_node, 'flows', [])
            print(f"  Total flows: {len(flows)}")
            
            target_flows = [f for f in flows if f.target_label == 'day02_p_room_choices']
            print(f"  Flows TO day02_p_room_choices: {len(target_flows)}")
            
            for i, flow in enumerate(target_flows):
                print(f"    Flow {i+1}:")
                print(f"      Source: {flow.source_label}")
                print(f"      Target: {flow.target_label}")
                print(f"      Type: {flow.flow_type}")
                print(f"      Context: {getattr(flow, 'context', 'None')}")
                print(f"      Source Type: {getattr(flow, 'source_type', 'None')}")
        else:
            print("day02_l_conversation not found in flow graph")
            
        # Now check what happens during connection conversion
        print(f"\n" + "="*60)
        print("TESTING CONNECTION CONVERSION")
        print("="*60)
        
        # Re-run the analysis to see connection filtering
        visualization_data = adapter.analyze_project(project_path)
        
        # Check connections TO day02_p_room_choices
        incoming_connections = [c for c in visualization_data.connections 
                              if c.target_node_id == "day02_p_room_choices"]
        
        print(f"\nConnections TO day02_p_room_choices: {len(incoming_connections)}")
        for conn in incoming_connections:
            print(f"  {conn.source_node_id} -> {conn.target_node_id} ({conn.connection_type})")
            
        # Check connections FROM day02_l_conversation
        outgoing_connections = [c for c in visualization_data.connections 
                               if c.source_node_id == "day02_l_conversation"]
        
        print(f"\nConnections FROM day02_l_conversation: {len(outgoing_connections)}")
        for conn in outgoing_connections:
            print(f"  {conn.source_node_id} -> {conn.target_node_id} ({conn.connection_type})")
            
        # Look for any connections containing both nodes
        related_connections = [c for c in visualization_data.connections 
                             if ('day02_l_conversation' in [c.source_node_id, c.target_node_id] or
                                 'day02_p_room_choices' in [c.source_node_id, c.target_node_id])]
        
        print(f"\nAll connections involving either node: {len(related_connections)}")
        for conn in related_connections:
            print(f"  {conn.source_node_id} -> {conn.target_node_id} ({conn.connection_type})")
            
    except Exception as e:
        print(f"ERROR during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_connection_conversion() 