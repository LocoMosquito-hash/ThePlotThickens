#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Batch Character Tagging Dialog for The Plot Thickens application.

This module contains the dialog for batch tagging/untagging characters from multiple images.
"""

from typing import List, Dict, Any, Set
import os
import logging

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox, QProgressDialog,
    QApplication, QWidget, QFrame
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QPixmap, QFont

from app.db_sqlite import (
    get_story_characters, add_character_tag_to_image, 
    remove_character_tag, get_image_character_tags,
    update_character_last_tagged
)


class CharacterListItem(QListWidgetItem):
    """Custom list item for displaying characters with avatars."""
    
    def __init__(self, character_data: Dict[str, Any], parent=None):
        """Initialize the character list item.
        
        Args:
            character_data: Character data dictionary
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.character_data = character_data
        self.character_id = character_data["id"]
        self.character_name = character_data["name"]
        
        # Set the display text
        self.setText(self.character_name)
        
        # Store character data
        self.setData(Qt.ItemDataRole.UserRole, character_data)
        
        # Set item size hint for avatar display
        self.setSizeHint(QSize(200, 60))
        
        # Load avatar if available
        self._load_avatar()
    
    def _load_avatar(self):
        """Load character avatar if available."""
        # Check if character has an avatar path
        avatar_path = self.character_data.get("avatar_path")
        
        if avatar_path and os.path.exists(avatar_path):
            # Load the avatar image
            pixmap = QPixmap(avatar_path)
            
            if not pixmap.isNull():
                # Scale the avatar to a reasonable size
                scaled_pixmap = pixmap.scaled(
                    QSize(48, 48),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                # Set as icon (convert QPixmap to QIcon)
                from PyQt6.QtGui import QIcon
                self.setIcon(QIcon(scaled_pixmap))
        else:
            # Create a placeholder avatar with initials
            self._create_placeholder_avatar()
    
    def _create_placeholder_avatar(self):
        """Create a placeholder avatar with character initials."""
        # Create a simple colored square with initials
        pixmap = QPixmap(48, 48)
        
        # Use a hash of the character name to generate a consistent color
        name_hash = hash(self.character_name)
        hue = abs(name_hash) % 360
        
        # Create a color based on the hash
        from PyQt6.QtGui import QColor, QPainter, QBrush
        color = QColor.fromHsv(hue, 180, 200)
        pixmap.fill(color)
        
        # Draw initials
        painter = QPainter(pixmap)
        painter.setPen(Qt.GlobalColor.white)
        painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        
        # Get initials (first letter of each word, max 2)
        words = self.character_name.split()
        initials = ""
        for word in words[:2]:
            if word:
                initials += word[0].upper()
        
        # Draw the initials centered
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, initials)
        painter.end()
        
        # Set as icon (convert QPixmap to QIcon)
        from PyQt6.QtGui import QIcon
        self.setIcon(QIcon(pixmap))


