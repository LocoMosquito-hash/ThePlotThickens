"""
VN Flow Visualizer V2 - Simple Working Version

A simplified but working demonstration of the clean interface approach.
This shows how the visualizer can use VisualizationData without direct renpy-source-api dependencies.
"""

from typing import Dict, Any, Optional, List
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem, QGraphicsPathItem
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QPen, QBrush, QColor, QFont, QPainterPath, QPolygonF
import math

from flow_visualizer_interface import VisualizationData, VisualizationNode, VisualizationConnection
from renpy_data_adapter import RenpyFlowDataAdapter


class BezierConnection(QGraphicsPathItem):
    """A Bezier curve connection with an arrowhead."""
    
    def __init__(self, source_node: QGraphicsRectItem, target_node: QGraphicsRectItem):
        super().__init__()
        self.source_node = source_node
        self.target_node = target_node
        self.update_path()
        
        # Set appearance - NO FILL, only stroke
        pen = QPen(QColor(80, 80, 80), 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.setPen(pen)
        self.setBrush(QBrush(Qt.BrushStyle.NoBrush))  # No fill - only stroke
        
        # Make sure connections are drawn behind nodes
        self.setZValue(-1)
    
    def update_path(self):
        """Update the Bezier path and arrow."""
        # Get anchor points on the edges of nodes
        source_point = self._get_source_anchor()
        target_point = self._get_target_anchor()
        
        # Create Bezier curve
        path = QPainterPath()
        path.moveTo(source_point)
        
        # Calculate control points for smooth curve
        dx = target_point.x() - source_point.x()
        dy = target_point.y() - source_point.y()
        
        # Control points for nice curve
        ctrl1 = QPointF(source_point.x() + dx * 0.3, source_point.y() + abs(dy) * 0.2)
        ctrl2 = QPointF(target_point.x() - dx * 0.3, target_point.y() - abs(dy) * 0.2)
        
        path.cubicTo(ctrl1, ctrl2, target_point)
        
        # Add arrowhead at target
        arrow = self._create_arrowhead(target_point, source_point)
        path.addPolygon(arrow)
        
        self.setPath(path)
    
    def _get_source_anchor(self) -> QPointF:
        """Get connection point on source node (right edge center)."""
        if self.source_node.parentItem():
            # For child items, get scene position
            source_rect = self.source_node.sceneBoundingRect()
        else:
            source_rect = self.source_node.boundingRect()
            source_rect.translate(self.source_node.pos())
        
        return QPointF(source_rect.right(), source_rect.center().y())
    
    def _get_target_anchor(self) -> QPointF:
        """Get connection point on target node (left edge center)."""
        if self.target_node.parentItem():
            # For child items, get scene position
            target_rect = self.target_node.sceneBoundingRect()
        else:
            target_rect = self.target_node.boundingRect()
            target_rect.translate(self.target_node.pos())
        
        return QPointF(target_rect.left(), target_rect.center().y())
    
    def _create_arrowhead(self, tip: QPointF, tail: QPointF) -> QPolygonF:
        """Create an arrowhead polygon pointing toward the tip."""
        # Calculate arrow direction
        dx = tip.x() - tail.x()
        dy = tip.y() - tail.y()
        length = math.sqrt(dx*dx + dy*dy)
        
        if length == 0:
            return QPolygonF()
        
        # Normalize direction
        dx /= length
        dy /= length
        
        # Arrow dimensions
        arrow_length = 12
        arrow_width = 6
        
        # Calculate arrow points
        base = QPointF(tip.x() - dx * arrow_length, tip.y() - dy * arrow_length)
        side1 = QPointF(base.x() - dy * arrow_width, base.y() + dx * arrow_width)
        side2 = QPointF(base.x() + dy * arrow_width, base.y() - dx * arrow_width)
        
        arrow = QPolygonF([tip, side1, side2])
        return arrow


class SimpleVisualNode(QGraphicsRectItem):
    """Simple visual representation of a node for demonstration."""
    
    def __init__(self, vis_node: VisualizationNode):
        super().__init__()
        
        self.vis_node = vis_node
        self.node_id = vis_node.node_id
        
        # Set size based on node type
        if vis_node.node_type == 'menu_container':
            width, height = 200, 150
        elif vis_node.node_type == 'choice_button':
            width, height = 180, 35  # Slightly wider for choice text
        else:  # label
            width, height = 120, 40
            
        self.setRect(0, 0, width, height)
        
        # Set color based on hint
        color_map = {
            'green': QColor(100, 250, 100),
            'lightgreen': QColor(180, 255, 180),  # Light green for entry point
            'red': QColor(250, 100, 100),
            'blue': QColor(100, 150, 250),
            'lightblue': QColor(150, 200, 250),
            'purple': QColor(200, 100, 250),
            'yellow': QColor(250, 250, 100),
            'orange': QColor(255, 140, 0),
            'gray': QColor(150, 150, 150)
        }
        
        color = color_map.get(vis_node.color_hint, QColor(100, 150, 250))
        self.setBrush(QBrush(color))
        self.setPen(QPen(color.darker(150), 2))
        
        # Add text with proper contrast
        self.text_item = QGraphicsTextItem(vis_node.display_name, self)
        self.text_item.setPos(5, 5)
        self.text_item.setFont(QFont("Arial", 9))
        
        # Set text color for proper contrast based on background
        text_color = self._get_contrast_text_color(color)
        self.text_item.setDefaultTextColor(text_color)
        
        # Make interactive
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable)
        
        # Tooltip
        tooltip_lines = [f"ID: {vis_node.node_id}", f"Type: {vis_node.node_type}"]
        if vis_node.metadata:
            for key, value in list(vis_node.metadata.items())[:3]:
                tooltip_lines.append(f"{key}: {value}")
        self.setToolTip("\n".join(tooltip_lines))
    
    def _get_contrast_text_color(self, background_color: QColor) -> QColor:
        """
        Calculate appropriate text color for contrast based on background.
        
        Uses relative luminance to determine if dark or light text is better.
        Based on WCAG contrast guidelines.
        """
        # Get RGB values (0-255)
        r, g, b = background_color.red(), background_color.green(), background_color.blue()
        
        # Convert to relative luminance (0-1)
        # Formula from WCAG 2.0
        def to_linear(c):
            c = c / 255.0
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        
        luminance = 0.2126 * to_linear(r) + 0.7152 * to_linear(g) + 0.0722 * to_linear(b)
        
        # Use black text for light backgrounds, white text for dark backgrounds
        # Threshold at 0.5 gives good results
        if luminance > 0.5:
            return QColor(0, 0, 0)  # Black text
        else:
            return QColor(255, 255, 255)  # White text


