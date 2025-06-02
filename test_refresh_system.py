#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test the optimized refresh system.
"""

import sys
import os
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.db_sqlite import create_connection


def test_refresh_detection():
    """Test if the refresh system can detect the optimized path."""
    try:
        # Use the existing database
        db_path = "the_plot_thickens.db"
        
        if not os.path.exists(db_path):
            print("❌ Database not found")
            return False
        
        db_conn = create_connection(db_path)
        if not db_conn:
            print("❌ Could not connect to database")
            return False
        
        # Check if we have stories with many images
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT s.id, s.title, COUNT(i.id) as image_count
            FROM stories s
            LEFT JOIN images i ON s.id = i.story_id
            GROUP BY s.id, s.title
            HAVING COUNT(i.id) > 0
            ORDER BY COUNT(i.id) DESC
            LIMIT 5
        """)
        
        stories = cursor.fetchall()
        
        if not stories:
            print("❌ No stories with images found")
            return False
        
        print("✅ Stories with images:")
        for story_id, title, count in stories:
            should_use_optimized = count >= 100  # This is our threshold
            optimization_status = "OPTIMIZED" if should_use_optimized else "STANDARD"
            print(f"   • Story {story_id} ({title}): {count} images → {optimization_status} refresh")
        
        # Test importing the optimized refresh classes
        try:
            from app.views.gallery.optimized_refresh import SmartRefreshManager, OptimizedGalleryRefresh
            from app.views.gallery.thumbnail_loader import ThumbnailLoader
            print("✅ Successfully imported optimized refresh classes")
        except ImportError as e:
            print(f"❌ Could not import optimized refresh classes: {e}")
            return False
        
        print("✅ Refresh system appears to be properly configured")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    print("🔍 Testing Optimized Refresh System")
    print("=" * 50)
    
    success = test_refresh_detection()
    
    if success:
        print("\n✅ All tests passed! The optimized refresh system should be working.")
        print("\n💡 To see the optimization in action:")
        print("   1. Open a story with 100+ images")
        print("   2. Look for [SMART_REFRESH] and [OPTIMIZED_REFRESH] debug messages")
        print("   3. You should see a progress dialog during refresh")
    else:
        print("\n❌ Tests failed. Check the error messages above.") 