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
    QTextEdit, QCheckBox, QMessageBox, QComboBox, QRadioButton, 
    QButtonGroup, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFocusEvent

from app.utils.character_completer import CharacterCompleter
from app.utils.quick_event_manager import QuickEventManager
from app.db_sqlite import get_story_characters

class FocusAwareTextEdit(QTextEdit):
    """QTextEdit subclass that emits a signal when it receives focus."""
    
    focused = pyqtSignal()
    
    def focusInEvent(self, event: QFocusEvent) -> None:
        """Override to emit signal while preserving original behavior."""
        super().focusInEvent(event)
        self.focused.emit()

class FocusAwareComboBox(QComboBox):
    """QComboBox subclass that emits a signal when it receives focus."""
    
    focused = pyqtSignal()
    
    def focusInEvent(self, event: QFocusEvent) -> None:
        """Override to emit signal while preserving original behavior."""
        super().focusInEvent(event)
        self.focused.emit()

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
        self.selected_existing_event_id = None
        
        # Create a quick event manager
        self.qe_manager = QuickEventManager(db_conn)
        
        # Get all characters for the story for tagging
        self.characters = get_story_characters(db_conn, self.story_id)
        
        # Load recent quick events
        self.recent_events = []
        self.recent_events = self.qe_manager.get_recent_events(self.story_id, limit=15)
        
        # Initialize UI
        self.init_ui()
        
        # Setup character completer
        self.setup_character_completer()
        
        # Set initial text if provided
        if self.initial_text:
            self.text_edit.setText(self.initial_text)
            self.text_radio.setChecked(True)
    
    def init_ui(self):
        """Initialize the user interface."""
        # Use custom title if provided
        if "title" in self.options:
            self.setWindowTitle(self.options["title"])
        else:
            self.setWindowTitle("Create Quick Event")
            
        self.resize(450, 300)
        
        layout = QVBoxLayout(self)
        
        # Check if we're in the Character Recognition window context
        is_char_recog = self.context.get("source", "").startswith("recognition_dialog")
        
        # Create button group for radio buttons
        self.input_group = QButtonGroup(self)
        
        # If in Character Recognition context, show the dropdown for existing events
        if is_char_recog:
            # Existing Events Dropdown Section
            existing_group = QGroupBox("Choose Existing Event")
            existing_layout = QVBoxLayout(existing_group)
            
            # Radio button for existing events
            self.existing_radio = QRadioButton("Use existing quick event:")
            self.input_group.addButton(self.existing_radio)
            existing_layout.addWidget(self.existing_radio)
            
            # Dropdown for recent events - using our custom subclass
            self.events_dropdown = FocusAwareComboBox()
            self.events_dropdown.addItem("Select an existing quick event", None)
            self.events_dropdown.focused.connect(lambda: self.existing_radio.setChecked(True))
            
            # Populate dropdown with recent events
            for event in self.recent_events:
                display_text = event.get('text', '')
                if len(display_text) > 60:
                    display_text = display_text[:57] + "..."
                    
                # Format differently based on character or anonymous event
                if event.get('character_name'):
                    item_text = f"{event['character_name']}: {display_text}"
                else:
                    item_text = f"Anonymous: {display_text}"
                    
                self.events_dropdown.addItem(item_text, event.get('id'))
            
            self.events_dropdown.currentIndexChanged.connect(self.on_event_selected)
            existing_layout.addWidget(self.events_dropdown)
            
            layout.addWidget(existing_group)
            
            # New Event Section
            new_group = QGroupBox("Create New Event")
            new_layout = QVBoxLayout(new_group)
            
            # Radio button for new event
            self.text_radio = QRadioButton("Create new quick event:")
            self.input_group.addButton(self.text_radio)
            new_layout.addWidget(self.text_radio)
            
            # Text edit for new event - using our custom subclass
            self.text_edit = FocusAwareTextEdit()
            self.text_edit.setPlaceholderText("Enter quick event text. Use @name to tag characters (e.g., @John kissed @Mary)")
            self.text_edit.focused.connect(lambda: self.text_radio.setChecked(True))
            new_layout.addWidget(self.text_edit)
            
            layout.addWidget(new_group)
            
            # Set default selection
            self.text_radio.setChecked(True)
        else:
            # Regular text edit without dropdown for other contexts
            self.text_radio = QRadioButton()  # Hidden radio button for consistency
            self.input_group.addButton(self.text_radio)
            self.text_radio.setChecked(True)
            self.text_radio.hide()
            
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
                
            # Special note for force_anonymous mode
            if self.options.get("force_anonymous", False):
                force_anon_label = QLabel("Note: This quick event will be created without a character owner.")
                force_anon_label.setWordWrap(True)
                force_anon_label.setStyleSheet("color: #c44; font-style: italic;")
                layout.addWidget(force_anon_label)
        else:
            # No characters available
            no_chars_label = QLabel("No characters available. You can still create a general event.")
            no_chars_label.setWordWrap(True)
            no_chars_label.setStyleSheet("color: #666; font-style: italic;")
            layout.addWidget(no_chars_label)
        
        # Show recent events section only if not in Character Recognition (since we already show them in dropdown)
        if not is_char_recog and self.options.get("show_recent_events", True) and self.recent_events:
            recent_label = QLabel("Recent events:")
            recent_label.setStyleSheet("color: #666; font-style: italic; margin-top: 5px;")
            layout.addWidget(recent_label)
            
            # Display each recent event
            for event in self.recent_events[:3]:  # Limit to 3 to save space
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
    
    def on_event_selected(self, index: int):
        """Handle selection of an event from the dropdown."""
        if hasattr(self, 'existing_radio'):
            self.existing_radio.setChecked(True)
        
        if hasattr(self, 'events_dropdown'):
            self.selected_existing_event_id = self.events_dropdown.currentData()
    
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
        
        # Make sure text input radio is selected when typing character tags
        if hasattr(self, 'text_radio'):
            self.text_radio.setChecked(True)
    
    def get_event_text(self) -> str:
        """Get the plain text from the editor."""
        return self.text_edit.toPlainText()
    
    def get_character_id(self) -> Optional[int]:
        """
        Get the character ID based on mentions and preferences.
        
        Returns:
            Character ID or None for a characterless event
        """
        # Check if we're forcing anonymous events (no character_id)
        if self.options.get("force_anonymous", False):
            print("[DEBUG] Forcing anonymous quick event (no character)")
            return None
            
        # If a specific character is preferred, use it
        if self.preferred_character_id is not None:
            # Ensure we return an integer even if a dictionary was passed
            if isinstance(self.preferred_character_id, dict) and 'id' in self.preferred_character_id:
                return int(self.preferred_character_id['id'])
            elif isinstance(self.preferred_character_id, (int, str)):
                return int(self.preferred_character_id)
            else:
                print(f"WARNING: Unexpected character_id type: {type(self.preferred_character_id)}")
                return None
            
        # Try to auto-detect from mentioned characters
        text = self.get_event_text()
        character_id = self.qe_manager.auto_detect_character(text, self.story_id)
        
        return character_id
    
    def save_quick_event(self):
        """Save the quick event and accept the dialog."""
        # Check if we're in Character Recognition mode with radio buttons
        is_char_recog = hasattr(self, 'existing_radio') and hasattr(self, 'text_radio')
        
        if is_char_recog:
            # Using existing event
            if self.existing_radio.isChecked():
                if not self.selected_existing_event_id:
                    QMessageBox.warning(self, "Error", "Please select an existing quick event from the dropdown.")
                    return
                
                # Find the selected event text
                for event in self.recent_events:
                    if event.get('id') == self.selected_existing_event_id:
                        # We return the existing event's ID and text
                        self.result_event_id = self.selected_existing_event_id
                        
                        # Emit the signal with the result
                        self.quick_event_created.emit(
                            self.selected_existing_event_id,
                            event.get('text', ''),
                            self.context
                        )
                        
                        # Accept the dialog
                        self.accept()
                        return
                        
                # If we get here, something went wrong
                QMessageBox.warning(self, "Error", "Selected event not found.")
                return
            
            # Creating new event (text radio selected)
            elif self.text_radio.isChecked():
                text = self.get_event_text()
                
                if not text.strip():
                    QMessageBox.warning(self, "Error", "Please enter text for the quick event.")
                    return
                
                # Continue with normal quick event creation flow
            else:
                # Neither radio button selected (shouldn't happen)
                QMessageBox.warning(self, "Error", "Please either select an existing event or create a new one.")
                return
        else:
            # Regular mode - just get the text
            text = self.get_event_text()
            
            if not text.strip():
                QMessageBox.warning(self, "Error", "Please enter text for the quick event.")
                return
        
        # From here, we're creating a new event
        
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
            # Make sure we're passing the correct story_id (as an integer)
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
            import traceback
            print(f"Error creating quick event: {e}")
            print(traceback.format_exc())
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