#!/usr/bin/env python3
"""
Simple test script for jump following functionality.
Tests the new Simple Jump Following feature in FlowTracer.
"""

import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path to import flow_tracer
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))

from flow_tracer import FlowTracer

def create_test_project(files_dict):
    """Create a temporary test project with given files."""
    test_dir = tempfile.mkdtemp()
    project_root = Path(test_dir)
    game_dir = project_root / 'game'
    game_dir.mkdir(exist_ok=True)
    
    for filename, content in files_dict.items():
        file_path = game_dir / filename
        file_path.write_text(content)
    
    return str(project_root)

def test_simple_jump_following():
    """Test basic jump following functionality."""
    print("🧪 Testing Simple Jump Following...")
    
    project = create_test_project({
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
    
    try:
        tracer = FlowTracer(project)
        result = tracer.trace_from_start()
        
        print(f"   ✅ Stop reason: {result.stop_reason}")
        print(f"   ✅ Flow control encountered: {result.flow_control_encountered}")
        print(f"   ✅ Total steps traced: {len(result.steps)}")
        
        # Print the sequence of steps
        print("\n   📝 Traced sequence:")
        for i, step in enumerate(result.steps, 1):
            print(f"      {i:2d}. [{step.statement_type:15}] {step.content}")
        
        # Verify we followed jumps correctly
        labels_visited = [step.content for step in result.steps if step.statement_type == 'label']
        print(f"\n   🏷️  Labels visited: {len(labels_visited)}")
        for label in labels_visited:
            print(f"      - {label}")
        
        # Check that we reached the return statement
        if result.stop_reason == "flow_control_return":
            print("   ✅ SUCCESS: Correctly followed jumps and reached return statement")
        else:
            print(f"   ❌ FAILED: Expected to stop at return, but stopped at: {result.stop_reason}")
            
        return result.stop_reason == "flow_control_return"
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        shutil.rmtree(project)

def test_infinite_loop_prevention():
    """Test prevention of infinite jump loops."""
    print("\n🧪 Testing Infinite Loop Prevention...")
    
    project = create_test_project({
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
    
    try:
        tracer = FlowTracer(project)
        result = tracer.trace_from_start()
        
        print(f"   ✅ Stop reason: {result.stop_reason}")
        print(f"   ✅ Total steps: {len(result.steps)}")
        
        if result.stop_reason == "infinite_jump_loop":
            print("   ✅ SUCCESS: Correctly detected infinite jump loop")
            return True
        else:
            print(f"   ❌ FAILED: Expected infinite_jump_loop, got: {result.stop_reason}")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False
    finally:
        shutil.rmtree(project)

def test_cross_file_jumping():
    """Test jumping between different files."""
    print("\n🧪 Testing Cross-File Jumping...")
    
    project = create_test_project({
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
    
    try:
        tracer = FlowTracer(project)
        result = tracer.trace_from_start()
        
        print(f"   ✅ Stop reason: {result.stop_reason}")
        print(f"   ✅ Total steps: {len(result.steps)}")
        
        # Check files visited
        files_visited = set(step.file_path for step in result.steps)
        print(f"   📁 Files visited: {len(files_visited)}")
        for file_path in files_visited:
            filename = Path(file_path).name
            print(f"      - {filename}")
        
        if result.stop_reason == "flow_control_return" and len(files_visited) >= 3:
            print("   ✅ SUCCESS: Correctly followed jumps across multiple files")
            return True
        else:
            print(f"   ❌ FAILED: Expected to visit 3 files and reach return")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False
    finally:
        shutil.rmtree(project)

def test_jump_target_not_found():
    """Test handling of jump to non-existent label."""
    print("\n🧪 Testing Jump Target Not Found...")
    
    project = create_test_project({
        "script.rpy": '''
label start:
    "Beginning"
    jump nonexistent_label
    "This should not be reached"
'''
    })
    
    try:
        tracer = FlowTracer(project)
        result = tracer.trace_from_start()
        
        print(f"   ✅ Stop reason: {result.stop_reason}")
        print(f"   ✅ Total steps: {len(result.steps)}")
        
        if result.stop_reason == "jump_target_not_found":
            print("   ✅ SUCCESS: Correctly handled missing jump target")
            return True
        else:
            print(f"   ❌ FAILED: Expected jump_target_not_found, got: {result.stop_reason}")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False
    finally:
        shutil.rmtree(project)

def main():
    """Run all jump following tests."""
    print("🚀 Simple Jump Following Feature Tests")
    print("=" * 50)
    
    tests = [
        test_simple_jump_following,
        test_infinite_loop_prevention,
        test_cross_file_jumping,
        test_jump_target_not_found
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        if test_func():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Simple Jump Following is working correctly!")
        return True
    else:
        print(f"❌ {total - passed} test(s) failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 