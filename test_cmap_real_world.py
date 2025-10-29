#!/usr/bin/env python3
"""
Test CMAP with real-world Ren'Py menu patterns from "The Question".
"""

import sys
from pathlib import Path

# Add the CMAP module to path
app_dir = Path("app/renpy-source-api")
sys.path.insert(0, str(app_dir))

def test_real_world_menus():
    """Test CMAP with real-world menu patterns."""
    print("TESTING CMAP WITH REAL-WORLD MENUS")
    print("=" * 50)
    
    try:
        from renpy_sdk.cmap import CMAPParser
        print("CMAP imported successfully")
        
        parser = CMAPParser()
        print("CMAP parser initialized")
        
        # Test 1: Menu with descriptive text (from "The Question")
        menu1 = '''menu:
    "As soon as she catches my eye, I decide..."
    
    "To ask her right away.":
        jump rightaway
    
    "To ask her later.":
        jump later'''
        
        print("\nTesting menu with descriptive text:")
        print(menu1)
        
        result1 = parser.parse_menu(menu1)
        if result1:
            print(f"SUCCESS! Parsed {len(result1.choices)} choices")
            for i, choice in enumerate(result1.choices):
                print(f"  Choice {i+1}: '{choice.text}'")
        else:
            print("FAILED to parse menu with descriptive text")
        
        # Test 2: Menu with character dialogue (from "The Question")
        menu2 = '''menu:
    s "Sure, but what's a \\"visual novel?\\""
    
    "It's a videogame.":
        jump game
    
    "It's an interactive book.":
        jump book'''
        
        print("\nTesting menu with character dialogue:")
        print(menu2)
        
        result2 = parser.parse_menu(menu2)
        if result2:
            print(f"SUCCESS! Parsed {len(result2.choices)} choices")
            for i, choice in enumerate(result2.choices):
                print(f"  Choice {i+1}: '{choice.text}'")
        else:
            print("FAILED to parse menu with character dialogue")
        
        # Test 3: Simple menu (should still work)
        menu3 = '''menu:
    "Choice 1":
        jump label1
    "Choice 2" if flag:
        pass'''
        
        print("\nTesting simple menu (regression test):")
        print(menu3)
        
        result3 = parser.parse_menu(menu3)
        if result3:
            print(f"SUCCESS! Parsed {len(result3.choices)} choices")
            for i, choice in enumerate(result3.choices):
                conditional = "conditional" if choice.is_conditional else "simple"
                print(f"  Choice {i+1}: '{choice.text}' ({conditional})")
        else:
            print("FAILED to parse simple menu")
        
        # Summary
        success_count = sum([1 for result in [result1, result2, result3] if result])
        print(f"\nSUMMARY: {success_count}/3 tests passed")
        
        if success_count == 3:
            print("ALL TESTS PASSED! CMAP can now handle real-world menus!")
            return True
        else:
            print("Some tests failed - need more grammar fixes")
            return False
            
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_real_world_menus()
