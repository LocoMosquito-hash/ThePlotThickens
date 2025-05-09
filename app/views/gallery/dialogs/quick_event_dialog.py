#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Quick Event Dialog for The Plot Thickens application.

This module contains dialogs for selecting and editing quick events.
"""

import re
from typing import List, Dict, Any, Optional, Tuple

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QComboBox,
    QDialogButtonBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QTextCursor

from app.utils.character_completer import CharacterCompleter
# Import the centralized character reference functions
from app.utils.character_references import convert_mentions_to_char_refs, convert_char_refs_to_mentions

from app.db_sqlite import (
    get_story_characters, get_image_quick_events, get_character_quick_events,
    create_quick_event, get_next_quick_event_sequence_number,
    get_quick_event_tagged_characters, process_quick_event_character_tags
)


class QuickEventSelectionDialog(QDialog):
    """Dialog for selecting quick events to associate with an image."""
    
    def __init__(self, db_conn, story_id: int, image_id: int, current_quick_event_ids: List[int] = None, parent=None):
        """Initialize the quick event selection dialog.
        
        Args:
            db_conn: Database connection
            story_id: ID of the story
            image_id: ID of the image to associate quick events with
            current_quick_event_ids: List of quick event IDs already associated with the image
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.story_id = story_id
        self.image_id = image_id
        self.current_quick_event_ids = current_quick_event_ids or []
        self.characters = []
        self.all_quick_events = []
        
        self.setWindowTitle("Select Quick Events")
        self.init_ui()
        self.load_characters()
        self.load_quick_events()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setMinimumWidth(500)
        layout = QVBoxLayout(self)
        
        # Character filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by Character:"))
        
        self.character_combo = QComboBox()
        self.character_combo.addItem("All Characters", None)
        self.character_combo.currentIndexChanged.connect(self.on_character_changed)
        filter_layout.addWidget(self.character_combo)
        
        layout.addLayout(filter_layout)
        
        # Quick events list
        self.events_list = QListWidget()
        self.events_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        layout.addWidget(self.events_list)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def load_characters(self):
        """Load characters for the filter dropdown."""
        characters = get_story_characters(self.db_conn, self.story_id)
        self.characters = characters
        
        for character in characters:
            self.character_combo.addItem(character["name"], character["id"])
    
    def load_quick_events(self):
        """Load all quick events for the story."""
        # Get all quick events for the story
        all_events = []
        
        # Get events from image tags
        image_events = get_image_quick_events(self.db_conn, self.story_id)
        all_events.extend(image_events)
        
        # Get events from character tags
        character_events = get_character_quick_events(self.db_conn, self.story_id)
        all_events.extend(character_events)
        
        # Remove duplicates by converting to a dictionary with event_id as key
        events_dict = {event["id"]: event for event in all_events}
        self.all_quick_events = list(events_dict.values())
        
        # Sort by sequence number
        self.all_quick_events.sort(key=lambda x: x.get("sequence_number", 0))
        
        # Populate the list with all events
        self.populate_event_list(self.all_quick_events)
    
    def populate_event_list(self, quick_events: List[Dict[str, Any]]):
        """Populate the event list with the given quick events.
        
        Args:
            quick_events: List of quick events to display
        """
        self.events_list.clear()
        
        for event in quick_events:
            # Get the characters tagged in this event
            tagged_characters = get_quick_event_tagged_characters(self.db_conn, event["id"])
            
            # Format the event text for display
            display_text = self.format_display_text(event["text"], tagged_characters)
            
            # Create a list item
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, event["id"])
            
            # Pre-select if already associated
            if event["id"] in self.current_quick_event_ids:
                item.setSelected(True)
            
            self.events_list.addItem(item)
    
    def format_display_text(self, text: str, tagged_characters: Dict[str, Dict]) -> str:
        """Format the display text by converting character references to names.
        
        Args:
            text: The text with character references
            tagged_characters: Dictionary of character data by character ID
            
        Returns:
            Formatted text with character names
        """
        # Convert character references to mentions
        return convert_char_refs_to_mentions(text, tagged_characters)
    
    def on_character_changed(self, index: int):
        """Filter quick events when a character is selected in the dropdown.
        
        Args:
            index: Index of the selected character in the dropdown
        """
        character_id = self.character_combo.currentData()
        
        if character_id is None:
            # "All Characters" is selected
            self.populate_event_list(self.all_quick_events)
        else:
            # Filter events by character
            filtered_events = []
            
            for event in self.all_quick_events:
                # Get the characters tagged in this event
                tagged_characters = get_quick_event_tagged_characters(self.db_conn, event["id"])
                
                # Check if the selected character is tagged in this event
                if str(character_id) in tagged_characters:
                    filtered_events.append(event)
            
            self.populate_event_list(filtered_events)
    
    def get_selected_quick_event_ids(self) -> List[int]:
        """Get the IDs of selected quick events.
        
        Returns:
            List of selected quick event IDs
        """
        selected_ids = []
        
        for i in range(self.events_list.count()):
            item = self.events_list.item(i)
            if item.isSelected():
                event_id = item.data(Qt.ItemDataRole.UserRole)
                selected_ids.append(event_id)
        
        return selected_ids


