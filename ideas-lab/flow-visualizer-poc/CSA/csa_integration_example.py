#!/usr/bin/env python3
"""
CSA Integration Example

Demonstrates how to use CSA to extract elements from conditional blocks
in Ren'Py screens. This shows the integration pattern that will be used
in CSAP and CMAP.
"""

import sys
import re
from pathlib import Path
from typing import List, Tuple

# Add parent to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

from CSA import ConditionalStructureAnalyzer


class CSAScreenElementExtractor:
    """
    Example integration showing how to use CSA to extract screen elements
    from conditional blocks.
    
    This demonstrates the "show all paths" approach where elements from ALL
    conditional branches are extracted for flow visualization.
    """
    
    def __init__(self):
        self.csa = ConditionalStructureAnalyzer()
        
        # Simple patterns for detecting elements (simplified for demo)
        self.textbutton_pattern = re.compile(r'textbutton\s+"([^"]+)"')
        self.imagebutton_pattern = re.compile(r'imagebutton')
        self.jump_pattern = re.compile(r'Jump\("([^"]+)"\)')
        self.call_pattern = re.compile(r'Call\("([^"]+)"\)')
    
    def extract_elements_with_csa(self, screen_text: str) -> List[Tuple[str, str, str]]:
        """
        Extract interactive elements using CSA to handle conditionals.
        
        Returns list of (element_type, text, destination) tuples.
        """
        elements = []
        lines = screen_text.split('\n')
        
        # Find conditional blocks
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check if this line starts a conditional
            if line.strip().startswith('if '):
                # Use CSA to analyze the conditional
                remaining_text = '\n'.join(lines[i:])
                try:
                    conditional = self.csa.analyze_conditional(remaining_text)
                    
                    # Extract elements from ALL branches (show all paths)
                    for branch in conditional.branches:
                        branch_content = '\n'.join(branch.content_lines)
                        
                        # Find textbuttons
                        for match in self.textbutton_pattern.finditer(branch_content):
                            button_text = match.group(1)
                            # Find associated jump/call
                            jump_match = self.jump_pattern.search(branch_content[match.end():])
                            if jump_match:
                                elements.append((
                                    'textbutton',
                                    button_text,
                                    jump_match.group(1)
                                ))
                    
                    # Skip past the conditional block
                    i = conditional.end_line - conditional.start_line + i + 1
                except ValueError:
                    # Not a valid conditional, move on
                    i += 1
            else:
                # Non-conditional line - check for direct elements
                if 'textbutton' in line:
                    text_match = self.textbutton_pattern.search(line)
                    if text_match:
                        # Look ahead for jump/call
                        lookahead = '\n'.join(lines[i:min(i+5, len(lines))])
                        jump_match = self.jump_pattern.search(lookahead)
                        if jump_match:
                            elements.append((
                                'textbutton',
                                text_match.group(1),
                                jump_match.group(1)
                            ))
                i += 1
        
        return elements


def test_csa_integration():
    """Test CSA integration with real Ren'Py pattern."""
    print("=" * 60)
    print("CSA Integration Example")
    print("=" * 60)
    
    # Example screen with conditionals from DressingRoom3
    screen_text = """screen DressingRoom3:
    if DressingRoom3Status == 0:
        add "gui/choices/c11.png"
        textbutton "Try opening the door" xalign 0.5 action [Jump("DressingRoom3_TryHandle")]
        textbutton "Back away from the door" xalign 0.5 action [Jump("DressingRoomsStart")]
    elif DressingRoom3Status == 1:
        add "gui/choices/c001.png"
        textbutton "Peek inside" xalign 0.5 action [Jump("DressingRoom3_TryPeek")]
        textbutton "Back away" xalign 0.5 action [Jump("DressingRoomsStart")]
    else:
        textbutton "Nothing here" action [Jump("DressingRoomsStart")]"""
    
    extractor = CSAScreenElementExtractor()
    elements = extractor.extract_elements_with_csa(screen_text)
    
    print(f"\n✅ Extracted {len(elements)} elements using CSA:")
    for elem_type, text, dest in elements:
        print(f"  - {elem_type}: '{text}' → {dest}")
    
    # Verify we got elements from all branches
    destinations = [dest for _, _, dest in elements]
    expected = ["DressingRoom3_TryHandle", "DressingRoomsStart", "DressingRoom3_TryPeek"]
    
    print(f"\n🎯 Unique destinations: {set(destinations)}")
    print(f"📋 Expected destinations: {set(expected)}")
    
    if all(exp in destinations for exp in expected):
        print("\n✅ SUCCESS: CSA correctly extracted elements from all conditional branches!")
        return True
    else:
        print("\n❌ FAIL: Some elements were not extracted")
        return False


if __name__ == "__main__":
    success = test_csa_integration()
    print("\n" + "=" * 60)
    print("🎉 CSA Integration PoC Complete!" if success else "❌ Integration needs work")
    print("=" * 60)
    sys.exit(0 if success else 1)

