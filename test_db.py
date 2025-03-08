#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for The Plot Thickens database.

This script initializes the database and performs some basic operations to test the models.
"""

import os
import sys
from datetime import datetime

from app.utils.db import initialize_database
from app.models import (
    Story, StoryType, Character, CharacterTrait, CharacterDetail, CharacterGroup,
    Relationship, RelationshipType, Image, ImageTag, Event, EventCharacter,
    AgeCategory, Gender, StoryBoardView
)


def main():
    """Test the database models."""
    print("Initializing database...")
    db = initialize_database()
    
    # Create a session
    session = db.get_session()
    
    try:
        # Create a story
        print("Creating a test story...")
        story = Story(
            title="Test Story",
            description="A test story for database validation",
            type=StoryType.VISUAL_NOVEL,
            folder_path=os.path.join(os.getcwd(), "test_story"),
            universe="Test Universe",
            is_part_of_series=False,
            author="Test Author",
            year=2023
        )
        session.add(story)
        session.flush()
        
        # Ensure folders exist
        story.ensure_folders_exist()
        
        # Create some characters
        print("Creating test characters...")
        john = Character(
            name="John Smith",
            aliases="Johnny, J",
            is_main_character=True,
            age_value=30,
            gender=Gender.MALE,
            story_id=story.id
        )
        session.add(john)
        
        jane = Character(
            name="Jane Doe",
            is_main_character=False,
            age_category=AgeCategory.ADULT,
            gender=Gender.FEMALE,
            story_id=story.id
        )
        session.add(jane)
        
        # Create a character trait
        print("Creating character traits...")
        brave = CharacterTrait(name="Brave", description="Shows courage in difficult situations")
        session.add(brave)
        
        # Add trait to character
        john.traits.append(brave)
        
        # Create a character detail
        print("Creating character details...")
        detail = CharacterDetail(key="Favorite Color", value="Blue", character_id=john.id)
        session.add(detail)
        
        # Create a character group
        print("Creating character groups...")
        group = CharacterGroup(name="Test Team", description="A team for testing", story_id=story.id)
        session.add(group)
        session.flush()
        
        # Add characters to group
        john.groups.append(group)
        jane.groups.append(group)
        
        # Create a relationship
        print("Creating relationships...")
        # Get the "Friend" relationship type
        friend_type = session.query(RelationshipType).filter_by(name="Friend").first()
        
        relationship = Relationship(
            source_id=john.id,
            target_id=jane.id,
            relationship_type_id=friend_type.id,
            description="They are good friends",
            color="#00FF00",
            width=2.0
        )
        session.add(relationship)
        
        # Create an event
        print("Creating events...")
        event = Event(
            title="First Meeting",
            description="John and Jane meet for the first time",
            date=datetime.now(),
            story_id=story.id
        )
        session.add(event)
        session.flush()
        
        # Add characters to event
        john_event = EventCharacter(
            event_id=event.id,
            character_id=john.id,
            role="Protagonist",
            description="John initiates the meeting"
        )
        session.add(john_event)
        
        jane_event = EventCharacter(
            event_id=event.id,
            character_id=jane.id,
            role="Deuteragonist",
            description="Jane responds to John's greeting"
        )
        session.add(jane_event)
        
        # Create an image
        print("Creating images...")
        image = Image(
            filename="test_image.jpg",
            path=story.images_folder,
            title="Test Image",
            description="A test image",
            width=800,
            height=600,
            file_size=1024,
            mime_type="image/jpeg",
            is_featured=True,
            date_taken=datetime.now(),
            story_id=story.id,
            event_id=event.id
        )
        session.add(image)
        session.flush()
        
        # Tag characters in the image
        john_tag = ImageTag(
            image_id=image.id,
            character_id=john.id,
            x=0.2,
            y=0.3,
            width=0.1,
            height=0.2
        )
        session.add(john_tag)
        
        jane_tag = ImageTag(
            image_id=image.id,
            character_id=jane.id,
            x=0.6,
            y=0.3,
            width=0.1,
            height=0.2
        )
        session.add(jane_tag)
        
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
        print(f"Story: {story.title} ({story.type})")
        print(f"Characters: {john.name}, {jane.name}")
        print(f"Relationship: {john.name} is {relationship.relationship_type.name} of {jane.name}")
        print(f"Event: {event.title} on {event.date_display}")
        print(f"Image: {image.title} ({image.width}x{image.height})")
        print(f"Story Board View: {view.name}")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback_session(session)
    finally:
        db.close_session(session)


if __name__ == "__main__":
    main() 