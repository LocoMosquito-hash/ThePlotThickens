#!/usr/bin/env python3
"""
Test the actual integration layer with the Hillside screen.
"""

import sys
import re

# Simulate the actual file content from Hillside
hillside_screen_file = r"""label ep02_start:
    # Some code here
    
screen screenEp02ChoosePhoto():

    modal True

    imagemap:

        ground "02_090"       

        hotspot(130, 345, 203, 233) action Jump("ep02_choice01")

        hotspot(395, 143, 337, 438) action Jump("ep02_choice02")

        hotspot(835, 244, 271, 332) action Jump("ep02_choice03")

        hotspot(1188, 137, 345, 430) action Jump("ep02_choice04")

        hotspot(1596, 316, 193, 231) action Jump("ep02_choice05")

label ep02_choice01:
    "Choice 1"
"""

def test_integration():
    """Test the integration layer."""
    print("Testing CSAP Integration Layer with Hillside screen...\n")
    print("=" * 70)
    
    try:
        from csap.csap_integration import CSAPIntegratedParser
        
        # Create parser
        parser = CSAPIntegratedParser()
        
        # Simulate what find_all_screens does
        lines = hillside_screen_file.split('\n')
        
        # Find the screen definition
        screen_definition_pattern = re.compile(r'^\s*screen\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\([^)]*\))?\s*:', re.IGNORECASE)
        
        for i, line in enumerate(lines):
            match = screen_definition_pattern.match(line)
            if match:
                screen_name = match.group(1)
                start_line = i + 1  # Convert to 1-based indexing
                
                print(f"Found screen '{screen_name}' at line {start_line}")
                
                # Parse using the integration layer
                screen_structure = parser.parse_screen_structure(
                    file_path="custom.rpy",
                    start_line=start_line,
                    lines=lines,
                    screen_name=screen_name
                )
                
                print(f"\n[RESULT]")
                print(f"  Screen name: {screen_structure.screen_name}")
                print(f"  Total elements: {screen_structure.total_elements}")
                print(f"  Interactive elements: {screen_structure.interactive_elements}")
                print(f"  Elements in list: {len(screen_structure.elements)}")
                
                if len(screen_structure.elements) == 0:
                    print(f"\n[FAIL] Integration layer returned 0 elements!")
                    print(f"  This is the bug - CSAP works but integration loses elements")
                else:
                    print(f"\n[OK] Integration layer found {len(screen_structure.elements)} elements")
                    for i, elem in enumerate(screen_structure.elements):
                        print(f"    {i+1}. {elem.element_type} -> {elem.destination}")
                
                break
        
    except Exception as e:
        print(f"[FAIL] Exception: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(test_integration())



