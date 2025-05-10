#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Character Dialog for The Plot Thickens application.

This module defines the dialog for editing character data.
"""

import os
import time
from typing import Optional, Dict, Any, List, Tuple

from PyQt6.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QSpinBox, QCheckBox, QPushButton,
    QFileDialog, QMessageBox, QApplication, QGroupBox, QListWidget, 
    QListWidgetItem, QMenu, QTextEdit, QSplitter,
    QTreeWidget, QTreeWidgetItem, QStyle
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QPixmap, QImage, QCloseEvent, QAction, QCursor, QColor

from app.utils.character_completer import CharacterCompleter

# Import the centralized character reference functions
from app.utils.character_references import convert_mentions_to_char_refs, convert_char_refs_to_mentions

from app.db_sqlite import (
    get_character, get_story, get_character_quick_events,
    create_quick_event, update_quick_event, delete_quick_event, 
    get_next_quick_event_sequence_number, get_quick_event_tagged_characters,
    get_story_characters, get_quick_event_images, associate_quick_event_with_image,
    remove_quick_event_image_association, get_story_images,
    add_character_detail, update_character_detail, delete_character_detail, 
    get_character_details, update_character_detail_sequence
)


class CharacterTagEditor(QDialog):
    """Dialog for editing quick event text with character tag support."""
    
    def __init__(self, db_conn, character_id: int, text: str = "", parent=None):
        """Initialize the character tag editor.
        
        Args:
            db_conn: Database connection
            character_id: ID of the character the quick event belongs to
            text: Initial text (default empty)
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.character_id = character_id
        
        # Get the story ID for this character
        character = get_character(db_conn, character_id)
        self.story_id = character.get('story_id') if character else None
        
        # Load available characters
        self.characters = []
        if self.story_id:
            self.characters = get_story_characters(db_conn, self.story_id)
        
        # Convert any [char:ID] references to @CharacterName format for display
        self.initial_text = convert_char_refs_to_mentions(text, self.characters)
        
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
        self.setWindowTitle("Quick Event")
        self.resize(450, 200)
        
        layout = QVBoxLayout(self)
        
        # Text edit
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Enter quick event text. Use @name to tag characters (e.g., @John kissed @Mary)")
        self.text_edit.setText(self.initial_text)
        layout.addWidget(self.text_edit)
        
        # Available characters
        if self.characters:
            char_names = [f"@{char['name']}" for char in self.characters]
            characters_label = QLabel("Available character tags: " + ", ".join(char_names))
            characters_label.setWordWrap(True)
            characters_label.setStyleSheet("color: #666; font-style: italic;")
            layout.addWidget(characters_label)
        
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
            The processed text from the editor with character references
        """
        display_text = self.text_edit.toPlainText()
        # Convert @mentions to [char:ID] for storage
        return convert_mentions_to_char_refs(display_text, self.characters)
    
    def on_character_selected(self, character_name: str):
        """Handle character selection from completer.
        
        Args:
            character_name: Name of the selected character
        """
        # Let the completer handle the insertion
        self.tag_completer.insert_character_tag(character_name)


class QuickEventItem(QListWidgetItem):
    """List widget item representing a quick event."""
    
    def __init__(self, event_data: Dict[str, Any], tagged_characters: List[Dict[str, Any]] = None, 
                associated_images: List[Dict[str, Any]] = None, viewing_character_id: int = None):
        """Initialize a quick event item.
        
        Args:
            event_data: Quick event data dictionary
            tagged_characters: List of tagged character dictionaries
            associated_images: List of associated image dictionaries
            viewing_character_id: ID of the character viewing this event (to determine ownership)
        """
        super().__init__()
        self.event_data = event_data
        self.event_id = event_data['id']
        self.raw_text = event_data['text']
        self.tagged_characters = tagged_characters or []
        self.associated_images = associated_images or []
        self.viewing_character_id = viewing_character_id
        self.is_owner = viewing_character_id == event_data.get('character_id')
        
        # Convert any [char:ID] references to @CharacterName format for display
        self.display_text = self.format_display_text(self.raw_text, self.tagged_characters)
        
        # Add a prefix to show if this character owns the event or was just tagged
        prefix = "" if self.is_owner else "↪ " 
        self.setText(f"{prefix}{self.display_text}")
        
        # Add character tags and associated images to tooltip
        tooltip = self.display_text
        
        # Add owner info to tooltip if this character is not the owner
        if not self.is_owner and event_data.get('character_id'):
            # Try to find the owner character in the tagged characters list
            owner_name = "Unknown"
            for char in self.tagged_characters:
                if char['id'] == event_data['character_id']:
                    owner_name = char['name']
                    break
            tooltip = f"From {owner_name}'s timeline:\n{tooltip}"
        
        if self.tagged_characters:
            char_names = [char['name'] for char in self.tagged_characters]
            tooltip += f"\n\nTagged characters: {', '.join(char_names)}"
            
        if self.associated_images:
            image_count = len(self.associated_images)
            tooltip += f"\n\nAssociated with {image_count} image{'s' if image_count != 1 else ''}"
            
        self.setToolTip(tooltip)
        
        # Store the event ID as user data
        self.setData(Qt.ItemDataRole.UserRole, self.event_id)
        
        # Set a different background color for events where this character is tagged but not the owner
        if not self.is_owner:
            self.setBackground(QColor(240, 240, 250))  # Light blue-ish background
            self.setForeground(QColor(0, 0, 0))  # Black text for better contrast
    
    def format_display_text(self, text: str, characters: List[Dict[str, Any]]) -> str:
        """Format text for display, converting [char:ID] references to @CharacterName.
        
        Args:
            text: Raw text with [char:ID] references
            characters: List of character dictionaries
            
        Returns:
            Formatted text for display
        """
        # Use the centralized implementation while maintaining the same interface
        return convert_char_refs_to_mentions(text, characters)


class ImageSelectionDialog(QDialog):
    """Dialog for selecting images to associate with a quick event."""
    
    def __init__(self, db_conn, story_id: int, current_image_ids: List[int] = None, parent=None):
        """Initialize the image selection dialog.
        
        Args:
            db_conn: Database connection
            story_id: ID of the story
            current_image_ids: List of already associated image IDs
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.story_id = story_id
        self.current_image_ids = current_image_ids or []
        self.selected_image_ids = []
        
        self.init_ui()
        self.load_images()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Select Images")
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # Image list
        self.image_list = QListWidget()
        self.image_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        layout.addWidget(self.image_list)
        
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
        
    def load_images(self):
        """Load images for the story."""
        try:
            # Get all images for the story
            images = get_story_images(self.db_conn, self.story_id)
            
            for image in images:
                # Create a list item with the image title or filename
                title = image.get('title') or image.get('filename') or f"Image {image['id']}"
                item = QListWidgetItem(title)
                item.setData(Qt.ItemDataRole.UserRole, image['id'])
                
                # Set the item to be pre-selected if it's already associated
                if image['id'] in self.current_image_ids:
                    item.setSelected(True)
                
                self.image_list.addItem(item)
        except Exception as e:
            print(f"Error loading images: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load images: {str(e)}")
    
    def get_selected_image_ids(self) -> List[int]:
        """Get the IDs of the selected images.
        
        Returns:
            List of selected image IDs
        """
        self.selected_image_ids = []
        
        for i in range(self.image_list.count()):
            item = self.image_list.item(i)
            if item.isSelected():
                image_id = item.data(Qt.ItemDataRole.UserRole)
                self.selected_image_ids.append(image_id)
                
        return self.selected_image_ids


