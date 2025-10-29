#!/usr/bin/env python3
"""
Debug Lark grammar parsing step by step.
"""

from lark import Lark

# Test with a minimal grammar
test_grammar = '''
start: menu_definition

menu_definition: "menu" ":" menu_body

menu_body: menu_item+

menu_item: simple_choice | conditional_choice

simple_choice: STRING ":" "pass"

conditional_choice: STRING "if" IDENTIFIER ":" "pass"

%import common.WS
%ignore WS

STRING: /"[^"]*"/
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/
'''

def test_minimal_grammar():
    """Test with minimal grammar."""
    print("🧪 MINIMAL GRAMMAR TEST")
    print("=" * 30)
    
    try:
        parser = Lark(test_grammar, parser='lalr')
        print("✅ Grammar compiled")
        
        # Test simple menu
        simple_test = '''menu:
    "Choice 1":
        pass'''
        
        print("\n📝 Testing simple menu:")
        print(simple_test)
        
        try:
            tree = parser.parse(simple_test)
            print("✅ Simple menu parsed!")
            print(f"Tree: {tree.pretty()}")
        except Exception as e:
            print(f"❌ Simple menu failed: {e}")
        
        # Test conditional menu
        conditional_test = '''menu:
    "Choice 1" if flag:
        pass'''
        
        print("\n📝 Testing conditional menu:")
        print(conditional_test)
        
        try:
            tree = parser.parse(conditional_test)
            print("✅ Conditional menu parsed!")
            print(f"Tree: {tree.pretty()}")
        except Exception as e:
            print(f"❌ Conditional menu failed: {e}")
            
    except Exception as e:
        print(f"❌ Grammar compilation failed: {e}")

if __name__ == "__main__":
    test_minimal_grammar()
