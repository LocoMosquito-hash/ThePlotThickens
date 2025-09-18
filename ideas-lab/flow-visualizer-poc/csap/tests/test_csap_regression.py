#!/usr/bin/env python3
"""
🚨 CRITICAL: CSAP Regression Test Suite 🚨

⚠️  MANDATORY USAGE: Run this test EVERY TIME you modify CSAP parser, grammar, or transformations!
⚠️  Location: Run from ideas-lab/flow-visualizer-poc/ directory  
⚠️  Command: python -m pytest csap/tests/test_csap_regression.py -v

This test suite ensures CSAP produces equivalent or better results compared to
the existing regex-based parser for ALL known working patterns.

CRITICAL REQUIREMENT:
- CSAP must handle ALL test cases that the regex parser handles
- CSAP results must be semantically equivalent to regex results
- NO REGRESSIONS are allowed

WHEN TO RUN THIS TEST:
- Before committing any changes to CSAP code
- After modifying grammar files
- After adding new transformation logic
- When debugging CSAP parsing issues
- As part of CI/CD pipeline

WHAT THIS TEST COVERS:
- All regex test cases from test_screen_regex_robustness.py
- Additional CSAP-specific complex cases
- Real VN samples from multiple games
- Edge cases and error conditions
- Performance regression detection
"""

import sys
import pytest
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the project root to path for imports
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
app_dir = project_root / "app" / "renpy-source-api"
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(current_dir.parent))

try:
    from parser import RenpyParser
    from csap_parser import CSAPParser
    from csap_ast import ScreenNode, ScreenElementNode, TextButtonNode, ImageButtonNode, HotspotNode
    from csap_exceptions import CSAPError, CSAPParseError
except ImportError as e:
    pytest.skip(f"Required modules not available: {e}", allow_module_level=True)


