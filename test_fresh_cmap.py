#!/usr/bin/env python3
"""
Fresh test of CMAP with new grammar.
"""

import sys
from pathlib import Path

# Add the CMAP module to path
app_dir = Path("app/renpy-source-api")
sys.path.insert(0, str(app_dir))

def test_fresh_cmap():
    """Test CMAP with fresh import."""
    print("🧪 FRESH CMAP TEST")
    print("=" * 30)
    
    try:
        from renpy_sdk.cmap import CMAPParser
        print("✅ CMAP imported")
        
        parser = CMAPParser()
        print("✅ Parser created")
        
        # Test simple conditional
        test_menu = '''menu:
    "Choice 1":
        pass
    "Choice 2" if flag:
        pass'''
        
        print("\n📝 Testing menu:")
        print(test_menu)
        
        result = parser.parse_menu(test_menu)
        
        if result:
            print(f"\n🎉 SUCCESS!")
            print(f"   Choices: {len(result.choices)}")
            for i, choice in enumerate(result.choices):
                print(f"   Choice {i+1}: '{choice.text}' (conditional: {choice.is_conditional})")
                if choice.condition:
                    print(f"     Condition: {choice.condition}")
        else:
            print(f"\n❌ FAILED - result is None")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fresh_cmap()
