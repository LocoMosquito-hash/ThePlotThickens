#!/usr/bin/env python3
"""
Test script to verify MenuAnalyzer on the specific ch1mckellycar file.
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Add renpy-source-api to path
app_dir = current_dir.parent.parent / "app"
sys.path.insert(0, str(app_dir / "renpy-source-api"))

# Import the menu analyzer
from control_flow.analyze_vn_menus import MenuAnalyzer

def test_specific_file():
    """Test MenuAnalyzer on the specific ch1mckellycar file."""
    
    print("🎯 TESTING SPECIFIC CH1MCKELLYCAR FILE")
    print("=" * 60)
    
    file_path = Path("T:/AG/LastCall-0.4-pc/game/chapters/chapter1/script/ch1s22mckellycar.rpy")
    
    print(f"📂 File path: {file_path}")
    print(f"   File exists: {file_path.exists()}")
    
    if not file_path.exists():
        print("❌ File not found!")
        return
        
    print(f"   File size: {file_path.stat().st_size} bytes")
    
    # Test MenuAnalyzer on this specific file
    analyzer = MenuAnalyzer()
    
    print(f"\n🔍 ANALYZING FILE WITH MenuAnalyzer:")
    print("-" * 40)
    
    file_analysis = analyzer._analyze_file_menus(file_path)
    
    print(f"📊 Analysis Results:")
    print(f"   Line count: {file_analysis['line_count']}")
    print(f"   Menus found: {len(file_analysis['menus'])}")
    
    if file_analysis['menus']:
        print(f"\n📋 MENU DETAILS:")
        for i, menu in enumerate(file_analysis['menus']):
            print(f"   Menu {i+1}:")
            print(f"     File: {menu.file_path}")
            print(f"     Line: {menu.line_number}")
            print(f"     Label context: {menu.label_context}")
            print(f"     Prompt: '{menu.prompt}'")
            print(f"     Choices: {len(menu.choices)}")
            
            for j, choice in enumerate(menu.choices):
                print(f"       Choice {j+1}: '{choice.text}'")
                print(f"         Destination: {choice.destination}")
                print(f"         Condition: {choice.condition}")
    else:
        print("❌ NO MENUS DETECTED")
        
    # Also test manual pattern matching
    print(f"\n🔧 MANUAL PATTERN TESTING:")
    print("-" * 40)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        current_label = None
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Track labels
            if line_stripped.startswith('label '):
                current_label = line_stripped.split()[1].rstrip(':')
                print(f"   📍 Line {i+1}: Found label '{current_label}'")
                
            # Track menus
            if 'menu:' in line:
                print(f"   🎯 Line {i+1}: Found menu in label '{current_label}'")
                print(f"       Line content: '{line_stripped}'")
                
                # Test regex pattern
                menu_match = analyzer.menu_patterns['menu_start'].match(line)
                if menu_match:
                    print(f"       ✅ Regex matches: {menu_match.groups()}")
                else:
                    print(f"       ❌ Regex doesn't match")
                    
                # Show next few lines (choices)
                for j in range(i+1, min(len(lines), i+5)):
                    choice_line = lines[j].strip()
                    if choice_line.startswith('"') and choice_line.endswith('":'):
                        print(f"       Choice at line {j+1}: {choice_line}")
                        
                        choice_match = analyzer.menu_patterns['choice'].match(lines[j])
                        if choice_match:
                            print(f"         ✅ Choice regex matches: {choice_match.groups()}")
                        else:
                            print(f"         ❌ Choice regex doesn't match")
                            
    except Exception as e:
        print(f"❌ Error reading file: {e}")

if __name__ == "__main__":
    test_specific_file() 