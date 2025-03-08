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
        os.makedirs(folder_path, exist_ok=True)
        os.makedirs(os.path.join(folder_path, "images"), exist_ok=True)
    
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
def create_character(conn: sqlite3.Connection, name: str, story_id: int, aliases: Optional[str] = None,
                    is_main_character: bool = False, age_value: Optional[int] = None, age_category: Optional[str] = None,
                    gender: str = "NOT_SPECIFIED", avatar_path: Optional[str] = None) -> int:
    """Create a new character in the database."""
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO characters (name, story_id, aliases, is_main_character, age_value, age_category, gender, avatar_path)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, story_id, aliases, 1 if is_main_character else 0, age_value, age_category, gender, avatar_path))
    
    conn.commit()
    return cursor.lastrowid


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