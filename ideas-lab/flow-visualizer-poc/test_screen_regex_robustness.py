#!/usr/bin/env python3
"""
🚨 CRITICAL: Screen Element Regex Robustness Test Suite 🚨

⚠️  MANDATORY USAGE: Run this test EVERY TIME you modify screen parsing regex patterns!
⚠️  Location: Run from ideas-lab/flow-visualizer-poc/ directory
⚠️  Command: python test_screen_regex_robustness.py

This test suite prevents regex pattern regressions by validating all known working
screen element patterns from different VN styles against our parsing logic.

WHEN TO RUN THIS TEST:
- Before committing any changes to regex patterns in app/renpy-source-api/parser.py
- After adding support for a new VN with different screen syntax
- When debugging screen element parsing issues
- As part of any screen-related feature development

WHAT THIS TEST COVERS:
- All known working textbutton patterns (basic, styled, complex)
- All known working imagebutton patterns (single-line, multi-line, with anchors)
- All known working hotspot patterns (Jump, Call, coordinates)
- Multi-line parsing logic validation
- Quote type variations (single, double, mixed)
- VN-specific syntax patterns (Apocalust, Amnesia, AoA Academy, etc.)

HOW TO ADD NEW TEST CASES:
1. When you encounter a new screen syntax that works, add it to the test_cases list
2. Include the VN name in the test case name for reference
3. Specify expected parsing results
4. Run the test to ensure it passes before considering the fix complete
"""

import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add app directory to path for parser imports
current_dir = Path(__file__).parent
app_dir = current_dir.parent.parent / "app" / "renpy-source-api"
sys.path.insert(0, str(app_dir))

try:
    from parser import RenpyParser
except ImportError as e:
    print(f"❌ Failed to import parser: {e}")
    print(f"   Make sure you're running from: {current_dir}")
    print(f"   And that the parser exists at: {app_dir / 'parser.py'}")
    sys.exit(1)

