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
    QGraphicsRectItem, QWidget, QDialogButtonBox, QProgressDialog,
    QSizePolicy
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QTimer, QPoint, QSize, QRectF, QPointF, QSizeF, QRect, QSettings
)
from PyQt6.QtGui import (
    QPixmap, QImage, QAction, QKeySequence, QShortcut, QCursor,
    QBrush, QColor, QPen, QPainter
)
from PyQt6.QtWidgets import QApplication

from app.views.gallery.character.widgets import OnSceneCharacterListWidget
from app.views.gallery.character.widgets import RecognitionResultsListWidget
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

# Import the ImageEnhancementWidget
from app.views.gallery.image_enhancement import ImageEnhancementWidget


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
        
        # Settings for persistent window properties
        self.settings = QSettings("ThePlotThickens", "ThePlotThickens")
        
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
        
        # Regions data
        self.regions = []         # List of region dictionaries
        self.region_rects = {}    # Dictionary of region index -> QGraphicsRectItem
        self.selected_region_idx = -1  # Currently selected region index
        
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
        
        # Restore window dimensions and position (moved after UI setup)
        self.restoreWindowGeometry()
    
    def init_ui(self) -> None:
        """Initialize the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create splitter for main layout sections
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter = splitter  # Store as instance variable
        
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
        self.regions_list.currentRowChanged.connect(self.on_region_selected)
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
        self.recognized_list = RecognitionResultsListWidget(self.db_conn, self)
        self.recognized_list.itemClicked.connect(self.on_recognized_character_clicked)
        results_layout.addWidget(self.recognized_list)
        
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
        
        # Set fixed width for the on-scene characters list
        self.onscene_list.setFixedWidth(250)
        self.onscene_list.setMinimumWidth(250)
        self.onscene_list.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        
        onscene_layout.addWidget(self.onscene_list)
        right_column.addWidget(onscene_group)
        
        # Set stretch factors for the columns - Modified to make regions/results narrower and on-scene wider
        # Original was 3:2, now using 24:26 (20% narrower left, 30% wider right)
        lists_layout.setStretch(0, 40)  # Left column (20% narrower than 50/50 split)
        lists_layout.setStretch(1, 60)  # Right column (30% wider than 50/50 split)
        
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
        
        # Tab for image enhancement
        enhance_tab = QWidget()
        enhance_layout = QVBoxLayout(enhance_tab)
        
        # Create the image enhancement widget
        self.enhancement_widget = ImageEnhancementWidget()
        self.enhancement_widget.set_image(self.pixmap)
        self.enhancement_widget.image_changed.connect(self.on_enhancement_image_changed)
        self.enhancement_widget.image_saved.connect(self.on_enhancement_image_saved)
        
        enhance_layout.addWidget(self.enhancement_widget)
        
        # Add the enhancement tab to tabs
        tabs.addTab(enhance_tab, "Enhance Image")
        
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
            # INSERT_YOUR_REWRITE_HERE
            
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
        
        # Add CTRL+Q shortcut for quick event
        quick_event_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        quick_event_shortcut.activated.connect(self.quick_event_shortcut_triggered)
    
    def quick_event_shortcut_triggered(self) -> None:
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
    
    def on_quick_event_created(self, event_id: int, text: str, context: Dict[str, Any]) -> None:
        """Handle the quick event created signal."""
        if not event_id:
            return
            
        # Store the new quick event ID
        self.new_quick_event_id = event_id
        self.associated_quick_event_id = event_id
        
        # Get the image ID from context or from current instance
        image_id = context.get("image_id", None) or self.image_id
        
        print(f"[DEBUG] Using image_id for association: {image_id}")
        
        # Update the quick events list if it exists
        if hasattr(self, 'events_list') and self.events_list:
            # Get quick events data
            self.load_quick_events_data()
            
        # Show a success message
        self._status_bar.showMessage(f"Quick event created: {text[:50]}...")
    
    def auto_recognize_characters(self) -> None:
        """Automatically recognize characters in all regions."""
        # Check if we have regions to process
        if not self.regions:
            QMessageBox.information(
                self,
                "No Regions",
                "No regions have been selected. Please draw regions around the faces you want to recognize."
            )
            return
            
        try:
            # Show a progress dialog for longer operations
            progress_dialog = QProgressDialog(
                "Analyzing regions for character recognition...",
                "Cancel", 0, len(self.regions), self
            )
            progress_dialog.setWindowTitle("Character Recognition")
            progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            progress_dialog.setMinimumDuration(500)  # Show after 500ms delay
            progress_dialog.setValue(0)
            
            # Process each region
            for i, region in enumerate(self.regions):
                # Check if the user canceled
                if progress_dialog.wasCanceled():
                    break
                    
                # Update progress
                progress_dialog.setValue(i)
                progress_dialog.setLabelText(f"Analyzing region {i+1} of {len(self.regions)}...")
                
                # Extract the region from the image
                region_rect = QRect(
                    region["x"], 
                    region["y"], 
                    region["width"], 
                    region["height"]
                )
                region_image = self.image.copy(region_rect)
                
                # Run recognition with the story_id to limit results to this story's characters
                results = self.recognition_util.recognize_faces(region_image, story_id=self.story_id)
                
                # Store the results in the correct format for the region
                region["characters"] = []
                for result in results:
                    region["characters"].append({
                        "id": result["character_id"],
                        "name": result["character_name"],
                        "confidence": result["similarity"]
                    })
                
                # Update progress
                QApplication.processEvents()
                
            # Complete progress
            progress_dialog.setValue(len(self.regions))
            progress_dialog.close()
            
            # Select the first region to show recognition results
            if self.regions and len(self.regions) > 0:
                self.regions_list.setCurrentRow(0)
                
            self._status_bar.showMessage(f"Character recognition completed for {len(self.regions)} regions")
            
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
        """Override accept to save settings before accepting."""
        # Save window geometry
        self.saveWindowGeometry()
        
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
    
    def reject(self):
        """Override reject to save settings before rejecting."""
        # Save window geometry
        self.saveWindowGeometry()
        
        # Call the parent reject method
        super().reject()
    
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
                update_character_last_tagged(self.db_conn, self.story_id, character_id)
    
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
        current_row = self.regions_list.currentRow()
        if current_row >= 0 and current_row < len(self.regions):
            # Remove visual rectangle from scene
            if current_row in self.region_rects:
                rect_item = self.region_rects[current_row]
                self.scene.removeItem(rect_item)
                del self.region_rects[current_row]
            
            # Remove from data
            self.regions.pop(current_row)
            
            # Remove from list widget
            self.regions_list.takeItem(current_row)
            
            # Update the UI to reflect the change
            self._status_bar.showMessage(f"Region {current_row + 1} removed")
            
            # Renumber remaining regions in the UI
            for i in range(current_row, self.regions_list.count()):
                region = self.regions[i]
                item_text = f"Region {i + 1}: {region['width']}x{region['height']}"
                self.regions_list.item(i).setText(item_text)
    
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
        # Remove all visual rectangles from the scene
        for rect_item in self.region_rects.values():
            self.scene.removeItem(rect_item)
        
        # Clear dictionaries and lists
        self.region_rects.clear()
        self.regions.clear()
        self.regions_list.clear()
        
        # Reset selected region
        self.selected_region_idx = -1
        
        # Clear recognition results
        self.recognized_list.clear()
        
        # Update status
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
        self.current_rect = None
        self.start_pos = None
        self.selecting = False
    
    def scene_mouse_press(self, event) -> None:
        """Handle mouse press event for region selection."""
        # Only process right mouse button
        if event.button() == Qt.MouseButton.RightButton:
            self.start_pos = event.scenePos()
            self.selecting = True
            
            # Create temporary selection rectangle
            self.current_rect = self.scene.addRect(
                QRectF(self.start_pos, QSizeF(0, 0)),
                QPen(QColor(0, 255, 0, 200), 2),  # Green pen for drawing
                QBrush(QColor(0, 255, 0, 50))     # Semi-transparent green brush
            )
        
        # Call the original event handler if it exists
        if hasattr(self, 'original_mouse_press') and self.original_mouse_press:
            self.original_mouse_press(event)
    
    def scene_mouse_move(self, event) -> None:
        """Handle mouse move event for region selection."""
        if self.selecting and self.current_rect:
            current_pos = event.scenePos()
            rect = QRectF(
                self.start_pos,
                current_pos
            ).normalized()
            self.current_rect.setRect(rect)
        
        # Call the original event handler if it exists
        if hasattr(self, 'original_mouse_move') and self.original_mouse_move:
            self.original_mouse_move(event)
    
    def scene_mouse_release(self, event) -> None:
        """Handle mouse release event for region selection."""
        # Only process right mouse button
        if event.button() == Qt.MouseButton.RightButton and self.selecting and self.current_rect:
            # Get the final rectangle dimensions
            rect = self.current_rect.rect()
            
            # Only add if the region has a significant size (20x20 pixels minimum)
            if rect.width() > 20 and rect.height() > 20:
                # Create region data
                region_idx = len(self.regions)
                region_data = {
                    "x": int(rect.x()),
                    "y": int(rect.y()),
                    "width": int(rect.width()),
                    "height": int(rect.height()),
                    "characters": []  # Will hold recognition results
                }
                self.regions.append(region_data)
                
                # Keep the current rectangle and store it
                self.region_rects[region_idx] = self.current_rect
                
                # Style it as a non-selected region (green border)
                self.current_rect.setPen(QPen(QColor(0, 255, 0, 200), 2))
                self.current_rect.setBrush(QBrush(QColor(0, 255, 0, 50)))
                
                # Add to UI list
                item_text = f"Region {region_idx + 1}: {int(rect.width())}x{int(rect.height())}"
                self.regions_list.addItem(item_text)
                
                # Update the UI to reflect the change
                self._status_bar.showMessage(f"Region {region_idx + 1} added")
                
                # Reset the current rectangle reference but keep the visual rectangle in the scene
                self.current_rect = None
                
                # Auto-select this region
                self.regions_list.setCurrentRow(region_idx)
                
                # Run character recognition on this region
                self.recognize_characters_in_region(region_idx)
            else:
                # Remove the temporary rectangle if it's too small
                if self.current_rect in self.scene.items():
                    self.scene.removeItem(self.current_rect)
                self.current_rect = None
            
            # Reset selection state
            self.selecting = False
        
        # Call the original event handler if it exists
        if hasattr(self, 'original_mouse_release') and self.original_mouse_release:
            self.original_mouse_release(event)

    def on_region_selected(self, row: int) -> None:
        """Handle region selection from the list.
        
        Args:
            row: Selected row index
        """
        # Validate row
        if row < 0 or row >= len(self.regions):
            return
        
        # Update selected region index
        self.selected_region_idx = row
        
        # Update all region rectangles to show selection state
        for idx, rect_item in self.region_rects.items():
            if idx == row:
                # Highlight selected region with orange border and fill
                rect_item.setPen(QPen(QColor(255, 165, 0, 200), 2))  # Orange
                rect_item.setBrush(QBrush(QColor(255, 165, 0, 50)))  # Semi-transparent orange
            else:
                # Non-selected regions get green border and fill
                rect_item.setPen(QPen(QColor(0, 255, 0, 200), 2))    # Green
                rect_item.setBrush(QBrush(QColor(0, 255, 0, 50)))    # Semi-transparent green
        
        # Run recognition if needed
        self.recognize_characters_in_region(row)
    
    def recognize_characters_in_region(self, region_idx: int) -> None:
        """Run character recognition on a specific region.
        
        Args:
            region_idx: Index of the region to analyze
        """
        # Validate index
        if region_idx < 0 or region_idx >= len(self.regions):
            return
            
        # Get the region data
        region = self.regions[region_idx]
        
        # Check if we've already analyzed this region
        if region.get("characters"):
            self.display_recognition_results(region_idx)
            return
        
        # Extract the region from the image
        region_rect = QRect(
            region["x"], 
            region["y"], 
            region["width"], 
            region["height"]
        )
        region_image = self.image.copy(region_rect)
        
        try:
            # Run recognition
            recognition_results = self.recognition_util.recognize_faces(region_image, story_id=self.story_id)
            
            # Store results
            region["characters"] = []
            
            if recognition_results:
                for result in recognition_results:
                    region["characters"].append({
                        "id": result["character_id"],
                        "name": result["character_name"],
                        "confidence": result["similarity"]
                    })
            
            # Display results
            self.display_recognition_results(region_idx)
        except Exception as e:
            self._status_bar.showMessage(f"Error recognizing characters: {str(e)}")
    
    def display_recognition_results(self, region_idx: int) -> None:
        """Display recognition results for a region.
        
        Args:
            region_idx: Index of the region
        """
        # Clear the recognition results list
        self.recognized_list.clear()
        
        if region_idx < 0 or region_idx >= len(self.regions):
            return
        
        region = self.regions[region_idx]
        recognized_chars = region.get("characters", [])
        
        # Add header item
        header_item = QListWidgetItem(f"Characters found in Region {region_idx + 1}:")
        header_item.setFlags(Qt.ItemFlag.NoItemFlags)  # Make non-selectable
        self.recognized_list.addItem(header_item)
        
        # Sort by confidence (highest first)
        recognized_chars.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        
        # Add recognized characters
        matched_character_ids = set()
        for char in recognized_chars:
            confidence = char.get("confidence", 0)
            if confidence > 0:
                character_id = char.get("id")
                matched_character_ids.add(character_id)
                item_text = f"{char.get('name')} ({int(confidence * 100)}% match)"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, character_id)
                self.recognized_list.addItem(item)
        
        # Add a separator
        separator_item = QListWidgetItem("_______________________________")
        separator_item.setFlags(Qt.ItemFlag.NoItemFlags)  # Make non-selectable
        self.recognized_list.addItem(separator_item)
        
        # Add "Other characters in this story" header
        other_header = QListWidgetItem("Other characters in this story:")
        other_header.setFlags(Qt.ItemFlag.NoItemFlags)  # Make non-selectable
        self.recognized_list.addItem(other_header)
        
        # Add other characters not recognized
        for char in self.characters:
            if char["id"] not in matched_character_ids:
                item_text = f"{char['name']} (0% match)"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, char["id"])
                self.recognized_list.addItem(item)
                
        # Connect to selection change if not already connected
        self.recognized_list.itemClicked.connect(self.on_recognized_character_clicked)
    
    def on_recognized_character_clicked(self, item: QListWidgetItem) -> None:
        """Handle recognition result item click to tag a character.
        
        Args:
            item: Selected list item
        """
        # Check if this is a header or separator
        if not item.flags() & Qt.ItemFlag.ItemIsSelectable:
            return
            
        character_id = item.data(Qt.ItemDataRole.UserRole)
        if not character_id:
            return
            
        # Get character name from item text (parse out the match percentage)
        text = item.text()
        name = text.split(" (")[0] if " (" in text else text
        
        # Get region data
        if self.selected_region_idx < 0 or self.selected_region_idx >= len(self.regions):
            self._status_bar.showMessage("No region selected. Please select a region first.")
            return
            
        region = self.regions[self.selected_region_idx]
        
        # Get confidence from the matching character if available
        confidence = 0
        for char in region.get("characters", []):
            if char.get("id") == character_id:
                confidence = char.get("confidence", 0)
                break
        
        # Create normalized region coordinates for the tag
        img_width = self.image.width()
        img_height = self.image.height()
        
        if img_width == 0 or img_height == 0:
            self._status_bar.showMessage("Invalid image dimensions")
            return
            
        x = region["x"] / img_width
        y = region["y"] / img_height
        width = region["width"] / img_width
        height = region["height"] / img_height
        
        # Add to tagged characters
        tag = {
            'character_id': character_id,
            'character_name': name,
            'region_index': self.selected_region_idx,
            'region': {
                'x': x + (width / 2),  # Center X
                'y': y + (height / 2),  # Center Y
                'width': width,
                'height': height
            },
            'similarity': confidence,
            'description': f"Tagged with {int(confidence * 100)}% confidence"
        }
        
        # Check if we already have this character tagged for this region
        existing_tag_index = -1
        for i, existing_tag in enumerate(self.tagged_characters):
            if (existing_tag.get('character_id') == character_id and 
                existing_tag.get('region_index') == self.selected_region_idx):
                existing_tag_index = i
                break
                
        if existing_tag_index >= 0:
            # Replace the existing tag
            self.tagged_characters[existing_tag_index] = tag
        else:
            # Add as a new tag
            self.tagged_characters.append(tag)
        
        # Update the region list item to show the character
        self.update_region_list_item(self.selected_region_idx, name)
        
        # Update last tagged timestamp for this character
        update_character_last_tagged(self.db_conn, self.story_id, character_id)
        
        # Show confirmation message
        self._status_bar.showMessage(f"Tagged character: {name} for Region {self.selected_region_idx + 1}")
        
        # Add the tagged character to the tagged characters list (if it's not already there)
        self.update_tagged_list()
    
    def update_region_list_item(self, region_idx: int, character_name: Optional[str] = None) -> None:
        """Update the text for a region list item.
        
        Args:
            region_idx: Index of the region
            character_name: Name of the tagged character (optional)
        """
        if region_idx < 0 or region_idx >= len(self.regions):
            return
            
        region = self.regions[region_idx]
        
        # Base text with dimensions
        item_text = f"Region {region_idx + 1}: {region['width']}x{region['height']}"
        
        # Add character name if provided
        if character_name:
            item_text += f" - {character_name}"
            
        # Update the list item
        self.regions_list.item(region_idx).setText(item_text)

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

    def update_tagged_list(self) -> None:
        """Update the tagged characters list display."""
        if not hasattr(self, 'tagged_list'):
            return
            
        # Clear the current list
        self.tagged_list.clear()
        
        # Group tags by character
        character_tags = {}
        for tag in self.tagged_characters:
            character_id = tag.get('character_id')
            character_name = tag.get('character_name', 'Unknown')
            region_index = tag.get('region_index', -1)
            
            if character_id not in character_tags:
                character_tags[character_id] = {
                    'name': character_name,
                    'regions': []
                }
                
            # Only add region if it's a valid region (not -1 for regionless tags)
            if region_index >= 0:
                character_tags[character_id]['regions'].append(region_index)
        
        # Add entries to the list
        for character_id, data in character_tags.items():
            if data['regions']:
                # Character with regions
                region_text = ", ".join([f"Region {r+1}" for r in data['regions']])
                item_text = f"{data['name']} - Found in {region_text}"
            else:
                # Character without specific regions (scene presence only)
                item_text = f"{data['name']} - Present in scene"
                
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, character_id)
            self.tagged_list.addItem(item)
            
        # Update the tab name to show the count
        if hasattr(self, 'tabs'):
            tagged_count = len(character_tags)
            self.tabs.setTabText(1, f"Tagged Characters ({tagged_count})")

    def closeEvent(self, event):
        """Save window state when closing.
        
        Args:
            event: Close event
        """
        # Save window geometry
        self.saveWindowGeometry()
        
        # Continue with normal close event
        super().closeEvent(event)

    def restoreWindowGeometry(self) -> None:
        """Restore window geometry (size and position) from settings."""
        # Default size if no saved settings
        default_size = QSize(1000, 700)
        
        # Get saved size with fallback to default
        saved_size = self.settings.value("recognition_dialog/size", default_size, type=QSize)
        if saved_size.isValid():
            self.resize(saved_size)
        else:
            self.resize(default_size)
        
        # Get saved position - only use if valid
        if self.settings.contains("recognition_dialog/pos"):
            pos = self.settings.value("recognition_dialog/pos")
            # Check if position is on screen (prevent window appearing off-screen)
            available_geometry = QApplication.primaryScreen().availableGeometry()
            if (pos.x() >= 0 and pos.x() < available_geometry.width() and
                pos.y() >= 0 and pos.y() < available_geometry.height()):
                self.move(pos)
        
        # Restore splitter state if available
        if hasattr(self, 'splitter') and self.settings.contains("recognition_dialog/splitter_state"):
            splitter_state = self.settings.value("recognition_dialog/splitter_state")
            self.splitter.restoreState(splitter_state)
    
    def saveWindowGeometry(self) -> None:
        """Save window geometry (size and position) to settings."""
        self.settings.setValue("recognition_dialog/size", self.size())
        self.settings.setValue("recognition_dialog/pos", self.pos())
        
        # Save splitter state
        if hasattr(self, 'splitter'):
            self.settings.setValue("recognition_dialog/splitter_state", self.splitter.saveState())
            
        # Ensure settings are written to disk
        self.settings.sync()

    def on_enhancement_image_changed(self, pixmap: QPixmap) -> None:
        """Handle image changes from the enhancement widget.
        
        Args:
            pixmap: Enhanced pixmap
        """
        if pixmap and not pixmap.isNull():
            # Update the displayed image in the scene
            self.scene.removeItem(self.pixmap_item)
            self.pixmap = pixmap
            self.pixmap_item = QGraphicsPixmapItem(self.pixmap)
            self.scene.addItem(self.pixmap_item)
            
            # Update the image with the enhanced version
            self.image = self.pixmap.toImage()
            
            # Fit the scene in view
            self.fit_scene_in_view()
            
            # Show status message
            self._status_bar.showMessage("Image enhanced")

    def on_enhancement_image_saved(self, file_path: str) -> None:
        """Handle image saved event from the enhancement widget.
        
        Args:
            file_path: Path where the image was saved
        """
        # Update status bar with saved path
        self._status_bar.showMessage(f"Image saved to: {file_path}")
        
        # Update parent gallery if available
        parent_gallery = self.parent()
        if parent_gallery and hasattr(parent_gallery, 'refresh_gallery'):
            try:
                parent_gallery.refresh_gallery()
            except Exception as e:
                self._status_bar.showMessage(f"Could not refresh gallery: {str(e)}")
