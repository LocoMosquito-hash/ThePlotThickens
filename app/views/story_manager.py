#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Story Manager widget for The Plot Thickens application.

This module defines the widget for managing stories.
"""

import os
import sys
import uuid
import random
import string
from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, QFormLayout,
    QGroupBox, QFileDialog, QMessageBox, QSplitter, QApplication
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QSettings
from PyQt6.QtGui import QFont, QPixmap, QImage, QClipboard

from app.db_sqlite import (
    StoryType, create_story, update_story, get_all_stories, get_story, update_story_folder_path
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
        self.artwork_pixmap: Optional[QPixmap] = None
        
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
        
        # Artwork section
        artwork_layout = QVBoxLayout()
        self.artwork_label = QLabel("No artwork set")
        self.artwork_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.artwork_label.setMinimumHeight(150)
        self.artwork_label.setStyleSheet("background-color: #444; border: 1px solid #666;")
        artwork_layout.addWidget(self.artwork_label)
        
        artwork_buttons_layout = QHBoxLayout()
        self.paste_artwork_button = QPushButton("Paste from Clipboard")
        self.paste_artwork_button.clicked.connect(self.on_paste_artwork)
        artwork_buttons_layout.addWidget(self.paste_artwork_button)
        
        self.clear_artwork_button = QPushButton("Clear")
        self.clear_artwork_button.clicked.connect(self.on_clear_artwork)
        self.clear_artwork_button.setEnabled(False)
        artwork_buttons_layout.addWidget(self.clear_artwork_button)
        
        artwork_layout.addLayout(artwork_buttons_layout)
        details_layout.addRow("Artwork:", artwork_layout)
        
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
        
        # Set the universe
        self.universe_edit.setText(story_data["universe"] or "")
        
        # Set series information
        is_part_of_series = story_data["is_part_of_series"] in (True, 1)
        self.series_check.setCurrentIndex(1 if is_part_of_series else 0)
        
        if is_part_of_series:
            self.series_name_edit.setEnabled(True)
            self.series_name_edit.setText(story_data["series_name"] or "")
            
            self.series_order_edit.setEnabled(True)
            if story_data["series_order"] is not None:
                self.series_order_edit.setText(str(story_data["series_order"]))
            else:
                self.series_order_edit.clear()
        else:
            self.series_name_edit.setEnabled(False)
            self.series_name_edit.clear()
            
            self.series_order_edit.setEnabled(False)
            self.series_order_edit.clear()
        
        # Set author and year
        self.author_edit.setText(story_data["author"] or "")
        
        if story_data["year"] is not None:
            self.year_edit.setText(str(story_data["year"]))
        else:
            self.year_edit.clear()
        
        # Load artwork if it exists
        self.load_artwork(story_data["folder_path"])
        
        # Enable the load button
        self.load_story_button.setEnabled(True)
        
        # Emit the story selected signal
        self.story_selected.emit(story_id, story_data)
    
    def generate_random_id(self, length: int = 6) -> str:
        """Generate a random alphanumeric ID.
        
        Args:
            length: Length of the ID
            
        Returns:
            Random alphanumeric ID
        """
        # Use uppercase letters and digits for better readability
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    def clear_form(self) -> None:
        """Clear the story details form to create a new story."""
        self.title_edit.clear()
        self.description_edit.clear()
        self.type_combo.setCurrentIndex(0)
        self.universe_edit.clear()
        self.series_check.setCurrentIndex(0)
        self.series_name_edit.clear()
        self.series_name_edit.setEnabled(False)
        self.series_order_edit.clear()
        self.series_order_edit.setEnabled(False)
        self.author_edit.clear()
        self.year_edit.clear()
        
        # Clear the artwork
        self.clear_artwork()
        
        # Deselect any story in the list
        self.story_list.clearSelection()
        
        # Disable the load button
        self.load_story_button.setEnabled(False)
        
        # Set focus to title field
        self.title_edit.setFocus()
    
    def on_new_story(self) -> None:
        """Handle new story button click - clear form to create a new story."""
        # Clear the form to start fresh
        self.clear_form()
        
        # Show a message to the user
        QMessageBox.information(
            self,
            "New Story",
            "Enter details for your new story and click 'Save Story' when ready."
        )
    
    def on_paste_artwork(self) -> None:
        """Handle paste artwork button click - paste image from clipboard."""
        clipboard = QApplication.clipboard()
        pixmap = clipboard.pixmap()
        
        if pixmap.isNull():
            QMessageBox.warning(
                self,
                "No Image in Clipboard",
                "There is no image in the clipboard. Copy an image first."
            )
            return
        
        # Store the pixmap and display it
        self.artwork_pixmap = pixmap
        self.display_artwork()
        self.clear_artwork_button.setEnabled(True)
    
    def on_clear_artwork(self) -> None:
        """Handle clear artwork button click."""
        self.clear_artwork()
    
    def clear_artwork(self) -> None:
        """Clear the artwork display and data."""
        self.artwork_pixmap = None
        self.artwork_label.setText("No artwork set")
        self.artwork_label.setPixmap(QPixmap())
        self.clear_artwork_button.setEnabled(False)
    
    def display_artwork(self) -> None:
        """Display the current artwork pixmap in the label."""
        if self.artwork_pixmap:
            # Calculate the size to fit the label while maintaining aspect ratio
            label_size = self.artwork_label.size()
            scaled_pixmap = self.artwork_pixmap.scaled(
                label_size, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self.artwork_label.setPixmap(scaled_pixmap)
            self.artwork_label.setText("")
    
    def load_artwork(self, folder_path: str) -> None:
        """Load artwork from the story folder if it exists.
        
        Args:
            folder_path: Path to the story folder
        """
        if not folder_path:
            self.clear_artwork()
            return
        
        artwork_path = os.path.join(folder_path, "artwork.png")
        if os.path.exists(artwork_path):
            pixmap = QPixmap(artwork_path)
            if not pixmap.isNull():
                self.artwork_pixmap = pixmap
                self.display_artwork()
                self.clear_artwork_button.setEnabled(True)
                return
        
        # No artwork found
        self.clear_artwork()
    
    def save_artwork(self, folder_path: str) -> None:
        """Save the artwork to the story folder.
        
        Args:
            folder_path: Path to the story folder
        """
        if not self.artwork_pixmap or not folder_path:
            return
        
        # Ensure the folder exists
        os.makedirs(folder_path, exist_ok=True)
        
        # Save the artwork
        artwork_path = os.path.join(folder_path, "artwork.png")
        self.artwork_pixmap.save(artwork_path, "PNG")
    
    def on_save_story(self) -> None:
        """Handle save story button click."""
        # Get the form data
        title = self.title_edit.text().strip()
        description = self.description_edit.toPlainText().strip()
        type_name = self.type_combo.currentData()
        universe = self.universe_edit.text().strip() or None
        
        # Get series information
        is_part_of_series = self.series_check.currentData() in (True, 1)
        series_name = None
        series_order = None
        
        if is_part_of_series:
            series_name = self.series_name_edit.text().strip() or None
            series_order_text = self.series_order_edit.text().strip()
            if series_order_text:
                try:
                    series_order = int(series_order_text)
                except ValueError:
                    QMessageBox.warning(
                        self,
                        "Invalid Series Order",
                        "Series order must be a number. Please enter a valid number."
                    )
                    self.series_order_edit.setFocus()
                    return
        
        # Get author and year
        author = self.author_edit.text().strip() or None
        year = None
        year_text = self.year_edit.text().strip()
        if year_text:
            try:
                year = int(year_text)
            except ValueError:
                QMessageBox.warning(
                    self,
                    "Invalid Year",
                    "Year must be a number. Please enter a valid year."
                )
                self.year_edit.setFocus()
                return
        
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
                try:
                    # Update the story in the database
                    updated_story = update_story(
                        self.db_conn,
                        story_id=story_id,
                        title=title,
                        description=description,
                        type_name=type_name,
                        universe=universe,
                        is_part_of_series=is_part_of_series,
                        series_name=series_name,
                        series_order=series_order,
                        author=author,
                        year=year
                    )
                    
                    # Save artwork if available
                    if self.artwork_pixmap:
                        self.save_artwork(story_data["folder_path"])
                    
                    # Update local copy of the story data
                    for i, story in enumerate(self.stories):
                        if story["id"] == story_id:
                            self.stories[i] = updated_story
                            break
                    
                    # Update the item in the list widget if title changed
                    if story_data["title"] != title:
                        item = selected_items[0]
                        item.setText(title)
                    
                    # Show a success message
                    QMessageBox.information(
                        self,
                        "Story Updated",
                        f"Story '{title}' updated successfully."
                    )
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Failed to update story: {str(e)}"
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
                folder_path="",  # Temporary, will be updated after we get the ID
                universe=universe,
                is_part_of_series=is_part_of_series,
                series_name=series_name,
                series_order=series_order,
                author=author,
                year=year
            )
            
            # Create the story folder with a random ID to avoid conflicts with saga titles
            random_id = self.generate_random_id()
            story_folder_name = f"{title.replace(' ', '_')}_{random_id}"
            story_folder = os.path.join(stories_folder, story_folder_name)
            
            # Update the story with the folder path
            story_data = update_story_folder_path(self.db_conn, story_id, story_folder)
            
            # Save artwork if available
            if self.artwork_pixmap:
                self.save_artwork(story_folder)
            
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
    
    def on_series_changed(self, index: int) -> None:
        """Handle series selection change.
        
        Args:
            index: Index of the selected item
        """
        is_part_of_series = self.series_check.currentData() in (True, 1)
        self.series_name_edit.setEnabled(is_part_of_series)
        self.series_order_edit.setEnabled(is_part_of_series)

    def add_story_to_list(self, story_data: Dict[str, Any]) -> None:
        """Add a story to the list widget.
        
        Args:
            story_data: Story data dictionary
        """
        item = QListWidgetItem(story_data["title"])
        item.setData(Qt.ItemDataRole.UserRole, story_data["id"])
        self.story_list.addItem(item)
        self.story_list.setCurrentItem(item) 