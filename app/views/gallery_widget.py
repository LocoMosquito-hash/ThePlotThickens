#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gallery widget for The Plot Thickens application.

This module provides a widget for managing and displaying a story's image gallery.
"""

import os
import uuid
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QGridLayout, QFileDialog, QMessageBox,
    QSizePolicy, QFrame, QApplication, QDialog, QListWidget,
    QListWidgetItem, QMenu, QTabWidget, QSplitter, QComboBox,
    QToolButton, QInputDialog, QTextEdit
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QByteArray, QUrl, QBuffer, QIODevice, QPoint, QRect, QRectF
from PyQt6.QtGui import QPixmap, QImage, QClipboard, QImageReader, QAction, QCursor, QBrush, QColor, QPainter, QPen, QFont, QTextCursor
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from app.db_sqlite import (
    get_image_quick_events, get_character_quick_events,
    associate_quick_event_with_image, remove_quick_event_image_association,
    get_story_characters, get_character,
    add_character_tag_to_image, update_character_tag, remove_character_tag,
    get_image_character_tags, create_quick_event, get_next_quick_event_sequence_number,
    get_quick_event_characters
)

class ThumbnailWidget(QFrame):
    """Widget for displaying a thumbnail image with basic controls."""
    
    clicked = pyqtSignal(int)  # Signal emitted when thumbnail is clicked
    delete_requested = pyqtSignal(int)  # Signal emitted when delete button is clicked
    
    def __init__(self, image_id: int, pixmap: QPixmap, title: str = "", parent=None) -> None:
        """Initialize the thumbnail widget.
        
        Args:
            image_id: ID of the image
            pixmap: QPixmap of the image
            title: Title of the image
            parent: Parent widget
        """
        super().__init__(parent)
        self.image_id = image_id
        self.pixmap = pixmap
        self.title = title
        
        # Set up the widget
        self.setFrameShape(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setLineWidth(1)
        self.setStyleSheet("background-color: #333337; border: 1px solid #555555;")
        self.setFixedSize(200, 220)  # Fixed size for the thumbnail widget
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Create image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(QSize(180, 150))
        self.image_label.setMaximumSize(QSize(180, 150))
        self.image_label.setScaledContents(False)
        
        # Scale the pixmap to fit the label while maintaining aspect ratio
        scaled_pixmap = self.pixmap.scaled(
            QSize(180, 150),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)
        
        # Create title label
        self.title_label = QLabel(title if title else f"Image {image_id}")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumHeight(40)
        
        # Create delete button
        self.delete_button = QPushButton("Delete")
        self.delete_button.setFixedHeight(25)
        self.delete_button.clicked.connect(self._on_delete_clicked)
        
        # Add widgets to layout
        layout.addWidget(self.image_label)
        layout.addWidget(self.title_label)
        layout.addWidget(self.delete_button)
        
        # Set up mouse events
        self.setMouseTracking(True)
    
    def mousePressEvent(self, event) -> None:
        """Handle mouse press events."""
        super().mousePressEvent(event)
        self.clicked.emit(self.image_id)
    
    def _on_delete_clicked(self) -> None:
        """Handle delete button click."""
        self.delete_requested.emit(self.image_id)


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
            # Create a list item with the event text
            text = event['text']
            if len(text) > 80:
                text = text[:77] + "..."
                
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, event['id'])
            
            # Set the item to be pre-selected if it's already associated
            if event['id'] in self.current_quick_event_ids:
                item.setSelected(True)
            
            self.event_list.addItem(item)
            
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
        """Initialize the taggable image label.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)
        
        self.tags = []  # List of tag objects
        self.selected_tag_id = None
        self.hover_tag_id = None
        self.tag_mode = False  # True when in tag adding mode
        
        # Store the actual image size (needed for scaling)
        self.image_width = 0
        self.image_height = 0
        self.offset_x = 0
        self.offset_y = 0
        
    def set_image(self, pixmap):
        """Set the image for the label.
        
        Args:
            pixmap: QPixmap to display
        """
        self.setPixmap(pixmap)
        self.image_width = pixmap.width()
        self.image_height = pixmap.height()
        
        # Calculate offsets for centered image
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
        if event.button() == Qt.MouseButton.LeftButton:
            if self.tag_mode:
                # Add a new tag
                # Convert to relative coordinates (0.0-1.0)
                rel_x, rel_y = self._to_relative_coords(event.position().x(), event.position().y())
                if 0 <= rel_x <= 1 and 0 <= rel_y <= 1:
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
        # Adjust for image offset within label
        x = x - self.offset_x
        y = y - self.offset_y
        
        # Convert to relative coordinates
        rel_x = max(0, min(1, x / self.image_width if self.image_width > 0 else 0))
        rel_y = max(0, min(1, y / self.image_height if self.image_height > 0 else 0))
        
        return rel_x, rel_y
        
    def _to_absolute_coords(self, rel_x, rel_y):
        """Convert relative coordinates to absolute coordinates.
        
        Args:
            rel_x: Relative x coordinate (0.0-1.0)
            rel_y: Relative y coordinate (0.0-1.0)
            
        Returns:
            Tuple of (absolute_x, absolute_y)
        """
        # Convert to absolute coordinates
        abs_x = int(rel_x * self.image_width) + self.offset_x
        abs_y = int(rel_y * self.image_height) + self.offset_y
        
        return abs_x, abs_y
        
    def _get_tag_at_position(self, x, y):
        """Get the tag ID at the given position.
        
        Args:
            x: Absolute x coordinate
            y: Absolute y coordinate
            
        Returns:
            Tag ID or None if no tag at position
        """
        rel_x, rel_y = self._to_relative_coords(x, y)
        
        for tag in self.tags:
            tag_x = tag['x_position']
            tag_y = tag['y_position']
            tag_width = tag['width']
            tag_height = tag['height']
            
            if (tag_x <= rel_x <= tag_x + tag_width and
                tag_y <= rel_y <= tag_y + tag_height):
                return tag['id']
                
        return None
        
    def paintEvent(self, event):
        """Override paint event to draw tags.
        
        Args:
            event: Paint event
        """
        # Draw the image first
        super().paintEvent(event)
        
        if not self.tags:
            return
            
        painter = QPainter(self)
        
        for tag in self.tags:
            tag_id = tag['id']
            tag_x = tag['x_position']
            tag_y = tag['y_position']
            tag_width = tag['width']
            tag_height = tag['height']
            character_name = tag.get('character_name', 'Unknown')
            
            # Convert to absolute coordinates
            abs_x, abs_y = self._to_absolute_coords(tag_x, tag_y)
            abs_width = int(tag_width * self.image_width)
            abs_height = int(tag_height * self.image_height)
            
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
                
            painter.setPen(pen)
            
            # Draw tag rectangle
            painter.drawRect(abs_x, abs_y, abs_width, abs_height)
            
            # Draw character name
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.setPen(QColor(255, 255, 255))  # White text
            
            # Draw background for text
            text_rect = QRect(abs_x, abs_y - 20, abs_width, 20)
            painter.fillRect(text_rect, QColor(0, 0, 0, 180))  # Semi-transparent black background
            
            # Draw text
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, character_name)


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
        self.tag_completer = CharacterTagCompleter(self)
        self.tag_completer.set_characters(self.characters)
        self.tag_completer.character_selected.connect(self.insert_character_tag)
        self.tag_completer.hide()
        
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
        """Get the edited text.
        
        Returns:
            The text from the editor
        """
        return self.text_edit.toPlainText()
        
    def get_character_id(self) -> int:
        """Get the selected character ID.
        
        Returns:
            ID of the selected character
        """
        return self.character_combo.currentData()
        
    def check_for_character_tag(self):
        """Check if the user is typing a character tag and provide suggestions."""
        cursor = self.text_edit.textCursor()
        text = self.text_edit.toPlainText()
        
        # Find the current word being typed
        pos = cursor.position()
        start = max(0, pos - 1)
        
        # Check if we're in the middle of typing a tag
        if start >= 0 and pos <= len(text):
            # Look backward to find the start of the current tag
            tag_start = text.rfind('@', 0, pos)
            
            if tag_start >= 0 and tag_start < pos:
                # We found a @ character before the cursor
                # Extract the partial tag text
                partial_tag = text[tag_start + 1:pos]
                
                # Only show suggestions if we're actively typing a tag
                if tag_start == pos - 1 or partial_tag.strip():
                    # Position the completer popup below the cursor
                    cursor_rect = self.text_edit.cursorRect()
                    global_pos = self.text_edit.mapToGlobal(cursor_rect.bottomLeft())
                    
                    self.tag_completer.set_filter(partial_tag)
                    self.tag_completer.move(global_pos)
                    return
                    
        # Hide the completer if we're not typing a tag
        self.tag_completer.hide()
        
    def insert_character_tag(self, character_name: str):
        """Insert a character tag at the current cursor position.
        
        Args:
            character_name: Name of the character to tag
        """
        cursor = self.text_edit.textCursor()
        text = self.text_edit.toPlainText()
        pos = cursor.position()
        
        # Find the start of the current tag
        tag_start = text.rfind('@', 0, pos)
        
        if tag_start >= 0:
            # Replace the partial tag with the full tag
            cursor.setPosition(tag_start, QTextCursor.MoveMode.MoveAnchor)
            cursor.setPosition(pos, QTextCursor.MoveMode.KeepAnchor)
            cursor.insertText(f"@{character_name}")
            
            # Add a space after the tag
            cursor.insertText(" ")
            
            # Set focus back to the text edit
            self.text_edit.setFocus()


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
        self.image_id = image_id
        self.image_data = image_data
        self.pixmap = pixmap
        self.quick_events = []
        self.character_tags = []
        
        # Get the story ID for this image
        self.story_id = image_data.get('story_id')
        
        # Load characters for the story (needed for character tagging)
        self.characters = []
        if self.story_id:
            self.characters = get_story_characters(self.db_conn, self.story_id)
        
        self.init_ui()
        self.load_quick_events()
        self.load_character_tags()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle(self.image_data.get('title') or f"Image {self.image_id}")
        self.resize(800, 600)
        
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
        
        # Taggable image label
        self.image_label = TaggableImageLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Scale image to fit dialog
        max_size = QSize(750, 500)
        scaled_pixmap = self.pixmap.scaled(
            max_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.image_label.set_image(scaled_pixmap)
        self.image_label.tag_added.connect(self.add_character_tag)
        self.image_label.tag_selected.connect(self.on_tag_selected)
        
        image_view_layout.addWidget(self.image_label)
        
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
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        main_layout.addLayout(button_layout)
    
    def toggle_tag_mode(self, enabled):
        """Toggle character tagging mode.
        
        Args:
            enabled: Whether tagging mode is enabled
        """
        self.image_label.enable_tag_mode(enabled)
    
    def load_character_tags(self):
        """Load character tags for this image."""
        try:
            self.character_tags = get_image_character_tags(self.db_conn, self.image_id)
            self.update_character_tags_list()
            self.image_label.set_tags(self.character_tags)
        except Exception as e:
            print(f"Error loading character tags: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load character tags: {str(e)}")
    
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
            x_position: X position (0.0-1.0)
            y_position: Y position (0.0-1.0)
        """
        if not self.story_id:
            QMessageBox.warning(self, "Error", "Cannot determine story ID for this image.")
            return
        
        # Show character selection dialog
        dialog = CharacterSelectionDialog(
            self.db_conn,
            self.story_id,
            parent=self
        )
        
        if dialog.exec():
            character_id = dialog.get_selected_character_id()
            
            if not character_id:
                return
                
            # Ask for an optional note
            note, ok = QInputDialog.getText(
                self,
                "Tag Note",
                "Enter an optional note for this tag:"
            )
            
            if not ok:
                note = None
                
            try:
                # Add the tag to the database
                tag_id = add_character_tag_to_image(
                    self.db_conn,
                    self.image_id,
                    character_id,
                    x_position,
                    y_position,
                    0.1,  # Default tag width (10% of image)
                    0.1,  # Default tag height (10% of image)
                    note
                )
                
                if tag_id:
                    # Reload character tags to update the UI
                    self.load_character_tags()
                    
                    # Turn off tag mode
                    self.tag_mode_button.setChecked(False)
                else:
                    QMessageBox.warning(self, "Error", "Failed to add character tag.")
            except Exception as e:
                print(f"Error adding character tag: {e}")
                QMessageBox.warning(self, "Error", f"Failed to add character tag: {str(e)}")
    
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
        self.image_label.selected_tag_id = tag_id
        self.image_label.update()
        
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
            self.quick_events = get_image_quick_events(self.db_conn, self.image_id)
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
        character_events = {}
        for event in self.quick_events:
            character_id = event.get('character_id')
            character_name = event.get('character_name', 'Unknown Character')
            
            if character_id not in character_events:
                character_events[character_id] = {
                    'name': character_name,
                    'events': []
                }
                
            character_events[character_id]['events'].append(event)
        
        # Add items for each character's events
        for character_id, data in character_events.items():
            # Add a header item for this character
            header_item = QListWidgetItem(f"--- {data['name']} ---")
            header_item.setFlags(Qt.ItemFlag.NoItemFlags)  # Make non-selectable
            header_item.setBackground(QBrush(QColor("#333333")))
            self.quick_events_list.addItem(header_item)
            
            # Add events for this character
            for event in data['events']:
                item = QListWidgetItem(event['text'])
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
        
        # Add spacer to push buttons to the left
        button_layout.addStretch()
        
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
        
        # Add container to scroll area
        self.scroll_area.setWidget(self.thumbnails_container)
        
        # Add scroll area to main layout
        main_layout.addWidget(self.scroll_area)
        
        # Create status label
        self.status_label = QLabel("No story selected")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        main_layout.addWidget(self.status_label)
    
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
        
        # Update status
        self.status_label.setText(f"Gallery for: {story_data['title']}")
        
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
        
        # Create thumbnails
        for i, image in enumerate(images):
            image_id = image['id']
            filename = image['filename']
            
            # Get thumbnail path
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
                        continue
                else:
                    print(f"Warning: Original image not found: {original_path}")
                    continue
            
            # Load thumbnail
            pixmap = QPixmap(thumbnail_path)
            if not pixmap.isNull():
                # Create thumbnail widget
                row = i // 4  # 4 thumbnails per row
                col = i % 4
                thumbnail = ThumbnailWidget(image_id, pixmap, image['title'])
                thumbnail.clicked.connect(self.on_thumbnail_clicked)
                thumbnail.delete_requested.connect(self.on_delete_image)
                
                # Add to layout
                self.thumbnails_layout.addWidget(thumbnail, row, col)
                self.thumbnails[image_id] = thumbnail
            else:
                print(f"Warning: Failed to load thumbnail: {thumbnail_path}")
        
        # Update status
        if images:
            self.status_label.setText(f"Gallery for: {self.current_story_data['title']} ({len(images)} images)")
        else:
            self.status_label.setText(f"Gallery for: {self.current_story_data['title']} (No images)")
    
    def clear_thumbnails(self) -> None:
        """Clear all thumbnails."""
        # Remove all thumbnails from layout
        for thumbnail in self.thumbnails.values():
            self.thumbnails_layout.removeWidget(thumbnail)
            thumbnail.deleteLater()
        
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
            image: QImage to save
        """
        if not self.current_story_id or not self.current_story_data:
            return
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"image_{timestamp}_{unique_id}.png"
        
        # Get story folders
        images_folder = os.path.join(self.current_story_data['folder_path'], "images")
        thumbnails_folder = os.path.join(self.current_story_data['folder_path'], "thumbnails")
        
        # Ensure folders exist
        os.makedirs(images_folder, exist_ok=True)
        os.makedirs(thumbnails_folder, exist_ok=True)
        
        # Save original image to file
        image_path = os.path.join(images_folder, filename)
        success = image.save(image_path, "PNG")
        
        if success:
            # Generate and save thumbnail
            thumbnail = self._generate_thumbnail(image, max_dimension=320)
            thumbnail_path = os.path.join(thumbnails_folder, filename)
            thumbnail_success = thumbnail.save(thumbnail_path, "PNG")
            
            if not thumbnail_success:
                print(f"Warning: Failed to save thumbnail to {thumbnail_path}")
            
            # Save to database
            cursor = self.db_conn.cursor()
            cursor.execute(
                """
                INSERT INTO images (
                    filename, path, title, width, height, 
                    file_size, mime_type, story_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                """,
                (
                    filename,
                    images_folder,
                    f"Image {timestamp}",
                    image.width(),
                    image.height(),
                    os.path.getsize(image_path),
                    "image/png",
                    self.current_story_id
                )
            )
            self.db_conn.commit()
            
            # Reload images
            self.load_images()
        else:
            self.show_error("Save Failed", f"Failed to save image to {image_path}")
    
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
        """Handle thumbnail click.
        
        Args:
            image_id: ID of the clicked image
        """
        # Get image from database
        cursor = self.db_conn.cursor()
        cursor.execute(
            "SELECT * FROM images WHERE id = ?",
            (image_id,)
        )
        image_data = cursor.fetchone()
        
        if image_data:
            # Convert to dictionary for easier access
            image_data = dict(image_data)
            
            # Load the image
            image_path = os.path.join(image_data['path'], image_data['filename'])
            if os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    # Show image in detail dialog
                    dialog = ImageDetailDialog(self.db_conn, image_id, image_data, pixmap, self)
                    dialog.exec()
    
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