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
    QPolygonF, QLinearGradient, QRadialGradient
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
        
        # Create scene
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # Visualization state
        self.flow_graph: Optional[Dict[str, Any]] = None
        self.nodes: Dict[str, VNLabelNode] = {}
        self.connections: List[VNFlowConnection] = []
        
        # Set up view properties
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        
        # Enable zooming and panning
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
        self.apply_layout('spring')
        
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
            
    def apply_layout(self, layout_type: str = 'spring'):
        """Apply layout algorithm to position nodes."""
        if not self.graph or not self.nodes:
            return
            
        # Generate positions using NetworkX
        if layout_type == 'spring':
            # Use larger area and more iterations for better spread
            pos = nx.spring_layout(self.graph, k=3, iterations=100)
        elif layout_type == 'circular':
            pos = nx.circular_layout(self.graph)
        elif layout_type == 'hierarchical':
            try:
                pos = nx.nx_agraph.graphviz_layout(self.graph, prog='dot')
            except:
                # Fall back to spring layout if graphviz not available
                pos = nx.spring_layout(self.graph, k=3, iterations=100)
        elif layout_type == 'random':
            pos = nx.random_layout(self.graph)
        else:
            pos = nx.spring_layout(self.graph, k=3, iterations=100)
        
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