class QuickEventsTab(QWidget):
    """Tab for managing character quick events."""
    
    def __init__(self, db_conn, character_id: int, parent=None):
        """Initialize the quick events tab.
        
        Args:
            db_conn: Database connection
            character_id: ID of the character
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.character_id = character_id
        self.quick_events = []
        
        # Get the story ID for this character
        character = get_character(db_conn, character_id)
        self.story_id = character.get('story_id') if character else None
        
        self.init_ui()
        self.load_quick_events()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Header with explanation
        header_label = QLabel(
            "Quick events are simple actions or moments related to this character. "
            "Use @name to tag other characters involved in the event."
        )
        header_label.setWordWrap(True)
        layout.addWidget(header_label)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        self.add_event_button = QPushButton("Add Quick Event")
        self.add_event_button.clicked.connect(self.add_quick_event)
        toolbar_layout.addWidget(self.add_event_button)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # Splitter for events list and associated images
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Quick events list
        self.events_list = QListWidget()
        self.events_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.events_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.events_list.customContextMenuRequested.connect(self.show_context_menu)
        self.events_list.currentItemChanged.connect(self.on_event_selected)
        splitter.addWidget(self.events_list)
        
        # Associated images panel
        images_widget = QWidget()
        images_layout = QVBoxLayout(images_widget)
        images_layout.setContentsMargins(0, 0, 0, 0)
        
        images_header = QLabel("Associated Images:")
        images_layout.addWidget(images_header)
        
        self.images_list = QListWidget()
        self.images_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.images_list.customContextMenuRequested.connect(self.show_images_context_menu)
        images_layout.addWidget(self.images_list)
        
        splitter.addWidget(images_widget)
        
        # Set initial sizes
        splitter.setSizes([400, 200])
        
        layout.addWidget(splitter)
        
    def load_quick_events(self):
        """Load quick events for the character."""
        try:
            # Clear existing items
            self.events_list.clear()
            self.images_list.clear()
            
            # Get all quick events for the character
            self.quick_events = get_character_quick_events(self.db_conn, self.character_id)
            
            if not self.quick_events:
                # No events found
                empty_item = QListWidgetItem("No quick events found for this character.")
                empty_item.setFlags(Qt.ItemFlag.NoItemFlags)  # Make non-selectable
                self.events_list.addItem(empty_item)
                return
            
            # Add quick events to the list
            for event in self.quick_events:
                # Get the tagged characters and associated images for this event
                tagged_characters = get_quick_event_tagged_characters(self.db_conn, event['id'])
                associated_images = get_quick_event_images(self.db_conn, event['id'])
                
                item = QuickEventItem(event, tagged_characters, associated_images, self.character_id)
                self.events_list.addItem(item)
        except Exception as e:
            print(f"Error loading quick events: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load quick events: {str(e)}")
    
    def on_event_selected(self, current, previous):
        """Handle event selection change.
        
        Args:
            current: Currently selected item
            previous: Previously selected item
        """
        self.images_list.clear()
        
        if not current or not isinstance(current, QuickEventItem):
            return
            
        # Display associated images
        if current.associated_images:
            for image in current.associated_images:
                title = image.get('title') or image.get('filename') or f"Image {image['id']}"
                item = QListWidgetItem(title)
                item.setData(Qt.ItemDataRole.UserRole, image['id'])
                
                # Add note as tooltip if available
                if image.get('note'):
                    item.setToolTip(image['note'])
                    
                self.images_list.addItem(item)
        else:
            empty_item = QListWidgetItem("No images associated with this event.")
            empty_item.setFlags(Qt.ItemFlag.NoItemFlags)  # Make non-selectable
            self.images_list.addItem(empty_item)
    
    def add_quick_event(self):
        """Add a new quick event."""
        dialog = CharacterTagEditor(self.db_conn, self.character_id, parent=self)
        
        if dialog.exec():
            text = dialog.get_text()
            
            if not text.strip():
                QMessageBox.warning(self, "Error", "Quick event text cannot be empty.")
                return
                
            try:
                # Get the next sequence number to place the event at the end
                sequence_number = get_next_quick_event_sequence_number(self.db_conn, self.character_id)
                
                # Create the quick event
                quick_event_id = create_quick_event(
                    self.db_conn,
                    text,
                    self.character_id,
                    sequence_number
                )
                
                if quick_event_id:
                    # Reload the events
                    self.load_quick_events()
                else:
                    QMessageBox.warning(self, "Error", "Failed to create quick event.")
            except Exception as e:
                print(f"Error adding quick event: {e}")
                QMessageBox.warning(self, "Error", f"Failed to add quick event: {str(e)}")
    
    def edit_quick_event(self, event_id: int):
        """Edit an existing quick event.
        
        Args:
            event_id: ID of the quick event to edit
        """
        # Find the event in the list
        event = next((e for e in self.quick_events if e['id'] == event_id), None)
        if not event:
            return
            
        dialog = CharacterTagEditor(self.db_conn, self.character_id, event['text'], parent=self)
        
        if dialog.exec():
            text = dialog.get_text()
            
            if not text.strip():
                QMessageBox.warning(self, "Error", "Quick event text cannot be empty.")
                return
                
            try:
                # Update the quick event
                success = update_quick_event(
                    self.db_conn,
                    event_id,
                    text=text
                )
                
                if success:
                    # Reload the events
                    self.load_quick_events()
                else:
                    QMessageBox.warning(self, "Error", "Failed to update quick event.")
            except Exception as e:
                print(f"Error updating quick event: {e}")
                QMessageBox.warning(self, "Error", f"Failed to update quick event: {str(e)}")
    
    def delete_quick_event(self, event_id: int):
        """Delete a quick event.
        
        Args:
            event_id: ID of the quick event to delete
        """
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this quick event?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                success = delete_quick_event(self.db_conn, event_id)
                
                if success:
                    # Reload the events
                    self.load_quick_events()
                else:
                    QMessageBox.warning(self, "Error", "Failed to delete quick event.")
            except Exception as e:
                print(f"Error deleting quick event: {e}")
                QMessageBox.warning(self, "Error", f"Failed to delete quick event: {str(e)}")
    
    def manage_event_images(self, event_id: int):
        """Manage images associated with a quick event.
        
        Args:
            event_id: ID of the quick event
        """
        # Check if we have a story ID
        if not self.story_id:
            QMessageBox.warning(self, "Error", "Cannot get story ID for this character.")
            return
            
        # Get current associated images
        try:
            current_images = get_quick_event_images(self.db_conn, event_id)
            current_image_ids = [img['id'] for img in current_images]
        except Exception as e:
            print(f"Error getting current images: {e}")
            current_image_ids = []
            
        # Show image selection dialog
        dialog = ImageSelectionDialog(
            self.db_conn, 
            self.story_id,
            current_image_ids,
            parent=self
        )
        
        if dialog.exec():
            selected_image_ids = dialog.get_selected_image_ids()
            
            try:
                # Remove associations for images that were deselected
                for image_id in current_image_ids:
                    if image_id not in selected_image_ids:
                        remove_quick_event_image_association(self.db_conn, event_id, image_id)
                
                # Add associations for newly selected images
                for image_id in selected_image_ids:
                    if image_id not in current_image_ids:
                        associate_quick_event_with_image(self.db_conn, event_id, image_id)
                        
                # Reload events to update the UI
                self.load_quick_events()
                
                # Update the selected event to refresh the images list
                current_item = self.events_list.currentItem()
                if current_item and isinstance(current_item, QuickEventItem) and current_item.event_id == event_id:
                    self.on_event_selected(current_item, None)
                    
            except Exception as e:
                print(f"Error managing event images: {e}")
                QMessageBox.warning(self, "Error", f"Failed to update image associations: {str(e)}")
    
    def remove_image_association(self, image_id: int):
        """Remove an image association from the current quick event.
        
        Args:
            image_id: ID of the image to disassociate
        """
        current_item = self.events_list.currentItem()
        if not current_item or not isinstance(current_item, QuickEventItem):
            return
            
        event_id = current_item.event_id
        
        confirm = QMessageBox.question(
            self,
            "Confirm Removal",
            "Are you sure you want to remove this image association?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                success = remove_quick_event_image_association(self.db_conn, event_id, image_id)
                
                if success:
                    # Reload events to update the UI
                    self.load_quick_events()
                    
                    # Update the selected event to refresh the images list
                    self.on_event_selected(current_item, None)
                else:
                    QMessageBox.warning(self, "Error", "Failed to remove image association.")
            except Exception as e:
                print(f"Error removing image association: {e}")
                QMessageBox.warning(self, "Error", f"Failed to remove image association: {str(e)}")
    
    def show_context_menu(self, position: QPoint):
        """Show context menu for a quick event.
        
        Args:
            position: Position where the menu should be displayed
        """
        item = self.events_list.itemAt(position)
        
        if not item or not isinstance(item, QuickEventItem):
            return
            
        event_id = item.event_id
        
        menu = QMenu(self)
        
        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(lambda: self.edit_quick_event(event_id))
        menu.addAction(edit_action)
        
        manage_images_action = QAction("Manage Associated Images", self)
        manage_images_action.triggered.connect(lambda: self.manage_event_images(event_id))
        menu.addAction(manage_images_action)
        
        menu.addSeparator()
        
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.delete_quick_event(event_id))
        menu.addAction(delete_action)
        
        # Show the menu
        menu.exec(QCursor.pos())
    
    def show_images_context_menu(self, position: QPoint):
        """Show context menu for an associated image.
        
        Args:
            position: Position where the menu should be displayed
        """
        item = self.images_list.itemAt(position)
        
        if not item or item.flags() & Qt.ItemFlag.ItemIsSelectable == 0:
            return
            
        image_id = item.data(Qt.ItemDataRole.UserRole)
        
        menu = QMenu(self)
        
        remove_action = QAction("Remove Association", self)
        remove_action.triggered.connect(lambda: self.remove_image_association(image_id))
        menu.addAction(remove_action)
        
        # Show the menu
        menu.exec(QCursor.pos())


class CharacterDetailsTab(QWidget):
    """Tab for managing character details."""
    
    def __init__(self, db_conn, character_id: int, parent=None):
        """Initialize the character details tab.
        
        Args:
            db_conn: Database connection
            character_id: ID of the character
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.character_id = character_id
        
        # Define the global categories
        self.global_categories = [
            ("Work", "WORK"),
            ("Study", "STUDY"),
            ("Relationship Status", "RELATIONSHIP"),
            ("Housing", "HOUSING"),
            ("Family", "FAMILY"),
            ("Quotes", "QUOTES"),
            # Keep existing categories
            ("General", "GENERAL"),
            ("Background", "BACKGROUND"),
            ("Personality", "PERSONALITY"),
            ("Physical", "PHYSICAL"),
        ]
        
        self.init_ui()
        self.load_details()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Filter layout (top)
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by type:"))
        
        self.type_combo = QComboBox()
        self.type_combo.addItem("All", None)
        
        # Add global categories to combo box
        for name, code in self.global_categories:
            self.type_combo.addItem(name, code)
            
        self.type_combo.currentIndexChanged.connect(self.filter_details)
        filter_layout.addWidget(self.type_combo)
        
        filter_layout.addStretch()
        
        # Add button
        self.add_button = QPushButton("Add Detail")
        self.add_button.clicked.connect(self.add_detail)
        filter_layout.addWidget(self.add_button)
        
        layout.addLayout(filter_layout)
        
        # Details tree view
        self.details_tree = QTreeWidget()
        self.details_tree.setHeaderLabels(["Details"])
        self.details_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.details_tree.customContextMenuRequested.connect(self.show_context_menu)
        self.details_tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.details_tree.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
        self.details_tree.setExpandsOnDoubleClick(True)
        self.details_tree.setAnimated(True)
        self.details_tree.setIndentation(20)
        
        # Connect folder icon updating when expanded/collapsed
        folder_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DirClosedIcon)
        open_folder_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon)
        
        self.details_tree.itemExpanded.connect(
            lambda item: item.setIcon(0, open_folder_icon) if not hasattr(item, 'detail_id') else None
        )
        self.details_tree.itemCollapsed.connect(
            lambda item: item.setIcon(0, folder_icon) if not hasattr(item, 'detail_id') else None
        )
        
        # Enable drag and drop for reordering
        self.details_tree.model().rowsMoved.connect(self.on_items_reordered)
        
        layout.addWidget(self.details_tree)
    
    def load_details(self):
        """Load details for this character."""
        try:
            self.details = get_character_details(self.db_conn, self.character_id)
            self.update_details_tree()
        except Exception as e:
            print(f"Error loading character details: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load character details: {str(e)}")
            
    def update_details_tree(self):
        """Update the details tree with current details."""
        self.details_tree.clear()
        
        if not self.details:
            empty_item = QTreeWidgetItem(["No details added yet."])
            # Make it non-selectable
            empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.details_tree.addTopLevelItem(empty_item)
            return
        
        # Create a dictionary to store category items
        category_items = {}
        
        # Get folder icons for categories - using theme-compatible icons
        folder_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DirClosedIcon)
        
        # Filter by type if needed
        selected_type = self.type_combo.currentData()
        
        # Create category nodes
        if selected_type is None:
            # Create all category folders
            for name, code in self.global_categories:
                category_item = QTreeWidgetItem([name])
                category_item.setData(0, Qt.ItemDataRole.UserRole, code)
                category_item.setFlags(category_item.flags() | Qt.ItemFlag.ItemIsAutoTristate)
                # Add folder icon
                category_item.setIcon(0, folder_icon)
                category_items[code] = category_item
                self.details_tree.addTopLevelItem(category_item)
        else:
            # Create just one category folder
            for name, code in self.global_categories:
                if code == selected_type:
                    category_item = QTreeWidgetItem([name])
                    category_item.setData(0, Qt.ItemDataRole.UserRole, code)
                    category_item.setFlags(category_item.flags() | Qt.ItemFlag.ItemIsAutoTristate)
                    # Add folder icon
                    category_item.setIcon(0, folder_icon)
                    category_items[code] = category_item
                    self.details_tree.addTopLevelItem(category_item)
                    break
        
        # Add details to their respective categories
        for detail in self.details:
            detail_type = detail['detail_type']
            
            # Skip if filtering and not matching
            if selected_type is not None and detail_type != selected_type:
                continue
                
            # If the category doesn't exist yet, create an "Other" category
            if detail_type not in category_items:
                category_item = QTreeWidgetItem(["Other"])
                category_item.setData(0, Qt.ItemDataRole.UserRole, "OTHER")
                # Add folder icon
                category_item.setIcon(0, folder_icon)
                category_items[detail_type] = category_item
                self.details_tree.addTopLevelItem(category_item)
            
            # Create the detail item
            detail_item = QTreeWidgetItem([detail['detail_text']])
            detail_item.setData(0, Qt.ItemDataRole.UserRole, detail['id'])
            detail_item.setToolTip(0, detail['detail_text'])
            
            # Store the detail data for later use
            detail_item.detail_id = detail['id']
            detail_item.detail_text = detail['detail_text']
            detail_item.detail_type = detail['detail_type']
            detail_item.sequence_number = detail['sequence_number']
            
            # Add to the appropriate category
            category_items[detail_type].addChild(detail_item)
        
        # Expand all categories
        self.details_tree.expandAll()
                
    def filter_details(self):
        """Filter details by type."""
        self.update_details_tree()
        
    def add_detail(self):
        """Add a new character detail."""
        # Show the add detail dialog
        dialog = AddDetailDialog(self.global_categories, parent=self)
        
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        # Get the entered data
        detail_text = dialog.get_detail_text()
        detail_type = dialog.get_detail_type()
        
        if not detail_text:
            return
        
        try:
            # Add the detail to the database
            detail_id = add_character_detail(
                self.db_conn,
                self.character_id,
                detail_text,
                detail_type
            )
            
            if detail_id:
                # Reload details to update the tree
                self.load_details()
            else:
                QMessageBox.warning(self, "Error", "Failed to add character detail.")
        except Exception as e:
            print(f"Error adding character detail: {e}")
            QMessageBox.warning(self, "Error", f"Failed to add character detail: {str(e)}")
            
    def edit_detail(self, item):
        """Edit a character detail.
        
        Args:
            item: The detail tree item to edit
        """
        # Only allow editing detail items, not category folders
        if not hasattr(item, 'detail_id'):
            return
        
        # Show the edit detail dialog
        dialog = AddDetailDialog(
            self.global_categories,
            detail_text=item.detail_text,
            detail_type=item.detail_type,
            parent=self
        )
        
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        # Get the entered data
        detail_text = dialog.get_detail_text()
        detail_type = dialog.get_detail_type()
        
        if not detail_text:
            return
        
        try:
            # Update the detail in the database
            success = update_character_detail(
                self.db_conn,
                item.detail_id,
                detail_text,
                detail_type
            )
            
            if success:
                # Reload details to update the tree
                self.load_details()
            else:
                QMessageBox.warning(self, "Error", "Failed to update character detail.")
        except Exception as e:
            print(f"Error updating character detail: {e}")
            QMessageBox.warning(self, "Error", f"Failed to update character detail: {str(e)}")
            
    def delete_detail(self, item):
        """Delete a character detail.
        
        Args:
            item: The detail tree item to delete
        """
        # Only allow deleting detail items, not category folders
        if not hasattr(item, 'detail_id'):
            return
            
        # Confirm deletion
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete this detail?\n\n{item.detail_text}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm != QMessageBox.StandardButton.Yes:
            return
            
        try:
            # Delete the detail from the database
            success = delete_character_detail(self.db_conn, item.detail_id)
            
            if success:
                # Reload details to update the tree
                self.load_details()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete character detail.")
        except Exception as e:
            print(f"Error deleting character detail: {e}")
            QMessageBox.warning(self, "Error", f"Failed to delete character detail: {str(e)}")
            
    def on_items_reordered(self):
        """Handle reordering of items through drag and drop."""
        try:
            # This is more complex with a tree structure
            # We'll need to update sequence numbers within each category
            
            # Update sequence numbers for all items
            sequence = 0
            
            for cat_idx in range(self.details_tree.topLevelItemCount()):
                category = self.details_tree.topLevelItem(cat_idx)
                
                for detail_idx in range(category.childCount()):
                    item = category.child(detail_idx)
                    
                    # Skip non-detail items
                    if not hasattr(item, 'detail_id'):
                        continue
                        
                    # Update sequence number
                    if item.sequence_number != sequence:
                        update_character_detail_sequence(self.db_conn, item.detail_id, sequence)
                        item.sequence_number = sequence
                    
                    sequence += 1
                    
            # Reload the data to ensure everything is in sync
            self.load_details()
        except Exception as e:
            print(f"Error updating sequence numbers: {e}")
            QMessageBox.warning(self, "Error", f"Failed to update sequence numbers: {str(e)}")
            
    def show_context_menu(self, position: QPoint):
        """Show context menu for a detail.
        
        Args:
            position: Position where the menu should be displayed
        """
        item = self.details_tree.itemAt(position)
        
        if not item:
            return
            
        # Only show edit/delete options for detail items, not categories
        if not hasattr(item, 'detail_id'):
            return
            
        menu = QMenu(self)
        
        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(lambda: self.edit_detail(item))
        menu.addAction(edit_action)
        
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.delete_detail(item))
        menu.addAction(delete_action)
        
        # Show the menu
        menu.exec(self.details_tree.mapToGlobal(position))


