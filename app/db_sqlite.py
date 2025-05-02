#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple SQLite database for The Plot Thickens application.

This module provides functions to create and interact with a SQLite database.
"""

import os
import json
import sqlite3
from datetime import datetime
from enum import Enum, auto
from typing import List, Dict, Any, Optional, Tuple

# Import the centralized character reference functions
from app.utils.character_references import (
    process_quick_event_references as centralized_process_quick_event_references,
    extract_character_ids,
    get_quick_event_story_id
)


# Enumerations
class StoryType(Enum):
    """Enumeration of story types."""
    VISUAL_NOVEL = auto()
    TV_SERIES = auto()
    MOVIE = auto()
    GAME = auto()
    OTHER = auto()
    
    def __str__(self):
        return self.name.replace('_', ' ').title()


# Database functions
def create_connection(db_path: str) -> sqlite3.Connection:
    """Create a database connection to the SQLite database specified by db_path."""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        raise


def create_tables(conn: sqlite3.Connection) -> None:
    """Create the database tables if they don't exist."""
    cursor = conn.cursor()
    
    # Create stories table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        title TEXT NOT NULL,
        description TEXT,
        type_name TEXT NOT NULL DEFAULT 'OTHER',
        folder_path TEXT NOT NULL UNIQUE,
        universe TEXT,
        is_part_of_series INTEGER DEFAULT 0,
        series_name TEXT,
        series_order INTEGER,
        author TEXT,
        year INTEGER
    )
    ''')
    
    # Create characters table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS characters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        name TEXT NOT NULL,
        aliases TEXT,
        is_main_character INTEGER DEFAULT 0,
        age_value INTEGER,
        age_category TEXT,
        gender TEXT DEFAULT 'NOT_SPECIFIED',
        avatar_path TEXT,
        is_archived INTEGER DEFAULT 0,
        is_deceased INTEGER DEFAULT 0,
        story_id INTEGER NOT NULL,
        FOREIGN KEY (story_id) REFERENCES stories (id) ON DELETE CASCADE
    )
    ''')
    
    # Create relationships table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS relationships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        description TEXT,
        relationship_type TEXT NOT NULL,
        color TEXT DEFAULT '#FF0000',
        width REAL DEFAULT 1.0,
        source_id INTEGER NOT NULL,
        target_id INTEGER NOT NULL,
        FOREIGN KEY (source_id) REFERENCES characters (id) ON DELETE CASCADE,
        FOREIGN KEY (target_id) REFERENCES characters (id) ON DELETE CASCADE
    )
    ''')
    
    # Create story_board_views table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS story_board_views (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        name TEXT NOT NULL,
        description TEXT,
        layout_data TEXT NOT NULL,
        story_id INTEGER NOT NULL,
        FOREIGN KEY (story_id) REFERENCES stories (id) ON DELETE CASCADE
    )
    ''')
    
    # Create events table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        title TEXT NOT NULL,
        description TEXT,
        event_type TEXT DEFAULT 'SCENE',
        start_date TEXT,
        end_date TEXT,
        location TEXT,
        importance INTEGER DEFAULT 3,
        color TEXT DEFAULT '#3498db',
        is_milestone INTEGER DEFAULT 0,
        story_id INTEGER NOT NULL,
        parent_event_id INTEGER,
        sequence_number INTEGER DEFAULT 0,
        FOREIGN KEY (story_id) REFERENCES stories (id) ON DELETE CASCADE,
        FOREIGN KEY (parent_event_id) REFERENCES events (id) ON DELETE SET NULL
    )
    ''')
    
    # Create event_characters table (for character participation in events)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS event_characters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        event_id INTEGER NOT NULL,
        character_id INTEGER NOT NULL,
        role TEXT DEFAULT 'PARTICIPANT',
        notes TEXT,
        FOREIGN KEY (event_id) REFERENCES events (id) ON DELETE CASCADE,
        FOREIGN KEY (character_id) REFERENCES characters (id) ON DELETE CASCADE
    )
    ''')
    
    # Create quick_events table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quick_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        text TEXT NOT NULL,
        sequence_number INTEGER DEFAULT 0,
        character_id INTEGER NOT NULL,
        FOREIGN KEY (character_id) REFERENCES characters (id) ON DELETE CASCADE
    )
    ''')
    
    # Create quick_event_characters table (for character tagging in quick events)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quick_event_characters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        quick_event_id INTEGER NOT NULL,
        character_id INTEGER NOT NULL,
        FOREIGN KEY (quick_event_id) REFERENCES quick_events (id) ON DELETE CASCADE,
        FOREIGN KEY (character_id) REFERENCES characters (id) ON DELETE CASCADE
    )
    ''')
    
    # Create scene_quick_events table (for associating quick events with scenes)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS scene_quick_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        scene_event_id INTEGER NOT NULL,
        quick_event_id INTEGER NOT NULL,
        sequence_number INTEGER DEFAULT 0,
        FOREIGN KEY (scene_event_id) REFERENCES events (id) ON DELETE CASCADE,
        FOREIGN KEY (quick_event_id) REFERENCES quick_events (id) ON DELETE CASCADE,
        UNIQUE(scene_event_id, quick_event_id)
    )
    ''')
    
    # Create scene_images table (for directly associating images with scenes)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS scene_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        scene_event_id INTEGER NOT NULL,
        image_id INTEGER NOT NULL,
        sequence_number INTEGER DEFAULT 0,
        FOREIGN KEY (scene_event_id) REFERENCES events (id) ON DELETE CASCADE,
        FOREIGN KEY (image_id) REFERENCES images (id) ON DELETE CASCADE,
        UNIQUE(scene_event_id, image_id)
    )
    ''')
    
    # Create timeline_views table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS timeline_views (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        name TEXT NOT NULL,
        description TEXT,
        view_type TEXT DEFAULT 'CHRONOLOGICAL',
        layout_data TEXT,
        story_id INTEGER NOT NULL,
        FOREIGN KEY (story_id) REFERENCES stories (id) ON DELETE CASCADE
    )
    ''')
    
    # Create images table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        filename TEXT NOT NULL,
        path TEXT NOT NULL,
        title TEXT,
        description TEXT,
        width INTEGER,
        height INTEGER,
        file_size INTEGER,
        mime_type TEXT,
        is_featured INTEGER DEFAULT 0,
        date_taken TIMESTAMP,
        metadata_json TEXT,
        story_id INTEGER NOT NULL,
        event_id INTEGER,
        FOREIGN KEY (story_id) REFERENCES stories (id) ON DELETE CASCADE,
        FOREIGN KEY (event_id) REFERENCES events (id) ON DELETE SET NULL
    )
    ''')
    
    # Create image_tags table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS image_tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        image_id INTEGER NOT NULL,
        character_id INTEGER NOT NULL,
        x REAL,
        y REAL,
        width REAL,
        height REAL,
        FOREIGN KEY (image_id) REFERENCES images (id) ON DELETE CASCADE,
        FOREIGN KEY (character_id) REFERENCES characters (id) ON DELETE CASCADE
    )
    ''')
    
    # Create quick_event_images table (for linking quick events to images)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quick_event_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        quick_event_id INTEGER NOT NULL,
        image_id INTEGER NOT NULL,
        note TEXT,
        FOREIGN KEY (quick_event_id) REFERENCES quick_events (id) ON DELETE CASCADE,
        FOREIGN KEY (image_id) REFERENCES images (id) ON DELETE CASCADE,
        UNIQUE(quick_event_id, image_id)
    )
    ''')
    
    # Create image_character_tags table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS image_character_tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        image_id INTEGER NOT NULL,
        character_id INTEGER NOT NULL,
        x_position REAL NOT NULL,
        y_position REAL NOT NULL,
        width REAL NOT NULL,
        height REAL NOT NULL,
        note TEXT,
        FOREIGN KEY (image_id) REFERENCES images (id) ON DELETE CASCADE,
        FOREIGN KEY (character_id) REFERENCES characters (id) ON DELETE CASCADE
    )
    ''')
    
    # Create character_details table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS character_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        character_id INTEGER NOT NULL,
        detail_text TEXT NOT NULL,
        detail_type TEXT DEFAULT 'GENERAL',
        sequence_number INTEGER DEFAULT 0,
        FOREIGN KEY (character_id) REFERENCES characters (id) ON DELETE CASCADE
    )
    ''')
    
    # Create character_last_tagged table to track when characters were last tagged in a story
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS character_last_tagged (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        story_id INTEGER NOT NULL,
        character_id INTEGER NOT NULL,
        last_tagged_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (story_id) REFERENCES stories (id) ON DELETE CASCADE,
        FOREIGN KEY (character_id) REFERENCES characters (id) ON DELETE CASCADE,
        UNIQUE(story_id, character_id)
    )
    ''')
    
    # Create indexes for efficient querying
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_character_last_tagged_story_id ON character_last_tagged(story_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_character_last_tagged_character_id ON character_last_tagged(character_id)')
    
    conn.commit()


# Story functions
def create_story(conn: sqlite3.Connection, title: str, description: str, type_name: str, folder_path: str,
                universe: Optional[str] = None, is_part_of_series: bool = False, series_name: Optional[str] = None,
                series_order: Optional[int] = None, author: Optional[str] = None, year: Optional[int] = None) -> Tuple[int, Dict[str, Any]]:
    """Create a new story in the database.
    
    Returns:
        Tuple containing the story ID and the story data
    """
    cursor = conn.cursor()
    
    # Ensure the folder exists if provided
    if folder_path:
        # Create all required folders
        story_data = {'folder_path': folder_path}
        ensure_story_folders_exist(story_data)
    
    cursor.execute('''
    INSERT INTO stories (title, description, type_name, folder_path, universe, is_part_of_series, series_name, series_order, author, year)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (title, description, type_name, folder_path, universe, 1 if is_part_of_series else 0, series_name, series_order, author, year))
    
    conn.commit()
    story_id = cursor.lastrowid
    
    # Get the created story
    story_data = get_story(conn, story_id)
    
    return story_id, story_data


