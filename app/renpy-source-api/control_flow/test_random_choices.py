#!/usr/bin/env python3
"""
Test script for random choice selection functionality in FlowTracer.

This script demonstrates the difference between "first" and "random" choice
selection strategies and shows how random selection discovers different paths.
"""

import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from flow_tracer import FlowTracer, FlowTracerError

def create_complex_test_vn():
    """Create a VN with multiple menus and branching paths for testing."""
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="test_random_vn_")
    
    # Create script.rpy file with multiple menus
    script_content = '''
# Complex branching VN for random choice testing
label start:
    "Welcome to the adventure!"
    "You find yourself at a crossroads."
    
    menu:
        "Take the forest path":
            jump forest_path
        "Follow the mountain trail":
            jump mountain_path
        "Head to the village":
            jump village_path

label forest_path:
    "You enter the dark forest."
    "Strange sounds echo around you."
    
    menu:
        "Investigate the sounds":
            jump forest_mystery
        "Keep walking quickly":
            jump forest_continue
        "Turn back":
            jump start

label mountain_path:
    "You climb the rocky mountain trail."
    "The view is breathtaking!"
    
    menu:
        "Rest and enjoy the view":
            "You rest peacefully."
            jump mountain_ending
        "Continue climbing":
            jump mountain_peak
        "Look for a cave":
            jump mountain_cave

label village_path:
    "You arrive at a peaceful village."
    "The villagers welcome you warmly."
    
    menu:
        "Visit the inn":
            jump village_inn
        "Explore the market":
            jump village_market
        "Talk to the elder":
            jump village_elder

label forest_mystery:
    "You discover a hidden fairy ring!"
    "This leads to a magical ending."
    return

label forest_continue:
    "You safely exit the forest."
    "A simple but safe journey."
    return

label mountain_peak:
    "You reach the summit!"
    "You find an ancient shrine."
    return

label mountain_cave:
    "Inside the cave, you find treasure!"
    "Lucky discovery!"
    return

label mountain_ending:
    "You enjoyed a peaceful mountain rest."
    return

label village_inn:
    "The innkeeper tells you local legends."
    return

label village_market:
    "You buy interesting local crafts."
    return

label village_elder:
    "The elder shares ancient wisdom."
    return
'''
    
    script_file = Path(temp_dir) / "script.rpy"
    script_file.write_text(script_content)
    
    return temp_dir

def test_choice_strategies():
    """Test both first and random choice selection strategies."""
    
    print("🧪 Testing Choice Selection Strategies")
    print("=" * 50)
    
    # Create test VN
    test_dir = create_complex_test_vn()
    
    try:
        # Test first choice strategy
        print("\n📋 Testing 'first' choice strategy:")
        print("-" * 40)
        
        tracer_first = FlowTracer(test_dir, choice_strategy="first")
        result_first = tracer_first.trace_flow(max_steps=50)
        
        print(f"✅ First strategy completed: {len(result_first.steps)} steps")
        print(f"   Stop reason: {result_first.stop_reason}")
        
        # Show the path taken
        first_path = []
        for step in result_first.steps:
            if step.statement_type == 'menu' and step.parsed_data:
                choice = step.parsed_data['choice_selected']
                total = step.parsed_data['total_choices']
                first_path.append(f"'{choice}' (1/{total})")
        
        print(f"   Path: {' → '.join(first_path)}")
        
        # Test random choice strategy multiple times
        print(f"\n🎲 Testing 'random' choice strategy (5 runs):")
        print("-" * 40)
        
        random_paths = []
        for run in range(5):
            tracer_random = FlowTracer(test_dir, choice_strategy="random", random_seed=run)
            result_random = tracer_random.trace_flow(max_steps=50)
            
            # Extract path taken
            random_path = []
            for step in result_random.steps:
                if step.statement_type == 'menu' and step.parsed_data:
                    choice = step.parsed_data['choice_selected']
                    all_choices = step.parsed_data['all_choices']
                    choice_idx = all_choices.index(choice) + 1
                    total = step.parsed_data['total_choices']
                    random_path.append(f"'{choice}' ({choice_idx}/{total})")
            
            path_str = ' → '.join(random_path)
            random_paths.append(path_str)
            print(f"   Run {run+1}: {path_str}")
        
        # Check for path diversity
        unique_paths = len(set(random_paths))
        print(f"\n📊 Path Diversity:")
        print(f"   Unique paths discovered: {unique_paths}/5")
        print(f"   First strategy path: {' → '.join(first_path)}")
        
        if unique_paths > 1:
            print(f"✅ Random selection successfully discovered different paths!")
        else:
            print(f"⚠️  All random runs took the same path (may happen with small menus)")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        shutil.rmtree(test_dir)

def test_choice_metadata():
    """Test that choice metadata is properly captured."""
    
    print(f"\n🔍 Testing Choice Metadata")
    print("=" * 40)
    
    # Create test VN
    test_dir = create_complex_test_vn()
    
    try:
        tracer = FlowTracer(test_dir, choice_strategy="random", random_seed=42)
        result = tracer.trace_flow(max_steps=30)
        
        menu_count = 0
        for i, step in enumerate(result.steps):
            if step.statement_type == 'menu' and step.parsed_data:
                menu_count += 1
                data = step.parsed_data
                
                print(f"\n🎯 Menu {menu_count} at step {i+1}:")
                print(f"   Strategy: {data['strategy']}")
                print(f"   Selected: '{data['choice_selected']}'")
                print(f"   Action: {data['action']}")
                print(f"   Total choices: {data['total_choices']}")
                print(f"   All choices: {data['all_choices']}")
        
        print(f"\n📊 Summary: Found {menu_count} menus with complete metadata")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        shutil.rmtree(test_dir)

def compare_strategies_side_by_side():
    """Compare first vs random strategies side by side."""
    
    print(f"\n🔄 Side-by-Side Strategy Comparison")
    print("=" * 50)
    
    # Create test VN
    test_dir = create_complex_test_vn()
    
    try:
        # Run both strategies
        tracer_first = FlowTracer(test_dir, choice_strategy="first")
        tracer_random = FlowTracer(test_dir, choice_strategy="random", random_seed=123)
        
        result_first = tracer_first.trace_flow(max_steps=50)
        result_random = tracer_random.trace_flow(max_steps=50)
        
        print(f"{'Strategy':<10} {'Steps':<6} {'Menus':<6} {'Path'}")
        print("-" * 60)
        
        # Analyze first strategy
        first_menus = [s for s in result_first.steps if s.statement_type == 'menu']
        first_choices = [s.parsed_data['choice_selected'] for s in first_menus if s.parsed_data]
        
        print(f"{'First':<10} {len(result_first.steps):<6} {len(first_menus):<6} {' → '.join(first_choices[:3])}")
        
        # Analyze random strategy  
        random_menus = [s for s in result_random.steps if s.statement_type == 'menu']
        random_choices = [s.parsed_data['choice_selected'] for s in random_menus if s.parsed_data]
        
        print(f"{'Random':<10} {len(result_random.steps):<6} {len(random_menus):<6} {' → '.join(random_choices[:3])}")
        
        # Check if paths differ
        if first_choices != random_choices:
            print(f"\n✅ Strategies produced different paths!")
        else:
            print(f"\n⚠️  Both strategies took the same path")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        shutil.rmtree(test_dir)

if __name__ == "__main__":
    print("🎲 Random Choice Selection Test Suite")
    print("Testing random choice exploration capabilities...")
    
    # Run all tests
    test_choice_strategies()
    test_choice_metadata()
    compare_strategies_side_by_side()
    
    print("\n✅ Random choice selection tests completed!") 