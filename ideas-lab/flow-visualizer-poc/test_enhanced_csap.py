#!/usr/bin/env python3
"""
Test Enhanced CSAP with Complex VN Patterns

Tests the enhanced grammar against complex patterns from real VNs.
"""

import sys
from pathlib import Path

# Add CSAP to path
sys.path.append(str(Path(__file__).parent / "csap"))

from csap_parser import CSAPParser
from csap_ast import ScreenNode, TextButtonNode
from csap_exceptions import CSAPError


def test_complex_textbutton():
    """Test complex styled textbutton from Apocalust VN."""
    
    print("🧪 Testing Complex Textbutton (Apocalust VN Style)")
    
    parser = CSAPParser()
    
    # This is the actual complex pattern from Apocalust VN
    complex_screen = '''screen kitchen_convo:
    textbutton "{image=chat_bubble_1.png} Do I seem any different to you?" text_color "#EFEFEF" text_size 32 action Jump("ep1_dial_kitchen_doiseem")'''
    
    try:
        result = parser.parse_screen_text(complex_screen)
        
        print(f"✅ Parsed screen: {result.screen_name}")
        print(f"   Elements: {len(result.elements)}")
        
        if result.elements and isinstance(result.elements[0], TextButtonNode):
            element = result.elements[0]
            print(f"   Text: '{element.text}'")
            print(f"   Properties: {len(element.properties)}")
            for prop in element.properties:
                print(f"     - {prop.property_name}: {prop.property_value}")
            if element.action:
                print(f"   Action: {element.action.action_type}('{element.action.destination}')")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_simple_patterns():
    """Test that simple patterns still work."""
    
    print("\\n🧪 Testing Simple Patterns (Backward Compatibility)")
    
    parser = CSAPParser()
    
    simple_screen = '''screen test:
    textbutton "Click me" action Jump("destination")'''
    
    try:
        result = parser.parse_screen_text(simple_screen)
        print(f"✅ Simple textbutton still works: '{result.elements[0].text}' -> {result.elements[0].action.destination}")
        return True
    except Exception as e:
        print(f"❌ Simple pattern failed: {e}")
        return False


def main():
    """Run enhanced CSAP tests."""
    
    print("🎯 Enhanced CSAP Testing")
    print("=" * 40)
    
    tests_passed = 0
    total_tests = 2
    
    if test_simple_patterns():
        tests_passed += 1
    
    if test_complex_textbutton():
        tests_passed += 1
    
    print("\\n" + "=" * 40)
    print(f"📊 Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Enhanced grammar working.")
        return True
    else:
        print("❌ Some tests failed. Grammar needs refinement.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
