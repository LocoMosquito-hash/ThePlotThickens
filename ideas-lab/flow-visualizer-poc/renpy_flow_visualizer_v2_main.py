#!/usr/bin/env python3
"""
Renpy Flow Visualizer - POC Main Application (Updated for Clean Architecture)

This is the updated main application that uses the clean interface architecture,
eliminating direct renpy-source-api dependencies and circular development issues.

Phase 3 of the flow visualizer refactoring.
"""

import sys
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QSplitter,
    QStatusBar, QMenuBar, QMessageBox, QProgressBar, QComboBox,
    QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QAction

# Import our updated components using clean architecture
from vn_flow_visualizer_v2_simple import VNFlowVisualizerV2Simple
from vn_control_panel import VNControlPanel


class RenpyFlowMapperV2(QMainWindow):
    """
    Updated main application window using clean interface architecture.
    
    This version eliminates direct renpy-source-api dependencies and uses
    the adapter pattern for clean separation of concerns.
    """
    
    def __init__(self):
        super().__init__()
        self.current_project_path: Optional[str] = None
        self.settings_file = Path.home() / ".renpy_flow_visualizer_paths.json"
        self.recent_paths: List[str] = []
        
        self.load_recent_paths()
        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()
        
        # Connect signals
        self.visualizer.node_selected.connect(self.control_panel.update_node_details)
        self.control_panel.layout_changed.connect(self.visualizer.apply_layout)
        self.control_panel.search_node.connect(self.visualizer.search_and_select_node)
        
        # Give control panel access to visualizer for relationship data
        self.control_panel.set_visualizer(self.visualizer)
        self.control_panel.edge_highlighting_changed.connect(self.visualizer.set_edge_highlighting_enabled)
        
        self.setWindowTitle("Renpy Flow Visualizer - POC (Clean Architecture)")
        self.resize(1400, 900)
        
        # Start maximized for better workflow
        self.showMaximized()
        
    def load_recent_paths(self):
        """Load recent paths from settings file."""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                    self.recent_paths = data.get('recent_paths', [])[:100]  # Keep only last 100
        except Exception:
            self.recent_paths = []
            
    def save_recent_paths(self):
        """Save recent paths to settings file."""
        try:
            data = {'recent_paths': self.recent_paths[:100]}  # Keep only last 100
            with open(self.settings_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass  # Fail silently
            
    def add_recent_path(self, path: str):
        """Add a path to recent paths, avoiding duplicates."""
        if path in self.recent_paths:
            self.recent_paths.remove(path)
        self.recent_paths.insert(0, path)
        self.recent_paths = self.recent_paths[:100]  # Keep only last 100
        self.save_recent_paths()
        self.update_path_combo()
        
    def update_path_combo(self):
        """Update the path combo box with recent paths."""
        current_text = self.path_combo.currentText()
        self.path_combo.clear()
        
        # Add recent paths
        for path in self.recent_paths:
            self.path_combo.addItem(path)
            
        # Set current text back
        if current_text:
            self.path_combo.setCurrentText(current_text)
        
    def setup_ui(self):
        """Set up the main user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # File path section
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Renpy Game Path:"))
        
        # Path combo box for history
        self.path_combo = QComboBox()
        self.path_combo.setEditable(True)
        self.path_combo.setPlaceholderText("Select or enter path to Renpy game folder...")
        path_layout.addWidget(self.path_combo)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_for_path)
        path_layout.addWidget(self.browse_button)
        
        # Enhanced analysis option
        self.sdk_checkbox = QCheckBox("Enhanced Analysis (SDK)")
        self.sdk_checkbox.setToolTip("Use official Ren'Py SDK for more accurate parsing of complex VNs")
        self.sdk_checkbox.setChecked(True)  # Default to enhanced
        path_layout.addWidget(self.sdk_checkbox)
        
        self.load_button = QPushButton("Load & Analyze")
        self.load_button.clicked.connect(self.load_project)
        self.load_button.setEnabled(False)
        path_layout.addWidget(self.load_button)
        
        main_layout.addLayout(path_layout)
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Visualization area (using new clean architecture)
        self.visualizer = VNFlowVisualizerV2Simple()
        splitter.addWidget(self.visualizer)
        
        # Control panel
        self.control_panel = VNControlPanel()
        self.control_panel.setMaximumWidth(300)
        self.control_panel.setMinimumWidth(250)
        splitter.addWidget(self.control_panel)
        
        # Set splitter proportions
        splitter.setStretchFactor(0, 17)  # Visualization gets much more space
        splitter.setStretchFactor(1, 3)   # Control panel gets less space
        splitter.setSizes([1000, 200])
        
        main_layout.addWidget(splitter)
        
        # Load recent paths and connect signals
        self.update_path_combo()
        self.path_combo.currentTextChanged.connect(self.on_path_changed)
        self.path_combo.editTextChanged.connect(self.on_path_changed)
        
    def setup_menu(self):
        """Set up the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        # Load project action
        load_action = QAction("Load Project", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self.browse_for_path)
        file_menu.addAction(load_action)
        
        file_menu.addSeparator()
        
        # Clear recent paths action
        clear_recent_action = QAction("Clear Recent Paths", self)
        clear_recent_action.triggered.connect(self.clear_recent_paths)
        file_menu.addAction(clear_recent_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        # Fit to content action (using new visualizer method)
        fit_view_action = QAction("Fit to Content", self)
        fit_view_action.setShortcut("Ctrl+F")
        fit_view_action.triggered.connect(self.visualizer.fit_view_to_content)
        view_menu.addAction(fit_view_action)
        
        # Analysis menu (new)
        analysis_menu = menubar.addMenu("Analysis")
        
        # Toggle SDK analysis
        sdk_action = QAction("Use Enhanced Analysis", self)
        sdk_action.setCheckable(True)
        sdk_action.setChecked(True)
        sdk_action.triggered.connect(lambda checked: self.sdk_checkbox.setChecked(checked))
        analysis_menu.addAction(sdk_action)
        
    def setup_status_bar(self):
        """Set up the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        self.status_bar.showMessage("Ready - Select a Renpy game folder to analyze")
    
    def on_path_changed(self, text: str):
        """Handle path text changes."""
        self.load_button.setEnabled(bool(text.strip()))
        
    def clear_recent_paths(self):
        """Clear the recent paths list."""
        self.recent_paths = []
        self.save_recent_paths()
        self.update_path_combo()
        
    def browse_for_path(self):
        """Open a file dialog to browse for the Renpy game folder."""
        # Start from the most recent path if available
        start_dir = ""
        if self.recent_paths:
            start_dir = str(Path(self.recent_paths[0]).parent)
            
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Renpy Game Folder",
            start_dir,
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder_path:
            self.path_combo.setCurrentText(folder_path)
            
    def load_project(self):
        """
        Load and analyze the selected Renpy project using clean interface.
        
        This method now uses the new clean architecture instead of direct API calls.
        """
        project_path = self.path_combo.currentText().strip()
        
        if not project_path:
            QMessageBox.warning(self, "No Path", "Please select a Renpy game folder.")
            return
            
        if not Path(project_path).exists():
            QMessageBox.warning(self, "Invalid Path", "The selected folder does not exist.")
            return
        
        self.current_project_path = project_path
        
        # Add to recent paths
        self.add_recent_path(project_path)
        
        # Clear current visualization
        self.visualizer.clear_visualization()
        self.control_panel.clear_project_info()
        
        # Show progress
        self.load_button.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.status_bar.showMessage("Analyzing project...")
        
        # Use enhanced analysis if checkbox is checked
        use_sdk = self.sdk_checkbox.isChecked()
        
        try:
            # Load project using clean interface - no more background threads needed!
            success = self.visualizer.load_project(project_path, use_sdk=use_sdk)
            
            if success:
                # Update control panel with project info
                project_info = self.visualizer.get_project_info()
                self.control_panel.update_project_info(project_info)
                
                # Update status with analysis results
                analysis_metadata = self.visualizer.get_analysis_metadata()
                total_labels = project_info.get('total_labels', 0)
                parser_type = analysis_metadata.get('parser_type', 'unknown')
                
                status_msg = f"Project loaded: {total_labels} labels analyzed ({parser_type})"
                if use_sdk and 'sdk_usage_percent' in analysis_metadata:
                    sdk_percent = analysis_metadata['sdk_usage_percent']
                    status_msg += f", SDK: {sdk_percent:.1f}%"
                
                self.status_bar.showMessage(status_msg)
                
                # Show complexity detection info if available
                if analysis_metadata.get('complexity_detected'):
                    reasons = analysis_metadata.get('complexity_reasons', [])
                    if reasons:
                        complexity_msg = "Complex structures detected:\n" + "\n".join(f"• {r}" for r in reasons[:3])
                        if len(reasons) > 3:
                            complexity_msg += f"\n• ... and {len(reasons) - 3} more"
                        
                        QMessageBox.information(self, "Enhanced Analysis Used", complexity_msg)
                
            else:
                QMessageBox.critical(
                    self, "Analysis Failed", 
                    "Failed to analyze the Renpy project. Check the console for details."
                )
                self.status_bar.showMessage("Analysis failed")
                
        except Exception as e:
            QMessageBox.critical(
                self, "Analysis Failed", 
                f"Failed to analyze the Renpy project:\n\n{str(e)}"
            )
            self.status_bar.showMessage("Analysis failed")
        
        finally:
            # Reset UI state
            self.load_button.setEnabled(True)
            self.browse_button.setEnabled(True)
            self.progress_bar.setVisible(False)


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Renpy Flow Visualizer")
    app.setApplicationVersion("2.0.0")  # Updated version for clean architecture
    app.setOrganizationName("The Plot Thickens")
    
    # Create and show main window
    window = RenpyFlowMapperV2()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main()) 