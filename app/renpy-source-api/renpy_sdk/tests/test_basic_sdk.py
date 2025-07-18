"""
Basic SDK integration test.

Run this to verify that the Ren'Py SDK can be imported and used for parsing.
"""

import sys
import os
from pathlib import Path

# Add the src directory to path so we can import our utilities
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

from sdk_utils import sdk_manager


def test_sdk_initialization():
    """Test SDK path setup and initialization."""
    print("="*60)
    print("TESTING SDK INITIALIZATION")
    print("="*60)
    
    # Show SDK info before initialization
    info = sdk_manager.get_sdk_info()
    print("SDK Info (before initialization):")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    print("\nAttempting to initialize SDK...")
    success = sdk_manager.initialize_sdk()
    
    # Show SDK info after initialization
    info = sdk_manager.get_sdk_info()
    print("\nSDK Info (after initialization):")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    return success


def test_simple_parsing():
    """Test parsing a simple Ren'Py script."""
    print("\n" + "="*60)
    print("TESTING SIMPLE SCRIPT PARSING")
    print("="*60)
    
    simple_script = '''
label start:
    "Hello, world!"
    "This is a simple test."
    
    menu:
        "Choice 1":
            jump choice1
        "Choice 2":
            jump choice2
    
label choice1:
    "You chose option 1"
    return
    
label choice2:
    "You chose option 2"
    return
'''
    
    print("Script to parse:")
    print(simple_script)
    print("\nParsing...")
    
    success, result = sdk_manager.parse_script(simple_script, "test_simple.rpy")
    
    if success:
        print("✅ Parsing successful!")
        print(f"Number of AST nodes: {len(result)}")
        
        print("\nAST Node Analysis:")
        for i, node in enumerate(result):
            node_type = type(node).__name__
            print(f"  Node {i}: {node_type}")
            
            # Try to extract basic info from common node types
            if hasattr(node, 'name'):
                print(f"    Name: {node.name}")
            if hasattr(node, 'what'):
                print(f"    Text: {repr(node.what)}")
            if hasattr(node, 'items') and node_type == 'Menu':
                print(f"    Menu items: {len(node.items)}")
                for j, item in enumerate(node.items):
                    if hasattr(item, 'caption'):
                        print(f"      Choice {j}: {repr(item.caption)}")
    else:
        print(f"❌ Parsing failed: {result}")
    
    return success


def test_complex_parsing():
    """Test parsing with Python expressions and complex features."""
    print("\n" + "="*60)
    print("TESTING COMPLEX SCRIPT PARSING")
    print("="*60)
    
    complex_script = '''
default points = 0

label start:
    "Welcome to the complex test."
    $ points = 10
    
    menu:
        "Increase points" if points < 20:
            $ points += 5
            "Points increased to [points]!"
            
        "Decrease points" if points > 0:
            $ points -= 3
            "Points decreased to [points]!"
            
        "Continue":
            pass
    
    if points > 15:
        "You have high points!"
    else:
        "You have low points."
    
    return
'''
    
    print("Complex script to parse:")
    print(complex_script)
    print("\nParsing...")
    
    success, result = sdk_manager.parse_script(complex_script, "test_complex.rpy")
    
    if success:
        print("✅ Complex parsing successful!")
        print(f"Number of AST nodes: {len(result)}")
        
        print("\nComplex AST Node Analysis:")
        for i, node in enumerate(result):
            node_type = type(node).__name__
            print(f"  Node {i}: {node_type}")
            
            # More detailed analysis for complex nodes
            if hasattr(node, 'name'):
                print(f"    Name: {node.name}")
            if hasattr(node, 'what'):
                print(f"    Text: {repr(node.what)}")
            if hasattr(node, 'expr') and node_type == 'Python':
                print(f"    Python expression: {node.expr}")
            if hasattr(node, 'items') and node_type == 'Menu':
                print(f"    Menu items: {len(node.items)}")
                for j, item in enumerate(node.items):
                    if hasattr(item, 'caption'):
                        print(f"      Choice {j}: {repr(item.caption)}")
                    if hasattr(item, 'condition'):
                        print(f"        Condition: {item.condition}")
    else:
        print(f"❌ Complex parsing failed: {result}")
    
    return success


def main():
    """Run all tests."""
    print("Ren'Py SDK Integration Test")
    print("Running basic tests to verify SDK functionality...")
    
    # Test 1: SDK initialization
    init_success = test_sdk_initialization()
    
    if not init_success:
        print("\n❌ SDK initialization failed. Cannot proceed with parsing tests.")
        return False
    
    # Test 2: Simple parsing
    simple_success = test_simple_parsing()
    
    # Test 3: Complex parsing
    complex_success = test_complex_parsing()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"SDK Initialization: {'✅ PASS' if init_success else '❌ FAIL'}")
    print(f"Simple Parsing:     {'✅ PASS' if simple_success else '❌ FAIL'}")
    print(f"Complex Parsing:    {'✅ PASS' if complex_success else '❌ FAIL'}")
    
    all_success = init_success and simple_success and complex_success
    print(f"\nOverall Result:     {'✅ ALL TESTS PASSED' if all_success else '❌ SOME TESTS FAILED'}")
    
    return all_success


if __name__ == "__main__":
    main() 