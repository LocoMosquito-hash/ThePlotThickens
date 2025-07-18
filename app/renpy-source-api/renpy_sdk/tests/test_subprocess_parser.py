"""
Test the subprocess-based Ren'Py parser.

This test demonstrates the working solution for Ren'Py integration.
"""

import sys
import os
from pathlib import Path

# Add the src directory to path so we can import our utilities
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

from subprocess_parser import subprocess_parser


def test_subprocess_parser_info():
    """Test basic parser information."""
    print("="*60)
    print("TESTING SUBPROCESS PARSER INFO")
    print("="*60)
    
    info = subprocess_parser.get_info()
    print("Parser Info:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    return info["is_available"]


def test_analyze_tutorial_project():
    """Test analyzing the tutorial project."""
    print("\n" + "="*60)
    print("TESTING TUTORIAL PROJECT ANALYSIS")
    print("="*60)
    
    # Get path to tutorial project
    tutorial_path = subprocess_parser.sdk_path / "tutorial" / "game"
    
    if not tutorial_path.exists():
        print(f"❌ Tutorial project not found: {tutorial_path}")
        return False
    
    print(f"🔄 Analyzing tutorial project: {tutorial_path}")
    
    # Run the analysis
    success, results = subprocess_parser.analyze_project(str(tutorial_path), timeout=60)
    
    if success:
        print("✅ Analysis completed successfully!")
        
        # Display results summary
        metadata = results.get("metadata", {})
        project_info = results.get("project_info", {})
        
        print(f"\n📊 Analysis Results:")
        print(f"  Ren'Py Version: {metadata.get('renpy_version', 'Unknown')}")
        print(f"  Files Found: {project_info.get('rpy_files', 0)}")
        print(f"  Labels Found: {len(results.get('labels', []))}")
        print(f"  Characters Found: {len(results.get('characters', []))}")
        print(f"  Menus Found: {len(results.get('menus', []))}")
        print(f"  Errors: {len(results.get('errors', []))}")
        
        # Show some sample data
        labels = results.get("labels", [])
        if labels:
            print(f"\n📝 Sample Labels (first 5):")
            for label in labels[:5]:
                print(f"  - {label['name']} (in {label['file']}:{label['line']})")
        
        characters = results.get("characters", [])
        if characters:
            print(f"\n👥 Characters Found:")
            for char in characters:
                print(f"  - {char['name']} (in {char['file']}:{char['line']})")
        
        errors = results.get("errors", [])
        if errors:
            print(f"\n❌ Errors:")
            for error in errors[:3]:  # Show first 3 errors
                print(f"  - {error}")
        
        return True
    else:
        print("❌ Analysis failed!")
        error = results.get("error", "Unknown error")
        print(f"Error: {error}")
        
        # Show debug info if available
        if "stdout" in results:
            print(f"\nStdout: {results['stdout'][:200]}...")
        if "stderr" in results:
            print(f"\nStderr: {results['stderr'][:200]}...")
            
        return False


def test_analyze_the_question_project():
    """Test analyzing 'The Question' example project."""
    print("\n" + "="*60)
    print("TESTING 'THE QUESTION' PROJECT ANALYSIS")
    print("="*60)
    
    # Get path to 'The Question' project
    question_path = subprocess_parser.sdk_path / "the_question" / "game"
    
    if not question_path.exists():
        print(f"❌ 'The Question' project not found: {question_path}")
        return False
    
    print(f"🔄 Analyzing 'The Question' project: {question_path}")
    
    # Run the analysis with shorter timeout for simpler project
    success, results = subprocess_parser.analyze_project(str(question_path), timeout=30)
    
    if success:
        print("✅ Analysis completed successfully!")
        
        # Display results summary
        project_info = results.get("project_info", {})
        print(f"\n📊 'The Question' Analysis Results:")
        print(f"  Files Found: {project_info.get('rpy_files', 0)}")
        print(f"  Labels Found: {len(results.get('labels', []))}")
        print(f"  Characters Found: {len(results.get('characters', []))}")
        print(f"  Menus Found: {len(results.get('menus', []))}")
        
        return True
    else:
        print("❌ Analysis failed!")
        error = results.get("error", "Unknown error")
        print(f"Error: {error}")
        return False


def main():
    """Run all subprocess parser tests."""
    print("Subprocess Ren'Py Parser Test")
    print("Testing the working solution for Ren'Py integration...")
    
    # Test 1: Basic info
    info_success = test_subprocess_parser_info()
    
    if not info_success:
        print("\n❌ Parser not available. Cannot proceed with analysis tests.")
        return False
    
    # Test 2: Tutorial project analysis
    tutorial_success = test_analyze_tutorial_project()
    
    # Test 3: The Question project analysis  
    question_success = test_analyze_the_question_project()
    
    # Summary
    print("\n" + "="*60)
    print("SUBPROCESS PARSER TEST SUMMARY")
    print("="*60)
    print(f"Parser Available:       {'✅ PASS' if info_success else '❌ FAIL'}")
    print(f"Tutorial Analysis:      {'✅ PASS' if tutorial_success else '❌ FAIL'}")
    print(f"The Question Analysis:  {'✅ PASS' if question_success else '❌ FAIL'}")
    
    all_success = info_success and (tutorial_success or question_success)
    print(f"\nOverall Result:         {'✅ SUCCESS' if all_success else '❌ FAILURE'}")
    
    if all_success:
        print("\n🎉 Subprocess parser approach works!")
        print("This can now be integrated into your existing RenpyParser as a fallback.")
        print("\nNext steps:")
        print("1. Integrate subprocess_parser into your main RenpyParser class")
        print("2. Use it as fallback for complex parsing cases")
        print("3. Consume the JSON output in your TPT application")
    else:
        print("\n💥 Subprocess parser tests failed.")
        print("Check the error messages above for debugging.")
    
    return all_success


if __name__ == "__main__":
    main() 