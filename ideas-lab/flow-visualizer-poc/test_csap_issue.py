#!/usr/bin/env python3
"""
Test script to debug CSAP parsing issue with if/elif/else statements.
"""

import sys
from pathlib import Path

# Add CSAP to path
sys.path.insert(0, str(Path(__file__).parent))

from csap.csap_parser import CSAPParser
from csap.csap_exceptions import CSAPError

# The problematic screen from Desire of Fate
test_screen = '''screen freeplay_trainStation_ep2v1office():
    if ep2v1ofr == "ep2v1_Office_openspace_Freeroam":
        imagebutton auto "images/ep2v1/ep2v1freeroam/ep2v1_freeroam_left_%s.png" focus_mask True hover_sound sound_menu_button action Hide("freeplay_trainStation_ep2v1office"), SetVariable("ep2v1ofr", "ep2v1_Office_jessicaroom_Freeroam"), Jump("ep2v1_Office_jessicaroom_Freeroam")
        imagebutton auto "images/ep2v1/ep2v1freeroam/ep2v1_freeroam_right_%s.png" focus_mask True hover_sound sound_menu_button action Hide("freeplay_trainStation_ep2v1office"), SetVariable("ep2v1ofr", "ep2v1_Office_seniors_Freeroam"), Jump("ep2v1_Office_seniors_Freeroam")
        imagebutton auto "images/ep2v1/ep2v1freeroam/ep2v1_freeroam_openspace_allen_%s.png" focus_mask True hover_sound sound_menu_button action Hide("freeplay_trainStation_ep2v1office"), Jump("ep2v1_Office_Allen_Conv")
        imagebutton auto "images/ep2v1/ep2v1freeroam/ep2v1_freeroam_openspace_thea_%s.png" focus_mask True hover_sound sound_menu_button action Hide("freeplay_trainStation_ep2v1office"), Jump("ep2v1_Office_Thea_Conv")

    elif ep2v1ofr == "ep2v1_Office_jessicaroom_Freeroam":
        imagebutton auto "images/ep2v1/ep2v1freeroam/ep2v1_freeroam_right_%s.png" focus_mask True hover_sound sound_menu_button action Hide("freeplay_trainStation_ep2v1office"), SetVariable("ep2v1ofr", "ep2v1_Office_openspace_Freeroam"), Jump("ep2v1_Office_openspace_Freeroam")
        imagebutton auto "images/ep2v1/ep2v1freeroam/ep2v1_freeroam_jess_jessica_%s.png" focus_mask True hover_sound sound_menu_button action Hide("freeplay_trainStation_ep2v1office"), Jump("ep2v1_Office_jessicaroom_conv")

    elif ep2v1ofr == "ep2v1_Office_seniors_Freeroam":
        imagebutton auto "images/ep2v1/ep2v1freeroam/ep2v1_freeroam_left_%s.png" focus_mask True hover_sound sound_menu_button action Hide("freeplay_trainStation_ep2v1office"), SetVariable("ep2v1ofr", "ep2v1_Office_openspace_Freeroam"), Jump("ep2v1_Office_openspace_Freeroam")
        imagebutton auto "images/ep2v1/ep2v1freeroam/ep2v1_freeroam_right_%s.png" focus_mask True hover_sound sound_menu_button action Hide("freeplay_trainStation_ep2v1office"), SetVariable("ep2v1ofr", "ep2v1_Office_chisaroom_Freeroam"), Jump("ep2v1_Office_chisaroom_Freeroam")
        imagebutton auto "images/ep2v1/ep2v1freeroam/ep2v1_freeroam_seniors_henry_%s.png" focus_mask True hover_sound sound_menu_button action Hide("freeplay_trainStation_ep2v1office"), Jump("ep2v1_Office_Henry_Conv")
        imagebutton auto "images/ep2v1/ep2v1freeroam/ep2v1_freeroam_seniors_jeff_%s.png" focus_mask True hover_sound sound_menu_button action Hide("freeplay_trainStation_ep2v1office"), Jump("ep2v1_Office_Jeff_Conv")
        imagebutton auto "images/ep2v1/ep2v1freeroam/ep2v1_freeroam_seniors_laura_%s.png" focus_mask True hover_sound sound_menu_button action Hide("freeplay_trainStation_ep2v1office"), Jump("ep2v1_Office_Laura_Conv")

    elif ep2v1ofr == "ep2v1_Office_chisaroom_Freeroam":
        imagebutton auto "images/ep2v1/ep2v1freeroam/ep2v1_freeroam_left_%s.png" focus_mask True hover_sound sound_menu_button action Hide("freeplay_trainStation_ep2v1office"), SetVariable("ep2v1ofr", "ep2v1_Office_seniors_Freeroam"), Jump("ep2v1_Office_seniors_Freeroam")
        imagebutton auto "images/ep2v1/ep2v1freeroam/ep2v1_freeroam_right_%s.png" focus_mask True hover_sound sound_menu_button action Hide("freeplay_trainStation_ep2v1office"), SetVariable("ep2v1ofr", "ep2v1_Office_IT_room_Freeroam"), Jump("ep2v1_Office_IT_room_Freeroam")
        imagebutton auto "images/ep2v1/ep2v1freeroam/ep2v1_freeroam_chisa_chisa_%s.png" focus_mask True hover_sound sound_menu_button action Hide("freeplay_trainStation_ep2v1office"), Jump("ep2v1_Office_Chisa_Conv")

    elif ep2v1ofr == "ep2v1_Office_IT_room_Freeroam":
        imagebutton auto "images/ep2v1/ep2v1freeroam/ep2v1_freeroam_left_%s.png" focus_mask True hover_sound sound_menu_button action Hide("freeplay_trainStation_ep2v1office"), SetVariable("ep2v1ofr", "ep2v1_Office_chisaroom_Freeroam"), Jump("ep2v1_Office_chisaroom_Freeroam")
        imagebutton auto "images/ep2v1/ep2v1freeroam/ep2v1_freeroam_elio_%s.png" focus_mask True hover_sound sound_menu_button action Hide("freeplay_trainStation_ep2v1office"), Jump("ep2v1_Office_elio_Conv")
        imagebutton auto "images/ep2v1/ep2v1freeroam/ep2v1_freeroam_ozzy_%s.png" focus_mask True hover_sound sound_menu_button action Hide("freeplay_trainStation_ep2v1office"), Jump("ep2v1_Office_Ozzy_Conv")
'''