def update_story_folder_path(conn: sqlite3.Connection, story_id: int, folder_path: str) -> Dict[str, Any]:
    """Update the folder path for a story.
    
    Args:
        conn: Database connection
        story_id: ID of the story to update
        folder_path: New folder path
        
    Returns:
        Updated story data
    """
    cursor = conn.cursor()
    
    # Ensure the folder exists
    os.makedirs(folder_path, exist_ok=True)
    os.makedirs(os.path.join(folder_path, "images"), exist_ok=True)
    
    # Update the story
    cursor.execute('''
    UPDATE stories
    SET folder_path = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    ''', (folder_path, story_id))
    
    conn.commit()
    
    # Get the updated story
    return get_story(conn, story_id)


def get_story(conn: sqlite3.Connection, story_id: int) -> Dict[str, Any]:
    """Get a story by ID."""
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM stories WHERE id = ?', (story_id,))
    return dict(cursor.fetchone())


def get_all_stories(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Get all stories."""
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM stories ORDER BY title')
    return [dict(row) for row in cursor.fetchall()]


def update_story(conn: sqlite3.Connection, story_id: int, title: str, description: str, 
                type_name: str, universe: Optional[str] = None, is_part_of_series: bool = False, 
                series_name: Optional[str] = None, series_order: Optional[int] = None, 
                author: Optional[str] = None, year: Optional[int] = None) -> Dict[str, Any]:
    """Update an existing story in the database.
    
    Args:
        conn: Database connection
        story_id: ID of the story to update
        title: Story title
        description: Story description
        type_name: Story type name
        universe: Universe name
        is_part_of_series: Whether the story is part of a series
        series_name: Series name
        series_order: Order within the series
        author: Author name
        year: Year of publication
        
    Returns:
        Updated story data
    """
    cursor = conn.cursor()
    
    cursor.execute('''
    UPDATE stories SET
        title = ?,
        description = ?,
        type_name = ?,
        universe = ?,
        is_part_of_series = ?,
        series_name = ?,
        series_order = ?,
        author = ?,
        year = ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    ''', (title, description, type_name, universe, 1 if is_part_of_series else 0, 
         series_name, series_order, author, year, story_id))
    
    conn.commit()
    
    # Return the updated story data
    return get_story(conn, story_id)


# Character functions
def create_character(conn, name, story_id, aliases=None, is_main_character=False, age_value=None, age_category=None, gender=None, avatar_path=None):
    """Create a new character.
    
    Args:
        conn: Database connection
        name: Character name
        story_id: ID of the story
        aliases: Character aliases
        is_main_character: Whether this is a main character
        age_value: Age value
        age_category: Age category
        gender: Gender
        avatar_path: Path to avatar image
        
    Returns:
        ID of the created character
    """
    try:
        cursor = conn.cursor()
        
        # Print debug info
        print(f"DEBUG: Creating character '{name}' for story {story_id}")
        
        # Insert the character
        cursor.execute("""
            INSERT INTO characters (name, story_id, aliases, is_main_character, age_value, age_category, gender, avatar_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, story_id, aliases, is_main_character, age_value, age_category, gender, avatar_path))
        
        # Get the ID of the inserted character
        character_id = cursor.lastrowid
        
        # Commit the changes
        conn.commit()
        
        print(f"DEBUG: Created character with ID {character_id}")
        
        return character_id
    except Exception as e:
        print(f"Error creating character: {e}")
        conn.rollback()
        return None


def get_character(conn: sqlite3.Connection, character_id: int) -> Dict[str, Any]:
    """Get a character by ID."""
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM characters WHERE id = ?', (character_id,))
    return dict(cursor.fetchone())


def get_story_characters(conn: sqlite3.Connection, story_id: int) -> List[Dict[str, Any]]:
    """Get all characters for a story."""
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM characters WHERE story_id = ? ORDER BY name', (story_id,))
    return [dict(row) for row in cursor.fetchall()]


def update_character(conn: sqlite3.Connection, character_id: int, name: str, aliases: Optional[str] = None,
                    is_main_character: bool = False, age_value: Optional[int] = None, age_category: Optional[str] = None,
                    gender: str = "NOT_SPECIFIED", avatar_path: Optional[str] = None) -> Dict[str, Any]:
    """Update an existing character in the database.
    
    Args:
        conn: Database connection
        character_id: ID of the character to update
        name: Character name
        aliases: Character aliases (comma-separated)
        is_main_character: Whether this is a main character
        age_value: Numeric age value
        age_category: Age category
        gender: Gender
        avatar_path: Path to avatar image
        
    Returns:
        Updated character data
    """
    cursor = conn.cursor()
    
    cursor.execute('''
    UPDATE characters SET
        name = ?,
        aliases = ?,
        is_main_character = ?,
        age_value = ?,
        age_category = ?,
        gender = ?,
        avatar_path = ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    ''', (name, aliases, 1 if is_main_character else 0, age_value, age_category, gender, avatar_path, character_id))
    
    conn.commit()
    
    # Return the updated character data
    return get_character(conn, character_id)


def delete_character(db_conn, character_id: int) -> bool:
    """Delete a character and all associated relationships.
    
    Args:
        db_conn: Database connection
        character_id: ID of the character to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = db_conn.cursor()
        
        # First, delete all relationships involving this character
        cursor.execute("""
            DELETE FROM relationships 
            WHERE source_id = ? OR target_id = ?
        """, (character_id, character_id))
        
        # Delete the character
        cursor.execute("DELETE FROM characters WHERE id = ?", (character_id,))
        
        # Commit the changes
        db_conn.commit()
        
        return True
    except Exception as e:
        print(f"Error deleting character: {e}")
        db_conn.rollback()
        return False


# Relationship functions
def create_relationship(conn: sqlite3.Connection, source_id: int, target_id: int, relationship_type: str,
                       description: Optional[str] = None, color: str = "#FF0000", width: float = 1.0) -> int:
    """Create a new relationship in the database."""
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO relationships (source_id, target_id, relationship_type, description, color, width)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (source_id, target_id, relationship_type, description, color, width))
    
    conn.commit()
    return cursor.lastrowid


def get_character_relationships(conn: sqlite3.Connection, character_id: int) -> List[Dict[str, Any]]:
    """Get all relationships for a character (both outgoing and incoming)."""
    cursor = conn.cursor()
    cursor.execute('''
    SELECT * FROM relationships 
    WHERE source_id = ? OR target_id = ?
    ''', (character_id, character_id))
    return [dict(row) for row in cursor.fetchall()]


def get_relationship_types(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Get all relationship types from the database."""
    cursor = conn.cursor()
    
    # Check if relationship_types table exists
    cursor.execute('''
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='relationship_types'
    ''')
    
    if cursor.fetchone():
        # If the table exists, get all relationship types
        cursor.execute('SELECT * FROM relationship_types')
        return [dict(row) for row in cursor.fetchall()]
    else:
        # If the table doesn't exist, return a list of default relationship types
        return [
            {"id": 1, "name": "Father", "has_inverse": True, "male_variant": "Son", "female_variant": "Daughter"},
            {"id": 2, "name": "Mother", "has_inverse": True, "male_variant": "Son", "female_variant": "Daughter"},
            {"id": 3, "name": "Son", "has_inverse": True},
            {"id": 4, "name": "Daughter", "has_inverse": True},
            {"id": 5, "name": "Brother", "has_inverse": True, "male_variant": "Brother", "female_variant": "Sister"},
            {"id": 6, "name": "Sister", "has_inverse": True, "male_variant": "Brother", "female_variant": "Sister"},
            {"id": 7, "name": "Friend", "has_inverse": True},
            {"id": 8, "name": "Enemy", "has_inverse": True},
            {"id": 9, "name": "Coworker", "has_inverse": True},
            {"id": 10, "name": "Boss", "has_inverse": True, "inverse_name": "Employee"},
            {"id": 11, "name": "Employee", "has_inverse": True, "inverse_name": "Boss"},
            {"id": 12, "name": "Spouse", "has_inverse": True},
            {"id": 13, "name": "Boyfriend", "has_inverse": True, "inverse_name": "Girlfriend"},
            {"id": 14, "name": "Girlfriend", "has_inverse": True, "inverse_name": "Boyfriend"},
            {"id": 15, "name": "Mentor", "has_inverse": True, "inverse_name": "Student"},
            {"id": 16, "name": "Student", "has_inverse": True, "inverse_name": "Mentor"}
        ]


