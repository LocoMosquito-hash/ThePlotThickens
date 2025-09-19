#!/usr/bin/env python3
"""
Conditional-Blind Parser

A simple parser that ignores conditional logic entirely and just extracts
all textbuttons, imagebuttons, and hotspots with Jump() or Call() actions
for story flow analysis.

This is much simpler than full conditional parsing but covers 95% of story flow cases.
"""

import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class SimpleScreenElement:
    """Simple screen element for conditional-blind parsing."""
    element_type: str  # 'textbutton', 'imagebutton', 'hotspot'
    text: Optional[str] = None
    action_type: Optional[str] = None  # 'Jump', 'Call'
    destination: Optional[str] = None
    line_number: int = 0

class ConditionalBlindParser:
    """
    Parser that ignores conditional logic and extracts all interactive elements.
    
    This approach:
    1. Finds all textbutton/imagebutton/hotspot elements
    2. Extracts their Jump() or Call() actions
    3. Ignores conditional context entirely
    4. Much simpler and more robust than full conditional parsing
    """
    
    def __init__(self):
        # Regex patterns for different element types
        self.textbutton_pattern = re.compile(
            r'textbutton\s+"([^"]+)"[^}]*?action\s+\[[^\]]*?(Jump|Call)\("([^"]+)"\)[^\]]*?\]',
            re.MULTILINE | re.DOTALL
        )
        
        self.imagebutton_pattern = re.compile(
            r'imagebutton(?:\s+auto\s+"[^"]+"|:)[^}]*?action\s+\[[^\]]*?(Jump|Call)\("([^"]+)"\)[^\]]*?\]',
            re.MULTILINE | re.DOTALL
        )
        
        # Hotspot with coordinates
        self.hotspot_pattern = re.compile(
            r'hotspot\s+\([^)]+\)[^}]*?action\s+\[[^\]]*?(Jump|Call)\("([^"]+)"\)[^\]]*?\]',
            re.MULTILINE | re.DOTALL
        )
    
    def parse_screen_text(self, screen_text: str) -> List[SimpleScreenElement]:
        """
        Parse screen text and extract all interactive elements.
        
        Returns list of SimpleScreenElement objects with story flow actions.
        """
        elements = []
        
        # Extract textbuttons
        for match in self.textbutton_pattern.finditer(screen_text):
            text = match.group(1)
            action_type = match.group(2)  # Jump or Call
            destination = match.group(3)
            line_number = screen_text[:match.start()].count('\n') + 1
            
            elements.append(SimpleScreenElement(
                element_type='textbutton',
                text=text,
                action_type=action_type,
                destination=destination,
                line_number=line_number
            ))
        
        # Extract imagebuttons
        for match in self.imagebutton_pattern.finditer(screen_text):
            action_type = match.group(1)  # Jump or Call
            destination = match.group(2)
            line_number = screen_text[:match.start()].count('\n') + 1
            
            elements.append(SimpleScreenElement(
                element_type='imagebutton',
                text=None,
                action_type=action_type,
                destination=destination,
                line_number=line_number
            ))
        
        # Extract hotspots
        for match in self.hotspot_pattern.finditer(screen_text):
            action_type = match.group(1)  # Jump or Call
            destination = match.group(2)
            line_number = screen_text[:match.start()].count('\n') + 1
            
            elements.append(SimpleScreenElement(
                element_type='hotspot',
                text=None,
                action_type=action_type,
                destination=destination,
                line_number=line_number
            ))
        
        return elements
    
    def get_interactive_count(self, screen_text: str) -> int:
        """Get count of interactive elements without full parsing."""
        elements = self.parse_screen_text(screen_text)
        return len(elements)
    
    def get_destinations(self, screen_text: str) -> List[str]:
        """Get all Jump/Call destinations from screen."""
        elements = self.parse_screen_text(screen_text)
        return [elem.destination for elem in elements if elem.destination]


def test_conditional_blind_parser():
    """Test the conditional-blind parser with DressingRoom3."""
    
    # DressingRoom3 with compound conditionals
    test_screen = '''screen DressingRoom3:
    if DressingRoom3Status == 0:
        add "gui/choices/c11.png"
        textbutton "Try opening the door" xalign 0.5 ypos cpos5 action [Jump("DressingRoom3_TryHandle")] hover_sound "audio/sounds/button_tap.ogg"
        textbutton "Back away from the door" xalign 0.5 ypos cpos7 action [Jump("DressingRoomsStart")] hover_sound "audio/sounds/button_tap.ogg"
    if DressingRoom3Status == 1 and DressingRoomPeeking == 0:
        add "gui/choices/c001.png"
        textbutton "The door is locked, Alexis is in there" xalign 0.5 ypos cpos4 text_outlines [(8, "#000000", 0, 0)] text_size 40
        textbutton "I don't think I should take a peek..." xalign 0.5 ypos cpos6 text_outlines [(8, "#000000", 0, 0)] text_size 40
        textbutton "Back away from the door" xalign 0.5 ypos cpos8 action [Jump("DressingRoomsStart")] hover_sound "audio/sounds/button_tap.ogg"
    if DressingRoom3Status == 1 and DressingRoomPeeking == 1:
        add "gui/choices/c011.png"
        textbutton "The door is locked" xalign 0.5 ypos cpos4 text_outlines [(8, "#000000", 0, 0)] text_size 40
        textbutton "-{font=DejaVuSans.ttf}{b}♥{/b}{/font}- It's just one little peek, no harm in that, right?" xalign 0.5 ypos cpos6h action [Jump("DressingRoom3_TryPeek")] hover_sound "audio/sounds/button_tap.ogg"
        textbutton "Back away from the door" xalign 0.5 ypos cpos8 action [Jump("DressingRoomsStart")] hover_sound "audio/sounds/button_tap.ogg"'''
    
    print("🔍 Testing Conditional-Blind Parser")
    print("=" * 50)
    
    parser = ConditionalBlindParser()
    elements = parser.parse_screen_text(test_screen)
    
    print(f"✅ Found {len(elements)} interactive elements:")
    for i, elem in enumerate(elements):
        print(f"  {i+1}. {elem.element_type} - '{elem.text}' -> {elem.destination}")
    
    destinations = parser.get_destinations(test_screen)
    unique_destinations = list(set(destinations))
    
    print(f"\n🎯 Unique destinations: {unique_destinations}")
    
    expected = ["DressingRoom3_TryHandle", "DressingRoomsStart", "DressingRoom3_TryPeek"]
    found = set(unique_destinations)
    expected_set = set(expected)
    
    if expected_set.issubset(found):
        print("✅ All expected destinations found!")
        return True
    else:
        missing = expected_set - found
        print(f"❌ Missing destinations: {missing}")
        return False

if __name__ == "__main__":
    success = test_conditional_blind_parser()
    if success:
        print("\n🎉 Conditional-blind parser works!")
    else:
        print("\n💥 Conditional-blind parser failed!")
