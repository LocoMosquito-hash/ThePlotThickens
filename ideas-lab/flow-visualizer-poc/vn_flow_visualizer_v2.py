"""
VN Flow Visualizer V2 - Clean Interface Version

Enhanced flow visualizer with clean separation of concerns between parsing and visualization.
This version uses the standardized VisualizationData interface while keeping all GUI components identical.

Phase 2 of the flow visualizer refactoring.
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

# Import the clean interface components
from flow_visualizer_interface import FlowVisualizer, VisualizationData, VisualizationNode, VisualizationConnection
from renpy_data_adapter import RenpyFlowDataAdapter

# Import the existing graphics components (keep the same GUI)
from menu_graphics_items import MenuContainerGraphicsItem, ChoiceButtonGraphicsItem


class VNLabelNodeV2(QGraphicsObject):
    """
    Enhanced VNLabelNode that works with VisualizationNode data.
    
    Keeps the same visual appearance but uses standardized data interface.
    """
    
    def __init__(self, vis_node: VisualizationNode, parent=None):
        super().__init__(parent)
        
        # Store the visualization node data
        self.vis_node = vis_node
        self.node_id = vis_node.node_id
        self.node_name = vis_node.display_name
        self.semantic_classification = vis_node.metadata.get('semantic_type', 'regular')
        
        # Visual properties (same as before)
        self.base_width = 120
        self.height = 40
        self.selected_scale = 1.2
        self.colors = self._determine_colors()
        
        # Calculate dynamic width based on text length
        self.width = max(self.base_width, len(self.node_name) * 8 + 20)
        
        # State
        self._selected = False
        self._highlighted = False
        
        # Make item interactive (same as before)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)
        
        # Accept hover events for tooltips
        self.setAcceptHoverEvents(True)
        
    def _determine_colors(self) -> Dict[str, QColor]:
        """Determine node colors based on semantic classification."""
        
        # Use the color hint from visualization data, or fall back to semantic classification
        if self.vis_node.color_hint:
            color_map = {
                'green': QColor(100, 250, 100),
                'red': QColor(250, 100, 100),
                'blue': QColor(100, 150, 250),
                'lightblue': QColor(150, 200, 250),
                'purple': QColor(200, 100, 250),
                'yellow': QColor(250, 250, 100),
                'orange': QColor(255, 140, 0),
                'gray': QColor(150, 150, 150)
            }
            base_color = color_map.get(self.vis_node.color_hint, QColor(100, 150, 250))
        else:
            # Fallback to semantic classification
            color_map = {
                'start': QColor(100, 250, 100),
                'ending': QColor(250, 100, 100),
                'hub': QColor(200, 100, 250),
                'regular': QColor(100, 150, 250)
            }
            base_color = color_map.get(self.semantic_classification, QColor(100, 150, 250))
        
        return {
            'normal': base_color,
            'selected': base_color.lighter(130),
            'highlighted': base_color.lighter(150),
            'border': base_color.darker(150)
        }
    
    def boundingRect(self) -> QRectF:
        """Define the bounding rectangle for the node."""
        return QRectF(-self.width/2, -self.height/2, self.width, self.height)
    
    def paint(self, painter: QPainter, option, widget):
        """Paint the node (same as original VNLabelNode)."""
        rect = self.boundingRect()
        
        # Choose colors based on state
        if self._selected:
            fill_color = self.colors['selected']
            border_color = self.colors['border']
            border_width = 3
        elif self._highlighted:
            fill_color = self.colors['highlighted']
            border_color = self.colors['border']
            border_width = 2
        else:
            fill_color = self.colors['normal']
            border_color = self.colors['border']
            border_width = 1
        
        # Create gradient fill
        gradient = QLinearGradient(0, rect.top(), 0, rect.bottom())
        gradient.setColorAt(0, fill_color.lighter(110))
        gradient.setColorAt(1, fill_color)
        
        # Draw rounded rectangle
        painter.setPen(QPen(border_color, border_width))
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(rect, 5, 5)
        
        # Draw text
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        
        # Truncate text if too long
        display_text = self.node_name
        if len(display_text) > 15:
            display_text = display_text[:12] + "..."
        
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, display_text)
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event and event.button() == Qt.MouseButton.LeftButton:
            self.setSelected(True)
        super().mousePressEvent(event)
    
    def hoverEnterEvent(self, event):
        """Handle hover enter events."""
        self._highlighted = True
        self.update()
        
        # Create tooltip from metadata
        tooltip_lines = [
            f"Label: {self.node_name}",
            f"Type: {self.semantic_classification}",
        ]
        
        if self.vis_node.metadata:
            if 'file_path' in self.vis_node.metadata:
                tooltip_lines.append(f"File: {self.vis_node.metadata['file_path']}")
            if 'line_number' in self.vis_node.metadata:
                tooltip_lines.append(f"Line: {self.vis_node.metadata['line_number']}")
            if 'flow_complexity' in self.vis_node.metadata:
                tooltip_lines.append(f"Complexity: {self.vis_node.metadata['flow_complexity']}")
        
        self.setToolTip("\n".join(tooltip_lines))
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Handle hover leave events."""
        self._highlighted = False
        self.update()
        super().hoverLeaveEvent(event)


