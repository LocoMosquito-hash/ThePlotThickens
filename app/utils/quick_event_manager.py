#!/usr/bin/env python3
"""
Quick Event Manager Module.

This module provides a centralized manager for creating and managing quick events
across the application.
"""

import sqlite3
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime
from PyQt6.QtWidgets import QDialog, QWidget

from app.db_sqlite import (
    create_quick_event, 
    get_story_characters, 
    get_character, 
    search_quick_events,
    get_next_quick_event_sequence_number,
    get_quick_event_tagged_characters
)
from app.utils.character_references import (
    convert_mentions_to_char_refs,
    convert_char_refs_to_mentions,
    find_mentioned_characters
)

class QuickEventManager:
    """
    Centralizes quick event creation and management functionality.
    
    This class provides methods for creating, formatting, and managing quick events
    across the application. It separates the business logic from the UI components.
    """
    
    def __init__(self, db_conn: sqlite3.Connection):
        """
        Initialize the Quick Event Manager.
        
        Args:
            db_conn: SQLite database connection
        """
        self.db_conn = db_conn
    
    def create_quick_event(self, 
                          text: str, 
                          story_id: int, 
                          character_id: Optional[int] = None,
                          sequence_number: Optional[int] = None) -> int:
        """
        Create a new quick event.
        
        Args:
            text: Text content of the quick event
            story_id: ID of the story
            character_id: Optional ID of the character (None for general events)
            sequence_number: Optional sequence number (will be auto-generated if None)
            
        Returns:
            ID of the created quick event
        """
        # Debug logging for parameter types
        print(f"[DEBUG] create_quick_event - text: {text} ({type(text)})")
        print(f"[DEBUG] create_quick_event - story_id: {story_id} ({type(story_id)})")
        print(f"[DEBUG] create_quick_event - character_id: {character_id} ({type(character_id)})")
        print(f"[DEBUG] create_quick_event - sequence_number: {sequence_number} ({type(sequence_number)})")
        
        # Process character mentions to [char:ID] format
        characters = get_story_characters(self.db_conn, story_id)
        processed_text = convert_mentions_to_char_refs(text, characters)
        
        # If sequence_number is not provided, generate one
        if sequence_number is None:
            if character_id:
                try:
                    # Ensure character_id is an integer
                    char_id = int(character_id) if character_id is not None else None
                    sequence_number = get_next_quick_event_sequence_number(self.db_conn, char_id)
                except (TypeError, ValueError) as e:
                    print(f"[ERROR] Failed to convert character_id to int: {character_id}")
                    print(f"[ERROR] Type: {type(character_id)}")
                    if isinstance(character_id, dict) and 'id' in character_id:
                        char_id = int(character_id['id'])
                        sequence_number = get_next_quick_event_sequence_number(self.db_conn, char_id)
                    else:
                        # Default to no character
                        character_id = None
                        sequence_number = 0
            else:
                sequence_number = 0
                
        # Create the quick event - ensure all parameters have the correct types
        try:
            # Try to convert character_id to int if not None
            if character_id is not None:
                if isinstance(character_id, dict) and 'id' in character_id:
                    character_id_int = int(character_id['id'])
                else:
                    character_id_int = int(character_id)
            else:
                character_id_int = None
                
            # Create the quick event
            quick_event_id = create_quick_event(
                self.db_conn,
                processed_text,  # text as string
                character_id_int,  # character_id as int or None
                int(sequence_number)  # sequence_number as int
            )
            
            return quick_event_id
        except Exception as e:
            import traceback
            print(f"[ERROR] Exception in create_quick_event: {e}")
            print(traceback.format_exc())
            raise
    
    def get_formatted_event_text(self, event_id: int) -> str:
        """
        Get a quick event's text with @mentions formatted.
        
        Args:
            event_id: ID of the quick event
            
        Returns:
            Formatted text with @mentions
        """
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT text FROM quick_events WHERE id = ?", (event_id,))
        row = cursor.fetchone()
        
        if not row:
            return ""
            
        text = row['text']
        
        # If the text contains character references, convert them to @mentions
        if "[char:" in text:
            tagged_characters = get_quick_event_tagged_characters(self.db_conn, event_id)
            return convert_char_refs_to_mentions(text, tagged_characters)
        
        return text
    
    def get_recent_events(self, story_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent quick events for a story.
        
        Args:
            story_id: ID of the story
            limit: Maximum number of events to return
            
        Returns:
            List of recent quick events with formatted text
        """
        # Get recent quick events
        events = search_quick_events(
            self.db_conn,
            story_id,
            text_query=None,
            character_id=None,
            from_date=None,
            to_date=None
        )
        
        # Sort by most recent first and limit
        events.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        events = events[:limit]
        
        # Format the events
        formatted_events = []
        for event in events:
            event_id = event.get('id')
            character_id = event.get('character_id')
            
            # Get character name if there's a character_id
            character_name = None
            if character_id:
                character = get_character(self.db_conn, character_id)
                if character:
                    character_name = character.get('name')
            
            # Format the text with @mentions
            formatted_text = self.get_formatted_event_text(event_id)
            
            formatted_events.append({
                'id': event_id,
                'character_id': character_id,
                'character_name': character_name,
                'text': formatted_text,
                'created_at': event.get('created_at'),
                'updated_at': event.get('updated_at')
            })
        
        return formatted_events
    
    def auto_detect_character(self, text: str, story_id: int) -> Optional[int]:
        """
        Auto-detect the most likely character for a quick event based on mentions.
        
        Args:
            text: Quick event text
            story_id: ID of the story
            
        Returns:
            ID of the detected character or None if no character is detected
        """
        characters = get_story_characters(self.db_conn, story_id)
        
        # Find mentioned characters
        char_ids = find_mentioned_characters(text, characters)
        
        # Return the first mentioned character's ID or None
        return char_ids[0] if char_ids else None 