def get_used_relationship_types(conn: sqlite3.Connection) -> List[str]:
    """Get all unique relationship types that have been used in the database.
    
    Args:
        conn: Database connection
        
    Returns:
        List of unique relationship type names
    """
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT relationship_type FROM relationships')
    return [row[0] for row in cursor.fetchall()]


def get_story_relationships(conn: sqlite3.Connection, story_id: int) -> List[Dict[str, Any]]:
    """Get all relationships for a story."""
    cursor = conn.cursor()
    cursor.execute('''
    SELECT r.* FROM relationships r
    JOIN characters c1 ON r.source_id = c1.id
    WHERE c1.story_id = ?
    ''', (story_id,))
    return [dict(row) for row in cursor.fetchall()]


# Story Board View functions
def create_story_board_view(conn: sqlite3.Connection, name: str, story_id: int, layout_data: str,
                           description: Optional[str] = None) -> int:
    """Create a new story board view in the database."""
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO story_board_views (name, story_id, layout_data, description)
    VALUES (?, ?, ?, ?)
    ''', (name, story_id, layout_data, description))
    
    conn.commit()
    return cursor.lastrowid


def get_story_board_views(conn: sqlite3.Connection, story_id: int) -> List[Dict[str, Any]]:
    """Get all story board views for a story."""
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM story_board_views WHERE story_id = ? ORDER BY name', (story_id,))
    return [dict(row) for row in cursor.fetchall()]


def get_story_board_view(conn: sqlite3.Connection, view_id: int) -> Dict[str, Any]:
    """Get a story board view by ID."""
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM story_board_views WHERE id = ?', (view_id,))
    return dict(cursor.fetchone())


def update_story_board_view_layout(conn: sqlite3.Connection, view_id: int, layout_data: str) -> None:
    """Update the layout data for a story board view."""
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE story_board_views
    SET layout_data = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    ''', (layout_data, view_id))
    conn.commit()


# Initialize the database
def initialize_database(db_path: str) -> sqlite3.Connection:
    """Initialize the database and create the necessary tables.
    
    Args:
        db_path: Path to the database file
        
    Returns:
        Database connection
    """
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Create or open the database connection
    conn = create_connection(db_path)
    
    # Create tables
    create_tables(conn)
    
    # Make sure the image_character_tags table is created
    create_image_character_tags_table(conn)
    
    # Make sure the character_last_tagged table is created
    create_character_last_tagged_table(conn)
    
    return conn


def get_story_images(conn: sqlite3.Connection, story_id: int) -> List[Dict[str, Any]]:
    """Get all images for a story.
    
    Args:
        conn: Database connection
        story_id: ID of the story
        
    Returns:
        List of image dictionaries
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM images
        WHERE story_id = ?
        ORDER BY created_at DESC
        """,
        (story_id,)
    )
    return [dict(row) for row in cursor.fetchall()]


def get_image(conn: sqlite3.Connection, image_id: int) -> Dict[str, Any]:
    """Get an image by ID.
    
    Args:
        conn: Database connection
        image_id: ID of the image
        
    Returns:
        Image dictionary
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM images WHERE id = ?", (image_id,))
    return dict(cursor.fetchone())


def create_image(conn: sqlite3.Connection, filename: str, path: str, story_id: int, 
                title: Optional[str] = None, description: Optional[str] = None,
                width: Optional[int] = None, height: Optional[int] = None,
                file_size: Optional[int] = None, mime_type: Optional[str] = None,
                is_featured: bool = False, date_taken: Optional[str] = None,
                metadata_json: Optional[str] = None, event_id: Optional[int] = None) -> int:
    """Create a new image.
    
    Args:
        conn: Database connection
        filename: Name of the image file
        path: Path to the image file
        story_id: ID of the story
        title: Title of the image
        description: Description of the image
        width: Width of the image in pixels
        height: Height of the image in pixels
        file_size: Size of the image file in bytes
        mime_type: MIME type of the image
        is_featured: Whether the image is featured
        date_taken: Date the image was taken
        metadata_json: JSON string with metadata
        event_id: ID of the associated event
        
    Returns:
        ID of the created image
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO images (
            filename, path, title, description, width, height,
            file_size, mime_type, is_featured, date_taken,
            metadata_json, story_id, event_id,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """,
        (
            filename, path, title, description, width, height,
            file_size, mime_type, 1 if is_featured else 0, date_taken,
            metadata_json, story_id, event_id
        )
    )
    conn.commit()
    return cursor.lastrowid


def update_image(conn: sqlite3.Connection, image_id: int, title: Optional[str] = None, 
                description: Optional[str] = None, is_featured: Optional[bool] = None) -> None:
    """Update an image.
    
    Args:
        conn: Database connection
        image_id: ID of the image
        title: New title
        description: New description
        is_featured: New featured status
    """
    # Build update query dynamically based on provided parameters
    update_parts = []
    params = []
    
    if title is not None:
        update_parts.append("title = ?")
        params.append(title)
    
    if description is not None:
        update_parts.append("description = ?")
        params.append(description)
    
    if is_featured is not None:
        update_parts.append("is_featured = ?")
        params.append(1 if is_featured else 0)
    
    if not update_parts:
        return  # Nothing to update
    
    # Add updated_at timestamp
    update_parts.append("updated_at = datetime('now')")
    
    # Build and execute query
    query = f"UPDATE images SET {', '.join(update_parts)} WHERE id = ?"
    params.append(image_id)
    
    cursor = conn.cursor()
    cursor.execute(query, tuple(params))
    conn.commit()


def delete_image(conn: sqlite3.Connection, image_id: int) -> bool:
    """Delete an image.
    
    Args:
        conn: Database connection
        image_id: ID of the image
        
    Returns:
        True if the image was deleted, False otherwise
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM images WHERE id = ?", (image_id,))
    conn.commit()
    return cursor.rowcount > 0


def create_image_tag(conn: sqlite3.Connection, image_id: int, character_id: int,
                    x: Optional[float] = None, y: Optional[float] = None,
                    width: Optional[float] = None, height: Optional[float] = None) -> int:
    """Create a new image tag.
    
    Args:
        conn: Database connection
        image_id: ID of the image
        character_id: ID of the character
        x: X coordinate (0.0 to 1.0)
        y: Y coordinate (0.0 to 1.0)
        width: Width of the tag box (0.0 to 1.0)
        height: Height of the tag box (0.0 to 1.0)
        
    Returns:
        ID of the created tag
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO image_tags (
            image_id, character_id, x, y, width, height,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """,
        (image_id, character_id, x, y, width, height)
    )
    conn.commit()
    return cursor.lastrowid


def get_image_tags(conn: sqlite3.Connection, image_id: int) -> List[Dict[str, Any]]:
    """Get all tags for an image.
    
    Args:
        conn: Database connection
        image_id: ID of the image
        
    Returns:
        List of tag dictionaries
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT it.*, c.name as character_name
        FROM image_tags it
        JOIN characters c ON it.character_id = c.id
        WHERE it.image_id = ?
        """,
        (image_id,)
    )
    return [dict(row) for row in cursor.fetchall()]


def get_character_images(conn: sqlite3.Connection, character_id: int) -> List[Dict[str, Any]]:
    """Get all images for a character.
    
    Args:
        conn: Database connection
        character_id: ID of the character
        
    Returns:
        List of image dictionaries
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT i.*
        FROM images i
        JOIN image_tags it ON i.id = it.image_id
        WHERE it.character_id = ?
        ORDER BY i.created_at DESC
        """,
        (character_id,))
    return [dict(row) for row in cursor.fetchall()]


