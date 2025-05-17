#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Migration script to convert existing relationships to the new relationship system.

This module handles the migration of relationship data from the old format to the new format.
"""

import os
import sqlite3
from typing import List, Dict, Any, Optional, Tuple

from app.relationships import (
    create_relationship_tables,
    initialize_relationship_categories, 
    initialize_relationship_types,
    get_relationship_categories,
    get_relationship_types
)


def migrate_relationships(db_path: str) -> bool:
    """Migrate existing relationships to the new relationship system.
    
    Args:
        db_path: Path to the database file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        
        # Check if we have old relationships to migrate
        has_old_relationships = check_for_old_relationships(conn)
        if not has_old_relationships:
            print("No old relationships found. Migration not needed.")
            return True
        
        # Initialize the new tables
        create_relationship_tables(conn)
        initialize_relationship_categories(conn)
        initialize_relationship_types(conn)
        
        # Get categories and relationship types for lookup
        categories = {cat['name'].upper(): cat['id'] for cat in get_relationship_categories(conn)}
        rel_types = {rel['name']: rel['id'] for rel in get_relationship_types(conn)}
        
        # Create a mapping of old relationship types to new relationship type IDs
        type_mapping = create_type_mapping(rel_types)
        
        # Migrate the old relationships
        migrate_old_relationships(conn, type_mapping)
        
        # Update the schema version or set a flag to indicate migration is complete
        set_migration_complete(conn)
        
        conn.close()
        print("Relationship migration completed successfully.")
        return True
    except Exception as e:
        print(f"Error migrating relationships: {e}")
        return False


def check_for_old_relationships(conn: sqlite3.Connection) -> bool:
    """Check if there are old relationships to migrate.
    
    Args:
        conn: Database connection
        
    Returns:
        True if old relationships exist, False otherwise
    """
    cursor = conn.cursor()
    
    # Check if the relationships table exists
    cursor.execute('''
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='relationships'
    ''')
    table_exists = cursor.fetchone() is not None
    
    if not table_exists:
        return False
    
    # Check if there are rows in the relationships table
    cursor.execute('SELECT COUNT(*) FROM relationships')
    count = cursor.fetchone()[0]
    
    # Check if the relationship_type column exists and has values
    cursor.execute("PRAGMA table_info(relationships)")
    columns = [col[1] for col in cursor.fetchall()]
    
    has_old_format = 'relationship_type' in columns
    
    # Check if any relationships use the old relationship_type column
    if has_old_format and count > 0:
        cursor.execute('''
        SELECT COUNT(*) FROM relationships 
        WHERE relationship_type IS NOT NULL 
        AND (relationship_type_id IS NULL OR relationship_type_id = 0)
        ''')
        old_format_count = cursor.fetchone()[0]
        return old_format_count > 0
    
    return False


def create_type_mapping(rel_types: Dict[str, int]) -> Dict[str, int]:
    """Create a mapping of old relationship type names to new relationship type IDs.
    
    Args:
        rel_types: Dictionary mapping relationship type names to IDs
        
    Returns:
        Dictionary mapping old relationship type strings to new relationship type IDs
    """
    # Define mappings from old relationship types to new ones
    # Format: {'OLD_TYPE': 'NEW_TYPE'}
    manual_mappings = {
        'FATHER': 'Father',
        'MOTHER': 'Mother',
        'SON': 'Son',
        'DAUGHTER': 'Daughter',
        'BROTHER': 'Brother',
        'SISTER': 'Sister',
        'HUSBAND': 'Husband',
        'WIFE': 'Wife',
        'FRIEND': 'Friend',
        'BOYFRIEND': 'Boyfriend',
        'GIRLFRIEND': 'Girlfriend',
        'BOSS': 'Boss',
        'EMPLOYEE': 'Employee',
        'COWORKER': 'Coworker',
        'COLLEAGUE': 'Colleague',
        'ROOMMATE': 'Roommate',
        'CLASSMATE': 'Classmate',
        'TEACHER': 'Teacher',
        'STUDENT': 'Student',
        'MENTOR': 'Mentor',
        'MENTEE': 'Mentee',
        'RIVAL': 'Rival',
        'ENEMY': 'Enemy',
        'SPOUSE': 'Spouse',
        'PARTNER': 'Partner',
        'EX-BOYFRIEND': 'Ex-boyfriend',
        'EX-GIRLFRIEND': 'Ex-girlfriend',
        'EX-HUSBAND': 'Ex-husband',
        'EX-WIFE': 'Ex-wife',
        'GRANDFATHER': 'Grandfather',
        'GRANDMOTHER': 'Grandmother',
        'GRANDSON': 'Grandson',
        'GRANDDAUGHTER': 'Granddaughter',
        'UNCLE': 'Uncle',
        'AUNT': 'Aunt',
        'NEPHEW': 'Nephew',
        'NIECE': 'Niece',
        'COUSIN': 'Cousin',
        # Add more mappings as needed
    }
    
    # Create the mapping from old types to new type IDs
    result = {}
    for old_type, new_type in manual_mappings.items():
        # If the new type exists in our set of relationship types
        if new_type in rel_types:
            result[old_type] = rel_types[new_type]
    
    return result


