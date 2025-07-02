#!/usr/bin/env python3
"""
Test script for label flow analysis and scene connectivity mapping.
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

def test_label_flow_analysis():
    """Test the label flow analysis and scene connectivity features."""
    print("=" * 70)
    print("LABEL FLOW ANALYSIS TEST")
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
        
        # Test 1: Label Flow Analysis
        print("\n🔗 Test 1: Label Flow Analysis")
        print("-" * 40)
        
        flow_analysis = project.get_label_flow_analysis()
        print(f"✅ Flow analysis completed")
        print(f"   📊 Total labels: {flow_analysis['total_labels']}")
        print(f"   🌊 Total flows: {flow_analysis['total_flows']}")
        print(f"   🎯 Reachable labels: {flow_analysis['reachable_labels']}")
        print(f"   🚫 Unreachable labels: {flow_analysis['unreachable_labels']}")
        print(f"   💀 Dead end labels: {flow_analysis['dead_end_labels']}")
        print(f"   🚪 Entry points: {flow_analysis['entry_points']}")
        
        print(f"\n🔄 Flow Types:")
        for flow_type, count in flow_analysis['flow_types'].items():
            print(f"   • {flow_type}: {count}")
        
        print(f"\n📈 Flow Metrics:")
        print(f"   • Average complexity: {flow_analysis['average_complexity']}")
        print(f"   • Connectivity ratio: {flow_analysis['connectivity_ratio']}")
        print(f"   • Reachability ratio: {flow_analysis['reachability_ratio']}")
        print(f"   • Flow clusters: {flow_analysis['flow_clusters']}")
        print(f"   • Largest cluster: {flow_analysis['largest_cluster_size']} labels")
        
        # Test 2: Scene Connectivity
        print("\n🕸️  Test 2: Scene Connectivity Analysis")
        print("-" * 40)
        
        connectivity = project.get_scene_connectivity()
        print(f"✅ Connectivity analysis completed")
        
        print(f"\n📊 Reachability Summary:")
        reachability = connectivity['reachability_summary']
        print(f"   • Total scenes: {reachability['total_labels']}")
        print(f"   • Reachable: {reachability['reachable_labels']}")
        print(f"   • Unreachable: {reachability['unreachable_labels']}")
        print(f"   • Reachability: {reachability['reachability_ratio']:.1%}")
        
        print(f"\n🌐 Navigation Patterns:")
        navigation = connectivity['navigation_patterns']
        print(f"   • Total flows: {navigation['total_flows']}")
        print(f"   • Connectivity ratio: {navigation['connectivity_ratio']}")
        print(f"   • Flow types: {list(navigation['flow_types'].keys())}")
        
        print(f"\n🏗️  Structural Analysis:")
        structure = connectivity['structural_analysis']
        print(f"   • Entry points: {structure['entry_points']}")
        print(f"   • Dead ends: {structure['dead_ends']}")
        print(f"   • High complexity scenes: {structure['high_complexity_scenes']}")
        print(f"   • Flow clusters: {structure['flow_clusters']}")
        
        print(f"\n🏆 Most Connected Scenes:")
        most_incoming = connectivity['most_connected_scenes']['most_incoming'][:5]
        most_outgoing = connectivity['most_connected_scenes']['most_outgoing'][:5]
        
        print(f"   📥 Most Incoming:")
        for label, count in most_incoming:
            print(f"     • {label}: {count} incoming flows")
        
        print(f"   📤 Most Outgoing:")
        for label, count in most_outgoing:
            print(f"     • {label}: {count} outgoing flows")
        
        # Test 3: Flow Quality Assessment
        print("\n⭐ Test 3: Narrative Flow Quality")
        print("-" * 40)
        
        quality = connectivity['narrative_flow_quality']
        print(f"✅ Flow quality assessment completed")
        print(f"   🏆 Overall score: {quality['overall_score']}/100")
        print(f"   📊 Quality rating: {quality['quality_rating'].upper()}")
        print(f"   🎯 Reachability score: {quality['reachability_score']}/80")
        print(f"   🔗 Connectivity score: {quality['connectivity_score']}/20")
        
        if quality['issues']:
            print(f"\n⚠️  Issues Found:")
            for issue in quality['issues']:
                print(f"     • {issue}")
        
        if quality['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in quality['recommendations']:
                print(f"     • {rec}")
        
        # Test 4: Narrative Paths  
        print("\n🛤️  Test 4: Narrative Path Finding")
        print("-" * 40)
        
        # Find paths from start
        start_label = 'start' if 'start' in [item[0] for item in most_outgoing] else most_outgoing[0][0]
        paths = project.find_narrative_paths(start_label, max_depth=5)
        
        print(f"✅ Path finding completed")
        print(f"   🚀 Starting from: {start_label}")
        print(f"   🛤️  Total paths found: {len(paths)}")
        
        if paths:
            print(f"\n📍 Sample Paths:")
            for i, path in enumerate(paths[:5]):
                path_str = ' → '.join(path)
                print(f"   {i+1}. {path_str}")
                if len(path_str) > 60:
                    print(f"      ({len(path)} scenes)")
            
            if len(paths) > 5:
                print(f"   ... and {len(paths) - 5} more paths")
        
        # Test 5: Scene Timeline
        print("\n📅 Test 5: Scene Timeline Generation")
        print("-" * 40)
        
        timeline = project.get_scene_timeline()
        print(f"✅ Timeline generation completed")
        print(f"   📝 Total scenes in timeline: {len(timeline)}")
        
        if timeline:
            print(f"\n⏰ Timeline Overview:")
            for i, scene in enumerate(timeline[:10]):
                depth_info = "  " * scene['depth']
                menu_info = " [MENU]" if scene['has_menu'] else ""
                dialogue_info = " [DIALOGUE]" if scene['has_dialogue'] else ""
                complexity_info = f" ({scene['flow_complexity']} flows)" if scene['flow_complexity'] > 0 else ""
                
                print(f"   {depth_info}{scene['label']}{menu_info}{dialogue_info}{complexity_info}")
            
            if len(timeline) > 10:
                print(f"   ... and {len(timeline) - 10} more scenes")
                
            # Show depth distribution
            depth_distribution = {}
            for scene in timeline:
                depth = scene['depth']
                if depth not in depth_distribution:
                    depth_distribution[depth] = 0
                depth_distribution[depth] += 1
            
            print(f"\n📊 Depth Distribution:")
            for depth in sorted(depth_distribution.keys())[:5]:
                print(f"   • Depth {depth}: {depth_distribution[depth]} scenes")
        
        # Test 6: Flow Pattern Analysis
        print("\n🔍 Test 6: Flow Pattern Analysis")
        print("-" * 40)
        
        # Test different pattern types
        pattern_types = ['cycles', 'bridges', 'hubs']
        
        for pattern_type in pattern_types:
            patterns = project.search_flow_patterns(pattern_type)
            print(f"\n🔎 {pattern_type.capitalize()} Analysis:")
            print(f"   📊 Found {len(patterns)} {pattern_type}")
            
            if patterns:
                for i, pattern in enumerate(patterns[:3]):
                    if pattern_type == 'cycles':
                        path_str = ' → '.join(pattern['path'])
                        print(f"     {i+1}. Cycle: {path_str} (length: {pattern['length']})")
                    elif pattern_type == 'bridges':
                        print(f"     {i+1}. Bridge: {pattern['label']} "
                              f"({pattern['incoming_count']}→{pattern['outgoing_count']})")
                    elif pattern_type == 'hubs':
                        print(f"     {i+1}. Hub: {pattern['label']} "
                              f"({pattern['total_connections']} total connections)")
                        
                if len(patterns) > 3:
                    print(f"     ... and {len(patterns) - 3} more {pattern_type}")
        
        print("\n" + "=" * 70)
        print("🎉 LABEL FLOW ANALYSIS TESTS PASSED!")
        print("=" * 70)
        
        # Summary
        print(f"\n📈 Label Flow Analysis Summary:")
        print(f"   🏷️  Total labels: {flow_analysis['total_labels']}")
        print(f"   🌊 Total flows: {flow_analysis['total_flows']}")
        print(f"   🎯 Reachability: {flow_analysis['reachability_ratio']:.1%}")
        print(f"   🔗 Connectivity: {flow_analysis['connectivity_ratio']:.2f}")
        print(f"   ⭐ Quality score: {quality['overall_score']}/100 ({quality['quality_rating']})")
        print(f"   🛤️  Narrative paths: {len(paths)}")
        print(f"   📅 Timeline scenes: {len(timeline)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting label flow analysis tests...\n")
    
    success = test_label_flow_analysis()
    
    if success:
        print("\n✅ All tests passed!")
    
    print("\n🔚 Label flow analysis test finished.") 