class VNFlowConnectionV2(QGraphicsPathItem):
    """
    Enhanced flow connection that works with VisualizationConnection data.
    
    Keeps the same visual appearance but uses standardized data interface.
    """
    
    def __init__(self, vis_connection: VisualizationConnection, 
                 source_node: QGraphicsObject, target_node: QGraphicsObject, parent=None):
        super().__init__(parent)
        
        self.vis_connection = vis_connection
        self.source_node = source_node
        self.target_node = target_node
        
        # Visual properties based on connection data
        self.arrow_size = 15
        self.line_width = vis_connection.weight_hint or 2
        
        # Set color from visualization data
        color_map = {
            'gray': QColor(100, 100, 100),
            'blue': QColor(50, 100, 200),
            'red': QColor(200, 50, 50),
            'orange': QColor(255, 140, 0),
            'lightgray': QColor(150, 150, 150)
        }
        self.color = color_map.get(vis_connection.color_hint, QColor(100, 100, 100))
        
        # Set line style
        if vis_connection.line_style == 'dashed':
            pen_style = Qt.PenStyle.DashLine
        elif vis_connection.line_style == 'dotted':
            pen_style = Qt.PenStyle.DotLine
        else:
            pen_style = Qt.PenStyle.SolidLine
        
        # Set up path
        self.setPen(QPen(self.color, self.line_width, pen_style))
        self.setZValue(-1)  # Draw behind nodes
        
        # Connect to nodes for updates
        if not hasattr(source_node, 'connected_edges'):
            setattr(source_node, 'connected_edges', [])
        if not hasattr(target_node, 'connected_edges'):
            setattr(target_node, 'connected_edges', [])
            
        getattr(source_node, 'connected_edges').append(self)
        getattr(target_node, 'connected_edges').append(self)
        
        self.update_path()
    
    def update_path(self):
        """Update the connection path (same logic as original)."""
        if not self.source_node or not self.target_node:
            return
        
        start_pos = self.source_node.scenePos()
        end_pos = self.target_node.scenePos()
        
        # Create bezier curve
        path = QPainterPath()
        path.moveTo(start_pos)
        
        # Control points for smooth curve
        dx = end_pos.x() - start_pos.x()
        dy = end_pos.y() - start_pos.y()
        
        control1 = QPointF(start_pos.x() + dx * 0.5, start_pos.y())
        control2 = QPointF(end_pos.x() - dx * 0.5, end_pos.y())
        
        path.cubicTo(control1, control2, end_pos)
        
        # Add arrowhead
        self._add_arrow_to_path(path, end_pos, start_pos)
        
        self.setPath(path)
    
    def _add_arrow_to_path(self, path: QPainterPath, end_pos: QPointF, start_pos: QPointF):
        """Add arrowhead to the path."""
        # Calculate arrow direction
        angle = math.atan2((end_pos.y() - start_pos.y()), (end_pos.x() - start_pos.x()))
        
        # Arrow points
        arrow_length = self.arrow_size
        arrow_angle = math.pi / 6  # 30 degrees
        
        arrow_p1 = QPointF(
            end_pos.x() - arrow_length * math.cos(angle - arrow_angle),
            end_pos.y() - arrow_length * math.sin(angle - arrow_angle)
        )
        
        arrow_p2 = QPointF(
            end_pos.x() - arrow_length * math.cos(angle + arrow_angle),
            end_pos.y() - arrow_length * math.sin(angle + arrow_angle)
        )
        
        # Create arrow
        arrow = QPolygonF([end_pos, arrow_p1, arrow_p2])
        path.addPolygon(arrow)


