#!/usr/bin/env python3
"""
Debug Flow Detection for Label Menus
===================================

This script checks if flows to label menus are being detected
in the raw flow graph before any filtering.
"""

import sys
import os

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_flow_detection():
    """Debug flow detection for label menus."""
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    if not os.path.exists(project_path):
        print(f"ERROR: Project path not found: {project_path}")
        return
    
    print(f"🔍 Debugging flow detection for: {project_path}")
    print("=" * 60)
    
    from renpy_data_adapter import RenpyFlowDataAdapter
    
    adapter = RenpyFlowDataAdapter(use_hybrid=True)
    
    print(f"\n📊 Analyzing project...")
    visualization_data = adapter.analyze_project(project_path)
    
    # Access the stored flow graph
    if hasattr(adapter, '_last_flow_graph') and adapter._last_flow_graph:
        flow_graph = adapter._last_flow_graph
        print(f"✅ Flow graph available with {len(flow_graph)} labels")
        
        # Look for day02_l_conversation specifically
        if 'day02_l_conversation' in flow_graph:
            label_node = flow_graph['day02_l_conversation']
            print(f"\n🎯 Found day02_l_conversation label")
            print(f"   Outgoing flows: {len(label_node.flows) if hasattr(label_node, 'flows') else 'N/A'}")
            
            # Check for flows to day02_p_room_choices
            if hasattr(label_node, 'flows'):
                target_flows = []
                for flow in label_node.flows:
                    if hasattr(flow, 'target') and flow.target == 'day02_p_room_choices':
                        target_flows.append(flow)
                        print(f"   ✅ FOUND FLOW: {flow.source} -> {flow.target}")
                        print(f"      Context: {getattr(flow, 'context', 'N/A')}")
                        print(f"      Type: {getattr(flow, 'flow_type', 'N/A')}")
                
                if not target_flows:
                    print(f"   ❌ NO FLOWS to day02_p_room_choices found")
                    print(f"   📋 All outgoing flows:")
                    for i, flow in enumerate(label_node.flows):
                        target = getattr(flow, 'target', 'N/A')
                        context = getattr(flow, 'context', 'N/A')
                        print(f"      {i+1}. -> {target} (context: {context})")
                else:
                    print(f"   ✅ Found {len(target_flows)} flows to day02_p_room_choices")
        else:
            print(f"\n❌ day02_l_conversation label not found in flow graph")
            print(f"📋 Available day02 labels:")
            day02_labels = [name for name in flow_graph.keys() if 'day02' in name]
            for label in sorted(day02_labels):
                print(f"   - {label}")
    else:
        print(f"❌ Flow graph not available for debugging")

if __name__ == "__main__":
    debug_flow_detection() 