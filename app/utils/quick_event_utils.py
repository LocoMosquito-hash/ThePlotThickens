#!/usr/bin/env python3
"""
Quick Event Utilities.

This module provides utility functions for working with quick events
across the application.
"""

import sqlite3
from typing import Dict, List, Any, Optional, Tuple, Callable
from PyQt6.QtWidgets import QWidget

def show_quick_event_dialog(
    db_conn: sqlite3.Connection,
    story_id: int,
    parent: Optional[QWidget] = None,
    callback: Optional[Callable] = None,
    initial_text: str = "",
    character_id: Optional[int] = None,
    context: Optional[Dict[str, Any]] = None,
    options: Optional[Dict[str, bool]] = None
) -> None:
    """
    Show the quick event dialog and handle the result.
    
    This is a convenience function that can be called from anywhere in the application
    to show the quick event dialog.
    
    Args:
        db_conn: Database connection
        story_id: ID of the story
        parent: Parent widget
        callback: Optional callback function to call with the result
        initial_text: Optional initial text
        character_id: Optional character ID
        context: Optional context information
        options: Optional UI customization options
    """
    try:
        # Debug output for parameter types
        print(f"[DEBUG] show_quick_event_dialog - story_id: {story_id} ({type(story_id)})")
        print(f"[DEBUG] show_quick_event_dialog - character_id: {character_id} ({type(character_id)})")
        print(f"[DEBUG] show_quick_event_dialog - context: {context}")
        
        # Import here to avoid circular imports
        from app.views.quick_event_dialog import QuickEventDialog
        
        # Create default context if not provided
        if context is None:
            context = {
                "source": "generic",
                "caller": parent.__class__.__name__ if parent else "unknown"
            }
        
        # Create default options if not provided
        if options is None:
            options = {
                "show_recent_events": True,
                "show_character_tags": True,
                "show_optional_note": True,
                "allow_characterless_events": True
            }
        
        # Ensure story_id is an integer
        try:
            story_id_int = int(story_id)
        except (TypeError, ValueError):
            print(f"[ERROR] Invalid story_id type: {type(story_id)}")
            return
            
        # Check if character_id is a dictionary and extract the ID if needed
        if isinstance(character_id, dict) and 'id' in character_id:
            print(f"[DEBUG] Converting character_id from dictionary: {character_id}")
            character_id = character_id['id']
            
        # Create the dialog
        dialog = QuickEventDialog(
            db_conn=db_conn,
            story_id=story_id_int,
            parent=parent,
            context=context,
            initial_text=initial_text,
            character_id=character_id,
            options=options
        )
        
        # Connect the signal to the callback if provided
        if callback:
            dialog.quick_event_created.connect(callback)
        
        # Show the dialog (non-modal)
        dialog.show()
        
    except Exception as e:
        import traceback
        print(f"[ERROR] Error showing quick event dialog: {e}")
        print(traceback.format_exc())

def format_quick_event_text(
    db_conn: sqlite3.Connection,
    event_id: int
) -> str:
    """
    Format a quick event's text with @mentions.
    
    Args:
        db_conn: Database connection
        event_id: ID of the quick event
        
    Returns:
        Formatted text with @mentions
    """
    try:
        # Import here to avoid circular imports
        from app.utils.quick_event_manager import QuickEventManager
        
        # Create a manager and get the formatted text
        manager = QuickEventManager(db_conn)
        return manager.get_formatted_event_text(event_id)
        
    except Exception as e:
        print(f"Error formatting quick event text: {e}")
        return "" 