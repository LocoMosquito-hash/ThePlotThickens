#!/usr/bin/env python3
"""
Test the new Authoritative Hierarchy system vs the old string-based system.

This script specifically tests with Haley's Story ep2cont5 to see if the new
hierarchy eliminates the rogue node issue.
"""

import sys
from pathlib import Path

# Add renpy-source-api to path
current_dir = Path(__file__).parent
app_dir = current_dir.parent.parent / "app"
sys.path.insert(0, str(app_dir / "renpy-source-api"))

from renpy_data_adapter import RenpyFlowDataAdapter

def test_haley_hierarchy():
    """Test the authoritative hierarchy with Haley's Story."""
    
    game_path = "F:\\Bin\\Games\\Haley-1.1-alt-pc\\game"
    
    print("🧪 Testing Authoritative Hierarchy vs Old String-Based System")
    print("=" * 70)
    print(f"📁 Game: Haley's Story")
    print(f"📂 Path: {game_path}")
    print(f"🎯 Target: ep2cont5 rogue node issue")
    print()
    
    # Initialize adapter with hybrid parsing
    adapter = RenpyFlowDataAdapter(use_hybrid=True)
    
    print("🔄 Running analysis with both systems...")
    
    # This will now build both the old system AND the new authoritative hierarchy
    visualization_data = adapter.analyze_project(game_path)
    
    print("\n📊 Analysis complete!")
    print(f"📈 Total nodes generated: {len(visualization_data.nodes)}")
    print(f"🔗 Total connections generated: {len(visualization_data.connections)}")
    
    # The comparison will be automatically printed by _compare_hierarchy_systems()
    
    print("\n" + "=" * 70)
    print("🎯 Key Findings:")
    print("✅ Both systems have been built and compared")
    print("📋 Check the comparison output above for differences")
    print("🔍 Look for rogue node detection results")

if __name__ == "__main__":
    test_haley_hierarchy()