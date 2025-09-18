#!/usr/bin/env python3
"""
Run CSAP Regression Tests

Simplified version to test CSAP against regex patterns without pytest.
"""

import sys
from pathlib import Path

# Add paths for imports
sys.path.append(str(Path(__file__).parent / "csap"))
sys.path.append(str(Path(__file__).parent.parent.parent / "app" / "renpy-source-api"))

from csap_parser import CSAPParser
from csap_ast import ScreenNode, TextButtonNode, ImageButtonNode, HotspotNode
from csap_exceptions import CSAPError


def get_test_cases():
    """Get test cases from regex robustness test."""
    return [
        {
            "name": "Basic textbutton",
            "content": '''screen test_screen:
    textbutton "Click me" action Jump("destination")''',
            "expected": {
                "text": "Click me",
                "action_type": "Jump",
                "destination": "destination"
            }
        },
        {
            "name": "Complex styled textbutton (Apocalust VN)",
            "content": '''screen kitchen_convo:
    textbutton "{image=chat_bubble_1.png} Do I seem any different to you?" text_color "#EFEFEF" text_size 32 action Jump("ep1_dial_kitchen_doiseem")''',
            "expected": {
                "text": "{image=chat_bubble_1.png} Do I seem any different to you?",
                "action_type": "Jump",
                "destination": "ep1_dial_kitchen_doiseem"
            }
        },
        {
            "name": "Basic hotspot",
            "content": '''screen test_screen:
    hotspot (100, 200, 50, 50) action Jump("target")''',
            "expected": {
                "coordinates": (100, 200, 50, 50),
                "action_type": "Jump",
                "destination": "target"
            }
        },
        {
            "name": "Hotspot with Call action (AoA Academy VN)",
            "content": '''screen c1aca_exp_corridor_au:
    hotspot (35, 755, 290, 281) action Call("c1_aca_exp_corridor_exit")''',
            "expected": {
                "coordinates": (35, 755, 290, 281),
                "action_type": "Call",
                "destination": "c1_aca_exp_corridor_exit"
            }
        },
        {
            "name": "Basic imagebutton",
            "content": '''screen test_screen:
    imagebutton idle "image.png" action Jump("destination")''',
            "expected": {
                "action_type": "Jump",
                "destination": "destination"
            }
        }
    ]


def run_test_case(parser, test_case):
    """Run a single test case."""
    print(f"\\n🧪 Testing: {test_case['name']}")
    
    try:
        result = parser.parse_screen_text(test_case['content'])
        
        if not isinstance(result, ScreenNode):
            print(f"   ❌ Expected ScreenNode, got {type(result)}")
            return False
        
        interactive_elements = result.get_interactive_elements()
        if not interactive_elements:
            print(f"   ❌ No interactive elements found")
            return False
        
        element = interactive_elements[0]
        expected = test_case['expected']
        
        # Check element-specific properties
        if isinstance(element, TextButtonNode):
            if element.text != expected.get('text', ''):
                print(f"   ❌ Text mismatch: expected '{expected['text']}', got '{element.text}'")
                return False
        elif isinstance(element, HotspotNode):
            if element.coordinates != expected.get('coordinates'):
                print(f"   ❌ Coordinates mismatch: expected {expected['coordinates']}, got {element.coordinates}")
                return False
        
        # Check action for all types
        if element.action:
            if element.action.action_type != expected['action_type']:
                print(f"   ❌ Action type mismatch: expected '{expected['action_type']}', got '{element.action.action_type}'")
                return False
            if element.action.destination != expected['destination']:
                print(f"   ❌ Destination mismatch: expected '{expected['destination']}', got '{element.action.destination}'")
                return False
        else:
            print(f"   ❌ No action found")
            return False
        
        print(f"   ✅ PASS")
        return True
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False


def main():
    """Run regression tests."""
    print("🧪 CSAP Regression Test Suite")
    print("=" * 50)
    
    try:
        parser = CSAPParser()
        print("✅ CSAP Parser initialized")
        
        test_cases = get_test_cases()
        print(f"📊 Running {len(test_cases)} test cases...")
        
        passed = 0
        failed = 0
        
        for test_case in test_cases:
            if run_test_case(parser, test_case):
                passed += 1
            else:
                failed += 1
        
        print("\\n" + "=" * 50)
        print("📊 REGRESSION TEST SUMMARY")
        print("=" * 50)
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Total:  {len(test_cases)}")
        
        if failed > 0:
            print("\\n🚨 SOME TESTS FAILED!")
            print("🔧 Action required: Fix failing patterns")
            return False
        else:
            print("\\n🎉 ALL TESTS PASSED!")
            print("✅ CSAP successfully handles all regex patterns")
            return True
            
    except Exception as e:
        print(f"❌ Test suite failed to initialize: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
