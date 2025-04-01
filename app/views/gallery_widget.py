#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gallery Widget for The Plot Thickens application.

This widget displays a gallery of images for a story.
"""

import os
import sys
import time
import io
import re
import pickle
import string
import random
import base64
import urllib.parse
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set, Union
from datetime import datetime

import numpy as np

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QGridLayout, QFileDialog, QMessageBox,
    QSizePolicy, QFrame, QApplication, QDialog, QListWidget,
    QListWidgetItem, QMenu, QTabWidget, QSplitter, QComboBox,
    QToolButton, QInputDialog, QTextEdit, QCheckBox, QProgressBar,
    QGroupBox, QGraphicsView, QGraphicsScene, QGraphicsRectItem, 
    QGraphicsPixmapItem, QGraphicsItem, QGraphicsTextItem, QProgressDialog,
    QStyleFactory, QMainWindow, QStatusBar, QToolTip, QRadioButton,
    QSpinBox, QLineEdit, QAbstractItemView, QDialogButtonBox
)
from PyQt6.QtCore import (
    Qt, QSize, pyqtSignal, QByteArray, QUrl, QBuffer, QIODevice, 
    QPoint, QRect, QRectF, QPointF, QRegularExpression, QSortFilterProxyModel,
    QTimer
)
from PyQt6.QtGui import (
    QPixmap, QImage, QColor, QBrush, QPen, QPainter, QFont, 
    QPalette, QCursor, QIcon, QAction, QTransform, QClipboard, QImageReader,
    QTextCursor, QStandardItemModel, QStandardItem, QKeySequence, QShortcut
)
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from app.utils.character_completer import CharacterCompleter
# Import the centralized character reference functions
from app.utils.character_references import convert_mentions_to_char_refs, convert_char_refs_to_mentions

from app.db_sqlite import (
    get_image_quick_events, get_character_quick_events,
    associate_quick_event_with_image, remove_quick_event_image_association,
    get_story_characters, get_character,
    add_character_tag_to_image, update_character_tag, remove_character_tag,
    get_image_character_tags, create_quick_event, get_next_quick_event_sequence_number,
    get_quick_event_characters, get_quick_event_tagged_characters,
    search_quick_events, get_story_folder_paths, create_image,
    process_quick_event_character_tags, get_quick_event_scenes
)

# Import our image recognition utility
from app.utils.image_recognition_util import ImageRecognitionUtil

class ThumbnailWidget(QFrame):
    """Widget for displaying a thumbnail image with basic controls."""
    
    clicked = pyqtSignal(int)  # Signal emitted when thumbnail is clicked
    delete_requested = pyqtSignal(int)  # Signal emitted when delete button is clicked
    
    def __init__(self, image_id: int, pixmap: QPixmap, title: str = "", parent=None) -> None:
        """Initialize the thumbnail widget.
        
        Args:
            image_id: ID of the image
            pixmap: Image pixmap
            title: Optional title to display
            parent: Parent widget
        """
        super().__init__(parent)
        self.image_id = image_id
        self.title = title
        self.original_pixmap = pixmap
        self.displayed_pixmap = pixmap
        self.is_nsfw = False
        self.quick_event_text = ""
        
        # Visual styling
        self.setFrameShape(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setLineWidth(1)
        self.setStyleSheet("ThumbnailWidget { border: 1px solid #666; background-color: #333; }")
        
        # Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        
        # Delete button
        self.delete_btn = QPushButton("×")
        self.delete_btn.setFlat(True)
        self.delete_btn.setFixedSize(23, 23)  # Increased from 20x20
        self.delete_btn.setStyleSheet("""
            QPushButton { 
                background-color: rgba(200, 0, 0, 0.7); 
                color: white; 
                border-radius: 11px; 
                font-weight: bold; 
                font-size: 16px;
            }
            QPushButton:hover { 
                background-color: rgba(255, 0, 0, 0.9);
            }
        """)
        delete_layout = QHBoxLayout()
        delete_layout.addStretch(1)
        delete_layout.addWidget(self.delete_btn)
        self.layout.addLayout(delete_layout)
        
        # Image label
        self.image_label = QLabel()
        self.image_label.setMinimumSize(150, 130)  # Increased from 130x110
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.update_displayed_pixmap()
        self.layout.addWidget(self.image_label)
        
        # Title label
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("color: white; font-size: 11px;")  # Increased from 10px
        self.layout.addWidget(self.title_label)
        
        # Quick event label
        self.quick_event_label = QLabel()
        self.quick_event_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.quick_event_label.setWordWrap(True)
        self.quick_event_label.setStyleSheet("color: #aaffaa; font-size: 10px; font-style: italic; background-color: rgba(0, 0, 0, 0.2); border-radius: 3px; padding: 2px;")  # Increased from 9px
        self.quick_event_label.setMaximumHeight(45)  # Increased from 40
        self.layout.addWidget(self.quick_event_label)
        self.quick_event_label.hide()  # Initially hidden until we have content
        
        # Connect signals
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        
        # Set size policy - Fixed size to prevent shrinking
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setMinimumSize(170, 195)  # Increased from 150x170
        self.setFixedSize(170, 230)  # Increased from 150x200
        
        # Enable context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def update_displayed_pixmap(self):
        """Update the displayed pixmap in the image label."""
        # Scale to fit within the image label (150x130)
        scaled_pixmap = self.original_pixmap.scaled(
            150, 130,  # Increased from 130x110
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)
    
    def update_pixmap(self, new_pixmap: QPixmap):
        """Update the thumbnail's pixmap.
        
        Args:
            new_pixmap: New pixmap to display
        """
        self.original_pixmap = new_pixmap
        self.update_displayed_pixmap()
    
    def mousePressEvent(self, event) -> None:
        """Handle mouse press events."""
        super().mousePressEvent(event)
        self.clicked.emit(self.image_id)
    
    def _on_delete_clicked(self) -> None:
        """Handle delete button click."""
        self.delete_requested.emit(self.image_id)
    
    def show_context_menu(self, position):
        """Show context menu when right-clicking on the thumbnail.
        
        Args:
            position: Position where the context menu should appear
        """
        # Get the parent GalleryWidget
        parent = self.parent()
        while parent and not isinstance(parent, GalleryWidget):
            parent = parent.parent()
            
        # If we found the GalleryWidget parent, delegate to its context menu handler
        if parent and isinstance(parent, GalleryWidget):
            parent.on_thumbnail_context_menu(position, self)
        else:
            # Fallback if parent can't be found
            menu = QMenu()
            
            view_action = QAction("View Image", self)
            view_action.triggered.connect(lambda: self.clicked.emit(self.image_id))
            menu.addAction(view_action)
            
            delete_action = QAction("Delete Image", self)
            delete_action.triggered.connect(self._on_delete_clicked)
            menu.addAction(delete_action)
            
            menu.exec(self.mapToGlobal(position))
    
    def set_quick_event_text(self, text: str) -> None:
        """Set the quick event text for this thumbnail.
        
        Args:
            text: Quick event text
        """
        if text:
            self.quick_event_text = text
            # Truncate to roughly 120 characters
            if len(text) > 120:
                text = text[:117] + "..."
            
            # Set the text
            self.quick_event_label.setText(text)
            
            # Show the label
            self.quick_event_label.show()
        else:
            self.quick_event_text = ""
            self.quick_event_label.hide()


class SeparatorWidget(QFrame):
    """Widget for displaying a separator with a title between image groups."""
    
    def __init__(self, title: str, parent=None) -> None:
        """Initialize the separator widget.
        
        Args:
            title: Title text to display
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Visual styling
        self.setFrameShape(QFrame.Shape.Box)
        self.setLineWidth(2)
        self.setStyleSheet("""
            SeparatorWidget {
                border-top: 2px solid #666;
                border-bottom: 2px solid #666;
                background-color: #333;
                margin-top: 10px;
                margin-bottom: 5px;
            }
        """)
        
        # Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 5, 10, 5)
        
        # Title label
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        self.layout.addWidget(self.title_label)
        
        # Set size policy - Expanding horizontally, fixed vertically
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(40)


class QuickEventSelectionDialog(QDialog):
    """Dialog for selecting quick events to associate with an image."""
    
    def __init__(self, db_conn, story_id: int, image_id: int, current_quick_event_ids: List[int] = None, parent=None):
        """Initialize the quick event selection dialog.
        
        Args:
            db_conn: Database connection
            story_id: ID of the story
            image_id: ID of the image
            current_quick_event_ids: List of already associated quick event IDs
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.story_id = story_id
        self.image_id = image_id
        self.current_quick_event_ids = current_quick_event_ids or []
        self.selected_quick_event_ids = []
        
        self.init_ui()
        self.load_quick_events()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Select Quick Events")
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # Character selection
        character_layout = QHBoxLayout()
        character_layout.addWidget(QLabel("Character:"))
        self.character_combo = QComboBox()
        self.character_combo.currentIndexChanged.connect(self.on_character_changed)
        character_layout.addWidget(self.character_combo)
        layout.addLayout(character_layout)
        
        # Quick event list
        self.event_list = QListWidget()
        self.event_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        layout.addWidget(self.event_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.select_button = QPushButton("Select")
        self.select_button.clicked.connect(self.accept)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.select_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def load_characters(self):
        """Load characters for the story."""
        try:
            # Get all characters for the story
            characters = get_story_characters(self.db_conn, self.story_id)
            
            # Add to combo box
            self.character_combo.clear()
            self.character_combo.addItem("All Characters", None)
            
            for character in characters:
                name = character['name']
                self.character_combo.addItem(name, character['id'])
                
        except Exception as e:
            print(f"Error loading characters: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load characters: {str(e)}")
        
    def load_quick_events(self):
        """Load quick events for the story."""
        try:
            # Clear existing items
            self.event_list.clear()
            
            # Only load characters if this is the initial load
            # (block the signal to avoid recursive call)
            if self.character_combo.count() == 0:
                # Disconnect signal temporarily to prevent recursion
                self.character_combo.blockSignals(True)
                self.load_characters()
                self.character_combo.blockSignals(False)
            
            # Get current selected character ID
            character_id = self.character_combo.currentData()
            
            if character_id is not None:
                # If a specific character is selected, only show their quick events
                quick_events = get_character_quick_events(self.db_conn, character_id)
                self.populate_event_list(quick_events)
            else:
                # If "All Characters" is selected, load quick events for each character
                characters = get_story_characters(self.db_conn, self.story_id)
                for character in characters:
                    quick_events = get_character_quick_events(self.db_conn, character['id'])
                    if quick_events:
                        # Add a header item for this character
                        header_item = QListWidgetItem(f"--- {character['name']} ---")
                        header_item.setFlags(Qt.ItemFlag.NoItemFlags)  # Make non-selectable
                        header_item.setBackground(QBrush(QColor("#333333")))
                        self.event_list.addItem(header_item)
                        
                        # Add this character's quick events
                        self.populate_event_list(quick_events)
                        
        except Exception as e:
            print(f"Error loading quick events: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load quick events: {str(e)}")
            
    def populate_event_list(self, quick_events: List[Dict[str, Any]]):
        """Populate the event list with quick events.
        
        Args:
            quick_events: List of quick event dictionaries
        """
        for event in quick_events:
            # Get the event text and tagged characters
            text = event['text']
            
            # Get tagged characters for this event
            tagged_characters = []
            try:
                tagged_characters = get_quick_event_tagged_characters(self.db_conn, event['id'])
            except Exception as e:
                print(f"Error loading tagged characters: {e}")
            
            # Convert character references to @mentions for display
            display_text = self.format_display_text(text, tagged_characters)
            
            # Truncate if too long
            if len(display_text) > 80:
                display_text = display_text[:77] + "..."
                
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, event['id'])
            
            # Set the item to be pre-selected if it's already associated
            if event['id'] in self.current_quick_event_ids:
                item.setSelected(True)
            
            self.event_list.addItem(item)
    
    def format_display_text(self, text: str, tagged_characters: Dict[str, Dict]) -> str:
        """Format the text for display, converting character references to mentions.
        
        Args:
            text: The text to format
            tagged_characters: Dictionary of characters by ID
            
        Returns:
            Formatted text with character references converted to mentions
        """
        # Use the centralized function to convert [char:ID] to @mentions
        return convert_char_refs_to_mentions(text, tagged_characters)
    
    def on_character_changed(self, index: int):
        """Handle character selection change.
        
        Args:
            index: Index of the selected character
        """
        # Load quick events for the selected character without reloading characters
        try:
            # Clear existing items
            self.event_list.clear()
            
            # Get current selected character ID
            character_id = self.character_combo.currentData()
            
            if character_id is not None:
                # If a specific character is selected, only show their quick events
                quick_events = get_character_quick_events(self.db_conn, character_id)
                self.populate_event_list(quick_events)
            else:
                # If "All Characters" is selected, load quick events for each character
                characters = get_story_characters(self.db_conn, self.story_id)
                for character in characters:
                    quick_events = get_character_quick_events(self.db_conn, character['id'])
                    if quick_events:
                        # Add a header item for this character
                        header_item = QListWidgetItem(f"--- {character['name']} ---")
                        header_item.setFlags(Qt.ItemFlag.NoItemFlags)  # Make non-selectable
                        header_item.setBackground(QBrush(QColor("#333333")))
                        self.event_list.addItem(header_item)
                        
                        # Add this character's quick events
                        self.populate_event_list(quick_events)
        except Exception as e:
            print(f"Error loading quick events: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load quick events: {str(e)}")
    
    def get_selected_quick_event_ids(self) -> List[int]:
        """Get the IDs of the selected quick events.
        
        Returns:
            List of selected quick event IDs
        """
        self.selected_quick_event_ids = []
        
        for i in range(self.event_list.count()):
            item = self.event_list.item(i)
            if item.isSelected():
                event_id = item.data(Qt.ItemDataRole.UserRole)
                if event_id is not None:  # Skip header items
                    self.selected_quick_event_ids.append(event_id)
                
        return self.selected_quick_event_ids


class TaggableImageLabel(QLabel):
    """A custom image label that allows for character tagging."""
    
    tag_added = pyqtSignal(float, float)  # x, y position in relative coordinates (0.0-1.0)
    tag_selected = pyqtSignal(int)  # tag_id
    
    def __init__(self, parent=None):
        """Initialize the taggable image label."""
        super().__init__(parent)
        self.tags = []
        self.tag_mode = False
        self.selected_tag_id = None
        self.hover_tag_id = None
        
        # Store dimensions for coordinate conversions
        self.image_width = 0
        self.image_height = 0
        self.orig_width = 0  # Original image width
        self.orig_height = 0  # Original image height
        self.offset_x = 0
        self.offset_y = 0
        
        # Set larger minimum size
        self.setMinimumSize(200, 150)
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        
    def set_image(self, pixmap, orig_width=None, orig_height=None):
        """Set the image for the label.
        
        Args:
            pixmap: QPixmap to display
            orig_width: Original image width (if scaled)
            orig_height: Original image height (if scaled)
        """
        self.setPixmap(pixmap)
        self.image_width = pixmap.width()
        self.image_height = pixmap.height()
        
        # Store original dimensions if provided, otherwise use displayed dimensions
        self.orig_width = orig_width if orig_width is not None else self.image_width
        self.orig_height = orig_height if orig_height is not None else self.image_height
        
        # Log dimensions for debugging
        print(f"TaggableImageLabel set_image: display={self.image_width}x{self.image_height}, " +
              f"original={self.orig_width}x{self.orig_height}")
        
        # Calculate offsets for centered image
        self.update_offsets()
    
    def update_offsets(self):
        """Update offset calculations for a centered image."""
        label_width = self.width()
        label_height = self.height()
        
        self.offset_x = max(0, (label_width - self.image_width) // 2)
        self.offset_y = max(0, (label_height - self.image_height) // 2)
    
    def set_tags(self, tags):
        """Set the character tags to display.
        
        Args:
            tags: List of tag dictionaries
        """
        self.tags = tags
        self.update()
        
    def enable_tag_mode(self, enabled=True):
        """Enable or disable tag adding mode.
        
        Args:
            enabled: Whether to enable tag mode
        """
        self.tag_mode = enabled
        if enabled:
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        
    def mousePressEvent(self, event):
        """Handle mouse press events.
        
        Args:
            event: Mouse event
        """
        if self.tag_mode and self.pixmap():
            if event.button() == Qt.MouseButton.LeftButton:
                # Get raw click coordinates
                click_x = event.position().x()
                click_y = event.position().y()
                
                # Convert to relative coordinates within the image
                rel_x, rel_y = self._to_relative_coords(click_x, click_y)
                
                # Debug info to track exact coordinates at every step
                print(f"MOUSE CLICK: raw=({click_x}, {click_y}), rel=({rel_x:.4f}, {rel_y:.4f})")
                
                if 0 <= rel_x <= 1 and 0 <= rel_y <= 1:
                    # Emit signal with relative coordinates
                    self.tag_added.emit(rel_x, rel_y)
            else:
                # Check if a tag was clicked
                clicked_tag_id = self._get_tag_at_position(event.position().x(), event.position().y())
                if clicked_tag_id is not None:
                    self.selected_tag_id = clicked_tag_id
                    self.tag_selected.emit(clicked_tag_id)
                    self.update()
                else:
                    # Deselect if clicking outside any tag
                    if self.selected_tag_id is not None:
                        self.selected_tag_id = None
                        self.update()
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events.
        
        Args:
            event: Mouse event
        """
        if not self.tag_mode:
            # Check if hovering over a tag
            hover_tag_id = self._get_tag_at_position(event.position().x(), event.position().y())
            if hover_tag_id != self.hover_tag_id:
                self.hover_tag_id = hover_tag_id
                self.update()
        
        super().mouseMoveEvent(event)
    
    def _to_relative_coords(self, x, y):
        """Convert absolute coordinates to relative coordinates.
        
        Args:
            x: Absolute x coordinate
            y: Absolute y coordinate
            
        Returns:
            Tuple of (relative_x, relative_y)
        """
        # Simple direct calculation
        # Get current pixmap size
        displayed_width = self.pixmap().width() if self.pixmap() else self.image_width
        displayed_height = self.pixmap().height() if self.pixmap() else self.image_height
        
        # Adjust for image offset within label
        adjusted_x = x - self.offset_x
        adjusted_y = y - self.offset_y
        
        # Direct conversion with bounds checking
        rel_x = max(0.0, min(1.0, adjusted_x / displayed_width if displayed_width > 0 else 0.0))
        rel_y = max(0.0, min(1.0, adjusted_y / displayed_height if displayed_height > 0 else 0.0))
        
        # Debug info with exact values
        print(f"_to_relative_coords: raw=({x}, {y}), " +
              f"adjusted=({adjusted_x}, {adjusted_y}), " +
              f"relative=({rel_x:.4f}, {rel_y:.4f})")
        
        return rel_x, rel_y
        
    def _to_absolute_coords(self, rel_x, rel_y):
        """Convert relative coordinates to absolute coordinates.
        
        Args:
            rel_x: Relative x coordinate (0.0-1.0)
            rel_y: Relative y coordinate (0.0-1.0)
            
        Returns:
            Tuple of (absolute_x, absolute_y)
        """
        # Get current pixmap size
        displayed_width = self.pixmap().width() if self.pixmap() else self.image_width
        displayed_height = self.pixmap().height() if self.pixmap() else self.image_height
        
        # CRITICAL: Direct coordinate calculation
        # Calculate absolute position based on the relative position multiplied by the dimensions
        # Add the offset to position correctly within the label
        abs_x = self.offset_x + (rel_x * displayed_width)
        abs_y = self.offset_y + (rel_y * displayed_height)
        
        print(f"_to_absolute_coords FIXED: ({rel_x:.3f}, {rel_y:.3f}) -> ({abs_x:.1f}, {abs_y:.1f})")
        
        return abs_x, abs_y
        
    def _get_tag_at_position(self, x, y):
        """Get the tag at the given position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Tag ID or None if no tag found
        """
        if not self.tags or not self.pixmap():
            return None
            
        rel_x, rel_y = self._to_relative_coords(x, y)
        
        # Debug information
        print(f"Click at ({x}, {y}) -> relative ({rel_x:.2f}, {rel_y:.2f})")
        
        for tag in self.tags:
            # Tag coordinates are center points
            center_x = tag['x_position']
            center_y = tag['y_position']
            half_width = tag['width'] / 2.0  # Use floating point division
            half_height = tag['height'] / 2.0  # Use floating point division
            
            # Check if point is within rectangle defined by center and half-dimensions
            if (center_x - half_width <= rel_x <= center_x + half_width and
                center_y - half_height <= rel_y <= center_y + half_height):
                print(f"Hit tag: {tag['id']} center=({center_x:.2f}, {center_y:.2f}), " +
                      f"bounds=({center_x-half_width:.2f}, {center_y-half_height:.2f}, " +
                      f"{center_x+half_width:.2f}, {center_y+half_height:.2f})")
                return tag['id']
        
        return None
        
    def paintEvent(self, event):
        """Override paint event to draw tags.
        
        Args:
            event: Paint event
        """
        # Draw the image first
        super().paintEvent(event)
        
        if not self.tags or not self.pixmap():
            return
            
        painter = QPainter(self)
        
        # Get current display dimensions
        displayed_width = self.pixmap().width()
        displayed_height = self.pixmap().height()
        
        # Text height for character names
        text_height = 20
        
        # Debug info
        print(f"Painting tags - Image dimensions: {self.image_width}x{self.image_height}")
        print(f"Display dimensions: {displayed_width}x{displayed_height}")
        print(f"Label dimensions: {self.width()}x{self.height()}")
        print(f"Offsets: {self.offset_x}x{self.offset_y}")
        
        for tag in self.tags:
            tag_id = tag['id']
            # These are center coordinates (0-1 range) relative to the original image
            center_x = tag['x_position']
            center_y = tag['y_position']
            tag_width_ratio = tag['width']      # Width as proportion of original image width
            tag_height_ratio = tag['height']    # Height as proportion of original image height
            character_name = tag.get('character_name', 'Unknown')
            
            # FIXED COORDINATE MAPPING: Simple direct calculation
            # Position the rectangle centered exactly at the specified coordinates
            abs_center_x = self.offset_x + (center_x * displayed_width)
            abs_center_y = self.offset_y + (center_y * displayed_height)
            
            # Calculate display dimensions of the tag
            display_width = tag_width_ratio * displayed_width
            display_height = tag_height_ratio * displayed_height
            
            # Calculate top-left corner for drawing the rectangle
            rect_x = int(abs_center_x - (display_width / 2))
            rect_y = int(abs_center_y - (display_height / 2))
            
            # Debug info
            print(f"Tag {tag_id}: DB coords=({center_x:.4f}, {center_y:.4f}), " + 
                  f"Calculated center=({abs_center_x:.1f}, {abs_center_y:.1f}), " +
                  f"Rectangle top-left=({rect_x}, {rect_y})")
            
            # Set pen color based on selection/hover state
            if tag_id == self.selected_tag_id:
                pen = QPen(QColor(255, 165, 0))  # Orange for selected
                pen.setWidth(3)
            elif tag_id == self.hover_tag_id:
                pen = QPen(QColor(255, 255, 0))  # Yellow for hover
                pen.setWidth(2)
            else:
                pen = QPen(QColor(0, 255, 0))  # Green for normal
                pen.setWidth(2)
                
            # FIRST: Draw the rectangle at the exact calculated position
            painter.setPen(pen)
            painter.drawRect(rect_x, rect_y, int(display_width), int(display_height))
            
            # SECOND: Draw text as a completely separate element above the rectangle
            # Calculate text position independently from the rectangle
            text_x = rect_x
            text_y = max(0, rect_y - text_height - 2)  # Ensure text y position is never negative
            
            # Draw text background
            painter.setPen(QPen(Qt.PenStyle.NoPen))  # FIXED: Create a QPen object with NoPen style
            text_rect = QRect(text_x, text_y, int(display_width), text_height)
            painter.fillRect(text_rect, QColor(0, 0, 0, 180))
            
            # Draw text
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, character_name)
    
    def resizeEvent(self, event):
        """Handle resize events to recalculate offsets.
        
        Args:
            event: Resize event
        """
        super().resizeEvent(event)
        if hasattr(self, 'image_width'):  # Only recalculate if we have an image
            self.update_offsets()


