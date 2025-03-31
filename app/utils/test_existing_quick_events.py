"""
Test script for checking existing quick events in the database.

This script tests how the new QuickEventsManager handles real quick events 
that already exist in the database.
"""

import sys
import os
import sqlite3
from typing import List, Dict, Any

# Add the parent directory to sys.path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.utils.quick_events_manager import QuickEventsManager


def get_database_path() -> str:
    """Get the path to the SQLite database file."""
    # Check common locations
    locations = [
        'the_plot_thickens.db',  # In the project root
        '../the_plot_thickens.db',  # If running from app directory
        '../../the_plot_thickens.db',  # If running from app/utils
        'data/story_db.sqlite',
        '../data/story_db.sqlite',
    ]
    
    for loc in locations:
        if os.path.exists(loc):
            return os.path.abspath(loc)
    
    # If not found, prompt the user
    print("Database file not found in standard locations.")
    db_path = input("Please enter the path to your database file: ")
    
    if os.path.exists(db_path):
        return os.path.abspath(db_path)
    else:
        raise FileNotFoundError(f"Database file not found at {db_path}")


def connect_to_database(db_path: str) -> sqlite3.Connection:
    """Connect to the SQLite database and return the connection."""
    print(f"Connecting to database at: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def find_quick_events_with_char_refs(conn: sqlite3.Connection) -> List[int]:
    """Find quick events that might contain character references.
    
    Args:
        conn: Database connection
        
    Returns:
        List of quick event IDs that might contain character references
    """
    cursor = conn.cursor()
    
    # Look for quick events that contain '[char:' or '@'
    cursor.execute('''
    SELECT id FROM quick_events
    WHERE text LIKE '%[char:%' OR text LIKE '%@%'
    LIMIT 20
    ''')
    
    return [row['id'] for row in cursor.fetchall()]


def get_quick_events_with_most_characters(conn: sqlite3.Connection, limit: int = 10) -> List[int]:
    """Get quick events with the most tagged characters.
    
    Args:
        conn: Database connection
        limit: Maximum number of events to return
        
    Returns:
        List of quick event IDs
    """
    cursor = conn.cursor()
    
    # Count how many characters are tagged in each quick event
    cursor.execute('''
    SELECT qe.id, COUNT(qec.character_id) AS character_count
    FROM quick_events qe
    LEFT JOIN quick_event_characters qec ON qe.id = qec.quick_event_id
    GROUP BY qe.id
    ORDER BY character_count DESC
    LIMIT ?
    ''', (limit,))
    
    return [row['id'] for row in cursor.fetchall()]


def test_existing_quick_events(conn: sqlite3.Connection, event_ids: List[int]) -> None:
    """Test how the QuickEventsManager handles existing quick events.
    
    Args:
        conn: Database connection
        event_ids: List of quick event IDs to check
    """
    # Create a QuickEventsManager
    manager = QuickEventsManager(conn)
    
    for event_id in event_ids:
        print(f"\n=== Testing Quick Event ID: {event_id} ===")
        
        # Get the quick event
        quick_event = manager.get_quick_event(event_id)
        if not quick_event:
            print(f"Quick event with ID {event_id} not found.")
            continue
        
        print(f"Raw stored text: {quick_event.get('text', '')}")
        
        # Get the tagged characters
        tagged_chars = manager.get_quick_event_tagged_characters(event_id)
        print(f"Tagged characters: {len(tagged_chars)}")
        for char in tagged_chars:
            print(f"  - {char.get('name', 'Unknown')} (ID: {char.get('id', 'Unknown')})")
        
        # Format the text for display (convert [char:ID] to @mentions)
        formatted_text = manager.format_quick_event_text(quick_event.get('text', ''), tagged_chars)
        print(f"Formatted text: {formatted_text}")


def main():
    """Main function."""
    try:
        # Get database path and connect
        db_path = get_database_path()
        conn = connect_to_database(db_path)
        
        print("\n=== Looking for quick events with character references ===")
        char_ref_events = find_quick_events_with_char_refs(conn)
        print(f"Found {len(char_ref_events)} quick events with potential character references: {char_ref_events}")
        
        print("\n=== Looking for quick events with the most tagged characters ===")
        most_chars_events = get_quick_events_with_most_characters(conn)
        print(f"Found quick events with most tagged characters: {most_chars_events}")
        
        # Combine the two lists, remove duplicates, and sort
        event_ids = sorted(set(char_ref_events + most_chars_events))
        
        # Also include the original range (184-191)
        original_ids = list(range(184, 192))
        event_ids = sorted(set(event_ids + original_ids))
        
        print(f"\nTesting {len(event_ids)} quick events: {event_ids}")
        
        # Run the test
        test_existing_quick_events(conn, event_ids)
        
        # Close the connection
        conn.close()
        
        print("\nTest completed successfully.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 