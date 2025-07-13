#!/usr/bin/env python3
"""
Test script for menu following functionality in FlowTracer.

This script tests the new menu following capability that follows the first
available choice in a menu instead of stopping.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from flow_tracer import FlowTracer, FlowTracerError

def test_menu_following():
    """Test menu following functionality with real VN projects."""
    
    # Test projects that we know have menus
    test_projects = [
        r"C:\Users\juanc\Desktop\giga_renpy_collection\adult-vns\Savior",
        r"C:\Users\juanc\Desktop\giga_renpy_collection\adult-vns\AlisonFalloftheApple",
        r"C:\Users\juanc\Desktop\giga_renpy_collection\adult-vns\MySisterMyRoommate"
    ]
    
    for project_path in test_projects:
        if not Path(project_path).exists():
            print(f"⚠️  Skipping {Path(project_path).name} - not found")
            continue
            
        print(f"\n🧪 Testing Menu Following: {Path(project_path).name}")
        print("=" * 60)
        
        try:
            # Create FlowTracer instance
            tracer = FlowTracer(project_path)
            print(f"✅ FlowTracer initialized successfully")
            print(f"📍 Start location: {tracer.start_location}")
            
            # Trace flow with menu following enabled
            result = tracer.trace_flow(max_steps=200)  # Increased steps to see menu following
            
            print(f"\n📊 Flow Trace Results:")
            print(f"   Steps traced: {len(result.steps)}")
            print(f"   Stop reason: {result.stop_reason}")
            print(f"   Stop location: {result.stop_location}")
            
            # Look for menu steps and choice selections
            menu_steps = []
            for i, step in enumerate(result.steps):
                if step.statement_type == 'menu':
                    menu_steps.append((i, step))
            
            if menu_steps:
                print(f"\n🎯 Menu Steps Found: {len(menu_steps)}")
                for i, (step_idx, step) in enumerate(menu_steps):
                    print(f"   Menu {i+1} at step {step_idx}:")
                    print(f"     File: {Path(step.file_path).name}:{step.line_number}")
                    print(f"     Content: {step.content[:50]}...")
                    
                    if step.parsed_data and 'choice_selected' in step.parsed_data:
                        choice = step.parsed_data['choice_selected']
                        action = step.parsed_data['action']
                        print(f"     🔄 Selected choice: '{choice}'")
                        print(f"     ➡️  Action: {action}")
                    else:
                        print(f"     ❌ No choice data found")
                        
                    # Show next few steps to see if we continued tracing
                    print(f"     Next steps:")
                    for j in range(step_idx + 1, min(step_idx + 4, len(result.steps))):
                        next_step = result.steps[j]
                        print(f"       {j}: {next_step.statement_type} - {next_step.content[:40]}...")
                    print()
            else:
                print(f"   ❌ No menu steps found in trace")
            
            # Analyze stop reason
            if "menu" in result.stop_reason:
                print(f"🎯 Menu-related stop: {result.stop_reason}")
                if result.stop_reason == "menu_jump_target_not_found":
                    print("   ❌ Menu choice target label not found")
                elif result.stop_reason == "menu_no_choices":
                    print("   ❌ Menu found but no choices detected")
            elif result.stop_reason == "max_steps_reached":
                print("🔄 Reached maximum steps - menu following might be working!")
            
        except Exception as e:
            print(f"❌ Error testing {Path(project_path).name}: {e}")
            import traceback
            traceback.print_exc()

def demo_menu_following_detailed(project_path: str, max_steps: int = 100):
    """Detailed demo showing menu following step by step."""
    
    print(f"\n🔍 Detailed Menu Following Demo")
    print(f"Project: {Path(project_path).name}")
    print("=" * 60)
    
    try:
        tracer = FlowTracer(project_path)
        result = tracer.trace_flow(max_steps=max_steps)
        
        print(f"Tracing {len(result.steps)} steps...")
        
        for i, step in enumerate(result.steps):
            print(f"Step {i+1:3d}: {step.statement_type:15s} | {Path(step.file_path).name:20s}:{step.line_number:4d} | {step.content[:50]}")
            
            # Highlight menu steps
            if step.statement_type == 'menu':
                print(f"         🎯 MENU DETECTED!")
                if step.parsed_data and 'choice_selected' in step.parsed_data:
                    choice = step.parsed_data['choice_selected']
                    action = step.parsed_data['action']
                    print(f"         🔄 Following choice: '{choice}' → {action}")
                else:
                    print(f"         ❌ No choice data!")
            
            # Stop at first 10 steps for readability
            if i >= 10:
                print(f"         ... (showing first 10 steps)")
                break
        
        print(f"\nFinal result: {result.stop_reason}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Menu Following Test Suite")
    print("Testing the new menu following functionality...")
    
    # Run basic tests
    test_menu_following()
    
    # Run detailed demo on first available project
    test_projects = [
        r"C:\Users\juanc\Desktop\giga_renpy_collection\adult-vns\Savior",
        r"C:\Users\juanc\Desktop\giga_renpy_collection\adult-vns\AlisonFalloftheApple"
    ]
    
    for project_path in test_projects:
        if Path(project_path).exists():
            demo_menu_following_detailed(project_path, max_steps=50)
            break
    
    print("\n✅ Menu following tests completed!") 