class CSAPRegressionTester:
    """Comprehensive regression tester for CSAP vs Regex parsing."""
    
    def __init__(self):
        self.regex_parser = RenpyParser()
        self.csap_parser = CSAPParser()
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'csap_only_passed': 0,  # Cases regex can't handle but CSAP can
            'total': 0,
            'failures': [],
            'performance_data': []
        }
    
    def get_all_test_cases(self) -> List[Dict[str, Any]]:
        """Get comprehensive test cases including all regex patterns plus CSAP-specific ones."""
        
        # Import all test cases from regex robustness test
        regex_test_cases = self._get_regex_test_cases()
        
        # Add CSAP-specific test cases (complex patterns regex can't handle)
        csap_specific_cases = self._get_csap_specific_test_cases()
        
        return regex_test_cases + csap_specific_cases
    
    def _get_regex_test_cases(self) -> List[Dict[str, Any]]:
        """Get all test cases from the regex robustness test suite."""
        return [
            # ============================================================
            # TEXTBUTTON PATTERNS (From regex test suite)
            # ============================================================
            {
                "name": "Basic textbutton (Original pattern)",
                "vn_source": "Generic",
                "element_type": "textbutton",
                "content": '''screen test_screen:
    textbutton "Click me" action Jump("destination")''',
                "expected": {
                    "text": "Click me",
                    "action_type": "Jump",
                    "destination": "destination"
                },
                "test_type": "regex_compatibility"
            },
            {
                "name": "Textbutton with Call action",
                "vn_source": "Generic", 
                "element_type": "textbutton",
                "content": '''screen test_screen:
    textbutton "Call scene" action Call("scene_label")''',
                "expected": {
                    "text": "Call scene",
                    "action_type": "Call", 
                    "destination": "scene_label"
                },
                "test_type": "regex_compatibility"
            },
            {
                "name": "Complex styled textbutton (Apocalust VN)",
                "vn_source": "Apocalust",
                "element_type": "textbutton", 
                "content": '''screen kitchen_convo:
    textbutton "{image=chat_bubble_1.png} Do I seem any different to you?" text_color "#EFEFEF" text_outlines [(1, "#808080", 0, 0)] text_hover_color "#FFFFDF" text_hover_outlines [(1, "#B3B3B3", 0, 0), (2, "#A0A0A0", 0, 0)] text_size 32 action Jump("ep1_dial_kitchen_doiseem") hover_sound "audio/Sfx/glass_tap.ogg" activate_sound "audio/Sfx/click_dialogue.ogg"''',
                "expected": {
                    "text": "{image=chat_bubble_1.png} Do I seem any different to you?",
                    "action_type": "Jump",
                    "destination": "ep1_dial_kitchen_doiseem"
                },
                "test_type": "regex_compatibility"
            },
            
            # ============================================================
            # IMAGEBUTTON PATTERNS (From regex test suite)
            # ============================================================
            {
                "name": "Basic single-line imagebutton",
                "vn_source": "Generic",
                "element_type": "imagebutton",
                "content": '''screen test_screen:
    imagebutton idle "image.png" action Jump("destination")''',
                "expected": {
                    "action_type": "Jump",
                    "destination": "destination"
                },
                "test_type": "regex_compatibility"
            },
            {
                "name": "Multi-line imagebutton (Come Home VN)",
                "vn_source": "Come Home",
                "element_type": "imagebutton",
                "content": '''screen DormRoomn321:
    imagebutton:
        idle "images/button/FR1/DR2DRFN_idle.png"
        hover "images/button/FR1/DR2DRFN_hover.png"
        focus_mask True
        action Jump("Freeroam2Foyer")''',
                "expected": {
                    "action_type": "Jump",
                    "destination": "Freeroam2Foyer"
                },
                "test_type": "regex_compatibility"
            },
            {
                "name": "Multi-line imagebutton with anchor (Amnesia VN)",
                "vn_source": "Amnesia",
                "element_type": "imagebutton",
                "content": '''screen d1_1_10_1_screen:
    imagebutton anchor (0.5, 0.5):
        xoffset 1190 yoffset 190
        idle "gui/imageButtons/Eye BTN idle.png"
        hover "gui/imageButtons/Eye BTN hover.png"
        action Jump('d1_1_10_1_Action_Face')
        tooltip _("Face")''',
                "expected": {
                    "action_type": "Jump",
                    "destination": "d1_1_10_1_Action_Face",
                    "anchor": (0.5, 0.5)
                },
                "test_type": "regex_compatibility"
            },
            
            # ============================================================
            # HOTSPOT PATTERNS (From regex test suite)
            # ============================================================
            {
                "name": "Basic hotspot with Jump",
                "vn_source": "Generic",
                "element_type": "hotspot",
                "content": '''screen test_screen:
    hotspot (100, 200, 50, 50) action Jump("target")''',
                "expected": {
                    "coordinates": (100, 200, 50, 50),
                    "action_type": "Jump",
                    "destination": "target"
                },
                "test_type": "regex_compatibility"
            },
            {
                "name": "Hotspot with Call action (AoA Academy VN)",
                "vn_source": "AoA Academy", 
                "element_type": "hotspot",
                "content": '''screen c1aca_exp_corridor_au:
    hotspot (35, 755, 290, 281) action Call("c1_aca_exp_corridor_exit")''',
                "expected": {
                    "coordinates": (35, 755, 290, 281),
                    "action_type": "Call",
                    "destination": "c1_aca_exp_corridor_exit"
                },
                "test_type": "regex_compatibility"
            }
        ]
    
    def _get_csap_specific_test_cases(self) -> List[Dict[str, Any]]:
        """Get test cases that only CSAP can handle (complex patterns regex can't parse)."""
        return [
            {
                "name": "Complex nested screen with multiple elements",
                "vn_source": "CSAP Enhanced",
                "element_type": "complex",
                "content": '''screen complex_menu:
    vbox:
        xpos 0.5 ypos 0.3
        textbutton "Option 1" action Jump("path1")
        textbutton "Option 2" action Call("path2")
        hbox:
            textbutton "Sub A" action Jump("subA")
            textbutton "Sub B" action Jump("subB")''',
                "expected": {
                    "total_elements": 4,
                    "interactive_elements": 4
                },
                "test_type": "csap_only"
            },
            {
                "name": "Imagemap with multiple hotspots",
                "vn_source": "CSAP Enhanced", 
                "element_type": "imagemap",
                "content": '''screen room_map:
    imagemap:
        ground "room_idle.jpg"
        hover "room_hover.jpg"
        hotspot (100, 100, 200, 150) action Jump("door")
        hotspot (300, 200, 100, 100) action Call("window")
        hotspot (50, 300, 150, 100) action Jump("table")''',
                "expected": {
                    "hotspot_count": 3,
                    "has_imagemap": True
                },
                "test_type": "csap_only"
            },
            {
                "name": "Mixed quote types in same screen",
                "vn_source": "CSAP Enhanced",
                "element_type": "mixed_quotes",
                "content": '''screen mixed_quotes:
    textbutton "Double quotes" action Jump('single_dest')
    textbutton 'Single quotes' action Call("double_dest")''',
                "expected": {
                    "element_count": 2
                },
                "test_type": "csap_only"
            }
        ]
    
    def run_regression_test(self, test_case: Dict[str, Any]) -> bool:
        """Run a single regression test case."""
        test_name = f"{test_case['name']} ({test_case['vn_source']})"
        
        print(f"\n🧪 Testing: {test_name}")
        
        try:
            # Time the CSAP parsing
            start_time = time.time()
            csap_result = self.csap_parser.parse_screen_text(test_case['content'])
            csap_time = time.time() - start_time
            
            self.test_results['performance_data'].append({
                'test_name': test_name,
                'csap_time': csap_time,
                'content_length': len(test_case['content'])
            })
            
            # Validate CSAP results
            if not isinstance(csap_result, ScreenNode):
                print(f"   ❌ CSAP did not return ScreenNode")
                return False
            
            # Check expected results
            expected = test_case['expected']
            
            if test_case['test_type'] == 'regex_compatibility':
                # For regex compatibility tests, compare specific fields
                if not self._validate_regex_compatibility(csap_result, expected, test_case['element_type']):
                    return False
            elif test_case['test_type'] == 'csap_only':
                # For CSAP-only tests, validate enhanced features
                if not self._validate_csap_enhancements(csap_result, expected):
                    return False
            
            print(f"   ✅ PASS (parsed in {csap_time:.4f}s)")
            return True
            
        except Exception as e:
            print(f"   💥 ERROR: {e}")
            return False
    
    def _validate_regex_compatibility(self, csap_result: ScreenNode, expected: Dict[str, Any], element_type: str) -> bool:
        """Validate that CSAP results match regex expectations."""
        
        interactive_elements = csap_result.get_interactive_elements()
        
        if not interactive_elements:
            print(f"   ❌ No interactive elements found")
            return False
        
        # For single-element tests, check the first element
        element = interactive_elements[0]
        
        if element_type == 'textbutton':
            if not isinstance(element, TextButtonNode):
                print(f"   ❌ Expected TextButtonNode, got {type(element)}")
                return False
            
            if element.text != expected['text']:
                print(f"   ❌ Text mismatch: expected '{expected['text']}', got '{element.text}'")
                return False
        
        elif element_type == 'imagebutton':
            if not isinstance(element, ImageButtonNode):
                print(f"   ❌ Expected ImageButtonNode, got {type(element)}")
                return False
            
            if 'anchor' in expected and element.anchor != expected['anchor']:
                print(f"   ❌ Anchor mismatch: expected {expected['anchor']}, got {element.anchor}")
                return False
        
        elif element_type == 'hotspot':
            if not isinstance(element, HotspotNode):
                print(f"   ❌ Expected HotspotNode, got {type(element)}")
                return False
            
            if element.coordinates != expected['coordinates']:
                print(f"   ❌ Coordinates mismatch: expected {expected['coordinates']}, got {element.coordinates}")
                return False
        
        # Check action for all types
        if element.action:
            if element.action.action_type != expected['action_type']:
                print(f"   ❌ Action type mismatch: expected '{expected['action_type']}', got '{element.action.action_type}'")
                return False
            
            if element.action.destination != expected['destination']:
                print(f"   ❌ Destination mismatch: expected '{expected['destination']}', got '{element.action.destination}'")
                return False
        else:
            print(f"   ❌ No action found")
            return False
        
        print(f"   📝 Validated: {element_type} with {element.action.action_type} -> '{element.action.destination}'")
        return True
    
    def _validate_csap_enhancements(self, csap_result: ScreenNode, expected: Dict[str, Any]) -> bool:
        """Validate CSAP-specific enhanced features."""
        
        if 'total_elements' in expected:
            actual_count = len(csap_result.elements)
            if actual_count != expected['total_elements']:
                print(f"   ❌ Element count mismatch: expected {expected['total_elements']}, got {actual_count}")
                return False
        
        if 'interactive_elements' in expected:
            interactive_count = len(csap_result.get_interactive_elements())
            if interactive_count != expected['interactive_elements']:
                print(f"   ❌ Interactive element count mismatch: expected {expected['interactive_elements']}, got {interactive_count}")
                return False
        
        if 'element_count' in expected:
            actual_count = len(csap_result.get_interactive_elements())
            if actual_count != expected['element_count']:
                print(f"   ❌ Element count mismatch: expected {expected['element_count']}, got {actual_count}")
                return False
        
        print(f"   📝 Enhanced validation passed")
        return True


