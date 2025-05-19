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
import re
import json
import shutil
from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, QFormLayout,
    QGroupBox, QFileDialog, QMessageBox, QSplitter, QApplication, QStyledItemDelegate, QStyle,
    QMenu, QProgressDialog
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QSettings, QRect, QPoint
from PyQt6.QtGui import QFont, QPixmap, QImage, QClipboard, QPainter, QColor, QBrush, QPen, QAction

from app.db_sqlite import (
    StoryType, create_story, update_story, get_all_stories, get_story, update_story_folder_path,
    get_story_characters, get_story_relationships, get_story_board_views, get_story_events, get_event_characters,
    create_character, create_relationship, create_story_board_view, add_character_to_event, update_event, update_character,
    create_event, get_story_images, create_image, get_image_character_tags, add_character_tag_to_image, add_image_to_scene,
    get_story_decision_points, get_decision_options, create_decision_point, add_decision_option
)
from app.views.settings_dialog import SettingsDialog
from app.utils.icons import icon_manager


class StoryItemDelegate(QStyledItemDelegate):
    """Custom delegate to display story items with artwork thumbnails."""
    
    def __init__(self) -> None:
        """Initialize the delegate."""
        super().__init__()
        self.title_height = 20  # Height for story title
        self.thumbnail_height = 60  # Height for artwork thumbnail
        self.margin = 5  # Margin between elements
    
    def sizeHint(self, option, index) -> QSize:
        """Return the size hint for the item.
        
        Args:
            option: Style options
            index: Item index
            
        Returns:
            Suggested size for the item
        """
        # Get the artwork data
        artwork_path = index.data(Qt.ItemDataRole.UserRole + 1)
        
        # Base height includes title and margins
        height = self.title_height + self.margin * 2
        
        # Add artwork height if available
        if artwork_path and os.path.exists(artwork_path):
            height += self.thumbnail_height + self.margin
        
        return QSize(option.rect.width(), height)
    
    def paint(self, painter: QPainter, option, index) -> None:
        """Paint the item.
        
        Args:
            painter: Painter to use
            option: Style options
            index: Item index
        """
        painter.save()
        
        # Draw background
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
            text_color = option.palette.highlightedText().color()
        else:
            painter.fillRect(option.rect, option.palette.base())
            text_color = option.palette.text().color()
        
        # Calculate title rect
        title_rect = QRect(
            option.rect.left() + self.margin,
            option.rect.top() + self.margin,
            option.rect.width() - 2 * self.margin,
            self.title_height
        )
        
        # Draw title
        title = index.data(Qt.ItemDataRole.DisplayRole)
        painter.setPen(QPen(text_color))
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, title)
        
        # Get the artwork data
        artwork_path = index.data(Qt.ItemDataRole.UserRole + 1)
        
        # Draw artwork if available
        if artwork_path and os.path.exists(artwork_path):
            # Load the pixmap
            pixmap = QPixmap(artwork_path)
            if not pixmap.isNull():
                # Calculate artwork rect
                artwork_rect = QRect(
                    option.rect.left() + self.margin,
                    title_rect.bottom() + self.margin,
                    option.rect.width() - 2 * self.margin,
                    self.thumbnail_height
                )
                
                # Scale and draw the artwork
                scaled_pixmap = pixmap.scaled(
                    artwork_rect.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                # Center the pixmap in the artwork rect
                pixmap_x = artwork_rect.left() + (artwork_rect.width() - scaled_pixmap.width()) // 2
                pixmap_y = artwork_rect.top()
                painter.drawPixmap(pixmap_x, pixmap_y, scaled_pixmap)
        
        painter.restore()


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
        # Set up click behavior
        self.story_list.currentItemChanged.connect(self.on_story_selected)
        self.story_list.itemDoubleClicked.connect(self.on_story_double_clicked)
        # Set up right-click context menu
        self.story_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.story_list.customContextMenuRequested.connect(self.show_context_menu)
        # Set the custom delegate for story items
        self.story_list.setItemDelegate(StoryItemDelegate())
        self.story_list.setSpacing(2)  # Add some space between items
        
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
    
    def get_artwork_path(self, folder_path: str) -> Optional[str]:
        """Get the path to the story artwork if it exists.
        
        Args:
            folder_path: Path to the story folder
            
        Returns:
            Path to the artwork file or None if not found
        """
        if not folder_path:
            return None
        
        artwork_path = os.path.join(folder_path, "artwork.png")
        if os.path.exists(artwork_path):
            return artwork_path
        
        return None
    
    def load_stories(self) -> None:
        """Load stories from the database."""
        self.stories = get_all_stories(self.db_conn)
        
        self.story_list.clear()
        for story in self.stories:
            item = QListWidgetItem(story["title"])
            item.setData(Qt.ItemDataRole.UserRole, story["id"])
            
            # Add artwork path if available
            artwork_path = self.get_artwork_path(story["folder_path"])
            item.setData(Qt.ItemDataRole.UserRole + 1, artwork_path)
            
            self.story_list.addItem(item)
    
    def on_story_selected(self, current: QListWidgetItem, previous: QListWidgetItem) -> None:
        """Handle story selection - updates the Story Details pane only.
        
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
        
        # No longer emit the story_selected signal here - only on double-click or explicit load
    
    def on_story_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle story double-click - opens the story.
        
        Args:
            item: The clicked item
        """
        if not item:
            return
        
        # Get the story ID
        story_id = item.data(Qt.ItemDataRole.UserRole)
        
        # Get the story data
        story_data = None
        for story in self.stories:
            if story["id"] == story_id:
                story_data = story
                break
        
        if not story_data:
            return
        
        # Emit the story selected signal to open the story
        self.story_selected.emit(story_id, story_data)
    
    def show_context_menu(self, position: QPoint) -> None:
        """Show context menu for story list items.
        
        Args:
            position: Position where the menu should be displayed
        """
        item = self.story_list.itemAt(position)
        if not item:
            return
        
        # Get the story ID and data
        story_id = item.data(Qt.ItemDataRole.UserRole)
        story_data = None
        for story in self.stories:
            if story["id"] == story_id:
                story_data = story
                break
        
        if not story_data:
            return
        
        # Create context menu
        menu = QMenu(self)
        
        # Add actions with icons
        load_action = QAction(icon_manager.get_icon("arrow-right"), "Load", self)
        load_action.triggered.connect(lambda: self.on_load_story_from_menu(story_id, story_data))
        menu.addAction(load_action)
        
        duplicate_action = QAction(icon_manager.get_icon("copy"), "Duplicate", self)
        duplicate_action.triggered.connect(lambda: self.on_duplicate_story(story_id))
        menu.addAction(duplicate_action)
        
        menu.addSeparator()
        
        delete_action = QAction(icon_manager.get_icon("trash"), "Delete", self)
        delete_action.triggered.connect(lambda: self.on_delete_story(story_id))
        menu.addAction(delete_action)
        
        # Show the menu
        menu.exec(self.story_list.mapToGlobal(position))
    
    def on_load_story_from_menu(self, story_id: int, story_data: Dict[str, Any]) -> None:
        """Handle loading a story from the context menu.
        
        Args:
            story_id: ID of the story to load
            story_data: Data of the story to load
        """
        # Emit the story selected signal
        self.story_selected.emit(story_id, story_data)
    
    def on_duplicate_story(self, story_id: int) -> None:
        """Handle duplicating a story.
        
        Args:
            story_id: ID of the story to duplicate
        """
        try:
            # Get the original story data
            original_story_data = None
            for story in self.stories:
                if story["id"] == story_id:
                    original_story_data = story
                    break
            
            if not original_story_data:
                QMessageBox.critical(
                    self,
                    "Error",
                    "Failed to find the selected story."
                )
                return
                
            # Debug info
            print("DEBUG: Original story data:")
            for key, value in original_story_data.items():
                print(f"  {key}: {value}")
                
            # Ensure description field is sanitized
            if "description" in original_story_data and original_story_data["description"] is None:
                original_story_data["description"] = ""
                print("DEBUG: Sanitized NULL description field to empty string")
            
            # Get user folder from settings
            user_folder = self.settings.value("user_folder", "")
            if not user_folder:
                QMessageBox.warning(
                    self,
                    "User Folder Not Set",
                    "Please set the User Folder in Settings before duplicating a story."
                )
                settings_dialog = SettingsDialog(self.window())
                if settings_dialog.exec():
                    user_folder = self.settings.value("user_folder", "")
                else:
                    return
            
            # Create the stories folder if it doesn't exist
            stories_folder = os.path.join(user_folder, "Stories")
            os.makedirs(stories_folder, exist_ok=True)
            
            # Get progress dialog ready for our operations
            progress_dialog = QProgressDialog("Creating a copy of the story. Please wait...", "Cancel", 0, 100, self)
            progress_dialog.setWindowTitle("Creating Story Copy")
            progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            progress_dialog.setAutoClose(True)
            progress_dialog.setMinimumDuration(0)
            progress_dialog.setValue(0)
            progress_dialog.show()
            QApplication.processEvents()
            
            # Find appropriate copy number for the title
            original_title = original_story_data["title"]
            copy_suffix = 1
            base_title = original_title
            
            # Check if the story title already ends with "(Copy - N)"
            copy_match = re.search(r'\(Copy - (\d+)\)$', original_title)
            if copy_match:
                # If already a copy, extract the base title without the copy suffix
                copy_number = int(copy_match.group(1))
                base_title = original_title[:original_title.rfind("(Copy")].strip()
                copy_suffix = copy_number + 1
            
            # Find the highest existing copy number
            for story in self.stories:
                # Look for stories with the same base title and a copy suffix
                title = story["title"]
                if title.startswith(base_title) and "(Copy -" in title:
                    match = re.search(r'\(Copy - (\d+)\)', title)
                    if match:
                        num = int(match.group(1))
                        copy_suffix = max(copy_suffix, num + 1)
            
            progress_dialog.setValue(10)
            if progress_dialog.wasCanceled():
                return
            
            # Create new story title
            new_title = f"{base_title} (Copy - {copy_suffix})"
            
            # Create a new folder path with a random ID
            random_id = self.generate_random_id()
            new_folder_name = f"{new_title.replace(' ', '_')}_{random_id}"
            new_folder_path = os.path.join(stories_folder, new_folder_name)
            
            # Step 1: Create a new story record with empty folder path
            cursor = self.db_conn.cursor()
            
            # Get the original timestamps for the story
            cursor.execute(
                "SELECT created_at, updated_at FROM stories WHERE id = ?",
                (story_id,)
            )
            timestamp_data = cursor.fetchone()
            created_at = timestamp_data["created_at"] if timestamp_data else None
            updated_at = timestamp_data["updated_at"] if timestamp_data else None
            
            # Insert the new story directly with SQL to ensure all fields are handled correctly
            cursor.execute("""
                INSERT INTO stories (
                    title, description, type_name, folder_path, universe, 
                    is_part_of_series, series_name, series_order, author, year,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                new_title, 
                original_story_data["description"] or "", 
                original_story_data["type_name"] or "OTHER",
                "",  # Temporary empty folder path
                original_story_data["universe"] or "",
                1 if original_story_data["is_part_of_series"] in (True, 1) else 0,
                original_story_data["series_name"] or "",
                original_story_data["series_order"],
                original_story_data["author"] or "",
                original_story_data["year"],
                created_at or "CURRENT_TIMESTAMP",
                updated_at or "CURRENT_TIMESTAMP"
            ))
            
            new_story_id = cursor.lastrowid
            self.db_conn.commit()
            
            # Update the folder path
            cursor.execute(
                "UPDATE stories SET folder_path = ? WHERE id = ?",
                (new_folder_path, new_story_id)
            )
            self.db_conn.commit()
            
            # Get the updated story data
            cursor.execute("SELECT * FROM stories WHERE id = ?", (new_story_id,))
            new_story_data = dict(cursor.fetchone())
            
            # Update progress
            progress_dialog.setValue(20)
            progress_dialog.setLabelText("Copying story data...")
            if progress_dialog.wasCanceled():
                return
            QApplication.processEvents()
            
            # Step 2: Copy all related data
            
            # Step 2.1: Copy characters
            original_characters = get_story_characters(self.db_conn, story_id)
            new_character_id_map = {}  # Maps original character IDs to new character IDs
            
            progress_dialog.setValue(30)
            if progress_dialog.wasCanceled():
                return
            QApplication.processEvents()
            
            for character in original_characters:
                # For debugging
                print(f"DEBUG: Copying character {character['name']} with gender {character['gender']}")
                
                # Get the original character's timestamps
                cursor = self.db_conn.cursor()
                cursor.execute(
                    "SELECT created_at, updated_at FROM characters WHERE id = ?",
                    (character["id"],)
                )
                timestamp_data = cursor.fetchone()
                created_at = timestamp_data["created_at"] if timestamp_data else None
                updated_at = timestamp_data["updated_at"] if timestamp_data else None
                
                # Update avatar path if it exists
                avatar_path = None
                if character["avatar_path"]:
                    # Convert the original path to the new story folder path
                    avatar_path = character["avatar_path"].replace(original_story_data["folder_path"], new_folder_path)
                    print(f"DEBUG: Updated avatar path from {character['avatar_path']} to {avatar_path}")
                
                # Create a new character directly with SQL to ensure all fields are copied
                cursor.execute("""
                    INSERT INTO characters (
                        name, story_id, aliases, is_main_character, age_value, age_category, 
                        gender, avatar_path, is_archived, is_deceased, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    character["name"],
                    new_story_id,
                    character["aliases"] or "",  # Convert None to empty string for aliases
                    1 if character["is_main_character"] in (True, 1) else 0,
                    character["age_value"],
                    character["age_category"] or "",  # Convert None to empty string for age_category
                    character["gender"] or "NOT_SPECIFIED",  # Ensure gender is never None
                    avatar_path,  # Updated avatar path instead of None
                    1 if character.get("is_archived") in (True, 1) else 0,
                    1 if character.get("is_deceased") in (True, 1) else 0,
                    created_at or "CURRENT_TIMESTAMP",
                    updated_at or "CURRENT_TIMESTAMP"
                ))
                
                new_character_id = cursor.lastrowid
                self.db_conn.commit()
                
                # Store the mapping between old and new character IDs
                new_character_id_map[character["id"]] = new_character_id
            
            # Step 2.2: Copy relationships
            progress_dialog.setValue(40)
            if progress_dialog.wasCanceled():
                return
            QApplication.processEvents()
            
            original_relationships = get_story_relationships(self.db_conn, story_id)
            
            for relationship in original_relationships:
                source_id = relationship["source_id"]
                target_id = relationship["target_id"]
                
                # Skip if either character is not from this story
                if source_id not in new_character_id_map or target_id not in new_character_id_map:
                    continue
                
                # Ensure description isn't missing
                relationship_description = relationship.get("description", "")
                if relationship_description is None:
                    relationship_description = ""
                
                # Get the relationship type ID
                relationship_type_id = relationship.get("relationship_type_id")
                if relationship_type_id is None and "relationship_type" in relationship:
                    # For backward compatibility, get relationship type ID from name
                    cursor = self.db_conn.cursor()
                    cursor.execute("SELECT id FROM relationship_types WHERE name = ?", 
                                  (relationship["relationship_type"],))
                    result = cursor.fetchone()
                    if result:
                        relationship_type_id = result["id"]
                
                # If we still don't have a relationship type ID, skip this relationship
                if relationship_type_id is None:
                    print(f"WARNING: Could not find relationship type ID for {relationship.get('relationship_type', 'unknown')}. Skipping.")
                    continue
                
                # Create a new relationship between the new characters
                try:
                    create_relationship(
                        self.db_conn,
                        source_id=new_character_id_map[source_id],
                        target_id=new_character_id_map[target_id],
                        relationship_type_id=relationship_type_id,
                        description=relationship_description,
                        color=relationship.get("color", "#000000"),  # Default to black if missing
                        width=relationship.get("width", 1.0),  # Default to 1.0 if missing
                        is_custom=relationship.get("is_custom", False),
                        custom_label=relationship.get("custom_label")
                    )
                except Exception as rel_error:
                    print(f"WARNING: Error copying relationship: {rel_error}")
                    import traceback
                    traceback.print_exc()
                    # Try again with defaults for all non-essential fields
                    try:
                        create_relationship(
                            self.db_conn,
                            source_id=new_character_id_map[source_id],
                            target_id=new_character_id_map[target_id],
                            relationship_type_id=relationship_type_id,
                            description="",  # Empty description
                            color="#000000",  # Default color
                            width=1.0  # Default width
                        )
                    except Exception as retry_error:
                        print(f"ERROR: Failed on second attempt to copy relationship: {retry_error}")
                        import traceback
                        traceback.print_exc()
            
            # Step 2.3: Copy story board views
            progress_dialog.setValue(50)
            if progress_dialog.wasCanceled():
                return
            QApplication.processEvents()
            
            try:
                original_views = get_story_board_views(self.db_conn, story_id)
                print(f"DEBUG: Found {len(original_views)} story board views to copy")
                
                for view in original_views:
                    try:
                        print(f"DEBUG: Copying view: {view.get('name', 'unnamed')}")
                        
                        # Parse the layout data to update character IDs
                        layout_data = {}
                        try:
                            layout_json = view.get("layout_data", "{}")
                            if layout_json:
                                layout_data = json.loads(layout_json)
                            else:
                                layout_data = {}
                                print("DEBUG: Empty layout data, using empty dict")
                        except json.JSONDecodeError as jde:
                            print(f"WARNING: Could not parse layout data: {jde}")
                            layout_data = {}  # Use empty dict as fallback
                        
                        # Update character IDs in the layout data
                        if "characters" in layout_data:
                            updated_characters = {}
                            for char_id, char_data in layout_data["characters"].items():
                                try:
                                    char_id_int = int(char_id)
                                    if char_id_int in new_character_id_map:
                                        new_id = new_character_id_map[char_id_int]
                                        updated_characters[str(new_id)] = char_data
                                except (ValueError, KeyError) as e:
                                    print(f"WARNING: Error updating character ID {char_id}: {e}")
                                    continue
                            
                            layout_data["characters"] = updated_characters
                        
                        # Ensure description isn't None
                        view_name = view.get("name", "View")
                        if view_name is None:
                            view_name = "View"
                            print("DEBUG: Sanitized NULL view name to 'View'")
                            
                        view_description = view.get("description", "")
                        if view_description is None:
                            view_description = ""
                            print("DEBUG: Sanitized NULL view description to empty string")
                        
                        # Create a new view with the updated layout data
                        try:
                            new_view_id = create_story_board_view(
                                self.db_conn,
                                name=view_name,
                                story_id=new_story_id,
                                layout_data=json.dumps(layout_data),
                                description=view_description
                            )
                            print(f"DEBUG: Created story board view with ID {new_view_id}")
                        except Exception as view_error:
                            print(f"WARNING: Error creating story board view: {view_error}")
                            import traceback
                            traceback.print_exc()
                            # Try again with empty description
                            new_view_id = create_story_board_view(
                                self.db_conn,
                                name=view_name,
                                story_id=new_story_id,
                                layout_data=json.dumps(layout_data),
                                description=""
                            )
                            print(f"DEBUG: Created story board view on second attempt with ID {new_view_id}")
                    except Exception as e:
                        print(f"WARNING: Failed to copy story board view: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
            except Exception as e:
                print(f"WARNING: Failed to copy story board views: {e}")
                import traceback
                traceback.print_exc()
                # Continue with the duplication process
            
            # Step 2.4: Copy events
            progress_dialog.setValue(60)
            if progress_dialog.wasCanceled():
                return
            QApplication.processEvents()
            
            original_events = get_story_events(self.db_conn, story_id)
            event_id_map = {}  # Maps original event IDs to new event IDs
            
            # First pass: create all events without parent relationships
            for event in original_events:
                # Ensure description isn't None
                event_description = event.get("description", "")
                if event_description is None:
                    event_description = ""
                
                try:
                    new_event_id = create_event(
                        self.db_conn,
                        title=event["title"],
                        story_id=new_story_id,
                        description=event_description,
                        event_type=event["event_type"],
                        start_date=event["start_date"],
                        end_date=event["end_date"],
                        location=event["location"],
                        importance=event["importance"],
                        color=event["color"],
                        is_milestone=event["is_milestone"] in (True, 1),
                        parent_event_id=None,  # Set parent in second pass
                        sequence_number=event["sequence_number"]
                    )
                except Exception as event_error:
                    print(f"WARNING: Error copying event: {event_error}")
                    # Try again with empty description
                    new_event_id = create_event(
                        self.db_conn,
                        title=event["title"],
                        story_id=new_story_id,
                        description="",  # Force empty string
                        event_type=event["event_type"],
                        start_date=event["start_date"],
                        end_date=event["end_date"],
                        location=event["location"],
                        importance=event["importance"],
                        color=event["color"],
                        is_milestone=event["is_milestone"] in (True, 1),
                        parent_event_id=None,  # Set parent in second pass
                        sequence_number=event["sequence_number"]
                    )
                
                event_id_map[event["id"]] = new_event_id
                
                # Get characters associated with this event
                event_characters = get_event_characters(self.db_conn, event["id"])
                
                # Associate the new characters with the new event
                for ec in event_characters:
                    if ec["character_id"] in new_character_id_map:
                        add_character_to_event(
                            self.db_conn,
                            event_id=new_event_id,
                            character_id=new_character_id_map[ec["character_id"]],
                            role=ec["role"],
                            notes=ec["notes"]
                        )
            
            # Second pass: update parent event IDs
            progress_dialog.setValue(65)
            if progress_dialog.wasCanceled():
                return
            QApplication.processEvents()
            
            for event in original_events:
                if event["parent_event_id"] is not None and event["parent_event_id"] in event_id_map:
                    update_event(
                        self.db_conn,
                        event_id=event_id_map[event["id"]],
                        parent_event_id=event_id_map[event["parent_event_id"]]
                    )
            
            # Step 2.5: Copy images
            progress_dialog.setValue(70)
            progress_dialog.setLabelText("Copying image records...")
            if progress_dialog.wasCanceled():
                return
            QApplication.processEvents()
            
            # Get all images for the original story
            original_images = get_story_images(self.db_conn, story_id)
            image_id_map = {}
            
            for image in original_images:
                # Update the path to the new story folder
                original_path = image["path"]
                new_path = original_path.replace(original_story_data["folder_path"], new_folder_path)
                
                # Ensure no NULL values in fields
                image_description = image.get("description", "")
                if image_description is None:
                    image_description = ""
                
                # Get the original created_at and updated_at timestamps
                cursor = self.db_conn.cursor()
                cursor.execute(
                    "SELECT created_at, updated_at FROM images WHERE id = ?",
                    (image["id"],)
                )
                timestamp_data = cursor.fetchone()
                created_at = timestamp_data["created_at"] if timestamp_data else None
                updated_at = timestamp_data["updated_at"] if timestamp_data else None
                
                # Create new image record with preserved timestamps
                try:
                    if created_at and updated_at:
                        cursor.execute(
                            """
                            INSERT INTO images (
                                filename, path, story_id, title, description, width, height,
                                file_size, mime_type, is_featured, date_taken,
                                metadata_json, event_id, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                image["filename"], new_path, new_story_id, image["title"], 
                                image_description, image["width"], image["height"],
                                image["file_size"], image["mime_type"], 
                                1 if image["is_featured"] in (True, 1) else 0, 
                                image["date_taken"], image["metadata_json"],
                                event_id_map.get(image["event_id"]) if image["event_id"] else None,
                                created_at, updated_at
                            )
                        )
                        new_image_id = cursor.lastrowid
                        self.db_conn.commit()
                    else:
                        # Fallback to create_image if timestamps are not available
                        new_image_id = create_image(
                            self.db_conn,
                            filename=image["filename"],
                            path=new_path,
                            story_id=new_story_id,
                            title=image["title"],
                            description=image_description,
                            width=image["width"],
                            height=image["height"],
                            file_size=image["file_size"],
                            mime_type=image["mime_type"],
                            is_featured=image["is_featured"] in (True, 1),
                            date_taken=image["date_taken"],
                            metadata_json=image["metadata_json"],
                            event_id=event_id_map.get(image["event_id"]) if image["event_id"] else None
                        )
                except Exception as img_error:
                    print(f"WARNING: Error creating image record: {img_error}")
                    # Try again with empty description
                    new_image_id = create_image(
                        self.db_conn,
                        filename=image["filename"],
                        path=new_path,
                        story_id=new_story_id,
                        title=image["title"],
                        description="",  # Force empty string
                        width=image["width"],
                        height=image["height"],
                        file_size=image["file_size"],
                        mime_type=image["mime_type"],
                        is_featured=image["is_featured"] in (True, 1),
                        date_taken=image["date_taken"],
                        metadata_json=image["metadata_json"],
                        event_id=event_id_map.get(image["event_id"]) if image["event_id"] else None
                    )
                
                # Store the mapping
                image_id_map[image["id"]] = new_image_id
                
                # Copy character tags for this image
                tags = get_image_character_tags(self.db_conn, image["id"])
                for tag in tags:
                    if tag["character_id"] in new_character_id_map:
                        # Ensure no NULL values in position coordinates for image_character_tags
                        x_position = tag["x_position"] if tag["x_position"] is not None else 0.0
                        y_position = tag["y_position"] if tag["y_position"] is not None else 0.0
                        width = tag["width"] if tag["width"] is not None else 0.0
                        height = tag["height"] if tag["height"] is not None else 0.0
                        
                        add_character_tag_to_image(
                            self.db_conn,
                            new_image_id,
                            new_character_id_map[tag["character_id"]],
                            x_position,
                            y_position,
                            width,
                            height,
                            tag.get("note", "")
                        )
                self.db_conn.commit()
            
            # Step 2.5.1: Copy image_tags (front-end visible tags)
            progress_dialog.setValue(72)
            progress_dialog.setLabelText("Copying image tags...")
            if progress_dialog.wasCanceled():
                return
            QApplication.processEvents()
            
            try:
                cursor = self.db_conn.cursor()
                cursor.execute('''
                    SELECT * FROM image_tags
                    WHERE image_id IN (
                        SELECT id FROM images WHERE story_id = ?
                    )
                ''', (story_id,))
                image_tags = cursor.fetchall()
                
                for tag in image_tags:
                    try:
                        if tag["image_id"] in image_id_map and tag["character_id"] in new_character_id_map:
                            # Safely access position values with defaults if they don't exist or are NULL
                            x = 0.0
                            if "x" in tag and tag["x"] is not None:
                                x = tag["x"]
                                
                            y = 0.0
                            if "y" in tag and tag["y"] is not None:
                                y = tag["y"]
                                
                            width = 0.0
                            if "width" in tag and tag["width"] is not None:
                                width = tag["width"]
                                
                            height = 0.0
                            if "height" in tag and tag["height"] is not None:
                                height = tag["height"]
                            
                            cursor.execute('''
                                INSERT INTO image_tags (
                                    created_at, updated_at, x, y, width, height, 
                                    image_id, character_id
                                ) VALUES (
                                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?, ?, ?,
                                    ?, ?
                                )
                            ''', (
                                x, y, width, height,
                                image_id_map[tag["image_id"]], new_character_id_map[tag["character_id"]]
                            ))
                    except KeyError as ke:
                        print(f"Warning: Missing key in image tag: {ke}")
                        continue
                    except Exception as te:
                        print(f"Warning: Error copying image tag: {te}")
                        continue
                        
                self.db_conn.commit()
            except Exception as e:
                print(f"Warning: Failed to copy image tags: {e}")
                # Continue with the rest of the duplication process
            
            # Step 2.5.2: Copy image_features (for character recognition)
            progress_dialog.setValue(73)
            progress_dialog.setLabelText("Copying image features...")
            if progress_dialog.wasCanceled():
                return
            QApplication.processEvents()
            
            try:
                cursor.execute('''
                    SELECT * FROM image_features
                    WHERE character_id IN (
                        SELECT id FROM characters WHERE story_id = ?
                    )
                ''', (story_id,))
                image_features = cursor.fetchall()
                
                for feature in image_features:
                    try:
                        new_image_id = None
                        if "image_id" in feature and feature["image_id"] is not None and feature["image_id"] in image_id_map:
                            new_image_id = image_id_map[feature["image_id"]]
                            
                        if "character_id" in feature and feature["character_id"] in new_character_id_map:
                            cursor.execute('''
                                INSERT INTO image_features (
                                    character_id, image_id, is_avatar, feature_data,
                                    color_histogram, created_at, updated_at
                                ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            ''', (
                                new_character_id_map[feature["character_id"]],
                                new_image_id,
                                feature.get("is_avatar", 0),
                                feature.get("feature_data", None),
                                feature.get("color_histogram", None)
                            ))
                    except Exception as fe:
                        print(f"Warning: Error copying image feature: {fe}")
                        continue
                
                self.db_conn.commit()
            except Exception as e:
                print(f"Warning: Failed to copy image features: {e}")
                # Continue with the duplication process
                
            # Step 2.7: Copy character_details
            progress_dialog.setValue(76)
            progress_dialog.setLabelText("Copying character details...")
            if progress_dialog.wasCanceled():
                return
            QApplication.processEvents()
            
            try:
                cursor.execute('''
                    SELECT cd.*
                    FROM character_details cd
                    JOIN characters c ON cd.character_id = c.id
                    WHERE c.story_id = ?
                ''', (story_id,))
                character_details = cursor.fetchall()
                
                for detail in character_details:
                    try:
                        if "character_id" in detail and detail["character_id"] in new_character_id_map:
                            # Safely get values with defaults
                            detail_text = detail.get("detail_text", "")
                            detail_type = detail.get("detail_type", "GENERAL")
                            sequence_number = detail.get("sequence_number", 0)
                            created_at = detail.get("created_at", "CURRENT_TIMESTAMP")
                            updated_at = detail.get("updated_at", "CURRENT_TIMESTAMP")
                            
                            cursor.execute('''
                                INSERT INTO character_details (
                                    created_at, updated_at, character_id, detail_text,
                                    detail_type, sequence_number
                                ) VALUES (
                                    ?, ?, ?, ?, ?, ?
                                )
                            ''', (
                                created_at,
                                updated_at,
                                new_character_id_map[detail["character_id"]],
                                detail_text,
                                detail_type,
                                sequence_number
                            ))
                    except Exception as de:
                        print(f"Warning: Error copying character detail: {de}")
                        continue
                
                self.db_conn.commit()
            except Exception as e:
                print(f"Warning: Failed to copy character details: {e}")
                # Continue with the duplication process
                
            # Step 2.13: Copy timeline_views
            progress_dialog.setValue(82)
            progress_dialog.setLabelText("Copying timeline views...")
            if progress_dialog.wasCanceled():
                return
            QApplication.processEvents()
            
            try:
                cursor.execute('''
                    SELECT * FROM timeline_views
                    WHERE story_id = ?
                ''', (story_id,))
                timeline_views = cursor.fetchall()
                
                for view in timeline_views:
                    try:
                        # Parse and update the layout data if it exists
                        layout_data = view.get("layout_data", None)
                        if layout_data:
                            try:
                                layout_json = json.loads(layout_data)
                                # Update any event IDs in the layout data
                                # This depends on the structure of your layout data
                                # This is a simplified example - you may need to adapt
                                if "events" in layout_json:
                                    updated_events = {}
                                    for event_id, event_data in layout_json["events"].items():
                                        if int(event_id) in event_id_map:
                                            updated_events[str(event_id_map[int(event_id)])] = event_data
                                    layout_json["events"] = updated_events
                                layout_data = json.dumps(layout_json)
                            except (json.JSONDecodeError, TypeError) as je:
                                print(f"Warning: Could not parse layout data: {je}")
                                # If we can't parse it, leave it as is
                                pass
                        
                        # Ensure description and view_type values aren't None
                        view_name = view.get("name", "")
                        if view_name is None:
                            view_name = ""
                            
                        view_description = view.get("description", "")
                        if view_description is None:
                            view_description = ""
                            
                        view_type = view.get("view_type", "")
                        if view_type is None:
                            view_type = ""
                        
                        cursor.execute('''
                            INSERT INTO timeline_views (
                                created_at, updated_at, name, description, view_type, layout_data, story_id
                            ) VALUES (
                                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?
                            )
                        ''', (
                            view_name,
                            view_description,
                            view_type,
                            layout_data,
                            new_story_id
                        ))
                    except Exception as ve:
                        print(f"Warning: Error copying timeline view: {ve}")
                        continue
                
                self.db_conn.commit()
            except Exception as e:
                print(f"Warning: Failed to copy timeline views: {e}")
                # Continue with the duplication process
                
            # Step 5: Copy decision points and their options
            progress_dialog.setValue(95)
            progress_dialog.setLabelText("Copying decision points...")
            if progress_dialog.wasCanceled():
                return
            QApplication.processEvents()
            
            try:
                # Print each step for debugging
                print("DEBUG: Starting decision points copy")
                
                # Get decision points for the original story
                original_decision_points = get_story_decision_points(self.db_conn, story_id)
                print(f"DEBUG: Found {len(original_decision_points)} decision points")
                
                decision_point_id_map = {}  # Maps original decision point IDs to new decision point IDs
                
                # Copy each decision point
                for dp in original_decision_points:
                    try:
                        # Print what we're working with for debugging
                        print(f"DEBUG: Copying decision point: ID={dp.get('id', 'unknown')}, Title={dp.get('title', 'untitled')}")
                        
                        # Create new decision point with defensive access to attributes
                        title = dp.get("title", "Untitled")  # Default to "Untitled" if title is missing
                        description = dp.get("description", "")  # Default to empty string if description is missing
                        is_ordered_list = dp.get("is_ordered_list", 0) in (1, True)
                        
                        # Ensure description is not None
                        if description is None:
                            description = ""
                            print("DEBUG: Sanitized NULL description to empty string")
                            
                        print(f"DEBUG: Creating decision point with title='{title}', description='{description}', is_ordered_list={is_ordered_list}")
                        
                        try:
                            new_dp_id = create_decision_point(
                                self.db_conn,
                                title=title,
                                story_id=new_story_id,
                                description=description,
                                is_ordered_list=is_ordered_list
                            )
                            print(f"DEBUG: Created decision point with ID {new_dp_id}")
                        except Exception as dp_create_error:
                            print(f"ERROR creating decision point: {dp_create_error}")
                            import traceback
                            traceback.print_exc()
                            # Try one more time with an empty description
                            new_dp_id = create_decision_point(
                                self.db_conn,
                                title=title,
                                story_id=new_story_id,
                                description="",  # Force empty string
                                is_ordered_list=is_ordered_list
                            )
                            print(f"DEBUG: Created decision point on second attempt with ID {new_dp_id}")
                        
                        # Store mapping if we have the original ID
                        if "id" in dp and dp["id"] is not None:
                            decision_point_id_map[dp["id"]] = new_dp_id
                        
                        # Get options for this decision point
                        try:
                            options = get_decision_options(self.db_conn, dp["id"])
                            print(f"DEBUG: Found {len(options)} options for decision point")
                        
                            # Copy each option
                            for option in options:
                                try:
                                    print(f"DEBUG: Copying option: {option.get('text', 'no text')}")
                                    
                                    # Defensively access option attributes
                                    text = option.get("text", "")
                                    if text is None:
                                        text = ""
                                        print("DEBUG: Sanitized NULL option text to empty string")
                                        
                                    is_selected = option.get("is_selected", 0) in (1, True)
                                    display_order = option.get("display_order", 0)
                                    played_order = option.get("played_order", None)
                                    
                                    add_decision_option(
                                        self.db_conn,
                                        decision_point_id=new_dp_id,
                                        text=text,
                                        is_selected=is_selected,
                                        display_order=display_order,
                                        played_order=played_order
                                    )
                                except Exception as oe:
                                    print(f"WARNING: Error copying decision option: {oe}")
                                    import traceback
                                    traceback.print_exc()
                                    continue
                        except Exception as opt_error:
                            print(f"ERROR: Failed to get decision options: {opt_error}")
                            import traceback
                            traceback.print_exc()
                            continue
                    except Exception as dpe:
                        print(f"WARNING: Error copying decision point: {dpe}")
                        import traceback
                        traceback.print_exc()
                        continue
            except Exception as e:
                print(f"WARNING: Failed to copy decision points: {e}")
                import traceback
                traceback.print_exc()
                # Continue with the duplication process
            
            # Step 5.5: Copy actual image files
            progress_dialog.setValue(98)
            progress_dialog.setLabelText("Copying image files...")
            if progress_dialog.wasCanceled():
                return
            QApplication.processEvents()
            
            try:
                print("DEBUG: Starting image file copying")
                
                # Create images directory in the new story folder
                original_images_dir = os.path.join(original_story_data["folder_path"], "images")
                new_images_dir = os.path.join(new_folder_path, "images")
                
                os.makedirs(new_images_dir, exist_ok=True)
                print(f"DEBUG: Created directory {new_images_dir}")
                
                # Get list of image files
                if os.path.exists(original_images_dir):
                    image_files = os.listdir(original_images_dir)
                    print(f"DEBUG: Found {len(image_files)} image files to copy")
                    
                    for filename in image_files:
                        src_path = os.path.join(original_images_dir, filename)
                        dst_path = os.path.join(new_images_dir, filename)
                        
                        if os.path.isfile(src_path):
                            try:
                                shutil.copy2(src_path, dst_path)
                                print(f"DEBUG: Copied {filename}")
                            except Exception as copy_error:
                                print(f"ERROR: Failed to copy image file {filename}: {copy_error}")
                                import traceback
                                traceback.print_exc()
                                continue
                else:
                    print(f"WARNING: Original images directory {original_images_dir} does not exist")
                
                # Create thumbnails directory if needed
                original_thumbnails_dir = os.path.join(original_story_data["folder_path"], "thumbnails")
                if os.path.exists(original_thumbnails_dir):
                    new_thumbnails_dir = os.path.join(new_folder_path, "thumbnails")
                    os.makedirs(new_thumbnails_dir, exist_ok=True)
                    print(f"DEBUG: Created thumbnails directory {new_thumbnails_dir}")
                    
                    thumbnail_files = os.listdir(original_thumbnails_dir)
                    print(f"DEBUG: Found {len(thumbnail_files)} thumbnail files to copy")
                    
                    for filename in thumbnail_files:
                        src_path = os.path.join(original_thumbnails_dir, filename)
                        dst_path = os.path.join(new_thumbnails_dir, filename)
                        
                        if os.path.isfile(src_path):
                            try:
                                shutil.copy2(src_path, dst_path)
                                print(f"DEBUG: Copied thumbnail {filename}")
                            except Exception as copy_error:
                                print(f"ERROR: Failed to copy thumbnail file {filename}: {copy_error}")
                                continue
                
                # Create avatars directory if needed
                original_avatars_dir = os.path.join(original_story_data["folder_path"], "avatars")
                if os.path.exists(original_avatars_dir):
                    new_avatars_dir = os.path.join(new_folder_path, "avatars")
                    os.makedirs(new_avatars_dir, exist_ok=True)
                    print(f"DEBUG: Created avatars directory {new_avatars_dir}")
                    
                    avatar_files = os.listdir(original_avatars_dir)
                    print(f"DEBUG: Found {len(avatar_files)} avatar files to copy")
                    
                    for filename in avatar_files:
                        src_path = os.path.join(original_avatars_dir, filename)
                        dst_path = os.path.join(new_avatars_dir, filename)
                        
                        if os.path.isfile(src_path):
                            try:
                                shutil.copy2(src_path, dst_path)
                                print(f"DEBUG: Copied avatar {filename}")
                            except Exception as copy_error:
                                print(f"ERROR: Failed to copy avatar file {filename}: {copy_error}")
                                continue
                
                # Copy artwork.png if it exists
                original_artwork_path = os.path.join(original_story_data["folder_path"], "artwork.png")
                if os.path.exists(original_artwork_path):
                    new_artwork_path = os.path.join(new_folder_path, "artwork.png")
                    try:
                        shutil.copy2(original_artwork_path, new_artwork_path)
                        print(f"DEBUG: Copied story artwork from {original_artwork_path} to {new_artwork_path}")
                    except Exception as artwork_error:
                        print(f"ERROR: Failed to copy story artwork: {artwork_error}")
                        import traceback
                        traceback.print_exc()
            except Exception as e:
                print(f"ERROR: Failed to copy image files: {e}")
                import traceback
                traceback.print_exc()
                # Continue with the duplication process, even if image copying failed
            
            # Step 6: Add the new story to our local list and UI
            progress_dialog.setValue(100)
            QApplication.processEvents()
            
            self.stories.append(new_story_data)
            self.add_story_to_list(new_story_data)
            
            # Show success message
            QMessageBox.information(
                self,
                "Story Duplicated",
                f"Story '{original_title}' has been duplicated as '{new_title}'."
            )
            
        except Exception as e:
            print(f"ERROR: Failed to duplicate story: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Create more detailed error message
            error_type = type(e).__name__
            error_message = str(e)
            
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to duplicate story: {error_type} - {error_message}\n\n"
                "Check the console for more detailed error information."
            )
    
    def on_delete_story(self, story_id: int) -> None:
        """Handle deleting a story.
        
        Args:
            story_id: ID of the story to delete
        """
        try:
            # Get the story data
            story_data = None
            for story in self.stories:
                if story["id"] == story_id:
                    story_data = story
                    break
            
            if not story_data:
                QMessageBox.critical(
                    self,
                    "Error",
                    "Failed to find the selected story."
                )
                return
            
            # Confirm deletion
            title = story_data["title"]
            confirm = QMessageBox.question(
                self,
                "Confirm Deletion",
                f"Are you sure you want to delete the story '{title}'?\n\n"
                "This action will permanently delete the story and all its data, "
                "including characters, relationships, events, and images.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if confirm != QMessageBox.StandardButton.Yes:
                return
            
            # Create a progress dialog
            progress_dialog = QProgressDialog("Preparing to delete story...", "Cancel", 0, 100, self)
            progress_dialog.setWindowTitle("Deleting Story")
            progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            progress_dialog.setAutoClose(True)
            progress_dialog.setMinimumDuration(0)
            progress_dialog.show()
            QApplication.processEvents()
            
            # Step 1: Get the story folder path
            folder_path = story_data["folder_path"]
            
            # Validate that this is a legitimate story path before deleting
            if not folder_path or not os.path.exists(folder_path):
                QMessageBox.warning(
                    self,
                    "Warning",
                    f"The story folder doesn't exist at {folder_path}. Will only delete database records."
                )
            else:
                # Extra safety check: verify the folder belongs only to this story
                # Check if any other stories use this folder or a subfolder of it
                cursor = self.db_conn.cursor()
                cursor.execute(
                    "SELECT id, title FROM stories WHERE folder_path LIKE ? AND id != ?", 
                    (folder_path + "%", story_id)
                )
                conflicts = cursor.fetchall()
                
                if conflicts:
                    conflict_titles = ", ".join([f"'{c['title']}'" for c in conflicts])
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Cannot delete the story folder because it contains or is used by other stories: {conflict_titles}. "
                        "Only database records will be deleted."
                    )
                    # Set folder_path to None to skip file deletion
                    folder_path = None
            
            progress_dialog.setValue(10)
            progress_dialog.setLabelText("Collecting records to delete...")
            QApplication.processEvents()
            
            # Collect counts of related records for progress reporting
            cursor = self.db_conn.cursor()
            
            # Count characters
            cursor.execute("SELECT COUNT(*) as count FROM characters WHERE story_id = ?", (story_id,))
            char_count = cursor.fetchone()["count"]
            
            # Count events
            cursor.execute("SELECT COUNT(*) as count FROM events WHERE story_id = ?", (story_id,))
            event_count = cursor.fetchone()["count"]
            
            # Count images
            cursor.execute("SELECT COUNT(*) as count FROM images WHERE story_id = ?", (story_id,))
            image_count = cursor.fetchone()["count"]
            
            progress_dialog.setValue(15)
            progress_dialog.setLabelText(f"Deleting story data ({char_count} characters, {event_count} events, {image_count} images)...")
            QApplication.processEvents()
            
            # Step 2: Begin transaction to ensure all deletions are atomic
            self.db_conn.execute("BEGIN TRANSACTION")
            
            try:
                # Step
                progress_dialog.setValue(20)
                QApplication.processEvents()
                
                # Delete in order of dependency to avoid constraint issues
                # Note: The database has ON DELETE CASCADE for related entries,
                # but we'll delete in a logical order for clarity and progress reporting
                
                # Step 3.1: Delete image-related records first
                progress_dialog.setValue(30)
                progress_dialog.setLabelText("Deleting image data...")
                QApplication.processEvents()
                
                # Image tags will be automatically deleted by CASCADE
                # Face encodings will be automatically deleted by CASCADE
                # Image features will be automatically deleted by CASCADE
                
                # Step 3.2: Delete character-related records
                progress_dialog.setValue(40)
                progress_dialog.setLabelText("Deleting character data...")
                QApplication.processEvents()
                
                # Character details will be automatically deleted by CASCADE
                # Relationships will be automatically deleted by CASCADE
                
                # Step 3.3: Delete event-related records
                progress_dialog.setValue(50)
                progress_dialog.setLabelText("Deleting event data...")
                QApplication.processEvents()
                
                # Scene_images will be automatically deleted by CASCADE
                # Event_characters will be automatically deleted by CASCADE
                
                # Step 3.4: Delete decision points and options
                progress_dialog.setValue(60)
                progress_dialog.setLabelText("Deleting decision data...")
                QApplication.processEvents()
                
                # Decision options will be automatically deleted by CASCADE
                
                # Step 3.5: Delete story views
                progress_dialog.setValue(70)
                progress_dialog.setLabelText("Deleting story views...")
                QApplication.processEvents()
                
                # Story board views will be automatically deleted by CASCADE
                # Timeline views will be automatically deleted by CASCADE
                
                # Step 3.6: Finally delete the story itself
                progress_dialog.setValue(80)
                progress_dialog.setLabelText("Removing story record...")
                QApplication.processEvents()
                
                cursor = self.db_conn.cursor()
                cursor.execute("DELETE FROM stories WHERE id = ?", (story_id,))
                
                # Commit all database changes
                self.db_conn.commit()
                
                # Step 4: Delete from the local stories list
                self.stories = [story for story in self.stories if story["id"] != story_id]
                
                # Step 5: Delete from the UI
                for i in range(self.story_list.count()):
                    item = self.story_list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == story_id:
                        self.story_list.takeItem(i)
                        break
                
            except Exception as e:
                # If anything goes wrong, roll back the transaction
                self.db_conn.rollback()
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to delete story database records: {str(e)}"
                )
                progress_dialog.close()
                return
            
            # Step 6: Delete the story folder and all its contents if it exists and is safe
            if folder_path and os.path.exists(folder_path):
                progress_dialog.setValue(85)
                progress_dialog.setLabelText("Removing story files...")
                QApplication.processEvents()
                
                try:
                    # Do one more check to ensure we're deleting the right folder
                    if os.path.basename(folder_path).startswith(title.replace(' ', '_')) or title in folder_path:
                        # Use shutil to remove the directory and all its contents
                        shutil.rmtree(folder_path)
                    else:
                        QMessageBox.warning(
                            self,
                            "Warning",
                            f"Skipped deletion of folder {folder_path} as a safety precaution. "
                            "The folder name doesn't match the story title."
                        )
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        "Warning",
                        f"The story was removed from the database, but there was an error deleting the story folder: {str(e)}"
                    )
            
            # Step 7: Clear the form if the deleted story was currently selected
            progress_dialog.setValue(95)
            QApplication.processEvents()
            
            selected_items = self.story_list.selectedItems()
            if not selected_items:
                self.clear_form()
            
            # Complete the progress
            progress_dialog.setValue(100)
            QApplication.processEvents()
            
            # Show success message
            QMessageBox.information(
                self,
                "Story Deleted",
                f"Story '{title}' has been deleted."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to delete story: {str(e)}"
            )
            import traceback
            traceback.print_exc()
    
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
    
    def update_story_list_item(self, story_id: int) -> None:
        """Update the story list item with the current artwork.
        
        Args:
            story_id: ID of the story to update
        """
        # Find the story item
        for i in range(self.story_list.count()):
            item = self.story_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == story_id:
                # Find the story data to get the folder path
                for story in self.stories:
                    if story["id"] == story_id:
                        # Get the artwork path
                        artwork_path = self.get_artwork_path(story["folder_path"])
                        # Update the item data
                        item.setData(Qt.ItemDataRole.UserRole + 1, artwork_path)
                        # Force a repaint
                        self.story_list.update()
                        break
                break
    
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
                        self.update_story_list_item(story_id)
                    
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
            
            # Add artwork path if available
            artwork_path = self.get_artwork_path(story_folder)
            item.setData(Qt.ItemDataRole.UserRole + 1, artwork_path)
            
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
        
        # Emit the story selected signal to open the story
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
        
        # Add artwork path if available
        artwork_path = self.get_artwork_path(story_data["folder_path"])
        item.setData(Qt.ItemDataRole.UserRole + 1, artwork_path)
        
        self.story_list.addItem(item)
        self.story_list.setCurrentItem(item) 