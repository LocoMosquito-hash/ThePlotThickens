#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scene selection dialog for The Plot Thickens gallery.

Provides an interface for selecting a scene to move images to.
"""

from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, 
    QPushButton, QHBoxLayout, QLineEdit
)
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QKeyEvent

# Import character completer and database functions
from app.utils.character_completer import CharacterCompleter, convert_mentions_to_char_refs
from app.db_sqlite import get_story_characters
from app.utils.character_references import convert_char_refs_to_mentions

class SceneSelectionDialog(QDialog):
    """Dialog for selecting a scene to move images to."""
    
    def __init__(self, db_conn, story_id: int, parent=None):
        """Initialize the dialog.
        
        Args:
            db_conn: Database connection
            story_id: ID of the story
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.story_id = story_id
        self.selected_scene_id = None
        self.new_scene_name = None
        self.characters = []  # Initialize characters list
        
        self.setWindowTitle("Move to Scene")
        self.init_ui()
        self.load_characters()  # Load characters first
        self.load_scenes()      # Then load scenes (so character conversion works)
        
    def init_ui(self) -> None:
        """Initialize the UI."""
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel("Select a scene to move the selected images to:")
        layout.addWidget(instructions)
        
        # Scene list
        self.scene_list = QListWidget()
        self.scene_list.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.scene_list)
        
        # New scene group
        new_scene_layout = QHBoxLayout()
        new_scene_layout.addWidget(QLabel("Or create new scene:"))
        
        self.new_scene_input = QLineEdit()
        self.new_scene_input.setPlaceholderText("Enter scene name")
        self.new_scene_input.textChanged.connect(self.on_selection_changed)
        new_scene_layout.addWidget(self.new_scene_input)
        
        layout.addLayout(new_scene_layout)
        
        # Set up character completer for the new scene input
        self.character_completer = CharacterCompleter(self)
        self.character_completer.character_selected.connect(self.on_character_selected)
        self.character_completer.attach_to_widget(
            self.new_scene_input,
            add_shortcut=True,
            shortcut_key="Ctrl+Space",
            at_trigger=True
        )
        
        # Buttons
        button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        self.move_button = QPushButton("Move Images")
        self.move_button.clicked.connect(self.on_move_to_scene)
        self.move_button.setEnabled(False)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.move_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.resize(400, 500)
        
    def load_characters(self) -> None:
        """Load characters for the current story to enable character completion."""
        try:
            self.characters = get_story_characters(self.db_conn, self.story_id)
            # Set characters in the completer
            if hasattr(self, 'character_completer'):
                self.character_completer.set_characters(self.characters)
        except Exception as e:
            print(f"Error loading characters: {e}")
            self.characters = []
        
    def on_character_selected(self, character_name: str) -> None:
        """Handle character selection from the completer.
        
        Args:
            character_name: Name of the selected character
        """
        # Let the character completer handle the tag insertion
        self.character_completer.insert_character_tag(character_name)
        
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events for the dialog.
        
        Args:
            event: Key event
        """
        key = event.key()
        
        # Handle Escape key to close dialog
        if key == Qt.Key.Key_Escape:
            self.reject()
            event.accept()
            return
            
        # Handle Enter key when new scene input has focus
        if (key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter):
            # Check if the new scene input has focus and has text
            if (self.new_scene_input.hasFocus() and 
                self.new_scene_input.text().strip() and 
                self.move_button.isEnabled()):
                self.on_move_to_scene()
                event.accept()
                return
            # If scene list has focus or selection, also allow Enter to trigger move
            elif (self.scene_list.hasFocus() and 
                  self.scene_list.selectedItems() and 
                  self.move_button.isEnabled()):
                self.on_move_to_scene()
                event.accept()
                return
        
        # Let parent handle other events
        super().keyPressEvent(event)
        
    def load_scenes(self) -> None:
        """Load the scenes from the database."""
        cursor = self.db_conn.cursor()
        
        # Get all scenes in this story (scenes are stored as events with event_type = 'SCENE')
        cursor.execute("""
            SELECT id, title, sequence_number FROM events 
            WHERE story_id = ? AND event_type = 'SCENE'
            ORDER BY sequence_number DESC
        """, (self.story_id,))
        
        scenes = cursor.fetchall()
        
        for scene in scenes:
            scene_id = scene['id']
            title = scene['title']
            
            # Convert character references to readable names for display
            display_title = convert_char_refs_to_mentions(title, self.characters)
            
            item = QListWidgetItem(display_title)
            item.setData(Qt.ItemDataRole.UserRole, scene_id)
            self.scene_list.addItem(item)
    
    def on_selection_changed(self) -> None:
        """Handle selection changes."""
        # Enable the move button if either a scene is selected or a new scene name is entered
        has_selection = len(self.scene_list.selectedItems()) > 0
        has_new_scene = bool(self.new_scene_input.text().strip())
        
        self.move_button.setEnabled(has_selection or has_new_scene)
        
        # Update the selected scene ID
        selected_items = self.scene_list.selectedItems()
        if selected_items:
            self.selected_scene_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        else:
            self.selected_scene_id = None
    
    def get_selected_scene_id(self) -> Optional[int]:
        """Get the ID of the selected scene.
        
        Returns:
            Selected scene ID, or None if no scene was selected
        """
        return self.selected_scene_id
    
    def on_move_to_scene(self) -> None:
        """Handle the move button click."""
        if self.new_scene_input.text().strip():
            # Create a new scene
            scene_name = self.new_scene_input.text().strip()
            
            # Convert character mentions to references before saving
            processed_scene_name = convert_mentions_to_char_refs(scene_name, self.characters)
            
            self.new_scene_name = processed_scene_name
            cursor = self.db_conn.cursor()
            
            # Get the next sequence number for scenes
            cursor.execute("""
                SELECT MAX(sequence_number) as max_seq FROM events
                WHERE story_id = ? AND event_type = 'SCENE'
            """, (self.story_id,))
            
            result = cursor.fetchone()
            next_seq = (result['max_seq'] + 1) if result and result['max_seq'] is not None else 0
            
            # Insert the new scene as an event
            cursor.execute("""
                INSERT INTO events (story_id, title, event_type, sequence_number, created_at, updated_at)
                VALUES (?, ?, 'SCENE', ?, datetime('now'), datetime('now'))
            """, (self.story_id, processed_scene_name, next_seq))
            
            self.db_conn.commit()
            
            # Get the ID of the newly created scene
            cursor.execute("""
                SELECT id FROM events 
                WHERE story_id = ? AND event_type = 'SCENE' AND title = ?
                ORDER BY id DESC LIMIT 1
            """, (self.story_id, processed_scene_name))
            
            result = cursor.fetchone()
            if result:
                self.selected_scene_id = result['id']
        else:
            # Use selected scene
            selected_items = self.scene_list.selectedItems()
            if selected_items:
                self.selected_scene_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        
        self.accept()
