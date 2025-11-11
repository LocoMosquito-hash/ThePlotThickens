#!/usr/bin/env python3
"""
Test screen22 structure to identify parsing issues.
"""
import sys
import codecs

# Fix encoding on Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

def test_screen22():
    """Test the screen22 structure."""
    
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
    
    print("Testing screen22 structure...")
    print("=" * 70)
    
    try:
        from csap.csap_parser import CSAPParser
        from csap.csap_compatibility import convert_csap_to_screen_structure
        
        parser = CSAPParser()
        
        print("\n[PARSING WITH CSAP]")
        screen_node = parser.parse_screen_text(screen_text)
        
        print(f"  Screen name: {screen_node.screen_name}")
        print(f"  Top-level elements: {len(screen_node.elements)}")
        
        interactive = screen_node.get_interactive_elements()
        print(f"  Interactive elements: {len(interactive)}")
        
        for i, elem in enumerate(interactive):
            action_type = elem.action.action_type if elem.action else "None"
            destination = elem.action.destination if elem.action else "N/A"
            print(f"    {i+1}. {type(elem).__name__}: {action_type} -> {destination}")
        
        print(f"\n[CONVERTING TO SCREEN STRUCTURE]")
        screen_structure = convert_csap_to_screen_structure(screen_node, "test.rpy")
        print(f"  ScreenStructure elements: {len(screen_structure.elements)}")
        
        if len(screen_structure.elements) == 2:
            print(f"\n✅ SUCCESS: Both textbuttons parsed!")
            return 0
        else:
            print(f"\n❌ FAILED: Expected 2 elements, got {len(screen_structure.elements)}")
            return 1
        
    except Exception as e:
        print(f"\n❌ Parse Exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_screen22())

