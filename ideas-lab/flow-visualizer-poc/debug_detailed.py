#!/usr/bin/env python3
"""
Detailed debug with print statements.
"""

import sys
from pathlib import Path

# Add CSAP to path
sys.path.append(str(Path(__file__).parent / "csap"))

from csap_parser import CSAPParser, CSAPTransformer
from csap_ast import PropertyNode, ActionNode
from lark import Lark


class DebugTransformer(CSAPTransformer):
    """Transformer with debug prints."""
    
    def textbutton_single_line(self, items):
        """Transform single-line textbutton with debug."""
        print(f"\\n🔍 textbutton_single_line called with {len(items)} items:")
        for i, item in enumerate(items):
            print(f"  Item {i}: {type(item)} = {item}")
        
        result = super().textbutton_single_line(items)
        print(f"  Result properties: {len(result.properties)}")
        return result
    
    def textbutton_properties(self, items):
        """Transform textbutton properties with debug."""
        print(f"\\n🔍 textbutton_properties called with {len(items)} items:")
        for i, item in enumerate(items):
            print(f"  Item {i}: {type(item)} = {item}")
        
        result = super().textbutton_properties(items)
        print(f"  Result: {result}")
        return result
    
    def textbutton_property(self, items):
        """Transform textbutton property with debug."""
        print(f"\\n🔍 textbutton_property called with {len(items)} items:")
        for i, item in enumerate(items):
            print(f"  Item {i}: {type(item)} = {item}")
        
        # Call the parent method manually
        line, column = self._get_node_location(items)
        prop_name = items[0]
        prop_value = items[1] if len(items) > 1 else ""
        
        result = PropertyNode(
            property_name=prop_name,
            property_value=prop_value,
            line_number=line,
            column=column
        )
        print(f"  Result: {type(result)} = {result}")
        return result


def debug_with_prints():
    """Debug with detailed print statements."""
    
    print("🔍 Detailed Debug with Prints")
    
    # Create parser with debug transformer
    parser = CSAPParser()
    parser.transformer = DebugTransformer()
    
    # Test with property
    prop_screen = '''screen test:
    textbutton "Test" text_color "#EFEFEF" action Jump("dest")'''
    
    try:
        result = parser.parse_screen_text(prop_screen)
        print(f"\\n✅ Final result: {result}")
        
        if result.elements:
            element = result.elements[0]
            print(f"Element properties: {len(element.properties)}")
            for prop in element.properties:
                print(f"  - {prop.property_name}: {prop.property_value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    debug_with_prints()
