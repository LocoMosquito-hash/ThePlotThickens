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
from PyQt6.QtGui import QPalette, QColor

from app.db_sqlite import initialize_database
from app.views.main_window import MainWindow
from app.utils.image_recognition_util import ImageRecognitionUtil
from app.utils.theme_manager import ThemeManager


def _create_dark_palette() -> QPalette:
    """Create a dark color palette for the application.
    
    Returns:
        QPalette configured with dark theme colors
    """
    palette = QPalette()
    
    # Set colors for various palette roles
    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(45, 45, 45))
    palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    
    # Set colors for disabled state
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(127, 127, 127))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(127, 127, 127))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(127, 127, 127))
    
    # Set tooltip colors
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
    
    return palette


def main() -> None:
    """Main entry point for the application."""
    print("Starting The Plot Thickens application...")
    
    # Get the application directory
    app_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Initialize the database
    db_path = os.path.join(app_dir, "..", "the_plot_thickens.db")
    print(f"Database path: {db_path}")
    try:
        db_conn = initialize_database(db_path)
        print("Database initialized successfully")
        
        # Initialize image recognition
        try:
            image_recognition = ImageRecognitionUtil(db_conn)
        except Exception as e:
            print(f"Warning: Could not initialize image recognition: {e}")
            
    except Exception as e:
        print(f"Error initializing database: {e}")
        return
    
    # Start the application
    print("Creating QApplication instance...")
    app = QApplication(sys.argv)
    
    # Initialize and apply the theme
    theme_manager = ThemeManager(app_dir)
    theme_manager.apply_theme()
    
    # Create and show the main window
    print("Creating main window...")
    try:
        window = MainWindow(db_conn)
        # Pass the theme manager to the main window
        window.theme_manager = theme_manager
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