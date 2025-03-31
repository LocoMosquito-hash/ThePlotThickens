#!/usr/bin/env python3
"""
Test script to verify that quick events work with optional character_id.
"""

import sqlite3
import os
from typing import Dict, List, Any, Optional
import tempfile

from app.utils.quick_events_manager import QuickEventsManager
from app.utils.character_references import convert_char_refs_to_mentions

def create_test_database() -> sqlite3.Connection:
    """Create a test database with the updated schema."""
    # Create a temporary database in memory
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON")
    
    # Create the tables
    conn.executescript('''
    -- Create characters table
    CREATE TABLE characters (
        id INTEGER PRIMARY KEY,
        created_at TEXT,
        updated_at TEXT,
        name TEXT NOT NULL,
        aliases TEXT,
        story_id INTEGER NOT NULL,
        is_main_character INTEGER DEFAULT 0,
        age_value INTEGER,
        age_category TEXT,
        gender TEXT DEFAULT 'NOT_SPECIFIED',
        avatar_path TEXT
    );
    
    -- Create quick_events table with optional character_id
    CREATE TABLE quick_events (
        id INTEGER PRIMARY KEY,
        created_at TEXT,
        updated_at TEXT,
        text TEXT NOT NULL,
        sequence_number INTEGER DEFAULT 0,
        character_id INTEGER,
        FOREIGN KEY (character_id) REFERENCES characters (id)
    );
    
    -- Create quick_event_characters table
    CREATE TABLE quick_event_characters (
        id INTEGER PRIMARY KEY,
        created_at TEXT,
        updated_at TEXT,
        quick_event_id INTEGER NOT NULL,
        character_id INTEGER NOT NULL,
        FOREIGN KEY (quick_event_id) REFERENCES quick_events (id),
        FOREIGN KEY (character_id) REFERENCES characters (id)
    );
    
    -- Create scene_quick_events table
    CREATE TABLE scene_quick_events (
        id INTEGER PRIMARY KEY,
        created_at TEXT,
        updated_at TEXT,
        scene_event_id INTEGER NOT NULL,
        quick_event_id INTEGER NOT NULL,
        sequence_number INTEGER DEFAULT 0,
        UNIQUE(scene_event_id, quick_event_id)
    );
    ''')
    
    # Insert test data
    conn.executescript('''
    -- Insert a test story
    INSERT INTO characters (id, name, aliases, story_id, is_main_character)
    VALUES 
        (1, 'John Smith', 'JS, Johnny', 1, 1),
        (2, 'Mary Johnson', 'MJ', 1, 1),
        (3, 'Robert Williams', 'Bob', 1, 0);
    ''')
    
    conn.commit()
    return conn

def test_create_quick_event_with_character() -> bool:
    """
    Test creating a quick event with a character.
    
    Returns:
        True if the test passed, False otherwise
    """
    conn = create_test_database()
    manager = QuickEventsManager(conn)
    
    # Create a quick event with a character
    text = "John did something important"
    character_id = 1
    qe_id = manager.create_quick_event(text, character_id)
    
    # Get the quick event
    qe = manager.get_quick_event(qe_id)
    
    # Verify the quick event has the correct character_id
    passed = qe and qe['character_id'] == character_id
    
    if passed:
        print("✓ Test passed: Created quick event with character")
    else:
        print("✗ Test failed: Quick event with character")
        
    return passed

def test_create_quick_event_without_character() -> bool:
    """
    Test creating a quick event without a character.
    
    Returns:
        True if the test passed, False otherwise
    """
    conn = create_test_database()
    manager = QuickEventsManager(conn)
    
    # Create a quick event without a character
    text = "The door opened slowly"
    qe_id = manager.create_quick_event(text)
    
    # Get the quick event
    qe = manager.get_quick_event(qe_id)
    
    # Verify the quick event has NULL character_id
    passed = qe and qe['character_id'] is None
    
    if passed:
        print("✓ Test passed: Created quick event without character")
    else:
        print("✗ Test failed: Quick event without character")
        
    return passed

def test_character_mentions_in_characterless_event() -> bool:
    """
    Test that character mentions work in events without an owner character.
    
    Returns:
        True if the test passed, False otherwise
    """
    conn = create_test_database()
    manager = QuickEventsManager(conn)
    
    # Create a quick event with character mentions but no owner
    text = "@John Smith met with @Mary Johnson"
    qe_id = manager.create_quick_event(text)
    
    # Get the quick event tagged characters
    tagged_chars = manager.get_quick_event_tagged_characters(qe_id)
    
    # Verify that it found the mentioned characters
    passed = len(tagged_chars) == 2
    
    if passed:
        print("✓ Test passed: Character mentions in characterless event")
    else:
        print("✗ Test failed: Character mentions in characterless event")
        
    return passed

def main():
    """Run all the tests."""
    print("Testing quick events with optional character_id...\n")
    
    tests = [
        test_create_quick_event_with_character,
        test_create_quick_event_without_character,
        test_character_mentions_in_characterless_event
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n{passed}/{len(tests)} tests passed")

if __name__ == "__main__":
    main() 