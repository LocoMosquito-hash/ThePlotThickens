#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Icon Example for The Plot Thickens application.

This module provides a simple example of how to use the icon manager.
"""

import sys
import os
import logging
from typing import List
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QGridLayout, QScrollArea
)
from PyQt6.QtCore import Qt, QSize

# Configure basic logging - show on console
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("IconExample")

print("Starting icon example...")

# Add parent directory to path for imports when running as a script
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
    print(f"Added {parent_dir} to sys.path")

try:
    # Import the icon manager
    print("Importing icon_manager...")
    from app.utils.icons.icon_manager import icon_manager
    print("Successfully imported icon_manager")
except ImportError as e:
    print(f"Error importing icon_manager: {e}")
    sys.exit(1)


class IconExampleWindow(QMainWindow):
    """Example window to demonstrate Tabler icons usage."""
    
    def __init__(self) -> None:
        """Initialize the example window."""
        super().__init__()
        
        print("Initializing example window...")
        
        self.setWindowTitle("Tabler Icons Example")
        self.setMinimumSize(800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create theme toggle button
        theme_layout = QHBoxLayout()
        theme_button = QPushButton("Toggle Theme (Dark/Light)")
        theme_button.clicked.connect(self.toggle_theme)
        theme_layout.addWidget(QLabel("Icon Theme:"))
        theme_layout.addWidget(theme_button)
        theme_layout.addStretch()
        main_layout.addLayout(theme_layout)
        
        # Display current icon implementation status
        status_label = QLabel()
        status_label.setWordWrap(True)
        
        if hasattr(icon_manager, "_using_pytablericons") and icon_manager._using_pytablericons:
            status_label.setText("Using pytablericons (Pillow-based full icon set)")
            status_label.setStyleSheet("color: green; font-weight: bold;")
        elif hasattr(icon_manager, "_using_tabler_qicon") and icon_manager._using_tabler_qicon:
            status_label.setText("Using tabler-qicon library (QIcon-based full icon set)")
            status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            status_label.setText("Using Qt built-in fallback icons (limited set)")
            status_label.setStyleSheet("color: red; font-weight: bold;")
        
        main_layout.addWidget(status_label)
        
        # Create scroll area for icons
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)
        
        # Create container widget for icon grid
        icon_container = QWidget()
        scroll_area.setWidget(icon_container)
        
        # Create grid layout for icons
        grid_layout = QGridLayout(icon_container)
        grid_layout.setSpacing(10)
        
        # Add common Tabler icons as buttons to the grid
        icon_names = [
            "home", "search", "settings", "user", "mail", "file", 
            "folder", "trash", "edit", "check", "x", "plus", "minus",
            "bookmark", "star", "heart", "bell", "calendar", "clock",
            "camera", "phone", "message", "info_circle", "alert_triangle",
            "help", "refresh", "download", "upload", "share", "link",
            "eye", "eye_off", "lock", "unlock", "shield", "key", "flag",
            "map_pin", "navigation", "printer", "device_desktop", "device_mobile",
            "device_tablet", "cloud", "sun", "moon", "player_play", 
            "player_pause", "player_stop", "volume", "microphone"
        ]
        
        # Create a grid of buttons with icons
        print(f"Creating grid with {len(icon_names)} icons...")
        success_count = 0
        error_count = 0
        
        for i, icon_name in enumerate(icon_names):
            row = i // 6
            col = i % 6
            
            button = QPushButton()
            try:
                button.setIcon(icon_manager.get_icon(icon_name))
                button.setIconSize(QSize(24, 24))
                button.setText(icon_name)
                success_count += 1
            except Exception as e:
                button.setText(f"{icon_name} (error)")
                print(f"Error loading icon '{icon_name}': {e}")
                error_count += 1
            
            button.setMinimumHeight(50)
            grid_layout.addWidget(button, row, col)
        
        print(f"Icon loading complete: {success_count} success, {error_count} errors")
    
    def toggle_theme(self) -> None:
        """Toggle between dark and light themes for icons."""
        try:
            if icon_manager._current_theme == "dark":
                icon_manager.set_theme("light")
                print("Switched to light theme")
            else:
                icon_manager.set_theme("dark")
                print("Switched to dark theme")
            
            # Force the window to update
            self.repaint()
        except Exception as e:
            print(f"Error toggling theme: {e}")


def main() -> None:
    """Run the example application."""
    try:
        print("Creating QApplication...")
        app = QApplication(sys.argv)
        
        print("Creating main window...")
        window = IconExampleWindow()
        
        print("Showing window...")
        window.show()
        
        print("Starting event loop...")
        sys.exit(app.exec())
    except Exception as e:
        print(f"Error running application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 