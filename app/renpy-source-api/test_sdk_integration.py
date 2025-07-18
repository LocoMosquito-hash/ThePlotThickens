#!/usr/bin/env python3
"""
Test script for SDK integration with hybrid parser.

This script tests the new hybrid parsing functionality that combines
regex parsing with SDK analysis for better accuracy on complex VNs.
"""

import os
import sys
from pathlib import Path

# Add current directory to path for imports
current_dir = str(Path(__file__).parent)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from core import RenpyProject
    from sdk_integration import HybridRenpyParser, RenpySDKAnalyzer, ComplexityDetector
    from exceptions import RenpyProjectError, RenpyAnalysisError
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Test configuration
TEST_VN_PATHS = [
    r"T:\AG\Savior-0.16c-pc\game",
    r"T:\AG\MySisterMyRoommateV1.69-pc\game",
    r"T:\AG\AcceptthePast-0.1-pc\game",
]

def find_test_vn() -> str:
    """Find an available test VN from the list."""
    for vn_path in TEST_VN_PATHS:
        if os.path.exists(vn_path):
            return vn_path
    
    print("❌ No test VN found. Please update TEST_VN_PATHS in the script.")
    return ""

def test_sdk_analyzer():
    """Test the standalone SDK analyzer."""
    print("🧪 Testing SDK Analyzer")
    print("=" * 50)
    
    vn_path = find_test_vn()
    if not vn_path:
        return False
    
    print(f"📂 Test VN: {vn_path}")
    
    # Test SDK availability
    analyzer = RenpySDKAnalyzer()
    print(f"SDK Available: {analyzer.is_available}")
    
    if not analyzer.is_available:
        print("❌ SDK analyzer not available - check SDK installation")
        return False
    
    # Test analysis
    try:
        print("🔄 Running SDK analysis...")
        result = analyzer.analyze_project(vn_path, verbose=True)
        
        if result.success:
            print("✅ SDK analysis successful!")
            print(f"   Analysis time: {result.analysis_time:.2f}s")
            print(f"   Cache hit: {result.cache_hit}")
            
            if result.data:
                project_info = result.data.get('project_info', {})
                print(f"   Files: {project_info.get('rpy_files', 0)}")
                print(f"   Labels: {project_info.get('total_labels', 0)}")
                print(f"   Characters: {project_info.get('total_characters', 0)}")
                print(f"   Menus: {project_info.get('total_menus', 0)}")
            
            return True
        else:
            print(f"❌ SDK analysis failed: {result.error}")
            return False
    
    except Exception as e:
        print(f"❌ SDK analysis exception: {e}")
        return False

def test_complexity_detector():
    """Test the complexity detection logic."""
    print("\n🔍 Testing Complexity Detector")
    print("=" * 50)
    
    vn_path = find_test_vn()
    if not vn_path:
        return False
    
    detector = ComplexityDetector()
    
    print(f"📂 Analyzing complexity: {vn_path}")
    
    try:
        needs_sdk, reasons = detector.needs_sdk_analysis(vn_path)
        
        print(f"Needs SDK: {needs_sdk}")
        print(f"Reasons ({len(reasons)}):")
        for reason in reasons:
            print(f"   • {reason}")
        
        return True
    
    except Exception as e:
        print(f"❌ Complexity detection failed: {e}")
        return False

def test_hybrid_parser():
    """Test the hybrid parser functionality."""
    print("\n🔄 Testing Hybrid Parser")
    print("=" * 50)
    
    vn_path = find_test_vn()
    if not vn_path:
        return False
    
    try:
        # Test basic hybrid parser
        parser = HybridRenpyParser()
        print(f"📂 Analyzing with hybrid parser: {vn_path}")
        
        results = parser.analyze_project(vn_path, verbose=True)
        
        print("✅ Hybrid analysis successful!")
        print(f"   Files: {results.total_rpy_files}")
        print(f"   Lines: {results.total_lines}")
        print(f"   Dialogue: {results.total_dialogue_lines}")
        print(f"   Labels: {results.total_labels}")
        print(f"   Characters: {results.total_characters}")
        print(f"   Menus: {results.total_menus}")
        print(f"   Errors: {len(results.errors)}")
        
        # Show statistics
        stats = parser.get_analysis_stats()
        print(f"\n📊 Analysis Statistics:")
        print(f"   Total projects: {stats['total_projects']}")
        print(f"   Regex only: {stats['regex_only']} ({stats['regex_only_percent']:.1f}%)")
        print(f"   SDK usage: {stats['sdk_fallback'] + stats['sdk_preferred']} ({stats['sdk_usage_percent']:.1f}%)")
        print(f"   Cache hits: {stats['cache_hits']} ({stats['cache_hit_percent']:.1f}%)")
        
        return True
    
    except Exception as e:
        print(f"❌ Hybrid parser test failed: {e}")
        return False

def test_renpy_project_integration():
    """Test the integration with RenpyProject class."""
    print("\n🔗 Testing RenpyProject Integration")
    print("=" * 50)
    
    vn_path = find_test_vn()
    if not vn_path:
        return False
    
    try:
        # Test with regular parser
        print("📝 Testing regular parser...")
        project1 = RenpyProject(vn_path, use_hybrid_parser=False)
        overview1 = project1.analyze()
        
        print(f"Regular parser results:")
        print(f"   Labels: {overview1.total_labels}")
        print(f"   Characters: {overview1.total_characters}")
        print(f"   Menus: {overview1.total_menus}")
        
        # Test with hybrid parser
        print("\n🔄 Testing hybrid parser...")
        project2 = RenpyProject(vn_path, use_hybrid_parser=True)
        overview2 = project2.analyze()
        
        print(f"Hybrid parser results:")
        print(f"   Labels: {overview2.total_labels}")
        print(f"   Characters: {overview2.total_characters}")
        print(f"   Menus: {overview2.total_menus}")
        
        # Compare results
        print(f"\n📊 Comparison:")
        print(f"   Labels: {overview1.total_labels} → {overview2.total_labels} ({'+' if overview2.total_labels > overview1.total_labels else ''})")
        print(f"   Characters: {overview1.total_characters} → {overview2.total_characters} ({'+' if overview2.total_characters > overview1.total_characters else ''})")
        print(f"   Menus: {overview1.total_menus} → {overview2.total_menus} ({'+' if overview2.total_menus > overview1.total_menus else ''})")
        
        return True
    
    except Exception as e:
        print(f"❌ RenpyProject integration test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 SDK Integration Test Suite")
    print("=" * 60)
    
    tests = [
        ("SDK Analyzer", test_sdk_analyzer),
        ("Complexity Detector", test_complexity_detector),
        ("Hybrid Parser", test_hybrid_parser),
        ("RenpyProject Integration", test_renpy_project_integration),
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
    print("🏁 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:<10} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! SDK integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main() 