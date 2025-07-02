#!/usr/bin/env python3
"""
Test script for asset tracking features.
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

def test_asset_tracking():
    """Test the asset tracking features."""
    print("=" * 70)
    print("ASSET TRACKING TEST")
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
        
        # Test 1: Get All Assets
        print("\n📦 Test 1: Asset Discovery")
        print("-" * 40)
        
        assets_by_category = project.get_all_assets()
        total_assets = sum(len(set(asset['name'] for asset in assets)) 
                          for assets in assets_by_category.values())
        
        print(f"✅ Asset discovery completed")
        print(f"   📊 Total unique assets found: {total_assets}")
        
        for category, assets in assets_by_category.items():
            unique_assets = set(asset['name'] for asset in assets)
            if unique_assets:
                print(f"   📂 {category.title()}: {len(unique_assets)} unique ({len(assets)} total usages)")
        
        # Test 2: Asset Usage Statistics
        print("\n📈 Test 2: Asset Usage Statistics")
        print("-" * 40)
        
        usage_stats = project.get_asset_usage_stats()
        print(f"✅ Usage statistics calculated")
        print(f"   📊 Total unique assets: {usage_stats['total_assets']}")
        
        print(f"\n📋 Assets by Category:")
        for category, stats in usage_stats['by_category'].items():
            if stats['unique_count'] > 0:
                print(f"   📂 {category.title()}: {stats['unique_count']} unique, {stats['total_usages']} usages")
        
        print(f"\n🎭 Usage Patterns:")
        patterns = usage_stats['usage_patterns']
        print(f"   🎬 Scene backgrounds: {patterns['scene_backgrounds']}")
        print(f"   👤 Character sprites: {patterns['character_sprites']}")
        print(f"   🎵 Background music: {patterns['background_music']}")
        print(f"   🔊 Sound effects: {patterns['sound_effects']}")
        print(f"   🖼️  Image definitions: {patterns['image_definitions']}")
        
        # Test 3: Most Used Assets
        print("\n🏆 Test 3: Most Used Assets")
        print("-" * 40)
        
        most_used = project.get_most_used_assets(limit=15)
        print(f"✅ Most used assets retrieved ({len(most_used)} assets)")
        
        for i, asset in enumerate(most_used[:10]):
            print(f"   {i+1}. {asset['name']} ({asset['category']})")
            print(f"      📊 Usage: {asset['usage_count']} times")
            print(f"      📂 Files: {asset['files_count']}")
            print(f"      🏷️  Labels: {asset['labels_count']}")
            print(f"      🎭 Types: {', '.join(asset['usage_types'])}")
            print()
        
        # Test 4: Asset Search
        print("\n🔍 Test 4: Asset Search")
        print("-" * 40)
        
        # Search for common asset types
        search_terms = ["bg", "image", "music", "sound", ".png", ".mp3"]
        
        for term in search_terms:
            results = project.search_assets(term)
            if results:
                print(f"   🔍 Search '{term}': {len(results)} matches")
                for result in results[:3]:  # Show top 3 matches
                    usage_count = result.get('total_usage_count', 'unknown')
                    print(f"     • {result['name']} ({result['category']}) - used {usage_count} times")
                print()
                break
        
        # Test 5: Assets by Category
        print("\n📂 Test 5: Assets by Category")
        print("-" * 40)
        
        # Test each category
        for category in ['images', 'audio', 'video']:
            category_assets = project.get_assets_by_category(category)
            unique_assets = set(asset['name'] for asset in category_assets)
            
            if unique_assets:
                print(f"   📂 {category.title()}: {len(unique_assets)} unique assets")
                
                # Show sample assets
                for asset_name in sorted(list(unique_assets))[:5]:
                    print(f"     • {asset_name}")
                
                if len(unique_assets) > 5:
                    print(f"     • ... and {len(unique_assets) - 5} more")
                print()
        
        # Test 6: Asset Timeline (for most used asset)
        print("\n⏰ Test 6: Asset Timeline")
        print("-" * 40)
        
        if most_used:
            top_asset = most_used[0]
            timeline = project.get_asset_timeline(top_asset['name'])
            
            print(f"✅ Timeline retrieved for '{top_asset['name']}'")
            print(f"   📊 {len(timeline)} usage instances found")
            
            if timeline:
                print(f"   📝 Usage timeline:")
                for i, usage in enumerate(timeline[:8]):
                    label_info = f" (label: {usage['label']})" if usage['label'] else ""
                    print(f"     {i+1}. {usage['file']}:{usage['line_number']} - {usage['usage_type']}{label_info}")
                
                if len(timeline) > 8:
                    print(f"     ... and {len(timeline) - 8} more usages")
        
        # Test 7: Most Used by Category
        print("\n🎵 Test 7: Most Used by Category (Audio)")
        print("-" * 40)
        
        most_used_audio = project.get_most_used_assets(limit=8, category='audio')
        if most_used_audio:
            print(f"✅ Most used audio assets ({len(most_used_audio)} found)")
            
            for i, asset in enumerate(most_used_audio[:5]):
                print(f"   {i+1}. {asset['name']}")
                print(f"      📊 Usage: {asset['usage_count']} times")
                print(f"      🎭 Types: {', '.join(asset['usage_types'])}")
        else:
            print("   ℹ️  No audio assets found")
        
        print("\n" + "=" * 70)
        print("🎉 ASSET TRACKING TESTS PASSED!")
        print("=" * 70)
        
        # Summary
        print(f"\n📈 Asset Tracking Summary:")
        print(f"   📦 Total assets: {usage_stats['total_assets']}")
        print(f"   🖼️  Images: {usage_stats['by_category']['images']['unique_count']}")
        print(f"   🎵 Audio: {usage_stats['by_category']['audio']['unique_count']}")
        print(f"   🎬 Video: {usage_stats['by_category']['video']['unique_count']}")
        print(f"   🎭 Usage patterns detected: {sum(usage_stats['usage_patterns'].values())} total usages")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def export_asset_analysis(filename: str = "asset_analysis.json"):
    """Export detailed asset analysis to JSON."""
    print(f"\n📤 Exporting asset analysis to {filename}...")
    
    try:
        test_vn_path = get_test_vn_path()
        project = RenpyProject(test_vn_path)
        
        # Get all analysis data
        assets_by_category = project.get_all_assets()
        usage_stats = project.get_asset_usage_stats()
        most_used = project.get_most_used_assets(50)
        
        # Get timelines for top assets
        for asset in most_used[:10]:
            timeline = project.get_asset_timeline(asset['name'])
            asset['timeline'] = timeline
        
        # Compile complete analysis
        analysis = {
            "project_path": test_vn_path,
            "analysis_type": "asset_tracking_analysis",
            "timestamp": project.get_project_overview()["analysis_timestamp"],
            "assets_by_category": assets_by_category,
            "usage_statistics": usage_stats,
            "most_used_assets": most_used,
            "categories_summary": {
                category: {
                    "unique_count": len(set(asset['name'] for asset in assets)),
                    "total_usages": len(assets),
                    "sample_assets": sorted(list(set(asset['name'] for asset in assets)))[:20]
                }
                for category, assets in assets_by_category.items()
                if assets
            }
        }
        
        # Export to JSON
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Asset analysis exported to {filename}")
        print(f"   📦 {usage_stats['total_assets']} unique assets")
        print(f"   🏆 Top {len(most_used)} assets with timelines")
        print(f"   📈 Complete usage statistics and patterns")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting asset tracking tests...\n")
    
    success = test_asset_tracking()
    
    if success:
        # Ask if user wants to export analysis
        try:
            response = input("\n❓ Export detailed asset analysis to JSON? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                export_asset_analysis()
        except KeyboardInterrupt:
            print("\n\n👋 Test completed!")
    
    print("\n🔚 Asset tracking test finished.") 