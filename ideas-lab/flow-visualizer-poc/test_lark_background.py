#!/usr/bin/env python3
"""
Test Lark parsing directly for background property.
"""
import sys
import codecs
from pathlib import Path

# Fix encoding on Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

def test_lark_background():
    """Test Lark parser directly."""
    
    from lark import Lark
    from csap.csap_parser import RenpyIndenter
    
    grammar_path = Path("csap/grammars/enhanced_screen.lark")
    grammar_text = grammar_path.read_text(encoding='utf-8')
    
    parser = Lark(grammar_text, start='start', parser='earley', postlex=RenpyIndenter())
    
    screen_text = """screen test:
    textbutton("Click"):
        background "image.png"
        action Jump("label1")
"""
    
    print("Testing Lark parse...")
    try:
        tree = parser.parse(screen_text)
        print("✅ Lark parse SUCCESS")
        print("\nParse tree:")
        print(tree.pretty())
    except Exception as e:
        print(f"❌ Lark parse FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_lark_background()

