#!/usr/bin/env python3
"""
Advanced Exploration Test - Realistic VN Simulation

Creates a complex VN structure that mimics real visual novel branching
patterns to demonstrate random choice exploration capabilities.
"""

import sys
import tempfile
import shutil
from pathlib import Path
import time

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from flow_tracer import FlowTracer, FlowTracerError

def create_realistic_vn():
    """Create a VN with realistic complexity similar to actual VNs."""
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="realistic_vn_")
    
    # Create script.rpy with complex branching like real VNs
    script_content = '''
# Realistic VN Demo - Complex Branching Structure
label start:
    "Welcome to the academy!"
    "You are a new student at Mystic Academy."
    "As you walk through the gates, you see several people you could approach."
    
    menu:
        "Approach the girl reading under the tree":
            jump meet_scholar
        "Talk to the group playing basketball":
            jump meet_athletes  
        "Head straight to the dormitory":
            jump explore_dorm
        "Visit the library first":
            jump library_intro

label meet_scholar:
    "You approach Luna, who's reading an ancient tome."
    "Luna" "Oh, hello! Are you interested in magical theory?"
    
    menu:
        "Yes, magic fascinates me!":
            $ luna_points = 2
            jump luna_magic_route
        "Not really, just being friendly":
            $ luna_points = 1
            jump luna_friendship_route
        "Actually, I should go explore more":
            jump academy_courtyard

label meet_athletes:
    "You walk over to the basketball court."
    "Jake" "Hey new kid! Want to shoot some hoops?"
    
    menu:
        "Sure, I love basketball!":
            $ jake_points = 2
            jump jake_sports_route
        "I'll watch for now":
            $ jake_points = 1
            jump jake_casual_route
        "Maybe later, I should meet others first":
            jump academy_courtyard

label explore_dorm:
    "You head to the dormitory building."
    "Your roommate Maya is unpacking."
    "Maya" "You must be my new roommate! Want to explore together?"
    
    menu:
        "Absolutely! Let's be friends":
            $ maya_points = 2
            jump maya_best_friend_route
        "Sure, but I like my independence":
            $ maya_points = 1
            jump maya_casual_route
        "I prefer exploring alone":
            jump solo_exploration

label library_intro:
    "The library is massive and filled with mysterious books."
    "Librarian" "Welcome, student. Are you here for research or leisure?"
    
    menu:
        "Research on academy history":
            jump library_research_route
        "Just browsing for fun":
            jump library_casual_route
        "Looking for magical texts":
            jump library_magic_route

# Luna Routes
label luna_magic_route:
    "Luna's eyes light up with excitement."
    "Luna" "Finally, someone who appreciates the arcane arts!"
    "She shows you a spell that makes flowers bloom instantly."
    
    menu:
        "Can you teach me that spell?":
            jump luna_apprentice_route
        "That's amazing! What else can you do?":
            jump luna_demonstration_route
        "We should find other magic users":
            jump magic_club_route

label luna_friendship_route:
    "Luna smiles warmly."
    "Luna" "That's okay! Friendship is more important than shared interests."
    
    menu:
        "Want to study together sometime?":
            jump luna_study_buddy_route
        "Should we grab lunch?":
            jump luna_lunch_route
        "Let me introduce you to others":
            jump social_group_route

# Jake Routes  
label jake_sports_route:
    "You play basketball with Jake and his friends."
    "Jake" "You've got skills! Want to join our team?"
    
    menu:
        "Yes! I love team sports":
            jump basketball_team_route
        "I prefer individual training":
            jump solo_training_route
        "Let me think about it":
            jump undecided_sports_route

label jake_casual_route:
    "You watch the game and chat with Jake."
    "Jake" "No pressure! Sports aren't for everyone."
    
    menu:
        "Actually, maybe I'll try next time":
            jump delayed_sports_interest
        "I prefer other activities":
            jump non_sports_activities
        "Want to hang out after?":
            jump jake_friendship_route

# Convergence points and complex branching
label academy_courtyard:
    "You find yourself in the main courtyard."
    "Several groups are hanging out here."
    
    menu:
        "Join the art students sketching":
            jump art_club_route
        "Sit with the music group":
            jump music_club_route
        "Approach the debate team":
            jump debate_club_route
        "Find a quiet spot to think":
            jump contemplation_route

label magic_club_route:
    "Luna takes you to the secret magic club meeting."
    "You discover there are other students with magical abilities."
    
    menu:
        "I want to join the magic club":
            jump magic_club_member_route
        "This is too intense for me":
            jump magic_club_observer_route
        "Can we invite my other friends?":
            jump magic_club_expansion_route

# Ending branches
label luna_apprentice_route:
    "Luna becomes your magic mentor."
    "You spend your academy days learning powerful spells."
    "This leads to the Scholar's Path ending."
    return

label basketball_team_route:
    "You become the star player of the basketball team."
    "Your athletic achievements make you famous at the academy."
    "This leads to the Champion's Path ending."
    return

label maya_best_friend_route:
    "Maya becomes your closest friend and confidant."
    "Together you navigate all the academy's challenges."
    "This leads to the Friendship's Path ending."
    return

label magic_club_member_route:
    "You become a core member of the secret magic club."
    "Your magical abilities grow stronger each day."
    "This leads to the Mystic's Path ending."
    return

label art_club_route:
    "You discover your hidden artistic talents."
    "Your artwork becomes renowned throughout the academy."
    "This leads to the Artist's Path ending."
    return

# More ending routes for variety
label library_research_route:
    "Your research uncovers ancient academy secrets."
    "This leads to the Historian's Path ending."
    return

label solo_exploration:
    "You become the academy's mysterious lone wolf."
    "This leads to the Independent Path ending."
    return

label contemplation_route:
    "Your thoughtful nature leads to philosophical insights."
    "This leads to the Philosopher's Path ending."
    return

# Fallback routes
label luna_study_buddy_route:
    "You and Luna become excellent study partners."
    return

label jake_friendship_route:
    "You and Jake develop a strong friendship."
    return

label maya_casual_route:
    "You and Maya have a good roommate relationship."
    return

label library_casual_route:
    "You enjoy spending leisure time in the library."
    return

label music_club_route:
    "You join the academy's music club."
    return

label debate_club_route:
    "You become part of the debate team."
    return

label social_group_route:
    "You help form a large social group."
    return

label non_sports_activities:
    "You focus on academic and creative pursuits."
    return
'''
    
    script_file = Path(temp_dir) / "script.rpy"
    script_file.write_text(script_content)
    
    return temp_dir

