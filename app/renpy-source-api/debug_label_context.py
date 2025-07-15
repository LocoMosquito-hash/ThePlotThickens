"""
Debug script to check why label context isn't being set in menu parsing.
"""

import os
import re
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from parser import RenpyParser
except ImportError:
    print("❌ Could not import RenpyParser")
    sys.exit(1)


def debug_label_context():
    """Debug the label context issue in menu parsing."""
    print("🐛 Debugging Label Context Issue")
    print("="*50)
    
    # VN file path
    vn_path = r"T:\AG\MySisterMyRoommateV1.69-pc\game"
    parser = RenpyParser()
    
    print("🔍 Testing find_all_menus method...")
    try:
        menus = parser.find_all_menus(vn_path)
        print(f"✅ Found {len(menus)} total menus")
        
        # Look for our specific menu
        ch4_menus = [menu for menu in menus if 
                    menu.file_path.endswith('script.rpy') and 
                    any('Fashion' in choice.text for choice in menu.choices)]
        
        print(f"📋 Found {len(ch4_menus)} ch4ashbagdone-style menus:")
        for i, menu in enumerate(ch4_menus):
            print(f"  Menu {i+1}:")
            print(f"    File: {os.path.basename(menu.file_path)}")
            print(f"    Line: {menu.line_number}")
            print(f"    Label context: {menu.label_context}")
            print(f"    Choices: {[choice.text for choice in menu.choices]}")
            print()
    
    except Exception as e:
        print(f"❌ Error in find_all_menus: {e}")
    
    print("🔍 Manual file parsing test...")
    
    # Find the script.rpy file
    script_file = None
    for root, dirs, files in os.walk(vn_path):
        for file in files:
            if file == 'script.rpy':
                script_file = os.path.join(root, file)
                break
        if script_file:
            break
    
    if not script_file:
        print("❌ Could not find script.rpy")
        return
    
    print(f"📄 Reading: {script_file}")
    
    try:
        with open(script_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(script_file, 'r', encoding='latin-1') as f:
            lines = f.readlines()
    
    current_label = None
    found_ch4ashbagdone = False
    menu_line = None
    
    for line_num, line in enumerate(lines, 1):
        stripped_line = line.strip()
        
        # Track labels
        label_match = parser.patterns['label'].match(line)
        if label_match:
            label_name = label_match.group(1)
            current_label = label_name
            if label_name == 'ch4ashbagdone':
                found_ch4ashbagdone = True
                print(f"🎯 Found ch4ashbagdone at line {line_num}")
                print(f"    Current label context: {current_label}")
        
        # Track menus
        if (parser.patterns['menu'].match(line) or 
            parser.patterns['menu_with_name'].match(line)):
            
            if found_ch4ashbagdone and not menu_line:
                menu_line = line_num
                print(f"🎯 Found menu at line {line_num}")
                print(f"    Current label context: {current_label}")
                print(f"    Menu line: '{stripped_line}'")
                
                # Check the next few lines for choices
                print("    Following lines:")
                for i in range(5):
                    if line_num + i < len(lines):
                        next_line = lines[line_num + i].strip()
                        if next_line:
                            choice_match = parser.patterns['menu_choice'].match(lines[line_num + i])
                            print(f"      {line_num + i + 1}: '{next_line}' {'(CHOICE)' if choice_match else ''}")
                break
    
    print(f"\n🎯 Summary:")
    print(f"    Found ch4ashbagdone: {found_ch4ashbagdone}")
    print(f"    Found menu in context: {menu_line is not None}")
    print(f"    Final current_label: {current_label}")


if __name__ == "__main__":
    debug_label_context() 