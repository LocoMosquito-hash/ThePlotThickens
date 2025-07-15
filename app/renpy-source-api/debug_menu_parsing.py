#!/usr/bin/env python3
"""
Debug script to investigate menu parsing issues with ch4ashbagdone.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from parser import RenpyParser

def test_exact_ch4ashbagdone():
    """Test with the exact content provided by the user."""
    print("🔍 Testing exact ch4ashbagdone content...")
    
    # Exact content from the user's attachment
    test_content = '''    label ch4ashbagdone:

    scene ch4ashbeach5

    A "Thank you so much for watching my things!"

    T "No problem!"

    T "I was happy to do it..."

    "I need to think of something to bring up to keep the conversation going..."

    menu:

        "Fashion" :
            jump ch4ashfashion

        "Drinking" :
            jump ch4ashdrink

        "Animals" :
            jump ch4ashanimal

        "Vegetables" :
            jump ch4ashveg'''
    
    print("📄 Original content:")
    print(repr(test_content))
    
    # Write to file and test parsing
    test_file = "debug_ch4ashbagdone.rpy"
    try:
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        parser = RenpyParser()
        
        # Test 1: Check if our patterns detect the menu line
        print("\n🔍 Step 1: Pattern matching test")
        lines = test_content.split('\n')
        for i, line in enumerate(lines):
            if 'menu' in line.lower():
                print(f"  Line {i+1}: '{line.strip()}'")
                menu_match = parser.patterns['menu'].match(line)
                menu_with_name_match = parser.patterns['menu_with_name'].match(line)
                print(f"    Basic menu pattern match: {bool(menu_match)}")
                print(f"    Named menu pattern match: {bool(menu_with_name_match)}")
        
        # Test 2: Test find_all_menus method
        print("\n🔍 Step 2: find_all_menus test")
        # Create a mini project structure
        test_dir = "debug_project"
        os.makedirs(test_dir, exist_ok=True)
        test_project_file = os.path.join(test_dir, "script.rpy")
        with open(test_project_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        menus = parser.find_all_menus(test_dir)
        print(f"  Found {len(menus)} menus")
        
        for i, menu in enumerate(menus):
            print(f"  Menu {i+1}:")
            print(f"    File: {menu.file_path}")
            print(f"    Line: {menu.line_number}")
            print(f"    Label context: {menu.label_context}")
            print(f"    Total choices: {menu.total_choices}")
            print(f"    Choices: {[choice.text for choice in menu.choices]}")
        
        # Test 3: Manual menu structure parsing
        print("\n🔍 Step 3: Manual menu parsing test")
        lines = test_content.split('\n')
        menu_line_num = None
        for i, line in enumerate(lines):
            if parser.patterns['menu'].match(line.strip()):
                menu_line_num = i + 1
                break
        
        if menu_line_num:
            print(f"  Menu found at line {menu_line_num}")
            menu_structure = parser.parse_menu_structure(test_file, menu_line_num, lines)
            print(f"  Parsed menu structure:")
            print(f"    Label context: {menu_structure.label_context}")
            print(f"    Total choices: {menu_structure.total_choices}")
            print(f"    Choice details:")
            for j, choice in enumerate(menu_structure.choices):
                print(f"      {j+1}. '{choice.text}' -> {choice.destination} ({choice.action_type})")
        else:
            print("  ❌ No menu line found!")
        
        # Test 4: Check individual choice parsing
        print("\n🔍 Step 4: Individual choice parsing test")
        choice_lines = [
            '        "Fashion" :',
            '            jump ch4ashfashion',
            '        "Drinking" :',
            '            jump ch4ashdrink',
        ]
        
        for line in choice_lines:
            choice_match = parser.patterns['menu_choice'].match(line)
            print(f"  Line: '{line.strip()}'")
            print(f"    Choice pattern match: {bool(choice_match)}")
            if choice_match:
                print(f"    Captured text: '{choice_match.group(1)}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during debug: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
        if os.path.exists(test_project_file):
            os.remove(test_project_file)
        if os.path.exists(test_dir):
            os.rmdir(test_dir)

def test_regex_patterns():
    """Test our regex patterns directly."""
    print("\n🔧 Testing regex patterns...")
    
    parser = RenpyParser()
    
    test_cases = [
        ("menu:", "Basic menu"),
        ("    menu:", "Indented menu"),
        ("menu ch4_menu:", "Named menu"),
        ('        "Fashion" :', "Choice line"),
        ('        "Fashion":  ', "Choice with extra spaces"),
        ('        "Buy expensive item" if player_money >= 100:', "Conditional choice"),
        ("            jump ch4ashfashion", "Jump action"),
        ("label ch4ashbagdone:", "Label definition"),
    ]
    
    patterns_to_test = [
        ('menu', 'menu'),
        ('menu_with_name', 'menu_with_name'),
        ('menu_choice', 'menu_choice'),
        ('choice_with_condition', 'choice_with_condition'),
        ('choice_jump', 'choice_jump'),
        ('label', 'label'),
    ]
    
    for test_input, description in test_cases:
        print(f"\n  Testing: {description}")
        print(f"    Input: '{test_input}'")
        
        for pattern_name, pattern_key in patterns_to_test:
            if pattern_key in parser.patterns:
                match = parser.patterns[pattern_key].match(test_input)
                if match:
                    print(f"    ✅ {pattern_name}: {match.groups()}")

def main():
    print("🐛 Debugging Menu Parsing Issues")
    print("=" * 50)
    
    test_exact_ch4ashbagdone()
    test_regex_patterns()
    
    print("\n" + "=" * 50)
    print("🎯 Debug complete. Check the output above to identify parsing issues.")

if __name__ == "__main__":
    main() 