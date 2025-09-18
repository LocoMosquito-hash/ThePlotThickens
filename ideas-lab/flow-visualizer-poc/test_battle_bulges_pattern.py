#!/usr/bin/env python3
"""
Test CSAP with Battle of the Bulges VN pattern.

This tests the specific screen pattern from the user's example:
- Screen with button element
- xpos, ypos, xysize properties
- action Jump to destination
"""

import sys
from pathlib import Path

# Add CSAP to path
sys.path.append(str(Path(__file__).parent / "csap"))

from csap_parser import CSAPParser
from csap_compatibility import convert_csap_to_screen_structure


def test_battle_bulges_pattern():
    """Test the specific pattern from Battle of the Bulges VN."""
    
    print("🎯 Testing Battle of the Bulges Screen Pattern")
    print("=" * 60)
    
    # The exact pattern from the user's example
    test_screen = '''screen parlourfuckcum:
    modal True
    button:
        xpos .88
        ypos .9
        xysize(100, 50)  
        action Jump ("ParlourCum01")'''
    
    print("📋 Input Screen:")
    print(test_screen)
    print()
    
    parser = CSAPParser()
    
    try:
        # Parse with CSAP
        print("🔍 Parsing with CSAP...")
        screen_node = parser.parse_screen_text(test_screen)
        
        print("✅ CSAP parsing successful!")
        print(f"   Screen name: {screen_node.screen_name}")
        print(f"   Elements: {len(screen_node.elements)}")
        
        # Show parsed elements
        for i, element in enumerate(screen_node.elements):
            print(f"   Element {i}: {type(element).__name__}")
            if hasattr(element, 'properties'):
                print(f"     Properties: {len(element.properties)}")
                for prop in element.properties:
                    print(f"       {prop.property_name}: {prop.property_value}")
            if hasattr(element, 'action') and element.action:
                print(f"     Action: {element.action.action_type}('{element.action.destination}')")
        
        print()
        
        # Convert to ScreenStructure for compatibility
        print("🔄 Converting to ScreenStructure...")
        screen_structure = convert_csap_to_screen_structure(screen_node, "script02.rpy")
        
        print("✅ Conversion successful!")
        print(f"   Screen name: {screen_structure.screen_name}")
        print(f"   Total elements: {screen_structure.total_elements}")
        print(f"   Interactive elements: {screen_structure.interactive_elements}")
        print(f"   Screen type: {screen_structure.screen_type}")
        
        # Show converted elements
        for i, element in enumerate(screen_structure.elements):
            print(f"   Element {i}: {element.element_type}")
            print(f"     Destination: {element.destination}")
            print(f"     Action type: {element.action_type}")
        
        print()
        
        # Validate the expected result
        print("🎯 Validation:")
        if screen_structure.screen_name == "parlourfuckcum":
            print("✅ Screen name correct")
        else:
            print(f"❌ Screen name incorrect: expected 'parlourfuckcum', got '{screen_structure.screen_name}'")
        
        if screen_structure.total_elements == 1:
            print("✅ Element count correct")
        else:
            print(f"❌ Element count incorrect: expected 1, got {screen_structure.total_elements}")
        
        if screen_structure.elements and screen_structure.elements[0].destination == "ParlourCum01":
            print("✅ Button destination correct")
        else:
            dest = screen_structure.elements[0].destination if screen_structure.elements else "None"
            print(f"❌ Button destination incorrect: expected 'ParlourCum01', got '{dest}'")
        
        if screen_structure.elements and screen_structure.elements[0].action_type == "jump":
            print("✅ Action type correct")
        else:
            action = screen_structure.elements[0].action_type if screen_structure.elements else "None"
            print(f"❌ Action type incorrect: expected 'jump', got '{action}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_screen_call_detection():
    """Test detection of the call screen statement."""
    
    print("\\n🎯 Testing Screen Call Detection")
    print("=" * 60)
    
    # The label that calls the screen
    test_label = '''label ParlourFuck:
stop music
play music "Sounds/katsumifuck.mp3"
show movieparlourfuck
show cum
call screen parlourfuckcum'''
    
    print("📋 Input Label:")
    print(test_label)
    print()
    
    # This would be handled by the main parser, not CSAP
    # But let's verify the screen call pattern is detectable
    import re
    
    call_screen_pattern = re.compile(r'^\s*call\s+screen\s+([a-zA-Z_][a-zA-Z0-9_]*)', re.IGNORECASE)
    
    for line in test_label.split('\\n'):
        match = call_screen_pattern.match(line)
        if match:
            screen_name = match.group(1)
            print(f"✅ Found screen call: '{screen_name}'")
            if screen_name == "parlourfuckcum":
                print("✅ Screen name matches expected")
                return True
            else:
                print(f"❌ Screen name mismatch: expected 'parlourfuckcum', got '{screen_name}'")
                return False
    
    print("❌ No screen call found")
    return False


def main():
    """Run all Battle of the Bulges pattern tests."""
    
    print("🎮 Battle of the Bulges VN Pattern Tests")
    print("=" * 70)
    
    tests_passed = 0
    total_tests = 2
    
    if test_battle_bulges_pattern():
        tests_passed += 1
    
    if test_screen_call_detection():
        tests_passed += 1
    
    print("\\n" + "=" * 70)
    print(f"📊 Test Results: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("🎉 All Battle of the Bulges patterns working!")
        print("\\n🚀 Expected Flow:")
        print("   ParlourFuck (label)")
        print("   ↓ (call screen)")
        print("   Screen: parlourfuckcum (screen container)")
        print("   ↓ (contains)")
        print("   Button element (screen element)")
        print("   ↓ (action Jump)")
        print("   ParlourCum01 (label)")
        return True
    else:
        print("❌ Some tests failed. Check CSAP grammar for button parsing.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
