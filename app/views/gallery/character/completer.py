#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Character auto-completion for The Plot Thickens gallery.

This module contains widgets for character name auto-completion.
"""

from typing import List, Dict, Any

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt, pyqtSignal, QPoint

class CharacterTagCompleter(QWidget):
    """Popup widget for character tag autocompletion."""
    
    character_selected = pyqtSignal(str)  # Signal emitted when a character is selected
    
    def __init__(self, parent=None):
        """Initialize the completer.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.characters = []
        self.filtered_characters = []
        self.filter_text = ""
        
        self.init_ui()
        
        # Hide by default
        self.hide()
    
    def init_ui(self):
        """Initialize the UI."""
        # Set up the widget to appear as a popup
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(1, 1, 1, 1)
        
        # List widget for character suggestions
        self.suggestion_list = QListWidget()
        self.suggestion_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.suggestion_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.suggestion_list.itemClicked.connect(self.on_item_clicked)
        
        # Style the widget
        self.setStyleSheet("""
            QListWidget {
                border: 1px solid gray;
                background-color: white;
            }
            QListWidget::item {
                padding: 4px;
            }
            QListWidget::item:selected {
                background-color: #e0e0e0;
            }
        """)
        
        layout.addWidget(self.suggestion_list)
        self.setLayout(layout)
    
    def set_characters(self, characters: List[Dict[str, Any]]):
        """Set the available characters.
        
        Args:
            characters: List of character dictionaries with 'name' key
        """
        self.characters = characters
        self.update_suggestions()
    
    def set_filter(self, filter_text: str):
        """Set the filter text and update suggestions.
        
        Args:
            filter_text: Text to filter characters by
        """
        self.filter_text = filter_text.lower()
        self.update_suggestions()
    
    def update_suggestions(self):
        """Update the suggestion list based on current filter text."""
        self.suggestion_list.clear()
        
        if not self.filter_text:
            self.filtered_characters = []
            self.hide()
            return
        
        # Filter characters that contain the filter text
        self.filtered_characters = [
            char for char in self.characters 
            if self.filter_text in char["name"].lower()
        ]
        
        # Sort by relevance (characters that start with the filter text first)
        self.filtered_characters.sort(
            key=lambda c: (
                0 if c["name"].lower().startswith(self.filter_text) else 1,
                c["name"]
            )
        )
        
        # Add to suggestion list
        for character in self.filtered_characters:
            item = QListWidgetItem(character["name"])
            self.suggestion_list.addItem(item)
        
        # Show if we have suggestions, hide otherwise
        if self.filtered_characters:
            self.suggestion_list.setCurrentRow(0)  # Select first item
            self.resize_to_content()
            self.show()
        else:
            self.hide()
    
    def on_item_clicked(self, item: QListWidgetItem):
        """Handle item click event.
        
        Args:
            item: The clicked item
        """
        character_name = item.text()
        self.character_selected.emit(character_name)
        self.hide()
    
    def keyPressEvent(self, event):
        """Handle key press events.
        
        Args:
            event: Key event
        """
        current_row = self.suggestion_list.currentRow()
        
        if event.key() == Qt.Key.Key_Up:
            # Move selection up
            if current_row > 0:
                self.suggestion_list.setCurrentRow(current_row - 1)
            event.accept()
        elif event.key() == Qt.Key.Key_Down:
            # Move selection down
            if current_row < self.suggestion_list.count() - 1:
                self.suggestion_list.setCurrentRow(current_row + 1)
            event.accept()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            # Select current item
            current_item = self.suggestion_list.currentItem()
            if current_item:
                self.on_item_clicked(current_item)
            event.accept()
        elif event.key() == Qt.Key.Key_Escape:
            # Hide popup
            self.hide()
            event.accept()
        else:
            event.ignore()
    
    def resize_to_content(self):
        """Resize the widget to fit its content."""
        # Adjust width based on widest item
        width = self.suggestion_list.sizeHintForColumn(0) + 25  # Add some padding
        
        # Limit number of visible items
        visible_items = min(self.suggestion_list.count(), 6)
        height = self.suggestion_list.sizeHintForRow(0) * visible_items + 10
        
        # Set minimum width
        width = max(width, 150)
        
        self.resize(width, height)
