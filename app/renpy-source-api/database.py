"""
Database integration for Ren'Py source analysis.

This module extends the existing database schema with Ren'Py-specific tables
for caching analysis results and providing fast queries.
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from .exceptions import RenpyDatabaseError


class RenpyDatabase:
    """
    Database interface for storing and retrieving Ren'Py analysis data.
    
    This class extends the existing Plot Thickens database with tables
    specifically for Ren'Py project analysis and caching.
    """
    
    def __init__(self, db_connection: sqlite3.Connection):
        """
        Initialize the Ren'Py database interface.
        
        Args:
            db_connection: Existing database connection from the main app
        """
        self.conn = db_connection
        self.ensure_renpy_tables()
    
    def ensure_renpy_tables(self) -> None:
        """Create Ren'Py-specific tables if they don't exist."""
        try:
            cursor = self.conn.cursor()
            
            # Ren'Py projects table - links to existing stories table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS renpy_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                story_id INTEGER NOT NULL UNIQUE,
                game_folder_path TEXT NOT NULL,
                last_analyzed TIMESTAMP,
                analysis_version TEXT DEFAULT '0.1.0',
                
                -- Project metadata
                total_rpy_files INTEGER DEFAULT 0,
                total_lines INTEGER DEFAULT 0,
                total_dialogue_lines INTEGER DEFAULT 0,
                total_labels INTEGER DEFAULT 0,
                total_menus INTEGER DEFAULT 0,
                
                -- Analysis status
                is_analyzed INTEGER DEFAULT 0,
                analysis_error TEXT,
                
                FOREIGN KEY (story_id) REFERENCES stories (id) ON DELETE CASCADE
            )
            ''')
            
            # Ren'Py files table - tracks individual .rpy files
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS renpy_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                project_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                relative_path TEXT NOT NULL,
                file_hash TEXT,
                file_size INTEGER,
                last_modified TIMESTAMP,
                
                -- File statistics
                line_count INTEGER DEFAULT 0,
                dialogue_count INTEGER DEFAULT 0,
                label_count INTEGER DEFAULT 0,
                menu_count INTEGER DEFAULT 0,
                
                FOREIGN KEY (project_id) REFERENCES renpy_projects (id) ON DELETE CASCADE,
                UNIQUE(project_id, relative_path)
            )
            ''')
            
            # Ren'Py labels table - tracks all labels (scenes/functions)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS renpy_labels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                project_id INTEGER NOT NULL,
                file_id INTEGER NOT NULL,
                label_name TEXT NOT NULL,
                line_number INTEGER,
                
                -- Label metadata
                label_type TEXT DEFAULT 'scene',  -- 'scene', 'function', 'menu', etc.
                description TEXT,
                
                -- Flow analysis
                is_entry_point INTEGER DEFAULT 0,
                is_ending INTEGER DEFAULT 0,
                jump_targets TEXT,  -- JSON array of target labels
                call_targets TEXT,  -- JSON array of called labels
                menu_choices TEXT,  -- JSON array of menu options
                
                FOREIGN KEY (project_id) REFERENCES renpy_projects (id) ON DELETE CASCADE,
                FOREIGN KEY (file_id) REFERENCES renpy_files (id) ON DELETE CASCADE,
                UNIQUE(project_id, label_name)
            )
            ''')
            
            # Ren'Py dialogue table - stores all dialogue lines
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS renpy_dialogue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                project_id INTEGER NOT NULL,
                file_id INTEGER NOT NULL,
                label_id INTEGER,
                line_number INTEGER,
                
                -- Dialogue content
                speaker_code TEXT,    -- Raw speaker (e.g., 'e', 'narrator')
                speaker_name TEXT,    -- Resolved character name
                dialogue_text TEXT NOT NULL,
                
                -- Context
                preceding_images TEXT,  -- JSON array of images shown before this line
                preceding_audio TEXT,   -- JSON array of audio played before this line
                
                -- Search optimization
                dialogue_text_lower TEXT,  -- Lowercase version for fast searching
                
                FOREIGN KEY (project_id) REFERENCES renpy_projects (id) ON DELETE CASCADE,
                FOREIGN KEY (file_id) REFERENCES renpy_files (id) ON DELETE CASCADE,
                FOREIGN KEY (label_id) REFERENCES renpy_labels (id) ON DELETE SET NULL
            )
            ''')
            
            # Ren'Py characters table - character definitions from .rpy files
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS renpy_characters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                project_id INTEGER NOT NULL,
                file_id INTEGER NOT NULL,
                
                -- Character definition
                character_code TEXT NOT NULL,     -- e.g., 'e', 'protagonist'
                character_name TEXT,              -- e.g., 'Eileen', 'You'
                character_color TEXT,             -- Hex color from definition
                definition_line INTEGER,
                
                -- Statistics (calculated during analysis)
                dialogue_count INTEGER DEFAULT 0,
                word_count INTEGER DEFAULT 0,
                
                FOREIGN KEY (project_id) REFERENCES renpy_projects (id) ON DELETE CASCADE,
                FOREIGN KEY (file_id) REFERENCES renpy_files (id) ON DELETE CASCADE,
                UNIQUE(project_id, character_code)
            )
            ''')
            
            # Ren'Py assets table - tracks images, audio, video references
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS renpy_assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                project_id INTEGER NOT NULL,
                file_id INTEGER NOT NULL,
                
                -- Asset information
                asset_type TEXT NOT NULL,  -- 'image', 'audio', 'video'
                asset_name TEXT,           -- Defined name (e.g., 'bg beach')
                asset_filename TEXT,       -- Actual filename
                statement_type TEXT,       -- 'image', 'scene', 'show', 'play', etc.
                line_number INTEGER,
                
                -- Usage tracking
                is_definition INTEGER DEFAULT 0,  -- 1 if this is an asset definition
                usage_count INTEGER DEFAULT 1,
                
                FOREIGN KEY (project_id) REFERENCES renpy_projects (id) ON DELETE CASCADE,
                FOREIGN KEY (file_id) REFERENCES renpy_files (id) ON DELETE CASCADE
            )
            ''')
            
            # Ren'Py menus table - tracks menu choices and branching
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS renpy_menus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                project_id INTEGER NOT NULL,
                file_id INTEGER NOT NULL,
                label_id INTEGER,
                line_number INTEGER,
                
                -- Menu structure
                menu_text TEXT,            -- Optional menu prompt text
                choices TEXT NOT NULL,     -- JSON array of choice objects
                
                FOREIGN KEY (project_id) REFERENCES renpy_projects (id) ON DELETE CASCADE,
                FOREIGN KEY (file_id) REFERENCES renpy_files (id) ON DELETE CASCADE,
                FOREIGN KEY (label_id) REFERENCES renpy_labels (id) ON DELETE SET NULL
            )
            ''')
            
            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_renpy_dialogue_text ON renpy_dialogue(dialogue_text_lower)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_renpy_dialogue_speaker ON renpy_dialogue(speaker_code)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_renpy_dialogue_label ON renpy_dialogue(label_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_renpy_labels_name ON renpy_labels(label_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_renpy_assets_type ON renpy_assets(asset_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_renpy_assets_filename ON renpy_assets(asset_filename)')
            
            self.conn.commit()
            
        except sqlite3.Error as e:
            raise RenpyDatabaseError(f"Failed to create Ren'Py tables: {e}")
    
    def create_or_update_project(self, story_id: int, game_folder_path: str) -> int:
        """
        Create or update a Ren'Py project record.
        
        Args:
            story_id: ID of the story from the main stories table
            game_folder_path: Path to the game folder containing .rpy files
            
        Returns:
            Project ID
        """
        try:
            cursor = self.conn.cursor()
            
            # Check if project already exists
            cursor.execute('''
            SELECT id FROM renpy_projects WHERE story_id = ?
            ''', (story_id,))
            
            row = cursor.fetchone()
            
            if row:
                # Update existing project
                project_id = row[0]
                cursor.execute('''
                UPDATE renpy_projects 
                SET game_folder_path = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                ''', (game_folder_path, project_id))
            else:
                # Create new project
                cursor.execute('''
                INSERT INTO renpy_projects (story_id, game_folder_path)
                VALUES (?, ?)
                ''', (story_id, game_folder_path))
                project_id = cursor.lastrowid
            
            self.conn.commit()
            return project_id
            
        except sqlite3.Error as e:
            raise RenpyDatabaseError(f"Failed to create/update project: {e}")
    
    def get_project_by_story_id(self, story_id: int) -> Optional[Dict[str, Any]]:
        """Get Ren'Py project data by story ID."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            SELECT * FROM renpy_projects WHERE story_id = ?
            ''', (story_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
            
        except sqlite3.Error as e:
            raise RenpyDatabaseError(f"Failed to get project: {e}")
    
    def mark_project_analyzed(self, project_id: int, stats: Dict[str, Any]) -> None:
        """Mark a project as analyzed and update statistics."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            UPDATE renpy_projects 
            SET is_analyzed = 1,
                last_analyzed = CURRENT_TIMESTAMP,
                total_rpy_files = ?,
                total_lines = ?,
                total_dialogue_lines = ?,
                total_labels = ?,
                total_menus = ?,
                analysis_error = NULL
            WHERE id = ?
            ''', (
                stats.get('total_rpy_files', 0),
                stats.get('total_lines', 0),
                stats.get('total_dialogue_lines', 0),
                stats.get('total_labels', 0),
                stats.get('total_menus', 0),
                project_id
            ))
            
            self.conn.commit()
            
        except sqlite3.Error as e:
            raise RenpyDatabaseError(f"Failed to mark project as analyzed: {e}")
    
    def clear_project_data(self, project_id: int) -> None:
        """Clear all analysis data for a project (for re-analysis)."""
        try:
            cursor = self.conn.cursor()
            
            # Clear all dependent tables (foreign keys will handle cascade)
            cursor.execute('DELETE FROM renpy_dialogue WHERE project_id = ?', (project_id,))
            cursor.execute('DELETE FROM renpy_menus WHERE project_id = ?', (project_id,))
            cursor.execute('DELETE FROM renpy_assets WHERE project_id = ?', (project_id,))
            cursor.execute('DELETE FROM renpy_characters WHERE project_id = ?', (project_id,))
            cursor.execute('DELETE FROM renpy_labels WHERE project_id = ?', (project_id,))
            cursor.execute('DELETE FROM renpy_files WHERE project_id = ?', (project_id,))
            
            # Reset project analysis status
            cursor.execute('''
            UPDATE renpy_projects 
            SET is_analyzed = 0,
                total_rpy_files = 0,
                total_lines = 0,
                total_dialogue_lines = 0,
                total_labels = 0,
                total_menus = 0
            WHERE id = ?
            ''', (project_id,))
            
            self.conn.commit()
            
        except sqlite3.Error as e:
            raise RenpyDatabaseError(f"Failed to clear project data: {e}") 