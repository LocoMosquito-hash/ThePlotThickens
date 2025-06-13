#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Drag and drop widgets for Tier Maker.

This module contains the core drag-drop widgets adapted from PyQt6 examples
for use in the tier maker application.
"""

import os
from typing import List, Optional, Any
from PyQt6.QtCore import Qt, QMimeData, pyqtSignal, QSize
from PyQt6.QtGui import QDrag, QPixmap, QPainter, QFont
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, 
    QFrame, QSizePolicy
)

from models.rankable_item import RankableItem
from utils.drag_drop_utils import DragDropMixin, setup_drop_target, get_drop_position


class DragTargetIndicator(QLabel):
    """Visual indicator showing where an item will be dropped."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setContentsMargins(5, 5, 5, 5)
        self.setStyleSheet("""
            QLabel { 
                background-color: rgba(66, 165, 245, 0.3); 
                border: 2px dashed #42a5f5; 
                border-radius: 4px;
            }
        """)
        self.setFixedHeight(80)  # Match character item height


class CharacterDragItem(QLabel, DragDropMixin):
    """A draggable widget representing a character with avatar and name."""
    
    def __init__(self, item: RankableItem, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.item = item
        self.setFixedSize(70, 80)  # Square-ish for avatar + name
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 1px solid #666;
                border-radius: 4px;
                background-color: #2b2b2b;
                color: white;
                padding: 2px;
            }
            QLabel:hover {
                border-color: #42a5f5;
                background-color: #3b3b3b;
            }
        """)
        
        # Set tooltip
        self.setToolTip(item.get_tooltip())
        
        # Load and display avatar or show name
        self._setup_display()
    
    def _setup_display(self) -> None:
        """Set up the visual display of the character."""
        if self.item.avatar_path and os.path.exists(self.item.avatar_path):
            # Load avatar image
            pixmap = QPixmap(self.item.avatar_path)
            if not pixmap.isNull():
                # Scale to fit while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    60, 60, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                
                # Create a pixmap with text below the image
                final_pixmap = QPixmap(68, 78)
                final_pixmap.fill(Qt.GlobalColor.transparent)
                
                painter = QPainter(final_pixmap)
                
                # Draw the avatar
                x = (68 - scaled_pixmap.width()) // 2
                y = 2
                painter.drawPixmap(x, y, scaled_pixmap)
                
                # Draw the name below
                painter.setPen(Qt.GlobalColor.white)
                font = QFont()
                font.setPointSize(8)
                painter.setFont(font)
                
                name_rect = painter.fontMetrics().boundingRect(self.item.name)
                if name_rect.width() > 66:
                    # Truncate name if too long
                    name = self.item.name[:8] + "..."
                else:
                    name = self.item.name
                
                text_y = y + scaled_pixmap.height() + 12
                painter.drawText(1, text_y, 66, 14, Qt.AlignmentFlag.AlignCenter, name)
                painter.end()
                
                self.setPixmap(final_pixmap)
            else:
                self._set_text_display()
        else:
            self._set_text_display()
    
    def _set_text_display(self) -> None:
        """Set up text-only display when no avatar is available."""
        # Truncate name if too long
        display_name = self.item.name
        if len(display_name) > 10:
            display_name = display_name[:8] + "..."
        
        self.setText(display_name)
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        self.setFont(font)
        self.setWordWrap(True)
    
    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move events to start drag operations."""
        if event.buttons() == Qt.MouseButton.LeftButton:
            # Create mime data with character information
            mime_data = self.create_mime_data("character", str(self.item.id))
            self.start_drag(self, mime_data)


class DragItem(QLabel, DragDropMixin):
    """Generic draggable item widget."""
    
    def __init__(self, text: str = "", data: Any = None, parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.data = data or text
        self.setContentsMargins(10, 5, 10, 5)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 1px solid #666;
                border-radius: 4px;
                background-color: #2b2b2b;
                color: white;
                padding: 5px;
            }
            QLabel:hover {
                border-color: #42a5f5;
                background-color: #3b3b3b;
            }
        """)
    
    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move events to start drag operations."""
        if event.buttons() == Qt.MouseButton.LeftButton:
            mime_data = self.create_mime_data("item", str(self.data))
            self.start_drag(self, mime_data)


