#!/usr/bin/env python3
"""
Debug script to investigate menu parsing issues.
"""

import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from flow_tracer import FlowTracer

def debug_menu_parsing():
    """Debug menu parsing to see what's happening."""
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="debug_menu_")
    
    # Create simple test script
    script_content = '''label start:
    "Welcome!"
    
    menu:
        "Choice A":
            jump choice_a
        "Choice B":
            jump choice_b
        "Choice C":
            jump choice_c

label choice_a:
    "You picked A"
    return

label choice_b:
    "You picked B"
    return

label choice_c:
    "You picked C"
    return
'''
    
    script_file = Path(temp_dir) / "script.rpy"
    script_file.write_text(script_content)
    
    try:
        tracer = FlowTracer(temp_dir, choice_strategy="random")
        
        # Get the file lines
        file_lines = tracer._get_file_lines(str(script_file))
        
        print("🔍 Debug Menu Parsing")
        print("=" * 40)
        print(f"Total lines in file: {len(file_lines)}")
        
        # Find menu line
        menu_line_idx = None
        for i, line in enumerate(file_lines):
            print(f"Line {i+1:2d}: {line.line_type:15s} | {line.content}")
            if 'menu:' in line.content:
                menu_line_idx = i
                print(f"         ^^ MENU FOUND AT INDEX {i}")
        
        if menu_line_idx is not None:
            print(f"\n🎯 Testing menu parsing at index {menu_line_idx}")
            
            # Test our parsing method
            choices = tracer._parse_menu_choices(file_lines, menu_line_idx)
            
            print(f"📋 Parsed choices:")
            for i, (choice_text, action) in enumerate(choices):
                print(f"   {i+1}. '{choice_text}' → {action}")
            
            print(f"\n📊 Total choices found: {len(choices)}")
            
            if len(choices) != 3:
                print(f"❌ Expected 3 choices, got {len(choices)}")
                
                # Debug line by line after menu
                print(f"\n🔍 Lines after menu (index {menu_line_idx}):")
                for i in range(menu_line_idx + 1, min(menu_line_idx + 15, len(file_lines))):
                    line = file_lines[i]
                    print(f"Line {i+1:2d}: {line.line_type:15s} | '{line.content}'")
            else:
                print(f"✅ Found all 3 choices correctly!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    debug_menu_parsing() 