#!/usr/bin/env python3
"""
Debug script to test the space issue in Jump action.
"""

import sys
from pathlib import Path

# Add CSAP to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "csap"))

from csap_parser import CSAPParser

def test_space_in_jump():
    """Test the specific space issue in Jump action."""
    
    parser = CSAPParser()
    
    # Test patterns with and without space
    test_patterns = [
        # Without space (should work)
        '''screen test1:
    button:
        action Jump("ParlourCum01")''',
        
        # With space (Battle of the Bulges pattern - currently failing)
        '''screen test2:
    button:
        action Jump ("ParlourCum01")''',
        
        # Different spacing variations
        '''screen test3:
    button:
        action Jump  ("ParlourCum01")''',
    ]
    
    for i, pattern in enumerate(test_patterns, 1):
        print(f"\n🧪 Testing pattern {i}:")
        print(f"   {pattern.split('action')[1].strip()}")
        
        try:
            result = parser.parse_screen_text(pattern)
            print(f"   ✅ SUCCESS: {len(result.elements)} elements parsed")
            if result.elements:
                element = result.elements[0]
                if hasattr(element, 'action') and element.action:
                    print(f"   🎯 Action: {element.action.action_type}('{element.action.destination}')")
                else:
                    print(f"   ❌ No action found in element")
        except Exception as e:
            print(f"   ❌ FAILED: {e}")

if __name__ == "__main__":
    test_space_in_jump()
