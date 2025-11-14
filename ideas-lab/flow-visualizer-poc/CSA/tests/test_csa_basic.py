#!/usr/bin/env python3
"""
Basic CSA functionality tests.

Tests core boundary detection for conditional blocks (if/elif/else).
Covers 20+ test cases including edge cases.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent.parent))

from CSA import ConditionalStructureAnalyzer, ConditionalBlock, ConditionalBranch
from CSA.conditional_structures import ConditionalBranch, ConditionalBlock


class TestCSABasicBoundaryDetection:
    """Test basic boundary detection functionality."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a CSA instance."""
        return ConditionalStructureAnalyzer()
    
    def test_single_if_block(self, analyzer):
        """Test parsing a simple if block with no else."""
        text = """if condition:
    jump target_a"""
        
        block = analyzer.analyze_conditional(text)
        
        assert block is not None
        assert block.get_branch_count() == 1
        assert block.branches[0].branch_type == 'if'
        assert block.branches[0].condition == 'condition'
        assert len(block.branches[0].content_lines) == 1
        assert 'jump target_a' in block.branches[0].content_lines[0]
    
    def test_if_else_block(self, analyzer):
        """Test parsing if/else block."""
        text = """if x > 5:
    jump path_a
else:
    jump path_b"""
        
        block = analyzer.analyze_conditional(text)
        
        assert block.get_branch_count() == 2
        assert block.branches[0].branch_type == 'if'
        assert block.branches[0].condition == 'x > 5'
        assert block.branches[1].branch_type == 'else'
        assert block.branches[1].condition is None
    
    def test_if_elif_else_chain(self, analyzer):
        """Test parsing if/elif/else chain."""
        text = """if score == 1:
    jump ending_bad
elif score == 2:
    jump ending_neutral
else:
    jump ending_good"""
        
        block = analyzer.analyze_conditional(text)
        
        assert block.get_branch_count() == 3
        assert block.branches[0].branch_type == 'if'
        assert block.branches[0].condition == 'score == 1'
        assert block.branches[1].branch_type == 'elif'
        assert block.branches[1].condition == 'score == 2'
        assert block.branches[2].branch_type == 'else'
    
    def test_multiple_elif_branches(self, analyzer):
        """Test parsing multiple elif branches."""
        text = """if day == 1:
    jump monday
elif day == 2:
    jump tuesday
elif day == 3:
    jump wednesday
elif day == 4:
    jump thursday
else:
    jump other_day"""
        
        block = analyzer.analyze_conditional(text)
        
        assert block.get_branch_count() == 5
        elif_branches = block.get_all_branches_by_type('elif')
        assert len(elif_branches) == 3
        assert elif_branches[0].condition == 'day == 2'
        assert elif_branches[1].condition == 'day == 3'
        assert elif_branches[2].condition == 'day == 4'
    
    def test_indented_conditional(self, analyzer):
        """Test parsing conditional that is already indented."""
        text = """    if nested_condition:
        do_something()
    else:
        do_something_else()"""
        
        block = analyzer.analyze_conditional(text)
        
        assert block.get_branch_count() == 2
        assert block.base_indentation == 4
        assert block.branches[0].indentation == 4
    
    def test_empty_branch(self, analyzer):
        """Test parsing conditional with empty branch."""
        text = """if condition:
    pass
else:
    jump target"""
        
        block = analyzer.analyze_conditional(text)
        
        assert block.get_branch_count() == 2
        # Empty branch should still be captured
        assert block.branches[0].branch_type == 'if'
    
    def test_blank_lines_in_branch(self, analyzer):
        """Test handling blank lines within branch content."""
        text = """if condition:
    line1 = True
    
    line2 = True
else:
    other_line = False"""
        
        block = analyzer.analyze_conditional(text)
        
        assert block.get_branch_count() == 2
        # Blank lines should be included in content
        assert '' in [line.strip() for line in block.branches[0].content_lines]
    
    def test_comments_in_branch(self, analyzer):
        """Test handling comments within branch content."""
        text = """if flag:
    # This is a comment
    do_action()
    # Another comment
else:
    # Comment in else
    other_action()"""
        
        block = analyzer.analyze_conditional(text)
        
        assert block.get_branch_count() == 2
        # Comments should be included in content lines
        content = '\n'.join(block.branches[0].content_lines)
        assert '# This is a comment' in content
    
    def test_inline_comment_after_colon(self, analyzer):
        """Test handling inline comments after conditional colon."""
        text = """if condition:  # This is an inline comment
    do_something()
else:  # Another comment
    do_else()"""
        
        block = analyzer.analyze_conditional(text)
        
        assert block.get_branch_count() == 2
        assert block.branches[0].condition == 'condition'
    
    def test_complex_condition(self, analyzer):
        """Test parsing complex boolean condition."""
        text = """if (flag1 and flag2) or (not flag3 and flag4):
    complex_action()
else:
    simple_action()"""
        
        block = analyzer.analyze_conditional(text)
        
        assert block.branches[0].condition == '(flag1 and flag2) or (not flag3 and flag4)'
    
    def test_condition_with_function_call(self, analyzer):
        """Test condition containing function calls."""
        text = """if hasattr(obj, 'method') and obj.is_valid():
    use_object()
else:
    skip()"""
        
        block = analyzer.analyze_conditional(text)
        
        assert 'hasattr' in block.branches[0].condition
        assert 'is_valid()' in block.branches[0].condition
    
    def test_multiline_content(self, analyzer):
        """Test branch with multiple lines of content."""
        text = """if ready:
    variable1 = True
    variable2 = False
    call helper_function
    jump next_scene
else:
    wait()"""
        
        block = analyzer.analyze_conditional(text)
        
        assert len(block.branches[0].content_lines) >= 4
    
    def test_nested_indentation_not_nested_conditional(self, analyzer):
        """Test deeply nested indentation (not nested conditionals)."""
        text = """if outer:
    for item in items:
        process(item)
        do_more()
else:
    skip_all()"""
        
        block = analyzer.analyze_conditional(text)
        
        # Should parse the outer conditional only
        assert block.get_branch_count() == 2
        # The for loop should be part of the if branch content
        content = '\n'.join(block.branches[0].content_lines)
        assert 'for item in items' in content
    
    def test_get_all_content(self, analyzer):
        """Test get_all_content() method."""
        text = """if a:
    line_a1
    line_a2
elif b:
    line_b1
else:
    line_c1"""
        
        block = analyzer.analyze_conditional(text)
        all_content = block.get_all_content()
        
        # Should contain content from all branches
        content_str = '\n'.join(all_content)
        assert 'line_a1' in content_str or 'line_a' in content_str
        assert 'line_b1' in content_str or 'line_b' in content_str
        assert 'line_c1' in content_str or 'line_c' in content_str
    
    def test_start_and_end_lines(self, analyzer):
        """Test that start_line and end_line are correctly calculated."""
        text = """if condition:
    action1()
    action2()
else:
    action3()"""
        
        block = analyzer.analyze_conditional(text, start_line=10)
        
        # Start line should be adjusted by start_line parameter
        assert block.start_line == 10
        # End line should be after all content
        assert block.end_line > block.start_line
    
    def test_dedent_detection(self, analyzer):
        """Test that dedenting properly ends a conditional."""
        text = """if condition:
    inside_if = True
outside_if = False"""
        
        block = analyzer.analyze_conditional(text)
        
        # Should only capture the if block, not the dedented line
        content = '\n'.join(block.branches[0].content_lines)
        assert 'inside_if' in content
        assert 'outside_if' not in content
    
    def test_elif_without_else(self, analyzer):
        """Test if/elif without else."""
        text = """if x == 1:
    jump one
elif x == 2:
    jump two"""
        
        block = analyzer.analyze_conditional(text)
        
        assert block.get_branch_count() == 2
        assert block.branches[1].branch_type == 'elif'
        # Should not have an else branch
        assert block.get_branch('else') is None
    
    def test_string_with_colon_in_content(self, analyzer):
        """Test that strings with colons in content don't confuse parser."""
        text = """if show_text:
    text = "Hello: world"
    display(text)
else:
    skip()"""
        
        block = analyzer.analyze_conditional(text)
        
        assert block.get_branch_count() == 2
        content = '\n'.join(block.branches[0].content_lines)
        assert 'Hello: world' in content
    
    def test_tab_indentation(self, analyzer):
        """Test handling tab indentation (should be normalized to spaces)."""
        text = "if tab_test:\n\tjump target\nelse:\n\tskip()"
        
        block = analyzer.analyze_conditional(text)
        
        assert block.get_branch_count() == 2
        # Should handle tabs properly
        assert block.branches[0].branch_type == 'if'
    
    def test_eof_after_conditional(self, analyzer):
        """Test conditional that ends at EOF with no dedent."""
        text = """if at_end:
    final_action()
    last_line()"""
        
        block = analyzer.analyze_conditional(text)
        
        assert block.get_branch_count() == 1
        assert len(block.branches[0].content_lines) >= 2


class TestCSAEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.fixture
    def analyzer(self):
        return ConditionalStructureAnalyzer()
    
    def test_no_if_statement_raises_error(self, analyzer):
        """Test that missing if statement raises ValueError."""
        text = """some_code = True
other_code = False"""
        
        with pytest.raises(ValueError, match="No 'if' statement found"):
            analyzer.analyze_conditional(text)
    
    def test_multiline_condition(self, analyzer):
        """Test multi-line condition spanning multiple lines."""
        text = """if (condition1 and
    condition2 and
    condition3):
    do_something()
else:
    do_else()"""
        
        block = analyzer.analyze_conditional(text)
        
        assert block.get_branch_count() == 2
        # Condition should be combined
        assert 'condition1' in block.branches[0].condition
        assert 'condition2' in block.branches[0].condition
        assert 'condition3' in block.branches[0].condition
    
    def test_mixed_spaces_and_tabs(self, analyzer):
        """Test that mixed spaces and tabs are handled (normalized)."""
        # Note: In real code this is bad practice, but we should handle it
        text = "if mixed:\n    space_indent()\nelse:\n\ttab_indent()"
        
        block = analyzer.analyze_conditional(text)
        
        assert block.get_branch_count() == 2


class TestCSADataStructures:
    """Test ConditionalBranch and ConditionalBlock data structures."""
    
    def test_conditional_branch_validation(self):
        """Test ConditionalBranch validates branch_type."""
        with pytest.raises(ValueError, match="Invalid branch_type"):
            ConditionalBranch(
                branch_type='invalid',
                condition=None,
                content_lines=[],
                start_line=0,
                end_line=0,
                indentation=0
            )
    
    def test_else_branch_cannot_have_condition(self):
        """Test that else branch with condition raises error."""
        with pytest.raises(ValueError, match="'else' branches cannot have a condition"):
            ConditionalBranch(
                branch_type='else',
                condition='some_condition',
                content_lines=[],
                start_line=0,
                end_line=0,
                indentation=0
            )
    
    def test_if_branch_must_have_condition(self):
        """Test that if/elif branch without condition raises error."""
        with pytest.raises(ValueError, match="must have a condition"):
            ConditionalBranch(
                branch_type='if',
                condition=None,
                content_lines=[],
                start_line=0,
                end_line=0,
                indentation=0
            )
    
    def test_conditional_block_must_start_with_if(self):
        """Test that ConditionalBlock validates first branch is 'if'."""
        else_branch = ConditionalBranch(
            branch_type='else',
            condition=None,
            content_lines=[],
            start_line=0,
            end_line=0,
            indentation=0
        )
        
        with pytest.raises(ValueError, match="First branch must be 'if'"):
            ConditionalBlock(
                branches=[else_branch],
                start_line=0,
                end_line=0,
                base_indentation=0
            )
    
    def test_conditional_block_no_branches_after_else(self):
        """Test that no branches can come after else."""
        if_branch = ConditionalBranch(
            branch_type='if',
            condition='test',
            content_lines=[],
            start_line=0,
            end_line=0,
            indentation=0
        )
        else_branch = ConditionalBranch(
            branch_type='else',
            condition=None,
            content_lines=[],
            start_line=1,
            end_line=1,
            indentation=0
        )
        elif_branch = ConditionalBranch(
            branch_type='elif',
            condition='other',
            content_lines=[],
            start_line=2,
            end_line=2,
            indentation=0
        )
        
        with pytest.raises(ValueError, match="No branches allowed after 'else'"):
            ConditionalBlock(
                branches=[if_branch, else_branch, elif_branch],
                start_line=0,
                end_line=2,
                base_indentation=0
            )
    
    def test_has_jump_in_branch(self):
        """Test has_jump_in_branch() method."""
        if_branch = ConditionalBranch(
            branch_type='if',
            condition='test',
            content_lines=['jump target'],
            start_line=0,
            end_line=1,
            indentation=0,
            contains_jump=True
        )
        else_branch = ConditionalBranch(
            branch_type='else',
            condition=None,
            content_lines=['pass'],
            start_line=2,
            end_line=3,
            indentation=0,
            contains_jump=False
        )
        
        block = ConditionalBlock(
            branches=[if_branch, else_branch],
            start_line=0,
            end_line=3,
            base_indentation=0
        )
        
        assert block.has_jump_in_branch(0) == True
        assert block.has_jump_in_branch(1) == False
    
    def test_has_jump_in_branch_out_of_range(self):
        """Test has_jump_in_branch() with invalid index."""
        if_branch = ConditionalBranch(
            branch_type='if',
            condition='test',
            content_lines=[],
            start_line=0,
            end_line=0,
            indentation=0
        )
        
        block = ConditionalBlock(
            branches=[if_branch],
            start_line=0,
            end_line=0,
            base_indentation=0
        )
        
        with pytest.raises(IndexError):
            block.has_jump_in_branch(5)


