#!/usr/bin/env python3
"""
Debug script to test MenuAnalyzer menu detection on Last Call game.
"""

import sys
import os
import re
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Add renpy-source-api to path
app_dir = current_dir.parent.parent / "app"
sys.path.insert(0, str(app_dir / "renpy-source-api"))

# Import the menu analyzer
from control_flow.analyze_vn_menus import MenuAnalyzer

def test_menu_patterns():
    """Test the menu patterns against known Last Call menu syntax."""
    
    print("🔍 TESTING MENU DETECTION PATTERNS")
    print("=" * 60)
    
    # Test the regex patterns directly
    analyzer = MenuAnalyzer()
    patterns = analyzer.menu_patterns
    
    # Test cases from Last Call ch1mckellycar
    test_lines = [
        "    menu:",                                    # Simple menu
        "        \"I'm sorry, I can't.\":",            # Choice 1
        "        \"You know what? I'd love to.\":",    # Choice 2
        "menu:",                                        # No indentation
        "menu somename:",                               # Named menu
        "    \"Choice text\":",                         # Simple choice
    ]
    
    print("📋 TESTING INDIVIDUAL PATTERNS:")
    print("-" * 40)
    
    for line in test_lines:
        print(f"Testing line: '{line}'")
        
        # Test menu_start pattern
        menu_match = patterns['menu_start'].match(line)
        if menu_match:
            print(f"  ✅ MENU MATCH: {menu_match.groups()}")
        else:
            print(f"  ❌ NO MENU MATCH")
            
        # Test choice pattern
        choice_match = patterns['choice'].match(line)
        if choice_match:
            print(f"  ✅ CHOICE MATCH: {choice_match.groups()}")
        else:
            print(f"  ❌ NO CHOICE MATCH")
        print()

def test_last_call_file():
    """Test MenuAnalyzer on actual Last Call files."""
    
    print("🎯 TESTING LAST CALL FILE ANALYSIS")
    print("=" * 60)
    
    game_path = "T:/AG/LastCall-0.4-pc/game"
    
    if not os.path.exists(game_path):
        print(f"❌ Game path not found: {game_path}")
        return
        
    analyzer = MenuAnalyzer()
    
    # Test the full project analysis
    print("📊 FULL PROJECT ANALYSIS:")
    analysis = analyzer.analyze_vn_menus(game_path)
    
    print(f"  Total files: {analysis.get('total_files', 0)}")
    print(f"  Total menus: {analysis.get('total_menus', 0)}")
    print(f"  Files with menus: {len(analysis.get('files_with_menus', []))}")
    
    if analysis.get('files_with_menus'):
        print("  Files containing menus:")
        for file_name, menu_count in analysis['files_with_menus']:
            print(f"    {file_name}: {menu_count} menus")
    
    # Check menu structures
    menu_structures = analysis.get('menu_structures', [])
    print(f"  Menu structures found: {len(menu_structures)}")
    
    for i, menu in enumerate(menu_structures):
        print(f"    Menu {i+1}:")
        print(f"      File: {menu.file_path}")
        print(f"      Line: {menu.line_number}")
        print(f"      Label context: {menu.label_context}")
        print(f"      Choices: {len(menu.choices)}")
        for j, choice in enumerate(menu.choices):
            print(f"        Choice {j+1}: '{choice.text}' → {choice.destination}")
            
def test_specific_file_content():
    """Test on the specific file content that should contain ch1mckellycar menu."""
    
    print("📄 TESTING SPECIFIC FILE CONTENT")
    print("=" * 60)
    
    # Find files that might contain ch1mckellycar
    game_path = Path("T:/AG/LastCall-0.4-pc/game")
    
    if not game_path.exists():
        print(f"❌ Game path not found: {game_path}")
        return
        
    # Search for files containing ch1mckellycar
    found_files = []
    for rpy_file in game_path.glob("*.rpy"):
        try:
            with open(rpy_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if 'ch1mckellycar' in content:
                    found_files.append(rpy_file)
        except:
            continue
            
    print(f"📁 Files containing 'ch1mckellycar': {len(found_files)}")
    
    for file_path in found_files:
        print(f"\n🔍 Analyzing file: {file_path.name}")
        
        analyzer = MenuAnalyzer()
        file_analysis = analyzer._analyze_file_menus(file_path)
        
        print(f"  Line count: {file_analysis['line_count']}")
        print(f"  Menus found: {len(file_analysis['menus'])}")
        
        # Also manually search for menu patterns
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            in_ch1mckellycar = False
            for i, line in enumerate(lines):
                if 'label ch1mckellycar:' in line:
                    in_ch1mckellycar = True
                    print(f"  📍 Found label ch1mckellycar at line {i+1}")
                elif in_ch1mckellycar and line.strip().startswith('label '):
                    in_ch1mckellycar = False
                elif in_ch1mckellycar and 'menu:' in line:
                    print(f"  🎯 Found menu at line {i+1}: '{line.strip()}'")
                    # Show surrounding context
                    start = max(0, i-2)
                    end = min(len(lines), i+10)
                    print(f"  📝 Context lines {start+1}-{end}:")
                    for j in range(start, end):
                        marker = " → " if j == i else "   "
                        print(f"  {marker}{j+1:3d}: {lines[j].rstrip()}")
                    break
        except Exception as e:
            print(f"  ❌ Error reading file: {e}")

if __name__ == "__main__":
    test_menu_patterns()
    print("\n" + "="*60 + "\n")
    test_last_call_file()
    print("\n" + "="*60 + "\n")
    test_specific_file_content() 