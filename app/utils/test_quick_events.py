"""
Comprehensive test script for Quick Events utilities.

This script tests both character references and the QuickEventsManager.
"""

import sys
import os
import sqlite3
import traceback
from datetime import datetime

# Add the parent directory to sys.path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.utils.character_references import (
    convert_mentions_to_char_refs,
    convert_char_refs_to_mentions,
    extract_character_ids,
    find_mentioned_characters
)
from app.utils.quick_events_manager import QuickEventsManager


def test_character_references():
    """Test character reference conversion functions."""
    print("\n=== Testing Character References ===\n")
    
    # Sample character data
    characters = [
        {"id": 1, "name": "John Doe", "aliases": "Johnny, JD"},
        {"id": 2, "name": "Mary Smith", "aliases": ""},
        {"id": 3, "name": "Robert Johnson", "aliases": "Bob, Bobby"}
    ]
    
    # Test convert_mentions_to_char_refs
    test_text = "@John Doe met with @Mary Smith and discussed a project with @Robert Johnson"
    print(f"Original text: {test_text}")
    
    converted = convert_mentions_to_char_refs(test_text, characters)
    print(f"Converted to char refs: {converted}")
    
    # Test convert_char_refs_to_mentions
    back_converted = convert_char_refs_to_mentions(converted, characters)
    print(f"Converted back to mentions: {back_converted}")
    
    # Test extract_character_ids
    char_ids = extract_character_ids(converted)
    print(f"Extracted character IDs: {char_ids}")
    
    # Test find_mentioned_characters
    mentioned = find_mentioned_characters(test_text, characters)
    print("Mentioned characters:")
    for char in mentioned:
        print(f"  - {char['name']} (ID: {char['id']})")


