#!/usr/bin/env python3

import re

def debug_imagebutton_regex():
    """Debug the imagebutton regex pattern to see why we're missing matches."""
    
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
    
    print("=== DEBUGGING IMAGEBUTTON REGEX ===")
    
    # Current pattern
    pattern = re.compile(
        r'imagebutton(?:\s+auto\s+"[^"]+"|[^:]*:|:).*?action\s+(?:\[.*?)?(Jump|Call)\s*\(\s*["\']([^"\']+)["\']\s*\)',
        re.MULTILINE | re.DOTALL
    )
    
    print("Pattern:")
    print(pattern.pattern)
    print()
    
    # Find all matches
    matches = list(pattern.finditer(screen_text))
    print(f"Total matches found: {len(matches)}")
    
    for i, match in enumerate(matches, 1):
        print(f"\nMatch {i}:")
        print(f"  Full match: {repr(match.group(0)[:100])}...")
        print(f"  Action type: {match.group(1)}")
        print(f"  Destination: {match.group(2)}")
        print(f"  Start position: {match.start()}")
        print(f"  End position: {match.end()}")
        
        # Show the context
        start = max(0, match.start() - 20)
        end = min(len(screen_text), match.end() + 20)
        context = screen_text[start:end].replace('\n', '\\n')
        print(f"  Context: ...{context}...")
    
    print(f"\n=== MANUAL ANALYSIS ===")
    
    # Let's manually identify the three imagebuttons
    expected_matches = [
        ("act_1d1_FreeRoam_Home.Bedroom_MC", "Back button"),
        ("d1_1_ChanageCloting", "Conditional clothing button"),
        ("act_1d1_FreeRoam_Home.Bedroom_MC_Wardrobe_Panty", "Wardrobe button with complex action")
    ]
    
    print("Expected matches:")
    for dest, desc in expected_matches:
        print(f"  - {desc}: Jump to '{dest}'")
        
        # Check if this destination appears in our matches
        found = any(match.group(2) == dest for match in matches)
        print(f"    Found: {'✅' if found else '❌'}")
        
        if not found:
            # Try to find why this wasn't matched
            if dest in screen_text:
                print(f"    Destination '{dest}' is in the text")
                # Find the line containing this destination
                lines = screen_text.split('\n')
                for line_num, line in enumerate(lines, 1):
                    if dest in line:
                        print(f"    Line {line_num}: {line.strip()}")
            else:
                print(f"    Destination '{dest}' NOT in text!")
    
    # Test if conditional blocks are causing issues
    print(f"\n=== CONDITIONAL BLOCK ANALYSIS ===")
    
    # Try a simpler pattern that ignores conditionals entirely
    simple_pattern = re.compile(
        r'(Jump|Call)\s*\(\s*["\']([^"\']+)["\']\s*\)',
        re.MULTILINE
    )
    
    simple_matches = list(simple_pattern.finditer(screen_text))
    print(f"Simple Jump/Call pattern found {len(simple_matches)} matches:")
    
    for match in simple_matches:
        print(f"  - {match.group(1)} to '{match.group(2)}'")

if __name__ == "__main__":
    debug_imagebutton_regex()
