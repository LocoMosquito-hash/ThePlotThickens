"""
Character References Utility Module.

This module provides functions for working with character references in text.
It handles conversions between user-friendly @mentions format and the persistent [char:ID] format.
"""

import re
import sqlite3
from typing import Dict, List, Any, Optional, Set, Tuple


def convert_mentions_to_char_refs(text: str, characters: List[Dict[str, Any]]) -> str:
    """Convert @mentions in text to [char:ID] references.
    
    This function performs a case-insensitive conversion of @mentions to the [char:ID] format
    used for persistent storage. It handles character names that contain spaces and special
    characters, and processes aliases as well.
    
    Args:
        text: Text containing @mentions (e.g., "@John went to the store with @Mary Smith")
        characters: List of character dictionaries with 'id', 'name', and optional 'aliases' keys
        
    Returns:
        Text with @mentions converted to [char:ID] format
    """
    if not text or not characters:
        return text
    
    # Create mapping of character names/aliases to IDs
    # Sort characters by name length (longest first) to ensure we match the longest name first
    name_to_id = {}
    sorted_characters = sorted(characters, key=lambda x: len(x.get('name', '')), reverse=True)
    
    for char in sorted_characters:
        # Add main character name
        if 'name' in char and char['name']:
            name_to_id[char['name'].lower()] = char['id']
        
        # Add aliases if available
        aliases = char.get('aliases', '')
        if aliases:
            for alias in aliases.split(','):
                alias = alias.strip()
                if alias:
                    name_to_id[alias.lower()] = char['id']
    
    # Process each character name separately to handle spaces and special characters
    result = text
    for name, char_id in name_to_id.items():
        # Create pattern that matches '@' followed by the exact name
        pattern = r'@(' + re.escape(name) + r')(\b|\s|$)'
        
        # Replace with [char:ID] format
        result = re.sub(pattern, f"[char:{char_id}]\\2", result, flags=re.IGNORECASE)
    
    # Look for any remaining simple @name patterns that weren't matched
    def replace_simple_mention(match):
        mention = match.group(1).lower()
        if mention in name_to_id:
            return f"[char:{name_to_id[mention]}]"
        return match.group(0)  # Keep original if not found
    
    # Apply the simple pattern matcher as a fallback
    result = re.sub(r'@(\w+)', replace_simple_mention, result)
    
    return result


def convert_char_refs_to_mentions(text: str, characters: List[Dict[str, Any]]) -> str:
    """Convert [char:ID] references to @mentions format.
    
    Args:
        text: Text containing [char:ID] references
        characters: List of character dictionaries with 'id' and 'name' keys
        
    Returns:
        Text with [char:ID] references converted to @mentions
    """
    if not text or not characters:
        return text
    
    # Create mapping of character IDs to names
    id_to_name = {char['id']: char['name'] for char in characters if 'id' in char and 'name' in char}
    
    # Function to replace character references with @mentions
    def replace_reference(match):
        char_id_str = match.group(1)
        try:
            char_id = int(char_id_str)
            if char_id in id_to_name:
                return f"@{id_to_name[char_id]}"
            return match.group(0)  # Keep original if not found
        except ValueError:
            return match.group(0)  # Keep original if not a valid ID
    
    # Replace all [char:ID] references with @mentions
    result = re.sub(r'\[char:(\d+)\]', replace_reference, text)
    
    return result


def extract_character_ids(text: str) -> Set[int]:
    """Extract character IDs from text containing [char:ID] references.
    
    Args:
        text: Text containing [char:ID] references
        
    Returns:
        Set of character IDs mentioned in the text
    """
    if not text:
        return set()
    
    # Find all [char:ID] references
    matches = re.findall(r'\[char:(\d+)\]', text)
    
    # Convert to integers and return as a set
    return {int(char_id) for char_id in matches if char_id.isdigit()}


def find_mentioned_characters(text: str, characters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find characters mentioned in text.
    
    This works with either @mentions or [char:ID] formats.
    
    Args:
        text: Text containing character mentions
        characters: List of character dictionaries
        
    Returns:
        List of character dictionaries for characters mentioned in the text
    """
    if not text or not characters:
        return []
    
    # Create a dictionary for character lookup
    char_by_id = {str(char['id']): char for char in characters if 'id' in char}
    char_by_name_lower = {char['name'].lower(): char for char in characters if 'name' in char}
    
    mentioned_chars = set()
    
    # Check for [char:ID] references
    char_id_matches = re.findall(r'\[char:(\d+)\]', text)
    for char_id in char_id_matches:
        if char_id in char_by_id:
            mentioned_chars.add(char_by_id[char_id]['id'])
    
    # Check for @mentions
    mention_matches = re.findall(r'@(\w+)', text)
    for mention in mention_matches:
        mention_lower = mention.lower()
        if mention_lower in char_by_name_lower:
            mentioned_chars.add(char_by_name_lower[mention_lower]['id'])
    
    # Return the character dictionaries for mentioned characters
    return [char for char in characters if char.get('id') in mentioned_chars]


def process_char_refs_from_db(conn: sqlite3.Connection, text: str, story_id: int) -> str:
    """Process character references in text using the database connection.
    
    This converts @mentions to [char:ID] format using character data from the database.
    
    Args:
        conn: SQLite database connection
        text: Text containing @mentions
        story_id: ID of the story to find characters in
        
    Returns:
        Text with @mentions converted to [char:ID] format
    """
    if not text or not story_id:
        return text
    
    try:
        # Get all characters for this story
        cursor = conn.cursor()
        cursor.execute('''
        SELECT id, name, aliases FROM characters WHERE story_id = ?
        ''', (story_id,))
        
        characters = [dict(row) for row in cursor.fetchall()]
        
        # Convert mentions
        return convert_mentions_to_char_refs(text, characters)
    
    except sqlite3.Error as e:
        print(f"Database error processing character references: {e}")
        return text


def get_quick_event_story_id(conn: sqlite3.Connection, quick_event_id: int) -> Optional[int]:
    """Get the story ID for a quick event.
    
    Args:
        conn: SQLite database connection
        quick_event_id: ID of the quick event
        
    Returns:
        Story ID for the quick event, or None if not found
    """
    try:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT c.story_id 
        FROM quick_events qe
        JOIN characters c ON qe.character_id = c.id
        WHERE qe.id = ?
        ''', (quick_event_id,))
        
        row = cursor.fetchone()
        if row:
            return dict(row).get('story_id')
        return None
    
    except sqlite3.Error as e:
        print(f"Database error getting quick event story ID: {e}")
        return None


def process_quick_event_references(conn: sqlite3.Connection, text: str, quick_event_id: int) -> str:
    """Process character references in a quick event's text.
    
    Args:
        conn: SQLite database connection
        text: Text containing @mentions
        quick_event_id: ID of the quick event
        
    Returns:
        Text with @mentions converted to [char:ID] format
    """
    if not text or not quick_event_id:
        return text
    
    # Get the story ID for this quick event
    story_id = get_quick_event_story_id(conn, quick_event_id)
    if not story_id:
        return text
    
    # Process character references using the story ID
    return process_char_refs_from_db(conn, text, story_id)


# Test code (uncomment when testing directly)
"""
def test_character_references():
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

if __name__ == "__main__":
    test_character_references()
""" 