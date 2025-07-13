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
        self.current_node_data: Optional[Dict[str, Any]] = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the control panel interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)  # Reduced spacing
        layout.setContentsMargins(3, 3, 3, 3)  # Reduced margins
        
        # Layout Controls section
        layout_group = self.create_layout_controls()
        layout.addWidget(layout_group)
        
        # Project Information section
        self.project_group = self.create_project_info_section()
        layout.addWidget(self.project_group)
        
        # Selected Node Details section
        self.node_group = self.create_node_details_section()
        layout.addWidget(self.node_group)
        
        # Add stretch to push everything up
        layout.addStretch()
        
    def create_layout_controls(self) -> QGroupBox:
        """Create the layout algorithm controls."""
        group = QGroupBox("Layout Controls")
        layout = QVBoxLayout(group)
        layout.setSpacing(3)  # Reduced spacing
        
        # Algorithm selection
        alg_layout = QHBoxLayout()
        alg_layout.addWidget(QLabel("Algorithm:"))
        
        self.layout_combo = QComboBox()
        self.layout_combo.addItems([
            "spring", "circular", "hierarchical", "random"
        ])
        self.layout_combo.setCurrentText("spring")
        alg_layout.addWidget(self.layout_combo)
        
        layout.addLayout(alg_layout)
        
        # Apply and Reset buttons
        button_layout = QHBoxLayout()
        
        self.apply_button = QPushButton("Apply Layout")
        self.apply_button.clicked.connect(self.apply_layout)
        button_layout.addWidget(self.apply_button)
        
        self.reset_button = QPushButton("Reset View")
        self.reset_button.clicked.connect(self.reset_view)
        button_layout.addWidget(self.reset_button)
        
        layout.addLayout(button_layout)
        
        return group
        
    def create_project_info_section(self) -> QGroupBox:
        """Create the project information display."""
        group = QGroupBox("Project Information")
        layout = QGridLayout(group)
        layout.setSpacing(2)  # Reduced spacing
        
        # Use smaller font for labels to save space
        small_font = QFont()
        small_font.setPointSize(8)
        
        # Project stats labels
        self.project_name_label = QLabel("No project loaded")
        self.project_name_label.setFont(QFont("", 9, QFont.Weight.Bold))
        layout.addWidget(QLabel("Name:"), 0, 0)
        layout.addWidget(self.project_name_label, 0, 1)
        
        # Explicitly define label attributes
        label_font = QFont()
        label_font.setPointSize(8)
        
        # Labels
        labels_label = QLabel("Labels:")
        labels_label.setFont(label_font)
        self.total_labels_label = QLabel("-")
        self.total_labels_label.setFont(label_font)
        layout.addWidget(labels_label, 1, 0)
        layout.addWidget(self.total_labels_label, 1, 1)
        
        # Files
        files_label = QLabel("Files:")
        files_label.setFont(label_font)
        self.rpy_files_label = QLabel("-")
        self.rpy_files_label.setFont(label_font)
        layout.addWidget(files_label, 2, 0)
        layout.addWidget(self.rpy_files_label, 2, 1)
        
        # Lines
        lines_label = QLabel("Lines:")
        lines_label.setFont(label_font)
        self.dialogue_lines_label = QLabel("-")
        self.dialogue_lines_label.setFont(label_font)
        layout.addWidget(lines_label, 3, 0)
        layout.addWidget(self.dialogue_lines_label, 3, 1)
        
        # Path on separate row, with smaller text
        path_label = QLabel("Path:")
        path_label.setFont(label_font)
        self.project_path_label = QLabel("-")
        self.project_path_label.setWordWrap(True)
        self.project_path_label.setMaximumHeight(40)  # Reduced height
        self.project_path_label.setFont(label_font)
        layout.addWidget(path_label, 4, 0)
        layout.addWidget(self.project_path_label, 4, 1)
        
        return group
        
    def create_node_details_section(self) -> QGroupBox:
        """Create the selected node details display."""
        group = QGroupBox("Selected Node Details")
        layout = QVBoxLayout(group)
        layout.setSpacing(3)  # Reduced spacing
        
        # Node info display area - smaller
        self.node_info = QTextEdit()
        self.node_info.setMaximumHeight(120)  # Reduced height
        self.node_info.setReadOnly(True)
        self.node_info.setPlainText("No node selected")
        # Smaller font for details
        small_font = QFont()
        small_font.setPointSize(8)
        self.node_info.setFont(small_font)
        layout.addWidget(self.node_info)
        
        # Action buttons - smaller
        button_layout = QHBoxLayout()
        
        self.highlight_button = QPushButton("Paths")
        self.highlight_button.setEnabled(False)
        button_layout.addWidget(self.highlight_button)
        
        self.show_details_button = QPushButton("Details")
        self.show_details_button.setEnabled(False)
        button_layout.addWidget(self.show_details_button)
        
        layout.addLayout(button_layout)
        
        return group
        
    def apply_layout(self):
        """Apply the selected layout algorithm."""
        layout_type = self.layout_combo.currentText()
        self.layout_changed.emit(layout_type)
        
    def reset_view(self):
        """Signal to reset the visualization view."""
        # This would be connected to the visualizer's reset method
        pass
        
    def update_project_info(self, project_data: Dict[str, Any]):
        """Update the project information display."""
        self.current_project_info = project_data
        
        # Update project name
        name = project_data.get('name', 'Unknown Project')
        self.project_name_label.setText(name)
        
        # Update path
        path = project_data.get('path', '')
        self.project_path_label.setText(path)
        
        # Update stats with real data
        total_labels = project_data.get('labels', 0)
        self.total_labels_label.setText(str(total_labels))
        
        rpy_files = project_data.get('rpy_files', 0)
        self.rpy_files_label.setText(str(rpy_files))
        
        dialogue_lines = project_data.get('dialogue_lines', 0)
        self.dialogue_lines_label.setText(str(dialogue_lines))
        
    def clear_project_info(self):
        """Clear the project information display."""
        self.current_project_info = None
        
        self.project_name_label.setText("No project loaded")
        self.project_path_label.setText("-")
        self.total_labels_label.setText("-")
        self.rpy_files_label.setText("-")
        self.dialogue_lines_label.setText("-")
        
    def update_node_details(self, node_id: str, node_data: Dict[str, Any]):
        """Update the selected node details display."""
        self.current_node_data = node_data
        
        # Format node information
        info_text = f"Label: {node_id}\n\n"
        
        # Add basic node properties
        if 'file_path' in node_data:
            info_text += f"File: {node_data['file_path']}\n"
        if 'line_number' in node_data:
            info_text += f"Line: {node_data['line_number']}\n"
        
        info_text += "\nProperties:\n"
        if node_data.get('has_menu', False):
            info_text += "• Has menu choices\n"
        if node_data.get('has_dialogue', False):
            info_text += "• Contains dialogue\n"
        if node_data.get('is_reachable', True):
            info_text += "• Reachable from start\n"
        if node_data.get('is_dead_end', False):
            info_text += "• Dead end (no outgoing flows)\n"
        
        # Add flow information
        incoming_flows = node_data.get('incoming_flows', [])
        outgoing_flows = node_data.get('outgoing_flows', [])
        
        info_text += f"\nConnections:\n"
        info_text += f"• Incoming: {len(incoming_flows)}\n"
        info_text += f"• Outgoing: {len(outgoing_flows)}\n"
        
        if outgoing_flows:
            info_text += "\nOutgoing Connections:\n"
            for flow in outgoing_flows[:5]:  # Show first 5
                target = flow.get('target_label', 'Unknown')
                flow_type = flow.get('flow_type', 'unknown')
                info_text += f"• {target} ({flow_type})\n"
            
            if len(outgoing_flows) > 5:
                info_text += f"... and {len(outgoing_flows) - 5} more\n"
        
        self.node_info.setPlainText(info_text)
        
        # Enable action buttons
        self.highlight_button.setEnabled(True)
        self.show_details_button.setEnabled(True)
        
    def clear_node_details(self):
        """Clear the node details display."""
        self.current_node_data = None
        self.node_info.setPlainText("No node selected")
        self.highlight_button.setEnabled(False)
        self.show_details_button.setEnabled(False) 