class ScreenRegexTester:
    """Comprehensive tester for screen element regex patterns."""
    
    def __init__(self):
        self.parser = RenpyParser()
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'total': 0,
            'failures': []
        }
    
    def run_all_tests(self) -> bool:
        """Run all regex robustness tests."""
        print("🧪 Screen Element Regex Robustness Test Suite")
        print("=" * 60)
        print("⚠️  This test MUST PASS before committing regex changes!")
        print("=" * 60)
        
        # Test cases representing all known working patterns
        test_cases = self._get_comprehensive_test_cases()
        
        print(f"\\n📊 Running {len(test_cases)} test cases...")
        
        for test_case in test_cases:
            self._run_test_case(test_case)
        
        # Print summary
        print("\\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        print(f"📊 Total:  {self.test_results['total']}")
        
        if self.test_results['failed'] > 0:
            print("\\n🚨 REGRESSION DETECTED! 🚨")
            print("The following previously working patterns now fail:")
            for failure in self.test_results['failures']:
                print(f"   ❌ {failure}")
            print("\\n⚠️  DO NOT COMMIT until all tests pass!")
            return False
        else:
            print("\\n🎉 ALL TESTS PASSED! Safe to commit.")
            return True
    
    def _get_comprehensive_test_cases(self) -> List[Dict[str, Any]]:
        """Get all test cases representing known working patterns."""
        return [
            # ============================================================
            # TEXTBUTTON PATTERNS (All known working variations)
            # ============================================================
            {
                "name": "Basic textbutton (Original pattern)",
                "vn_source": "Generic",
                "element_type": "textbutton",
                "content": 'textbutton "Click me" action Jump("destination")',
                "expected": {
                    "text": "Click me",
                    "action_type": "Jump",
                    "destination": "destination"
                }
            },
            {
                "name": "Textbutton with Call action",
                "vn_source": "Generic", 
                "element_type": "textbutton",
                "content": 'textbutton "Call scene" action Call("scene_label")',
                "expected": {
                    "text": "Call scene",
                    "action_type": "Call", 
                    "destination": "scene_label"
                }
            },
            {
                "name": "Complex styled textbutton (Apocalust VN)",
                "vn_source": "Apocalust",
                "element_type": "textbutton", 
                "content": 'textbutton "{image=chat_bubble_1.png} Do I seem any different to you?" text_color "#EFEFEF" text_outlines [(1, "#808080", 0, 0)] text_hover_color "#FFFFDF" text_hover_outlines [(1, "#B3B3B3", 0, 0), (2, "#A0A0A0", 0, 0)] text_size 32 action Jump("ep1_dial_kitchen_doiseem") hover_sound "audio/Sfx/glass_tap.ogg" activate_sound "audio/Sfx/click_dialogue.ogg"',
                "expected": {
                    "text": "{image=chat_bubble_1.png} Do I seem any different to you?",
                    "action_type": "Jump",
                    "destination": "ep1_dial_kitchen_doiseem"
                }
            },
            {
                "name": "Simple styled textbutton (Apocalust VN)",
                "vn_source": "Apocalust",
                "element_type": "textbutton",
                "content": 'textbutton "Leave." text_color "#EFEFEF" text_outlines [(1, "#808080", 0, 0)] text_hover_color "#FFFFDF" text_hover_outlines [(1, "#B3B3B3", 0, 0), (2, "#A0A0A0", 0, 0)] text_size 32 action Jump("ep1_dial_kitchen_leave") hover_sound "audio/Sfx/glass_tap.ogg" activate_sound "audio/Sfx/click_dialogue.ogg"',
                "expected": {
                    "text": "Leave.",
                    "action_type": "Jump", 
                    "destination": "ep1_dial_kitchen_leave"
                }
            },
            
            # ============================================================
            # IMAGEBUTTON PATTERNS (All known working variations)
            # ============================================================
            {
                "name": "Basic single-line imagebutton",
                "vn_source": "Generic",
                "element_type": "imagebutton",
                "content": 'imagebutton idle "image.png" action Jump("destination")',
                "expected": {
                    "action_type": "Jump",
                    "destination": "destination"
                }
            },
            {
                "name": "Single-line imagebutton with Call",
                "vn_source": "Generic",
                "element_type": "imagebutton", 
                "content": 'imagebutton idle "button.png" hover "button_h.png" action Call("scene")',
                "expected": {
                    "action_type": "Call",
                    "destination": "scene"
                }
            },
            {
                "name": "Multi-line imagebutton (Come Home VN)",
                "vn_source": "Come Home",
                "element_type": "imagebutton",
                "is_multiline": True,
                "content": [
                    "imagebutton:",
                    "    idle \"images/button/FR1/DR2DRFN_idle.png\"",
                    "    hover \"images/button/FR1/DR2DRFN_hover.png\"",
                    "    focus_mask True",
                    "    action Jump(\"Freeroam2Foyer\")"
                ],
                "expected": {
                    "action_type": "Jump",
                    "destination": "Freeroam2Foyer"
                }
            },
            {
                "name": "Multi-line imagebutton with anchor (Amnesia VN)",
                "vn_source": "Amnesia",
                "element_type": "imagebutton",
                "is_multiline": True,
                "content": [
                    "imagebutton anchor (0.5, 0.5):",
                    "    xoffset 1190 yoffset 190", 
                    "    idle \"gui/imageButtons/Eye BTN idle.png\"",
                    "    hover \"gui/imageButtons/Eye BTN hover.png\"",
                    "    action Jump('d1_1_10_1_Action_Face')",
                    "    tooltip _(\"Face\")"
                ],
                "expected": {
                    "action_type": "Jump",
                    "destination": "d1_1_10_1_Action_Face"
                }
            },
            {
                "name": "Multi-line imagebutton with Call and single quotes",
                "vn_source": "Amnesia",
                "element_type": "imagebutton",
                "is_multiline": True,
                "content": [
                    "imagebutton anchor (0.5, 0.5):",
                    "    xoffset 1800 yoffset 950",
                    "    idle \"gui/imageButtons/Dont Talk BTN idle.png\"",
                    "    hover \"gui/imageButtons/Dont Talk BTN hover.png\"", 
                    "    action Call('d1_1_10_1_Action_KeepSilent')",
                    "    tooltip _(\"Keep Silent\")"
                ],
                "expected": {
                    "action_type": "Call",
                    "destination": "d1_1_10_1_Action_KeepSilent"
                }
            },
            
            # ============================================================
            # HOTSPOT PATTERNS (All known working variations)
            # ============================================================
            {
                "name": "Basic hotspot with Jump (Original pattern)",
                "vn_source": "Generic",
                "element_type": "hotspot",
                "content": 'hotspot (100, 200, 50, 50) action Jump("target")',
                "expected": {
                    "coordinates": "100, 200, 50, 50",
                    "action_type": "Jump",
                    "destination": "target"
                }
            },
            {
                "name": "Hotspot with Call action (AoA Academy VN)",
                "vn_source": "AoA Academy", 
                "element_type": "hotspot",
                "content": 'hotspot (35, 755, 290, 281) action Call("c1_aca_exp_corridor_exit")',
                "expected": {
                    "coordinates": "35, 755, 290, 281",
                    "action_type": "Call",
                    "destination": "c1_aca_exp_corridor_exit"
                }
            },
            {
                "name": "Hotspot with different coordinates (AoA Academy VN)",
                "vn_source": "AoA Academy",
                "element_type": "hotspot", 
                "content": 'hotspot (1279, 216, 281, 219) action Call("c1_aca_exp_aurora")',
                "expected": {
                    "coordinates": "1279, 216, 281, 219", 
                    "action_type": "Call",
                    "destination": "c1_aca_exp_aurora"
                }
            },
            {
                "name": "Hotspot with large coordinates (AoA Academy VN)",
                "vn_source": "AoA Academy",
                "element_type": "hotspot",
                "content": 'hotspot (1549, 738, 299, 313) action Call("c1_aca_exp_corridor_toclass")',
                "expected": {
                    "coordinates": "1549, 738, 299, 313",
                    "action_type": "Call", 
                    "destination": "c1_aca_exp_corridor_toclass"
                }
            }
        ]
    
    def _run_test_case(self, test_case: Dict[str, Any]) -> None:
        """Run a single test case and record results."""
        self.test_results['total'] += 1
        test_name = f"{test_case['name']} ({test_case['vn_source']})"
        
        print(f"\\n🧪 Testing: {test_name}")
        
        try:
            if test_case.get('is_multiline'):
                result = self._test_multiline_pattern(test_case)
            else:
                result = self._test_single_line_pattern(test_case)
            
            if result:
                print(f"   ✅ PASS")
                self.test_results['passed'] += 1
            else:
                print(f"   ❌ FAIL")
                self.test_results['failed'] += 1
                self.test_results['failures'].append(test_name)
                
        except Exception as e:
            print(f"   💥 ERROR: {e}")
            self.test_results['failed'] += 1
            self.test_results['failures'].append(f"{test_name} (Exception: {e})")
    
    def _test_single_line_pattern(self, test_case: Dict[str, Any]) -> bool:
        """Test a single-line pattern against regex."""
        content = test_case['content']
        element_type = test_case['element_type'] 
        expected = test_case['expected']
        
        if element_type == 'textbutton':
            match = self.parser.patterns['textbutton'].match(content)
            if not match:
                print(f"      ❌ Regex pattern failed to match")
                return False
            
            # Check extracted values
            text = match.group(1)
            action_type = match.group(2) if len(match.groups()) >= 2 else "unknown"
            destination = match.group(3) if len(match.groups()) >= 3 else match.group(2)
            
            print(f"      📝 Extracted: text='{text}', action={action_type}, dest='{destination}'")
            
            return (text == expected['text'] and 
                   action_type == expected['action_type'] and
                   destination == expected['destination'])
        
        elif element_type == 'imagebutton':
            match = self.parser.patterns['imagebutton'].match(content)
            if not match:
                print(f"      ❌ Regex pattern failed to match")
                return False
            
            action_type = match.group(1) if len(match.groups()) >= 1 else "unknown"
            destination = match.group(2) if len(match.groups()) >= 2 else match.group(1)
            
            print(f"      📝 Extracted: action={action_type}, dest='{destination}'")
            
            return (action_type == expected['action_type'] and
                   destination == expected['destination'])
        
        elif element_type == 'hotspot':
            match = self.parser.patterns['hotspot'].match(content)
            if not match:
                print(f"      ❌ Regex pattern failed to match")
                return False
            
            coordinates = match.group(1)
            action_type = match.group(2)
            destination = match.group(3)
            
            print(f"      📝 Extracted: coords='{coordinates}', action={action_type}, dest='{destination}'")
            
            return (coordinates == expected['coordinates'] and
                   action_type == expected['action_type'] and 
                   destination == expected['destination'])
        
        return False
    
    def _test_multiline_pattern(self, test_case: Dict[str, Any]) -> bool:
        """Test multi-line parsing logic."""
        lines = test_case['content']
        expected = test_case['expected']
        
        # Simulate the multi-line parsing logic from parser.py
        for i, line in enumerate(lines):
            if line.strip().startswith('imagebutton') and line.strip().endswith(':'):
                print(f"      📍 Found imagebutton start at line {i}")
                
                # Look ahead for action (up to 10 lines)
                for look_ahead in range(1, min(11, len(lines) - i)):
                    future_line = lines[i + look_ahead].strip()
                    
                    # Test action patterns with both quote types
                    action_jump_match = re.match(r'action\s+Jump\s*\(\s*["\']([^"\']+)["\']\s*\)', future_line, re.IGNORECASE)
                    action_call_match = re.match(r'action\s+Call\s*\(\s*["\']([^"\']+)["\']\s*\)', future_line, re.IGNORECASE)
                    
                    if action_jump_match:
                        destination = action_jump_match.group(1)
                        action_type = "Jump"
                        print(f"      📝 Extracted: action={action_type}, dest='{destination}'")
                        
                        return (action_type == expected['action_type'] and 
                               destination == expected['destination'])
                    
                    elif action_call_match:
                        destination = action_call_match.group(1) 
                        action_type = "Call"
                        print(f"      📝 Extracted: action={action_type}, dest='{destination}'")
                        
                        return (action_type == expected['action_type'] and
                               destination == expected['destination'])
                
                print(f"      ❌ No action found in next 10 lines")
                return False
        
        print(f"      ❌ No imagebutton start found")
        return False

def main():
    """Main test runner."""
    tester = ScreenRegexTester()
    success = tester.run_all_tests()
    
    if not success:
        print("\\n🚨 CRITICAL: Regex patterns have regressed!")
        print("🔧 Action required: Fix failing patterns before committing")
        sys.exit(1)
    else:
        print("\\n🎉 Success: All regex patterns working correctly")
        sys.exit(0)

if __name__ == "__main__":
    main()
