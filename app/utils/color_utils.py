#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Color utilities for The Plot Thickens application.

This module provides functions for color operations, including generating colors from strings
and calculating contrasting colors.
"""

import hashlib
from typing import Tuple


def string_to_color(input_string: str) -> str:
    """
    Convert a string to a consistent hex color code.
    
    Args:
        input_string: A non-empty string to convert to a color
        
    Returns:
        A hex color code in the format '#RRGGBB'
    """
    if not input_string:
        raise ValueError("Input string cannot be empty")
    
    # Create a hash of the string
    hash_object = hashlib.md5(input_string.encode())
    hex_digest = hash_object.hexdigest()
    
    # Use the first 6 characters of the hash as the color code
    color_hex = hex_digest[:6]
    
    # Return with # prefix
    return f"#{color_hex}"


def get_contrasting_text_color(background_color: str) -> str:
    """
    Get a contrasting color (black or white) based on the brightness of the background color.
    
    Args:
        background_color: A hex color code in the format '#RRGGBB'
        
    Returns:
        '#000000' for black or '#FFFFFF' for white depending on which provides better contrast
    """
    # Remove # if present
    color = background_color.lstrip('#')
    
    # Convert hex to RGB
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)
    
    # Calculate perceived brightness using the formula from W3C
    # https://www.w3.org/TR/AERT/#color-contrast
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    
    # Return black for bright colors and white for dark colors
    if brightness > 125:
        return "#000000"  # Black text for bright backgrounds
    else:
        return "#FFFFFF"  # White text for dark backgrounds


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    Convert a hex color code to RGB values.
    
    Args:
        hex_color: A hex color code in the format '#RRGGBB' or 'RRGGBB'
        
    Returns:
        Tuple of (R, G, B) values as integers (0-255)
    """
    color = hex_color.lstrip('#')
    return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """
    Convert RGB values to a hex color code.
    
    Args:
        rgb: Tuple of (R, G, B) values as integers (0-255)
        
    Returns:
        A hex color code in the format '#RRGGBB'
    """
    return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}' 