class VNFlowVisualizerV2Simple(QGraphicsView):
    """
    Simplified flow visualizer demonstrating clean interface approach.
    
    This version shows how to use VisualizationData without direct renpy-source-api dependencies.
    """
    
    node_selected = pyqtSignal(str, dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize graphics scene
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # Data provider using clean interface
        self.data_provider = RenpyFlowDataAdapter(use_hybrid=True)
        
        # Current state
        self.current_data: Optional[VisualizationData] = None
        self.nodes: Dict[str, SimpleVisualNode] = {}
        self.connections: List[BezierConnection] = []
        
        # View settings
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        
        # Enable middle mouse button panning
        self.setRenderHint(self.renderHints())
        self._pan_active = False
        self._last_pan_point = None
        
    def load_project(self, project_path: str, use_sdk: bool = False) -> bool:
        """
        Load a project using the clean interface.
        
        Args:
            project_path: Path to Renpy project
            use_sdk: Whether to use SDK analysis
            
        Returns:
            True if successful
        """
        try:
            print(f"🔍 Loading project: {project_path}")
            print(f"🔧 Using SDK: {use_sdk}")
            
            # Get visualization data from adapter
            self.current_data = self.data_provider.analyze_project(project_path, use_sdk)
            
            # Load the data
            self.load_flow_data(self.current_data)
            
            # Show analysis info
            metadata = self.data_provider.get_analysis_metadata()
            print(f"📊 Analysis completed:")
            print(f"   Parser type: {metadata.get('parser_type', 'unknown')}")
            if 'sdk_usage_percent' in metadata:
                print(f"   SDK usage: {metadata['sdk_usage_percent']:.1f}%")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to load project: {e}")
            return False
    
    def load_flow_data(self, data: VisualizationData) -> None:
        """
        Load visualization data - this is the clean interface method.
        
        Args:
            data: Standardized visualization data
        """
        self.clear_visualization()
        self.current_data = data
        
        print(f"📦 Loading visualization data:")
        print(f"   Nodes: {len(data.nodes)}")
        print(f"   Connections: {len(data.connections)}")
        
        # Create visual nodes with proper menu container hierarchy
        menu_containers = {}  # Track container nodes
        choice_buttons_data = []   # Track choice button data for later processing
        
        # First pass: Create containers and regular nodes
        for i, node_data in enumerate(data.nodes):
            if node_data.node_type == 'menu_container':
                visual_node = SimpleVisualNode(node_data)
                # Position containers in a grid
                x = (len(menu_containers) % 3) * 300  # 3 containers per row
                y = (len(menu_containers) // 3) * 250  # Multiple rows if needed
                visual_node.setPos(x, y)
                menu_containers[node_data.node_id] = visual_node
                self.scene.addItem(visual_node)
                self.nodes[node_data.node_id] = visual_node
                
            elif node_data.node_type == 'choice_button':
                # Store choice button data for second pass
                choice_buttons_data.append(node_data)
                
            else:
                # Regular label nodes
                visual_node = SimpleVisualNode(node_data)
                x = (i % 5) * 250
                y = (i // 5) * 200
                visual_node.setPos(x, y)
                self.scene.addItem(visual_node)
                self.nodes[node_data.node_id] = visual_node
        
        # Second pass: Create choice buttons as children of their containers
        for choice_data in choice_buttons_data:
            parent_container_id = choice_data.metadata.get('parent_container')
            
            if parent_container_id and parent_container_id in menu_containers:
                container = menu_containers[parent_container_id]
                choice_index = choice_data.metadata.get('choice_index', 0)
                
                # Create choice button
                choice_visual = SimpleVisualNode(choice_data)
                
                # Set container as parent BEFORE positioning (this is crucial)
                choice_visual.setParentItem(container)
                
                # Position relative to container (0,0 is container's top-left)
                x_offset = 10  # Left margin
                y_offset = 25 + (choice_index * 40)  # Below container header
                choice_visual.setPos(x_offset, y_offset)
                
                # Store in nodes dict for connections
                self.nodes[choice_data.node_id] = choice_visual
            else:
                # Fallback: add as regular node if no container found
                choice_visual = SimpleVisualNode(choice_data)
                self.scene.addItem(choice_visual)
                self.nodes[choice_data.node_id] = choice_visual
        
        # Create visual connections with Bezier curves and arrows
        for connection in data.connections:
            source_node = self.nodes.get(connection.source_node_id)
            target_node = self.nodes.get(connection.target_node_id)
            
            if source_node and target_node:
                # Create Bezier connection with arrow
                bezier_connection = BezierConnection(source_node, target_node)
                self.scene.addItem(bezier_connection)
                
                # Store connection for potential updates
                self.connections.append(bezier_connection)
        
        print(f"✅ Created {len(self.nodes)} visual nodes and {len(data.connections)} connections")
        
        # Auto-apply default layout (dot_like) and fit view
        self.apply_layout("dot_like")
        self.update_all_connections()
        self.fit_view_to_content()
    
    def clear_visualization(self):
        """Clear the current visualization."""
        self.scene.clear()
        self.nodes.clear()
        self.connections.clear()
    
    def fit_view_to_content(self):
        """Fit the view to show all content."""
        if self.scene.items():
            self.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
    
    def reset_view(self):
        """Reset view to default zoom and position."""
        self.resetTransform()
        self.fit_view_to_content()
    
    def search_and_select_node(self, node_id: str):
        """Search for and select a node by ID."""
        if node_id in self.nodes:
            node = self.nodes[node_id]
            self.scene.clearSelection()
            node.setSelected(True)
            self.centerOn(node)
            # Emit selection signal
            self.node_selected.emit(node_id, node.vis_node.metadata or {})
    
    def update_all_connections(self):
        """Update all connection paths after nodes have been moved."""
        for connection in self.connections:
            connection.update_path()
    
    def apply_layout(self, layout_type: str):
        """Apply a layout algorithm based on the selected type."""
        if not self.nodes:
            return
            
        # Filter to only include top-level nodes (nodes without parents)
        # This preserves parent-child visual hierarchy for menu containers and choice buttons
        top_level_nodes = [node for node in self.nodes.values() if node.parentItem() is None]
        print(f"🎨 Applying layout: {layout_type} to {len(top_level_nodes)} top-level nodes (filtered from {len(self.nodes)} total)")
        
        if layout_type == "narrative":
            self._apply_narrative_layout(top_level_nodes)
        elif layout_type == "dot_like":
            self._apply_dot_like_layout(top_level_nodes)
        elif layout_type == "topological":
            self._apply_topological_layout(top_level_nodes)
        elif layout_type == "spring":
            self._apply_spring_layout(top_level_nodes)
        elif layout_type == "circular":
            self._apply_circular_layout(top_level_nodes)
        elif layout_type == "hierarchical":
            self._apply_hierarchical_layout(top_level_nodes)
        else:
            # Default grid layout
            self._apply_grid_layout(top_level_nodes)
    
    def _apply_grid_layout(self, nodes):
        """Simple grid layout."""
        cols = int(len(nodes) ** 0.5) + 1
        for i, node in enumerate(nodes):
            row = i // cols
            col = i % cols
            x = col * 250
            y = row * 200
            node.setPos(x, y)
    
    def _apply_narrative_layout(self, nodes):
        """Narrative flow layout - labels on top, menu containers below."""
        labels = [n for n in nodes if n.vis_node.node_type == 'label']
        menu_containers = [n for n in nodes if n.vis_node.node_type == 'menu_container']
        # Note: choice_buttons are now children of containers, so we don't position them directly
        
        # Labels in top tier
        for i, node in enumerate(labels):
            x = i * 180
            y = 0
            node.setPos(x, y)
        
        # Menu containers in middle tier
        for i, node in enumerate(menu_containers):
            x = i * 220
            y = 300
            node.setPos(x, y)
        
        # Choice buttons are automatically positioned relative to their parent containers
    
    def _apply_dot_like_layout(self, nodes):
        """DOT-like hierarchical layout (Sugiyama framework simulation)."""
        # Group nodes by type and create layers
        layers = []
        
        # Layer 0: Start nodes (FIXED - detect visual Start node properly)
        start_nodes = []
        
        # FIRST PRIORITY: Visual Start node (always __VISUAL_START__)
        start_nodes = [n for n in nodes if n.vis_node.node_id == '__VISUAL_START__']
        
        # Second priority: nodes with node_type='start' 
        if not start_nodes:
            start_nodes = [n for n in nodes if n.vis_node.node_type == 'start']
        
        # Third priority: nodes literally named "start"
        if not start_nodes:
            start_nodes = [n for n in nodes if n.vis_node.node_id.lower() == 'start']
        
        # Fourth priority: nodes with "start" or "intro" in the name
        if not start_nodes:
            start_nodes = [n for n in nodes if 'start' in n.vis_node.node_id.lower() or 'intro' in n.vis_node.node_id.lower()]
        
        # Last resort: first node
        if not start_nodes and nodes:
            start_nodes = [nodes[0]]

        
        # Layer 1: Labels
        labels = [n for n in nodes if n.vis_node.node_type == 'label' and n not in start_nodes]
        
        # Layer 2: Menu containers
        menu_containers = [n for n in nodes if n.vis_node.node_type == 'menu_container']
        
        # Layer 3: Choice buttons
        choice_buttons = [n for n in nodes if n.vis_node.node_type == 'choice_button']
        
        layers = [start_nodes, labels, menu_containers, choice_buttons]
        
        # Position nodes layer by layer
        y_positions = [0, 200, 400, 600]
        
        for layer_idx, layer in enumerate(layers):
            if not layer:
                continue
                
            y = y_positions[layer_idx]
            
            # Spread nodes horizontally within each layer
            total_width = max(1200, len(layer) * 180)
            x_spacing = total_width / (len(layer) + 1)
            
            for i, node in enumerate(layer):
                x = (i + 1) * x_spacing - total_width / 2
                node.setPos(x, y)
    
    def _apply_topological_layout(self, nodes):
        """Simple topological sort layout."""
        # Sort nodes by node_id for consistent ordering
        sorted_nodes = sorted(nodes, key=lambda n: n.vis_node.node_id)
        
        # Create tiers based on node type priority
        tiers = {
            'label': 0,
            'menu_container': 1,
            'choice_button': 2
        }
        
        tier_nodes = {0: [], 1: [], 2: []}
        
        for node in sorted_nodes:
            tier = tiers.get(node.vis_node.node_type, 2)
            tier_nodes[tier].append(node)
        
        # Position each tier
        for tier, tier_node_list in tier_nodes.items():
            y = tier * 250
            for i, node in enumerate(tier_node_list):
                x = i * 200
                node.setPos(x, y)
    
    def _apply_spring_layout(self, nodes):
        """Simple spring-based layout simulation."""
        import math
        
        # Initialize positions randomly
        for i, node in enumerate(nodes):
            angle = (i * 2 * math.pi) / len(nodes)
            radius = 200 + (i % 3) * 100
            x = math.cos(angle) * radius
            y = math.sin(angle) * radius
            node.setPos(x, y)
    
    def _apply_circular_layout(self, nodes):
        """Arrange nodes in a circle."""
        import math
        
        if len(nodes) <= 1:
            return
            
        center_x, center_y = 0, 0
        radius = max(300, len(nodes) * 30)
        
        for i, node in enumerate(nodes):
            angle = (i * 2 * math.pi) / len(nodes)
            x = center_x + math.cos(angle) * radius
            y = center_y + math.sin(angle) * radius
            node.setPos(x, y)
    
    def _apply_hierarchical_layout(self, nodes):
        """Tree-like hierarchical layout."""
        # Group by node type
        labels = [n for n in nodes if n.vis_node.node_type == 'label']
        others = [n for n in nodes if n.vis_node.node_type != 'label']
        
        # Labels at root level
        for i, node in enumerate(labels):
            x = i * 300
            y = 0
            node.setPos(x, y)
        
        # Others spread below
        cols = max(1, int(len(others) ** 0.5))
        for i, node in enumerate(others):
            row = i // cols
            col = i % cols
            x = col * 250
            y = 200 + row * 150
            node.setPos(x, y)
    
    def get_project_info(self) -> Dict[str, Any]:
        """Get information about the loaded project."""
        if self.current_data:
            return self.current_data.project_info
        return {}
    
    def get_analysis_metadata(self) -> Dict[str, Any]:
        """Get analysis metadata."""
        return self.data_provider.get_analysis_metadata()
    
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming."""
        zoom_factor = 1.15
        if event.angleDelta().y() > 0:
            self.scale(zoom_factor, zoom_factor)
        else:
            self.scale(1/zoom_factor, 1/zoom_factor)
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self._pan_active = True
            self._last_pan_point = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        if self._pan_active and self._last_pan_point is not None:
            # Calculate delta
            delta = event.position().toPoint() - self._last_pan_point
            self._last_pan_point = event.position().toPoint()
            
            # Pan the view
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self._pan_active = False
            self._last_pan_point = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)
        event.accept()


def test_visualizer_v2():
    """Test function to demonstrate the new visualizer."""
    import sys
    from PyQt6.QtWidgets import QApplication
    from pathlib import Path
    
    app = QApplication(sys.argv)
    
    # Create visualizer
    visualizer = VNFlowVisualizerV2Simple()
    visualizer.resize(800, 600)
    visualizer.setWindowTitle("VN Flow Visualizer V2 - Clean Interface Demo")
    
    # Try to load a test project
    app_dir = Path(__file__).parent.parent.parent / "app"
    test_project = app_dir / "renpy-source-api" / "renpy_sdk" / "vn_analyzer" / "game"
    
    if test_project.exists():
        print("🧪 Testing with SDK analysis...")
        success = visualizer.load_project(str(test_project), use_sdk=True)
        
        if success:
            print("✅ Project loaded successfully!")
            visualizer.show()
            
            # Show project info
            project_info = visualizer.get_project_info()
            print(f"\n📊 Project Info:")
            for key, value in project_info.items():
                print(f"   {key}: {value}")
                
        else:
            print("❌ Failed to load project")
    else:
        print("⚠️ No test project found")
        # Show empty visualizer anyway
        visualizer.show()
    
    return app.exec()


if __name__ == "__main__":
    test_visualizer_v2() 