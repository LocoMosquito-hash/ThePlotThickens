#!/usr/bin/env python3
"""
Debug script for jump following functionality.
Helps identify issues with the implementation.
"""

import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path to import flow_tracer
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))

from flow_tracer import FlowTracer

def create_test_project():
    """Create a simple test project."""
    test_dir = tempfile.mkdtemp()
    project_root = Path(test_dir)
    game_dir = project_root / 'game'
    game_dir.mkdir(exist_ok=True)
    
    script_content = '''
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
    
    script_path = game_dir / 'script.rpy'
    script_path.write_text(script_content)
    
    return str(project_root)

def debug_label_cache():
    """Debug the label cache building."""
    print("🔍 Debugging Label Cache Building...")
    
    project = create_test_project()
    
    try:
        tracer = FlowTracer(project)
        
        # Force build label cache
        tracer._build_label_cache()
        
        print(f"   📋 Label cache built: {tracer._label_cache_built}")
        print(f"   📋 Labels found: {len(tracer._label_cache)}")
        
        for label_name, (file_path, line_num) in tracer._label_cache.items():
            print(f"      - {label_name}: {file_path}:{line_num}")
        
        # Test label lookup
        print(f"\n   🔍 Testing label lookups:")
        labels_to_test = ['start', 'middle_scene', 'ending', 'nonexistent']
        
        for label in labels_to_test:
            location = tracer._find_label_location(label)
            if location:
                file_path, line_num = location
                print(f"      - {label}: Found at {file_path}:{line_num}")
            else:
                print(f"      - {label}: Not found")
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        shutil.rmtree(project)

def debug_file_parsing():
    """Debug how files are being parsed."""
    print("\n🔍 Debugging File Parsing...")
    
    project = create_test_project()
    
    try:
        tracer = FlowTracer(project)
        
        # Get the start file and parse it
        start_file = tracer.start_location[0]
        print(f"   📂 Start file: {start_file}")
        
        # Parse the file
        lines = tracer._get_file_lines(start_file)
        print(f"   📄 Parsed lines: {len(lines)}")
        
        for i, line in enumerate(lines):
            print(f"      {i+1:2d}. [{line.line_type:10}] '{line.content}' (label: {line.label_name})")
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        shutil.rmtree(project)

def debug_trace_steps():
    """Debug the tracing step by step."""
    print("\n🔍 Debugging Trace Steps...")
    
    project = create_test_project()
    
    try:
        tracer = FlowTracer(project)
        result = tracer.trace_from_start(max_steps=20)
        
        print(f"   📊 Total steps: {len(result.steps)}")
        print(f"   🛑 Stop reason: {result.stop_reason}")
        print(f"   🔄 Flow control: {result.flow_control_encountered}")
        
        print(f"\n   📝 Step-by-step trace:")
        for i, step in enumerate(result.steps):
            print(f"      {i+1:2d}. Line {step.line_number} in {Path(step.file_path).name}")
            print(f"          Type: {step.statement_type}")
            print(f"          Content: '{step.content}'")
            print(f"          Parsed data: {step.parsed_data}")
            print()
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        shutil.rmtree(project)

def main():
    """Run debug analysis."""
    print("🔧 Jump Following Debug Analysis")
    print("=" * 50)
    
    debug_label_cache()
    debug_file_parsing()
    debug_trace_steps()
    
    print("=" * 50)
    print("✅ Debug analysis complete!")

if __name__ == "__main__":
    main() 