def delete_image_tag(conn: sqlite3.Connection, tag_id: int) -> bool:
    """Delete an image tag.
    
    Args:
        conn: Database connection
        tag_id: ID of the tag
        
    Returns:
        True if the tag was deleted, False otherwise
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM image_tags WHERE id = ?", (tag_id,))
    conn.commit()
    return cursor.rowcount > 0


def get_story_folder_paths(story_data: Dict[str, Any]) -> Dict[str, str]:
    """Get folder paths for a story.
    
    Args:
        story_data: Story data dictionary
        
    Returns:
        Dictionary of folder paths
    """
    folder_path = story_data['folder_path']
    return {
        'folder_path': folder_path,
        'images_folder': os.path.join(folder_path, "images"),
        'thumbnails_folder': os.path.join(folder_path, "thumbnails"),
        'avatars_folder': os.path.join(folder_path, "avatars"),
        'backups_folder': os.path.join(folder_path, "backups")
    }


def ensure_story_folders_exist(story_data: Dict[str, Any]) -> None:
    """Ensure that all required folders for a story exist.
    
    Args:
        story_data: Story data dictionary
    """
    folders = get_story_folder_paths(story_data)
    for folder in folders.values():
        os.makedirs(folder, exist_ok=True)


# Timeline and Event functions
def create_event(conn: sqlite3.Connection, title: str, story_id: int, description: Optional[str] = None,
                event_type: str = "SCENE", start_date: Optional[str] = None, end_date: Optional[str] = None,
                location: Optional[str] = None, importance: int = 3, color: str = "#3498db",
                is_milestone: bool = False, parent_event_id: Optional[int] = None,
                sequence_number: int = 0) -> int:
    """Create a new event.
    
    Args:
        conn: Database connection
        title: Event title
        story_id: ID of the story
        description: Event description
        event_type: Type of event (SCENE, CHAPTER, etc.)
        start_date: Start date of the event (ISO format or story-specific format)
        end_date: End date of the event
        location: Location of the event
        importance: Importance level (1-5, with 5 being most important)
        color: Color for the event in the timeline
        is_milestone: Whether this is a milestone event
        parent_event_id: ID of the parent event (for hierarchical events)
        sequence_number: Order in the timeline
        
    Returns:
        ID of the created event
    """
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO events (
                title, description, event_type, start_date, end_date, location,
                importance, color, is_milestone, story_id, parent_event_id, sequence_number
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            title, description, event_type, start_date, end_date, location,
            importance, color, 1 if is_milestone else 0, story_id, parent_event_id, sequence_number
        ))
        
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error creating event: {e}")
        conn.rollback()
        return None


def get_event(conn: sqlite3.Connection, event_id: int) -> Dict[str, Any]:
    """Get an event by ID.
    
    Args:
        conn: Database connection
        event_id: ID of the event
        
    Returns:
        Event data as a dictionary
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    return dict(cursor.fetchone())


def update_event(conn: sqlite3.Connection, event_id: int, title: Optional[str] = None,
                description: Optional[str] = None, event_type: Optional[str] = None,
                start_date: Optional[str] = None, end_date: Optional[str] = None,
                location: Optional[str] = None, importance: Optional[int] = None,
                color: Optional[str] = None, is_milestone: Optional[bool] = None,
                parent_event_id: Optional[int] = None, sequence_number: Optional[int] = None) -> bool:
    """Update an event.
    
    Args:
        conn: Database connection
        event_id: ID of the event to update
        title: Event title
        description: Event description
        event_type: Type of event
        start_date: Start date of the event
        end_date: End date of the event
        location: Location of the event
        importance: Importance level
        color: Color for the event
        is_milestone: Whether this is a milestone event
        parent_event_id: ID of the parent event
        sequence_number: Order in the timeline
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()
        
        # Get current event data
        cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
        current_data = cursor.fetchone()
        
        if not current_data:
            return False
            
        # Update only provided fields
        updates = {}
        if title is not None:
            updates['title'] = title
        if description is not None:
            updates['description'] = description
        if event_type is not None:
            updates['event_type'] = event_type
        if start_date is not None:
            updates['start_date'] = start_date
        if end_date is not None:
            updates['end_date'] = end_date
        if location is not None:
            updates['location'] = location
        if importance is not None:
            updates['importance'] = importance
        if color is not None:
            updates['color'] = color
        if is_milestone is not None:
            updates['is_milestone'] = 1 if is_milestone else 0
        if parent_event_id is not None:
            updates['parent_event_id'] = parent_event_id
        if sequence_number is not None:
            updates['sequence_number'] = sequence_number
        
        # Add updated_at timestamp
        updates['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Build the SQL query
        if not updates:
            return True  # Nothing to update
            
        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values())
        values.append(event_id)
        
        cursor.execute(f"UPDATE events SET {set_clause} WHERE id = ?", values)
        conn.commit()
        
        return True
    except Exception as e:
        print(f"Error updating event: {e}")
        conn.rollback()
        return False


def delete_event(conn: sqlite3.Connection, event_id: int) -> bool:
    """Delete an event.
    
    Args:
        conn: Database connection
        event_id: ID of the event to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()
        
        # Delete the event
        cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
        
        # Commit the changes
        conn.commit()
        
        return True
    except Exception as e:
        print(f"Error deleting event: {e}")
        conn.rollback()
        return False


def get_story_events(conn: sqlite3.Connection, story_id: int) -> List[Dict[str, Any]]:
    """Get all events for a story.
    
    Args:
        conn: Database connection
        story_id: ID of the story
        
    Returns:
        List of event dictionaries
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM events 
        WHERE story_id = ? 
        ORDER BY sequence_number, start_date, title
    """, (story_id,))
    return [dict(row) for row in cursor.fetchall()]


def add_character_to_event(conn: sqlite3.Connection, event_id: int, character_id: int,
                          role: str = "PARTICIPANT", notes: Optional[str] = None) -> int:
    """Add a character to an event.
    
    Args:
        conn: Database connection
        event_id: ID of the event
        character_id: ID of the character
        role: Role of the character in the event
        notes: Additional notes
        
    Returns:
        ID of the created event_character entry
    """
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO event_characters (event_id, character_id, role, notes)
            VALUES (?, ?, ?, ?)
        """, (event_id, character_id, role, notes))
        
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error adding character to event: {e}")
        conn.rollback()
        return None


def remove_character_from_event(conn: sqlite3.Connection, event_id: int, character_id: int) -> bool:
    """Remove a character from an event.
    
    Args:
        conn: Database connection
        event_id: ID of the event
        character_id: ID of the character
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM event_characters 
            WHERE event_id = ? AND character_id = ?
        """, (event_id, character_id))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error removing character from event: {e}")
        conn.rollback()
        return False


def get_event_characters(conn: sqlite3.Connection, event_id: int) -> List[Dict[str, Any]]:
    """Get all characters participating in an event.
    
    Args:
        conn: Database connection
        event_id: ID of the event
        
    Returns:
        List of character dictionaries with role information
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, ec.role, ec.notes
        FROM characters c
        JOIN event_characters ec ON c.id = ec.character_id
        WHERE ec.event_id = ?
        ORDER BY c.name
    """, (event_id,))
    return [dict(row) for row in cursor.fetchall()]


def get_character_events(conn: sqlite3.Connection, character_id: int) -> List[Dict[str, Any]]:
    """Get all events a character participates in.
    
    Args:
        conn: Database connection
        character_id: ID of the character
        
    Returns:
        List of event dictionaries with role information
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.*, ec.role, ec.notes
        FROM events e
        JOIN event_characters ec ON e.id = ec.event_id
        WHERE ec.character_id = ?
        ORDER BY e.sequence_number, e.start_date, e.title
    """, (character_id,))
    return [dict(row) for row in cursor.fetchall()]


def create_timeline_view(conn: sqlite3.Connection, name: str, story_id: int,
                        description: Optional[str] = None, view_type: str = "CHRONOLOGICAL",
                        layout_data: Optional[str] = None) -> int:
    """Create a new timeline view.
    
    Args:
        conn: Database connection
        name: View name
        story_id: ID of the story
        description: View description
        view_type: Type of view (CHRONOLOGICAL, CHARACTER_FOCUSED, etc.)
        layout_data: JSON string with layout data
        
    Returns:
        ID of the created timeline view
    """
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO timeline_views (name, description, view_type, layout_data, story_id)
            VALUES (?, ?, ?, ?, ?)
        """, (name, description, view_type, layout_data, story_id))
        
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error creating timeline view: {e}")
        conn.rollback()
        return None


def get_timeline_view(conn: sqlite3.Connection, view_id: int) -> Dict[str, Any]:
    """Get a timeline view by ID.
    
    Args:
        conn: Database connection
        view_id: ID of the timeline view
        
    Returns:
        Timeline view data as a dictionary
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM timeline_views WHERE id = ?", (view_id,))
    return dict(cursor.fetchone())


def get_story_timeline_views(conn: sqlite3.Connection, story_id: int) -> List[Dict[str, Any]]:
    """Get all timeline views for a story.
    
    Args:
        conn: Database connection
        story_id: ID of the story
        
    Returns:
        List of timeline view dictionaries
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM timeline_views WHERE story_id = ? ORDER BY name", (story_id,))
    return [dict(row) for row in cursor.fetchall()]


def update_timeline_view(conn: sqlite3.Connection, view_id: int, name: Optional[str] = None,
                        description: Optional[str] = None, view_type: Optional[str] = None,
                        layout_data: Optional[str] = None) -> bool:
    """Update a timeline view.
    
    Args:
        conn: Database connection
        view_id: ID of the timeline view
        name: View name
        description: View description
        view_type: Type of view
        layout_data: JSON string with layout data
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()
        
        # Get current view data
        cursor.execute("SELECT * FROM timeline_views WHERE id = ?", (view_id,))
        current_data = cursor.fetchone()
        
        if not current_data:
            return False
            
        # Update only provided fields
        updates = {}
        if name is not None:
            updates['name'] = name
        if description is not None:
            updates['description'] = description
        if view_type is not None:
            updates['view_type'] = view_type
        if layout_data is not None:
            updates['layout_data'] = layout_data
        
        # Add updated_at timestamp
        updates['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Build the SQL query
        if not updates:
            return True  # Nothing to update
            
        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values())
        values.append(view_id)
        
        cursor.execute(f"UPDATE timeline_views SET {set_clause} WHERE id = ?", values)
        conn.commit()
        
        return True
    except Exception as e:
        print(f"Error updating timeline view: {e}")
        conn.rollback()
        return False


def delete_timeline_view(conn: sqlite3.Connection, view_id: int) -> bool:
    """Delete a timeline view.
    
    Args:
        conn: Database connection
        view_id: ID of the timeline view to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()
        
        # Delete the timeline view
        cursor.execute("DELETE FROM timeline_views WHERE id = ?", (view_id,))
        conn.commit()
        
        # Check if the deletion was successful
        if cursor.rowcount > 0:
            return True
        else:
            return False
    except sqlite3.Error as e:
        print(f"Error deleting timeline view: {e}")
        return False


