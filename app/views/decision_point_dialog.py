#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Decision Point Dialog for The Plot Thickens application.

This dialog allows users to create and manage decision points for visual novels.
"""

import os
import io
from typing import List, Dict, Any, Optional, Tuple

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QGroupBox, QScrollArea, QWidget, QRadioButton,
    QInputDialog, QMessageBox, QTextEdit, QSplitter, QCheckBox,
    QTabWidget, QApplication
)
from PyQt6.QtCore import Qt, QSize, QBuffer, QIODevice
from PyQt6.QtGui import (
    QPixmap, QImage, QClipboard, QAction, QKeySequence, QColor
)

# Import pytesseract for OCR functionality
try:
    import pytesseract
    from PIL import Image, ImageOps
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

# Try to import OpenCV for image preprocessing
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

# Common Tesseract installation paths to check
COMMON_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"C:\Tesseract-OCR\tesseract.exe",
]

# Check and set Tesseract path
def set_tesseract_path():
    """Try to set the Tesseract path automatically."""
    if not TESSERACT_AVAILABLE:
        return
        
    for path in COMMON_TESSERACT_PATHS:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            return True
    return False

# Try to set Tesseract path on module import
if TESSERACT_AVAILABLE:
    set_tesseract_path()


class DecisionPointDialog(QDialog):
    """Dialog for managing decision points."""
    
    def __init__(self, db_conn, story_id: int, parent=None):
        """Initialize the decision point dialog.
        
        Args:
            db_conn: Database connection
            story_id: ID of the story
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.story_id = story_id
        self.decision_point_id = None
        self.options_list = []
        self.current_image: Optional[QImage] = None
        
        self.setWindowTitle("Add decision point")
        self.setMinimumWidth(600)
        self.setMinimumHeight(600)
        
        self.init_ui()
    
    def init_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create tabs for decision points and OCR
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Decision Point tab
        decision_tab = QWidget()
        decision_layout = QVBoxLayout(decision_tab)
        
        # Decision point title
        title_layout = QHBoxLayout()
        title_label = QLabel("Decision point:")
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Enter decision point title")
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.title_edit)
        decision_layout.addLayout(title_layout)
        
        # Add option button
        self.add_option_button = QPushButton("Add option")
        self.add_option_button.clicked.connect(self.on_add_option)
        decision_layout.addWidget(self.add_option_button)
        
        # Options group
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)
        
        # Options list (with radio buttons)
        self.options_container = QWidget()
        self.options_container_layout = QVBoxLayout(self.options_container)
        self.options_container_layout.setContentsMargins(0, 0, 0, 0)
        self.options_container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Add options container to a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.options_container)
        
        options_layout.addWidget(scroll_area)
        decision_layout.addWidget(options_group)
        
        # Add the decision tab
        self.tab_widget.addTab(decision_tab, "Decision Point")
        
        # OCR Tab
        ocr_tab = QWidget()
        ocr_layout = QVBoxLayout(ocr_tab)
        
        # Create a splitter to separate image and text areas
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Image area widget
        image_widget = QWidget()
        image_layout = QVBoxLayout(image_widget)
        
        # Image display
        self.image_label = QLabel("Paste an image (Ctrl+V) to start")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumHeight(200)
        self.image_label.setStyleSheet("background-color: #222; color: #fff; border: 1px solid #444;")
        image_layout.addWidget(self.image_label)
        
        # OCR Controls
        controls_layout = QHBoxLayout()
        
        # Paste button
        self.paste_button = QPushButton("Paste Image (Ctrl+V)")
        self.paste_button.clicked.connect(self.paste_image)
        controls_layout.addWidget(self.paste_button)
        
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

        # Add option for adding white background
        self.add_background_check = QCheckBox("Add White Background")
        self.add_background_check.setChecked(True)
        self.add_background_check.setToolTip("Add a white background to transparent images")
        options_layout.addWidget(self.add_background_check)
        
        image_layout.addWidget(options_group)
        
        splitter.addWidget(image_widget)
        
        # Text area widget
        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        
        # Text output
        text_layout.addWidget(QLabel("Extracted Text:"))
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(False)  # Allow editing to facilitate text selection
        text_layout.addWidget(self.text_edit)
        
        # Text controls
        text_controls = QHBoxLayout()
        
        # Copy text button
        self.copy_button = QPushButton("Copy Text (Ctrl+C)")
        self.copy_button.clicked.connect(self.copy_text)
        self.copy_button.setEnabled(False)
        text_controls.addWidget(self.copy_button)
        
        # Add as option button
        self.add_as_option_button = QPushButton("Add Selection as Option")
        self.add_as_option_button.clicked.connect(self.add_selection_as_option)
        self.add_as_option_button.setEnabled(False)
        text_controls.addWidget(self.add_as_option_button)
        
        # Clear button
        self.clear_button = QPushButton("Clear (Ctrl+X)")
        self.clear_button.clicked.connect(self.clear_ocr)
        text_controls.addWidget(self.clear_button)
        
        text_layout.addLayout(text_controls)
        
        splitter.addWidget(text_widget)
        
        # Add the splitter to the OCR tab layout
        ocr_layout.addWidget(splitter)
        
        # Add the OCR tab
        self.tab_widget.addTab(ocr_tab, "OCR Tool")
        
        # Set up OCR keyboard shortcuts
        self.setup_ocr_shortcuts()
        
        # Connect text edit's text changed signal
        self.text_edit.textChanged.connect(self.on_text_changed)
        self.text_edit.selectionChanged.connect(self.on_selection_changed)
        
        # Buttons layout for main dialog
        buttons_layout = QHBoxLayout()
        
        # Add save button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.save_button)
        
        # Add cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(buttons_layout)
    
    def setup_ocr_shortcuts(self):
        """Set up keyboard shortcuts for OCR functionality."""
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
        clear_shortcut = QAction("Clear", self)
        clear_shortcut.setShortcut(QKeySequence("Ctrl+X"))
        clear_shortcut.triggered.connect(self.clear_ocr)
        self.addAction(clear_shortcut)
    
    def paste_image(self):
        """Paste image from clipboard."""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasImage():
            self.current_image = QImage(clipboard.image())
            self.display_image()
            self.ocr_button.setEnabled(True)
            # Switch to the OCR tab if we're not already there
            if self.tab_widget.currentIndex() != 1:
                self.tab_widget.setCurrentIndex(1)
        else:
            QMessageBox.information(
                self,
                "No Image Found",
                "No image found in clipboard. Copy an image and try again."
            )
    
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

    def add_white_background(self, image):
        """Add a white background to an image with transparency."""
        if not TESSERACT_AVAILABLE:
            return image
            
        try:
            # Convert QImage to PIL Image
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.ReadWrite)
            image.save(buffer, "PNG")
            bytes_data = buffer.data().data()
            
            pil_img = Image.open(io.BytesIO(bytes_data))
            
            # Check if image has an alpha channel
            if pil_img.mode in ('RGBA', 'LA') or (pil_img.mode == 'P' and 'transparency' in pil_img.info):
                # Create a white background image of the same size
                background = Image.new('RGBA', pil_img.size, (255, 255, 255, 255))
                # Alpha composite the original image over the background
                composite = Image.alpha_composite(background.convert('RGBA'), pil_img.convert('RGBA'))
                # Convert back to RGB (no alpha)
                pil_img = composite.convert('RGB')
            
            # Convert back to QImage
            img_bytes = io.BytesIO()
            pil_img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            # Create QImage from bytes
            qimg = QImage()
            qimg.loadFromData(img_bytes.getvalue())
            
            return qimg
        except Exception as e:
            print(f"Error adding white background: {e}")
            return image
    
    def preprocess_image(self, image):
        """Apply preprocessing to the image for better OCR results."""
        if not OPENCV_AVAILABLE:
            return image
            
        try:
            # Convert QImage to numpy array
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.ReadWrite)
            image.save(buffer, "PNG")
            bytes_data = buffer.data().data()
            
            nparr = np.frombuffer(bytes_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Increase contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            gray = clahe.apply(gray)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY_INV if self.is_dark_text(img) else cv2.THRESH_BINARY, 
                11, 2
            )
            
            # Optional: Apply noise removal
            kernel = np.ones((1, 1), np.uint8)
            opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
            
            # Convert back to QImage
            h, w = opening.shape
            bytes_per_line = w
            q_img = QImage(opening.data, w, h, bytes_per_line, QImage.Format.Format_Grayscale8)
            
            return q_img
        except Exception as e:
            print(f"Error during image preprocessing: {e}")
            return image
    
    def is_dark_text(self, img):
        """Determine if the image has dark text on light background or vice versa."""
        try:
            # Calculate the mean brightness of the image
            mean_brightness = np.mean(img)
            # If the image is generally bright, text is likely dark
            return mean_brightness > 127
        except:
            return True  # Default to assuming dark text
    
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
                "Tesseract Not Found",
                "pytesseract library is not installed or Tesseract OCR is not configured properly.\n\n"
                "Please install pytesseract and Tesseract OCR to use this feature."
            )
            return
        
        try:
            # Apply preprocessing if needed
            img = self.current_image
            
            # Add white background for transparent images if checked
            if self.add_background_check.isChecked():
                img = self.add_white_background(img)
            
            # Apply preprocessing if checked
            if self.preprocess_check.isChecked() and OPENCV_AVAILABLE:
                img = self.preprocess_image(img)
            
            # Convert QImage to format suitable for pytesseract
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.ReadWrite)
            img.save(buffer, "PNG")
            bytes_data = buffer.data().data()
            
            # OCR configuration - English language only
            config = ""
            if self.line_mode_check.isChecked():
                config = "--psm 7"  # Treat the image as a single line of text
            
            # Perform OCR
            pil_img = Image.open(io.BytesIO(bytes_data))
            text = pytesseract.image_to_string(pil_img, lang="eng", config=config)
            
            # Display the results
            if text.strip():
                self.text_edit.setPlainText(text)
                self.copy_button.setEnabled(True)
                self.add_as_option_button.setEnabled(True)
            else:
                self.text_edit.setPlainText("No text detected in the image.")
                self.copy_button.setEnabled(False)
                self.add_as_option_button.setEnabled(False)
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "OCR Error",
                f"An error occurred during OCR:\n{str(e)}"
            )
    
    def copy_text(self):
        """Copy the extracted text to clipboard."""
        text = self.text_edit.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copy", "Text copied to clipboard", QMessageBox.StandardButton.Ok)
    
    def on_text_changed(self):
        """Handler for when the text in the text edit changes."""
        # Enable or disable buttons based on whether there's text
        has_text = bool(self.text_edit.toPlainText().strip())
        self.copy_button.setEnabled(has_text)
    
    def on_selection_changed(self):
        """Handler for when the text selection changes."""
        # Enable the "Add as Option" button only when text is selected
        cursor = self.text_edit.textCursor()
        has_selection = cursor.hasSelection()
        self.add_as_option_button.setEnabled(has_selection)
    
    def add_selection_as_option(self):
        """Add the currently selected text as a decision option."""
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText().strip()
            if selected_text:
                # Switch to the Decision Point tab
                self.tab_widget.setCurrentIndex(0)
                # Add the selected text as an option
                self.add_option(selected_text)
                QMessageBox.information(
                    self,
                    "Option Added",
                    f"Added \"{selected_text}\" as a decision option.",
                    QMessageBox.StandardButton.Ok
                )
            else:
                QMessageBox.warning(
                    self,
                    "Empty Selection",
                    "Please select some text to add as an option.",
                    QMessageBox.StandardButton.Ok
                )
        else:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select some text to add as an option.",
                QMessageBox.StandardButton.Ok
            )
    
    def clear_ocr(self):
        """Clear the OCR image and text."""
        self.current_image = None
        self.image_label.clear()
        self.image_label.setText("Paste an image (Ctrl+V) to start")
        self.text_edit.clear()
        self.ocr_button.setEnabled(False)
        self.copy_button.setEnabled(False)
        self.add_as_option_button.setEnabled(False)
    
    def on_add_option(self):
        """Handle add option button click."""
        option_text, ok = QInputDialog.getText(self, "Add Option", "Enter option text:")
        if ok and option_text.strip():
            self.add_option(option_text)
    
    def add_option(self, option_text: str, is_selected: bool = False):
        """Add an option to the list.
        
        Args:
            option_text: Text of the option
            is_selected: Whether the option is selected
        """
        # Create a container for the option and its radio button
        option_container = QWidget()
        option_layout = QHBoxLayout(option_container)
        option_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create a radio button for the option
        radio_button = QRadioButton(option_text)
        radio_button.setChecked(is_selected)
        option_layout.addWidget(radio_button)
        
        # Add the container to the options layout
        self.options_container_layout.addWidget(option_container)
        
        # Add the option to the list
        self.options_list.append({
            "text": option_text,
            "radio_button": radio_button,
            "container": option_container,
            "is_selected": is_selected
        })
    
    def get_selected_option_index(self) -> int:
        """Get the index of the selected option.
        
        Returns:
            Index of the selected option, or -1 if none is selected
        """
        for i, option in enumerate(self.options_list):
            if option["radio_button"].isChecked():
                return i
        return -1
    
    def get_next_decision_point_number(self) -> int:
        """Get the next sequential decision point number for the current story.
        
        Returns:
            Next sequential number for a default decision point title
        """
        from app.db_sqlite import get_story_decision_points
        
        try:
            # Get all decision points for the story
            decision_points = get_story_decision_points(self.db_conn, self.story_id)
            
            # Find the highest number used in a default title
            default_prefix = "Decision Point "
            max_number = 0
            
            for dp in decision_points:
                title = dp.get("title", "")
                if title.startswith(default_prefix):
                    try:
                        num_str = title[len(default_prefix):]
                        num = int(num_str)
                        max_number = max(max_number, num)
                    except ValueError:
                        # Not a numbered decision point
                        pass
            
            # Return the next number in sequence
            return max_number + 1
        except Exception as e:
            print(f"Error getting next decision point number: {e}")
            return 1  # Start with 1 if there's any error
    
    def accept(self):
        """Handle dialog acceptance (save)."""
        # Make sure we're on the decision point tab
        self.tab_widget.setCurrentIndex(0)
        
        title = self.title_edit.text().strip()
        if not title:
            # Generate a default title with sequential numbering
            next_number = self.get_next_decision_point_number()
            title = f"Decision Point {next_number}"
        
        if not self.options_list:
            QMessageBox.warning(self, "Error", "Please add at least one option.")
            return
        
        selected_index = self.get_selected_option_index()
        if selected_index == -1:
            QMessageBox.warning(self, "Error", "Please select one of the options.")
            return
        
        # Save the decision point and options to the database
        try:
            from app.db_sqlite import (
                create_decision_point, add_decision_option, select_decision_option
            )
            
            # Create the decision point
            decision_point_id = create_decision_point(self.db_conn, title, self.story_id)
            
            # Add the options
            for i, option in enumerate(self.options_list):
                option_id = add_decision_option(
                    self.db_conn, 
                    decision_point_id, 
                    option["text"],
                    option["radio_button"].isChecked(),
                    i
                )
            
            # Store the decision point ID
            self.decision_point_id = decision_point_id
            
            # Close the dialog
            super().accept()
            
        except Exception as e:
            print(f"Error saving decision point: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save decision point: {str(e)}")
    
    def resizeEvent(self, event):
        """Handle resize events to update the image display."""
        super().resizeEvent(event)
        if self.current_image and not self.current_image.isNull():
            self.display_image() 