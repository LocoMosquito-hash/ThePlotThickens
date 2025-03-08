#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for the minimal database schema.

This script initializes the database and performs some basic operations to test the models.
"""

import os
import sys
from datetime import datetime

from app.db_schema_minimal import initialize_database, Story, StoryType, Character, Relationship, StoryBoardView


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
            folder_path=os.path.join(os.getcwd(), "test_story")
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
        
        # Create a relationship
        print("Creating relationships...")
        relationship = Relationship(
            source_id=john.id,
            target_id=jane.id,
            relationship_type="Friend",
            description="They are good friends",
            color="#00FF00",
            width=2.0
        )
        session.add(relationship)
        
        # Create a story board view
        print("Creating story board view...")
        view = StoryBoardView(
            name="Default View",
            description="The default story board view",
            layout_data='{"characters": [{"id": 1, "x": 100, "y": 100}, {"id": 2, "x": 300, "y": 100}], "relationships": [{"id": 1, "points": [[100, 100], [300, 100]]}]}',
            story_id=story.id
        )
        session.add(view)
        
        # Commit the changes
        db.commit_session(session)
        print("Database test completed successfully!")
        
        # Print some information
        print(f"Story: {story.title} ({story.type_name})")
        print(f"Characters: {john.name}, {jane.name}")
        print(f"Relationship: {john.name} is {relationship.relationship_type} of {jane.name}")
        print(f"Story Board View: {view.name}")
        
        # Test queries
        print("\nTesting queries...")
        
        # Get all characters for the story
        story_characters = session.query(Character).filter_by(story_id=story.id).all()
        print(f"Story has {len(story_characters)} characters")
        
        # Get all relationships for a character
        john_relationships = john.all_relationships
        print(f"{john.name} has {len(john_relationships)} relationships")
        
        # Get the layout of the story board view
        layout = view.layout
        print(f"Story Board View '{view.name}' has {len(layout['characters'])} characters and {len(layout['relationships'])} relationships")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback_session(session)
    finally:
        db.close_session(session)


if __name__ == "__main__":
    main() 