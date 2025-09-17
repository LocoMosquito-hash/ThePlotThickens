#!/usr/bin/env python3
"""
Test script to identify regex fragility issues in screen element parsing.
This will help us understand where our regex patterns are failing.
"""

import re
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "app" / "renpy-source-api"))

from parser import RenpyParser

def test_regex_patterns():
    """Test various screen element patterns to identify parsing issues."""
    
    parser = RenpyParser()
    
    # Test cases that represent different VN styles
    test_cases = [
        # Basic patterns (should work)
        {
            "name": "Basic textbutton",
            "content": 'textbutton "Click me" action Jump("destination")',
            "expected": ["Click me", "destination"]
        },
        {
            "name": "Basic imagebutton single line",
            "content": 'imagebutton idle "image.png" action Jump("dest")',
            "expected": ["dest"]
        },
        {
            "name": "Basic hotspot",
            "content": 'hotspot (100, 200, 50, 50) action Jump("target")',
            "expected": ["target"]
        },
        
        # Complex patterns that might be failing
        {
            "name": "Textbutton with styling (Apocalust style)",
            "content": 'textbutton "{image=chat_bubble_1.png} Do I seem different?" text_color "#EFEFEF" text_outlines [(1, "#808080", 0, 0)] action Jump("ep1_dial_kitchen_doiseem")',
            "expected": ["Do I seem different?", "ep1_dial_kitchen_doiseem"]
        },
        {
            "name": "Imagebutton with anchor (Amnesia style)",
            "content": 'imagebutton anchor (0.5, 0.5) idle "btn.png" hover "btn_h.png" action Jump("destination")',
            "expected": ["destination"]
        },
        {
            "name": "Hotspot with Call action (AoA Academy style)",
            "content": 'hotspot (35, 755, 290, 281) action Call("c1_aca_exp_corridor_exit")',
            "expected": ["c1_aca_exp_corridor_exit"]
        },
        {
            "name": "Single quotes in action",
            "content": "imagebutton idle 'image.png' action Jump('destination')",
            "expected": ["destination"]
        },
        {
            "name": "Mixed quotes",
            "content": 'imagebutton idle "image.png" action Jump(\'destination\')',
            "expected": ["destination"]
        },
        {
            "name": "Textbutton with complex text and Call",
            "content": 'textbutton "Leave." text_color "#EFEFEF" action Call("exit_scene")',
            "expected": ["Leave.", "exit_scene"]
        },
        
        # Multi-line patterns (these should fail with current regex)
        {
            "name": "Multi-line imagebutton (Amnesia style)",
            "content": [
                "imagebutton anchor (0.5, 0.5):",
                "    xoffset 1190 yoffset 190",
                "    idle \"gui/imageButtons/Eye BTN idle.png\"",
                "    hover \"gui/imageButtons/Eye BTN hover.png\"",
                "    action Jump('d1_1_10_1_Action_Face')",
                "    tooltip _(\"Face\")"
            ],
            "expected": ["d1_1_10_1_Action_Face"],
            "is_multiline": True
        },
        {
            "name": "Simple multi-line imagebutton",
            "content": [
                "imagebutton:",
                "    idle \"image.png\"",
                "    action Jump(\"target\")"
            ],
            "expected": ["target"],
            "is_multiline": True
        }
    ]
    
    print("🧪 Testing Regex Pattern Robustness")
    print("=" * 50)
    
    # Test single-line patterns
    print("\\n📝 Testing Single-Line Patterns:")
    for test_case in test_cases:
        if test_case.get("is_multiline"):
            continue
            
        print(f"\\n  Test: {test_case['name']}")
        print(f"  Content: {test_case['content']}")
        
        # Test textbutton pattern
        if "textbutton" in test_case['content']:
            match = parser.patterns['textbutton'].match(test_case['content'])
            if match:
                text = match.group(1)
                action_type = match.group(2) if len(match.groups()) >= 2 else "unknown"
                destination = match.group(3) if len(match.groups()) >= 3 else match.group(2)
                print(f"  ✅ Textbutton matched: '{text}' -> {destination} via {action_type}")
            else:
                print(f"  ❌ Textbutton pattern failed")
        
        # Test imagebutton pattern
        elif "imagebutton" in test_case['content']:
            match = parser.patterns['imagebutton'].match(test_case['content'])
            if match:
                destination = match.group(1)
                print(f"  ✅ Imagebutton matched: -> {destination}")
            else:
                print(f"  ❌ Imagebutton pattern failed")
        
        # Test hotspot pattern
        elif "hotspot" in test_case['content']:
            match = parser.patterns['hotspot'].match(test_case['content'])
            if match:
                coords = match.group(1)
                action_type = match.group(2)
                destination = match.group(3)
                print(f"  ✅ Hotspot matched: ({coords}) -> {destination} via {action_type}")
            else:
                print(f"  ❌ Hotspot pattern failed")
    
    # Test multi-line parsing logic
    print("\\n📝 Testing Multi-Line Patterns:")
    for test_case in test_cases:
        if not test_case.get("is_multiline"):
            continue
            
        print(f"\\n  Test: {test_case['name']}")
        lines = test_case['content']
        print(f"  Lines: {len(lines)}")
        
        # Simulate the multi-line parsing logic
        found_elements = []
        
        for i, line in enumerate(lines):
            if line.strip().startswith('imagebutton') and line.strip().endswith(':'):
                print(f"    Found imagebutton start at line {i}: {line.strip()}")
                
                # Look ahead for action
                for j in range(i + 1, min(i + 11, len(lines))):
                    future_line = lines[j].strip()
                    
                    # Test both quote types
                    action_jump_match = re.match(r'action\\s+Jump\\s*\\(\\s*[\"\\']([^\"\\']+)[\"\\']\\s*\\)', future_line, re.IGNORECASE)
                    action_call_match = re.match(r'action\\s+Call\\s*\\(\\s*[\"\\']([^\"\\']+)[\"\\']\\s*\\)', future_line, re.IGNORECASE)
                    
                    if action_jump_match:
                        destination = action_jump_match.group(1)
                        found_elements.append(f"{destination} via jump")
                        print(f"    ✅ Found action at line {j}: Jump -> {destination}")
                        break
                    elif action_call_match:
                        destination = action_call_match.group(1)
                        found_elements.append(f"{destination} via call")
                        print(f"    ✅ Found action at line {j}: Call -> {destination}")
                        break
                else:
                    print(f"    ❌ No action found in next 10 lines")
        
        if found_elements:
            print(f"  ✅ Multi-line parsing found: {found_elements}")
        else:
            print(f"  ❌ Multi-line parsing failed")
    
    print("\\n" + "=" * 50)
    print("🔍 Analysis Complete")

if __name__ == "__main__":
    test_regex_patterns()
