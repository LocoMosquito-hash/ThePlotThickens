#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to run the Character Picker Example for The Plot Thickens application.

This script initializes and displays the character picker example window.
"""

import sys
import os

# Add the project root directory to the system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import and run the example from the module
from app.utils.character_picker import CharacterPicker
from PyQt6.QtWidgets import QApplication, QMainWindow

# Sample character data
sample_characters = [
    {
        "id": 1,
        "name": "John Doe",
        "is_main_character": True,
        "avatar_path": None,
        "gender": "Male",
        "age_category": "Adult"
    },
    {
        "id": 2,
        "name": "Jane Smith",
        "is_main_character": False,
        "avatar_path": None,
        "gender": "Female",
        "age_category": "Young"
    },
    {
        "id": 3,
        "name": "Robert Johnson",
        "is_main_character": False,
        "avatar_path": None,
        "gender": "Male",
        "age_category": "Mature",
        "is_deceased": True
    },
    {
        "id": 4,
        "name": "Emily Wilson",
        "is_main_character": False,
        "avatar_path": None,
        "gender": "Female",
        "age_category": "Teen",
        "is_archived": True
    },
    {
        "id": 5,
        "name": "David Clark",
        "is_main_character": True,
        "avatar_path": None,
        "gender": "Male",
        "age_category": "Young"
    }
]

if __name__ == "__main__":
    # Create application
    app = QApplication(sys.argv)
    
    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Character Picker Example")
    window.resize(400, 500)
    
    # Create character picker with sample data
    picker = CharacterPicker(
        characters=sample_characters,
        multi_select=True,
        show_filter=True
    )
    
    # Handle character selection
    def on_character_selected(character_id, character_data):
        print(f"Selected character: {character_data.get('name')} (ID: {character_id})")
    
    picker.character_selected.connect(on_character_selected)
    
    # Set as central widget
    window.setCentralWidget(picker)
    
    # Show window
    window.show()
    
    # Run application
    sys.exit(app.exec()) 