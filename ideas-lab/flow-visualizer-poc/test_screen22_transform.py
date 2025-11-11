#!/usr/bin/env python3
"""
Test screen22 transformation with debug output.
"""
import sys
import codecs
from pathlib import Path

# Fix encoding on Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

def test_transform():
    """Test transformation with debug output."""
    
    from lark import Lark
    from csap.csap_parser import RenpyIndenter, CSAPTransformer
    
    grammar_path = Path("csap/grammars/enhanced_screen.lark")
    grammar_text = grammar_path.read_text(encoding='utf-8')
    
    parser = Lark(grammar_text, start='start', parser='earley', postlex=RenpyIndenter())
    
    screen_text = """screen screen22:
    textbutton(""):
        area(320, 330, 200, 400)
        background "gui/button/yes.png"
        hover_background "gui/button/yesas.png"
        action Jump("day10yes")
"""
    
    print("Testing transformation...")
    try:
        tree = parser.parse(screen_text)
        print("✅ Lark parse SUCCESS\n")
        
        transformer = CSAPTransformer()
        screen_node = transformer.transform(tree)
        
        print(f"[SCREEN NODE]")
        print(f"  Name: {screen_node.screen_name}")
        print(f"  Elements: {len(screen_node.elements)}")
        
        for i, elem in enumerate(screen_node.elements):
            print(f"    {i}. {type(elem).__name__}")
        
        interactive = screen_node.get_interactive_elements()
        print(f"\n[INTERACTIVE]")
        print(f"  Count: {len(interactive)}")
        
        for i, elem in enumerate(interactive):
            print(f"    {i}. {type(elem).__name__}")
            if elem.action:
                print(f"       Action: {elem.action.action_type} -> {elem.action.destination}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_transform()