print("Testing CSAP parsing with if/elif/else statements...")
print("=" * 70)

try:
    parser = CSAPParser()
    screen_node = parser.parse_screen_text(test_screen, "test_screen")
    
    print("[SUCCESS] Parsing successful!")
    print(f"Screen name: {screen_node.screen_name}")
    print(f"Total elements: {len(screen_node.elements)}")
    
    # Debug: Show what elements were parsed
    print("\nElements in screen:")
    for i, elem in enumerate(screen_node.elements):
        elem_type = type(elem).__name__
        if hasattr(elem, 'element_type'):
            print(f"  {i+1}. {elem_type} (element_type: {elem.element_type})")
        else:
            print(f"  {i+1}. {elem_type}")
        
        # If it's a conditional, show branches
        if hasattr(elem, 'branches'):
            print(f"      Branches: {len(elem.branches)}")
            for j, branch in enumerate(elem.branches):
                print(f"        Branch {j+1}: {branch.branch_type}, body items: {len(branch.body)}")
                for k, body_item in enumerate(branch.body):
                    body_type = type(body_item).__name__
                    if hasattr(body_item, 'action') and body_item.action:
                        print(f"          Item {k+1}: {body_type} -> {body_item.action.action_type}({body_item.action.destination})")
                    else:
                        print(f"          Item {k+1}: {body_type}")
    
    interactive = screen_node.get_interactive_elements()
    print(f"\nInteractive elements: {len(interactive)}")
    
    for i, elem in enumerate(interactive):
        if hasattr(elem, 'action') and elem.action:
            print(f"  {i+1}. {elem.element_type} -> {elem.action.action_type}({elem.action.destination})")
    
except CSAPError as e:
    print(f"[ERROR] CSAP Error: {e}")
    print(f"   Line: {e.line}, Column: {e.column}")
    if e.context:
        print(f"   Context: {e.context}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")
    import traceback
    traceback.print_exc()

