#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Migration: Add source_path column to stories table

This migration adds a source_path column to the stories table to store
the path to the source code for each story (for Ren'Py source analysis).
"""

import sqlite3
from typing import Any, Dict


def migrate_up(cursor: sqlite3.Cursor) -> None:
    """
    Apply the migration.
    
    Args:
        cursor: Database cursor
    """
    # Add source_path column to stories table
    cursor.execute("""
        ALTER TABLE stories 
        ADD COLUMN source_path TEXT
    """)
    
    print("✓ Added source_path column to stories table")


def migrate_down(cursor: sqlite3.Cursor) -> None:
    """
    Reverse the migration.
    
    Args:
        cursor: Database cursor
    """
    # SQLite doesn't support DROP COLUMN directly, so we would need to:
    # 1. Create new table without the column
    # 2. Copy data
    # 3. Drop old table
    # 4. Rename new table
    
    # For now, just note that this migration is not easily reversible
    print("Warning: Reversing this migration requires manual intervention")
    print("The source_path column will remain in the database")


def get_migration_info() -> Dict[str, Any]:
    """
    Get migration metadata.
    
    Returns:
        Dictionary containing migration information
    """
    return {
        "version": "20250127_001",
        "description": "Add source_path column to stories table",
        "requires_backup": False,
        "affects_tables": ["stories"]
    } 