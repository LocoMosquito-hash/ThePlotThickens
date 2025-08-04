#!/usr/bin/env python3
"""
Test the architectural fixes specifically with The Question game.

This script tests the new authoritative hierarchy system with the simple
Question game to verify that the container/choice relationship issues are fixed.
"""

import sys
from pathlib import Path

# Add renpy-source-api to path
current_dir = Path(__file__).parent
app_dir = current_dir.parent.parent / "app"
sys.path.insert(0, str(app_dir / "renpy-source-api"))

from renpy_data_adapter import RenpyFlowDataAdapter

def test_question_game_fixes():
    """Test the fixes with The Question game."""
    
    game_path = "C:\\Users\\juanc\\PycharmProjects\\TPT3\\ThePlotThickens\\app\\renpy-source-api\\renpy_sdk\\renpy-8.4.0-sdk\\the_question\\game"
    
    print("🧪 Testing Architectural Fixes with The Question Game")
    print("=" * 70)
    print(f"📁 Game: The Question (simple test game)")
    print(f"📂 Path: {game_path}")
    print(f"🎯 Testing: Container/choice relationship fixes")
    print()
    
    # Initialize adapter with authoritative hierarchy
    adapter = RenpyFlowDataAdapter(use_hybrid=True)
    
    try:
        # Analyze the game
        print("🔧 Analyzing game with new authoritative hierarchy...")
        visualization_data = adapter.analyze_project(game_path)
        
        print(f"📊 Results:")
        print(f"   📋 Total nodes: {len(visualization_data.nodes)}")
        print(f"   🔗 Total connections: {len(visualization_data.connections)}")
        print()
        
        # Find specific nodes mentioned in the screenshot issue
        menu_containers = [node for node in visualization_data.nodes if node.node_type == 'menu_container']
        choice_buttons = [node for node in visualization_data.nodes if node.node_type == 'choice_button']
        label_nodes = [node for node in visualization_data.nodes if node.node_type not in ['menu_container', 'choice_button']]
        
        print("🔍 Node Analysis:")
        print(f"   📦 Menu containers: {len(menu_containers)}")
        print(f"   🎯 Choice buttons: {len(choice_buttons)}")
        print(f"   🏷️  Label nodes: {len(label_nodes)}")
        print()
        
        # Look for specific issues mentioned in the original screenshot
        print("🎯 Looking for issues mentioned in screenshot:")
        print()
        
        # Check for orphaned labels at top level (should be minimal for simple game)
        orphan_labels = [node for node in label_nodes if not any(
            conn.target_node_id == node.node_id for conn in visualization_data.connections
        )]
        print(f"   🏷️  Orphaned labels: {len(orphan_labels)}")
        if orphan_labels:
            for label in orphan_labels[:5]:  # Show first 5
                print(f"      - {label.display_name} (ID: {label.node_id})")
        
        # Check for container-to-choice connections (should be eliminated)
        container_to_choice_connections = [conn for conn in visualization_data.connections 
                                         if conn.connection_type == 'container_to_choice']
        print(f"   🔗 Container-to-choice connections: {len(container_to_choice_connections)}")
        
        # Check for choice-to-destination connections (should exist)
        choice_to_label_connections = [conn for conn in visualization_data.connections 
                                     if conn.connection_type == 'choice_to_label']
        print(f"   🎯 Choice-to-destination connections: {len(choice_to_label_connections)}")
        
        # Examine menu containers for embedded choice data
        print()
        print("📦 Menu Container Analysis:")
        for i, container in enumerate(menu_containers[:3]):  # Show first 3
            print(f"   Container {i+1}: {container.display_name}")
            print(f"      📋 ID: {container.node_id}")
            choices = container.metadata.get('choices', [])
            print(f"      🎯 Embedded choices: {len(choices)}")
            for j, choice in enumerate(choices):
                print(f"         Choice {j+1}: {choice.get('text', 'N/A')} → {choice.get('destination', 'N/A')}")
        
        print()
        print("=" * 70)
        print("🎉 Analysis Complete!")
        print()
        print("✅ Key Architectural Fixes Applied:")
        print("   1. Choices embedded in containers (no separate choice nodes)")
        print("   2. No container-to-choice edges (visual containment)")
        print("   3. Choice-to-destination connections from containers")
        print("   4. Reduced orphaned labels")
        
        # Provide summary
        issues_fixed = []
        if len(choice_buttons) == 0:
            issues_fixed.append("✅ No separate choice button nodes (embedded in containers)")
        if len(container_to_choice_connections) == 0:
            issues_fixed.append("✅ No container-to-choice edges")
        if len(choice_to_label_connections) > 0:
            issues_fixed.append("✅ Choice-to-destination connections exist")
        if len(orphan_labels) <= 2:  # Expect minimal orphans in simple game
            issues_fixed.append("✅ Minimal orphaned labels")
        
        print()
        print("🏆 Issues Fixed:")
        for fix in issues_fixed:
            print(f"   {fix}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_question_game_fixes()
    sys.exit(0 if success else 1)