# Quick Event Functions

def process_quick_event_character_tags(conn: sqlite3.Connection, quick_event_id: int, text: str) -> None:
    """Process character tags in quick event text and create associations.
    
    Args:
        conn: Database connection
        quick_event_id: ID of the quick event
        text: Text to parse for character tags
    """
    try:
        # Extract character IDs from the text 
        char_ids = extract_character_ids(text)
        
        if not char_ids:
            return
        
        # Get the story ID for this quick event to validate characters
        story_id = get_quick_event_story_id(conn, quick_event_id)
        if story_id is None:
            return
        
        cursor = conn.cursor()
        
        for char_id in char_ids:
            # Verify this character belongs to the same story
            cursor.execute('''
            SELECT id FROM characters WHERE id = ? AND story_id = ?
            ''', (char_id, story_id))
            
            if cursor.fetchone():
                # Add the character reference
                cursor.execute('''
                INSERT OR IGNORE INTO quick_event_characters (quick_event_id, character_id)
                VALUES (?, ?)
                ''', (quick_event_id, char_id))
        
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error processing quick event character tags: {e}")


def get_quick_event(conn: sqlite3.Connection, quick_event_id: int) -> Dict[str, Any]:
    """Get a quick event by ID.
    
    Args:
        conn: Database connection
        quick_event_id: ID of the quick event to retrieve
        
    Returns:
        Dictionary with quick event data
    """
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM quick_events WHERE id = ?
    ''', (quick_event_id,))
    
    row = cursor.fetchone()
    
    if row:
        return dict(row)
    else:
        return {}


def get_character_quick_events(conn: sqlite3.Connection, character_id: int) -> List[Dict[str, Any]]:
    """Get all quick events for a character.
    
    Returns both events where this character is the primary character (owner)
    and events where this character is tagged/mentioned.
    
    Args:
        conn: Database connection
        character_id: ID of the character
        
    Returns:
        List of dictionaries with quick event data
    """
    cursor = conn.cursor()
    
    # Get events where this character is the primary owner
    cursor.execute('''
    SELECT qe.* FROM quick_events qe
    WHERE qe.character_id = ?
    UNION 
    -- Get events where this character is tagged/mentioned
    SELECT qe.* FROM quick_events qe
    JOIN quick_event_characters qec ON qe.id = qec.quick_event_id
    WHERE qec.character_id = ? AND qe.character_id != ?
    ORDER BY sequence_number, created_at
    ''', (character_id, character_id, character_id))
    
    rows = cursor.fetchall()
    
    # Convert rows to dictionaries and return
    return [dict(row) for row in rows]


def get_quick_event_characters(conn: sqlite3.Connection, quick_event_id: int) -> List[Dict[str, Any]]:
    """Get all characters tagged in a quick event.
    
    Args:
        conn: Database connection
        quick_event_id: ID of the quick event
        
    Returns:
        List of dictionaries with character data
    """
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT c.* FROM characters c
    JOIN quick_event_characters qec ON c.id = qec.character_id
    WHERE qec.quick_event_id = ?
    ORDER BY c.name
    ''', (quick_event_id,))
    
    rows = cursor.fetchall()
    
    # Convert rows to dictionaries and return
    return [dict(row) for row in rows]


def update_quick_event(conn: sqlite3.Connection, quick_event_id: int, 
                      text: Optional[str] = None, 
                      sequence_number: Optional[int] = None) -> bool:
    """Update a quick event.
    
    Args:
        conn: Database connection
        quick_event_id: ID of the quick event to update
        text: New text for the quick event
        sequence_number: New sequence number
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()
        
        # Get current timestamp
        now = datetime.now().isoformat()
        
        # Build the query dynamically based on provided parameters
        update_fields = ['updated_at = ?']
        params = [now]
        
        if text is not None:
            # Convert @mentions to [char:ID] format if possible
            processed_text = centralized_process_quick_event_references(conn, text, quick_event_id)
            update_fields.append('text = ?')
            params.append(processed_text)
            
        if sequence_number is not None:
            update_fields.append('sequence_number = ?')
            params.append(sequence_number)
            
        # If no fields to update, return False
        if len(update_fields) <= 1:  # Only updated_at
            return False
            
        # Build the final query
        query = f'''
        UPDATE quick_events 
        SET {', '.join(update_fields)} 
        WHERE id = ?
        '''
        
        # Add the quick_event_id to params
        params.append(quick_event_id)
        
        # Execute the update
        cursor.execute(query, tuple(params))
        conn.commit()
        
        # If text was updated, update character tags
        if text is not None:
            # Delete existing tags
            cursor.execute('''
            DELETE FROM quick_event_characters
            WHERE quick_event_id = ?
            ''', (quick_event_id,))
            
            # Process new tags
            process_quick_event_character_tags(conn, quick_event_id, processed_text)
        
        # Check if the update was successful
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error updating quick event: {e}")
        return False


def process_character_references(conn: sqlite3.Connection, text: str, quick_event_id: int) -> str:
    """Process character references in text, converting @mentions to [char:ID] format where possible.
    
    Args:
        conn: Database connection
        text: Text to process
        quick_event_id: ID of the quick event (to determine story)
        
    Returns:
        Processed text with character references in [char:ID] format
    """
    # Use the centralized implementation while maintaining the same interface
    return centralized_process_quick_event_references(conn, text, quick_event_id)


def create_quick_event(conn: sqlite3.Connection, text: str, character_id: Optional[int] = None, 
                      sequence_number: int = 0) -> int:
    """Create a new quick event.
    
    Args:
        conn: Database connection
        text: Text description of the quick event
        character_id: Optional ID of the character the quick event belongs to (None for events with no character)
        sequence_number: Order in the timeline (default 0)
        
    Returns:
        ID of the newly created quick event
    """
    try:
        cursor = conn.cursor()
        
        # Get current timestamp
        now = datetime.now().isoformat()
        
        # Insert the quick event (we'll process references after we have an ID)
        cursor.execute('''
        INSERT INTO quick_events (
            created_at, updated_at, text, sequence_number, character_id
        ) VALUES (?, ?, ?, ?, ?)
        ''', (now, now, text, sequence_number, character_id))
        
        conn.commit()
        
        # Get the new quick event ID
        quick_event_id = cursor.lastrowid
        
        # Process character references only if a character_id is provided
        if character_id is not None:
            # Now that we have an ID, process the text to convert @mentions to [char:ID] format
            processed_text = centralized_process_quick_event_references(conn, text, quick_event_id)
            
            # If we converted any mentions, update the text
            if processed_text != text:
                cursor.execute('''
                UPDATE quick_events
                SET text = ?
                WHERE id = ?
                ''', (processed_text, quick_event_id))
                conn.commit()
            
            # Process character mentions/tags
            process_quick_event_character_tags(conn, quick_event_id, processed_text)
        
        return quick_event_id
    except sqlite3.Error as e:
        print(f"Error creating quick event: {e}")
        raise


def delete_quick_event(conn: sqlite3.Connection, quick_event_id: int) -> bool:
    """Delete a quick event.
    
    Args:
        conn: Database connection
        quick_event_id: ID of the quick event to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()
        
        # Delete the quick event
        cursor.execute("DELETE FROM quick_events WHERE id = ?", (quick_event_id,))
        conn.commit()
        
        # Check if the deletion was successful
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error deleting quick event: {e}")
        return False


def get_next_quick_event_sequence_number(conn: sqlite3.Connection, character_id: int) -> int:
    """Get the next sequence number for a new quick event.
    
    Args:
        conn: Database connection
        character_id: ID of the character
        
    Returns:
        The next sequence number (max sequence number + 1)
    """
    try:
        cursor = conn.cursor()
        
        # Get the maximum sequence number for the character's quick events
        cursor.execute('''
        SELECT MAX(sequence_number) as max_seq
        FROM quick_events
        WHERE character_id = ?
        ''', (character_id,))
        
        result = cursor.fetchone()
        
        if result and result['max_seq'] is not None:
            return result['max_seq'] + 1
        else:
            return 0
    except sqlite3.Error as e:
        print(f"Error getting next sequence number: {e}")
        return 0


# Quick Event Image Functions

