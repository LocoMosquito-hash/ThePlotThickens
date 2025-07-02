#!/usr/bin/env python3
"""
Test script for the Ren'Py Source API.

This script allows testing the Ren'Py analysis functionality with a hardcoded
test VN path. You can modify the TEST_VN_PATH constant to point to your
decompiled Ren'Py game folder.

Usage:
    python test_renpy_api.py
"""

import os
import sys
import sqlite3
import json
from pathlib import Path

# Add the parent directory to the path so we can import the app modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import configuration
from config import get_test_vn_path, list_available_vns, validate_vn_path

def test_basic_functionality():
    """Test basic Ren'Py API functionality."""
    print("=" * 60)
    print("REN'PY SOURCE API TEST")
    print("=" * 60)
    
    # Get test VN path from configuration
    try:
        test_vn_path = get_test_vn_path()
        available_vns = list_available_vns()
        
        print(f"📁 Available VNs: {len(available_vns)}")
        for name, path in available_vns.items():
            print(f"   • {name}: {path}")
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("\n📝 To use this test script:")
        print("1. Edit config.py")
        print("2. Change TEST_VN_PATH to point to your decompiled Ren'Py game folder")
        print("3. Make sure the path points to the 'game' folder containing .rpy files")
        print("\nExample paths:")
        print("  Windows: r'C:\\Games\\RenPy\\MyVN\\game'")
        print("  Linux:   '/home/user/games/MyVN/game'")
        print("  macOS:   '/Users/username/games/MyVN/game'")
        return False
    
    # Validate the test path
    is_valid, message = validate_vn_path(test_vn_path)
    if not is_valid:
        print(f"❌ {message}")
        print(f"\nPlease update config.py with a valid Ren'Py game folder path.")
        return False
    
    print(f"📁 Testing with VN path: {test_vn_path}")
    print(f"✅ {message}")
    
    try:
        # Import our API
        print("📦 Importing Ren'Py API...")
        
        # Add current directory to path for imports
        current_dir = str(Path(__file__).parent)
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        from core import RenpyProject
        from parser import RenpyParser
        from exceptions import RenpyProjectError, RenpyAnalysisError
        
        # Test 1: Basic project initialization
        print("\n🔧 Test 1: Project Initialization")
        print("-" * 30)
        
        try:
            project = RenpyProject(test_vn_path)
            print(f"✅ Project created successfully")
            print(f"   Path: {project.project_path}")
        except RenpyProjectError as e:
            print(f"❌ Project initialization failed: {e}")
            return False
        
        # Test 2: Project analysis
        print("\n📊 Test 2: Project Analysis")
        print("-" * 30)
        
        try:
            overview = project.analyze()
            print("✅ Analysis completed successfully")
            print(f"   📄 .rpy files: {overview.total_rpy_files}")
            print(f"   📝 Total lines: {overview.total_lines}")
            print(f"   💬 Dialogue lines: {overview.total_dialogue_lines}")
            print(f"   🏷️  Labels: {overview.total_labels}")
            print(f"   📋 Menus: {overview.total_menus}")
            print(f"   👥 Characters: {overview.total_characters}")
            
            if overview.errors:
                print(f"   ⚠️  Errors: {len(overview.errors)}")
                for i, error in enumerate(overview.errors[:3]):
                    print(f"     {i+1}. {error}")
                if len(overview.errors) > 3:
                    print(f"     ... and {len(overview.errors) - 3} more")
        
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            return False
        
        # Test 3: Project overview
        print("\n📋 Test 3: Project Overview")
        print("-" * 30)
        
        try:
            overview_data = project.get_project_overview()
            print("✅ Project overview retrieved")
            print(f"   📁 Files found: {len(overview_data['files'])}")
            
            # Show first few files
            if overview_data['files']:
                print("   📄 Sample files:")
                for file in overview_data['files'][:5]:
                    print(f"     • {file}")
                if len(overview_data['files']) > 5:
                    print(f"     • ... and {len(overview_data['files']) - 5} more")
            
        except Exception as e:
            print(f"❌ Overview retrieval failed: {e}")
            return False
        
        # Test 4: Character definitions
        print("\n👥 Test 4: Character Definitions")
        print("-" * 30)
        
        try:
            char_stats = project.get_character_stats()
            print(f"✅ Character stats retrieved")
            print(f"   👤 Characters found: {len(char_stats)}")
            
            if char_stats:
                print("   📝 Character definitions:")
                for code, info in list(char_stats.items())[:5]:
                    print(f"     • {code} = \"{info['name']}\"")
                if len(char_stats) > 5:
                    print(f"     • ... and {len(char_stats) - 5} more")
            else:
                print("   ℹ️  No character definitions found (this is normal for some VNs)")
        
        except Exception as e:
            print(f"❌ Character stats failed: {e}")
            return False
        
        # Test 5: Labels
        print("\n🏷️  Test 5: Labels")
        print("-" * 30)
        
        try:
            labels = project.get_labels()
            print(f"✅ Labels retrieved")
            print(f"   🔖 Labels found: {len(labels)}")
            
            if labels:
                print("   📝 Sample labels:")
                for label in labels[:10]:
                    print(f"     • {label}")
                if len(labels) > 10:
                    print(f"     • ... and {len(labels) - 10} more")
        
        except Exception as e:
            print(f"❌ Label retrieval failed: {e}")
            return False
        
        # Test 6: Dialogue search
        print("\n🔍 Test 6: Dialogue Search")
        print("-" * 30)
        
        try:
            # Search for a common word
            search_results = project.search_dialogue("the", case_sensitive=False)
            print(f"✅ Dialogue search completed")
            print(f"   🔍 Results for 'the': {len(search_results)} matches")
            
            if search_results:
                print("   📝 Sample matches:")
                for result in search_results[:3]:
                    speaker = result['speaker'] or 'narrator'
                    dialogue = result['dialogue'][:50] + "..." if len(result['dialogue']) > 50 else result['dialogue']
                    print(f"     • {speaker}: \"{dialogue}\" ({result['file']}:{result['line_number']})")
                if len(search_results) > 3:
                    print(f"     • ... and {len(search_results) - 3} more matches")
        
        except Exception as e:
            print(f"❌ Dialogue search failed: {e}")
            return False
        
        # Test 7: Database integration (basic)
        print("\n💾 Test 7: Database Integration")
        print("-" * 30)
        
        try:
            # Create a temporary in-memory database for testing
            test_db = sqlite3.connect(":memory:")
            test_db.row_factory = sqlite3.Row
            
            # Create a minimal stories table for testing
            cursor = test_db.cursor()
            cursor.execute('''
            CREATE TABLE stories (
                id INTEGER PRIMARY KEY,
                title TEXT,
                folder_path TEXT
            )
            ''')
            
            # Insert a test story
            cursor.execute('''
            INSERT INTO stories (title, folder_path)
            VALUES (?, ?)
            ''', ("Test VN", test_vn_path))
            
            test_story_id = cursor.lastrowid
            test_db.commit()
            
            # Test database integration
            project_with_db = RenpyProject(test_vn_path, test_db)
            if test_story_id is not None:
                project_with_db.link_to_story(test_story_id)
            
            print("✅ Database integration working")
            print(f"   🔗 Linked to story ID: {test_story_id}")
            
            test_db.close()
        
        except Exception as e:
            print(f"❌ Database integration failed: {e}")
            return False
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED! Ren'Py API is working correctly.")
        print("=" * 60)
        print("\n📈 Summary:")
        print(f"   • Successfully analyzed {overview.total_rpy_files} .rpy files")
        print(f"   • Found {overview.total_dialogue_lines} dialogue lines")
        print(f"   • Discovered {overview.total_characters} character definitions")
        print(f"   • Identified {overview.total_labels} labels")
        print(f"   • Detected {overview.total_menus} menus")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're running this from the correct directory")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def export_sample_data():
    """Export sample analysis data to JSON for inspection."""
    print("\n📤 Exporting sample data...")
    
    try:
        # Add current directory to path for imports (if not already done)
        current_dir = str(Path(__file__).parent)
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
            
        from core import RenpyProject
        
        # Get the test VN path
        test_vn_path = get_test_vn_path()
        project = RenpyProject(test_vn_path)
        overview_data = project.get_project_overview()
        
        # Export to JSON file
        output_file = "renpy_analysis_sample.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(overview_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Sample data exported to: {output_file}")
        print("   You can inspect this file to see the analysis structure")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")


if __name__ == "__main__":
    print("Starting Ren'Py API tests...\n")
    
    # Run the tests
    success = test_basic_functionality()
    
    if success:
        # Ask if user wants to export sample data
        try:
            response = input("\n❓ Export sample analysis data to JSON? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                export_sample_data()
        except KeyboardInterrupt:
            print("\n\n👋 Test completed!")
    
    else:
        print("\n💡 Tips for troubleshooting:")
        print("1. Make sure TEST_VN_PATH points to a valid Ren'Py 'game' folder")
        print("2. Check that the folder contains .rpy files")
        print("3. Verify the path format is correct for your operating system")
        print("4. Try with a simple/small VN first to test the functionality")
    
    print("\n🔚 Test script finished.") 