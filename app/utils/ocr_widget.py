#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OCR Widget for The Plot Thickens application.

This module provides a reusable widget for OCR (Optical Character Recognition)
that can extract text from clipboard images.
"""

import os
import io
from typing import Optional, Dict, List, Callable, Tuple, Any, Union

try:
    import pytesseract
    from PIL import Image
    import cv2
    import numpy as np
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    # Define placeholder for imports
    pytesseract = None
    Image = None
    cv2 = None
    np = None

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QComboBox, QTextEdit, QFileDialog, QApplication,
    QSplitter, QFrame, QGroupBox, QMessageBox, QSizePolicy
)
from PyQt6.QtGui import QImage, QPixmap, QClipboard, QPainter, QKeySequence
from PyQt6.QtCore import Qt, QBuffer, QIODevice, QSize
from PyQt6.QtGui import QShortcut


# Common paths where Tesseract might be installed
COMMON_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"C:\Tesseract-OCR\tesseract.exe",
    "/usr/bin/tesseract",
    "/usr/local/bin/tesseract",
]


class OCRWidget(QWidget):
    """Reusable OCR widget that extracts text from clipboard images."""
    
    def __init__(self, parent=None, on_text_extracted: Callable[[str], None] = None):
        """Initialize the OCR widget.
        
        Args:
            parent: Parent widget
            on_text_extracted: Optional callback for when text is extracted
        """
        super().__init__(parent)
        
        self.current_image = None
        self.on_text_extracted = on_text_extracted
        
        # Dictionary mapping display names to language codes
        self.ocr_languages = {
            "English": "eng",
            "Spanish": "spa",
            "French": "fra",
            "German": "deu",
            "Italian": "ita",
            "Portuguese": "por",
            "Dutch": "nld",
            "Chinese (Simplified)": "chi_sim",
            "Chinese (Traditional)": "chi_tra",
            "Japanese": "jpn",
            "Korean": "kor",
            "Russian": "rus",
            "Arabic": "ara",
            "Hindi": "hin"
        }
        
        self.init_ui()
        self.check_tesseract()
    
    def init_ui(self) -> None:
        """Initialize the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create splitter for resizable sections
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        
        # ======================
        # Top section: Image area
        # ======================
        image_widget = QWidget()
        image_layout = QVBoxLayout(image_widget)
        
        # Image display
        self.image_label = QLabel("Paste an image (Ctrl+V)")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(400, 200)
        self.image_label.setFrameShape(QFrame.Shape.StyledPanel)
        self.image_label.setStyleSheet("background-color: #f0f0f0;")
        image_layout.addWidget(self.image_label)
        
        # Controls for image
        image_controls_layout = QHBoxLayout()
        
        # Paste button
        self.paste_button = QPushButton("Paste Image (Ctrl+V)")
        self.paste_button.clicked.connect(self.paste_image)
        image_controls_layout.addWidget(self.paste_button)
        
        # Language selection
        self.language_combo = QComboBox()
        for lang in self.ocr_languages.keys():
            self.language_combo.addItem(lang)
        self.language_combo.setCurrentText("English")  # Default to English
        image_controls_layout.addWidget(QLabel("Language:"))
        image_controls_layout.addWidget(self.language_combo)
        
        # Extract text button
        self.ocr_button = QPushButton("Extract Text (Ctrl+E)")
        self.ocr_button.clicked.connect(self.perform_ocr)
        self.ocr_button.setEnabled(False)  # Disabled until image is pasted
        image_controls_layout.addWidget(self.ocr_button)
        
        image_layout.addLayout(image_controls_layout)
        
        # OCR options group
        ocr_options_group = QGroupBox("OCR Options")
        ocr_options_layout = QHBoxLayout(ocr_options_group)
        
        # Preprocessing checkbox
        self.preprocess_check = QCheckBox("Preprocess Image")
        self.preprocess_check.setChecked(True)
        ocr_options_layout.addWidget(self.preprocess_check)
        
        # Line mode checkbox
        self.line_mode_check = QCheckBox("Line Mode")
        self.line_mode_check.setToolTip("Optimize for single lines of text")
        ocr_options_layout.addWidget(self.line_mode_check)

        # Add white background checkbox
        self.white_bg_check = QCheckBox("Add White Background")
        self.white_bg_check.setToolTip("Add white background to transparent images")
        self.white_bg_check.setChecked(True)
        ocr_options_layout.addWidget(self.white_bg_check)
        
        # Tesseract path button
        self.path_button = QPushButton("Set Tesseract Path")
        self.path_button.clicked.connect(self.set_tesseract_path)
        ocr_options_layout.addWidget(self.path_button)
        
        image_layout.addWidget(ocr_options_group)
        
        # ======================
        # Bottom section: Text area
        # ======================
        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        
        # Text display
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(False)  # Allow manual edits
        self.text_edit.setPlaceholderText("Extracted text will appear here...")
        text_layout.addWidget(self.text_edit)
        
        # Text controls
        text_controls_layout = QHBoxLayout()
        
        # Copy button
        self.copy_button = QPushButton("Copy Text (Ctrl+C)")
        self.copy_button.clicked.connect(self.copy_text)
        self.copy_button.setEnabled(False)  # Disabled until text is extracted
        text_controls_layout.addWidget(self.copy_button)
        
        # Use selected text button
        self.use_selected_button = QPushButton("Use Selected Text")
        self.use_selected_button.clicked.connect(self.use_selected_text)
        self.use_selected_button.setEnabled(False)  # Disabled until text is extracted
        text_controls_layout.addWidget(self.use_selected_button)
        
        # Use all text button
        self.use_all_button = QPushButton("Use All Text")
        self.use_all_button.clicked.connect(self.use_all_text)
        self.use_all_button.setEnabled(False)  # Disabled until text is extracted
        text_controls_layout.addWidget(self.use_all_button)
        
        # Clear button
        self.clear_button = QPushButton("Clear All (Ctrl+X)")
        self.clear_button.clicked.connect(self.clear_all)
        text_controls_layout.addWidget(self.clear_button)
        
        text_layout.addLayout(text_controls_layout)
        
        # Add widgets to splitter
        self.splitter.addWidget(image_widget)
        self.splitter.addWidget(text_widget)
        
        # Set initial sizes
        self.splitter.setSizes([300, 300])
        
        # Add splitter to main layout
        main_layout.addWidget(self.splitter)
        
        # Setup keyboard shortcuts
        self.setup_shortcuts()
        
        # Disable if tesseract not available
        if not TESSERACT_AVAILABLE:
            self.show_tesseract_error()
    
    def setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts for the widget."""
        # These shortcuts will only work when this widget has focus
        self.paste_shortcut = QShortcut(QKeySequence("Ctrl+V"), self)
        self.paste_shortcut.activated.connect(self.paste_image)
        
        self.extract_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        self.extract_shortcut.activated.connect(self.perform_ocr)
        
        self.copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        self.copy_shortcut.activated.connect(self.copy_text)
        
        self.clear_shortcut = QShortcut(QKeySequence("Ctrl+X"), self) 
        self.clear_shortcut.activated.connect(self.clear_all)
    
    def check_tesseract(self) -> bool:
        """Check if Tesseract is installed and set the path.
        
        Returns:
            True if Tesseract is found, False otherwise
        """
        if not TESSERACT_AVAILABLE:
            return False
            
        # Check if Tesseract path is already set
        if hasattr(pytesseract, 'pytesseract') and pytesseract.pytesseract.tesseract_cmd:
            if os.path.exists(pytesseract.pytesseract.tesseract_cmd):
                print(f"Using Tesseract from: {pytesseract.pytesseract.tesseract_cmd}")
                return True
        
        # Try to find Tesseract in common installation locations
        for path in COMMON_TESSERACT_PATHS:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                print(f"Using Tesseract from: {path}")
                return True
        
        # Tesseract not found
        print("Tesseract not found. Please set the path manually.")
        return False
    
    def set_tesseract_path(self) -> None:
        """Manually set the Tesseract executable path."""
        if not TESSERACT_AVAILABLE:
            self.show_tesseract_error()
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Tesseract Executable",
            "",
            "Executable Files (*.exe);;All Files (*)"
        )
        
        if file_path:
            pytesseract.pytesseract.tesseract_cmd = file_path
            print(f"Tesseract path set to: {file_path}")
            
            # Verify that the selected path works
            try:
                pytesseract.get_tesseract_version()
                QMessageBox.information(
                    self,
                    "Success",
                    f"Tesseract found successfully: {file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Selected path is not a valid Tesseract installation: {str(e)}"
                )
    
    def show_tesseract_error(self) -> None:
        """Show error message about missing Tesseract dependencies."""
        # Disable OCR functionality
        self.ocr_button.setEnabled(False)
        self.paste_button.setEnabled(False)
        self.path_button.setEnabled(False)
        
        # Show error message
        QMessageBox.critical(
            self,
            "Dependencies Missing",
            "OCR functionality requires pytesseract, PIL, OpenCV, and numpy.\n\n"
            "Please install these packages using:\n"
            "pip install pytesseract pillow opencv-python numpy"
        )
    
    def paste_image(self) -> None:
        """Paste image from clipboard."""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasImage():
            self.current_image = QImage(clipboard.image())
            self.display_image()
            self.ocr_button.setEnabled(True)
            print("Image pasted from clipboard")
        else:
            self.image_label.setText("No image in clipboard. Copy an image and press Ctrl+V.")
            print("No image found in clipboard")
    
    def display_image(self) -> None:
        """Display the current image in the image label."""
        if not self.current_image:
            return
            
        # Create a pixmap from the image
        pixmap = QPixmap.fromImage(self.current_image)
        
        # Scale the pixmap to fit the label while preserving aspect ratio
        label_size = self.image_label.size()
        scaled_pixmap = pixmap.scaled(
            label_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Display the scaled pixmap
        self.image_label.setPixmap(scaled_pixmap)
    
    def preprocess_image(self, img_array: Any) -> Any:
        """Preprocess the image to improve OCR accuracy.
        
        Args:
            img_array: NumPy array containing the image
            
        Returns:
            Preprocessed image as NumPy array
        """
        if not TESSERACT_AVAILABLE:
            return img_array
            
        # Convert to grayscale
        gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Apply noise removal
        kernel = np.ones((1, 1), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        return opening
    
    def qimage_to_numpy(self, qimage: QImage) -> Any:
        """Convert QImage to NumPy array for OpenCV processing.
        
        Args:
            qimage: QImage to convert
            
        Returns:
            NumPy array representation of the image
        """
        if not TESSERACT_AVAILABLE:
            return None
            
        # Add white background if needed
        if self.white_bg_check.isChecked() and qimage.hasAlphaChannel():
            background = QImage(qimage.size(), QImage.Format.Format_RGB32)
            background.fill(Qt.GlobalColor.white)
            painter = QPainter(background)
            painter.drawImage(0, 0, qimage)
            painter.end()
            qimage = background
        
        # Convert to correct format
        width = qimage.width()
        height = qimage.height()
        
        # Convert to RGB format
        if qimage.format() != QImage.Format.Format_RGB32:
            qimage = qimage.convertToFormat(QImage.Format.Format_RGB32)
            
        # Get pointer to data
        ptr = qimage.bits()
        
        # Create NumPy array from the data
        arr = np.frombuffer(ptr, np.uint8).reshape((height, width, 4))
        
        # Convert to BGR format (for OpenCV)
        arr = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
        
        return arr
    
    def qimage_to_pil(self, qimage: QImage) -> Any:
        """Convert QImage to PIL Image for pytesseract.
        
        Args:
            qimage: QImage to convert
            
        Returns:
            PIL Image object
        """
        if not TESSERACT_AVAILABLE:
            return None
            
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.ReadWrite)
        qimage.save(buffer, "PNG")
        
        # Get the bytes data
        bytes_data = buffer.data().data()
        
        # Convert to PIL Image
        pil_img = Image.open(io.BytesIO(bytes_data))
        
        return pil_img
    
    def perform_ocr(self) -> None:
        """Perform OCR on the current image."""
        if not self.current_image:
            print("No image to process")
            return
            
        if not TESSERACT_AVAILABLE:
            self.show_tesseract_error()
            return
            
        if not self.check_tesseract():
            QMessageBox.warning(
                self,
                "Tesseract Not Found",
                "Tesseract OCR engine not found. Please set the path manually."
            )
            return
        
        try:
            # Get selected language
            selected_lang = self.language_combo.currentText()
            lang_code = self.ocr_languages[selected_lang]
            
            # Prepare image
            img = self.current_image
            
            # Apply preprocessing if needed
            if self.preprocess_check.isChecked():
                # Convert QImage to numpy array
                img_array = self.qimage_to_numpy(img)
                
                # Preprocess the image
                processed_array = self.preprocess_image(img_array)
                
                # Convert back to PIL Image for OCR
                pil_img = Image.fromarray(processed_array)
            else:
                # Convert directly to PIL without preprocessing
                pil_img = self.qimage_to_pil(img)
            
            # Set OCR config based on options
            config = ""
            if self.line_mode_check.isChecked():
                config = "--psm 7"  # Treat the image as a single line of text
            
            # Perform OCR
            print(f"Performing OCR with language: {lang_code}, config: {config}")
            text = pytesseract.image_to_string(pil_img, lang=lang_code, config=config)
            
            # Update text display
            if text.strip():
                self.text_edit.setPlainText(text)
                self.copy_button.setEnabled(True)
                self.use_selected_button.setEnabled(True)
                self.use_all_button.setEnabled(True)
                print("Text extracted successfully")
            else:
                self.text_edit.setPlainText("No text detected in the image.")
                self.copy_button.setEnabled(False)
                self.use_selected_button.setEnabled(False)
                self.use_all_button.setEnabled(False)
                print("No text detected")
                
        except Exception as e:
            self.text_edit.setPlainText(f"Error during OCR: {str(e)}")
            print(f"Error during OCR: {e}")
            QMessageBox.critical(
                self,
                "OCR Error",
                f"An error occurred during OCR processing: {str(e)}"
            )
    
    def copy_text(self) -> None:
        """Copy the text in the text edit to clipboard."""
        text = self.text_edit.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            print("Text copied to clipboard")
    
    def use_selected_text(self) -> None:
        """Use the selected text in the callback function."""
        selected_text = self.text_edit.textCursor().selectedText()
        if selected_text and self.on_text_extracted:
            self.on_text_extracted(selected_text)
            print("Selected text sent to callback")
        elif not selected_text:
            print("No text selected")
    
    def use_all_text(self) -> None:
        """Use all text in the callback function."""
        text = self.text_edit.toPlainText()
        if text and self.on_text_extracted:
            self.on_text_extracted(text)
            print("All text sent to callback")
    
    def clear_all(self) -> None:
        """Clear the image and text."""
        self.current_image = None
        self.image_label.setText("Paste an image (Ctrl+V)")
        self.image_label.setPixmap(QPixmap())
        self.text_edit.clear()
        self.ocr_button.setEnabled(False)
        self.copy_button.setEnabled(False)
        self.use_selected_button.setEnabled(False)
        self.use_all_button.setEnabled(False)
        print("All cleared")
    
    def set_on_text_extracted_callback(self, callback: Callable[[str], None]) -> None:
        """Set the callback function for when text is extracted.
        
        Args:
            callback: Function to call with the extracted text
        """
        self.on_text_extracted = callback
    
    def get_text(self) -> str:
        """Get the current text.
        
        Returns:
            The text in the text edit
        """
        return self.text_edit.toPlainText()
    
    def get_selected_text(self) -> str:
        """Get the selected text.
        
        Returns:
            The selected text in the text edit
        """
        return self.text_edit.textCursor().selectedText()


# Standalone test function
def test_ocr_widget():
    """Test the OCR widget as a standalone application."""
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow
    
    app = QApplication(sys.argv)
    
    # Create main window
    window = QMainWindow()
    window.setWindowTitle("OCR Widget Test")
    window.setMinimumSize(800, 600)
    
    # Create OCR widget with callback
    def on_text_extracted(text):
        print(f"Text extracted: {text[:50]}...")
    
    ocr_widget = OCRWidget(on_text_extracted=on_text_extracted)
    
    # Set as central widget
    window.setCentralWidget(ocr_widget)
    
    # Show window
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    test_ocr_widget() 