def associate_quick_event_with_image(conn: sqlite3.Connection, 
                                   quick_event_id: int, 
                                   image_id: int,
                                   note: Optional[str] = None) -> bool:
    """Associate a quick event with an image.
    
    Args:
        conn: Database connection
        quick_event_id: ID of the quick event
        image_id: ID of the image
        note: Optional note about the association
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()
        
        # Get current timestamp
        now = datetime.now().isoformat()
        
        # Check if the association already exists
        cursor.execute('''
        SELECT id FROM quick_event_images
        WHERE quick_event_id = ? AND image_id = ?
        ''', (quick_event_id, image_id))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update the existing association
            cursor.execute('''
            UPDATE quick_event_images
            SET updated_at = ?, note = ?
            WHERE quick_event_id = ? AND image_id = ?
            ''', (now, note, quick_event_id, image_id))
        else:
            # Create a new association
            cursor.execute('''
            INSERT INTO quick_event_images (
                created_at, updated_at, quick_event_id, image_id, note
            ) VALUES (?, ?, ?, ?, ?)
            ''', (now, now, quick_event_id, image_id, note))
            
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error associating quick event with image: {e}")
        return False


def remove_quick_event_image_association(conn: sqlite3.Connection, 
                                       quick_event_id: int, 
                                       image_id: int) -> bool:
    """Remove an association between a quick event and an image.
    
    Args:
        conn: Database connection
        quick_event_id: ID of the quick event
        image_id: ID of the image
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()
        
        cursor.execute('''
        DELETE FROM quick_event_images
        WHERE quick_event_id = ? AND image_id = ?
        ''', (quick_event_id, image_id))
        
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error removing quick event-image association: {e}")
        return False


def get_quick_event_images(conn: sqlite3.Connection, quick_event_id: int) -> List[Dict[str, Any]]:
    """Get all images associated with a quick event.
    
    Args:
        conn: Database connection
        quick_event_id: ID of the quick event
        
    Returns:
        List of image dictionaries
    """
    try:
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT i.*, qei.note, qei.created_at as association_date
        FROM images i
        JOIN quick_event_images qei ON i.id = qei.image_id
        WHERE qei.quick_event_id = ?
        ORDER BY i.created_at DESC
        ''', (quick_event_id,))
        
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"Error getting quick event images: {e}")
        return []


def get_image_quick_events(conn: sqlite3.Connection, image_id: int) -> List[Dict[str, Any]]:
    """Get all quick events associated with an image.
    
    Args:
        conn: Database connection
        image_id: ID of the image
        
    Returns:
        List of quick event dictionaries
    """
    try:
        cursor = conn.cursor()
        
        # Use LEFT JOIN to include events without a character (NULL character_id)
        cursor.execute('''
        SELECT qe.*, c.name as character_name, qei.note, qei.created_at as association_date
        FROM quick_events qe
        LEFT JOIN characters c ON qe.character_id = c.id
        JOIN quick_event_images qei ON qe.id = qei.quick_event_id
        WHERE qei.image_id = ?
        ORDER BY qe.sequence_number, qe.created_at
        ''', (image_id,))
        
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"Error getting image quick events: {e}")
        return []


def create_image_character_tags_table(conn: sqlite3.Connection) -> None:
    """Create the image_character_tags table if it doesn't exist.
    
    This table stores character tags on images (Facebook-like tagging).
    
    Args:
        conn: Database connection
    """
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS image_character_tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        image_id INTEGER NOT NULL,
        character_id INTEGER NOT NULL,
        x_position REAL NOT NULL,
        y_position REAL NOT NULL,
        width REAL NOT NULL,
        height REAL NOT NULL,
        note TEXT,
        FOREIGN KEY (image_id) REFERENCES images (id) ON DELETE CASCADE,
        FOREIGN KEY (character_id) REFERENCES characters (id) ON DELETE CASCADE
    )
    ''')
    
    conn.commit()


def add_character_tag_to_image(conn: sqlite3.Connection, 
                             image_id: int, 
                             character_id: int,
                             x_position: float,
                             y_position: float,
                             width: float = 0.1,
                             height: float = 0.1,
                             note: str = None) -> int:
    """Add a character tag to an image.
    
    Args:
        conn: Database connection
        image_id: ID of the image
        character_id: ID of the character
        x_position: X position of the tag (0.0-1.0, relative to image width)
        y_position: Y position of the tag (0.0-1.0, relative to image height)
        width: Width of the tag box (0.0-1.0, relative to image width)
        height: Height of the tag box (0.0-1.0, relative to image height)
        note: Optional note for the tag
        
    Returns:
        ID of the new tag or None if failed
    """
    try:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
        INSERT INTO image_character_tags (
            created_at, updated_at, image_id, character_id, 
            x_position, y_position, width, height, note
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (now, now, image_id, character_id, x_position, y_position, width, height, note))
        
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error adding character tag to image: {e}")
        return None


def update_character_tag(conn: sqlite3.Connection,
                        tag_id: int,
                        x_position: float = None,
                        y_position: float = None,
                        width: float = None,
                        height: float = None,
                        note: str = None) -> bool:
    """Update a character tag on an image.
    
    Args:
        conn: Database connection
        tag_id: ID of the tag to update
        x_position: New X position of the tag (optional)
        y_position: New Y position of the tag (optional)
        width: New width of the tag box (optional)
        height: New height of the tag box (optional)
        note: New note for the tag (optional)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        # Get current values
        cursor.execute('''
        SELECT x_position, y_position, width, height, note
        FROM image_character_tags
        WHERE id = ?
        ''', (tag_id,))
        
        row = cursor.fetchone()
        if not row:
            return False
            
        # Use provided values or keep existing ones
        x_pos = x_position if x_position is not None else row['x_position']
        y_pos = y_position if y_position is not None else row['y_position']
        w = width if width is not None else row['width']
        h = height if height is not None else row['height']
        n = note if note is not None else row['note']
        
        cursor.execute('''
        UPDATE image_character_tags
        SET updated_at = ?, x_position = ?, y_position = ?, width = ?, height = ?, note = ?
        WHERE id = ?
        ''', (now, x_pos, y_pos, w, h, n, tag_id))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error updating character tag: {e}")
        return False


def remove_character_tag(conn: sqlite3.Connection, tag_id: int) -> bool:
    """Remove a character tag from an image.
    
    Args:
        conn: Database connection
        tag_id: ID of the tag to remove
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()
        
        cursor.execute('''
        DELETE FROM image_character_tags
        WHERE id = ?
        ''', (tag_id,))
        
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error removing character tag: {e}")
        return False


def get_image_character_tags(conn: sqlite3.Connection, image_id: int) -> List[Dict[str, Any]]:
    """Get all character tags for an image.
    
    Args:
        conn: Database connection
        image_id: ID of the image
        
    Returns:
        List of tag dictionaries
    """
    try:
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT t.*, c.name as character_name
        FROM image_character_tags t
        JOIN characters c ON t.character_id = c.id
        WHERE t.image_id = ?
        ORDER BY t.created_at
        ''', (image_id,))
        
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"Error getting image character tags: {e}")
        return []


def get_character_image_tags(conn: sqlite3.Connection, character_id: int) -> List[Dict[str, Any]]:
    """Get all image tags for a character.
    
    Args:
        conn: Database connection
        character_id: ID of the character
        
    Returns:
        List of tag dictionaries
    """
    try:
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT t.*, i.title as image_title, i.filename as image_filename, i.path as image_path
        FROM image_character_tags t
        JOIN images i ON t.image_id = i.id
        WHERE t.character_id = ?
        ORDER BY t.created_at DESC
        ''', (character_id,))
        
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"Error getting character image tags: {e}")
        return []


def create_character_details_table(conn: sqlite3.Connection) -> None:
    """Create the character_details table if it doesn't exist.
    
    This table stores miscellaneous details about characters like traits, 
    background info, personality characteristics, etc.
    
    Args:
        conn: Database connection
    """
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS character_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        character_id INTEGER NOT NULL,
        detail_text TEXT NOT NULL,
        detail_type TEXT DEFAULT 'GENERAL',
        sequence_number INTEGER DEFAULT 0,
        FOREIGN KEY (character_id) REFERENCES characters (id) ON DELETE CASCADE
    )
    ''')
    
    conn.commit()


def add_character_detail(conn: sqlite3.Connection, 
                       character_id: int, 
                       detail_text: str,
                       detail_type: str = "GENERAL") -> int:
    """Add a new detail to a character.
    
    Args:
        conn: Database connection
        character_id: ID of the character
        detail_text: Text describing the detail (e.g., "Afraid of heights")
        detail_type: Category of detail (e.g., "TRAIT", "BACKGROUND", "PERSONALITY")
        
    Returns:
        ID of the new detail or None if failed
    """
    try:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        # Get the next sequence number
        cursor.execute('''
        SELECT MAX(sequence_number) as max_seq
        FROM character_details
        WHERE character_id = ?
        ''', (character_id,))
        
        result = cursor.fetchone()
        next_seq = 0
        if result and result['max_seq'] is not None:
            next_seq = result['max_seq'] + 1
        
        cursor.execute('''
        INSERT INTO character_details (
            created_at, updated_at, character_id, detail_text, 
            detail_type, sequence_number
        ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (now, now, character_id, detail_text, detail_type, next_seq))
        
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error adding character detail: {e}")
        return None


