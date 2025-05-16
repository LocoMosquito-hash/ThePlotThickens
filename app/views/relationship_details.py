#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Relationship Details Dialog for The Plot Thickens application.

This module provides a dialog for viewing and editing relationships between characters.
"""

import os
from typing import Optional, Dict, Any, List, Tuple

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QLineEdit, QListWidget, QListWidgetItem,
    QComboBox, QCompleter, QSizePolicy, QWidget
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPoint
from PyQt6.QtGui import QPixmap, QIcon, QColor, QPainter, QPen

from app.db_sqlite import get_relationship_types, get_used_relationship_types


class SearchableComboBox(QComboBox):
    """A ComboBox with search functionality."""
    
    def __init__(self, parent=None):
        """Initialize the searchable combo box.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Make editable to allow searching
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        
        # Enable autocomplete
        self.completer = QCompleter(self.model())
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.setCompleter(self.completer)
        
        # Style the combo box
        self.setMinimumHeight(30)


class RelationshipCard(QFrame):
    """A card displaying a relationship between two characters."""
    
    def __init__(self, source_id: int, source_name: str, target_id: int, 
                 target_name: str, source_avatar: Optional[str] = None, 
                 target_avatar: Optional[str] = None, is_forward: bool = True, 
                 relationship_types: List[str] = None, parent=None):
        """Initialize the relationship card.
        
        Args:
            source_id: ID of the source character
            source_name: Name of the source character
            target_id: ID of the target character
            target_name: Name of the target character
            source_avatar: Path to the source character's avatar
            target_avatar: Path to the target character's avatar
            is_forward: If True, displays source -> target; if False, displays target -> source
            relationship_types: List of relationship types to populate the combobox
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.source_id = source_id
        self.source_name = source_name
        self.target_id = target_id
        self.target_name = target_name
        self.source_avatar = source_avatar
        self.target_avatar = target_avatar
        self.is_forward = is_forward
        self.relationship_types = relationship_types or []
        self._is_enabled = True
        
        # Set up the frame style
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setStyleSheet("""
            RelationshipCard {
                border-radius: 6px;
                padding: 8px;
            }
        """)
        
        self._init_ui()
    
    def setEnabled(self, enabled: bool) -> None:
        """Enable or disable the card.
        
        Args:
            enabled: Whether the card should be enabled
        """
        self._is_enabled = enabled
        super().setEnabled(enabled)
        
        # Update visual appearance
        if enabled:
            self.setStyleSheet("""
                RelationshipCard {
                    border-radius: 6px;
                    padding: 8px;
                }
            """)
        else:
            self.setStyleSheet("""
                RelationshipCard {
                    border-radius: 6px;
                    padding: 8px;
                    background-color: rgba(30, 30, 30, 180);
                }
            """)
        
        # Also enable/disable the combo box
        if hasattr(self, 'relationship_combo'):
            self.relationship_combo.setEnabled(enabled)
    
    def _init_ui(self) -> None:
        """Initialize the user interface."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)
        
        # Create left side with label and avatars
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        
        # Create label with relationship text
        if self.is_forward:
            label_text = f"{self.source_name} is {self.target_name}'s:"
        else:
            label_text = f"{self.target_name} is {self.source_name}'s:"
        
        relationship_label = QLabel(label_text)
        relationship_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(relationship_label)
        
        # Create avatars container with arrow
        avatars_widget = QWidget()
        avatars_layout = QHBoxLayout(avatars_widget)
        avatars_layout.setContentsMargins(0, 0, 0, 0)
        avatars_layout.setSpacing(10)
        
        # Add avatars and arrow in the correct order
        first_avatar = self._create_avatar(self.source_avatar if self.is_forward else self.target_avatar)
        arrow_label = self._create_arrow()
        second_avatar = self._create_avatar(self.target_avatar if self.is_forward else self.source_avatar)
        
        avatars_layout.addWidget(first_avatar)
        avatars_layout.addWidget(arrow_label)
        avatars_layout.addWidget(second_avatar)
        
        left_layout.addWidget(avatars_widget)
        main_layout.addWidget(left_widget)
        
        # Create right side with searchable combobox
        self.relationship_combo = SearchableComboBox()
        self.relationship_combo.addItems(self.relationship_types)
        self.relationship_combo.setCurrentIndex(-1)  # No selection by default
        self.relationship_combo.setPlaceholderText("Select relationship type...")
        
        main_layout.addWidget(self.relationship_combo)
    
    def _create_avatar(self, avatar_path: Optional[str] = None) -> QLabel:
        """Create an avatar label with the character's image.
        
        Args:
            avatar_path: Path to the avatar image
            
        Returns:
            QLabel with the avatar image
        """
        avatar_label = QLabel()
        avatar_label.setFixedSize(64, 64)
        avatar_label.setScaledContents(True)
        
        if avatar_path and os.path.exists(avatar_path):
            pixmap = QPixmap(avatar_path)
        else:
            # Use a default avatar if no avatar is available
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.GlobalColor.lightGray)
        
        avatar_label.setPixmap(pixmap)
        
        # Add a border to the avatar
        avatar_label.setStyleSheet("""
            QLabel {
                border: 1px solid #777777;
                background-color: #333333;
            }
        """)
        
        return avatar_label
    
    def _create_arrow(self) -> QLabel:
        """Create an arrow label pointing from source to target.
        
        Returns:
            QLabel with the arrow image
        """
        arrow_label = QLabel()
        arrow_label.setFixedSize(32, 32)
        
        # Create a pixmap for the arrow
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        # Draw the arrow
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pen = QPen(QColor("#FF0000"))
        pen.setWidth(2)
        painter.setPen(pen)
        
        # Draw arrow line
        painter.drawLine(5, 16, 27, 16)
        
        # Draw arrow head
        painter.drawLine(20, 8, 27, 16)
        painter.drawLine(20, 24, 27, 16)
        
        painter.end()
        
        arrow_label.setPixmap(pixmap)
        return arrow_label
    
    def get_selected_relationship(self) -> Optional[str]:
        """Get the selected relationship type.
        
        Returns:
            Selected relationship type or None if none selected
        """
        return self.relationship_combo.currentText() if self.relationship_combo.currentText() else None


