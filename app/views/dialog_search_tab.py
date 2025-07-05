#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dialog Search Tab for The Plot Thickens application.

This module provides the Dialog Search tab widget that integrates
Ren'Py source code analysis for searching dialogue and displaying
associated visual media in a spoiler-free manner.
"""

import os
import sys
from typing import Optional, Dict, Any, List
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, 
    QTableWidget, QTableWidgetItem, QGroupBox, QProgressBar, QMessageBox,
    QGridLayout, QScrollArea, QFrame, QSizePolicy, QHeaderView
)
from PyQt6.QtCore import Qt, QSettings, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QPixmap

from app.utils.icons import icon_manager


class DialogSearchWorker(QThread):
    """Worker thread for performing dialogue search in the background."""
    
    # Signals
    progress_updated = pyqtSignal(int)  # Progress percentage (0-100)
    status_updated = pyqtSignal(str)   # Status message
    search_completed = pyqtSignal(list)  # Search results
    search_failed = pyqtSignal(str)  # Error message
    
    def __init__(self, source_path: str, search_query: str, parent=None):
        """Initialize the worker thread.
        
        Args:
            source_path: Path to the Ren'Py source code directory
            search_query: Text to search for in dialogue
            parent: Parent widget
        """
        super().__init__(parent)
        self.source_path = source_path
        self.search_query = search_query
        self._is_cancelled = False
        
    def run(self):
        """Run the dialogue search."""
        try:
            self.status_updated.emit("Initializing search...")
            self.progress_updated.emit(10)
            
            # Import the Ren'Py API here using path manipulation
            api_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'renpy-source-api')
            if api_dir not in sys.path:
                sys.path.insert(0, api_dir)
            
            from core import RenpyProject
            
            if self._is_cancelled:
                return
                
            self.status_updated.emit("Loading project...")
            self.progress_updated.emit(25)
            
            # Initialize the project
            project = RenpyProject(self.source_path)
            
            if self._is_cancelled:
                return
                
            self.status_updated.emit("Analyzing source files...")
            self.progress_updated.emit(50)
            
            # Ensure project is analyzed
            if not project.is_analyzed:
                project.analyze()
            
            if self._is_cancelled:
                return
                
            self.status_updated.emit("Searching dialogue...")
            self.progress_updated.emit(75)
            
            # Search for dialogue
            dialogue_matches = project.search_dialogue(self.search_query, case_sensitive=False)
            
            if self._is_cancelled:
                return
                
            self.status_updated.emit("Processing results...")
            self.progress_updated.emit(90)
            
            # Process and enhance results
            enhanced_results = []
            for match in dialogue_matches:
                # Add current label context (this will be used for media counting later)
                enhanced_match = {
                    'character': match.get('speaker', 'Unknown'),
                    'dialogue': match.get('dialogue', ''),
                    'label': 'Unknown',  # We'll enhance this in later stages
                    'file': match.get('file', ''),
                    'line_number': match.get('line_number', 0),
                    'media_count': 0  # Placeholder for Stage 4
                }
                enhanced_results.append(enhanced_match)
            
            # Sort by file and line number as requested
            enhanced_results.sort(key=lambda x: (x['file'], x['line_number']))
            
            self.progress_updated.emit(100)
            self.status_updated.emit(f"Found {len(enhanced_results)} matches")
            
            self.search_completed.emit(enhanced_results)
            
        except Exception as e:
            self.search_failed.emit(f"Search failed: {str(e)}")
    
    def cancel(self):
        """Cancel the search."""
        self._is_cancelled = True


class MinimalThumbnailWidget(QLabel):
    """A minimal thumbnail widget for displaying 320x320px images."""
    
    def __init__(self, parent=None):
        """Initialize the thumbnail widget."""
        super().__init__(parent)
        self.setFixedSize(320, 320)
        self.setScaledContents(True)
        self.setStyleSheet("""
            MinimalThumbnailWidget {
                border: 2px solid #666;
                border-radius: 8px;
                background-color: #f0f0f0;
            }
        """)
        self.setText("No Image")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
    def set_image(self, image_path: str):
        """Set the image for this thumbnail.
        
        Args:
            image_path: Path to the image file
        """
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Scale to fit 320x320 while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    320, 320, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                self.setPixmap(scaled_pixmap)
                self.setText("")
            else:
                self.setText("Invalid Image")
        else:
            self.setText("Image Not Found")


class DialogSearchTab(QWidget):
    """Dialog Search tab for searching Ren'Py dialogue and displaying associated media."""
    
    def __init__(self, db_conn, parent=None):
        """Initialize the dialog search tab.
        
        Args:
            db_conn: Database connection
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.story_id: Optional[int] = None
        self.settings = QSettings("ThePlotThickens", "ThePlotThickens")
        self.search_worker: Optional[DialogSearchWorker] = None
        self.search_results: List[Dict[str, Any]] = []
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Source Status Section
        self.create_source_status_section(layout)
        
        # Search Section
        self.create_search_section(layout)
        
        # Results Section 
        self.create_results_section(layout)
        
        # Minimal Gallery Section
        self.create_minimal_gallery_section(layout)
        
    def create_source_status_section(self, layout: QVBoxLayout):
        """Create the source analysis status section.
        
        Args:
            layout: Layout to add the section to
        """
        status_group = QGroupBox("Source Analysis Status")
        status_layout = QVBoxLayout(status_group)
        
        self.source_status_label = QLabel()
        self.source_status_label.setWordWrap(True)
        status_layout.addWidget(self.source_status_label)
        
        layout.addWidget(status_group)
        
    def create_search_section(self, layout: QVBoxLayout):
        """Create the search input section.
        
        Args:
            layout: Layout to add the section to
        """
        search_group = QGroupBox("Dialogue Search")
        search_layout = QVBoxLayout(search_group)
        
        # Search input row
        input_layout = QHBoxLayout()
        
        input_layout.addWidget(QLabel("Search text:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter dialogue text to find in the script...")
        self.search_input.returnPressed.connect(self.perform_search)
        input_layout.addWidget(self.search_input)
        
        self.search_button = QPushButton("Search")
        self.search_button.setIcon(icon_manager.get_icon("search"))
        self.search_button.clicked.connect(self.perform_search)
        input_layout.addWidget(self.search_button)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.setIcon(icon_manager.get_icon("x"))
        self.clear_button.clicked.connect(self.clear_search)
        input_layout.addWidget(self.clear_button)
        
        search_layout.addLayout(input_layout)
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        search_layout.addWidget(self.progress_bar)
        
        # Status label
        self.search_status_label = QLabel("Ready to search")
        self.search_status_label.setStyleSheet("color: #666; font-style: italic;")
        search_layout.addWidget(self.search_status_label)
        
        layout.addWidget(search_group)
        
    def create_results_section(self, layout: QVBoxLayout):
        """Create the search results table section.
        
        Args:
            layout: Layout to add the section to
        """
        results_group = QGroupBox("Search Results")
        results_layout = QVBoxLayout(results_group)
        
        # Results count
        self.results_count_label = QLabel("0 matches found")
        self.results_count_label.setStyleSheet("color: #666; font-style: italic;")
        results_layout.addWidget(self.results_count_label)
        
        # Results table
        self.results_table = QTableWidget(0, 5)
        self.results_table.setHorizontalHeaderLabels([
            "Character", "Dialogue", "Label", "File", "Media Count"
        ])
        
        # Configure table
        header = self.results_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Character
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)           # Dialogue  
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Label
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # File
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Media Count
        
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.results_table.setAlternatingRowColors(True)
        
        # Connect selection changed signal
        self.results_table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        
        results_layout.addWidget(self.results_table)
        layout.addWidget(results_group)
        
    def create_minimal_gallery_section(self, layout: QVBoxLayout):
        """Create the minimal thumbnail gallery section.
        
        Args:
            layout: Layout to add the section to
        """
        gallery_group = QGroupBox("Associated Media")
        gallery_layout = QVBoxLayout(gallery_group)
        
        # Gallery info
        self.gallery_info_label = QLabel("Select a dialogue result to view associated media")
        self.gallery_info_label.setStyleSheet("color: #666; font-style: italic;")
        gallery_layout.addWidget(self.gallery_info_label)
        
        # Scroll area for thumbnails
        self.gallery_scroll = QScrollArea()
        self.gallery_scroll.setWidgetResizable(True)
        self.gallery_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.gallery_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Container widget for thumbnails
        self.gallery_widget = QWidget()
        self.gallery_layout = QGridLayout(self.gallery_widget)
        self.gallery_layout.setSpacing(10)
        self.gallery_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        self.gallery_scroll.setWidget(self.gallery_widget)
        gallery_layout.addWidget(self.gallery_scroll)
        
        layout.addWidget(gallery_group)
        
    def set_story(self, story_id: int, story_data: Dict[str, Any]):
        """Set the current story for analysis.
        
        Args:
            story_id: ID of the story
            story_data: Story data dictionary
        """
        self.story_id = story_id
        self.update_source_status()
        self.update_search_ui_state()
        
    def update_source_status(self):
        """Update the source analysis status indicator."""
        if not self.story_id:
            self.source_status_label.setText("❌ No story selected")
            self.source_status_label.setStyleSheet("color: #cc0000; font-weight: bold;")
            return
            
        source_path = self.settings.value(f"story_{self.story_id}/source_path", "")
        
        if source_path and source_path.strip():
            if os.path.exists(source_path):
                # Check for .rpy files
                rpy_count = 0
                try:
                    for root, dirs, files in os.walk(source_path):
                        rpy_count += len([f for f in files if f.endswith('.rpy')])
                except Exception:
                    rpy_count = 0
                
                if rpy_count > 0:
                    self.source_status_label.setText(
                        f"✅ Source analysis available\n"
                        f"📁 Path: {source_path}\n"
                        f"📄 Found {rpy_count} .rpy files"
                    )
                    self.source_status_label.setStyleSheet("color: #2d8f2d; font-weight: bold;")
                    self.source_analysis_available = True
                else:
                    self.source_status_label.setText(
                        f"⚠️ No .rpy files found in configured path\n"
                        f"📁 Path: {source_path}"
                    )
                    self.source_status_label.setStyleSheet("color: #cc7a00; font-weight: bold;")
                    self.source_analysis_available = False
            else:
                self.source_status_label.setText(
                    f"❌ Configured source path does not exist\n"
                    f"📁 Path: {source_path}"
                )
                self.source_status_label.setStyleSheet("color: #cc0000; font-weight: bold;")
                self.source_analysis_available = False
        else:
            self.source_status_label.setText(
                "❌ No source code path configured\n"
                "Please configure source path in the Setup tab"
            )
            self.source_status_label.setStyleSheet("color: #cc0000; font-weight: bold;")
            self.source_analysis_available = False
    
    def update_search_ui_state(self):
        """Update the search UI based on source analysis availability."""
        has_source = getattr(self, 'source_analysis_available', False)
        self.search_input.setEnabled(has_source)
        self.search_button.setEnabled(has_source)
        
        if not has_source:
            self.search_input.setPlaceholderText("Source analysis not available - configure in Setup tab")
            self.search_status_label.setText("Source analysis required for dialogue search")
        else:
            self.search_input.setPlaceholderText("Enter dialogue text to find in the script...")
            self.search_status_label.setText("Ready to search")
    
    def perform_search(self):
        """Perform the dialogue search."""
        search_text = self.search_input.text().strip()
        if not search_text:
            QMessageBox.warning(self, "Search", "Please enter text to search for.")
            return
        
        if not getattr(self, 'source_analysis_available', False):
            QMessageBox.warning(self, "Search", "Source analysis not available. Please configure source path in Setup tab.")
            return
        
        # Get source path
        source_path = self.settings.value(f"story_{self.story_id}/source_path", "")
        if not source_path or not source_path.strip():
            QMessageBox.warning(self, "Search", "No source path configured for this story.")
            return
        
        # Clear previous results
        self.clear_results()
        
        # Update UI
        self.search_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.search_status_label.setText("Searching...")
        
        # Start worker thread
        self.search_worker = DialogSearchWorker(source_path, search_text)
        self.search_worker.progress_updated.connect(self.progress_bar.setValue)
        self.search_worker.status_updated.connect(self.search_status_label.setText)
        self.search_worker.search_completed.connect(self.on_search_completed)
        self.search_worker.search_failed.connect(self.on_search_failed)
        self.search_worker.finished.connect(self.on_search_finished)
        
        self.search_worker.start()
        
    def clear_search(self):
        """Clear search input and results."""
        self.search_input.clear()
        self.clear_results()
        self.search_status_label.setText("Ready to search")
        
    def clear_results(self):
        """Clear search results and gallery."""
        self.results_table.setRowCount(0)
        self.search_results.clear()
        self.results_count_label.setText("0 matches found")
        self.clear_gallery()
        
    def clear_gallery(self):
        """Clear the thumbnail gallery."""
        # Remove all thumbnail widgets
        while self.gallery_layout.count():
            child = self.gallery_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self.gallery_info_label.setText("Select a dialogue result to view associated media")
        
    def on_search_completed(self, results: List[Dict[str, Any]]):
        """Handle successful search completion.
        
        Args:
            results: List of search result dictionaries
        """
        self.search_results = results
        self.populate_results_table(results)
        self.results_count_label.setText(f"{len(results)} matches found")
        
    def on_search_failed(self, error_message: str):
        """Handle search failure.
        
        Args:
            error_message: Error message to display
        """
        QMessageBox.critical(self, "Search Failed", error_message)
        self.search_status_label.setText("Search failed")
        
    def on_search_finished(self):
        """Handle search thread finishing (success or failure)."""
        self.search_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if self.search_worker:
            self.search_worker.deleteLater()
            self.search_worker = None
    
    def populate_results_table(self, results: List[Dict[str, Any]]):
        """Populate the results table with search results.
        
        Args:
            results: List of search result dictionaries
        """
        self.results_table.setRowCount(len(results))
        
        for row, result in enumerate(results):
            # Character
            character_item = QTableWidgetItem(result.get('character', 'Unknown'))
            self.results_table.setItem(row, 0, character_item)
            
            # Dialogue (truncated if too long)
            dialogue = result.get('dialogue', '')
            if len(dialogue) > 100:
                dialogue = dialogue[:97] + "..."
            dialogue_item = QTableWidgetItem(dialogue)
            dialogue_item.setToolTip(result.get('dialogue', ''))  # Full text in tooltip
            self.results_table.setItem(row, 1, dialogue_item)
            
            # Label
            label_item = QTableWidgetItem(result.get('label', 'Unknown'))
            self.results_table.setItem(row, 2, label_item)
            
            # File
            file_item = QTableWidgetItem(result.get('file', ''))
            self.results_table.setItem(row, 3, file_item)
            
            # Media Count
            media_count_item = QTableWidgetItem(str(result.get('media_count', 0)))
            self.results_table.setItem(row, 4, media_count_item)
    
    def on_selection_changed(self):
        """Handle table selection changes."""
        selected_rows = self.results_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            if 0 <= row < len(self.search_results):
                selected_result = self.search_results[row]
                self.update_gallery(selected_result)
        else:
            self.clear_gallery()
    
    def update_gallery(self, selected_result: Dict[str, Any]):
        """Update the gallery with associated media for the selected dialogue.
        
        Args:
            selected_result: The selected search result
        """
        # Clear existing gallery
        self.clear_gallery()
        
        # For Stage 1, just show placeholder
        self.gallery_info_label.setText(
            f"Selected: {selected_result.get('character', 'Unknown')} in {selected_result.get('label', 'Unknown')}\n"
            "Media discovery will be implemented in Stage 4"
        )
        
        # Add a placeholder thumbnail
        placeholder_thumbnail = MinimalThumbnailWidget()
        placeholder_thumbnail.setText("Media Discovery\nComing Soon")
        self.gallery_layout.addWidget(placeholder_thumbnail, 0, 0) 