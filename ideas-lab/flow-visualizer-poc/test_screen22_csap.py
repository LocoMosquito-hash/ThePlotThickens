#!/usr/bin/env python3
"""
Test screen22 with CSAP parser and show any errors.
"""
import sys
import codecs
import traceback

# Fix encoding on Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

def test_screen22():
    """Test the screen22 structure with full error reporting."""
    
    screen_text = """screen screen22:
    textbutton(""):
        area(320, 330, 200, 400)
        background "gui/button/yes.png"
        hover_background "gui/button/yesas.png"
        action Jump("day10yes")
"""
    
    print("Testing screen22 with CSAP...")
    print("=" * 70)
    
    try:
        from csap.csap_parser import CSAPParser
        
        parser = CSAPParser()
        
        print("\n[PARSING]")
        screen_node = parser.parse_screen_text(screen_text)
        
        print(f"  ✅ Parsed successfully!")
        print(f"  Screen name: {screen_node.screen_name}")
        print(f"  Top-level elements: {len(screen_node.elements)}")
        
        interactive = screen_node.get_interactive_elements()
        print(f"  Interactive elements: {len(interactive)}")
        
        for i, elem in enumerate(interactive):
            action_type = elem.action.action_type if elem.action else "None"
            destination = elem.action.destination if elem.action else "N/A"
            print(f"    {i+1}. {type(elem).__name__}: {action_type} -> {destination}")
        
        return 0 if len(interactive) == 1 else 1
        
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_screen22())

