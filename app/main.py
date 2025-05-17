#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main entry point for The Plot Thickens application.

This module initializes the application and starts the GUI.
"""

import sys
import os
import logging
from typing import Optional

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor

from app.db_sqlite import initialize_database
from app.views.main_window import MainWindow
from app.utils.image_recognition_util import ImageRecognitionUtil
from app.utils.theme_manager import ThemeManager
from app.utils.icons import icon_manager
from app.migration_manager import check_and_run_migrations


def _setup_logging() -> None:
    """Set up logging configuration for the application.
    
    Configures logging to output to both console and a log file.
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    log_file = os.path.join(log_dir, "the_plot_thickens.log")
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Set to DEBUG to capture all logs
    
    # File handler for all logs
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # Console handler for info and above
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Less verbose for console
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    logging.info("Logging initialized")


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
    # Set up logging first
    _setup_logging()
    
    logging.info("Starting The Plot Thickens application...")
    
    # Get the application directory
    app_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Initialize the database
    db_path = os.path.join(app_dir, "..", "the_plot_thickens.db")
    logging.info(f"Database path: {db_path}")
    
    try:
        # Run any pending migrations first
        logging.info("Checking for database migrations...")
        migrations_success = check_and_run_migrations(db_path)
        if not migrations_success:
            logging.warning("Some migrations may have failed. Application may not function correctly.")
            
        # Now initialize the database
        db_conn = initialize_database(db_path)
        logging.info("Database initialized successfully")
        
        # Initialize image recognition
        try:
            image_recognition = ImageRecognitionUtil(db_conn)
        except Exception as e:
            logging.warning(f"Could not initialize image recognition: {e}")
            
    except Exception as e:
        logging.error(f"Error initializing database: {e}", exc_info=True)
        return
    
    # Start the application
    logging.info("Creating QApplication instance...")
    app = QApplication(sys.argv)
    
    # Initialize and apply the theme
    theme_manager = ThemeManager(app_dir)
    theme_manager.apply_theme()
    
    # Preload commonly used icons
    logging.info("Preloading common icons...")
    common_icons = [
        "home", "settings", "user", "file", "folder", "trash",
        "edit", "check", "x", "plus", "minus", "refresh",
        "calendar", "info_circle", "alert_triangle", "sun", "moon"
    ]
    
    for icon_name in common_icons:
        try:
            icon_manager.get_icon(icon_name)
        except Exception as e:
            logging.warning(f"Could not preload icon '{icon_name}': {str(e)}")
    
    logging.info("Icon initialization completed")
    
    # Create and show the main window
    logging.info("Creating main window...")
    try:
        window = MainWindow(db_conn)
        # Pass the theme manager to the main window
        window.theme_manager = theme_manager
        logging.info("Showing main window...")
        window.show()
    except Exception as e:
        logging.error(f"Error creating or showing main window: {e}", exc_info=True)
        return
    
    # Run the application
    logging.info("Starting application event loop...")
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 