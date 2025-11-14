#!/usr/bin/env python3
"""
Phase 2 CSA Tests - Content Detection, Context Awareness, and Nesting

Tests the enhanced features added in Phase 2.
"""

import sys
from pathlib import Path

# Add parent directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent.parent))

from CSA import ConditionalStructureAnalyzer


def test_content_detection_jump():
    """Test 1: Detect jump statements in branches."""
    print("\n[Test 1] Content detection - jump statements...")
    analyzer = ConditionalStructureAnalyzer()
    text = """if ready:
    jump target_label
else:
    pass"""
    
    try:
        block = analyzer.analyze_conditional(text)
        assert block.branches[0].contains_jump == True, "Should detect jump in if branch"
        assert block.branches[1].contains_jump == False, "Should not detect jump in else branch"
        print("✅ PASS")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def test_content_detection_call():
    """Test 2: Detect call statements."""
    print("\n[Test 2] Content detection - call statements...")
    analyzer = ConditionalStructureAnalyzer()
    text = """if condition:
    call helper_label
else:
    skip()"""
    
    try:
        block = analyzer.analyze_conditional(text)
        assert block.branches[0].contains_call == True, "Should detect call"
        print("✅ PASS")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def test_content_detection_menu():
    """Test 3: Detect menu definitions."""
    print("\n[Test 3] Content detection - menu definitions...")
    analyzer = ConditionalStructureAnalyzer()
    text = """if show_menu:
    menu:
        "Choice 1":
            jump a
else:
    jump b"""
    
    try:
        block = analyzer.analyze_conditional(text)
        assert block.branches[0].contains_menu == True, "Should detect menu"
        print("✅ PASS")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def test_content_detection_screen_element():
    """Test 4: Detect screen elements."""
    print("\n[Test 4] Content detection - screen elements...")
    analyzer = ConditionalStructureAnalyzer()
    text = """if active:
    textbutton "Click me" action Jump("target")
else:
    imagebutton auto "btn_%s.png" action Jump("other")"""
    
    try:
        block = analyzer.analyze_conditional(text)
        assert block.branches[0].contains_screen_element == True, "Should detect textbutton"
        assert block.branches[1].contains_screen_element == True, "Should detect imagebutton"
        print("✅ PASS")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def test_nested_conditionals():
    """Test 5: Detect and parse nested conditionals."""
    print("\n[Test 5] Nested conditionals...")
    analyzer = ConditionalStructureAnalyzer()
    text = """if outer:
    if inner:
        jump a
    else:
        jump b
else:
    jump c"""
    
    try:
        block = analyzer.analyze_conditional(text)
        # Outer conditional should have 2 branches (if/else)
        assert block.get_branch_count() == 2, f"Expected 2 branches, got {block.get_branch_count()}"
        
        # The if branch should have nested conditionals
        if_branch = block.branches[0]
        assert len(if_branch.nested_conditionals) > 0, "Should detect nested conditional"
        
        print("✅ PASS")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_context_aware_choice_detection():
    """Test 6: Context-aware choice detection."""
    print("\n[Test 6] Context-aware choice detection...")
    analyzer = ConditionalStructureAnalyzer()
    
    # Without menu context, "string": pattern needs action nearby
    text_no_context = """if x:
    "Some text":
        pass"""
    
    # With actual choice-like content
    text_with_action = """if x:
    "Choice text":
        jump target"""
    
    try:
        # First case: no clear action
        block1 = analyzer.analyze_conditional(text_no_context)
        # Should be cautious about detecting as choice without menu context
        
        # Second case: has jump action
        block2 = analyzer.analyze_conditional(text_with_action)
        # Should detect choice when action is present
        assert block2.branches[0].contains_choice == True, "Should detect choice with action"
        
        print("✅ PASS")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def test_nested_depth_limit():
    """Test 7: Nested depth limit prevents infinite recursion."""
    print("\n[Test 7] Nested depth limit...")
    analyzer = ConditionalStructureAnalyzer()
    
    # Create deeply nested structure
    nested_text = "if a:\n"
    indent = 4
    for i in range(15):  # Try to nest 15 levels deep (should hit limit at 10)
        nested_text += " " * indent + "if b:\n"
        nested_text += " " * (indent + 4) + "x = 1\n"
        indent += 4
    
    try:
        # Should not crash, but may not parse deepest levels
        block = analyzer.analyze_conditional(nested_text, max_depth=5)
        # As long as it doesn't crash, we're good
        print("✅ PASS")
        return True
    except ValueError as e:
        if "too deep" in str(e):
            # This is expected - depth limit working
            print("✅ PASS (depth limit enforced)")
            return True
        print(f"❌ FAIL: Unexpected error: {e}")
        return False
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def test_multiple_content_types():
    """Test 8: Branch with multiple content types."""
    print("\n[Test 8] Multiple content types in one branch...")
    analyzer = ConditionalStructureAnalyzer()
    text = """if complex_branch:
    call setup_function
    textbutton "Continue" action Jump("next_scene")
    menu:
        "Option 1":
            jump path_a
        "Option 2":
            jump path_b
else:
    pass"""
    
    try:
        block = analyzer.analyze_conditional(text)
        if_branch = block.branches[0]
        
        # Should detect multiple types
        assert if_branch.contains_call == True, "Should detect call"
        assert if_branch.contains_screen_element == True, "Should detect textbutton"
        assert if_branch.contains_menu == True, "Should detect menu"
        assert if_branch.contains_jump == True, "Should detect jump"
        
        print("✅ PASS")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def test_has_jump_in_branch_method():
    """Test 9: ConditionalBlock.has_jump_in_branch() method."""
    print("\n[Test 9] has_jump_in_branch() method...")
    analyzer = ConditionalStructureAnalyzer()
    text = """if condition:
    jump target_a
elif other:
    call helper
else:
    jump target_b"""
    
    try:
        block = analyzer.analyze_conditional(text)
        
        assert block.has_jump_in_branch(0) == True, "Branch 0 should have jump"
        assert block.has_jump_in_branch(1) == False, "Branch 1 has call, not jump"
        assert block.has_jump_in_branch(2) == True, "Branch 2 should have jump"
        
        print("✅ PASS")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def test_real_world_screen_pattern():
    """Test 10: Real-world Ren'Py screen pattern with conditionals."""
    print("\n[Test 10] Real-world screen pattern...")
    analyzer = ConditionalStructureAnalyzer()
    text = """    if variable is False:
        auto "images/active_%s.webp"
        action Jump("active_path")
        hovered Function(show_tooltip, "Active")
    else:
        idle "images/inactive.webp"
        action NullAction()"""
    
    try:
        block = analyzer.analyze_conditional(text)
        
        # Should parse with proper indentation
        assert block.get_branch_count() == 2
        assert block.base_indentation == 4
        
        # Should detect jump in first branch
        assert block.branches[0].contains_jump == True
        
        print("✅ PASS")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def main():
    """Run all Phase 2 tests."""
    print("="*60)
    print("🧪 CSA Phase 2 Test Suite")
    print("="*60)
    
    tests = [
        test_content_detection_jump,
        test_content_detection_call,
        test_content_detection_menu,
        test_content_detection_screen_element,
        test_nested_conditionals,
        test_context_aware_choice_detection,
        test_nested_depth_limit,
        test_multiple_content_types,
        test_has_jump_in_branch_method,
        test_real_world_screen_pattern,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print("\n" + "="*60)
    print(f"📊 Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("="*60)
    
    if failed == 0:
        print("\n🎉 All Phase 2 tests passed!")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) need attention")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