def update_character_detail(conn: sqlite3.Connection,
                          detail_id: int,
                          detail_text: str = None,
                          detail_type: str = None) -> bool:
    """Update a character detail.
    
    Args:
        conn: Database connection
        detail_id: ID of the detail to update
        detail_text: New text for the detail
        detail_type: New type for the detail
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        # Build the query based on provided parameters
        update_parts = ['updated_at = ?']
        params = [now]
        
        if detail_text is not None:
            update_parts.append('detail_text = ?')
            params.append(detail_text)
            
        if detail_type is not None:
            update_parts.append('detail_type = ?')
            params.append(detail_type)
        
        # If nothing to update, return early
        if len(params) == 1:  # Only updated_at
            return True
            
        # Complete the query
        query = f'''
        UPDATE character_details
        SET {', '.join(update_parts)}
        WHERE id = ?
        '''
        
        params.append(detail_id)
        cursor.execute(query, tuple(params))
        
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error updating character detail: {e}")
        return False


def delete_character_detail(conn: sqlite3.Connection, detail_id: int) -> bool:
    """Delete a character detail.
    
    Args:
        conn: Database connection
        detail_id: ID of the detail to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()
        
        cursor.execute('''
        DELETE FROM character_details
        WHERE id = ?
        ''', (detail_id,))
        
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error deleting character detail: {e}")
        return False


def get_character_details(conn: sqlite3.Connection, character_id: int) -> List[Dict[str, Any]]:
    """Get all details for a character.
    
    Args:
        conn: Database connection
        character_id: ID of the character
        
    Returns:
        List of detail dictionaries
    """
    try:
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT *
        FROM character_details
        WHERE character_id = ?
        ORDER BY sequence_number, created_at
        ''', (character_id,))
        
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"Error getting character details: {e}")
        return []


def update_character_detail_sequence(conn: sqlite3.Connection, 
                                  detail_id: int, 
                                  new_sequence: int) -> bool:
    """Update the sequence number of a character detail.
    
    Args:
        conn: Database connection
        detail_id: ID of the detail
        new_sequence: New sequence number
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
        UPDATE character_details
        SET sequence_number = ?, updated_at = ?
        WHERE id = ?
        ''', (new_sequence, now, detail_id))
        
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error updating character detail sequence: {e}")
        return False 


def get_quick_event_tagged_characters(conn: sqlite3.Connection, quick_event_id: int) -> List[Dict[str, Any]]:
    """Get all characters tagged in a quick event (alias for get_quick_event_characters).
    
    Args:
        conn: Database connection
        quick_event_id: ID of the quick event
        
    Returns:
        List of dictionaries with character data
    """
    return get_quick_event_characters(conn, quick_event_id)


def search_quick_events(conn: sqlite3.Connection, story_id: int, 
                     text_query: Optional[str] = None,
                     character_id: Optional[int] = None,
                     from_date: Optional[str] = None,
                     to_date: Optional[str] = None,
                     limit: int = 100) -> List[Dict[str, Any]]:
    """Search quick events with various filters.
    
    Args:
        conn: Database connection
        story_id: ID of the story to search in
        text_query: Optional text to search for in the event content
        character_id: Optional character ID to filter by (either owner or tagged)
        from_date: Optional start date in ISO format (YYYY-MM-DD)
        to_date: Optional end date in ISO format (YYYY-MM-DD)
        limit: Maximum number of results to return
        
    Returns:
        List of dictionaries with quick event data
    """
    try:
        cursor = conn.cursor()
        
        print(f"DEBUG DB - search_quick_events called with: story_id={story_id}, character_id={character_id}, text_query={text_query}")
        
        # Build the base query for quick events with characters
        query = """
        SELECT DISTINCT qe.* FROM quick_events qe
        LEFT JOIN characters c ON qe.character_id = c.id
        LEFT JOIN quick_event_characters qec ON qe.id = qec.quick_event_id
        WHERE c.story_id = ?
        """
        params = [story_id]
        
        # Add filters
        if text_query:
            query += " AND qe.text LIKE ?"
            params.append(f"%{text_query}%")
            
        if character_id:
            query += " AND (qe.character_id = ? OR qec.character_id = ?)"
            params.extend([character_id, character_id])
            
        if from_date:
            query += " AND qe.created_at >= ?"
            params.append(f"{from_date}T00:00:00")
            
        if to_date:
            query += " AND qe.created_at <= ?"
            params.append(f"{to_date}T23:59:59")
            
        # Add a query to get events with NULL character_id
        # Anonymously created events don't have a character_id to link to story_id,
        # so we need to query them separately
        query_null_character = """
        SELECT qe.* FROM quick_events qe
        JOIN quick_event_images qei ON qe.id = qei.quick_event_id
        JOIN images i ON qei.image_id = i.id
        WHERE qe.character_id IS NULL
        AND i.story_id = ?
        """
        params_null = [story_id]
        
        if text_query:
            query_null_character += " AND qe.text LIKE ?"
            params_null.append(f"%{text_query}%")
            
        if from_date:
            query_null_character += " AND qe.created_at >= ?"
            params_null.append(f"{from_date}T00:00:00")
            
        if to_date:
            query_null_character += " AND qe.created_at <= ?"
            params_null.append(f"{to_date}T23:59:59")
        
        # Combine both queries with UNION
        full_query = f"{query} UNION {query_null_character} ORDER BY created_at DESC LIMIT ?"
        combined_params = params + params_null + [limit]
        
        print(f"DEBUG DB - SQL Query: {full_query}")
        print(f"DEBUG DB - Parameters: {combined_params}")
        
        cursor.execute(full_query, tuple(combined_params))
        rows = cursor.fetchall()
        
        print(f"DEBUG DB - Found {len(rows)} results")
        
        # Convert rows to dictionaries and return
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"Error searching quick events: {e}")
        print(f"DEBUG DB - Error: {e}")
        return []


def get_story_characters_with_events(conn: sqlite3.Connection, story_id: int) -> List[Dict[str, Any]]:
    """Get characters in a story that have quick events (either as owner or tagged).
    
    Args:
        conn: Database connection
        story_id: ID of the story
        
    Returns:
        List of dictionaries with character data
    """
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT DISTINCT c.* FROM characters c
        LEFT JOIN quick_events qe ON c.id = qe.character_id
        LEFT JOIN quick_event_characters qec ON c.id = qec.character_id
        WHERE c.story_id = ? AND (qe.id IS NOT NULL OR qec.quick_event_id IS NOT NULL)
        ORDER BY c.name
        """, (story_id,))
        
        rows = cursor.fetchall()
        
        # Convert rows to dictionaries and return
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"Error getting characters with events: {e}")
        return []


# Scene-QuickEvent association functions
def add_quick_event_to_scene(conn: sqlite3.Connection, 
                           scene_event_id: int, 
                           quick_event_id: int) -> int:
    """Associate a quick event with a scene.
    
    Args:
        conn: Database connection
        scene_event_id: ID of the scene event
        quick_event_id: ID of the quick event
        
    Returns:
        ID of the created association, or None if failed
    """
    try:
        cursor = conn.cursor()
        
        # Get the next sequence number for this scene
        cursor.execute('''
        SELECT MAX(sequence_number) as max_seq
        FROM scene_quick_events
        WHERE scene_event_id = ?
        ''', (scene_event_id,))
        
        result = cursor.fetchone()
        sequence_number = result['max_seq'] + 1 if result and result['max_seq'] is not None else 0
        
        # Insert the association
        cursor.execute('''
        INSERT INTO scene_quick_events (
            scene_event_id, quick_event_id, sequence_number
        ) VALUES (?, ?, ?)
        ''', (scene_event_id, quick_event_id, sequence_number))
        
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error adding quick event to scene: {e}")
        conn.rollback()
        return None


def remove_quick_event_from_scene(conn: sqlite3.Connection, 
                                scene_event_id: int, 
                                quick_event_id: int) -> bool:
    """Remove a quick event from a scene.
    
    Args:
        conn: Database connection
        scene_event_id: ID of the scene event
        quick_event_id: ID of the quick event
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()
        
        cursor.execute('''
        DELETE FROM scene_quick_events
        WHERE scene_event_id = ? AND quick_event_id = ?
        ''', (scene_event_id, quick_event_id))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error removing quick event from scene: {e}")
        conn.rollback()
        return False


