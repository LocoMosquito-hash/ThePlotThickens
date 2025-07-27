"""
VN Control Panel Widget

Side panel for controlling visualization options, displaying project information,
and showing details about selected nodes.
"""

from typing import Dict, Any, Optional, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QPushButton, QComboBox, QTextEdit, QScrollArea, QFrame,
    QGridLayout, QSizePolicy, QLineEdit, QCheckBox, QTreeWidget,
    QTreeWidgetItem, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QAction


class VNControlPanel(QWidget):
    """
    Control panel for the VN Flow Visualizer.
    
    Provides controls for layout, project information display,
    and detailed node information.
    """
    
    layout_changed = pyqtSignal(str)  # layout_type
    search_node = pyqtSignal(str)  # node_name
    edge_highlighting_changed = pyqtSignal(bool)  # highlight_enabled
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_project_info: Optional[Dict[str, Any]] = None
        self.current_node_data: Optional[Dict[str, Any]] = None
        self.visualizer = None  # Reference to visualizer for accessing connection data
        
        self.setup_ui()
        
    def set_visualizer(self, visualizer):
        """Set reference to the visualizer to access VisualizationData."""
        self.visualizer = visualizer
        
    def setup_ui(self):
        """Set up the control panel interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)  # Reduced spacing
        layout.setContentsMargins(3, 3, 3, 3)  # Reduced margins
        
        # Node Search section
        search_group = self.create_search_section()
        layout.addWidget(search_group)
        
        # Layout Controls section
        layout_group = self.create_layout_controls()
        layout.addWidget(layout_group)
        
        # Visual Options section
        visual_group = self.create_visual_options_section()
        layout.addWidget(visual_group)
        
        # Project Information section
        self.project_group = self.create_project_info_section()
        layout.addWidget(self.project_group)
        
        # Selected Node Details section
        self.node_group = self.create_node_details_section()
        layout.addWidget(self.node_group)
        
        # Add stretch to push everything up
        layout.addStretch()
        
    def create_search_section(self) -> QGroupBox:
        """Create the node search section."""
        group = QGroupBox("Find Node")
        layout = QVBoxLayout(group)
        layout.setSpacing(3)
        
        # Search input
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter node name (e.g., ch4ashbagdone)")
        self.search_input.returnPressed.connect(self.perform_search)
        search_layout.addWidget(self.search_input)
        
        self.search_button = QPushButton("Find")
        self.search_button.clicked.connect(self.perform_search)
        search_layout.addWidget(self.search_button)
        
        layout.addLayout(search_layout)
        
        # Search help text
        help_text = QLabel("Enter partial or full node name\nPress Enter or click Find")
        help_text.setFont(QFont("", 7))
        help_text.setStyleSheet("color: gray;")
        layout.addWidget(help_text)
        
        return group
        
    def perform_search(self):
        """Emit search signal with the search text."""
        search_text = self.search_input.text().strip()
        if search_text:
            self.search_node.emit(search_text)
            
    def on_edge_highlighting_changed(self, state):
        """Handle edge highlighting checkbox state change."""
        enabled = state == Qt.CheckState.Checked.value
        self.edge_highlighting_changed.emit(enabled)
        
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
            "narrative", "narrative_flow", "flow_aware", "dot_like", "topological", "spring", "circular", "hierarchical", "random"
        ])
        self.layout_combo.setCurrentText("dot_like")
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
        
        # Add layout help text
        help_text = QLabel("• Narrative: Story-aware flow\n• Narrative Flow: True story progression\n• Flow Aware: Phase 3 - JumpAnalyzer+FlowTracer intelligence\n• DOT-like: Sugiyama framework\n• Topological: DAG layers")
        help_text.setFont(QFont("", 7))
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: gray;")
        layout.addWidget(help_text)
        
        return group
        
    def create_visual_options_section(self) -> QGroupBox:
        """Create the visual options controls."""
        group = QGroupBox("Visual Options")
        layout = QVBoxLayout(group)
        layout.setSpacing(3)  # Reduced spacing
        
        # Edge highlighting checkbox
        self.highlight_edges_checkbox = QCheckBox("Highlight selected node edges")
        self.highlight_edges_checkbox.setToolTip(
            "When enabled, selected node's incoming edges will be colored yellow\n"
            "and outgoing edges will be colored red"
        )
        self.highlight_edges_checkbox.stateChanged.connect(self.on_edge_highlighting_changed)
        layout.addWidget(self.highlight_edges_checkbox)
        
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
        
        # Node relationships tree widget
        self.relationships_tree = QTreeWidget()
        self.relationships_tree.setHeaderHidden(True)
        self.relationships_tree.setMaximumHeight(150)  # Compact size
        self.relationships_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.relationships_tree.customContextMenuRequested.connect(self.show_tree_context_menu)
        # Same small font as the text edit
        self.relationships_tree.setFont(small_font)
        layout.addWidget(self.relationships_tree)
        
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
        # This should be connected to the visualizer's reset method in the main window
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
        # Handle case when no node is selected
        if not node_id or not node_data:
            self.clear_node_details()
            return
            
        self.current_node_data = node_data
        
        # Format node information
        info_text = f"Label: {node_id}\n"
        
        # Special handling for menu choice nodes - show the choice text
        if '_choice_' in node_id and 'full_text' in node_data:
            choice_text = node_data['full_text']
            info_text += f"\nChoice Text: \"{choice_text}\"\n"
            
            # Show parent container
            if 'parent_container' in node_data:
                parent = node_data['parent_container']
                info_text += f"Parent Menu: {parent}\n"
                
            # Show choice index
            if 'choice_index' in node_data:
                choice_idx = node_data['choice_index']
                info_text += f"Choice Index: {choice_idx}\n"
            
            # Show destination if available
            if 'destination' in node_data:
                destination = node_data['destination']
                info_text += f"Destination: {destination}\n"
                
            # Show action type
            if 'action_type' in node_data:
                action_type = node_data['action_type']
                info_text += f"Action Type: {action_type}\n"
                
            # Show condition if available
            if 'condition' in node_data and node_data['condition']:
                condition = node_data['condition']
                info_text += f"Condition: {condition}\n"
        
        # Special handling for menu container nodes
        elif '_menu_' in node_id and 'prompt' in node_data:
            if node_data['prompt']:
                info_text += f"\nMenu Prompt: \"{node_data['prompt']}\"\n"
            
            if 'total_choices' in node_data:
                total_choices = node_data['total_choices']
                info_text += f"Total Choices: {total_choices}\n"
                
            if 'parent_label' in node_data:
                parent_label = node_data['parent_label']
                info_text += f"Parent Label: {parent_label}\n"
        
        info_text += "\n"
        
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
        
        # Populate the relationships tree
        self.populate_relationships_tree(node_id, node_data)
        
        # Enable action buttons
        self.highlight_button.setEnabled(True)
        self.show_details_button.setEnabled(True)
        
    def clear_node_details(self):
        """Clear the node details display."""
        self.current_node_data = None
        self.node_info.setPlainText("No node selected")
        self.relationships_tree.clear()
        self.highlight_button.setEnabled(False)
        self.show_details_button.setEnabled(False)
        
    def show_tree_context_menu(self, position):
        """Show context menu for tree items."""
        item = self.relationships_tree.itemAt(position)
        if not item:
            return
            
        # Don't show context menu for category items (Parents, Children, Siblings)
        if not item.parent():
            return
            
        menu = QMenu(self)
        
        # Simple placeholder actions
        go_to_action = QAction("Go to Node", self)
        go_to_action.triggered.connect(lambda: self.placeholder_action("Go to Node", item))
        menu.addAction(go_to_action)
        
        highlight_action = QAction("Highlight Path", self)
        highlight_action.triggered.connect(lambda: self.placeholder_action("Highlight Path", item))
        menu.addAction(highlight_action)
        
        details_action = QAction("Show Details", self)
        details_action.triggered.connect(lambda: self.placeholder_action("Show Details", item))
        menu.addAction(details_action)
        
        menu.exec(self.relationships_tree.mapToGlobal(position))
        
    def placeholder_action(self, action_name: str, item: QTreeWidgetItem):
        """Placeholder for future implementation."""
        node_id = item.data(0, Qt.ItemDataRole.UserRole)
        print(f"Future implementation: {action_name} for node {node_id}")
        
    def populate_relationships_tree(self, node_id: str, node_data: Dict[str, Any]):
        """Populate the relationships tree with Parents, Children, and Siblings."""
        self.relationships_tree.clear()
        
        # Add node_id to node_data for the extraction methods
        enhanced_node_data = node_data.copy()
        enhanced_node_data['node_id'] = node_id
        
        # Extract relationships from VisualizationConnection objects
        parents = self.extract_parents(enhanced_node_data)
        children = self.extract_children(enhanced_node_data)
        siblings = self.extract_siblings(node_id, enhanced_node_data, parents)
        
        # Create category items
        parents_item = QTreeWidgetItem([f"Parents ({len(parents)})"])
        children_item = QTreeWidgetItem([f"Children ({len(children)})"])
        siblings_item = QTreeWidgetItem([f"Siblings ({len(siblings)})"])
        
        self.relationships_tree.addTopLevelItem(parents_item)
        self.relationships_tree.addTopLevelItem(children_item)
        self.relationships_tree.addTopLevelItem(siblings_item)
        
        # Populate parents
        for parent_id in parents:
            parent_node = QTreeWidgetItem([parent_id])
            parent_node.setData(0, Qt.ItemDataRole.UserRole, parent_id)
            parents_item.addChild(parent_node)
            
        # Populate children
        for child_id in children:
            child_node = QTreeWidgetItem([child_id])
            child_node.setData(0, Qt.ItemDataRole.UserRole, child_id)
            children_item.addChild(child_node)
            
        # Populate siblings
        for sibling_id in siblings:
            sibling_node = QTreeWidgetItem([sibling_id])
            sibling_node.setData(0, Qt.ItemDataRole.UserRole, sibling_id)
            siblings_item.addChild(sibling_node)
        
        # Expand all categories by default
        self.relationships_tree.expandAll()
        
    def extract_parents(self, node_data: Dict[str, Any]) -> List[str]:
        """Extract immediate parent node IDs from VisualizationConnection objects."""
        if not self.visualizer or not hasattr(self.visualizer, 'current_data') or not self.visualizer.current_data:
            return []
        
        current_node_id = node_data.get('node_id', '')
        if not current_node_id:
            return []
        
        parents = []
        
        # Find all connections that target this node
        for connection in self.visualizer.current_data.connections:
            if connection.target_node_id == current_node_id:
                parents.append(connection.source_node_id)
        
        return sorted(list(set(parents)))  # Remove duplicates
        
    def extract_children(self, node_data: Dict[str, Any]) -> List[str]:
        """Extract immediate children node IDs from VisualizationConnection objects."""
        if not self.visualizer or not hasattr(self.visualizer, 'current_data') or not self.visualizer.current_data:
            return []
        
        current_node_id = node_data.get('node_id', '')
        if not current_node_id:
            return []
        
        children = []
        
        # Find all connections that originate from this node
        for connection in self.visualizer.current_data.connections:
            if connection.source_node_id == current_node_id:
                children.append(connection.target_node_id)
        
        return sorted(list(set(children)))  # Remove duplicates
        
    def extract_siblings(self, node_id: str, node_data: Dict[str, Any], parents: List[str]) -> List[str]:
        """Extract sibling node IDs (nodes that share the same immediate parents)."""
        if not self.visualizer or not hasattr(self.visualizer, 'current_data') or not self.visualizer.current_data:
            return []
        
        if not parents:
            return []
        
        siblings = set()
        
        # For each parent, find all its children (excluding current node)
        for parent_id in parents:
            for connection in self.visualizer.current_data.connections:
                if connection.source_node_id == parent_id and connection.target_node_id != node_id:
                    siblings.add(connection.target_node_id)
        
        return sorted(list(siblings)) 