class TestCSARenpyPatterns:
    """Test real-world Ren'Py patterns from documented issues."""
    
    @pytest.fixture
    def analyzer(self):
        return ConditionalStructureAnalyzer()
    
    def test_dressingroom3_pattern(self, analyzer):
        """Test DressingRoom3 conditional pattern from conditional_blind_parser.py."""
        text = """    if DressingRoom3Status == 0:
        add "gui/choices/c11.png"
        textbutton "Try opening the door" xalign 0.5 ypos cpos5 action [Jump("DressingRoom3_TryHandle")]
    if DressingRoom3Status == 1 and DressingRoomPeeking == 0:
        add "gui/choices/c001.png"
        textbutton "Back away from the door" xalign 0.5 ypos cpos8 action [Jump("DressingRoomsStart")]"""
        
        # This has TWO separate if statements - should parse the first one
        block = analyzer.analyze_conditional(text)
        
        assert block.branches[0].branch_type == 'if'
        assert 'DressingRoom3Status == 0' in block.branches[0].condition
        content = '\n'.join(block.branches[0].content_lines)
        assert 'textbutton' in content
    
    def test_imagebutton_conditional_pattern(self, analyzer):
        """Test imagebutton conditional from CSAP_ACTION_TUPLES_AND_CONDITIONALS.md."""
        text = """    if variable is False:
        auto "images/active_%s.webp"
        action Jump("active_path")
    else:
        idle "images/inactive.webp"
        action NullAction()"""
        
        block = analyzer.analyze_conditional(text)
        
        assert block.get_branch_count() == 2
        assert 'variable is False' in block.branches[0].condition
        assert 'auto' in '\n'.join(block.branches[0].content_lines)
        assert 'idle' in '\n'.join(block.branches[1].content_lines)


def main():
    """Run all tests."""
    print("🧪 Running CSA Basic Tests...")
    print("=" * 60)
    
    # Run pytest
    result = pytest.main([
        __file__,
        '-v',  # Verbose
        '--tb=short',  # Short traceback format
        '-x'  # Stop on first failure
    ])
    
    return result == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

