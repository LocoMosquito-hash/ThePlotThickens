#!/usr/bin/env python3
"""
Test simple multi-line textbutton WITHOUT area() to isolate the issue.
"""
import sys
import codecs

# Fix encoding on Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

def test_simple():
    """Test a simple multi-line textbutton without area()."""
    
    # Test 1: Simple with just action
    test1 = """screen test1:
    textbutton("Click"):
        action Jump("label1")
"""
    
    # Test 2: With background property
    test2 = """screen test2:
    textbutton("Click"):
        background "image.png"
        action Jump("label1")
"""
    
    # Test 3: With identifier property
    test3 = """screen test3:
    textbutton("Click"):
        xalign 0.5
        action Jump("label1")
"""
    
    tests = [
        ("Just action", test1),
        ("With background", test2),
        ("With xalign", test3)
    ]
    
    from csap.csap_parser import CSAPParser
    parser = CSAPParser()
    
    for name, screen_text in tests:
        print(f"\n{'='*70}")
        print(f"Testing: {name}")
        print(f"{'='*70}")
        try:
            screen_node = parser.parse_screen_text(screen_text)
            interactive = screen_node.get_interactive_elements()
            print(f"  ✅ Parsed: {len(interactive)} interactive elements")
            
            if len(interactive) > 0:
                elem = interactive[0]
                print(f"     Type: {type(elem).__name__}")
                print(f"     Action: {elem.action.action_type if elem.action else 'None'}")
                print(f"     Destination: {elem.action.destination if elem.action else 'N/A'}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    test_simple()

