#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to run database migrations manually.

This script runs all pending database migrations for The Plot Thickens application.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

from app.migration_manager import check_and_run_migrations, register_migration_complete


def setup_logging() -> None:
    """Set up logging for the migration script."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def main() -> None:
    """Main entry point for the migration script."""
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Run database migrations for The Plot Thickens')
    parser.add_argument('--db-path', help='Path to the database file')
    parser.add_argument('--force', action='store_true', help='Force specific migration to run')
    parser.add_argument('--migration', help='Specific migration to run (when used with --force)')
    args = parser.parse_args()
    
    # Set up logging
    setup_logging()
    
    # Determine database path
    if args.db_path:
        db_path = args.db_path
    else:
        # Try to find the database in common locations
        possible_paths = [
            "./the_plot_thickens.db",
            "./data/the_plot_thickens.db",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "the_plot_thickens.db"),
            str(Path.home() / "the_plot_thickens.db"),
            str(Path.home() / "Documents" / "the_plot_thickens.db")
        ]
        
        db_path = None
        for path in possible_paths:
            if os.path.exists(path):
                db_path = path
                break
        
        if not db_path:
            logging.error("Database file not found. Please specify the path using --db-path.")
            sys.exit(1)
    
    # Check if the database file exists
    if not os.path.exists(db_path):
        logging.error(f"Database file not found at: {db_path}")
        sys.exit(1)
    
    logging.info(f"Using database at: {db_path}")
    
    # If forcing a specific migration
    if args.force and args.migration:
        logging.info(f"Forcing migration: {args.migration}")
        
        # Import and run the specific migration
        if args.migration == 'relationship_migration_v1':
            from app.migrations.migrate_relationships import migrate_relationships
            success = migrate_relationships(db_path)
            
            if success:
                # Register the migration as complete
                register_migration_complete(db_path, args.migration)
                logging.info(f"Successfully completed migration: {args.migration}")
                sys.exit(0)
            else:
                logging.error(f"Failed to complete migration: {args.migration}")
                sys.exit(1)
        else:
            logging.error(f"Unknown migration: {args.migration}")
            sys.exit(1)
    else:
        # Run all pending migrations
        logging.info("Checking for pending migrations...")
        success = check_and_run_migrations(db_path)
        
        if success:
            logging.info("All migrations completed successfully.")
            sys.exit(0)
        else:
            logging.error("Some migrations failed.")
            sys.exit(1)


if __name__ == "__main__":
    main() 