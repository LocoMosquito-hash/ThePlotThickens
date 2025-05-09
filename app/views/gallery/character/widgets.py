#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Character-related widgets for The Plot Thickens gallery.

This module contains widgets for character selection, filtering and listing.
"""

from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QMenu, QToolTip
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QAction

class CharacterListWidget(QListWidget):
    """List widget for displaying characters with hover effects."""
    
    def __init__(self, db_conn, parent=None):
        """Initialize the character list widget.
        
        Args:
            db_conn: Database connection
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.hoveredItem = None
        self.setMouseTracking(True)
        
    def mouseMoveEvent(self, event):
        """Handle mouse move events for hover highlighting.
        
        Args:
            event: Mouse event
        """
        # Find the item under the cursor
        item = self.itemAt(event.pos())
        
        # If hovering over a valid item
        if item:
            # Check if the item has character data
            if item.data(Qt.ItemDataRole.UserRole):
                character_data = item.data(Qt.ItemDataRole.UserRole)
                
                # Only update if hovering over a new item
                if self.hoveredItem != item:
                    self.hoveredItem = item
                    
                    # Show character info in tooltip
                    character_name = "Unknown"
                    if hasattr(character_data, '__contains__') and 'name' in character_data:
                        character_name = character_data['name']
                    elif hasattr(character_data, 'get'):
                        character_name = character_data.get('name', "Unknown")
                    
                    QToolTip.showText(
                        self.mapToGlobal(event.pos()), 
                        f"<b>{character_name}</b>"
                    )
            else:
                self.hoveredItem = None
                QToolTip.hideText()
        else:
            self.hoveredItem = None
            QToolTip.hideText()
        
        # Call the parent class method
        super().mouseMoveEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave events to reset hover state.
        
        Args:
            event: Leave event
        """
        self.hoveredItem = None
        QToolTip.hideText()
        super().leaveEvent(event)

class OnSceneCharacterListWidget(CharacterListWidget):
    """List widget for characters that appear in a scene."""
    
    def __init__(self, db_conn, parent=None):
        """Initialize the on-scene character list widget."""
        super().__init__(db_conn, parent)
        # Implementation will be moved here from gallery_widget.py

class GalleryFilterCharacterListWidget(CharacterListWidget):
    """List widget for filtering characters in the gallery."""
    
    def __init__(self, db_conn, parent=None):
        """Initialize the gallery filter character list widget."""
        super().__init__(db_conn, parent)
        # Implementation will be moved here from gallery_widget.py

class FilterCharacterListWidget(CharacterListWidget):
    """List widget for character filtering with context menu options."""
    
    def __init__(self, db_conn, parent=None):
        """Initialize the filter character list widget."""
        super().__init__(db_conn, parent)
        # Implementation will be moved here from gallery_widget.py