class DragWidget(QWidget, DragDropMixin):
    """Generic drag-drop container widget with visual drop indicators."""
    
    orderChanged = pyqtSignal(list)
    
    def __init__(self, orientation: Qt.Orientation = Qt.Orientation.Horizontal, 
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        setup_drop_target(self)
        
        self.orientation = orientation
        self.items: List[QWidget] = []
        
        if self.orientation == Qt.Orientation.Vertical:
            self.layout = QVBoxLayout()
        else:
            self.layout = QHBoxLayout()
        
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)
        
        # Add drag target indicator (hidden by default)
        self._drag_target_indicator = DragTargetIndicator()
        self.layout.addWidget(self._drag_target_indicator)
        self._drag_target_indicator.hide()
        
        self.setLayout(self.layout)
        
        # Style the container
        self.setStyleSheet("""
            DragWidget {
                background-color: #1e1e1e;
                border: 1px solid #444;
                border-radius: 4px;
            }
        """)
    
    def dragEnterEvent(self, event) -> None:
        """Handle drag enter events."""
        if self._can_accept_drop(event.mimeData()):
            event.accept()
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event) -> None:
        """Handle drag leave events."""
        self._drag_target_indicator.hide()
        event.accept()
    
    def dragMoveEvent(self, event) -> None:
        """Handle drag move events to show drop indicator."""
        if not self._can_accept_drop(event.mimeData()):
            event.ignore()
            return
        
        # Find the correct location for the drop target indicator
        index = self._find_drop_location(event)
        if index is not None:
            # Move the indicator to the correct position
            self.layout.insertWidget(index, self._drag_target_indicator)
            # Hide the item being dragged if it's from this container
            source = event.source()
            if source and source.parent() == self:
                source.hide()
            # Show the target indicator
            self._drag_target_indicator.show()
        
        event.accept()
    
    def dropEvent(self, event) -> None:
        """Handle drop events."""
        if not self._can_accept_drop(event.mimeData()):
            event.ignore()
            return
        
        source = event.source()
        
        # Hide the target indicator
        self._drag_target_indicator.hide()
        
        # Get the drop index
        index = self.layout.indexOf(self._drag_target_indicator)
        
        if source and hasattr(source, 'item'):
            # This is a character item being dropped
            if source.parent() != self:
                # Item from another container - create a copy
                new_item = CharacterDragItem(source.item, self)
                self.layout.insertWidget(index, new_item)
                self.items.insert(index, new_item)
            else:
                # Item from this container - move it
                self.layout.insertWidget(index, source)
                source.show()
                # Update items list
                if source in self.items:
                    self.items.remove(source)
                self.items.insert(index, source)
        
        # Emit order changed signal
        self.orderChanged.emit(self.get_item_data())
        event.accept()
    
    def _can_accept_drop(self, mime_data: QMimeData) -> bool:
        """Check if we can accept the drop."""
        return (mime_data.hasFormat("application/x-tiermaker-character") or 
                mime_data.hasFormat("application/x-tiermaker-item"))
    
    def _find_drop_location(self, event) -> Optional[int]:
        """Find where to place the drop indicator."""
        pos = get_drop_position(event)
        spacing = self.layout.spacing() / 2
        
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if widget == self._drag_target_indicator:
                continue
            
            if self.orientation == Qt.Orientation.Vertical:
                # Vertical layout
                drop_here = (
                    pos[1] >= widget.y() - spacing and
                    pos[1] <= widget.y() + widget.height() + spacing
                )
            else:
                # Horizontal layout
                drop_here = (
                    pos[0] >= widget.x() - spacing and
                    pos[0] <= widget.x() + widget.width() + spacing
                )
            
            if drop_here:
                return i
        
        # Drop at the end
        return self.layout.count() - 1  # -1 because indicator is always last
    
    def add_item(self, item: QWidget) -> None:
        """Add an item to this container."""
        # Insert before the drag target indicator
        index = self.layout.count() - 1
        self.layout.insertWidget(index, item)
        self.items.append(item)
    
    def remove_item(self, item: QWidget) -> None:
        """Remove an item from this container."""
        if item in self.items:
            self.items.remove(item)
            self.layout.removeWidget(item)
            item.setParent(None)
    
    def clear_items(self) -> None:
        """Remove all items from this container."""
        for item in self.items[:]:  # Copy list to avoid modification during iteration
            self.remove_item(item)
    
    def get_item_data(self) -> List[Any]:
        """Get data from all items in this container."""
        data = []
        for item in self.items:
            if hasattr(item, 'item'):
                # Character item
                data.append(item.item)
            elif hasattr(item, 'data'):
                # Generic item
                data.append(item.data)
        return data 