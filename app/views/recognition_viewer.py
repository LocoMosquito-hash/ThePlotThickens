#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Recognition Database Viewer for The Plot Thickens application.

This module provides a visualization interface for the image recognition database.
"""

import os
import json
import sqlite3
from typing import Dict, List, Any, Optional, Tuple

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QSplitter, QWidget, QTabWidget,
    QScrollArea, QGridLayout, QFileDialog, QMessageBox, QProgressBar,
    QComboBox, QGroupBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QPainter, QColor, QBrush, QPen, QImage, QDragEnterEvent, QDropEvent, QIcon

from app.utils.image_recognition_util import ImageRecognitionUtil


class HistogramWidget(QWidget):
    """Widget to display a color histogram."""
    
    def __init__(self, histogram: List[float], parent=None) -> None:
        """Initialize the histogram widget.
        
        Args:
            histogram: Color histogram data (64 bins for 4x4x4 RGB)
            parent: Parent widget
        """
        super().__init__(parent)
        self.histogram = histogram
        self.setMinimumSize(256, 100)
        
    def paintEvent(self, event) -> None:
        """Paint the histogram.
        
        Args:
            event: Paint event
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), QColor(240, 240, 240))
        
        if not self.histogram or len(self.histogram) != 64:
            # Draw error message if histogram is invalid
            painter.setPen(QColor(255, 0, 0))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Invalid histogram data")
            return
            
        # Find max value for scaling
        max_value = max(self.histogram) if self.histogram else 1.0
        
        # Draw each bin
        bin_width = self.width() / 64
        for i, value in enumerate(self.histogram):
            # Calculate bin position and height
            x = i * bin_width
            height = (value / max_value) * self.height() * 0.9
            y = self.height() - height
            
            # Calculate RGB color for this bin
            r = (i // 16) * 85
            g = ((i // 4) % 4) * 85
            b = (i % 4) * 85
            
            # Draw bin
            painter.fillRect(
                int(x), int(y),
                int(bin_width), int(height),
                QColor(r, g, b)
            )
            
        # Draw border
        painter.setPen(QColor(0, 0, 0))
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)


class FeatureDisplayWidget(QWidget):
    """Widget to display image features and histogram."""
    
    def __init__(self, features: Dict[str, Any], parent=None) -> None:
        """Initialize the feature display widget.
        
        Args:
            features: Image features dictionary
            parent: Parent widget
        """
        super().__init__(parent)
        self.features = features
        
        layout = QVBoxLayout(self)
        
        # Create grid for feature values
        feature_grid = QGridLayout()
        
        # Add basic features
        row = 0
        for key, value in features["features"].items():
            feature_grid.addWidget(QLabel(f"{key}:"), row, 0)
            feature_grid.addWidget(QLabel(f"{value:.4f}" if isinstance(value, float) else str(value)), row, 1)
            row += 1
        
        feature_group = QGroupBox("Feature Values")
        feature_group.setLayout(feature_grid)
        layout.addWidget(feature_group)
        
        # Add histogram
        histogram_label = QLabel("Color Histogram:")
        layout.addWidget(histogram_label)
        
        self.histogram_widget = HistogramWidget(features["color_histogram"])
        layout.addWidget(self.histogram_widget)
        
        layout.addStretch()


class RecognitionDatabaseViewer(QDialog):
    """Dialog for visualizing the image recognition database."""
    
    def __init__(self, db_conn: sqlite3.Connection, parent=None) -> None:
        """Initialize the recognition database viewer.
        
        Args:
            db_conn: Database connection
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.image_recognition = ImageRecognitionUtil(db_conn)
        
        self.setWindowTitle("Recognition Database Viewer")
        self.resize(1000, 700)
        
        self.init_ui()
        self.load_characters()
        
    def init_ui(self) -> None:
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        
        # Create splitter for left (characters) and right (details) panels
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)
        
        # Left panel - Characters list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Create filter for story
        story_layout = QHBoxLayout()
        story_layout.addWidget(QLabel("Filter by Story:"))
        
        self.story_combo = QComboBox()
        self.story_combo.currentIndexChanged.connect(self.on_story_selected)
        story_layout.addWidget(self.story_combo)
        
        left_layout.addLayout(story_layout)
        
        # Create character list
        self.character_list = QListWidget()
        self.character_list.setIconSize(QSize(40, 40))
        self.character_list.currentItemChanged.connect(self.on_character_selected)
        left_layout.addWidget(QLabel("Characters:"))
        left_layout.addWidget(self.character_list)
        
        # Create rebuild button
        self.rebuild_button = QPushButton("Rebuild Recognition Database")
        self.rebuild_button.clicked.connect(self.on_rebuild_database)
        left_layout.addWidget(self.rebuild_button)
        
        # Add left panel to splitter
        self.splitter.addWidget(left_panel)
        
        # Right panel - Features and test area
        right_panel = QTabWidget()
        
        # Features tab
        self.features_tab = QScrollArea()
        self.features_tab.setWidgetResizable(True)
        self.features_widget = QWidget()
        self.features_layout = QVBoxLayout(self.features_widget)
        self.features_tab.setWidget(self.features_widget)
        right_panel.addTab(self.features_tab, "Features")
        
        # Test Recognition tab
        self.test_tab = QWidget()
        test_layout = QVBoxLayout(self.test_tab)
        
        # Instructions
        test_layout.addWidget(QLabel("Drop an image here or click browse to test recognition:"))
        
        # Browse button
        browse_layout = QHBoxLayout()
        self.browse_button = QPushButton("Browse for Image...")
        self.browse_button.clicked.connect(self.on_browse_image)
        browse_layout.addWidget(self.browse_button)
        browse_layout.addStretch()
        test_layout.addLayout(browse_layout)
        
        # Test image display
        self.test_image_label = QLabel("No image loaded")
        self.test_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.test_image_label.setMinimumHeight(200)
        self.test_image_label.setStyleSheet("border: 1px solid #ccc;")
        test_layout.addWidget(self.test_image_label)
        
        # Results list
        test_layout.addWidget(QLabel("Recognition Results:"))
        self.results_list = QListWidget()
        test_layout.addWidget(self.results_list)
        
        right_panel.addTab(self.test_tab, "Test Recognition")
        
        # Add right panel to splitter
        self.splitter.addWidget(right_panel)
        
        # Set stretch factors for the splitter
        self.splitter.setSizes([300, 700])
        
        # Enable drag and drop for the test tab
        self.test_tab.setAcceptDrops(True)
        # Override dragEnterEvent and dropEvent
        self.test_tab.dragEnterEvent = self.dragEnterEvent
        self.test_tab.dropEvent = self.dropEvent
        
        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Add close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        main_layout.addLayout(button_layout)
        
    def load_stories(self) -> None:
        """Load stories into the combo box."""
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT id, title FROM stories ORDER BY title")
        stories = cursor.fetchall()
        
        # Clear and add "All Stories" option
        self.story_combo.clear()
        self.story_combo.addItem("All Stories", None)
        
        # Add stories
        for story in stories:
            self.story_combo.addItem(story["title"], story["id"])
    
    def load_characters(self, story_id: Optional[int] = None) -> None:
        """Load characters with avatars.
        
        Args:
            story_id: Optional story ID to filter by
        """
        self.character_list.clear()
        
        cursor = self.db_conn.cursor()
        
        # Get all characters with avatars
        if story_id:
            cursor.execute('''
            SELECT id, name, avatar_path 
            FROM characters 
            WHERE avatar_path IS NOT NULL AND avatar_path != '' AND story_id = ?
            ORDER BY name
            ''', (story_id,))
        else:
            cursor.execute('''
            SELECT id, name, avatar_path 
            FROM characters 
            WHERE avatar_path IS NOT NULL AND avatar_path != ''
            ORDER BY name
            ''')
        
        characters = cursor.fetchall()
        
        # Get image features for each character
        feature_counts = self._get_feature_counts()
        
        # Add to list
        for character in characters:
            char_id = character["id"]
            name = character["name"]
            avatar_path = character["avatar_path"]
            
            # Create item
            item = QListWidgetItem(f"{name} ({feature_counts.get(char_id, 0)} features)")
            item.setData(Qt.ItemDataRole.UserRole, char_id)
            
            # Set avatar icon if it exists
            if os.path.exists(avatar_path):
                pixmap = QPixmap(avatar_path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio)
                    item.setIcon(QIcon(pixmap))
            
            self.character_list.addItem(item)
    
    def _get_feature_counts(self) -> Dict[int, int]:
        """Get count of features for each character.
        
        Returns:
            Dictionary mapping character ID to feature count
        """
        cursor = self.db_conn.cursor()
        cursor.execute('''
        SELECT character_id, COUNT(*) as count
        FROM image_features
        GROUP BY character_id
        ''')
        
        return {row["character_id"]: row["count"] for row in cursor.fetchall()}
    
    def on_story_selected(self) -> None:
        """Handle story selection change."""
        story_id = self.story_combo.currentData()
        self.load_characters(story_id)
    
    def on_character_selected(self, current: QListWidgetItem, previous: QListWidgetItem) -> None:
        """Handle character selection.
        
        Args:
            current: Currently selected item
            previous: Previously selected item
        """
        if not current:
            return
        
        # Clear features panel
        while self.features_layout.count():
            item = self.features_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get character ID
        character_id = current.data(Qt.ItemDataRole.UserRole)
        
        # Get character info
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT name, avatar_path FROM characters WHERE id = ?", (character_id,))
        character = cursor.fetchone()
        
        if not character:
            return
        
        # Display character info
        char_name = character["name"]
        avatar_path = character["avatar_path"]
        
        # Add character header
        header_layout = QHBoxLayout()
        
        # Add avatar
        avatar_label = QLabel()
        if os.path.exists(avatar_path):
            pixmap = QPixmap(avatar_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio)
                avatar_label.setPixmap(pixmap)
        
        header_layout.addWidget(avatar_label)
        
        # Add name
        name_label = QLabel(f"<h2>{char_name}</h2>")
        header_layout.addWidget(name_label)
        header_layout.addStretch()
        
        self.features_layout.addLayout(header_layout)
        
        # Get features for this character
        character_features = self.image_recognition.get_character_image_features(character_id)
        
        if character_id not in character_features or not character_features[character_id]:
            self.features_layout.addWidget(QLabel("No image features found for this character."))
            return
        
        # Add feature displays
        for i, feature_data in enumerate(character_features[character_id]):
            # Create group box for each feature set
            group_box = QGroupBox(f"Feature Set {i+1}")
            feature_display = FeatureDisplayWidget(feature_data)
            group_layout = QVBoxLayout(group_box)
            group_layout.addWidget(feature_display)
            
            self.features_layout.addWidget(group_box)
        
        # Add stretch to bottom
        self.features_layout.addStretch()
    
    def on_rebuild_database(self) -> None:
        """Handle rebuild database button click."""
        # Get the selected story ID (None for All Stories)
        selected_story_id = self.story_combo.currentData()
        
        # Prepare a message based on whether we're rebuilding for all stories or just one
        if selected_story_id is None:
            message = "Are you sure you want to rebuild the ENTIRE recognition database? This will regenerate all image features from character avatars and tagged regions for ALL stories."
        else:
            story_name = self.story_combo.currentText()
            message = f"Are you sure you want to rebuild the recognition database for \"{story_name}\"? This will regenerate image features only for this story."
        
        reply = QMessageBox.question(
            self,
            "Rebuild Recognition Database",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Show progress
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(20)
            
            # Rebuild database for the selected story or all stories
            try:
                self.image_recognition.build_character_image_database(story_id=selected_story_id)
                
                # Update UI
                self.progress_bar.setValue(100)
                self.load_characters(self.story_combo.currentData())
                
                # Show success message
                if selected_story_id is None:
                    QMessageBox.information(self, "Database Rebuilt", "The complete recognition database has been successfully rebuilt.")
                else:
                    story_name = self.story_combo.currentText()
                    QMessageBox.information(self, "Database Rebuilt", f"The recognition database for \"{story_name}\" has been successfully rebuilt.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to rebuild recognition database: {str(e)}")
            finally:
                # Hide progress bar
                self.progress_bar.setVisible(False)
    
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter event.
        
        Args:
            event: Drag enter event
        """
        # Accept event if it's a URL (file)
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop event.
        
        Args:
            event: Drop event
        """
        # Get the first URL
        urls = event.mimeData().urls()
        if urls:
            # Get the local path
            file_path = urls[0].toLocalFile()
            
            # Process the image
            self.test_recognition(file_path)
    
    def on_browse_image(self) -> None:
        """Handle browse image button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if file_path:
            self.test_recognition(file_path)
    
    def test_recognition(self, image_path: str) -> None:
        """Test recognition on an image.
        
        Args:
            image_path: Path to the image file
        """
        if not os.path.exists(image_path):
            QMessageBox.warning(self, "Error", f"Image file not found: {image_path}")
            return
        
        try:
            # Display the image
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Scale for display
                scaled_pixmap = pixmap.scaled(
                    400, 300,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.test_image_label.setPixmap(scaled_pixmap)
            
            # Extract features
            features = self.image_recognition.extract_features_from_path(image_path)
            
            # Run recognition
            story_id = self.story_combo.currentData()  # May be None for all stories
            results = self.image_recognition.identify_characters_in_image(
                features, 
                threshold=0.5,  # Lower threshold for testing
                story_id=story_id
            )
            
            # Display results
            self.results_list.clear()
            
            if not results:
                self.results_list.addItem("No matches found")
                return
            
            for result in results:
                char_name = result["character_name"]
                similarity = result["similarity"]
                item = QListWidgetItem(f"{char_name}: {similarity:.2f} similarity")
                
                # Get avatar for this character
                char_id = result["character_id"]
                cursor = self.db_conn.cursor()
                cursor.execute("SELECT avatar_path FROM characters WHERE id = ?", (char_id,))
                avatar = cursor.fetchone()
                
                if avatar and avatar["avatar_path"] and os.path.exists(avatar["avatar_path"]):
                    pixmap = QPixmap(avatar["avatar_path"])
                    if not pixmap.isNull():
                        pixmap = pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio)
                        item.setIcon(QIcon(pixmap))
                
                self.results_list.addItem(item)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to process image: {str(e)}")

    def showEvent(self, event) -> None:
        """Handle show event to initialize data.
        
        Args:
            event: Show event
        """
        super().showEvent(event)
        # Load stories - do this on show to get the latest data
        self.load_stories() 