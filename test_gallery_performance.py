#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Performance testing script for gallery refresh optimizations.

This script measures the time taken for various gallery operations
to validate the performance improvements.
"""

import time
import sqlite3
import sys
import os
from typing import List, Dict, Any

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from db_sqlite import (
    get_image_character_tags, get_image_quick_events, get_story_characters,
    get_images_character_tags_batch, get_images_quick_events_batch
)


def measure_time(func, *args, **kwargs):
    """Measure execution time of a function."""
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    return result, end_time - start_time


def test_individual_queries(conn: sqlite3.Connection, story_id: int, image_ids: List[int]):
    """Test performance of individual database queries (old method)."""
    print(f"Testing individual queries for {len(image_ids)} images...")
    
    start_time = time.time()
    
    # Load characters for each image (simulating old behavior)
    for _ in image_ids:
        get_story_characters(conn, story_id)
    
    # Load character tags for each image
    for image_id in image_ids:
        get_image_character_tags(conn, image_id)
    
    # Load quick events for each image
    for image_id in image_ids:
        get_image_quick_events(conn, image_id)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"Individual queries took: {total_time:.3f} seconds")
    print(f"Average per image: {total_time / len(image_ids):.3f} seconds")
    return total_time


def test_batch_queries(conn: sqlite3.Connection, story_id: int, image_ids: List[int]):
    """Test performance of batch database queries (new method)."""
    print(f"Testing batch queries for {len(image_ids)} images...")
    
    start_time = time.time()
    
    # Load characters once
    get_story_characters(conn, story_id)
    
    # Batch load character tags
    get_images_character_tags_batch(conn, image_ids)
    
    # Batch load quick events
    get_images_quick_events_batch(conn, image_ids)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"Batch queries took: {total_time:.3f} seconds")
    print(f"Average per image: {total_time / len(image_ids):.3f} seconds")
    return total_time


def get_test_data(conn: sqlite3.Connection):
    """Get test data from the database."""
    cursor = conn.cursor()
    
    # Get a story with images
    cursor.execute("SELECT id FROM stories LIMIT 1")
    story_result = cursor.fetchone()
    if not story_result:
        print("No stories found in database")
        return None, []
    
    story_id = story_result[0]
    
    # Get images for this story
    cursor.execute("SELECT id FROM images WHERE story_id = ? LIMIT 100", (story_id,))
    image_results = cursor.fetchall()
    image_ids = [row[0] for row in image_results]
    
    print(f"Found story {story_id} with {len(image_ids)} images")
    return story_id, image_ids


def main():
    """Run performance tests."""
    # Connect to database
    db_path = "the_plot_thickens.db"
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    try:
        # Get test data
        story_id, image_ids = get_test_data(conn)
        if not story_id or not image_ids:
            print("No test data available")
            return
        
        print("=" * 60)
        print("GALLERY PERFORMANCE TEST")
        print("=" * 60)
        
        # Test individual queries (old method)
        individual_time = test_individual_queries(conn, story_id, image_ids)
        
        print()
        
        # Test batch queries (new method)
        batch_time = test_batch_queries(conn, story_id, image_ids)
        
        print()
        print("=" * 60)
        print("RESULTS")
        print("=" * 60)
        
        if individual_time > 0:
            improvement = (individual_time - batch_time) / individual_time * 100
            speedup = individual_time / batch_time if batch_time > 0 else float('inf')
            
            print(f"Individual queries: {individual_time:.3f} seconds")
            print(f"Batch queries:      {batch_time:.3f} seconds")
            print(f"Improvement:        {improvement:.1f}% faster")
            print(f"Speedup:            {speedup:.1f}x")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main() 