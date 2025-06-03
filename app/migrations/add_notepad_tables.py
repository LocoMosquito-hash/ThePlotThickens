#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Migration to add Story Notepad tables.

This migration adds the necessary tables for storing plot details and plot questions
for the Story Notepad feature.
"""

import sqlite3
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def migrate_add_notepad_tables(db_path: str) -> bool:
    """Add tables for Story Notepad functionality.
    
    Args:
        db_path: Path to the database file
        
    Returns:
        True if migration was successful, False otherwise
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        logger.info("Adding Story Notepad tables...")
        
        # Create plot_details table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS plot_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            is_scratched BOOLEAN DEFAULT FALSE,
            order_index INTEGER DEFAULT 0,
            character_refs TEXT DEFAULT '',  -- JSON array of character IDs mentioned
            custom_data TEXT DEFAULT '{}',   -- JSON for additional data
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (story_id) REFERENCES stories (id) ON DELETE CASCADE
        )
        ''')
        
        # Create plot_questions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS plot_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            is_scratched BOOLEAN DEFAULT FALSE,
            order_index INTEGER DEFAULT 0,
            character_refs TEXT DEFAULT '',  -- JSON array of character IDs mentioned
            custom_data TEXT DEFAULT '{}',   -- JSON for additional data
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (story_id) REFERENCES stories (id) ON DELETE CASCADE
        )
        ''')
        
        # Create plot_answers table (for answers to questions)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS plot_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            is_scratched BOOLEAN DEFAULT FALSE,
            order_index INTEGER DEFAULT 0,
            character_refs TEXT DEFAULT '',  -- JSON array of character IDs mentioned
            custom_data TEXT DEFAULT '{}',   -- JSON for additional data
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (question_id) REFERENCES plot_questions (id) ON DELETE CASCADE
        )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_plot_details_story_id ON plot_details(story_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_plot_details_order ON plot_details(story_id, order_index)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_plot_questions_story_id ON plot_questions(story_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_plot_questions_order ON plot_questions(story_id, order_index)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_plot_answers_question_id ON plot_answers(question_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_plot_answers_order ON plot_answers(question_id, order_index)')
        
        # Add triggers to update timestamps
        cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS update_plot_details_timestamp 
        AFTER UPDATE ON plot_details
        BEGIN
            UPDATE plot_details SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
        ''')
        
        cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS update_plot_questions_timestamp 
        AFTER UPDATE ON plot_questions
        BEGIN
            UPDATE plot_questions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
        ''')
        
        cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS update_plot_answers_timestamp 
        AFTER UPDATE ON plot_answers
        BEGIN
            UPDATE plot_answers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info("Story Notepad tables created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating Story Notepad tables: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False


def check_notepad_migration_needed(conn: sqlite3.Connection) -> bool:
    """Check if the notepad tables migration is needed.
    
    Args:
        conn: Database connection
        
    Returns:
        True if migration is needed, False otherwise
    """
    cursor = conn.cursor()
    
    # Check if the plot_details table exists
    cursor.execute('''
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='plot_details'
    ''')
    
    return cursor.fetchone() is None


if __name__ == "__main__":
    # Test the migration
    import os
    test_db = "test_notepad_migration.db"
    
    try:
        success = migrate_add_notepad_tables(test_db)
        print(f"Migration test result: {'SUCCESS' if success else 'FAILED'}")
        
        # Verify tables were created
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['plot_details', 'plot_questions', 'plot_answers']
        for table in expected_tables:
            if table in tables:
                print(f"✓ Table {table} created successfully")
            else:
                print(f"✗ Table {table} NOT created")
        
        conn.close()
        
        # Clean up test database
        if os.path.exists(test_db):
            os.remove(test_db)
            
    except Exception as e:
        print(f"Migration test failed: {e}") 