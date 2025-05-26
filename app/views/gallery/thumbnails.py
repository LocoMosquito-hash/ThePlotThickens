#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Thumbnail widgets for The Plot Thickens application's gallery.

This module contains widgets for displaying thumbnails in the gallery.
"""

from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSizePolicy, QCheckBox, QMenu
)
from PyQt6.QtCore import (
    Qt, QSize, pyqtSignal, QPoint
)
from PyQt6.QtGui import (
    QPixmap, QFont, QPainter, QColor, QBrush, QPen, QCursor, QAction
)

class ThumbnailWidget(QFrame):
    """Widget for displaying a thumbnail image with basic controls."""
    
    clicked = pyqtSignal(int)  # Signal emitted when thumbnail is clicked
    delete_requested = pyqtSignal(int)  # Signal emitted when delete button is clicked
    checkbox_toggled = pyqtSignal(int, bool)  # Signal emitted when checkbox is toggled (image_id, checked)
    
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
        # Remove custom styling to allow ThumbnailWidget to inherit from PyQtDarkTheme
        
        # Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        
        # Top controls layout
        top_controls = QHBoxLayout()
        
        # Checkbox for selection
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(False)  # Explicitly set to unchecked
        self.checkbox.setToolTip("Select for batch operations")
        # Remove custom styling to allow checkbox to inherit from PyQtDarkTheme
        self.checkbox.stateChanged.connect(self._on_checkbox_toggled)
        top_controls.addWidget(self.checkbox)
        
        # Add spacer to push delete button to the right
        top_controls.addStretch(1)
        
        # Delete button
        self.delete_btn = QPushButton("×")
        self.delete_btn.setFlat(True)
        self.delete_btn.setFixedSize(23, 23)  # Increased from 20x20
        # Use simplified styling that works with both dark and light themes
        self.delete_btn.setStyleSheet("""
            QPushButton { 
                border-radius: 11px; 
                font-weight: bold; 
                font-size: 16px;
            }
        """)
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        top_controls.addWidget(self.delete_btn)
        
        self.layout.addLayout(top_controls)
        
        # Image label
        self.image_label = QLabel()
        self.image_label.setMinimumSize(150, 130)  # Increased from 130x110
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(False)
        self.update_displayed_pixmap()
        self.layout.addWidget(self.image_label)
        
        # Quick event label (optional, shown only if set)
        self.quick_event_label = QLabel()
        self.quick_event_label.setWordWrap(True)
        self.quick_event_label.setStyleSheet("font-size: 9px;")  # Remove explicit color to inherit from theme
        self.quick_event_label.setMaximumHeight(60)
        self.quick_event_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.layout.addWidget(self.quick_event_label)
        self.quick_event_label.hide()
        
        # Make the thumbnail clickable for image viewing (except for checkbox area)
        self.setMouseTracking(True)
        
        # Set a context menu policy
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def mousePressEvent(self, event) -> None:
        """Handle mouse press events."""
        # Don't trigger thumbnail click if clicking on the checkbox (let the checkbox handle it)
        checkbox_rect = self.checkbox.geometry()
        
        # If clicking outside the checkbox area
        if not checkbox_rect.contains(event.pos()):
            # Check if CTRL is pressed
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.button() == Qt.MouseButton.LeftButton:
                # If CTRL+click, toggle the checkbox
                current_state = self.checkbox.checkState()
                new_state = Qt.CheckState.Unchecked if current_state == Qt.CheckState.Checked else Qt.CheckState.Checked
                self.checkbox.setCheckState(new_state)
            else:
                # Normal behavior - pass to parent and emit clicked signal for left-click
                super().mousePressEvent(event)
                if event.button() == Qt.MouseButton.LeftButton:
                    self.clicked.emit(self.image_id)

    def _on_checkbox_toggled(self, state: int) -> None:
        """Handle checkbox toggle."""
        # Qt.CheckState.Checked is 2
        is_checked = (state == 2)  # Use direct integer comparison for reliability
        print(f"Checkbox on thumbnail {self.image_id} toggled to {is_checked} (state value: {state})")
        self.checkbox_toggled.emit(self.image_id, is_checked)
    
    def update_displayed_pixmap(self):
        """Update the displayed pixmap in the image label."""
        # Scale to fit within the image label (150x130)
        scaled_pixmap = self.original_pixmap.scaled(
            150, 130,  # Increased from 130x110
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)

    def _on_delete_clicked(self) -> None:
        """Handle delete button click."""
        self.delete_requested.emit(self.image_id)

    def update_pixmap(self, new_pixmap: QPixmap):
        """Update the thumbnail's pixmap.
        
        Args:
            new_pixmap: New pixmap to display
        """
        self.original_pixmap = new_pixmap
        self.update_displayed_pixmap()
    
    def show_context_menu(self, position):
        """Show context menu when right-clicking on the thumbnail.
        
        Args:
            position: Position where the context menu should appear
        """
        # Get the parent GalleryWidget
        parent = self.parent()
        while parent and not hasattr(parent, 'on_thumbnail_context_menu'):
            parent = parent.parent()
            
        # If we found the GalleryWidget parent, delegate to its context menu handler
        if parent and hasattr(parent, 'on_thumbnail_context_menu'):
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
        
        # Visual styling with more robust CSS
        self.setFrameShape(QFrame.Shape.Box)
        self.setLineWidth(2)
        self.setStyleSheet("""
            SeparatorWidget {
                border-top: 2px solid #666;
                border-bottom: 2px solid #666;
                background-color: #333;
                margin-top: 10px;
                margin-bottom: 5px;
                min-height: 40px;
                max-height: 50px;
            }
        """)
        
        # Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 8, 10, 8)
        
        # Title label with better styling
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("""
            color: white; 
            font-size: 14px; 
            font-weight: bold;
            min-height: 24px;
        """)
        self.layout.addWidget(self.title_label)
        
        # Set size policy - Expanding horizontally, Fixed vertically
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Use fixed height settings to prevent compression
        self.setMinimumHeight(40)
        self.setMaximumHeight(50)
        self.setFixedHeight(45)  # Ensure consistent height 