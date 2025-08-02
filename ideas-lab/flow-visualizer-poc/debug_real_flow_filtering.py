#!/usr/bin/env python3
"""
Debug Real Flow Filtering
=========================

This script examines the actual flow processing to understand why
day02_l_conversation flows to day02_p_room_choices aren't converted.
"""

import sys
import os

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_real_flow_filtering():
    """Debug actual flow filtering without patching."""
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    if not os.path.exists(project_path):
        print(f"ERROR: Project path not found: {project_path}")
        return
    
    print(f"🔍 Direct debugging of flow filtering")
    print("=" * 60)
    
    try:
        from renpy_data_adapter import RenpyFlowDataAdapter
        
        # Add debug prints directly to the _get_label_menu_names method
        adapter = RenpyFlowDataAdapter(use_hybrid=True)
        
        print(f"🚀 Running analysis...")
        visualization_data = adapter.analyze_project(project_path)
        
        # Check if we can access the internal flow graph
        flow_graph = getattr(adapter, '_last_flow_graph', None)
        if not flow_graph:
            print("ERROR: No flow graph available")
            return
            
        print(f"\n📊 Flow Graph Analysis:")
        print(f"   Labels in flow graph: {len(flow_graph)}")
        
        # Check day02_l_conversation specifically
        if 'day02_l_conversation' in flow_graph:
            label_node = flow_graph['day02_l_conversation']
            print(f"\n🎯 day02_l_conversation analysis:")
            print(f"   Has flows: {hasattr(label_node, 'outgoing_flows')}")
            
            if hasattr(label_node, 'outgoing_flows'):
                flows = label_node.outgoing_flows
                print(f"   Total outgoing flows: {len(flows)}")
                
                # Check flows to day02_p_room_choices
                target_flows = [f for f in flows if f.target_label == 'day02_p_room_choices']
                print(f"   Flows to day02_p_room_choices: {len(target_flows)}")
                
                for i, flow in enumerate(target_flows):
                    print(f"     Flow {i+1}: {flow.source_label} -> {flow.target_label} ({flow.flow_type})")
                    
                # Check ALL flows to see what types exist
                flow_types = {}
                for flow in flows:
                    flow_type = flow.flow_type
                    if flow_type not in flow_types:
                        flow_types[flow_type] = 0
                    flow_types[flow_type] += 1
                    
                print(f"   Flow types distribution: {flow_types}")
            else:
                print(f"   No outgoing_flows attribute")
        else:
            print("❌ day02_l_conversation NOT found in flow graph")
            
        # Now check the actual connections created
        print(f"\n📊 Connection Analysis:")
        day02_connections = [c for c in visualization_data.connections 
                           if 'day02' in c.source_node_id or 'day02' in c.target_node_id]
        
        print(f"   Total day02 connections: {len(day02_connections)}")
        
        # Look for any connections involving day02_l_conversation
        l_conv_connections = [c for c in visualization_data.connections 
                            if c.source_node_id == 'day02_l_conversation']
        
        print(f"   Connections FROM day02_l_conversation: {len(l_conv_connections)}")
        for conn in l_conv_connections[:10]:  # Show first 10
            print(f"     {conn.source_node_id} -> {conn.target_node_id} ({conn.connection_type})")
            
        # Look for any connections involving day02_p_room_choices
        p_room_connections = [c for c in visualization_data.connections 
                            if c.target_node_id == 'day02_p_room_choices']
        
        print(f"   Connections TO day02_p_room_choices: {len(p_room_connections)}")
        for conn in p_room_connections[:10]:  # Show first 10
            print(f"     {conn.source_node_id} -> {conn.target_node_id} ({conn.connection_type})")
            
        # Check if the _get_label_menu_names method is working
        print(f"\n🏷️  Testing _get_label_menu_names directly:")
        if hasattr(adapter, '_get_label_menu_names'):
            label_menu_names = adapter._get_label_menu_names(flow_graph)
            print(f"   Total label menus found: {len(label_menu_names)}")
            if 'day02_p_room_choices' in label_menu_names:
                print(f"   ✅ day02_p_room_choices IS in label_menu_names")
            else:
                print(f"   ❌ day02_p_room_choices NOT in label_menu_names")
                print(f"   Label menus: {list(label_menu_names)[:10]}...")
        else:
            print(f"   ❌ _get_label_menu_names method not found")
            
    except Exception as e:
        print(f"ERROR during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_real_flow_filtering() 