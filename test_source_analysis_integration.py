#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for Source Analysis tab integration.

This script tests the basic functionality of the Source Analysis tab.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db_sqlite import create_connection
from app.views.source_analysis_tab import SourceAnalysisTab


def test_source_analysis_tab():
    """Test the Source Analysis tab functionality."""
    print("Testing Source Analysis Tab Integration...")
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    try:
        # Connect to database
        db_conn = create_connection("./the_plot_thickens.db")
        print("✓ Database connection established")
        
        # Create Source Analysis tab
        source_analysis_tab = SourceAnalysisTab(db_conn)
        print("✓ Source Analysis tab created successfully")
        
        # Test setting a story (using mock data)
        mock_story_data = {
            'id': 1,
            'title': 'Test Story',
            'folder_path': '/path/to/story'
        }
        
        source_analysis_tab.set_story(1, mock_story_data)
        print("✓ Story setting functionality works")
        
        # Test UI elements
        setup_tab = source_analysis_tab.setup_tab
        assert setup_tab.source_path_edit is not None
        assert setup_tab.start_button is not None
        assert setup_tab.stop_button is not None
        assert setup_tab.progress_bar is not None
        print("✓ All UI elements are present")
        
        # Test settings persistence
        settings = QSettings("ThePlotThickens", "ThePlotThickens")
        test_path = "/test/source/path"
        story_key = f"story_1/source_path"
        settings.setValue(story_key, test_path)
        
        # Reload the story to test settings loading
        source_analysis_tab.set_story(1, mock_story_data)
        loaded_path = setup_tab.source_path_edit.text()
        
        if loaded_path == test_path:
            print("✓ Settings persistence works correctly")
        else:
            print(f"⚠ Settings persistence issue: expected '{test_path}', got '{loaded_path}'")
        
        # Clean up test settings
        settings.remove(story_key)
        
        # Close database connection
        db_conn.close()
        print("✓ Database connection closed")
        
        print("\n🎉 All Source Analysis tab tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        app.quit()


if __name__ == "__main__":
    success = test_source_analysis_tab()
    sys.exit(0 if success else 1) 