class AddDetailDialog(QDialog):
    """Dialog for adding or editing a character detail with category support."""
    
    def __init__(self, categories: List[Tuple[str, str]], 
                 detail_text: str = "", detail_type: str = None, parent=None):
        """Initialize the add detail dialog.
        
        Args:
            categories: List of (name, code) tuples for categories
            detail_text: Initial detail text (for edit mode)
            detail_type: Initial detail type (for edit mode)
            parent: Parent widget
        """
        super().__init__(parent)
        self.categories = categories
        self.detail_text = detail_text
        self.detail_type = detail_type
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Character Detail")
        self.resize(400, 150)
        
        layout = QVBoxLayout(self)
        
        # Detail text
        layout.addWidget(QLabel("Enter detail (e.g., 'Afraid of heights' or 'Has a scar on left cheek'):"))
        self.text_edit = QLineEdit(self.detail_text)
        layout.addWidget(self.text_edit)
        
        # Category selection
        layout.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        
        # Populate category dropdown
        selected_index = 0
        for i, (name, code) in enumerate(self.categories):
            self.category_combo.addItem(name, code)
            if code == self.detail_type:
                selected_index = i
                
        # Set the current selection if editing
        if self.detail_type:
            self.category_combo.setCurrentIndex(selected_index)
            
        layout.addWidget(self.category_combo)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setDefault(True)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
        
    def get_detail_text(self) -> str:
        """Get the entered detail text.
        
        Returns:
            The detail text entered by the user
        """
        return self.text_edit.text().strip()
        
    def get_detail_type(self) -> str:
        """Get the selected detail type code.
        
        Returns:
            The code of the selected detail type
        """
        return self.category_combo.currentData()