class CharacterSelectionDialog(QDialog):
    """Dialog for selecting a character to tag."""
    
    def __init__(self, db_conn, story_id: int, parent=None):
        """Initialize the character selection dialog.
        
        Args:
            db_conn: Database connection
            story_id: ID of the story
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.story_id = story_id
        self.selected_character_id = None
        
        self.init_ui()
        self.load_characters()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Select Character to Tag")
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # Character list
        self.character_list = QListWidget()
        self.character_list.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self.character_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.select_button = QPushButton("Select")
        self.select_button.clicked.connect(self.accept)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.select_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def load_characters(self):
        """Load characters for the story."""
        try:
            # Get all characters for the story
            characters = get_story_characters(self.db_conn, self.story_id)
            
            # Add to list widget
            for character in characters:
                item = QListWidgetItem(character['name'])
                item.setData(Qt.ItemDataRole.UserRole, character['id'])
                self.character_list.addItem(item)
                
            # Select first character if available
            if self.character_list.count() > 0:
                self.character_list.setCurrentRow(0)
                
        except Exception as e:
            print(f"Error loading characters: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load characters: {str(e)}")
    
    def get_selected_character_id(self) -> int:
        """Get the ID of the selected character.
        
        Returns:
            Character ID or None if no selection
        """
        current_item = self.character_list.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None


class CharacterTagCompleter(QWidget):
    """Popup widget for character tag autocompletion."""
    
    character_selected = pyqtSignal(str)  # Signal emitted when a character is selected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.characters = []
        self.filtered_characters = []
        self.current_filter = ""
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create a list widget for character suggestions
        self.list_widget = QListWidget()
        self.list_widget.setFrameShape(QFrame.Shape.NoFrame)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.setMaximumHeight(200)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        
        # Style the list widget
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #2D2D30;
                color: #FFFFFF;
                border: 1px solid #3E3E42;
                border-radius: 3px;
            }
            QListWidget::item {
                padding: 4px;
            }
            QListWidget::item:selected {
                background-color: #3399FF;
            }
            QListWidget::item:hover {
                background-color: #3E3E40;
            }
        """)
        
        layout.addWidget(self.list_widget)
        
    def set_characters(self, characters):
        """Set the available characters.
        
        Args:
            characters: List of character dictionaries
        """
        self.characters = characters
        
    def set_filter(self, filter_text):
        """Set the filter for character suggestions.
        
        Args:
            filter_text: Text to filter characters by
        """
        self.current_filter = filter_text.lower()
        self.update_suggestions()
        
    def update_suggestions(self):
        """Update the character suggestions based on the current filter."""
        self.list_widget.clear()
        
        self.filtered_characters = []
        
        for character in self.characters:
            name = character['name']
            
            # Filter characters based on the current text
            if self.current_filter in name.lower():
                self.filtered_characters.append(character)
                self.list_widget.addItem(name)
        
        # Show or hide the popup based on whether there are suggestions
        if self.filtered_characters:
            self.list_widget.setCurrentRow(0)  # Select the first item
            self.resize(self.list_widget.sizeHint())
            self.show()
        else:
            self.hide()
            
    def on_item_clicked(self, item):
        """Handle item clicks.
        
        Args:
            item: The clicked list item
        """
        character_name = item.text()
        self.character_selected.emit(character_name)
        self.hide()
        
    def keyPressEvent(self, event):
        """Handle key press events.
        
        Args:
            event: Key event
        """
        key = event.key()
        
        if key == Qt.Key.Key_Escape:
            self.hide()
            event.accept()
        elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            current_item = self.list_widget.currentItem()
            if current_item:
                self.on_item_clicked(current_item)
            event.accept()
        elif key == Qt.Key.Key_Up:
            current_row = self.list_widget.currentRow()
            if current_row > 0:
                self.list_widget.setCurrentRow(current_row - 1)
            event.accept()
        elif key == Qt.Key.Key_Down:
            current_row = self.list_widget.currentRow()
            if current_row < self.list_widget.count() - 1:
                self.list_widget.setCurrentRow(current_row + 1)
            event.accept()
        else:
            super().keyPressEvent(event)


