#!/usr/bin/env python3
"""
Debug Source Parsing for Label Menus
===================================

This script examines the actual source code parsing to see why
flows from choices are not being detected correctly.
"""

import sys
import os

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def debug_source_parsing():
    """Debug source code parsing for day02_l_conversation."""
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    if not os.path.exists(project_path):
        print(f"ERROR: Project path not found: {project_path}")
        return
    
    # Find day02.rpy file
    day02_file = os.path.join(project_path, "day02.rpy")
    if not os.path.exists(day02_file):
        print(f"ERROR: day02.rpy not found at {day02_file}")
        return
    
    print(f"🔍 Examining source code in: {day02_file}")
    print("=" * 60)
    
    # Read the source file
    with open(day02_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the day02_l_conversation label
    in_conversation_label = False
    conversation_start = -1
    conversation_lines = []
    
    for i, line in enumerate(lines):
        if 'label day02_l_conversation:' in line:
            print(f"🎯 Found day02_l_conversation at line {i+1}")
            in_conversation_label = True
            conversation_start = i
            conversation_lines.append((i+1, line.rstrip()))
        elif in_conversation_label:
            # Check if we hit another label (end of current label)
            if line.strip().startswith('label ') and not line.strip().startswith('label day02_l_conversation'):
                print(f"📍 End of day02_l_conversation at line {i}")
                break
            conversation_lines.append((i+1, line.rstrip()))
    
    if not conversation_lines:
        print("❌ day02_l_conversation label not found in source")
        return
    
    print(f"\n📋 Content of day02_l_conversation ({len(conversation_lines)} lines):")
    print("-" * 50)
    
    # Look specifically for menu statements and choices that mention room_choices
    in_menu = False
    menu_depth = 0
    
    for line_num, line_content in conversation_lines:
        print(f"{line_num:4d}: {line_content}")
        
        # Track menu statements
        if 'menu:' in line_content or line_content.strip().startswith('menu '):
            in_menu = True
            menu_depth = 0
            print(f"     ┌─ MENU START")
        
        # Track choices in menus  
        if in_menu and '"' in line_content and ':' in line_content:
            # This looks like a menu choice
            choice_text = line_content.strip()
            print(f"     ├─ CHOICE: {choice_text}")
        
        # Look for jumps or calls
        if 'jump ' in line_content or 'call ' in line_content:
            target = line_content.strip()
            print(f"     └─ FLOW: {target}")
            
            if 'day02_p_room_choices' in target:
                print(f"     🎯 FOUND TARGET: {target}")
        
        # Track when we leave the menu
        if in_menu and line_content.strip() and not line_content.startswith('    ') and not line_content.startswith('\t'):
            if not ('menu' in line_content or '"' in line_content):
                in_menu = False
                print(f"     └─ MENU END")

if __name__ == "__main__":
    debug_source_parsing() 