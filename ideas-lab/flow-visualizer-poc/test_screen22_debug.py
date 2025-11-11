#!/usr/bin/env python3
"""
Debug screen22 parsing issues step by step.
"""
import sys
import codecs
from pathlib import Path

# Fix encoding on Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

def test_variations():
    """Test different variations to isolate the problem."""
    
    from lark import Lark
    from csap.csap_parser import RenpyIndenter
    
    grammar_path = Path("csap/grammars/enhanced_screen.lark")
    grammar_text = grammar_path.read_text(encoding='utf-8')
    
    parser = Lark(grammar_text, start='start', parser='lalr', postlex=RenpyIndenter())
    
    # Test 1: Simple textbutton with empty string
    test1 = """screen test():
    textbutton("") action Jump("label1")
"""
    
    # Test 2: Without extra blank lines
    test2 = """screen screen22:
    textbutton(""):
        area(320, 330, 200, 400)
        action Jump("day10yes")
"""
    
    # Test 3: With extra blank lines (original)
    test3 = """screen screen22:


    textbutton(""):
        area(320, 330, 200, 400)
        action Jump("day10yes")
"""
    
    tests = [
        ("Simple empty string", test1),
        ("Multi-line without blank lines", test2),
        ("Multi-line with blank lines", test3)
    ]
    
    for name, test_code in tests:
        print(f"\n{'='*70}")
        print(f"Testing: {name}")
        print(f"{'='*70}")
        try:
            tree = parser.parse(test_code)
            print("✅ Lark parse SUCCESS")
        except Exception as e:
            print(f"❌ Lark parse FAILED: {e}")
            # Show first 200 chars of error
            error_str = str(e)
            if len(error_str) > 200:
                print(f"   {error_str[:200]}...")
            else:
                print(f"   {error_str}")

if __name__ == "__main__":
    test_variations()

