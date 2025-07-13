#!/usr/bin/env python3
"""
Renpy Flow Visualizer - Standalone POC
Interactive branching map for Renpy visual novels

This is a proof-of-concept standalone application that visualizes
the narrative flow and branching structure of Renpy visual novels.
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QSplitter,
    QStatusBar, QMenuBar, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction

# Import our custom components
from vn_flow_visualizer import VNFlowVisualizer
from vn_control_panel import VNControlPanel


class RenpyFlowMapper(QMainWindow):
    """
    Main application window for the Renpy Flow Visualizer.
    
    Provides file loading interface and houses the main visualization components.
    """
    
    def __init__(self):
        super().__init__()
        self.current_project_path: Optional[str] = None
        self.flow_graph: Optional[Dict[str, Any]] = None
        
        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()
        
        # Set window properties
        self.setWindowTitle("Renpy Flow Visualizer - POC")
        self.setGeometry(100, 100, 1400, 900)
        
    def setup_ui(self):
        """Set up the main user interface components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        
        # File loading section
        file_section = self.create_file_loading_section()
        layout.addWidget(file_section)
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Visualization area (main)
        self.visualizer = VNFlowVisualizer()
        splitter.addWidget(self.visualizer)
        
        # Control panel (side)
        self.control_panel = VNControlPanel()
        splitter.addWidget(self.control_panel)
        
        # Set splitter proportions (80% visualizer, 20% controls)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        
        # Connect signals
        self.control_panel.layout_changed.connect(self.visualizer.apply_layout)
        self.visualizer.node_selected.connect(self.control_panel.show_node_details)
        
    def create_file_loading_section(self) -> QWidget:
        """Create the file path loading interface."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Path label and input
        layout.addWidget(QLabel("Renpy Game Path:"))
        
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Select the game folder containing .rpy files...")
        layout.addWidget(self.path_input)
        
        # Browse button
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_for_path)
        layout.addWidget(self.browse_button)
        
        # Load button
        self.load_button = QPushButton("Load & Analyze")
        self.load_button.clicked.connect(self.load_project)
        self.load_button.setEnabled(False)
        layout.addWidget(self.load_button)
        
        # Connect path input changes
        self.path_input.textChanged.connect(self.on_path_changed)
        
        widget.setMaximumHeight(60)
        return widget
        
    def setup_menu(self):
        """Set up the application menu bar."""
        menubar = self.menuBar()
        assert menubar is not None  # Ensure menubar is available
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        # Open action
        open_action = QAction("Open Renpy Project...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.browse_for_path)
        file_menu.addAction(open_action)
        
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
        
    def setup_status_bar(self):
        """Set up the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Select a Renpy project to begin")
        
    def on_path_changed(self, path: str):
        """Handle path input changes."""
        self.load_button.setEnabled(bool(path.strip()))
        
    def browse_for_path(self):
        """Open file dialog to browse for Renpy project path."""
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setWindowTitle("Select Renpy Game Directory")
        
        # Look for typical Renpy project indicators
        if dialog.exec():
            selected_dirs = dialog.selectedFiles()
            if selected_dirs:
                path = selected_dirs[0]
                self.path_input.setText(path)
                
    def load_project(self):
        """Load and analyze the selected Renpy project."""
        path = self.path_input.text().strip()
        if not path:
            return
            
        if not os.path.exists(path):
            QMessageBox.warning(self, "Error", f"Path does not exist: {path}")
            return
            
        # Validate it looks like a Renpy project
        if not self.validate_renpy_project(path):
            reply = QMessageBox.question(
                self, "Confirm",
                f"The selected path doesn't appear to contain .rpy files.\n"
                f"Continue anyway?\n\nPath: {path}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
                
        try:
            self.status_bar.showMessage("Loading and analyzing project...")
            QApplication.processEvents()  # Update UI
            
            # Load using your existing renpy-source-api
            self.current_project_path = path
            self.flow_graph = self.analyze_renpy_project(path)
            
            # Update visualization
            self.visualizer.load_flow_graph(self.flow_graph)
            self.control_panel.update_project_info(self.flow_graph)
            
            self.status_bar.showMessage(f"Loaded project: {Path(path).name}")
            
        except Exception as e:
            self.status_bar.showMessage("Error loading project")
            QMessageBox.critical(self, "Error", f"Failed to load project:\n{str(e)}")
            
    def validate_renpy_project(self, path: str) -> bool:
        """Validate that the path contains Renpy project files."""
        path_obj = Path(path)
        if not path_obj.exists():
            return False
            
        # Look for .rpy files
        rpy_files = list(path_obj.glob("**/*.rpy"))
        return len(rpy_files) > 0
        
    def analyze_renpy_project(self, path: str) -> Dict[str, Any]:
        """
        Analyze the Renpy project and return flow graph data.
        
        This will integrate with your existing renpy-source-api.
        For now, returns mock data for testing.
        """
        # TODO: Integrate with your existing renpy-source-api
        # from app.renpy_source_api.core import RenpyProject
        # project = RenpyProject(path)
        # return project.get_flow_graph()
        
        # Mock data for POC
        return {
            'nodes': {
                'start': {
                    'name': 'start',
                    'file_path': f'{path}/script.rpy',
                    'line_number': 1,
                    'has_menu': False,
                    'has_dialogue': True,
                    'outgoing_flows': ['chapter1', 'tutorial']
                },
                'tutorial': {
                    'name': 'tutorial',
                    'file_path': f'{path}/script.rpy',
                    'line_number': 25,
                    'has_menu': True,
                    'has_dialogue': True,
                    'outgoing_flows': ['chapter1']
                },
                'chapter1': {
                    'name': 'chapter1',
                    'file_path': f'{path}/chapter1.rpy',
                    'line_number': 1,
                    'has_menu': True,
                    'has_dialogue': True,
                    'outgoing_flows': ['chapter1_good', 'chapter1_bad']
                },
                'chapter1_good': {
                    'name': 'chapter1_good',
                    'file_path': f'{path}/chapter1.rpy',
                    'line_number': 45,
                    'has_menu': False,
                    'has_dialogue': True,
                    'outgoing_flows': ['ending_good']
                },
                'chapter1_bad': {
                    'name': 'chapter1_bad',
                    'file_path': f'{path}/chapter1.rpy',
                    'line_number': 78,
                    'has_menu': False,
                    'has_dialogue': True,
                    'outgoing_flows': ['ending_bad']
                },
                'ending_good': {
                    'name': 'ending_good',
                    'file_path': f'{path}/chapter1.rpy',
                    'line_number': 120,
                    'has_menu': False,
                    'has_dialogue': True,
                    'outgoing_flows': []
                },
                'ending_bad': {
                    'name': 'ending_bad',
                    'file_path': f'{path}/chapter1.rpy',
                    'line_number': 145,
                    'has_menu': False,
                    'has_dialogue': True,
                    'outgoing_flows': []
                }
            },
            'stats': {
                'total_labels': 7,
                'total_flows': 8,
                'has_start': True,
                'project_path': path
            }
        }


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Renpy Flow Visualizer")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("The Plot Thickens")
    
    # Create and show main window
    window = RenpyFlowMapper()
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 