#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Migration: Add story_slots table

This migration creates a dedicated table to persist the Ren'Py source slot
metadata per story, allowing the UI and backend services to share a single
source of truth.
"""

import sqlite3
from typing import Any, Dict


def migrate_up(cursor: sqlite3.Cursor) -> None:
    """
    Apply the migration.

    Args:
        cursor: Database cursor
    """
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS story_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
            slot_number INTEGER NOT NULL,
            source_type TEXT NOT NULL CHECK (source_type IN ('directory', 'compressed')),
            destination_path TEXT NOT NULL,
            original_source_path TEXT,
            metadata_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (story_id) REFERENCES stories (id) ON DELETE CASCADE,
            UNIQUE (story_id, slot_number)
        )
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_story_slots_story_id
        ON story_slots (story_id)
        """
    )
    print("✓ Added story_slots table")


def migrate_down(cursor: sqlite3.Cursor) -> None:
    """
    Reverse the migration.

    Args:
        cursor: Database cursor
    """
    cursor.execute("DROP TABLE IF EXISTS story_slots")
    print("✓ Removed story_slots table")


def get_migration_info() -> Dict[str, Any]:
    """
    Get migration metadata.

    Returns:
        Dictionary containing migration information
    """
    return {
        "version": "20251129_001",
        "description": "Add story_slots table for FlowViz slot persistence",
        "requires_backup": False,
        "affects_tables": ["story_slots"],
    }

