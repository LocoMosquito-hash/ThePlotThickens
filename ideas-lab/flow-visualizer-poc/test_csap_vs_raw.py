#!/usr/bin/env python3
"""
Compare CSAPParser vs raw Lark parsing.
"""
import sys
import codecs
from pathlib import Path

# Fix encoding on Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

def test_both():
    """Test both approaches."""
    
    screen_text = """screen screen22:
    textbutton(""):
        area(320, 330, 200, 400)
        background "gui/button/yes.png"
        hover_background "gui/button/yesas.png"
        action Jump("day10yes")
"""
    
    print("Testing CSAPParser...")
    try:
        from csap.csap_parser import CSAPParser
        parser = CSAPParser()
        screen_node = parser.parse_screen_text(screen_text)
        interactive = screen_node.get_interactive_elements()
        print(f"  CSAPParser result: {len(interactive)} elements")
    except Exception as e:
        print(f"  CSAPParser error: {e}")
    
    print("\nTesting raw Lark + transformer...")
    try:
        from lark import Lark
        from csap.csap_parser import RenpyIndenter, CSAPTransformer
        
        grammar_path = Path("csap/grammars/enhanced_screen.lark")
        grammar_text = grammar_path.read_text(encoding='utf-8')
        
        lark_parser = Lark(grammar_text, start='start', parser='earley', postlex=RenpyIndenter())
        tree = lark_parser.parse(screen_text)
        transformer = CSAPTransformer()
        screen_node = transformer.transform(tree)
        interactive = screen_node.get_interactive_elements()
        print(f"  Raw Lark result: {len(interactive)} elements")
    except Exception as e:
        print(f"  Raw Lark error: {e}")

if __name__ == "__main__":
    test_both()

