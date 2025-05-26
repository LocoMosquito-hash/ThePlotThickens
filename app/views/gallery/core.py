#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Core Gallery Widget for The Plot Thickens application.

This module contains the main GalleryWidget class that manages the gallery view.
"""

from typing import List, Dict, Any, Optional, Tuple, Set
import os
import re
from datetime import datetime
import time
import logging
from io import BytesIO
import tempfile
import random
import string

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QGridLayout, QFileDialog, QMessageBox,
    QCheckBox, QSplitter, QTabWidget, QFrame, QMenu,
    QApplication, QDialog, QProgressDialog
)
from PyQt6.QtCore import (
    Qt, QSize, pyqtSignal, QBuffer, QIODevice, 
    QUrl, QPoint, QRect, QTimer, QSettings
)
from PyQt6.QtGui import (
    QPixmap, QImage, QColor, QBrush, QPen, QPainter, 
    QFont, QCursor, QAction, QKeySequence
)
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

# Import gallery components
from app.views.gallery.thumbnails import ThumbnailWidget, SeparatorWidget
from app.views.gallery.tagging import TaggableImageLabel, GraphicsTagView
from app.views.gallery.dialogs.image_detail import ImageDetailDialog
from app.views.gallery.dialogs.region_selection import RegionSelectionDialog
from app.views.gallery.dialogs.filter_dialog import GalleryFilterDialog
from app.views.gallery.dialogs.quick_event_dialog import (
    QuickEventSelectionDialog, QuickEventEditor
)
from app.views.gallery.dialogs.batch_character_tagging import BatchCharacterTaggingDialog
from app.views.gallery.dialogs.batch_context_tagging import BatchContextTaggingDialog
from app.views.gallery.character.widgets import (
    CharacterListWidget, OnSceneCharacterListWidget
)
from app.views.gallery.character.completer import CharacterTagCompleter

# Import database functions
from app.db_sqlite import (
    get_image_quick_events, get_character_quick_events,
    associate_quick_event_with_image, remove_quick_event_image_association,
    get_story_characters, get_character,
    add_character_tag_to_image, remove_character_tag,
    get_image_character_tags, create_quick_event, get_next_quick_event_sequence_number,
    get_quick_event_tagged_characters,
    process_quick_event_character_tags, get_quick_event_scenes,
    add_image_to_scene, remove_image_from_scene, get_image_scenes,
    update_character_last_tagged, get_characters_by_last_tagged,
    get_story_folder_paths, ensure_story_folders_exist,
    get_images_character_tags_batch, get_images_quick_events_batch,
    get_character_image_counts_by_story
)

# Import image recognition utility
from app.utils.image_recognition_util import ImageRecognitionUtil

# Import icon manager for Tabler icons
from app.utils.icons import icon_manager


class GalleryWidget(QWidget):
    """Widget for managing and displaying a story's image gallery."""
    
    def __init__(self, db_conn, parent=None) -> None:
        """Initialize the gallery widget.
        
        Args:
            db_conn: Database connection
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        
        # Settings
        self.settings = QSettings("ThePlotThickens", "ThePlotThickens")
        
        # Story data
        self.story_id = None
        self.story_data = None
        
        # Image and thumbnail data
        self.thumbnails = {}  # Map of image_id -> ThumbnailWidget
        self.images = []      # List of image data dicts
        self.pixmap_cache = {}  # Cache of image_id -> QPixmap
        
        # Cached data for performance
        self.story_characters = {}  # Cache of story characters
        self.image_character_tags_cache = {}  # Cache of image character tags
        self.image_quick_events_cache = {}  # Cache of image quick events
        
        # Selection state
        self.selected_images = set()  # Set of selected image IDs
        
        # Filters and display options
        self.show_nsfw = self.settings.value("gallery/show_nsfw", False, type=bool)
        self.scene_grouping = self.settings.value("gallery/scene_grouping", False, type=bool)
        self.character_filters = []  # List of (character_id, include) tuples
        
        # Network manager for downloading images
        self.network_manager = QNetworkAccessManager()
        
        # Image recognition utility for character recognition
        self.recognition_util = ImageRecognitionUtil(self.db_conn)
        
        # Load nsfw placeholder
        self.nsfw_placeholder = self._create_nsfw_placeholder()
        
        # Initialize UI
        self.init_ui()
        
        # Hide batch operations panel initially
        self.batch_operations_panel.setVisible(False)
    
    def init_ui(self) -> None:
        """Initialize the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Control buttons at the top
        control_layout = QHBoxLayout()
        
        # Import image button
        import_btn = QPushButton("Import Image")
        import_btn.setIcon(icon_manager.get_icon("upload"))
        import_btn.clicked.connect(self.import_image)
        control_layout.addWidget(import_btn)
        
        # Paste image button
        paste_btn = QPushButton("Paste from Clipboard")
        paste_btn.setIcon(icon_manager.get_icon("clipboard"))
        paste_btn.clicked.connect(self.paste_image)
        control_layout.addWidget(paste_btn)
        
        # Add a separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.VLine)
        separator1.setFrameShadow(QFrame.Shadow.Sunken)
        control_layout.addWidget(separator1)
        
        # Add create decision point button
        create_decision_btn = QPushButton("Create Decision Point")
        create_decision_btn.setIcon(icon_manager.get_icon("git-branch"))
        create_decision_btn.clicked.connect(self.create_decision_point)
        create_decision_btn.setToolTip("Create a new decision point")
        control_layout.addWidget(create_decision_btn)
        
        # Add create scene button
        create_scene_btn = QPushButton("Create Scene")
        create_scene_btn.setIcon(icon_manager.get_icon("movie"))
        create_scene_btn.clicked.connect(self.create_scene)
        create_scene_btn.setToolTip("Create a new scene")
        control_layout.addWidget(create_scene_btn)
        
        # Add a separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.VLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        control_layout.addWidget(separator2)
        
        # Toggle NSFW button
        self.nsfw_toggle = QCheckBox("Show NSFW Images")
        self.nsfw_toggle.setChecked(self.show_nsfw)
        self.nsfw_toggle.stateChanged.connect(self.on_nsfw_toggle)
        control_layout.addWidget(self.nsfw_toggle)
        
        # Toggle scene grouping
        self.scene_grouping_toggle = QCheckBox("Group by Scene")
        self.scene_grouping_toggle.setChecked(self.scene_grouping)
        self.scene_grouping_toggle.stateChanged.connect(self.on_scene_grouping_toggle)
        control_layout.addWidget(self.scene_grouping_toggle)
        
        # Add filter button
        filter_btn = QPushButton("Filters")
        filter_btn.setIcon(icon_manager.get_icon("filter"))
        filter_btn.clicked.connect(self.show_filters_dialog)
        control_layout.addWidget(filter_btn)
        
        # Add clear filters button
        clear_filters_btn = QPushButton("Clear Filters")
        clear_filters_btn.setIcon(icon_manager.get_icon("filter-off"))
        clear_filters_btn.clicked.connect(self.clear_filters)
        control_layout.addWidget(clear_filters_btn)
        
        # Add rebuild recognition database button
        rebuild_db_btn = QPushButton("Rebuild Recognition DB")
        rebuild_db_btn.setIcon(icon_manager.get_icon("database"))
        rebuild_db_btn.clicked.connect(self.rebuild_recognition_database)
        control_layout.addWidget(rebuild_db_btn)
        
        # Add control layout to main layout
        main_layout.addLayout(control_layout)
        
        # Create batch operations panel
        self.batch_operations_panel = QWidget()
        batch_layout = QVBoxLayout(self.batch_operations_panel)
        
        # Batch operations header
        batch_header = QLabel("Batch Operations")
        batch_header.setStyleSheet("font-weight: bold; font-size: 14px;")
        batch_layout.addWidget(batch_header)
        
        # Instructions label
        instructions_label = QLabel("Select images using checkboxes")
        batch_layout.addWidget(instructions_label)
        
        # Batch operations buttons
        batch_buttons_layout = QHBoxLayout()
        
        # Move to scene button
        move_to_scene_btn = QPushButton("Move to Scene...")
        move_to_scene_btn.setIcon(icon_manager.get_icon("folder-plus"))
        move_to_scene_btn.clicked.connect(self.on_move_to_scene)
        batch_buttons_layout.addWidget(move_to_scene_btn)
        
        # Batch character tagging button
        batch_tag_btn = QPushButton("Batch Tag Characters...")
        batch_tag_btn.setIcon(icon_manager.get_icon("users"))
        batch_tag_btn.clicked.connect(self.on_batch_character_tagging)
        batch_buttons_layout.addWidget(batch_tag_btn)
        
        # Batch context tagging button
        batch_context_btn = QPushButton("Batch Tag Contexts...")
        batch_context_btn.setIcon(icon_manager.get_icon("tag"))
        batch_context_btn.clicked.connect(self.on_batch_context_tagging)
        batch_buttons_layout.addWidget(batch_context_btn)
        
        batch_buttons_layout.addStretch()
        batch_layout.addLayout(batch_buttons_layout)
        
        # Add batch operations panel to main layout
        main_layout.addWidget(self.batch_operations_panel)
        
        # Create scroll area for thumbnails
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        # Create the thumbnails layout (grid layout for thumbnails)
        self.thumbnails_layout = QGridLayout()
        self.thumbnails_layout.setSpacing(10)
        self.thumbnails_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Create a widget to hold the thumbnails layout
        self.thumbnails_widget = QWidget()
        self.thumbnails_widget.setLayout(self.thumbnails_layout)
        
        # Add to scroll area
        self.scroll_area.setWidget(self.thumbnails_widget)
        
        # Add scroll area to main layout
        main_layout.addWidget(self.scroll_area)
        
        # Create status text to show filter information
        self.status_label = QLabel()
        main_layout.addWidget(self.status_label)
        
        # Set minimum size
        self.setMinimumSize(800, 600)
    
    def _create_nsfw_placeholder(self) -> QPixmap:
        """Create a placeholder pixmap for NSFW images.
        
        Returns:
            Placeholder pixmap
        """
        # Create a solid color pixmap with text
        pixmap = QPixmap(200, 180)
        pixmap.fill(QColor(30, 30, 30))
        
        # Add text
        painter = QPainter(pixmap)
        painter.setPen(QColor(200, 200, 200))
        painter.setFont(QFont("Arial", 14))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "NSFW Content\nHidden")
        painter.end()
        
        return pixmap
    
    def on_nsfw_toggle(self, state: int) -> None:
        """Handle NSFW toggle state change.
        
        Args:
            state: Checkbox state
        """
        print(f"NSFW toggle state changed to value: {state}")
        self.show_nsfw = (state == 2)  # Qt.CheckState.Checked is 2
        print(f"NSFW mode is now: {'ON' if self.show_nsfw else 'OFF'}")
        
        # Save the state to settings
        self.settings.setValue("gallery/show_nsfw", self.show_nsfw)
        
        # Update all thumbnails using the dedicated method
        self.update_thumbnail_visibility()
    
    def on_scene_grouping_toggle(self, state: int) -> None:
        """Handle scene grouping toggle state change.
        
        Args:
            state: Checkbox state
        """
        self.scene_grouping = (state == Qt.CheckState.Checked.value)
        
        # Save the state to settings
        self.settings.setValue("gallery/scene_grouping", self.scene_grouping)
        
        # Reload images with new grouping using progress indicator
        if self.story_id:
            self.refresh_gallery_with_progress()
    
    def update_thumbnail_visibility(self) -> None:
        """Update thumbnail visibility based on filters and settings."""
        print(f"Updating thumbnail visibility for {len(self.thumbnails)} thumbnails. NSFW mode: {self.show_nsfw}")
        
        for image_id, thumbnail in self.thumbnails.items():
            if self.show_nsfw:
                # If NSFW mode is on, set all thumbnails to NSFW
                self.set_thumbnail_nsfw(thumbnail)
            else:
                # Otherwise, restore normal images
                self.set_thumbnail_normal(thumbnail, image_id)
            
            # Make sure the widget is visible and properly redrawn
            thumbnail.setVisible(True)
            thumbnail.update()
    
    def set_thumbnail_nsfw(self, thumbnail: ThumbnailWidget) -> None:
        """Set a thumbnail to show the NSFW placeholder.
        
        Args:
            thumbnail: Thumbnail widget to update
        """
        # Make sure we have a placeholder pixmap
        if not hasattr(self, 'nsfw_placeholder') or self.nsfw_placeholder is None:
            self.nsfw_placeholder = self._create_nsfw_placeholder()
        
        # Scale the placeholder pixmap
        scaled_pixmap = self.nsfw_placeholder.scaled(
            QSize(170, 150),  # Increased from 180, 150
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Use the thumbnail's update_pixmap method
        thumbnail.update_pixmap(self.nsfw_placeholder)
        
        # Mark as NSFW
        thumbnail.is_nsfw = True
        
        # Hide quick event text
        thumbnail.quick_event_label.hide()
    
    def set_thumbnail_normal(self, thumbnail: ThumbnailWidget, image_id: int) -> None:
        """Set a thumbnail back to its normal image.
        
        Args:
            thumbnail: Thumbnail widget to update
            image_id: ID of the image
        """
        # Get the original pixmap path from database
        cursor = self.db_conn.cursor()
        cursor.execute(
            "SELECT filename, path FROM images WHERE id = ?",
            (image_id,)
        )
        image = cursor.fetchone()
        
        if image:
            thumbnails_folder = os.path.join(os.path.dirname(image['path']), "thumbnails")
            thumbnail_path = os.path.join(thumbnails_folder, image['filename'])
            
            if os.path.exists(thumbnail_path):
                # Load the original thumbnail
                pixmap = QPixmap(thumbnail_path)
                if not pixmap.isNull():
                    # Update the thumbnail
                    thumbnail.update_pixmap(pixmap)
                    
                    # Mark as not NSFW
                    thumbnail.is_nsfw = False
                    
                    # Set quick event text
                    self._set_thumbnail_quick_event_text(thumbnail, image_id)
                    return
        
        # If we got here, we couldn't restore the normal image
        # Get the image from the images list
        image_data = next((img for img in self.images if img["id"] == image_id), None)
        if image_data:
            # Get a new pixmap (will handle errors internally)
            pixmap = self._get_image_thumbnail_pixmap(image_data)
            thumbnail.update_pixmap(pixmap)
            
            # Mark as not NSFW
            thumbnail.is_nsfw = False
            
            # Set quick event text
            self._set_thumbnail_quick_event_text(thumbnail, image_id)
    
    def _set_thumbnail_quick_event_text(self, thumbnail: ThumbnailWidget, image_id: int) -> None:
        """Set quick event text on a thumbnail if any exists.
        
        Args:
            thumbnail: Thumbnail widget to update
            image_id: ID of the image
        """
        # Get quick events for this image
        quick_events = get_image_quick_events(self.db_conn, image_id)
        
        if quick_events:
            # Use the first quick event as the thumbnail text
            quick_event = quick_events[0]
            
            # Get all characters for this story to resolve references properly
            characters = get_story_characters(self.db_conn, self.story_id)
            
            # Format the text
            from app.utils.character_references import convert_char_refs_to_mentions
            display_text = convert_char_refs_to_mentions(quick_event["text"], characters)
            
            # Set on the thumbnail
            thumbnail.set_quick_event_text(display_text)
        else:
            # No quick events
            thumbnail.set_quick_event_text("")
    
    def _set_thumbnail_quick_event_text_cached(self, thumbnail: ThumbnailWidget, image_id: int) -> None:
        """Set quick event text on a thumbnail using cached data.
        
        Args:
            thumbnail: Thumbnail widget to update
            image_id: ID of the image
        """
        # Get quick events for this image from cache
        quick_events = self.image_quick_events_cache.get(image_id, [])
        
        if quick_events:
            # Use the first quick event as the thumbnail text
            quick_event = quick_events[0]
            
            # Format the text using cached characters
            from app.utils.character_references import convert_char_refs_to_mentions
            characters = list(self.story_characters.values())
            display_text = convert_char_refs_to_mentions(quick_event["text"], characters)
            
            # Set on the thumbnail
            thumbnail.set_quick_event_text(display_text)
        else:
            # No quick events
            thumbnail.set_quick_event_text("")
    
    def clear_thumbnails(self) -> None:
        """Clear all thumbnails from the display."""
        # First, delete all thumbnail widgets
        for thumbnail in self.thumbnails.values():
            # Remove from layout
            self.thumbnails_layout.removeWidget(thumbnail)
            # Delete the widget
            thumbnail.deleteLater()
        
        # Clear the dictionary and pixmap cache
        self.thumbnails.clear()
        self.pixmap_cache.clear()
        
        # Clear selected images set
        self.selected_images.clear()
    
    def clear_thumbnails_preserve_cache(self) -> None:
        """Clear thumbnails but preserve data caches for performance."""
        # First, delete all thumbnail widgets
        for thumbnail in self.thumbnails.values():
            # Remove from layout
            self.thumbnails_layout.removeWidget(thumbnail)
            # Delete the widget
            thumbnail.deleteLater()
        
        # Clear the dictionary but preserve caches
        self.thumbnails.clear()
        # Don't clear pixmap_cache, story_characters, image_character_tags_cache, image_quick_events_cache
        
        # Clear selected images set
        self.selected_images.clear()
    
    def refresh_single_image(self, image_id: int) -> None:
        """Refresh a single image's data and thumbnail.
        
        Args:
            image_id: ID of the image to refresh
        """
        # Update caches for this specific image
        self.image_character_tags_cache[image_id] = get_image_character_tags(self.db_conn, image_id)
        self.image_quick_events_cache[image_id] = get_image_quick_events(self.db_conn, image_id)
        
        # Update thumbnail if it exists
        if image_id in self.thumbnails:
            thumbnail = self.thumbnails[image_id]
            self._set_thumbnail_quick_event_text_cached(thumbnail, image_id)
            
            # Update thumbnail visibility
            if self.show_nsfw:
                self.set_thumbnail_nsfw(thumbnail)
            else:
                self.set_thumbnail_normal(thumbnail, image_id)
    
    def set_story(self, story_id: int, story_data: Dict[str, Any]) -> None:
        """Set the story to display in the gallery.
        
        Args:
            story_id: ID of the story
            story_data: Dictionary containing story data
        """
        # Store story data
        self.story_id = story_id
        self.story_data = story_data
        
        # Clear existing thumbnails
        self.clear_thumbnails()
        
        # Update window title
        if self.parent() and hasattr(self.parent(), 'setWindowTitle'):
            title = f"Gallery - {story_data.get('title', 'Untitled Story')}"
            self.parent().setWindowTitle(title)
        
        # Load images for this story with progress indicator
        self.refresh_gallery_with_progress()
    
    def load_images(self) -> None:
        """Load and display images for the current story."""
        if not self.story_id:
            return
        
        # Get images from database
        cursor = self.db_conn.cursor()
        
        query = """
            SELECT id, title, path, filename, created_at, width, height, is_featured, story_id
            FROM images
            WHERE story_id = ?
            ORDER BY created_at DESC
        """
        
        cursor.execute(query, (self.story_id,))
        
        # Convert to list of dicts
        images = []
        for row in cursor.fetchall():
            images.append({
                "id": row[0],
                "title": row[1],
                "path": row[2],
                "filename": row[3],  # Include the filename in the dictionary
                "timestamp": row[4],  # We'll keep the name timestamp in our dict for compatibility
                "width": row[5],
                "height": row[6],
                "is_nsfw": False,  # Using is_featured as is_nsfw is not available
                "story_id": row[8]
            })
        
        # Store images
        self.images = images
        
        # Pre-load all data in batch for better performance
        self._preload_gallery_data(images)
        
        # Display images based on grouping option
        if self.scene_grouping:
            self._display_images_with_scene_grouping(images)
        else:
            self._display_images_classic_view(images)
        
        # Update filter status
        self.update_filter_status()
    
    def _preload_gallery_data(self, images: List[Dict[str, Any]]) -> None:
        """Pre-load all data needed for gallery display in batch queries.
        
        Args:
            images: List of image data dictionaries
        """
        if not images:
            return
        
        image_ids = [img["id"] for img in images]
        
        # Load story characters once
        self.story_characters = {char["id"]: char for char in get_story_characters(self.db_conn, self.story_id)}
        
        # Batch load character tags for all images
        self.image_character_tags_cache = get_images_character_tags_batch(self.db_conn, image_ids)
        
        # Batch load quick events for all images
        self.image_quick_events_cache = get_images_quick_events_batch(self.db_conn, image_ids)
    
    def _display_images_classic_view(self, images: List[Dict[str, Any]]) -> None:
        """Display images in a standard grid layout without scene grouping.
        
        Args:
            images: List of image data dictionaries
        """
        # Clear existing thumbnails
        self.clear_thumbnails()
        
        # Filter images based on character filters
        filtered_images = self._filter_images_by_character(images)
        
        # Display all filtered images in a grid
        current_row = 0
        current_col = 0
        columns = 4  # Number of columns in the grid
        
        for image in filtered_images:
            # Get the pixmap for this image
            pixmap = self._get_image_thumbnail_pixmap(image)
            
            # Create a thumbnail widget
            thumbnail = ThumbnailWidget(image["id"], pixmap, image.get("title"))
            
            # Connect signals
            thumbnail.clicked.connect(self.on_thumbnail_clicked)
            thumbnail.delete_requested.connect(self.on_delete_image)
            thumbnail.checkbox_toggled.connect(self.on_thumbnail_checkbox_toggled)
            
            # Add to layout
            self.thumbnails_layout.addWidget(thumbnail, current_row, current_col)
            
            # Add to thumbnails dictionary
            self.thumbnails[image["id"]] = thumbnail
            
            # Set quick event text using cached data
            self._set_thumbnail_quick_event_text_cached(thumbnail, image["id"])
            
            # Increment column
            current_col += 1
            
            # Move to next row if we've filled a row
            if current_col >= columns:
                current_col = 0
                current_row += 1
        
        # Update visibility based on nsfw setting
        self.update_thumbnail_visibility()
    
    def _display_images_with_scene_grouping(self, images: List[Dict[str, Any]]) -> None:
        """Display images grouped by scene.
        
        Args:
            images: List of image data dictionaries
        """
        # Clear existing thumbnails
        self.clear_thumbnails()
        
        if not images:
            return
        
        # Convert images from sqlite3.Row objects to dictionaries
        images_dict = []
        for image in images:
            image_dict = dict(image)
            images_dict.append(image_dict)
        
        # Replace the original images list with our dictionary version
        images = images_dict
        
        # Get all scenes in this story
        cursor = self.db_conn.cursor()
        cursor.execute(
            "SELECT id, title, sequence_number FROM events WHERE story_id = ? AND event_type = 'SCENE' ORDER BY sequence_number DESC",
            (self.story_id,)
        )
        scenes = cursor.fetchall()
        
        # First, obtain creation timestamps for all images
        for image in images:
            cursor.execute(
                "SELECT created_at FROM images WHERE id = ?",
                (image['id'],)
            )
            result = cursor.fetchone()
            if result:
                image['created_at'] = result['created_at']
            else:
                image['created_at'] = '1970-01-01 00:00:00'  # Default fallback
        
        # Sort images by creation timestamp (newest first)
        images.sort(key=lambda x: x['created_at'], reverse=True)
        
        # If we have no scenes defined, treat all images as orphans
        if not scenes:
            # Apply character filters to all images
            filtered_images = self._filter_images_by_character(images)
            
            row = 0
            separator = SeparatorWidget("Ungrouped")
            self.thumbnails_layout.addWidget(separator, row, 0, 1, 4)  # Span all columns
            row += 1
            
            self._display_image_list(filtered_images, row)
            return
        
        # Get all quick event associations for all images
        image_ids = [image['id'] for image in images]
        image_quick_events = {}
        for image_id in image_ids:
            quick_events = get_image_quick_events(self.db_conn, image_id)
            if quick_events:
                image_quick_events[image_id] = quick_events
        
        # Find scenes for each image through:
        # 1. Quick events associated with the image that are in scenes
        # 2. Direct image-scene associations
        image_scenes = {}
        
        # First, process indirect associations via quick events
        for image_id, quick_events in image_quick_events.items():
            for quick_event in quick_events:
                scenes_for_quick_event = get_quick_event_scenes(self.db_conn, quick_event['id'])
                if scenes_for_quick_event:
                    # Associate image with all scenes containing the quick event
                    if image_id not in image_scenes:
                        image_scenes[image_id] = set()
                    for scene in scenes_for_quick_event:
                        image_scenes[image_id].add((scene['id'], scene['title'], scene['sequence_number']))
        
        # Second, process direct image-scene associations
        for image_id in image_ids:
            direct_scenes = get_image_scenes(self.db_conn, image_id)
            if direct_scenes:
                if image_id not in image_scenes:
                    image_scenes[image_id] = set()
                for scene in direct_scenes:
                    image_scenes[image_id].add((scene['id'], scene['title'], scene['sequence_number']))
        
        # Apply character filters to all images first
        filtered_images = self._filter_images_by_character(images)
        
        # Group filtered images by scene
        scene_images = {}
        orphan_images = []
        
        for image in filtered_images:
            image_id = image['id']
            if image_id in image_scenes:
                for scene_id, scene_title, sequence_number in image_scenes[image_id]:
                    if scene_id not in scene_images:
                        scene_images[scene_id] = {
                            'title': scene_title,
                            'sequence_number': sequence_number,
                            'images': [],
                            # Get the newest creation timestamp for any quick event in this scene
                            'newest_timestamp': self._get_scene_newest_timestamp(scene_id)
                        }
                    scene_images[scene_id]['images'].append(image)
            else:
                # Image not associated with a scene
                orphan_images.append(image)
        
        # If we have no images in any scenes, treat all filtered images as orphans
        if not scene_images:
            row = 0
            separator = SeparatorWidget("Ungrouped")
            self.thumbnails_layout.addWidget(separator, row, 0, 1, 4)  # Span all columns
            row += 1
            
            self._display_image_list(orphan_images, row)
            return
        
        # Now create a chronological display order with scenes and ungrouped images interspersed
        # Create a new display order with scenes only
        display_order = []
        
        # Sort scenes by sequence number (highest first = newest scenes first)
        sorted_scenes = sorted(
            scene_images.items(),
            key=lambda x: x[1]['sequence_number'],
            reverse=True
        )
        
        # Track scene IDs to prevent duplicates
        added_scene_ids = set()
        
        # Add all scenes in order of sequence number (highest first)
        for scene_id, scene_data in sorted_scenes:
            # Only add each scene ID once to prevent duplicates
            if scene_id not in added_scene_ids:
                display_order.append(('scene', scene_id))
                added_scene_ids.add(scene_id)
        
        # Now, place unassigned images in a separate group at the top
        if orphan_images:
            # Sort orphaned images by creation timestamp (newest first)
            orphan_images.sort(key=lambda x: x['created_at'], reverse=True)
            # Insert the ungrouped section at the beginning of display_order
            display_order.insert(0, ('ungrouped', orphan_images))
        
        # Now display everything according to our calculated order
        row = 0
        
        # Clear any lingering layout spacers or empty cells
        while self.thumbnails_layout.count() > 0:
            item = self.thumbnails_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        for item_type, item_data in display_order:
            if item_type == 'scene':
                scene_id = item_data
                scene_data = scene_images[scene_id]
                
                # Add a separator for this scene
                separator = SeparatorWidget(scene_data['title'])
                self.thumbnails_layout.addWidget(separator, row, 0, 1, 4)  # Span all columns
                
                row += 1
                
                # Only proceed if there are images to display
                if scene_data['images']:
                    # Display this scene's images and get the next row
                    next_row = self._display_image_list(scene_data['images'], row)
                    
                    # Update row to the row after the last image
                    row = next_row
                
                # No need for extra spacing here - _display_image_list already returns the correct next row
            
            elif item_type == 'ungrouped':
                ungrouped_images = item_data
                if ungrouped_images:
                    # Add separator for ungrouped images
                    separator = SeparatorWidget("Ungrouped")
                    self.thumbnails_layout.addWidget(separator, row, 0, 1, 4)  # Span all columns
                    
                    row += 1
                    
                    # Display ungrouped images and get the next row
                    next_row = self._display_image_list(ungrouped_images, row)
                    
                    # Update row to the row after the last image 
                    row = next_row
                
                # No need for extra spacing here - _display_image_list already returns the correct next row
        
        # Ensure columns have equal width
        for col in range(4):
            self.thumbnails_layout.setColumnStretch(col, 1)
        
        # Update visibility based on nsfw setting
        self.update_thumbnail_visibility()
    
    def _display_image_list(self, images: List[Dict[str, Any]], start_row: int) -> int:
        """Display a list of images in the gallery.
        
        Args:
            images: List of image data dictionaries
            start_row: Row in the grid layout to start displaying from
            
        Returns:
            Next row number after the displayed images
        """
        current_row = start_row
        cols = 4  # Number of thumbnails per row
        
        for i, image in enumerate(images):
            col = i % cols
            row = current_row + (i // cols)
            
            image_id = image['id']
            
            # Get thumbnail pixmap
            pixmap = self._get_image_thumbnail_pixmap(image)
            
            # Create thumbnail widget
            thumbnail = ThumbnailWidget(image_id, pixmap)
            thumbnail.clicked.connect(lambda tid=image_id: self.on_thumbnail_clicked(tid))
            thumbnail.delete_requested.connect(lambda tid=image_id: self.on_delete_image(tid))
            thumbnail.checkbox_toggled.connect(self.on_thumbnail_checkbox_toggled)
            
            # Add quick event text if any
            self._set_thumbnail_quick_event_text_cached(thumbnail, image_id)
            
            # Add to thumbnails dictionary
            self.thumbnails[image_id] = thumbnail
            
            # Add to layout
            self.thumbnails_layout.addWidget(thumbnail, row, col)
        
        # Return the next row after the last one we used
        return current_row + ((len(images) - 1) // cols) + 1
    
    def _get_image_thumbnail_pixmap(self, image: Dict[str, Any]) -> QPixmap:
        """Get the thumbnail pixmap for an image.
        
        Args:
            image: Image data dictionary
            
        Returns:
            QPixmap object of the thumbnail, possibly a placeholder if in NSFW mode
        """
        # Check if we have a cached pixmap
        image_id = image["id"]
        if image_id in self.pixmap_cache:
            return self.pixmap_cache[image_id]
        
        # Handle NSFW mode
        if image.get("is_nsfw", False) and not self.show_nsfw:
            # Use NSFW placeholder for NSFW images when not showing NSFW content
            if not hasattr(self, 'nsfw_placeholder') or self.nsfw_placeholder is None:
                self.nsfw_placeholder = self._create_nsfw_placeholder()
            placeholder = self.nsfw_placeholder
            self.pixmap_cache[image_id] = placeholder
            return placeholder
        
        # Get image details
        filename = image.get('filename')
        img_folder = image.get('path')
        story_id = image.get('story_id')
        
        if not filename or not img_folder or not story_id:
            logging.error(f"Missing path, filename, or story_id for image {image_id}")
            placeholder = self._create_placeholder_pixmap(image)
            self.pixmap_cache[image_id] = placeholder
            return placeholder
        
        try:
            # Get story data from database to determine the proper folder structure
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT * FROM stories WHERE id = ?", (story_id,))
            story_data = cursor.fetchone()
            
            if not story_data:
                logging.error(f"Story data not found for image {image_id}")
                placeholder = self._create_placeholder_pixmap(image)
                self.pixmap_cache[image_id] = placeholder
                return placeholder
            
            # Get folder paths
            from app.db_sqlite import get_story_folder_paths
            folder_paths = get_story_folder_paths(dict(story_data))
            
            # Get paths to original image and thumbnail
            original_path = os.path.join(folder_paths['images_folder'], filename)
            thumbnail_path = os.path.join(folder_paths['thumbnails_folder'], filename)
            
            # logging.debug(f"Looking for thumbnail at: {thumbnail_path}")
            
            # Check if thumbnail exists, if not, create the directories and generate it
            if not os.path.exists(thumbnail_path):
                logging.debug(f"Thumbnail not found, attempting to generate from original")
                
                # Ensure thumbnails directory exists
                os.makedirs(folder_paths['thumbnails_folder'], exist_ok=True)
                
                if os.path.exists(original_path):
                    # Load the original image
                    original_image = QImage(original_path)
                    if not original_image.isNull():
                        # Generate and save thumbnail
                        thumbnail = self._generate_thumbnail(original_image)
                        
                        # Save the thumbnail
                        if thumbnail.save(thumbnail_path, "PNG"):
                            logging.debug(f"Generated and saved new thumbnail to: {thumbnail_path}")
                            
                            # Use the newly generated thumbnail
                            pixmap = QPixmap.fromImage(thumbnail)
                            self.pixmap_cache[image_id] = pixmap
                            return pixmap
                        else:
                            logging.error(f"Failed to save thumbnail to: {thumbnail_path}")
                    else:
                        logging.error(f"Failed to load original image: {original_path}")
                else:
                    logging.error(f"Original image not found: {original_path}")
                    
                    # Try alternative paths (legacy support)
                    alt_path = os.path.join(img_folder, filename)
                    if os.path.exists(alt_path) and alt_path != original_path:
                        logging.debug(f"Trying alternative path: {alt_path}")
                        original_image = QImage(alt_path)
                        if not original_image.isNull():
                            # Generate and save thumbnail
                            thumbnail = self._generate_thumbnail(original_image)
                            
                            # Save the thumbnail
                            if thumbnail.save(thumbnail_path, "PNG"):
                                logging.debug(f"Generated and saved new thumbnail to: {thumbnail_path}")
                                
                                # Use the newly generated thumbnail
                                pixmap = QPixmap.fromImage(thumbnail)
                                self.pixmap_cache[image_id] = pixmap
                                return pixmap
                            else:
                                logging.error(f"Failed to save thumbnail to: {thumbnail_path}")
                        else:
                            logging.error(f"Failed to load image from alternative path: {alt_path}")
            else:
                # Thumbnail exists, load it
                # logging.debug(f"Found existing thumbnail at: {thumbnail_path}")
                pixmap = QPixmap(thumbnail_path)
                if not pixmap.isNull():
                    self.pixmap_cache[image_id] = pixmap
                    return pixmap
                else:
                    logging.error(f"Failed to load thumbnail image: {thumbnail_path}")
        except Exception as e:
            logging.exception(f"Error loading thumbnail for image {image_id}: {str(e)}")
        
        # If we get here, we couldn't load a thumbnail
        placeholder = self._create_placeholder_pixmap(image)
        self.pixmap_cache[image_id] = placeholder
        return placeholder
    
    def _create_placeholder_pixmap(self, image: Dict[str, Any]) -> QPixmap:
        """Create a placeholder pixmap for an image that couldn't be loaded.
        
        Args:
            image: Image data dictionary
            
        Returns:
            Placeholder pixmap
        """
        # Create a placeholder pixmap
        pixmap = QPixmap(160, 120)
        pixmap.fill(QColor(50, 50, 50))
        
        # Draw text on the pixmap if we have a title
        if image.get("title"):
            painter = QPainter(pixmap)
            painter.setPen(Qt.GlobalColor.white)
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, image["title"])
            painter.end()
        else:
            # Or use the filename
            painter = QPainter(pixmap)
            painter.setPen(Qt.GlobalColor.white)
            text = image.get("filename", "Unknown Image")
            if len(text) > 20:
                text = text[:17] + "..."
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)
            painter.end()
        
        # Cache the pixmap
        self.pixmap_cache[image.get("id", 0)] = pixmap
        
        return pixmap
    
    def keyPressEvent(self, event) -> None:
        """Handle key press events.
        
        Args:
            event: Key event
        """
        # Handle Ctrl+V to paste an image
        if event.key() == Qt.Key.Key_V and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.paste_image()
        else:
            # Pass to parent
            super().keyPressEvent(event)
    
    def paste_image(self) -> None:
        """Paste an image from the clipboard."""
        # Get the clipboard
        clipboard = QApplication.clipboard()
        
        # Check if the clipboard has an image
        mime_data = clipboard.mimeData()
        
        if mime_data.hasImage():
            # Get the image from the clipboard
            image = clipboard.image()
            
            if not image.isNull():
                # Save the image to the story
                self.save_image_to_story(image)
            else:
                self.show_error("Clipboard Error", "Could not get valid image from clipboard")
        elif mime_data.hasUrls():
            # Check if it's a local file URL
            urls = mime_data.urls()
            
            if urls and urls[0].isLocalFile():
                # Get the local file path
                file_path = urls[0].toLocalFile()
                
                # Check if it's an image file
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    # Load the image
                    image = QImage(file_path)
                    
                    if not image.isNull():
                        # Save the image to the story
                        self.save_image_to_story(image)
                    else:
                        self.show_error("Image Error", f"Could not load image from {file_path}")
                else:
                    self.show_error("File Type Error", "The file in the clipboard is not a supported image format")
            else:
                # It's a remote URL
                for url in urls:
                    # Check if it's an image URL
                    url_str = url.toString()
                    if any(url_str.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']):
                        # Download the image
                        self._download_image(url)
                        break
                else:
                    # No valid image URLs
                    self.debug_clipboard()
        elif mime_data.hasHtml():
            # Check the HTML for image tags
            html = mime_data.html()
            urls = self._extract_image_urls_from_html(html)
            
            if urls:
                # Download the first image
                url = QUrl(urls[0])
                self._download_image(url)
            else:
                # No image URLs found
                self.debug_clipboard()
        else:
            # No image in clipboard
            self.debug_clipboard()
    
    def _download_image(self, url: QUrl) -> None:
        """Download an image from a URL.
        
        Args:
            url: URL to download
        """
        # Create a progress dialog
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("Downloading Image")
        msg_box.setText(f"Downloading image from {url.toString()}")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Cancel)
        msg_box.setDefaultButton(QMessageBox.StandardButton.Cancel)
        
        # Start the request
        request = QNetworkRequest(url)
        reply = self.network_manager.get(request)
        
        # Connect signals
        reply.finished.connect(lambda: self._handle_network_reply(reply, msg_box))
        
        # Show the dialog
        msg_box.exec()
        
        # If the dialog is closed, abort the request
        if reply.isRunning():
            reply.abort()
    
    def _handle_network_reply(self, reply, msg_box):
        """Handle a completed network request.
        
        Args:
            reply: Network reply
            msg_box: Message box dialog
        """
        # Close the message box
        msg_box.close()
        
        # Check for errors
        if reply.error() != QNetworkReply.NetworkError.NoError:
            self.show_error("Download Error", f"Failed to download image: {reply.errorString()}")
            reply.deleteLater()
            return
        
        # Read the image data
        image_data = reply.readAll()
        
        # Create an image from the data
        image = QImage.fromData(image_data)
        
        if image.isNull():
            self.show_error("Image Error", "Could not create image from downloaded data")
        else:
            # Save the image to the story
            self.save_image_to_story(image)
        
        # Clean up
        reply.deleteLater()
    
    def import_image(self) -> None:
        """Open a file dialog to import an image."""
        # Get file path from dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Image",
            "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        
        if not file_path:
            return
        
        # Load the image
        image = QImage(file_path)
        
        if image.isNull():
            self.show_error("Image Error", f"Could not load image from {file_path}")
            return
        
        # Save the image to the story
        self.save_image_to_story(image)
    
    def save_image_to_story(self, image: QImage) -> None:
        """Save an image to the current story.
        
        Args:
            image: Image to save
        """
        if not self.story_id:
            self.show_error("Error", "No story selected")
            return
        
        try:
            # Get the story data
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT * FROM stories WHERE id = ?", (self.story_id,))
            story_data = dict(cursor.fetchone())
            
            if not story_data:
                self.show_error("Error", "Story data not found")
                return
            
            # Get folder paths using the utility function
            from app.db_sqlite import get_story_folder_paths, ensure_story_folders_exist
            
            # Ensure all story folders exist
            ensure_story_folders_exist(story_data)
            
            # Get paths
            folder_paths = get_story_folder_paths(story_data)
            images_folder = folder_paths['images_folder']
            thumbnails_folder = folder_paths['thumbnails_folder']
            
            # Create folders if they don't exist
            os.makedirs(images_folder, exist_ok=True)
            os.makedirs(thumbnails_folder, exist_ok=True)
            
            # Generate a unique file name
            timestamp = time.strftime("%Y%m%d%H%M%S")
            random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            file_name = f"img_{timestamp}_{random_string}.png"
            
            # Define full file paths
            image_path = os.path.join(images_folder, file_name)
            thumbnail_path = os.path.join(thumbnails_folder, file_name)
            
            # Generate thumbnail
            thumbnail_image = self._generate_thumbnail(image)
            
            # Save the full image
            if not image.save(image_path, "PNG"):
                self.show_error("Save Error", "Could not save image to file")
                return
            
            # Save the thumbnail
            if not thumbnail_image.save(thumbnail_path, "PNG"):
                logging.warning(f"Could not save thumbnail to {thumbnail_path}")
            
            # Create timestamps
            now = datetime.now().isoformat()
            
            # Insert into database with the columns we actually have
            query = """
                INSERT INTO images (story_id, title, path, created_at, updated_at, width, height, is_featured, filename)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(
                query,
                (
                    self.story_id,
                    "Imported Image",    # title
                    images_folder,       # path (store folder path)
                    now,                 # created_at
                    now,                 # updated_at
                    image.width(),       # width
                    image.height(),      # height
                    0,                   # is_featured (not NSFW)
                    file_name            # filename
                )
            )
            
            # Get the new image ID
            image_id = cursor.lastrowid
            
            # Commit changes
            self.db_conn.commit()
            
            # Add the new image to our list
            new_image = {
                "id": image_id,
                "title": "Imported Image",
                "path": images_folder,
                "timestamp": now,
                "width": image.width(),
                "height": image.height(),
                "is_nsfw": False,
                "story_id": self.story_id,
                "filename": file_name
            }
            
            self.images.insert(0, new_image)  # Add to start (newest)
            
            # Run character recognition on the image
            # Show a progress dialog for the longer operation
            progress_dialog = QProgressDialog(
                "Analyzing image for character recognition...",
                "Cancel", 0, 100, self
            )
            progress_dialog.setWindowTitle("Character Recognition")
            progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            progress_dialog.setMinimumDuration(500)  # Show after 500ms delay
            progress_dialog.setValue(0)
            
            # Allow some processing before showing the dialog
            QApplication.processEvents()
            
            # Open the RegionSelectionDialog for character recognition
            from app.views.gallery.dialogs.region_selection import RegionSelectionDialog
            region_dialog = RegionSelectionDialog(self.db_conn, image, self.story_id, self, image_id=image_id)
            
            progress_dialog.setValue(100)
            progress_dialog.close()
            
            # Show the dialog - this will block until it's closed
            if region_dialog.exec():
                # Get selected character data and process it if needed
                try:
                    # Get the data returned from the dialog
                    result_data = region_dialog.get_selected_character_data()
                    if result_data:
                        # Process character tags and quick event information
                        character_data = result_data.get('characters', [])
                        quick_event_id = result_data.get('quick_event_id')
                        
                        # Process character tags
                        if character_data:
                            from app.db_sqlite import add_character_tag_to_image
                            for character in character_data:
                                character_id = character['character_id']
                                region = character['region']
                                
                                # Add the character tag to the image with the region coordinates
                                add_character_tag_to_image(
                                    self.db_conn,
                                    image_id,
                                    character_id,
                                    region['x'],  # Center X (normalized)
                                    region['y'],  # Center Y (normalized)
                                    region['width'],  # Width (normalized)
                                    region['height'],  # Height (normalized),
                                    character.get('description', "Character tag added")
                                )
                        
                        # Associate quick event if one was selected
                        if quick_event_id:
                            self.associate_quick_event_with_image(image_id, quick_event_id)
                except Exception as e:
                    self.show_error("Error", f"Failed to process character recognition data: {str(e)}")
                    logging.exception(f"Error processing character recognition data: {e}")
            
            # Reload images
            self.load_images()
        except Exception as e:
            self.show_error("Save Error", f"Could not save image: {str(e)}")
            logging.exception(f"Error saving image to story: {e}")
    
    def associate_quick_event_with_image(self, image_id: int, quick_event_id: int) -> None:
        """Associate a quick event with an image.
        
        Args:
            image_id: ID of the image
            quick_event_id: ID of the quick event
        """
        associate_quick_event_with_image(self.db_conn, quick_event_id, image_id)
        
        # Update the thumbnail if it exists
        if image_id in self.thumbnails:
            self._set_thumbnail_quick_event_text(self.thumbnails[image_id], image_id)
    
    def _generate_thumbnail(self, image: QImage, max_dimension: int = 320) -> QImage:
        """Generate a thumbnail from an image.
        
        Args:
            image: Source image
            max_dimension: Maximum dimension for the thumbnail
            
        Returns:
            Thumbnail image
        """
        # Calculate scale factor to fit within max_dimension
        width = image.width()
        height = image.height()
        
        if width <= max_dimension and height <= max_dimension:
            # Image is already small enough
            return image.copy()
        
        # Scale to fit in max_dimension x max_dimension box while preserving aspect ratio
        if width > height:
            # Landscape orientation
            scale_factor = max_dimension / width
        else:
            # Portrait orientation
            scale_factor = max_dimension / height
        
        # Calculate new dimensions
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        
        # Create the thumbnail (use smooth transformation for better quality)
        return image.scaled(
            new_width,
            new_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
    
    def on_thumbnail_clicked(self, image_id: int) -> None:
        """Handle thumbnail click event.
        
        Args:
            image_id: ID of the clicked image
        """
        try:
            # Get complete image data directly from the database
            cursor = self.db_conn.cursor()
            cursor.execute('SELECT * FROM images WHERE id = ?', (image_id,))
            
            image_data = cursor.fetchone()
            
            if not image_data:
                self.show_error("Image Not Found", f"Image with ID {image_id} not found.")
                return
            
            # Convert to a dictionary
            image_data = dict(image_data)
            
            # Get the image path
            image_path = os.path.join(image_data['path'], image_data['filename'])
            
            if not os.path.exists(image_path):
                self.show_error("Image Not Found", f"Image file not found at {image_path}")
                return
            
            # Load image
            pixmap = QPixmap(image_path)
            
            if pixmap.isNull():
                self.show_error("Image Load Failed", f"Failed to load image from {image_path}")
                return
            
            # Get all image IDs in the gallery for navigation
            gallery_images = [img["id"] for img in self.images]
            
            # Find the index of the current image
            try:
                current_index = gallery_images.index(image_id)
            except ValueError:
                current_index = -1
            
            # Create and show the dialog
            dialog = ImageDetailDialog(
                self.db_conn,
                image_id,
                image_data,
                pixmap,
                self,
                gallery_images,
                current_index
            )
            
            dialog.exec()
            
            # Use incremental refresh instead of full reload for better performance
            self.refresh_single_image(image_id)
            
        except Exception as e:
            self.show_error("Error", f"An error occurred: {str(e)}")
    
    def get_image_pixmap(self, image_id: int) -> QPixmap:
        """Get the full-size pixmap for an image.
        
        Args:
            image_id: ID of the image
            
        Returns:
            QPixmap of the image
        """
        try:
            # Get image data directly from the database
            cursor = self.db_conn.cursor()
            cursor.execute('SELECT path, filename FROM images WHERE id = ?', (image_id,))
            
            result = cursor.fetchone()
            
            if not result:
                logging.error(f"Image with ID {image_id} not found in database")
                return QPixmap()
            
            # Get the image path
            file_path = result[0]
            filename = result[1]
            
            if not file_path or not filename:
                logging.error(f"Image {image_id} has NULL path or filename in database")
                return QPixmap()
                
            # Construct full path
            full_path = os.path.join(file_path, filename)
            
            if not os.path.exists(full_path):
                logging.error(f"Image file not found at {full_path}")
                return QPixmap()
            
            # Load the image from file
            pixmap = QPixmap(full_path)
            
            if pixmap.isNull():
                logging.error(f"Failed to load image from {full_path}")
                
            return pixmap
            
        except Exception as e:
            logging.exception(f"Error loading image pixmap: {str(e)}")
            return QPixmap()
    
    def get_image_data(self, image_id: int) -> Dict[str, Any]:
        """Get image data for an image.
        
        Args:
            image_id: ID of the image
            
        Returns:
            Dictionary with image data, or None if not found
        """
        return next((img for img in self.images if img["id"] == image_id), None)
    
    def on_thumbnail_context_menu(self, position: QPoint, thumbnail: ThumbnailWidget) -> None:
        """Show context menu for a thumbnail.
        
        Args:
            position: Position where to show the menu
            thumbnail: Thumbnail widget
        """
        image_id = thumbnail.image_id
        
        # Find the image data
        image_data = next((img for img in self.images if img["id"] == image_id), None)
        
        if not image_data:
            return
        
        # Create the menu
        menu = QMenu(self)
        
        # View action
        view_action = QAction("View Image", self)
        view_action.triggered.connect(lambda: self.on_thumbnail_clicked(image_id))
        menu.addAction(view_action)
        
        # Toggle NSFW action
        is_nsfw = image_data.get("is_nsfw", False)
        nsfw_action = QAction("Mark as Safe" if is_nsfw else "Mark as NSFW", self)
        nsfw_action.triggered.connect(lambda: self.toggle_image_nsfw(image_id))
        menu.addAction(nsfw_action)
        
        # Quick events submenu
        quick_events_menu = QMenu("Quick Events", self)
        
        add_quick_event_action = QAction("Add Quick Event", self)
        add_quick_event_action.triggered.connect(lambda: self.open_quick_event_dialog(image_id))
        quick_events_menu.addAction(add_quick_event_action)
        
        menu.addMenu(quick_events_menu)
        
        # Move to scene action
        scene_action = QAction("Move to Scene", self)
        scene_action.triggered.connect(self.on_move_to_scene)
        menu.addAction(scene_action)
        
        # Character recognition action
        recognition_action = QAction("Character Recognition", self)
        recognition_action.triggered.connect(lambda: self.on_recognize_characters(image_id))
        menu.addAction(recognition_action)
        
        # Delete action
        delete_action = QAction("Delete Image", self)
        delete_action.triggered.connect(lambda: self.on_delete_image(image_id))
        menu.addAction(delete_action)
        
        # Show the menu
        menu.exec(thumbnail.mapToGlobal(position))
    
    def open_quick_event_dialog(self, image_id: int) -> None:
        """Open the quick event dialog for an image.
        
        Args:
            image_id: ID of the image
        """
        # Find the image data
        image_data = next((img for img in self.images if img["id"] == image_id), None)
        
        if not image_data:
            self.show_error("Error", f"Image data not found for ID {image_id}")
            return
        
        # Get current quick events
        current_events = get_image_quick_events(self.db_conn, image_id)
        current_event_ids = [event["id"] for event in current_events]
        
        # Create and show the dialog
        dialog = QuickEventSelectionDialog(
            self.db_conn,
            self.story_id,
            image_id,
            current_event_ids,
            self
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get selected quick events
            selected_ids = dialog.get_selected_quick_event_ids()
            
            # Update associations in the database
            # First, remove all existing associations
            for event_id in current_event_ids:
                if event_id not in selected_ids:
                    remove_quick_event_image_association(self.db_conn, event_id, image_id)
            
            # Then add new associations
            for event_id in selected_ids:
                if event_id not in current_event_ids:
                    associate_quick_event_with_image(self.db_conn, event_id, image_id)
            
            # Update the thumbnail
            if image_id in self.thumbnails:
                self._set_thumbnail_quick_event_text(self.thumbnails[image_id], image_id)
    
    def on_delete_image(self, image_id: int) -> None:
        """Handle delete image action.
        
        Args:
            image_id: ID of the image to delete
        """
        # Find the image data
        image_data = next((img for img in self.images if img["id"] == image_id), None)
        
        if not image_data:
            self.show_error("Error", f"Image data not found for ID {image_id}")
            return
        
        # Ask for confirmation
        confirmation = QMessageBox.question(
            self,
            "Delete Image",
            "Are you sure you want to delete this image? This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirmation != QMessageBox.StandardButton.Yes:
            return
        
        # Delete the image file if it exists
        file_path = image_data.get("path")
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                # Log the error but continue with database deletion
                print(f"Error deleting image file: {e}")
        
        # Delete from database
        cursor = self.db_conn.cursor()
        
        # Delete related data first
        cursor.execute("DELETE FROM image_tags WHERE image_id = ?", (image_id,))
        cursor.execute("DELETE FROM quick_event_images WHERE image_id = ?", (image_id,))
        cursor.execute("DELETE FROM scene_images WHERE image_id = ?", (image_id,))
        
        # Then delete the image
        cursor.execute("DELETE FROM images WHERE id = ?", (image_id,))
        
        # Commit changes
        self.db_conn.commit()
        
        # Remove from our list
        self.images = [img for img in self.images if img["id"] != image_id]
        
        # Remove the thumbnail widget
        if image_id in self.thumbnails:
            # Remove from layout
            thumbnail = self.thumbnails[image_id]
            self.thumbnails_layout.removeWidget(thumbnail)
            
            # Delete the widget
            thumbnail.deleteLater()
            
            # Remove from dictionary
            del self.thumbnails[image_id]
        
        # Remove from pixmap cache
        if image_id in self.pixmap_cache:
            del self.pixmap_cache[image_id]
        
        # Remove from selected images
        if image_id in self.selected_images:
            self.selected_images.remove(image_id)
    
    def show_error(self, title: str, message: str) -> None:
        """Show an error message.
        
        Args:
            title: Error title
            message: Error message
        """
        QMessageBox.critical(self, title, message)
    
    def debug_clipboard(self) -> None:
        """Debug clipboard contents."""
        # Get the clipboard
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        # Build a debug message
        formats = mime_data.formats()
        debug_text = "Clipboard content types:\n"
        
        for fmt in formats:
            debug_text += f"- {fmt}\n"
        
        if mime_data.hasText():
            text = mime_data.text()
            if len(text) > 100:
                text = text[:100] + "..."
            debug_text += f"\nText: {text}\n"
        
        if mime_data.hasHtml():
            html = mime_data.html()
            if len(html) > 100:
                html = html[:100] + "..."
            debug_text += f"\nHTML: {html}\n"
        
        if mime_data.hasUrls():
            urls = mime_data.urls()
            debug_text += "\nURLs:\n"
            for url in urls:
                debug_text += f"- {url.toString()}\n"
        
        # Show debug message
        QMessageBox.information(self, "Clipboard Debug", debug_text)
    
    def _extract_image_urls_from_html(self, html: str) -> List[str]:
        """Extract image URLs from HTML.
        
        Args:
            html: HTML string
            
        Returns:
            List of image URLs
        """
        # Use regex to find image tags and extract src attribute
        img_pattern = r'<img[^>]+src="([^"]+)"'
        matches = re.findall(img_pattern, html)
        
        # Filter to only keep URLs that look like images
        return [url for url in matches if any(url.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp'])] 

    def rebuild_recognition_database(self) -> None:
        """Rebuild the character recognition database from all tagged images."""
        # First, check if there are any images
        if not self.images:
            self.show_error("Error", "No images available to process")
            return
        
        # Create a progress dialog
        progress = QProgressDialog("Rebuilding recognition database...", "Cancel", 0, 100, self)
        progress.setWindowTitle("Recognition Database")
        progress.setMinimumDuration(0)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setValue(0)
        progress.show()
        QApplication.processEvents()
        
        # Initialize the recognition util if needed
        if not hasattr(self, 'recognition_util') or not self.recognition_util:
            self.recognition_util = ImageRecognitionUtil(self.db_conn)
        
        try:
            # Update progress
            progress.setValue(10)
            progress.setLabelText(f"Clearing existing database for story {self.story_id}...")
            QApplication.processEvents()
            
            # Rebuild the database with the complete method, but only for this story
            self.recognition_util.build_character_image_database(story_id=self.story_id)
            
            # Update progress
            progress.setValue(90)
            QApplication.processEvents()
            
            # Complete the progress
            progress.setValue(100)
            QApplication.processEvents()
            
            # Show completion message
            QMessageBox.information(self, "Recognition Database", 
                                   f"Character recognition database has been rebuilt successfully for the current story.")
        except Exception as e:
            print(f"Error rebuilding recognition database: {e}")
            QMessageBox.critical(self, "Error", f"Failed to rebuild recognition database: {str(e)}")
        finally:
            # Close the progress dialog
            progress.close()
    
    def add_region_to_recognition_database(self, image: QImage, character_id: int, 
                                          character_name: str, region: Dict[str, float]) -> None:
        """Add a region to the character recognition database.
        
        Args:
            image: Source image
            character_id: ID of the character
            character_name: Name of the character
            region: Region dictionary with x, y, width, height as relative coordinates (0.0-1.0)
        """
        # Convert relative coordinates to absolute
        img_width = image.width()
        img_height = image.height()
        
        x = int(region["x"] * img_width)
        y = int(region["y"] * img_height)
        width = int(region["width"] * img_width)
        height = int(region["height"] * img_height)
        
        # Ensure coordinates are valid
        x = max(0, min(x, img_width - 1))
        y = max(0, min(y, img_height - 1))
        width = max(1, min(width, img_width - x))
        height = max(1, min(height, img_height - y))
        
        # Extract the region as a QImage
        region_image = image.copy(x, y, width, height)
        
        # Add to recognition database
        self.recognition_util.add_face(character_id, character_name, region_image)
    
    def on_recognize_characters(self, image_id: int) -> None:
        """Open the character recognition dialog for an image.
        
        Args:
            image_id: ID of the image
        """
        # Find the image data
        image_data = next((img for img in self.images if img["id"] == image_id), None)
        
        if not image_data:
            self.show_error("Error", f"Image data not found for ID {image_id}")
            return
        
        # Get the file path
        file_path = image_data.get("path")
        
        if not file_path or not os.path.exists(file_path):
            self.show_error("Error", f"Image file not found at {file_path}")
            return
        
        # Load the image
        image = QImage(file_path)
        
        if image.isNull():
            self.show_error("Error", "Could not load image")
            return
        
        # Create and show the region selection dialog
        dialog = RegionSelectionDialog(
            self.db_conn,
            image,
            self.story_id,
            self,
            image_id
        )
        
        dialog.exec()
        
        # Reload images to reflect any changes
        self.load_images()
    
    def on_suggest_character_tags(self, image: QImage):
        """Suggest character tags based on face recognition.
        
        Args:
            image: Image to analyze
        """
        # Check if we have a recognition database
        if not self.recognition_util.has_faces():
            self.show_error(
                "Recognition Database Empty", 
                "The character recognition database is empty. Please add character tags to images first, " +
                "then rebuild the recognition database."
            )
            return []
        
        # Find faces in the image
        results = self.recognition_util.recognize_faces(image)
        
        if not results:
            self.show_error("No Characters Found", "No recognizable characters were found in this image.")
            return []
        
        # Format results as a list of dictionaries
        character_suggestions = []
        
        for result in results:
            character_id = result["id"]
            name = result["name"]
            confidence = result["confidence"]
            region = result["region"]  # x, y, width, height as relative coordinates (0.0-1.0)
            
            character_suggestions.append({
                "id": character_id,
                "name": name,
                "confidence": confidence,
                "region": region
            })
        
        # Sort by confidence (descending)
        character_suggestions.sort(key=lambda x: x["confidence"], reverse=True)
        
        return character_suggestions
    
    def on_thumbnail_checkbox_toggled(self, image_id: int, checked: bool) -> None:
        """Handle thumbnail checkbox toggle.
        
        Args:
            image_id: ID of the image
            checked: Whether the checkbox is checked
        """
        if checked:
            self.selected_images.add(image_id)
        else:
            self.selected_images.discard(image_id)
        
        # Update UI based on selection state
        self.update_selection_ui()
    
    def update_selection_ui(self) -> None:
        """Update UI based on selection state."""
        # Show or hide the batch operations panel based on selection
        selection_count = len(self.selected_images)
        self.batch_operations_panel.setVisible(selection_count > 0)
        
        # For debugging
        if selection_count > 0:
            print(f"Selected {selection_count} images: {self.selected_images}")
    
    def on_move_to_scene(self) -> None:
        """Handle move to scene action."""
        # Check if any images are selected
        if not self.selected_images:
            self.show_error("No Images Selected", "Please select images to move to a scene")
            return
        
        # Get all scenes for this story
        cursor = self.db_conn.cursor()
        
        query = """
            SELECT id, title, sequence_number
            FROM events
            WHERE story_id = ? AND event_type = 'SCENE'
            ORDER BY sequence_number DESC
        """
        
        cursor.execute(query, (self.story_id,))
        
        # Convert to list of dicts
        scenes = []
        for row in cursor.fetchall():
            scenes.append({
                "id": row[0],
                "title": row[1],
                "sequence_number": row[2]
            })
        
        if not scenes:
            self.show_error("No Scenes", "This story has no scenes. Please create a scene first.")
            return
        
        # Create a dialog to select the scene
        from app.views.gallery.dialogs.scene_selection import SceneSelectionDialog
        dialog = SceneSelectionDialog(self.db_conn, self.story_id, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get the selected scene ID
            scene_id = dialog.get_selected_scene_id()
            
            if scene_id is None:
                return
            
            # Update each selected image
            for image_id in self.selected_images:
                # Add to scene - this function handles checking if it's already in the scene
                add_image_to_scene(self.db_conn, scene_id, image_id)
            
            # Reload images to reflect the changes
            self.load_images()
    
    def on_batch_character_tagging(self) -> None:
        """Handle batch character tagging action."""
        # Check if any images are selected
        if not self.selected_images:
            self.show_error("No Images Selected", "Please select images to batch tag characters")
            return
        
        # Create and show the batch character tagging dialog
        dialog = BatchCharacterTaggingDialog(
            self.db_conn, 
            self.story_id, 
            self.selected_images.copy(),  # Pass a copy of the set
            self
        )
        
        # Show the dialog
        dialog.exec()
        
        # After the dialog closes, refresh the gallery to reflect any changes
        # Show a progress indicator during refresh
        self.refresh_gallery_with_progress()
    
    def on_batch_context_tagging(self) -> None:
        """Handle batch context tagging action."""
        # Check if any images are selected
        if not self.selected_images:
            self.show_error("No Images Selected", "Please select images to batch tag contexts")
            return
        
        # Create and show the batch context tagging dialog
        dialog = BatchContextTaggingDialog(
            self.db_conn, 
            self.selected_images.copy(),  # Pass a copy of the set
            self
        )
        
        # Show the dialog
        dialog.exec()
        
        # After the dialog closes, refresh the gallery to reflect any changes
        # Show a progress indicator during refresh
        self.refresh_gallery_with_progress()
    
    def refresh_gallery_with_progress(self) -> None:
        """Refresh the gallery with a visual progress indicator."""
        # Create a progress dialog
        progress = QProgressDialog(
            "Refreshing gallery...",
            None,  # No cancel button
            0,
            0,  # Indeterminate progress
            self
        )
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)  # Show immediately
        progress.setWindowTitle("Gallery Refresh")
        
        # Show the progress dialog
        progress.show()
        QApplication.processEvents()  # Ensure it's displayed
        
        try:
            # Perform the actual refresh
            self.load_images()
            
            # Brief delay to ensure user sees the progress indicator
            QTimer.singleShot(100, progress.close)
            
        except Exception as e:
            # Ensure progress dialog is closed even if there's an error
            progress.close()
            logging.exception(f"Error during gallery refresh: {e}")
            self.show_error("Refresh Error", f"Failed to refresh gallery: {str(e)}")
        
        finally:
            # Ensure progress dialog is always closed
            if progress.isVisible():
                progress.close()
    
    def get_on_scene_characters(self) -> List[Dict[str, Any]]:
        """Get a list of characters that appear in the active scene.
        
        Returns:
            List of character dictionaries
        """
        # This is a stub for now
        # In a real implementation, this would return characters that are "on scene"
        # based on the active scene or other context
        
        # For now, just return some recently tagged characters
        return get_characters_by_last_tagged(self.db_conn, self.story_id, limit=5)
    
    def show_filters_dialog(self):
        """Show the gallery filter dialog."""
        if not self.story_id:
            return
            
        dialog = GalleryFilterDialog(self.db_conn, self.story_id, self)
        
        # Set current filters
        dialog.character_filters = self.character_filters.copy()
        
        # Explicitly populate the filter list with current filters
        dialog.populate_filter_list()
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get updated filters
            self.character_filters = dialog.get_character_filters()
            
            # Apply filters
            self.apply_filters()
    
    def apply_filters(self):
        """Apply filters to the gallery view."""
        # Reload images with current filters using progress indicator
        self.refresh_gallery_with_progress()
        
        # Update filter status
        self.update_filter_status()
    
    def clear_filters(self) -> None:
        """Clear all active filters and refresh the gallery."""
        self.character_filters = []
        
        # Reload all images with progress indicator
        self.refresh_gallery_with_progress()
        
        # Update status
        self.update_filter_status()
    
    def update_filter_status(self) -> None:
        """Update the filter status label."""
        # Build a status message
        status_text = ""
        
        # Character filters
        if self.character_filters:
            # Get character names
            character_names = []
            
            for character_id, include in self.character_filters:
                # Get character name
                cursor = self.db_conn.cursor()
                cursor.execute("SELECT name FROM characters WHERE id = ?", (character_id,))
                result = cursor.fetchone()
                
                if result:
                    character_name = result[0]
                    if include:
                        character_names.append(f"Include: {character_name}")
                    else:
                        character_names.append(f"Exclude: {character_name}")
            
            if character_names:
                status_text += "Filters: " + ", ".join(character_names)
        
        # NSFW setting
        if self.show_nsfw:
            if status_text:
                status_text += " | "
            status_text += "Showing NSFW content"
        
        # Set the label text
        self.status_label.setText(status_text)
    
    def toggle_image_nsfw(self, image_id: int) -> None:
        """Toggle NSFW status for an image.
        
        Args:
            image_id: ID of the image
        """
        # Find the image data
        image_data = next((img for img in self.images if img["id"] == image_id), None)
        
        if not image_data:
            return
        
        # Toggle NSFW status
        is_nsfw = not image_data.get("is_nsfw", False)
        
        # Update database
        cursor = self.db_conn.cursor()
        cursor.execute("UPDATE images SET is_nsfw = ? WHERE id = ?", (is_nsfw, image_id))
        self.db_conn.commit()
        
        # Update image data
        image_data["is_nsfw"] = is_nsfw
        
        # Update thumbnail if it exists
        if image_id in self.thumbnails:
            thumbnail = self.thumbnails[image_id]
            
            if is_nsfw and not self.show_nsfw:
                # If now NSFW and not showing NSFW, set to placeholder
                self.set_thumbnail_nsfw(thumbnail)
            else:
                # Otherwise, show normal thumbnail
                self.set_thumbnail_normal(thumbnail, image_id)
    
    def _get_scene_newest_timestamp(self, scene_id: int) -> str:
        """Get the newest timestamp for any quick event in a scene.
        
        Args:
            scene_id: ID of the scene
            
        Returns:
            Timestamp string of the newest quick event
        """
        cursor = self.db_conn.cursor()
        cursor.execute("""
            SELECT MAX(qe.created_at) as newest_timestamp
            FROM quick_events qe
            JOIN scene_quick_events sqe ON qe.id = sqe.quick_event_id
            WHERE sqe.scene_event_id = ?
        """, (scene_id,))
        
        result = cursor.fetchone()
        if result and result[0]:
            return result[0]
        else:
            # If no quick events found, use scene creation date
            cursor.execute("""
                SELECT created_at FROM events
                WHERE id = ?
            """, (scene_id,))
            
            result = cursor.fetchone()
            if result and result[0]:
                return result[0]
            
            # Last resort fallback
            return '1970-01-01 00:00:00'
    
    def create_decision_point(self) -> None:
        """Open the decision point dialog to create a new decision point."""
        if not self.story_id:
            QMessageBox.warning(self, "Error", "No story selected.")
            return
            
        try:
            # Import here to avoid circular imports
            from app.views.decision_point_dialog import DecisionPointDialog
            
            # Create and show the dialog
            dialog = DecisionPointDialog(self.db_conn, self.story_id, parent=self)
            
            # If the dialog is accepted (user clicked Save), show a success message
            if dialog.exec() == QDialog.DialogCode.Accepted:
                QMessageBox.information(self, "Success", "Decision point created successfully.")
        except Exception as e:
            print(f"Error creating decision point: {e}")
            QMessageBox.warning(self, "Error", f"Failed to create decision point: {str(e)}")
    
    def create_scene(self) -> None:
        """Open the scene dialog to create a new scene."""
        if not self.story_id:
            QMessageBox.warning(self, "Error", "No story selected.")
            return
            
        try:
            # Import SceneDialog from timeline_widget to avoid circular imports
            from app.views.timeline_widget import SceneDialog
            
            # Create and show the dialog
            dialog = SceneDialog(self.db_conn, self.story_id, parent=self)
            
            # If the dialog is accepted (user clicked Save), show a success message
            if dialog.exec() == QDialog.DialogCode.Accepted:
                QMessageBox.information(self, "Success", "Scene created successfully.")
        except Exception as e:
            print(f"Error creating scene: {e}")
            QMessageBox.warning(self, "Error", f"Failed to create scene: {str(e)}")
    
    def _filter_images_by_character(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter images based on character filters.
        
        Args:
            images: List of image data dictionaries
            
        Returns:
            Filtered list of images
        """
        if not self.character_filters:
            # No filters, return all images
            return images
        
        filtered_images = []
        
        for image in images:
            # Get character tags for this image from cache
            tags = self.image_character_tags_cache.get(image["id"], [])
            character_ids = set(tag["character_id"] for tag in tags)
            
            # Check if this image should be included
            include_image = True
            
            for character_id, include in self.character_filters:
                if include:
                    # If this filter is to include, then the image must have this character
                    if character_id not in character_ids:
                        include_image = False
                        break
                else:
                    # If this filter is to exclude, then the image must not have this character
                    if character_id in character_ids:
                        include_image = False
                        break
            
            if include_image:
                filtered_images.append(image)
        
        return filtered_images