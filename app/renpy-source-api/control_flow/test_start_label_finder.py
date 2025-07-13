"""
Unit tests for StartLabelFinder class.

Tests the ability to locate 'start' labels in Ren'Py projects with various
scenarios including normal cases, edge cases, and error conditions.
"""

import unittest
import tempfile
import os
import shutil
from pathlib import Path
from typing import Dict, List

try:
    # Try relative imports
    from .start_label_finder import StartLabelFinder, StartLabelNotFoundError
    from ..exceptions import RenpyProjectError, RenpyParseError
except ImportError:
    # Fall back to direct imports for standalone testing
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from control_flow.start_label_finder import StartLabelFinder, StartLabelNotFoundError
    from exceptions import RenpyProjectError, RenpyParseError


class TestStartLabelFinder(unittest.TestCase):
    """Test cases for StartLabelFinder class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test projects
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)
    
    def create_test_project(self, files: Dict[str, str]) -> str:
        """
        Create a test Ren'Py project with specified files.
        
        Args:
            files: Dictionary mapping file names to their content
            
        Returns:
            str: Path to the created test project directory
        """
        project_path = os.path.join(self.test_dir, f"test_project_{len(os.listdir(self.test_dir))}")
        os.makedirs(project_path, exist_ok=True)
        
        for filename, content in files.items():
            file_path = os.path.join(project_path, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return project_path
    
    def test_find_start_label_simple(self):
        """Test finding start label in a simple project."""
        project = self.create_test_project({
            "script.rpy": '''
# Simple test script
define e = Character("Eileen")

label start:
    e "Hello, world!"
    return
'''
        })
        
        finder = StartLabelFinder(project)
        start_line = finder.find_start_label()
        
        self.assertEqual(start_line.line_type, 'label')
        self.assertEqual(start_line.label_name, 'start')
        self.assertEqual(start_line.line_number, 5)
        self.assertIn('label start:', start_line.content)
    
    def test_find_start_label_case_insensitive(self):
        """Test finding start label with different case."""
        project = self.create_test_project({
            "script.rpy": '''
label Start:
    "Testing case insensitivity"
    return
'''
        })
        
        finder = StartLabelFinder(project)
        start_line = finder.find_start_label()
        
        self.assertEqual(start_line.label_name, 'Start')
        self.assertEqual(start_line.line_number, 2)
    
    def test_find_start_label_multiple_files(self):
        """Test finding start label across multiple files."""
        project = self.create_test_project({
            "script.rpy": '''
# Main script file
define e = Character("Eileen")

label intro:
    e "This is the intro"
    jump start
''',
            "chapter1.rpy": '''
# Chapter 1
label start:
    "Chapter 1 begins here"
    return
''',
            "characters.rpy": '''
# Character definitions
define m = Character("Mary")
'''
        })
        
        finder = StartLabelFinder(project)
        start_line = finder.find_start_label()
        
        self.assertEqual(start_line.label_name, 'start')
        self.assertIn('chapter1.rpy', start_line.file_path)
    
    def test_start_label_not_found(self):
        """Test handling when start label is missing."""
        project = self.create_test_project({
            "script.rpy": '''
# No start label here
define e = Character("Eileen")

label intro:
    e "Just an intro"
    return
'''
        })
        
        finder = StartLabelFinder(project)
        
        with self.assertRaises(StartLabelNotFoundError) as context:
            finder.find_start_label()
        
        self.assertIn("No 'start' label found", str(context.exception))
        self.assertIn("script.rpy", str(context.exception))
    
    def test_no_rpy_files(self):
        """Test handling when no .rpy files exist."""
        project = self.create_test_project({
            "readme.txt": "This is not a Ren'Py project",
            "script.py": "print('Wrong file type')"
        })
        
        with self.assertRaises(RenpyProjectError) as context:
            StartLabelFinder(project)
        
        self.assertIn("does not appear to be a Ren'Py project", str(context.exception))
    
    def test_invalid_project_path(self):
        """Test handling invalid project paths."""
        invalid_path = os.path.join(self.test_dir, "nonexistent")
        
        with self.assertRaises(RenpyProjectError) as context:
            StartLabelFinder(invalid_path)
        
        self.assertIn("Project path does not exist", str(context.exception))
    
    def test_get_start_location(self):
        """Test getting start label location as tuple."""
        project = self.create_test_project({
            "story.rpy": '''
label start:
    "Story begins"
    return
'''
        })
        
        finder = StartLabelFinder(project)
        file_path, line_number = finder.get_start_location()
        
        self.assertEqual(file_path, "story.rpy")
        self.assertEqual(line_number, 2)
    
    def test_validate_start_label_exists(self):
        """Test validation when start label exists."""
        project = self.create_test_project({
            "script.rpy": '''
label start:
    "Valid project"
    return
'''
        })
        
        finder = StartLabelFinder(project)
        self.assertTrue(finder.validate_start_label())
    
    def test_validate_start_label_missing(self):
        """Test validation when start label is missing."""
        project = self.create_test_project({
            "script.rpy": '''
label intro:
    "No start label"
    return
'''
        })
        
        finder = StartLabelFinder(project)
        self.assertFalse(finder.validate_start_label())
    
    def test_get_project_info_with_start(self):
        """Test getting project info when start label exists."""
        project = self.create_test_project({
            "script.rpy": '''
label start:
    "Main story"
    return
''',
            "characters.rpy": '''
define e = Character("Eileen")
'''
        })
        
        finder = StartLabelFinder(project)
        info = finder.get_project_info()
        
        self.assertEqual(info['total_rpy_files'], 2)
        self.assertTrue(info['has_start_label'])
        self.assertEqual(info['start_file'], "script.rpy")
        self.assertEqual(info['start_line'], 2)
        self.assertIn("script.rpy", info['rpy_files'])
        self.assertIn("characters.rpy", info['rpy_files'])
    
    def test_get_project_info_without_start(self):
        """Test getting project info when start label is missing."""
        project = self.create_test_project({
            "script.rpy": '''
label intro:
    "No start here"
    return
'''
        })
        
        finder = StartLabelFinder(project)
        info = finder.get_project_info()
        
        self.assertEqual(info['total_rpy_files'], 1)
        self.assertFalse(info['has_start_label'])
        self.assertIsNone(info['start_file'])
        self.assertIsNone(info['start_line'])
    
    def test_malformed_rpy_file(self):
        """Test handling malformed .rpy files."""
        project = self.create_test_project({
            "good.rpy": '''
label start:
    "This works"
    return
''',
            "bad.rpy": '''
This is not valid Ren'Py syntax at all!
No proper structure here.
'''
        })
        
        # Should still find start label in the good file
        finder = StartLabelFinder(project)
        start_line = finder.find_start_label()
        
        self.assertEqual(start_line.label_name, 'start')
        self.assertIn('good.rpy', start_line.file_path)
    
    def test_empty_rpy_file(self):
        """Test handling empty .rpy files."""
        project = self.create_test_project({
            "empty.rpy": "",
            "script.rpy": '''
label start:
    "Found it"
    return
'''
        })
        
        finder = StartLabelFinder(project)
        start_line = finder.find_start_label()
        
        self.assertEqual(start_line.label_name, 'start')
    
    def test_start_label_with_indentation(self):
        """Test finding start label with various indentation."""
        project = self.create_test_project({
            "script.rpy": '''
if True:
    pass

label start:
    "Properly indented start"
    return
'''
        })
        
        finder = StartLabelFinder(project)
        start_line = finder.find_start_label()
        
        self.assertEqual(start_line.label_name, 'start')
        self.assertEqual(start_line.line_number, 5)
    
    def test_start_label_with_comments(self):
        """Test finding start label with comments."""
        project = self.create_test_project({
            "script.rpy": '''
# This is the main script file
# Author: Test

# Main story entry point
label start:  # This is where the game begins
    "Welcome to the game!"
    return
'''
        })
        
        finder = StartLabelFinder(project)
        start_line = finder.find_start_label()
        
        self.assertEqual(start_line.label_name, 'start')
        self.assertEqual(start_line.line_number, 6)
    
    def test_excluded_files_ignored(self):
        """Test that excluded system files are properly ignored."""
        project = self.create_test_project({
            "script.rpy": '''
label start:
    "Main story"
    return
''',
            "screens.rpy": '''
# This should be ignored
label start:
    "Fake start in screens"
    return
''',
            "gui.rpy": '''
# GUI file with fake start
label start:
    "Another fake start"
    return
'''
        })
        
        finder = StartLabelFinder(project)
        start_line = finder.find_start_label()
        
        # Should find the start in script.rpy, not in excluded files
        self.assertEqual(start_line.label_name, 'start')
        self.assertIn('script.rpy', start_line.file_path)
        self.assertNotIn('screens.rpy', start_line.file_path)
        self.assertNotIn('gui.rpy', start_line.file_path)


class TestStartLabelFinderIntegration(unittest.TestCase):
    """Integration tests for StartLabelFinder with realistic scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)
    
    def create_realistic_project(self) -> str:
        """Create a realistic Ren'Py project structure."""
        project_path = os.path.join(self.test_dir, "realistic_vn")
        os.makedirs(project_path, exist_ok=True)
        
        files = {
            "script.rpy": '''
# The main script file for the visual novel
define e = Character("Eileen", color="#c8ffc8")
define m = Character("Me", color="#c8c8ff")

# The game starts here
label start:
    scene bg room
    show eileen happy
    
    e "You've created a new Ren'Py game."
    e "Once you add a story, pictures, and music, you can release it to the world!"
    
    return
''',
            "characters.rpy": '''
# Character definitions
define narrator = Character(None, kind=nvl)
define side_character = Character("Side Character", color="#ffff00")
''',
            "chapter1.rpy": '''
# Chapter 1 content
label chapter1_start:
    "Chapter 1 begins here"
    
    call some_scene
    return

label some_scene:
    "This is a scene"
    return
''',
            "options.rpy": '''
# Game options and configuration
define config.name = "Test VN"
define config.version = "1.0"
''',
            "screens.rpy": '''
# Screen definitions (should be ignored)
screen main_menu():
    vbox:
        textbutton "Start" action Start()
'''
        }
        
        for filename, content in files.items():
            file_path = os.path.join(project_path, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return project_path
    
    def test_realistic_project_analysis(self):
        """Test analysis of a realistic Ren'Py project."""
        project = self.create_realistic_project()
        
        finder = StartLabelFinder(project)
        
        # Test finding the start label
        start_line = finder.find_start_label()
        self.assertEqual(start_line.label_name, 'start')
        self.assertIn('script.rpy', start_line.file_path)
        
        # Test project info
        info = finder.get_project_info()
        self.assertTrue(info['has_start_label'])
        self.assertEqual(info['start_file'], 'script.rpy')
        self.assertGreaterEqual(info['total_rpy_files'], 3)  # script, characters, chapter1, others
        
        # Verify excluded files are not counted (screens.rpy should be excluded)
        self.assertNotIn('screens.rpy', info['rpy_files'])
        self.assertIn('script.rpy', info['rpy_files'])
        self.assertIn('characters.rpy', info['rpy_files'])
        self.assertIn('chapter1.rpy', info['rpy_files'])


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestStartLabelFinder))
    suite.addTests(loader.loadTestsFromTestCase(TestStartLabelFinderIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1) 