#!/usr/bin/env python3
"""
Demo script for StartLabelFinder - Ren'Py Control Flow Analysis

This script demonstrates how to use the StartLabelFinder class to locate
the entry point of Ren'Py visual novels.
"""

import sys
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from app.renpy_source_api.control_flow import StartLabelFinder
    from app.renpy_source_api.control_flow.start_label_finder import StartLabelNotFoundError
    from app.renpy_source_api.exceptions import RenpyProjectError
except ImportError:
    # Fallback for standalone usage
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from control_flow.start_label_finder import StartLabelFinder, StartLabelNotFoundError
    from exceptions import RenpyProjectError


def demo_basic_usage():
    """Demo basic StartLabelFinder usage."""
    print("🎯 DEMO: Basic StartLabelFinder Usage")
    print("=" * 50)
    
    # Example paths - you can modify these to test with real VNs
    example_paths = [
        r"T:\AG\MySisterMyRoommateV1.69-pc\game",  # Complete VN
        r"T:\AG\TheAlphaGender-0.3b-pc\game",       # Small VN
        r"T:\AG\Savior-0.16c-pc\game",              # Large VN
    ]
    
    for i, project_path in enumerate(example_paths, 1):
        print(f"\n📁 Example {i}: {Path(project_path).name}")
        print("-" * 30)
        
        try:
            # Initialize the finder
            finder = StartLabelFinder(project_path)
            print(f"✅ Valid Ren'Py project found")
            
            # Find the start label
            start_line = finder.find_start_label()
            print(f"🎯 Start label found!")
            print(f"   File: {Path(start_line.file_path).name}")
            print(f"   Line: {start_line.line_number}")
            print(f"   Content: {start_line.content.strip()}")
            
            # Get additional project info
            info = finder.get_project_info()
            print(f"📊 Project info:")
            print(f"   Total .rpy files: {info['total_rpy_files']}")
            print(f"   Start location: {info['start_file']}:{info['start_line']}")
            
        except StartLabelNotFoundError as e:
            print(f"⚠️  No start label found: {e}")
            
        except RenpyProjectError as e:
            print(f"❌ Project error: {e}")
            
        except Exception as e:
            print(f"🔧 Error: {e}")


def demo_validation():
    """Demo validation features."""
    print("\n\n🔍 DEMO: Validation Features")
    print("=" * 50)
    
    test_paths = [
        r"T:\AG\MySisterMyRoommateV1.69-pc\game",
        r"C:\NonExistent\Path",
        r"C:\Windows\System32",  # Not a Ren'Py project
    ]
    
    for path in test_paths:
        print(f"\n📂 Testing: {path}")
        print("-" * 40)
        
        try:
            finder = StartLabelFinder(path)
            
            # Quick validation
            is_valid = finder.validate_start_label()
            print(f"Has valid start label: {is_valid}")
            
            if is_valid:
                file_path, line_number = finder.get_start_location()
                print(f"Location: {file_path}:{line_number}")
                
        except Exception as e:
            print(f"❌ {type(e).__name__}: {e}")


def demo_project_info():
    """Demo detailed project information extraction."""
    print("\n\n📊 DEMO: Project Information")
    print("=" * 50)
    
    project_path = r"T:\AG\MySisterMyRoommateV1.69-pc\game"
    
    try:
        finder = StartLabelFinder(project_path)
        info = finder.get_project_info()
        
        print(f"Project: {Path(project_path).parent.name}")
        print(f"Path: {info['project_path']}")
        print(f"Total .rpy files: {info['total_rpy_files']}")
        print(f"Has start label: {info['has_start_label']}")
        
        if info['has_start_label']:
            print(f"Start file: {info['start_file']}")
            print(f"Start line: {info['start_line']}")
            print(f"Start location: {info['start_location']}")
        
        print(f"\n📄 .rpy files found:")
        for i, file in enumerate(info['rpy_files'][:10], 1):  # Show first 10
            print(f"  {i:2d}. {file}")
        if len(info['rpy_files']) > 10:
            print(f"      ... and {len(info['rpy_files']) - 10} more files")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def demo_error_handling():
    """Demo error handling scenarios."""
    print("\n\n🚨 DEMO: Error Handling")
    print("=" * 50)
    
    scenarios = [
        ("Missing path", r"C:\DoesNotExist\game"),
        ("Not a Ren'Py project", r"C:\Windows"),
        ("No start label", None),  # We'll create a test case for this
    ]
    
    for scenario_name, path in scenarios:
        print(f"\n🔬 Scenario: {scenario_name}")
        print("-" * 30)
        
        try:
            if path:
                finder = StartLabelFinder(path)
                start_line = finder.find_start_label()
                print(f"✅ Unexpected success: {start_line.label_name}")
            else:
                print("⚠️  Would test 'no start label' scenario with custom test project")
                
        except StartLabelNotFoundError as e:
            print(f"🎯 Expected: StartLabelNotFoundError - {e}")
            
        except RenpyProjectError as e:
            print(f"🎯 Expected: RenpyProjectError - {e}")
            
        except Exception as e:
            print(f"❌ Unexpected error: {type(e).__name__} - {e}")


def interactive_demo():
    """Interactive demo where user can test their own paths."""
    print("\n\n🎮 INTERACTIVE DEMO")
    print("=" * 50)
    
    while True:
        print("\nEnter a Ren'Py project path (or 'quit' to exit):")
        user_input = input("Path: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            break
            
        if not user_input:
            continue
            
        print(f"\n🔍 Analyzing: {user_input}")
        print("-" * 40)
        
        try:
            finder = StartLabelFinder(user_input)
            
            # Quick analysis
            is_valid = finder.validate_start_label()
            info = finder.get_project_info()
            
            print(f"Valid Ren'Py project: ✅")
            print(f"Total .rpy files: {info['total_rpy_files']}")
            print(f"Has start label: {'✅' if is_valid else '❌'}")
            
            if is_valid:
                start_line = finder.find_start_label()
                print(f"Start location: {info['start_file']}:{info['start_line']}")
                print(f"Content: {start_line.content.strip()}")
                
        except Exception as e:
            print(f"❌ {type(e).__name__}: {e}")


def main():
    """Main demo function."""
    print("🚀 StartLabelFinder Demo")
    print("=" * 60)
    
    # Run demos
    demo_basic_usage()
    demo_validation()
    demo_project_info()
    demo_error_handling()
    
    # Ask if user wants interactive demo
    print("\n" + "=" * 60)
    response = input("Would you like to try the interactive demo? (y/n): ").strip().lower()
    
    if response in ['y', 'yes']:
        interactive_demo()
    
    print("\n🎉 Demo complete!")
    print("\nNext steps:")
    print("- Use StartLabelFinder in your control flow analysis")
    print("- Build upon this foundation for label flow tracing")
    print("- Integrate with The Plot Thickens main application")


if __name__ == "__main__":
    main() 