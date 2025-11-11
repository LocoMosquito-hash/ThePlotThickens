#!/usr/bin/env python3
"""
Test if transforms at the end break CSAP parsing.
"""
import sys
import codecs

# Fix encoding on Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

def test_with_and_without_transforms():
    """Test CSAP with and without transforms at the end."""
    
    from pathlib import Path
    from csap.csap_parser import CSAPParser
    
    # Read the extracted content
    extracted = Path("debug_extracted_dreams_visualizer.txt").read_text(encoding='utf-8')
    
    # Split at the transform line
    lines = extracted.split('\n')
    screen_only = '\n'.join(lines[:53])  # Up to line 52 + empty line
    
    parser = CSAPParser()
    
    print("Testing WITH transforms at the end:")
    print("=" * 70)
    try:
        screen_node = parser.parse_screen_text(extracted)
        interactive = screen_node.get_interactive_elements()
        print(f"  Parsed: {len(interactive)} elements")
        for i, elem in enumerate(interactive):
            print(f"    {i+1}. {elem.action.action_type} -> {elem.action.destination}")
    except Exception as e:
        print(f"  ERROR: {e}")
    
    print("\nTesting WITHOUT transforms (screen only):")
    print("=" * 70)
    try:
        screen_node = parser.parse_screen_text(screen_only)
        interactive = screen_node.get_interactive_elements()
        print(f"  Parsed: {len(interactive)} elements")
        for i, elem in enumerate(interactive):
            print(f"    {i+1}. {elem.action.action_type} -> {elem.action.destination}")
    except Exception as e:
        print(f"  ERROR: {e}")

if __name__ == "__main__":
    test_with_and_without_transforms()

