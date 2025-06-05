#!/usr/bin/env python3
"""
Test script to verify Video Conversion Lab setup
"""

import sys
import subprocess
import importlib

def test_python_version():
    """Test Python version"""
    print("Testing Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} - Need Python 3.10+")
        return False

def test_pyqt6():
    """Test PyQt6 installation"""
    print("\nTesting PyQt6 installation...")
    try:
        import PyQt6.QtWidgets
        import PyQt6.QtCore
        import PyQt6.QtGui
        import PyQt6.QtMultimedia
        import PyQt6.QtMultimediaWidgets
        print("✓ PyQt6 core modules - OK")
        
        # Test basic functionality
        app = PyQt6.QtWidgets.QApplication([])
        widget = PyQt6.QtWidgets.QWidget()
        app.quit()
        print("✓ PyQt6 basic functionality - OK")
        return True
    except ImportError as e:
        print(f"✗ PyQt6 import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ PyQt6 test failed: {e}")
        return False

def test_ffmpeg():
    """Test FFmpeg installation"""
    print("\nTesting FFmpeg installation...")
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            # Extract version info
            lines = result.stdout.split('\n')
            version_line = lines[0] if lines else "Unknown version"
            print(f"✓ FFmpeg found: {version_line}")
            
            # Check for required codecs
            codecs_to_check = ['libx264', 'libx265', 'libwebp', 'gif']
            print("  Checking codecs...")
            
            codec_result = subprocess.run(['ffmpeg', '-codecs'], 
                                        capture_output=True, text=True, timeout=10)
            codec_output = codec_result.stdout.lower()
            
            for codec in codecs_to_check:
                if codec in codec_output:
                    print(f"  ✓ {codec} - Available")
                else:
                    print(f"  ? {codec} - Not found (may still work)")
            
            return True
        else:
            print(f"✗ FFmpeg returned error code {result.returncode}")
            print(f"  Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("✗ FFmpeg test timed out")
        return False
    except FileNotFoundError:
        print("✗ FFmpeg not found in PATH")
        print("  Please install FFmpeg and add it to your system PATH")
        return False
    except Exception as e:
        print(f"✗ FFmpeg test failed: {e}")
        return False

def test_temp_directory():
    """Test temporary directory creation"""
    print("\nTesting temporary directory access...")
    try:
        import tempfile
        import os
        
        temp_dir = tempfile.mkdtemp(prefix="video_lab_test_")
        print(f"✓ Temporary directory created: {temp_dir}")
        
        # Test write access
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        
        # Clean up
        os.remove(test_file)
        os.rmdir(temp_dir)
        print("✓ Temporary directory write/cleanup - OK")
        return True
    except Exception as e:
        print(f"✗ Temporary directory test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Video Conversion Lab - Setup Test")
    print("=" * 40)
    
    tests = [
        test_python_version,
        test_pyqt6,
        test_ffmpeg,
        test_temp_directory
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 40)
    print("Test Summary:")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✓ All {total} tests passed! You're ready to use the Video Conversion Lab.")
        return 0
    else:
        print(f"✗ {total - passed} of {total} tests failed. Please fix the issues above.")
        print("\nInstallation help:")
        print("1. Install PyQt6: pip install PyQt6")
        print("2. Install FFmpeg: https://ffmpeg.org/download.html")
        print("3. Make sure FFmpeg is in your system PATH")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 