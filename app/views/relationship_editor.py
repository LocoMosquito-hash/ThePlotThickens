#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Relationship Editor for The Plot Thickens application.

This module defines a dialog for creating and editing relationships between characters.
"""

from typing import List, Dict, Any, Optional, Tuple

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, 
    QListWidgetItem, QLabel, QWidget, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QIcon, QColor, QPalette

from app.db_sqlite import get_story_characters


class CharacterItemWidget(QWidget):
    """Custom widget for character list items."""
    
    def __init__(self, character_data: Dict[str, Any], parent=None):
        """Initialize the character item widget.
        
        Args:
            character_data: Character data dictionary
            parent: Parent widget
        """
        super().__init__(parent)
        self.character_data = character_data
        
        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Create avatar placeholder
        self.avatar_label = QLabel()
        self.avatar_label.setMinimumSize(40, 40)
        self.avatar_label.setMaximumSize(40, 40)
        self.avatar_label.setStyleSheet("background-color: #D8C6F3; border-radius: 5px;")
        
        # Load avatar if available
        if character_data.get('avatar_path'):
            pixmap = QPixmap(character_data['avatar_path'])
            if not pixmap.isNull():
                # Scale the pixmap to fit
                pixmap = pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.avatar_label.setPixmap(pixmap)
        
        layout.addWidget(self.avatar_label)
        
        # Create name label
        self.name_label = QLabel(character_data['name'])
        self.name_label.setStyleSheet("color: white; font-weight: bold;")
        layout.addWidget(self.name_label)
        
        # Set the background color for the widget
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#555555"))
        self.setPalette(palette)
        
        # Set fixed height for consistency
        self.setFixedHeight(50)


class CharacterListItem(QListWidgetItem):
    """An item in the character list that displays a character's avatar and name."""
    
    def __init__(self, character_data: Dict[str, Any]):
        """Initialize the character list item.
        
        Args:
            character_data: Character data dictionary
        """
        super().__init__()
        self.character_data = character_data
        self.character_id = character_data['id']
        
        # Set size hint for the item
        self.setSizeHint(QSize(0, 50))


class RelationshipEditorDialog(QDialog):
    """Dialog for creating and editing relationships between characters."""
    
    def __init__(self, db_conn, story_id: int, parent=None):
        """Initialize the relationship editor dialog.
        
        Args:
            db_conn: Database connection
            story_id: ID of the story
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.story_id = story_id
        
        # Store the characters data
        self.characters = get_story_characters(db_conn, story_id)
        
        # Sort characters alphabetically by name
        self.characters.sort(key=lambda x: x['name'])
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Edit Relationship")
        self.resize(900, 600)  # Set a reasonable size
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create horizontal layout for the character lists
        lists_layout = QHBoxLayout()
        
        # Left characters list
        left_list_container = QWidget()
        left_list_layout = QVBoxLayout(left_list_container)
        
        left_list_label = QLabel("Source Character")
        left_list_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        left_list_layout.addWidget(left_list_label)
        
        self.left_characters_list = QListWidget()
        self.left_characters_list.setStyleSheet("""
            QListWidget {
                background-color: #333333;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                border-bottom: 1px solid #444444;
                padding: 2px;
            }
            QListWidget::item:selected {
                background-color: #4a4a6a;
            }
        """)
        # Set selection mode to single selection
        self.left_characters_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        left_list_layout.addWidget(self.left_characters_list)
        
        # Right characters list
        right_list_container = QWidget()
        right_list_layout = QVBoxLayout(right_list_container)
        
        right_list_label = QLabel("Target Character")
        right_list_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        right_list_layout.addWidget(right_list_label)
        
        self.right_characters_list = QListWidget()
        self.right_characters_list.setStyleSheet("""
            QListWidget {
                background-color: #333333;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                border-bottom: 1px solid #444444;
                padding: 2px;
            }
            QListWidget::item:selected {
                background-color: #4a4a6a;
            }
        """)
        # Set selection mode to single selection
        self.right_characters_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        right_list_layout.addWidget(self.right_characters_list)
        
        # Set fixed width for the list containers to ensure they're the same size
        left_list_container.setMinimumWidth(250)
        right_list_container.setMinimumWidth(250)
        
        # Add the lists to the horizontal layout with a lot of space in between
        lists_layout.addWidget(left_list_container)
        lists_layout.addStretch(1)  # Add stretch to create space
        lists_layout.addWidget(right_list_container)
        
        # Add the lists layout to the main layout
        main_layout.addLayout(lists_layout)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setMinimumWidth(100)
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept)
        self.save_button.setMinimumWidth(100)
        
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.save_button)
        
        main_layout.addLayout(buttons_layout)
        
        # Populate the character lists
        self.populate_character_lists()
        
        # Set dialog to be modal
        self.setModal(True)
    
    def populate_character_lists(self):
        """Populate the character lists with character data."""
        # Clear the lists first
        self.left_characters_list.clear()
        self.right_characters_list.clear()
        
        # Add characters to both lists
        for character in self.characters:
            # Create list items for each list
            left_item = CharacterListItem(character)
            right_item = CharacterListItem(character)
            
            # Add to respective lists
            self.left_characters_list.addItem(left_item)
            self.right_characters_list.addItem(right_item)
            
            # Create and set custom widgets
            left_widget = CharacterItemWidget(character)
            right_widget = CharacterItemWidget(character)
            
            # Set as item widgets
            self.left_characters_list.setItemWidget(left_item, left_widget)
            self.right_characters_list.setItemWidget(right_item, right_widget) 