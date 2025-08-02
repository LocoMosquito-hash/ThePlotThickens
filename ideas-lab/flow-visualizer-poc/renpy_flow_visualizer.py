#!/usr/bin/env python3
"""
Renpy Flow Visualizer - Standalone POC
Interactive branching map for Renpy visual novels

This is a proof-of-concept standalone application that visualizes
the narrative flow and branching structure of Renpy visual novels.
"""

# =============================================================================
# DEPRECATED: This is the older version of the Flow Visualizer POC
# =============================================================================
# This file is no longer being actively maintained or updated.
# Please use 'renpy_flow_visualizer_v2_main.py' for the current version.
# This older version is kept for reference purposes only.
# =============================================================================

import sys
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add the main app directory to path for renpy-source-api imports
current_dir = Path(__file__).parent
app_dir = current_dir.parent.parent / "app"
renpy_api_dir = app_dir / "renpy-source-api"
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(renpy_api_dir))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QSplitter,
    QStatusBar, QMenuBar, QMessageBox, QProgressBar, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot, QStandardPaths
from PyQt6.QtGui import QAction

# Import our custom components
from vn_flow_visualizer_v2_simple import VNFlowVisualizerV2Simple
from vn_control_panel import VNControlPanel

# Import renpy-source-api modules directly
try:
    from core import RenpyProject
    from parser import RenpyParser
    from exceptions import RenpyParseError, RenpyProjectError
    RENPY_API_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import renpy-source-api: {e}")
    RENPY_API_AVAILABLE = False


class ProjectAnalysisThread(QThread):
    """Thread for analyzing Renpy projects without blocking the UI."""
    
    analysis_completed = pyqtSignal(dict)  # flow_graph_data
    analysis_failed = pyqtSignal(str)  # error_message
    progress_updated = pyqtSignal(str)  # status_message
    
    def __init__(self, project_path: str):
        super().__init__()
        self.project_path = project_path
        
    def run(self):
        """Analyze the Renpy project in a separate thread."""
        try:
            self.progress_updated.emit("Initializing project analysis...")
            
            if not RENPY_API_AVAILABLE:
                self.analysis_failed.emit("renpy-source-api not available")
                return
                
            # Initialize the Renpy project
            project = RenpyProject(self.project_path)
            
            self.progress_updated.emit("Analyzing project structure...")
            
            # Perform full analysis
            overview = project.analyze()
            
            self.progress_updated.emit("Building flow graph...")
            
            # Get the flow graph
            flow_graph = project.get_flow_graph()
            
            self.progress_updated.emit("Generating flow statistics...")
            
            # Get additional analysis data
            flow_patterns = project.parser.analyze_flow_patterns(self.project_path)
            
            # Combine data for the visualizer
            analysis_data = {
                'flow_graph': flow_graph,
                'flow_patterns': flow_patterns,
                'project_path': self.project_path,
                'total_labels': len(flow_graph),
                'project_info': {
                    'name': Path(self.project_path).name,
                    'path': self.project_path,
                    'rpy_files': overview.total_rpy_files,
                    'total_lines': overview.total_lines,
                    'dialogue_lines': overview.total_dialogue_lines,
                    'characters': overview.total_characters,
                    'labels': overview.total_labels,
                    'menus': overview.total_menus
                }
            }
            
            self.progress_updated.emit("Analysis complete!")
            self.analysis_completed.emit(analysis_data)
            
        except (RenpyParseError, RenpyProjectError) as e:
            self.analysis_failed.emit(f"Renpy parsing error: {str(e)}")
        except Exception as e:
            self.analysis_failed.emit(f"Unexpected error: {str(e)}")


