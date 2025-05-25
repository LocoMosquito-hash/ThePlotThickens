#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utility functions for the story board module.
"""

import math
from typing import List, Dict, Any
from PyQt6.QtWidgets import QFrame
from PyQt6.QtCore import QPointF

# Constants
CARD_WIDTH = 180
CARD_HEIGHT = 240
DEFAULT_GRID_SIZE = 50
MIN_ZOOM = 0.1
MAX_ZOOM = 4.0
ZOOM_FACTOR = 1.25

def create_vertical_line() -> QFrame:
    """Create a vertical line for use as a separator.
    
    Returns:
        A vertical line widget
    """
    line = QFrame()
    line.setFrameShape(QFrame.Shape.VLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    line.setFixedWidth(2)
    line.setFixedHeight(24)
    return line

def calculate_grid_position(position: QPointF, grid_size: int) -> QPointF:
    """Snap a position to the grid.
    
    Args:
        position: The position to snap
        grid_size: Grid size in pixels
        
    Returns:
        The snapped position
    """
    snapped_x = round(position.x() / grid_size) * grid_size
    snapped_y = round(position.y() / grid_size) * grid_size
    return QPointF(snapped_x, snapped_y)

def calculate_grid_layout(character_count: int, start_x: float = 100, start_y: float = 100) -> List[Dict[str, float]]:
    """Calculate grid positions for characters.
    
    Args:
        character_count: Number of characters to position
        start_x: Starting X coordinate
        start_y: Starting Y coordinate
        
    Returns:
        List of position dictionaries with 'x' and 'y' keys
    """
    positions = []
    cols = max(1, int(math.sqrt(character_count)))
    
    for i in range(character_count):
        row = i // cols
        col = i % cols
        
        x = start_x + col * 200
        y = start_y + row * 250
        
        positions.append({"x": x, "y": y})
    
    return positions 