#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OCR Clipboard Tool

A simple GUI application that allows pasting images from clipboard
and performs OCR to extract text from them.
"""

import sys
import os
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QSplitter, QMessageBox,
    QComboBox, QCheckBox, QGroupBox, QFileDialog
)
from PyQt6.QtGui import (
    QPixmap, QImage, QClipboard, QPainter, QColor, QFont,
    QAction, QKeySequence
)
from PyQt6.QtCore import Qt, QSize, QBuffer, QByteArray, QIODevice

# Import pytesseract for OCR functionality
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


# Common Tesseract installation paths to check
COMMON_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"C:\Tesseract-OCR\tesseract.exe",
]


class OCRClipboardTool(QMainWindow):
    """Main window for the OCR Clipboard Tool application."""
    
    def __init__(self):
        """Initialize the application."""
        super().__init__()
        
        self.current_image: Optional[QImage] = None
        self.ocr_languages = {
            "English": "eng",
            "Spanish": "spa",
            "French": "fra",
            "German": "deu",
            "Italian": "ita",
            "Portuguese": "por",
            "Japanese": "jpn",
            "Korean": "kor",
            "Chinese Simplified": "chi_sim",
            "Chinese Traditional": "chi_tra",
            "Russian": "rus",
        }
        
        self.init_ui()
        self.check_tesseract()
        
    def init_ui(self):
        """Initialize the user interface."""
        # Set window properties
        self.setWindowTitle("OCR Clipboard Tool")
        self.setMinimumSize(800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Create a splitter to allow resizing the image and text areas
        splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(splitter)
        
        # Image area
        image_widget = QWidget()
        image_layout = QVBoxLayout(image_widget)
        
        # Image display
        self.image_label = QLabel("Paste an image (Ctrl+V) to start")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumHeight(200)
        self.image_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        image_layout.addWidget(self.image_label)
        
        # OCR Controls
        controls_layout = QHBoxLayout()
        
        # Paste button
        self.paste_button = QPushButton("Paste Image (Ctrl+V)")
        self.paste_button.clicked.connect(self.paste_image)
        controls_layout.addWidget(self.paste_button)
        
        # Language selection
        self.language_combo = QComboBox()
        for lang_name in self.ocr_languages.keys():
            self.language_combo.addItem(lang_name)
        controls_layout.addWidget(QLabel("Language:"))
        controls_layout.addWidget(self.language_combo)
        
        # OCR button
        self.ocr_button = QPushButton("Extract Text (Ctrl+E)")
        self.ocr_button.clicked.connect(self.perform_ocr)
        self.ocr_button.setEnabled(False)
        controls_layout.addWidget(self.ocr_button)
        
        image_layout.addLayout(controls_layout)
        
        # OCR options
        options_group = QGroupBox("OCR Options")
        options_layout = QHBoxLayout(options_group)
        
        # Add preprocessing options
        self.preprocess_check = QCheckBox("Preprocess Image")
        self.preprocess_check.setChecked(True)
        options_layout.addWidget(self.preprocess_check)
        
        # Add options for OCR modes
        self.line_mode_check = QCheckBox("Line Mode")
        self.line_mode_check.setChecked(False)
        options_layout.addWidget(self.line_mode_check)
        
        # Add Tesseract Path button
        self.set_path_button = QPushButton("Set Tesseract Path")
        self.set_path_button.clicked.connect(self.set_tesseract_path)
        options_layout.addWidget(self.set_path_button)
        
        # Add options for OCR configurations
        image_layout.addWidget(options_group)
        
        splitter.addWidget(image_widget)
        
        # Text area
        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        
        # Text output
        text_layout.addWidget(QLabel("Extracted Text:"))
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        text_layout.addWidget(self.text_edit)
        
        # Output controls
        output_controls = QHBoxLayout()
        
        # Copy text button
        self.copy_button = QPushButton("Copy Text (Ctrl+C)")
        self.copy_button.clicked.connect(self.copy_text)
        self.copy_button.setEnabled(False)
        output_controls.addWidget(self.copy_button)
        
        # Clear button
        self.clear_button = QPushButton("Clear All (Ctrl+X)")
        self.clear_button.clicked.connect(self.clear_all)
        output_controls.addWidget(self.clear_button)
        
        text_layout.addLayout(output_controls)
        
        splitter.addWidget(text_widget)
        
        # Set initial splitter position
        splitter.setSizes([int(self.height() * 0.6), int(self.height() * 0.4)])
        
        # Set up keyboard shortcuts
        self.setup_shortcuts()
        
        # Create status bar
        self.statusBar().showMessage("Ready")
        
    def setup_shortcuts(self):
        """Set up keyboard shortcuts for the application."""
        # Paste shortcut
        paste_shortcut = QAction("Paste", self)
        paste_shortcut.setShortcut(QKeySequence.StandardKey.Paste)
        paste_shortcut.triggered.connect(self.paste_image)
        self.addAction(paste_shortcut)
        
        # OCR shortcut
        ocr_shortcut = QAction("Extract Text", self)
        ocr_shortcut.setShortcut(QKeySequence("Ctrl+E"))
        ocr_shortcut.triggered.connect(self.perform_ocr)
        self.addAction(ocr_shortcut)
        
        # Copy text shortcut
        copy_shortcut = QAction("Copy Text", self)
        copy_shortcut.setShortcut(QKeySequence.StandardKey.Copy)
        copy_shortcut.triggered.connect(self.copy_text)
        self.addAction(copy_shortcut)
        
        # Clear shortcut
        clear_shortcut = QAction("Clear All", self)
        clear_shortcut.setShortcut(QKeySequence("Ctrl+X"))
        clear_shortcut.triggered.connect(self.clear_all)
        self.addAction(clear_shortcut)
    
    def set_tesseract_path(self):
        """Set the path to Tesseract OCR manually."""
        # First try to find Tesseract in common locations
        for path in COMMON_TESSERACT_PATHS:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                self.statusBar().showMessage(f"Found Tesseract at: {path}")
                QMessageBox.information(
                    self,
                    "Tesseract Found",
                    f"Tesseract was found at: {path}\nPath has been configured successfully."
                )
                return True
                
        # If not found in common locations, ask the user to browse for it
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Tesseract Executable",
            "",
            "Executable Files (*.exe);;All Files (*)"
        )
        
        if file_path:
            pytesseract.pytesseract.tesseract_cmd = file_path
            self.statusBar().showMessage(f"Tesseract path set to: {file_path}")
            QMessageBox.information(
                self,
                "Tesseract Path Set",
                f"Tesseract path has been set to:\n{file_path}"
            )
            return True
            
        return False
        
    def check_tesseract(self):
        """Check if Tesseract is available and configured correctly."""
        if not TESSERACT_AVAILABLE:
            QMessageBox.warning(
                self,
                "Tesseract Not Found",
                "pytesseract library is not installed. Please install it using pip:\n"
                "pip install pytesseract\n\n"
                "You will also need to install Tesseract OCR engine."
            )
            return False
        
        try:
            # Try to find Tesseract in common installation locations
            for path in COMMON_TESSERACT_PATHS:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    self.statusBar().showMessage(f"Using Tesseract from: {path}")
                    return True
            
            # Check if Tesseract is installed and accessible
            pytesseract.get_tesseract_version()
            self.statusBar().showMessage("Tesseract found in PATH")
            return True
        except Exception as e:
            QMessageBox.warning(
                self,
                "Tesseract Error",
                f"Tesseract OCR engine not found or not properly configured.\n\n"
                f"Error: {str(e)}\n\n"
                f"Please install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki\n"
                f"Or use the 'Set Tesseract Path' button to locate it manually."
            )
            return False
        
    def paste_image(self):
        """Paste image from clipboard."""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasImage():
            self.current_image = QImage(clipboard.image())
            self.display_image()
            self.ocr_button.setEnabled(True)
        elif mime_data.hasUrls():
            # Try to load the first URL as an image
            url = mime_data.urls()[0]
            if url.isLocalFile():
                file_path = url.toLocalFile()
                if os.path.exists(file_path) and self.is_image_file(file_path):
                    self.current_image = QImage(file_path)
                    self.display_image()
                    self.ocr_button.setEnabled(True)
        else:
            QMessageBox.information(
                self,
                "No Image Found",
                "No image found in clipboard. Copy an image and try again."
            )
    
    def is_image_file(self, file_path):
        """Check if a file is an image based on its extension."""
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']
        _, ext = os.path.splitext(file_path.lower())
        return ext in image_extensions
    
    def display_image(self):
        """Display the current image in the image label."""
        if self.current_image and not self.current_image.isNull():
            # Scale the image to fit the label while maintaining aspect ratio
            label_size = self.image_label.size()
            scaled_pixmap = QPixmap.fromImage(self.current_image).scaled(
                label_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            self.image_label.setText("No image available")
            self.ocr_button.setEnabled(False)
    
    def preprocess_image(self, image):
        """Apply preprocessing to the image for better OCR results."""
        try:
            import cv2
            import numpy as np
            
            # Convert QImage to numpy array
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.ReadWrite)
            image.save(buffer, "PNG")
            bytes_data = buffer.data().data()
            
            nparr = np.frombuffer(bytes_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Optional: Apply noise removal
            kernel = np.ones((1, 1), np.uint8)
            opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
            
            # Convert back to QImage
            h, w = opening.shape
            bytes_per_line = w
            q_img = QImage(opening.data, w, h, bytes_per_line, QImage.Format.Format_Grayscale8)
            
            return q_img
        except ImportError:
            QMessageBox.warning(
                self,
                "OpenCV Not Found",
                "OpenCV library is not installed. Skipping preprocessing.\n"
                "For better results, install OpenCV using:\n"
                "pip install opencv-python"
            )
            return image
        except Exception as e:
            QMessageBox.warning(
                self,
                "Preprocessing Error",
                f"Error during image preprocessing: {str(e)}\n"
                "Using original image instead."
            )
            return image
    
    def perform_ocr(self):
        """Perform OCR on the current image."""
        if not self.current_image or self.current_image.isNull():
            QMessageBox.information(
                self,
                "No Image",
                "Please paste an image first."
            )
            return
        
        if not TESSERACT_AVAILABLE:
            QMessageBox.warning(
                self,
                "Tesseract Not Available",
                "pytesseract library is not installed."
            )
            return
            
        # Try to verify tesseract is properly configured
        try:
            pytesseract.get_tesseract_version()
        except Exception as e:
            result = QMessageBox.question(
                self,
                "Tesseract Error",
                "Tesseract is not properly configured. Would you like to set the path manually?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if result == QMessageBox.StandardButton.Yes:
                if not self.set_tesseract_path():
                    return  # User canceled or failed to set path
            else:
                return  # User chose not to set path
        
        try:
            # Get the selected language
            selected_lang = self.language_combo.currentText()
            lang_code = self.ocr_languages[selected_lang]
            
            # Apply preprocessing if needed
            img = self.current_image
            if self.preprocess_check.isChecked():
                img = self.preprocess_image(img)
            
            # Convert QImage to format suitable for pytesseract
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.ReadWrite)
            img.save(buffer, "PNG")
            bytes_data = buffer.data().data()
            
            # OCR configuration
            config = ""
            if self.line_mode_check.isChecked():
                config = "--psm 7"  # Treat the image as a single line of text
            
            # Perform OCR
            from PIL import Image
            import io
            
            pil_img = Image.open(io.BytesIO(bytes_data))
            text = pytesseract.image_to_string(pil_img, lang=lang_code, config=config)
            
            # Display the results
            if text.strip():
                self.text_edit.setPlainText(text)
                self.copy_button.setEnabled(True)
                self.statusBar().showMessage("Text extracted successfully")
            else:
                self.text_edit.setPlainText("No text detected in the image.")
                self.copy_button.setEnabled(False)
                self.statusBar().showMessage("No text detected")
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "OCR Error",
                f"An error occurred during OCR:\n{str(e)}"
            )
            self.statusBar().showMessage(f"Error: {str(e)}")
    
    def copy_text(self):
        """Copy the extracted text to clipboard."""
        text = self.text_edit.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.statusBar().showMessage("Text copied to clipboard", 3000)
    
    def clear_all(self):
        """Clear the image and text."""
        self.current_image = None
        self.image_label.clear()
        self.image_label.setText("Paste an image (Ctrl+V) to start")
        self.text_edit.clear()
        self.ocr_button.setEnabled(False)
        self.copy_button.setEnabled(False)
        self.statusBar().showMessage("Cleared", 3000)
    
    def resizeEvent(self, event):
        """Handle resize events to update the image display."""
        super().resizeEvent(event)
        if self.current_image and not self.current_image.isNull():
            self.display_image()


def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)
    
    # Set the application style
    app.setStyle("Fusion")
    
    # Create and show the main window
    window = OCRClipboardTool()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 