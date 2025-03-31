"""
Quick Events Manager Module.

This module provides a centralized class for managing Quick Events functionality,
including creation, reading, updating, and processing of character references.
"""

import sqlite3
import re
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime

from app.utils.character_references import (
    convert_mentions_to_char_refs,
    convert_char_refs_to_mentions,
    extract_character_ids,
    find_mentioned_characters,
    process_char_refs_from_db
)


class QuickEventsManager:
    """Manager class for handling Quick Events operations."""
    
    def __init__(self, db_conn: sqlite3.Connection):
        """Initialize the Quick Events Manager.
        
        Args:
            db_conn: SQLite database connection
        """
        self.conn = db_conn
    
    # ==== Quick Event Creation ====
    
    def create_quick_event(self, text: str, character_id: Optional[int] = None, 
                         sequence_number: int = 0) -> int:
        """Create a new quick event.
        
        Args:
            text: Text description of the quick event
            character_id: Optional ID of the character the quick event belongs to
            sequence_number: Order in the timeline (default 0)
            
        Returns:
            ID of the newly created quick event
            
        Raises:
            sqlite3.Error: If there's a database error
        """
        try:
            cursor = self.conn.cursor()
            
            # Get current timestamp
            now = datetime.now().isoformat()
            
            # Insert the quick event (we'll process references after we have an ID)
            cursor.execute('''
            INSERT INTO quick_events (
                created_at, updated_at, text, sequence_number, character_id
            ) VALUES (?, ?, ?, ?, ?)
            ''', (now, now, text, sequence_number, character_id))
            
            self.conn.commit()
            
            # Get the new quick event ID
            quick_event_id = cursor.lastrowid
            
            # Process character references if we have a character_id to determine story_id
            if character_id is not None:
                # Get the story_id for this character to process character references
                cursor.execute('SELECT story_id FROM characters WHERE id = ?', (character_id,))
                row = cursor.fetchone()
                story_id = dict(row).get('story_id') if row else None
                
                if story_id:
                    # Process the text to convert @mentions to [char:ID] format
                    processed_text = process_char_refs_from_db(self.conn, text, story_id)
                    
                    # If we converted any mentions, update the text
                    if processed_text != text:
                        cursor.execute('''
                        UPDATE quick_events
                        SET text = ?
                        WHERE id = ?
                        ''', (processed_text, quick_event_id))
                        self.conn.commit()
                    
                    # Process character mentions/tags
                    self._process_quick_event_character_tags(quick_event_id, processed_text)
            else:
                # Try to determine the story_id from any @mentions in the text
                story_id = None
                
                # Process @mentions to extract potential character IDs
                mentioned_chars = re.findall(r'@(\w+(?:\s+\w+)*)', text)
                
                if mentioned_chars:
                    # Find characters that match the mentions
                    placeholders = []
                    query_params = []
                    
                    # Create search conditions for each character name
                    for name in mentioned_chars:
                        placeholders.append("name = ?")
                        query_params.append(name)
                    
                    cursor.execute(f'''
                    SELECT id, name, story_id FROM characters 
                    WHERE {" OR ".join(placeholders)}
                    LIMIT 1
                    ''', query_params)
                    
                    char_result = cursor.fetchone()
                    
                    if char_result:
                        char_dict = dict(char_result)
                        story_id = char_dict.get('story_id')
                
                if story_id:
                    # Process the text to convert @mentions to [char:ID] format
                    processed_text = process_char_refs_from_db(self.conn, text, story_id)
                    
                    # If we converted any mentions, update the text
                    if processed_text != text:
                        cursor.execute('''
                        UPDATE quick_events
                        SET text = ?
                        WHERE id = ?
                        ''', (processed_text, quick_event_id))
                        self.conn.commit()
                    
                    # Process character mentions/tags
                    self._process_quick_event_character_tags(quick_event_id, processed_text)
            
            return quick_event_id
        except sqlite3.Error as e:
            print(f"Error creating quick event: {e}")
            raise
    
    def _process_quick_event_character_tags(self, quick_event_id: int, text: str) -> None:
        """Process character tags in quick event text and create associations.
        
        Args:
            quick_event_id: ID of the quick event
            text: Text to parse for character tags
        """
        try:
            # Extract character IDs from the text
            char_ids = extract_character_ids(text)
            if not char_ids:
                return
                
            cursor = self.conn.cursor()
            
            # Get the story_id by looking up the character_id of the quick event
            # or by looking at the characters mentioned in the text if there's no owner
            cursor.execute('''
            SELECT qe.character_id, c.story_id
            FROM quick_events qe
            LEFT JOIN characters c ON qe.character_id = c.id
            WHERE qe.id = ?
            ''', (quick_event_id,))
            
            result = cursor.fetchone()
            if not result:
                return
                
            result_dict = dict(result)
            character_id = result_dict.get('character_id')
            story_id = result_dict.get('story_id')
            
            # If we don't have a story_id from the character_id (NULL), try to get it from one of the tagged characters
            if story_id is None and char_ids:
                # Try to find the story_id from one of the mentioned characters
                char_id_placeholders = ','.join(['?'] * len(char_ids))
                cursor.execute(f'''
                SELECT story_id FROM characters WHERE id IN ({char_id_placeholders}) LIMIT 1
                ''', char_ids)
                
                story_result = cursor.fetchone()
                if story_result:
                    story_id = dict(story_result).get('story_id')
            
            if story_id is None:
                return
                
            # For each character ID, verify it belongs to the same story and add association
            for char_id in char_ids:
                cursor.execute('''
                SELECT id FROM characters WHERE id = ? AND story_id = ?
                ''', (char_id, story_id))
                
                if cursor.fetchone():
                    # Add the character reference (ignore if already exists)
                    cursor.execute('''
                    INSERT OR IGNORE INTO quick_event_characters (quick_event_id, character_id)
                    VALUES (?, ?)
                    ''', (quick_event_id, char_id))
            
            self.conn.commit()
            
        except (ValueError, sqlite3.Error) as e:
            print(f"Error processing quick event character tags: {e}")
    
    # ==== Quick Event Reading ====
    
    def get_quick_event(self, quick_event_id: int) -> Dict[str, Any]:
        """Get a quick event by ID.
        
        Args:
            quick_event_id: ID of the quick event to retrieve
            
        Returns:
            Dictionary with quick event data
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
        SELECT * FROM quick_events WHERE id = ?
        ''', (quick_event_id,))
        
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        else:
            return {}
    
    def get_character_quick_events(self, character_id: int) -> List[Dict[str, Any]]:
        """Get all quick events for a character.
        
        Returns both events where this character is the primary character (owner)
        and events where this character is tagged/mentioned.
        
        Args:
            character_id: ID of the character
            
        Returns:
            List of dictionaries with quick event data
        """
        cursor = self.conn.cursor()
        
        # Get events where this character is the primary owner
        cursor.execute('''
        SELECT qe.* FROM quick_events qe
        WHERE qe.character_id = ?
        UNION 
        -- Get events where this character is tagged/mentioned
        SELECT qe.* FROM quick_events qe
        JOIN quick_event_characters qec ON qe.id = qec.quick_event_id
        WHERE qec.character_id = ? AND (qe.character_id != ? OR qe.character_id IS NULL)
        ORDER BY sequence_number, created_at
        ''', (character_id, character_id, character_id))
        
        rows = cursor.fetchall()
        
        # Convert rows to dictionaries and return
        return [dict(row) for row in rows]
    
    def get_quick_event_tagged_characters(self, quick_event_id: int) -> List[Dict[str, Any]]:
        """Get all characters tagged in a quick event.
        
        Args:
            quick_event_id: ID of the quick event
            
        Returns:
            List of character dictionaries
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
        SELECT c.* FROM characters c
        JOIN quick_event_characters qec ON c.id = qec.character_id
        WHERE qec.quick_event_id = ?
        UNION
        SELECT c.* FROM characters c
        JOIN quick_events qe ON c.id = qe.character_id
        WHERE qe.id = ?
        ORDER BY c.name
        ''', (quick_event_id, quick_event_id))
        
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def get_scene_quick_events(self, scene_event_id: int) -> List[Dict[str, Any]]:
        """Get all quick events associated with a scene.
        
        Args:
            scene_event_id: ID of the scene event
            
        Returns:
            List of quick event dictionaries with association data
        """
        try:
            cursor = self.conn.cursor()
            
            cursor.execute('''
            SELECT qe.*, c.name as character_name, sqe.sequence_number, sqe.id as association_id
            FROM quick_events qe
            JOIN characters c ON qe.character_id = c.id
            JOIN scene_quick_events sqe ON qe.id = sqe.quick_event_id
            WHERE sqe.scene_event_id = ?
            ORDER BY sqe.sequence_number, qe.created_at
            ''', (scene_event_id,))
            
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"Error getting scene quick events: {e}")
            return []
    
    def get_image_quick_events(self, image_id: int) -> List[Dict[str, Any]]:
        """Get all quick events associated with an image.
        
        Args:
            image_id: ID of the image
            
        Returns:
            List of quick event dictionaries
        """
        try:
            cursor = self.conn.cursor()
            
            cursor.execute('''
            SELECT qe.*, c.name as character_name, qei.note, qei.created_at as association_date
            FROM quick_events qe
            JOIN characters c ON qe.character_id = c.id
            JOIN quick_event_images qei ON qe.id = qei.quick_event_id
            WHERE qei.image_id = ?
            ORDER BY qe.sequence_number, qe.created_at
            ''', (image_id,))
            
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"Error getting image quick events: {e}")
            return []
    
    def get_next_quick_event_sequence_number(self, character_id: int) -> int:
        """Get the next sequence number for a character's quick events.
        
        Args:
            character_id: ID of the character
            
        Returns:
            Next sequence number
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
        SELECT MAX(sequence_number) as max_seq FROM quick_events
        WHERE character_id = ?
        ''', (character_id,))
        
        result = cursor.fetchone()
        if result and result['max_seq'] is not None:
            return result['max_seq'] + 1
        
        return 0
    
    # ==== Quick Event Updating ====
    
    def update_quick_event(self, quick_event_id: int, 
                         text: Optional[str] = None, 
                         sequence_number: Optional[int] = None) -> bool:
        """Update a quick event.
        
        Args:
            quick_event_id: ID of the quick event to update
            text: New text for the quick event (optional)
            sequence_number: New sequence number (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            
            # Get the quick event to check if it exists and get the story ID
            cursor.execute('''
            SELECT qe.*, c.story_id
            FROM quick_events qe
            JOIN characters c ON qe.character_id = c.id
            WHERE qe.id = ?
            ''', (quick_event_id,))
            
            quick_event = cursor.fetchone()
            if not quick_event:
                return False
                
            # Convert to dict for easier access
            qe_dict = dict(quick_event)
            story_id = qe_dict.get('story_id')
            
            # Get current timestamp
            now = datetime.now().isoformat()
            
            # Process text changes
            processed_text = None
            if text is not None and story_id:
                # Process character references
                processed_text = process_char_refs_from_db(self.conn, text, story_id)
            
            # Build the update SQL
            update_fields = []
            params = []
            
            # Always update the timestamp
            update_fields.append("updated_at = ?")
            params.append(now)
            
            if processed_text is not None:
                update_fields.append("text = ?")
                params.append(processed_text)
            
            if sequence_number is not None:
                update_fields.append("sequence_number = ?")
                params.append(sequence_number)
            
            # Add the quick_event_id to params
            params.append(quick_event_id)
            
            # Execute the update
            cursor.execute(f'''
            UPDATE quick_events
            SET {", ".join(update_fields)}
            WHERE id = ?
            ''', params)
            
            # If text was updated, update character tags
            if processed_text is not None:
                # Delete existing tags
                cursor.execute('''
                DELETE FROM quick_event_characters
                WHERE quick_event_id = ?
                ''', (quick_event_id,))
                
                # Process new tags
                self._process_quick_event_character_tags(quick_event_id, processed_text)
            
            self.conn.commit()
            
            # Check if any rows were affected
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error updating quick event: {e}")
            return False
    
    def delete_quick_event(self, quick_event_id: int) -> bool:
        """Delete a quick event.
        
        Args:
            quick_event_id: ID of the quick event to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            
            # Delete the quick event
            cursor.execute("DELETE FROM quick_events WHERE id = ?", (quick_event_id,))
            self.conn.commit()
            
            # Check if the deletion was successful
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error deleting quick event: {e}")
            return False
    
    # ==== Quick Event Associations ====
    
    def associate_quick_event_with_scene(self, quick_event_id: int, scene_event_id: int,
                                      sequence_number: int = 0) -> bool:
        """Associate a quick event with a scene.
        
        Args:
            quick_event_id: ID of the quick event
            scene_event_id: ID of the scene event
            sequence_number: Order in the scene (default 0)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            
            # Get current timestamp
            now = datetime.now().isoformat()
            
            # Insert the association (or update if it already exists)
            cursor.execute('''
            INSERT INTO scene_quick_events (
                created_at, updated_at, scene_event_id, quick_event_id, sequence_number
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(scene_event_id, quick_event_id) 
            DO UPDATE SET updated_at = ?, sequence_number = ?
            ''', (now, now, scene_event_id, quick_event_id, sequence_number, now, sequence_number))
            
            self.conn.commit()
            
            return True
        except sqlite3.Error as e:
            print(f"Error associating quick event with scene: {e}")
            return False
    
    def remove_quick_event_from_scene(self, quick_event_id: int, scene_event_id: int) -> bool:
        """Remove a quick event from a scene.
        
        Args:
            quick_event_id: ID of the quick event
            scene_event_id: ID of the scene event
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            
            # Delete the association
            cursor.execute('''
            DELETE FROM scene_quick_events 
            WHERE quick_event_id = ? AND scene_event_id = ?
            ''', (quick_event_id, scene_event_id))
            
            self.conn.commit()
            
            # Check if the deletion was successful
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error removing quick event from scene: {e}")
            return False
    
    # ==== Character Reference Processing ====
    
    def format_quick_event_text(self, quick_event_text: str, characters: List[Dict[str, Any]]) -> str:
        """Format quick event text for display, converting [char:ID] to @mentions.
        
        Args:
            quick_event_text: Text containing [char:ID] references
            characters: List of character dictionaries
            
        Returns:
            Text with character references formatted for display
        """
        return convert_char_refs_to_mentions(quick_event_text, characters)


