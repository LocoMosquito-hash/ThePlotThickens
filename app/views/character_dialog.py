#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Character Dialog for The Plot Thickens application.

This module defines the dialog for adding and editing characters.
"""

import os
import sys
from typing import Optional, Dict, Any, Tuple

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox,
    QDialogButtonBox, QGroupBox, QMessageBox, QCheckBox,
    QSpinBox, QFileDialog, QApplication
)
from PyQt6.QtCore import Qt, QSettings, QBuffer, QByteArray, QSize, QDateTime
from PyQt6.QtGui import QPixmap, QImage, QClipboard


class CharacterDialog(QDialog):
    """Dialog for adding and editing characters."""
    
    def __init__(self, parent=None, story_id: int = None, character_data: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the character dialog.
        
        Args:
            parent: Parent widget
            story_id: ID of the story this character belongs to
            character_data: Character data for editing, or None for a new character
        """
        super().__init__(parent)
        
        self.story_id = story_id
        self.character_data = character_data or {}
        self.is_editing = bool(character_data)
        self.avatar_pixmap: Optional[QPixmap] = None
        self.avatar_path: Optional[str] = None
        
        self.settings = QSettings("ThePlotThickens", "ThePlotThickens")
        
        self.init_ui()
        self.load_character_data()
    
    def init_ui(self) -> None:
        """Set up the user interface."""
        # Set window properties
        self.setWindowTitle("Add Character" if not self.is_editing else "Edit Character")
        self.setMinimumWidth(500)
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create basic info group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        # Create name field
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter character name (or leave blank for 'Unnamed')")
        basic_layout.addRow("Name:", self.name_edit)
        
        # Create aliases field
        self.aliases_edit = QLineEdit()
        self.aliases_edit.setPlaceholderText("Separate aliases with commas")
        basic_layout.addRow("Aliases:", self.aliases_edit)
        
        # Create main character checkbox
        self.mc_checkbox = QCheckBox("Main Character")
        basic_layout.addRow("", self.mc_checkbox)
        
        # Create age fields
        age_layout = QHBoxLayout()
        
        self.age_value_spin = QSpinBox()
        self.age_value_spin.setRange(0, 999)
        self.age_value_spin.setSpecialValueText("Not specified")
        age_layout.addWidget(self.age_value_spin)
        
        self.age_category_combo = QComboBox()
        self.age_category_combo.addItem("Not specified", "")
        self.age_category_combo.addItem("Minor", "MINOR")
        self.age_category_combo.addItem("Teen", "TEEN")
        self.age_category_combo.addItem("Young", "YOUNG")
        self.age_category_combo.addItem("Adult", "ADULT")
        self.age_category_combo.addItem("Middle-aged", "MIDDLE_AGED")
        self.age_category_combo.addItem("Mature", "MATURE")
        self.age_category_combo.addItem("Old", "OLD")
        age_layout.addWidget(self.age_category_combo)
        
        basic_layout.addRow("Age:", age_layout)
        
        # Create gender field
        self.gender_combo = QComboBox()
        self.gender_combo.addItem("Not specified", "NOT_SPECIFIED")
        self.gender_combo.addItem("Male", "MALE")
        self.gender_combo.addItem("Female", "FEMALE")
        self.gender_combo.addItem("Futa", "FUTA")
        basic_layout.addRow("Gender:", self.gender_combo)
        
        main_layout.addWidget(basic_group)
        
        # Create avatar group
        avatar_group = QGroupBox("Avatar")
        avatar_layout = QVBoxLayout(avatar_group)
        
        # Create avatar preview
        self.avatar_preview = QLabel("No avatar")
        self.avatar_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_preview.setMinimumHeight(200)
        self.avatar_preview.setStyleSheet("background-color: #CCCCCC; border: 1px solid #999999;")
        avatar_layout.addWidget(self.avatar_preview)
        
        # Create avatar buttons
        avatar_buttons_layout = QHBoxLayout()
        
        self.paste_button = QPushButton("Paste from Clipboard")
        self.paste_button.clicked.connect(self.on_paste_avatar)
        avatar_buttons_layout.addWidget(self.paste_button)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.on_browse_avatar)
        avatar_buttons_layout.addWidget(self.browse_button)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.on_clear_avatar)
        avatar_buttons_layout.addWidget(self.clear_button)
        
        avatar_layout.addLayout(avatar_buttons_layout)
        
        main_layout.addWidget(avatar_group)
        
        # Add dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.on_accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
    
    def load_character_data(self) -> None:
        """Load character data into the form."""
        if not self.character_data:
            return
        
        # Load basic info
        self.name_edit.setText(self.character_data.get('name', ''))
        self.aliases_edit.setText(self.character_data.get('aliases', ''))
        self.mc_checkbox.setChecked(bool(self.character_data.get('is_main_character', False)))
        
        # Load age
        age_value = self.character_data.get('age_value')
        if age_value is not None:
            self.age_value_spin.setValue(age_value)
        
        age_category = self.character_data.get('age_category', '')
        index = self.age_category_combo.findData(age_category)
        if index >= 0:
            self.age_category_combo.setCurrentIndex(index)
        
        # Load gender
        gender = self.character_data.get('gender', 'NOT_SPECIFIED')
        index = self.gender_combo.findData(gender)
        if index >= 0:
            self.gender_combo.setCurrentIndex(index)
        
        # Load avatar
        avatar_path = self.character_data.get('avatar_path')
        if avatar_path and os.path.exists(avatar_path):
            self.avatar_path = avatar_path
            self.avatar_pixmap = QPixmap(avatar_path)
            self.update_avatar_preview()
    
    def on_paste_avatar(self) -> None:
        """Handle paste avatar button click."""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasImage():
            image = QImage(mime_data.imageData())
            if not image.isNull():
                self.avatar_pixmap = QPixmap.fromImage(image)
                self.update_avatar_preview()
            else:
                QMessageBox.warning(
                    self,
                    "Invalid Image",
                    "The clipboard contains an invalid image."
                )
        else:
            QMessageBox.warning(
                self,
                "No Image",
                "No image found in clipboard. Copy an image first."
            )
    
    def on_browse_avatar(self) -> None:
        """Handle browse avatar button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Avatar Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            self.avatar_pixmap = QPixmap(file_path)
            self.update_avatar_preview()
    
    def on_clear_avatar(self) -> None:
        """Handle clear avatar button click."""
        self.avatar_pixmap = None
        self.avatar_path = None
        self.avatar_preview.setText("No avatar")
        self.avatar_preview.setPixmap(QPixmap())
    
    def update_avatar_preview(self) -> None:
        """Update the avatar preview."""
        if not self.avatar_pixmap:
            return
        
        # Scale the pixmap to fit the preview
        scaled_pixmap = self.avatar_pixmap.scaled(
            self.avatar_preview.width(),
            self.avatar_preview.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.avatar_preview.setPixmap(scaled_pixmap)
        self.avatar_preview.setText("")
    
    def save_avatar(self) -> Optional[str]:
        """Save the avatar to disk.
        
        Returns:
            Path to the saved avatar, or None if no avatar
        """
        if not self.avatar_pixmap:
            return self.avatar_path  # Return existing path if any
        
        # Get the user folder from settings
        user_folder = self.settings.value("user_folder", "")
        if not user_folder:
            QMessageBox.warning(
                self,
                "User Folder Not Set",
                "Please set the User Folder in Settings before saving an avatar."
            )
            return None
        
        # Get the story folder path
        from app.db_sqlite import get_story
        story_data = get_story(self.parent().db_conn, self.story_id)
        story_folder = story_data.get('folder_path', '')
        
        if not story_folder or not os.path.exists(story_folder):
            # Create a default path if the story folder doesn't exist
            story_folder = os.path.join(user_folder, "Stories", f"Story_{self.story_id}")
            os.makedirs(story_folder, exist_ok=True)
        
        # Create the avatars folder
        avatar_folder = os.path.join(story_folder, "avatars")
        os.makedirs(avatar_folder, exist_ok=True)
        
        # Generate a unique filename
        character_name = self.name_edit.text().strip() or "Unnamed"
        character_name = character_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
        avatar_filename = f"{character_name}_{int(QDateTime.currentDateTime().toSecsSinceEpoch())}.png"
        avatar_path = os.path.join(avatar_folder, avatar_filename)
        
        # Save the avatar
        self.avatar_pixmap.save(avatar_path, "PNG")
        
        return avatar_path
    
    def on_accept(self) -> None:
        """Handle dialog acceptance."""
        # Validate the form
        name = self.name_edit.text().strip()
        if not name:
            name = f"Unnamed {int(QDateTime.currentDateTime().toSecsSinceEpoch())}"
        
        # Save the avatar
        avatar_path = self.save_avatar()
        
        # Prepare the character data
        self.character_data = {
            'name': name,
            'aliases': self.aliases_edit.text().strip(),
            'is_main_character': self.mc_checkbox.isChecked(),
            'age_value': self.age_value_spin.value() if self.age_value_spin.value() > 0 else None,
            'age_category': self.age_category_combo.currentData(),
            'gender': self.gender_combo.currentData(),
            'avatar_path': avatar_path,
            'story_id': self.story_id
        }
        
        # Accept the dialog
        self.accept()
    
    def get_character_data(self) -> Dict[str, Any]:
        """Get the character data.
        
        Returns:
            Character data
        """
        return self.character_data 