"""
VN Control Panel Widget

Side panel for controlling visualization options, displaying project information,
and showing details about selected nodes.
"""

from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QPushButton, QComboBox, QTextEdit, QScrollArea, QFrame,
    QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class VNControlPanel(QWidget):
    """
    Control panel for the VN Flow Visualizer.
    
    Provides controls for layout, project information display,
    and detailed node information.
    """
    
    layout_changed = pyqtSignal(str)  # layout_type
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_project_info: Optional[Dict[str, Any]] = None
        self.current_node_info: Optional[Dict[str, Any]] = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the control panel user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Create scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        
        # Layout Controls Section
        layout_group = self.create_layout_controls()
        content_layout.addWidget(layout_group)
        
        # Project Information Section
        self.project_info_group = self.create_project_info_section()
        content_layout.addWidget(self.project_info_group)
        
        # Node Details Section
        self.node_details_group = self.create_node_details_section()
        content_layout.addWidget(self.node_details_group)
        
        # Add stretch to push content to top
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
        # Set panel properties
        self.setMaximumWidth(350)
        self.setMinimumWidth(250)
        
    def create_layout_controls(self) -> QGroupBox:
        """Create layout control section."""
        group = QGroupBox("Layout Controls")
        layout = QVBoxLayout(group)
        
        # Layout algorithm selection
        layout_layout = QHBoxLayout()
        layout_layout.addWidget(QLabel("Algorithm:"))
        
        self.layout_combo = QComboBox()
        self.layout_combo.addItems([
            "spring", "circular", "hierarchical"
        ])
        self.layout_combo.currentTextChanged.connect(self.on_layout_changed)
        layout_layout.addWidget(self.layout_combo)
        
        layout.addLayout(layout_layout)
        
        # Layout control buttons
        button_layout = QHBoxLayout()
        
        self.apply_layout_btn = QPushButton("Apply Layout")
        self.apply_layout_btn.clicked.connect(self.apply_current_layout)
        button_layout.addWidget(self.apply_layout_btn)
        
        self.reset_view_btn = QPushButton("Reset View")
        self.reset_view_btn.clicked.connect(self.reset_view)
        button_layout.addWidget(self.reset_view_btn)
        
        layout.addLayout(button_layout)
        
        return group
        
    def create_project_info_section(self) -> QGroupBox:
        """Create project information section."""
        group = QGroupBox("Project Information")
        layout = QVBoxLayout(group)
        
        # Project stats grid
        self.stats_layout = QGridLayout()
        layout.addLayout(self.stats_layout)
        
        # Initially show "No project loaded"
        self.no_project_label = QLabel("No project loaded")
        self.no_project_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_project_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.no_project_label)
        
        return group
        
    def create_node_details_section(self) -> QGroupBox:
        """Create node details section."""
        group = QGroupBox("Selected Node Details")
        layout = QVBoxLayout(group)
        
        # Node details text area
        self.node_details_text = QTextEdit()
        self.node_details_text.setReadOnly(True)
        self.node_details_text.setMaximumHeight(200)
        self.node_details_text.setPlainText("No node selected")
        layout.addWidget(self.node_details_text)
        
        # Node actions
        actions_layout = QHBoxLayout()
        
        self.highlight_paths_btn = QPushButton("Highlight Paths")
        self.highlight_paths_btn.setEnabled(False)
        self.highlight_paths_btn.clicked.connect(self.highlight_node_paths)
        actions_layout.addWidget(self.highlight_paths_btn)
        
        self.show_details_btn = QPushButton("Show Details")
        self.show_details_btn.setEnabled(False)
        self.show_details_btn.clicked.connect(self.show_detailed_node_info)
        actions_layout.addWidget(self.show_details_btn)
        
        layout.addLayout(actions_layout)
        
        return group
        
    def update_project_info(self, flow_graph: Dict[str, Any]):
        """Update project information display."""
        self.current_project_info = flow_graph
        
        # Hide "no project" label
        self.no_project_label.hide()
        
        # Clear existing stats
        self.clear_layout(self.stats_layout)
        
        # Extract statistics
        stats = flow_graph.get('stats', {})
        nodes = flow_graph.get('nodes', {})
        
        # Calculate additional stats
        total_labels = len(nodes)
        menu_labels = sum(1 for node in nodes.values() if node.get('has_menu', False))
        ending_labels = sum(1 for node in nodes.values() if not node.get('outgoing_flows', []))
        dialogue_labels = sum(1 for node in nodes.values() if node.get('has_dialogue', False))
        
        # Display stats in grid
        stat_items = [
            ("Total Labels:", str(total_labels)),
            ("Menu Choices:", str(menu_labels)),
            ("Ending Labels:", str(ending_labels)),
            ("With Dialogue:", str(dialogue_labels)),
            ("Has Start Label:", "Yes" if stats.get('has_start', False) else "No"),
        ]
        
        for i, (label_text, value_text) in enumerate(stat_items):
            label = QLabel(label_text)
            label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            value = QLabel(value_text)
            value.setAlignment(Qt.AlignmentFlag.AlignRight)
            
            # Style the value
            font = QFont()
            font.setBold(True)
            value.setFont(font)
            
            self.stats_layout.addWidget(label, i, 0)
            self.stats_layout.addWidget(value, i, 1)
            
        # Project path (if available)
        project_path = stats.get('project_path', '')
        if project_path:
            path_label = QLabel("Path:")
            path_value = QLabel(project_path)
            path_value.setWordWrap(True)
            path_value.setStyleSheet("font-size: 9px; color: gray;")
            
            row = len(stat_items)
            self.stats_layout.addWidget(path_label, row, 0)
            self.stats_layout.addWidget(path_value, row, 1)
            
    def show_node_details(self, node_id: str, node_data: Dict[str, Any]):
        """Display details for selected node."""
        self.current_node_info = {'id': node_id, 'data': node_data}
        
        # Format node details
        details = []
        details.append(f"Label: {node_data.get('name', node_id)}")
        details.append(f"ID: {node_id}")
        details.append("")
        
        # File location
        file_path = node_data.get('file_path', 'Unknown')
        line_number = node_data.get('line_number', 0)
        details.append(f"File: {file_path}")
        details.append(f"Line: {line_number}")
        details.append("")
        
        # Properties
        properties = []
        if node_data.get('has_menu', False):
            properties.append("Has Menu Choices")
        if node_data.get('has_dialogue', False):
            properties.append("Has Dialogue")
        if not node_data.get('outgoing_flows', []):
            properties.append("Ending Label")
        if node_id == 'start':
            properties.append("Start Label")
            
        if properties:
            details.append("Properties:")
            for prop in properties:
                details.append(f"  • {prop}")
            details.append("")
            
        # Outgoing flows
        outgoing = node_data.get('outgoing_flows', [])
        if outgoing:
            details.append(f"Connects to ({len(outgoing)}):")
            for target in outgoing:
                details.append(f"  → {target}")
        else:
            details.append("No outgoing connections")
            
        # Update display
        self.node_details_text.setPlainText("\n".join(details))
        
        # Enable action buttons
        self.highlight_paths_btn.setEnabled(True)
        self.show_details_btn.setEnabled(True)
        
    def clear_layout(self, layout):
        """Clear all widgets from a layout."""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
    def on_layout_changed(self, layout_type: str):
        """Handle layout algorithm change."""
        # Emit signal will be handled by main window
        pass
        
    def apply_current_layout(self):
        """Apply the currently selected layout."""
        layout_type = self.layout_combo.currentText()
        self.layout_changed.emit(layout_type)
        
    def reset_view(self):
        """Reset the visualization view."""
        # This will be connected to the visualizer's reset_view method
        pass
        
    def highlight_node_paths(self):
        """Highlight paths from/to selected node."""
        if self.current_node_info:
            # TODO: Implement path highlighting
            print(f"Highlighting paths for: {self.current_node_info['id']}")
            
    def show_detailed_node_info(self):
        """Show detailed information dialog for selected node."""
        if self.current_node_info:
            from PyQt6.QtWidgets import QMessageBox
            
            node_id = self.current_node_info['id']
            node_data = self.current_node_info['data']
            
            # Create detailed info message
            info_parts = []
            info_parts.append(f"Label: {node_data.get('name', node_id)}")
            info_parts.append(f"Unique ID: {node_id}")
            info_parts.append("")
            info_parts.append(f"File: {node_data.get('file_path', 'Unknown')}")
            info_parts.append(f"Line Number: {node_data.get('line_number', 0)}")
            info_parts.append("")
            
            # Add all available data
            if 'has_menu' in node_data:
                info_parts.append(f"Has Menu: {node_data['has_menu']}")
            if 'has_dialogue' in node_data:
                info_parts.append(f"Has Dialogue: {node_data['has_dialogue']}")
                
            outgoing = node_data.get('outgoing_flows', [])
            info_parts.append(f"Outgoing Connections: {len(outgoing)}")
            if outgoing:
                info_parts.append("Targets:")
                for target in outgoing:
                    info_parts.append(f"  • {target}")
                    
            message = "\n".join(info_parts)
            
            QMessageBox.information(
                self, f"Node Details: {node_id}", message
            ) 