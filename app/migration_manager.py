#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Migration manager for The Plot Thickens application.

This module handles database migrations to ensure schema compatibility.
"""

import os
import sqlite3
from typing import Optional, List, Dict, Any
import logging

from app.migrations.migrate_relationships import migrate_relationships

# Set up logging
logger = logging.getLogger(__name__)


def check_and_run_migrations(db_path: str) -> bool:
    """Check if migrations are needed and run them.
    
    Args:
        db_path: Path to the database file
        
    Returns:
        True if all migrations were successful or not needed, False otherwise
    """
    try:
        # Create connection to database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Check if any migrations are needed
        migrations_needed = get_pending_migrations(conn)
        
        if not migrations_needed:
            logger.info("No migrations needed.")
            conn.close()
            return True
        
        logger.info(f"The following migrations are needed: {', '.join(migrations_needed)}")
        
        # Run needed migrations
        success = True
        for migration in migrations_needed:
            if migration == 'relationship_migration_v1':
                logger.info("Running relationship migration...")
                success = success and migrate_relationships(db_path)
            # Add other migrations as needed
        
        conn.close()
        return success
    except Exception as e:
        logger.error(f"Error checking or running migrations: {e}")
        return False


def get_pending_migrations(conn: sqlite3.Connection) -> List[str]:
    """Get a list of pending migrations.
    
    Args:
        conn: Database connection
        
    Returns:
        List of migration names that need to be run
    """
    cursor = conn.cursor()
    
    # Check if the migration_status table exists
    cursor.execute('''
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='migration_status'
    ''')
    
    migration_table_exists = cursor.fetchone() is not None
    
    if not migration_table_exists:
        # Create the migration_status table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS migration_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            migration_name TEXT NOT NULL UNIQUE,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        conn.commit()
    
    # Get list of completed migrations
    cursor.execute('SELECT migration_name FROM migration_status')
    completed_migrations = {row['migration_name'] for row in cursor.fetchall()}
    
    # Check if the app_settings table exists and contains migration info
    cursor.execute('''
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='app_settings'
    ''')
    
    if cursor.fetchone():
        cursor.execute('''
        SELECT key, value FROM app_settings
        WHERE key LIKE '%migration%'
        ''')
        
        for row in cursor.fetchall():
            if row['value'] == 'true' and row['key'] == 'relationship_migration_complete':
                completed_migrations.add('relationship_migration_v1')
    
    # Get all available migrations
    all_migrations = [
        'relationship_migration_v1',
        # Add other migrations as they are developed
    ]
    
    # Check if we need to run the relationship migration
    relationship_migration_needed = not check_relationship_migration_needed(conn)
    
    # If relationship migration isn't needed, mark it as completed
    if not relationship_migration_needed and 'relationship_migration_v1' not in completed_migrations:
        completed_migrations.add('relationship_migration_v1')
    
    # Get list of pending migrations
    pending_migrations = [m for m in all_migrations if m not in completed_migrations]
    
    # If relationship migration is needed, ensure it's in the list
    if relationship_migration_needed and 'relationship_migration_v1' not in pending_migrations:
        pending_migrations.append('relationship_migration_v1')
    
    return pending_migrations


def check_relationship_migration_needed(conn: sqlite3.Connection) -> bool:
    """Check if the relationship migration is needed.
    
    Args:
        conn: Database connection
        
    Returns:
        True if migration is needed, False otherwise
    """
    cursor = conn.cursor()
    
    # Check if the relationships table exists
    cursor.execute('''
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='relationships'
    ''')
    
    if not cursor.fetchone():
        # No relationships table, no migration needed
        return False
    
    # Check if the relationship_type column exists and has values
    cursor.execute("PRAGMA table_info(relationships)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'relationship_type' not in columns:
        # No relationship_type column, migration not needed
        return False
    
    # Check if any relationships use the old relationship_type column
    cursor.execute('''
    SELECT COUNT(*) FROM relationships 
    WHERE relationship_type IS NOT NULL 
    AND (relationship_type_id IS NULL OR relationship_type_id = 0)
    ''')
    
    old_format_count = cursor.fetchone()[0]
    
    # Migration is needed if there are relationships using the old format
    return old_format_count > 0


def register_migration_complete(db_path: str, migration_name: str) -> bool:
    """Register a migration as complete.
    
    Args:
        db_path: Path to the database file
        migration_name: Name of the completed migration
        
    Returns:
        True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Ensure the migration_status table exists
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS migration_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            migration_name TEXT NOT NULL UNIQUE,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Register the migration as complete
        cursor.execute('''
        INSERT OR REPLACE INTO migration_status (migration_name, completed_at)
        VALUES (?, CURRENT_TIMESTAMP)
        ''', (migration_name,))
        
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"Error registering migration completion: {e}")
        return False 