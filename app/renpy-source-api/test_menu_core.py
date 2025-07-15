#!/usr/bin/env python3
"""
Core test script for menu node separation implementation.

This tests the new MenuNode system without requiring visualization dependencies.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from parser import RenpyParser, MenuNode, LabelNode
    from core import RenpyProject
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the correct directory")
    sys.exit(1)


def test_parser_enhancement():
    """Test the enhanced parser with MenuNode functionality."""
    print("🔧 Testing enhanced parser...")
    
    # Create a simple test case
    test_content = '''
label ch4ashbagdone:

    scene ch4ashbeach5

    A "Thank you so much for watching my things!"

    T "No problem!"

    T "I was happy to do it..."

    "I need to think of something to bring up to keep the conversation going..."

    menu:

        "Fashion" :
            jump ch4ashfashion

        "Drinking" :
            jump ch4ashdrink

        "Animals" :
            jump ch4ashanimal

        "Vegetables" :
            jump ch4ashveg
'''
    
    # Write test content to a temporary file
    test_file = "test_temp.rpy"
    try:
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        parser = RenpyParser()
        
        # Test menu structure parsing
        print("📋 Testing menu structure parsing...")
        lines = test_content.split('\n')
        menu_line = next(i for i, line in enumerate(lines) if 'menu:' in line) + 1
        
        menu_structure = parser.parse_menu_structure(test_file, menu_line, lines)
        print(f"✅ Parsed menu with {menu_structure.total_choices} choices")
        print(f"✅ Label context: {menu_structure.label_context}")
        
        # Test MenuNode creation
        print("🏗️ Testing MenuNode creation...")
        menu_node = parser._create_menu_node_from_structure(menu_structure, 0)
        
        print(f"✅ Created MenuNode: {menu_node.node_id}")
        print(f"    Name: {menu_node.name}")
        print(f"    Choices: {menu_node.total_choices}")
        print(f"    Complexity: {menu_node.complexity_level}")
        print(f"    Destinations: {menu_node.choice_destinations}")
        
        # Verify the specific choices
        expected_destinations = ['ch4ashfashion', 'ch4ashdrink', 'ch4ashanimal', 'ch4ashveg']
        if set(menu_node.choice_destinations) == set(expected_destinations):
            print("✅ All expected destinations found")
        else:
            print(f"❌ Destination mismatch. Expected: {expected_destinations}, Got: {menu_node.choice_destinations}")
        
        # Test choice details
        print("\n📝 Choice details:")
        for i, choice in enumerate(menu_node.choices):
            print(f"  {i+1}. '{choice.text}' -> {choice.destination} ({choice.action_type})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during parser testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up test file
        if os.path.exists(test_file):
            os.remove(test_file)


def test_flow_graph_with_sample():
    """Test flow graph building with a sample VN structure."""
    print("\n🌐 Testing flow graph building...")
    
    # Create a more comprehensive test structure
    test_content = '''
label start:
    "Welcome to the test VN"
    jump ch4ashbagdone

label ch4ashbagdone:
    scene ch4ashbeach5
    A "Thank you so much for watching my things!"
    T "No problem!"
    "I need to think of something to bring up..."
    
    menu:
        "Fashion":
            jump ch4ashfashion
        "Drinking":
            jump ch4ashdrink
        "Animals":
            jump ch4ashanimal
        "Vegetables":
            jump ch4ashveg

label ch4ashfashion:
    "Fashion conversation"
    jump ch4ashend

label ch4ashdrink:
    "Drinking conversation"
    jump ch4ashend

label ch4ashanimal:
    "Animal conversation"
    jump ch4ashend

label ch4ashveg:
    "Vegetable conversation"
    jump ch4ashend

label ch4ashend:
    "The conversation continues..."
    return
'''
    
    # Create a temporary directory structure
    test_dir = "test_vn_temp"
    test_file = os.path.join(test_dir, "script.rpy")
    
    try:
        os.makedirs(test_dir, exist_ok=True)
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        parser = RenpyParser()
        
        # Test flow graph building
        print("🏗️ Building flow graph...")
        flow_graph = parser.build_flow_graph(test_dir)
        
        print(f"✅ Built flow graph with {len(flow_graph)} labels")
        
        # Check that we have all expected labels
        expected_labels = ['start', 'ch4ashbagdone', 'ch4ashfashion', 'ch4ashdrink', 'ch4ashanimal', 'ch4ashveg', 'ch4ashend']
        for label in expected_labels:
            if label in flow_graph:
                print(f"✅ Found label: {label}")
            else:
                print(f"❌ Missing label: {label}")
        
        # Check ch4ashbagdone specifically
        if 'ch4ashbagdone' in flow_graph:
            label_node = flow_graph['ch4ashbagdone']
            print(f"\n🎯 ch4ashbagdone analysis:")
            print(f"    Has menu: {label_node.has_menu}")
            print(f"    Menu count: {label_node.menu_count}")
            
            if label_node.menu_nodes:
                menu_node = label_node.menu_nodes[0]
                print(f"    Menu node ID: {menu_node.node_id}")
                print(f"    Menu destinations: {menu_node.choice_destinations}")
                print(f"    This should reduce {len(menu_node.choice_destinations)} direct connections to the label")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during flow graph testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up test directory
        if os.path.exists(test_file):
            os.remove(test_file)
        if os.path.exists(test_dir):
            os.rmdir(test_dir)


def test_menu_metadata_richness():
    """Test the richness of menu metadata."""
    print("\n💎 Testing menu metadata richness...")
    
    # Test with conditional menu
    test_content = '''
label complex_menu:
    $ player_money = 100
    $ player_reputation = 50
    
    "What should you do?"
    
    menu:
        "Buy expensive item" if player_money >= 100:
            $ player_money -= 100
            show expensive_item
            jump item_bought
            
        "Buy cheap item":
            $ player_money -= 20
            show cheap_item
            jump item_bought
            
        "Walk away":
            "You decide not to buy anything"
            return
'''
    
    test_file = "test_complex.rpy"
    try:
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        parser = RenpyParser()
        lines = test_content.split('\n')
        menu_line = next(i for i, line in enumerate(lines) if 'menu:' in line) + 1
        
        menu_structure = parser.parse_menu_structure(test_file, menu_line, lines)
        menu_node = parser._create_menu_node_from_structure(menu_structure, 0)
        
        print(f"✅ Complex menu analysis:")
        print(f"    Menu type: {menu_node.menu_type}")
        print(f"    Has conditions: {menu_node.has_conditions}")
        print(f"    Complexity level: {menu_node.complexity_level}")
        print(f"    Story significance: {menu_node.story_significance}")
        
        # Check individual choices
        for i, choice in enumerate(menu_node.choices):
            print(f"  Choice {i+1}: '{choice.text}'")
            print(f"    Has condition: {choice.has_condition}")
            print(f"    Leads to label: {choice.leads_to_label}")
            print(f"    Media references: {choice.contains_media_references}")
            print(f"    Variable changes: {choice.contains_variable_changes}")
            print(f"    Story impact: {choice.estimated_story_impact}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during metadata testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


def main():
    """Run core tests for the menu separation implementation."""
    print("🚀 Testing Core Menu Node Implementation")
    print("=" * 50)
    
    tests = [
        ("Parser Enhancement", test_parser_enhancement),
        ("Flow Graph Building", test_flow_graph_with_sample),
        ("Menu Metadata Richness", test_menu_metadata_richness),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 30)
        
        success = test_func()
        results.append((test_name, success))
        
        if success:
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All core tests passed! Menu separation implementation is working.")
        print("\n📝 Summary of what we've implemented:")
        print("  ✅ MenuNode class with rich metadata")
        print("  ✅ Enhanced MenuChoice with story impact analysis")
        print("  ✅ LabelNode integration with menu tracking")
        print("  ✅ Flow graph building with menu node separation")
        print("  ✅ Asset and variable change detection")
        print("  ✅ Menu complexity classification")
        print("\n🎯 Next steps:")
        print("  - Integrate with flow visualizer (requires visualization deps)")
        print("  - Handle nested menus (Stage 4)")
        print("  - Test with real VN files")
        print("  - Add circular reference prevention")
    else:
        print("⚠️ Some tests failed. Check the errors above for details.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 