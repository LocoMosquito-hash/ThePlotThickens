#!/usr/bin/env python3
"""
Test basic property parsing without list literals.
"""

import sys
from pathlib import Path

# Add CSAP to path
sys.path.append(str(Path(__file__).parent / "csap"))

from csap_parser import CSAPParser
from csap_exceptions import CSAPError


def main():
    """Test basic properties."""
    print("🧪 Testing Basic Properties (No Lists)")
    
    parser = CSAPParser()
    
    # Test simple properties first
    simple_screen = '''screen test:
    textbutton "Test" action Jump("dest")'''
    
    try:
        result = parser.parse_screen_text(simple_screen)
        print("✅ Basic textbutton works")
        
        # Test with simple properties
        prop_screen = '''screen test:
    textbutton "Test" text_color "#EFEFEF" action Jump("dest")'''
        
        result2 = parser.parse_screen_text(prop_screen)
        print("✅ Textbutton with simple property works")
        
        element = result2.elements[0]
        print(f"   Properties: {len(element.properties)}")
        for prop in element.properties:
            print(f"     - {prop.property_name}: {prop.property_value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
