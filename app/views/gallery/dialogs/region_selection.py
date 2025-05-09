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
    QGraphicsRectItem, QWidget
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QTimer, QPoint, QSize, QRectF, QPointF
)
from PyQt6.QtGui import (
    QPixmap, QImage, QAction, QKeySequence, QShortcut, QCursor,
    QBrush, QColor, QPen
)

from app.views.gallery.character.widgets import OnSceneCharacterListWidget
from app.views.gallery.dialogs.quick_event_dialog import QuickEventEditor
from app.views.gallery.character.completer import CharacterTagCompleter

from app.db_sqlite import (
    get_story_characters, update_character_last_tagged,
    create_quick_event, get_next_quick_event_sequence_number,
    process_quick_event_character_tags, get_image_quick_events,
    get_characters_by_last_tagged
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
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        
        # Add the image to the scene
        self.pixmap_item = QGraphicsPixmapItem(self.pixmap)
        self.graphics_scene.addItem(self.pixmap_item)
        
        # Fit the scene in the view
        self.graphics_view.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
        
        # Add graphics view to image layout
        image_layout.addWidget(self.graphics_view)
        
        # Add image panel to splitter
        splitter.addWidget(image_panel)
        
        # Create control panel
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        
        # Create tabs for different functionalities
        tabs = QTabWidget()
        
        # Tab for character tagging
        character_tab = QWidget()
        character_layout = QVBoxLayout(character_tab)
        
        # Create on-scene characters list
        onscene_group = QGroupBox("On-Scene Characters")
        onscene_layout = QVBoxLayout(onscene_group)
        self.onscene_list = OnSceneCharacterListWidget(self.db_conn, self)
        onscene_layout.addWidget(self.onscene_list)
        character_layout.addWidget(onscene_group)
        
        # Create recognized characters list
        recognized_group = QGroupBox("Recognized Characters")
        recognized_layout = QVBoxLayout(recognized_group)
        self.recognized_list = QListWidget()
        recognized_layout.addWidget(self.recognized_list)
        character_layout.addWidget(recognized_group)
        
        # Add character tab to tabs
        tabs.addTab(character_tab, "Characters")
        
        # Tab for quick events
        quick_event_tab = QWidget()
        quick_event_layout = QVBoxLayout(quick_event_tab)
        
        # Quick event selection
        qe_group = QGroupBox("Quick Event")
        qe_layout = QVBoxLayout(qe_group)
        self.quick_events_combo = QComboBox()
        qe_layout.addWidget(self.quick_events_combo)
        
        # Add button to create new quick event
        new_qe_btn = QPushButton("Create New Quick Event")
        new_qe_btn.clicked.connect(self.create_new_quick_event)
        qe_layout.addWidget(new_qe_btn)
        
        quick_event_layout.addWidget(qe_group)
        
        # Add quick event tab to tabs
        tabs.addTab(quick_event_tab, "Quick Events")
        
        # Add tabs to control layout
        control_layout.addWidget(tabs)
        
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
        self.quick_events_combo.clear()
        
        # Add "No Quick Event" option
        self.quick_events_combo.addItem("No Quick Event", -1)
        
        # Get quick events for this image if it exists
        if self.image_id:
            image_quick_events = get_image_quick_events(self.db_conn, self.image_id)
            
            for event in image_quick_events:
                self.quick_events_combo.addItem(event['text'], event['id'])
    
    def setup_shortcuts(self) -> None:
        """Set up keyboard shortcuts for the dialog."""
        # Shortcut to cancel
        cancel_shortcut = QShortcut(QKeySequence.StandardKey.Cancel, self)
        cancel_shortcut.activated.connect(self.reject)
    
    def auto_recognize_characters(self) -> None:
        """Automatically recognize characters in the image."""
        if not self.recognition_util.has_faces():
            QMessageBox.information(
                self,
                "No Recognition Data",
                "No character recognition data available. Add character tags to build the database first."
            )
            return
        
        # Show status message
        self._status_bar.showMessage("Recognizing characters...")
        
        # Run recognition
        results = self.recognition_util.recognize_faces(self.image)
        
        # Clear existing recognized characters
        self.recognized_list.clear()
        
        if not results:
            self._status_bar.showMessage("No characters recognized")
            return
        
        # Add recognized characters to the list
        for result in results:
            character_id = result["id"]
            name = result["name"]
            confidence = result["confidence"]
            region = result["region"]  # x, y, width, height as relative coordinates (0.0-1.0)
            
            # Create item
            item = QListWidgetItem(f"{name} ({confidence:.0%})")
            item.setData(Qt.ItemDataRole.UserRole, character_id)
            item.setCheckState(Qt.CheckState.Checked)
            
            # Add to list
            self.recognized_list.addItem(item)
            
            # Add to tagged characters
            self.tagged_characters.append({
                'character_id': character_id,
                'character_name': name,
                'region': region,
                'similarity': confidence,
                'description': f"Auto-detected with {int(confidence * 100)}% confidence"
            })
        
        self._status_bar.showMessage(f"Recognized {len(results)} characters")
    
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
                    
                    # Add to combo box
                    self.quick_events_combo.addItem(quick_event_text, quick_event_id)
                    
                    # Select the new quick event
                    index = self.quick_events_combo.findData(quick_event_id)
                    if index >= 0:
                        self.quick_events_combo.setCurrentIndex(index)
                    
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
        if hasattr(self, 'quick_events_combo') and self.quick_events_combo.currentData() != -1:
            self.associated_quick_event_id = self.quick_events_combo.currentData()
        
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