class CharacterDialog(QDialog):
    """Dialog for creating and editing characters."""
    
    # Signal emitted when a character is updated
    character_updated = pyqtSignal(int, dict)
    
    def __init__(self, db_conn, story_id: int, character_id: Optional[int] = None, parent=None) -> None:
        """Initialize the character dialog.
        
        Args:
            db_conn: Database connection
            story_id: ID of the story
            character_id: ID of the character to edit (None for new character)
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.db_conn = db_conn
        self.story_id = story_id
        self.character_id = character_id
        self.avatar_path = None
        self.avatar_changed = False
        self.has_unsaved_changes = False
        
        # Initialize character data
        self.character_data = {
            'id': character_id,
            'name': '',
            'story_id': story_id,
            'aliases': '',
            'is_main_character': False,
            'age_value': None,
            'age_category': None,
            'gender': 'NOT_SPECIFIED',
            'avatar_path': None
        }
        
        # If editing an existing character, load its data
        if character_id is not None:
            character = get_character(db_conn, character_id)
            if character:
                self.character_data = character
                self.avatar_path = character['avatar_path']
        
        self.init_ui()
        self.load_character_data()
        
        # Connect signals
        self.connect_signals()
        
        # Set window properties
        self.setWindowTitle("Character Details")
        self.resize(800, 600)
    
    def init_ui(self) -> None:
        """Initialize the user interface."""
        self.setWindowTitle("Character Details")
        self.resize(800, 600)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self.summary_tab = QWidget()
        
        # Create the quick events tab if editing an existing character
        if self.character_id:
            self.quick_events_tab = QWidget()
            self.details_tab = QWidget()  # Add this line
        
        # Create tab contents
        self.create_summary_tab()
        
        # Add tabs to widget
        self.tab_widget.addTab(self.summary_tab, "Summary")
        
        if self.character_id:
            self.quick_events_tab = QuickEventsTab(self.db_conn, self.character_id)
            self.tab_widget.addTab(self.quick_events_tab, "Quick Events")
            
            # Add details tab
            self.details_tab = CharacterDetailsTab(self.db_conn, self.character_id)
            self.tab_widget.addTab(self.details_tab, "Details")
        
        layout.addWidget(self.tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_character)
        
        button_layout.addWidget(self.close_button)
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
    
    def create_summary_tab(self) -> None:
        """Create the summary tab."""
        layout = QVBoxLayout(self.summary_tab)
        
        # Create form layout for basic info
        form_layout = QFormLayout()
        
        # Name field
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Optional - will generate 'Unnamed X' if empty")
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
        self.avatar_preview.setScaledContents(False)
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
        if self.character_data['avatar_path']:
            avatar_path = self.character_data['avatar_path']
            print(f"DEBUG: Loading avatar from path: {avatar_path}")
            
            # Try to load the avatar
            pixmap = QPixmap(avatar_path)
            
            # If the pixmap is null, try to resolve the path
            if pixmap.isNull():
                # Try absolute path
                if not os.path.isabs(avatar_path):
                    abs_path = os.path.abspath(avatar_path)
                    print(f"DEBUG: Trying absolute path: {abs_path}")
                    pixmap = QPixmap(abs_path)
                
                # If still null, try to get the story folder path and construct the path
                if pixmap.isNull():
                    try:
                        # Get the story folder path from the database
                        story_data = get_story(self.db_conn, self.story_id)
                        story_folder = story_data['folder_path']
                        
                        # Extract the filename from the avatar path
                        filename = os.path.basename(avatar_path)
                        
                        # Construct the new path
                        new_path = os.path.join(story_folder, "images", filename)
                        print(f"DEBUG: Trying path with story folder: {new_path}")
                        pixmap = QPixmap(new_path)
                    except Exception as e:
                        print(f"DEBUG: Error resolving avatar path: {str(e)}")
            
            if not pixmap.isNull():
                scaled_pixmap = self._scale_pixmap_for_avatar(pixmap)
                self.avatar_preview.setPixmap(scaled_pixmap)
                print("DEBUG: Avatar loaded successfully")
            else:
                self.avatar_preview.setText("No Avatar")
                print(f"DEBUG: Failed to load avatar from path: {avatar_path}")
        else:
            self.avatar_preview.setText("No Avatar")
            print("DEBUG: No avatar path specified")
        
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
    
    def connect_signals(self) -> None:
        """Connect signals to slots."""
        # Field change signals are already connected in create_summary_tab
        # Button signals are already connected in init_ui
        # This method is provided for consistency and future expansion
        pass
    
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
                scaled_pixmap = self._scale_pixmap_for_avatar(pixmap)
                self.avatar_preview.setPixmap(scaled_pixmap)
                self.avatar_path = file_path
                self.avatar_changed = True
                self.on_field_changed()
    
    def paste_avatar(self) -> None:
        """Paste an image from the clipboard as the avatar."""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasImage():
            print("DEBUG: Found image in clipboard")
            image = QImage(clipboard.image())
            if not image.isNull():
                pixmap = QPixmap.fromImage(image)
                scaled_pixmap = self._scale_pixmap_for_avatar(pixmap)
                self.avatar_preview.setPixmap(scaled_pixmap)
                # We set avatar_path to None to indicate it's a pasted image
                # but we'll still have the pixmap in avatar_preview
                self.avatar_path = None
                self.avatar_changed = True
                self.on_field_changed()
                print("DEBUG: Set pasted image as avatar")
            else:
                print("DEBUG: Image from clipboard is null")
        else:
            print("DEBUG: No image found in clipboard")
            QMessageBox.warning(self, "Paste Failed", "No image found in clipboard.")
    
    def delete_avatar(self) -> None:
        """Delete the avatar."""
        self.avatar_preview.clear()
        self.avatar_preview.setText("No Avatar")
        self.avatar_path = None
        self.avatar_changed = True
        self.on_field_changed()
    
    def save_avatar(self) -> str:
        """Save the avatar image to the story folder.
        
        Returns:
            Path to the saved avatar image, or empty string if no avatar
        """
        if not self.avatar_changed:
            print("DEBUG: Avatar not changed, returning existing path")
            return self.character_data.get('avatar_path', '')
        
        # If avatar was deleted, return empty string
        if self.avatar_changed and self.avatar_preview.pixmap() is None:
            print("DEBUG: Avatar was deleted, returning empty string")
            return ""
        
        # Get the story folder
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT folder_path FROM stories WHERE id = ?", (self.story_id,))
        story_folder = cursor.fetchone()['folder_path']
        
        # Ensure the avatars folder exists
        avatars_folder = os.path.join(story_folder, "avatars")
        os.makedirs(avatars_folder, exist_ok=True)
        
        # Get absolute paths for debugging
        abs_story_folder = os.path.abspath(story_folder)
        abs_avatars_folder = os.path.abspath(avatars_folder)
        print(f"DEBUG: Story folder absolute path: {abs_story_folder}")
        print(f"DEBUG: Avatars folder absolute path: {abs_avatars_folder}")
        
        # Generate a filename for the avatar
        filename = f"avatar_temp_{int(time.time())}.png" if self.character_id is None else f"avatar_{self.character_id}.png"
        avatar_path = os.path.join(avatars_folder, filename)
        abs_avatar_path = os.path.abspath(avatar_path)
        print(f"DEBUG: Avatar will be saved to: {avatar_path}")
        print(f"DEBUG: Avatar absolute path: {abs_avatar_path}")
        
        # If new avatar was selected from file, copy it
        if self.avatar_path and os.path.exists(self.avatar_path):
            print(f"DEBUG: Copying avatar from {self.avatar_path}")
            pixmap = QPixmap(self.avatar_path)
            saved = pixmap.save(avatar_path, "PNG")
            print(f"DEBUG: Avatar saved successfully: {saved}")
            print(f"DEBUG: Final avatar path stored in DB: {abs_avatar_path}")
            return abs_avatar_path
        
        # If avatar was pasted from clipboard (or set programmatically)
        pixmap = self.avatar_preview.pixmap()
        if pixmap and not pixmap.isNull():
            print("DEBUG: Saving pixmap from avatar_preview")
            saved = pixmap.save(avatar_path, "PNG")
            print(f"DEBUG: Avatar saved successfully: {saved}")
            print(f"DEBUG: Final avatar path stored in DB: {abs_avatar_path}")
            return abs_avatar_path
        
        # If we get here, no valid avatar to save
        print("DEBUG: No valid avatar to save, returning empty string")
        return ""
    
    def save_character(self) -> None:
        """Save the character data."""
        # Get the character data from the form
        character_data = self.get_character_data()
        
        # Generate a default name if none is provided
        if not character_data['name']:
            # Get the count of unnamed characters in this story to generate a unique name
            cursor = self.db_conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) as count FROM characters WHERE story_id = ? AND name LIKE 'Unnamed %'",
                (self.story_id,)
            )
            count = cursor.fetchone()['count']
            
            # Generate a name like "Unnamed 1", "Unnamed 2", etc.
            character_data['name'] = f"Unnamed {count + 1}"
            print(f"DEBUG: Generated default name: {character_data['name']}")
        
        # Print debug info
        print(f"DEBUG: Initial character data: {character_data}")
        
        # Save the avatar if needed and update the avatar path
        if self.avatar_changed:
            saved_avatar_path = self.save_avatar()
            character_data['avatar_path'] = saved_avatar_path
            print(f"DEBUG: Updated avatar path in character data: {saved_avatar_path}")
        
        # Print final character data
        print(f"DEBUG: Final character data to be saved: {character_data}")
        
        # If this is a new character, create it
        if self.character_id is None:
            print(f"DEBUG: Creating new character for story {self.story_id}")
            from app.db_sqlite import create_character
            
            self.character_id = create_character(
                self.db_conn,
                name=character_data['name'],
                story_id=self.story_id,
                aliases=character_data['aliases'],
                is_main_character=character_data['is_main_character'],
                age_value=character_data['age_value'],
                age_category=character_data['age_category'],
                gender=character_data['gender'],
                avatar_path=character_data['avatar_path']
            )
            
            print(f"DEBUG: Created character with ID {self.character_id}")
        else:
            # Update existing character
            print(f"DEBUG: Updating existing character {self.character_id}")
            from app.db_sqlite import update_character
            
            update_character(
                self.db_conn,
                self.character_id,
                name=character_data['name'],
                aliases=character_data['aliases'],
                is_main_character=character_data['is_main_character'],
                age_value=character_data['age_value'],
                age_category=character_data['age_category'],
                gender=character_data['gender'],
                avatar_path=character_data['avatar_path']
            )
            print(f"DEBUG: Character {self.character_id} updated successfully")
        
        # Emit the character_updated signal
        self.character_updated.emit(self.character_id, character_data)
        
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

    def get_character_data(self) -> Dict[str, Any]:
        """Get the character data from the form.
        
        Returns:
            Dictionary of character data
        """
        # Get name (can be empty, will generate a default name later if needed)
        name = self.name_edit.text().strip()
        
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
        
        # Get avatar path - preserve existing path if not changed
        if self.avatar_changed:
            avatar_path = self.avatar_path
        else:
            avatar_path = self.character_data.get('avatar_path', None)
        
        # Return the data
        return {
            'name': name,
            'aliases': aliases,
            'is_main_character': is_main_character,
            'age_value': age_value,
            'age_category': age_category,
            'gender': gender,
            'avatar_path': avatar_path
        } 

    def _scale_pixmap_for_avatar(self, pixmap: QPixmap) -> QPixmap:
        """Scale a pixmap to fit the avatar preview while maintaining aspect ratio.
        
        Args:
            pixmap: The original pixmap
            
        Returns:
            Scaled pixmap
        """
        if pixmap.isNull():
            return pixmap
            
        # Get the size of the avatar preview
        preview_size = self.avatar_preview.size()
        max_width = preview_size.width()
        max_height = preview_size.height()
        
        # If the pixmap is smaller than the preview, no need to scale
        if pixmap.width() <= max_width and pixmap.height() <= max_height:
            return pixmap
            
        # Scale the pixmap to fit the preview while maintaining aspect ratio
        return pixmap.scaled(
            max_width, 
            max_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ) 