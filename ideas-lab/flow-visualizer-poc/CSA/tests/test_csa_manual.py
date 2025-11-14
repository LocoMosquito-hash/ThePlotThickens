#!/usr/bin/env python3
"""
Manual CSA tests without pytest dependency.
Quick validation that CSA works correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent.parent))

from CSA import ConditionalStructureAnalyzer, ConditionalBlock, ConditionalBranch


def test_single_if():
    """Test 1: Single if block."""
    print("\n[Test 1] Single if block...")
    analyzer = ConditionalStructureAnalyzer()
    text = """if condition:
    jump target_a"""
    
    try:
        block = analyzer.analyze_conditional(text)
        assert block.get_branch_count() == 1
        assert block.branches[0].branch_type == 'if'
        assert block.branches[0].condition == 'condition'
        print("✅ PASS")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def test_if_else():
    """Test 2: If/else block."""
    print("\n[Test 2] If/else block...")
    analyzer = ConditionalStructureAnalyzer()
    text = """if x > 5:
    jump path_a
else:
    jump path_b"""
    
    try:
        block = analyzer.analyze_conditional(text)
        assert block.get_branch_count() == 2
        assert block.branches[0].branch_type == 'if'
        assert block.branches[1].branch_type == 'else'
        print("✅ PASS")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def test_if_elif_else():
    """Test 3: If/elif/else chain."""
    print("\n[Test 3] If/elif/else chain...")
    analyzer = ConditionalStructureAnalyzer()
    text = """if score == 1:
    jump ending_bad
elif score == 2:
    jump ending_neutral
else:
    jump ending_good"""
    
    try:
        block = analyzer.analyze_conditional(text)
        assert block.get_branch_count() == 3
        assert block.branches[0].branch_type == 'if'
        assert block.branches[1].branch_type == 'elif'
        assert block.branches[2].branch_type == 'else'
        print("✅ PASS")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def test_multiple_elif():
    """Test 4: Multiple elif branches."""
    print("\n[Test 4] Multiple elif branches...")
    analyzer = ConditionalStructureAnalyzer()
    text = """if day == 1:
    jump monday
elif day == 2:
    jump tuesday
elif day == 3:
    jump wednesday
else:
    jump other_day"""
    
    try:
        block = analyzer.analyze_conditional(text)
        assert block.get_branch_count() == 4
        elif_branches = block.get_all_branches_by_type('elif')
        assert len(elif_branches) == 2
        print("✅ PASS")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def test_indented_conditional():
    """Test 5: Already indented conditional."""
    print("\n[Test 5] Indented conditional...")
    analyzer = ConditionalStructureAnalyzer()
    text = """    if nested:
        do_something()
    else:
        do_else()"""
    
    try:
        block = analyzer.analyze_conditional(text)
        assert block.get_branch_count() == 2
        assert block.base_indentation == 4
        print("✅ PASS")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def test_comments():
    """Test 6: Comments in branches."""
    print("\n[Test 6] Comments in branches...")
    analyzer = ConditionalStructureAnalyzer()
    text = """if flag:
    # This is a comment
    do_action()
else:
    other_action()"""
    
    try:
        block = analyzer.analyze_conditional(text)
        assert block.get_branch_count() == 2
        content = '\n'.join(block.branches[0].content_lines)
        assert '# This is a comment' in content
        print("✅ PASS")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def test_complex_condition():
    """Test 7: Complex boolean condition."""
    print("\n[Test 7] Complex condition...")
    analyzer = ConditionalStructureAnalyzer()
    text = """if (flag1 and flag2) or (not flag3):
    action()
else:
    skip()"""
    
    try:
        block = analyzer.analyze_conditional(text)
        assert 'flag1' in block.branches[0].condition
        assert 'flag2' in block.branches[0].condition
        print("✅ PASS")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def test_multiline_condition():
    """Test 8: Multi-line condition."""
    print("\n[Test 8] Multi-line condition...")
    analyzer = ConditionalStructureAnalyzer()
    text = """if (condition1 and
    condition2):
    do_something()
else:
    do_else()"""
    
    try:
        block = analyzer.analyze_conditional(text)
        assert block.get_branch_count() == 2
        assert 'condition1' in block.branches[0].condition
        assert 'condition2' in block.branches[0].condition
        print("✅ PASS")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def test_get_all_content():
    """Test 9: get_all_content() method."""
    print("\n[Test 9] get_all_content() method...")
    analyzer = ConditionalStructureAnalyzer()
    text = """if a:
    line_a
elif b:
    line_b
else:
    line_c"""
    
    try:
        block = analyzer.analyze_conditional(text)
        all_content = block.get_all_content()
        content_str = '\n'.join(all_content)
        # Should contain content from all branches
        assert len(all_content) > 0
        print("✅ PASS")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def test_renpy_pattern():
    """Test 10: Real Ren'Py pattern with screen elements."""
    print("\n[Test 10] Real Ren'Py pattern...")
    analyzer = ConditionalStructureAnalyzer()
    text = """    if DressingRoom3Status == 0:
        add "gui/choices/c11.png"
        textbutton "Try opening" action [Jump("Target")]
    else:
        textbutton "Back" action [Jump("Start")]"""
    
    try:
        block = analyzer.analyze_conditional(text)
        assert block.branches[0].branch_type == 'if'
        content = '\n'.join(block.branches[0].content_lines)
        assert 'textbutton' in content
        print("✅ PASS")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def test_data_structures():
    """Test 11: Data structure validation."""
    print("\n[Test 11] Data structure validation...")
    
    # Test invalid branch type
    try:
        branch = ConditionalBranch(
            branch_type='invalid',
            condition=None,
            content_lines=[],
            start_line=0,
            end_line=0,
            indentation=0
        )
        print("❌ FAIL: Should have raised ValueError for invalid branch_type")
        return False
    except ValueError:
        pass
    
    # Test else with condition
    try:
        branch = ConditionalBranch(
            branch_type='else',
            condition='bad',
            content_lines=[],
            start_line=0,
            end_line=0,
            indentation=0
        )
        print("❌ FAIL: Should have raised ValueError for else with condition")
        return False
    except ValueError:
        pass
    
    print("✅ PASS")
    return True


def main():
    """Run all manual tests."""
    print("="*60)
    print("🧪 CSA Manual Test Suite")
    print("="*60)
    
    tests = [
        test_single_if,
        test_if_else,
        test_if_elif_else,
        test_multiple_elif,
        test_indented_conditional,
        test_comments,
        test_complex_condition,
        test_multiline_condition,
        test_get_all_content,
        test_renpy_pattern,
        test_data_structures,
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
        print("\n🎉 All tests passed!")
        return True
    else:
        print(f"\n❌ {failed} test(s) failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