def migrate_old_relationships(conn: sqlite3.Connection, type_mapping: Dict[str, int]) -> None:
    """Migrate old relationships to the new format.
    
    Args:
        conn: Database connection
        type_mapping: Mapping of old relationship type names to new relationship type IDs
    """
    cursor = conn.cursor()
    
    # Get all relationships that need migration
    cursor.execute('''
    SELECT id, source_id, target_id, relationship_type, description, color, width, strength
    FROM relationships
    WHERE relationship_type IS NOT NULL 
    AND (relationship_type_id IS NULL OR relationship_type_id = 0)
    ''')
    
    old_relationships = cursor.fetchall()
    print(f"Found {len(old_relationships)} relationships to migrate.")
    
    update_count = 0
    custom_count = 0
    
    for rel in old_relationships:
        rel_dict = dict(rel)
        old_type = rel_dict['relationship_type'].upper()
        
        # Try to find a matching relationship type ID
        if old_type in type_mapping:
            # This is a known relationship type - update the relationship_type_id
            new_type_id = type_mapping[old_type]
            cursor.execute('''
            UPDATE relationships
            SET relationship_type_id = ?, is_custom = 0, custom_label = NULL
            WHERE id = ?
            ''', (new_type_id, rel_dict['id']))
            update_count += 1
        else:
            # This is a custom relationship type - set is_custom and keep the label
            cursor.execute('''
            UPDATE relationships
            SET is_custom = 1, custom_label = ?
            WHERE id = ?
            ''', (rel_dict['relationship_type'], rel_dict['id']))
            custom_count += 1
    
    # Commit the changes
    conn.commit()
    print(f"Updated {update_count} relationships to use relationship_type_id.")
    print(f"Marked {custom_count} relationships as custom with custom_label.")


def set_migration_complete(conn: sqlite3.Connection) -> None:
    """Set a flag to indicate the relationship migration is complete.
    
    Args:
        conn: Database connection
    """
    cursor = conn.cursor()
    
    # Check if app_settings table exists
    cursor.execute('''
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='app_settings'
    ''')
    
    if cursor.fetchone():
        # Set a flag in app_settings
        cursor.execute('''
        INSERT OR REPLACE INTO app_settings (key, value) 
        VALUES ('relationship_migration_complete', 'true')
        ''')
    else:
        # Create a simple migration_status table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS migration_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            migration_name TEXT NOT NULL UNIQUE,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute('''
        INSERT INTO migration_status (migration_name)
        VALUES ('relationship_migration_v1')
        ''')
    
    conn.commit()


if __name__ == "__main__":
    # If run as a script, find and migrate the database
    import sys
    from pathlib import Path
    
    # Try to find the database file
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        # Try to find the database in common locations
        possible_paths = [
            "./the_plot_thickens.db",
            "./data/the_plot_thickens.db",
            "../data/the_plot_thickens.db",
            str(Path.home() / "the_plot_thickens.db"),
            str(Path.home() / "Documents" / "the_plot_thickens.db")
        ]
        
        db_path = None
        for path in possible_paths:
            if os.path.exists(path):
                db_path = path
                break
        
        if not db_path:
            print("Database file not found. Please specify the path as an argument.")
            sys.exit(1)
    
    # Run the migration
    success = migrate_relationships(db_path)
    if success:
        print(f"Successfully migrated relationships in {db_path}")
        sys.exit(0)
    else:
        print(f"Failed to migrate relationships in {db_path}")
        sys.exit(1) 