def run_exploration_comparison():
    """Run comprehensive exploration comparison."""
    
    print("🎮 Advanced VN Exploration Demo")
    print("Testing with realistic VN branching patterns...")
    print("=" * 60)
    
    # Create realistic VN
    test_dir = create_realistic_vn()
    
    try:
        print("📋 VN Structure Analysis:")
        tracer = FlowTracer(test_dir, choice_strategy="first")
        
        # Quick analysis of the VN structure
        print(f"   ✅ VN created successfully")
        print(f"   📁 Location: {test_dir}")
        print(f"   🎯 Start location: {tracer.start_location}")
        
        # Test exploration strategies
        compare_exploration_strategies(test_dir)
        
        # Detailed exploration analysis
        analyze_exploration_depth(test_dir)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        shutil.rmtree(test_dir)

def compare_exploration_strategies(test_dir: str):
    """Compare first vs random exploration strategies."""
    
    print(f"\n📊 Strategy Comparison")
    print("-" * 40)
    
    max_steps = 200
    
    # First Choice Strategy
    print(f"🥇 First Choice Strategy:")
    tracer_first = FlowTracer(test_dir, choice_strategy="first")
    start_time = time.time()
    result_first = tracer_first.trace_flow(max_steps=max_steps)
    first_time = time.time() - start_time
    
    first_menus = extract_menu_choices(result_first)
    print(f"   ⏱️  Time: {first_time:.3f}s")
    print(f"   📝 Steps: {len(result_first.steps)}")
    print(f"   🎯 Menus: {len(first_menus)}")
    print(f"   🛑 Stop: {result_first.stop_reason}")
    
    if first_menus:
        path = " → ".join([f"'{choice}'" for choice in first_menus[:6]])
        if len(first_menus) > 6:
            path += f" → (+{len(first_menus)-6} more)"
        print(f"   🗂️  Path: {path}")
    
    # Random Choice Strategy - Multiple runs
    print(f"\n🎲 Random Choice Strategy (5 exploration runs):")
    
    random_results = []
    for run in range(5):
        tracer_random = FlowTracer(test_dir, choice_strategy="random", random_seed=run * 17)
        start_time = time.time()
        result_random = tracer_random.trace_flow(max_steps=max_steps)
        random_time = time.time() - start_time
        
        random_menus = extract_menu_choices(result_random)
        random_results.append((result_random, random_menus, random_time))
        
        print(f"   Run {run+1}: {len(result_random.steps)} steps, {len(random_menus)} menus, {random_time:.3f}s")
        if random_menus:
            path = " → ".join([f"'{choice}'" for choice in random_menus[:4]])
            if len(random_menus) > 4:
                path += f" → (+{len(random_menus)-4} more)"
            print(f"          Path: {path}")
    
    # Analyze diversity
    print(f"\n🔍 Path Diversity Analysis:")
    
    first_path_str = "→".join(first_menus)
    unique_paths = set()
    
    different_from_first = 0
    for i, (result, menus, _) in enumerate(random_results):
        random_path_str = "→".join(menus)
        unique_paths.add(random_path_str)
        
        if random_path_str != first_path_str:
            different_from_first += 1
            print(f"   🔄 Run {i+1}: DIFFERENT from first strategy")
        else:
            print(f"   ↔️  Run {i+1}: SAME as first strategy")
    
    print(f"\n📈 Exploration Statistics:")
    print(f"   🎯 Total unique paths discovered: {len(unique_paths)}")
    print(f"   🔄 Runs different from first: {different_from_first}/5")
    print(f"   📊 Path diversity: {len(unique_paths)}/6 possible patterns")
    
    if len(unique_paths) > 1:
        print(f"   ✅ Random exploration successfully discovers multiple narrative branches!")
    else:
        print(f"   ⚠️  Limited path diversity (early convergence or few choices)")

