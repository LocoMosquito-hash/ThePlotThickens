"""
VN Flow Visualizer Widget

Interactive PyQt6 QGraphicsView-based visualization for Renpy narrative flow graphs.
This widget handles the display, interaction, and manipulation of VN branching structures.
"""

import math
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsObject,
    QGraphicsEllipseItem, QGraphicsPathItem, QGraphicsTextItem,
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMenu, QMessageBox, QGraphicsRectItem, QGraphicsLineItem
)
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import (
    QPen, QBrush, QColor, QPainter, QPainterPath, QFont,
    QPolygonF, QLinearGradient, QRadialGradient, QMouseEvent
)
import networkx as nx

# Import renpy-source-api control flow modules
try:
    # Add path for renpy-source-api imports
    current_dir = Path(__file__).parent
    app_dir = current_dir.parent.parent / "app"
    renpy_api_dir = app_dir / "renpy-source-api"
    sys.path.insert(0, str(renpy_api_dir))
    
    from control_flow.start_label_finder import StartLabelFinder
    from control_flow.analyze_vn_menus import MenuAnalyzer
    from control_flow.analyze_vn_jumps import analyze_jumps_in_vn
    CONTROL_FLOW_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import control_flow modules: {e}")
    CONTROL_FLOW_AVAILABLE = False

# Import the new menu graphics components
from menu_graphics_items import MenuContainerGraphicsItem, ChoiceButtonGraphicsItem


class VNLabelNode(QGraphicsObject):
    """
    A custom QGraphicsItem representing a Renpy label in the flow graph.
    
    Visual representation of story labels with different styles based on properties
    (start label, menu choices, endings, etc.)
    """
    
    def __init__(self, node_id: str, node_data: Dict[str, Any], semantic_classification: str = "linear", parent=None):
        super().__init__(parent)
        
        self.node_id = node_id
        self.node_data = node_data
        self.node_name = node_data.get('name', node_id)
        self.semantic_classification = semantic_classification
        
        # Visual properties
        self.base_width = 120  # Base width for rectangular nodes
        self.height = 40       # Height of rectangular nodes
        self.selected_scale = 1.2  # Scale factor when selected
        self.colors = self._determine_colors()
        
        # Calculate dynamic width based on text length
        self.width = max(self.base_width, len(self.node_name) * 8 + 20)
        
        # State
        self._selected = False
        self._highlighted = False
        
        # Make item interactive
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)
        
        # Accept hover events for tooltips
        self.setAcceptHoverEvents(True)
        
    def _determine_colors(self) -> Dict[str, QColor]:
        """Determine node colors based on semantic classification."""
        
        # Phase 2: Intelligent Node Classification Color Scheme
        color_map = {
            'start': QColor(100, 250, 100),         # Green - True start node
            'decision': QColor(250, 200, 100),      # Yellow - Decision points (legacy)
            'decision_point': QColor(255, 215, 0),  # GOLD - Menu decision points from MenuAnalyzer
            'menu_container': QColor(255, 140, 0),  # ORANGE - Menu container nodes
            'linear': QColor(100, 150, 250),        # Blue - Linear story progression
            'orphaned': QColor(150, 150, 150),      # Gray - Orphaned/unreachable nodes
            'jump_target': QColor(200, 100, 250),   # Purple - Jump targets
        }
        
        # Get base color from semantic classification
        base_color = color_map.get(self.semantic_classification, QColor(100, 150, 250))
        
        # Priority 1: Check node_type (overrides everything)
        node_type = self.node_data.get('node_type')
        if node_type == 'menu_container':
            base_color = QColor(255, 140, 0)  # ORANGE for menu containers
        # Priority 2: Special handling for endings (no outgoing flows)
        elif not self.node_data.get('outgoing_flows', []) and self.semantic_classification != 'orphaned':
            base_color = QColor(250, 100, 100)  # Red for endings
            
        return {
            'normal': base_color,
            'hover': base_color.lighter(120),
            'selected': base_color.darker(120),
            'text': QColor(255, 255, 255)
        }
        
    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of this item."""
        scale = self.selected_scale if self._selected else 1.0
        width = self.width * scale
        height = self.height * scale
        return QRectF(-width/2, -height/2, width, height)
        
    def paint(self, painter: QPainter, option, widget=None):
        """Paint the node."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Determine current size and color
        scale = self.selected_scale if self._selected else 1.0
        width = self.width * scale
        height = self.height * scale
        color = self.colors['selected'] if self._selected else \
                self.colors['hover'] if self._highlighted else \
                self.colors['normal']
        
        # Create gradient
        gradient = QLinearGradient(0, -height/2, 0, height/2)
        gradient.setColorAt(0, color.lighter(130))
        gradient.setColorAt(1, color.darker(110))
        
        # Draw rounded rectangle
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(color.darker(140), 2))
        rect = QRectF(-width/2, -height/2, width, height)
        painter.drawRoundedRect(rect, 8, 8)  # 8px corner radius
        
        # Draw text
        painter.setPen(QPen(self.colors['text']))
        font = QFont()
        font.setBold(True)
        font.setPointSize(9)  # Fixed size for better readability
        painter.setFont(font)
        
        # Calculate text rectangle with padding
        text_rect = QRectF(-width/2 + 8, -height/2 + 5, width - 16, height - 10)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, self.node_name)
        
        # Draw special indicators
        if self.node_data.get('has_menu', False):
            # Draw menu indicator (small triangle in top-right corner)
            triangle = QPolygonF([
                QPointF(width/2 - 15, -height/2 + 5),
                QPointF(width/2 - 5, -height/2 + 5),
                QPointF(width/2 - 10, -height/2 + 15)
            ])
            painter.setBrush(QBrush(QColor(255, 255, 0)))
            painter.drawPolygon(triangle)
            
    def hoverEnterEvent(self, event):
        """Handle mouse hover enter."""
        self._highlighted = True
        self.update()
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        """Handle mouse hover leave."""
        self._highlighted = False
        self.update()
        super().hoverLeaveEvent(event)
        
    def mousePressEvent(self, event):
        """Handle mouse press for selection."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.setSelected(True)
        elif event.button() == Qt.MouseButton.RightButton:
            self.show_context_menu(event.screenPos())
        super().mousePressEvent(event)
        
    def show_context_menu(self, pos):
        """Show context menu for node."""
        menu = QMenu()
        
        # Node info action
        info_action = menu.addAction(f"Label: {self.node_name}")
        info_action.setEnabled(False)
        
        menu.addSeparator()
        
        # File location
        file_path = self.node_data.get('file_path', 'Unknown')
        line_num = self.node_data.get('line_number', 0)
        location_action = menu.addAction(f"Location: {file_path}:{line_num}")
        location_action.triggered.connect(lambda: self.show_file_location())
        
        # Show outgoing connections
        outgoing = self.node_data.get('outgoing_flows', [])
        if outgoing:
            menu.addSeparator()
            submenu = menu.addMenu(f"Connects to ({len(outgoing)})")
            for target in outgoing:
                action = submenu.addAction(target)
                action.triggered.connect(lambda checked, t=target: self.highlight_path_to(t))
                
        menu.exec(pos)
        
    def show_file_location(self):
        """Show file location details."""
        file_path = self.node_data.get('file_path', 'Unknown')
        line_num = self.node_data.get('line_number', 0)
        QMessageBox.information(
            None, "Label Location",
            f"Label: {self.node_name}\n"
            f"File: {file_path}\n"
            f"Line: {line_num}"
        )
        
    def highlight_path_to(self, target_node: str):
        """Highlight path to target node."""
        # This will be implemented when we add path highlighting
        pass
        
    def itemChange(self, change, value):
        """Handle item changes (like position updates)."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Notify connected edges to update
            if hasattr(self, 'connected_edges'):
                for edge in self.connected_edges:
                    edge.update_path()
        return super().itemChange(change, value)


