#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for the SQLite database.

This script initializes the database and performs some basic operations to test the functions.
"""

import os
import sys
import json
from datetime import datetime

from app.db_sqlite import (
    initialize_database, StoryType,
    create_story, get_story, get_all_stories,
    create_character, get_character, get_story_characters,
    create_relationship, get_character_relationships,
    create_story_board_view, get_story_board_views, get_story_board_view, update_story_board_view_layout
)


def main():
    """Test the database functions."""
    print("Initializing database...")
    # Use an in-memory database for testing
    conn = initialize_database(":memory:")
    
    try:
        # Create a story
        print("Creating a test story...")
        story_id = create_story(
            conn,
            title="Test Story",
            description="A test story for database validation",
            type_name=StoryType.VISUAL_NOVEL.name,
            folder_path=os.path.join(os.getcwd(), "test_story")
        )
        
        # Get the story
        story = get_story(conn, story_id)
        print(f"Created story: {story['title']} ({story['type_name']})")
        
        # Create some characters
        print("Creating test characters...")
        john_id = create_character(
            conn,
            name="John Smith",
            story_id=story_id,
            aliases="Johnny, J",
            is_main_character=True,
            age_value=30,
            gender="MALE"
        )
        
        jane_id = create_character(
            conn,
            name="Jane Doe",
            story_id=story_id,
            is_main_character=False,
            age_category="ADULT",
            gender="FEMALE"
        )
        
        # Get the characters
        john = get_character(conn, john_id)
        jane = get_character(conn, jane_id)
        print(f"Created characters: {john['name']}, {jane['name']}")
        
        # Create a relationship
        print("Creating relationships...")
        relationship_id = create_relationship(
            conn,
            source_id=john_id,
            target_id=jane_id,
            relationship_type="Friend",
            description="They are good friends",
            color="#00FF00",
            width=2.0
        )
        
        # Get the relationships
        john_relationships = get_character_relationships(conn, john_id)
        print(f"{john['name']} has {len(john_relationships)} relationships")
        
        # Create a story board view
        print("Creating story board view...")
        layout_data = json.dumps({
            "characters": [
                {"id": john_id, "x": 100, "y": 100},
                {"id": jane_id, "x": 300, "y": 100}
            ],
            "relationships": [
                {"id": relationship_id, "points": [[100, 100], [300, 100]]}
            ]
        })
        
        view_id = create_story_board_view(
            conn,
            name="Default View",
            story_id=story_id,
            layout_data=layout_data,
            description="The default story board view"
        )
        
        # Get the story board view
        view = get_story_board_view(conn, view_id)
        print(f"Created story board view: {view['name']}")
        
        # Parse the layout data
        layout = json.loads(view['layout_data'])
        print(f"Story Board View '{view['name']}' has {len(layout['characters'])} characters and {len(layout['relationships'])} relationships")
        
        # Update the layout
        print("Updating story board view layout...")
        new_layout = json.loads(layout_data)
        new_layout["characters"][0]["x"] = 150  # Move John a bit to the right
        update_story_board_view_layout(conn, view_id, json.dumps(new_layout))
        
        # Get the updated view
        updated_view = get_story_board_view(conn, view_id)
        updated_layout = json.loads(updated_view['layout_data'])
        print(f"Updated {john['name']}'s position to x={updated_layout['characters'][0]['x']}")
        
        # Test queries
        print("\nTesting queries...")
        
        # Get all stories
        stories = get_all_stories(conn)
        print(f"Database has {len(stories)} stories")
        
        # Get all characters for the story
        story_characters = get_story_characters(conn, story_id)
        print(f"Story has {len(story_characters)} characters")
        
        # Get all story board views for the story
        views = get_story_board_views(conn, story_id)
        print(f"Story has {len(views)} story board views")
        
        print("Database test completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    main() 