class RelationshipDetailsDialog(QDialog):
    """Dialog for editing relationship details between characters."""
    
    def __init__(self, db_conn, source_id: int, source_name: str, target_id: int, 
                 target_name: str, parent=None):
        """Initialize the relationship details dialog.
        
        Args:
            db_conn: Database connection
            source_id: ID of the source character
            source_name: Name of the source character
            target_id: ID of the target character
            target_name: Name of the target character
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.db_conn = db_conn
        self.source_id = source_id
        self.source_name = source_name
        self.target_id = target_id
        self.target_name = target_name
        
        # Apply dark theme if available
        try:
            import qdarktheme
            qdarktheme.setup_theme()
        except ImportError:
            print("PyQtDarkTheme not available. Using default theme.")
        
        # Get avatar paths from the database
        self.source_avatar = self._get_character_avatar_path(source_id)
        self.target_avatar = self._get_character_avatar_path(target_id)
        
        # Set up the dialog
        self.setWindowTitle("Relationship Details")
        self.resize(600, 400)
        
        self._init_ui()
        
        # Initially disable the backward card
        self.backward_card.setEnabled(False)
        
        # Connect the forward card combo box's currentTextChanged signal
        self.forward_card.relationship_combo.currentTextChanged.connect(self._on_forward_relationship_changed)
    
    def _get_character_avatar_path(self, character_id: int) -> Optional[str]:
        """Get the avatar path for a character.
        
        Args:
            character_id: ID of the character
            
        Returns:
            Path to the avatar image file or None
        """
        if not character_id:
            return None
            
        try:
            cursor = self.db_conn.cursor()
            
            # Try characters.avatar_path first (most likely location)
            cursor.execute("""
                SELECT avatar_path 
                FROM characters 
                WHERE id = ?
            """, (character_id,))
            
            result = cursor.fetchone()
            if result and result[0]:
                avatar_path = result[0]
                if os.path.exists(avatar_path):
                    return avatar_path
                    
            # If not found or doesn't exist, try character_details.avatar_path
            cursor.execute("""
                SELECT avatar_path 
                FROM character_details 
                WHERE character_id = ?
            """, (character_id,))
            
            result = cursor.fetchone()
            if result and result[0]:
                avatar_path = result[0]
                if os.path.exists(avatar_path):
                    return avatar_path
            
            # If we still haven't found a valid avatar, try checking media folders
            # Look up the story_id for this character
            cursor.execute("SELECT story_id FROM characters WHERE id = ?", (character_id,))
            story_result = cursor.fetchone()
            
            if story_result and story_result[0]:
                story_id = story_result[0]
                
                # Get the character's name for constructing default avatar paths
                cursor.execute("SELECT name FROM characters WHERE id = ?", (character_id,))
                name_result = cursor.fetchone()
                if name_result and name_result[0]:
                    character_name = name_result[0]
                    
                    # Get story folder paths
                    cursor.execute("SELECT * FROM stories WHERE id = ?", (story_id,))
                    story_data = cursor.fetchone()
                    if story_data:
                        # Import here to avoid circular imports
                        from app.db_sqlite import get_story_folder_paths
                        folder_paths = get_story_folder_paths(dict(story_data))
                        
                        # Check common avatar locations
                        possible_locations = [
                            os.path.join(folder_paths.get('characters_folder', ''), f"{character_name}.png"),
                            os.path.join(folder_paths.get('characters_folder', ''), f"{character_name}.jpg"),
                            os.path.join(folder_paths.get('characters_folder', ''), f"avatar_{character_name}.png"),
                            os.path.join(folder_paths.get('characters_folder', ''), f"avatar_{character_name}.jpg"),
                            os.path.join(folder_paths.get('base_folder', ''), "characters", f"{character_name}.png"),
                            os.path.join(folder_paths.get('base_folder', ''), "characters", f"{character_name}.jpg")
                        ]
                        
                        for location in possible_locations:
                            if os.path.exists(location):
                                return location
                
        except Exception as e:
            print(f"Error getting character avatar: {e}")
            
        return None
    
    def _init_ui(self) -> None:
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)
        
        # Get relationship types from the database
        standard_types = [rt['name'] for rt in get_relationship_types(self.db_conn)]
        used_types = get_used_relationship_types(self.db_conn)
        
        # Combine lists with used types at the top
        relationship_items = []
        
        # Add used types first (if they exist)
        if used_types:
            relationship_items.extend(used_types)
            relationship_items.append("---")  # Separator
        
        # Add standard types
        relationship_items.extend(standard_types)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_items = []
        for item in relationship_items:
            if item not in seen and item != "---":
                seen.add(item)
                unique_items.append(item)
            elif item == "---" and unique_items:  # Only add separator if we have items before it
                unique_items.append(item)
        
        # Create the forward relationship card (A -> B)
        self.forward_card = RelationshipCard(
            self.source_id, self.source_name, 
            self.target_id, self.target_name,
            self.source_avatar, self.target_avatar,
            True, unique_items
        )
        main_layout.addWidget(self.forward_card)
        
        # Create the backward relationship card (B -> A)
        self.backward_card = RelationshipCard(
            self.source_id, self.source_name, 
            self.target_id, self.target_name,
            self.source_avatar, self.target_avatar,
            False, unique_items
        )
        main_layout.addWidget(self.backward_card)
        
        # Add stretch to push everything up
        main_layout.addStretch()
        
        # Create buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(10)
        
        # Add spacer to push buttons to the right
        buttons_layout.addStretch()
        
        # Create Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        # Create Apply button
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.apply_button)
        
        main_layout.addLayout(buttons_layout)
    
    def get_selected_relationships(self) -> Tuple[Optional[str], Optional[str]]:
        """Get the selected relationship types.
        
        Returns:
            Tuple of (forward_relationship, backward_relationship)
        """
        forward_relationship = self.forward_card.get_selected_relationship()
        backward_relationship = self.backward_card.get_selected_relationship()
        
        return forward_relationship, backward_relationship
    
    def _on_forward_relationship_changed(self, text: str) -> None:
        """Handle when the forward relationship type changes.
        
        Args:
            text: Selected relationship type text
        """
        # Enable the backward card only if a valid relationship type is selected
        self.backward_card.setEnabled(bool(text)) 