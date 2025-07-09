#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Migration: Add version and release date columns to stories table

This migration adds version, first_release, and current_release columns
to the stories table to support additional story metadata.
"""

import sqlite3
from typing import Any, Dict


def migrate_up(cursor: sqlite3.Cursor) -> None:
    """
    Apply the migration.
    
    Args:
        cursor: Database cursor
    """
    # Add version column to stories table (alphanumeric)
    cursor.execute("""
        ALTER TABLE stories 
        ADD COLUMN version TEXT
    """)
    
    # Add first_release column to stories table (date)
    cursor.execute("""
        ALTER TABLE stories 
        ADD COLUMN first_release TEXT
    """)
    
    # Add current_release column to stories table (date)
    cursor.execute("""
        ALTER TABLE stories 
        ADD COLUMN current_release TEXT
    """)
    
    print("✓ Added version column to stories table")
    print("✓ Added first_release column to stories table")
    print("✓ Added current_release column to stories table")


def migrate_down(cursor: sqlite3.Cursor) -> None:
    """
    Reverse the migration.
    
    Args:
        cursor: Database cursor
    """
    # SQLite doesn't support DROP COLUMN directly, so we would need to:
    # 1. Create new table without the columns
    # 2. Copy data
    # 3. Drop old table
    # 4. Rename new table
    
    # For now, just note that this migration is not easily reversible
    print("Warning: Reversing this migration requires manual intervention")
    print("The version, first_release, and current_release columns will remain in the database")


def get_migration_info() -> Dict[str, Any]:
    """
    Get migration metadata.
    
    Returns:
        Dictionary containing migration information
    """
    return {
        "version": "20250127_002",
        "description": "Add version and release date columns to stories table",
        "requires_backup": False,
        "affects_tables": ["stories"]
    } 