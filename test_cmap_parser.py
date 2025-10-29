#!/usr/bin/env python3
"""
Test CMAP (Custom Menu AST Parser) functionality.
"""

import sys
from pathlib import Path

# Add the CMAP module to path
app_dir = Path("app/renpy-source-api")
sys.path.insert(0, str(app_dir))

def test_cmap_parser():
    """Test CMAP parser with a simple menu."""
    print("🧪 TESTING CMAP (Custom Menu AST Parser)")
    print("=" * 50)
    
    try:
        from renpy_sdk.cmap import CMAPParser
        print("✅ CMAP imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import CMAP: {e}")
        return False
    
    # Create a test menu
    test_menu = '''menu:
    "Choice 1":
        jump label1
    "Choice 2" if score > 10:
        call function1
        return
    "Choice 3":
        pass'''
    
    print(f"\n📝 Test menu:")
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
            print(f"\n🎉 CMAP parsing SUCCESS!")
            print(f"   Menu name: {menu_node.name}")
            print(f"   Choices: {len(menu_node.choices)}")
            
            for i, choice in enumerate(menu_node.choices):
                print(f"   Choice {i+1}: '{choice.text}'")
                print(f"     Conditional: {choice.is_conditional}")
                if choice.condition:
                    print(f"     Condition: {choice.condition}")
                print(f"     Body statements: {len(choice.body)}")
                for j, stmt in enumerate(choice.body):
                    print(f"       {j+1}. {type(stmt).__name__}: {getattr(stmt, 'target', getattr(stmt, 'code', 'N/A'))}")
            
            return True
        else:
            print(f"\n❌ CMAP parsing returned None")
            return False
            
    except Exception as e:
        print(f"\n❌ CMAP parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ast_menu_parser_with_cmap():
    """Test ASTMenuParser with CMAP integration."""
    print("\n\n🧪 TESTING AST MENU PARSER WITH CMAP")
    print("=" * 50)
    
    try:
        from renpy_sdk.ast_menu_parser import ASTMenuParser
        print("✅ ASTMenuParser imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import ASTMenuParser: {e}")
        return False
    
    # Initialize parser
    try:
        parser = ASTMenuParser()
        print(f"✅ ASTMenuParser initialized")
        print(f"   Has AST: {parser.has_ast}")
        print(f"   Has CMAP: {parser.has_cmap}")
    except Exception as e:
        print(f"❌ Failed to initialize ASTMenuParser: {e}")
        return False
    
    # Create a test file
    test_file = "test_menu.rpy"
    test_content = '''label start:
    menu:
        "Go to park":
            jump park_scene
        "Stay home" if tired:
            "You decide to rest."
            return
        "Visit friend":
            call visit_friend
    return

menu named_menu:
    "Option A":
        $ flag = True
        jump option_a
    "Option B" if flag == False:
        jump option_b
'''
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print(f"\n📝 Created test file: {test_file}")
    
    # Parse the file
    try:
        menus = parser.parse_file_menus(test_file)
        print(f"\n🎉 Parsed {len(menus)} menus!")
        
        for i, menu in enumerate(menus):
            print(f"\n📋 Menu {i+1}:")
            print(f"   Line: {menu.line_number}")
            print(f"   Name: {menu.menu_name}")
            print(f"   Choices: {len(menu.choices)}")
            print(f"   Complexity: {menu.menu_complexity}")
            print(f"   Has conditionals: {menu.has_complex_conditionals}")
            
            for j, choice in enumerate(menu.choices):
                print(f"   ├─ Choice {j+1}: '{choice.text}'")
                print(f"   │  ├─ Conditional: {choice.is_conditional}")
                if choice.primary_condition:
                    print(f"   │  ├─ Condition: {choice.primary_condition}")
                print(f"   │  └─ Destinations: {choice.destinations}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ File parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up test file
        try:
            Path(test_file).unlink()
        except:
            pass

if __name__ == "__main__":
    success1 = test_cmap_parser()
    success2 = test_ast_menu_parser_with_cmap()
    
    print(f"\n🏁 FINAL RESULTS:")
    print(f"   CMAP Parser: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"   AST Integration: {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 and success2:
        print(f"\n🎉 ALL TESTS PASSED! CMAP is working correctly!")
    else:
        print(f"\n❌ Some tests failed. Check the output above.")