class QuickEventEditor(QDialog):
    """Dialog for creating and editing quick events."""
    
    def __init__(self, db_conn, story_id: int, image_id: int, parent=None):
        """Initialize the quick event editor.
        
        Args:
            db_conn: Database connection
            story_id: ID of the story
            image_id: ID of the image to associate the quick event with
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.story_id = story_id
        self.image_id = image_id
        self.character_completer = None
        self.character_list = []
        
        # Character being typed (for autocompletion)
        self.typing_character = False
        self.character_start_pos = 0
        
        self.setWindowTitle("Create Quick Event")
        self.init_ui()
        
        # Load character data for the character dropdown
        characters = get_story_characters(self.db_conn, self.story_id)
        self.character_list = characters
        
        for character in characters:
            self.character_combo.addItem(character["name"], character["id"])
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        self.setMinimumSize(500, 300)
        
        # Quick event text editor
        editor_group = QGroupBox("Quick Event Description")
        editor_layout = QVBoxLayout(editor_group)
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Describe what's happening here...")
        self.text_edit.textChanged.connect(self.check_for_character_tag)
        editor_layout.addWidget(self.text_edit)
        
        hint_label = QLabel("Tip: Type @ to tag characters")
        hint_label.setStyleSheet("color: gray; font-size: 9pt;")
        editor_layout.addWidget(hint_label)
        
        layout.addWidget(editor_group)
        
        # Character dropdown
        character_group = QGroupBox("Primary Character (Optional)")
        character_layout = QHBoxLayout(character_group)
        
        character_label = QLabel("Select a character:")
        character_layout.addWidget(character_label)
        
        self.character_combo = QComboBox()
        self.character_combo.addItem("None", None)
        character_layout.addWidget(self.character_combo)
        
        layout.addWidget(character_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        create_button = QPushButton("Create")
        create_button.clicked.connect(self.accept)
        create_button.setDefault(True)
        button_layout.addWidget(create_button)
        
        layout.addLayout(button_layout)
        
        # Character completer (for @mentions)
        self.character_completer = CharacterCompleter(self)
        self.character_completer.character_selected.connect(self.on_character_selected)
        self.character_completer.hide()
    
    def get_text(self) -> str:
        """Get the quick event text with character references.
        
        Returns:
            Quick event text with character references
        """
        # Convert character mentions to references
        text = self.text_edit.toPlainText()
        return self.convert_mentions_to_char_refs(text)
    
    def convert_mentions_to_char_refs(self, text: str) -> str:
        """Convert @mentions to character references.
        
        Args:
            text: Text with @mentions
            
        Returns:
            Text with character references
        """
        # Use the centralized function
        return convert_mentions_to_char_refs(text, self.character_list)
    
    def get_character_id(self) -> int:
        """Get the selected character ID.
        
        Returns:
            Selected character ID, or None if no character is selected
        """
        return self.character_combo.currentData()
    
    def on_character_selected(self, character_name: str):
        """Handle character selection from the completer.
        
        Args:
            character_name: Name of the selected character
        """
        self.insert_character_tag(character_name)
    
    def check_for_character_tag(self):
        """Check for @ character to show the character completer."""
        # Implemented in the base class to allow for character tagging
        pass
    
    def insert_character_tag(self, character_name: str):
        """Insert a character tag at the current cursor position.
        
        Args:
            character_name: Name of the character to tag
        """
        # Implemented in the base class to allow for character tagging
        pass
