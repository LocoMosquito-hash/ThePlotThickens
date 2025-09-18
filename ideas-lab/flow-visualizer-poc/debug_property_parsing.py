#!/usr/bin/env python3
"""
Debug property parsing in detail.
"""

import sys
from pathlib import Path

# Add CSAP to path
sys.path.append(str(Path(__file__).parent / "csap"))

from csap_parser import CSAPParser
from lark import Tree


def debug_property_parsing():
    """Debug property parsing step by step."""
    
    print("🔍 Debugging Property Parsing")
    
    parser = CSAPParser()
    
    # Test with property
    prop_screen = '''screen test:
    textbutton "Test" text_color "#EFEFEF" action Jump("dest")'''
    
    try:
        # Parse to tree
        tree = parser.parser.parse(prop_screen)
        print("✅ Parse tree created")
        
        # Print the tree structure
        def print_tree(node, indent=0):
            if isinstance(node, Tree):
                print("  " * indent + f"Tree: {node.data}")
                for child in node.children:
                    print_tree(child, indent + 1)
            else:
                print("  " * indent + f"Token: {node.type} = '{node.value}'")
        
        print("\\n📊 Parse Tree Structure:")
        print_tree(tree)
        
        # Transform
        result = parser.transformer.transform(tree)
        print("\\n✅ Transformation complete")
        print(f"Result: {result}")
        
        if hasattr(result, 'elements') and result.elements:
            element = result.elements[0]
            print(f"\\nElement text: '{element.text}'")
            print(f"Properties count: {len(element.properties)}")
            print(f"Action: {element.action}")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    debug_property_parsing()
