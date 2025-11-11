#!/usr/bin/env python3
"""
Test the complete screen22 with both textbuttons.
"""
import sys
import codecs

# Fix encoding on Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

def test_full_screen():
    """Test the complete user-provided screen."""
    
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
    
    print("Testing complete screen22...")
    print("=" * 70)
    
    from csap.csap_parser import CSAPParser
    parser = CSAPParser()
    
    try:
        screen_node = parser.parse_screen_text(screen_text)
        
        print(f"\n✅ Parsed successfully!")
        print(f"  Screen: {screen_node.screen_name}")
        print(f"  Elements: {len(screen_node.elements)}")
        
        interactive = screen_node.get_interactive_elements()
        print(f"  Interactive: {len(interactive)}")
        
        for i, elem in enumerate(interactive):
            print(f"\n  Button {i+1}:")
            print(f"    Type: {type(elem).__name__}")
            if elem.action:
                print(f"    Action: {elem.action.action_type} -> {elem.action.destination}")
            if elem.properties:
                print(f"    Properties: {len(elem.properties)}")
                for prop in elem.properties:
                    print(f"      - {prop.property_name}: {prop.property_value[:50] if len(str(prop.property_value)) > 50 else prop.property_value}")
        
        if len(interactive) == 2:
            print(f"\n{'='*70}")
            print("✅ SUCCESS: Both textbuttons parsed correctly!")
            print(f"{'='*70}")
            return 0
        else:
            print(f"\n❌ FAILED: Expected 2 buttons, got {len(interactive)}")
            return 1
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_full_screen())

