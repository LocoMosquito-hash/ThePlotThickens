#!/usr/bin/env python3
"""
Test screen22 WITHOUT extra blank lines.
"""
import sys
import codecs

# Fix encoding on Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

def test_no_blanks():
    """Test without extra blank lines."""
    
    screen_text = """screen screen22:
    textbutton(""):
        area(320, 330, 200, 400)
        background "gui/button/yes.png"
        hover_background "gui/button/yesas.png"
        action Jump("day10yes")
    
    textbutton(""):
        area(1400, 500, 200, 500)
        background im.MatrixColor("gui/button/no.png", im.matrix.desaturate())
        hover_background "gui/button/noa.png"
        action Jump("day10no")
"""
    
    print("Testing screen22 WITHOUT extra blank lines...")
    print("=" * 70)
    
    from csap.csap_parser import CSAPParser
    parser = CSAPParser()
    
    try:
        screen_node = parser.parse_screen_text(screen_text)
        
        interactive = screen_node.get_interactive_elements()
        print(f"  Interactive elements: {len(interactive)}")
        
        for i, elem in enumerate(interactive):
            if elem.action:
                print(f"    {i+1}. {elem.action.action_type} -> {elem.action.destination}")
        
        if len(interactive) == 2:
            print("\n✅ SUCCESS: Both buttons found!")
            return 0
        else:
            print(f"\n❌ FAILED: Expected 2, got {len(interactive)}")
            return 1
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(test_no_blanks())

