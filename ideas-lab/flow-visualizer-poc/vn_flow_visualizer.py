"""
VN Flow Visualizer Widget

Interactive PyQt6 QGraphicsView-based visualization for Renpy narrative flow graphs.
This widget handles the display, interaction, and manipulation of VN branching structures.
"""

import math
from typing import Dict, Any, Optional, List, Tuple
from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsObject,
    QGraphicsEllipseItem, QGraphicsPathItem, QGraphicsTextItem,
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import (
    QPen, QBrush, QColor, QPainter, QPainterPath, QFont,
    QPolygonF, QLinearGradient, QRadialGradient, QMouseEvent
)
import networkx as nx


class VNLabelNode(QGraphicsObject):
    """
    A custom QGraphicsItem representing a Renpy label in the flow graph.
    
    Visual representation of story labels with different styles based on properties
    (start label, menu choices, endings, etc.)
    """
    
    def __init__(self, node_id: str, node_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        
        self.node_id = node_id
        self.node_data = node_data
        self.node_name = node_data.get('name', node_id)
        
        # Visual properties
        self.radius = 40
        self.selected_radius = 50
        self.colors = self._determine_colors()
        
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
        """Determine node colors based on node properties."""
        base_color = QColor(100, 150, 250)  # Default blue
        
        # Special colors for different node types
        if self.node_name == 'start':
            base_color = QColor(100, 250, 100)  # Green for start
        elif not self.node_data.get('outgoing_flows', []):
            base_color = QColor(250, 100, 100)  # Red for endings
        elif self.node_data.get('has_menu', False):
            base_color = QColor(250, 200, 100)  # Yellow for choice points
            
        return {
            'normal': base_color,
            'hover': base_color.lighter(120),
            'selected': base_color.darker(120),
            'text': QColor(255, 255, 255)
        }
        
    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of this item."""
        radius = self.selected_radius if self._selected else self.radius
        return QRectF(-radius, -radius, radius * 2, radius * 2)
        
    def paint(self, painter: QPainter, option, widget=None):
        """Paint the node."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Determine current radius and color
        radius = self.selected_radius if self._selected else self.radius
        color = self.colors['selected'] if self._selected else \
                self.colors['hover'] if self._highlighted else \
                self.colors['normal']
        
        # Create gradient
        gradient = QRadialGradient(0, 0, radius)
        gradient.setColorAt(0, color.lighter(130))
        gradient.setColorAt(1, color.darker(110))
        
        # Draw circle
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(color.darker(140), 2))
        painter.drawEllipse(-radius, -radius, radius * 2, radius * 2)
        
        # Draw text
        painter.setPen(QPen(self.colors['text']))
        font = QFont()
        font.setBold(True)
        font.setPointSize(8 if len(self.node_name) > 10 else 10)
        painter.setFont(font)
        
        # Calculate text rectangle
        text_rect = QRectF(-radius + 5, -radius + 5, (radius - 5) * 2, (radius - 5) * 2)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, self.node_name)
        
        # Draw special indicators
        if self.node_data.get('has_menu', False):
            # Draw menu indicator (small triangle)
            triangle = QPolygonF([
                QPointF(radius - 15, -radius + 5),
                QPointF(radius - 5, -radius + 5),
                QPointF(radius - 10, -radius + 15)
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
        
    def update_path(self):
        """Update the connection path between nodes."""
        if not self.source_node or not self.target_node:
            return
            
        # Get node positions
        source_pos = self.source_node.scenePos()
        target_pos = self.target_node.scenePos()
        
        # Calculate connection points (edge of circles)
        dx = target_pos.x() - source_pos.x()
        dy = target_pos.y() - source_pos.y()
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance == 0:
            return
            
        # Unit vector from source to target
        ux = dx / distance
        uy = dy / distance
        
        # Connection points
        source_radius = self.source_node.radius
        target_radius = self.target_node.radius
        
        start_point = QPointF(
            source_pos.x() + ux * source_radius,
            source_pos.y() + uy * source_radius
        )
        end_point = QPointF(
            target_pos.x() - ux * target_radius,
            target_pos.y() - uy * target_radius
        )
        
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
        
        # Convert renpy-source-api flow graph to NetworkX format
        self.graph = self._convert_flow_graph_to_networkx(flow_graph)
        
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
        """Create visual elements from flow graph data."""
        if not self.graph:
            return
             
        # Create nodes
        for node_id in self.graph.nodes:
            node_item = VNLabelNode(node_id, self.graph.nodes[node_id])
            self.scene.addItem(node_item)
            self.nodes[node_id] = node_item
             
        # Create connections based on graph edges
        for source_id, target_id in self.graph.edges:
            if source_id in self.nodes and target_id in self.nodes:
                source_node = self.nodes[source_id]
                target_node = self.nodes[target_id]
                edge_data = self.graph.edges[source_id, target_id]
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
        else:
            pos = self._narrative_hierarchical_layout()  # Default to narrative
        
        # Scale positions for better visibility
        scale = 400
        scaled_pos = {node: (x * scale, y * scale) for node, (x, y) in pos.items()}
        
        # Apply positions to nodes
        for node_id, (x, y) in scaled_pos.items():
            if node_id in self.nodes:
                self.nodes[node_id].setPos(x, y)
        
        # Update connections
        for connection in self.connections:
            connection.update_path()
            
        # Automatically fit view after layout
        self.fit_view_to_content()
        
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
        
        # Find potential start nodes
        start_candidates = self._find_start_nodes(subgraph)
        
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
        
    def _find_start_nodes(self, subgraph: nx.DiGraph) -> List[str]:
        """Find likely story start nodes."""
        start_candidates = []
        
        # Check for common start label names
        start_names = ['start', 'main', 'begin', 'intro', 'prologue', 'opening']
        for node in subgraph.nodes():
            node_lower = str(node).lower()
            if any(start_name in node_lower for start_name in start_names):
                start_candidates.append(node)
                
        return start_candidates
        
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
        layer_height = 3  # Vertical space between layers
        
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
        
        # Step 1: Find and position start nodes at the top
        start_nodes = self._find_start_nodes(subgraph)
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
                start_candidates = self._find_start_nodes(subgraph)
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
        # Find start nodes (nodes with no incoming edges)
        start_nodes = [n for n in subgraph.nodes() if subgraph.in_degree(n) == 0]
        
        if not start_nodes:
            # If no start nodes, look for nodes with minimum incoming degree
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
        layer_spacing = 4
        
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