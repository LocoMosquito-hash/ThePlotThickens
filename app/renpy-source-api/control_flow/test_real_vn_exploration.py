#!/usr/bin/env python3
"""
Real VN Exploration Test - Random Choice Selection

Tests random choice selection with actual VN projects to demonstrate
path exploration and narrative branch discovery capabilities.
"""

import sys
from pathlib import Path
import time

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from flow_tracer import FlowTracer, FlowTracerError

def test_real_vn_exploration():
    """Test random choice exploration with real VN projects."""
    
    # Real VN projects to test
    test_projects = [
        (r"C:\Users\juanc\Desktop\giga_renpy_collection\adult-vns\Savior", "Savior"),
        (r"C:\Users\juanc\Desktop\giga_renpy_collection\adult-vns\AlisonFalloftheApple", "Alison Fall"),
        (r"C:\Users\juanc\Desktop\giga_renpy_collection\adult-vns\MySisterMyRoommate", "MySister"),
        (r"C:\Users\juanc\Desktop\giga_renpy_collection\adult-vns\TheAlphaGender", "AlphaGender")
    ]
    
    print("🎮 Real VN Exploration Test Suite")
    print("Testing random choice selection with actual VN projects...")
    print("=" * 70)
    
    for project_path, project_name in test_projects:
        if not Path(project_path).exists():
            print(f"⚠️  Skipping {project_name} - not found")
            continue
            
        print(f"\n🎯 Testing: {project_name}")
        print("-" * 50)
        
        try:
            # Test both strategies
            explore_vn_paths(project_path, project_name)
            
        except Exception as e:
            print(f"❌ Error testing {project_name}: {e}")

def explore_vn_paths(project_path: str, project_name: str):
    """Explore different paths in a VN using both first and random strategies."""
    
    max_steps = 150  # Increased to see more exploration
    
    try:
        # Test First Choice Strategy
        print(f"📋 First Choice Strategy:")
        tracer_first = FlowTracer(project_path, choice_strategy="first")
        start_time = time.time()
        result_first = tracer_first.trace_flow(max_steps=max_steps)
        first_time = time.time() - start_time
        
        first_menus = analyze_menu_path(result_first, "FIRST")
        
        print(f"   ✅ Completed: {len(result_first.steps)} steps in {first_time:.2f}s")
        print(f"   🎯 Menus encountered: {len(first_menus)}")
        print(f"   🛑 Stop reason: {result_first.stop_reason}")
        
        # Show path taken
        if first_menus:
            choices_path = " → ".join([menu['choice'] for menu in first_menus[:5]])
            if len(first_menus) > 5:
                choices_path += f" → (+{len(first_menus)-5} more)"
            print(f"   🗂️  Path: {choices_path}")
        
        # Test Random Choice Strategy - Multiple Runs
        print(f"\n🎲 Random Choice Strategy (3 exploration runs):")
        
        random_paths = []
        for run in range(3):
            print(f"\n   Run {run+1}:")
            tracer_random = FlowTracer(project_path, choice_strategy="random", random_seed=run + 42)
            start_time = time.time()
            result_random = tracer_random.trace_flow(max_steps=max_steps)
            random_time = time.time() - start_time
            
            random_menus = analyze_menu_path(result_random, f"RANDOM-{run+1}")
            random_paths.append(random_menus)
            
            print(f"     ✅ Steps: {len(result_random.steps)}, Menus: {len(random_menus)}, Time: {random_time:.2f}s")
            print(f"     🛑 Stop: {result_random.stop_reason}")
            
            # Show path for this run
            if random_menus:
                choices_path = " → ".join([menu['choice'] for menu in random_menus[:4]])
                if len(random_menus) > 4:
                    choices_path += f" → (+{len(random_menus)-4} more)"
                print(f"     🗂️  Path: {choices_path}")
        
        # Analyze Path Diversity
        print(f"\n📊 Path Analysis:")
        
        # Compare first vs random paths
        first_choices = [menu['choice'] for menu in first_menus]
        
        unique_random_paths = 0
        for i, random_menus in enumerate(random_paths):
            random_choices = [menu['choice'] for menu in random_menus]
            if random_choices != first_choices:
                unique_random_paths += 1
                print(f"   🔄 Run {i+1}: DIFFERENT path from first strategy")
            else:
                print(f"   ↔️  Run {i+1}: SAME path as first strategy")
        
        # Check diversity between random runs
        random_choice_sets = []
        for random_menus in random_paths:
            random_choice_sets.append([menu['choice'] for menu in random_menus])
        
        unique_random_sets = len(set(str(choices) for choices in random_choice_sets))
        print(f"   🎲 Random path diversity: {unique_random_sets}/3 unique paths")
        
        if unique_random_paths > 0 or unique_random_sets > 1:
            print(f"   ✅ Random exploration is discovering new paths!")
        else:
            print(f"   ⚠️  All runs took similar paths (limited branching or early termination)")
            
    except Exception as e:
        print(f"❌ Exploration error: {e}")
        import traceback
        traceback.print_exc()

