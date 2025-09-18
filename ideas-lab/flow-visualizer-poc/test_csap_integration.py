#!/usr/bin/env python3
"""
Test CSAP Integration Layer

Tests the compatibility and integration of CSAP with the existing flow visualizer.
"""

import sys
from pathlib import Path

# Add CSAP to path
sys.path.append(str(Path(__file__).parent / "csap"))

from csap_integration import CSAPIntegratedParser
from csap_compatibility import convert_csap_to_screen_structure
from csap_parser import CSAPParser
from csap_ast import ScreenNode


def test_compatibility_layer():
    """Test the CSAP compatibility layer."""
    
    print("🧪 Testing CSAP Compatibility Layer")
    print("=" * 50)
    
    # Test CSAP -> ScreenStructure conversion
    parser = CSAPParser()
    
    test_screen = '''screen test_menu:
    textbutton "Start Game" action Jump("start_game")
    textbutton "Load Game" action Call("load_menu")
    hotspot (100, 200, 150, 100) action Jump("secret_area")'''
    
    try:
        # Parse with CSAP
        screen_node = parser.parse_screen_text(test_screen)
        print(f"✅ CSAP parsed screen: {screen_node.screen_name}")
        print(f"   Elements: {len(screen_node.elements)}")
        
        # Convert to ScreenStructure
        screen_structure = convert_csap_to_screen_structure(screen_node, "test.rpy")
        print(f"✅ Converted to ScreenStructure:")
        print(f"   Name: {screen_structure.screen_name}")
        print(f"   Elements: {len(screen_structure.elements)}")
        print(f"   Interactive: {screen_structure.interactive_elements}")
        print(f"   Type: {screen_structure.screen_type}")
        
        # Validate elements
        for i, element in enumerate(screen_structure.elements):
            print(f"   Element {i}: {element.element_type} -> {element.action_type}('{element.destination}')")
            if element.text:
                print(f"     Text: '{element.text}'")
            if element.coordinates:
                print(f"     Coordinates: {element.coordinates}")
        
        return True
        
    except Exception as e:
        print(f"❌ Compatibility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integrated_parser():
    """Test the integrated parser."""
    
    print("\\n🧪 Testing CSAP Integrated Parser")
    print("=" * 50)
    
    integrated_parser = CSAPIntegratedParser()
    
    # Simulate parsing a screen from file lines
    test_lines = [
        'label start:',
        '    "Welcome to the game!"',
        '',
        'screen main_menu:',
        '    textbutton "Start Game" action Jump("chapter1")',
        '    textbutton "Load Game" action Call("load_screen")',
        '    hotspot (50, 100, 200, 80) action Jump("options")',
        '',
        'label chapter1:',
        '    "Chapter 1 begins..."'
    ]
    
    try:
        # Test parse_screen_structure method
        screen_structure = integrated_parser.parse_screen_structure(
            file_path="test.rpy",
            start_line=4,  # Line with "screen main_menu:"
            lines=test_lines,
            screen_name="main_menu"
        )
        
        print(f"✅ Integrated parser result:")
        print(f"   Name: {screen_structure.screen_name}")
        print(f"   Elements: {len(screen_structure.elements)}")
        print(f"   Interactive: {screen_structure.interactive_elements}")
        
        for i, element in enumerate(screen_structure.elements):
            print(f"   Element {i}: {element.element_type} -> {element.action_type}('{element.destination}')")
        
        return True
        
    except Exception as e:
        print(f"❌ Integrated parser test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_performance_tracking():
    """Test performance tracking features."""
    
    print("\\n🧪 Testing Performance Tracking")
    print("=" * 50)
    
    integrated_parser = CSAPIntegratedParser()
    
    # Test multiple screens
    test_cases = [
        ("screen good_screen:", "textbutton 'Test' action Jump('dest')"),
        ("screen complex_screen:", "textbutton 'Complex' text_color '#FFF' action Jump('dest')"),
        ("screen bad_screen:", "invalid syntax here"),  # Should trigger fallback
    ]
    
    for i, (screen_def, screen_content) in enumerate(test_cases):
        lines = [screen_def, f"    {screen_content}"]
        screen_name = f"test_screen_{i}"
        
        try:
            result = integrated_parser.parse_screen_structure(
                file_path="test.rpy",
                start_line=1,
                lines=lines,
                screen_name=screen_name
            )
            print(f"✅ Parsed {screen_name}: {len(result.elements)} elements")
        except Exception as e:
            print(f"⚠️  {screen_name} failed: {e}")
    
    # Print statistics
    stats = integrated_parser.get_parsing_stats()
    print(f"\\n📊 Performance Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    return True


def main():
    """Run all integration tests."""
    
    print("🎯 CSAP Integration Test Suite")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 3
    
    if test_compatibility_layer():
        tests_passed += 1
    
    if test_integrated_parser():
        tests_passed += 1
    
    if test_performance_tracking():
        tests_passed += 1
    
    print("\\n" + "=" * 60)
    print(f"📊 Integration Test Results: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("🎉 All integration tests passed! CSAP is ready for deployment.")
        print("\\n🚀 Next Steps:")
        print("   1. Replace regex parser with CSAP in production")
        print("   2. Test with real VN projects")
        print("   3. Monitor performance and accuracy")
        return True
    else:
        print("❌ Some integration tests failed. Fix issues before deployment.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
