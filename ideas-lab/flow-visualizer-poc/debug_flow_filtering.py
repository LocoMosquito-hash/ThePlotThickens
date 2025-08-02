#!/usr/bin/env python3
"""
Debug Flow Filtering for Label Menus
====================================

This script traces exactly why flows from day02_l_conversation to day02_p_room_choices
are still being filtered out despite our multiple parent fix.
"""

import sys
import os

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_flow_filtering():
    """Debug flow filtering for the specific day02 case."""
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    if not os.path.exists(project_path):
        print(f"ERROR: Project path not found: {project_path}")
        return
    
    print(f"🔍 Debugging flow filtering for: {project_path}")
    print("=" * 60)
    
    try:
        from renpy_data_adapter import RenpyFlowDataAdapter
        
        # Create adapter with fresh analysis
        adapter = RenpyFlowDataAdapter(use_hybrid=True)
        
        # Patch the flow conversion method to add debug output
        original_convert_flows = adapter._convert_flows_to_connections
        original_get_label_menu_names = adapter._get_label_menu_names
        
        def debug_get_label_menu_names(flow_graph):
            """Debug version of _get_label_menu_names."""
            print("\n🏷️  DEBUGGING _get_label_menu_names()")
            print("-" * 40)
            
            label_menu_names = set()
            for label_name, label_node in flow_graph.items():
                if hasattr(label_node, 'menu_nodes') and label_node.menu_nodes:
                    for menu_node in label_node.menu_nodes:
                        if menu_node.label_name:
                            label_menu_names.add(menu_node.label_name)
                            print(f"✅ Found label menu: {menu_node.label_name} (in {label_name})")
                            
            print(f"🎯 Total label menus found: {len(label_menu_names)}")
            if 'day02_p_room_choices' in label_menu_names:
                print(f"✅ day02_p_room_choices IS in label_menu_names")
            else:
                print(f"❌ day02_p_room_choices NOT in label_menu_names")
                print(f"📋 Label menus found: {list(label_menu_names)[:10]}...")
                
            return label_menu_names
        
        def debug_convert_flows_to_connections(flow_graph):
            """Debug version with detailed tracing."""
            print("\n🔄 DEBUGGING _convert_flows_to_connections()")
            print("-" * 40)
            
            # Get label menu names first
            label_menu_names = debug_get_label_menu_names(flow_graph)
            
            # Look for day02_l_conversation flows specifically
            if 'day02_l_conversation' in flow_graph:
                label_node = flow_graph['day02_l_conversation']
                print(f"\n🎯 Examining day02_l_conversation flows:")
                
                flows = getattr(label_node, 'outgoing_flows', [])
                print(f"   Total outgoing flows: {len(flows)}")
                
                target_flows = [f for f in flows if f.target_label == 'day02_p_room_choices']
                print(f"   Flows TO day02_p_room_choices: {len(target_flows)}")
                
                for i, flow in enumerate(target_flows):
                    print(f"\n   📍 Flow {i+1}:")
                    print(f"      Source: {flow.source_label}")
                    print(f"      Target: {flow.target_label}")
                    print(f"      Type: {flow.flow_type}")
                    print(f"      Context: {getattr(flow, 'context', 'None')}")
                    
                    # Test our filtering logic
                    if flow.flow_type == 'menu_choice':
                        if flow.target_label in label_menu_names:
                            print(f"      ✅ Would ALLOW: menu_choice to label menu")
                        else:
                            print(f"      ❌ Would FILTER: menu_choice but not label menu")
                    else:
                        print(f"      ✅ Would ALLOW: not menu_choice type")
            else:
                print("❌ day02_l_conversation not found in flow_graph")
            
            # Now call the original method and trace results
            print(f"\n📊 Calling original _convert_flows_to_connections...")
            connections = original_convert_flows(flow_graph)
            
            # Check results
            target_connections = [c for c in connections 
                                if c.source_node_id == 'day02_l_conversation' 
                                and c.target_node_id == 'day02_p_room_choices']
            
            print(f"\n🎯 RESULT: day02_l_conversation -> day02_p_room_choices connections: {len(target_connections)}")
            for conn in target_connections:
                print(f"   ✅ {conn.source_node_id} -> {conn.target_node_id} ({conn.connection_type})")
                
            return connections
        
        # Apply patches
        adapter._convert_flows_to_connections = debug_convert_flows_to_connections
        adapter._get_label_menu_names = debug_get_label_menu_names
        
        # Run analysis
        print(f"🚀 Starting analysis...")
        visualization_data = adapter.analyze_project(project_path)
        
        print(f"\n" + "="*60)
        print(f"📊 FINAL RESULTS")
        print(f"="*60)
        
        # Final check
        final_connections = [c for c in visualization_data.connections 
                           if c.source_node_id == 'day02_l_conversation' 
                           and c.target_node_id == 'day02_p_room_choices']
        
        print(f"🎯 Final connections day02_l_conversation -> day02_p_room_choices: {len(final_connections)}")
        
        if final_connections:
            print(f"✅ SUCCESS: Connections found!")
            for conn in final_connections:
                print(f"   {conn.source_node_id} -> {conn.target_node_id} ({conn.connection_type})")
        else:
            print(f"❌ FAILED: No connections found!")
            
            # Check if day02_p_room_choices exists at all
            day02_nodes = [n for n in visualization_data.nodes if 'day02_p_room_choices' in n.node_id]
            print(f"📋 day02_p_room_choices nodes found: {len(day02_nodes)}")
            for node in day02_nodes:
                print(f"   {node.node_id} ({node.node_type}) - color: {getattr(node, 'color_hint', 'None')}")
                
    except Exception as e:
        print(f"ERROR during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_flow_filtering() 