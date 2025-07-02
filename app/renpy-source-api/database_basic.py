"""
Database integration for Ren'Py source analysis.
"""

import sqlite3
from typing import Dict, Any, Optional

class RenpyDatabase:
    """Database interface for Ren'Py analysis data."""
    
    def __init__(self, db_connection: sqlite3.Connection):
        self.conn = db_connection
        self.ensure_renpy_tables()
    
    def ensure_renpy_tables(self) -> None:
        """Create Ren'Py-specific tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Basic projects table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS renpy_projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            story_id INTEGER NOT NULL UNIQUE,
            game_folder_path TEXT NOT NULL,
            is_analyzed INTEGER DEFAULT 0,
            FOREIGN KEY (story_id) REFERENCES stories (id) ON DELETE CASCADE
        )
        ''')
        
        self.conn.commit()
    
    def create_or_update_project(self, story_id: int, game_folder_path: str) -> int:
        """Create or update a Ren'Py project record."""
        cursor = self.conn.cursor()
        
        # Check if project exists
        cursor.execute('SELECT id FROM renpy_projects WHERE story_id = ?', (story_id,))
        row = cursor.fetchone()
        
        if row:
            # Update existing
            project_id = row[0]
            cursor.execute('''
            UPDATE renpy_projects 
            SET game_folder_path = ? 
            WHERE id = ?
            ''', (game_folder_path, project_id))
        else:
            # Create new
            cursor.execute('''
            INSERT INTO renpy_projects (story_id, game_folder_path)
            VALUES (?, ?)
            ''', (story_id, game_folder_path))
            project_id = cursor.lastrowid
        
        self.conn.commit()
        return project_id 