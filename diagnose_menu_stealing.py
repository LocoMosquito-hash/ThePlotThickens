#!/usr/bin/env python3
"""
Diagnose menu choice stealing issue in 16 years later game.
Specifically analyzing chloeskateboardrom label.
"""

import sys
from pathlib import Path

# Add the app/renpy-source-api directory to the path
app_dir = Path("app/renpy-source-api")
sys.path.insert(0, str(app_dir))

from renpy_sdk.ast_menu_parser import ASTMenuParser

def find_label_boundaries(file_path: str, target_label: str):
    """Find the start and end lines of a specific label."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        label_start = None
        label_end = len(lines)
        
        # Find the target label
        for i, line in enumerate(lines):
            if line.strip().startswith(f"label {target_label}"):
                label_start = i + 1  # 1-based line numbers
                print(f"🎯 Found label '{target_label}' at line {label_start}")
                break
        
        if label_start is None:
            return None, None
        
        # Find the next label to determine the end boundary
        for i in range(label_start, len(lines)):
            line = lines[i].strip()
            if line.startswith("label ") and not line.startswith(f"label {target_label}"):
                label_end = i + 1
                print(f"📍 Label '{target_label}' ends at line {label_end - 1}")
                break
        
        return label_start, label_end
        
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return None, None

def diagnose_menu_stealing():
    """Analyze the specific menu stealing issue."""
    
    print("🔍 DIAGNOSING MENU CHOICE STEALING")
    print("=" * 60)
    print("Game: 16 years later!")
    print("Label: chloeskateboardrom")
    print("File: romanceday05script2b_1.rpy")
    
    parser = ASTMenuParser()
    parser.has_ast = False  # Use enhanced regex parser
    
    file_path = r"T:\AG\sixteenyearslaternb-episode5.3-pc\game\romanceday05script2b_1.rpy"
    target_label = "chloeskateboardrom"
    
    try:
        print(f"\n📁 Analyzing file: {file_path}")
        
        # Find the boundaries of the target label
        label_start, label_end = find_label_boundaries(file_path, target_label)
        
        if label_start is None:
            print(f"❌ Could not find label '{target_label}' in the file")
            return
        
        print(f"🎯 Analyzing label '{target_label}' (lines {label_start}-{label_end})")
        
        # Parse all menus in the file
        all_menus = parser.parse_file_menus(file_path)
        
        # Filter menus that fall within the target label's boundaries
        label_menus = []
        for menu in all_menus:
            if label_start <= menu.line_number < label_end:
                label_menus.append(menu)
        
        print(f"✅ Found {len(all_menus)} total menus in file")
        print(f"🎯 Found {len(label_menus)} menus within '{target_label}' label")
        
        print("\n🔍 DETAILED MENU ANALYSIS:")
        print("-" * 40)
        
        if not label_menus:
            print("❌ No menus found within the target label boundaries")
            return
        
        for i, menu in enumerate(label_menus):
            print(f"\n📋 Menu {i+1}:")
            print(f"   📍 Line: {menu.line_number}")
            print(f"   🎯 Choices: {len(menu.choices)}")
            print(f"   🔀 Conditional paths: {menu.total_conditional_paths}")
            print(f"   🧠 Complexity: {menu.menu_complexity}")
            
            # Show all choices for this menu
            for j, choice in enumerate(menu.choices):
                choice_preview = choice.text[:60] + "..." if len(choice.text) > 60 else choice.text
                print(f"   ├─ Choice {j+1}: \"{choice_preview}\"")
                print(f"   │  ├─ Line: {choice.line_number}")
                print(f"   │  ├─ Conditional: {choice.is_conditional}")
                if choice.is_conditional:
                    print(f"   │  └─ Condition: {choice.primary_condition}")
                else:
                    print(f"   │  └─ Unconditional")
        
        # Look for patterns that might indicate choice stealing
        print("\n🚨 POTENTIAL ISSUES DETECTED:")
        print("-" * 40)
        
        issues_found = False
        
        # Check for menus with unusually high choice counts
        for i, menu in enumerate(label_menus):
            if len(menu.choices) > 5:  # Arbitrary threshold
                print(f"⚠️  Menu {i+1} (Line {menu.line_number}) has {len(menu.choices)} choices - potentially stealing from other menus")
                issues_found = True
        
        # Check for duplicate choices across menus within the label
        all_choices = []
        for i, menu in enumerate(label_menus):
            for j, choice in enumerate(menu.choices):
                all_choices.append((choice.text, i+1, menu.line_number))
        
        seen_choices = set()
        for choice_text, menu_num, line_num in all_choices:
            if choice_text in seen_choices:
                print(f"⚠️  Duplicate choice detected: \"{choice_text[:40]}...\" in Menu {menu_num} (Line {line_num})")
                issues_found = True
            seen_choices.add(choice_text)
        
        if not issues_found:
            print("✅ No obvious choice stealing patterns detected in parser output")
            print("   The issue might be in the flow visualizer's rendering logic")
        
        # Show specific menus mentioned by user
        print("\n🎯 SPECIFIC MENUS MENTIONED BY USER:")
        print("-" * 40)
        
        target_choices = [
            "You're very good.",
            "Tell me a bit about [felicia].",
            "What do you usually do in your free time?",
            "You are beautiful too.",
            "It's not stupid at all."
        ]
        
        for target in target_choices:
            found = False
            for i, menu in enumerate(label_menus):
                for j, choice in enumerate(menu.choices):
                    if target.lower() in choice.text.lower():
                        print(f"🎯 Found \"{target}\" in Menu {i+1} (Line {menu.line_number}) within '{target_label}' label")
                        found = True
                        break
            if not found:
                print(f"❌ Could not find choice: \"{target}\" within '{target_label}' label")
        
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        print("   Please verify the file path is correct")
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose_menu_stealing()