class QuickEventEditor(QDialog):
    """Dialog for creating a quick event with character tag support."""
    
    def __init__(self, db_conn, story_id: int, image_id: int, parent=None):
        """Initialize the quick event editor.
        
        Args:
            db_conn: Database connection
            story_id: ID of the story
            image_id: ID of the image to associate with the quick event
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.story_id = story_id
        self.image_id = image_id
        
        # Get all characters for the story for tagging
        self.characters = get_story_characters(db_conn, self.story_id)
        
        self.init_ui()
        
        # Create character tag completer
        self.tag_completer = CharacterCompleter(self)
        self.tag_completer.set_characters(self.characters)
        self.tag_completer.character_selected.connect(self.on_character_selected)
        self.tag_completer.attach_to_widget(
            self.text_edit,
            add_shortcut=True,
            shortcut_key="Ctrl+Space",
            at_trigger=True
        )
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Create Quick Event")
        self.resize(450, 200)
        
        layout = QVBoxLayout(self)
        
        # Character selection
        character_layout = QHBoxLayout()
        character_layout.addWidget(QLabel("Character:"))
        
        self.character_combo = QComboBox()
        
        # Add characters to combo box
        for character in self.characters:
            self.character_combo.addItem(character['name'], character['id'])
            
        character_layout.addWidget(self.character_combo)
        layout.addLayout(character_layout)
        
        # Text edit
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Enter quick event text. Use @name to tag characters (e.g., @John kissed @Mary)")
        self.text_edit.textChanged.connect(self.check_for_character_tag)
        layout.addWidget(self.text_edit)
        
        # Available characters
        if self.characters:
            char_names = [f"@{char['name']}" for char in self.characters]
            characters_label = QLabel("Available character tags: " + ", ".join(char_names))
            characters_label.setWordWrap(True)
            characters_label.setStyleSheet("color: #666; font-style: italic;")
            layout.addWidget(characters_label)
        
        # Note explaining automatic association
        note_label = QLabel("Note: This quick event will be automatically associated with the current image.")
        note_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(note_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
    def get_text(self) -> str:
        """Get the edited text, converting @mentions to [char:ID] format for storage.
        
        Returns:
            The text from the editor with character references in [char:ID] format
        """
        display_text = self.text_edit.toPlainText()
        # Convert @mentions to [char:ID] for storage
        return self.convert_mentions_to_char_refs(display_text)
        
    def convert_mentions_to_char_refs(self, text: str) -> str:
        """Convert @mentions to [char:ID] format for storage.
        
        Args:
            text: The text with @mentions
            
        Returns:
            Text with @mentions converted to [char:ID] format
        """
        # Use the centralized function, passing the characters from the parent dialog
        return convert_mentions_to_char_refs(text, self.characters)
        
    def get_character_id(self) -> int:
        """Get the selected character ID.
        
        Returns:
            ID of the selected character
        """
        return self.character_combo.currentData()
        

    def on_character_selected(self, character_name: str):
        """Handle character selection from completer.
        
        Args:
            character_name: Name of the selected character
        """
        self.tag_completer.insert_character_tag(character_name)
        
    def check_for_character_tag(self):
        """This method is now handled by CharacterCompleter."""
        pass
        
    def insert_character_tag(self, character_name: str):
        """This method is now handled by CharacterCompleter."""
        self.on_character_selected(character_name)


class ImageDetailDialog(QDialog):
    """Dialog for viewing image details and managing associated quick events."""
    
    def __init__(self, db_conn, image_id: int, image_data: Dict[str, Any], pixmap: QPixmap, parent=None):
        """Initialize the image detail dialog.
        
        Args:
            db_conn: Database connection
            image_id: ID of the image
            image_data: Dictionary with image data
            pixmap: QPixmap of the image
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.db = db_conn  # Add a reference to db_conn as db for compatibility
        self.image_id = image_id
        self.image_data = image_data
        self.orig_pixmap = pixmap  # Store the original pixmap
        self.pixmap = pixmap  # This may be scaled for display
        self.quick_events = []
        self.character_tags = []
        
        # Get the story ID for this image
        self.story_id = image_data.get('story_id')
        
        # Cache image dimensions
        self.image_width = pixmap.width()
        self.image_height = pixmap.height()
        
        # Log original dimensions
        print(f"Original image dimensions: {self.image_width}x{self.image_height}")
        
        # Load characters for the story (needed for character tagging)
        self.characters = []
        if self.story_id:
            self.characters = get_story_characters(self.db_conn, self.story_id)
        
        # Create status bar for messages
        self.status_bar = QStatusBar(self)
        
        self.init_ui()
        
        # Setup keyboard shortcuts
        self.setup_shortcuts()
        
        self.load_quick_events()
        self.load_character_tags()
    
    def statusBar(self):
        """Get the status bar.
        
        Returns:
            QStatusBar: The status bar
        """
        return self.status_bar
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts for the dialog."""
        from PyQt6.QtGui import QKeySequence, QShortcut
        
        # Add CTRL+Q shortcut for quick event
        quick_event_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        quick_event_shortcut.activated.connect(self.quick_event_shortcut_triggered)
    
    def quick_event_shortcut_triggered(self):
        """Handle CTRL+Q shortcut key press - create a quick event with special rules."""
        try:
            # Import the needed utilities
            from app.utils.quick_event_utils import show_quick_event_dialog
            
            # Create context for image viewer dialog
            context = {
                "source": "image_viewer_shortcut",
                "image_id": self.image_id,
                "allow_extra_options": True,
                "show_associate_checkbox": True,
                "shortcut": "CTRL+Q"
            }
            
            # Debug output
            print(f"\n[DEBUG] QuickEventDialog CTRL+Q triggered from Image Viewer - context: {context}\n")
            
            # Show the dialog with specific options for this context
            show_quick_event_dialog(
                db_conn=self.db_conn,
                story_id=self.story_id,
                parent=self,
                callback=self.on_quick_event_created,
                context=context,
                options={
                    "show_recent_events": True,
                    "show_character_tags": True,
                    "show_optional_note": True,
                    "allow_characterless_events": True,
                    "title": "Quick Event - Image Viewer"
                }
            )
        except Exception as e:
            import traceback
            print(f"Error creating quick event from shortcut: {e}")
            print(traceback.format_exc())
            QMessageBox.critical(
                self,
                "Error",
                f"Error creating quick event: {str(e)}",
                QMessageBox.StandardButton.Ok
            )
    
    def on_quick_event_created(self, event_id: int, text: str, context: Dict[str, Any]) -> None:
        """Handle the quick event created signal.
        
        Args:
            event_id: ID of the created quick event
            text: Text of the quick event
            context: Context dictionary passed to the dialog
        """
        if not event_id:
            return
        
        # Debug info about the current state
        print(f"[DEBUG] Quick event created - ID: {event_id}")
        print(f"[DEBUG] Context data: {context}")
        print(f"[DEBUG] Current image_id: {self.image_id}")
        
        try:
            # Associate the quick event with the image
            success = associate_quick_event_with_image(
                self.db_conn, 
                event_id, 
                self.image_id
            )
            
            if success:
                # Show a success message
                self.status_bar.showMessage(f"Quick event created and associated with this image", 5000)
                
                # Reload the quick events list
                self.load_quick_events()
                
                # Switch to the Quick Events tab
                for i in range(self.tab_widget.count()):
                    if self.tab_widget.tabText(i) == "Quick Events":
                        self.tab_widget.setCurrentIndex(i)
                        break
            else:
                self.status_bar.showMessage("Failed to associate quick event with image", 5000)
        except Exception as e:
            print(f"Error associating quick event with image: {e}")
            self.status_bar.showMessage(f"Error: {str(e)}", 5000)
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle(self.image_data.get('title') or f"Image {self.image_id}")
        self.resize(1024, 768)  # Increase default size for better viewing
        
        main_layout = QVBoxLayout(self)
        
        # Create tabs
        self.tab_widget = QTabWidget()
        
        # Image tab
        image_tab = QWidget()
        image_layout = QVBoxLayout(image_tab)
        
        # Image view with tagging toolbar
        image_view_layout = QVBoxLayout()
        
        # Tagging toolbar
        tagging_toolbar = QHBoxLayout()
        
        self.tag_mode_button = QPushButton("Tag Character")
        self.tag_mode_button.setCheckable(True)
        self.tag_mode_button.toggled.connect(self.toggle_tag_mode)
        tagging_toolbar.addWidget(self.tag_mode_button)
        
        tagging_toolbar.addStretch()
        
        image_view_layout.addLayout(tagging_toolbar)
        
        # Create the graphics view for image and tags (NEW)
        self.image_view = GraphicsTagView()
        
        # Set minimum size for the view
        self.image_view.setMinimumSize(800, 600)
        
        # Use original pixmap directly - don't scale it
        # This ensures coordinates match exactly with the source image
        print(f"INIT_UI: Setting image with dimensions {self.image_width}x{self.image_height}")
        self.image_view.set_image(self.pixmap, self.image_width, self.image_height)
        
        # Connect signals
        self.image_view.tag_added.connect(self.add_character_tag)
        self.image_view.tag_selected.connect(self.on_tag_selected)
        
        # Add view to layout
        image_view_layout.addWidget(self.image_view)
        
        image_layout.addLayout(image_view_layout)
        
        # Image metadata
        metadata_layout = QHBoxLayout()
        
        # Left side: basic info
        info_layout = QVBoxLayout()
        
        title = self.image_data.get('title', '')
        filename = self.image_data.get('filename', '')
        created_at = self.image_data.get('created_at', '')
        description = self.image_data.get('description', '')
        
        info_layout.addWidget(QLabel(f"<b>Title:</b> {title}"))
        info_layout.addWidget(QLabel(f"<b>Filename:</b> {filename}"))
        info_layout.addWidget(QLabel(f"<b>Created:</b> {created_at}"))
        if description:
            info_layout.addWidget(QLabel(f"<b>Description:</b> {description}"))
            
        metadata_layout.addLayout(info_layout)
        metadata_layout.addStretch()
        
        image_layout.addLayout(metadata_layout)
        
        # Quick Events tab
        quick_events_tab = QWidget()
        quick_events_layout = QVBoxLayout(quick_events_tab)
        
        # Toolbar for quick events
        toolbar_layout = QHBoxLayout()
        
        self.associate_button = QPushButton("Associate Quick Events")
        self.associate_button.clicked.connect(self.associate_quick_events)
        toolbar_layout.addWidget(self.associate_button)
        
        self.create_quick_event_button = QPushButton("Create Quick Event")
        self.create_quick_event_button.clicked.connect(self.create_quick_event)
        toolbar_layout.addWidget(self.create_quick_event_button)
        
        toolbar_layout.addStretch()
        quick_events_layout.addLayout(toolbar_layout)
        
        # Quick events list
        self.quick_events_list = QListWidget()
        self.quick_events_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.quick_events_list.customContextMenuRequested.connect(self.show_quick_event_context_menu)
        quick_events_layout.addWidget(self.quick_events_list)
        
        # Character Tags tab
        tags_tab = QWidget()
        tags_layout = QVBoxLayout(tags_tab)
        
        # Toolbar for character tags
        tags_toolbar_layout = QHBoxLayout()
        
        self.remove_tag_button = QPushButton("Remove Selected Tag")
        self.remove_tag_button.setEnabled(False)
        self.remove_tag_button.clicked.connect(self.remove_selected_tag)
        tags_toolbar_layout.addWidget(self.remove_tag_button)
        
        tags_toolbar_layout.addStretch()
        tags_layout.addLayout(tags_toolbar_layout)
        
        # Character tags list
        self.character_tags_list = QListWidget()
        self.character_tags_list.itemClicked.connect(self.on_tag_list_item_clicked)
        tags_layout.addWidget(self.character_tags_list)
        
        # Add tabs
        self.tab_widget.addTab(image_tab, "Image")
        self.tab_widget.addTab(quick_events_tab, "Quick Events")
        self.tab_widget.addTab(tags_tab, "Character Tags")
        
        main_layout.addWidget(self.tab_widget)
        
        # Add status bar to the bottom of the dialog
        main_layout.addWidget(self.status_bar)
        
        # Create close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        
        # Add button to layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        main_layout.addLayout(button_layout)
    
    def toggle_tag_mode(self, enabled):
        """Toggle character tagging mode.
        
        Args:
            enabled: Whether tag mode is enabled
        """
        # Enable tag mode on the image view
        self.image_view.enable_tag_mode(enabled)
        
        if enabled:
            # Show help message with detailed instructions
            help_message = "Click on a character's face to tag them. "
            help_message += "You can add multiple tags by clicking different faces. "
            help_message += "Tags will appear in the Character Tags tab."
            self.statusBar().showMessage(help_message)
            
            # Switch to the Image tab to make tagging easier
            if self.tab_widget.currentIndex() != 0:  # If not already on Image tab
                self.tab_widget.setCurrentIndex(0)  # Switch to Image tab
        else:
            self.statusBar().showMessage("")
            
    def load_character_tags(self):
        """Load character tags for this image."""
        try:
            # Import the function to get image character tags
            from app.db_sqlite import get_image_character_tags
            
            # Fetch tags from the database using the correct function
            self.character_tags = get_image_character_tags(self.db_conn, self.image_id)
            
            # Add them to the image view
            self.image_view.set_tags(self.character_tags)
            
            # Update the character tags list
            self.update_character_tags_list()
            
        except Exception as e:
            print(f"Error loading character tags: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load character tags: {str(e)}")
    
    def save_all_tag_crops(self):
        """Save crops of all tag rectangles for debugging."""
        # for tag in self.character_tags:
        #     tag_id = tag['id']
        #     character_name = tag.get('character_name', f"Unknown_{tag_id}")
        #     self.image_view.save_tag_crop(tag_id, character_name)
        pass  # Method disabled
    
    def update_character_tags_list(self):
        """Update the character tags list with current tags."""
        self.character_tags_list.clear()
        
        if not self.character_tags:
            empty_item = QListWidgetItem("No character tags on this image.")
            empty_item.setFlags(Qt.ItemFlag.NoItemFlags)  # Make non-selectable
            self.character_tags_list.addItem(empty_item)
            return
        
        # Add items for each tag
        for tag in self.character_tags:
            character_name = tag.get('character_name', 'Unknown')
            position_text = f"({int(tag['x_position'] * 100)}%, {int(tag['y_position'] * 100)}%)"
            
            item = QListWidgetItem(f"{character_name} {position_text}")
            item.setData(Qt.ItemDataRole.UserRole, tag['id'])
            
            if tag.get('note'):
                item.setToolTip(tag['note'])
                
            self.character_tags_list.addItem(item)
    
    def add_character_tag(self, x_position, y_position):
        """Add a character tag at the given position.
        
        Args:
            x_position: X position (0.0-1.0, center point)
            y_position: Y position (0.0-1.0, center point)
        """
        if not self.story_id:
            QMessageBox.warning(self, "Error", "Cannot determine story ID for this image.")
            return
        
        # Debug info to ensure correct coordinates are being used
        print(f"ADD CHARACTER TAG: Using exact coordinates ({x_position:.4f}, {y_position:.4f})")
        
        # Show character selection dialog
        dialog = CharacterSelectionDialog(
            self.db_conn,
            self.story_id,
            parent=self
        )
        
        if dialog.exec():
            character_id = dialog.get_selected_character_id()
            
            if character_id:
                # Default tag size
                width = 0.1  # 10% of image width
                height = 0.15  # 15% of image height
                
                # CRITICAL: Store exact coordinates without adjustment
                print(f"ADDING TAG TO DATABASE: character_id={character_id}, " +
                      f"position=({x_position:.4f}, {y_position:.4f}), " +
                      f"size=({width:.2f}, {height:.2f})")
                
                # Get character name for crop filename
                character = get_character(self.db_conn, character_id)
                character_name = character.get('name', f"Unknown_{character_id}")
                
                # Add tag to database - coordinates are center point of the tag
                tag_id = add_character_tag_to_image(
                    self.db_conn,
                    self.image_id,
                    character_id,
                    x_position,
                    y_position,
                    width,
                    height,
                    "Added manually"
                )
                
                if tag_id:
                    # Reload tags to update the UI
                    self.load_character_tags()
                    
                    # Save a cropped image of the tag rectangle for debugging
                    # Since we need to wait for the UI to update and the tag rectangle to be created,
                    # we'll use a short timer to allow that to happen
                    QTimer.singleShot(500, lambda: self.image_view.save_tag_crop(tag_id, character_name))
                else:
                    QMessageBox.warning(self, "Error", "Failed to add character tag.")
            else:
                QMessageBox.warning(self, "Error", "No character selected.")
    
    def on_tag_selected(self, tag_id):
        """Handle tag selection on the image.
        
        Args:
            tag_id: ID of the selected tag
        """
        # Select the corresponding item in the list
        for i in range(self.character_tags_list.count()):
            item = self.character_tags_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == tag_id:
                self.character_tags_list.setCurrentItem(item)
                break
                
        # Enable the remove button
        self.remove_tag_button.setEnabled(True)
    
    def on_tag_list_item_clicked(self, item):
        """Handle tag selection in the list.
        
        Args:
            item: Selected list item
        """
        tag_id = item.data(Qt.ItemDataRole.UserRole)
        
        # Select the tag on the image
        self.image_view.selected_tag_id = tag_id
        self.image_view.update()
        
        # Enable the remove button
        self.remove_tag_button.setEnabled(True)
    
    def remove_selected_tag(self):
        """Remove the selected character tag."""
        # Get the selected tag ID
        current_item = self.character_tags_list.currentItem()
        if not current_item:
            return
            
        tag_id = current_item.data(Qt.ItemDataRole.UserRole)
        
        # Confirm deletion
        confirm = QMessageBox.question(
            self,
            "Confirm Removal",
            "Are you sure you want to remove this character tag?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                success = remove_character_tag(self.db_conn, tag_id)
                
                if success:
                    # Reload character tags to update the UI
                    self.load_character_tags()
                    
                    # Disable the remove button
                    self.remove_tag_button.setEnabled(False)
                else:
                    QMessageBox.warning(self, "Error", "Failed to remove character tag.")
            except Exception as e:
                print(f"Error removing character tag: {e}")
                QMessageBox.warning(self, "Error", f"Failed to remove character tag: {str(e)}")
    
    def load_quick_events(self):
        """Load quick events associated with this image."""
        try:
            # Load quick events for this image
            self.quick_events = get_image_quick_events(self.db_conn, self.image_id)
            
            # Load all characters for this story if not already loaded
            if not self.characters and self.story_id:
                self.characters = get_story_characters(self.db_conn, self.story_id)
                
            # Load tagged characters for each quick event
            for event in self.quick_events:
                try:
                    tagged_chars = get_quick_event_tagged_characters(self.db_conn, event['id'])
                    # Add any characters not already in self.characters
                    for char in tagged_chars:
                        if not any(c['id'] == char['id'] for c in self.characters):
                            self.characters.append(char)
                except Exception as e:
                    print(f"Error loading tagged characters for event {event['id']}: {e}")
            
            self.update_quick_events_list()
        except Exception as e:
            print(f"Error loading quick events: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load quick events: {str(e)}")
    
    def update_quick_events_list(self):
        """Update the quick events list with current associations."""
        self.quick_events_list.clear()
        
        if not self.quick_events:
            empty_item = QListWidgetItem("No quick events associated with this image.")
            empty_item.setFlags(Qt.ItemFlag.NoItemFlags)  # Make non-selectable
            self.quick_events_list.addItem(empty_item)
            return
            
        # Group quick events by character
        events_by_character = {}
        for event in self.quick_events:
            character_id = event.get('character_id')
            # Use "Anonymous" for NULL character_id events
            character_name = event.get('character_name') if character_id is not None else "Anonymous"
            
            if character_id not in events_by_character:
                events_by_character[character_id] = {
                    'name': character_name,
                    'events': []
                }
            events_by_character[character_id]['events'].append(event)
            
        # Add items for each character and their events
        for character_id, data in events_by_character.items():
            # Add character header
            header_item = QListWidgetItem(f"--- {data['name']} ---")
            header_item.setFlags(Qt.ItemFlag.NoItemFlags)  # Make non-selectable
            header_item.setBackground(QBrush(QColor(70, 70, 70)))
            self.quick_events_list.addItem(header_item)
            
            # Add events for this character
            for event in data['events']:
                # Format character references in the text
                formatted_text = convert_char_refs_to_mentions(event['text'], self.characters)
                
                item = QListWidgetItem()
                item.setText(formatted_text)
                item.setData(Qt.ItemDataRole.UserRole, event['id'])
                self.quick_events_list.addItem(item)
    
    def associate_quick_events(self):
        """Associate quick events with this image."""
        if not self.story_id:
            QMessageBox.warning(self, "Error", "Cannot determine story ID for this image.")
            return
            
        # Get current associated quick events
        current_quick_event_ids = [event['id'] for event in self.quick_events]
        
        # Show quick event selection dialog
        dialog = QuickEventSelectionDialog(
            self.db_conn,
            self.story_id,
            self.image_id,
            current_quick_event_ids,
            parent=self
        )
        
        if dialog.exec():
            selected_quick_event_ids = dialog.get_selected_quick_event_ids()
            
            try:
                # Remove associations for quick events that were deselected
                for event_id in current_quick_event_ids:
                    if event_id not in selected_quick_event_ids:
                        remove_quick_event_image_association(self.db_conn, event_id, self.image_id)
                
                # Add associations for newly selected quick events
                for event_id in selected_quick_event_ids:
                    if event_id not in current_quick_event_ids:
                        associate_quick_event_with_image(self.db_conn, event_id, self.image_id)
                        
                # Reload quick events to update the UI
                self.load_quick_events()
            except Exception as e:
                print(f"Error managing quick event associations: {e}")
                QMessageBox.warning(self, "Error", f"Failed to update quick event associations: {str(e)}")
    
    def show_quick_event_context_menu(self, position: QPoint):
        """Show context menu for a quick event.
        
        Args:
            position: Position where the menu should be displayed
        """
        item = self.quick_events_list.itemAt(position)
        
        if not item or item.flags() & Qt.ItemFlag.ItemIsSelectable == 0:
            return
            
        quick_event_id = item.data(Qt.ItemDataRole.UserRole)
        
        menu = QMenu(self)
        
        remove_action = QAction("Remove Association", self)
        remove_action.triggered.connect(lambda: self.remove_quick_event_association(quick_event_id))
        menu.addAction(remove_action)
        
        # Show the menu
        menu.exec(QCursor.pos())

    def remove_quick_event_association(self, quick_event_id: int):
        """Remove a quick event association from this image.
        
        Args:
            quick_event_id: ID of the quick event to disassociate
        """
        confirm = QMessageBox.question(
            self,
            "Confirm Removal",
            "Are you sure you want to remove this quick event association?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                success = remove_quick_event_image_association(self.db_conn, quick_event_id, self.image_id)
                
                if success:
                    # Reload quick events to update the UI
                    self.load_quick_events()
                else:
                    QMessageBox.warning(self, "Error", "Failed to remove quick event association.")
            except Exception as e:
                print(f"Error removing quick event association: {e}")
                QMessageBox.warning(self, "Error", f"Failed to remove quick event association: {str(e)}")

    def create_quick_event(self):
        """Create a new quick event and associate it with this image."""
        if not self.story_id:
            QMessageBox.warning(self, "Error", "Cannot determine story ID for this image.")
            return
            
        # Show character selection and quick event editor dialog
        dialog = QuickEventEditor(
            self.db_conn,
            self.story_id,
            self.image_id,
            parent=self
        )
        
        if dialog.exec():
            try:
                # Get the character ID and text
                character_id = dialog.get_character_id()
                text = dialog.get_text()
                
                if not text.strip():
                    QMessageBox.warning(self, "Error", "Quick event text cannot be empty.")
                    return
                
                # Get the next sequence number for this character
                sequence_number = get_next_quick_event_sequence_number(self.db_conn, character_id)
                
                # Create the quick event
                quick_event_id = create_quick_event(
                    self.db_conn,
                    text,
                    character_id,
                    sequence_number
                )
                
                if quick_event_id:
                    # Associate the quick event with this image
                    associate_quick_event_with_image(
                        self.db_conn,
                        quick_event_id,
                        self.image_id
                    )
                    
                    # Process character tags in the text
                    chars_text = text
                    tagged_characters = []
                    
                    for character in self.characters:
                        tag = f"@{character['name']}"
                        if tag in chars_text:
                            # Tag character
                            tagged_character_id = character['id']
                            if tagged_character_id != character_id:  # Don't tag the main character
                                tagged_characters.append(tagged_character_id)
                    
                    # Associate the tagged characters with the quick event
                    # This would typically call a function like associate_character_with_quick_event
                    # For now, we'll just show a message with the tagged characters
                    if tagged_characters:
                        print(f"Tagged characters for quick event {quick_event_id}: {tagged_characters}")
                        
                        # Process character tags in the text
                        process_quick_event_character_tags(self.db_conn, quick_event_id, text)
                    
                    # Reload all characters to ensure we have all characters needed for formatting
                    if self.story_id:
                        self.characters = get_story_characters(self.db_conn, self.story_id)
                    
                    # Reload quick events to update the UI
                    self.load_quick_events()
                    
                    # Switch to the Quick Events tab
                    for i in range(self.tab_widget.count()):
                        if self.tab_widget.tabText(i) == "Quick Events":
                            self.tab_widget.setCurrentIndex(i)
                            break
                else:
                    QMessageBox.warning(self, "Error", "Failed to create quick event.")
            except Exception as e:
                print(f"Error creating quick event: {e}")
                QMessageBox.warning(self, "Error", f"Failed to create quick event: {str(e)}")


class TagSuggestionDialog(QDialog):
    """Dialog for displaying and selecting character tag suggestions."""
    
    def __init__(self, db_conn, character_suggestions: List[Dict[str, Any]], 
                image: QImage, parent=None):
        """Initialize the tag suggestion dialog.
        
        Args:
            db_conn: Database connection
            character_suggestions: List of character suggestion dicts with 'character_id', 
                                  'character_name', and 'similarity' fields
            image: The image being analyzed
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.character_suggestions = character_suggestions
        self.image = image
        self.selected_character_ids = []
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Character Recognition Results")
        self.resize(500, 450)
        
        layout = QVBoxLayout(self)
        
        # Image preview
        preview_label = QLabel()
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Scale image for preview
        preview_pixmap = QPixmap.fromImage(self.image)
        if preview_pixmap.width() > 300 or preview_pixmap.height() > 200:
            preview_pixmap = preview_pixmap.scaled(
                300, 200, 
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        preview_label.setPixmap(preview_pixmap)
        
        layout.addWidget(preview_label)
        
        # Explanation label
        explanation = QLabel(
            "The following characters may appear in this image based on visual similarity. "
            "Select the characters you want to tag in this image."
        )
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        
        # Character list
        self.character_list = QListWidget()
        
        for suggestion in self.character_suggestions:
            item = QListWidgetItem()
            item.setText(f"{suggestion['character_name']} ({int(suggestion['similarity'] * 100)}% match)")
            item.setData(Qt.ItemDataRole.UserRole, suggestion['character_id'])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)  # Default to unchecked
            self.character_list.addItem(item)
        
        layout.addWidget(self.character_list)
        
        # Tag options group
        options_group = QGroupBox("Tagging Options")
        options_layout = QVBoxLayout(options_group)
        
        # Position tag options
        self.tag_position_checkbox = QCheckBox("Add position tags for selected characters")
        self.tag_position_checkbox.setChecked(False)
        options_layout.addWidget(self.tag_position_checkbox)
        
        # Manual positioning option
        self.manual_position_checkbox = QCheckBox("Position tags manually for each character")
        self.manual_position_checkbox.setChecked(False)
        self.manual_position_checkbox.setEnabled(False)  # Only enable when position tags are checked
        options_layout.addWidget(self.manual_position_checkbox)
        
        # Add to recognition database option
        self.add_to_database_checkbox = QCheckBox("Add to character recognition database")
        self.add_to_database_checkbox.setToolTip("Add these characters to the recognition database to improve future identification")
        self.add_to_database_checkbox.setChecked(False)
        options_layout.addWidget(self.add_to_database_checkbox)
        
        # Connect the checkboxes
        self.tag_position_checkbox.stateChanged.connect(self.on_position_checkbox_changed)
        
        # Tag size options
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Tag size:"))
        
        self.tag_size_combo = QComboBox()
        self.tag_size_combo.addItems(["Small (10%)", "Medium (15%)", "Large (20%)"])
        self.tag_size_combo.setCurrentIndex(0)  # Default to small
        self.tag_size_combo.setEnabled(False)  # Only enable when position tags are checked
        size_layout.addWidget(self.tag_size_combo)
        
        options_layout.addLayout(size_layout)
        
        # Add options group to main layout
        layout.addWidget(options_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.tag_button = QPushButton("Tag Selected Characters")
        self.tag_button.clicked.connect(self.accept)
        
        self.skip_button = QPushButton("Skip Tagging")
        self.skip_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.tag_button)
        button_layout.addWidget(self.skip_button)
        
        layout.addLayout(button_layout)
    
    def on_position_checkbox_changed(self, state):
        """Handle changes to the position checkbox state.
        
        Args:
            state: New checkbox state
        """
        enabled = state == Qt.CheckState.Checked.value
        self.manual_position_checkbox.setEnabled(enabled)
        self.tag_size_combo.setEnabled(enabled)
    
    def get_selected_character_ids(self) -> List[int]:
        """Get the IDs of the selected characters.
        
        Returns:
            List of selected character IDs
        """
        self.selected_character_ids = []
        
        for i in range(self.character_list.count()):
            item = self.character_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                character_id = item.data(Qt.ItemDataRole.UserRole)
                self.selected_character_ids.append(character_id)
                
        return self.selected_character_ids
    
    def should_tag_positions(self) -> bool:
        """Check if position tags should be added.
        
        Returns:
            True if position tags should be added
        """
        return self.tag_position_checkbox.isChecked()
    
    def should_position_manually(self) -> bool:
        """Check if tags should be positioned manually.
        
        Returns:
            True if tags should be positioned manually
        """
        return self.manual_position_checkbox.isChecked()
    
    def get_tag_size(self) -> Tuple[float, float]:
        """Get the tag size as a proportion of the image size.
        
        Returns:
            Tuple of (width_proportion, height_proportion)
        """
        index = self.tag_size_combo.currentIndex()
        if index == 0:  # Small
            return (0.1, 0.1)
        elif index == 1:  # Medium
            return (0.15, 0.15)
        else:  # Large
            return (0.2, 0.2)
    
    def should_add_to_database(self) -> bool:
        """Check if characters should be added to the recognition database.
        
        Returns:
            True if characters should be added to the database
        """
        return self.add_to_database_checkbox.isChecked()