class VNFlowConnection(QGraphicsPathItem):
    """
    A custom QGraphicsPathItem representing connections between labels.
    
    Draws bezier curves with arrows to show narrative flow.
    """
    
    def __init__(self, source_node: VNLabelNode, target_node: VNLabelNode, 
                 connection_data: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        
        self.source_node = source_node
        self.target_node = target_node
        self.connection_data = connection_data or {}
        
        # Visual properties
        self.arrow_size = 15
        self.line_width = 2
        self.color = QColor(100, 100, 100)
        
        # Set up path
        self.setPen(QPen(self.color, self.line_width))
        self.setZValue(-1)  # Draw behind nodes
        
        # Connect to nodes
        if not hasattr(source_node, 'connected_edges'):
            source_node.connected_edges = []
        if not hasattr(target_node, 'connected_edges'):
            target_node.connected_edges = []
            
        source_node.connected_edges.append(self)
        target_node.connected_edges.append(self)
        
        self.update_path()
        
    def _get_rectangle_intersection(self, center_pos: QPointF, ux: float, uy: float, node: 'VNLabelNode', is_source: bool) -> QPointF:
        """Calculate intersection point of line with rectangular node edge."""
        # NEW: Choice-aware landing zones for MenuContainerGraphicsItem
        if hasattr(node, 'container_width') and hasattr(node, 'get_outgoing_connection_point'):
            # This is a MenuContainerGraphicsItem - use sophisticated landing zones
            
            if is_source:
                # Outgoing connection FROM menu container
                # Use the target destination to find the appropriate choice zone
                target_destination = self.connection_data.get('target_destination')
                if target_destination:
                    landing_point = node.get_outgoing_connection_point(target_destination)
                    if landing_point:
                        # Convert from local to scene coordinates
                        return node.mapToScene(landing_point)
                
                # Fallback to center-right if no specific choice found
                container_rect = node.rect()
                fallback_point = QPointF(container_rect.right(), container_rect.center().y())
                return node.mapToScene(fallback_point)
            
            else:
                # Incoming connection TO menu container
                # Use header zone or general connection logic
                import math
                connection_angle = math.atan2(uy, ux)
                
                # For incoming connections, use header zone (simpler approach)
                landing_zones = node.calculate_choice_landing_zones()
                if 'header' in landing_zones:
                    header_zone = landing_zones['header']['boundaries']
                    header_center_y = header_zone['choice_center_y']
                    
                    # Choose side based on connection angle
                    angle = connection_angle % (2 * math.pi)
                    if angle < math.pi / 2 or angle > 3 * math.pi / 2:
                        # Coming from left -> land on left side of header
                        landing_point = QPointF(header_zone['left_top'][0], header_center_y)
                    else:
                        # Coming from right -> land on right side of header  
                        landing_point = QPointF(header_zone['right_top'][0], header_center_y)
                    
                    return node.mapToScene(landing_point)
                
                # Fallback to center-left for incoming
                container_rect = node.rect()
                fallback_point = QPointF(container_rect.left(), container_rect.center().y())
                return node.mapToScene(fallback_point)
        
        # EXISTING: Standard rectangular intersection for VNLabelNode
        if hasattr(node, 'width'):
            # VNLabelNode
            half_width = node.width / 2
            half_height = node.height / 2
        else:
            # Fallback for unknown node types
            rect = node.boundingRect()
            half_width = rect.width() / 2
            half_height = rect.height() / 2
        
        # Calculate intersection with rectangle edges
        # We need to find which edge the line intersects first
        
        # Time to reach each edge (if moving in direction ux, uy)
        if ux != 0:
            t_right = half_width / abs(ux) if ux > 0 else float('inf')
            t_left = half_width / abs(ux) if ux < 0 else float('inf')
        else:
            t_right = t_left = float('inf')
            
        if uy != 0:
            t_bottom = half_height / abs(uy) if uy > 0 else float('inf')
            t_top = half_height / abs(uy) if uy < 0 else float('inf')
        else:
            t_bottom = t_top = float('inf')
        
        # Find the minimum time (closest edge)
        t_min = min(t_right, t_left, t_bottom, t_top)
        
        # Calculate intersection point
        if t_min == float('inf'):
            # No intersection (shouldn't happen), return center
            return center_pos
        
        # Calculate the actual intersection point
        intersection_x = center_pos.x() + ux * t_min
        intersection_y = center_pos.y() + uy * t_min
        
        # Clamp to rectangle bounds to avoid floating point errors
        intersection_x = max(center_pos.x() - half_width, min(center_pos.x() + half_width, intersection_x))
        intersection_y = max(center_pos.y() - half_height, min(center_pos.y() + half_height, intersection_y))
        
        return QPointF(intersection_x, intersection_y)

    def update_path(self):
        """Update the connection path between nodes."""
        if not self.source_node or not self.target_node:
            return
            
        # Get node positions (centers)
        source_pos = self.source_node.scenePos()
        target_pos = self.target_node.scenePos()
        
        # Calculate connection points (edge of rectangles)
        dx = target_pos.x() - source_pos.x()
        dy = target_pos.y() - source_pos.y()
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance == 0:
            return
            
        # Unit vector from source to target
        ux = dx / distance
        uy = dy / distance
        
        # Calculate intersection points with rectangular node edges
        start_point = self._get_rectangle_intersection(source_pos, ux, uy, self.source_node, True)
        end_point = self._get_rectangle_intersection(target_pos, -ux, -uy, self.target_node, False)
        
        # Create bezier curve
        path = QPainterPath()
        path.moveTo(start_point)
        
        # Control points for smooth curve
        control_offset = min(100, distance / 3)
        control1 = QPointF(start_point.x() + control_offset, start_point.y())
        control2 = QPointF(end_point.x() - control_offset, end_point.y())
        
        path.cubicTo(control1, control2, end_point)
        
        # Add arrow head
        arrow_path = self.create_arrow_head(control2, end_point)
        path.addPath(arrow_path)
        
        self.setPath(path)
        
    def create_arrow_head(self, control_point: QPointF, end_point: QPointF) -> QPainterPath:
        """Create arrow head at the end of the line."""
        # Calculate direction
        dx = end_point.x() - control_point.x()
        dy = end_point.y() - control_point.y()
        length = math.sqrt(dx*dx + dy*dy)
        
        if length == 0:
            return QPainterPath()
            
        # Unit vector
        ux = dx / length
        uy = dy / length
        
        # Arrow points
        arrow_length = self.arrow_size
        arrow_width = self.arrow_size * 0.6
        
        # Arrow tip points
        tip = end_point
        base1 = QPointF(
            tip.x() - arrow_length * ux + arrow_width * uy,
            tip.y() - arrow_length * uy - arrow_width * ux
        )
        base2 = QPointF(
            tip.x() - arrow_length * ux - arrow_width * uy,
            tip.y() - arrow_length * uy + arrow_width * ux
        )
        
        # Create arrow path
        arrow = QPainterPath()
        arrow.moveTo(tip)
        arrow.lineTo(base1)
        arrow.lineTo(base2)
        arrow.closeSubpath()
        
        return arrow


class VNFlowVisualizer(QGraphicsView):
    """
    Main visualization widget for Renpy narrative flow graphs.
    
    Provides interactive display, layout, and manipulation of VN branching structures.
    """
    
    node_selected = pyqtSignal(str, dict)  # node_id, node_data
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize graphics components
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # Storage for graph elements
        self.nodes: Dict[str, VNLabelNode] = {}
        self.connections: List[VNFlowConnection] = []
        self.graph: Optional[nx.DiGraph] = None
        self.current_flow_graph: Optional[Dict[str, Any]] = None
        
        # Semantic analysis data
        self.project_path: Optional[str] = None
        self.semantic_start_node: Optional[str] = None
        self.semantic_classifications: Dict[str, str] = {}  # node_id -> classification
        
        # Middle mouse button state
        self._middle_button_pressed = False
        
        # Set up view properties
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # Connect scene selection changes
        self.scene.selectionChanged.connect(self.on_selection_changed)
        
    def load_flow_graph(self, analysis_data: Dict[str, Any]):
        """
        Load and visualize a flow graph from renpy-source-api analysis data.
        
        Args:
            analysis_data: Complete analysis data from ProjectAnalysisThread
        """
        self.clear_visualization()
        
        # Extract flow graph data
        flow_graph = analysis_data.get('flow_graph', {})
        if not flow_graph:
            return
            
        # Store current graph data
        self.current_flow_graph = analysis_data
        
        # Extract project path for semantic analysis
        self.project_path = analysis_data.get('project_path')
        
        # Find the semantic start node using StartLabelFinder
        self.semantic_start_node = self._find_semantic_start_node(self.project_path)
        
        # Convert renpy-source-api flow graph to NetworkX format
        self.graph = self._convert_flow_graph_to_networkx(flow_graph)
        
        # Perform semantic node classification
        self.semantic_classifications = self._classify_nodes_semantically(self.project_path)
        
        # Create visualization
        self.create_visualization()
        
    def _convert_flow_graph_to_networkx(self, flow_graph: Dict[str, Any]) -> nx.DiGraph:
        """
        Convert renpy-source-api flow graph format to NetworkX DiGraph.
        
        Args:
            flow_graph: Flow graph data from renpy-source-api
            
        Returns:
            NetworkX directed graph
        """
        G = nx.DiGraph()
        
        # Add nodes with their properties
        for label_name, label_data in flow_graph.items():
            # Determine node type for color coding
            node_type = self._determine_node_type(label_name, label_data)
            
            # Add node with attributes
            G.add_node(label_name, 
                name=label_data.get('name', label_name),
                file_path=label_data.get('file_path', ''),
                line_number=label_data.get('line_number', 0),
                has_menu=label_data.get('has_menu', False),
                has_dialogue=label_data.get('has_dialogue', False),
                is_reachable=label_data.get('is_reachable', True),
                is_dead_end=label_data.get('is_dead_end', False),
                flow_complexity=label_data.get('flow_complexity', 0),
                node_type=node_type,
                incoming_flows=label_data.get('incoming_flows', []),
                outgoing_flows=label_data.get('outgoing_flows', [])
            )
        
        # Add edges from outgoing flows
        for label_name, label_data in flow_graph.items():
            outgoing_flows = label_data.get('outgoing_flows', [])
            
            for flow in outgoing_flows:
                target_label = flow.get('target_label')
                if target_label and target_label in flow_graph:
                    # Add edge with flow properties
                    G.add_edge(label_name, target_label,
                        flow_type=flow.get('flow_type', 'unknown'),
                        context=flow.get('context', ''),
                        condition=flow.get('condition', ''),
                        source_file=flow.get('file_path', ''),
                        source_line=flow.get('line_number', 0)
                    )
        
        return G
        
    def _determine_node_type(self, label_name: str, label_data: Dict[str, Any]) -> str:
        """
        Determine the node type for color coding.
        
        Args:
            label_name: Name of the label
            label_data: Label data from flow graph
            
        Returns:
            Node type string ('start', 'menu', 'ending', 'regular')
        """
        # Check for start label
        if label_name.lower() in ['start', 'main', 'begin', 'intro']:
            return 'start'
            
        # Check for menu/choice points
        if label_data.get('has_menu', False):
            return 'menu'
            
        # Check for ending labels (no outgoing flows)
        if label_data.get('is_dead_end', False) or not label_data.get('outgoing_flows', []):
            return 'ending'
            
        # Default to regular label
        return 'regular'
        
    def clear_visualization(self):
        """Clear current visualization."""
        self.scene.clear()
        self.nodes.clear()
        self.connections.clear()
        
    def create_visualization(self):
        """Create visual elements from flow graph data with menu containers."""
        if not self.graph:
            return
        
        # Step 1: Create all regular nodes with semantic classification
        for node_id in self.graph.nodes:
            semantic_classification = self.semantic_classifications.get(node_id, "linear")
            node_item = VNLabelNode(node_id, self.graph.nodes[node_id], semantic_classification)
            self.scene.addItem(node_item)
            self.nodes[node_id] = node_item
        
        # Step 2: Create menu container nodes and build edge mapping
        menu_containers = {}
        menu_choice_edges = set()
        
        # Analyze flow graph data to find menu containers needed
        for node_id, node_data in self.graph.nodes.items():
            outgoing_flows = node_data.get('outgoing_flows', [])
            menu_choices = [flow for flow in outgoing_flows 
                          if flow.get('flow_type') == 'menu_choice']
            
            if menu_choices:
                # Create menu container node with proper choice data
                menu_node_id = f"{node_id}_menu_container"
                
                # Prepare menu choice data for the graphics item
                choice_data_list = []
                seen_destinations = set()  # Track destinations to avoid duplicates
                
                for choice in menu_choices:
                    destination = choice.get('target_label')
                    
                    # Skip if we've already seen this destination
                    if destination and destination in seen_destinations:
                        continue
                        
                    choice_data = {
                        'text': choice.get('choice_text', f"Choice -> {destination or 'unknown'}"),
                        'destination': destination,
                        'condition': choice.get('condition', ''),
                        'flow_type': choice.get('flow_type', 'menu_choice')
                    }
                    
                    choice_data_list.append(choice_data)
                    if destination:
                        seen_destinations.add(destination)
                
                # Create the new menu container graphics item
                menu_item = MenuContainerGraphicsItem(menu_node_id, choice_data_list)
                self.scene.addItem(menu_item)
                self.nodes[menu_node_id] = menu_item
                menu_containers[node_id] = menu_node_id
                
                # Track which edges should go through menu containers
                for choice in menu_choices:
                    target = choice.get('target_label')
                    if target:
                        menu_choice_edges.add((node_id, target))
        
        # Step 3: Create connections with menu container logic
        for source_id, target_id in self.graph.edges:
            if source_id in self.nodes and target_id in self.nodes:
                edge_data = self.graph.edges[source_id, target_id]
                edge_key = (source_id, target_id)
                
                # Check if this edge should go through a menu container
                if edge_key in menu_choice_edges and source_id in menu_containers:
                    menu_container_id = menu_containers[source_id]
                    
                    # Create: label -> menu container
                    if source_id in self.nodes and menu_container_id in self.nodes:
                        connection1 = VNFlowConnection(
                            self.nodes[source_id], 
                            self.nodes[menu_container_id], 
                            {'flow_type': 'to_menu', 'style': 'menu_entry'}
                        )
                        self.scene.addItem(connection1)
                        self.connections.append(connection1)
                    
                    # Create: menu container -> target
                    if menu_container_id in self.nodes and target_id in self.nodes:
                        connection2 = VNFlowConnection(
                            self.nodes[menu_container_id], 
                            self.nodes[target_id], 
                            {'flow_type': 'menu_choice', 'style': 'menu_choice', 'target_destination': target_id}
                        )
                        self.scene.addItem(connection2)
                        self.connections.append(connection2)
                else:
                    # Create direct connection for non-menu edges
                    source_node = self.nodes[source_id]
                    target_node = self.nodes[target_id]
                    connection = VNFlowConnection(source_node, target_node, edge_data)
                    self.scene.addItem(connection)
                    self.connections.append(connection)
                
        # Apply initial layout and ensure proper scaling
        self.apply_layout('narrative')
        
        # Force fit view to content with proper margins
        self.fitInView(self.scene.itemsBoundingRect().adjusted(-50, -50, 50, 50), 
                      Qt.AspectRatioMode.KeepAspectRatio)
        
    def fit_view_to_content(self):
        """Fit the view to show all content with proper margins."""
        if self.scene.items():
            bounding_rect = self.scene.itemsBoundingRect()
            # Add margins around the content
            margined_rect = bounding_rect.adjusted(-100, -100, 100, 100)
            self.fitInView(margined_rect, Qt.AspectRatioMode.KeepAspectRatio)
            
    def apply_layout(self, layout_type: str = 'narrative'):
        """Apply layout algorithm to position nodes with narrative awareness."""
        if not self.graph or not self.nodes:
            return
        
        # Debug output
        self._debug_graph_analysis(layout_type)
            
        # Handle different layout types
        if layout_type == 'narrative':
            pos = self._narrative_hierarchical_layout()
        elif layout_type == 'narrative_flow':
            pos = self._narrative_flow_layout()
        elif layout_type == 'topological':
            pos = self._topological_layout()
        elif layout_type == 'spring':
            pos = nx.spring_layout(self.graph, k=3, iterations=100)
        elif layout_type == 'circular':
            pos = nx.circular_layout(self.graph)
        elif layout_type == 'hierarchical':
            try:
                pos = nx.nx_agraph.graphviz_layout(self.graph, prog='dot')
            except:
                pos = self._narrative_hierarchical_layout()  # Fallback to narrative
        elif layout_type == 'dot_like':
            pos = self._dot_like_layout()
        elif layout_type == 'random':
            pos = nx.random_layout(self.graph)
        elif layout_type == 'flow_aware':
            pos = self._flow_aware_layout()
        else:
            pos = self._narrative_hierarchical_layout()  # Default to narrative
        
        # Scale positions for better visibility
        scale = 400
        scaled_pos = {node: (x * scale, y * scale) for node, (x, y) in pos.items()}
        
        # Apply positions to nodes
        for node_id, (x, y) in scaled_pos.items():
            if node_id in self.nodes:
                self.nodes[node_id].setPos(x, y)
        
        # Step 2: Apply menu container positioning fixes
        self._position_menu_containers_relative_to_parents()
        
        # Update connections
        for connection in self.connections:
            connection.update_path()
            
        # Automatically fit view after layout
        self.fit_view_to_content()
        
    def _position_menu_containers_relative_to_parents(self):
        """
        Position menu container nodes relative to their parent label nodes.
        
        This fixes the issue where menu containers get positioned by layout algorithms
        as if they were disconnected nodes, causing them to pile up.
        """
        # Increased offset to prevent overlap, accounting for node widths
        base_offset = 140  # Base separation distance
        
        for node_id, node_item in self.nodes.items():
            if node_id.endswith('_menu_container'):
                # Extract parent node ID
                parent_id = node_id.replace('_menu_container', '')
                
                if parent_id in self.nodes:
                    parent_node = self.nodes[parent_id]
                    parent_pos = parent_node.pos()
                    
                    # Calculate separation based on node widths
                    # Parent node is VNLabelNode, menu container is MenuContainerGraphicsItem
                    parent_width = getattr(parent_node, 'width', 120)  # VNLabelNode width
                    menu_width = getattr(node_item, 'container_width', 200)  # MenuContainerGraphicsItem width
                    
                    # Ensure enough separation: half parent width + base offset + half menu width
                    separation = (parent_width / 2) + base_offset + (menu_width / 2)
                    
                    # Position menu container to the right of its parent with proper separation
                    menu_pos_x = parent_pos.x() + separation
                    menu_pos_y = parent_pos.y()  # Same vertical level
                    
                    node_item.setPos(menu_pos_x, menu_pos_y)
                    
                    print(f"Positioned {node_id} at ({menu_pos_x:.1f}, {menu_pos_y:.1f}) - separation: {separation:.1f}px")
        
    def _narrative_hierarchical_layout(self) -> Dict[str, Tuple[float, float]]:
        """
        Create a narrative-aware hierarchical layout that respects story progression.
        
        Handles:
        - Story progression from start to endings
        - Disconnected components separately  
        - Branching paths with vertical separation
        - Decision points kept central
        """
        pos = {}
        
        # Find disconnected components
        if self.graph.is_directed():
            components = list(nx.weakly_connected_components(self.graph))
        else:
            components = list(nx.connected_components(self.graph))
        
        component_width = 8  # Space between components
        current_x_offset = 0
        
        for component_nodes in components:
            # Create subgraph for this component
            subgraph = self.graph.subgraph(component_nodes).copy()
            
            # Get component layout
            component_pos = self._layout_narrative_component(subgraph)
            
            # Offset this component horizontally
            for node, (x, y) in component_pos.items():
                pos[node] = (x + current_x_offset, y)
            
            # Calculate component width for next offset
            if component_pos:
                min_x = min(x for x, y in component_pos.values())
                max_x = max(x for x, y in component_pos.values())
                current_x_offset += (max_x - min_x) + component_width
        
        return pos
        
    def _layout_narrative_component(self, subgraph: nx.DiGraph) -> Dict[str, Tuple[float, float]]:
        """Layout a single connected component with narrative awareness."""
        
        # Find potential start nodes using semantic detection
        start_candidates = self._find_start_nodes(subgraph, self.semantic_start_node)
        
        if not start_candidates:
            # If no clear start, use nodes with no incoming edges
            start_candidates = [n for n in subgraph.nodes() if subgraph.in_degree(n) == 0]
            
        if not start_candidates:
            # If still no start, pick node with highest out-degree
            start_candidates = [max(subgraph.nodes(), key=lambda n: subgraph.out_degree(n))]
        
        # Create narrative layers using BFS from start nodes
        layers = self._create_narrative_layers(subgraph, start_candidates)
        
        # Position nodes in layers
        return self._position_narrative_layers(layers, subgraph)
        
    def _find_semantic_start_node(self, project_path: Optional[str]) -> Optional[str]:
        """
        Find the true semantic start node using StartLabelFinder.
        
        Args:
            project_path: Path to the Renpy project's game directory
            
        Returns:
            The actual start label name, or None if not found
        """
        if not CONTROL_FLOW_AVAILABLE or not project_path:
            return None
            
        try:
            finder = StartLabelFinder(project_path)
            start_label_obj = finder.find_start_label()
            if start_label_obj and hasattr(start_label_obj, 'label_name'):
                start_label = start_label_obj.label_name
                print(f"Semantic start node detection: Found '{start_label}' in {project_path}")
                return start_label
            else:
                print(f"Semantic start node detection: No valid start label found in {project_path}")
                return None
        except Exception as e:
            print(f"Error finding semantic start node: {e}")
            return None
    
    def _classify_nodes_semantically(self, project_path: Optional[str]) -> Dict[str, str]:
        """
        Classify nodes based on semantic analysis using MenuAnalyzer, StartLabelFinder,
        and jump analysis for intelligent node coloring.
        
        Returns:
            Dict mapping node_id -> classification ('start', 'decision_point', 'jump_target', 'linear', 'orphaned')
        """
        classifications = {}
        
        if not project_path:
            # Fallback: classify based on graph structure only
            for node in self.graph.nodes():
                in_degree = self.graph.in_degree(node)
                out_degree = self.graph.out_degree(node)
                
                if in_degree == 0:
                    classifications[node] = 'orphaned'
                elif out_degree > 1:
                    classifications[node] = 'decision_point'
                else:
                    classifications[node] = 'linear'
            return classifications
        
        print("Starting semantic node classification...")
        
        try:
            # Import analysis modules
            from app.renpy_source_api.control_flow import StartLabelFinder
            from app.renpy_source_api.control_flow.analyze_vn_menus import analyze_menus_in_vn
            from app.renpy_source_api.control_flow.analyze_vn_jumps import analyze_jumps_in_vn
            
            # Step 1: Find semantic start node
            start_finder = StartLabelFinder(project_path)
            try:
                start_line = start_finder.find_start_label()
                start_node = start_line.label_name
                classifications[start_node] = 'start'
                print(f"Classified '{start_node}' as start node")
            except Exception as e:
                print(f"Warning: Could not find start label: {e}")
                start_node = None
            
            # Step 2: Find decision points using MenuAnalyzer
            try:
                menu_analysis = analyze_menus_in_vn(project_path)
                decision_nodes = set()
                
                for menu_info in menu_analysis.get('menus', []):
                    # Get the label that contains this menu
                    if 'label' in menu_info:
                        decision_nodes.add(menu_info['label'])
                    # Also check if the menu creates jump targets
                    for choice in menu_info.get('choices', []):
                        if choice.get('has_jumps', False) and choice.get('destination'):
                            decision_nodes.add(choice['destination'])
                
                for node in decision_nodes:
                    if node in self.graph.nodes():
                        classifications[node] = 'decision_point'
                
                print(f"Classified {len(decision_nodes)} decision point nodes from MenuAnalyzer")
            except Exception as e:
                print(f"Warning: MenuAnalyzer failed: {e}")
            
            # Step 3: Find jump targets using JumpAnalyzer
            try:
                jump_analysis = analyze_jumps_in_vn(project_path)
                jump_targets = set(jump_analysis.get('jump_targets', []))
                
                for target in jump_targets:
                    if target in self.graph.nodes() and target not in classifications:
                        classifications[target] = 'jump_target'
                
                print(f"Classified {len(jump_targets)} jump target nodes")
            except Exception as e:
                print(f"Warning: JumpAnalyzer failed: {e}")
            
            # Step 4: Classify remaining nodes based on reachability
            classified_nodes = set(classifications.keys())
            
            for node in self.graph.nodes():
                if node not in classified_nodes:
                    # Check if node is reachable from start
                    if start_node and node in self.graph.nodes() and start_node in self.graph.nodes():
                        try:
                            if nx.has_path(self.graph, start_node, node):
                                classifications[node] = 'linear'
                            else:
                                classifications[node] = 'orphaned'
                        except:
                            classifications[node] = 'orphaned'
                    else:
                        # No start node or unreachable - check structural patterns
                        in_degree = self.graph.in_degree(node)
                        if in_degree == 0:
                            classifications[node] = 'orphaned'
                        else:
                            classifications[node] = 'linear'
            
            print("Semantic classification complete: {} nodes classified".format(len(classifications)))
            
            # Debug: Print classification summary
            class_counts = {}
            for classification in classifications.values():
                class_counts[classification] = class_counts.get(classification, 0) + 1
            print(f"Classification summary: {class_counts}")
            
        except Exception as e:
            print(f"Error in semantic classification: {e}")
            # Fallback to structural classification
            for node in self.graph.nodes():
                in_degree = self.graph.in_degree(node)
                out_degree = self.graph.out_degree(node)
                
                if in_degree == 0:
                    classifications[node] = 'orphaned'
                elif out_degree > 1:
                    classifications[node] = 'decision_point'
                else:
                    classifications[node] = 'linear'
        
        return classifications

    def _analyze_narrative_flow_patterns(self, project_path: Optional[str]) -> Dict[str, Any]:
        """
        Phase 3: Analyze actual narrative flow patterns using FlowTracer and JumpAnalyzer.
        
        This provides comprehensive flow intelligence for layout optimization:
        - Jump density mapping
        - Decision tree clustering
        - Common narrative paths
        - Flow bottlenecks and convergence points
        
        Returns:
            Dictionary with detailed flow analysis
        """
        flow_analysis = {
            'jump_density_map': {},      # node -> jump frequency
            'decision_trees': {},        # clusters of related decisions  
            'common_paths': [],          # frequently traversed routes
            'bottlenecks': [],           # high convergence points
            'orphaned_regions': [],     # disconnected subgraphs
            'chapter_progression': {},   # detected chapter/version boundaries
            'flow_complexity': {}       # complexity metrics per region
        }
        
        if not project_path:
            return flow_analysis
            
        try:
            print("🔍 Phase 3: Analyzing narrative flow patterns...")
            
            # Import flow analysis modules
            from app.renpy_source_api.control_flow.analyze_vn_jumps import analyze_jumps_in_vn
            from app.renpy_source_api.control_flow.analyze_vn_menus import analyze_menus_in_vn
            from app.renpy_source_api.control_flow import FlowTracer
            
            # 1. Jump Density Analysis
            print("  📊 Analyzing jump density patterns...")
            jump_analysis = analyze_jumps_in_vn(project_path)
            
            # Map jump frequency for each node
            for file_name, line_num, target in jump_analysis.get('jump_locations', []):
                if target in self.graph.nodes():
                    current_count = flow_analysis['jump_density_map'].get(target, 0)
                    flow_analysis['jump_density_map'][target] = current_count + 1
            
            # 2. Decision Tree Clustering
            print("  🌳 Identifying decision tree clusters...")
            menu_analysis = analyze_menus_in_vn(project_path)
            
            decision_clusters = {}
            for menu_info in menu_analysis.get('menus', []):
                menu_label = menu_info.get('label', 'unknown')
                if menu_label in self.graph.nodes():
                    # Find all nodes reachable from this decision point
                    cluster_nodes = []
                    try:
                        # Get nodes within 3 hops of this decision point
                        for target_node in self.graph.nodes():
                            try:
                                if nx.has_path(self.graph, menu_label, target_node):
                                    path_length = nx.shortest_path_length(self.graph, menu_label, target_node)
                                    if path_length <= 3:  # Local decision cluster
                                        cluster_nodes.append(target_node)
                            except:
                                continue
                        
                        if cluster_nodes:
                            decision_clusters[menu_label] = {
                                'center': menu_label,
                                'nodes': cluster_nodes,
                                'complexity': len(menu_info.get('choices', [])),
                                'depth': max(3, len(cluster_nodes) // 3)
                            }
                    except:
                        continue
            
            flow_analysis['decision_trees'] = decision_clusters
            
            # 3. Common Path Analysis using FlowTracer
            print("  🛤️  Tracing common narrative paths...")
            try:
                tracer = FlowTracer(project_path, choice_strategy="first")
                flow_result = tracer.trace_flow(max_steps=50)
                
                if flow_result and flow_result.steps:
                    # Extract the path taken by the tracer
                    traced_path = []
                    for step in flow_result.steps:
                        if step.statement_type == 'label':
                            traced_path.append(step.parsed_data.get('label_name', 'unknown'))
                    
                    # Store as a common path (in real implementation, you'd run multiple traces)
                    if len(traced_path) > 1:
                        flow_analysis['common_paths'].append({
                            'path': traced_path,
                            'length': len(traced_path),
                            'strategy': 'first_choice'
                        })
                        
                        print(f"    ✅ Traced path with {len(traced_path)} labels")
                
            except Exception as e:
                print(f"    ⚠️  FlowTracer warning: {e}")
            
            # 4. Bottleneck Detection (high in-degree nodes)
            print("  🔍 Detecting flow bottlenecks...")
            for node in self.graph.nodes():
                in_degree = self.graph.in_degree(node)
                if in_degree >= 3:  # Convergence point
                    flow_analysis['bottlenecks'].append({
                        'node': node,
                        'convergence': in_degree,
                        'type': 'convergence_point'
                    })
            
            # 5. Chapter/Version Progression Detection
            print("  📖 Detecting chapter progression...")
            chapter_patterns = ['ch', 'chapter', 'v', 'version', 'ep', 'episode', 'part']
            chapter_nodes = {}
            
            for node in self.graph.nodes():
                node_lower = str(node).lower()
                for pattern in chapter_patterns:
                    if pattern in node_lower:
                        # Extract number if possible
                        import re
                        match = re.search(r'(\d+)', node_lower)
                        if match:
                            chapter_num = int(match.group(1))
                            if chapter_num not in chapter_nodes:
                                chapter_nodes[chapter_num] = []
                            chapter_nodes[chapter_num].append(node)
                        break
            
            flow_analysis['chapter_progression'] = chapter_nodes
            
            # 6. Orphaned Region Detection
            print("  🏝️  Identifying orphaned regions...")
            if self.graph.is_directed():
                weak_components = list(nx.weakly_connected_components(self.graph))
            else:
                weak_components = list(nx.connected_components(self.graph))
            
            # Components with < 5 nodes are likely orphaned regions
            for component in weak_components:
                if len(component) < 5:
                    flow_analysis['orphaned_regions'].append(list(component))
            
            print(f"  ✅ Flow analysis complete:")
            print(f"    • Jump targets: {len(flow_analysis['jump_density_map'])}")
            print(f"    • Decision trees: {len(flow_analysis['decision_trees'])}")
            print(f"    • Common paths: {len(flow_analysis['common_paths'])}")
            print(f"    • Bottlenecks: {len(flow_analysis['bottlenecks'])}")
            print(f"    • Chapter groups: {len(flow_analysis['chapter_progression'])}")
            print(f"    • Orphaned regions: {len(flow_analysis['orphaned_regions'])}")
            
        except Exception as e:
            print(f"⚠️  Flow analysis error: {e}")
        
        return flow_analysis

    def _flow_aware_layout(self) -> Dict[str, Tuple[float, float]]:
        """
        Phase 3: Create flow-aware layout based on actual narrative patterns.
        
        This algorithm:
        1. Uses FlowTracer results to understand actual story progression
        2. Groups related decision trees using MenuAnalyzer
        3. Positions nodes based on narrative flow density
        4. Minimizes orphaned label disruption
        5. Optimizes for common player choice paths
        """
        print("🎯 Creating Phase 3 flow-aware layout...")
        
        # Get flow analysis data
        flow_analysis = self._analyze_narrative_flow_patterns(self.project_path)
        pos = {}
        
        # Find disconnected components
        if self.graph.is_directed():
            components = list(nx.weakly_connected_components(self.graph))
        else:
            components = list(nx.connected_components(self.graph))
        
        component_width = 20  # More space for complex flow patterns
        current_x_offset = 0
        
        for component_nodes in components:
            # Create subgraph for this component
            subgraph = self.graph.subgraph(component_nodes).copy()
            
            if len(component_nodes) == 1:
                # Single node component (likely orphaned)
                node = list(component_nodes)[0]
                pos[node] = (current_x_offset, 0)
                current_x_offset += 3
                continue
            
            # Analyze this component for flow patterns
            component_pos = self._layout_flow_aware_component(subgraph, flow_analysis)
            
            # Offset and add to main position dict
            for node, (x, y) in component_pos.items():
                pos[node] = (x + current_x_offset, y)
            
            # Calculate component width for next offset
            if component_pos:
                component_x_coords = [x for x, y in component_pos.values()]
                component_width_actual = max(component_x_coords) - min(component_x_coords) + 5
                current_x_offset += max(component_width, component_width_actual)
        
        print(f"✅ Flow-aware layout complete: {len(pos)} nodes positioned")
        return pos

    def _layout_flow_aware_component(self, subgraph: nx.DiGraph, flow_analysis: Dict[str, Any]) -> Dict[str, Tuple[float, float]]:
        """
        Layout a single component using flow-aware positioning algorithms.
        
        This is the core of Phase 3 flow-aware layout, implementing:
        - Decision tree clustering and grouping
        - Jump density-based positioning
        - Common path optimization
        - Chapter progression respect
        """
        pos = {}
        nodes = list(subgraph.nodes())
        
        if len(nodes) <= 1:
            if nodes:
                pos[nodes[0]] = (0, 0)
            return pos
        
        # 1. Identify flow patterns in this component
        component_decision_trees = {}
        component_jump_targets = set()
        component_bottlenecks = []
        
        # Extract relevant flow data for this component
        for tree_center, tree_data in flow_analysis.get('decision_trees', {}).items():
            if tree_center in nodes:
                component_decision_trees[tree_center] = tree_data
        
        for node in nodes:
            if node in flow_analysis.get('jump_density_map', {}):
                component_jump_targets.add(node)
        
        for bottleneck in flow_analysis.get('bottlenecks', []):
            if bottleneck['node'] in nodes:
                component_bottlenecks.append(bottleneck)
        
        # 2. Find semantic start for this component
        semantic_start = self._find_semantic_start_node(self.project_path)
        start_nodes = self._find_start_nodes(subgraph, semantic_start)
        
        if not start_nodes:
            # Fallback: use highest jump target or highest in-degree
            if component_jump_targets:
                start_nodes = [max(component_jump_targets, 
                                 key=lambda n: flow_analysis['jump_density_map'].get(n, 0))]
            else:
                start_nodes = [max(nodes, key=lambda n: subgraph.in_degree(n))]
        
        # 3. Create flow-aware layers
        flow_layers = self._create_flow_aware_layers(subgraph, start_nodes, flow_analysis)
        
        # 4. Position nodes based on flow intelligence
        layer_height = 3.0  # Vertical spacing
        
        for layer_index, layer_nodes in enumerate(flow_layers):
            y = -layer_index * layer_height
            
            # Sort nodes in layer by flow importance
            sorted_nodes = self._sort_nodes_by_flow_importance(layer_nodes, subgraph, flow_analysis)
            
            # Position horizontally with flow-aware spacing
            if len(sorted_nodes) == 1:
                pos[sorted_nodes[0]] = (0, y)
            else:
                # Group decision trees together
                decision_groups = []
                regular_nodes = []
                
                for node in sorted_nodes:
                    if node in component_decision_trees:
                        # This is a decision tree center - group with its cluster
                        tree_data = component_decision_trees[node]
                        cluster_nodes_in_layer = [n for n in tree_data['nodes'] if n in layer_nodes]
                        if cluster_nodes_in_layer:
                            decision_groups.append(cluster_nodes_in_layer)
                        else:
                            regular_nodes.append(node)
                    else:
                        regular_nodes.append(node)
                
                # Position decision groups compactly, regular nodes with more space
                x_offset = 0
                
                # Position decision groups first (more compact)
                for group in decision_groups:
                    group_width = len(group) * 1.2  # Tight spacing for decision clusters
                    for i, node in enumerate(group):
                        x = x_offset + (i - (len(group) - 1) / 2) * 1.2
                        pos[node] = (x, y)
                    x_offset += group_width + 2  # Space between groups
                
                # Position regular nodes with normal spacing
                if regular_nodes:
                    regular_width = len(regular_nodes) * 2.0  # Normal spacing
                    for i, node in enumerate(regular_nodes):
                        x = x_offset + (i - (len(regular_nodes) - 1) / 2) * 2.0
                        pos[node] = (x, y)
        
        return pos
    
    def _create_flow_aware_layers(self, subgraph: nx.DiGraph, start_nodes: List[str], 
                                  flow_analysis: Dict[str, Any]) -> List[List[str]]:
        """Create layers that respect actual narrative flow patterns."""
        visited = set()
        layers = []
        current_layer = list(start_nodes)
        
        # Track common paths to prioritize main narrative flow
        common_paths = flow_analysis.get('common_paths', [])
        priority_nodes = set()
        
        for path_info in common_paths:
            priority_nodes.update(path_info.get('path', []))
        
        while current_layer:
            # Remove already visited nodes
            current_layer = [n for n in current_layer if n not in visited]
            
            if not current_layer:
                break
                
            layers.append(current_layer[:])
            visited.update(current_layer)
            
            # Find next layer with flow awareness
            next_layer = []
            
            for node in current_layer:
                successors = list(subgraph.successors(node))
                
                # Prioritize nodes that are part of common paths
                priority_successors = [s for s in successors if s in priority_nodes and s not in visited]
                regular_successors = [s for s in successors if s not in priority_nodes and s not in visited]
                
                # Add priority nodes first
                next_layer.extend(priority_successors)
                next_layer.extend(regular_successors)
            
            current_layer = list(set(next_layer))  # Remove duplicates
        
        # Add any remaining unvisited nodes as final layer
        remaining = [n for n in subgraph.nodes() if n not in visited]
        if remaining:
            layers.append(remaining)
            
        return layers
    
    def _sort_nodes_by_flow_importance(self, layer_nodes: List[str], subgraph: nx.DiGraph, 
                                       flow_analysis: Dict[str, Any]) -> List[str]:
        """Sort nodes within a layer by narrative flow importance."""
        def flow_importance(node):
            # Multi-criteria importance scoring
            jump_frequency = flow_analysis.get('jump_density_map', {}).get(node, 0)
            is_decision_center = node in flow_analysis.get('decision_trees', {})
            is_bottleneck = any(b['node'] == node for b in flow_analysis.get('bottlenecks', []))
            in_common_path = any(node in path['path'] for path in flow_analysis.get('common_paths', []))
            
            out_deg = subgraph.out_degree(node)
            in_deg = subgraph.in_degree(node)
            
            # Priority scoring
            priority = 0
            
            if is_decision_center:
                priority += 1000  # Highest priority for decision points
            if is_bottleneck:
                priority += 500   # High priority for convergence points
            if in_common_path:
                priority += 200   # Medium priority for main path nodes
            
            priority += jump_frequency * 10  # Jump popularity
            priority += out_deg * 5          # Branching factor
            priority += in_deg * 2           # Convergence factor
            
            return priority
        
        return sorted(layer_nodes, key=flow_importance, reverse=True)

    def _find_start_nodes(self, subgraph: nx.DiGraph, semantic_start: Optional[str] = None) -> List[str]:
        """
        Find story start nodes using semantic analysis when possible.
        
        Args:
            subgraph: The graph component to analyze
            semantic_start: The true start node from StartLabelFinder
            
        Returns:
            List of start node candidates
        """
        # Priority 1: Use semantic start node if available and in this subgraph
        if semantic_start and semantic_start in subgraph.nodes():
            print(f"Using semantic start node: {semantic_start}")
            return [semantic_start]
        
        # Priority 2: Look for common start label names
        start_candidates = []
        start_names = ['start', 'main', 'begin', 'intro', 'prologue', 'opening']
        for node in subgraph.nodes():
            node_lower = str(node).lower()
            if any(start_name in node_lower for start_name in start_names):
                start_candidates.append(node)
        
        if start_candidates:
            print(f"Using heuristic start nodes: {start_candidates}")
            return start_candidates
            
        # Priority 3: Fallback to nodes with no incoming edges (current problematic behavior)
        fallback_candidates = [n for n in subgraph.nodes() if subgraph.in_degree(n) == 0]
        print(f"Fallback to orphaned start nodes: {fallback_candidates}")
        return fallback_candidates
        
    def _create_narrative_layers(self, subgraph: nx.DiGraph, start_nodes: List[str]) -> List[List[str]]:
        """Create narrative depth layers using BFS from start nodes."""
        visited = set()
        layers = []
        current_layer = list(start_nodes)
        
        while current_layer:
            # Remove already visited nodes
            current_layer = [n for n in current_layer if n not in visited]
            
            if not current_layer:
                break
                
            layers.append(current_layer[:])
            visited.update(current_layer)
            
            # Find next layer
            next_layer = []
            for node in current_layer:
                for successor in subgraph.successors(node):
                    if successor not in visited:
                        next_layer.append(successor)
            
            current_layer = list(set(next_layer))  # Remove duplicates
        
        # Add any remaining unvisited nodes as final layer
        remaining = [n for n in subgraph.nodes() if n not in visited]
        if remaining:
            layers.append(remaining)
            
        return layers
        
    def _position_narrative_layers(self, layers: List[List[str]], subgraph: nx.DiGraph) -> Dict[str, Tuple[float, float]]:
        """Position nodes within narrative layers for optimal flow visualization."""
        pos = {}
        layer_height = 2.5  # Reduced spacing for tighter layout
        
        for layer_index, layer_nodes in enumerate(layers):
            y = -layer_index * layer_height  # Progress downward through story
            
            # Sort nodes in layer by importance/connectivity
            layer_nodes_sorted = self._sort_layer_nodes(layer_nodes, subgraph)
            
            # Position nodes horizontally within layer
            if len(layer_nodes_sorted) == 1:
                pos[layer_nodes_sorted[0]] = (0, y)
            else:
                # Spread nodes across horizontal space
                layer_width = max(6, len(layer_nodes_sorted) * 1.5)
                for i, node in enumerate(layer_nodes_sorted):
                    x = (i - (len(layer_nodes_sorted) - 1) / 2) * (layer_width / len(layer_nodes_sorted))
                    pos[node] = (x, y)
        
        return pos
        
    def _sort_layer_nodes(self, layer_nodes: List[str], subgraph: nx.DiGraph) -> List[str]:
        """Sort nodes within a layer by narrative importance."""
        def node_importance(node):
            # Prioritize by: out_degree (decision points), in_degree (convergence), node_type
            node_data = subgraph.nodes.get(node, {})
            out_deg = subgraph.out_degree(node)
            in_deg = subgraph.in_degree(node)
            
            # Menu/decision points get central position
            if node_data.get('has_menu', False) or node_data.get('node_type') == 'menu':
                return (2, -out_deg, -in_deg)  # High priority, then by connectivity
            
            # End nodes get edge positions  
            if out_deg == 0:
                return (0, -in_deg, 0)  # Lower priority
                
            # Regular nodes sorted by connectivity
            return (1, -out_deg, -in_deg)
        
        return sorted(layer_nodes, key=node_importance, reverse=True)
        
    def _topological_layout(self) -> Dict[str, Tuple[float, float]]:
        """Create layout using NetworkX topological generations."""
        try:
            # Use topological generations for DAG layout
            layers = list(nx.topological_generations(self.graph))
            
            # Add layer attribute to nodes
            for layer_index, layer_nodes in enumerate(layers):
                for node in layer_nodes:
                    self.graph.nodes[node]['layer'] = layer_index
            
            # Use multipartite layout
            return nx.multipartite_layout(self.graph, subset_key='layer')
            
        except nx.NetworkXError:
            # Graph has cycles, fall back to narrative layout
            return self._narrative_hierarchical_layout()
    
    def _narrative_flow_layout(self) -> Dict[str, Tuple[float, float]]:
        """
        Create a narrative flow layout that prioritizes story progression over neat organization.
        
        This algorithm:
        1. Ensures start nodes are always at the top
        2. Detects chapter progression and respects it
        3. Follows main narrative threads closely
        4. Minimizes line crossings for better visual flow
        """
        pos = {}
        
        # Find disconnected components
        if self.graph.is_directed():
            components = list(nx.weakly_connected_components(self.graph))
        else:
            components = list(nx.connected_components(self.graph))
        
        component_width = 15  # More space between components for clarity
        current_x_offset = 0
        
        for component_nodes in components:
            # Create subgraph for this component
            subgraph = self.graph.subgraph(component_nodes).copy()
            
            # Get component layout using narrative flow
            component_pos = self._layout_narrative_flow_component(subgraph)
            
            # Offset this component horizontally
            for node, (x, y) in component_pos.items():
                pos[node] = (x + current_x_offset, y)
            
            # Calculate component width for next offset
            if component_pos:
                min_x = min(x for x, y in component_pos.values())
                max_x = max(x for x, y in component_pos.values())
                current_x_offset += (max_x - min_x) + component_width
        
        return pos
    
    def _layout_narrative_flow_component(self, subgraph: nx.DiGraph) -> Dict[str, Tuple[float, float]]:
        """Layout a component prioritizing narrative flow over neat organization."""
        
        # Step 1: Find and position start nodes at the top using semantic detection
        start_nodes = self._find_start_nodes(subgraph, self.semantic_start_node)
        if not start_nodes:
            start_nodes = [n for n in subgraph.nodes() if subgraph.in_degree(n) == 0]
        if not start_nodes:
            start_nodes = [max(subgraph.nodes(), key=lambda n: subgraph.out_degree(n))]
        
        # Step 2: Detect chapter progression  
        chapter_groups = self._detect_chapter_groups(subgraph)
        
        # Step 3: Create narrative threads following main paths
        narrative_threads = self._create_narrative_threads(subgraph, start_nodes)
        
        # Step 4: Position nodes prioritizing flow over organization
        return self._position_narrative_flow_nodes(subgraph, start_nodes, chapter_groups, narrative_threads)
    
    def _detect_chapter_groups(self, subgraph: nx.DiGraph) -> Dict[str, List[str]]:
        """Detect chapter groupings from node names."""
        chapter_groups = {}
        
        for node in subgraph.nodes():
            node_str = str(node).lower()
            
            # Look for chapter indicators
            if 'ch1' in node_str or 'chapter1' in node_str:
                chapter_groups.setdefault('ch1', []).append(node)
            elif 'ch2' in node_str or 'chapter2' in node_str:
                chapter_groups.setdefault('ch2', []).append(node)
            elif 'ch3' in node_str or 'chapter3' in node_str:
                chapter_groups.setdefault('ch3', []).append(node)
            elif 'ch4' in node_str or 'chapter4' in node_str:
                chapter_groups.setdefault('ch4', []).append(node)
            elif 'ch5' in node_str or 'chapter5' in node_str:
                chapter_groups.setdefault('ch5', []).append(node)
            else:
                # No clear chapter, put in general group
                chapter_groups.setdefault('general', []).append(node)
        
        return chapter_groups
    
    def _create_narrative_threads(self, subgraph: nx.DiGraph, start_nodes: List[str]) -> List[List[str]]:
        """Create narrative threads by following main paths from start nodes."""
        threads = []
        visited = set()
        
        for start_node in start_nodes:
            if start_node in visited:
                continue
            
            # Follow the main path from this start node
            thread = []
            current = start_node
            
            while current and current not in visited:
                thread.append(current)
                visited.add(current)
                
                # Find the most likely next node (prefer single successor, then highest degree)
                successors = list(subgraph.successors(current))
                if not successors:
                    break
                elif len(successors) == 1:
                    current = successors[0]
                else:
                    # Choose successor with highest importance/connectivity
                    current = max(successors, key=lambda n: (
                        subgraph.out_degree(n),
                        subgraph.in_degree(n),
                        1 if subgraph.nodes.get(n, {}).get('has_menu', False) else 0
                    ))
            
            if thread:
                threads.append(thread)
        
        return threads
    
    def _position_narrative_flow_nodes(self, subgraph: nx.DiGraph, start_nodes: List[str], 
                                     chapter_groups: Dict[str, List[str]], 
                                     narrative_threads: List[List[str]]) -> Dict[str, Tuple[float, float]]:
        """Position nodes to optimize narrative flow visualization."""
        pos = {}
        
        # Step 1: Position start nodes at the very top
        start_y = 0
        for i, start_node in enumerate(start_nodes):
            x = (i - len(start_nodes)/2) * 4
            pos[start_node] = (x, start_y)
        
        # Step 2: Position main narrative threads vertically
        thread_y_offset = -4  # Start below start nodes
        positioned_nodes = set(start_nodes)
        
        for thread_idx, thread in enumerate(narrative_threads):
            current_y = thread_y_offset
            
            for node_idx, node in enumerate(thread):
                if node in positioned_nodes:
                    continue
                
                # Position main thread nodes vertically with some horizontal spread
                x = thread_idx * 2 + (node_idx % 3 - 1) * 0.5  # Slight horizontal variation
                y = current_y - node_idx * 2
                pos[node] = (x, y)
                positioned_nodes.add(node)
        
        # Step 3: Position chapter groups, respecting their logical order
        chapter_order = ['ch1', 'ch2', 'ch3', 'ch4', 'ch5', 'general']
        chapter_y_start = min(pos.values(), key=lambda p: p[1])[1] - 6  # Below main threads
        
        for chapter_idx, chapter in enumerate(chapter_order):
            if chapter not in chapter_groups:
                continue
                
            chapter_nodes = [n for n in chapter_groups[chapter] if n not in positioned_nodes]
            if not chapter_nodes:
                continue
            
            # Position chapter nodes in a more spread-out pattern
            chapter_y = chapter_y_start - chapter_idx * 8
            nodes_per_row = max(3, min(6, len(chapter_nodes) // 2))
            
            for i, node in enumerate(chapter_nodes):
                row = i // nodes_per_row
                col = i % nodes_per_row
                x = (col - nodes_per_row/2) * 3
                y = chapter_y - row * 3
                pos[node] = (x, y)
                positioned_nodes.add(node)
        
        # Step 4: Position any remaining nodes
        remaining_nodes = [n for n in subgraph.nodes() if n not in positioned_nodes]
        if remaining_nodes:
            remaining_y = min(pos.values(), key=lambda p: p[1])[1] - 8
            for i, node in enumerate(remaining_nodes):
                x = (i % 5 - 2) * 4
                y = remaining_y - (i // 5) * 3
                pos[node] = (x, y)
        
        return pos
    
    def _debug_graph_analysis(self, layout_type: str):
        """Debug function to analyze graph structure and layout decisions."""
        if not self.graph:
            return
            
        import os
        debug_file = f"debug_layout_{layout_type}.txt"
        
        with open(debug_file, 'w') as f:
            f.write(f"=== GRAPH ANALYSIS FOR {layout_type.upper()} LAYOUT ===\n\n")
            
            # Basic graph stats
            f.write(f"Total nodes: {len(self.graph.nodes)}\n")
            f.write(f"Total edges: {len(self.graph.edges)}\n")
            f.write(f"Is directed: {self.graph.is_directed()}\n\n")
            
            # Node analysis
            f.write("=== NODE ANALYSIS ===\n")
            for node in self.graph.nodes:
                node_data = self.graph.nodes.get(node, {})
                in_degree = self.graph.in_degree(node)
                out_degree = self.graph.out_degree(node)
                
                f.write(f"Node: {node}\n")
                f.write(f"  In-degree: {in_degree}, Out-degree: {out_degree}\n")
                f.write(f"  Type: {node_data.get('node_type', 'unknown')}\n")
                f.write(f"  Has menu: {node_data.get('has_menu', False)}\n")
                
                # Check for chapter indicators
                node_lower = str(node).lower()
                chapter_indicators = []
                for ch in ['ch1', 'ch2', 'ch3', 'ch4', 'ch5']:
                    if ch in node_lower:
                        chapter_indicators.append(ch)
                f.write(f"  Chapter indicators: {chapter_indicators}\n")
                
                # Check for start indicators
                start_indicators = []
                for start in ['start', 'main', 'begin', 'intro', 'prologue', 'opening']:
                    if start in node_lower:
                        start_indicators.append(start)
                f.write(f"  Start indicators: {start_indicators}\n")
                
                f.write(f"  Predecessors: {list(self.graph.predecessors(node))}\n")
                f.write(f"  Successors: {list(self.graph.successors(node))}\n\n")
            
            # Component analysis
            f.write("=== COMPONENT ANALYSIS ===\n")
            if self.graph.is_directed():
                components = list(nx.weakly_connected_components(self.graph))
            else:
                components = list(nx.connected_components(self.graph))
            
            for i, component in enumerate(components):
                f.write(f"Component {i+1}: {len(component)} nodes\n")
                f.write(f"  Nodes: {list(component)}\n\n")
            
            # Start node detection
            f.write("=== START NODE DETECTION ===\n")
            for i, component in enumerate(components):
                subgraph = self.graph.subgraph(component)
                start_candidates = self._find_start_nodes(subgraph, self.semantic_start_node)
                f.write(f"Component {i+1} start candidates: {start_candidates}\n")
                
                # Also check nodes with no incoming edges
                no_incoming = [n for n in component if self.graph.in_degree(n) == 0]
                f.write(f"  Nodes with no incoming edges: {no_incoming}\n\n")
        
        print(f"Debug analysis saved to {debug_file}")
    
    def _dot_like_layout(self) -> Dict[str, Tuple[float, float]]:
        """
        DOT-like layout algorithm following the Sugiyama framework.
        
        This implements the four phases of the Sugiyama framework:
        1. Layer Assignment - assign nodes to hierarchical layers
        2. Crossing Reduction - minimize edge crossings
        3. Coordinate Assignment - assign final positions
        """
        pos = {}
        
        # Find disconnected components
        if self.graph.is_directed():
            components = list(nx.weakly_connected_components(self.graph))
        else:
            components = list(nx.connected_components(self.graph))
        
        component_width = 20  # Space between components
        current_x_offset = 0
        
        for component_nodes in components:
            # Create subgraph for this component
            subgraph = self.graph.subgraph(component_nodes).copy()
            
            # Apply DOT algorithm to this component
            component_pos = self._dot_like_component(subgraph)
            
            # Offset this component horizontally
            for node, (x, y) in component_pos.items():
                pos[node] = (x + current_x_offset, y)
            
            # Calculate component width for next offset
            if component_pos:
                min_x = min(x for x, y in component_pos.values())
                max_x = max(x for x, y in component_pos.values())
                current_x_offset += (max_x - min_x) + component_width
        
        return pos
    
    def _dot_like_component(self, subgraph: nx.DiGraph) -> Dict[str, Tuple[float, float]]:
        """Apply DOT algorithm to a single component following Sugiyama framework."""
        
        # Phase 1: Layer Assignment
        layers = self._assign_layers_dot(subgraph)
        
        # Phase 2: Crossing Reduction
        optimized_layers = self._reduce_crossings_dot(subgraph, layers)
        
        # Phase 3: Coordinate Assignment
        return self._assign_coordinates_dot(subgraph, optimized_layers)
    
    def _assign_layers_dot(self, subgraph: nx.DiGraph) -> List[List[str]]:
        """
        Phase 1: Layer Assignment using longest path algorithm.
        
        This assigns each node to a layer based on its longest path from start nodes.
        """
        # Use semantic start node detection instead of naive orphaned label approach
        start_nodes = self._find_start_nodes(subgraph, self.semantic_start_node)
        
        if not start_nodes:
            # If no start nodes found, look for nodes with minimum incoming degree
            min_in_degree = min(subgraph.in_degree(n) for n in subgraph.nodes())
            start_nodes = [n for n in subgraph.nodes() if subgraph.in_degree(n) == min_in_degree]
        
        # Calculate layer for each node using longest path
        node_layers = {}
        
        # Initialize all nodes to layer 0
        for node in subgraph.nodes():
            node_layers[node] = 0
        
        # Set start nodes to layer 0
        for node in start_nodes:
            node_layers[node] = 0
        
        print(f"DOT-like algorithm: Found start nodes: {start_nodes}")
        
        # Use topological sort to process nodes in correct order
        try:
            topo_order = list(nx.topological_sort(subgraph))
        except (nx.NetworkXError, nx.NetworkXUnfeasible):
            # Graph has cycles, fall back to narrative layout
            print(f"DOT-like layout detected cycles, falling back to narrative layout")
            return self._create_narrative_layers(subgraph, start_nodes)
        
        # For each node, set its layer to max(predecessor_layers) + 1
        for node in topo_order:
            if node in start_nodes:
                continue
            
            predecessors = list(subgraph.predecessors(node))
            if predecessors:
                max_pred_layer = max(node_layers[pred] for pred in predecessors)
                node_layers[node] = max_pred_layer + 1
        
        # Group nodes by layer
        max_layer = max(node_layers.values()) if node_layers else 0
        layers = [[] for _ in range(max_layer + 1)]
        
        for node, layer in node_layers.items():
            layers[layer].append(node)
        
        print(f"DOT-like algorithm: Created {len(layers)} layers")
        for i, layer_nodes in enumerate(layers):
            print(f"  Layer {i}: {layer_nodes[:3]}{'...' if len(layer_nodes) > 3 else ''} ({len(layer_nodes)} nodes)")
        
        return layers
    
    def _reduce_crossings_dot(self, subgraph: nx.DiGraph, layers: List[List[str]]) -> List[List[str]]:
        """
        Phase 2: Crossing Reduction using barycenter method.
        
        This performs layer-by-layer sweeps to minimize edge crossings.
        """
        if len(layers) <= 1:
            return layers
        
        # Make a copy to avoid modifying the original
        working_layers = [layer[:] for layer in layers]
        
        # Perform multiple sweeps
        for _ in range(5):  # Maximum 5 iterations
            # Forward sweep (top to bottom)
            for i in range(1, len(working_layers)):
                working_layers[i] = self._order_layer_by_barycenter(
                    subgraph, working_layers[i-1], working_layers[i], direction='down'
                )
            
            # Backward sweep (bottom to top)
            for i in range(len(working_layers) - 2, -1, -1):
                working_layers[i] = self._order_layer_by_barycenter(
                    subgraph, working_layers[i+1], working_layers[i], direction='up'
                )
        
        return working_layers
    
    def _order_layer_by_barycenter(self, subgraph: nx.DiGraph, fixed_layer: List[str], 
                                   moving_layer: List[str], direction: str) -> List[str]:
        """Order nodes in a layer by their barycenter positions."""
        
        # Create position mapping for fixed layer
        fixed_positions = {node: i for i, node in enumerate(fixed_layer)}
        
        # Calculate barycenter for each node in moving layer
        node_barycenters = []
        
        for node in moving_layer:
            if direction == 'down':
                # Look at predecessors in the layer above
                neighbors = [n for n in subgraph.predecessors(node) if n in fixed_positions]
            else:
                # Look at successors in the layer below
                neighbors = [n for n in subgraph.successors(node) if n in fixed_positions]
            
            if neighbors:
                # Calculate barycenter (average position)
                barycenter = sum(fixed_positions[n] for n in neighbors) / len(neighbors)
            else:
                # Node has no relevant neighbors, use current position
                barycenter = moving_layer.index(node)
            
            node_barycenters.append((node, barycenter))
        
        # Sort by barycenter and return ordered nodes
        node_barycenters.sort(key=lambda x: x[1])
        return [node for node, _ in node_barycenters]
    
    def _assign_coordinates_dot(self, subgraph: nx.DiGraph, layers: List[List[str]]) -> Dict[str, Tuple[float, float]]:
        """
        Phase 3: Coordinate Assignment.
        
        This assigns final x,y coordinates to each node.
        Start nodes appear at the top, flowing downward.
        """
        pos = {}
        
        # Assign Y coordinates based on layer
        layer_spacing = 2.5  # Reduced spacing for tighter layout
        
        for layer_idx, layer_nodes in enumerate(layers):
            # Start nodes (layer 0) should be at the top (smallest Y value)
            y = layer_idx * layer_spacing
            
            print(f"DOT coordinates: Layer {layer_idx} -> Y={y}, nodes: {layer_nodes[:3]}{'...' if len(layer_nodes) > 3 else ''}")
            
            # Assign X coordinates within the layer
            if len(layer_nodes) == 1:
                x = 0
                pos[layer_nodes[0]] = (x, y)
            else:
                # Spread nodes horizontally
                total_width = max(8, (len(layer_nodes) - 1) * 3)
                for i, node in enumerate(layer_nodes):
                    x = (i * total_width) / max(1, len(layer_nodes) - 1) - total_width / 2
                    pos[node] = (x, y)
        
        return pos
            
    def mousePressEvent(self, event):
        """Handle mouse press events for navigation."""
        if event.button() == Qt.MouseButton.MiddleButton:
            # Enable hand drag for middle mouse button
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self._middle_button_pressed = True
            # Create a modified event with left button to trick the drag system
            modified_event = QMouseEvent(
                event.type(),
                event.position(),
                Qt.MouseButton.LeftButton,  # Change to left button
                Qt.MouseButton.LeftButton,
                event.modifiers()
            )
            super().mousePressEvent(modified_event)
        else:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self._middle_button_pressed = False
            # Create a modified event with left button
            modified_event = QMouseEvent(
                event.type(),
                event.position(),
                Qt.MouseButton.LeftButton,  # Change to left button
                Qt.MouseButton.LeftButton,
                event.modifiers()
            )
            super().mouseReleaseEvent(modified_event)
        else:
            super().mouseReleaseEvent(event)
        
    def reset_view(self):
        """Reset view to show all content."""
        self.fit_view_to_content()
        
    def search_and_select_node(self, search_text: str) -> bool:
        """
        Search for a node by name and select it if found.
        
        Args:
            search_text: Partial or full node name to search for
            
        Returns:
            True if node was found and selected, False otherwise
        """
        search_text = search_text.lower().strip()
        found_nodes = []
        
        # Search through all nodes
        for node_id, node_item in self.nodes.items():
            # Handle both VNLabelNode and MenuContainerGraphicsItem
            if hasattr(node_item, 'node_name'):
                # VNLabelNode
                node_name = node_item.node_name.lower()
            elif hasattr(node_item, 'menu_id'):
                # MenuContainerGraphicsItem
                node_name = node_item.menu_id.lower()
            else:
                # Fallback to node_id
                node_name = node_id.lower()
                
            if search_text in node_name or search_text in node_id.lower():
                found_nodes.append((node_id, node_item))
        
        if not found_nodes:
            print(f"No nodes found matching '{search_text}'")
            return False
        
        # If multiple matches, prefer exact matches first
        exact_matches = []
        for nid, ni in found_nodes:
            # Handle both node types for exact matching too
            if hasattr(ni, 'node_name'):
                node_name = ni.node_name.lower()
            elif hasattr(ni, 'menu_id'):
                node_name = ni.menu_id.lower()
            else:
                node_name = nid.lower()
                
            if nid.lower() == search_text or node_name == search_text:
                exact_matches.append((nid, ni))
        
        if exact_matches:
            target_node_id, target_node = exact_matches[0]
        else:
            target_node_id, target_node = found_nodes[0]
            if len(found_nodes) > 1:
                print(f"Multiple matches found for '{search_text}', selecting first: {target_node_id}")
                print("Other matches:", [nid for nid, _ in found_nodes[1:5]])  # Show first 5 others
        
        # Clear current selection
        self.scene.clearSelection()
        
        # Select and center on the found node
        target_node.setSelected(True)
        
        # Center the view on the selected node
        node_pos = target_node.scenePos()
        self.centerOn(node_pos)
        
        # Optionally highlight with a brief animation effect
        target_node._highlighted = True
        target_node.update()
        
        print(f"Found and selected node: {target_node_id}")
        return True
        
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming."""
        # Zoom functionality
        zoom_factor = 1.15
        if event.angleDelta().y() < 0:
            zoom_factor = 1 / zoom_factor
            
        self.scale(zoom_factor, zoom_factor)
         
    def on_selection_changed(self):
        """Handle scene selection changes."""
        selected_items = self.scene.selectedItems()
        
        for item in selected_items:
            if isinstance(item, VNLabelNode):
                self.node_selected.emit(item.node_id, item.node_data)
                break 