# Test code (uncomment when testing directly)
"""
def test_quick_events_manager():
    import sqlite3
    from pathlib import Path
    
    # Create an in-memory database for testing
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    
    # Create the necessary tables
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
    
    # Create quick_event_characters table
    cursor.execute('''
    CREATE TABLE quick_event_characters (
        id INTEGER PRIMARY KEY,
        created_at TEXT,
        updated_at TEXT,
        quick_event_id INTEGER NOT NULL,
        character_id INTEGER NOT NULL,
        FOREIGN KEY (quick_event_id) REFERENCES quick_events (id),
        FOREIGN KEY (character_id) REFERENCES characters (id)
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
        UNIQUE(scene_event_id, quick_event_id)
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
    
    conn.commit()
    
    # Create a quick events manager
    manager = QuickEventsManager(conn)
    
    # Test creating a quick event
    print("Testing create_quick_event:")
    qe_id = manager.create_quick_event('@John Doe met with @Mary Smith', 1)
    print(f"Created quick event with ID: {qe_id}")
    
    # Test getting a quick event
    print("\nTesting get_quick_event:")
    qe = manager.get_quick_event(qe_id)
    print(f"Quick event: {qe}")
    
    # Test getting quick event tagged characters
    print("\nTesting get_quick_event_tagged_characters:")
    tagged_chars = manager.get_quick_event_tagged_characters(qe_id)
    print(f"Tagged characters: {tagged_chars}")
    
    # Test updating a quick event
    print("\nTesting update_quick_event:")
    updated = manager.update_quick_event(qe_id, '@John Doe met with @Mary Smith and @Robert Johnson')
    print(f"Update successful: {updated}")
    
    # Check that the tagged characters were updated
    tagged_chars = manager.get_quick_event_tagged_characters(qe_id)
    print(f"Tagged characters after update: {tagged_chars}")
    
    # Test deleting a quick event
    print("\nTesting delete_quick_event:")
    deleted = manager.delete_quick_event(qe_id)
    print(f"Delete successful: {deleted}")
    
    # Close the connection
    conn.close()

if __name__ == "__main__":
    test_quick_events_manager()
""" 