class RenpyFlowMapper(QMainWindow):
    """
    Main application window for the Renpy Flow Visualizer POC.
    
    Provides file loading, visualization control, and project analysis.
    """
    
    def __init__(self):
        super().__init__()
        self.current_project_path: Optional[str] = None
        self.analysis_thread: Optional[ProjectAnalysisThread] = None
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
        
        # Connect the reset button to the visualizer's reset_view method
        self.control_panel.reset_button.clicked.connect(self.visualizer.reset_view)
        
        self.setWindowTitle("Renpy Flow Visualizer - POC")
        self.resize(1400, 900)
        
    def load_recent_paths(self):
        """Load recent paths from settings file."""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                    self.recent_paths = data.get('recent_paths', [])[:10]  # Keep only last 10
        except Exception:
            self.recent_paths = []
            
    def save_recent_paths(self):
        """Save recent paths to settings file."""
        try:
            data = {'recent_paths': self.recent_paths[:10]}  # Keep only last 10
            with open(self.settings_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass  # Fail silently
            
    def add_recent_path(self, path: str):
        """Add a path to recent paths, avoiding duplicates."""
        if path in self.recent_paths:
            self.recent_paths.remove(path)
        self.recent_paths.insert(0, path)
        self.recent_paths = self.recent_paths[:10]  # Keep only last 10
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
        
        # Use combo box instead of line edit for path history
        self.path_combo = QComboBox()
        self.path_combo.setEditable(True)
        self.path_combo.setPlaceholderText("Select or enter path to Renpy game folder...")
        self.path_combo.setSizePolicy(self.path_combo.sizePolicy().horizontalPolicy(), self.path_combo.sizePolicy().verticalPolicy())
        path_layout.addWidget(self.path_combo)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_for_path)
        path_layout.addWidget(self.browse_button)
        
        self.load_button = QPushButton("Load & Analyze")
        self.load_button.clicked.connect(self.load_project)
        self.load_button.setEnabled(False)
        path_layout.addWidget(self.load_button)
        
        main_layout.addLayout(path_layout)
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Visualization area
        self.visualizer = VNFlowVisualizerV2Simple()
        splitter.addWidget(self.visualizer)
        
        # Control panel
        self.control_panel = VNControlPanel()
        self.control_panel.setMaximumWidth(300)  # Limit control panel width
        self.control_panel.setMinimumWidth(250)
        splitter.addWidget(self.control_panel)
        
        # Set splitter proportions (85% visualizer, 15% control panel)
        splitter.setStretchFactor(0, 17)  # Visualization gets much more space
        splitter.setStretchFactor(1, 3)   # Control panel gets less space
        splitter.setSizes([1000, 200])    # Set initial sizes explicitly
        
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
        
        # Reset view action
        reset_view_action = QAction("Reset View", self)
        reset_view_action.setShortcut("Ctrl+R")
        reset_view_action.triggered.connect(self.visualizer.reset_view)
        view_menu.addAction(reset_view_action)
        
        # Fit to content action
        fit_view_action = QAction("Fit to Content", self)
        fit_view_action.setShortcut("Ctrl+F")
        fit_view_action.triggered.connect(self.visualizer.fit_view_to_content)
        view_menu.addAction(fit_view_action)
        
    def setup_status_bar(self):
        """Set up the status bar with progress information."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Progress bar for analysis
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        self.status_bar.showMessage("Ready - Select a Renpy game folder to begin")
        
    def on_path_changed(self):
        """Handle changes to the path input."""
        path = self.path_combo.currentText().strip()
        self.load_button.setEnabled(bool(path))
        
    def clear_recent_paths(self):
        """Clear the recent paths history."""
        self.recent_paths.clear()
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
        """Load and analyze the selected Renpy project."""
        project_path = self.path_combo.currentText().strip()
        
        if not project_path:
            QMessageBox.warning(self, "No Path", "Please select a Renpy game folder.")
            return
            
        if not Path(project_path).exists():
            QMessageBox.warning(self, "Invalid Path", "The selected folder does not exist.")
            return
            
        if not RENPY_API_AVAILABLE:
            QMessageBox.critical(
                self, "Missing Dependencies", 
                "renpy-source-api is not available. Please check the installation."
            )
            return
        
        self.current_project_path = project_path
        
        # Add to recent paths
        self.add_recent_path(project_path)
        
        # Clear current visualization
        self.visualizer.clear_visualization()
        self.control_panel.clear_project_info()
        
        # Start analysis in background thread
        self.analysis_thread = ProjectAnalysisThread(project_path)
        self.analysis_thread.analysis_completed.connect(self.on_analysis_completed)
        self.analysis_thread.analysis_failed.connect(self.on_analysis_failed)
        self.analysis_thread.progress_updated.connect(self.on_progress_updated)
        
        # Update UI for analysis state
        self.load_button.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        self.analysis_thread.start()
        
    @pyqtSlot(dict)
    def on_analysis_completed(self, analysis_data: Dict[str, Any]):
        """Handle successful project analysis completion."""
        # Update control panel with project info
        self.control_panel.update_project_info(analysis_data.get('project_info', {}))
        
        # Load the flow graph into the visualizer
        # Handle both old and new visualizer interfaces
        if hasattr(self.visualizer, 'load_flow_graph'):
        self.visualizer.load_flow_graph(analysis_data)
        elif hasattr(self.visualizer, 'load_flow_data'):
            # Convert analysis_data to VisualizationData format if needed
            self.visualizer.load_flow_data(analysis_data)
        else:
            print("Warning: Visualizer has no compatible load method")
        
        # Update status
        total_labels = analysis_data.get('total_labels', 0)
        self.status_bar.showMessage(f"Project loaded: {total_labels} labels analyzed")
        
        # Reset UI state
        self.load_button.setEnabled(True)
        self.browse_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
    @pyqtSlot(str)
    def on_analysis_failed(self, error_message: str):
        """Handle project analysis failure."""
        QMessageBox.critical(
            self, "Analysis Failed", 
            f"Failed to analyze the Renpy project:\n\n{error_message}"
        )
        
        # Reset UI state
        self.load_button.setEnabled(True)
        self.browse_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Analysis failed")
        
    @pyqtSlot(str)
    def on_progress_updated(self, message: str):
        """Handle progress updates during analysis."""
        self.status_bar.showMessage(message)


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Renpy Flow Visualizer")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("The Plot Thickens")
    
    # Create and show main window
    window = RenpyFlowMapper()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main()) 