def analyze_menu_path(result, run_label: str):
    """Analyze menu choices from a flow trace result."""
    
    menus = []
    for i, step in enumerate(result.steps):
        if step.statement_type == 'menu' and step.parsed_data:
            data = step.parsed_data
            menu_info = {
                'step': i + 1,
                'choice': data['choice_selected'],
                'total_choices': data['total_choices'],
                'all_choices': data['all_choices'],
                'action': data['action'],
                'file': Path(step.file_path).name,
                'line': step.line_number
            }
            menus.append(menu_info)
    
    return menus

def detailed_exploration_demo(project_path: str, project_name: str):
    """Show detailed exploration of a specific VN."""
    
    print(f"\n🔍 Detailed Exploration Demo: {project_name}")
    print("=" * 60)
    
    try:
        # Random exploration with detailed output
        tracer = FlowTracer(project_path, choice_strategy="random", random_seed=999)
        result = tracer.trace_flow(max_steps=100)
        
        print(f"📋 Exploration Results:")
        print(f"   Total steps: {len(result.steps)}")
        print(f"   Stop reason: {result.stop_reason}")
        
        menu_count = 0
        print(f"\n🎯 Menu Choices Made:")
        
        for i, step in enumerate(result.steps):
            if step.statement_type == 'menu' and step.parsed_data:
                menu_count += 1
                data = step.parsed_data
                
                print(f"\n   Menu {menu_count} @ Step {i+1}:")
                print(f"     📍 Location: {Path(step.file_path).name}:{step.line_number}")
                print(f"     🎲 Strategy: {data['strategy']}")
                print(f"     ✅ Selected: '{data['choice_selected']}'")
                print(f"     📋 Available: {data['all_choices']}")
                print(f"     🎯 Total choices: {data['total_choices']}")
                print(f"     ➡️  Action: {data['action']}")
                
                # Show selection position
                try:
                    choice_idx = data['all_choices'].index(data['choice_selected']) + 1
                    print(f"     🔢 Selected choice #{choice_idx}/{data['total_choices']}")
                except ValueError:
                    print(f"     ⚠️  Choice index not found")
        
        if menu_count == 0:
            print(f"   ❌ No menus encountered in trace")
        else:
            print(f"\n📊 Summary: {menu_count} menus navigated with random selection")
            
    except Exception as e:
        print(f"❌ Demo error: {e}")

if __name__ == "__main__":
    # Run comprehensive exploration tests
    test_real_vn_exploration()
    
    # Run detailed demo on first available project
    test_projects = [
        (r"C:\Users\juanc\Desktop\giga_renpy_collection\adult-vns\Savior", "Savior"),
        (r"C:\Users\juanc\Desktop\giga_renpy_collection\adult-vns\AlisonFalloftheApple", "Alison Fall")
    ]
    
    for project_path, project_name in test_projects:
        if Path(project_path).exists():
            detailed_exploration_demo(project_path, project_name)
            break
    
    print("\n✅ Real VN exploration tests completed!") 