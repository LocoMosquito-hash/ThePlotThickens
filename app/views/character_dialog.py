#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Character Dialog for The Plot Thickens application.

This module defines the dialog for editing character data.
"""

import os
import sys
from typing import Optional, Dict, Any, List, Tuple, Set

from PyQt6.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QSpinBox, QCheckBox, QPushButton,
    QFileDialog, QMessageBox, QApplication, QGroupBox
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QBuffer, QByteArray
from PyQt6.QtGui import QPixmap, QImage, QCloseEvent

from app.db_sqlite import get_character, update_character


class CharacterDialog(QDialog):
    """Dialog for editing character data."""
    
    # Signal emitted when character data is updated
    character_updated = pyqtSignal(int, dict)
    
    def __init__(self, db_conn, character_id: int, parent=None) -> None:
        """Initialize the dialog.
        
        Args:
            db_conn: Database connection
            character_id: ID of the character to edit
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.db_conn = db_conn
        self.character_id = character_id
        self.character_data = get_character(db_conn, character_id)
        self.original_data = self.character_data.copy()
        self.has_unsaved_changes = False
        
        # Store the original avatar path
        self.original_avatar_path = self.character_data.get('avatar_path')
        self.new_avatar_path = None
        self.new_avatar_pixmap = None
        
        self.init_ui()
        self.load_character_data()
        
        # Initially disable the save button
        self.save_button.setEnabled(False)
    
    def init_ui(self) -> None:
        """Initialize the user interface."""
        # Set window properties
        self.setWindowTitle(f"Edit Character: {self.character_data['name']}")
        self.setMinimumSize(500, 600)
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create summary tab
        self.summary_tab = QWidget()
        self.tab_widget.addTab(self.summary_tab, "Summary")
        
        # Create relationships tab (placeholder)
        self.relationships_tab = QWidget()
        relationships_layout = QVBoxLayout(self.relationships_tab)
        relationships_layout.addWidget(QLabel("Relationships will be implemented later."))
        self.tab_widget.addTab(self.relationships_tab, "Relationships")
        
        # Create gallery tab (placeholder)
        self.gallery_tab = QWidget()
        gallery_layout = QVBoxLayout(self.gallery_tab)
        gallery_layout.addWidget(QLabel("Gallery will be implemented later."))
        self.tab_widget.addTab(self.gallery_tab, "Gallery")
        
        # Create summary tab layout
        self.create_summary_tab()
        
        # Create buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_character)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
    
    def create_summary_tab(self) -> None:
        """Create the summary tab."""
        layout = QVBoxLayout(self.summary_tab)
        
        # Create form layout for basic info
        form_layout = QFormLayout()
        
        # Name field
        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self.on_field_changed)
        form_layout.addRow("Name:", self.name_edit)
        
        # Avatar section
        avatar_group = QGroupBox("Avatar")
        avatar_layout = QVBoxLayout(avatar_group)
        
        # Avatar preview
        self.avatar_preview = QLabel()
        self.avatar_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_preview.setMinimumSize(180, 180)
        self.avatar_preview.setMaximumSize(300, 300)
        self.avatar_preview.setScaledContents(True)
        avatar_layout.addWidget(self.avatar_preview)
        
        # Avatar buttons
        avatar_buttons = QHBoxLayout()
        
        self.edit_avatar_button = QPushButton("Browse...")
        self.edit_avatar_button.setToolTip("Select an image file for the avatar")
        self.edit_avatar_button.clicked.connect(self.edit_avatar)
        
        self.paste_avatar_button = QPushButton("Paste")
        self.paste_avatar_button.setToolTip("Paste an image from the clipboard")
        self.paste_avatar_button.clicked.connect(self.paste_avatar)
        
        self.delete_avatar_button = QPushButton("Delete")
        self.delete_avatar_button.setToolTip("Remove the avatar")
        self.delete_avatar_button.clicked.connect(self.delete_avatar)
        
        avatar_buttons.addWidget(self.edit_avatar_button)
        avatar_buttons.addWidget(self.paste_avatar_button)
        avatar_buttons.addWidget(self.delete_avatar_button)
        avatar_layout.addLayout(avatar_buttons)
        
        # Add avatar group to layout
        layout.addLayout(form_layout)
        layout.addWidget(avatar_group)
        
        # Continue with form layout
        form_layout2 = QFormLayout()
        
        # Aliases field
        self.aliases_edit = QLineEdit()
        self.aliases_edit.setPlaceholderText("Comma-separated list of aliases")
        self.aliases_edit.textChanged.connect(self.on_field_changed)
        form_layout2.addRow("Aliases:", self.aliases_edit)
        
        # Main character checkbox
        self.mc_checkbox = QCheckBox("Main Character")
        self.mc_checkbox.stateChanged.connect(self.on_field_changed)
        form_layout2.addRow("", self.mc_checkbox)
        
        # Age section
        age_layout = QHBoxLayout()
        
        # Age value
        self.age_value_spin = QSpinBox()
        self.age_value_spin.setRange(0, 999)
        self.age_value_spin.setSpecialValueText("Not specified")
        self.age_value_spin.valueChanged.connect(self.on_field_changed)
        
        # Age category
        self.age_category_combo = QComboBox()
        self.age_category_combo.addItem("Not specified", None)
        self.age_category_combo.addItem("Minor", "MINOR")
        self.age_category_combo.addItem("Teen", "TEEN")
        self.age_category_combo.addItem("Young", "YOUNG")
        self.age_category_combo.addItem("Adult", "ADULT")
        self.age_category_combo.addItem("Middle-aged", "MIDDLE_AGED")
        self.age_category_combo.addItem("Mature", "MATURE")
        self.age_category_combo.addItem("Old", "OLD")
        self.age_category_combo.currentIndexChanged.connect(self.on_field_changed)
        
        age_layout.addWidget(QLabel("Value:"))
        age_layout.addWidget(self.age_value_spin)
        age_layout.addWidget(QLabel("Category:"))
        age_layout.addWidget(self.age_category_combo)
        
        form_layout2.addRow("Age:", age_layout)
        
        # Gender field
        self.gender_combo = QComboBox()
        self.gender_combo.addItem("Not specified", "NOT_SPECIFIED")
        self.gender_combo.addItem("Male", "MALE")
        self.gender_combo.addItem("Female", "FEMALE")
        self.gender_combo.addItem("Futa", "FUTA")
        self.gender_combo.currentIndexChanged.connect(self.on_field_changed)
        form_layout2.addRow("Gender:", self.gender_combo)
        
        layout.addLayout(form_layout2)
        layout.addStretch()
    
    def load_character_data(self) -> None:
        """Load character data into the form."""
        # Set name
        self.name_edit.setText(self.character_data['name'])
        
        # Set avatar
        if self.character_data['avatar_path'] and os.path.exists(self.character_data['avatar_path']):
            pixmap = QPixmap(self.character_data['avatar_path'])
            self.avatar_preview.setPixmap(pixmap)
        else:
            self.avatar_preview.setText("No Avatar")
        
        # Set aliases
        if self.character_data['aliases']:
            self.aliases_edit.setText(self.character_data['aliases'])
        
        # Set main character checkbox
        self.mc_checkbox.setChecked(bool(self.character_data['is_main_character']))
        
        # Set age value
        if self.character_data['age_value'] is not None:
            self.age_value_spin.setValue(self.character_data['age_value'])
        
        # Set age category
        if self.character_data['age_category']:
            index = self.age_category_combo.findData(self.character_data['age_category'])
            if index >= 0:
                self.age_category_combo.setCurrentIndex(index)
        
        # Set gender
        index = self.gender_combo.findData(self.character_data['gender'])
        if index >= 0:
            self.gender_combo.setCurrentIndex(index)
    
    def on_field_changed(self) -> None:
        """Handle field changes."""
        self.has_unsaved_changes = True
        self.save_button.setEnabled(True)
    
    def edit_avatar(self) -> None:
        """Open a file dialog to select a new avatar."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Avatar Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.avatar_preview.setPixmap(pixmap)
                self.new_avatar_path = file_path
                self.new_avatar_pixmap = None
                self.on_field_changed()
    
    def paste_avatar(self) -> None:
        """Paste an image from the clipboard as the avatar."""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasImage():
            image = QImage(clipboard.image())
            if not image.isNull():
                pixmap = QPixmap.fromImage(image)
                self.avatar_preview.setPixmap(pixmap)
                self.new_avatar_pixmap = pixmap
                self.new_avatar_path = None
                self.on_field_changed()
        else:
            QMessageBox.warning(self, "Paste Failed", "No image found in clipboard.")
    
    def delete_avatar(self) -> None:
        """Delete the avatar."""
        self.avatar_preview.clear()
        self.avatar_preview.setText("No Avatar")
        self.new_avatar_path = ""  # Empty string to indicate deletion
        self.new_avatar_pixmap = None
        self.on_field_changed()
    
    def save_avatar(self) -> str:
        """Save the avatar and return the path.
        
        Returns:
            Path to the saved avatar, or empty string if no avatar
        """
        # If no changes to avatar, return the original path
        if self.new_avatar_path is None and self.new_avatar_pixmap is None:
            return self.original_avatar_path
        
        # If avatar was deleted, return empty string
        if self.new_avatar_path == "":
            return ""
        
        # If new avatar was selected from file, copy it to the story folder
        if self.new_avatar_path:
            # Get the story folder path
            story_id = self.character_data['story_id']
            story_folder = os.path.join("stories", f"story_{story_id}")
            
            # Create the images folder if it doesn't exist
            images_folder = os.path.join(story_folder, "images")
            os.makedirs(images_folder, exist_ok=True)
            
            # Generate a filename for the avatar
            filename = f"avatar_{self.character_id}.png"
            avatar_path = os.path.join(images_folder, filename)
            
            # Copy the image
            pixmap = QPixmap(self.new_avatar_path)
            pixmap.save(avatar_path, "PNG")
            
            return avatar_path
        
        # If new avatar was pasted from clipboard, save it
        if self.new_avatar_pixmap:
            # Get the story folder path
            story_id = self.character_data['story_id']
            story_folder = os.path.join("stories", f"story_{story_id}")
            
            # Create the images folder if it doesn't exist
            images_folder = os.path.join(story_folder, "images")
            os.makedirs(images_folder, exist_ok=True)
            
            # Generate a filename for the avatar
            filename = f"avatar_{self.character_id}.png"
            avatar_path = os.path.join(images_folder, filename)
            
            # Save the image
            self.new_avatar_pixmap.save(avatar_path, "PNG")
            
            return avatar_path
        
        # If we get here, something went wrong
        return self.original_avatar_path
    
    def save_character(self) -> None:
        """Save the character data."""
        # Validate name
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Name is required.")
            return
        
        # Get aliases
        aliases = self.aliases_edit.text().strip()
        
        # Get main character flag
        is_main_character = self.mc_checkbox.isChecked()
        
        # Get age value
        age_value = self.age_value_spin.value()
        if age_value == 0:  # Special value
            age_value = None
        
        # Get age category
        age_category = self.age_category_combo.currentData()
        
        # Get gender
        gender = self.gender_combo.currentData()
        
        # Save avatar
        avatar_path = self.save_avatar()
        
        # Update character in database
        updated_data = update_character(
            self.db_conn,
            self.character_id,
            name,
            aliases,
            is_main_character,
            age_value,
            age_category,
            gender,
            avatar_path
        )
        
        # Emit signal
        self.character_updated.emit(self.character_id, updated_data)
        
        # Reset unsaved changes flag
        self.has_unsaved_changes = False
        
        # Close dialog
        self.accept()
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle close event.
        
        Args:
            event: Close event
        """
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            
            if reply == QMessageBox.StandardButton.Save:
                self.save_character()
                event.accept()
            elif reply == QMessageBox.StandardButton.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept() 