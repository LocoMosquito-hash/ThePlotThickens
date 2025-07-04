#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Source Analysis Tab for The Plot Thickens application.

This module provides the Source Analysis tab widget that integrates
Ren'Py source code analysis capabilities into the main application.
"""

import os
import sys
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, 
    QPushButton, QLineEdit, QFileDialog, QTextEdit, QProgressBar,
    QMessageBox, QGroupBox, QFormLayout, QFrame
)
from PyQt6.QtCore import Qt, QSettings, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from app.utils.icons import icon_manager


class SourceAnalysisWorker(QThread):
    """Worker thread for running source code analysis in the background."""
    
    # Signals
    progress_updated = pyqtSignal(int)  # Progress percentage (0-100)
    status_updated = pyqtSignal(str)   # Status message
    analysis_completed = pyqtSignal(dict)  # Analysis results
    analysis_failed = pyqtSignal(str)  # Error message
    
    def __init__(self, source_path: str, story_id: int, parent=None):
        """Initialize the worker thread.
        
        Args:
            source_path: Path to the source code directory
            story_id: ID of the current story
            parent: Parent widget
        """
        super().__init__(parent)
        self.source_path = source_path
        self.story_id = story_id
        self._is_cancelled = False
        
    def run(self):
        """Run the source code analysis."""
        try:
            self.status_updated.emit("Initializing analysis...")
            self.progress_updated.emit(5)
            
            # Import the Ren'Py API here using path manipulation
            import sys
            import os
            
            # Add the renpy-source-api directory to the Python path
            api_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'renpy-source-api')
            if api_dir not in sys.path:
                sys.path.insert(0, api_dir)
            
            # Import the required modules
            from core import RenpyProject
            from database import RenpyAPIDataPersistence
            
            if self._is_cancelled:
                return
                
            self.status_updated.emit("Loading project...")
            self.progress_updated.emit(15)
            
            # Initialize the project
            project = RenpyProject(self.source_path)
            
            if self._is_cancelled:
                return
                
            self.status_updated.emit("Analyzing source files...")
            self.progress_updated.emit(30)
            
            # Run the analysis
            project.analyze()
            
            if self._is_cancelled:
                return
                
            self.status_updated.emit("Saving analysis results...")
            self.progress_updated.emit(80)
            
            # Save to database
            db_persistence = RenpyAPIDataPersistence()
            db_persistence.save_project_analysis(project)
            
            if self._is_cancelled:
                return
                
            self.status_updated.emit("Analysis completed successfully!")
            self.progress_updated.emit(100)
            
            # Get the project overview data
            overview_data = project.get_project_overview()
            stats = overview_data["statistics"]
            
            # Prepare results summary
            results = {
                "files_analyzed": stats["total_rpy_files"],
                "characters_found": stats["total_characters"],
                "labels_found": stats["total_labels"],
                "menus_found": stats["total_menus"],
                "flows_mapped": 0,  # Flow analysis would need separate calculation
                "analysis_quality": 85  # Default quality score, could be calculated based on errors
            }
            
            # Add error count if any
            if overview_data.get("errors"):
                results["errors_found"] = len(overview_data["errors"])
            
            self.analysis_completed.emit(results)
            
        except Exception as e:
            self.analysis_failed.emit(f"Analysis failed: {str(e)}")
    
    def cancel(self):
        """Cancel the analysis."""
        self._is_cancelled = True


class SourceAnalysisSetupTab(QWidget):
    """Setup tab for configuring source analysis."""
    
    def __init__(self, db_conn, parent=None):
        """Initialize the setup tab.
        
        Args:
            db_conn: Database connection
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.story_id: Optional[int] = None
        self.settings = QSettings("ThePlotThickens", "ThePlotThickens")
        self.analysis_worker: Optional[SourceAnalysisWorker] = None
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Source Path Configuration
        path_group = QGroupBox("Source Code Configuration")
        path_layout = QFormLayout(path_group)
        
        # Source path input
        path_input_layout = QHBoxLayout()
        self.source_path_edit = QLineEdit()
        self.source_path_edit.setPlaceholderText("Select the folder containing your story's source code (.rpy files)")
        path_input_layout.addWidget(self.source_path_edit)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_source_path)
        path_input_layout.addWidget(self.browse_button)
        
        path_layout.addRow("Source Path:", path_input_layout)
        
        # Path info
        self.path_info_label = QLabel("No source path selected")
        self.path_info_label.setStyleSheet("color: #666; font-style: italic;")
        path_layout.addRow("", self.path_info_label)
        
        layout.addWidget(path_group)
        
        # Analysis Controls
        analysis_group = QGroupBox("Analysis Control")
        analysis_layout = QVBoxLayout(analysis_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Analysis")
        self.start_button.clicked.connect(self.start_analysis)
        self.start_button.setEnabled(False)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop Analysis")
        self.stop_button.clicked.connect(self.stop_analysis)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        button_layout.addStretch()
        analysis_layout.addLayout(button_layout)
        
        # Progress tracking
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        analysis_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready to analyze")
        self.status_label.setStyleSheet("color: #666;")
        analysis_layout.addWidget(self.status_label)
        
        layout.addWidget(analysis_group)
        
        # Results Display (Optional)
        results_group = QGroupBox("Analysis Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(150)
        self.results_text.setReadOnly(True)
        self.results_text.setPlaceholderText("Analysis results will appear here...")
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_group)
        
        layout.addStretch()
        
        # Connect source path changes
        self.source_path_edit.textChanged.connect(self.on_source_path_changed)
        
    def set_story(self, story_id: int, story_data: Dict[str, Any]):
        """Set the current story and load its source path.
        
        Args:
            story_id: ID of the story
            story_data: Story data dictionary
        """
        self.story_id = story_id
        
        # Load saved source path for this story
        story_key = f"story_{story_id}/source_path"
        saved_path = self.settings.value(story_key, "", type=str)
        
        if saved_path:
            self.source_path_edit.setText(saved_path)
            self.update_path_info(saved_path)
        else:
            self.source_path_edit.clear()
            self.path_info_label.setText("No source path configured")
            
        self.results_text.clear()
        self.status_label.setText("Ready to analyze")
        
    def browse_source_path(self):
        """Open file dialog to select source path."""
        if not self.story_id:
            QMessageBox.warning(self, "No Story", "Please select a story first.")
            return
            
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setWindowTitle("Select Source Code Directory")
        
        if dialog.exec():
            selected_path = dialog.selectedFiles()[0]
            self.source_path_edit.setText(selected_path)
            
    def on_source_path_changed(self, path: str):
        """Handle source path changes.
        
        Args:
            path: New path string
        """
        if self.story_id:
            # Save to settings
            story_key = f"story_{self.story_id}/source_path"
            self.settings.setValue(story_key, path)
            
        # Update UI
        self.update_path_info(path)
        self.start_button.setEnabled(bool(path.strip() and os.path.isdir(path)))
        
    def update_path_info(self, path: str):
        """Update the path information display.
        
        Args:
            path: Path to analyze
        """
        if not path.strip():
            self.path_info_label.setText("No source path selected")
            return
            
        if os.path.isdir(path):
            # Count .rpy files
            rpy_files = []
            try:
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.endswith('.rpy'):
                            rpy_files.append(file)
            except Exception:
                pass
                
            if rpy_files:
                self.path_info_label.setText(f"✓ Valid source directory ({len(rpy_files)} .rpy files found)")
                self.path_info_label.setStyleSheet("color: #2e7d32; font-style: italic;")
            else:
                self.path_info_label.setText("⚠ Directory exists but no .rpy files found")
                self.path_info_label.setStyleSheet("color: #f57c00; font-style: italic;")
        else:
            self.path_info_label.setText("✗ Invalid or non-existent directory")
            self.path_info_label.setStyleSheet("color: #d32f2f; font-style: italic;")
            
    def start_analysis(self):
        """Start the source code analysis."""
        if not self.story_id:
            QMessageBox.warning(self, "No Story", "Please select a story first.")
            return
            
        source_path = self.source_path_edit.text().strip()
        if not source_path or not os.path.isdir(source_path):
            QMessageBox.warning(self, "Invalid Path", "Please select a valid source code directory.")
            return
            
        # Update UI
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.results_text.clear()
        
        # Start worker thread
        self.analysis_worker = SourceAnalysisWorker(source_path, self.story_id)
        self.analysis_worker.progress_updated.connect(self.progress_bar.setValue)
        self.analysis_worker.status_updated.connect(self.status_label.setText)
        self.analysis_worker.analysis_completed.connect(self.on_analysis_completed)
        self.analysis_worker.analysis_failed.connect(self.on_analysis_failed)
        self.analysis_worker.finished.connect(self.on_analysis_finished)
        
        self.analysis_worker.start()
        
    def stop_analysis(self):
        """Stop the running analysis."""
        if self.analysis_worker and self.analysis_worker.isRunning():
            self.analysis_worker.cancel()
            self.analysis_worker.wait(3000)  # Wait up to 3 seconds
            
        self.on_analysis_finished()
        
    def on_analysis_completed(self, results: Dict[str, Any]):
        """Handle successful analysis completion.
        
        Args:
            results: Analysis results dictionary
        """
        # Display results
        results_text = "Analysis completed successfully!\n\n"
        results_text += f"Files analyzed: {results.get('files_analyzed', 0)}\n"
        results_text += f"Characters found: {results.get('characters_found', 0)}\n"
        results_text += f"Labels found: {results.get('labels_found', 0)}\n"
        results_text += f"Menus found: {results.get('menus_found', 0)}\n"
        results_text += f"Flows mapped: {results.get('flows_mapped', 0)}\n"
        
        quality = results.get('analysis_quality', 0)
        results_text += f"Quality score: {quality:.1f}/100\n"
        
        self.results_text.setPlainText(results_text)
        
    def on_analysis_failed(self, error_message: str):
        """Handle analysis failure.
        
        Args:
            error_message: Error message to display
        """
        self.results_text.setPlainText(f"Analysis failed:\n{error_message}")
        self.status_label.setText("Analysis failed")
        
    def on_analysis_finished(self):
        """Handle analysis thread finishing (success or failure)."""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        if self.analysis_worker:
            self.analysis_worker.deleteLater()
            self.analysis_worker = None


class SourceAnalysisTab(QWidget):
    """Main Source Analysis tab widget with sub-tabs."""
    
    def __init__(self, db_conn, parent=None):
        """Initialize the source analysis tab.
        
        Args:
            db_conn: Database connection
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.story_id: Optional[int] = None
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create sub-tab widget
        self.sub_tabs = QTabWidget()
        layout.addWidget(self.sub_tabs)
        
        # Setup tab
        self.setup_tab = SourceAnalysisSetupTab(self.db_conn)
        self.sub_tabs.addTab(self.setup_tab, "Setup")
        
        # Add icon to Setup tab
        self.sub_tabs.setTabIcon(0, icon_manager.get_icon("settings"))
        
        # Future tabs can be added here
        # self.sub_tabs.addTab(VisualizationTab(), "Visualization")
        # self.sub_tabs.addTab(ExportTab(), "Export")
        
    def set_story(self, story_id: int, story_data: Dict[str, Any]):
        """Set the current story for analysis.
        
        Args:
            story_id: ID of the story
            story_data: Story data dictionary
        """
        self.story_id = story_id
        self.setup_tab.set_story(story_id, story_data) 