#!/usr/bin/env python3
"""
Debug Menu Flow Creation
========================

This script checks why flows from day02_l_conversation to day02_p_room_choices
aren't being created during the flow parsing stage.
"""

import sys
import os

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def debug_menu_flow_creation():
    """Debug menu flow creation specifically for day02_l_conversation."""
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    if not os.path.exists(project_path):
        print(f"ERROR: Project path not found: {project_path}")
        return
    
    print(f"🔍 Debugging menu flow creation for: {project_path}")
    print("=" * 60)
    
    try:
        # Import the parser
        sys.path.insert(0, os.path.join(project_root, "app", "renpy-source-api"))
        from parser import RenpyParser
        from control_flow.analyze_vn_menus import MenuAnalyzer
        
        parser = RenpyParser()
        
        print("\n📊 STEP 1: Analyzing menus...")
        
        # Get menu analysis
        analyzer = MenuAnalyzer()
        menu_analysis = analyzer.analyze_vn_menus(project_path)
        menus = menu_analysis.get('menu_structures', [])  # Fix: Use menu_structures instead of menus
        
        # Find day02_l_conversation menus
        day02_menus = []
        for menu in menus:
            if menu.label_context == 'day02_l_conversation':
                day02_menus.append(menu)
        
        print(f"Found {len(day02_menus)} menus in day02_l_conversation")
        
        # Examine each menu and its choices
        for i, menu in enumerate(day02_menus):
            print(f"\n🎯 MENU {i}: {menu.label_context}")
            print(f"   Label context: {menu.label_context}")
            print(f"   Number of choices: {len(menu.choices)}")
            
            for j, choice in enumerate(menu.choices):
                print(f"\n   📋 CHOICE {j}: '{choice.text[:50]}...'")
                print(f"      Destination: {choice.destination}")
                print(f"      Action type: {choice.action_type}")
                print(f"      Has condition: {choice.condition is not None}")
                
                # Check if this is our target choice
                if choice.destination == 'day02_p_room_choices':
                    print(f"      🎯 TARGET FOUND: This choice should create flow!")
                    print(f"         Source: {menu.label_context}")
                    print(f"         Target: {choice.destination}")
        
        print("\n📊 STEP 2: Creating flows...")
        
        # Now test flow creation
        flows = parser._find_explicit_flows(project_path)
        
        # Find flows from day02_l_conversation
        day02_flows = [f for f in flows if f.source_label == 'day02_l_conversation']
        
        print(f"Total flows created: {len(flows)}")
        print(f"Flows from day02_l_conversation: {len(day02_flows)}")
        
        # Look for our target flow
        target_flows = [f for f in day02_flows if f.target_label == 'day02_p_room_choices']
        
        print(f"Target flows (day02_l_conversation -> day02_p_room_choices): {len(target_flows)}")
        
        for flow in target_flows:
            print(f"   🎯 FLOW FOUND: {flow.source_label} -> {flow.target_label}")
            print(f"      Type: {flow.flow_type}")
            print(f"      Context: {flow.context}")
        
        if not target_flows:
            print("❌ TARGET FLOWS NOT CREATED!")
            
            # Debug why
            print("\n🔍 DEBUG: Checking menu choice destinations...")
            for menu in day02_menus:
                for choice in menu.choices:
                    if choice.destination:
                        print(f"   Choice '{choice.text[:30]}...' -> '{choice.destination}'")
        
        print(f"\n✅ Debug complete!")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_menu_flow_creation() 