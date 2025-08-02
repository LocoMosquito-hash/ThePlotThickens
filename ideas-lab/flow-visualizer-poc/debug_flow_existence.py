#!/usr/bin/env python3
"""
Debug Flow Existence
====================

Check if flows from day02_l_conversation to day02_p_room_choices exist.
"""

import sys
import os

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_flow_existence():
    """Check if specific flows exist."""
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    if not os.path.exists(project_path):
        print(f"ERROR: Project path not found: {project_path}")
        return
    
    print(f"DEBUG: Checking flow existence: day02_l_conversation -> day02_p_room_choices")
    print("=" * 70)
    
    try:
        from renpy_data_adapter import RenpyFlowDataAdapter
        
        adapter = RenpyFlowDataAdapter(use_hybrid=True)
        visualization_data = adapter.analyze_project(project_path)
        
        # Check if we can access the internal flow graph
        flow_graph = getattr(adapter, '_last_flow_graph', None)
        if not flow_graph:
            print("ERROR: No flow graph available")
            return
            
        print(f"Flow Graph: {len(flow_graph)} labels")
        
        # Check day02_l_conversation specifically
        if 'day02_l_conversation' in flow_graph:
            label_node = flow_graph['day02_l_conversation']
            print(f"FOUND day02_l_conversation")
            print(f"   Has outgoing_flows: {hasattr(label_node, 'outgoing_flows')}")
            
            if hasattr(label_node, 'outgoing_flows'):
                flows = label_node.outgoing_flows
                print(f"   Total outgoing flows: {len(flows)}")
                
                # Check flows to day02_p_room_choices
                target_flows = [f for f in flows if f.target_label == 'day02_p_room_choices']
                print(f"   Flows TO day02_p_room_choices: {len(target_flows)}")
                
                if target_flows:
                    print(f"FLOWS FOUND:")
                    for i, flow in enumerate(target_flows):
                        print(f"     Flow {i+1}: {flow.source_label} -> {flow.target_label}")
                        print(f"             Type: {flow.flow_type}")
                        print(f"             Context: {getattr(flow, 'context', 'None')}")
                else:
                    print(f"NO FLOWS TO day02_p_room_choices")
                    
                # Show first few flows to see what exists
                print(f"Sample outgoing flows (first 5):")
                for i, flow in enumerate(flows[:5]):
                    print(f"     {i+1}. {flow.source_label} -> {flow.target_label} ({flow.flow_type})")
                    
                # Check distribution of flow types
                flow_types = {}
                for flow in flows:
                    flow_type = flow.flow_type
                    if flow_type not in flow_types:
                        flow_types[flow_type] = 0
                    flow_types[flow_type] += 1
                    
                print(f"Flow types distribution: {flow_types}")
            else:
                print(f"   No outgoing_flows attribute")
        else:
            print("day02_l_conversation NOT found in flow graph")
            
        # Also check if day02_p_room_choices exists as a target anywhere
        print(f"Checking if day02_p_room_choices exists as flow target:")
        all_target_flows = []
        for label_name, label_node in flow_graph.items():
            if hasattr(label_node, 'outgoing_flows'):
                for flow in label_node.outgoing_flows:
                    if flow.target_label == 'day02_p_room_choices':
                        all_target_flows.append((label_name, flow))
                        
        print(f"   Total flows TO day02_p_room_choices from ANY source: {len(all_target_flows)}")
        for source_label, flow in all_target_flows:
            print(f"     {source_label} -> {flow.target_label} ({flow.flow_type})")
            
    except Exception as e:
        print(f"ERROR during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_flow_existence() 