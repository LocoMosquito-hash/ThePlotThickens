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
from PyQt6.QtCore import Qt

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
        
        self.setWindowTitle("Move to Scene")
        self.init_ui()
        self.load_scenes()
        
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
        
    def load_scenes(self) -> None:
        """Load the scenes from the database."""
        cursor = self.db_conn.cursor()
        
        # Get all scenes in this story
        cursor.execute("""
            SELECT id, name FROM scenes 
            WHERE story_id = ? 
            ORDER BY name
        """, (self.story_id,))
        
        scenes = cursor.fetchall()
        
        for scene in scenes:
            scene_id, name = scene
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, scene_id)
            self.scene_list.addItem(item)
    
    def on_selection_changed(self) -> None:
        """Handle selection changes."""
        # Enable the move button if either a scene is selected or a new scene name is entered
        has_selection = len(self.scene_list.selectedItems()) > 0
        has_new_scene = bool(self.new_scene_input.text().strip())
        
        self.move_button.setEnabled(has_selection or has_new_scene)
    
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
            self.new_scene_name = self.new_scene_input.text().strip()
            cursor = self.db_conn.cursor()
            
            cursor.execute("""
                INSERT INTO scenes (story_id, name)
                VALUES (?, ?)
            """, (self.story_id, self.new_scene_name))
            
            self.db_conn.commit()
            
            # Get the ID of the newly created scene
            cursor.execute("""
                SELECT id FROM scenes 
                WHERE story_id = ? AND name = ?
                ORDER BY id DESC LIMIT 1
            """, (self.story_id, self.new_scene_name))
            
            result = cursor.fetchone()
            if result:
                self.selected_scene_id = result[0]
        else:
            # Use selected scene
            selected_items = self.scene_list.selectedItems()
            if selected_items:
                self.selected_scene_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        
        self.accept()
