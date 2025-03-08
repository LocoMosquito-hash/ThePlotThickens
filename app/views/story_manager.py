#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Story Manager widget for The Plot Thickens application.

This module defines the widget for managing stories.
"""

import os
import sys
from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, QFormLayout,
    QGroupBox, QFileDialog, QMessageBox, QSplitter
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QSettings

from app.db_sqlite import (
    StoryType, create_story, get_all_stories, get_story, update_story_folder_path
)
from app.views.settings_dialog import SettingsDialog


class StoryManagerWidget(QWidget):
    """Widget for managing stories."""
    
    # Signal emitted when a story is selected
    story_selected = pyqtSignal(int, dict)
    
    def __init__(self, db_conn) -> None:
        """Initialize the story manager widget.
        
        Args:
            db_conn: Database connection
        """
        super().__init__()
        
        self.db_conn = db_conn
        self.stories: List[Dict[str, Any]] = []
        self.settings = QSettings("ThePlotThickens", "ThePlotThickens")
        
        self.init_ui()
        self.load_stories()
    
    def init_ui(self) -> None:
        """Set up the user interface."""
        # Create main layout
        main_layout = QHBoxLayout(self)
        
        # Create splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Create left panel (story list)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Create story list
        self.story_list = QListWidget()
        self.story_list.setMinimumWidth(300)
        self.story_list.currentItemChanged.connect(self.on_story_selected)
        left_layout.addWidget(QLabel("Stories:"))
        left_layout.addWidget(self.story_list)
        
        # Create buttons
        button_layout = QHBoxLayout()
        
        self.new_story_button = QPushButton("New Story")
        self.new_story_button.clicked.connect(self.on_new_story)
        button_layout.addWidget(self.new_story_button)
        
        self.load_story_button = QPushButton("Load Story")
        self.load_story_button.clicked.connect(self.on_load_story)
        self.load_story_button.setEnabled(False)
        button_layout.addWidget(self.load_story_button)
        
        left_layout.addLayout(button_layout)
        
        # Create right panel (story details)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Create story details form
        self.details_group = QGroupBox("Story Details")
        details_layout = QFormLayout(self.details_group)
        
        self.title_edit = QLineEdit()
        details_layout.addRow("Title:", self.title_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        details_layout.addRow("Description:", self.description_edit)
        
        self.type_combo = QComboBox()
        for story_type in StoryType:
            self.type_combo.addItem(str(story_type), story_type.name)
        details_layout.addRow("Type:", self.type_combo)
        
        self.folder_edit = QLineEdit()
        self.folder_edit.setReadOnly(True)
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self.folder_edit)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.on_browse_folder)
        folder_layout.addWidget(self.browse_button)
        
        details_layout.addRow("Folder:", folder_layout)
        
        self.universe_edit = QLineEdit()
        details_layout.addRow("Universe:", self.universe_edit)
        
        self.series_check = QComboBox()
        self.series_check.addItem("No", False)
        self.series_check.addItem("Yes", True)
        self.series_check.currentIndexChanged.connect(self.on_series_changed)
        details_layout.addRow("Part of Series:", self.series_check)
        
        self.series_name_edit = QLineEdit()
        self.series_name_edit.setEnabled(False)
        details_layout.addRow("Series Name:", self.series_name_edit)
        
        self.series_order_edit = QLineEdit()
        self.series_order_edit.setEnabled(False)
        details_layout.addRow("Series Order:", self.series_order_edit)
        
        self.author_edit = QLineEdit()
        details_layout.addRow("Author:", self.author_edit)
        
        self.year_edit = QLineEdit()
        details_layout.addRow("Year:", self.year_edit)
        
        right_layout.addWidget(self.details_group)
        
        # Create save button
        self.save_button = QPushButton("Save Story")
        self.save_button.clicked.connect(self.on_save_story)
        right_layout.addWidget(self.save_button)
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # Set initial splitter sizes
        splitter.setSizes([300, 700])
    
    def load_stories(self) -> None:
        """Load stories from the database."""
        self.stories = get_all_stories(self.db_conn)
        
        self.story_list.clear()
        for story in self.stories:
            item = QListWidgetItem(story["title"])
            item.setData(Qt.ItemDataRole.UserRole, story["id"])
            self.story_list.addItem(item)
    
    def on_story_selected(self, current: QListWidgetItem, previous: QListWidgetItem) -> None:
        """Handle story selection.
        
        Args:
            current: Currently selected item
            previous: Previously selected item
        """
        if not current:
            return
        
        # Get the story ID
        story_id = current.data(Qt.ItemDataRole.UserRole)
        
        # Get the story data
        story_data = None
        for story in self.stories:
            if story["id"] == story_id:
                story_data = story
                break
        
        if not story_data:
            return
        
        # Update the form
        self.title_edit.setText(story_data["title"])
        self.description_edit.setText(story_data["description"] or "")
        
        # Set the story type
        type_index = self.type_combo.findData(story_data["type_name"])
        if type_index >= 0:
            self.type_combo.setCurrentIndex(type_index)
        
        # Set the folder path
        self.folder_edit.setText(story_data["folder_path"])
        
        # Enable the load button
        self.load_story_button.setEnabled(True)
        
        # Emit the story selected signal
        self.story_selected.emit(story_id, story_data)
    
    def on_new_story(self) -> None:
        """Handle new story button click."""
        # Clear the form
        self.title_edit.clear()
        self.description_edit.clear()
        self.type_combo.setCurrentIndex(0)
        
        # Get the user folder from settings
        user_folder = self.settings.value("user_folder", "")
        
        if not user_folder:
            # If user folder is not set, show a message and open settings dialog
            QMessageBox.warning(
                self,
                "User Folder Not Set",
                "Please set the User Folder in Settings before creating a new story."
            )
            settings_dialog = SettingsDialog(self.window())
            if settings_dialog.exec():
                user_folder = self.settings.value("user_folder", "")
            else:
                return
        
        # Set the default folder path (will be updated when saving)
        self.folder_edit.clear()
        
        # Deselect any selected story
        self.story_list.clearSelection()
        self.load_story_button.setEnabled(False)
    
    def on_save_story(self) -> None:
        """Handle save story button click."""
        # Get the form data
        title = self.title_edit.text().strip()
        description = self.description_edit.toPlainText().strip()
        type_name = self.type_combo.currentData()
        
        # Validate the form data
        if not title:
            QMessageBox.warning(self, "Invalid Title", "Please enter a valid title.")
            return
        
        # Get the user folder from settings
        user_folder = self.settings.value("user_folder", "")
        
        if not user_folder:
            # If user folder is not set, show a message and open settings dialog
            QMessageBox.warning(
                self,
                "User Folder Not Set",
                "Please set the User Folder in Settings before saving a story."
            )
            settings_dialog = SettingsDialog(self.window())
            if settings_dialog.exec():
                user_folder = self.settings.value("user_folder", "")
            else:
                return
        
        # Check if we're editing an existing story
        selected_items = self.story_list.selectedItems()
        if selected_items:
            # Get the story ID
            story_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
            
            # Get the story data
            story_data = None
            for story in self.stories:
                if story["id"] == story_id:
                    story_data = story
                    break
            
            if story_data:
                # Update the story data
                story_data["title"] = title
                story_data["description"] = description
                story_data["type_name"] = type_name
                
                # TODO: Update the story in the database
                QMessageBox.information(
                    self,
                    "Not Implemented",
                    "Updating existing stories is not yet implemented."
                )
                return
        
        # We're creating a new story
        
        # Create the story folder
        stories_folder = os.path.join(user_folder, "Stories")
        
        try:
            # Create a new story in the database with an empty folder path initially
            story_id, story_data = create_story(
                self.db_conn,
                title=title,
                description=description,
                type_name=type_name,
                folder_path=""  # Temporary, will be updated after we get the ID
            )
            
            # Create the story folder with ID in the name to avoid conflicts
            story_folder_name = f"{title.replace(' ', '_')}_{story_id}"
            story_folder = os.path.join(stories_folder, story_folder_name)
            
            # Update the story with the folder path
            story_data = update_story_folder_path(self.db_conn, story_id, story_folder)
            
            # Add the story to the list
            self.stories.append(story_data)
            
            # Add the story to the list widget
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, story_id)
            self.story_list.addItem(item)
            
            # Select the new story
            self.story_list.setCurrentItem(item)
            
            # Show a success message
            QMessageBox.information(
                self,
                "Story Created",
                f"Story '{title}' created successfully."
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to create story: {str(e)}"
            )
    
    def on_load_story(self) -> None:
        """Handle load story button click."""
        # Get the selected story
        selected_items = self.story_list.selectedItems()
        if not selected_items:
            return
        
        # Get the story ID
        story_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        
        # Get the story data
        story_data = None
        for story in self.stories:
            if story["id"] == story_id:
                story_data = story
                break
        
        if not story_data:
            return
        
        # Emit the story selected signal
        self.story_selected.emit(story_id, story_data)
    
    def on_browse_folder(self) -> None:
        """Handle browse folder button click."""
        # Get the user folder from settings
        user_folder = self.settings.value("user_folder", "")
        
        if not user_folder:
            QMessageBox.warning(
                self,
                "User Folder Not Set",
                "Please set the User Folder in Settings before selecting a story folder."
            )
            return
        
        # Open a folder dialog
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Story Folder",
            os.path.join(user_folder, "Stories")
        )
        
        if folder:
            self.folder_edit.setText(folder)
    
    def on_series_changed(self, index: int) -> None:
        """Handle series selection change.
        
        Args:
            index: Index of the selected item
        """
        # TODO: Implement series selection
        pass 