class VNFlowVisualizerV2(QGraphicsView):
    """
    Enhanced flow visualizer with clean separation of concerns.
    
    Uses standardized VisualizationData interface while keeping all GUI components identical.
    This resolves circular development issues by separating parsing from visualization.
    """
    
    node_selected = pyqtSignal(str, dict)  # node_id, node_data
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize graphics components (same as before)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # Data provider (replaces direct parser usage)
        self.data_provider = RenpyFlowDataAdapter(use_hybrid=True)
        
        # Current visualization state
        self.current_data: Optional[VisualizationData] = None
        self.nodes: Dict[str, QGraphicsObject] = {}
        self.connections: List[QGraphicsObject] = []
        self.graph: Optional[nx.DiGraph] = None  # Keep for layout algorithms
        
        # Set up view properties (same as before)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # Connect scene selection changes
        self.scene.selectionChanged.connect(self.on_selection_changed)
    
    def load_project(self, project_path: str, use_sdk: bool = False) -> None:
        """
        Load and visualize a project using the data provider.
        
        Args:
            project_path: Path to the Renpy project
            use_sdk: Whether to force SDK analysis
        """
        try:
            # Get visualization data from provider
            self.current_data = self.data_provider.analyze_project(project_path, use_sdk)
            
            # Load the data into visualization
            self.load_flow_data(self.current_data)
            
        except Exception as e:
            print(f"❌ Failed to load project: {e}")
            QMessageBox.warning(self, "Load Error", f"Failed to load project:\n{str(e)}")
    
    def load_flow_data(self, data: VisualizationData) -> None:
        """
        Load visualization data and create the visual representation.
        
        This replaces the old load_flow_graph() method with clean interface.
        """
        self.clear_visualization()
        self.current_data = data
        
        # Create visual nodes
        for node_data in data.nodes:
            visual_node = self._create_visual_node(node_data)
            if visual_node:
                self.scene.addItem(visual_node)
                self.nodes[node_data.node_id] = visual_node
        
        # Create visual connections
        for conn_data in data.connections:
            visual_conn = self._create_visual_connection(conn_data)
            if visual_conn:
                self.scene.addItem(visual_conn)
                self.connections.append(visual_conn)
        
        # Create NetworkX graph for layout algorithms (simplified)
        self._create_networkx_graph_for_layout()
        
        # Apply default layout
        self.apply_layout('narrative_hierarchical')
    
    def _create_visual_node(self, node_data: VisualizationNode) -> Optional[QGraphicsObject]:
        """Create appropriate visual node based on type."""
        
        if node_data.node_type == 'label':
            return VNLabelNodeV2(node_data)
        
        elif node_data.node_type == 'menu_container':
            # Use existing MenuContainerGraphicsItem with metadata conversion
            container_data = {
                'container_id': node_data.node_id,
                'display_name': node_data.display_name,
                'parent_label': node_data.metadata.get('parent_label', ''),
                'total_choices': node_data.metadata.get('total_choices', 0),
                'complexity_level': node_data.metadata.get('complexity_level', 'simple'),
                'prompt': node_data.metadata.get('prompt', '')
            }
            return MenuContainerGraphicsItem(container_data)
        
        elif node_data.node_type == 'choice_button':
            # Use existing ChoiceButtonGraphicsItem with metadata conversion
            choice_data = {
                'choice_id': node_data.node_id,
                'choice_text': node_data.display_name,
                'parent_container': node_data.metadata.get('parent_container', ''),
                'choice_index': node_data.metadata.get('choice_index', 0),
                'condition': node_data.metadata.get('condition'),
                'destination': node_data.metadata.get('destination'),
                'action_type': node_data.metadata.get('action_type', 'jump')
            }
            return ChoiceButtonGraphicsItem(choice_data)
        
        else:
            # Fallback to label node
            return VNLabelNodeV2(node_data)
    
    def _create_visual_connection(self, conn_data: VisualizationConnection) -> Optional[QGraphicsObject]:
        """Create visual connection between nodes."""
        
        source_node = self.nodes.get(conn_data.source_node_id)
        target_node = self.nodes.get(conn_data.target_node_id)
        
        if not source_node or not target_node:
            return None
        
        return VNFlowConnectionV2(conn_data, source_node, target_node)
    
    def _create_networkx_graph_for_layout(self):
        """Create NetworkX graph from visualization data for layout algorithms."""
        if not self.current_data:
            return
        
        self.graph = nx.DiGraph()
        
        # Add nodes
        for node in self.current_data.nodes:
            self.graph.add_node(
                node.node_id,
                node_type=node.node_type,
                display_name=node.display_name,
                **node.metadata
            )
        
        # Add edges
        for conn in self.current_data.connections:
            if conn.source_node_id in self.graph.nodes and conn.target_node_id in self.graph.nodes:
                self.graph.add_edge(
                    conn.source_node_id,
                    conn.target_node_id,
                    connection_type=conn.connection_type,
                    **conn.metadata
                )
    
    def apply_layout(self, layout_type: str) -> None:
        """
        Apply a specific layout algorithm to the current data.
        
        This keeps all the existing layout algorithms from the original visualizer.
        """
        if not self.graph or not self.nodes:
            return
        
        # Use the same layout algorithms as before
        if layout_type == 'narrative_hierarchical':
            pos = self._narrative_hierarchical_layout()
        elif layout_type == 'spring':
            pos = nx.spring_layout(self.graph, k=3, iterations=100)
        elif layout_type == 'circular':
            pos = nx.circular_layout(self.graph)
        else:
            pos = nx.spring_layout(self.graph)
        
        # Apply positions to nodes
        scale = 400
        for node_id, (x, y) in pos.items():
            if node_id in self.nodes:
                self.nodes[node_id].setPos(x * scale, y * scale)
        
        # Update connections
        for connection in self.connections:
            if hasattr(connection, 'update_path'):
                connection.update_path()
        
        # Fit view to content
        self.fit_view_to_content()
    
    def _narrative_hierarchical_layout(self) -> Dict[str, Tuple[float, float]]:
        """Create a narrative-aware hierarchical layout (simplified version)."""
        if not self.graph:
            return {}
        
        # Find start nodes
        start_nodes = [n for n in self.graph.nodes() 
                      if self.graph.nodes[n].get('semantic_type') == 'start' or
                      n.lower() in ['start', 'main', 'begin']]
        
        if not start_nodes:
            start_nodes = [n for n in self.graph.nodes() if self.graph.in_degree(n) == 0]
        
        if not start_nodes:
            start_nodes = [list(self.graph.nodes())[0]]
        
        # Create simple hierarchical layout
        pos = {}
        visited = set()
        current_y = 0
        
        def layout_from_node(node, x_offset, y_level):
            nonlocal current_y
            if node in visited:
                return
            
            visited.add(node)
            pos[node] = (x_offset, y_level)
            
            # Layout successors
            successors = list(self.graph.successors(node))
            for i, successor in enumerate(successors):
                layout_from_node(successor, x_offset + i * 2, y_level - 1)
        
        # Layout from each start node
        for i, start in enumerate(start_nodes):
            layout_from_node(start, i * 4, 0)
        
        # Layout any remaining nodes
        remaining = set(self.graph.nodes()) - visited
        for i, node in enumerate(remaining):
            pos[node] = (len(start_nodes) * 4 + i, -2)
        
        return pos
    
    def highlight_path(self, start_node: str, end_node: str) -> None:
        """Highlight a path between two nodes."""
        # Implementation for path highlighting
        pass
    
    def export_image(self, file_path: str) -> bool:
        """Export the current visualization as an image."""
        # Implementation for image export
        return True
    
    def clear_visualization(self):
        """Clear current visualization."""
        self.scene.clear()
        self.nodes.clear()
        self.connections.clear()
        self.graph = None
    
    def fit_view_to_content(self):
        """Fit the view to show all content."""
        if self.scene.items():
            self.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
    
    def on_selection_changed(self):
        """Handle selection changes in the scene."""
        selected_items = self.scene.selectedItems()
        if selected_items:
            item = selected_items[0]
            if hasattr(item, 'vis_node'):
                # Emit signal with node data
                self.node_selected.emit(item.vis_node.node_id, item.vis_node.metadata or {})
    
    # Mouse event handling (same as before)
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events.""" 
        super().mouseMoveEvent(event)
    
    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming."""
        zoom_factor = 1.15
        if event.angleDelta().y() > 0:
            self.scale(zoom_factor, zoom_factor)
        else:
            self.scale(1/zoom_factor, 1/zoom_factor)
        
        event.accept()
    
    def reset_view(self):
        """Reset the view to default zoom and position."""
        self.resetTransform()
        self.fit_view_to_content() 