#!/usr/bin/env python3
"""
Test Script for Multiple Parent Label Menu Support
===============================================

This script tests whether label menus can properly handle multiple
incoming connections from different sources.
"""

import sys
import os
from pathlib import Path

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from renpy_data_adapter import RenpyFlowDataAdapter

def test_multiple_parents():
    """Test multiple parent connections for label menus."""
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    if not os.path.exists(project_path):
        print(f"ERROR: Project path not found: {project_path}")
        return
    
    print(f"🔍 Testing multiple parents for label menus...")
    print("=" * 60)
    
    # Use the existing data adapter
    adapter = RenpyFlowDataAdapter(use_hybrid=True)
    
    try:
        print(f"\n📊 Analyzing project with data adapter...")
        visualization_data = adapter.analyze_project(project_path)
        
        # Focus on label menus (goldish color)
        label_menus = [node for node in visualization_data.nodes 
                      if node.metadata.get('is_label_menu', False)]
        
        print(f"\n🎯 Found {len(label_menus)} label menus:")
        for menu in label_menus:
            print(f"   - {menu.node_id} (color: {menu.color_hint})")
        
        # Test case: day02_p_room_choices
        target_menu = "day02_p_room_choices"
        target_node = next((node for node in visualization_data.nodes 
                           if node.node_id == target_menu), None)
        
        if not target_node:
            print(f"\n❌ Target menu '{target_menu}' not found!")
            return
        
        print(f"\n🎯 Analyzing connections for: {target_menu}")
        print(f"   Display: {target_node.display_name}")
        print(f"   Color: {target_node.color_hint}")
        print(f"   Type: {target_node.node_type}")
        
        # Find all incoming connections to this label menu
        incoming_connections = [conn for conn in visualization_data.connections 
                               if conn.target_node_id == target_menu]
        
        print(f"\n📥 Incoming connections ({len(incoming_connections)}):")
        for conn in incoming_connections:
            source_node = next((node for node in visualization_data.nodes 
                               if node.node_id == conn.source_node_id), None)
            source_type = source_node.node_type if source_node else "unknown"
            print(f"   - FROM: {conn.source_node_id} ({source_type})")
            print(f"     Type: {conn.connection_type}")
            print(f"     Metadata: {conn.metadata}")
            print()
        
        # Check if there should be more connections
        print(f"\n🔍 Looking for potential missing connections...")
        
        # Search for any flows that mention this target in the flow graph
        # This requires accessing the internal flow graph data
        if hasattr(adapter, '_last_flow_graph'):
            flow_graph = adapter._last_flow_graph
            potential_sources = []
            
            for label_name, label_node in flow_graph.items():
                for flow in label_node.outgoing_flows:
                    if flow.target_label == target_menu:
                        potential_sources.append({
                            'source': label_name,
                            'flow_type': flow.flow_type,
                            'condition': getattr(flow, 'condition', None)
                        })
            
            print(f"🔍 Potential sources found in flow graph:")
            for source in potential_sources:
                print(f"   - {source['source']} (type: {source['flow_type']})")
                
            # Compare with actual connections
            actual_sources = {conn.source_node_id for conn in incoming_connections}
            flow_sources = {source['source'] for source in potential_sources}
            missing_sources = flow_sources - actual_sources
            
            if missing_sources:
                print(f"\n⚠️  Missing connections detected:")
                for missing in missing_sources:
                    print(f"   - {missing} -> {target_menu}")
            else:
                print(f"\n✅ All potential connections are present")
        
    except Exception as e:
        print(f"ERROR during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_multiple_parents() 