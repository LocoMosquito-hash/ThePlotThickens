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
        FOREIGN KEY (story_id) REFERENCES stories (id) ON DELETE CASCADE
    )
    ''')
    
    # Create image_tags table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS image_tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        x REAL,
        y REAL,
        width REAL,
        height REAL,
        image_id INTEGER NOT NULL,
        character_id INTEGER NOT NULL,
        FOREIGN KEY (image_id) REFERENCES images (id) ON DELETE CASCADE,
        FOREIGN KEY (character_id) REFERENCES characters (id) ON DELETE CASCADE
    )
    ''')
    
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
    """Initialize the database and create tables if they don't exist.
    
    Args:
        db_path: Path to the SQLite database, can be a URI format (sqlite:///path) or direct path
        
    Returns:
        sqlite3.Connection: Database connection
    """
    # Handle sqlite:/// URI format
    if db_path.startswith('sqlite:///'):
        db_path = db_path[10:]  # Remove 'sqlite:///'
    
    # Ensure directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    conn = create_connection(db_path)
    create_tables(conn)
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
    cursor.execute(query, params)
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
        (character_id,)
    )
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