class BatchCharacterTaggingDialog(QDialog):
    """Dialog for batch tagging/untagging characters from multiple images."""
    
    def __init__(self, db_conn, story_id: int, selected_image_ids: Set[int], parent=None):
        """Initialize the batch character tagging dialog.
        
        Args:
            db_conn: Database connection
            story_id: ID of the current story
            selected_image_ids: Set of selected image IDs
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.db_conn = db_conn
        self.story_id = story_id
        self.selected_image_ids = selected_image_ids
        
        # Set up the dialog
        self.setWindowTitle("Batch Character Tagging")
        self.setModal(True)
        self.resize(400, 600)
        
        # Initialize UI
        self.init_ui()
        
        # Load characters
        self.load_characters()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Header with information
        header_label = QLabel(f"Batch Character Tagging")
        header_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(header_label)
        
        # Info about selected images
        info_label = QLabel(f"Selected images: {len(self.selected_image_ids)}")
        info_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(info_label)
        
        # Instructions
        instructions = QLabel(
            "Select a character from the list below, then choose to tag or untag "
            "them from all selected images."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 10px;")
        layout.addWidget(instructions)
        
        # Character list
        characters_label = QLabel("Characters:")
        characters_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(characters_label)
        
        self.characters_list = QListWidget()
        self.characters_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.characters_list.itemSelectionChanged.connect(self.on_character_selection_changed)
        layout.addWidget(self.characters_list)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        
        self.tag_button = QPushButton("Tag Character")
        self.tag_button.setEnabled(False)
        self.tag_button.clicked.connect(self.tag_character)
        self.tag_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        actions_layout.addWidget(self.tag_button)
        
        self.untag_button = QPushButton("Untag Character")
        self.untag_button.setEnabled(False)
        self.untag_button.clicked.connect(self.untag_character)
        self.untag_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        actions_layout.addWidget(self.untag_button)
        
        layout.addLayout(actions_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Close button
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        close_button.setDefault(True)
        close_layout.addWidget(close_button)
        
        layout.addLayout(close_layout)
    
    def load_characters(self):
        """Load characters from the database and populate the list."""
        try:
            # Get all characters for this story
            characters = get_story_characters(self.db_conn, self.story_id)
            
            # Sort alphabetically by name
            characters.sort(key=lambda x: x["name"].lower())
            
            # Clear the list
            self.characters_list.clear()
            
            # Add characters to the list
            for character in characters:
                item = CharacterListItem(character)
                self.characters_list.addItem(item)
            
            # Update status
            if not characters:
                # Show a message if no characters exist
                no_chars_item = QListWidgetItem("No characters found in this story")
                no_chars_item.setFlags(Qt.ItemFlag.NoItemFlags)  # Make it non-selectable
                no_chars_item.setForeground(Qt.GlobalColor.gray)
                self.characters_list.addItem(no_chars_item)
        
        except Exception as e:
            logging.exception(f"Error loading characters: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load characters: {str(e)}")
    
    def on_character_selection_changed(self):
        """Handle character selection changes."""
        selected_items = self.characters_list.selectedItems()
        
        # Enable/disable buttons based on selection
        has_selection = len(selected_items) > 0 and selected_items[0].data(Qt.ItemDataRole.UserRole) is not None
        
        self.tag_button.setEnabled(has_selection)
        self.untag_button.setEnabled(has_selection)
    
    def get_selected_character(self) -> Dict[str, Any]:
        """Get the currently selected character.
        
        Returns:
            Character data dictionary or None if no selection
        """
        selected_items = self.characters_list.selectedItems()
        
        if not selected_items:
            return None
        
        character_data = selected_items[0].data(Qt.ItemDataRole.UserRole)
        return character_data
    
    def tag_character(self):
        """Tag the selected character to all selected images."""
        character = self.get_selected_character()
        
        if not character:
            QMessageBox.warning(self, "No Selection", "Please select a character to tag.")
            return
        
        character_id = character["id"]
        character_name = character["name"]
        
        # Confirm the action
        reply = QMessageBox.question(
            self,
            "Confirm Tagging",
            f"Tag '{character_name}' to {len(self.selected_image_ids)} selected images?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Create progress dialog
        progress = QProgressDialog(
            f"Tagging '{character_name}' to images...",
            "Cancel",
            0,
            len(self.selected_image_ids),
            self
        )
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(500)
        
        # Process each image
        tagged_count = 0
        skipped_count = 0
        
        try:
            for i, image_id in enumerate(self.selected_image_ids):
                # Check if user cancelled
                if progress.wasCanceled():
                    break
                
                # Update progress
                progress.setValue(i)
                progress.setLabelText(f"Processing image {i + 1} of {len(self.selected_image_ids)}...")
                QApplication.processEvents()
                
                # Check if character is already tagged to this image
                existing_tags = get_image_character_tags(self.db_conn, image_id)
                already_tagged = any(tag["character_id"] == character_id for tag in existing_tags)
                
                if already_tagged:
                    skipped_count += 1
                    continue
                
                # Add the character tag (using center position as default)
                tag_id = add_character_tag_to_image(
                    self.db_conn,
                    image_id,
                    character_id,
                    0.5,  # x_position (center)
                    0.5,  # y_position (center)
                    0.2,  # width (20% of image)
                    0.2,  # height (20% of image)
                    f"Batch tagged as {character_name}"
                )
                
                if tag_id:
                    tagged_count += 1
            
            # Update character's last tagged timestamp
            if tagged_count > 0:
                update_character_last_tagged(self.db_conn, self.story_id, character_id)
            
            # Complete progress
            progress.setValue(len(self.selected_image_ids))
            
            # Show results
            message = f"Tagging complete!\n\n"
            message += f"Tagged: {tagged_count} images\n"
            if skipped_count > 0:
                message += f"Skipped: {skipped_count} images (already tagged)"
            
            QMessageBox.information(self, "Tagging Complete", message)
        
        except Exception as e:
            logging.exception(f"Error during batch tagging: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred during tagging: {str(e)}")
        
        finally:
            progress.close()
    
    def untag_character(self):
        """Untag the selected character from all selected images."""
        character = self.get_selected_character()
        
        if not character:
            QMessageBox.warning(self, "No Selection", "Please select a character to untag.")
            return
        
        character_id = character["id"]
        character_name = character["name"]
        
        # Confirm the action
        reply = QMessageBox.question(
            self,
            "Confirm Untagging",
            f"Remove '{character_name}' tags from {len(self.selected_image_ids)} selected images?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Create progress dialog
        progress = QProgressDialog(
            f"Removing '{character_name}' tags from images...",
            "Cancel",
            0,
            len(self.selected_image_ids),
            self
        )
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(500)
        
        # Process each image
        removed_count = 0
        not_found_count = 0
        
        try:
            for i, image_id in enumerate(self.selected_image_ids):
                # Check if user cancelled
                if progress.wasCanceled():
                    break
                
                # Update progress
                progress.setValue(i)
                progress.setLabelText(f"Processing image {i + 1} of {len(self.selected_image_ids)}...")
                QApplication.processEvents()
                
                # Get existing tags for this image and character
                existing_tags = get_image_character_tags(self.db_conn, image_id)
                character_tags = [tag for tag in existing_tags if tag["character_id"] == character_id]
                
                if not character_tags:
                    not_found_count += 1
                    continue
                
                # Remove all tags for this character from this image
                for tag in character_tags:
                    success = remove_character_tag(self.db_conn, tag["id"])
                    if success:
                        removed_count += 1
            
            # Complete progress
            progress.setValue(len(self.selected_image_ids))
            
            # Show results
            message = f"Untagging complete!\n\n"
            message += f"Removed: {removed_count} tags\n"
            if not_found_count > 0:
                message += f"Not found: {not_found_count} images (character not tagged)"
            
            QMessageBox.information(self, "Untagging Complete", message)
        
        except Exception as e:
            logging.exception(f"Error during batch untagging: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred during untagging: {str(e)}")
        
        finally:
            progress.close() 