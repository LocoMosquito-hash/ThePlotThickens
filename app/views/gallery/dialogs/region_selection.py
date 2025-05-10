#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Region Selection Dialog for The Plot Thickens application.

This module contains the dialog for selecting regions in images for character recognition.
"""

from typing import List, Dict, Any, Optional, Tuple

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QListWidget, QListWidgetItem, QSplitter,
    QStatusBar, QTabWidget, QGroupBox, QCheckBox, QMessageBox,
    QComboBox, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QGraphicsRectItem, QWidget, QDialogButtonBox
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QTimer, QPoint, QSize, QRectF, QPointF, QSizeF
)
from PyQt6.QtGui import (
    QPixmap, QImage, QAction, QKeySequence, QShortcut, QCursor,
    QBrush, QColor, QPen, QPainter
)

from app.views.gallery.character.widgets import OnSceneCharacterListWidget
from app.views.gallery.dialogs.quick_event_dialog import QuickEventEditor
from app.views.gallery.character.completer import CharacterTagCompleter

from app.db_sqlite import (
    get_story_characters, update_character_last_tagged,
    create_quick_event, get_next_quick_event_sequence_number,
    process_quick_event_character_tags, get_image_quick_events,
    get_characters_by_last_tagged, get_story_folder_paths, ensure_story_folders_exist
)

# Import image recognition utility
from app.utils.image_recognition_util import ImageRecognitionUtil


class RegionSelectionDialog(QDialog):
    """Dialog for manually selecting regions to recognize characters in."""
    
    # Static class variable to store the IDs of characters tagged in the last session
    last_tagged_character_ids = []
    
    def __init__(self, db_conn, image: QImage, story_id: int, parent=None, image_id: Optional[int] = None):
        """Initialize the region selection dialog.
        
        Args:
            db_conn: Database connection
            image: Image to process
            story_id: ID of the story
            parent: Parent widget
            image_id: ID of the image (if available)
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.image = image
        self.story_id = story_id
        self.image_id = image_id
        
        # Create a pixmap from the image for display
        self.pixmap = QPixmap.fromImage(self.image)
        
        # For navigation between images
        self.gallery_images = []
        self.current_index = -1
        
        # Initialize the image recognition utility
        self.recognition_util = ImageRecognitionUtil(self.db_conn)
        
        # Selection rectangle state
        self.selection_active = False
        self.selection_start = QPointF(0, 0)
        self.selection_rect = QRectF(0, 0, 0, 0)
        
        # Regions list
        self.regions = []
        
        # Character data
        self.characters = []
        self.on_scene_characters = []
        
        # Tagged characters list - will store characters that have been tagged
        self.tagged_characters = []
        
        # Quick events data
        self.quick_events = []
        self.associated_quick_event_id = None  # ID of the selected quick event
        self.new_quick_event_id = None  # ID of a newly created quick event
        
        # Create graphics scene for image view
        self.scene = QGraphicsScene()
        
        # Set up window
        self.setWindowTitle("Character Recognition - Region Selection")
        self.resize(1000, 700)
        
        # Create status bar
        self._status_bar = QStatusBar(self)
        
        # Set up UI
        self.init_ui()
        
        # Load characters and quick events
        self.load_characters_data()
        self.load_quick_events_data()
        
        # Set up keyboard shortcuts
        self.setup_shortcuts()
        
        # Set up mouse events for region selection
        self.initialize_mouse_events()
    
    def init_ui(self) -> None:
        """Initialize the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create splitter for main layout sections
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Create image view panel
        image_panel = QWidget()
        image_layout = QVBoxLayout(image_panel)
        
        # Create graphics view for displaying the image
        self.graphics_view = QGraphicsView()
        self.graphics_view.setScene(self.scene)
        
        # Enable anti-aliasing for smoother rendering
        self.graphics_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.graphics_view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Add the image to the scene
        self.pixmap_item = QGraphicsPixmapItem(self.pixmap)
        self.scene.addItem(self.pixmap_item)
        
        # Make the graphics view respond to resize events
        self.graphics_view.resizeEvent = self.on_graphics_view_resize
        
        # Add instruction label
        instruction_label = QLabel("Right-click and drag to select face regions")
        instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_layout.addWidget(instruction_label)
        
        # Add graphics view to image layout
        image_layout.addWidget(self.graphics_view)
        
        # Add image panel to splitter
        splitter.addWidget(image_panel)
        
        # Create control panel
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        
        # Setup tabs
        tabs = QTabWidget()
        self.tabs = tabs  # Store as instance variable
        control_layout.addWidget(tabs)
        
        # Tab for region selection (first tab)
        region_tab = QWidget()
        region_layout = QVBoxLayout(region_tab)
        
        # Create horizontal layout for the lists
        lists_layout = QHBoxLayout()
        region_layout.addLayout(lists_layout)
        
        # Left column - Selected Regions and Character Recognition Results
        left_column = QVBoxLayout()
        lists_layout.addLayout(left_column)
        
        # Create selected regions list
        regions_group = QGroupBox("Selected Regions")
        regions_layout = QVBoxLayout(regions_group)
        self.regions_list = QListWidget()
        regions_layout.addWidget(self.regions_list)
        
        # Add region management buttons
        regions_buttons_layout = QHBoxLayout()
        self.remove_region_btn = QPushButton("Remove Region")
        self.remove_region_btn.clicked.connect(self.remove_selected_region)
        regions_buttons_layout.addWidget(self.remove_region_btn)
        
        self.add_to_db_btn = QPushButton("Add to Recognition DB")
        self.add_to_db_btn.clicked.connect(self.add_region_to_recognition_db)
        regions_buttons_layout.addWidget(self.add_to_db_btn)
        
        self.clear_all_btn = QPushButton("Clear All")
        self.clear_all_btn.clicked.connect(self.clear_all_regions)
        regions_buttons_layout.addWidget(self.clear_all_btn)
        
        regions_layout.addLayout(regions_buttons_layout)
        left_column.addWidget(regions_group)
        
        # Create character recognition results section
        results_group = QGroupBox("Character Recognition Results (Click to Tag)")
        results_layout = QVBoxLayout(results_group)
        
        # Create recognized characters list
        self.recognized_list = QListWidget()
        results_layout.addWidget(self.recognized_list)
        
        # Add label for other characters in story
        self.other_chars_label = QLabel("Other characters in this story:")
        results_layout.addWidget(self.other_chars_label)
        
        # Add rebuild recognition database button
        self.rebuild_db_btn = QPushButton("Rebuild Recognition Database")
        self.rebuild_db_btn.clicked.connect(self.rebuild_recognition_database)
        results_layout.addWidget(self.rebuild_db_btn)
        
        left_column.addWidget(results_group)
        
        # Right column - On-scene Characters
        right_column = QVBoxLayout()
        lists_layout.addLayout(right_column)
        
        # Create on-scene characters list on the right side
        onscene_group = QGroupBox("On-scene Characters")
        onscene_layout = QVBoxLayout(onscene_group)
        self.onscene_list = OnSceneCharacterListWidget(self.db_conn, self)
        onscene_layout.addWidget(self.onscene_list)
        right_column.addWidget(onscene_group)
        
        # Set stretch factors for the columns
        lists_layout.setStretch(0, 3)  # Left column gets more width
        lists_layout.setStretch(1, 2)  # Right column gets less width
        
        # Add region tab to tabs (first position)
        tabs.addTab(region_tab, "Region Selection")
        
        # Tab for tagged characters
        tagged_tab = QWidget()
        tagged_layout = QVBoxLayout(tagged_tab)
        
        # Create tagged characters list
        tagged_group = QGroupBox("Tagged Characters")
        tagged_layout_inner = QVBoxLayout(tagged_group)
        self.tagged_list = QListWidget()
        tagged_layout_inner.addWidget(self.tagged_list)
        tagged_layout.addWidget(tagged_group)
        
        # Add tagged tab to tabs
        tabs.addTab(tagged_tab, "Tagged Characters")
        
        # Tab for quick events
        events_tab = QWidget()
        events_layout = QVBoxLayout(events_tab)
        
        # Create quick events UI
        events_group = QGroupBox("Quick Events")
        events_layout_inner = QVBoxLayout(events_group)
        self.events_list = QListWidget()
        events_layout_inner.addWidget(self.events_list)
        
        # Add button to create new quick event
        new_qe_btn = QPushButton("Create New Quick Event")
        new_qe_btn.clicked.connect(self.create_new_quick_event)
        events_layout_inner.addWidget(new_qe_btn)
        
        events_layout.addWidget(events_group)
        
        # Add events tab to tabs
        tabs.addTab(events_tab, "Quick Events")
        
        # Set the first tab (Region Selection) as the default
        tabs.setCurrentIndex(0)
        
        # Add control panel to splitter
        splitter.addWidget(control_panel)
        
        # Set default sizes for the splitter
        splitter.setSizes([700, 300])
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
        
        # Add buttons at the bottom
        buttons_layout = QHBoxLayout()
        
        # Auto-recognize button
        auto_recognize_btn = QPushButton("Auto-Recognize Characters")
        auto_recognize_btn.clicked.connect(self.auto_recognize_characters)
        buttons_layout.addWidget(auto_recognize_btn)
        
        # Add spacer
        buttons_layout.addStretch()
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        # Apply button
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.accept)
        apply_btn.setDefault(True)
        buttons_layout.addWidget(apply_btn)
        
        # Add buttons layout to main layout
        main_layout.addLayout(buttons_layout)
        
        # Add status bar to main layout
        main_layout.addWidget(self._status_bar)
    
    def load_characters_data(self) -> None:
        """Load character data from the database."""
        # Get all characters for this story
        self.characters = get_story_characters(self.db_conn, self.story_id)
        
        # Populate on-scene characters list with most recently tagged characters
        if hasattr(self, 'onscene_list'):
            self.onscene_list.clear()
            
            # Get recently tagged characters - don't use the limit parameter
            recent_characters = get_characters_by_last_tagged(self.db_conn, self.story_id)
            
            # Limit to top 10 manually
            recent_characters = recent_characters[:10] if recent_characters else []
            
            # Add them to the list
            for character in recent_characters:
                item = QListWidgetItem(character['name'])
                item.setData(Qt.ItemDataRole.UserRole, character['id'])
                item.setCheckState(Qt.CheckState.Unchecked)
                self.onscene_list.addItem(item)
                
            # If we have previously tagged characters, pre-check them
            for i in range(self.onscene_list.count()):
                item = self.onscene_list.item(i)
                character_id = item.data(Qt.ItemDataRole.UserRole)
                if character_id in RegionSelectionDialog.last_tagged_character_ids:
                    item.setCheckState(Qt.CheckState.Checked)
    
    def load_quick_events_data(self) -> None:
        """Load quick events data from the database."""
        # Clear existing quick events
        self.events_list.clear()
        
        # Add "No Quick Event" option
        no_event_item = QListWidgetItem("No Quick Event")
        no_event_item.setData(Qt.ItemDataRole.UserRole, -1)
        self.events_list.addItem(no_event_item)
        
        # Get quick events for this image if it exists
        if self.image_id:
            image_quick_events = get_image_quick_events(self.db_conn, self.image_id)
            
            for event in image_quick_events:
                event_item = QListWidgetItem(event['text'])
                event_item.setData(Qt.ItemDataRole.UserRole, event['id'])
                self.events_list.addItem(event_item)
    
    def setup_shortcuts(self) -> None:
        """Set up keyboard shortcuts for the dialog."""
        # Shortcut to cancel
        cancel_shortcut = QShortcut(QKeySequence.StandardKey.Cancel, self)
        cancel_shortcut.activated.connect(self.reject)
    
    def auto_recognize_characters(self) -> None:
        """Automatically recognize characters in the image."""
        try:
            # Show warning that this feature is in development
            QMessageBox.information(
                self,
                "Auto Recognition",
                "Automatic character recognition is currently in development.\n\n"
                "In the future, this feature will analyze faces in the image and "
                "suggest character matches based on your previously tagged characters."
            )
            
            # Show status message
            self._status_bar.showMessage("Character recognition is in development...")
            
            # For now, we'll just demonstrate the UI flow without actual recognition
            # Add a placeholder result to show how it would work
            self.recognized_list.clear()
            
            # Get characters from the database to show as examples
            characters = self.characters[:min(len(self.characters), 3)]
            if characters:
                for character in characters:
                    confidence = 0.75  # Placeholder confidence value
                    
                    # Create item
                    item = QListWidgetItem(f"{character['name']} ({int(confidence * 100)}% match)")
                    item.setData(Qt.ItemDataRole.UserRole, character['id'])
                    item.setCheckState(Qt.CheckState.Unchecked)
                    
                    # Add to list
                    self.recognized_list.addItem(item)
                
                self._status_bar.showMessage(f"Found {len(characters)} potential character matches (demo)")
            else:
                self._status_bar.showMessage("No characters available for recognition")
                
        except Exception as e:
            QMessageBox.warning(
                self,
                "Recognition Error",
                f"An error occurred during character recognition:\n{str(e)}"
            )
            self._status_bar.showMessage("Character recognition failed")
    
    def create_new_quick_event(self) -> None:
        """Create a new quick event and associate it with the image."""
        # Create a quick event editor dialog
        editor = QuickEventEditor(self.db_conn, self.story_id, self)
        
        if editor.exec() == QDialog.DialogCode.Accepted:
            # Get the text and create a new quick event
            quick_event_text = editor.get_quick_event_text()
            
            if quick_event_text:
                # Get the next sequence number
                sequence_number = get_next_quick_event_sequence_number(self.db_conn, self.story_id)
                
                # Create the quick event
                quick_event_id = create_quick_event(
                    self.db_conn,
                    self.story_id,
                    quick_event_text,
                    sequence_number
                )
                
                if quick_event_id:
                    # Process character tags
                    process_quick_event_character_tags(self.db_conn, quick_event_id, quick_event_text)
                    
                    # Add to events list
                    event_item = QListWidgetItem(quick_event_text)
                    event_item.setData(Qt.ItemDataRole.UserRole, quick_event_id)
                    self.events_list.addItem(event_item)
                    
                    # Select the new quick event
                    items = self.events_list.findItems(quick_event_text, Qt.MatchFlag.MatchExactly)
                    if items:
                        self.events_list.setCurrentItem(items[0])
                    
                    # Store the ID of the new quick event
                    self.new_quick_event_id = quick_event_id
                    self.associated_quick_event_id = quick_event_id
    
    # Basic methods should go here
    def statusBar(self):
        """Get the status bar."""
        return self._status_bar
        
    # Add the get_selected_character_data method
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
        """Override accept to save the selected quick event association and process checked characters."""
        # Get the selected quick event ID if a quick event is selected
        if hasattr(self, 'events_list') and self.events_list.currentItem():
            current_item = self.events_list.currentItem()
            if current_item:
                self.associated_quick_event_id = current_item.data(Qt.ItemDataRole.UserRole)
        
        # Process the checked characters before accepting
        if hasattr(self, 'onscene_list'):
            self.tag_checked_onscene_characters()
        
        # Store the character IDs that were tagged in this session for future use
        RegionSelectionDialog.last_tagged_character_ids = [tag['character_id'] for tag in self.tagged_characters]
        
        # Call the parent accept method
        super().accept()
        
    def tag_checked_onscene_characters(self) -> None:
        """Tag all checked characters in the on-scene list as being present without regions."""
        if not hasattr(self, 'onscene_list'):
            return
            
        # Loop through all items in the on-scene list
        for i in range(self.onscene_list.count()):
            item = self.onscene_list.item(i)
            
            # Only process checked items
            if item.checkState() == Qt.CheckState.Checked:
                character_id = item.data(Qt.ItemDataRole.UserRole)
                character_name = item.text()
                
                # Create a "regionless" tag for this character
                self.create_regionless_tag(character_id, character_name)
                
                # Update the last tagged timestamp for this character
                update_character_last_tagged(self.db_conn, character_id)
    
    def create_regionless_tag(self, character_id: int, character_name: str) -> None:
        """Create a tag without a specific region for an on-scene character.
        
        Args:
            character_id: ID of the character
            character_name: Name of the character
        """
        # Create a tag entry with default values
        tag = {
            'character_id': character_id,
            'character_name': character_name,
            'region_index': -1,  # -1 indicates no specific region
            'region': {
                'x': 0.5,  # Center of image
                'y': 0.5,  # Center of image
                'width': 0.0,  # No width
                'height': 0.0,  # No height
            },
            'similarity': 1.0,  # 100% confidence since it's manually tagged
            'description': "Character is present in scene (no specific region)"
        }
        
        # Add to the tagged characters list
        self.tagged_characters.append(tag)

    # Add these new methods for region management
    def remove_selected_region(self) -> None:
        """Remove the selected region from the list."""
        current_item = self.regions_list.currentItem()
        if current_item:
            row = self.regions_list.row(current_item)
            self.regions_list.takeItem(row)
            
            # Remove the region from our data and from the scene
            if row < len(self.regions):
                # Remove from data
                self.regions.pop(row)
                
                # Update the UI to reflect the change
                self._status_bar.showMessage(f"Region {row + 1} removed")
    
    def add_region_to_recognition_db(self) -> None:
        """Add the selected region to the character recognition database."""
        current_item = self.regions_list.currentItem()
        if current_item:
            row = self.regions_list.row(current_item)
            if row < len(self.regions):
                # Show a message explaining this feature is not fully implemented
                QMessageBox.information(
                    self,
                    "Add to Recognition DB",
                    "This feature will add the selected region to the character recognition database.\n"
                    "You'll need to select a character to associate with this region."
                )
    
    def clear_all_regions(self) -> None:
        """Clear all regions from the list."""
        self.regions_list.clear()
        self.regions.clear()
        
        # Clear any region rectangles from the scene
        # (You'll need to implement the actual graphics rect management)
        
        self._status_bar.showMessage("All regions cleared")
    
    def rebuild_recognition_database(self) -> None:
        """Rebuild the character recognition database."""
        # Show a message explaining this feature
        QMessageBox.information(
            self,
            "Rebuild Recognition Database",
            "This will rebuild the character recognition database using all tagged faces.\n"
            "This operation may take some time to complete."
        )
        
        # In a real implementation, you would call the appropriate method
        # from the ImageRecognitionUtil class to rebuild the database

    # Method to add a region to the list
    def add_region(self, x: int, y: int, width: int, height: int) -> None:
        """Add a region to the regions list.
        
        Args:
            x: The x coordinate of the region
            y: The y coordinate of the region
            width: The width of the region
            height: The height of the region
        """
        # Store the region data
        region_idx = len(self.regions)
        region_data = {"x": x, "y": y, "width": width, "height": height}
        self.regions.append(region_data)
        
        # Add to UI list
        item_text = f"Region {region_idx + 1}: {width}x{height}"
        self.regions_list.addItem(item_text)
        
        # Update the UI to reflect the change
        self._status_bar.showMessage(f"Region {region_idx + 1} added")
    
    def initialize_mouse_events(self) -> None:
        """Initialize mouse events for region selection."""
        # Store original event handlers
        self.original_mouse_press = self.scene.mousePressEvent
        self.original_mouse_move = self.scene.mouseMoveEvent
        self.original_mouse_release = self.scene.mouseReleaseEvent
        
        # Set our custom event handlers
        self.scene.mousePressEvent = self.scene_mouse_press
        self.scene.mouseMoveEvent = self.scene_mouse_move
        self.scene.mouseReleaseEvent = self.scene_mouse_release
        
        # Initialize variables for region selection
        self.selection_rect = None
        self.start_pos = None
        self.selecting = False
    
    def scene_mouse_press(self, event) -> None:
        """Handle mouse press event for region selection."""
        # Only process right mouse button
        if event.button() == Qt.MouseButton.RightButton:
            self.start_pos = event.scenePos()
            self.selecting = True
            self.selection_rect = self.scene.addRect(
                QRectF(self.start_pos, QSizeF(0, 0)),
                QPen(QColor(255, 165, 0), 2),  # Orange pen
                QBrush(QColor(255, 255, 0, 70))  # Semi-transparent yellow
            )
        
        # Call the original event handler if it exists
        if hasattr(self, 'original_mouse_press') and self.original_mouse_press:
            self.original_mouse_press(event)
    
    def scene_mouse_move(self, event) -> None:
        """Handle mouse move event for region selection."""
        if self.selecting and self.selection_rect:
            current_pos = event.scenePos()
            rect = QRectF(
                self.start_pos,
                current_pos
            ).normalized()
            self.selection_rect.setRect(rect)
        
        # Call the original event handler if it exists
        if hasattr(self, 'original_mouse_move') and self.original_mouse_move:
            self.original_mouse_move(event)
    
    def scene_mouse_release(self, event) -> None:
        """Handle mouse release event for region selection."""
        # Only process right mouse button
        if event.button() == Qt.MouseButton.RightButton and self.selecting and self.selection_rect:
            # Get the final rectangle dimensions
            rect = self.selection_rect.rect()
            
            # Only add if the region has a significant size
            if rect.width() > 10 and rect.height() > 10:
                self.add_region(
                    int(rect.x()), int(rect.y()),
                    int(rect.width()), int(rect.height())
                )
            
            # Remove the selection rectangle from the scene
            if self.selection_rect in self.scene.items():
                self.scene.removeItem(self.selection_rect)
            
            # Reset selection state
            self.selecting = False
            self.selection_rect = None
        
        # Call the original event handler if it exists
        if hasattr(self, 'original_mouse_release') and self.original_mouse_release:
            self.original_mouse_release(event)

    def on_graphics_view_resize(self, event) -> None:
        """Handle resize event for the graphics view."""
        # Call the original resize event handler
        QGraphicsView.resizeEvent(self.graphics_view, event)
        
        # Fit the scene in the view
        self.fit_scene_in_view()
    
    def fit_scene_in_view(self) -> None:
        """Fit the scene in the view while maintaining aspect ratio."""
        if hasattr(self, 'graphics_view') and hasattr(self, 'pixmap_item'):
            self.graphics_view.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
    
    def showEvent(self, event) -> None:
        """Handle show event for the dialog."""
        super().showEvent(event)
        
        # Fit the scene in the view
        QTimer.singleShot(100, self.fit_scene_in_view)
        
        # Select the Region Selection tab
        if hasattr(self, 'tabs'):
            self.tabs.setCurrentIndex(0)
        
        # Set status message
        self._status_bar.showMessage("Ready. Right-click and drag to select face regions.")

    # Add utility functions for story path handling
    def get_story_folder_paths(self) -> Dict[str, str]:
        """Get the folder paths for the current story.
        
        Returns:
            Dictionary with folder paths
        """
        return get_story_folder_paths(self.db_conn.cursor().execute("SELECT * FROM stories WHERE id = ?", (self.story_id,)).fetchone())
    
    def ensure_story_folders_exist(self) -> None:
        """Ensure all story folders exist."""
        ensure_story_folders_exist(self.db_conn.cursor().execute("SELECT * FROM stories WHERE id = ?", (self.story_id,)).fetchone())
