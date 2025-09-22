#!/usr/bin/env python3

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'renpy-source-api'))
from parser import RenpyParser

def debug_choice_destinations():
    """Debug missing outgoing edges for specific choices in chloesee."""
    
    script_path = r"T:\AG\sixteenyearslaternb-episode5.3-pc\game\script.rpy"
    
    parser = RenpyParser()
    
    try:
        # Read the file
        with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.splitlines()
        
        # Find chloesee label
        chloesee_line = None
        for i, line in enumerate(lines):
            if line.strip().startswith('label chloesee'):
                chloesee_line = i + 1  # Convert to 1-based
                break
        
        if not chloesee_line:
            print("Could not find chloesee label")
            return
        
        print(f"Found chloesee at line {chloesee_line}")
        
        # Parse all menus in chloesee and examine the problematic choices
        menus = parser.find_all_menus(script_path)
        chloesee_menus = [m for m in menus if m.label_context == 'chloesee']
        
        print(f"Found {len(chloesee_menus)} menus in chloesee label")
        
        for i, menu in enumerate(chloesee_menus):
            print(f"\n=== MENU {i+1} at line {menu.line_number} ===")
            print(f"Menu has {len(menu.choices)} choices:")
            
            for j, choice in enumerate(menu.choices):
                print(f"  {j+1}. '{choice.text}' (line {choice.line_number})")
                print(f"      Action: {choice.action_type}")
                print(f"      Destination: {choice.destination}")
                
                # Check for the specific problematic choices
                if "Let's not talk about [chloe] now." in choice.text:
                    print(f"      *** FOUND PROBLEMATIC CHOICE 1 ***")
                    print(f"      Should have destinations: tourhome AND poolvisit")
                    
                    # Show the content of this choice to understand the conditional logic
                    print(f"      Subsequent lines:")
                    for line in choice.subsequent_lines:
                        print(f"        {line}")
                    
                    # Show actual script content around this choice
                    print(f"\n      Script context around line {choice.line_number}:")
                    start_line = max(0, choice.line_number - 5)
                    end_line = min(len(lines), choice.line_number + 20)
                    for line_num in range(start_line, end_line):
                        marker = ">>> " if line_num + 1 == choice.line_number else "    "
                        print(f"      {marker}{line_num + 1:4d}: {lines[line_num]}")
                
                elif "She deserved it." in choice.text:
                    print(f"      *** FOUND PROBLEMATIC CHOICE 2 ***")
                    print(f"      Should have destinations: tourhome AND gameover")
                    
                    # Show the content of this choice to understand the conditional logic
                    print(f"      Subsequent lines:")
                    for line in choice.subsequent_lines:
                        print(f"        {line}")
                    
                    # Show actual script content around this choice
                    print(f"\n      Script context around line {choice.line_number}:")
                    start_line = max(0, choice.line_number - 5)
                    end_line = min(len(lines), choice.line_number + 30)
                    for line_num in range(start_line, end_line):
                        marker = ">>> " if line_num + 1 == choice.line_number else "    "
                        print(f"      {marker}{line_num + 1:4d}: {lines[line_num]}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_choice_destinations()
