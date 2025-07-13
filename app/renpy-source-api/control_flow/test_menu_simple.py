#!/usr/bin/env python3
"""
Simple test for menu following functionality using the existing demo project.

Tests that menu following works with simulated menu structures.
"""

import sys
import tempfile
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from flow_tracer import FlowTracer, FlowTracerError

def create_test_vn_with_menu():
    """Create a temporary VN project with a menu for testing."""
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="test_menu_vn_")
    
    # Create script.rpy file with menu
    script_content = '''
# Test VN with menu
label start:
    "Welcome to the test!"
    "This is a story with choices."
    
    menu:
        "Go left":
            jump left_path
        "Go right":  
            jump right_path
        "Stay here":
            "You stayed put."
            return

label left_path:
    "You went left and found a treasure!"
    "This is the left path story."
    return

label right_path:
    "You went right and met a friend!"
    "This is the right path story."
    jump secret_ending

label secret_ending:
    "You discovered a secret ending!"
    return
'''
    
    script_file = Path(temp_dir) / "script.rpy"
    script_file.write_text(script_content)
    
    return temp_dir

def test_menu_parsing():
    """Test the menu parsing functionality directly."""
    
    print("🧪 Testing Menu Parsing Logic")
    print("=" * 40)
    
    # Create test VN
    test_dir = create_test_vn_with_menu()
    
    try:
        # Create FlowTracer
        tracer = FlowTracer(test_dir)
        print(f"✅ FlowTracer created for test VN")
        print(f"📍 Start location: {tracer.start_location}")
        
        # Test the menu parsing method directly
        file_lines = tracer._get_file_lines(tracer.start_location[0])
        
        # Find the menu line
        menu_line_idx = None
        for i, line in enumerate(file_lines):
            if 'menu:' in line.content:
                menu_line_idx = i
                break
        
        if menu_line_idx is not None:
            print(f"🎯 Found menu at line {menu_line_idx + 1}")
            
            # Test menu choice parsing
            first_choice = tracer._parse_menu_choices(file_lines, menu_line_idx)
            
            if first_choice:
                choice_text, action = first_choice
                print(f"✅ First choice parsed: '{choice_text}' → {action}")
            else:
                print(f"❌ Failed to parse menu choices")
        else:
            print(f"❌ No menu found in test file")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(test_dir)

def test_full_menu_following():
    """Test full menu following functionality."""
    
    print("\n🧪 Testing Full Menu Following")
    print("=" * 40)
    
    # Create test VN
    test_dir = create_test_vn_with_menu()
    
    try:
        # Create FlowTracer
        tracer = FlowTracer(test_dir)
        
        # Trace flow with menu following
        result = tracer.trace_flow(max_steps=50)
        
        print(f"📊 Flow Results:")
        print(f"   Steps: {len(result.steps)}")
        print(f"   Stop reason: {result.stop_reason}")
        
        # Look for menu steps
        menu_found = False
        print(f"\n📋 Step-by-step trace:")
        
        for i, step in enumerate(result.steps):
            print(f"  {i+1:2d}. {step.statement_type:15s} | Line {step.line_number:3d} | {step.content[:40]}")
            
            if step.statement_type == 'menu':
                menu_found = True
                print(f"      🎯 MENU DETECTED!")
                
                if step.parsed_data and 'choice_selected' in step.parsed_data:
                    choice = step.parsed_data['choice_selected']
                    action = step.parsed_data['action']
                    print(f"      🔄 Selected: '{choice}' → {action}")
                else:
                    print(f"      ❌ No choice data!")
        
        if menu_found:
            print(f"\n✅ Menu following successful!")
        else:
            print(f"\n❌ No menus found in trace")
            
        if "menu" in result.stop_reason:
            print(f"🎯 Stopped due to menu: {result.stop_reason}")
        elif result.stop_reason == "max_steps_reached":
            print(f"🔄 Reached max steps - potentially continuing through menus")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(test_dir)

if __name__ == "__main__":
    print("🧪 Simple Menu Following Test")
    print("Creating temporary VN with menu...")
    
    # Run tests
    test_menu_parsing()
    test_full_menu_following()
    
    print("\n✅ Tests completed!") 