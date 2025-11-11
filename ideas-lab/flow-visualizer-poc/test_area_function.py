#!/usr/bin/env python3
"""
Test area() function call parsing.
"""
import sys
import codecs
from pathlib import Path

# Fix encoding on Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

def test_area():
    """Test area() function call."""
    
    from lark import Lark
    from csap.csap_parser import RenpyIndenter
    
    grammar_path = Path("csap/grammars/enhanced_screen.lark")
    grammar_text = grammar_path.read_text(encoding='utf-8')
    
    parser = Lark(grammar_text, start='start', parser='earley', postlex=RenpyIndenter())
    
    screen_text = """screen test:
    textbutton("Click"):
        area(320, 330, 200, 400)
        action Jump("label1")
"""
    
    print("Testing Lark parse with area()...")
    try:
        tree = parser.parse(screen_text)
        print("✅ Lark parse SUCCESS\n")
        print(tree.pretty())
    except Exception as e:
        print(f"❌ Lark parse FAILED: {e}")

if __name__ == "__main__":
    test_area()

