#!/usr/bin/env python3
"""
Run the migration to make character_id column in quick_events table optional.
"""

import os
import sys
from pathlib import Path
import sqlite3
from typing import Optional, List

from app.migrations.make_quick_event_character_optional import migrate_database

def get_database_paths() -> List[str]:
    """
    Find all database files in the local directory.
    
    Returns:
        List of paths to database files
    """
    # Get the current directory
    current_dir = os.getcwd()
    
    # Look for SQLite database files
    db_paths = []
    for file in os.listdir(current_dir):
        if file.endswith('.db') or file.endswith('.sqlite'):
            db_paths.append(os.path.join(current_dir, file))
    
    return db_paths

def main():
    """Main entry point for the script."""
    print("Looking for database files...")
    db_paths = get_database_paths()
    
    if not db_paths:
        print("No database files found in the current directory.")
        sys.exit(1)
    
    print("Found the following database files:")
    for i, path in enumerate(db_paths):
        print(f"{i+1}. {path}")
    
    # Ask the user which database to migrate
    if len(db_paths) == 1:
        db_path = db_paths[0]
        confirm = input(f"Migrate database {db_path}? (y/n): ")
        if confirm.lower() != 'y':
            print("Migration cancelled.")
            sys.exit(0)
    else:
        while True:
            try:
                choice = int(input("\nEnter the number of the database to migrate (or 0 to cancel): "))
                if choice == 0:
                    print("Migration cancelled.")
                    sys.exit(0)
                elif 1 <= choice <= len(db_paths):
                    db_path = db_paths[choice-1]
                    break
                else:
                    print(f"Invalid choice. Please enter a number between 1 and {len(db_paths)}.")
            except ValueError:
                print("Invalid input. Please enter a number.")
    
    print(f"\nMigrating database: {db_path}")
    
    # Backup the database before migration
    backup_path = f"{db_path}.backup"
    print(f"Creating backup at {backup_path}")
    
    try:
        # Create a backup by copying the file
        with open(db_path, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())
        
        print("Backup created successfully.")
        
        # Run the migration
        print("Running migration...")
        success = migrate_database(db_path)
        
        if success:
            print("\nMigration completed successfully.")
            print("\nYou can now create quick events without assigning them to a character.")
            print("Existing quick events will continue to work as before.")
        else:
            print("\nMigration failed. The database may be in an inconsistent state.")
            print(f"You can restore from the backup at {backup_path}")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        print(f"You can restore from the backup at {backup_path}")
        sys.exit(1)

if __name__ == "__main__":
    main() 