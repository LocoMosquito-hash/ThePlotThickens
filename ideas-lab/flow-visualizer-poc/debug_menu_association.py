#!/usr/bin/env python3
"""
Debug Menu Association
======================

This script debugs why day02_p_room_choices label menu
is not being associated with day02_l_conversation.
"""

import sys
import os

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def debug_menu_association():
    """Debug menu association for day02_p_room_choices."""
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    if not os.path.exists(project_path):
        print(f"ERROR: Project path not found: {project_path}")
        return
    
    print(f"🔍 Debugging menu association for: {project_path}")
    print("=" * 60)
    
    try:
        # Import the menu analyzer
        sys.path.insert(0, os.path.join(project_root, "app", "renpy-source-api"))
        from control_flow.analyze_vn_menus import MenuAnalyzer
        
        analyzer = MenuAnalyzer()
        
        print("\n📊 STEP 1: Raw menu analysis...")
        menu_analysis = analyzer.analyze_vn_menus(project_path)
        menus = menu_analysis.get('menu_structures', [])  # Fix: Use menu_structures instead of menus
        
        print(f"Total menus found: {len(menus)}")
        print(f"Menu analysis keys: {list(menu_analysis.keys())}")  # Debug: Show what keys are available
        
        # Look for any menu related to day02_p_room_choices
        target_menus = []
        for menu in menus:
            # Check if the menu name contains our target
            if 'day02_p_room_choices' in (menu.label_name or ''):
                target_menus.append(menu)
                print(f"\n🎯 FOUND TARGET MENU BY LABEL_NAME:")
                print(f"   Label name: {menu.label_name}")
                print(f"   Label context: {menu.label_context}")
                print(f"   Nesting level: {menu.nesting_level}")
                print(f"   File: {menu.file_path}")
                print(f"   Line: {menu.line_number}")
            
            # Also check if it's in the label context
            if 'day02_p_room_choices' in (menu.label_context or ''):
                print(f"\n🎯 FOUND TARGET MENU BY LABEL_CONTEXT:")
                print(f"   Label name: {menu.label_name}")
                print(f"   Label context: {menu.label_context}")
                print(f"   Nesting level: {menu.nesting_level}")
        
        # Look for menus with day02_l_conversation context
        day02_l_menus = []
        for menu in menus:
            if menu.label_context == 'day02_l_conversation':
                day02_l_menus.append(menu)
        
        print(f"\n📋 Menus with day02_l_conversation context: {len(day02_l_menus)}")
        for i, menu in enumerate(day02_l_menus):
            print(f"   Menu {i}: label_name='{menu.label_name}', nesting={menu.nesting_level}")
        
        # Now check if day02_p_room_choices appears anywhere
        print(f"\n🔍 Searching for 'day02_p_room_choices' in all menus...")
        found_any = False
        for menu in menus:
            if 'day02_p_room_choices' in str(menu.label_name) or 'day02_p_room_choices' in str(menu.label_context):
                found_any = True
                print(f"   FOUND: label_name='{menu.label_name}', label_context='{menu.label_context}'")
        
        if not found_any:
            print("   ❌ day02_p_room_choices NOT FOUND in any menu!")
            
            # Let's check if it's detected as a nested menu but not recorded
            print(f"\n🔍 Let's examine the day02.rpy file directly...")
            day02_file = os.path.join(project_path, "day02.rpy")
            if os.path.exists(day02_file):
                with open(day02_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Look for the actual menu statement
                for i, line in enumerate(lines):
                    if 'menu day02_p_room_choices' in line:
                        print(f"   📍 FOUND at line {i+1}: {line.strip()}")
                        
                        # Show context around it
                        start = max(0, i-5)
                        end = min(len(lines), i+10)
                        print(f"   Context around line {i+1}:")
                        for j in range(start, end):
                            marker = " >>> " if j == i else "     "
                            print(f"   {marker}{j+1:4d}: {lines[j].rstrip()}")
        
        print(f"\n✅ Debug complete!")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_menu_association() 