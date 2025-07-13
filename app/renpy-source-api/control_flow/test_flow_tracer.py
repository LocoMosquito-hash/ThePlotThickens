"""
Unit tests for FlowTracer class.

Tests the ability to trace narrative flow in Ren'Py projects, starting from
the start label and following sequential execution until flow control is encountered.
"""

import unittest
import tempfile
import os
import shutil
from pathlib import Path
from typing import Dict, List

try:
    # Try relative imports
    from .flow_tracer import FlowTracer, FlowStep, FlowTraceResult, FlowTracerError
    from .start_label_finder import StartLabelNotFoundError
    from ..exceptions import RenpyProjectError, RenpyParseError
except ImportError:
    # Fall back to direct imports for standalone testing
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from control_flow.flow_tracer import FlowTracer, FlowStep, FlowTraceResult, FlowTracerError
    from control_flow.start_label_finder import StartLabelNotFoundError
    from exceptions import RenpyProjectError, RenpyParseError


class TestFlowTracer(unittest.TestCase):
    """Test cases for FlowTracer functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = None
    
    def tearDown(self):
        """Clean up test environment."""
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def create_test_project(self, files: Dict[str, str]) -> str:
        """
        Create a temporary test project with given files.
        
        Args:
            files: Dictionary mapping file paths to content
            
        Returns:
            Path to the test project root
        """
        self.test_dir = tempfile.mkdtemp()
        project_root = Path(self.test_dir)
        
        # Ensure game directory exists
        game_dir = project_root / "game"
        game_dir.mkdir(exist_ok=True)
        
        for file_path, content in files.items():
            full_path = game_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding='utf-8')
        
        return str(project_root)
    
    def test_simple_dialogue_flow(self):
        """Test tracing simple dialogue from start label."""
        project = self.create_test_project({
            "script.rpy": '''
label start:
    "Hello, world!"
    "This is a test."
    "End of dialogue."
    return
'''
        })
        
        tracer = FlowTracer(project)
        result = tracer.trace_from_start()
        
        self.assertEqual(len(result.steps), 4)  # label + 3 dialogue lines
        self.assertEqual(result.stop_reason, "flow_control_return")
        self.assertEqual(result.flow_control_encountered, "return")
        
        # Check step types
        self.assertEqual(result.steps[0].statement_type, "label")
        self.assertEqual(result.steps[1].statement_type, "dialogue")
        self.assertEqual(result.steps[2].statement_type, "dialogue")
        self.assertEqual(result.steps[3].statement_type, "dialogue")
    
    def test_character_dialogue_flow(self):
        """Test tracing character dialogue."""
        project = self.create_test_project({
            "script.rpy": '''
define e = Character("Eileen")

label start:
    e "Hello, I'm Eileen!"
    "Anonymous narrator speaking."
    e "Nice to meet you!"
    return
'''
        })
        
        tracer = FlowTracer(project)
        result = tracer.trace_from_start()
        
        # Find character dialogue steps
        char_dialogue_steps = [s for s in result.steps if s.statement_type == "character_dialogue"]
        self.assertEqual(len(char_dialogue_steps), 2)
        
        # Check character extraction
        self.assertIsNotNone(char_dialogue_steps[0].parsed_data)
        self.assertIsNotNone(char_dialogue_steps[1].parsed_data)
        if char_dialogue_steps[0].parsed_data:
            self.assertEqual(char_dialogue_steps[0].parsed_data['character'], 'e')
        if char_dialogue_steps[1].parsed_data:
            self.assertEqual(char_dialogue_steps[1].parsed_data['character'], 'e')
    
    def test_mixed_statements_flow(self):
        """Test tracing various types of statements."""
        project = self.create_test_project({
            "script.rpy": '''
define e = Character("Eileen")
default mood = "happy"

label start:
    scene bg room
    show eileen happy
    play music "theme.mp3"
    e "Welcome to the game!"
    $ player_name = "Player"
    "The story begins..."
    hide eileen
    stop music
    jump next_scene
'''
        })
        
        tracer = FlowTracer(project)
        result = tracer.trace_from_start()
        
        # Should stop at jump statement
        self.assertEqual(result.stop_reason, "flow_control_jump")
        self.assertEqual(result.flow_control_encountered, "jump")
        
        # Check variety of statement types
        statement_types = [step.statement_type for step in result.steps]
        self.assertIn("label", statement_types)
        self.assertIn("scene", statement_types)
        self.assertIn("show", statement_types)
        self.assertIn("play", statement_types)
        self.assertIn("character_dialogue", statement_types)
        self.assertIn("python", statement_types)
        self.assertIn("dialogue", statement_types)
        self.assertIn("hide", statement_types)
        self.assertIn("stop", statement_types)
        self.assertIn("jump", statement_types)
    
    def test_flow_control_detection(self):
        """Test detection of different flow control statements."""
        test_cases = [
            ("jump next_label", "flow_control_jump", "jump"),
            ("call subroutine", "flow_control_call", "call"),
            ("return", "flow_control_return", "return"),
            ("menu:", "flow_control_menu", "menu"),
        ]
        
        for flow_stmt, expected_reason, expected_control in test_cases:
            with self.subTest(flow_stmt=flow_stmt):
                project = self.create_test_project({
                    "script.rpy": f'''
label start:
    "Before flow control"
    {flow_stmt}
    "This should not be reached"
'''
                })
                
                tracer = FlowTracer(project)
                result = tracer.trace_from_start()
                
                self.assertEqual(result.stop_reason, expected_reason)
                self.assertEqual(result.flow_control_encountered, expected_control)
                self.assertEqual(len(result.steps), 2)  # label + dialogue
    
    def test_end_of_file_detection(self):
        """Test detection when end of file is reached."""
        project = self.create_test_project({
            "script.rpy": '''
label start:
    "First line"
    "Second line"
    "Last line"
'''
        })
        
        tracer = FlowTracer(project)
        result = tracer.trace_from_start()
        
        self.assertEqual(result.stop_reason, "end_of_file")
        self.assertIsNone(result.flow_control_encountered)
        self.assertEqual(len(result.steps), 4)  # label + 3 dialogue lines
    
    def test_max_steps_limit(self):
        """Test max steps limit prevents infinite loops."""
        project = self.create_test_project({
            "script.rpy": '''
label start:
    "Line 1"
    "Line 2"  
    "Line 3"
    "Line 4"
    "Line 5"
    "Line 6"
    "Line 7"
    "Line 8"
    "Line 9"
    "Line 10"
'''
        })
        
        tracer = FlowTracer(project)
        result = tracer.trace_flow(max_steps=5)
        
        self.assertEqual(result.stop_reason, "max_steps_reached")
        self.assertEqual(len(result.steps), 5)
    
    def test_comments_and_empty_lines(self):
        """Test handling of comments and empty lines."""
        project = self.create_test_project({
            "script.rpy": '''
# This is a comment
label start:
    # Another comment
    
    "Dialogue after empty line"
    
    # Final comment
    return
'''
        })
        
        tracer = FlowTracer(project)
        result = tracer.trace_from_start()
        
        # Check that comments and empty lines are captured
        statement_types = [step.statement_type for step in result.steps]
        self.assertIn("comment", statement_types)
        self.assertIn("empty", statement_types)
        self.assertIn("dialogue", statement_types)
    
    def test_flow_summary(self):
        """Test flow summary generation."""
        project = self.create_test_project({
            "script.rpy": '''
define e = Character("Eileen")

label start:
    scene bg room
    e "Hello!"
    "Narrator text"
    e "Goodbye!"
    jump next_scene
'''
        })
        
        tracer = FlowTracer(project)
        result = tracer.trace_from_start()
        summary = tracer.get_flow_summary(result)
        
        self.assertEqual(summary['total_lines_traced'], len(result.steps))
        self.assertEqual(summary['stop_reason'], "flow_control_jump")
        self.assertEqual(summary['flow_control_encountered'], "jump")
        self.assertEqual(summary['dialogue_lines'], 3)  # 2 character + 1 narrator
        
        # Check statement counts
        self.assertTrue('label' in summary['statement_counts'])
        self.assertTrue('character_dialogue' in summary['statement_counts'])
        self.assertTrue('dialogue' in summary['statement_counts'])
    
    def test_invalid_project_path(self):
        """Test handling of invalid project paths."""
        with self.assertRaises(RenpyProjectError):
            FlowTracer("/nonexistent/path")
    
    def test_no_start_label(self):
        """Test handling when start label is missing."""
        project = self.create_test_project({
            "script.rpy": '''
define e = Character("Eileen")

label chapter1:
    e "This is not the start!"
    return
'''
        })
        
        with self.assertRaises(StartLabelNotFoundError):
            FlowTracer(project)
    
    def test_jump_target_extraction(self):
        """Test extraction of jump target information."""
        project = self.create_test_project({
            "script.rpy": '''
label start:
    "Before jump"
    jump chapter2
'''
        })
        
        tracer = FlowTracer(project)
        result = tracer.trace_from_start()
        
        # Find the jump step
        jump_step = next(s for s in result.steps if s.statement_type == "jump")
        self.assertIsNotNone(jump_step.parsed_data)
        if jump_step.parsed_data:
            self.assertEqual(jump_step.parsed_data['target'], 'chapter2')
    
    def test_call_target_extraction(self):
        """Test extraction of call target information."""
        project = self.create_test_project({
            "script.rpy": '''
label start:
    "Before call"
    call subroutine
'''
        })
        
        tracer = FlowTracer(project)
        result = tracer.trace_from_start()
        
        # Find the call step
        call_step = next(s for s in result.steps if s.statement_type == "call")
        self.assertIsNotNone(call_step.parsed_data)
        if call_step.parsed_data:
            self.assertEqual(call_step.parsed_data['target'], 'subroutine')
    
    def test_unknown_statement_classification(self):
        """Test classification of unknown/custom statements."""
        project = self.create_test_project({
            "script.rpy": '''
label start:
    "Normal dialogue"
    custom_statement with parameters
    weird_syntax ??? unknown
    return
'''
        })
        
        tracer = FlowTracer(project)
        result = tracer.trace_from_start()
        
        # Check that unknown statements are classified as "unknown"
        unknown_steps = [s for s in result.steps if s.statement_type == "unknown"]
        self.assertEqual(len(unknown_steps), 2)

    def test_simple_jump_following(self):
        """Test basic jump following functionality."""
        project = self.create_test_project({
            "script.rpy": '''
label start:
    "Beginning of story"
    jump middle_scene
    "This should not be reached"

label middle_scene:
    "Middle of the story"
    "More dialogue"
    jump ending

label ending:
    "The end"
    return
'''
        })
        
        tracer = FlowTracer(project)
        result = tracer.trace_from_start()
        
        # Should follow both jumps and reach return
        self.assertEqual(result.stop_reason, "flow_control_return")
        self.assertEqual(result.flow_control_encountered, "return")
        
        # Check the sequence of steps
        expected_content = [
            "label start:",
            '"Beginning of story"',
            "jump middle_scene",
            "label middle_scene:",
            '"Middle of the story"',
            '"More dialogue"',
            "jump ending",
            "label ending:",
            '"The end"',
            "return"
        ]
        
        actual_content = [step.content for step in result.steps]
        self.assertEqual(actual_content, expected_content)
        
        # Verify we visited multiple labels
        labels_visited = [step.content for step in result.steps if step.statement_type == 'label']
        self.assertEqual(len(labels_visited), 3)  # start, middle_scene, ending
    
    def test_jump_infinite_loop_prevention(self):
        """Test prevention of infinite jump loops."""
        project = self.create_test_project({
            "script.rpy": '''
label start:
    "Beginning"
    jump loop_a

label loop_a:
    "In loop A"
    jump loop_b

label loop_b:
    "In loop B"
    jump loop_a
'''
        })
        
        tracer = FlowTracer(project)
        result = tracer.trace_from_start()
        
        # Should detect infinite loop and stop
        self.assertEqual(result.stop_reason, "infinite_jump_loop")
        self.assertEqual(result.flow_control_encountered, "jump")
        
        # Should have detected the loop before completing it multiple times
        self.assertGreater(len(result.steps), 5)  # At least some steps before loop detection
        self.assertLess(len(result.steps), 20)   # But not too many
    
    def test_jump_target_not_found(self):
        """Test handling of jump to non-existent label."""
        project = self.create_test_project({
            "script.rpy": '''
label start:
    "Beginning"
    jump nonexistent_label
    "This should not be reached"
'''
        })
        
        tracer = FlowTracer(project)
        result = tracer.trace_from_start()
        
        # Should stop when jump target is not found
        self.assertEqual(result.stop_reason, "jump_target_not_found")
        self.assertEqual(result.flow_control_encountered, "jump")
        
        # Should have traced up to the problematic jump
        self.assertEqual(len(result.steps), 3)  # label, dialogue, jump
    
    def test_cross_file_jumping(self):
        """Test jumping between different files."""
        project = self.create_test_project({
            "script.rpy": '''
label start:
    "In main script"
    jump chapter1
''',
            "chapter1.rpy": '''
label chapter1:
    "In chapter 1"
    "More content"
    jump epilogue
''',
            "epilogue.rpy": '''
label epilogue:
    "In epilogue"
    return
'''
        })
        
        tracer = FlowTracer(project)
        result = tracer.trace_from_start()
        
        # Should successfully follow jumps across files
        self.assertEqual(result.stop_reason, "flow_control_return")
        self.assertEqual(result.flow_control_encountered, "return")
        
        # Check that we visited all three files
        files_visited = set(step.file_path for step in result.steps)
        expected_files = {"game\\script.rpy", "game\\chapter1.rpy", "game\\epilogue.rpy"}
        
        # Convert to relative paths for comparison (handling different path separators)
        files_visited_relative = {f.replace("\\", "/").split("/")[-1] for f in files_visited}
        expected_files_relative = {"script.rpy", "chapter1.rpy", "epilogue.rpy"}
        
        self.assertEqual(files_visited_relative, expected_files_relative)
    
    def test_jump_vs_other_flow_control(self):
        """Test that jumps are followed but other flow control statements still stop tracing."""
        project = self.create_test_project({
            "script.rpy": '''
label start:
    "Beginning"
    jump middle

label middle:
    "Middle section"
    call subroutine
    "This should not be reached"

label subroutine:
    "In subroutine"
    return
'''
        })
        
        tracer = FlowTracer(project)
        result = tracer.trace_from_start()
        
        # Should follow the jump but stop at the call
        self.assertEqual(result.stop_reason, "flow_control_call")
        self.assertEqual(result.flow_control_encountered, "call")
        
        # Should have reached the middle label via jump
        labels_in_steps = [step.content for step in result.steps if step.statement_type == 'label']
        self.assertIn("label middle:", labels_in_steps)
    
    def test_local_label_jumping(self):
        """Test jumping to local labels."""
        project = self.create_test_project({
            "script.rpy": '''
label start:
    "Beginning"
    jump .local_scene

label .local_scene:
    "In local scene"
    return
'''
        })
        
        tracer = FlowTracer(project)
        result = tracer.trace_from_start()
        
        # Should successfully resolve and follow local label jump
        self.assertEqual(result.stop_reason, "flow_control_return")
        
        # Should have found both labels
        labels_in_steps = [step.content for step in result.steps if step.statement_type == 'label']
        self.assertEqual(len(labels_in_steps), 2)
        self.assertIn("label .local_scene:", labels_in_steps)


class TestFlowTracerIntegration(unittest.TestCase):
    """Integration tests for FlowTracer with complex scenarios."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = None
    
    def tearDown(self):
        """Clean up test environment."""
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def create_test_project(self, files: Dict[str, str]) -> str:
        """Create a temporary test project with given files."""
        self.test_dir = tempfile.mkdtemp()
        project_root = Path(self.test_dir)
        
        game_dir = project_root / "game"
        game_dir.mkdir(exist_ok=True)
        
        for file_path, content in files.items():
            full_path = game_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding='utf-8')
        
        return str(project_root)
    
    def test_realistic_vn_opening(self):
        """Test tracing a realistic VN opening sequence."""
        project = self.create_test_project({
            "script.rpy": '''
define e = Character("Eileen", color="#c8ffc8")
define n = Character("Narrator")

label start:
    scene bg room
    with fade
    
    play music "theme.mp3" fadeout 2.0 fadein 2.0
    
    "It was a dark and stormy night..."
    "The wind howled through the trees."
    
    show eileen happy
    with dissolve
    
    e "Hello! Welcome to my world!"
    
    $ player_name = renpy.input("What's your name?", default="Player")
    if player_name == "":
        $ player_name = "Player"
    
    e "Nice to meet you, [player_name]!"
    
    menu:
        "What would you like to do?"
        
        "Explore the house":
            jump explore_house
            
        "Talk to Eileen":
            jump talk_eileen
'''
        })
        
        tracer = FlowTracer(project)
        result = tracer.trace_from_start(max_steps=50)
        summary = tracer.get_flow_summary(result)
        
        # Should stop at menu
        self.assertEqual(result.stop_reason, "flow_control_menu")
        self.assertEqual(result.flow_control_encountered, "menu")
        
        # Should contain various statement types
        self.assertTrue(summary['dialogue_lines'] > 0)
        self.assertIn('scene', summary['statement_counts'])
        self.assertIn('play', summary['statement_counts'])
        self.assertIn('show', summary['statement_counts'])
        self.assertIn('character_dialogue', summary['statement_counts'])
        
        # Should trace significant number of lines
        self.assertGreater(summary['total_lines_traced'], 10)


def run_tests():
    """Run all FlowTracer tests."""
    print("Running FlowTracer Tests...")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestFlowTracer))
    suite.addTest(unittest.makeSuite(TestFlowTracerIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All FlowTracer tests passed!")
    else:
        print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1) 