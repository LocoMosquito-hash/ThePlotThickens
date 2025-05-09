#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Image Detail Dialog for The Plot Thickens application.

This module contains the dialog for viewing image details and managing character tags.
"""

from typing import List, Dict, Any, Optional, Tuple

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QListWidget, QListWidgetItem, QMenu, QSplitter,
    QStatusBar, QToolTip, QDialogButtonBox, QTabWidget, QGroupBox,
    QMessageBox
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QTimer, QPoint, QSize
)
from PyQt6.QtGui import (
    QPixmap, QAction, QKeySequence, QShortcut, QCursor
)

from app.views.gallery.tagging import TaggableImageLabel, GraphicsTagView
from app.views.gallery.dialogs.quick_event_dialog import QuickEventSelectionDialog, QuickEventEditor
from app.views.gallery.character.completer import CharacterTagCompleter

from app.db_sqlite import (
    get_image_character_tags, add_character_tag_to_image, remove_character_tag,
    get_image_quick_events, associate_quick_event_with_image, remove_quick_event_image_association,
    get_story_characters, get_character, get_quick_event_tagged_characters,
    update_character_last_tagged
)


class ImageDetailDialog(QDialog):
    """Dialog for viewing image details and managing character tags."""
    
    def __init__(self, db_conn, image_id: int, image_data: Dict[str, Any], pixmap: QPixmap, parent=None, 
                 gallery_images: List[int] = None, current_index: int = None):
        """Initialize the image detail dialog.
        
        Args:
            db_conn: Database connection
            image_id: ID of the image
            image_data: Image data from the database
            pixmap: Image pixmap
            parent: Parent widget
            gallery_images: List of all image IDs in the gallery (for navigation)
            current_index: Current index in the gallery_images list
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.image_id = image_id
        self.image_data = image_data
        self.original_pixmap = pixmap
        self.story_id = image_data.get("story_id")
        self.tag_mode_enabled = False
        
        # For navigation between images
        self.gallery_images = gallery_images or []
        self.current_index = current_index if current_index is not None else -1
        
        # If we've got a full list of images, find the current index
        if self.gallery_images and self.current_index == -1:
            try:
                self.current_index = self.gallery_images.index(self.image_id)
            except ValueError:
                self.current_index = -1
        
        # Set up window
        self.setWindowTitle(f"Image Details - {image_data.get('title', 'Untitled')}")
        self.resize(900, 600)
        
        # Create status bar
        self._status_bar = QStatusBar(self)
        
        # Set up UI
        self.init_ui()
        
        # Load image data
        self.load_character_tags()
        self.load_quick_events()
        
        # Set up keyboard shortcuts
        self.setup_shortcuts()
    
    def statusBar(self):
        """Get the status bar.
        
        Returns:
            Status bar widget
        """
        return self._status_bar
    
    def setup_shortcuts(self):
        """Set up keyboard shortcuts."""
        # Navigation shortcuts
        if self.can_navigate_previous():
            prev_shortcut = QShortcut(QKeySequence("Left"), self)
            prev_shortcut.activated.connect(self.navigate_to_previous)
        
        if self.can_navigate_next():
            next_shortcut = QShortcut(QKeySequence("Right"), self)
            next_shortcut.activated.connect(self.navigate_to_next)
        
        # Quick event shortcut (Ctrl+Q)
        quick_event_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        quick_event_shortcut.activated.connect(self.quick_event_shortcut_triggered)
    
    def keyPressEvent(self, event):
        """Handle key press events.
        
        Args:
            event: Key event
        """
        super().keyPressEvent(event)
    
    def can_navigate_previous(self) -> bool:
        """Check if navigation to the previous image is possible."""
        return self.gallery_images and self.current_index > 0
    
    def can_navigate_next(self) -> bool:
        """Check if navigation to the next image is possible."""
        return self.gallery_images and self.current_index < len(self.gallery_images) - 1
    
    def navigate_to_previous(self):
        """Navigate to the previous image in the gallery."""
        if self.can_navigate_previous():
            self.current_index -= 1
            self.load_image_at_current_index()
        else:
            self.statusBar().showMessage("No previous image")
    
    def navigate_to_next(self):
        """Navigate to the next image in the gallery."""
        if self.can_navigate_next():
            self.current_index += 1
            self.load_image_at_current_index()
        else:
            self.statusBar().showMessage("No next image")
    
    def load_image_at_current_index(self):
        """Load the image at the current index."""
        if not self.gallery_images or self.current_index < 0 or self.current_index >= len(self.gallery_images):
            return
        
        # Get the image ID at the current index
        image_id = self.gallery_images[self.current_index]
        
        # Get the parent gallery widget
        gallery_widget = self.parent()
        if not gallery_widget:
            self.statusBar().showMessage("Cannot navigate: No parent gallery widget")
            return
        
        # Ask the gallery widget to get the image data and pixmap
        image_data = gallery_widget.get_image_data(image_id)
        if not image_data:
            self.statusBar().showMessage(f"Cannot navigate: Image data not found for ID {image_id}")
            return
        
        pixmap = gallery_widget.get_image_pixmap(image_id)
        if pixmap.isNull():
            self.statusBar().showMessage(f"Cannot navigate: Image pixmap not found for ID {image_id}")
            return
        
        # Update this dialog with the new image
        self.image_id = image_id
        self.image_data = image_data
        self.original_pixmap = pixmap
        
        # Update the window title
        self.setWindowTitle(f"Image Details - {image_data.get('title', 'Untitled')}")
        
        # Update the image display
        self.image_label.set_image(pixmap, image_data.get("width"), image_data.get("height"))
        
        # Update character tags and quick events
        self.load_character_tags()
        self.load_quick_events()
        
        # Update tag mode
        self.toggle_tag_mode(self.tag_mode_enabled)
        
        # Update status bar
        self.statusBar().showMessage(f"Navigated to image {self.current_index + 1} of {len(self.gallery_images)}")
    
    def quick_event_shortcut_triggered(self):
        """Handle quick event shortcut (Ctrl+Q)."""
        # Get selected character from the tag list
        selected_items = self.character_tags_list.selectedItems()
        if not selected_items:
            # If no character is selected, just open the quick event dialog
            self.create_quick_event()
            return
        
        # Get the selected character
        selected_item = selected_items[0]
        character_data = selected_item.data(Qt.ItemDataRole.UserRole)
        
        if not character_data:
            self.create_quick_event()
            return
        
        # Create a context dictionary for the quick event
        context = {
            "origin": "character_tag",
            "character_id": character_data.get("character_id"),
            "character_name": character_data.get("character_name")
        }
        
        # Open the quick event editor
        quick_event_editor = QuickEventEditor(self.db_conn, self.story_id, self.image_id, self)
        
        # Pre-select the character
        character_id = character_data.get("character_id")
        for i in range(quick_event_editor.character_combo.count()):
            if quick_event_editor.character_combo.itemData(i) == character_id:
                quick_event_editor.character_combo.setCurrentIndex(i)
                break
        
        # Add a character tag to the text
        character_name = character_data.get("character_name")
        if character_name:
            quick_event_editor.text_edit.insertPlainText(f"@{character_name} ")
        
        # Show the dialog
        if quick_event_editor.exec() == QDialog.DialogCode.Accepted:
            # Get the text
            text = quick_event_editor.get_text()
            
            # Get the character ID (if selected)
            selected_character_id = quick_event_editor.get_character_id()
            
            # Create a new quick event
            sequence_number = get_next_quick_event_sequence_number(self.db_conn, self.story_id)
            event_id = create_quick_event(
                self.db_conn, 
                self.story_id, 
                text, 
                sequence_number, 
                selected_character_id
            )
            
            # Associate with the image
            associate_quick_event_with_image(self.db_conn, event_id, self.image_id)
            
            # Process character tags in the quick event text
            self.on_quick_event_created(event_id, text, context)
            
            # Reload quick events
            self.load_quick_events()
    
    def on_quick_event_created(self, event_id: int, text: str, context: Dict[str, Any]) -> None:
        """Handle quick event creation.
        
        Args:
            event_id: ID of the created quick event
            text: Text of the quick event
            context: Context information about the quick event
        """
        from app.db_sqlite import process_quick_event_character_tags
        
        # Process character tags in the text
        process_quick_event_character_tags(self.db_conn, event_id, text)
        
        # Update the UI
        self.statusBar().showMessage("Quick event created")
        
        # If the event was created from a character tag, update the character's last tagged timestamp
        if context.get("origin") == "character_tag":
            character_id = context.get("character_id")
            if character_id:
                update_character_last_tagged(self.db_conn, character_id)
    
    def init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        
        # Create a splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        
        # Left panel: Image display
        image_panel = QVBoxLayout()
        image_widget = QWidget()
        image_widget.setLayout(image_panel)
        
        # Image display label
        image_scroll_area = QScrollArea()
        image_scroll_area.setWidgetResizable(True)
        image_scroll_area.setMinimumWidth(500)
        
        # Use TaggableImageLabel for character tagging
        self.image_label = GraphicsTagView()  # Use GraphicsTagView for better tag display
        self.image_label.set_image(self.original_pixmap, 
                                  self.image_data.get("width"), 
                                  self.image_data.get("height"))
        self.image_label.tag_added.connect(self.add_character_tag)
        self.image_label.tag_selected.connect(self.on_tag_selected)
        
        image_scroll_area.setWidget(self.image_label)
        image_panel.addWidget(image_scroll_area)
        
        # Tag mode controls
        tag_controls = QHBoxLayout()
        
        self.tag_mode_btn = QPushButton("Enable Tag Mode")
        self.tag_mode_btn.setCheckable(True)
        self.tag_mode_btn.toggled.connect(self.toggle_tag_mode)
        tag_controls.addWidget(self.tag_mode_btn)
        
        self.save_crops_btn = QPushButton("Save All Tag Crops")
        self.save_crops_btn.clicked.connect(self.save_all_tag_crops)
        tag_controls.addWidget(self.save_crops_btn)
        
        # Navigation buttons (if we have gallery images)
        if self.gallery_images:
            nav_controls = QHBoxLayout()
            
            if self.can_navigate_previous():
                prev_btn = QPushButton("← Previous")
                prev_btn.clicked.connect(self.navigate_to_previous)
                nav_controls.addWidget(prev_btn)
            
            if self.can_navigate_next():
                next_btn = QPushButton("Next →")
                next_btn.clicked.connect(self.navigate_to_next)
                nav_controls.addWidget(next_btn)
            
            image_panel.addLayout(nav_controls)
        
        image_panel.addLayout(tag_controls)
        
        # Image info (optional)
        if self.image_data.get("timestamp"):
            timestamp_label = QLabel(f"Timestamp: {self.image_data.get('timestamp')}")
            image_panel.addWidget(timestamp_label)
        
        # Add the image panel to the splitter
        splitter.addWidget(image_widget)
        
        # Right panel: Tabs for character tags and quick events
        right_panel = QTabWidget()
        right_panel.setMinimumWidth(300)
        
        # Character Tags tab
        character_tab = QWidget()
        character_layout = QVBoxLayout(character_tab)
        
        # Character tags list
        character_tags_group = QGroupBox("Character Tags")
        character_tags_layout = QVBoxLayout(character_tags_group)
        
        self.character_tags_list = QListWidget()
        self.character_tags_list.itemClicked.connect(self.on_tag_list_item_clicked)
        character_tags_layout.addWidget(self.character_tags_list)
        
        # Character tag controls
        character_tag_controls = QHBoxLayout()
        
        remove_tag_btn = QPushButton("Remove Tag")
        remove_tag_btn.clicked.connect(self.remove_selected_tag)
        character_tag_controls.addWidget(remove_tag_btn)
        
        character_tags_layout.addLayout(character_tag_controls)
        
        character_layout.addWidget(character_tags_group)
        
        # Character completer (for character tagging)
        self.character_completer = CharacterTagCompleter(self)
        self.character_completer.hide()
        
        right_panel.addTab(character_tab, "Character Tags")
        
        # Quick Events tab
        quick_events_tab = QWidget()
        quick_events_layout = QVBoxLayout(quick_events_tab)
        
        # Quick events list
        quick_events_group = QGroupBox("Quick Events")
        quick_events_group_layout = QVBoxLayout(quick_events_group)
        
        self.quick_events_list = QListWidget()
        self.quick_events_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.quick_events_list.customContextMenuRequested.connect(self.show_quick_event_context_menu)
        quick_events_group_layout.addWidget(self.quick_events_list)
        
        # Quick event controls
        quick_event_controls = QHBoxLayout()
        
        add_quick_event_btn = QPushButton("Add Quick Event")
        add_quick_event_btn.clicked.connect(self.associate_quick_events)
        quick_event_controls.addWidget(add_quick_event_btn)
        
        create_quick_event_btn = QPushButton("Create New")
        create_quick_event_btn.clicked.connect(self.create_quick_event)
        quick_event_controls.addWidget(create_quick_event_btn)
        
        quick_events_group_layout.addLayout(quick_event_controls)
        
        quick_events_layout.addWidget(quick_events_group)
        
        right_panel.addTab(quick_events_tab, "Quick Events")
        
        # Add the right panel to the splitter
        splitter.addWidget(right_panel)
        
        # Add the splitter to the main layout
        main_layout.addWidget(splitter)
        
        # Add status bar
        main_layout.addWidget(self._status_bar)
        
        # Set the splitter sizes to give more space to the image panel
        splitter.setSizes([600, 300])
    
    def toggle_tag_mode(self, enabled):
        """Toggle tag mode for adding character tags.
        
        Args:
            enabled: Whether tag mode should be enabled
        """
        self.tag_mode_enabled = enabled
        
        if enabled:
            self.tag_mode_btn.setText("Disable Tag Mode")
            self.statusBar().showMessage("Tag Mode Enabled - Click on the image to add character tags")
        else:
            self.tag_mode_btn.setText("Enable Tag Mode")
            self.statusBar().showMessage("Tag Mode Disabled")
        
        # Tell the image label about the tag mode
        self.image_label.enable_tag_mode(enabled)
        
        # If we're enabling tag mode, make sure the character tags tab is shown
        if enabled:
            tab_widget = self.findChild(QTabWidget)
            if tab_widget:
                tab_widget.setCurrentIndex(0)  # Character Tags tab
    
    def load_character_tags(self):
        """Load character tags for the image."""
        # Get tags from database
        tags = get_image_character_tags(self.db_conn, self.image_id)
        
        # Set tags in the image label
        self.image_label.set_tags(tags)
        
        # Update the character tags list
        self.update_character_tags_list()
    
    def save_all_tag_crops(self):
        """Save all character tag crops to the database."""
        # First, load all tags
        tags = get_image_character_tags(self.db_conn, self.image_id)
        for tag in tags:
            self.image_label.save_tag_crop(tag["id"], tag["character_name"])
        
        self.statusBar().showMessage("All tag crops saved to database")
    
    def update_character_tags_list(self):
        """Update the character tags list widget."""
        self.character_tags_list.clear()
        
        # Get tags from database
        tags = get_image_character_tags(self.db_conn, self.image_id)
        
        for tag in tags:
            # Create a list item
            item = QListWidgetItem(tag["character_name"])
            item.setData(Qt.ItemDataRole.UserRole, tag)
            
            self.character_tags_list.addItem(item)
    
    def add_character_tag(self, x_position, y_position):
        """Add a character tag at the specified position.
        
        Args:
            x_position: X position in relative coordinates (0.0-1.0)
            y_position: Y position in relative coordinates (0.0-1.0)
        """
        # Get characters from database
        characters = get_story_characters(self.db_conn, self.story_id)
        
        # Get recently tagged characters first
        from app.db_sqlite import get_characters_by_last_tagged
        recent_characters = get_characters_by_last_tagged(self.db_conn, self.story_id, limit=5)
        
        # Add "On-Scene" characters to the context menu
        parent_gallery = self.parent()
        if parent_gallery:
            on_scene_characters = parent_gallery.get_on_scene_characters()
            # Combine with recent characters, ensuring no duplicates
            recent_ids = {char["id"] for char in recent_characters}
            for char in on_scene_characters:
                if char["id"] not in recent_ids:
                    recent_characters.append(char)
                    recent_ids.add(char["id"])
        
        # Create a context menu
        menu = QMenu(self)
        
        # Add a title
        title_action = QAction("Select Character:", self)
        title_action.setEnabled(False)
        menu.addAction(title_action)
        menu.addSeparator()
        
        # Add recently tagged characters
        if recent_characters:
            for character in recent_characters:
                action = QAction(f"{character['name']} (Recent)", self)
                action.setData(character)
                menu.addAction(action)
            menu.addSeparator()
        
        # Add all characters
        for character in characters:
            action = QAction(character["name"], self)
            action.setData(character)
            menu.addAction(action)
        
        # Show the menu
        selected = menu.exec(QCursor.pos())
        
        if selected and selected.data():
            character = selected.data()
            
            # Add tag to database
            tag_id = add_character_tag_to_image(
                self.db_conn, 
                self.image_id, 
                character["id"], 
                x_position, 
                y_position
            )
            
            if tag_id:
                # Update the character's last tagged timestamp
                update_character_last_tagged(self.db_conn, character["id"])
                
                # Reload character tags
                self.load_character_tags()
                
                # Update status bar
                self.statusBar().showMessage(f"Tagged {character['name']}")
    
    def on_tag_selected(self, tag_id):
        """Handle tag selection from the image.
        
        Args:
            tag_id: ID of the selected tag
        """
        # Find the tag in the list
        for i in range(self.character_tags_list.count()):
            item = self.character_tags_list.item(i)
            tag_data = item.data(Qt.ItemDataRole.UserRole)
            
            if tag_data and tag_data["id"] == tag_id:
                # Select the item in the list
                self.character_tags_list.setCurrentItem(item)
                break
    
    def on_tag_list_item_clicked(self, item):
        """Handle tag selection from the character tags list.
        
        Args:
            item: Selected list item
        """
        tag_data = item.data(Qt.ItemDataRole.UserRole)
        
        if tag_data:
            # Highlight the tag on the image
            self.image_label.highlight_tag(tag_data["id"])
            
            # Update status bar
            self.statusBar().showMessage(f"Selected tag: {tag_data['character_name']}")
    
    def remove_selected_tag(self):
        """Remove the selected character tag."""
        selected_items = self.character_tags_list.selectedItems()
        
        if not selected_items:
            self.statusBar().showMessage("No tag selected")
            return
        
        # Get the selected tag
        selected_item = selected_items[0]
        tag_data = selected_item.data(Qt.ItemDataRole.UserRole)
        
        if not tag_data:
            self.statusBar().showMessage("Invalid tag data")
            return
        
        # Show confirmation dialog
        confirmation = QMessageBox.question(
            self,
            "Remove Tag",
            f"Are you sure you want to remove the tag for {tag_data['character_name']}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirmation == QMessageBox.StandardButton.Yes:
            # Remove the tag from the database
            success = remove_character_tag(self.db_conn, tag_data["id"])
            
            if success:
                # Reload character tags
                self.load_character_tags()
                
                # Update status bar
                self.statusBar().showMessage(f"Removed tag for {tag_data['character_name']}")
            else:
                self.statusBar().showMessage("Failed to remove tag")
    
    def load_quick_events(self):
        """Load quick events for the image."""
        # Get quick events from database
        quick_events = get_image_quick_events(self.db_conn, self.image_id)
        
        # Update the quick events list
        self.update_quick_events_list()
    
    def update_quick_events_list(self):
        """Update the quick events list widget."""
        self.quick_events_list.clear()
        
        # Get quick events from database
        quick_events = get_image_quick_events(self.db_conn, self.image_id)
        
        for event in quick_events:
            # Get tagged characters
            tagged_characters = get_quick_event_tagged_characters(self.db_conn, event["id"])
            
            # Format the display text
            from app.utils.character_references import convert_char_refs_to_mentions
            display_text = convert_char_refs_to_mentions(event["text"], tagged_characters)
            
            # Create a list item
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, event)
            
            self.quick_events_list.addItem(item)
    
    def associate_quick_events(self):
        """Open the quick event selection dialog to associate events with the image."""
        # Get current quick events
        current_events = get_image_quick_events(self.db_conn, self.image_id)
        current_event_ids = [event["id"] for event in current_events]
        
        # Create and show the dialog
        dialog = QuickEventSelectionDialog(
            self.db_conn,
            self.story_id,
            self.image_id,
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
                    remove_quick_event_image_association(self.db_conn, event_id, self.image_id)
            
            # Then add new associations
            for event_id in selected_ids:
                if event_id not in current_event_ids:
                    associate_quick_event_with_image(self.db_conn, event_id, self.image_id)
            
            # Reload quick events
            self.load_quick_events()
            
            # Update status bar
            self.statusBar().showMessage("Updated quick events")
    
    def show_quick_event_context_menu(self, position: QPoint):
        """Show context menu for quick events list.
        
        Args:
            position: Position where to show the menu
        """
        item = self.quick_events_list.itemAt(position)
        
        if not item:
            return
        
        # Get the quick event data
        event_data = item.data(Qt.ItemDataRole.UserRole)
        
        if not event_data:
            return
        
        # Create the menu
        menu = QMenu(self)
        
        remove_action = QAction("Remove Association", self)
        remove_action.triggered.connect(lambda: self.remove_quick_event_association(event_data["id"]))
        menu.addAction(remove_action)
        
        # Show the menu
        menu.exec(self.quick_events_list.mapToGlobal(position))
    
    def remove_quick_event_association(self, quick_event_id: int):
        """Remove the association between a quick event and this image.
        
        Args:
            quick_event_id: ID of the quick event to disassociate
        """
        # Remove the association from the database
        success = remove_quick_event_image_association(self.db_conn, quick_event_id, self.image_id)
        
        if success:
            # Reload quick events
            self.load_quick_events()
            
            # Update status bar
            self.statusBar().showMessage("Removed quick event association")
        else:
            self.statusBar().showMessage("Failed to remove quick event association")
    
    def create_quick_event(self):
        """Open the quick event editor to create a new quick event."""
        # Create the quick event editor
        editor = QuickEventEditor(self.db_conn, self.story_id, self.image_id, self)
        
        # Show the dialog
        if editor.exec() == QDialog.DialogCode.Accepted:
            # Get the text
            text = editor.get_text()
            
            # Get the character ID (if selected)
            character_id = editor.get_character_id()
            
            # Create a context dictionary
            context = {
                "origin": "image_dialog",
                "character_id": character_id
            }
            
            # Create a new quick event
            sequence_number = get_next_quick_event_sequence_number(self.db_conn, self.story_id)
            event_id = create_quick_event(
                self.db_conn, 
                self.story_id, 
                text, 
                sequence_number, 
                character_id
            )
            
            # Associate with the image
            associate_quick_event_with_image(self.db_conn, event_id, self.image_id)
            
            # Process character tags
            self.on_quick_event_created(event_id, text, context)
            
            # Reload quick events
            self.load_quick_events()
