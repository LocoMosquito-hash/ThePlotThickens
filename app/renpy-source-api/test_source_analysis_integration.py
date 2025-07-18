#!/usr/bin/env python3
"""
Test Source Analysis Tab Integration

This script tests the integration of SDK functionality into the Source Analysis tab.
"""

import os
import sys
from pathlib import Path

# Add current directory to path for imports
current_dir = str(Path(__file__).parent)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_source_analysis_integration():
    """Test the Source Analysis tab integration."""
    print("🧪 Testing Source Analysis Tab Integration")
    print("=" * 50)
    
    # Test import of core components
    try:
        from core import RenpyProject
        print("✅ Core RenpyProject import successful")
        
        from sdk_integration import HybridRenpyParser, RenpySDKAnalyzer
        print("✅ SDK integration import successful")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Test tutorial project analysis
    sdk_dir = Path(__file__).parent / "renpy_sdk" / "renpy-8.4.0-sdk"
    tutorial_path = sdk_dir / "tutorial" / "game"
    
    if not tutorial_path.exists():
        print("❌ Tutorial project not found")
        return False
    
    print(f"📂 Testing with tutorial: {tutorial_path}")
    
    try:
        # Test regular analysis
        print("\n📝 Testing regular analysis...")
        project1 = RenpyProject(str(tutorial_path), use_hybrid_parser=False)
        overview1 = project1.analyze()
        print(f"   Regular parser: {overview1.total_labels} labels, {overview1.total_characters} characters")
        
        # Test enhanced analysis (what the Source Analysis tab will use)
        print("🔧 Testing enhanced analysis...")
        project2 = RenpyProject(str(tutorial_path), use_hybrid_parser=True)
        overview2 = project2.analyze()
        print(f"   Enhanced parser: {overview2.total_labels} labels, {overview2.total_characters} characters")
        
        # Show improvement
        label_improvement = overview2.total_labels - overview1.total_labels
        character_improvement = overview2.total_characters - overview1.total_characters
        
        print(f"\n📊 Enhancement Results:")
        print(f"   Labels: +{label_improvement} more accurate")
        print(f"   Characters: +{character_improvement} more accurate")
        
        if hasattr(project2.parser, 'get_analysis_stats'):
            stats = project2.parser.get_analysis_stats()
            print(f"   SDK Usage: {stats['sdk_usage_percent']:.1f}%")
            if stats['cache_hits'] > 0:
                print(f"   Cache Hits: {stats['cache_hits']}")
        
        print("✅ Source Analysis integration working!")
        return True
        
    except Exception as e:
        print(f"❌ Analysis test failed: {e}")
        return False

def test_caching_system():
    """Test the caching system functionality."""
    print("\n🗃️  Testing Caching System")
    print("=" * 50)
    
    try:
        from sdk_integration import SDKResultsCache
        
        cache = SDKResultsCache()
        print("✅ Cache system initialized")
        
        # Test with tutorial project
        sdk_dir = Path(__file__).parent / "renpy_sdk" / "renpy-8.4.0-sdk"
        tutorial_path = str(sdk_dir / "tutorial" / "game")
        
        if not Path(tutorial_path).exists():
            print("❌ Tutorial project not found for cache test")
            return False
        
        # Test hash generation
        hash1 = cache.get_project_hash(tutorial_path)
        hash2 = cache.get_project_hash(tutorial_path)
        
        if hash1 == hash2:
            print(f"✅ Consistent hash generation: {hash1[:16]}...")
        else:
            print(f"❌ Inconsistent hash generation")
            return False
        
        # Test cache storage (without actual analysis for speed)
        test_data = {
            "test": True,
            "project_info": {
                "total_labels": 10,
                "total_characters": 5
            }
        }
        
        cache.cache_result(tutorial_path, test_data)
        print("✅ Cache storage successful")
        
        # Test cache retrieval
        cached_data = cache.get_cached_result(tutorial_path)
        if cached_data and cached_data.get("test") == True:
            print("✅ Cache retrieval successful")
            print(f"   Cached data: {cached_data['project_info']}")
        else:
            print("❌ Cache retrieval failed")
            return False
        
        print("✅ Caching system working!")
        return True
        
    except Exception as e:
        print(f"❌ Cache test failed: {e}")
        return False

def main():
    """Run all integration tests."""
    print("🧪 Source Analysis Integration Test Suite")
    print("=" * 60)
    
    tests = [
        ("Source Analysis Integration", test_source_analysis_integration),
        ("Caching System", test_caching_system),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:<10} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        print("✨ The Source Analysis tab is ready for enhanced SDK analysis!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main() 