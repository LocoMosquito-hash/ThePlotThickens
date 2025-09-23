#!/usr/bin/env python3

import sys
import os

# Add the CSAP path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ideas-lab', 'flow-visualizer-poc', 'csap'))

try:
    from csap_parser import CSAPParser
    from conditional_blind_parser import ConditionalBlindParser
    csap_available = True
except ImportError as e:
    print(f"Warning: Could not import CSAP: {e}")
    csap_available = False

def debug_csap_vs_fallback():
    """Compare what CSAP finds vs what conditional-blind finds."""
    
    if not csap_available:
        print("❌ CSAP not available")
        return
    
    # The exact screen content from Amnesia
    screen_text = '''screen act_1d1_Bedroom_MC_Wardrobe:
    imagebutton anchor (0.5, 0.5):
        xoffset 960 yoffset 920
        idle "images/Free Roams/Back BTN idle.webp"
        hover "images/Free Roams/Back BTN hover.webp"
        action Jump ("act_1d1_FreeRoam_Home.Bedroom_MC")

    if task_1d1_Change_Clothing == 1:
        imagebutton:
            focus_mask True
            idle "images/1d1/Buttons/Bedroom MC Wardrobe clothing BTN idle.webp"
            hover "images/1d1/Buttons/Bedroom MC Wardrobe clothing BTN hover.webp"
            action Jump ("d1_1_ChanageCloting")
            tooltip _("Change clothing")

    imagebutton:
        focus_mask True
        idle "images/Free Roams/Home/Bedroom MC/Buttons/Bedroom MC wardrobe BTN idle.webp"
        hover "images/Free Roams/Home/Bedroom MC/Buttons/Bedroom MC wardrobe BTN hover.webp"
        action [Play ("sound", "audio/FX/FX wardrobe.mp3"), Jump ("act_1d1_FreeRoam_Home.Bedroom_MC_Wardrobe_Panty")]

    use tooltip_screen
'''
    
    print("=== CSAP vs CONDITIONAL-BLIND COMPARISON ===")
    
    try:
        # Test CSAP
        csap_parser = CSAPParser()
        csap_result = csap_parser.parse_screen_text(screen_text, "test.rpy")
        
        print("🔍 CSAP Results:")
        print(f"  Screen name: {csap_result.screen_name}")
        print(f"  Total elements: {len(csap_result.elements)}")
        
        csap_interactive = csap_result.get_interactive_elements()
        print(f"  Interactive elements: {len(csap_interactive)}")
        
        for i, element in enumerate(csap_interactive, 1):
            print(f"    {i}. {type(element).__name__}")
            if hasattr(element, 'action') and element.action:
                print(f"       Action: {element.action.action_type} → {element.action.destination}")
            if hasattr(element, 'line_number'):
                print(f"       Line: {element.line_number}")
        
        # Test Conditional-Blind
        cb_parser = ConditionalBlindParser()
        cb_result = cb_parser.parse_screen_text(screen_text)
        
        print(f"\n🔍 Conditional-Blind Results:")
        print(f"  Total elements: {len(cb_result)}")
        
        for i, element in enumerate(cb_result, 1):
            print(f"    {i}. {element.element_type}")
            print(f"       Action: {element.action_type} → {element.destination}")
            print(f"       Line: {element.line_number}")
        
        # Compare destinations
        print(f"\n📊 Comparison:")
        
        csap_destinations = set()
        for elem in csap_interactive:
            if hasattr(elem, 'action') and elem.action:
                csap_destinations.add(elem.action.destination)
        
        cb_destinations = set(elem.destination for elem in cb_result)
        
        print(f"  CSAP destinations: {sorted(csap_destinations)}")
        print(f"  CB destinations: {sorted(cb_destinations)}")
        
        missing_in_csap = cb_destinations - csap_destinations
        missing_in_cb = csap_destinations - cb_destinations
        
        if missing_in_csap:
            print(f"  ❌ Missing in CSAP: {sorted(missing_in_csap)}")
        if missing_in_cb:
            print(f"  ❌ Missing in CB: {sorted(missing_in_cb)}")
        
        if not missing_in_csap and not missing_in_cb:
            print(f"  ✅ Both parsers found the same destinations")
        
        # Analyze why CSAP might be missing elements
        print(f"\n🔍 CSAP Analysis:")
        
        if len(csap_interactive) < len(cb_result):
            print(f"  🐛 CSAP found fewer elements ({len(csap_interactive)} vs {len(cb_result)})")
            print(f"     Possible causes:")
            print(f"     - Grammar doesn't support 'anchor' property")
            print(f"     - Conditional blocks not handled properly")
            print(f"     - Complex action syntax not supported")
            print(f"     - Multiline imagebutton definitions issue")
            
            # Check for specific patterns
            if 'anchor' in screen_text:
                print(f"     - Screen uses 'anchor' property (might not be supported)")
            if 'if ' in screen_text:
                print(f"     - Screen has conditional blocks (might not be handled)")
            if 'action [' in screen_text:
                print(f"     - Screen has complex actions with lists (might not be supported)")
        
        # Test if fallback should be triggered with a lower threshold
        print(f"\n💡 Fallback Analysis:")
        
        if len(csap_interactive) < len(cb_result):
            print(f"  Current fallback threshold: 0 elements")
            print(f"  CSAP found: {len(csap_interactive)} elements")
            print(f"  CB found: {len(cb_result)} elements")
            print(f"  💡 Consider: Trigger fallback if CSAP finds < CB elements")
            print(f"     Or: Merge CSAP + CB results when CB finds more")
        
    except Exception as e:
        print(f"❌ Comparison failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_csap_vs_fallback()