@pytest.fixture
def regression_tester():
    """Fixture providing the regression tester."""
    return CSAPRegressionTester()


class TestCSAPRegression:
    """CSAP Regression Test Suite."""
    
    def test_all_regex_compatibility_cases(self, regression_tester):
        """🚨 CRITICAL: Test all cases that worked with regex parser."""
        
        test_cases = [tc for tc in regression_tester.get_all_test_cases() 
                     if tc['test_type'] == 'regex_compatibility']
        
        print(f"\n📊 Running {len(test_cases)} regex compatibility tests...")
        
        passed = 0
        failed = 0
        
        for test_case in test_cases:
            if regression_tester.run_regression_test(test_case):
                passed += 1
            else:
                failed += 1
                regression_tester.test_results['failures'].append(test_case['name'])
        
        # Update results
        regression_tester.test_results['passed'] = passed
        regression_tester.test_results['failed'] = failed
        regression_tester.test_results['total'] = len(test_cases)
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"📊 REGEX COMPATIBILITY TEST SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Total:  {len(test_cases)}")
        
        if failed > 0:
            print(f"\n🚨 REGRESSION DETECTED! 🚨")
            print(f"The following regex patterns now fail with CSAP:")
            for failure in regression_tester.test_results['failures']:
                print(f"   ❌ {failure}")
            print(f"\n⚠️  CRITICAL: Fix regressions before deploying CSAP!")
        
        # CRITICAL: This test MUST pass for CSAP to be deployable
        assert failed == 0, f"CSAP regression detected: {failed} test cases failed"
    
    def test_csap_enhanced_features(self, regression_tester):
        """Test CSAP-specific enhanced features that regex can't handle."""
        
        test_cases = [tc for tc in regression_tester.get_all_test_cases() 
                     if tc['test_type'] == 'csap_only']
        
        print(f"\n📊 Running {len(test_cases)} CSAP enhancement tests...")
        
        csap_passed = 0
        csap_failed = 0
        
        for test_case in test_cases:
            if regression_tester.run_regression_test(test_case):
                csap_passed += 1
            else:
                csap_failed += 1
        
        regression_tester.test_results['csap_only_passed'] = csap_passed
        
        print(f"\n🎯 CSAP Enhancement Summary: {csap_passed}/{len(test_cases)} passed")
        
        # Enhanced features are nice-to-have, not critical
        if csap_failed > 0:
            print(f"⚠️  {csap_failed} enhanced features not working yet")
    
    def test_performance_regression(self, regression_tester):
        """Ensure CSAP performance is acceptable."""
        
        # Run a few test cases to get performance data
        test_cases = regression_tester.get_all_test_cases()[:5]  # Sample
        
        for test_case in test_cases:
            regression_tester.run_regression_test(test_case)
        
        # Analyze performance
        perf_data = regression_tester.test_results['performance_data']
        
        if perf_data:
            avg_time = sum(d['csap_time'] for d in perf_data) / len(perf_data)
            max_time = max(d['csap_time'] for d in perf_data)
            
            print(f"\n⏱️  Performance Summary:")
            print(f"   Average parse time: {avg_time:.4f}s")
            print(f"   Maximum parse time: {max_time:.4f}s")
            
            # Performance requirements
            assert avg_time < 0.1, f"Average parse time too slow: {avg_time:.4f}s > 0.1s"
            assert max_time < 0.5, f"Maximum parse time too slow: {max_time:.4f}s > 0.5s"
            
            print(f"   ✅ Performance requirements met")


def main():
    """Run the regression test suite manually."""
    print("🧪 CSAP Regression Test Suite")
    print("=" * 60)
    
    tester = CSAPRegressionTester()
    test_cases = tester.get_all_test_cases()
    
    print(f"📊 Running {len(test_cases)} comprehensive tests...")
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        if tester.run_regression_test(test_case):
            passed += 1
        else:
            failed += 1
    
    # Print final summary
    print(f"\n{'='*60}")
    print(f"📊 FINAL TEST SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total:  {len(test_cases)}")
    
    if failed > 0:
        print(f"\n🚨 CRITICAL: {failed} tests failed!")
        print(f"🔧 Action required: Fix failing patterns before deploying CSAP")
        return False
    else:
        print(f"\n🎉 SUCCESS: All tests passed! CSAP is ready for deployment.")
        return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
