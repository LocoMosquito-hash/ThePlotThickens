#!/usr/bin/env python3
"""
Quick SDK Integration Test

This script tests the SDK integration using the tutorial project
included with the Ren'Py SDK.
"""

import os
import sys
from pathlib import Path

# Add current directory to path for imports
current_dir = str(Path(__file__).parent)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_sdk_integration():
    """Test the SDK integration with tutorial project."""
    print("🧪 Quick SDK Integration Test")
    print("=" * 50)
    
    try:
        from core import RenpyProject
        from sdk_integration import RenpySDKAnalyzer
        print("✅ Imports successful")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Find tutorial project
    sdk_dir = Path(__file__).parent / "renpy_sdk" / "renpy-8.4.0-sdk"
    tutorial_path = sdk_dir / "tutorial" / "game"
    
    print(f"📂 Looking for tutorial: {tutorial_path}")
    
    if not tutorial_path.exists():
        print("❌ Tutorial project not found")
        print("   The SDK might not be properly installed")
        return False
    
    print("✅ Tutorial project found")
    
    # Test SDK analyzer
    print("\n🔧 Testing SDK Analyzer...")
    try:
        analyzer = RenpySDKAnalyzer()
        print(f"   SDK Available: {analyzer.is_available}")
        
        if analyzer.is_available:
            result = analyzer.analyze_project(str(tutorial_path), verbose=True)
            if result.success:
                print("✅ SDK analysis successful!")
                if result.data:
                    project_info = result.data.get('project_info', {})
                    print(f"   Files: {project_info.get('rpy_files', 0)}")
                    print(f"   Labels: {project_info.get('total_labels', 0)}")
                    print(f"   Characters: {project_info.get('total_characters', 0)}")
            else:
                print(f"❌ SDK analysis failed: {result.error}")
        
    except Exception as e:
        print(f"❌ SDK test failed: {e}")
    
    # Test hybrid integration
    print("\n🔄 Testing Hybrid Integration...")
    try:
        # Regular parser
        project1 = RenpyProject(str(tutorial_path), use_hybrid_parser=False)
        overview1 = project1.analyze()
        print(f"   Regular: {overview1.total_labels} labels, {overview1.total_characters} characters")
        
        # Hybrid parser
        project2 = RenpyProject(str(tutorial_path), use_hybrid_parser=True)
        overview2 = project2.analyze()
        print(f"   Hybrid:  {overview2.total_labels} labels, {overview2.total_characters} characters")
        
        print("✅ Hybrid integration working!")
        
    except Exception as e:
        print(f"❌ Hybrid test failed: {e}")
    
    print("\n🎉 SDK integration test complete!")
    return True

if __name__ == "__main__":
    test_sdk_integration() 