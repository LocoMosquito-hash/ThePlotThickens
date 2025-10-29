#!/usr/bin/env python3
"""
Test if grammar changes are being loaded properly.
"""

import sys
from pathlib import Path

# Add the CMAP module to path
app_dir = Path("app/renpy-source-api")
sys.path.insert(0, str(app_dir))

def test_grammar_reload():
    """Test if grammar changes are loaded."""
    print("🧪 TESTING GRAMMAR RELOAD")
    print("=" * 40)
    
    # Read the current grammar file
    grammar_file = Path("app/renpy-source-api/renpy_sdk/cmap/menu_grammar.lark")
    with open(grammar_file, 'r') as f:
        grammar_content = f.read()
    
    print("📝 Current grammar content (relevant parts):")
    lines = grammar_content.split('\n')
    for i, line in enumerate(lines):
        if 'conditional_expression' in line or 'CONDITION_TEXT' in line or 'condition_text' in line:
            print(f"Line {i+1}: {line}")
    
    # Try to create a fresh parser instance
    try:
        from renpy_sdk.cmap import CMAPParser
        print("\n✅ CMAP imported successfully")
        
        # Create new parser instance
        parser = CMAPParser()
        print("✅ CMAP parser created")
        
        # Check if the grammar file exists and is readable
        print(f"Grammar file exists: {parser.grammar_file.exists()}")
        print(f"Grammar file path: {parser.grammar_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_grammar_reload()
