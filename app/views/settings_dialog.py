#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Settings dialog for The Plot Thickens application.

This module defines the settings dialog for configuring application settings.
"""

import os
import json
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QPushButton, QLabel, QLineEdit, QFileDialog,
    QDialogButtonBox, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt, QSettings


class SettingsDialog(QDialog):
    """Dialog for configuring application settings."""
    
    def __init__(self, parent=None) -> None:
        """Initialize the settings dialog.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.settings = QSettings("ThePlotThickens", "ThePlotThickens")
        self.user_folder: str = self.settings.value("user_folder", "")
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self) -> None:
        """Set up the user interface."""
        # Set window properties
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create folder settings group
        folder_group = QGroupBox("Folder Settings")
        folder_layout = QFormLayout(folder_group)
        
        # Create user folder selection
        user_folder_layout = QHBoxLayout()
        self.user_folder_edit = QLineEdit()
        self.user_folder_edit.setReadOnly(True)
        user_folder_layout.addWidget(self.user_folder_edit)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.on_browse_folder)
        user_folder_layout.addWidget(self.browse_button)
        
        folder_layout.addRow("User Folder:", user_folder_layout)
        
        # Add explanation label
        explanation_label = QLabel(
            "The User Folder will contain all your stories data. "
            "Each story will have its own subfolder within the 'Stories' directory."
        )
        explanation_label.setWordWrap(True)
        folder_layout.addRow("", explanation_label)
        
        main_layout.addWidget(folder_group)
        
        # Add dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.on_accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
    
    def load_settings(self) -> None:
        """Load settings from QSettings."""
        self.user_folder_edit.setText(self.user_folder)
    
    def on_browse_folder(self) -> None:
        """Handle browse folder button click."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select User Folder", self.user_folder or os.path.expanduser("~")
        )
        
        if folder:
            self.user_folder_edit.setText(folder)
    
    def on_accept(self) -> None:
        """Handle dialog acceptance."""
        # Get the selected user folder
        user_folder = self.user_folder_edit.text()
        
        # Validate the user folder
        if not user_folder:
            QMessageBox.warning(self, "Invalid Folder", "Please select a valid user folder.")
            return
        
        # Create the folder structure if it doesn't exist
        try:
            self.create_folder_structure(user_folder)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create folder structure: {str(e)}")
            return
        
        # Save the settings
        self.settings.setValue("user_folder", user_folder)
        
        # Accept the dialog
        self.accept()
    
    def create_folder_structure(self, user_folder: str) -> None:
        """Create the folder structure for the user folder.
        
        Args:
            user_folder: Path to the user folder
        """
        # Create the user folder if it doesn't exist
        os.makedirs(user_folder, exist_ok=True)
        
        # Create the Stories subfolder
        stories_folder = os.path.join(user_folder, "Stories")
        os.makedirs(stories_folder, exist_ok=True)
        
        # Create the images subfolder within Stories
        images_folder = os.path.join(stories_folder, "images")
        os.makedirs(images_folder, exist_ok=True)
    
    @staticmethod
    def get_user_folder() -> str:
        """Get the user folder from settings.
        
        Returns:
            Path to the user folder, or empty string if not set
        """
        settings = QSettings("ThePlotThickens", "ThePlotThickens")
        return settings.value("user_folder", "") 