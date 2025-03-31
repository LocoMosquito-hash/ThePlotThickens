"""
Test script for character_references.py.

This script tests the character reference functions to ensure they work properly.
"""

import sys
import os
import sqlite3

# Add the parent directory to sys.path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.utils.character_references import (
    convert_mentions_to_char_refs,
    convert_char_refs_to_mentions,
    extract_character_ids,
    find_mentioned_characters,
    process_char_refs_from_db
)


def test_character_references():
    """Test character reference conversion functions."""
    # Sample character data
    characters = [
        {"id": 1, "name": "John Doe", "aliases": "Johnny, JD"},
        {"id": 2, "name": "Mary Smith", "aliases": ""},
        {"id": 3, "name": "Robert Johnson", "aliases": "Bob, Bobby"}
    ]
    
    # Test convert_mentions_to_char_refs
    test_texts = [
        "@John Doe went to the store",
        "@Johnny and @Mary Smith went hiking",
        "Meeting between @John Doe and @Robert Johnson",
        "No mentions here",
        "@Unknown person not in the list"
    ]
    
    print("Testing convert_mentions_to_char_refs:")
    for text in test_texts:
        converted = convert_mentions_to_char_refs(text, characters)
        print(f"Original: {text}")
        print(f"Converted: {converted}")
        print()
    
    # Test convert_char_refs_to_mentions
    ref_texts = [
        "[char:1] went to the store",
        "[char:1] and [char:2] went hiking",
        "Meeting between [char:1] and [char:3]",
        "No references here",
        "[char:999] unknown ID"
    ]
    
    print("Testing convert_char_refs_to_mentions:")
    for text in ref_texts:
        converted = convert_char_refs_to_mentions(text, characters)
        print(f"Original: {text}")
        print(f"Converted: {converted}")
        print()
    
    # Test extract_character_ids
    ref_text = "Meeting between [char:1], [char:2] and [char:3]"
    char_ids = extract_character_ids(ref_text)
    print(f"Extracted character IDs from '{ref_text}': {char_ids}")
    
    # Test find_mentioned_characters
    mention_text = "@John Doe and @Mary Smith had a meeting"
    mentioned = find_mentioned_characters(mention_text, characters)
    print(f"Mentioned characters in '{mention_text}':")
    for char in mentioned:
        print(f"  - {char['name']} (ID: {char['id']})")


def setup_test_db():
    """Set up an in-memory test database."""
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
    
    # Add some test data
    cursor.executemany('''
    INSERT INTO characters (id, name, aliases, story_id) VALUES (?, ?, ?, ?)
    ''', [
        (1, 'John Doe', 'Johnny, JD', 1),
        (2, 'Mary Smith', '', 1),
        (3, 'Robert Johnson', 'Bob, Bobby', 1)
    ])
    
    # Create quick_events table
    cursor.execute('''
    CREATE TABLE quick_events (
        id INTEGER PRIMARY KEY,
        character_id INTEGER NOT NULL,
        FOREIGN KEY (character_id) REFERENCES characters (id)
    )
    ''')
    
    # Add a test quick event
    cursor.execute('INSERT INTO quick_events (id, character_id) VALUES (1, 1)')
    
    conn.commit()
    
    return conn


def test_db_references():
    """Test character reference functions that use the database."""
    conn = setup_test_db()
    
    print("\nTesting process_char_refs_from_db:")
    text = "@John Doe and @Mary Smith had a meeting with @Robert Johnson"
    processed = process_char_refs_from_db(conn, text, 1)
    print(f"Original: {text}")
    print(f"Processed: {processed}")
    
    # Clean up
    conn.close()


if __name__ == "__main__":
    print("=== Testing Character References Utility ===\n")
    test_character_references()
    test_db_references()
    print("\n=== All tests completed ===") 