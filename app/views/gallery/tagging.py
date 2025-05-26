#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tagging widgets for The Plot Thickens application's gallery.

This module contains widgets for tagging characters in images.
"""

from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QLabel, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QGraphicsRectItem, QGraphicsTextItem
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QPointF, QRect, QRectF
)
from PyQt6.QtGui import (
    QPixmap, QFont, QPainter, QColor, QBrush, QPen
)

class TaggableImageLabel(QLabel):
    """A custom image label that allows for character tagging."""
    
    tag_added = pyqtSignal(float, float)  # x, y position in relative coordinates (0.0-1.0)
    tag_selected = pyqtSignal(int)  # tag_id
    
    def __init__(self, parent=None):
        """Initialize the taggable image label."""
        super().__init__(parent)
        self.tags = []
        self.tag_mode = False
        self.selected_tag_id = None
        self.hover_tag_id = None
        
        # Store dimensions for coordinate conversions
        self.image_width = 0
        self.image_height = 0
        self.orig_width = 0  # Original image width
        self.orig_height = 0  # Original image height
        self.offset_x = 0
        self.offset_y = 0
        
        # Set larger minimum size
        self.setMinimumSize(200, 150)
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        
    def set_image(self, pixmap, orig_width=None, orig_height=None):
        """Set the image for the label.
        
        Args:
            pixmap: QPixmap to display
            orig_width: Original image width (if scaled)
            orig_height: Original image height (if scaled)
        """
        self.setPixmap(pixmap)
        self.image_width = pixmap.width()
        self.image_height = pixmap.height()
        
        # Store original dimensions if provided, otherwise use displayed dimensions
        self.orig_width = orig_width if orig_width is not None else self.image_width
        self.orig_height = orig_height if orig_height is not None else self.image_height
        
        # Log dimensions for debugging
        print(f"TaggableImageLabel set_image: display={self.image_width}x{self.image_height}, " +
              f"original={self.orig_width}x{self.orig_height}")
        
        # Calculate offsets for centered image
        self.update_offsets()
    
    def update_offsets(self):
        """Update offset calculations for a centered image."""
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
        if self.tag_mode and self.pixmap():
            if event.button() == Qt.MouseButton.LeftButton:
                # Get raw click coordinates
                click_x = event.position().x()
                click_y = event.position().y()
                
                # Convert to relative coordinates within the image
                rel_x, rel_y = self._to_relative_coords(click_x, click_y)
                
                # Debug info to track exact coordinates at every step
                print(f"MOUSE CLICK: raw=({click_x}, {click_y}), rel=({rel_x:.4f}, {rel_y:.4f})")
                
                if 0 <= rel_x <= 1 and 0 <= rel_y <= 1:
                    # Emit signal with relative coordinates
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
        # Simple direct calculation
        # Get current pixmap size
        displayed_width = self.pixmap().width() if self.pixmap() else self.image_width
        displayed_height = self.pixmap().height() if self.pixmap() else self.image_height
        
        # Adjust for image offset within label
        adjusted_x = x - self.offset_x
        adjusted_y = y - self.offset_y
        
        # Direct conversion with bounds checking
        rel_x = max(0.0, min(1.0, adjusted_x / displayed_width if displayed_width > 0 else 0.0))
        rel_y = max(0.0, min(1.0, adjusted_y / displayed_height if displayed_height > 0 else 0.0))
        
        # Debug info with exact values
        print(f"_to_relative_coords: raw=({x}, {y}), " +
              f"adjusted=({adjusted_x}, {adjusted_y}), " +
              f"relative=({rel_x:.4f}, {rel_y:.4f})")
        
        return rel_x, rel_y
        
    def _to_absolute_coords(self, rel_x, rel_y):
        """Convert relative coordinates to absolute coordinates.
        
        Args:
            rel_x: Relative x coordinate (0.0-1.0)
            rel_y: Relative y coordinate (0.0-1.0)
            
        Returns:
            Tuple of (absolute_x, absolute_y)
        """
        # Get current pixmap size
        displayed_width = self.pixmap().width() if self.pixmap() else self.image_width
        displayed_height = self.pixmap().height() if self.pixmap() else self.image_height
        
        # CRITICAL: Direct coordinate calculation
        # Calculate absolute position based on the relative position multiplied by the dimensions
        # Add the offset to position correctly within the label
        abs_x = self.offset_x + (rel_x * displayed_width)
        abs_y = self.offset_y + (rel_y * displayed_height)
        
        print(f"_to_absolute_coords FIXED: ({rel_x:.3f}, {rel_y:.3f}) -> ({abs_x:.1f}, {abs_y:.1f})")
        
        return abs_x, abs_y
        
    def _get_tag_at_position(self, x, y):
        """Get the tag at the given position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Tag ID or None if no tag found
        """
        if not self.tags or not self.pixmap():
            return None
            
        rel_x, rel_y = self._to_relative_coords(x, y)
        
        # Debug information
        print(f"Click at ({x}, {y}) -> relative ({rel_x:.2f}, {rel_y:.2f})")
        
        for tag in self.tags:
            # Tag coordinates are center points
            center_x = tag['x_position']
            center_y = tag['y_position']
            half_width = tag['width'] / 2.0  # Use floating point division
            half_height = tag['height'] / 2.0  # Use floating point division
            
            # Check if point is within rectangle defined by center and half-dimensions
            if (center_x - half_width <= rel_x <= center_x + half_width and
                center_y - half_height <= rel_y <= center_y + half_height):
                print(f"Hit tag: {tag['id']} center=({center_x:.2f}, {center_y:.2f}), " +
                      f"bounds=({center_x-half_width:.2f}, {center_y-half_height:.2f}, " +
                      f"{center_x+half_width:.2f}, {center_y+half_height:.2f})")
                return tag['id']
        
        return None
        
    def paintEvent(self, event):
        """Override paint event to draw tags.
        
        Args:
            event: Paint event
        """
        # Draw the image first
        super().paintEvent(event)
        
        if not self.tags or not self.pixmap():
            return
            
        painter = QPainter(self)
        
        # Get current display dimensions
        displayed_width = self.pixmap().width()
        displayed_height = self.pixmap().height()
        
        # Text height for character names
        text_height = 20
        
        # Debug info
        print(f"Painting tags - Image dimensions: {self.image_width}x{self.image_height}")
        print(f"Display dimensions: {displayed_width}x{displayed_height}")
        print(f"Label dimensions: {self.width()}x{self.height()}")
        print(f"Offsets: {self.offset_x}x{self.offset_y}")
        
        for tag in self.tags:
            tag_id = tag['id']
            # These are center coordinates (0-1 range) relative to the original image
            center_x = tag['x_position']
            center_y = tag['y_position']
            tag_width_ratio = tag['width']      # Width as proportion of original image width
            tag_height_ratio = tag['height']    # Height as proportion of original image height
            character_name = tag.get('character_name', 'Unknown')
            
            # FIXED COORDINATE MAPPING: Simple direct calculation
            # Position the rectangle centered exactly at the specified coordinates
            abs_center_x = self.offset_x + (center_x * displayed_width)
            abs_center_y = self.offset_y + (center_y * displayed_height)
            
            # Calculate display dimensions of the tag
            display_width = tag_width_ratio * displayed_width
            display_height = tag_height_ratio * displayed_height
            
            # Calculate top-left corner for drawing the rectangle
            rect_x = int(abs_center_x - (display_width / 2))
            rect_y = int(abs_center_y - (display_height / 2))
            
            # Debug info
            print(f"Tag {tag_id}: DB coords=({center_x:.4f}, {center_y:.4f}), " + 
                  f"Calculated center=({abs_center_x:.1f}, {abs_center_y:.1f}), " +
                  f"Rectangle top-left=({rect_x}, {rect_y})")
            
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
                
            # FIRST: Draw the rectangle at the exact calculated position (only if it has dimensions)
            if tag_width_ratio > 0.0 and tag_height_ratio > 0.0:
                painter.setPen(pen)
                painter.drawRect(rect_x, rect_y, int(display_width), int(display_height))
            
            # SECOND: Draw text as a completely separate element above the rectangle
            # Only draw character name overlay if tag has visible dimensions (not an invisible on-scene tag)
            if tag_width_ratio > 0.0 and tag_height_ratio > 0.0:
                # Calculate text position independently from the rectangle
                text_x = rect_x
                text_y = max(0, rect_y - text_height - 2)  # Ensure text y position is never negative
                
                # Draw text background
                painter.setPen(QPen(Qt.PenStyle.NoPen))  # FIXED: Create a QPen object with NoPen style
                text_rect = QRect(text_x, text_y, int(display_width), text_height)
                painter.fillRect(text_rect, QColor(0, 0, 0, 180))
                
                # Draw text
                painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, character_name)
    
    def resizeEvent(self, event):
        """Handle resize events to recalculate offsets.
        
        Args:
            event: Resize event
        """
        super().resizeEvent(event)
        if hasattr(self, 'image_width'):  # Only recalculate if we have an image
            self.update_offsets()

class GraphicsTagView(QGraphicsView):
    """A graphics view for displaying images with character tags."""
    
    tag_added = pyqtSignal(float, float)  # x, y position in relative coordinates (0.0-1.0)
    tag_selected = pyqtSignal(int)  # tag_id
    
    def __init__(self, parent=None):
        """Initialize the graphics tag view."""
        super().__init__(parent)
        
        # Create scene
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Image item
        self.pixmap_item = None
        
        # Tags
        self.tags = []
        self.tag_items = {}  # Map of tag_id -> (rect_item, text_item)
        self.selected_tag_id = None
        self.tag_mode = False
        
        # Store dimensions
        self.image_width = 0
        self.image_height = 0
        self.orig_width = 0
        self.orig_height = 0
        
        # Set rendering hints
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Set drag mode
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        
        # Enable mouse tracking
        self.setMouseTracking(True)
        
        # Set minimum size
        self.setMinimumSize(400, 300)
        
    def set_image(self, pixmap: QPixmap, orig_width=None, orig_height=None):
        """Set the image for the view.
        
        Args:
            pixmap: QPixmap to display
            orig_width: Original image width (if scaled)
            orig_height: Original image height (if scaled)
        """
        # Clear scene
        self.scene.clear()
        self.tag_items.clear()
        
        # Add pixmap item
        self.pixmap_item = self.scene.addPixmap(pixmap)
        
        # Store dimensions
        self.image_width = pixmap.width()
        self.image_height = pixmap.height()
        self.orig_width = orig_width if orig_width is not None else self.image_width
        self.orig_height = orig_height if orig_height is not None else self.image_height
        
        # Set scene rect
        self.scene.setSceneRect(0, 0, self.image_width, self.image_height)
        
        # Reset view
        self.resetTransform()
        self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        
        # Redraw tags if any
        if self.tags:
            self.set_tags(self.tags)
    
    def set_tags(self, tags):
        """Set the character tags to display.
        
        Args:
            tags: List of tag dictionaries
        """
        self.tags = tags
        
        # Clear existing tag items
        for tag_id, items in self.tag_items.items():
            rect_item, text_item, text_bg = items
            # Only remove items that exist (not None for invisible tags)
            if rect_item is not None:
                self.scene.removeItem(rect_item)
            if text_item is not None:
                self.scene.removeItem(text_item)
            if text_bg is not None:
                self.scene.removeItem(text_bg)
        self.tag_items.clear()
        
        # Create tag items
        for tag in tags:
            tag_id = tag['id']
            center_x = tag['x_position']
            center_y = tag['y_position']
            tag_width = tag['width']
            tag_height = tag['height']
            character_name = tag.get('character_name', 'Unknown')
            
            # Convert relative coordinates to absolute
            abs_x = center_x * self.image_width
            abs_y = center_y * self.image_height
            abs_width = tag_width * self.image_width
            abs_height = tag_height * self.image_height
            
            # Only create visible rectangle and text items if tag has dimensions (not an invisible on-scene tag)
            if tag_width > 0.0 and tag_height > 0.0:
                # Create rectangle item
                rect_x = abs_x - (abs_width / 2)
                rect_y = abs_y - (abs_height / 2)
                rect_item = QGraphicsRectItem(rect_x, rect_y, abs_width, abs_height)
                rect_item.setPen(QPen(QColor(0, 255, 0), 2))
                rect_item.setData(0, tag_id)  # Store tag ID in item data
                self.scene.addItem(rect_item)
                
                # Create text item
                text_item = QGraphicsTextItem(character_name)
                text_item.setDefaultTextColor(QColor(255, 255, 255))
                text_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                text_item.setPos(rect_x, rect_y - 25)  # Position above the rectangle
                
                # Add background rect to text
                # This is a simple approach - ideally we'd create a custom item that draws both
                text_bg = QGraphicsRectItem(text_item.boundingRect())
                text_bg.setBrush(QBrush(QColor(0, 0, 0, 180)))
                text_bg.setPen(QPen(Qt.PenStyle.NoPen))
                text_bg.setZValue(text_item.zValue() - 1)  # Place behind text
                text_bg.setPos(text_item.pos())
                self.scene.addItem(text_bg)
                
                self.scene.addItem(text_item)
                
                # Store items
                self.tag_items[tag_id] = (rect_item, text_item, text_bg)
            else:
                # For invisible on-scene tags, create empty placeholders to maintain the structure
                # This ensures the tag_items dictionary has entries for all tags
                self.tag_items[tag_id] = (None, None, None)
    
    def enable_tag_mode(self, enabled=True):
        """Enable or disable tag adding mode.
        
        Args:
            enabled: Whether to enable tag mode
        """
        self.tag_mode = enabled
        if enabled:
            self.setCursor(Qt.CursorShape.CrossCursor)
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
    
    def mousePressEvent(self, event):
        """Handle mouse press events.
        
        Args:
            event: Mouse event
        """
        if self.tag_mode and self.pixmap_item:
            if event.button() == Qt.MouseButton.LeftButton:
                # Get scene position
                scene_pos = self.mapToScene(event.pos())
                
                # Convert to relative coordinates
                rel_x = scene_pos.x() / self.image_width
                rel_y = scene_pos.y() / self.image_height
                
                # Check if within image bounds
                if 0 <= rel_x <= 1 and 0 <= rel_y <= 1:
                    # Emit signal with relative coordinates
                    self.tag_added.emit(rel_x, rel_y)
            else:
                # Pass to super for handling
                super().mousePressEvent(event)
        else:
            if event.button() == Qt.MouseButton.LeftButton:
                # Get scene position
                scene_pos = self.mapToScene(event.pos())
                
                # Check if clicked on a tag
                items = self.scene.items(scene_pos)
                for item in items:
                    if isinstance(item, QGraphicsRectItem) and item.data(0):
                        tag_id = item.data(0)
                        self.selected_tag_id = tag_id
                        self.highlight_tag(tag_id)
                        self.tag_selected.emit(tag_id)
                        return
            
            # Pass to super for handling
            super().mousePressEvent(event)
    
    def highlight_tag(self, tag_id):
        """Highlight a tag.
        
        Args:
            tag_id: ID of the tag to highlight
        """
        # Reset all tags to normal style
        for tid, (rect_item, text_item, text_bg) in self.tag_items.items():
            # Only highlight visible tags (not None for invisible on-scene tags)
            if rect_item is not None:
                if tid == tag_id:
                    # Highlight this tag
                    rect_item.setPen(QPen(QColor(255, 165, 0), 3))  # Orange for selected
                else:
                    # Normal style
                    rect_item.setPen(QPen(QColor(0, 255, 0), 2))  # Green for normal
        
        # Store selected tag ID
        self.selected_tag_id = tag_id
    
    def save_tag_crop(self, tag_id, tag_name):
        """Save a cropped image for a tag.
        
        This is a stub method that would crop the image at the tag position
        and save it to the recognition database.
        
        Args:
            tag_id: ID of the tag
            tag_name: Name of the character
        """
        # Stub implementation
        print(f"Would save crop for tag {tag_id} ({tag_name})")
        
        # In a real implementation, this would:
        # 1. Find the tag rect
        # 2. Crop the image at that rect
        # 3. Save to recognition database
    
    def resizeEvent(self, event):
        """Handle resize events.
        
        Args:
            event: Resize event
        """
        super().resizeEvent(event)
        if self.pixmap_item:
            # Fit the image in the view while preserving aspect ratio
            self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio) 