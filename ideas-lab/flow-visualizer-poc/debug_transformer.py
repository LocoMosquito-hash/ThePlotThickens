#!/usr/bin/env python3
"""
Debug the transformer step by step.
"""

import sys
from pathlib import Path

# Add CSAP to path
sys.path.append(str(Path(__file__).parent / "csap"))

from csap_parser import CSAPParser, CSAPTransformer
from csap_ast import PropertyNode
from lark import Lark


def debug_transformer():
    """Debug what the transformer is actually returning."""
    
    print("🔍 Debugging Transformer Step by Step")
    
    # Create parser
    parser = CSAPParser()
    
    # Test simple screen
    simple_screen = '''screen test:
    textbutton "Test" text_color "#EFEFEF" action Jump("dest")'''
    
    try:
        # Parse to tree first
        tree = parser.parser.parse(simple_screen)
        print("✅ Parsing to tree successful")
        print(f"Tree: {tree}")
        
        # Transform tree
        result = parser.transformer.transform(tree)
        print("✅ Transformation successful")
        print(f"Result type: {type(result)}")
        print(f"Result: {result}")
        
        if hasattr(result, 'elements') and result.elements:
            element = result.elements[0]
            print(f"Element type: {type(element)}")
            print(f"Element properties: {element.properties}")
            
            if element.properties:
                for i, prop in enumerate(element.properties):
                    print(f"  Property {i}: {type(prop)} = {prop}")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    debug_transformer()
