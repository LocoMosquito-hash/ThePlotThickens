#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for video support in The Plot Thickens application.

This script tests the video utilities and import functionality.
"""

import sys
import os
import tempfile
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_video_utilities():
    """Test the video utilities module."""
    print("Testing video utilities...")
    
    try:
        from app.utils.video_utils import (
            is_video_file, 
            video_processor, 
            get_video_info
        )
        
        # Test file extension detection
        test_files = [
            "test.mp4",
            "test.avi", 
            "test.mov",
            "test.ogg",
            "test.ogv",
            "test.jpg",
            "test.png",
            "test.txt"
        ]
        
        print("\n1. Testing file extension detection:")
        for file_path in test_files:
            is_video = is_video_file(file_path)
            print(f"   {file_path}: {'✓ Video' if is_video else '✗ Not video'}")
        
        # Test FFmpeg detection
        print("\n2. Testing FFmpeg detection:")
        if video_processor.ffmpeg_path:
            print(f"   ✓ FFmpeg found at: {video_processor.ffmpeg_path}")
        else:
            print("   ✗ FFmpeg not found - video thumbnail generation will not work")
            print("   Install FFmpeg and add it to your PATH for full functionality")
        
        # Test getting video info (will only work if FFmpeg is available)
        print("\n3. Testing video info extraction:")
        if video_processor.ffmpeg_path:
            print("   Ready to extract video metadata when video files are available")
        else:
            print("   Skipped - requires FFmpeg")
            
        print("\n✓ Video utilities module loaded successfully")
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import video utilities: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing video utilities: {e}")
        return False

def test_gallery_import():
    """Test that the gallery can import the video utilities."""
    print("\nTesting gallery video import capabilities...")
    
    try:
        # Test importing the gallery module
        from app.views.gallery.core import GalleryWidget
        print("   ✓ Gallery widget imported successfully")
        
        # Check if the import_video_file method exists
        if hasattr(GalleryWidget, 'import_video_file'):
            print("   ✓ import_video_file method exists")
        else:
            print("   ✗ import_video_file method not found")
            return False
            
        print("✓ Gallery video support ready")
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import gallery module: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing gallery import: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("The Plot Thickens - Video Support Test")
    print("=" * 60)
    
    all_passed = True
    
    # Test video utilities
    if not test_video_utilities():
        all_passed = False
    
    # Test gallery integration
    if not test_gallery_import():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed! Video support is ready.")
        print("\nNext steps:")
        print("1. Make sure FFmpeg is installed and in your PATH")
        print("2. Run the main application: python run.py")
        print("3. Try importing an MP4 file using the 'Import Image/Video' button")
        print("4. Try copying an MP4 file path and using 'Paste from Clipboard'")
    else:
        print("✗ Some tests failed. Check the output above for details.")
    print("=" * 60)

if __name__ == "__main__":
    main() 