class TagPositionDialog(QDialog):
    """Dialog for manually positioning a character tag on an image."""
    
    def __init__(self, image: QImage, character_name: str, 
                 default_size: Tuple[float, float] = (0.1, 0.1), parent=None):
        """Initialize the tag position dialog.
        
        Args:
            image: The image to tag
            character_name: Name of the character being tagged
            default_size: Default tag size as (width_prop, height_prop)
            parent: Parent widget
        """
        super().__init__(parent)
        self.image = image
        self.character_name = character_name
        self.default_size = default_size
        self.tag_rect = None
        self.tag_position = (0.5, 0.5)  # Default center
        self.tag_size = default_size
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle(f"Position Tag: {self.character_name}")
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Instruction label
        instructions = QLabel(
            "Click and drag to position the tag rectangle. "
            "Use mouse wheel to resize. Position the rectangle "
            "so the character face is in the top portion of the rectangle."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Graphics view for image and tag positioning
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Add image to scene
        pixmap = QPixmap.fromImage(self.image)
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)
        
        # Add tag rectangle - initially at the center
        width = self.image.width() * self.default_size[0]
        height = self.image.height() * self.default_size[1]
        x = (self.image.width() - width) / 2
        y = (self.image.height() - height) / 2
        
        self.tag_rect = QGraphicsRectItem(x, y, width, height)
        self.tag_rect.setBrush(QBrush(QColor(0, 255, 0, 100)))  # Semi-transparent green
        self.tag_rect.setPen(QPen(QColor(0, 255, 0), 2))
        self.tag_rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.tag_rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.scene.addItem(self.tag_rect)
        
        # Add character name label
        self.name_item = QGraphicsTextItem(self.character_name)
        self.name_item.setPos(x, y - 20)
        self.name_item.setDefaultTextColor(QColor(255, 255, 255))
        
        # Add a black background for the name
        name_rect = self.name_item.boundingRect()
        self.name_bg = QGraphicsRectItem(x, y - 20, name_rect.width(), name_rect.height())
        self.name_bg.setBrush(QBrush(QColor(0, 0, 0, 200)))
        self.name_bg.setPen(QPen(Qt.PenStyle.NoPen))
        
        self.scene.addItem(self.name_bg)
        self.scene.addItem(self.name_item)
        
        # Add the view to the layout
        layout.addWidget(self.view)
        
        # Fit the view to the scene
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        
        # Connect events
        self.view.wheelEvent = self.wheel_event
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
    def resizeEvent(self, event):
        """Handle resize events to maintain view fit.
        
        Args:
            event: Resize event
        """
        super().resizeEvent(event)
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        
    def wheel_event(self, event):
        """Handle mouse wheel events for resizing the tag rectangle.
        
        Args:
            event: Wheel event
        """
        delta = event.angleDelta().y()
        
        # Get current rect properties
        rect = self.tag_rect.rect()
        center = rect.center()
        width = rect.width()
        height = rect.height()
        
        # Adjust size based on wheel direction
        scale_factor = 1.1 if delta > 0 else 0.9
        new_width = max(20, min(width * scale_factor, self.image.width() * 0.8))
        new_height = max(20, min(height * scale_factor, self.image.height() * 0.8))
        
        # Update rectangle while maintaining center position
        new_x = center.x() - new_width / 2.0  # Use floating point division
        new_y = center.y() - new_height / 2.0  # Use floating point division
        self.tag_rect.setRect(new_x, new_y, new_width, new_height)
        
        # Update name label position
        self.name_item.setPos(new_x, new_y - 20)
        self.name_bg.setPos(new_x, new_y - 20)
    
    def get_tag_position_and_size(self) -> Tuple[float, float, float, float]:
        """Get the normalized tag position and size.
        
        Returns:
            Tuple of (x_position, y_position, width, height) as proportions of image size
        """
        # Get current rect properties
        rect = self.tag_rect.rect()
        img_width = self.image.width()
        img_height = self.image.height()
        
        # Calculate normalized values using floating point division
        # x_position is the center x-coordinate
        x_position = (rect.x() + rect.width() / 2.0) / img_width
        
        # For y_position, we use a position at 10% from the top of the rectangle
        # This better aligns with how we want faces to be positioned
        y_position = (rect.y() + rect.height() * 0.1) / img_height
        
        width = rect.width() / img_width
        height = rect.height() / img_height
        
        # Ensure values are within valid range (0.0-1.0)
        x_position = max(0.0, min(1.0, x_position))
        y_position = max(0.0, min(1.0, y_position))
        width = max(0.01, min(1.0, width))  # Ensure minimum width
        height = max(0.01, min(1.0, height))  # Ensure minimum height
        
        # Log the values
        print(f"TagPositionDialog returns: pos=({x_position:.3f}, {y_position:.3f}), size=({width:.3f}, {height:.3f})")
        
        return (x_position, y_position, width, height)


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
        self.current_story_id: Optional[int] = None
        self.current_story_data: Optional[Dict[str, Any]] = None
        self.thumbnails: Dict[int, ThumbnailWidget] = {}
        
        # Create image recognition utility
        self.image_recognition = ImageRecognitionUtil(db_conn)
        
        # Flag to track NSFW mode
        self.nsfw_mode = False
        
        # Flag to track scene grouping mode
        self.scene_grouping_mode = False
        
        self.init_ui()
    
    def init_ui(self) -> None:
        """Set up the user interface."""
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create button layout
        button_layout = QHBoxLayout()
        
        # Create paste button
        self.paste_button = QPushButton("Paste Image (Ctrl+V)")
        self.paste_button.setToolTip("Paste image from clipboard")
        self.paste_button.clicked.connect(self.paste_image)
        self.paste_button.setEnabled(False)  # Disabled until a story is selected
        button_layout.addWidget(self.paste_button)
        
        # Create import button
        self.import_button = QPushButton("Import Image")
        self.import_button.setToolTip("Import image from file")
        self.import_button.clicked.connect(self.import_image)
        self.import_button.setEnabled(False)  # Disabled until a story is selected
        button_layout.addWidget(self.import_button)
        
        # Create debug button
        self.debug_button = QPushButton("Debug Clipboard")
        self.debug_button.setToolTip("Show clipboard contents for debugging")
        self.debug_button.clicked.connect(self.debug_clipboard)
        button_layout.addWidget(self.debug_button)
        
        # Add recognition database rebuild button
        self.rebuild_recognition_button = QPushButton("Rebuild Recognition DB")
        self.rebuild_recognition_button.setToolTip("Rebuild the character recognition database")
        self.rebuild_recognition_button.clicked.connect(self.rebuild_recognition_database)
        self.rebuild_recognition_button.setEnabled(False)  # Disabled until a story is selected
        button_layout.addWidget(self.rebuild_recognition_button)
        
        # Add spacer to push buttons to the left
        button_layout.addStretch()
        
        # Add NSFW toggle checkbox
        self.nsfw_checkbox = QCheckBox("NSFW Mode")
        self.nsfw_checkbox.setToolTip("Hide thumbnails with placeholders")
        self.nsfw_checkbox.stateChanged.connect(self.on_nsfw_toggle)
        button_layout.addWidget(self.nsfw_checkbox)
        
        # Add Scene Grouping checkbox
        self.scene_grouping_checkbox = QCheckBox("Group by Scenes")
        self.scene_grouping_checkbox.setToolTip("Group thumbnails by their associated scenes")
        self.scene_grouping_checkbox.stateChanged.connect(self.on_scene_grouping_toggle)
        button_layout.addWidget(self.scene_grouping_checkbox)
        
        # Add button layout to main layout
        main_layout.addLayout(button_layout)
        
        # Create scroll area for thumbnails
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create container widget for thumbnails
        self.thumbnails_container = QWidget()
        self.thumbnails_layout = QGridLayout(self.thumbnails_container)
        self.thumbnails_layout.setContentsMargins(10, 10, 10, 10)
        self.thumbnails_layout.setSpacing(10)
        
        # Set fixed column width for the grid layout (5 columns)
        self.thumbnails_container.setMinimumWidth(5 * 200)  # 5 thumbnails of 170px + spacing
        
        # Add container to scroll area
        self.scroll_area.setWidget(self.thumbnails_container)
        
        # Add scroll area to main layout
        main_layout.addWidget(self.scroll_area)
        
        # Create status label
        self.status_label = QLabel("No story selected")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        main_layout.addWidget(self.status_label)
        
        # Create placeholder pixmap for NSFW mode
        self.placeholder_pixmap = self._create_nsfw_placeholder()
    
    def _create_nsfw_placeholder(self) -> QPixmap:
        """Create a placeholder pixmap for NSFW mode.
        
        Returns:
            A plain pixmap with "NSFW" text
        """
        # Create a plain gray pixmap
        pixmap = QPixmap(170, 150)  # Increased from 180, 150
        pixmap.fill(QColor(80, 80, 80))
        
        # Add "NSFW" text
        painter = QPainter(pixmap)
        painter.setPen(QPen(QColor(200, 200, 200)))
        painter.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "Null")
        painter.end()
        
        return pixmap
    
    def on_nsfw_toggle(self, state: int) -> None:
        """Handle NSFW toggle state change.
        
        Args:
            state: Qt.CheckState value
        """
        print(f"NSFW toggle state changed to value: {state}")
        self.nsfw_mode = (state == 2)  # Qt.CheckState.Checked is 2
        print(f"NSFW mode is now: {'ON' if self.nsfw_mode else 'OFF'}")
        
        # Update thumbnails if we have any loaded
        if len(self.thumbnails) > 0:
            print(f"Updating {len(self.thumbnails)} thumbnails")
            for image_id, thumbnail in self.thumbnails.items():
                try:
                    if self.nsfw_mode:
                        # Replace with NSFW placeholder
                        thumbnail.update_pixmap(self.placeholder_pixmap)
                        print(f"Set thumbnail {image_id} to NSFW mode")
                    else:
                        # Restore original thumbnail
                        # Get the original pixmap path
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
                                    thumbnail.update_pixmap(pixmap)
                                    print(f"Restored thumbnail {image_id} to normal mode")
                except Exception as e:
                    print(f"Error updating thumbnail {image_id}: {str(e)}")
    
    def on_scene_grouping_toggle(self, state: int) -> None:
        """Handle scene grouping toggle state change.
        
        Args:
            state: Qt.CheckState value
        """
        print(f"Scene grouping toggle state changed to value: {state}")
        self.scene_grouping_mode = (state == 2)  # Qt.CheckState.Checked is 2
        print(f"Scene grouping mode is now: {'ON' if self.scene_grouping_mode else 'OFF'}")
        
        # Reload images with new grouping layout
        self.load_images()
    
    def update_thumbnail_visibility(self) -> None:
        """Update all thumbnails based on NSFW mode."""
        print(f"Updating thumbnail visibility for {len(self.thumbnails)} thumbnails")
        for image_id, thumbnail in self.thumbnails.items():
            if self.nsfw_mode:
                # Switch to placeholder
                self.set_thumbnail_nsfw(thumbnail)
            else:
                # Restore original image
                self.set_thumbnail_normal(thumbnail, image_id)
    
    def set_thumbnail_nsfw(self, thumbnail: ThumbnailWidget) -> None:
        """Set a thumbnail to NSFW mode.
        
        Args:
            thumbnail: The thumbnail widget to update
        """
        # Scale the placeholder pixmap
        scaled_pixmap = self.placeholder_pixmap.scaled(
            QSize(170, 150),  # Increased from 180, 150
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        # Use the new update_pixmap method to properly update the thumbnail
        thumbnail.update_pixmap(self.placeholder_pixmap)
        print(f"Set thumbnail {thumbnail.image_id} to NSFW mode")
    
    def set_thumbnail_normal(self, thumbnail: ThumbnailWidget, image_id: int) -> None:
        """Restore the normal thumbnail image.
        
        Args:
            thumbnail: The thumbnail widget to update
            image_id: ID of the image
        """
        # Get the original pixmap path
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
                    # Use the new update_pixmap method
                    thumbnail.update_pixmap(pixmap)
                    print(f"Restored thumbnail {image_id} to normal mode")
    
    def set_story(self, story_id: int, story_data: Dict[str, Any]) -> None:
        """Set the current story.
        
        Args:
            story_id: ID of the story
            story_data: Data of the story
        """
        self.current_story_id = story_id
        self.current_story_data = story_data
        
        # Enable buttons
        self.paste_button.setEnabled(True)
        self.import_button.setEnabled(True)
        self.rebuild_recognition_button.setEnabled(True)
        
        # Update status
        self.status_label.setText(f"Gallery for: {story_data['title']}")
        
        # Build the image recognition database for this story's characters
        try:
            self.image_recognition.build_character_image_database()
        except Exception as e:
            print(f"Warning: Failed to build image recognition database: {e}")
        
        # Load images
        self.load_images()
    
    def load_images(self) -> None:
        """Load images for the current story."""
        if not self.current_story_id:
            return
        
        # Clear existing thumbnails
        self.clear_thumbnails()
        
        # Get images from database
        cursor = self.db_conn.cursor()
        cursor.execute(
            "SELECT id, filename, path, title, width, height FROM images WHERE story_id = ? ORDER BY created_at DESC",
            (self.current_story_id,)
        )
        images = cursor.fetchall()
        
        if not self.scene_grouping_mode:
            # Classic view - no scene grouping
            self._display_images_classic_view(images)
        else:
            # Scene grouping view
            self._display_images_with_scene_grouping(images)
            
        # Update status
        if images:
            self.status_label.setText(f"Gallery for: {self.current_story_data['title']} ({len(images)} images)")
        else:
            self.status_label.setText(f"Gallery for: {self.current_story_data['title']} (No images)")
            
        # Ensure the container is properly sized
        self.thumbnails_container.adjustSize()
    
    def _display_images_classic_view(self, images: List[Dict[str, Any]]) -> None:
        """Display images in the classic gallery view (no grouping).
        
        Args:
            images: List of image data dictionaries
        """
        # Create thumbnails
        for i, image in enumerate(images):
            image_id = image['id']
            
            # Get thumbnail pixmap
            pixmap = self._get_image_thumbnail_pixmap(image)
            if pixmap.isNull():
                continue
                
            # Create thumbnail widget
            row = i // 5  # 5 thumbnails per row
            col = i % 5
            thumbnail = ThumbnailWidget(image_id, pixmap, image['title'])
            thumbnail.clicked.connect(self.on_thumbnail_clicked)
            thumbnail.delete_requested.connect(self.on_delete_image)
            
            # Add to layout
            self.thumbnails_layout.addWidget(thumbnail, row, col)
            self.thumbnails[image_id] = thumbnail
            
            # Load quick events for this image
            self._set_thumbnail_quick_event_text(thumbnail, image_id)
        
        # Ensure columns have equal width
        for col in range(5):
            self.thumbnails_layout.setColumnStretch(col, 1)
    
    def _display_images_with_scene_grouping(self, images: List[Dict[str, Any]]) -> None:
        """Display images grouped by scenes.
        
        Args:
            images: List of image data dictionaries
        """
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
            (self.current_story_id,)
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
        
        # Get all quick event associations for all images
        image_ids = [image['id'] for image in images]
        image_quick_events = {}
        for image_id in image_ids:
            quick_events = get_image_quick_events(self.db_conn, image_id)
            if quick_events:
                image_quick_events[image_id] = quick_events
        
        # Find scenes for each image through its quick events
        image_scenes = {}
        for image_id, quick_events in image_quick_events.items():
            for quick_event in quick_events:
                scenes_for_quick_event = get_quick_event_scenes(self.db_conn, quick_event['id'])
                if scenes_for_quick_event:
                    # Associate image with all scenes containing the quick event
                    if image_id not in image_scenes:
                        image_scenes[image_id] = set()
                    for scene in scenes_for_quick_event:
                        image_scenes[image_id].add((scene['id'], scene['title'], scene['sequence_number']))
        
        # If we have no scenes defined, treat all images as orphans
        if not scenes:
            row = 0
            separator = SeparatorWidget("Ungrouped")
            self.thumbnails_layout.addWidget(separator, row, 0, 1, 5)  # Span all 5 columns
            row += 1
            
            self._display_image_list(images, row)
            return
        
        # Group images by scene
        scene_images = {}
        orphan_images = []
        
        for image in images:
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
        
        # If we have no images in any scenes, treat all images as orphans
        if not scene_images:
            row = 0
            separator = SeparatorWidget("Ungrouped")
            self.thumbnails_layout.addWidget(separator, row, 0, 1, 5)  # Span all 5 columns
            row += 1
            
            self._display_image_list(orphan_images, row)
            return
        
        # Sort scenes by sequence number (newest first)
        sorted_scenes = sorted(
            scene_images.items(),
            key=lambda x: x[1]['sequence_number'],
            reverse=True
        )
        
        # Now create a chronological display order with scenes and ungrouped images interspersed
        display_order = []
        
        # First, organize orphaned images by timestamp
        orphan_images_by_timestamp = {}
        for image in orphan_images:
            timestamp = image['created_at']
            if timestamp not in orphan_images_by_timestamp:
                orphan_images_by_timestamp[timestamp] = []
            orphan_images_by_timestamp[timestamp].append(image)
        
        # Then find cutpoints between scenes for placing orphaned images
        scene_timestamps = [(scene_id, data['newest_timestamp']) for scene_id, data in scene_images.items()]
        scene_timestamps.sort(key=lambda x: x[1], reverse=True)  # Sort by timestamp, newest first
        
        # If we have scene timestamps, add the first scene
        if scene_timestamps:
            first_scene_id = scene_timestamps[0][0]
            display_order.append(('scene', first_scene_id))
            
            # Find orphan images that need to go above the first scene
            orphans_before_first = []
            for image in orphan_images:
                if image['created_at'] > scene_timestamps[0][1]:
                    orphans_before_first.append(image)
            
            # If we have orphans before the first scene, add them at the very top
            if orphans_before_first:
                display_order.insert(0, ('ungrouped', orphans_before_first))
        
        # Now handle remaining scenes and orphans
        for i in range(len(scene_timestamps) - 1):
            current_scene_id, current_timestamp = scene_timestamps[i]
            next_scene_id, next_timestamp = scene_timestamps[i + 1]
            
            # Find orphan images that belong between these two scenes
            orphans_between = []
            for image in orphan_images:
                if next_timestamp < image['created_at'] < current_timestamp:
                    orphans_between.append(image)
            
            if orphans_between:
                display_order.append(('ungrouped', orphans_between))
            
            # Add the next scene
            display_order.append(('scene', next_scene_id))
            
        # Find orphan images that need to go below the last scene
        if scene_timestamps:
            last_scene_id, last_timestamp = scene_timestamps[-1]
            orphans_after_last = []
            for image in orphan_images:
                if image['created_at'] < last_timestamp:
                    orphans_after_last.append(image)
            
            # If we have orphans after the last scene, add them at the very bottom
            if orphans_after_last:
                display_order.append(('ungrouped', orphans_after_last))
        
        # Now display everything according to our calculated order
        row = 0
        for item_type, item_data in display_order:
            if item_type == 'scene':
                scene_id = item_data
                scene_data = scene_images[scene_id]
                
                # Add a separator for this scene
                separator = SeparatorWidget(scene_data['title'])
                self.thumbnails_layout.addWidget(separator, row, 0, 1, 5)  # Span all 5 columns
                row += 1
                
                # Display this scene's images
                row = self._display_image_list(scene_data['images'], row)
                
                # Add some spacing
                row += 1
            
            elif item_type == 'ungrouped':
                ungrouped_images = item_data
                if ungrouped_images:
                    # Add separator for ungrouped images
                    separator = SeparatorWidget("Ungrouped")
                    self.thumbnails_layout.addWidget(separator, row, 0, 1, 5)  # Span all 5 columns
                    row += 1
                    
                    # Display ungrouped images
                    row = self._display_image_list(ungrouped_images, row)
                    
                    # Add some spacing
                    row += 1
        
        # Ensure columns have equal width
        for col in range(5):
            self.thumbnails_layout.setColumnStretch(col, 1)
    
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
        if result and result['newest_timestamp']:
            return result['newest_timestamp']
        else:
            # If no quick events found, use scene creation date
            cursor.execute("""
                SELECT created_at FROM events
                WHERE id = ?
            """, (scene_id,))
            
            result = cursor.fetchone()
            if result and result['created_at']:
                return result['created_at']
            
            # Last resort fallback
            return '1970-01-01 00:00:00'
    
    def _display_image_list(self, images: List[Dict[str, Any]], start_row: int) -> int:
        """Display a list of images starting at the specified row.
        
        Args:
            images: List of image data dictionaries
            start_row: Starting row index
            
        Returns:
            The next available row index
        """
        row = start_row
        for i, image in enumerate(images):
            image_id = image['id']
            pixmap = self._get_image_thumbnail_pixmap(image)
            if pixmap.isNull():
                continue
                
            col = i % 5
            if col == 0 and i > 0:
                row += 1
                
            thumbnail = ThumbnailWidget(image_id, pixmap, image['title'])
            thumbnail.clicked.connect(self.on_thumbnail_clicked)
            thumbnail.delete_requested.connect(self.on_delete_image)
            
            self.thumbnails_layout.addWidget(thumbnail, row, col)
            self.thumbnails[image_id] = thumbnail
            
            self._set_thumbnail_quick_event_text(thumbnail, image_id)
        
        # Move to next row for future content
        if images and len(images) % 5 != 0:
            row += 1
            
        return row
    
    def _get_image_thumbnail_pixmap(self, image: Dict[str, Any]) -> QPixmap:
        """Get the thumbnail pixmap for an image.
        
        Args:
            image: Image data dictionary
            
        Returns:
            QPixmap object of the thumbnail, possibly a placeholder if in NSFW mode
        """
        # Choose pixmap based on NSFW mode
        if self.nsfw_mode:
            return self.placeholder_pixmap
            
        # Get thumbnail path
        filename = image['filename']
        thumbnails_folder = os.path.join(os.path.dirname(image['path']), "thumbnails")
        thumbnail_path = os.path.join(thumbnails_folder, filename)
        
        # Check if thumbnail exists, if not, generate it
        if not os.path.exists(thumbnail_path):
            # Load original image
            original_path = os.path.join(image['path'], filename)
            if os.path.exists(original_path):
                original_image = QImage(original_path)
                if not original_image.isNull():
                    # Generate and save thumbnail
                    thumbnail = self._generate_thumbnail(original_image)
                    os.makedirs(thumbnails_folder, exist_ok=True)
                    thumbnail.save(thumbnail_path, "PNG")
                else:
                    print(f"Warning: Failed to load original image: {original_path}")
                    return QPixmap()
            else:
                print(f"Warning: Original image not found: {original_path}")
                return QPixmap()
        
        # Load the thumbnail pixmap
        pixmap = QPixmap(thumbnail_path)
        return pixmap
    
    def _set_thumbnail_quick_event_text(self, thumbnail: ThumbnailWidget, image_id: int) -> None:
        """Set the quick event text for a thumbnail widget.
        
        Args:
            thumbnail: The thumbnail widget
            image_id: ID of the image
        """
        try:
            quick_events = get_image_quick_events(self.db_conn, image_id)
            if quick_events:
                # Get all characters to format mentions
                characters = get_story_characters(self.db_conn, self.current_story_id)
                
                # Format the first quick event's text
                first_event = quick_events[0]
                formatted_text = convert_char_refs_to_mentions(first_event['text'], characters)
                
                # Set the quick event text on the thumbnail
                thumbnail.set_quick_event_text(formatted_text)
        except Exception as e:
            print(f"Error loading quick events for image {image_id}: {e}")
    
    def clear_thumbnails(self) -> None:
        """Clear all thumbnails and separators."""
        # Remove all widgets from layout
        for i in reversed(range(self.thumbnails_layout.count())):
            widget = self.thumbnails_layout.itemAt(i).widget()
            if widget:
                self.thumbnails_layout.removeWidget(widget)
                widget.deleteLater()
        
        # Clear thumbnails dictionary
        self.thumbnails.clear()
    
    def keyPressEvent(self, event) -> None:
        """Handle keyboard events."""
        if event.key() == Qt.Key.Key_V and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.paste_image()
        else:
            super().keyPressEvent(event)
    
    def paste_image(self) -> None:
        """Paste image from clipboard."""
        if not self.current_story_id:
            return
        
        # Get clipboard
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        # Debug clipboard contents
        formats = mime_data.formats()
        print(f"Clipboard formats: {formats}")
        
        if mime_data.hasImage():
            # Get image from clipboard
            image = clipboard.image()
            
            if not image.isNull():
                # Save image
                self.save_image_to_story(image)
            else:
                self.show_error("Invalid Image", "The clipboard contains an invalid image.")
        elif mime_data.hasUrls():
            # Try to handle URLs (common when copying from browsers)
            urls = mime_data.urls()
            if urls and urls[0].isLocalFile():
                file_path = urls[0].toLocalFile()
                print(f"Found local file path: {file_path}")
                
                # Check if it's an image file by extension
                image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']
                if any(file_path.lower().endswith(ext) for ext in image_extensions):
                    # Try to load the image from the file
                    try:
                        image = QImage(file_path)
                        if not image.isNull():
                            self.save_image_to_story(image)
                        else:
                            self.show_error("Invalid Image", f"Could not load image from {file_path}")
                    except Exception as e:
                        self.show_error("Error", f"Failed to load image: {str(e)}")
                else:
                    self.show_error("Not an Image", f"The file {file_path} is not a recognized image format.")
            elif urls:
                # Handle remote URLs - try to download the image
                try:
                    url = urls[0].toString()
                    if any(url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']):
                        # Create a message box to show download progress
                        msg = QMessageBox(self)
                        msg.setWindowTitle("Downloading Image")
                        msg.setText(f"Downloading image from {url}...")
                        msg.setStandardButtons(QMessageBox.StandardButton.NoButton)
                        msg.show()
                        
                        # Create network manager
                        self.network_manager = QNetworkAccessManager()
                        self.network_manager.finished.connect(lambda reply: self._handle_network_reply(reply, msg))
                        
                        # Start download
                        self.network_manager.get(QNetworkRequest(QUrl(url)))
                    else:
                        self.show_error("Not an Image URL", "The URL does not point to a recognized image format.")
                except ImportError:
                    self.show_error("Network Support Missing", "Network support is not available.")
        elif mime_data.hasHtml():
            # Try to extract image URLs from HTML
            html = mime_data.html()
            image_urls = self._extract_image_urls_from_html(html)
            
            if image_urls:
                # Use the first image URL
                url = image_urls[0]
                try:
                    # Create a message box to show download progress
                    msg = QMessageBox(self)
                    msg.setWindowTitle("Downloading Image")
                    msg.setText(f"Downloading image from {url}...")
                    msg.setStandardButtons(QMessageBox.StandardButton.NoButton)
                    msg.show()
                    
                    # Create network manager
                    self.network_manager = QNetworkAccessManager()
                    self.network_manager.finished.connect(lambda reply: self._handle_network_reply(reply, msg))
                    
                    # Start download
                    self.network_manager.get(QNetworkRequest(QUrl(url)))
                except Exception as e:
                    self.show_error("Download Failed", f"Failed to download image: {str(e)}")
            else:
                self.show_error("No Image", "No image found in HTML content.")
        elif mime_data.hasFormat("text/plain"):
            # Check if the text is a file path or URL to an image
            text = mime_data.text().strip()
            
            # Check if it's a local file path
            if os.path.isfile(text):
                image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']
                if any(text.lower().endswith(ext) for ext in image_extensions):
                    try:
                        image = QImage(text)
                        if not image.isNull():
                            self.save_image_to_story(image)
                        else:
                            self.show_error("Invalid Image", f"Could not load image from {text}")
                    except Exception as e:
                        self.show_error("Error", f"Failed to load image: {str(e)}")
                else:
                    self.show_error("Not an Image", f"The file {text} is not a recognized image format.")
            # Check if it's a URL to an image
            elif text.startswith(("http://", "https://")) and any(text.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']):
                try:
                    # Create a message box to show download progress
                    msg = QMessageBox(self)
                    msg.setWindowTitle("Downloading Image")
                    msg.setText(f"Downloading image from {text}...")
                    msg.setStandardButtons(QMessageBox.StandardButton.NoButton)
                    msg.show()
                    
                    # Create network manager
                    self.network_manager = QNetworkAccessManager()
                    self.network_manager.finished.connect(lambda reply: self._handle_network_reply(reply, msg))
                    
                    # Start download
                    self.network_manager.get(QNetworkRequest(QUrl(text)))
                except Exception as e:
                    self.show_error("Download Failed", f"Failed to download image: {str(e)}")
            else:
                self.show_error("No Image", "No image found in clipboard. Copy an image first.")
        else:
            self.show_error("No Image", "No image found in clipboard. Copy an image first.")
    
    def _handle_network_reply(self, reply, msg_box):
        """Handle network reply when downloading an image.
        
        Args:
            reply: Network reply
            msg_box: Message box showing download progress
        """
        # Close the progress message box
        msg_box.close()
        
        if reply.error() == QNetworkReply.NetworkError.NoError:
            # Read the image data
            image_data = reply.readAll()
            
            # Create QImage from data
            image = QImage()
            if image.loadFromData(image_data):
                self.save_image_to_story(image)
            else:
                self.show_error("Invalid Image", "The downloaded data is not a valid image.")
        else:
            self.show_error("Download Failed", f"Failed to download image: {reply.errorString()}")
        
        # Clean up
        reply.deleteLater()
    
    def import_image(self) -> None:
        """Import image from file."""
        if not self.current_story_id:
            return
        
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        
        if file_path:
            # Load image
            image = QImage(file_path)
            if not image.isNull():
                # Save image
                self.save_image_to_story(image)
            else:
                self.show_error("Invalid Image", "The selected file is not a valid image.")
    
    def save_image_to_story(self, image: QImage) -> None:
        """Save image to story folder and database.
        
        Args:
            image: The image to save
        """
        if not self.current_story_id or not self.current_story_data:
            self.show_error("No Story Selected", "Please select a story before adding images.")
            return
            
        try:
            # Generate a unique filename
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            rand_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            filename = f"image_{timestamp}_{rand_suffix}.png"
            
            # Get story folder paths
            from app.db_sqlite import get_story_folder_paths, create_image, add_character_tag_to_image
            
            # Get story folder paths using the correct function signature
            path_lookup = get_story_folder_paths(self.current_story_data)
            
            # Check if required paths exist
            if not path_lookup or not path_lookup.get('images_folder') or not path_lookup.get('thumbnails_folder'):
                self.show_error("Error", "Could not determine story image folders.")
                return
                
            # Create paths
            images_path = path_lookup['images_folder']
            thumbnails_path = path_lookup['thumbnails_folder']
            
            # Ensure directories exist
            os.makedirs(images_path, exist_ok=True)
            os.makedirs(thumbnails_path, exist_ok=True)
            
            # Save original image
            full_path = os.path.join(images_path, filename)
            if not image.save(full_path, "PNG"):
                self.show_error("Save Failed", "Failed to save image file.")
                return
                
            # Generate and save thumbnail
            thumbnail = self._generate_thumbnail(image)
            thumbnail_path = os.path.join(thumbnails_path, filename)
            if not thumbnail.save(thumbnail_path, "PNG"):
                self.show_error("Save Failed", "Failed to save thumbnail.")
                os.remove(full_path)  # Clean up the original file
                return
                
            # Save to database
            image_id = create_image(
                self.db_conn,
                filename=filename,
                path=images_path,
                story_id=self.current_story_id,
                title="",  # Default empty title
                description="",  # Default empty description
                width=image.width(),
                height=image.height()
            )
            
            if not image_id:
                self.show_error("Database Error", "Failed to add image to database.")
                # Clean up files
                os.remove(full_path)
                os.remove(thumbnail_path)
                return
                
            # Run face detection to find possible character regions
            # Use a progress dialog for longer operations
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
            
            # Do character recognition 
            region_dialog = RegionSelectionDialog(self.db_conn, image, self.current_story_id, self, image_id=image_id)
            
            progress_dialog.setValue(100)
            progress_dialog.close()
            
            if region_dialog.exec():
                # Get selected character data and quick event information
                result_data = region_dialog.get_selected_character_data()
                character_data = result_data.get('characters', [])
                quick_event_id = result_data.get('quick_event_id')
                
                if character_data:
                    try:
                        # Process each selected character
                        for character in character_data:
                            character_id = character['character_id']
                            region = character['region']
                            
                            # Debug info
                            print(f"Adding tag for {character['character_name']} at position: ", 
                                  f"x={region['x']}, y={region['y']}, width={region['width']}, height={region['height']}")
                            
                            # Add the character tag to the image with the region coordinates
                            # The x and y values from region are already the center point
                            tag_id = add_character_tag_to_image(
                                self.db_conn,
                                image_id,
                                character_id,
                                region['x'],  # Already center X (normalized)
                                region['y'],  # Already center Y (normalized)
                                region['width'],  # Width (normalized)
                                region['height'],  # Height (normalized)
                                f"Auto-detected with {int(character['similarity'] * 100)}% confidence"
                            )
                            
                            print(f"Successfully added tag with ID: {tag_id}")
                            
                        # If a quick event was selected, associate it with the image
                        if quick_event_id:
                            self.associate_quick_event_with_image(image_id, quick_event_id)
                    except Exception as e:
                        print(f"Error saving character tags: {e}")
                        self.show_error("Error", f"Error saving character tags: {str(e)}")
            
            # Reload images to show the new one
            self.load_images()
            
        except Exception as e:
            self.show_error("Error", f"Failed to save image: {str(e)}")
            print(f"Error saving image: {e}")
    
    def associate_quick_event_with_image(self, image_id: int, quick_event_id: int) -> None:
        """Associate a quick event with an image.
        
        Args:
            image_id: ID of the image
            quick_event_id: ID of the quick event
        """
        try:
            from app.db_sqlite import associate_quick_event_with_image
            
            # Associate the quick event with the image
            success = associate_quick_event_with_image(
                self.db_conn,
                quick_event_id,
                image_id
            )
            
            if success:
                print(f"Successfully associated quick event {quick_event_id} with image {image_id}")
            else:
                print(f"Failed to associate quick event {quick_event_id} with image {image_id}")
                
        except Exception as e:
            print(f"Error associating quick event with image: {e}")
            self.show_error("Error", f"Error associating quick event with image: {str(e)}")
    
    def _generate_thumbnail(self, image: QImage, max_dimension: int = 320) -> QImage:
        """Generate a thumbnail from an image.
        
        Args:
            image: Original image
            max_dimension: Maximum dimension (width or height) for the thumbnail
            
        Returns:
            Thumbnail image
        """
        # Get original dimensions
        width = image.width()
        height = image.height()
        
        # Calculate new dimensions while maintaining aspect ratio
        if width > height:
            # Landscape orientation
            if width > max_dimension:
                new_width = max_dimension
                new_height = int(height * (max_dimension / width))
            else:
                # Image is already smaller than max dimension
                return image.copy()
        else:
            # Portrait orientation
            if height > max_dimension:
                new_height = max_dimension
                new_width = int(width * (max_dimension / height))
            else:
                # Image is already smaller than max dimension
                return image.copy()
        
        # Create scaled image with smooth transformation
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
            # Get image data
            cursor = self.db_conn.cursor()
            cursor.execute('''
            SELECT * FROM images WHERE id = ?
            ''', (image_id,))
            
            image_data = cursor.fetchone()
            
            if not image_data:
                self.show_error("Image Not Found", f"Image with ID {image_id} not found.")
                return
            
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
            
            # Show image detail dialog
            dialog = ImageDetailDialog(
                self.db_conn,
                image_id,
                image_data,
                pixmap,
                parent=self
            )
            
            # Check for character tags
            try:
                character_tags = get_image_character_tags(self.db_conn, image_id)
                print(f"Character tags found for image {image_id}: {len(character_tags)}")
                for tag in character_tags:
                    print(f"  Tag ID: {tag['id']}, Character: {tag.get('character_name', 'Unknown')}, " 
                          f"Position: ({tag['x_position']}, {tag['y_position']})")
            except Exception as e:
                print(f"Error checking image tags: {e}")
            
            dialog.exec()
            
        except Exception as e:
            self.show_error("Error", f"An error occurred: {str(e)}")
            
    def on_thumbnail_context_menu(self, position: QPoint, thumbnail: ThumbnailWidget) -> None:
        """Show context menu for a thumbnail.
        
        Args:
            position: Position where to show the menu
            thumbnail: The thumbnail widget that was right-clicked
        """
        image_id = thumbnail.image_id
        
        menu = QMenu()
        
        # Add options to the context menu
        view_action = QAction("View Image", self)
        view_action.triggered.connect(lambda: self.on_thumbnail_clicked(image_id))
        menu.addAction(view_action)
        
        tag_characters_action = QAction("Tag Characters", self)
        tag_characters_action.triggered.connect(lambda: self.open_image_for_tagging(image_id))
        menu.addAction(tag_characters_action)
        
        delete_action = QAction("Delete Image", self)
        delete_action.triggered.connect(lambda: self.on_delete_image(image_id))
        menu.addAction(delete_action)
        
        menu.exec(thumbnail.mapToGlobal(position))
        
    def open_image_for_tagging(self, image_id: int) -> None:
        """Open the image detail dialog with the Character Tags tab active.
        
        Args:
            image_id: ID of the image to tag
        """
        try:
            # Get image data
            cursor = self.db_conn.cursor()
            cursor.execute('''
            SELECT * FROM images WHERE id = ?
            ''', (image_id,))
            
            image_data = cursor.fetchone()
            
            if not image_data:
                self.show_error("Image Not Found", f"Image with ID {image_id} not found.")
                return
            
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
            
            # Show image detail dialog
            dialog = ImageDetailDialog(
                self.db_conn,
                image_id,
                image_data,
                pixmap,
                parent=self
            )
            
            # Switch to the Character Tags tab (index 2)
            dialog.tab_widget.setCurrentIndex(2)
            
            # Enable tag mode automatically
            dialog.tag_mode_button.setChecked(True)
            
            dialog.exec()
            
        except Exception as e:
            self.show_error("Error", f"An error occurred: {str(e)}")
            
    def on_delete_image(self, image_id: int) -> None:
        """Handle image deletion.
        
        Args:
            image_id: ID of the image to delete
        """
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this image?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Get image from database
            cursor = self.db_conn.cursor()
            cursor.execute(
                "SELECT filename, path FROM images WHERE id = ?",
                (image_id,)
            )
            image = cursor.fetchone()
            
            if image:
                # Delete original file
                image_path = os.path.join(image['path'], image['filename'])
                if os.path.exists(image_path):
                    try:
                        os.remove(image_path)
                    except Exception as e:
                        self.show_error("Delete Failed", f"Failed to delete image file: {str(e)}")
                        return
                
                # Delete thumbnail file
                thumbnails_folder = os.path.join(os.path.dirname(image['path']), "thumbnails")
                thumbnail_path = os.path.join(thumbnails_folder, image['filename'])
                if os.path.exists(thumbnail_path):
                    try:
                        os.remove(thumbnail_path)
                    except Exception as e:
                        print(f"Warning: Failed to delete thumbnail file: {str(e)}")
                
                # Delete from database
                cursor.execute("DELETE FROM images WHERE id = ?", (image_id,))
                self.db_conn.commit()
                
                # Remove thumbnail
                if image_id in self.thumbnails:
                    thumbnail = self.thumbnails[image_id]
                    self.thumbnails_layout.removeWidget(thumbnail)
                    thumbnail.deleteLater()
                    del self.thumbnails[image_id]
                
                # Reload images to update layout
                self.load_images()
    
    def show_error(self, title: str, message: str) -> None:
        """Show error message.
        
        Args:
            title: Error title
            message: Error message
        """
        QMessageBox.critical(self, title, message)
    
    def debug_clipboard(self) -> None:
        """Show clipboard contents for debugging."""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        # Get all formats
        formats = mime_data.formats()
        
        # Build debug message
        debug_text = "Clipboard Contents:\n\n"
        debug_text += f"Available Formats: {', '.join(formats)}\n\n"
        
        # Check for image
        debug_text += f"Has Image: {mime_data.hasImage()}\n"
        
        # Check for URLs
        if mime_data.hasUrls():
            urls = mime_data.urls()
            debug_text += f"URLs ({len(urls)}):\n"
            for url in urls:
                debug_text += f"  - {url.toString()}"
                if url.isLocalFile():
                    debug_text += f" (Local File: {url.toLocalFile()})"
                debug_text += "\n"
        
        # Check for text
        if mime_data.hasText():
            text = mime_data.text()
            if len(text) > 500:
                text = text[:500] + "... (truncated)"
            debug_text += f"\nText Content:\n{text}\n"
        
        # Check for HTML
        if mime_data.hasHtml():
            html = mime_data.html()
            if len(html) > 500:
                html = html[:500] + "... (truncated)"
            debug_text += f"\nHTML Content:\n{html}\n"
        
        # Show raw data for each format
        debug_text += "\nRaw Format Data:\n"
        for format_name in formats:
            try:
                data = mime_data.data(format_name)
                if data:
                    size = data.size()
                    debug_text += f"  - {format_name}: {size} bytes\n"
                    
                    # Try to decode as text if small enough
                    if size < 1000 and not format_name.startswith("application/"):
                        try:
                            text_data = bytes(data).decode('utf-8', errors='replace')
                            debug_text += f"    Content: {text_data[:100]}"
                            if len(text_data) > 100:
                                debug_text += "... (truncated)"
                            debug_text += "\n"
                        except Exception as e:
                            debug_text += f"    Error decoding: {str(e)}\n"
            except Exception as e:
                debug_text += f"  - {format_name}: Error: {str(e)}\n"
        
        # Show in a message box
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Clipboard Debug Information")
        msg_box.setText(debug_text)
        msg_box.setDetailedText(debug_text)  # Also add as detailed text for easy copying
        msg_box.exec()
        
        # Print to console for logging
        print(debug_text)
    
    def _extract_image_urls_from_html(self, html: str) -> List[str]:
        """Extract image URLs from HTML content.
        
        Args:
            html: HTML content
            
        Returns:
            List of image URLs
        """
        import re
        
        # Find all img tags
        img_tags = re.findall(r'<img[^>]+src="([^"]+)"', html)
        
        # Find all background images
        bg_images = re.findall(r'background-image:\s*url\([\'"]?([^\'"]+)[\'"]?\)', html)
        
        # Combine and filter for image extensions
        all_urls = img_tags + bg_images
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']
        
        # Filter for URLs that end with image extensions or contain image-related paths
        image_urls = []
        for url in all_urls:
            if any(url.lower().endswith(ext) for ext in image_extensions) or '/image' in url.lower():
                # Make sure it's an absolute URL
                if not url.startswith(('http://', 'https://')):
                    # Skip relative URLs for now
                    continue
                image_urls.append(url)
        
        return image_urls 

    def rebuild_recognition_database(self) -> None:
        """Rebuild the character recognition database."""
        if not self.current_story_id:
            QMessageBox.warning(self, "No Story Selected", "Please select a story first.")
            return
            
        # Show a progress dialog
        progress_dialog = QProgressDialog(
            "Rebuilding character recognition database...",
            "Cancel", 0, 100, self
        )
        progress_dialog.setWindowTitle("Building Recognition Database")
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.setMinimumDuration(0)  # Show immediately
        progress_dialog.setValue(0)
        progress_dialog.show()
        QApplication.processEvents()
        
        try:
            # Update progress
            progress_dialog.setValue(10)
            QApplication.processEvents()
            
            # Rebuild the database
            self.image_recognition.build_character_image_database()
            
            # Update progress
            progress_dialog.setValue(90)
            QApplication.processEvents()
            
            # Complete the progress
            progress_dialog.setValue(100)
            QApplication.processEvents()
            
            # Close progress dialog
            progress_dialog.close()
            
            # Show success message
            QMessageBox.information(
                self, 
                "Database Rebuilt", 
                "Character recognition database has been rebuilt successfully."
            )
        except Exception as e:
            # Close progress dialog
            progress_dialog.close()
            
            # Show error message
            QMessageBox.critical(
                self, 
                "Database Rebuild Failed", 
                f"Failed to rebuild character recognition database: {str(e)}"
            )

    def add_region_to_recognition_database(self, image: QImage, character_id: int, 
                                          character_name: str, region: Dict[str, float]) -> None:
        """Add an image region to the character's recognition database.
        
        Args:
            image: The complete image
            character_id: ID of the character
            character_name: Name of the character
            region: Region data with normalized coordinates (x, y, width, height)
        """
        try:
            # Convert normalized coordinates back to pixel coordinates
            x = int(region['x'] * image.width())
            y = int(region['y'] * image.height())
            width = int(region['width'] * image.width())
            height = int(region['height'] * image.height())
            
            # Calculate the absolute position of the region for extraction
            left = max(0, int(x - (width / 2)))
            top = max(0, int(y - (height / 2)))
            
            # Extract the region from the image
            region_rect = QRect(left, top, width, height)
            region_image = image.copy(region_rect)
            
            if region_image.isNull() or region_image.width() == 0 or region_image.height() == 0:
                print(f"Warning: Invalid region extracted for {character_name}")
                return
            
            # Extract features from the region
            features = self.image_recognition.extract_features_from_qimage(region_image)
            
            # Save features to database
            feature_id = self.image_recognition.save_character_image_features(
                character_id=character_id,
                features=features,
                is_avatar=False  # Not an avatar, but a tagged region
            )
            
            if feature_id:
                print(f"Added region to recognition database for {character_name} (ID: {character_id}), feature ID: {feature_id}")
                # Success message handled elsewhere to avoid too many popups
            else:
                print(f"Failed to add region to recognition database for {character_name}")
        except Exception as e:
            print(f"Error adding region to recognition database: {e}")
            # Don't show error to user - this is a background operation

    def on_suggest_character_tags(self, image: QImage):
        """Show a dialog for suggesting character tags based on image recognition.
        
        Args:
            image: The image to analyze
        """
        # Skip if no story is selected
        if not self.current_story_id:
            return
        
        try:
            # Extract image features
            features = self.image_recognition.extract_features_from_qimage(image)
            
            # Get character suggestions
            character_suggestions = self.image_recognition.identify_characters_in_image(
                features,
                threshold=0.6,  # Moderate threshold
                story_id=self.current_story_id
            )
            
            if not character_suggestions:
                QMessageBox.information(
                    self,
                    "No Characters Recognized",
                    "No characters were recognized in this image. "
                    "Try rebuilding the recognition database or adjusting the image.",
                    QMessageBox.StandardButton.Ok
                )
                return
            
            # Show the suggestion dialog
            dialog = TagSuggestionDialog(
                self.db_conn,
                character_suggestions,
                image,
                self
            )
            
            if dialog.exec():
                # Get the selected character IDs
                selected_character_ids = dialog.get_selected_character_ids()
                
                if not selected_character_ids:
                    return
                
                # Check if we should add the characters to the database
                add_to_database = dialog.should_add_to_database()
                
                # Process each selected character
                for character_id in selected_character_ids:
                    # Find the character data
                    character_data = next(
                        (c for c in character_suggestions if c['character_id'] == character_id),
                        None
                    )
                    
                    if character_data:
                        # If character should be added to database, extract and save features
                        if add_to_database:
                            # Extract features and add to recognition database
                            self.image_recognition.save_character_image_features(
                                character_id=character_id,
                                features=features,
                                is_avatar=False
                            )
                            print(f"Added image features to recognition database for {character_data['character_name']}")
                
                return True
        except Exception as e:
            print(f"Error suggesting character tags: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to suggest character tags: {str(e)}",
                QMessageBox.StandardButton.Ok
            )
        
        return False


class RegionSelectionDialog(QDialog):
    """Dialog for manually selecting regions to recognize characters in."""
    
    def __init__(self, db_conn, image: QImage, story_id: int, parent=None, image_id: Optional[int] = None):
        """Initialize the region selection dialog.
        
        Args:
            db_conn: Database connection
            image: The image to analyze
            story_id: The ID of the current story
            parent: Parent widget
            image_id: Optional ID of the image being processed
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.image = image
        self.story_id = story_id
        self.selected_regions = []
        self.current_region = None
        self.dragging = False
        self.tagged_characters = []  # Store characters that have been tagged
        
        # Quick events data
        self.characters = []
        self.quick_events = []
        self.associated_quick_event_id = None  # ID of the selected quick event
        self.new_quick_event_id = None  # ID of a newly created quick event
        
        # Image recognition utility
        self.image_recognition = ImageRecognitionUtil(db_conn)
        
        # Set image_id - try multiple sources
        self.image_id = image_id
        
        # If image_id is not provided directly, try to get it from parent
        if not self.image_id:
            if parent and hasattr(parent, 'image_id'):
                self.image_id = parent.image_id
            elif parent and hasattr(parent, 'selected_image_id'):
                self.image_id = parent.selected_image_id
        
        # Debug output
        print(f"[DEBUG] RegionSelectionDialog initialized with image_id: {self.image_id}")
        
        # Initialize UI first, then load characters and quick events
        self.init_ui()
        
        # Setup keyboard shortcuts
        self.setup_shortcuts()
        
        # Load characters and quick events AFTER UI is initialized
        self.load_characters_data()
        self.load_quick_events_data()
        
    # Add shortcut setup method
    def setup_shortcuts(self):
        """Setup keyboard shortcuts for the dialog."""
        from PyQt6.QtGui import QKeySequence, QShortcut
        
        # Add CTRL+Q shortcut for quick event
        quick_event_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        quick_event_shortcut.activated.connect(self.quick_event_shortcut_triggered)
    
    def quick_event_shortcut_triggered(self):
        """Handle CTRL+Q shortcut key press - create a quick event with special rules."""
        try:
            # Import the needed utilities
            from app.utils.quick_event_utils import show_quick_event_dialog
            
            # Create context for character recognition dialog
            context = {
                "source": "recognition_dialog_shortcut",
                "image_id": self.image_id,
                "tagged_characters": [char.get('character_id') for char in self.tagged_characters],
                "allow_extra_options": True,
                "show_associate_checkbox": True,
                "shortcut": "CTRL+Q"
            }
            
            # Debug output
            print(f"\n[DEBUG] QuickEventDialog CTRL+Q triggered from Character Recognition - context: {context}\n")
            
            # Show the dialog with specific options for this context
            show_quick_event_dialog(
                db_conn=self.db_conn,
                story_id=self.story_id,
                parent=self,
                callback=self.on_quick_event_created,
                context=context,
                character_id=None,  # Force anonymous event (no character_id)
                options={
                    "show_recent_events": True,
                    "show_character_tags": True,
                    "show_optional_note": True,
                    "allow_characterless_events": True,
                    "title": "Quick Event - Character Recognition",
                    "force_anonymous": True  # Special flag to enforce anonymous events
                }
            )
        except Exception as e:
            import traceback
            print(f"Error creating quick event from shortcut: {e}")
            print(traceback.format_exc())
            QMessageBox.critical(
                self,
                "Error",
                f"Error creating quick event: {str(e)}",
                QMessageBox.StandardButton.Ok
            )
    
    def load_characters_data(self):
        """Load characters for the story."""
        try:
            # Use existing functions to get characters
            from app.db_sqlite import get_story_characters
            self.characters = get_story_characters(self.db_conn, self.story_id)
        except Exception as e:
            print(f"Error loading characters: {e}")
            self.characters = []
    
    def load_quick_events_data(self):
        """Load quick events for the story."""
        try:
            # Get quick events for the story
            from app.db_sqlite import search_quick_events, get_quick_event_tagged_characters
            from app.utils.character_references import convert_char_refs_to_mentions
            
            self.quick_events = search_quick_events(
                self.db_conn,
                self.story_id,
                text_query=None,
                character_id=None,
                from_date=None,
                to_date=None
            )
            
            # Sort by most recent first
            self.quick_events.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            # Update the quick events combo box if it exists
            if hasattr(self, 'quick_events_combo'):
                self.quick_events_combo.clear()
                self.quick_events_combo.addItem("Select a quick event...", -1)
                
                for event in self.quick_events:
                    # Get the text and convert character references to @mentions
                    text = event.get('text', '')
                    event_id = event.get('id')
                    
                    # If the text contains character references, convert them to @mentions
                    if "[char:" in text:
                        # Get tagged characters for the quick event
                        tagged_characters = get_quick_event_tagged_characters(self.db_conn, event_id)
                        text = convert_char_refs_to_mentions(text, tagged_characters)
                    
                    # Truncate long text
                    if len(text) > 50:
                        text = text[:47] + "..."
                    
                    # Show event text without prefix for events without an owner
                    character_id = event.get('character_id')
                    if character_id:
                        character_name = "Unknown"
                        for char in self.characters:
                            if char.get('id') == character_id:
                                character_name = char.get('name', "Unknown")
                                break
                        display_text = f"{character_name}: {text}"
                    else:
                        # For events with no owner, just show the text directly
                        display_text = text
                    
                    self.quick_events_combo.addItem(display_text, event_id)
            
        except Exception as e:
            print(f"Error loading quick events: {e}")
            self.quick_events = []
            
    def init_ui(self):
        """Initialize the user interface."""
        # Set window properties
        self.setWindowTitle("Character Recognition")
        self.setMinimumSize(1000, 600)
        
        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Splitter for image view and controls
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left side - Image view
        view_widget = QWidget()
        view_layout = QVBoxLayout(view_widget)
        
        # Create scene and view for displaying the image
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        
        # Handle mouse events for region selection
        self.view.mousePressEvent = self.view_mouse_press
        self.view.mouseMoveEvent = self.view_mouse_move
        self.view.mouseReleaseEvent = self.view_mouse_release
        
        # Add image to scene
        pixmap_item = QGraphicsPixmapItem(QPixmap.fromImage(self.image))
        self.scene.addItem(pixmap_item)
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        
        # Add view to layout
        view_layout.addWidget(self.view)
        
        # Add instruction label
        instruction_label = QLabel("Right-click and drag to select face regions")
        instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        view_layout.addWidget(instruction_label)
        
        # Right side - Controls
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        
        # Add tabs for region selection and character tagging
        tabs = QTabWidget()
        controls_layout.addWidget(tabs)
        
        # Tab 1: Region selection
        region_tab = QWidget()
        region_layout = QVBoxLayout(region_tab)
        
        # Region list
        region_group = QGroupBox("Selected Regions")
        region_group_layout = QVBoxLayout(region_group)
        
        self.region_list = QListWidget()
        self.region_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.region_list.currentRowChanged.connect(self.on_region_selected)
        region_group_layout.addWidget(self.region_list)
        
        # Region buttons
        region_buttons = QHBoxLayout()
        
        self.remove_region_button = QPushButton("Remove Region")
        self.remove_region_button.clicked.connect(self.remove_selected_region)
        self.remove_region_button.setEnabled(False)
        region_buttons.addWidget(self.remove_region_button)
        
        clear_all_button = QPushButton("Clear All")
        clear_all_button.clicked.connect(self.clear_all_regions)
        region_buttons.addWidget(clear_all_button)
        
        region_group_layout.addLayout(region_buttons)
        region_layout.addWidget(region_group)
        
        # Result list
        result_group = QGroupBox("Character Recognition Results")
        result_group_layout = QVBoxLayout(result_group)
        
        self.result_list = QListWidget()
        self.result_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.result_list.itemSelectionChanged.connect(self.on_character_selection_changed)
        result_group_layout.addWidget(self.result_list)
        
        # Save tag button
        self.save_tag_button = QPushButton("Save Character Tag")
        self.save_tag_button.clicked.connect(self.save_current_tag)
        self.save_tag_button.setEnabled(False)
        result_group_layout.addWidget(self.save_tag_button)
        
        # Add to database checkbox
        self.add_to_db_checkbox = QCheckBox("Add face to recognition database")
        self.add_to_db_checkbox.setChecked(False)
        result_group_layout.addWidget(self.add_to_db_checkbox)
        
        # Rebuild database button
        rebuild_button = QPushButton("Rebuild Recognition Database")
        rebuild_button.clicked.connect(self.rebuild_recognition_database)
        result_group_layout.addWidget(rebuild_button)
        
        region_layout.addWidget(result_group)
        
        # Tab 2: Tagged characters
        tagged_tab = QWidget()
        tagged_layout = QVBoxLayout(tagged_tab)
        
        # Tagged list
        tagged_group = QGroupBox("Tagged Characters")
        tagged_group_layout = QVBoxLayout(tagged_group)
        
        self.tagged_list = QListWidget()
        tagged_group_layout.addWidget(self.tagged_list)
        
        tagged_layout.addWidget(tagged_group)
        
        # Tab 3: Quick events
        qe_tab = QWidget()
        qe_layout = QVBoxLayout(qe_tab)
        
        # Quick events selection
        qe_select_group = QGroupBox("Associate with Existing Quick Event")
        qe_select_layout = QVBoxLayout(qe_select_group)
        
        self.quick_events_combo = QComboBox()
        self.quick_events_combo.addItem("Select a quick event...", -1)
        self.quick_events_combo.currentIndexChanged.connect(self.on_quick_event_selected)
        qe_select_layout.addWidget(self.quick_events_combo)
        
        qe_layout.addWidget(qe_select_group)
        
        # Create new quick event
        qe_create_group = QGroupBox("Create New Quick Event")
        qe_create_layout = QVBoxLayout(qe_create_group)

        # Text entry - replaced with a single button
        create_qe_button = QPushButton("Create New Quick Event")
        create_qe_button.clicked.connect(self.create_quick_event)
        qe_create_layout.addWidget(create_qe_button)
        
        # Character tags help - not needed with new dialog approach
        help_label = QLabel("This will open the Quick Event dialog where you can tag characters and enter text.")
        help_label.setWordWrap(True)
        qe_create_layout.addWidget(help_label)
        
        qe_layout.addWidget(qe_create_group)
        
        # Character completer is no longer needed here as it's in the dialog
        
        # Add tabs
        tabs.addTab(region_tab, "Region Selection")
        tabs.addTab(tagged_tab, "Tagged Characters")
        tabs.addTab(qe_tab, "Quick Events")
        
        # Add dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        controls_layout.addWidget(button_box)
        
        # Add widgets to splitter
        splitter.addWidget(view_widget)
        splitter.addWidget(controls_widget)
        splitter.setSizes([600, 400])  # Set initial sizes
            

    def on_character_selected(self, character_name: str):
        """Handle character selection from completer.
        
        Args:
            character_name: Name of the selected character
        """
        self.tag_completer.insert_character_tag(character_name)
        
    def check_for_character_tag(self):
        """This method is now handled by CharacterCompleter."""
        pass
        
    def insert_character_tag(self, character_name: str):
        """Insert a character tag at the current cursor position.
        
        Args:
            character_name: Name of the character to insert
        """
        if not hasattr(self, 'qe_text_edit'):
            return
            
        cursor = self.qe_text_edit.textCursor()
        text = self.qe_text_edit.toPlainText()
        pos = cursor.position()
        
        # Find the @ that started this tag
        tag_start = text.rfind('@', 0, pos)
        
        if tag_start >= 0:
            # Delete everything from the @ to the cursor
            cursor.setPosition(tag_start)
            cursor.setPosition(pos, QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
            
            # Insert the character name with the @ prefix
            cursor.insertText(f"@{character_name}")
            
            # Add a space after the insertion if appropriate
            if cursor.position() < len(self.qe_text_edit.toPlainText()) and self.qe_text_edit.toPlainText()[cursor.position()] != ' ':
                cursor.insertText(" ")
            
            # Hide the completer
            self.tag_completer.hide()
            
            # Set focus back to the text edit
            self.qe_text_edit.setFocus()
    
    def create_quick_event(self):
        """Create a new quick event and add it to the database."""
        try:
            # Import the QuickEventManager
            from app.utils.quick_event_manager import QuickEventManager
            
            # Create context for character recognition dialog
            context = {
                "source": "recognition_dialog",
                "image_id": self.image_id,
                "tagged_characters": [char.get('character_id') for char in self.tagged_characters],
                "allow_extra_options": True,
                "show_associate_checkbox": True
            }
            
            # Show the dialog with specific options for this context
            from app.utils.quick_event_utils import show_quick_event_dialog
            
            show_quick_event_dialog(
                db_conn=self.db_conn,
                story_id=self.story_id,
                parent=self,
                callback=self.on_quick_event_created,
                context=context,
                options={
                    "show_recent_events": True,
                    "show_character_tags": True,
                    "show_optional_note": True,
                    "allow_characterless_events": True  # Always allow characterless events here
                }
            )
        except Exception as e:
            print(f"Error creating quick event: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error creating quick event: {str(e)}",
                QMessageBox.StandardButton.Ok
            )
            
    def on_quick_event_created(self, event_id: int, text: str, context: Dict[str, Any]) -> None:
        """Handle the quick event created signal.
        
        Args:
            event_id: ID of the created quick event
            text: Text of the quick event
            context: Context dictionary passed to the dialog
        """
        if not event_id:
            return
            
        # Store the new quick event ID
        self.new_quick_event_id = event_id
        self.associated_quick_event_id = event_id
        
        # Debug info about the current state
        print(f"[DEBUG] Quick event created - ID: {event_id}")
        print(f"[DEBUG] Context data: {context}")
        print(f"[DEBUG] Current image_id: {self.image_id}")
        
        # Get the image ID from context or from current instance
        image_id = context.get("image_id", None) or self.image_id
        
        print(f"[DEBUG] Using image_id for association: {image_id}")
        
        # Associate the quick event with the current image if we have an image_id
        if image_id:
            from app.db_sqlite import associate_quick_event_with_image
            try:
                note = "Automatically associated via Character Recognition window"
                print(f"[DEBUG] Associating quick event {event_id} with image {image_id}")
                
                success = associate_quick_event_with_image(
                    self.db_conn, 
                    event_id, 
                    image_id, 
                    note
                )
                
                # Verify association was created by querying the database
                cursor = self.db_conn.cursor()
                cursor.execute(
                    "SELECT id FROM quick_event_images WHERE quick_event_id = ? AND image_id = ?", 
                    (event_id, image_id)
                )
                association = cursor.fetchone()
                
                if success and association:
                    print(f"[DEBUG] Successfully associated quick event {event_id} with image {image_id}")
                    print(f"[DEBUG] Association record ID: {association['id'] if association else 'None'}")
                else:
                    print(f"[ERROR] Failed to associate quick event {event_id} with image {image_id}")
                    print(f"[ERROR] Association record found: {association is not None}")
                    
                    # Try to force the association again
                    print(f"[DEBUG] Forcing association with direct SQL")
                    from datetime import datetime
                    now = datetime.now().isoformat()
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO quick_event_images 
                        (quick_event_id, image_id, created_at, updated_at, note)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (event_id, image_id, now, now, note)
                    )
                    self.db_conn.commit()
            except Exception as e:
                import traceback
                print(f"[ERROR] Error associating quick event with image: {e}")
                print(traceback.format_exc())
        
        # Reload quick events
        self.load_quick_events_data()
        
        # Find and select the new event in the combo box
        for i in range(self.quick_events_combo.count()):
            if self.quick_events_combo.itemData(i) == event_id:
                self.quick_events_combo.setCurrentIndex(i)
                break
        
        # Success message
        QMessageBox.information(
            self,
            "Success",
            "Quick event created successfully and associated with this image.",
            QMessageBox.StandardButton.Ok
        )
    
    def on_quick_event_selected(self, index: int):
        """Handle selection of a quick event from the combo box.
        
        Args:
            index: Index of the selected item
        """
        # Get the selected quick event ID
        self.associated_quick_event_id = self.quick_events_combo.itemData(index)
        
        # Clear selection highlight when "Select a quick event..." is chosen
        if self.associated_quick_event_id == -1:
            return
            
        # Log the selection
        if self.associated_quick_event_id:
            print(f"Selected quick event ID: {self.associated_quick_event_id}")
            
            # Find the quick event in the list
            for event in self.quick_events:
                if event.get('id') == self.associated_quick_event_id:
                    # Get the quick event text
                    text = event.get('text', '')
                    character_id = event.get('character_id')
                    
                    # If the text contains character references, format them for display
                    if "[char:" in text:
                        # Get tagged characters for the quick event
                        from app.db_sqlite import get_quick_event_tagged_characters
                        from app.utils.character_references import convert_char_refs_to_mentions
                        
                        tagged_characters = get_quick_event_tagged_characters(self.db_conn, self.associated_quick_event_id)
                        formatted_text = convert_char_refs_to_mentions(text, tagged_characters)
                        
                        # Update the combo box text based on whether there's a character owner
                        current_text = self.quick_events_combo.currentText()
                        
                        if character_id:
                            # For events with a character owner
                            if ":" in current_text:
                                prefix = current_text.split(":", 1)[0]
                                display_text = f"{prefix}: {formatted_text}"
                                self.quick_events_combo.setItemText(index, display_text)
                            else:
                                # For events without a character owner, just show the formatted text
                                self.quick_events_combo.setItemText(index, formatted_text)
                            
                            print(f"Formatted quick event text: {formatted_text}")
                        break
    
    def get_selected_character_data(self) -> Dict[str, Any]:
        """Get data for all selected characters and quick event.
        
        Returns:
            Dictionary with character data and quick event ID
        """
        return {
            'characters': self.tagged_characters,
            'quick_event_id': self.associated_quick_event_id if self.associated_quick_event_id and self.associated_quick_event_id != -1 else None
        }
    
    def accept(self):
        """Override accept to save the selected quick event association."""
        # Get the selected quick event ID
        if hasattr(self, 'quick_events_combo'):
            self.associated_quick_event_id = self.quick_events_combo.currentData()
        
        # Call the parent accept
        super().accept()
    
    def rebuild_recognition_database(self):
        """Rebuild the character recognition database."""
        # Show a progress dialog
        progress_dialog = QProgressDialog(
            "Rebuilding character recognition database...",
            "Cancel", 0, 100, self
        )
        progress_dialog.setWindowTitle("Building Recognition Database")
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.setMinimumDuration(0)  # Show immediately
        progress_dialog.setValue(0)
        progress_dialog.show()
        QApplication.processEvents()
        
        try:
            # Update progress
            progress_dialog.setValue(10)
            QApplication.processEvents()
            
            # Rebuild the database
            self.image_recognition.build_character_image_database()
            
            # Update progress
            progress_dialog.setValue(90)
            QApplication.processEvents()
            
            # If a region is selected, re-run recognition on it
            current_row = self.region_list.currentRow()
            if current_row >= 0 and current_row < len(self.selected_regions):
                region = self.selected_regions[current_row]
                region_rect = QRect(
                    int(region['x']), 
                    int(region['y']), 
                    int(region['width']), 
                    int(region['height'])
                )
                region_image = self.image.copy(region_rect)
                self.recognize_characters_in_region(current_row, region_image)
            
            # Complete the progress
            progress_dialog.setValue(100)
            QApplication.processEvents()
            
            # Close progress dialog
            progress_dialog.close()
            
            # Show success message
            QMessageBox.information(
                self,
                "Database Rebuilt", 
                "Character recognition database has been rebuilt successfully."
            )
        except Exception as e:
            # Close progress dialog
            progress_dialog.close()
            
            # Show error message
            QMessageBox.critical(
                self, 
                "Database Rebuild Failed", 
                f"Failed to rebuild character recognition database: {str(e)}"
            )
    
    def on_character_selection_changed(self):
        """Enable/disable save tag button based on character selection."""
        selected_items = self.result_list.selectedItems()
        # Only enable if one item is selected and it's not a header item
        self.save_tag_button.setEnabled(
            len(selected_items) == 1 and 
            selected_items[0].data(Qt.ItemDataRole.UserRole) is not None
        )
    
    def save_current_tag(self):
        """Save the currently selected character tag."""
        selected_items = self.result_list.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]
        character_data = item.data(Qt.ItemDataRole.UserRole)
        if not character_data:
            return
            
        region_index = character_data['region_index']
        region = self.selected_regions[region_index]
        
        # Calculate the center point in original image coordinates
        center_x = region['x'] + (region['width'] / 2.0)  # Use floating point division
        
        # Adjust y position to center the tag on the face
        center_y = region['y'] + (region['height'] / 2.0)  # Center vertically in the region
        
        # Convert to normalized coordinates (0.0-1.0)
        x_normalized = center_x / self.image.width()
        y_normalized = center_y / self.image.height()
        width_normalized = region['width'] / self.image.width()
        height_normalized = region['height'] / self.image.height()
        
        # Log the coordinates for debugging
        print(f"Original region: x={region['x']}, y={region['y']}, w={region['width']}, h={region['height']}")
        print(f"Image dimensions: {self.image.width()} x {self.image.height()}")
        print(f"Center point: ({center_x}, {center_y})")
        print(f"Normalized: x={x_normalized}, y={y_normalized}, w={width_normalized}, h={height_normalized}")
        
        # Create a tag record
        tag = {
            'character_id': character_data['character_id'],
            'character_name': character_data['character_name'],
            'similarity': character_data['similarity'],
            'region_index': region_index,  # Store region_index for reference
            'region': {
                'x': x_normalized,  # Center X (normalized)
                'y': y_normalized,  # Adjusted Y (normalized)
                'width': width_normalized,
                'height': height_normalized
            }
        }
        
        # Check if this character is already tagged
        for existing_tag in self.tagged_characters:
            if existing_tag['character_id'] == tag['character_id']:
                reply = QMessageBox.question(
                    self,
                    "Character Already Tagged",
                    f"{tag['character_name']} is already tagged. Do you want to replace the existing tag?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
                # Remove existing tag
                self.tagged_characters.remove(existing_tag)
                break
        
        # Add the tag
        self.tagged_characters.append(tag)
            
        # Update the tagged list
        self.update_tagged_list()
        
        # Add to recognition database if checkbox is checked
        if self.add_to_db_checkbox.isChecked():
            self.add_region_to_recognition_database(region, character_data['character_id'], character_data['character_name'])
        
        # Clear the selection
        self.result_list.clearSelection()
        
        # Show confirmation message
        QMessageBox.information(
            self,
            "Tag Saved",
            f"Character tag for {tag['character_name']} has been saved.",
            QMessageBox.StandardButton.Ok
        )
            
    def update_tagged_list(self):
        """Update the list of tagged characters."""
        self.tagged_list.clear()
        for tag in self.tagged_characters:
            item = QListWidgetItem()
            item.setText(f"{tag['character_name']} ({int(tag['similarity'] * 100)}% match)")
            item.setData(Qt.ItemDataRole.UserRole, tag)
            self.tagged_list.addItem(item)
            
        
    def resizeEvent(self, event):
        """Handle resize events to maintain view fit.
        
        Args:
            event: Resize event
        """
        super().resizeEvent(event)
        # Use a small delay to ensure the resize is complete before fitting
        QTimer.singleShot(0, lambda: self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio))
    
    def view_mouse_press(self, event):
        """Handle mouse press events on the view.
        
        Args:
            event: Mouse event
        """
        if event.button() == Qt.MouseButton.RightButton:
            # Get the scene position under the mouse
            scene_pos = self.view.mapToScene(event.pos())
            
            # Convert scene position to original image coordinates
            image_pos = self.scene_to_image_coords(scene_pos)
            
            # Start creating a new region
            self.dragging = True
            self.current_region = {
                'start_x': image_pos.x(),
                'start_y': image_pos.y(),
                'end_x': image_pos.x(),
                'end_y': image_pos.y(),
                'rect_item': None
            }
            
            # Create a rectangle item for the new region
            rect = QRectF(
                self.current_region['start_x'],
                self.current_region['start_y'],
                1, 1  # Initial size (will be updated during drag)
            )
            
            rect_item = QGraphicsRectItem(rect)
            rect_item.setPen(QPen(QColor(0, 255, 0), 2))
            rect_item.setBrush(QBrush(QColor(0, 255, 0, 50)))  # Semi-transparent green
            self.scene.addItem(rect_item)
            
            self.current_region['rect_item'] = rect_item
        
        # Pass event to default handler
        QGraphicsView.mousePressEvent(self.view, event)
    
    def view_mouse_move(self, event):
        """Handle mouse move events on the view.
        
        Args:
            event: Mouse event
        """
        if self.dragging and self.current_region:
            # Get the scene position under the mouse
            scene_pos = self.view.mapToScene(event.pos())
            
            # Convert scene position to original image coordinates
            image_pos = self.scene_to_image_coords(scene_pos)
            
            # Update the end position of the current region
            self.current_region['end_x'] = image_pos.x()
            self.current_region['end_y'] = image_pos.y()
            
            # Update the rectangle
            if self.current_region['rect_item']:
                start_x = self.current_region['start_x']
                start_y = self.current_region['start_y']
                end_x = self.current_region['end_x']
                end_y = self.current_region['end_y']
                
                # Create rectangle from the two points
                rect = QRectF(
                    min(start_x, end_x),
                    min(start_y, end_y),
                    abs(end_x - start_x),
                    abs(end_y - start_y)
                )
                
                self.current_region['rect_item'].setRect(rect)
        
        # Pass event to default handler
        QGraphicsView.mouseMoveEvent(self.view, event)
    
    def view_mouse_release(self, event):
        """Handle mouse release events on the view.
        
        Args:
            event: Mouse event
        """
        if event.button() == Qt.MouseButton.RightButton and self.dragging and self.current_region:
            # Get the scene position under the mouse
            scene_pos = self.view.mapToScene(event.pos())
            
            # Convert scene position to original image coordinates
            image_pos = self.scene_to_image_coords(scene_pos)
            
            # Update the end position of the current region
            self.current_region['end_x'] = image_pos.x()
            self.current_region['end_y'] = image_pos.y()
            
            # Create a normalized rectangle for the region
            start_x = min(self.current_region['start_x'], self.current_region['end_x'])
            start_y = min(self.current_region['start_y'], self.current_region['end_y'])
            width = abs(self.current_region['end_x'] - self.current_region['start_x'])
            height = abs(self.current_region['end_y'] - self.current_region['start_y'])
            
            # Minimum size check (at least 20x20 pixels)
            if width < 20 or height < 20:
                # Region too small, remove it
                if self.current_region['rect_item']:
                    self.scene.removeItem(self.current_region['rect_item'])
                self.current_region = None
                self.dragging = False
                QGraphicsView.mouseReleaseEvent(self.view, event)
                return
            
            # Create a region object
            region = {
                'x': start_x,
                'y': start_y,
                'width': width,
                'height': height,
                'rect_item': self.current_region['rect_item'],
                'characters': []  # Will be populated after recognition
            }
            
            # Add region to the list
            region_index = len(self.selected_regions)
            self.selected_regions.append(region)
            
            # Add to the region list widget
            item = QListWidgetItem(f"Region {region_index + 1}: {int(width)}x{int(height)}")
            self.region_list.addItem(item)
            
            # Select the new region
            self.region_list.setCurrentRow(region_index)
            
            # Extract the region from the image
            region_rect = QRect(int(start_x), int(start_y), int(width), int(height))
            region_image = self.image.copy(region_rect)
            
            # Run character recognition on the region
            self.recognize_characters_in_region(region_index, region_image)
            
            # Reset state
            self.current_region = None
            self.dragging = False
        
        # Pass event to default handler
        QGraphicsView.mouseReleaseEvent(self.view, event)
    
    def scene_to_image_coords(self, scene_pos: QPointF) -> QPointF:
        """Convert scene coordinates to original image coordinates.
        
        Args:
            scene_pos: Position in scene coordinates
        
        Returns:
            Position in original image coordinates
        """
        # The scene has the pixmap item at position (0,0) so scene coordinates
        # directly correspond to image coordinates, but we need to ensure they
        # stay within bounds
        return QPointF(
            max(0, min(scene_pos.x(), self.image.width())),
            max(0, min(scene_pos.y(), self.image.height()))
        )
    
    def recognize_characters_in_region(self, region_index: int, region_image: QImage):
        """Recognize characters in a selected region.
        
        Args:
            region_index: Index of the region
            region_image: Image of the selected region
        """
        try:
            # Extract features from the region image
            region_features = self.image_recognition.extract_features_from_qimage(region_image)
            
            # Identify potential characters
            character_suggestions = self.image_recognition.identify_characters_in_image(
                region_features,
                threshold=0.5,  # Lower threshold to catch more potential matches
                story_id=self.story_id  # Restrict to current story
            )
            
            # Update region with character suggestions
            self.selected_regions[region_index]['characters'] = character_suggestions
            
            # Clear the result list
            self.result_list.clear()
            
            # Get all characters from the story
            cursor = self.db_conn.cursor()
            cursor.execute('SELECT id, name FROM characters WHERE story_id = ? ORDER BY name', (self.story_id,))
            all_characters = {row['id']: row['name'] for row in cursor.fetchall()}
            
            # Create set of already suggested character IDs
            suggested_ids = {suggestion['character_id'] for suggestion in character_suggestions}
            
            # Add header
            header_item = QListWidgetItem(f"Characters found in Region {region_index + 1}:")
            header_item.setFlags(header_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            header_item.setBackground(QColor(240, 240, 240))
            header_item.setForeground(QColor(0, 0, 0))
            self.result_list.addItem(header_item)
            
            # Add character suggestions with detected scores
            if character_suggestions:
                for suggestion in character_suggestions:
                    item = QListWidgetItem()
                    item.setText(f"{suggestion['character_name']} ({int(suggestion['similarity'] * 100)}% match)")
                    item.setData(Qt.ItemDataRole.UserRole, {
                        'region_index': region_index,
                        'character_id': suggestion['character_id'],
                        'character_name': suggestion['character_name'],
                        'similarity': suggestion['similarity']
                    })
                    self.result_list.addItem(item)
            
            # Add separator if we have suggestions
            if character_suggestions:
                separator = QListWidgetItem("──────────────────────────────")
                separator.setFlags(separator.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                separator.setForeground(QColor(150, 150, 150))
                self.result_list.addItem(separator)
                
                other_characters = QListWidgetItem("Other characters in this story:")
                other_characters.setFlags(other_characters.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                other_characters.setBackground(QColor(240, 240, 240))
                other_characters.setForeground(QColor(0, 0, 0))
                self.result_list.addItem(other_characters)
            
            # Add remaining characters with 0% match
            for char_id, char_name in all_characters.items():
                if char_id not in suggested_ids:
                    item = QListWidgetItem()
                    item.setText(f"{char_name} (0% match)")
                    item.setData(Qt.ItemDataRole.UserRole, {
                        'region_index': region_index,
                        'character_id': char_id,
                        'character_name': char_name,
                        'similarity': 0.0
                    })
                    self.result_list.addItem(item)
                    
            # Disable save button until a character is selected
            self.save_tag_button.setEnabled(False)
        except Exception as e:
            print(f"Error during character recognition: {e}")
            item = QListWidgetItem(f"Error during character recognition: {str(e)}")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.result_list.addItem(item)
    
    def on_region_selected(self, row: int):
        """Handle region selection change.
        
        Args:
            row: Selected row index
        """
        self.remove_region_button.setEnabled(row >= 0)
        
        if row >= 0 and row < len(self.selected_regions):
            # Update result list to show characters for the selected region
            region = self.selected_regions[row]
            
            # Clear the result list
            self.result_list.clear()
            
            # Get detected characters for this region
            character_suggestions = region['characters']
            
            # Get all characters from the story
            cursor = self.db_conn.cursor()
            cursor.execute('SELECT id, name FROM characters WHERE story_id = ? ORDER BY name', (self.story_id,))
            all_characters = {row['id']: row['name'] for row in cursor.fetchall()}
            
            # Create set of already suggested character IDs
            suggested_ids = {suggestion['character_id'] for suggestion in character_suggestions}
            
            # Add header
            header_item = QListWidgetItem(f"Characters found in Region {row + 1}:")
            header_item.setFlags(header_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            header_item.setBackground(QColor(240, 240, 240))
            header_item.setForeground(QColor(0, 0, 0))
            self.result_list.addItem(header_item)
            
            # Add character suggestions with detected scores
            if character_suggestions:
                for suggestion in character_suggestions:
                    item = QListWidgetItem()
                    item.setText(f"{suggestion['character_name']} ({int(suggestion['similarity'] * 100)}% match)")
                    item.setData(Qt.ItemDataRole.UserRole, {
                        'region_index': row,
                        'character_id': suggestion['character_id'],
                        'character_name': suggestion['character_name'],
                        'similarity': suggestion['similarity']
                    })
                    self.result_list.addItem(item)
            
            # Add separator if we have suggestions
            if character_suggestions:
                separator = QListWidgetItem("──────────────────────────────")
                separator.setFlags(separator.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                separator.setForeground(QColor(150, 150, 150))
                self.result_list.addItem(separator)
                
                other_characters = QListWidgetItem("Other characters in this story:")
                other_characters.setFlags(other_characters.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                other_characters.setBackground(QColor(240, 240, 240))
                other_characters.setForeground(QColor(0, 0, 0))
                self.result_list.addItem(other_characters)
            
            # Add remaining characters with 0% match
            for char_id, char_name in all_characters.items():
                if char_id not in suggested_ids:
                    item = QListWidgetItem()
                    item.setText(f"{char_name} (0% match)")
                    item.setData(Qt.ItemDataRole.UserRole, {
                        'region_index': row,
                        'character_id': char_id,
                        'character_name': char_name,
                        'similarity': 0.0
                    })
                    self.result_list.addItem(item)
                
            # Highlight the selected region
            for i, r in enumerate(self.selected_regions):
                if r['rect_item']:
                    if i == row:
                        # Highlight selected region
                        r['rect_item'].setPen(QPen(QColor(255, 165, 0), 3))  # Orange for selected
                    else:
                        # Normal color for other regions
                        r['rect_item'].setPen(QPen(QColor(0, 255, 0), 2))  # Green for others
    
    def remove_selected_region(self):
        """Remove the currently selected region."""
        row = self.region_list.currentRow()
        if row >= 0 and row < len(self.selected_regions):
            # Remove the region
            region = self.selected_regions[row]
            
            # Remove the rectangle item from the scene
            if region['rect_item']:
                self.scene.removeItem(region['rect_item'])
            
            # Remove from lists
            self.selected_regions.pop(row)
            self.region_list.takeItem(row)
            
            # Clear results
            self.result_list.clear()
            
            # Rename remaining regions
            for i in range(self.region_list.count()):
                self.region_list.item(i).setText(f"Region {i + 1}: {int(self.selected_regions[i]['width'])}x{int(self.selected_regions[i]['height'])}")
    
    def clear_all_regions(self):
        """Clear all selected regions."""
        # Confirm with user
        if self.selected_regions:
            confirm = QMessageBox.question(
                self,
                "Clear All Regions",
                "Are you sure you want to clear all selected regions?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if confirm == QMessageBox.StandardButton.Yes:
                # Remove all regions
                for region in self.selected_regions:
                    if region['rect_item']:
                        self.scene.removeItem(region['rect_item'])
                
                # Clear lists
                self.selected_regions.clear()
                self.region_list.clear()
                self.result_list.clear()
                
                # Clear tagged characters
                self.tagged_characters.clear()
                self.update_tagged_list()
                
                # Disable remove button
                self.remove_region_button.setEnabled(False)
    
    def add_region_to_recognition_database(self, region, character_id, character_name):
        """Add the selected region to the character's recognition database.
        
        Args:
            region: The region to add
            character_id: ID of the character
            character_name: Name of the character
        """
        try:
            # Extract the region from the image
            region_rect = QRect(int(region['x']), int(region['y']), int(region['width']), int(region['height']))
            region_image = self.image.copy(region_rect)
            
            # Extract features from the region
            features = self.image_recognition.extract_features_from_qimage(region_image)
            
            # Save features to database
            feature_id = self.image_recognition.save_character_image_features(
                character_id=character_id,
                features=features,
                is_avatar=False  # Not an avatar, but a tagged region
            )
            
            if feature_id:
                print(f"Added region to recognition database for {character_name} (ID: {character_id}), feature ID: {feature_id}")
                QMessageBox.information(
                    self,
                    "Added to Recognition Database",
                    f"The selected region has been added to {character_name}'s recognition database. "
                    f"This will improve character recognition in future images.",
                    QMessageBox.StandardButton.Ok
                )
            else:
                print(f"Failed to add region to recognition database for {character_name}")
                QMessageBox.warning(
                    self,
                    "Failed to Add to Database",
                    f"Failed to add the region to {character_name}'s recognition database.",
                    QMessageBox.StandardButton.Ok
                )
        except Exception as e:
            print(f"Error adding region to recognition database: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error adding region to recognition database: {str(e)}",
                QMessageBox.StandardButton.Ok
            )


class GraphicsTagView(QGraphicsView):
    """A graphics view for displaying images with character tags.
    
    This class uses QGraphicsView and QGraphicsScene for more precise positioning
    of character tags compared to painting directly on a QLabel.
    """
    
    tag_added = pyqtSignal(float, float)  # x, y position in relative coordinates (0.0-1.0)
    tag_selected = pyqtSignal(int)  # tag_id
    
    def __init__(self, parent=None):
        """Initialize the graphics view."""
        super().__init__(parent)
        
        # Set up the scene
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Image display
        self.image_item = None
        self.tag_items = {}  # Dict of tag_id -> (rect_item, text_item) tuples
        
        # Tag mode
        self.tag_mode = False
        self.selected_tag_id = None
        
        # Store dimensions and scaling factors
        self.image_width = 0
        self.image_height = 0
        self.scale_x = 1.0
        self.scale_y = 1.0
        
        # Set rendering quality
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.SmoothPixmapTransform
        )
        
        # CRITICAL: These settings ensure we get no margins
        self.setFrameShape(QFrame.Shape.NoFrame)  # Remove the frame
        self.setViewportMargins(0, 0, 0, 0)  # Zero margins for viewport
        
        # Disable scrollbars completely
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Viewport update mode
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        
        # Alignment center
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        
        # Transform changed tracking
        self.last_transform = self.transform()
    
    def set_image(self, pixmap, orig_width=None, orig_height=None):
        """Set the image for display.
        
        Args:
            pixmap: QPixmap to display
            orig_width: Original image width (if scaled)
            orig_height: Original image height (if scaled)
        """
        # Clear the scene
        self.scene.clear()
        self.tag_items.clear()
        
        # Store dimensions - use original dimensions if provided
        self.image_width = orig_width if orig_width is not None else pixmap.width()
        self.image_height = orig_height if orig_height is not None else pixmap.height()
        
        # CRITICAL: Print dimensions for verification
        print(f"GRAPHICS VIEW SET IMAGE: pixmap={pixmap.width()}x{pixmap.height()}, using={self.image_width}x{self.image_height}")
        
        # Add image to scene
        self.image_item = self.scene.addPixmap(pixmap)
        self.image_item.setZValue(0)  # Put image at the bottom
        
        # Set scene rect to exactly match pixmap dimensions
        self.scene.setSceneRect(0, 0, pixmap.width(), pixmap.height())
        
        # Calculate scaling factors if image was resized
        if orig_width is not None and orig_height is not None:
            self.scale_x = pixmap.width() / orig_width
            self.scale_y = pixmap.height() / orig_height
            print(f"IMAGE SCALING: scale_x={self.scale_x:.3f}, scale_y={self.scale_y:.3f}")
        else:
            self.scale_x = 1.0
            self.scale_y = 1.0
        
        # Fit the view to the image
        self._update_view_transform()
        
        # Log current view transformation for debugging
        matrix = self.transform()
        print(f"INITIAL TRANSFORM: m11={matrix.m11():.3f}, m22={matrix.m22():.3f}, dx={matrix.dx():.1f}, dy={matrix.dy():.1f}")
    
    def _update_view_transform(self):
        """Update the view transformation to ensure the image fills the entire view.
        
        This method calculates the perfect scale and position for the image
        to completely fill the view without any margins.
        """
        if not self.image_item or not self.scene:
            return
        
        # Get scene and viewport dimensions
        scene_rect = self.scene.sceneRect()
        viewport_size = self.viewport().size()
        
        if viewport_size.width() <= 0 or viewport_size.height() <= 0:
            return
            
        # Calculate scale factors for width and height
        scale_x = viewport_size.width() / scene_rect.width()
        scale_y = viewport_size.height() / scene_rect.height()
        
        # Use the larger scale factor to ensure the image fills the view completely
        scale = max(scale_x, scale_y)
        
        # Create a transform that scales the image
        transform = QTransform()
        transform.scale(scale, scale)
        
        # Calculate offsets to center the image
        if scale == scale_x:
            # If scaling by width, center vertically
            dx = 0
            dy = (viewport_size.height() - (scene_rect.height() * scale)) / 2
        else:
            # If scaling by height, center horizontally
            dx = (viewport_size.width() - (scene_rect.width() * scale)) / 2
            dy = 0
        
        # Apply translation
        transform.translate(dx/scale, dy/scale)
        
        # Set the transform
        self.setTransform(transform)
        
        # Log the new transform
        matrix = self.transform()
        print(f"UPDATE TRANSFORM: m11={matrix.m11():.3f}, m22={matrix.m22():.3f}, dx={matrix.dx():.1f}, dy={matrix.dy():.1f}")
    
    def resizeEvent(self, event):
        """Handle resize events.
        
        Args:
            event: Resize event
        """
        super().resizeEvent(event)
        
        # Update the view transform whenever the view is resized
        self._update_view_transform()
    
    def set_tags(self, tags):
        """Set the character tags to display.
        
        Args:
            tags: List of tag dictionaries
        """
        # Clear existing tags
        for tag_id in list(self.tag_items.keys()):
            self.remove_tag_item(tag_id)
        
        # Add new tags
        for tag in tags:
            self.add_tag_item(tag)
    
    def add_tag_item(self, tag):
        """Add a tag item to the scene.
        
        Args:
            tag: Tag dictionary
        """
        tag_id = tag['id']
        
        # Get tag data - these are normalized coordinates (0-1)
        center_x_norm = tag['x_position']
        center_y_norm = tag['y_position']
        width_norm = tag['width']
        height_norm = tag['height']
        character_name = tag.get('character_name', 'Unknown')
        
        # Convert normalized coordinates to scene coordinates
        center_point = self.norm_to_scene_coords(center_x_norm, center_y_norm)
        center_x = center_point.x()
        center_y = center_point.y()
        
        # DEBUG: Print the original normalized coordinates and calculated scene coordinates
        print(f"TAG COORDINATES: id={tag_id}")
        print(f"  - Normalized: ({center_x_norm:.4f}, {center_y_norm:.4f})")
        print(f"  - Scene: ({center_x:.1f}, {center_y:.1f})")
        
        # Calculate width and height in scene coordinates
        scene_rect = self.scene.sceneRect()
        scene_width = scene_rect.width()
        scene_height = scene_rect.height()
        width = width_norm * scene_width
        height = height_norm * scene_height
        
        # Calculate rectangle position (top-left corner from center)
        rect_x = center_x - (width / 2)
        rect_y = center_y - (height / 2)
        
        # DEBUG: Print full coordinate calculations
        print(f"TAG RECTANGLE: id={tag_id}")
        print(f"  - Center: ({center_x:.1f}, {center_y:.1f})")
        print(f"  - Size: {width:.1f}x{height:.1f}")
        print(f"  - Rectangle: ({rect_x:.1f}, {rect_y:.1f}, {width:.1f}, {height:.1f})")
        
        # Create rectangle item for the tag
        rect_item = QGraphicsRectItem(rect_x, rect_y, width, height)
        rect_item.setPen(QPen(QColor(0, 255, 0), 2))  # Green border
        rect_item.setZValue(1)  # Above image
        rect_item.setData(0, tag_id)  # Store tag ID
        
        # Create text background - positioned ABOVE the rectangle
        text_height = 20
        text_bg = QGraphicsRectItem(rect_x, rect_y - text_height - 2, width, text_height)
        text_bg.setBrush(QColor(0, 0, 0, 180))  # Semi-transparent black
        text_bg.setPen(QPen(Qt.PenStyle.NoPen))  # No border
        text_bg.setZValue(1)  # Same as rectangle
        
        # Create text item
        text_item = QGraphicsTextItem(character_name)
        text_item.setDefaultTextColor(QColor(255, 255, 255))  # White text
        text_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        text_item.setZValue(2)  # Above rectangle and background
        
        # Center text within background
        text_width = text_item.boundingRect().width()
        text_pos_x = rect_x + (width - text_width) / 2
        text_pos_y = rect_y - text_height - 2
        text_item.setPos(text_pos_x, text_pos_y)
        
        # Add items to scene
        self.scene.addItem(rect_item)
        self.scene.addItem(text_bg)
        self.scene.addItem(text_item)
        
        # Store references
        self.tag_items[tag_id] = (rect_item, text_bg, text_item)
    
    def remove_tag_item(self, tag_id):
        """Remove a tag item from the scene.
        
        Args:
            tag_id: ID of the tag to remove
        """
        if tag_id in self.tag_items:
            rect_item, text_bg, text_item = self.tag_items[tag_id]
            self.scene.removeItem(rect_item)
            self.scene.removeItem(text_bg)
            self.scene.removeItem(text_item)
            del self.tag_items[tag_id]
    
    def enable_tag_mode(self, enabled=True):
        """Enable or disable tag adding mode.
        
        Args:
            enabled: Whether to enable tag mode
        """
        self.tag_mode = enabled
        if enabled:
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            
        # Deselect any selected tag
        self.selected_tag_id = None
    
    def mousePressEvent(self, event):
        """Handle mouse press events.
        
        Args:
            event: Mouse event
        """
        if not self.image_item:
            super().mousePressEvent(event)
            return
        
        # Get current view transformation
        current_transform = self.transform()
        if current_transform != self.last_transform:
            print(f"TRANSFORM CHANGED: m11={current_transform.m11():.3f}, m22={current_transform.m22():.3f}, " +
                  f"dx={current_transform.dx():.1f}, dy={current_transform.dy():.1f}")
            self.last_transform = current_transform
            
        if self.tag_mode and event.button() == Qt.MouseButton.LeftButton:
            # Get scene position for click
            scene_pos = self.mapToScene(event.pos())
            
            # DEBUG: Print the original scene position
            print(f"CLICK SCENE POSITION: ({scene_pos.x():.1f}, {scene_pos.y():.1f})")
            
            # Get scene dimensions
            scene_rect = self.scene.sceneRect()
            scene_width = scene_rect.width()
            scene_height = scene_rect.height()
            
            # Convert scene position to normalized coordinates
            rel_x = scene_pos.x() / scene_width
            rel_y = scene_pos.y() / scene_height
            
            # Ensure coordinates are within bounds
            rel_x = max(0.0, min(1.0, rel_x))
            rel_y = max(0.0, min(1.0, rel_y))
            
            # DEBUG: Print normalized coordinates
            print(f"NORMALIZED CLICK COORDINATES: ({rel_x:.4f}, {rel_y:.4f})")
            
            # Emit signal with the normalized coordinates
            self.tag_added.emit(rel_x, rel_y)
        else:
            # Original code for handling tag selection
            scene_pos = self.mapToScene(event.pos())
            item = self.scene.itemAt(scene_pos, self.transform())
            if isinstance(item, QGraphicsRectItem) and item.data(0):
                # A tag rectangle was clicked
                tag_id = item.data(0)
                self.selected_tag_id = tag_id
                
                # Update appearance
                self.update_tag_appearance(tag_id)
                
                # Emit signal
                self.tag_selected.emit(tag_id)
            else:
                # Deselect if clicking outside any tag
                if self.selected_tag_id is not None:
                    prev_selected = self.selected_tag_id
                    self.selected_tag_id = None
                    self.update_tag_appearance(prev_selected)
        
        super().mousePressEvent(event)
    
    def update_tag_appearance(self, tag_id):
        """Update the appearance of a tag based on selection state.
        
        Args:
            tag_id: ID of the tag to update
        """
        if tag_id in self.tag_items:
            rect_item, _, _ = self.tag_items[tag_id]
            
            if tag_id == self.selected_tag_id:
                rect_item.setPen(QPen(QColor(255, 165, 0), 3))  # Orange, thicker
            else:
                rect_item.setPen(QPen(QColor(0, 255, 0), 2))  # Green, normal
    
    def save_tag_crop(self, tag_id, character_name):
        """Save a cropped image of the tag rectangle.
        
        Args:
            tag_id: ID of the tag
            character_name: Name of the character for the filename
        """
        # if tag_id not in self.tag_items:
        #     print(f"Error: Cannot save crop for tag {tag_id} - tag not found")
        #     return
            
        # try:
        #     # Create test_rectangle_crops directory if it doesn't exist
        #     import os
        #     from datetime import datetime
            
        #     crop_dir = "test_rectangle_crops"
        #     if not os.path.exists(crop_dir):
        #         os.makedirs(crop_dir)
            
        #     # Get the tag rectangle
        #     rect_item, _, _ = self.tag_items[tag_id]
        #     rect = rect_item.rect()
            
        #     # Create a QPixmap to hold the cropped image
        #     scene_rect = QRectF(rect)
            
        #     # Get the pixmap from the scene
        #     if not self.image_item or not self.image_item.pixmap():
        #         print("Error: No image available for cropping")
        #         return
                
        #     # Get the source image from the pixmap
        #     source_pixmap = self.image_item.pixmap()
        #     source_image = source_pixmap.toImage()
            
        #     # Convert scene rect to source image coordinates
        #     # Scene coordinates and image coordinates are the same in our implementation
        #     source_rect = QRect(
        #         int(rect.x()),
        #         int(rect.y()),
        #         int(rect.width()),
        #         int(rect.height())
        #     )
            
        #     # Make sure the rect is within the image bounds
        #     source_rect = source_rect.intersected(source_image.rect())
            
        #     # Crop the image
        #     cropped_image = source_image.copy(source_rect)
            
        #     # Generate filename with timestamp and character name
        #     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        #     safe_name = character_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
        #     filename = f"{crop_dir}/{timestamp}_{safe_name}_tag_{tag_id}.png"
            
        #     # Save the cropped image
        #     success = cropped_image.save(filename)
            
        #     if success:
        #         print(f"Saved cropped tag image to {filename}")
        #     else:
        #         print(f"Failed to save cropped tag image to {filename}")
                
        # except Exception as e:
        #     print(f"Error saving tag crop: {e}")
        #     import traceback
        #     traceback.print_exc()
        pass  # Method disabled
    
    def view_to_norm_coords(self, view_pos):
        """Convert view coordinates to normalized coordinates (0-1 range).
        
        Args:
            view_pos: Position in view coordinates (QPoint)
            
        Returns:
            Tuple of (rel_x, rel_y) coordinates in 0-1 range
        """
        # First convert view position to scene position
        scene_pos = self.mapToScene(view_pos)
        
        # Get scene bounds
        scene_rect = self.scene.sceneRect()
        scene_width = scene_rect.width()
        scene_height = scene_rect.height()
        
        # Convert scene position to normalized coordinates (0-1)
        rel_x = scene_pos.x() / scene_width
        rel_y = scene_pos.y() / scene_height
        
        # Ensure coordinates are within bounds
        rel_x = max(0.0, min(1.0, rel_x))
        rel_y = max(0.0, min(1.0, rel_y))
        
        # Print detailed debug info
        print(f"VIEW TO NORM COORDS:")
        print(f"  - View pos: ({view_pos.x()}, {view_pos.y()})")
        print(f"  - Scene pos: ({scene_pos.x():.1f}, {scene_pos.y():.1f})")
        print(f"  - Scene dimensions: {scene_width}x{scene_height}")
        print(f"  - Normalized: ({rel_x:.4f}, {rel_y:.4f})")
        
        return rel_x, rel_y
    
    def norm_to_scene_coords(self, rel_x, rel_y):
        """Convert normalized coordinates (0-1 range) to scene coordinates.
        
        Args:
            rel_x: Normalized x-coordinate (0-1)
            rel_y: Normalized y-coordinate (0-1)
            
        Returns:
            QPointF with scene coordinates
        """
        # Get scene bounds
        scene_rect = self.scene.sceneRect()
        scene_width = scene_rect.width()
        scene_height = scene_rect.height()
        
        # Convert normalized coordinates to scene coordinates
        scene_x = rel_x * scene_width
        scene_y = rel_y * scene_height
        
        # Print detailed debug info
        print(f"NORM TO SCENE COORDS:")
        print(f"  - Normalized: ({rel_x:.4f}, {rel_y:.4f})")
        print(f"  - Scene dimensions: {scene_width}x{scene_height}")
        print(f"  - Scene pos: ({scene_x:.1f}, {scene_y:.1f})")
        
        return QPointF(scene_x, scene_y)

    def load_characters(self):
        """Load characters for the story."""
        try:
            # Use existing functions to get characters
            from app.db_sqlite import get_story_characters
            self.characters = get_story_characters(self.db_conn, self.story_id)
        except Exception as e:
            print(f"Error loading characters: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to load characters: {str(e)}",
                QMessageBox.StandardButton.Ok
            )
            self.characters = []
    
    def load_quick_events(self):
        """Load quick events for the story."""
        try:
            # Get quick events for the story
            from app.db_sqlite import search_quick_events
            
            # Get all quick events for this story
            self.quick_events = search_quick_events(
                self.db_conn,
                self.story_id,
                text_query=None,
                character_id=None,
                from_date=None,
                to_date=None
            )
            
            # Sort by most recent first
            self.quick_events.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
        except Exception as e:
            print(f"Error loading quick events: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to load quick events: {str(e)}",
                QMessageBox.StandardButton.Ok
            )
            self.quick_events = []
    
    def create_quick_event(self):
        """Create a new quick event and associate it with the image."""
        try:
            # Get the text
            text = self.qe_text_edit.toPlainText().strip()
            if not text:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Please enter text for the quick event.",
                    QMessageBox.StandardButton.Ok
                )
                return
                
            # Make sure we have at least one character in the story to process @mentions
            if not self.characters:
                QMessageBox.warning(
                    self,
                    "Error",
                    "No characters available in your story. Please add characters first.",
                    QMessageBox.StandardButton.Ok
                )
                return
                
            # Convert any @mentions to [char:ID] format using the centralized function
            from app.db_sqlite import create_quick_event, get_next_quick_event_sequence_number
            
            # Process the text with the centralized function
            processed_text = convert_mentions_to_char_refs(text, self.characters)
            
            # Create the quick event with no character owner (character_id=None)
            quick_event_id = create_quick_event(
                self.db_conn,
                text=processed_text,
                character_id=None,  # No character owner
                sequence_number=0   # Default sequence number for characterless events
            )
            
            if quick_event_id:
                # Store the new quick event ID
                self.new_quick_event_id = quick_event_id
                self.associated_quick_event_id = quick_event_id
                
                # Reload quick events
                self.load_quick_events_data()
                
                # Find and select the new event in the combo box
                for i in range(self.quick_events_combo.count()):
                    if self.quick_events_combo.itemData(i) == quick_event_id:
                        self.quick_events_combo.setCurrentIndex(i)
                        break
                
                QMessageBox.information(
                    self,
                    "Success",
                    "Quick event created successfully and associated with this image.",
                    QMessageBox.StandardButton.Ok
                )
                
                # Clear the text edit
                self.qe_text_edit.clear()
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Failed to create quick event.",
                    QMessageBox.StandardButton.Ok
                )
        except Exception as e:
            print(f"Error creating quick event: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error creating quick event: {str(e)}",
                QMessageBox.StandardButton.Ok
            )
    
    def on_quick_event_selected(self, index: int):
        """Handle selection of a quick event from the combo box.
        
        Args:
            index: Index of the selected item
        """
        # Get the selected quick event ID
        self.associated_quick_event_id = self.quick_events_combo.itemData(index)
        
        # Clear selection highlight when "Select a quick event..." is chosen
        if self.associated_quick_event_id == -1:
            return
            
        # Log the selection
        if self.associated_quick_event_id:
            print(f"Selected quick event ID: {self.associated_quick_event_id}")
            
            # Find the quick event in the list
            for event in self.quick_events:
                if event.get('id') == self.associated_quick_event_id:
                    # Get the quick event text
                    text = event.get('text', '')
                    character_id = event.get('character_id')
                    
                    # If the text contains character references, format them for display
                    if "[char:" in text:
                        # Get tagged characters for the quick event
                        from app.db_sqlite import get_quick_event_tagged_characters
                        from app.utils.character_references import convert_char_refs_to_mentions
                        
                        tagged_characters = get_quick_event_tagged_characters(self.db_conn, self.associated_quick_event_id)
                        formatted_text = convert_char_refs_to_mentions(text, tagged_characters)
                        
                        # Update the combo box text based on whether there's a character owner
                        current_text = self.quick_events_combo.currentText()
                        
                        if character_id:
                            # For events with a character owner
                            if ":" in current_text:
                                prefix = current_text.split(":", 1)[0]
                                display_text = f"{prefix}: {formatted_text}"
                                self.quick_events_combo.setItemText(index, display_text)
                            else:
                                # For events without a character owner, just show the formatted text
                                self.quick_events_combo.setItemText(index, formatted_text)
                            
                            print(f"Formatted quick event text: {formatted_text}")
                        break
    
    def get_selected_character_data(self) -> Dict[str, Any]:
        """Get data for all selected characters and quick event.
        
        Returns:
            Dictionary with character data and quick event ID
        """
        return {
            'characters': self.tagged_characters,
            'quick_event_id': self.associated_quick_event_id if self.associated_quick_event_id and self.associated_quick_event_id != -1 else None
        }


    def on_character_selected(self, character_name: str):
        """Handle character selection from completer.
        
        Args:
            character_name: Name of the selected character
        """
        self.tag_completer.insert_character_tag(character_name)
        
    def insert_character_tag(self, character_name: str):
        """Insert a character tag at the current cursor position.
        
        Args:
            character_name: Name of the character to insert
        """
        if not hasattr(self, 'qe_text_edit'):
            return
            
        cursor = self.qe_text_edit.textCursor()
        text = self.qe_text_edit.toPlainText()
        pos = cursor.position()
        
        # Find the @ that started this tag
        tag_start = text.rfind('@', 0, pos)
        
        if tag_start >= 0:
            # Delete everything from the @ to the cursor
            cursor.setPosition(tag_start)
            cursor.setPosition(pos, QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
            
            # Insert the character name with the @ prefix
            cursor.insertText(f"@{character_name}")
            
            # Add a space after the insertion if appropriate
            if cursor.position() < len(self.qe_text_edit.toPlainText()) and self.qe_text_edit.toPlainText()[cursor.position()] != ' ':
                cursor.insertText(" ")
            
            # Hide the completer
            self.tag_completer.hide()
            
            # Set focus back to the text edit
            self.qe_text_edit.setFocus()

    def accept(self):
        """Override accept to save the selected quick event association."""
        # Get the selected quick event ID
        self.associated_quick_event_id = self.quick_events_combo.currentData()
        
        
        # Call the parent accept
        super().accept()

    def load_quick_events_data(self):
        """Load quick events data for the combo box."""
        try:
            # Get quick events for the story
            from app.db_sqlite import search_quick_events, get_quick_event_tagged_characters
            from app.utils.character_references import convert_char_refs_to_mentions
            
            # Ensure we have loaded the quick events
            if not hasattr(self, 'quick_events') or not self.quick_events:
                self.load_quick_events()
            
            # Update the quick events combo box if it exists
            if hasattr(self, 'quick_events_combo'):
                self.quick_events_combo.clear()
                self.quick_events_combo.addItem("Select a quick event...", -1)
                
                for event in self.quick_events:
                    # Get the text and convert character references to @mentions
                    text = event.get('text', '')
                    event_id = event.get('id')
                    
                    # If the text contains character references, convert them to @mentions
                    if "[char:" in text:
                        # Get tagged characters for the quick event
                        tagged_characters = get_quick_event_tagged_characters(self.db_conn, event_id)
                        text = convert_char_refs_to_mentions(text, tagged_characters)
                    
                    # Truncate long text
                    if len(text) > 50:
                        text = text[:47] + "..."
                    
                    # Show event text without prefix for events without an owner
                    character_id = event.get('character_id')
                    if character_id:
                        character_name = "Unknown"
                        for char in self.characters:
                            if char.get('id') == character_id:
                                character_name = char.get('name', "Unknown")
                                break
                        display_text = f"{character_name}: {text}"
                    else:
                        # For events with no owner, just show the text directly
                        display_text = text
                    
                    self.quick_events_combo.addItem(display_text, event_id)
            
        except Exception as e:
            print(f"Error loading quick events data: {e}")
            if hasattr(self, 'quick_events_combo'):
                self.quick_events_combo.clear()
                self.quick_events_combo.addItem("Select a quick event...", -1)