def extract_menu_choices(result):
    """Extract menu choice sequence from flow result."""
    choices = []
    for step in result.steps:
        if step.statement_type == 'menu' and step.parsed_data:
            choices.append(step.parsed_data['choice_selected'])
    return choices

def analyze_exploration_depth(test_dir: str):
    """Analyze the depth and quality of exploration."""
    
    print(f"\n🔬 Detailed Exploration Analysis")
    print("-" * 40)
    
    # Deep exploration run
    tracer = FlowTracer(test_dir, choice_strategy="random", random_seed=42)
    result = tracer.trace_flow(max_steps=300)
    
    print(f"📊 Exploration Results:")
    print(f"   📝 Total steps traced: {len(result.steps)}")
    print(f"   🛑 Final stop reason: {result.stop_reason}")
    
    # Analyze menu encounters
    menu_analysis = []
    for i, step in enumerate(result.steps):
        if step.statement_type == 'menu' and step.parsed_data:
            data = step.parsed_data
            menu_analysis.append({
                'step_num': i + 1,
                'choice': data['choice_selected'],
                'total_options': data['total_choices'],
                'all_options': data['all_choices'],
                'location': f"{Path(step.file_path).name}:{step.line_number}"
            })
    
    if menu_analysis:
        print(f"\n🎯 Menu Navigation Details:")
        print(f"   🔢 Total menus encountered: {len(menu_analysis)}")
        
        total_choices = sum(menu['total_options'] for menu in menu_analysis)
        avg_choices = total_choices / len(menu_analysis) if menu_analysis else 0
        print(f"   📊 Average choices per menu: {avg_choices:.1f}")
        
        print(f"\n🗂️  Menu-by-Menu Breakdown:")
        for i, menu in enumerate(menu_analysis[:8]):  # Show first 8 menus
            choice_idx = menu['all_options'].index(menu['choice']) + 1 if menu['choice'] in menu['all_options'] else 0
            print(f"   {i+1:2d}. Step {menu['step_num']:3d}: '{menu['choice']}' (#{choice_idx}/{menu['total_options']})")
            print(f"       Available: {menu['all_options']}")
        
        if len(menu_analysis) > 8:
            print(f"       ... and {len(menu_analysis) - 8} more menus")
    else:
        print(f"   ❌ No menus found in exploration")

if __name__ == "__main__":
    print("🚀 Advanced VN Exploration Test Suite")
    print("Demonstrating random choice selection with realistic VN patterns...\n")
    
    run_exploration_comparison()
    
    print("\n✅ Advanced exploration tests completed!") 