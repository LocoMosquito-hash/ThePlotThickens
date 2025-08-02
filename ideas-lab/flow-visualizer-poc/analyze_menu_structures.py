#!/usr/bin/env python3
"""
Direct Menu Structure Analysis
=============================

This script directly examines MenuStructure objects to understand
how label menus are detected and what data is available.
"""

import sys
import os
from pathlib import Path

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Import directly from the parser
try:
    from app.renpy_source_api.control_flow.analyze_vn_menus import MenuAnalyzer
    from app.renpy_source_api.parser import RenpyParser
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def analyze_sisterly_lust_menus():
    """Analyze menu structures in the SisterlyLust game."""
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    print("🔍 DIRECT MENU STRUCTURE ANALYSIS")
    print("=" * 50)
    print(f"Project: {project_path}")
    print()
    
    # Use MenuAnalyzer directly
    analyzer = MenuAnalyzer()
    
    # Look specifically at day02.rpy
    day02_file = Path(project_path) / "day02.rpy"
    if not day02_file.exists():
        print(f"❌ day02.rpy not found at {day02_file}")
        return
    
    print(f"📄 Analyzing: {day02_file}")
    print()
    
    try:
        # Use the MenuAnalyzer to get menu data
        menu_data = analyzer._analyze_file_menus(day02_file)
        menus = menu_data.get('menus', [])
        
        print(f"📋 Found {len(menus)} menus in day02.rpy")
        print()
        
        label_menus = []
        regular_menus = []
        target_menu = None
        
        for i, menu in enumerate(menus):
            print(f"🎯 Menu {i+1}:")
            print(f"   Label Name: {menu.label_name}")
            print(f"   Label Context: {menu.label_context}")
            print(f"   Line: {menu.line_number}")
            print(f"   Prompt: {menu.prompt}")
            print(f"   Choices: {len(menu.choices)}")
            print(f"   Nesting Level: {menu.nesting_level}")
            print(f"   Has Conditions: {menu.has_conditions}")
            
            # Categorize menus
            if menu.label_name:
                label_menus.append(menu)
                print(f"   🏷️ TYPE: Label Menu")
                
                # Check if this is our target
                if menu.label_name == "day02_living_room_conversation":
                    target_menu = menu
                    print(f"   🎯 TARGET FOUND!")
            else:
                regular_menus.append(menu)
                print(f"   📄 TYPE: Regular Menu")
            
            # Show choices
            for j, choice in enumerate(menu.choices):
                print(f"     Choice {j+1}: '{choice.text}'")
                print(f"       Condition: {choice.condition}")
                print(f"       Destination: {choice.destination}")
                print(f"       Action Type: {choice.action_type}")
                print(f"       Nested Labels: {choice.nested_labels}")
            
            print()
        
        print(f"📊 SUMMARY:")
        print(f"   Total menus: {len(menus)}")
        print(f"   Label menus: {len(label_menus)}")
        print(f"   Regular menus: {len(regular_menus)}")
        print()
        
        if target_menu:
            print(f"🎯 TARGET MENU ANALYSIS:")
            print(f"   Name: {target_menu.label_name}")
            print(f"   Context: {target_menu.label_context}")
            print(f"   Line: {target_menu.line_number}")
            print(f"   Choices: {len(target_menu.choices)}")
            print()
            
            print(f"   Choice Details:")
            for i, choice in enumerate(target_menu.choices):
                print(f"     {i+1}. '{choice.text}'")
                print(f"        Destination: {choice.destination}")
                print(f"        Nested Labels: {choice.nested_labels}")
        else:
            print(f"❌ Target menu 'day02_living_room_conversation' not found")
        
        # Look for the "Go to the living room" choice
        print(f"\n🔍 SEARCHING FOR 'Go to the living room' CHOICE:")
        for menu in menus:
            for choice in menu.choices:
                if "living room" in choice.text.lower():
                    print(f"   Found in menu: {menu.label_name or menu.label_context}")
                    print(f"   Choice: '{choice.text}'")
                    print(f"   Condition: {choice.condition}")
                    print(f"   Destination: {choice.destination}")
                    print(f"   Nested Labels: {choice.nested_labels}")
                    print()
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_sisterly_lust_menus() 