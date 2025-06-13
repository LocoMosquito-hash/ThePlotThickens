#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Drag and drop utilities for Tier Maker.

This module provides mixins and utilities for implementing drag-drop functionality.
Based on PyQt6 drag-drop patterns.
"""

from typing import Optional, Protocol
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDrag, QPixmap
from PyQt6.QtWidgets import QWidget


class DragDropMixin:
    """Mixin class to add drag-drop functionality to widgets.
    
    This mixin provides common drag-drop methods that can be used
    by various widgets in the tier maker.
    """
    
    def start_drag(self, widget: QWidget, mime_data: Optional[QMimeData] = None) -> None:
        """Start a drag operation for the given widget.
        
        Args:
            widget: The widget being dragged
            mime_data: Optional mime data for the drag operation
        """
        if mime_data is None:
            mime_data = QMimeData()
        
        drag = QDrag(widget)
        drag.setMimeData(mime_data)
        
        # Create a pixmap of the widget being dragged
        pixmap = QPixmap(widget.size())
        widget.render(pixmap)
        drag.setPixmap(pixmap)
        
        # Start the drag operation
        drag.exec(Qt.DropAction.MoveAction)
    
    def create_mime_data(self, data_type: str, data: str) -> QMimeData:
        """Create mime data for drag operations.
        
        Args:
            data_type: The type of data being dragged
            data: The data payload
            
        Returns:
            QMimeData object with the specified data
        """
        mime_data = QMimeData()
        mime_data.setData(f"application/x-tiermaker-{data_type}", data.encode())
        return mime_data
    
    def extract_mime_data(self, mime_data: QMimeData, data_type: str) -> Optional[str]:
        """Extract data from mime data.
        
        Args:
            mime_data: The mime data to extract from
            data_type: The type of data to extract
            
        Returns:
            The extracted data as string, or None if not found
        """
        format_name = f"application/x-tiermaker-{data_type}"
        if mime_data.hasFormat(format_name):
            data = mime_data.data(format_name)
            return data.data().decode()
        return None


class DropTargetProtocol(Protocol):
    """Protocol for widgets that can accept drops."""
    
    def can_accept_drop(self, mime_data: QMimeData) -> bool:
        """Check if this widget can accept the given drop.
        
        Args:
            mime_data: The mime data being dropped
            
        Returns:
            True if the drop can be accepted
        """
        ...
    
    def handle_drop(self, mime_data: QMimeData, position: tuple) -> bool:
        """Handle a drop operation.
        
        Args:
            mime_data: The mime data being dropped
            position: The drop position as (x, y) tuple
            
        Returns:
            True if the drop was handled successfully
        """
        ...


def setup_drop_target(widget: QWidget) -> None:
    """Set up a widget to accept drops.
    
    Args:
        widget: The widget to set up as a drop target
    """
    widget.setAcceptDrops(True)


def get_drop_position(event) -> tuple:
    """Get the drop position from a drop event.
    
    Args:
        event: The drop event
        
    Returns:
        Position as (x, y) tuple
    """
    pos = event.position()
    return (int(pos.x()), int(pos.y())) 