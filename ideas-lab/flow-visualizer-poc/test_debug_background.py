#!/usr/bin/env python3
"""
Debug why background property causes textbutton to disappear.
"""
import sys
import codecs

# Fix encoding on Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

def test_background():
    """Test background property and check transformation."""
    
    screen_text = """screen test:
    textbutton("Click"):
        background "image.png"
        action Jump("label1")
"""
    
    from csap.csap_parser import CSAPParser
    parser = CSAPParser()
    
    print("Parsing screen with background property...")
    try:
        screen_node = parser.parse_screen_text(screen_text)
        
        print(f"\n[SCREEN NODE]")
        print(f"  Name: {screen_node.screen_name}")
        print(f"  Elements: {len(screen_node.elements)}")
        
        for i, elem in enumerate(screen_node.elements):
            print(f"\n  Element {i}: {type(elem).__name__}")
            if hasattr(elem, 'properties'):
                print(f"    Properties: {len(elem.properties)}")
                for prop in elem.properties:
                    print(f"      - {prop.property_name} = {prop.property_value}")
            if hasattr(elem, 'action') and elem.action:
                print(f"    Action: {elem.action.action_type} -> {elem.action.destination}")
        
        interactive = screen_node.get_interactive_elements()
        print(f"\n[INTERACTIVE ELEMENTS]")
        print(f"  Count: {len(interactive)}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_background()

