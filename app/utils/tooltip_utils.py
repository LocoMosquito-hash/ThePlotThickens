#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tooltip utilities for The Plot Thickens application.

This module provides functions for generating consistent tooltips with avatars.
"""

import os
import base64
from typing import Optional, Tuple

from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtCore import QBuffer, QByteArray, QIODevice, Qt

def string_to_color(text: str) -> Tuple[str, str]:
    """Convert a string to a consistent color hex code and contrasting text color.
    
    Args:
        text: The text to convert to a color
        
    Returns:
        Tuple of (background_color, text_color) hex values
    """
    # Generate a consistent color from the text (simple hash-based approach)
    import hashlib
    md5_hash = hashlib.md5(text.encode()).hexdigest()
    bg_color = f"#{md5_hash[:6]}"
    
    # Calculate brightness using the W3C formula for perceived brightness
    r = int(md5_hash[:2], 16)
    g = int(md5_hash[2:4], 16)
    b = int(md5_hash[4:6], 16)
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    
    # Return contrasting text color (black for bright backgrounds, white for dark)
    text_color = "#000000" if brightness > 128 else "#FFFFFF"
    
    return bg_color, text_color

def generate_avatar_tooltip_html(character_name: str, avatar_path: Optional[str] = None, 
                               max_size: int = 160) -> str:
    """Generate HTML tooltip with character name and avatar.
    
    Args:
        character_name: Name of the character
        avatar_path: Path to avatar image file (optional)
        max_size: Maximum size for the avatar image
        
    Returns:
        HTML string for the tooltip
    """
    # Generate background color based on character name
    bg_color, text_color = string_to_color(character_name)
    
    # Start with the name header
    html = f"""
    <div style="background-color:{bg_color}; color:{text_color}; padding:5px; text-align:center;">
        <b>{character_name}</b>
    </div>
    """
    
    # Add avatar if available
    if avatar_path and os.path.exists(avatar_path):
        try:
            # Load and scale avatar
            pixmap = QPixmap(avatar_path)
            if not pixmap.isNull():
                # Scale pixmap while preserving aspect ratio
                pixmap = pixmap.scaled(max_size, max_size, 
                                     aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
                                     transformMode=Qt.TransformationMode.SmoothTransformation)
                
                # Convert pixmap to base64 for embedding in HTML
                byte_array = QByteArray()
                buffer = QBuffer(byte_array)
                buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                pixmap.save(buffer, "PNG")
                image_data = base64.b64encode(byte_array.data()).decode()
                
                # Add image to HTML
                html += f"""
                <div style="text-align:center; padding:5px;">
                    <img src="data:image/png;base64,{image_data}" 
                         style="max-width:{max_size}px; max-height:{max_size}px;"/>
                </div>
                """
        except Exception as e:
            print(f"Error generating avatar tooltip: {e}")
    
    return html 