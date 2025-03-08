#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for the simplified database schema.

This script initializes the database and performs some basic operations to test the models.
"""

import os
import sys
from datetime import datetime

from app.db_schema_simple import initialize_database, Story, Character, StoryType


def main():
    """Test the database models."""
    print("Initializing database...")
    db = initialize_database('sqlite:///:memory:')  # Use in-memory database for testing
    
    # Create a session
    session = db.get_session()
    
    try:
        # Create a story
        print("Creating a test story...")
        story = Story(
            title="Test Story",
            description="A test story for database validation",
            type_name=StoryType.VISUAL_NOVEL.name,
            folder_path=os.path.join(os.getcwd(), "test_story"),
            universe="Test Universe",
            is_part_of_series=False,
            author="Test Author",
            year=2023
        )
        session.add(story)
        session.flush()
        
        # Create some characters
        print("Creating test characters...")
        john = Character(
            name="John Smith",
            aliases="Johnny, J",
            is_main_character=True,
            age_value=30,
            gender="MALE",
            story_id=story.id
        )
        session.add(john)
        
        jane = Character(
            name="Jane Doe",
            is_main_character=False,
            age_category="ADULT",
            gender="FEMALE",
            story_id=story.id
        )
        session.add(jane)
        
        # Commit the changes
        db.commit_session(session)
        print("Database test completed successfully!")
        
        # Print some information
        print(f"Story: {story.title} ({story.type_name})")
        print(f"Characters: {john.name}, {jane.name}")
        
        # Query the database
        all_characters = session.query(Character).all()
        print(f"Number of characters: {len(all_characters)}")
        for character in all_characters:
            print(f"Character: {character.name}, Gender: {character.gender}, Age: {character.age_display}")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback_session(session)
    finally:
        db.close_session(session)


if __name__ == "__main__":
    main() 