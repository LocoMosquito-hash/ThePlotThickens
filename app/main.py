#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main entry point for The Plot Thickens application.

This module initializes the application and starts the GUI.
"""

import sys
import os
from typing import Optional

from PyQt6.QtWidgets import QApplication

from app.db_sqlite import initialize_database
from app.views.main_window import MainWindow


def main() -> None:
    """Main entry point for the application."""
    print("Starting The Plot Thickens application...")
    
    # Initialize the database
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "the_plot_thickens.db")
    print(f"Database path: {db_path}")
    try:
        db_conn = initialize_database(db_path)
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
        return
    
    # Start the application
    print("Creating QApplication instance...")
    app = QApplication(sys.argv)
    
    # Create and show the main window
    print("Creating main window...")
    try:
        window = MainWindow(db_conn)
        print("Showing main window...")
        window.show()
    except Exception as e:
        print(f"Error creating or showing main window: {e}")
        return
    
    # Run the application
    print("Starting application event loop...")
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 