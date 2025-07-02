#!/usr/bin/env python3
"""
Test script for menu/choice extraction and decision tree analysis.
"""

import os
import sys
import json
from pathlib import Path

# Add current directory to Python path for imports
current_dir = str(Path(__file__).parent)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    # Try relative imports (when used as package)
    from .core import RenpyProject
    from .config import TEST_VN_PATH, ALTERNATIVE_PATHS
except ImportError:
    # Fall back to direct imports (when run standalone)
    from core import RenpyProject
    from config import TEST_VN_PATH, ALTERNATIVE_PATHS

def get_test_vn_path() -> str:
    """Get the best available test VN path."""
    if os.path.exists(TEST_VN_PATH):
        return TEST_VN_PATH
    
    for name, path in ALTERNATIVE_PATHS.items():
        if os.path.exists(path):
            print(f"Using fallback VN: {name} at {path}")
            return path
    
    return TEST_VN_PATH

def test_menu_extraction():
    """Test the menu and choice extraction features."""
    print("=" * 70)
    print("MENU/CHOICE EXTRACTION TEST")
    print("=" * 70)
    
    # Get test VN path
    test_vn_path = get_test_vn_path()
    
    if not os.path.exists(test_vn_path):
        print(f"❌ Test VN path doesn't exist: {test_vn_path}")
        print("Please update TEST_VN_PATH in config.py")
        return False
    
    print(f"📁 Testing VN: {test_vn_path}")
    
    try:
        # Initialize project
        project = RenpyProject(test_vn_path)
        project.analyze()
        
        # Test 1: Get All Menus
        print("\n📋 Test 1: Menu Discovery")
        print("-" * 40)
        
        menus = project.get_all_menus()
        print(f"✅ Menu discovery completed")
        print(f"   📊 Total menus found: {len(menus)}")
        
        if menus:
            print(f"\n📝 Sample menus:")
            for i, menu in enumerate(menus[:5]):
                name_info = f" ({menu.name})" if menu.name else ""
                context_info = f" in {menu.label_context}" if menu.label_context else ""
                print(f"   {i+1}. Menu{name_info} - {menu.total_choices} choices{context_info}")
                print(f"      📍 {menu.file_path}:{menu.line_number}")
                
                # Show sample choices
                for j, choice in enumerate(menu.choices[:3]):
                    cond_info = f" (if {choice.condition})" if choice.condition else ""
                    dest_info = f" → {choice.destination}" if choice.destination else ""
                    print(f"        • \"{choice.text}\"{cond_info}{dest_info}")
                
                if len(menu.choices) > 3:
                    print(f"        • ... and {len(menu.choices) - 3} more choices")
                print()
        
        # Test 2: Menu Analysis
        print("\n📈 Test 2: Menu Analysis")
        print("-" * 40)
        
        analysis = project.get_menu_analysis()
        print(f"✅ Menu analysis completed")
        print(f"   📊 Total menus: {analysis['total_menus']}")
        print(f"   🎯 Total choices: {analysis['total_choices']}")
        print(f"   ❓ Conditional choices: {analysis['conditional_choices']}")
        print(f"   🌿 Branching points: {len(analysis['branching_points'])}")
        
        print(f"\n🎭 Choice Actions:")
        for action, count in analysis['choices_by_action'].items():
            if count > 0:
                print(f"   • {action}: {count}")
        
        print(f"\n🎯 Popular Choice Words:")
        for word, count in list(analysis['choice_popularity'].items())[:10]:
            print(f"   • '{word}': {count} times")
        
        if analysis['branching_points']:
            print(f"\n🌿 Branching Points:")
            for point in analysis['branching_points'][:5]:
                print(f"   • {point['label']} - {point['choices']} choices")
                print(f"     📍 {point['file']}:{point['line']}")
                print(f"     🎯 Destinations: {', '.join(point['destinations'][:3])}")
                print()
        
        # Test 3: Choice Search
        print("\n🔍 Test 3: Choice Search")
        print("-" * 40)
        
        # Search for common choice terms
        search_terms = ["yes", "no", "go", "stay", "help", "leave", "accept", "refuse"]
        
        for term in search_terms:
            results = project.search_choices(term)
            if results:
                print(f"   🔍 Search '{term}': {len(results)} matches")
                for result in results[:3]:  # Show top 3 matches
                    dest_info = f" → {result['destination']}" if result['destination'] else ""
                    cond_info = f" (if {result['condition']})" if result['condition'] else ""
                    print(f"     • \"{result['text']}\"{cond_info}{dest_info}")
                    print(f"       📍 {result['menu_context']['label'] or 'unknown'}")
                print()
                break
        
        # Test 4: Choice Destinations
        print("\n🎯 Test 4: Choice Destinations")
        print("-" * 40)
        
        destinations = project.get_choice_destinations()
        print(f"✅ Choice destinations analyzed")
        print(f"   🎯 Unique destinations: {len(destinations)}")
        
        if destinations:
            # Show most popular destinations
            popular_destinations = sorted(destinations.items(), key=lambda x: len(x[1]), reverse=True)
            
            print(f"\n📊 Most Popular Destinations:")
            for dest, sources in popular_destinations[:8]:
                print(f"   • {dest}: {len(sources)} choices lead here")
                for source in sources[:2]:  # Show first 2 sources
                    print(f"     ← {source}")
                if len(sources) > 2:
                    print(f"     ← ... and {len(sources) - 2} more")
                print()
        
        # Test 5: Branching Complexity
        print("\n🧮 Test 5: Branching Complexity")
        print("-" * 40)
        
        complexity = project.get_branching_complexity()
        print(f"✅ Complexity analysis completed")
        print(f"   🎯 Decision points: {complexity['total_decision_points']}")
        print(f"   📊 Avg choices per menu: {complexity['average_choices_per_menu']}")
        print(f"   📈 Max choices in menu: {complexity['max_choices_in_menu']}")
        print(f"   ❓ Conditional choice ratio: {complexity['conditional_choice_ratio']}")
        print(f"   🌿 Branching factor: {complexity['branching_factor']}")
        print(f"   📝 Linear sequences: {complexity['linear_sequences']}")
        print(f"   🎯 Complexity score: {complexity['complexity_score']}/100")
        
        # Test 6: Decision Tree (Sample)
        print("\n🌳 Test 6: Decision Tree Analysis")
        print("-" * 40)
        
        decision_tree = project.get_decision_tree()
        print(f"✅ Decision tree analysis completed")
        print(f"   🌱 Root type: {decision_tree['type']}")
        print(f"   🎯 Root label: {decision_tree['label']}")
        
        if decision_tree['type'] == 'decision_point':
            print(f"   🌿 Choices from root: {len(decision_tree['choices'])}")
            
            for i, choice in enumerate(decision_tree['choices'][:3]):
                dest_info = f" → {choice['destination']}" if choice['destination'] else ""
                print(f"     {i+1}. \"{choice['text'][:40]}...\"{dest_info}")
        
        elif decision_tree['type'] == 'project':
            print(f"   📊 Total decision points: {decision_tree['total_decision_points']}")
            print(f"   📋 All menus: {decision_tree['all_menus']}")
            print(f"   🏷️  Available labels: {len(decision_tree['available_labels'])}")
        
        # Test 7: Menu Statistics Summary
        print("\n📊 Test 7: Menu Statistics Summary")
        print("-" * 40)
        
        if analysis['menu_statistics']:
            total_choices = sum(menu['choice_count'] for menu in analysis['menu_statistics'])
            menus_with_conditions = sum(1 for menu in analysis['menu_statistics'] 
                                      if any(choice['condition'] for choice in menu['choices']))
            menus_with_destinations = sum(1 for menu in analysis['menu_statistics'] 
                                        if any(choice['destination'] for choice in menu['choices']))
            
            print(f"✅ Menu statistics calculated")
            print(f"   📋 Total menu structures: {len(analysis['menu_statistics'])}")
            print(f"   🎯 Total choice options: {total_choices}")
            print(f"   ❓ Menus with conditions: {menus_with_conditions}")
            print(f"   🎯 Menus with destinations: {menus_with_destinations}")
            print(f"   📊 Labels with menus: {len(analysis['menus_by_label'])}")
            
            # Show distribution
            choice_counts = [menu['choice_count'] for menu in analysis['menu_statistics']]
            if choice_counts:
                print(f"   📈 Choice distribution:")
                print(f"     • Min choices: {min(choice_counts)}")
                print(f"     • Max choices: {max(choice_counts)}")
                print(f"     • Avg choices: {round(sum(choice_counts) / len(choice_counts), 2)}")
        
        print("\n" + "=" * 70)
        print("🎉 MENU/CHOICE EXTRACTION TESTS PASSED!")
        print("=" * 70)
        
        # Summary
        print(f"\n📈 Menu/Choice Extraction Summary:")
        print(f"   📋 Menus discovered: {len(menus)}")
        print(f"   🎯 Total choices: {analysis['total_choices']}")
        print(f"   🌿 Decision points: {complexity['total_decision_points']}")
        print(f"   🎯 Complexity score: {complexity['complexity_score']}/100")
        print(f"   📊 Branching factor: {complexity['branching_factor']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def export_menu_analysis(filename: str = "menu_analysis.json"):
    """Export detailed menu analysis to JSON."""
    print(f"\n📤 Exporting menu analysis to {filename}...")
    
    try:
        test_vn_path = get_test_vn_path()
        project = RenpyProject(test_vn_path)
        
        # Get all analysis data
        menus = project.get_all_menus()
        analysis = project.get_menu_analysis()
        complexity = project.get_branching_complexity()
        destinations = project.get_choice_destinations()
        decision_tree = project.get_decision_tree()
        
        # Convert menu objects to serializable format
        serializable_menus = []
        for menu in menus:
            menu_data = {
                'name': menu.name,
                'file_path': menu.file_path,
                'line_number': menu.line_number,
                'label_context': menu.label_context,
                'total_choices': menu.total_choices,
                'choices': []
            }
            
            for choice in menu.choices:
                choice_data = {
                    'text': choice.text,
                    'condition': choice.condition,
                    'destination': choice.destination,
                    'action_type': choice.action_type,
                    'file_path': choice.file_path,
                    'line_number': choice.line_number,
                    'subsequent_lines': choice.subsequent_lines
                }
                menu_data['choices'].append(choice_data)
            
            serializable_menus.append(menu_data)
        
        # Compile complete analysis
        complete_analysis = {
            "project_path": test_vn_path,
            "analysis_type": "menu_choice_extraction",
            "timestamp": project.get_project_overview()["analysis_timestamp"],
            "menus": serializable_menus,
            "analysis": analysis,
            "complexity": complexity,
            "destinations": destinations,
            "decision_tree": decision_tree
        }
        
        # Export to JSON
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(complete_analysis, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Menu analysis exported to {filename}")
        print(f"   📋 {len(menus)} menu structures")
        print(f"   🎯 {analysis['total_choices']} choice options")
        print(f"   🌿 {complexity['total_decision_points']} decision points")
        print(f"   📊 Complete branching analysis")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting menu/choice extraction tests...\n")
    
    success = test_menu_extraction()
    
    if success:
        # Ask if user wants to export analysis
        try:
            response = input("\n❓ Export detailed menu analysis to JSON? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                export_menu_analysis()
        except KeyboardInterrupt:
            print("\n\n👋 Test completed!")
    
    print("\n🔚 Menu extraction test finished.") 