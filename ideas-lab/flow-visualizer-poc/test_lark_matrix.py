#!/usr/bin/env python3
"""
Test im.MatrixColor with raw Lark.
"""
import sys
import codecs
from pathlib import Path

# Fix encoding on Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

def test_lark():
    """Test with Lark."""
    
    from lark import Lark
    from csap.csap_parser import RenpyIndenter
    
    grammar_path = Path("csap/grammars/enhanced_screen.lark")
    grammar_text = grammar_path.read_text(encoding='utf-8')
    
    parser = Lark(grammar_text, start='start', parser='earley', postlex=RenpyIndenter())
    
    screen_text = """screen test:
    textbutton("Click"):
        background im.MatrixColor("image.png", im.matrix.desaturate())
        action Jump("label1")
"""
    
    print("Testing im.MatrixColor with Lark...")
    try:
        tree = parser.parse(screen_text)
        print("✅ Lark parse SUCCESS\n")
        print(tree.pretty()[:1000])  # First 1000 chars
    except Exception as e:
        print(f"❌ Lark parse FAILED: {e}")

if __name__ == "__main__":
    test_lark()

