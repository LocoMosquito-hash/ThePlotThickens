#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tag position dialog for The Plot Thickens gallery.

Provides an interface for manually positioning character tags.
"""

from typing import Tuple, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QScrollArea, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QGraphicsEllipseItem, QGraphicsRectItem, QFrame
)
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPixmap, QImage, QColor, QPen, QBrush, QWheelEvent

class TagPositionDialog(QDialog):
    """Dialog for manually positioning a character tag."""
    
    def __init__(self, image: QImage, character_name: str, 
                 default_size: Tuple[float, float] = (0.1, 0.1), parent=None):
        """Initialize the dialog.
        
        Args:
            image: The image to tag
            character_name: Name of the character to tag
            default_size: Default tag size as percentage of image (width, height)
            parent: Parent widget
        """
        super().__init__(parent)
        self.image = image
        self.character_name = character_name
        self.default_size = default_size
        
        # Tag position and size (normalized coordinates 0-1)
        self.tag_x = 0.5
        self.tag_y = 0.5
        self.tag_width = default_size[0]
        self.tag_height = default_size[1]
        
        # Setup dialog
        self.setWindowTitle(f"Position Tag: {character_name}")
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(
            f"Position the tag for <b>{self.character_name}</b> by dragging it.<br>"
            "Scroll to resize the tag."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Create graphics view for the image and tag
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(Qt.RenderHint.SmoothPixmapTransform)
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.wheelEvent = self.wheel_event  # Override wheel event
        
        # Add image to scene
        pixmap = QPixmap.fromImage(self.image)
        self.pixmap_item = self.scene.addPixmap(pixmap)
        self.image_width = pixmap.width()
        self.image_height = pixmap.height()
        
        # Add tag marker to scene
        tag_size_x = self.tag_width * self.image_width
        tag_size_y = self.tag_height * self.image_height
        tag_x = self.tag_x * self.image_width - tag_size_x / 2
        tag_y = self.tag_y * self.image_height - tag_size_y / 2
        
        # Create tag rectangle
        self.tag_rect = QGraphicsRectItem(tag_x, tag_y, tag_size_x, tag_size_y)
        self.tag_rect.setPen(QPen(QColor(255, 0, 0), 2))
        self.tag_rect.setBrush(QBrush(QColor(255, 0, 0, 50)))
        self.tag_rect.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable)
        self.scene.addItem(self.tag_rect)
        
        # Add character label
        self.label_item = self.scene.addText(self.character_name)
        self.label_item.setDefaultTextColor(Qt.GlobalColor.white)
        self.label_item.setPos(tag_x, tag_y - 20)
        
        # Fit scene in view
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        layout.addWidget(self.view)
        
        # Buttons
        button_layout = QHBoxLayout()
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        ok_button.setDefault(True)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.resize(800, 600)
    
    def resizeEvent(self, event):
        """Handle dialog resize events.
        
        Args:
            event: Resize event
        """
        super().resizeEvent(event)
        # Maintain aspect ratio of image when resizing dialog
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
    
    def wheel_event(self, event: QWheelEvent):
        """Handle mouse wheel events for tag resizing.
        
        Args:
            event: Wheel event
        """
        # Get the current rect
        rect = self.tag_rect.rect()
        
        # Calculate scaling factor based on wheel delta
        delta = event.angleDelta().y()
        factor = 1.1 if delta > 0 else 0.9
        
        # Resize but maintain aspect ratio
        new_width = max(20, min(self.image_width * 0.5, rect.width() * factor))
        new_height = max(20, min(self.image_height * 0.5, rect.height() * factor))
        
        # Calculate center point
        center_x = rect.x() + rect.width() / 2
        center_y = rect.y() + rect.height() / 2
        
        # Create new rect centered on the same point
        new_rect = QRectF(
            center_x - new_width / 2,
            center_y - new_height / 2,
            new_width,
            new_height
        )
        
        # Apply new rect
        self.tag_rect.setRect(new_rect)
        
        # Update label position
        self.label_item.setPos(new_rect.x(), new_rect.y() - 20)
        
        # Accept event
        event.accept()
    
    def get_tag_position_and_size(self) -> Tuple[float, float, float, float]:
        """Get the normalized tag position and size.
        
        Returns:
            Tuple of (x, y, width, height) in normalized coordinates (0-1)
        """
        rect = self.tag_rect.rect()
        
        # Calculate center point
        center_x = rect.x() + rect.width() / 2
        center_y = rect.y() + rect.height() / 2
        
        # Convert to normalized coordinates
        norm_x = center_x / self.image_width
        norm_y = center_y / self.image_height
        norm_width = rect.width() / self.image_width
        norm_height = rect.height() / self.image_height
        
        return (norm_x, norm_y, norm_width, norm_height)
