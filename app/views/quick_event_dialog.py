#!/usr/bin/env python3
"""
Quick Event Dialog Module.

This module provides a reusable dialog for creating and editing quick events.
"""

import sqlite3
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from app.utils.character_completer import CharacterCompleter
from app.utils.quick_event_manager import QuickEventManager
from app.db_sqlite import get_story_characters

class QuickEventDialog(QDialog):
    """
    Dialog for creating or editing quick events.
    
    This dialog can be used from any part of the application to create
    quick events. It supports various contexts and customization options.
    """
    
    # Signal emitted when a quick event is created or edited
    quick_event_created = pyqtSignal(int, str, object)  # event_id, text, context
    
    def __init__(self, 
                db_conn: sqlite3.Connection, 
                story_id: int, 
                parent: Optional[QWidget] = None,
                context: Optional[Dict[str, Any]] = None,
                initial_text: str = "",
                character_id: Optional[int] = None,
                options: Optional[Dict[str, bool]] = None):
        """
        Initialize the quick event dialog.
        
        Args:
            db_conn: Database connection
            story_id: ID of the story
            parent: Parent widget
            context: Optional context information
            initial_text: Optional initial text for the quick event
            character_id: Optional ID of a character to associate
            options: Optional UI customization options
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.story_id = story_id
        self.context = context or {}
        self.options = options or {
            "show_recent_events": True,
            "show_character_tags": True,
            "show_optional_note": True,
            "allow_characterless_events": True
        }
        self.initial_text = initial_text
        self.preferred_character_id = character_id
        self.result_event_id = None
        
        # Create a quick event manager
        self.qe_manager = QuickEventManager(db_conn)
        
        # Get all characters for the story for tagging
        self.characters = get_story_characters(db_conn, self.story_id)
        
        # Load recent quick events if enabled
        self.recent_events = []
        if self.options.get("show_recent_events", True):
            self.recent_events = self.qe_manager.get_recent_events(self.story_id, limit=3)
        
        # Initialize UI
        self.init_ui()
        
        # Setup character completer
        self.setup_character_completer()
        
        # Set initial text if provided
        if self.initial_text:
            self.text_edit.setText(self.initial_text)
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Create Quick Event")
        self.resize(450, 200)
        
        layout = QVBoxLayout(self)
        
        # Text edit - main focus of the dialog
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Enter quick event text. Use @name to tag characters (e.g., @John kissed @Mary)")
        layout.addWidget(self.text_edit)
        
        # Available characters section
        if self.options.get("show_character_tags", True) and self.characters:
            char_names = [f"@{char['name']}" for char in self.characters]
            characters_label = QLabel("Available character tags: " + ", ".join(char_names))
            characters_label.setWordWrap(True)
            characters_label.setStyleSheet("color: #666; font-style: italic;")
            layout.addWidget(characters_label)
            
            # Optional character note
            if self.options.get("show_optional_note", True) and self.options.get("allow_characterless_events", True):
                note_label = QLabel("Note: Character tagging is optional. You can create events without any character.")
                note_label.setWordWrap(True)
                note_label.setStyleSheet("color: #666; font-style: italic;")
                layout.addWidget(note_label)
        else:
            # No characters available
            no_chars_label = QLabel("No characters available. You can still create a general event.")
            no_chars_label.setWordWrap(True)
            no_chars_label.setStyleSheet("color: #666; font-style: italic;")
            layout.addWidget(no_chars_label)
        
        # Recent events section
        if self.options.get("show_recent_events", True) and self.recent_events:
            recent_label = QLabel("Recent events:")
            recent_label.setStyleSheet("color: #666; font-style: italic; margin-top: 5px;")
            layout.addWidget(recent_label)
            
            # Display each recent event
            for event in self.recent_events:
                # Format the display based on whether there's a character
                if event.get('character_name'):
                    text = f"{event['character_name']}: {event['text']}"
                else:
                    text = event['text']
                
                event_label = QLabel(text)
                event_label.setWordWrap(True)
                event_label.setStyleSheet("color: #888; font-size: 11px; margin-left: 10px;")
                layout.addWidget(event_label)
        
        # Extra options
        if self.context.get("allow_extra_options", False):
            option_layout = QHBoxLayout()
            
            # Add custom checkboxes or other UI elements based on context
            if self.context.get("show_associate_checkbox", False):
                self.associate_checkbox = QCheckBox("Associate with current context")
                self.associate_checkbox.setChecked(True)
                option_layout.addWidget(self.associate_checkbox)
            
            layout.addLayout(option_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_quick_event)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
    
    def setup_character_completer(self):
        """Setup character completer for @mentions."""
        self.tag_completer = CharacterCompleter(self)
        self.tag_completer.set_characters(self.characters)
        self.tag_completer.character_selected.connect(self.on_character_selected)
        self.tag_completer.attach_to_widget(
            self.text_edit,
            add_shortcut=True,
            shortcut_key="Ctrl+Space",
            at_trigger=True
        )
    
    def on_character_selected(self, character_name: str):
        """Handle character selection from completer."""
        self.tag_completer.insert_character_tag(character_name)
    
    def get_event_text(self) -> str:
        """Get the plain text from the editor."""
        return self.text_edit.toPlainText()
    
    def get_character_id(self) -> Optional[int]:
        """
        Get the character ID based on mentions and preferences.
        
        Returns:
            Character ID or None for a characterless event
        """
        # If a specific character is preferred, use it
        if self.preferred_character_id is not None:
            return self.preferred_character_id
            
        # Try to auto-detect from mentioned characters
        text = self.get_event_text()
        character_id = self.qe_manager.auto_detect_character(text, self.story_id)
        
        return character_id
    
    def save_quick_event(self):
        """Save the quick event and accept the dialog."""
        text = self.get_event_text()
        
        if not text.strip():
            QMessageBox.warning(self, "Error", "Please enter text for the quick event.")
            return
        
        # Get character ID
        character_id = self.get_character_id()
        
        # Check if characterless events are allowed
        if character_id is None and not self.options.get("allow_characterless_events", True):
            QMessageBox.warning(
                self, 
                "Error", 
                "No character detected. Please tag at least one character with @name."
            )
            return
        
        # Create the quick event
        try:
            quick_event_id = self.qe_manager.create_quick_event(
                text=text, 
                story_id=self.story_id,
                character_id=character_id
            )
            
            if quick_event_id:
                self.result_event_id = quick_event_id
                
                # Emit the signal with the result
                self.quick_event_created.emit(
                    quick_event_id, 
                    text, 
                    self.context
                )
                
                # Accept the dialog
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Failed to create quick event.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error creating quick event: {str(e)}")
    
    def get_result(self) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Get the result of the dialog.
        
        Returns:
            Tuple containing:
            - Success flag (True if a quick event was created)
            - Quick event ID (if created, otherwise None)
            - Text of the quick event (if created, otherwise None)
        """
        if self.result():
            return True, self.result_event_id, self.get_event_text()
        else:
            return False, None, None 