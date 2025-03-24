#!/usr/bin/env python3
"""
Test Pattern Generator for The Plot Thickens

This script generates a checkered pattern with numbered squares to help debug 
coordinate systems in the image tagging feature.
"""

import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np

def create_test_pattern(width=800, height=600, grid_size=80, save_path="test_pattern.png"):
    """
    Create a checkered test pattern with numbered squares.
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        grid_size: Size of each square in pixels
        save_path: Path to save the image
    """
    # Create a white background image
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # Try to load a font, fall back to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        font = ImageFont.load_default()
    
    # Draw the checkered pattern
    colors = [(200, 200, 200), (240, 240, 240)]  # Light gray and lighter gray
    text_colors = [(255, 0, 0), (200, 0, 0)]     # Red and darker red
    
    cell_counter = 0
    for y in range(0, height, grid_size):
        for x in range(0, width, grid_size):
            # Alternate colors
            color_idx = (x // grid_size + y // grid_size) % 2
            
            # Draw the square
            x2, y2 = min(x + grid_size, width), min(y + grid_size, height)
            draw.rectangle([x, y, x2, y2], fill=colors[color_idx])
            
            # Draw horizontal and vertical lines for the grid
            draw.line([x, y, x2, y], fill=(100, 100, 100))
            draw.line([x, y, x, y2], fill=(100, 100, 100))
            
            # Add the cell number
            cell_number = f"{cell_counter}"
            
            # Handle text sizing in a way that works with newer PIL versions
            try:
                # New method in newer PIL versions
                bbox = font.getbbox(cell_number)
                text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
            except AttributeError:
                try:
                    # Older method
                    text_width, text_height = draw.textsize(cell_number, font=font)
                except:
                    # Fallback method if all else fails
                    text_width, text_height = len(cell_number) * 10, 20
                    
            text_position = (x + (grid_size - text_width) // 2, y + (grid_size - text_height) // 2)
            draw.text(text_position, cell_number, fill=text_colors[color_idx], font=font)
            
            # Add coordinates in smaller text
            coord_text = f"({x},{y})"
            draw.text((x + 5, y + grid_size - 20), coord_text, fill=(0, 0, 200), font=ImageFont.load_default())
            
            cell_counter += 1
    
    # Draw a border around the image
    draw.rectangle([0, 0, width-1, height-1], outline=(0, 0, 0))
    
    # Add labels for the coordinate system
    draw.text((10, 10), "Origin (0,0) is at top-left", fill=(0, 0, 0), font=font)
    draw.text((10, 40), f"Grid size: {grid_size}px", fill=(0, 0, 0), font=font)
    draw.text((10, 70), f"Image size: {width}x{height}px", fill=(0, 0, 0), font=font)
    
    # Save the image
    image.save(save_path)
    print(f"Test pattern saved to {os.path.abspath(save_path)}")
    return save_path

def create_multiple_test_patterns():
    """Create multiple test patterns with different sizes."""
    create_test_pattern(800, 600, 80, "test_pattern_800x600.png")
    create_test_pattern(1024, 768, 100, "test_pattern_1024x768.png")
    create_test_pattern(1920, 1080, 120, "test_pattern_1920x1080.png")

if __name__ == "__main__":
    create_multiple_test_patterns()
    print("Test patterns created. Please paste them into the gallery and test the tag positioning.")
    print("Observe the cell numbers and coordinates to pinpoint any positioning issues.") 