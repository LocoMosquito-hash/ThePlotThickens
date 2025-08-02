#!/usr/bin/env python3
"""
Test Jump Detection in Menu Choices
==================================

This script tests why jump statements inside menu choice blocks
are not being detected as flows by the parser.
"""

import sys
import os

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def test_jump_detection():
    """Test jump detection in day02_l_conversation."""
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    if not os.path.exists(project_path):
        print(f"ERROR: Project path not found: {project_path}")
        return
    
    print(f"🔍 Testing jump detection in day02_l_conversation")
    print("=" * 60)
    
    try:
        # Import the parser from the correct location
        sys.path.insert(0, os.path.join(project_root, "app", "renpy-source-api"))
        from parser import RenpyParser
        
        # Create parser instance
        parser = RenpyParser()
        
        # Parse the specific file
        day02_file = os.path.join(project_path, "day02.rpy")
        if not os.path.exists(day02_file):
            print(f"ERROR: day02.rpy not found")
            return
        
        print(f"📊 Parsing {day02_file}...")
        
        # Parse the file
        parser_result = parser.parse_file(day02_file)
        flow_graph = parser.build_flow_graph(project_path)
        
        # Look specifically at day02_l_conversation
        if 'day02_l_conversation' in flow_graph:
            label_node = flow_graph['day02_l_conversation']
            print(f"\n🎯 Found day02_l_conversation label:")
            print(f"   Has flows attribute: {hasattr(label_node, 'flows')}")
            
            if hasattr(label_node, 'flows'):
                print(f"   Number of flows: {len(label_node.flows)}")
                
                if label_node.flows:
                    print(f"   📋 Flows detected:")
                    for i, flow in enumerate(label_node.flows):
                        source = getattr(flow, 'source', 'N/A')
                        target = getattr(flow, 'target', 'N/A')
                        context = getattr(flow, 'context', 'N/A')
                        flow_type = getattr(flow, 'flow_type', 'N/A')
                        print(f"      {i+1}. {source} -> {target}")
                        print(f"         Context: {context}")
                        print(f"         Type: {flow_type}")
                else:
                    print(f"   ❌ NO FLOWS DETECTED")
                    print(f"   📋 Analyzing why...")
                    
                    # Check if the label has menu nodes with choices that should create flows
                    if hasattr(label_node, 'menu_nodes'):
                        print(f"   Menu nodes: {len(label_node.menu_nodes) if label_node.menu_nodes else 0}")
                        
                        if label_node.menu_nodes:
                            for menu_idx, menu_node in enumerate(label_node.menu_nodes):
                                print(f"   📋 Menu {menu_idx}:")
                                print(f"      Choices: {len(menu_node.choices) if hasattr(menu_node, 'choices') else 0}")
                                
                                if hasattr(menu_node, 'choices') and menu_node.choices:
                                    for choice_idx, choice in enumerate(menu_node.choices):
                                        destination = getattr(choice, 'destination', 'N/A')
                                        action_type = getattr(choice, 'action_type', 'N/A')
                                        content = getattr(choice, 'content', 'N/A')
                                        print(f"         Choice {choice_idx}: {content[:50]}...")
                                        print(f"            Destination: {destination}")
                                        print(f"            Action type: {action_type}")
                                        
                                        if 'day02_p_room_choices' in str(destination):
                                            print(f"            🎯 FOUND TARGET IN CHOICE!")
                    
            else:
                print(f"   ❌ No flows attribute")
        else:
            print(f"❌ day02_l_conversation not found in flow graph")
            print(f"📋 Available labels:")
            day02_labels = [name for name in flow_graph.keys() if 'day02' in name]
            for label in sorted(day02_labels[:10]):  # First 10
                print(f"   - {label}")
    
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_jump_detection() 