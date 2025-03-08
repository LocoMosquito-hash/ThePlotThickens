#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Clipboard Image Viewer

A simple PyQt6 application that allows pasting images from clipboard and displaying them.
"""

import sys
import logging
import os
from typing import Optional, Union, List, Dict
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, 
    QVBoxLayout, QHBoxLayout, QWidget, QScrollArea,
    QFileDialog, QMessageBox, QTextEdit
)
from PyQt6.QtGui import QPixmap, QImage, QClipboard
from PyQt6.QtCore import Qt, QSize, QMimeData, QByteArray, QUrl

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('clipboard_debug.log')
    ]
)
logger = logging.getLogger('ClipboardViewer')


class ClipboardImageViewer(QMainWindow):
    """Main application window for viewing and pasting clipboard images."""
    
    def __init__(self) -> None:
        """Initialize the main window and UI components."""
        super().__init__()
        
        self.current_image: Optional[QPixmap] = None
        
        self.init_ui()
    
    def init_ui(self) -> None:
        """Set up the user interface."""
        # Set window properties
        self.setWindowTitle("Clipboard Image Viewer")
        self.setMinimumSize(800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create button layout
        button_layout = QHBoxLayout()
        
        # Create paste button
        self.paste_button = QPushButton("Paste Image (Ctrl+V)")
        self.paste_button.setToolTip("Paste image from clipboard")
        self.paste_button.clicked.connect(self.paste_image)
        button_layout.addWidget(self.paste_button)
        
        # Create save button
        self.save_button = QPushButton("Save Image")
        self.save_button.setToolTip("Save the current image to a file")
        self.save_button.clicked.connect(self.save_image)
        self.save_button.setEnabled(False)  # Disabled until an image is pasted
        button_layout.addWidget(self.save_button)
        
        # Create clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.setToolTip("Clear the current image")
        self.clear_button.clicked.connect(self.clear_image)
        self.clear_button.setEnabled(False)  # Disabled until an image is pasted
        button_layout.addWidget(self.clear_button)
        
        # Create debug button
        self.debug_button = QPushButton("Debug Clipboard")
        self.debug_button.setToolTip("Show detailed clipboard content information")
        self.debug_button.clicked.connect(self.debug_clipboard)
        button_layout.addWidget(self.debug_button)
        
        # Add button layout to main layout
        main_layout.addLayout(button_layout)
        
        # Create scroll area for the image
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create image label
        self.image_label = QLabel("No image. Press 'Paste Image' or Ctrl+V to paste from clipboard.")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(QSize(400, 300))
        self.image_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ddd;")
        
        # Add image label to scroll area
        self.scroll_area.setWidget(self.image_label)
        
        # Add scroll area to main layout
        main_layout.addWidget(self.scroll_area)
        
        # Create debug text area (initially hidden)
        self.debug_text = QTextEdit()
        self.debug_text.setReadOnly(True)
        self.debug_text.setMinimumHeight(150)
        self.debug_text.setVisible(False)
        main_layout.addWidget(self.debug_text)
        
        # Set up keyboard shortcuts
        self.shortcut_paste = Qt.Key.Key_V | Qt.KeyboardModifier.ControlModifier
        
    def keyPressEvent(self, event) -> None:
        """Handle keyboard events."""
        if event.key() == Qt.Key.Key_V and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.paste_image()
        else:
            super().keyPressEvent(event)
    
    def get_mime_data_info(self, mime_data: QMimeData) -> Dict[str, str]:
        """Extract detailed information about the mime data."""
        info = {}
        
        # Get all formats
        formats = mime_data.formats()
        info["Available Formats"] = ", ".join(formats)
        
        # Check for image
        info["Has Image"] = str(mime_data.hasImage())
        
        # Check for HTML
        if mime_data.hasHtml():
            html = mime_data.html()
            info["HTML"] = html[:100] + "..." if len(html) > 100 else html
        
        # Check for text
        if mime_data.hasText():
            text = mime_data.text()
            info["Text"] = text[:100] + "..." if len(text) > 100 else text
        
        # Check for URLs
        if mime_data.hasUrls():
            urls = [url.toString() for url in mime_data.urls()]
            info["URLs"] = ", ".join(urls)
        
        # Get raw data for each format
        for format_name in formats:
            try:
                data = mime_data.data(format_name)
                if data:
                    size = data.size()
                    info[f"Format '{format_name}' Size"] = f"{size} bytes"
                    
                    # Try to decode as text if small enough
                    if size < 1000 and not format_name.startswith("application/"):
                        try:
                            text_data = bytes(data).decode('utf-8', errors='replace')
                            info[f"Format '{format_name}' Data"] = text_data[:100] + "..." if len(text_data) > 100 else text_data
                        except:
                            pass
            except Exception as e:
                info[f"Format '{format_name}' Error"] = str(e)
        
        return info
    
    def debug_clipboard(self) -> None:
        """Display detailed information about the current clipboard content."""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        # Get detailed info
        info = self.get_mime_data_info(mime_data)
        
        # Format the info for display
        debug_text = "CLIPBOARD CONTENT DETAILS:\n\n"
        for key, value in info.items():
            debug_text += f"{key}: {value}\n\n"
        
        # Log the information
        logger.info("Clipboard Debug Information:\n%s", debug_text)
        
        # Show in the UI
        self.debug_text.setText(debug_text)
        self.debug_text.setVisible(True)
        
        # Also show in a dialog for easy copying
        QMessageBox.information(self, "Clipboard Debug Info", 
                               "Debug information has been logged to clipboard_debug.log and displayed below.")
    
    def paste_image(self) -> None:
        """Paste image from clipboard and display it."""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        # Log mime data information
        info = self.get_mime_data_info(mime_data)
        logger.info("Attempting to paste image. Clipboard contains: %s", info["Available Formats"])
        
        if mime_data.hasImage():
            # Get image from clipboard
            image = clipboard.image()
            
            if not image.isNull():
                # Convert QImage to QPixmap for display
                self.current_image = QPixmap.fromImage(image)
                self.display_image()
                self.save_button.setEnabled(True)
                self.clear_button.setEnabled(True)
                logger.info("Successfully pasted image: %dx%d pixels", 
                           image.width(), image.height())
            else:
                self.show_error("Invalid Image", "The clipboard contains an invalid image.")
                logger.warning("Clipboard has image data but image is null")
        else:
            # Try to handle other formats that might contain images
            handled = False
            
            # Check for URI list (file paths)
            if mime_data.hasFormat("text/uri-list"):
                urls = mime_data.urls()
                if urls and urls[0].isLocalFile():
                    file_path = urls[0].toLocalFile()
                    logger.info("Found local file path: %s", file_path)
                    
                    # Check if it's an image file by extension
                    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']
                    if any(file_path.lower().endswith(ext) for ext in image_extensions):
                        # Try to load the image from the file
                        try:
                            image = QImage(file_path)
                            if not image.isNull():
                                self.current_image = QPixmap.fromImage(image)
                                self.display_image()
                                self.save_button.setEnabled(True)
                                self.clear_button.setEnabled(True)
                                logger.info("Successfully loaded image from file: %s (%dx%d pixels)", 
                                           file_path, image.width(), image.height())
                                handled = True
                            else:
                                logger.warning("Failed to load image from file: %s", file_path)
                        except Exception as e:
                            logger.error("Error loading image from file: %s - %s", file_path, str(e))
            
            # Check for specific mime types that might contain images
            if not handled:
                for format_name in mime_data.formats():
                    logger.info("Checking format: %s", format_name)
                    
                    # Handle specific formats here as we discover them
                    # For example, if we find that a specific application uses a custom format
                    
                    # This is where we'll add support for additional formats based on our findings
                
                if not handled:
                    self.show_error("No Image", "No image found in clipboard. Copy an image first.")
                    logger.warning("No image found in clipboard. Available formats: %s", 
                                  ", ".join(mime_data.formats()))
                    
                    # Show debug info automatically when paste fails
                    self.debug_clipboard()
    
    def display_image(self) -> None:
        """Display the current image in the image label."""
        if self.current_image:
            # Scale the image to fit the scroll area while maintaining aspect ratio
            scaled_pixmap = self.current_image.scaled(
                self.scroll_area.width() - 20, 
                self.scroll_area.height() - 20,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            
            # Update the image label size to match the pixmap
            self.image_label.setMinimumSize(scaled_pixmap.size())
            
            # Hide debug text when displaying an image
            self.debug_text.setVisible(False)
    
    def save_image(self) -> None:
        """Save the current image to a file."""
        if not self.current_image:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Image",
            "",
            "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;All Files (*)"
        )
        
        if file_path:
            success = self.current_image.save(file_path)
            if success:
                QMessageBox.information(self, "Success", f"Image saved to {file_path}")
                logger.info("Image saved to %s", file_path)
            else:
                self.show_error("Save Failed", f"Failed to save image to {file_path}")
                logger.error("Failed to save image to %s", file_path)
    
    def clear_image(self) -> None:
        """Clear the current image."""
        self.current_image = None
        self.image_label.setText("No image. Press 'Paste Image' or Ctrl+V to paste from clipboard.")
        self.image_label.setPixmap(QPixmap())  # Clear the pixmap
        self.save_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        logger.info("Image cleared")
    
    def show_error(self, title: str, message: str) -> None:
        """Display an error message dialog."""
        QMessageBox.critical(self, title, message)
        logger.error("%s: %s", title, message)
    
    def resizeEvent(self, event) -> None:
        """Handle window resize events to scale the image appropriately."""
        super().resizeEvent(event)
        if self.current_image:
            self.display_image()


def main() -> None:
    """Application entry point."""
    app = QApplication(sys.argv)
    window = ClipboardImageViewer()
    window.show()
    logger.info("Application started")
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 