def get_scene_quick_events(conn: sqlite3.Connection, scene_event_id: int) -> List[Dict[str, Any]]:
    """Get all quick events associated with a scene.
    
    Args:
        conn: Database connection
        scene_event_id: ID of the scene event
        
    Returns:
        List of quick event dictionaries with association data
    """
    try:
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT qe.*, 
               CASE WHEN qe.character_id IS NULL THEN 'Anonymous' ELSE c.name END as character_name, 
               sqe.sequence_number, 
               sqe.id as association_id
        FROM quick_events qe
        LEFT JOIN characters c ON qe.character_id = c.id
        JOIN scene_quick_events sqe ON qe.id = sqe.quick_event_id
        WHERE sqe.scene_event_id = ?
        ORDER BY sqe.sequence_number, qe.created_at
        ''', (scene_event_id,))
        
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"Error getting scene quick events: {e}")
        return []


def get_quick_event_scenes(conn: sqlite3.Connection, quick_event_id: int) -> List[Dict[str, Any]]:
    """Get all scenes that contain a specific quick event.
    
    Args:
        conn: Database connection
        quick_event_id: ID of the quick event
        
    Returns:
        List of event dictionaries
    """
    try:
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT e.*, sqe.sequence_number
        FROM events e
        JOIN scene_quick_events sqe ON e.id = sqe.scene_event_id
        WHERE sqe.quick_event_id = ? AND e.event_type = 'SCENE'
        ORDER BY e.sequence_number
        ''', (quick_event_id,))
        
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"Error getting quick event scenes: {e}")
        return []


def get_unassigned_quick_events(conn: sqlite3.Connection, story_id: int) -> List[Dict[str, Any]]:
    """Get all quick events that aren't assigned to any scene in the story.
    
    Args:
        conn: Database connection
        story_id: ID of the story
        
    Returns:
        List of quick event dictionaries
    """
    try:
        cursor = conn.cursor()
        
        # First query: Get quick events with characters in this story that aren't assigned to any scene
        character_query = '''
        SELECT qe.*, c.name as character_name
        FROM quick_events qe
        JOIN characters c ON qe.character_id = c.id
        WHERE c.story_id = ? AND qe.id NOT IN (
            SELECT quick_event_id FROM scene_quick_events
        )
        '''
        
        # Second query: Get anonymous events (NULL character_id) linked to this story through images
        anonymous_query = '''
        SELECT DISTINCT qe.*, 'Anonymous' as character_name
        FROM quick_events qe
        JOIN quick_event_images qei ON qe.id = qei.quick_event_id
        JOIN images i ON qei.image_id = i.id
        WHERE qe.character_id IS NULL 
        AND i.story_id = ?
        AND qe.id NOT IN (
            SELECT quick_event_id FROM scene_quick_events
        )
        '''
        
        # Combine both queries with UNION
        full_query = f"{character_query} UNION {anonymous_query} ORDER BY created_at DESC"
        
        cursor.execute(full_query, (story_id, story_id))
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"Error getting unassigned quick events: {e}")
        return []


def add_image_to_scene(conn: sqlite3.Connection, 
                           scene_event_id: int, 
                           image_id: int) -> int:
    """Associate an image directly with a scene.
    
    Args:
        conn: Database connection
        scene_event_id: ID of the scene event
        image_id: ID of the image
        
    Returns:
        ID of the created association, or None if failed
    """
    try:
        cursor = conn.cursor()
        
        # Get the next sequence number for this scene
        cursor.execute('''
        SELECT MAX(sequence_number) as max_seq
        FROM scene_images
        WHERE scene_event_id = ?
        ''', (scene_event_id,))
        
        result = cursor.fetchone()
        sequence_number = result['max_seq'] + 1 if result and result['max_seq'] is not None else 0
        
        # Insert the association
        cursor.execute('''
        INSERT INTO scene_images (
            scene_event_id, image_id, sequence_number
        ) VALUES (?, ?, ?)
        ''', (scene_event_id, image_id, sequence_number))
        
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error adding image to scene: {e}")
        conn.rollback()
        return None


def remove_image_from_scene(conn: sqlite3.Connection, 
                                scene_event_id: int, 
                                image_id: int) -> bool:
    """Remove an image's direct association with a scene.
    
    Args:
        conn: Database connection
        scene_event_id: ID of the scene event
        image_id: ID of the image
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()
        
        cursor.execute('''
        DELETE FROM scene_images
        WHERE scene_event_id = ? AND image_id = ?
        ''', (scene_event_id, image_id))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error removing image from scene: {e}")
        conn.rollback()
        return False


def get_scene_images(conn: sqlite3.Connection, scene_event_id: int) -> List[Dict[str, Any]]:
    """Get all images directly associated with a scene.
    
    Args:
        conn: Database connection
        scene_event_id: ID of the scene event
        
    Returns:
        List of image dictionaries with association data
    """
    try:
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT i.*, si.sequence_number, si.id as association_id
        FROM images i
        JOIN scene_images si ON i.id = si.image_id
        WHERE si.scene_event_id = ?
        ORDER BY si.sequence_number, i.created_at DESC
        ''', (scene_event_id,))
        
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"Error getting scene images: {e}")
        return []


def get_image_scenes(conn: sqlite3.Connection, image_id: int) -> List[Dict[str, Any]]:
    """Get all scenes that have a direct association with an image.
    
    Args:
        conn: Database connection
        image_id: ID of the image
        
    Returns:
        List of event dictionaries with scene data
    """
    try:
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT e.*, si.sequence_number
        FROM events e
        JOIN scene_images si ON e.id = si.scene_event_id
        WHERE si.image_id = ? AND e.event_type = 'SCENE'
        ORDER BY e.sequence_number
        ''', (image_id,))
        
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"Error getting image scenes: {e}")
        return []


def update_character_last_tagged(conn, story_id: int, character_id: int) -> None:
    """Update the last tagged timestamp for a character in a story.
    
    Args:
        conn: Database connection
        story_id: ID of the story
        character_id: ID of the character
    """
    try:
        print(f"DEBUG: update_character_last_tagged called for story_id={story_id}, character_id={character_id}")
        
        # Create the table if it doesn't exist
        create_character_last_tagged_table(conn)
        
        cursor = conn.cursor()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"DEBUG: Setting last_tagged to {current_time}")
        
        # Check if an entry already exists for this character in this story
        cursor.execute('''
        SELECT id FROM character_last_tagged
        WHERE story_id = ? AND character_id = ?
        ''', (story_id, character_id))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing entry
            cursor.execute('''
            UPDATE character_last_tagged
            SET last_tagged_at = ?
            WHERE story_id = ? AND character_id = ?
            ''', (current_time, story_id, character_id))
        else:
            # Create new entry
            cursor.execute('''
            INSERT INTO character_last_tagged (story_id, character_id, last_tagged_at)
            VALUES (?, ?, ?)
            ''', (story_id, character_id, current_time))
        
        conn.commit()
        
        # Verify the update
        cursor.execute('''
        SELECT last_tagged_at FROM character_last_tagged
        WHERE story_id = ? AND character_id = ?
        ''', (story_id, character_id))
        
        result = cursor.fetchone()
        if result:
            print(f"DEBUG: Updated timestamp is: {result[0]}")
        else:
            print("DEBUG: Failed to retrieve updated timestamp!")
    except Exception as e:
        print(f"Error updating character last tagged timestamp: {e}")
        # Continue without updating the timestamp

def get_characters_by_last_tagged(conn, story_id: int) -> List[Dict[str, Any]]:
    """Get all characters for a story ordered by last tagged timestamp.
    
    Args:
        conn: Database connection
        story_id: ID of the story
    
    Returns:
        List of character dictionaries ordered by most recently tagged first
    """
    try:
        print(f"DEBUG: get_characters_by_last_tagged called for story ID {story_id}")
        cursor = conn.cursor()
        
        # First ensure the table exists
        create_character_last_tagged_table(conn)
        
        # Join characters with character_last_tagged table, using LEFT JOIN to include
        # characters that have never been tagged
        cursor.execute('''
        SELECT c.id, c.name, c.avatar_path, c.story_id, 
               clt.last_tagged_at as last_tagged
        FROM characters c
        LEFT JOIN character_last_tagged clt ON c.id = clt.character_id AND c.story_id = clt.story_id
        WHERE c.story_id = ?
        ORDER BY COALESCE(clt.last_tagged_at, '1970-01-01') DESC, c.name
        ''', (story_id,))
        
        results = [dict(row) for row in cursor.fetchall()]
        
        # Debug dump of all character data with timestamps
        print("DEBUG: Character data from database:")
        for i, character in enumerate(results):
            print(f"  {i+1}. ID: {character['id']}, Name: {character['name']}, Last Tagged: {character.get('last_tagged', 'Never')}")
            
        return results
    except Exception as e:
        print(f"Error in get_characters_by_last_tagged: {e}")
        # In case of error, fall back to regular character retrieval
        return get_story_characters(conn, story_id)

def create_character_last_tagged_table(conn: sqlite3.Connection) -> None:
    """Create the character_last_tagged table if it doesn't exist.
    
    Args:
        conn: Database connection
    """
    cursor = conn.cursor()
    
    # Create character_last_tagged table to track when characters were last tagged in a story
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS character_last_tagged (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        story_id INTEGER NOT NULL,
        character_id INTEGER NOT NULL,
        last_tagged_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (story_id) REFERENCES stories (id) ON DELETE CASCADE,
        FOREIGN KEY (character_id) REFERENCES characters (id) ON DELETE CASCADE,
        UNIQUE(story_id, character_id)
    )
    ''')
    
    # Create indexes for efficient querying
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_character_last_tagged_story_id ON character_last_tagged(story_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_character_last_tagged_character_id ON character_last_tagged(character_id)')
    
    conn.commit()