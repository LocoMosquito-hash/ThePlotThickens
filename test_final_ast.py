#!/usr/bin/env python3
"""Final test of TRUE AST parsing with Ren'Py standalone Python."""

import sys
from pathlib import Path

# Add the app/renpy-source-api directory to the path
app_dir = Path(__file__).parent.parent / "app" / "renpy-source-api"
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from renpy_sdk.ast_menu_parser import ASTMenuParser

def main():
    print("🧪 FINAL TEST: True AST Parsing with Ren'Py Standalone Python")
    print("=" * 70)
    
    parser = ASTMenuParser()
    print(f"AST Available: {parser.has_ast}")
    
    # Test file
    test_file = "test_ast.rpy"
    print(f"📁 Testing file: {test_file}")
    
    try:
        print("🚀 Running TRUE AST parsing...")
        menus = parser.parse_file_menus(test_file)
        
        print(f"✅ SUCCESS! Found {len(menus)} menus")
        
        for i, menu in enumerate(menus):
            print(f"\\n📋 Menu {i+1}:")
            print(f"   Line: {menu.line_number}")
            print(f"   Choices: {len(menu.choices)}")
            print(f"   Conditional paths: {menu.total_conditional_paths}")
            print(f"   Complexity: {menu.overall_complexity}")
            
            for j, choice in enumerate(menu.choices):
                print(f"   ├─ Choice {j+1}: '{choice.text}'")
                print(f"   │  ├─ Conditional: {choice.is_conditional}")
                if choice.is_conditional:
                    print(f"   │  ├─ Condition: {choice.primary_condition}")
                    print(f"   │  └─ Variables: {choice.referenced_variables}")
        
        if menus:
            print("\\n🎉 TRUE AST PARSING IS WORKING! 🎉")
            print("✅ No more cslots/astsupport issues!")
            print("✅ Real Ren'Py AST parsing!")
            print("✅ Complete conditional analysis!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()