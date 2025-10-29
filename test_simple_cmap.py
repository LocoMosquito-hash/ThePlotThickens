#!/usr/bin/env python3
"""
Test CMAP with very simple menu.
"""

import sys
from pathlib import Path

# Add the CMAP module to path
app_dir = Path("app/renpy-source-api")
sys.path.insert(0, str(app_dir))

def test_simple_menu():
    """Test CMAP parser with a very simple menu."""
    print("🧪 TESTING SIMPLE CMAP MENU")
    print("=" * 40)
    
    try:
        from renpy_sdk.cmap import CMAPParser
        print("✅ CMAP imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import CMAP: {e}")
        return False
    
    # Create a very simple test menu (no conditionals)
    test_menu = '''menu:
    "Choice 1":
        jump label1
    "Choice 2":
        pass'''
    
    print(f"\n📝 Simple test menu:")
    print(test_menu)
    
    # Initialize parser
    try:
        parser = CMAPParser()
        print("\n✅ CMAP parser initialized")
    except Exception as e:
        print(f"\n❌ Failed to initialize CMAP parser: {e}")
        return False
    
    # Parse the menu
    try:
        menu_node = parser.parse_menu(test_menu)
        if menu_node:
            print(f"\n🎉 SIMPLE CMAP parsing SUCCESS!")
            print(f"   Menu name: {menu_node.name}")
            print(f"   Choices: {len(menu_node.choices)}")
            
            for i, choice in enumerate(menu_node.choices):
                print(f"   Choice {i+1}: '{choice.text}'")
                print(f"     Body statements: {len(choice.body)}")
            
            return True
        else:
            print(f"\n❌ CMAP parsing returned None")
            return False
            
    except Exception as e:
        print(f"\n❌ CMAP parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_simple_menu()
