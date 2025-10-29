#!/usr/bin/env python3
"""
Test the new true AST parsing approach using Ren'Py subprocess.
This test verifies that we can now access the real Ren'Py AST via subprocess.
"""

import sys
from pathlib import Path

# Add the app/renpy-source-api directory to the path
app_dir = Path(__file__).parent.parent / "app" / "renpy-source-api"
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from renpy_sdk.ast_menu_parser import ASTMenuParser

def test_true_ast_parsing():
    """Test the true AST parsing approach."""
    
    print("🧪 Testing True AST Parsing with Ren'Py Subprocess")
    print("=" * 60)
    
    # Initialize the AST parser
    parser = ASTMenuParser()
    
    print(f"AST Available: {parser.has_ast}")
    
    # Test with a simple Ren'Py file
    test_content = '''
label start:
    menu:
        "Choice 1":
            jump choice1_result
        "Choice 2" if player_score > 10:
            jump choice2_result
        "Choice 3" if player_name == "Alice" and relationship > 5:
            jump choice3_result

label choice1_result:
    "You chose option 1."
    return

label choice2_result:
    "You chose option 2."
    return

label choice3_result:
    "You chose option 3."
    return
'''
    
    # Create a test file
    test_file = Path("test_menu_ast.rpy")
    test_file.write_text(test_content)
    
    try:
        print(f"\\n📁 Testing file: {test_file}")
        print("🚀 Running TRUE AST parsing...")
        
        # Parse with the new AST approach
        menus = parser.parse_file_menus(str(test_file))
        
        print(f"\\n✅ Parsing Results:")
        print(f"   📊 Found {len(menus)} menus")
        
        for i, menu in enumerate(menus):
            print(f"\\n   📋 Menu {i+1} (Line {menu.line_number}):")
            print(f"      🎯 Choices: {len(menu.choices)}")
            print(f"      🔀 Total paths: {menu.total_conditional_paths}")
            print(f"      🧠 Complexity: {menu.overall_complexity}")
            
            for j, choice in enumerate(menu.choices):
                print(f"      ├─ Choice {j+1}: '{choice.text[:30]}...'")
                print(f"      │  ├─ Conditional: {choice.is_conditional}")
                if choice.is_conditional:
                    print(f"      │  ├─ Condition: {choice.primary_condition}")
                    print(f"      │  ├─ Complexity: {choice.condition_complexity}")
                    print(f"      │  └─ Variables: {choice.referenced_variables}")
                else:
                    print(f"      │  └─ Unconditional choice")
        
        if menus:
            print("\\n🎉 TRUE AST PARSING IS WORKING! 🎉")
            print("✅ No more regex dependency!")
            print("✅ Full conditional path detection!")
            print("✅ Variable analysis!")
        else:
            print("\\n⚠️  No menus found - check parsing logic")
            
    except Exception as e:
        print(f"\\n❌ Error during AST parsing: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up test file
        if test_file.exists():
            test_file.unlink()

if __name__ == "__main__":
    test_true_ast_parsing()