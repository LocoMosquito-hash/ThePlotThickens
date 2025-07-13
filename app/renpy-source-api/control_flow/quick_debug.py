#!/usr/bin/env python3
"""
Quick debug to check line numbering in our test file.
"""

import sys
import tempfile
import shutil
from pathlib import Path

def main():
    """Check the exact line structure."""
    # Create test project
    test_dir = tempfile.mkdtemp()
    project_root = Path(test_dir)
    game_dir = project_root / 'game'
    game_dir.mkdir(exist_ok=True)
    
    script_content = '''
label start:
    "Beginning of story"
    jump middle_scene
    "This should not be reached"

label middle_scene:
    "Middle of the story"
    "More dialogue"
    jump ending

label ending:
    "The end"
    return
'''
    
    script_path = game_dir / 'script.rpy'
    script_path.write_text(script_content)
    
    try:
        # Read back and show line structure
        content = script_path.read_text()
        lines = content.split('\n')
        
        print("📄 File line structure:")
        for i, line in enumerate(lines, 1):
            print(f"   {i:2d}: '{line}'")
        
        print(f"\n📊 Total lines: {len(lines)}")
        
        # Find labels manually
        import re
        label_pattern = re.compile(r'^\s*label\s+([a-zA-Z_][a-zA-Z0-9_\.]*)\s*:', re.IGNORECASE)
        
        print(f"\n🏷️  Labels found:")
        for i, line in enumerate(lines, 1):
            match = label_pattern.match(line)
            if match:
                label_name = match.group(1)
                print(f"   {label_name}: line {i}")
        
    finally:
        shutil.rmtree(test_dir)

if __name__ == "__main__":
    main() 