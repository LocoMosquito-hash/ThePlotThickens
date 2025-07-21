"""
VN Flow Visualizer V2 - Simple Working Version

A simplified but working demonstration of the clean interface approach.
This shows how the visualizer can use VisualizationData without direct renpy-source-api dependencies.
"""

from typing import Dict, Any, Optional, List
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem, QGraphicsPathItem, QGraphicsItem
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
        # SAFETY: Guard against invalid states that cause QPainter errors
        if not self.source_node or not self.target_node:
            return
        
        # SAFETY: Don't update if nodes are not properly initialized
        try:
            source_scene = self.source_node.scene()
            target_scene = self.target_node.scene()
            if not source_scene or not target_scene:
                return
        except Exception as e:
            print(f"[ERROR] Failed to get node scenes: {e}")
            return
        
        # SAFETY: Check if graphics items are in a valid state
        try:
            # Get anchor points on the edges of nodes
            source_point = self._get_source_anchor()
            target_point = self._get_target_anchor()
            
            # SAFETY: Validate anchor points
            if source_point.isNull() or target_point.isNull():
                return
            
            # Create Bezier curve
            path = QPainterPath()
            path.moveTo(source_point)
            
            # Calculate control points for smooth downward curve
            dx = target_point.x() - source_point.x()
            dy = target_point.y() - source_point.y()
            
            # Control points for smooth hierarchical flow (downward curves)
            control_offset = max(50, abs(dy) * 0.3)  # Minimum curve for readability
            ctrl1 = QPointF(source_point.x(), source_point.y() + control_offset)
            ctrl2 = QPointF(target_point.x(), target_point.y() - control_offset)
            
            path.cubicTo(ctrl1, ctrl2, target_point)
            
            # Add arrowhead at target
            arrow = self._create_arrowhead(target_point, source_point)
            if not arrow.isEmpty():
                path.addPolygon(arrow)
            
            # SAFETY: Only set path if we're in a valid state
            try:
                connection_scene = self.scene()
                if connection_scene and path.elementCount() > 0:
                    self.setPath(path)
            except Exception as e:
                print(f"[ERROR] Failed to set path on scene: {e}")
                
        except Exception as e:
            # SAFETY: Catch any QPainter-related errors and skip update
            pass
    
    def _get_source_anchor(self) -> QPointF:
        """Get connection point on source node (bottom edge center for downward flow)."""
        try:
            if self.source_node.parentItem():
                # For child items, get scene position
                source_rect = self.source_node.sceneBoundingRect()
            else:
                source_rect = self.source_node.boundingRect()
                source_rect.translate(self.source_node.pos())
            
            return QPointF(source_rect.center().x(), source_rect.bottom())
        except Exception:
            # Return null point if calculation fails
            return QPointF()
    
    def _get_target_anchor(self) -> QPointF:
        """Get connection point on target node (top edge center for downward flow)."""
        try:
            if self.target_node.parentItem():
                # For child items, get scene position
                target_rect = self.target_node.sceneBoundingRect()
            else:
                target_rect = self.target_node.boundingRect()
                target_rect.translate(self.target_node.pos())
            
            return QPointF(target_rect.center().x(), target_rect.top())
        except Exception:
            # Return null point if calculation fails
            return QPointF()
    
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
        
        # Track connections attached to this node for automatic updates
        self.connected_beziers: List[BezierConnection] = []
        
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
        
        # FIXED: Set interactive flags based on node type for proper parent-child behavior
        if vis_node.node_type == 'choice_button':
            # Choice buttons should NOT be individually movable - they move with their container
            self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable, False)
            self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable, True)
            # Note: choice buttons get parented to containers later, so they'll move with container
            
        else:
            # Regular nodes and containers can be moved independently
            self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable, True)
            self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable, True)
        
        # Enable position change notifications for all node types
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        
        # Tooltip
        tooltip_lines = [f"ID: {vis_node.node_id}", f"Type: {vis_node.node_type}"]
        
        # Add behavior info based on node type
        if vis_node.node_type == 'choice_button':
            tooltip_lines.append("[LINKED] Moves with parent container")
            tooltip_lines.append("(Not individually draggable)")
        elif vis_node.node_type == 'menu_container':
            tooltip_lines.append("[CONTAINER] Drag to move with all choices")
        else:
            tooltip_lines.append("[MOVABLE] Drag to move")
        
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
    
    def add_connection(self, connection: 'BezierConnection'):
        """Register a Bezier connection attached to this node."""
        if connection not in self.connected_beziers:
            self.connected_beziers.append(connection)
    
    def remove_connection(self, connection: 'BezierConnection'):
        """Unregister a Bezier connection from this node."""
        if connection in self.connected_beziers:
            self.connected_beziers.remove(connection)
    
    def itemChange(self, change, value):
        """Override to detect position changes and update connected Bezier curves."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # THROTTLE: Only update connections if we're in a valid state and not during layout
            # This prevents QPainter flooding during rapid position changes
            try:
                scene = self.scene()
                if scene and hasattr(scene, 'views') and scene.views():
                    try:
                        # Update all connected Bezier curves when this node moves
                        for connection in self.connected_beziers:
                            if connection.scene():  # Only update if connection is still in scene
                                connection.update_path()
                        
                        # Also update connections for child nodes (e.g., choice buttons in menu containers)
                        # When a parent moves, children move with it but don't trigger their own itemChange
                        for child in self.childItems():
                            if isinstance(child, SimpleVisualNode):
                                for child_connection in child.connected_beziers:
                                    if child_connection.scene():  # Only update if connection is still in scene
                                        child_connection.update_path()
                    except Exception as e:
                        print(f"[ERROR] Failed to update connections in itemChange: {e}")
            except Exception as e:
                print(f"[ERROR] Failed to get scene in itemChange: {e}")
        
        return super().itemChange(change, value)


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
        
        # Connect selection changes to update node details
        self.scene.selectionChanged.connect(self.on_selection_changed)
        
        # Data provider using clean interface
        self.data_provider = RenpyFlowDataAdapter(use_hybrid=True)
        
        # Current state
        self.current_data: Optional[VisualizationData] = None
        self.nodes: Dict[str, SimpleVisualNode] = {}
        self.connections: List[BezierConnection] = []
        
        # Edge highlighting state
        self.edge_highlighting_enabled: bool = False
        self.highlighted_edges: List[BezierConnection] = []
        self.default_edge_color = QColor(80, 80, 80)
        self.incoming_edge_color = QColor(255, 255, 0)  # Yellow
        self.outgoing_edge_color = QColor(255, 0, 0)    # Red
        
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
                
                # CRITICAL: Set container as parent BEFORE positioning (this makes them move together)
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
            source_node: Optional[SimpleVisualNode] = self.nodes.get(connection.source_node_id)
            target_node: Optional[SimpleVisualNode] = self.nodes.get(connection.target_node_id)
            
            if source_node and target_node:
                # Create Bezier connection with arrow
                bezier_connection = BezierConnection(source_node, target_node)
                self.scene.addItem(bezier_connection)
                
                # Register connection with both source and target nodes for automatic updates
                source_node.add_connection(bezier_connection)
                target_node.add_connection(bezier_connection)
                
                # Store connection for potential updates
                self.connections.append(bezier_connection)
        
        print(f"✅ Created {len(self.nodes)} visual nodes and {len(data.connections)} connections")
        
        # Auto-apply default layout (dot_like) and fit view
        self.apply_layout("dot_like")  # This already calls update_all_connections() and _update_scene_margins()
        self.fit_view_to_content()
    
    def clear_visualization(self):
        """Clear the current visualization."""
        # Reset edge highlighting state
        self.reset_edge_highlighting()
        
        # Unregister all connections from nodes before clearing
        for connection in self.connections:
            if hasattr(connection, 'source_node') and isinstance(connection.source_node, SimpleVisualNode):
                connection.source_node.remove_connection(connection)
            if hasattr(connection, 'target_node') and isinstance(connection.target_node, SimpleVisualNode):
                connection.target_node.remove_connection(connection)
        
        self.scene.clear()
        self.nodes.clear()
        self.connections.clear()
    
    def fit_view_to_content(self):
        """Fit the view to show all content with comfortable margins."""
        if self.scene.items():
            # Get the actual content bounds
            content_rect = self.scene.itemsBoundingRect()
            
            # Add generous margins around the content for comfortable panning
            margin = 500  # Generous margin on all sides
            expanded_rect = content_rect.adjusted(-margin, -margin, margin, margin)
            
            # Set the scene rectangle to include the margins
            self.scene.setSceneRect(expanded_rect)
            
            # Fit the view to the actual content (not the expanded scene)
            self.fitInView(content_rect, Qt.AspectRatioMode.KeepAspectRatio)
    
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
    
    def set_edge_highlighting_enabled(self, enabled: bool):
        """Enable or disable edge highlighting for selected nodes."""
        self.edge_highlighting_enabled = enabled
        
        if not enabled:
            # Reset all highlighted edges to default color
            self.reset_edge_highlighting()
        else:
            # If there's a current selection, highlight its edges
            selected_items = self.scene.selectedItems()
            if selected_items:
                item = selected_items[0]
                if hasattr(item, 'vis_node'):
                    self.highlight_node_edges(item.vis_node.node_id)
    
    def reset_edge_highlighting(self):
        """Reset all highlighted edges to their default color."""
        for edge in self.highlighted_edges:
            pen = edge.pen()
            pen.setColor(self.default_edge_color)
            edge.setPen(pen)
        self.highlighted_edges.clear()
    
    def highlight_node_edges(self, node_id: str):
        """Highlight incoming and outgoing edges for the specified node."""
        if not self.edge_highlighting_enabled:
            return
            
        # First reset any previously highlighted edges
        self.reset_edge_highlighting()
        
        # Find all connections involving this node
        for connection in self.connections:
            if hasattr(connection, 'source_node') and hasattr(connection, 'target_node'):
                source_id = getattr(connection.source_node, 'node_id', None)
                target_id = getattr(connection.target_node, 'node_id', None)
                
                pen = connection.pen()
                highlighted = False
                
                # Check if this is an incoming edge (target is selected node)
                if target_id == node_id:
                    pen.setColor(self.incoming_edge_color)  # Yellow for incoming
                    highlighted = True
                
                # Check if this is an outgoing edge (source is selected node)
                elif source_id == node_id:
                    pen.setColor(self.outgoing_edge_color)  # Red for outgoing
                    highlighted = True
                
                if highlighted:
                    connection.setPen(pen)
                    self.highlighted_edges.append(connection)

    def on_selection_changed(self):
        """Handle selection changes in the scene."""
        selected_items = self.scene.selectedItems()
        if selected_items:
            item = selected_items[0]
            if hasattr(item, 'vis_node'):
                node_id = item.vis_node.node_id
                # Emit signal with node data
                self.node_selected.emit(node_id, item.vis_node.metadata or {})
                
                # Highlight edges if enabled
                if self.edge_highlighting_enabled:
                    self.highlight_node_edges(node_id)
        else:
            # Clear selection - emit empty signal
            self.node_selected.emit("", {})
            # Reset edge highlighting when no node is selected
            if self.edge_highlighting_enabled:
                self.reset_edge_highlighting()
    
    def update_all_connections(self):
        """Update all connection paths after nodes have been moved."""
        # SAFETY: Guard against QPainter errors during bulk updates
        # Handle both scene() method and scene property
        try:
            if callable(getattr(self, 'scene', None)):
                current_scene = self.scene()
            else:
                current_scene = getattr(self, 'scene', None)
            
            if current_scene is None:
                print(f"[ERROR] No scene available in update_all_connections")
                return
        except Exception as e:
            print(f"[ERROR] Failed to access scene in update_all_connections: {e}")
            return
        
        # BATCH UPDATE: Disable scene updates during bulk connection updates
        # This prevents QPainter flooding and improves performance
        self.setUpdatesEnabled(False)
        try:
            for connection in self.connections:
                try:
                    # Check if connection has a scene and is still in it
                    connection_scene = None
                    if hasattr(connection, 'scene'):
                        if callable(getattr(connection, 'scene')):
                            connection_scene = connection.scene()
                        else:
                            connection_scene = connection.scene
                    
                    if connection_scene:  # Only update connections still in scene
                        connection.update_path()
                except Exception as e:
                    print(f"[ERROR] Failed to update connection {connection}: {e}")
        except Exception as e:
            print(f"[ERROR] Failed during bulk connection updates: {e}")
        finally:
            # BATCH UPDATE: Re-enable updates
            self.setUpdatesEnabled(True)
    
    def apply_layout(self, layout_type: str):
        """Apply a layout algorithm based on the selected type."""
        if not self.nodes:
            return
        
        # BATCH LAYOUT: Disable updates during layout to prevent QPainter flooding
        self.setUpdatesEnabled(False)
        try:
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
            
            # Update all connections to reflect new node positions after layout
            self.update_all_connections()
            
            # Update scene rectangle with margins for comfortable panning
            self._update_scene_margins()
            
        finally:
            # BATCH LAYOUT: Re-enable updates after layout is complete
            self.setUpdatesEnabled(True)
    
    def _update_scene_margins(self):
        """Update scene rectangle with generous margins around content for comfortable panning."""
        if self.scene.items():
            # Get the actual content bounds
            content_rect = self.scene.itemsBoundingRect()
            
            # Add generous margins around the content for comfortable panning
            margin = 500  # Generous margin on all sides
            expanded_rect = content_rect.adjusted(-margin, -margin, margin, margin)
            
            # Set the scene rectangle to include the margins
            self.scene.setSceneRect(expanded_rect)
    
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
        """DOT-like hierarchical layout with cycle detection and SCC handling."""
        import networkx as nx
        
        # Build NetworkX graph from visualization connections
        G = nx.DiGraph()
        
        # Add all nodes
        for node in nodes:
            G.add_node(node.vis_node.node_id, node_obj=node, node_type=node.vis_node.node_type)
        
        # Add edges from connections (with debug info)
        edges_added = 0
        print(f"🐛 DEBUG: Processing {len(self.connections)} connections...")
        
        # Build a map of all connections including filtered nodes
        all_connections = {}
        for connection in self.connections:
            if hasattr(connection, 'source_node') and hasattr(connection, 'target_node'):
                source_node = connection.source_node
                target_node = connection.target_node
                
                if source_node and target_node:
                    source_id = source_node.vis_node.node_id if hasattr(source_node, 'vis_node') else str(source_node)
                    target_id = target_node.vis_node.node_id if hasattr(target_node, 'vis_node') else str(target_node)
                    
                    if source_id not in all_connections:
                        all_connections[source_id] = []
                    all_connections[source_id].append(target_id)
        
        # Build graph with indirect connections through filtered choice buttons
        for connection in self.connections:
            if hasattr(connection, 'source_node') and hasattr(connection, 'target_node'):
                source_node = connection.source_node
                target_node = connection.target_node
                
                if source_node and target_node:
                    source_id = source_node.vis_node.node_id if hasattr(source_node, 'vis_node') else str(source_node)
                    target_id = target_node.vis_node.node_id if hasattr(target_node, 'vis_node') else str(target_node)
                    
                    # Check if both nodes are in our graph (top-level nodes)
                    if source_id in G and target_id in G:
                        G.add_edge(source_id, target_id)
                        edges_added += 1
                    else:
                        # Handle connections through filtered choice buttons
                        source_in_graph = source_id in G
                        target_in_graph = target_id in G
                        
                        # If source is in graph but target is not, try to find indirect path
                        if source_in_graph and not target_in_graph:
                            if target_id in all_connections:
                                for indirect_target in all_connections[target_id]:
                                    if indirect_target in G:
                                        G.add_edge(source_id, indirect_target)
                                        edges_added += 1
                        
                        # If source is not in graph but target is, find parent menu
                        elif not source_in_graph and target_in_graph:
                            if 'choice' in source_id:
                                menu_parts = source_id.split('_choice_')
                                if len(menu_parts) > 1:
                                    parent_menu = menu_parts[0]
                                    if parent_menu in G:
                                        G.add_edge(parent_menu, target_id)
                                        edges_added += 1
        
        print(f"✅ Built narrative graph: {len(G.nodes())} nodes, {len(G.edges())} edges ({edges_added}/{len(self.connections)} connections)")
        
        # If graph is empty or has no edges, fall back to simple positioning
        if len(G.nodes()) == 0:
            return self._apply_grid_layout(nodes)
        
        if len(G.edges()) == 0:
            # Just arrange nodes in a single row
            for i, node in enumerate(nodes):
                node.setPos(i * 200, 0)
            return
        
        # 🎯 STEP 1: DETECT CYCLES AND STRONGLY CONNECTED COMPONENTS
        print(f"🔍 Detecting cycles and SCCs...")
        
        # Check if graph is a DAG (no cycles)
        print(f"📊 Checking if graph is DAG...")
        is_dag = nx.is_directed_acyclic_graph(G)
        print(f"📊 Graph is DAG: {is_dag}")
        
        # PERFORMANCE FIX: Skip expensive cycle enumeration, go straight to SCC analysis
        if not is_dag:
            print(f"🔴 Graph has cycles - using SCC-based approach (skipping expensive cycle enumeration)")
        
        print(f"🔍 Finding Strongly Connected Components...")
        try:
            # Find SCCs using Tarjan's algorithm (efficient)
            sccs = list(nx.strongly_connected_components(G))
            scc_count = len(sccs)
            non_trivial_sccs = [scc for scc in sccs if len(scc) > 1]
            
            print(f"🔗 Found {scc_count} SCCs ({len(non_trivial_sccs)} non-trivial):")
            for i, scc in enumerate(non_trivial_sccs[:3]):  # Show first 3 non-trivial SCCs
                scc_nodes = list(scc)[:5]  # Show first 5 nodes in SCC
                more_nodes = f"... ({len(scc)} nodes)" if len(scc) > 5 else f" ({len(scc)} nodes)"
                print(f"   SCC {i+1}: {scc_nodes}{more_nodes} ")
            if len(non_trivial_sccs) > 3:
                print(f"   ... and {len(non_trivial_sccs) - 3} more non-trivial SCCs")
        except Exception as e:
            print(f"⚠️ Error during SCC detection: {e}")
            sccs = [set([node]) for node in G.nodes()]
        
        # 🎯 STEP 2: CREATE CONDENSATION GRAPH (SCC-based hierarchy)
        print(f"🏗️ Creating SCC-based hierarchical layout...")
        
        try:
            # Create condensation graph where each SCC becomes a super-node
            print(f"📈 Creating condensation graph...")
            condensation_graph = nx.condensation(G)
            print(f"📈 Condensation graph created: {len(condensation_graph.nodes())} super-nodes, {len(condensation_graph.edges())} edges")
        except Exception as e:
            print(f"⚠️ Error creating condensation graph: {e}")
            print(f"⚠️ Falling back to simple grid layout")
            self._apply_grid_layout(nodes)
            return
        
        # The condensation graph is always a DAG, so we can use longest path on it
        if len(condensation_graph.edges()) > 0:
            print(f"🗺️ Mapping nodes to SCCs...")
            try:
                # Map each original node to its SCC
                node_to_scc = {}
                scc_to_nodes = {}
                for scc_id, scc_data in condensation_graph.nodes(data=True):
                    scc_nodes = scc_data['members']
                    scc_to_nodes[scc_id] = list(scc_nodes)
                    for node in scc_nodes:
                        node_to_scc[node] = scc_id
                print(f"🗺️ Node mapping completed successfully")
            except Exception as e:
                print(f"⚠️ Error mapping nodes to SCCs: {e}")
                print(f"⚠️ Falling back to simple grid layout")
                self._apply_grid_layout(nodes)
                return
            
            print(f"🔄 Computing longest path on condensation graph...")
            try:
                # Compute longest path on condensation graph
                scc_layers = self._compute_longest_path_on_condensation(condensation_graph, scc_to_nodes)
                print(f"🔄 Longest path computation completed")
            except Exception as e:
                print(f"⚠️ Error computing longest path: {e}")
                print(f"⚠️ Falling back to simple grid layout")
                self._apply_grid_layout(nodes)
                return
            
            print(f"📍 Positioning nodes with SCC layout...")
            try:
                # Position nodes within each SCC and across layers
                self._position_nodes_with_scc_layout(scc_layers, scc_to_nodes, nodes, G)
                print(f"📍 Node positioning completed")
            except Exception as e:
                print(f"⚠️ Error positioning nodes: {e}")
                print(f"⚠️ Falling back to simple grid layout")
                self._apply_grid_layout(nodes)
                return
            
        else:
            # Single SCC or disconnected - use simple layout
            print("⚠️ Using fallback layout for disconnected graph")
            self._apply_grid_layout(nodes)
        
        print(f"✅ Applied SCC-aware hierarchical layout successfully!")

    def _compute_longest_path_on_condensation(self, condensation_graph, scc_to_nodes):
        """Compute longest path layers on the condensation graph (which is always a DAG)."""
        import networkx as nx
        
        # Find source nodes (SCCs with no incoming edges)
        source_sccs = [scc for scc in condensation_graph.nodes() if condensation_graph.in_degree(scc) == 0]
        
        # Fallback: First node
        if not source_sccs:
            source_sccs = [list(condensation_graph.nodes())[0]]
        
        print(f"🐛 Source SCCs: {source_sccs} (containing {sum(len(scc_to_nodes.get(scc, [])) for scc in source_sccs)} nodes)")
        print(f"🐛 Total nodes with in_degree=0: {len([n for n in condensation_graph.nodes() if condensation_graph.in_degree(n) == 0])}")
        
        # Compute longest path distances for each SCC
        scc_distances = {}
        for scc in condensation_graph.nodes():
            scc_distances[scc] = 0
        
        # Process SCCs in topological order
        try:
            topo_order = list(nx.topological_sort(condensation_graph))
            
            for scc in topo_order:
                for successor_scc in condensation_graph.successors(scc):
                    scc_distances[successor_scc] = max(scc_distances[successor_scc], scc_distances[scc] + 1)
            
            # Group SCCs by distance (layer)
            max_distance = max(scc_distances.values()) if scc_distances else 0
            layers = [[] for _ in range(max_distance + 1)]
            
            for scc, distance in scc_distances.items():
                layers[distance].append(scc)
            
            print(f"🎯 SCC layers: {[len(layer) for layer in layers]}")
            return layers
            
        except:
            # Fallback if anything goes wrong
            print("⚠️ Fallback: grouping all SCCs in single layer")
            return [list(condensation_graph.nodes())]

    def _position_nodes_with_scc_layout(self, scc_layers, scc_to_nodes, nodes, original_graph):
        """Position nodes using SCC-aware hierarchical layout."""
        
        # Create node lookup
        node_lookup = {node.vis_node.node_id: node for node in nodes}
        
        # Layout parameters
        LAYER_HEIGHT = 300   # Generous spacing between SCC layers
        NODE_WIDTH = 200     # Horizontal spacing between nodes
        SCC_SPACING = 100    # Extra spacing between different SCCs in same layer
        MAX_NODES_PER_ROW = 12  # More nodes per row since we have better hierarchy now
        
        for layer_idx, layer_sccs in enumerate(scc_layers):
            y_base = layer_idx * LAYER_HEIGHT
            
            # Calculate total width needed for this layer
            total_nodes_in_layer = sum(len(scc_to_nodes.get(scc, [])) for scc in layer_sccs)
            
            x_offset = 0
            
            for scc_idx, scc in enumerate(layer_sccs):
                scc_nodes = scc_to_nodes.get(scc, [])
                
                if not scc_nodes:
                    continue
                
                # Position nodes within this SCC
                if len(scc_nodes) == 1:
                    # Single node - place directly
                    node_id = scc_nodes[0]
                    if node_id in node_lookup:
                        node_lookup[node_id].setPos(x_offset, y_base)
                        x_offset += NODE_WIDTH
                
                elif len(scc_nodes) <= MAX_NODES_PER_ROW:
                    # Small SCC - arrange in single row
                    for i, node_id in enumerate(scc_nodes):
                        if node_id in node_lookup:
                            node_lookup[node_id].setPos(x_offset + i * NODE_WIDTH, y_base)
                    x_offset += len(scc_nodes) * NODE_WIDTH + SCC_SPACING
                
                else:
                    # Large SCC - arrange in compact grid within the SCC
                    rows = (len(scc_nodes) + MAX_NODES_PER_ROW - 1) // MAX_NODES_PER_ROW
                    
                    for i, node_id in enumerate(scc_nodes):
                        if node_id in node_lookup:
                            row = i // MAX_NODES_PER_ROW
                            col = i % MAX_NODES_PER_ROW
                            
                            x_pos = x_offset + col * NODE_WIDTH
                            y_pos = y_base + row * 80  # Compact vertical spacing within SCC
                            
                            node_lookup[node_id].setPos(x_pos, y_pos)
                    
                    # Update offset for next SCC
                    scc_width = min(len(scc_nodes), MAX_NODES_PER_ROW) * NODE_WIDTH
                    x_offset += scc_width + SCC_SPACING
        
        print(f"✅ Positioned {len(nodes)} nodes across {len(scc_layers)} SCC layers")
    
    def _simple_layer_assignment(self, G, start_nodes):
        """Simple fallback layer assignment by node type (DEPRECATED - only for emergencies)."""
        print("⚠️ Using deprecated simple layer assignment - this may not respect narrative hierarchy!")
        
        layers = []
        
        # Group by node type as basic layering
        labels = [n for n in G.nodes() if G.nodes[n].get('node_type') == 'label']
        menus = [n for n in G.nodes() if G.nodes[n].get('node_type') == 'menu_container']
        choices = [n for n in G.nodes() if G.nodes[n].get('node_type') == 'choice_button']
        others = [n for n in G.nodes() if G.nodes[n].get('node_type') not in ['label', 'menu_container', 'choice_button']]
        
        # Create layers from node types
        if start_nodes:
            layers.append(start_nodes)
        if labels:
            layers.append(labels)
        if menus:
            layers.append(menus)
        if choices:
            layers.append(choices)
        if others:
            layers.append(others)
        
        return layers
    
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
        if event.button() == Qt.MouseButton.MiddleButton or (event.button() == Qt.MouseButton.LeftButton and event.modifiers() & Qt.KeyboardModifier.AltModifier):
            # Middle mouse or Alt+Left mouse for panning
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
        if event.button() == Qt.MouseButton.MiddleButton or (event.button() == Qt.MouseButton.LeftButton and self._pan_active):
            # Release middle mouse or Alt+Left mouse panning
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