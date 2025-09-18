#!/usr/bin/env python3
"""
CSAP Demo Script

Demonstrates the current Custom Screen AST Parser capabilities.
This shows what we've built so far in Phase 1.
"""

import sys
from pathlib import Path

# Add CSAP to path
sys.path.append(str(Path(__file__).parent / "csap"))

from csap_parser import CSAPParser
from csap_ast import ScreenNode, TextButtonNode, HotspotNode
from csap_exceptions import CSAPError


def demo_csap():
    """Demonstrate CSAP parsing capabilities."""
    
    print("🎯 CSAP (Custom Screen AST Parser) Demo")
    print("=" * 50)
    
    try:
        # Initialize parser
        parser = CSAPParser()
        print("✅ CSAP Parser initialized successfully")
        
        # Test 1: Simple textbutton
        print("\\n📝 Test 1: Simple TextButton")
        simple_screen = '''screen test_menu:
    textbutton "Start Game" action Jump("start_game")'''
        
        result = parser.parse_screen_text(simple_screen)
        print(f"   Screen: {result.screen_name}")
        print(f"   Elements: {len(result.elements)}")
        
        if result.elements:
            element = result.elements[0]
            if isinstance(element, TextButtonNode):
                print(f"   TextButton: '{element.text}' -> {element.action.action_type}('{element.action.destination}')")
        
        # Test 2: Hotspot
        print("\\n📝 Test 2: Hotspot Element")
        hotspot_screen = '''screen room_map:
    hotspot (100, 200, 150, 100) action Call("examine_door")'''
        
        result = parser.parse_screen_text(hotspot_screen)
        if result.elements:
            element = result.elements[0]
            if isinstance(element, HotspotNode):
                print(f"   Hotspot: {element.coordinates} -> {element.action.action_type}('{element.action.destination}')")
        
        # Test 3: Grammar validation
        print("\\n📝 Test 3: Grammar Validation")
        is_valid = parser.validate_grammar()
        print(f"   Grammar validation: {'✅ PASSED' if is_valid else '❌ FAILED'}")
        
        # Test 4: Error handling
        print("\\n📝 Test 4: Error Handling")
        try:
            invalid_screen = '''screen bad:
    invalid_syntax "test"'''
            parser.parse_screen_text(invalid_screen)
            print("   ❌ Should have failed!")
        except CSAPError as e:
            print(f"   ✅ Properly caught error: {type(e).__name__}")
        
        print("\\n" + "=" * 50)
        print("🎉 CSAP Demo completed successfully!")
        print("\\n📊 Current Status:")
        print("   ✅ Phase 1 Complete: Foundation, AST, Parser Core")
        print("   🔄 Phase 2 In Progress: Grammar Refinement & Testing")
        print("   ⏳ Phase 3 Pending: Integration with Flow Visualizer")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False


if __name__ == "__main__":
    success = demo_csap()
    sys.exit(0 if success else 1)
