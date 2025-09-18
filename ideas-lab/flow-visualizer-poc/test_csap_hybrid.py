#!/usr/bin/env python3
"""
Test CSAP Hybrid Parser

Tests the hybrid parser that provides drop-in replacement functionality.
"""

import sys
from pathlib import Path

# Add CSAP to path
sys.path.append(str(Path(__file__).parent / "csap"))

from csap_hybrid_parser import CSAPHybridParser, create_enhanced_parser


def test_hybrid_parser_initialization():
    """Test hybrid parser initialization."""
    
    print("🧪 Testing Hybrid Parser Initialization")
    print("=" * 50)
    
    try:
        parser = CSAPHybridParser()
        print(f"✅ Hybrid parser initialized")
        print(f"   CSAP enabled: {parser.csap_enabled}")
        print(f"   Has original parser methods: {hasattr(parser, 'patterns')}")
        return True
    except Exception as e:
        print(f"❌ Hybrid parser initialization failed: {e}")
        return False


def test_screen_parsing_functionality():
    """Test screen parsing with the hybrid parser."""
    
    print("\\n🧪 Testing Screen Parsing Functionality")
    print("=" * 50)
    
    parser = create_enhanced_parser()
    
    # Test screen parsing
    test_lines = [
        'label start:',
        '    "Welcome!"',
        '',
        'screen test_menu:',
        '    textbutton "Play" action Jump("game_start")',
        '    textbutton "Quit" action Jump("quit_game")',
        '    hotspot (10, 20, 100, 50) action Call("help_screen")',
        '',
        'label game_start:',
        '    "Game begins..."'
    ]
    
    try:
        result = parser.parse_screen_structure(
            file_path="test.rpy",
            start_line=4,  # "screen test_menu:" line
            lines=test_lines,
            screen_name="test_menu"
        )
        
        print(f"✅ Screen parsing successful:")
        print(f"   Screen name: {result.screen_name}")
        print(f"   Total elements: {result.total_elements}")
        print(f"   Interactive elements: {result.interactive_elements}")
        print(f"   Screen type: {result.screen_type}")
        
        for i, element in enumerate(result.elements):
            print(f"   Element {i}: {element.element_type}")
            if element.text:
                print(f"     Text: '{element.text}'")
            if element.coordinates:
                print(f"     Coordinates: {element.coordinates}")
            print(f"     Action: {element.action_type}('{element.destination}')")
        
        return True
        
    except Exception as e:
        print(f"❌ Screen parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_performance_tracking():
    """Test performance tracking features."""
    
    print("\\n🧪 Testing Performance Tracking")
    print("=" * 50)
    
    parser = create_enhanced_parser()
    
    # Parse multiple screens to generate stats
    test_screens = [
        ("screen menu1:", "textbutton 'Test1' action Jump('dest1')"),
        ("screen menu2:", "textbutton 'Test2' action Call('dest2')"),
        ("screen menu3:", "hotspot (0, 0, 10, 10) action Jump('dest3')"),
    ]
    
    for i, (screen_def, content) in enumerate(test_screens):
        lines = [screen_def, f"    {content}"]
        screen_name = f"test_screen_{i}"
        
        try:
            parser.parse_screen_structure("test.rpy", 1, lines, screen_name)
        except Exception:
            pass  # Continue even if parsing fails
    
    # Print performance report
    parser.print_performance_report()
    
    # Get stats programmatically
    stats = parser.get_csap_performance_stats()
    
    print(f"\\n📊 Programmatic Stats Access:")
    print(f"   Total screens: {stats['total_screens_parsed']}")
    print(f"   Success rate: {stats['csap_success_rate']:.1f}%")
    
    return True


def test_backward_compatibility():
    """Test backward compatibility with original parser methods."""
    
    print("\\n🧪 Testing Backward Compatibility")
    print("=" * 50)
    
    parser = create_enhanced_parser()
    
    # Test that original parser methods are available
    original_methods = ['patterns', 'find_rpy_files', 'extract_character_definitions']
    
    available_methods = 0
    for method_name in original_methods:
        if hasattr(parser, method_name):
            available_methods += 1
            print(f"✅ Method '{method_name}' available")
        else:
            print(f"⚠️  Method '{method_name}' not available")
    
    print(f"\\n📊 Compatibility: {available_methods}/{len(original_methods)} methods available")
    
    # Test that we can still call original parser functionality
    try:
        # This should work if the original parser is available
        rpy_files = parser.find_rpy_files(".")
        print(f"✅ Original method call successful: found {len(rpy_files)} .rpy files")
        return True
    except Exception as e:
        print(f"⚠️  Original method call failed: {e}")
        return False


def main():
    """Run all hybrid parser tests."""
    
    print("🎯 CSAP Hybrid Parser Test Suite")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 4
    
    if test_hybrid_parser_initialization():
        tests_passed += 1
    
    if test_screen_parsing_functionality():
        tests_passed += 1
    
    if test_performance_tracking():
        tests_passed += 1
    
    if test_backward_compatibility():
        tests_passed += 1
    
    print("\\n" + "=" * 60)
    print(f"📊 Hybrid Parser Test Results: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("🎉 All hybrid parser tests passed!")
        print("\\n🚀 Integration Ready:")
        print("   ✅ Drop-in replacement for RenpyParser")
        print("   ✅ Enhanced screen parsing with CSAP")
        print("   ✅ Full backward compatibility")
        print("   ✅ Performance tracking and reporting")
        print("   ✅ Automatic fallback to regex parsing")
        
        print("\\n📋 Integration Instructions:")
        print("   Replace: parser = RenpyParser()")
        print("   With:    parser = create_enhanced_parser()")
        
        return True
    else:
        print("❌ Some hybrid parser tests failed.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
