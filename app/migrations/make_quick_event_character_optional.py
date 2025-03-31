#!/usr/bin/env python3
"""
Migration script to make the character_id column in quick_events table optional.
"""

import sqlite3
from pathlib import Path
import sys
from typing import Optional

def migrate_database(db_path: str) -> bool:
    """
    Alter the quick_events table to make character_id nullable.
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        True if migration was successful, False otherwise
    """
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = OFF")
        
        # Start a transaction
        conn.execute("BEGIN TRANSACTION")
        
        # Create a new table with the updated schema
        conn.execute("""
        CREATE TABLE quick_events_new (
            id INTEGER PRIMARY KEY,
            created_at TEXT,
            updated_at TEXT,
            text TEXT NOT NULL,
            sequence_number INTEGER DEFAULT 0,
            character_id INTEGER,
            FOREIGN KEY (character_id) REFERENCES characters (id)
        )
        """)
        
        # Copy data from the old table to the new one
        conn.execute("""
        INSERT INTO quick_events_new
        SELECT id, created_at, updated_at, text, sequence_number, character_id
        FROM quick_events
        """)
        
        # Drop the old table
        conn.execute("DROP TABLE quick_events")
        
        # Rename the new table to the original name
        conn.execute("ALTER TABLE quick_events_new RENAME TO quick_events")
        
        # Re-create any indexes (if applicable)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_quick_events_character_id ON quick_events(character_id)")
        
        # Commit the transaction
        conn.execute("COMMIT")
        
        # Re-enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Close the connection
        conn.close()
        
        print(f"Successfully migrated database at {db_path}")
        return True
        
    except sqlite3.Error as e:
        print(f"Error migrating database: {e}")
        return False

def main():
    """Main entry point for the script."""
    if len(sys.argv) != 2:
        print("Usage: python make_quick_event_character_optional.py <path_to_database>")
        sys.exit(1)
    
    db_path = sys.argv[1]
    db_file = Path(db_path)
    
    if not db_file.exists():
        print(f"Error: Database file {db_path} does not exist")
        sys.exit(1)
    
    success = migrate_database(db_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 