def setup_test_db():
    """Set up an in-memory test database with the necessary tables."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    
    cursor = conn.cursor()
    
    # Create characters table
    cursor.execute('''
    CREATE TABLE characters (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        aliases TEXT,
        story_id INTEGER NOT NULL
    )
    ''')
    
    # Create quick_events table
    cursor.execute('''
    CREATE TABLE quick_events (
        id INTEGER PRIMARY KEY,
        created_at TEXT,
        updated_at TEXT,
        text TEXT NOT NULL,
        sequence_number INTEGER DEFAULT 0,
        character_id INTEGER NOT NULL,
        FOREIGN KEY (character_id) REFERENCES characters (id)
    )
    ''')
    
    # Create quick_event_characters table (for character tagging)
    cursor.execute('''
    CREATE TABLE quick_event_characters (
        id INTEGER PRIMARY KEY,
        created_at TEXT,
        updated_at TEXT,
        quick_event_id INTEGER NOT NULL,
        character_id INTEGER NOT NULL,
        FOREIGN KEY (quick_event_id) REFERENCES quick_events (id) ON DELETE CASCADE,
        FOREIGN KEY (character_id) REFERENCES characters (id) ON DELETE CASCADE
    )
    ''')
    
    # Create events table (for scenes)
    cursor.execute('''
    CREATE TABLE events (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        event_type TEXT NOT NULL,
        story_id INTEGER NOT NULL
    )
    ''')
    
    # Create scene_quick_events table
    cursor.execute('''
    CREATE TABLE scene_quick_events (
        id INTEGER PRIMARY KEY,
        created_at TEXT,
        updated_at TEXT,
        scene_event_id INTEGER NOT NULL,
        quick_event_id INTEGER NOT NULL,
        sequence_number INTEGER DEFAULT 0,
        FOREIGN KEY (scene_event_id) REFERENCES events (id) ON DELETE CASCADE,
        FOREIGN KEY (quick_event_id) REFERENCES quick_events (id) ON DELETE CASCADE,
        UNIQUE(scene_event_id, quick_event_id)
    )
    ''')
    
    # Create images table
    cursor.execute('''
    CREATE TABLE images (
        id INTEGER PRIMARY KEY,
        filename TEXT NOT NULL,
        story_id INTEGER NOT NULL
    )
    ''')
    
    # Create quick_event_images table
    cursor.execute('''
    CREATE TABLE quick_event_images (
        id INTEGER PRIMARY KEY,
        created_at TEXT,
        updated_at TEXT,
        quick_event_id INTEGER NOT NULL,
        image_id INTEGER NOT NULL,
        note TEXT,
        FOREIGN KEY (quick_event_id) REFERENCES quick_events (id) ON DELETE CASCADE,
        FOREIGN KEY (image_id) REFERENCES images (id) ON DELETE CASCADE
    )
    ''')
    
    # Add some test characters
    cursor.executemany('''
    INSERT INTO characters (id, name, aliases, story_id) VALUES (?, ?, ?, ?)
    ''', [
        (1, 'John Doe', 'Johnny, JD', 1),
        (2, 'Mary Smith', '', 1),
        (3, 'Robert Johnson', 'Bob, Bobby', 1)
    ])
    
    # Add a test scene
    cursor.execute('''
    INSERT INTO events (id, title, event_type, story_id) VALUES (?, ?, ?, ?)
    ''', (1, 'Test Scene', 'SCENE', 1))
    
    # Add a test image
    cursor.execute('''
    INSERT INTO images (id, filename, story_id) VALUES (?, ?, ?)
    ''', (1, 'test.jpg', 1))
    
    conn.commit()
    
    return conn


def test_quick_events_manager():
    """Test the QuickEventsManager class."""
    print("\n=== Testing QuickEventsManager ===\n")
    
    try:
        print("Setting up test database...")
        conn = setup_test_db()
        
        # Create a quick events manager
        manager = QuickEventsManager(conn)
        
        # Test creating a quick event
        print("\n1. Testing create_quick_event:")
        try:
            qe_id = manager.create_quick_event('@John Doe met with @Mary Smith', 1)
            print(f"   Created quick event with ID: {qe_id}")
        except Exception as e:
            print(f"   Error creating quick event: {e}")
            traceback.print_exc()
            return
        
        # Test getting a quick event
        print("\n2. Testing get_quick_event:")
        try:
            qe = manager.get_quick_event(qe_id)
            print(f"   Quick event text: {qe.get('text')}")
        except Exception as e:
            print(f"   Error getting quick event: {e}")
            traceback.print_exc()
        
        # Test getting character's quick events
        print("\n3. Testing get_character_quick_events:")
        try:
            char_events = manager.get_character_quick_events(1)
            print(f"   Character's quick events count: {len(char_events)}")
            if char_events:
                print(f"   First event text: {char_events[0].get('text')}")
        except Exception as e:
            print(f"   Error getting character quick events: {e}")
            traceback.print_exc()
        
        # Test getting quick event tagged characters
        print("\n4. Testing get_quick_event_tagged_characters:")
        try:
            tagged_chars = manager.get_quick_event_tagged_characters(qe_id)
            print(f"   Tagged characters count: {len(tagged_chars)}")
            for char in tagged_chars:
                print(f"   - {char['name']} (ID: {char['id']})")
        except Exception as e:
            print(f"   Error getting tagged characters: {e}")
            traceback.print_exc()
        
        # Test updating a quick event
        print("\n5. Testing update_quick_event:")
        try:
            updated = manager.update_quick_event(qe_id, '@John Doe met with @Mary Smith and @Robert Johnson')
            print(f"   Update successful: {updated}")
            
            # Get the updated text
            qe = manager.get_quick_event(qe_id)
            print(f"   Updated text: {qe.get('text')}")
            
            # Check that the tagged characters were updated
            tagged_chars = manager.get_quick_event_tagged_characters(qe_id)
            print(f"   Tagged characters after update count: {len(tagged_chars)}")
            for char in tagged_chars:
                print(f"   - {char['name']} (ID: {char['id']})")
        except Exception as e:
            print(f"   Error updating quick event: {e}")
            traceback.print_exc()
        
        # Test associating with a scene
        print("\n6. Testing associate_quick_event_with_scene:")
        try:
            associated = manager.associate_quick_event_with_scene(qe_id, 1)
            print(f"   Association successful: {associated}")
        except Exception as e:
            print(f"   Error associating quick event with scene: {e}")
            traceback.print_exc()
        
        # Test getting scene quick events
        print("\n7. Testing get_scene_quick_events:")
        try:
            scene_events = manager.get_scene_quick_events(1)
            print(f"   Scene quick events count: {len(scene_events)}")
            if scene_events:
                print(f"   First scene event text: {scene_events[0].get('text')}")
        except Exception as e:
            print(f"   Error getting scene quick events: {e}")
            traceback.print_exc()
        
        # Test removing from scene
        print("\n8. Testing remove_quick_event_from_scene:")
        try:
            removed = manager.remove_quick_event_from_scene(qe_id, 1)
            print(f"   Removal successful: {removed}")
        except Exception as e:
            print(f"   Error removing quick event from scene: {e}")
            traceback.print_exc()
        
        # Test deleting a quick event
        print("\n9. Testing delete_quick_event:")
        try:
            deleted = manager.delete_quick_event(qe_id)
            print(f"   Delete successful: {deleted}")
        except Exception as e:
            print(f"   Error deleting quick event: {e}")
            traceback.print_exc()
        
        # Close the connection
        conn.close()
        
        print("\nAll QuickEventsManager tests completed successfully.")
    except Exception as e:
        print(f"Test failed with error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    print("=== Quick Events Utility Tests ===\n")
    
    # Test character references
    test_character_references()
    
    # Test Quick Events Manager
    test_quick_events_manager()
    
    print("\n=== All tests completed ===") 