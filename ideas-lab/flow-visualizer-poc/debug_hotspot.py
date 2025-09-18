#!/usr/bin/env python3
"""
Debug hotspot coordinate parsing.
"""

import sys
from pathlib import Path

# Add CSAP to path
sys.path.append(str(Path(__file__).parent / "csap"))

from csap_parser import CSAPParser
from csap_ast import HotspotNode


def debug_hotspot():
    """Debug hotspot parsing."""
    
    print("🔍 Debugging Hotspot Parsing")
    
    parser = CSAPParser()
    
    # Test hotspot
    hotspot_screen = '''screen test:
    hotspot (100, 200, 50, 50) action Jump("target")'''
    
    try:
        # Parse without validation
        tree = parser.parser.parse(hotspot_screen)
        result = parser.transformer.transform(tree)
        print("✅ Parsing successful (validation bypassed)")
        
        if result.elements:
            element = result.elements[0]
            print(f"Element type: {type(element)}")
            
            if isinstance(element, HotspotNode):
                print(f"Coordinates: {element.coordinates}")
                print(f"Coordinates type: {type(element.coordinates)}")
                print(f"Coordinates length: {len(element.coordinates)}")
                print(f"Action: {element.action}")
                
                # Try validation
                errors = element.validate()
                if errors:
                    print(f"Validation errors: {errors}")
                else:
                    print("✅ Validation passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    debug_hotspot()
