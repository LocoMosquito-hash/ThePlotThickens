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
    QStatusBar, QTabWidget, QGroupBox, QCheckBox, QMessageBox
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
    process_quick_event_character_tags
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
        
        # Quick events data
        self.quick_events = []
        
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
    
    # Basic methods should go here
    def statusBar(self):
        """Get the status bar."""
        return self._status_bar
