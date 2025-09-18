#!/usr/bin/env python3
"""
Debug list literal parsing in CSAP.
"""

import sys
from pathlib import Path

# Add CSAP to path
sys.path.append(str(Path(__file__).parent / "csap"))

from csap_parser import CSAPParser
from csap_exceptions import CSAPError


def test_simple_list():
    """Test simple list parsing."""
    print("🧪 Testing simple textbutton without lists")
    
    parser = CSAPParser()
    
    simple_screen = '''screen test:
    textbutton "Test" text_color "#EFEFEF" text_size 32 action Jump("dest")'''
    
    try:
        result = parser.parse_screen_text(simple_screen)
        print("✅ Simple properties work")
        return True
    except Exception as e:
        print(f"❌ Simple properties failed: {e}")
        return False


def test_list_literal():
    """Test list literal parsing."""
    print("\\n🧪 Testing textbutton with list literal")
    
    parser = CSAPParser()
    
    # Try the problematic pattern
    list_screen = '''screen test:
    textbutton "Test" text_outlines [(1, "#808080", 0, 0)] action Jump("dest")'''
    
    try:
        result = parser.parse_screen_text(list_screen)
        print("✅ List literal works")
        return True
    except Exception as e:
        print(f"❌ List literal failed: {e}")
        return False


def main():
    """Debug list parsing."""
    print("🔍 CSAP List Literal Debug")
    print("=" * 30)
    
    success1 = test_simple_list()
    success2 = test_list_literal()
    
    if success1 and success2:
        print("\\n🎉 Both tests passed!")
        return True
    else:
        print("\\n❌ Some tests failed.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
