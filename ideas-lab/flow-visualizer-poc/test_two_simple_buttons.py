#!/usr/bin/env python3
"""
Test two simple textbuttons.
"""
import sys
import codecs

# Fix encoding on Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

def test_two_buttons():
    """Test two simple buttons."""
    
    screen_text = """screen screen22:
    textbutton("Yes"):
        area(320, 330, 200, 400)
        background "gui/button/yes.png"
        hover_background "gui/button/yesas.png"
        action Jump("day10yes")
    
    textbutton("No"):
        area(1400, 500, 200, 500)
        background "gui/button/no.png"
        hover_background "gui/button/noa.png"
        action Jump("day10no")
"""
    
    print("Testing two simple textbuttons...")
    
    from csap.csap_parser import CSAPParser
    parser = CSAPParser()
    
    try:
        screen_node = parser.parse_screen_text(screen_text)
        interactive = screen_node.get_interactive_elements()
        
        print(f"  Elements: {len(interactive)}")
        for i, elem in enumerate(interactive):
            if elem.action:
                print(f"    {i+1}. {elem.action.action_type} -> {elem.action.destination}")
        
        if len(interactive) == 2:
            print("\n✅ SUCCESS!")
        else:
            print(f"\n❌ Expected 2, got {len(interactive)}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_two_buttons()

