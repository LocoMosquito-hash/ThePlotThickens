#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gallery Filter Dialog for The Plot Thickens application.

This module contains the dialog for filtering gallery images by characters.
"""

from typing import List, Dict, Any, Optional, Tuple

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTabWidget, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QIcon

from app.views.gallery.character.widgets import (
    GalleryFilterCharacterListWidget,
    FilterCharacterListWidget
)

from app.db_sqlite import get_story_characters


class GalleryFilterDialog(QDialog):
    """Dialog for filtering gallery images."""
    
    def __init__(self, db_conn, story_id: int, parent=None):
        """Initialize the gallery filter dialog.
        
        Args:
            db_conn: Database connection
            story_id: ID of the story
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.story_id = story_id
        
        # Character filters (character_id, include)
        self.character_filters = []
        
        self.setWindowTitle("Gallery Filters")
        self.resize(600, 400)
        
        self.init_ui()
        self.load_characters()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Tabs for different filter types
        tabs = QTabWidget()
        
        # Character filters tab
        character_tab = QWidget()
        character_layout = QVBoxLayout(character_tab)
        
        # Character selection group
        character_group = QGroupBox("Characters")
        character_group_layout = QVBoxLayout(character_group)
        
        # Character list (scrollable)
        self.character_list = GalleryFilterCharacterListWidget(self.db_conn, self)
        character_group_layout.addWidget(self.character_list)
        
        # Include/exclude buttons
        button_layout = QHBoxLayout()
        
        self.include_btn = QPushButton("Include Selected")
        self.include_btn.clicked.connect(lambda: self.add_character_filter(self.character_list.get_selected_character(), True))
        button_layout.addWidget(self.include_btn)
        
        self.exclude_btn = QPushButton("Exclude Selected")
        self.exclude_btn.clicked.connect(lambda: self.add_character_filter(self.character_list.get_selected_character(), False))
        button_layout.addWidget(self.exclude_btn)
        
        character_group_layout.addLayout(button_layout)
        
        character_layout.addWidget(character_group)
        
        # Active filters group
        filters_group = QGroupBox("Active Filters")
        filters_group_layout = QVBoxLayout(filters_group)
        
        # Filter list
        self.filter_list = FilterCharacterListWidget(self.db_conn, self)
        filters_group_layout.addWidget(self.filter_list)
        
        # Remove filter button
        remove_btn = QPushButton("Remove Selected Filters")
        remove_btn.clicked.connect(self.remove_selected_filters)
        filters_group_layout.addWidget(remove_btn)
        
        character_layout.addWidget(filters_group)
        
        tabs.addTab(character_tab, "Character Filters")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply Filters")
        apply_btn.clicked.connect(self.accept)
        button_layout.addWidget(apply_btn)
        
        layout.addLayout(button_layout)
    
    def load_characters(self):
        """Load characters for the filter list."""
        # Get characters from database
        characters = get_story_characters(self.db_conn, self.story_id)
        
        # Set characters in the list widget
        self.character_list.load_characters(characters)
        
        # Restore any existing filters
        self.filter_list.clear()
        for character_id, include in self.character_filters:
            # Find the character in the list
            for character in characters:
                if character["id"] == character_id:
                    self.add_character_filter(character, include)
                    break
    
    def add_character_filter(self, character: Dict[str, Any], include: bool):
        """Add a character filter.
        
        Args:
            character: Character data
            include: Whether to include or exclude images with this character
        """
        if not character:
            return
        
        # Check if this character is already in the filter list
        for i in range(self.filter_list.count()):
            item = self.filter_list.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            
            if data["character_id"] == character["id"]:
                # Update the filter
                data["include"] = include
                
                # Update the item text
                item_text = f"{character['name']} - {'Include' if include else 'Exclude'}"
                item.setText(item_text)
                
                # Update the item icon
                icon = QIcon("resources/icons/include.png" if include else "resources/icons/exclude.png")
                if icon.isNull():
                    # Fallback icon text
                    icon_text = "✓" if include else "✗"
                    item_text = f"{icon_text} {character['name']}"
                    item.setText(item_text)
                else:
                    item.setIcon(icon)
                
                # Update the character filters list
                for i, (char_id, inc) in enumerate(self.character_filters):
                    if char_id == character["id"]:
                        self.character_filters[i] = (char_id, include)
                        break
                
                return
        
        # Create a new filter
        item_text = f"{character['name']} - {'Include' if include else 'Exclude'}"
        item = QListWidgetItem(item_text)
        
        # Store character data
        item.setData(Qt.ItemDataRole.UserRole, {
            "character_id": character["id"],
            "character_name": character["name"],
            "include": include
        })
        
        # Set icon
        icon = QIcon("resources/icons/include.png" if include else "resources/icons/exclude.png")
        if icon.isNull():
            # Fallback icon text
            icon_text = "✓" if include else "✗"
            item_text = f"{icon_text} {character['name']}"
            item.setText(item_text)
        else:
            item.setIcon(icon)
        
        # Add to list
        self.filter_list.addItem(item)
        
        # Add to filters
        self.character_filters.append((character["id"], include))
    
    def remove_selected_filters(self):
        """Remove selected filters from the list."""
        selected_items = self.filter_list.selectedItems()
        
        for item in selected_items:
            data = item.data(Qt.ItemDataRole.UserRole)
            
            # Remove from the list widget
            self.filter_list.takeItem(self.filter_list.row(item))
            
            # Remove from the filters list
            for i, (char_id, include) in enumerate(self.character_filters):
                if char_id == data["character_id"]:
                    self.character_filters.pop(i)
                    break
    
    def get_character_filters(self) -> List[Tuple[int, bool]]:
        """Get the character filters.
        
        Returns:
            List of tuples (character_id, include)
        """
        return self.character_filters
