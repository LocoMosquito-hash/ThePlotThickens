"""
VN Flow Visualizer V2 - Simple Working Version (DEMO/TESTING ONLY)

⚠️ **THIS IS NOT THE PRODUCTION VISUALIZER** - Use vn_flow_visualizer.py for all fixes!

🧪 PURPOSE: Clean architecture demonstration and isolated testing only
🚫 DO NOT EDIT: Unless specifically testing clean interface approach
📖 See: VISUALIZER_ARCHITECTURE_GUIDE.md for architecture details

This is a simplified but working demonstration of the clean interface approach.
This shows how the visualizer can use VisualizationData without direct renpy-source-api dependencies.

🎯 PRODUCTION VISUALIZER: vn_flow_visualizer.py
- All bug fixes and features go there
- Used by control panel and main POC application
- Has latest fixes: authoritative hierarchy, layout cleanup, narrative flow

⚠️ THIS FILE STATUS:
- May not have latest fixes from production version
- Used only by renpy_flow_visualizer_v2_main.py
- Kept for clean architecture reference and testing
- Intentionally simplified and may lag behind production features
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
            width = 200
            # Calculate dynamic height based on number of choices
            total_choices = vis_node.metadata.get('total_choices', 1)
            spacing = SimpleVisualNode.get_menu_container_spacing()
            
            # Calculate total height needed for all choices
            total_choice_height = total_choices * spacing['choice_height'] + (total_choices - 1) * spacing['choice_spacing']
            height = spacing['header_height'] + spacing['padding'] + total_choice_height + spacing['padding']
            
            # Ensure minimum height for small menus
            height = max(height, 80)
            
        elif vis_node.node_type == 'choice_button':
            width, height = 180, 35  # Slightly wider for choice text
        elif vis_node.node_type == 'screen_container':
            # Dynamic size based on element count (similar to menu containers)
            element_count = vis_node.metadata.get('element_count', 1)
            width = 200
            height = max(80, 40 + element_count * 30)  # Dynamic height
        elif vis_node.node_type == 'screen_element':
            width, height = 180, 35  # Same as choice buttons
        elif vis_node.node_type == 'screen':  # Legacy single screen nodes
            width, height = 180, 50  # Distinctive size for screens
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
            'gray': QColor(150, 150, 150),
            '#E6E6FA': QColor(230, 230, 250),  # Lavender for screen containers
            '#DDA0DD': QColor(221, 160, 221)   # Plum for screen elements
        }
        
        color = color_map.get(vis_node.color_hint, QColor(100, 150, 250))
        self.setBrush(QBrush(color))
        self.setPen(QPen(color.darker(150), 2))
        
        # Add text with proper contrast
        # Enhanced display name for menu containers to show choice count
        display_text = vis_node.display_name
        if vis_node.node_type == 'menu_container':
            total_choices = vis_node.metadata.get('total_choices', 0)
            if total_choices > 0:
                # Format with choice count
                display_text = f"{vis_node.display_name} ({total_choices} options)"
        
        self.text_item = QGraphicsTextItem(display_text, self)
        self.text_item.setPos(5, 5)
        self.text_item.setFont(QFont("Arial", 9))
        
        # Set text color for proper contrast based on background
        text_color = self._get_contrast_text_color(color)
        self.text_item.setDefaultTextColor(text_color)
        
        # Store the calculated dimensions for reference
        self.calculated_width = width
        self.calculated_height = height
        
        # FIXED: Set interactive flags based on node type for proper parent-child behavior
        if vis_node.node_type in ['choice_button', 'screen_element']:
            # Choice buttons and screen elements should NOT be individually movable - they move with their container
            self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable, False)
            self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable, True)
            # Note: these elements get parented to containers later, so they'll move with container
            
        else:
            # Regular nodes and containers can be moved independently
            self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable, True)
            self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable, True)
        
        # Enable position change notifications for all node types
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        
        # Tooltip
        tooltip_lines = [f"ID: {vis_node.node_id}", f"Type: {vis_node.node_type}"]
        
        # Add behavior info based on node type
        if vis_node.node_type in ['choice_button', 'screen_element']:
            tooltip_lines.append("[LINKED] Moves with parent container")
            tooltip_lines.append("(Not individually draggable)")
        elif vis_node.node_type in ['menu_container', 'screen_container']:
            container_type = "choices" if vis_node.node_type == 'menu_container' else "elements"
            tooltip_lines.append(f"[CONTAINER] Drag to move with all {container_type}")
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
    
    @staticmethod
    def get_menu_container_spacing():
        """Get consistent spacing parameters for menu containers and choice buttons."""
        return {
            'header_height': 25,
            'padding': 10,
            'choice_height': 35,
            'choice_spacing': 4
        }


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
        
        # Keyboard navigation constants
        self.MOVEMENT_SPEED_BASE = 50  # pixels
        self.MOVEMENT_SPEED_2X = self.MOVEMENT_SPEED_BASE * 2
        self.MOVEMENT_SPEED_4X = self.MOVEMENT_SPEED_BASE * 4
        
        # Enable keyboard focus for WASD navigation
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
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
                
            elif node_data.node_type == 'screen_element':
                # Store screen element data for second pass (similar to choice buttons)
                choice_buttons_data.append(node_data)  # Reuse same list for simplicity
                
            elif node_data.node_type in ['screen_container', 'screen']:
                # Screen nodes - special handling with distinct appearance
                visual_node = SimpleVisualNode(node_data)
                # Position screens in a separate area to avoid overlap
                screen_count = len([n for n in data.nodes[:i+1] if n.node_type in ['screen_container', 'screen']])
                x = (screen_count % 4) * 220  # 4 screens per row, wider spacing
                y = -150 - ((screen_count // 4) * 100)  # Above regular nodes, more vertical space
                visual_node.setPos(x, y)
                self.scene.addItem(visual_node)
                self.nodes[node_data.node_id] = visual_node
                
                # Store screen containers for screen element positioning
                if node_data.node_type == 'screen_container':
                    menu_containers[node_data.node_id] = visual_node  # Reuse menu container logic
                
            else:
                # Regular label nodes
                visual_node = SimpleVisualNode(node_data)
                x = (i % 5) * 250
                y = (i // 5) * 200
                visual_node.setPos(x, y)
                self.scene.addItem(visual_node)
                self.nodes[node_data.node_id] = visual_node
        
        # Second pass: Create choice buttons and screen elements as children of their containers
        for choice_data in choice_buttons_data:
            if choice_data.node_type == 'choice_button':
                parent_container_id = choice_data.metadata.get('parent_container')
                
                if parent_container_id and parent_container_id in menu_containers:
                    container = menu_containers[parent_container_id]
                    choice_index = choice_data.metadata.get('choice_index', 0)
                    
                    # Create choice button
                    choice_visual = SimpleVisualNode(choice_data)
                    
                    # CRITICAL: Set container as parent BEFORE positioning (this makes them move together)
                    choice_visual.setParentItem(container)
                    
                    # Position relative to container (0,0 is container's top-left)
                    # Use consistent spacing calculations
                    spacing = SimpleVisualNode.get_menu_container_spacing()
                    
                    x_offset = spacing['padding']  # Left margin
                    y_offset = spacing['header_height'] + spacing['padding'] + (choice_index * (spacing['choice_height'] + spacing['choice_spacing']))
                    choice_visual.setPos(x_offset, y_offset)
                    
                    # Store in nodes dict for connections
                    self.nodes[choice_data.node_id] = choice_visual
                else:
                    # Fallback: add as regular node if no container found
                    choice_visual = SimpleVisualNode(choice_data)
                    self.scene.addItem(choice_visual)
                    self.nodes[choice_data.node_id] = choice_visual
                    
            elif choice_data.node_type == 'screen_element':
                parent_screen_id = choice_data.metadata.get('parent_screen')
                
                if parent_screen_id and parent_screen_id in menu_containers:  # Screen containers stored here
                    container = menu_containers[parent_screen_id]
                    element_index = choice_data.metadata.get('element_index', 0)
                    
                    # Create screen element as child of screen container
                    element_visual = SimpleVisualNode(choice_data)
                    
                    # CRITICAL: Set container as parent BEFORE positioning
                    element_visual.setParentItem(container)
                    
                    # Position relative to container (similar to menu choices but simpler)
                    x_offset = 10  # Small left margin
                    y_offset = 40 + (element_index * 35)  # Header space + element spacing
                    element_visual.setPos(x_offset, y_offset)
                    
                    # Store in nodes dict for connections
                    self.nodes[choice_data.node_id] = element_visual
                else:
                    # Fallback: add as regular node if no container found
                    element_visual = SimpleVisualNode(choice_data)
                    self.scene.addItem(element_visual)
                    self.nodes[choice_data.node_id] = element_visual
        
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
    
    def search_and_select_node(self, search_text: str):
        """
        Search for and select a node by name.
        
        Now works with the AHS (Authoritative Hierarchical System) to provide
        intelligent search across label names, display names, and semantic IDs.
        """
        search_text = search_text.strip()
        if not search_text:
            return False
        
        # Try to use AHS search if available
        if hasattr(self.data_provider, '_authoritative_hierarchy'):
            hierarchy = self.data_provider._authoritative_hierarchy
            if hierarchy:
                matching_hierarchy_nodes = hierarchy.search_nodes(search_text)
                
                if matching_hierarchy_nodes:
                    # Find the graphics item corresponding to the first matching hierarchy node
                    target_hierarchy_node = matching_hierarchy_nodes[0]
                    target_node_id = target_hierarchy_node.content_hash
                    
                    # Find the corresponding graphics item
                    if target_node_id in self.nodes:
                        target_node = self.nodes[target_node_id]
                        
                        # Clear current selection and select the found node
                        self.scene.clearSelection()
                        target_node.setSelected(True)
                        self.centerOn(target_node)
                        
                        # Emit selection signal
                        self.node_selected.emit(target_node_id, target_node.vis_node.metadata or {})
                        
                        print(f"Found and selected node: {target_hierarchy_node.display_name} (ID: {target_node_id[:8]}...)")
                        if len(matching_hierarchy_nodes) > 1:
                            other_matches = [f"{node.display_name}" for node in matching_hierarchy_nodes[1:5]]
                            print(f"Other matches: {other_matches}")
                        
                        return True
                    else:
                        print(f"Found hierarchy node '{target_hierarchy_node.display_name}' but corresponding graphics item not found")
                        return False
                else:
                    print(f"No nodes found matching '{search_text}' in hierarchy")
                    return False
        
        # Fallback: try direct node ID lookup (legacy behavior)
        if search_text in self.nodes:
            node = self.nodes[search_text]
            self.scene.clearSelection()
            node.setSelected(True)
            self.centerOn(node)
            # Emit selection signal
            self.node_selected.emit(search_text, node.vis_node.metadata or {})
            print(f"Found node by direct ID lookup: {search_text}")
            return True
        
        # Fallback: search through display names
        search_text_lower = search_text.lower()
        for node_id, node in self.nodes.items():
            if hasattr(node, 'vis_node') and node.vis_node.display_name:
                if search_text_lower in node.vis_node.display_name.lower():
                    self.scene.clearSelection()
                    node.setSelected(True)
                    self.centerOn(node)
                    self.node_selected.emit(node_id, node.vis_node.metadata or {})
                    print(f"Found node by display name: {node.vis_node.display_name}")
                    return True
        
        print(f"No nodes found matching '{search_text}'")
        return False
    
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
        if len(selected_items) == 1:  # Only update for single selection
            item = selected_items[0]
            if hasattr(item, 'vis_node'):
                node_id = item.vis_node.node_id
                # Create comprehensive node data including connections
                node_data = item.vis_node.metadata.copy() if item.vis_node.metadata else {}
                node_data['incoming_connections'] = item.vis_node.incoming_connections
                node_data['outgoing_connections'] = item.vis_node.outgoing_connections
                
                # Emit signal with full node data
                self.node_selected.emit(node_id, node_data)
                
                # Highlight edges if enabled
                if self.edge_highlighting_enabled:
                    self.highlight_node_edges(node_id)
        else:
            # Clear selection - emit empty signal for no selection or multi-selection
            self.node_selected.emit("", {})
            # Reset edge highlighting when no single node is selected
            if self.edge_highlighting_enabled:
                self.reset_edge_highlighting()
    
    def keyPressEvent(self, event):
        """Handle keyboard navigation with WASD keys and speed modifiers."""
        key = event.key()
        modifiers = event.modifiers()
        
        # Determine movement speed based on modifiers
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            speed = self.MOVEMENT_SPEED_4X  # 4x speed
        elif modifiers & Qt.KeyboardModifier.ControlModifier:
            speed = self.MOVEMENT_SPEED_2X  # 2x speed
        else:
            speed = self.MOVEMENT_SPEED_BASE  # 1x speed
        
        # Handle WASD movement
        if key == Qt.Key.Key_W:  # Move up
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - speed)
            event.accept()
        elif key == Qt.Key.Key_S:  # Move down
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + speed)
            event.accept()
        elif key == Qt.Key.Key_A:  # Move left
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - speed)
            event.accept()
        elif key == Qt.Key.Key_D:  # Move right
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + speed)
            event.accept()
        else:
            # Pass other keys to parent
            super().keyPressEvent(event)
    
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
                    # Large SCC - use clustered force-directed layout instead of grid
                    cluster_positions = self._apply_clustered_force_layout(scc_nodes, original_graph, x_offset, y_base)
                    
                    # Apply positions to nodes
                    for node_id, (x_pos, y_pos) in cluster_positions.items():
                        if node_id in node_lookup:
                            node_lookup[node_id].setPos(x_pos, y_pos)
                    
                    # Update offset for next SCC - use actual width of clustered layout
                    if cluster_positions:
                        cluster_x_coords = [x for x, y in cluster_positions.values()]
                        cluster_width = max(cluster_x_coords) - min(cluster_x_coords) + NODE_WIDTH
                        x_offset += cluster_width + SCC_SPACING
                    else:
                        # Fallback in case clustering fails
                        x_offset += MAX_NODES_PER_ROW * NODE_WIDTH + SCC_SPACING
        
        print(f"✅ Positioned {len(nodes)} nodes across {len(scc_layers)} SCC layers")

    def _apply_clustered_force_layout(self, scc_nodes: list, original_graph, x_offset: float, y_base: float) -> dict:
        """
        Apply clustered force-directed layout for large SCCs.
        
        This replaces the problematic grid layout with:
        1. Community detection to find sub-clusters within the SCC
        2. Force-directed positioning within each sub-cluster  
        3. Meta-positioning of sub-clusters with adaptive spacing
        
        Args:
            scc_nodes: List of node IDs in this large SCC
            original_graph: NetworkX graph for edge information
            x_offset: Starting X position for this SCC
            y_base: Base Y position for this SCC layer
            
        Returns:
            Dictionary mapping node_id -> (x, y) positions
        """
        import networkx as nx
        import math
        
        print(f"🌐 Applying clustered force layout to {len(scc_nodes)} nodes")
        
        try:
            # Step 1: Create subgraph for this SCC
            scc_subgraph = original_graph.subgraph(scc_nodes).copy()
            
            # Step 2: Detect communities within this large SCC using Louvain algorithm
            try:
                import networkx.algorithms.community as nx_comm
                communities = list(nx_comm.louvain_communities(scc_subgraph, seed=42))
                print(f"🎯 Detected {len(communities)} sub-communities: {[len(c) for c in communities]}")
            except:
                # Fallback: Use greedy modularity if Louvain fails
                try:
                    communities = list(nx_comm.greedy_modularity_communities(scc_subgraph))
                    print(f"🎯 Fallback: Detected {len(communities)} communities via greedy modularity")
                except:
                    # Last resort: treat as single community
                    communities = [set(scc_nodes)]
                    print(f"⚠️ Community detection failed, treating as single cluster")
            
            # Step 3: Calculate cluster properties for adaptive spacing
            cluster_info = self._analyze_cluster_properties(communities, scc_nodes)
            
            # Step 4: Position communities using adaptive meta-layout
            community_centers = self._arrange_communities_adaptively(communities, cluster_info, x_offset, y_base)
            
            # Step 5: Apply collision-aware force-directed layout within each community
            final_positions = {}
            
            for (community, center, cluster_props) in zip(communities, community_centers, cluster_info):
                community_list = list(community)
                
                if len(community_list) == 1:
                    # Single node community - place at center with collision buffer
                    final_positions[community_list[0]] = self._adjust_for_collision(community_list[0], center)
                
                elif len(community_list) <= 4:
                    # Small community - collision-aware circular arrangement
                    positions = self._arrange_nodes_collision_aware(community_list, center, cluster_props)
                    final_positions.update(positions)
                
                else:
                    # Larger community - collision-aware force-directed spring layout
                    try:
                        community_subgraph = scc_subgraph.subgraph(community_list)
                        
                        # Use adaptive scale based on cluster properties
                        adaptive_scale = max(300, cluster_props['estimated_width'] * 0.8)
                        adaptive_k = max(250, len(community_list) * 20)  # Scale k with community size
                        
                        spring_positions = nx.spring_layout(
                            community_subgraph, 
                            center=center, 
                            k=adaptive_k,  # Adaptive spring constant
                            iterations=80,  
                            scale=adaptive_scale,  # Adaptive scale based on expected cluster size
                            seed=42
                        )
                        
                        # Convert NetworkX positions with collision adjustment
                        for node_id, (nx_x, nx_y) in spring_positions.items():
                            raw_pos = (center[0] + nx_x, center[1] + nx_y)
                            final_positions[node_id] = self._adjust_for_collision(node_id, raw_pos)
                            
                    except Exception as e:
                        print(f"⚠️ Spring layout failed for community: {e}, using collision-aware fallback")
                        positions = self._arrange_nodes_collision_aware(community_list, center, cluster_props)
                        final_positions.update(positions)
            
            print(f"✅ Clustered force layout complete: {len(final_positions)} nodes positioned")
            return final_positions
            
        except Exception as e:
            print(f"⚠️ Clustered force layout failed: {e}, using grid fallback")
            return self._fallback_grid_layout(scc_nodes, x_offset, y_base)

    def _fallback_grid_layout(self, scc_nodes: list, x_offset: float, y_base: float) -> dict:
        """Fallback grid layout in case clustered layout fails."""
        positions = {}
        MAX_NODES_PER_ROW = 12
        NODE_WIDTH = 200
        
        for i, node_id in enumerate(scc_nodes):
                            row = i // MAX_NODES_PER_ROW
                            col = i % MAX_NODES_PER_ROW
                            
                            x_pos = x_offset + col * NODE_WIDTH
                            y_pos = y_base + row * 80  # Compact vertical spacing
            
                            positions[node_id] = (x_pos, y_pos)
        
        return positions

    def _analyze_cluster_properties(self, communities: list, scc_nodes: list) -> list:
        """Analyze cluster properties for adaptive spacing."""
        import math
        
        cluster_info = []
        
        for community in communities:
            community_list = list(community)
            
            # Estimate space needed based on node types and count
            menu_containers = sum(1 for node_id in community_list 
                                if hasattr(self, 'nodes') and node_id in self.nodes 
                                and getattr(self.nodes[node_id].vis_node, 'node_type', '') == 'menu_container')
            
            regular_nodes = len(community_list) - menu_containers
            
            # Calculate estimated dimensions
            # Menu containers are ~220x120, regular nodes are ~100x30
            estimated_width = max(200, (menu_containers * 220 + regular_nodes * 100) * 0.7)
            estimated_height = max(150, math.sqrt(len(community_list)) * 80)
            
            # Calculate density factor (more nodes = need more space)
            density_factor = 1.0 + (len(community_list) / 20.0)  # Scale up for larger communities
            
            cluster_info.append({
                'size': len(community_list),
                'menu_containers': menu_containers,
                'regular_nodes': regular_nodes,
                'estimated_width': estimated_width * density_factor,
                'estimated_height': estimated_height * density_factor,
                'collision_radius': max(120, estimated_width * 0.3)  # Collision buffer
            })
        
        return cluster_info

    def _arrange_communities_adaptively(self, communities: list, cluster_info: list, x_offset: float, y_base: float) -> list:
        """Arrange community centers using adaptive spacing based on cluster content."""
        import math
        
        num_communities = len(communities)
        community_centers = []
        
        if num_communities == 1:
            # Single community - center it with generous offset
            cluster_props = cluster_info[0]
            buffer = cluster_props['collision_radius']
            community_centers.append((x_offset + buffer, y_base))
        
        elif num_communities <= 6:
            # Small number of communities - adaptive circular arrangement
            
            # Calculate dynamic radius based on largest cluster
            max_cluster_radius = max(props['collision_radius'] for props in cluster_info)
            base_radius = max(400, max_cluster_radius * 2.5)  # Ensure no overlap
            
            center_x = x_offset + base_radius
            center_y = y_base
            
            for i in range(num_communities):
                angle = (2 * math.pi * i) / num_communities
                
                # Add extra spacing for larger clusters
                cluster_radius_factor = cluster_info[i]['collision_radius'] / max_cluster_radius
                adjusted_radius = base_radius * (0.8 + 0.4 * cluster_radius_factor)
                
                x = center_x + adjusted_radius * math.cos(angle)
                y = center_y + adjusted_radius * math.sin(angle)
                community_centers.append((x, y))
        
        else:
            # Many communities - adaptive grid with dynamic spacing
            cols = math.ceil(math.sqrt(num_communities))
            
            # Calculate dynamic spacing based on cluster sizes
            max_width = max(props['estimated_width'] for props in cluster_info)
            max_height = max(props['estimated_height'] for props in cluster_info)
            
            horizontal_spacing = max(500, max_width * 1.3)  # Extra horizontal space as requested
            vertical_spacing = max(300, max_height * 1.2)
            
            for i, props in enumerate(cluster_info):
                row = i // cols
                col = i % cols
                
                # Add extra spacing for larger clusters
                size_factor = props['size'] / max(p['size'] for p in cluster_info)
                adjusted_h_spacing = horizontal_spacing * (0.9 + 0.3 * size_factor)
                adjusted_v_spacing = vertical_spacing * (0.9 + 0.2 * size_factor)
                
                x = x_offset + col * adjusted_h_spacing
                y = y_base + row * adjusted_v_spacing
                community_centers.append((x, y))
        
        return community_centers

    def _adjust_for_collision(self, node_id: str, position: tuple) -> tuple:
        """Adjust node position to avoid collision with menu containers."""
        # Check if this is a menu container - needs more space
        if hasattr(self, 'nodes') and node_id in self.nodes:
            node_type = getattr(self.nodes[node_id].vis_node, 'node_type', '')
            if node_type == 'menu_container':
                # Menu containers need extra collision buffer
                # This is a simplified collision avoidance - in a full implementation
                # you'd check against all other positioned nodes
                return position
        
        # For now, return original position
        # In a full implementation, this would check against all previously positioned nodes
        return position

    def _arrange_nodes_collision_aware(self, nodes: list, center: tuple, cluster_props: dict) -> dict:
        """Arrange nodes in a collision-aware pattern around the center point."""
        import math
        
        positions = {}
        num_nodes = len(nodes)
        
        # Base radius with collision awareness
        base_radius = max(100, cluster_props['collision_radius'] * 0.6)
        
        for i, node_id in enumerate(nodes):
            if num_nodes == 1:
                positions[node_id] = self._adjust_for_collision(node_id, center)
            else:
                angle = (2 * math.pi * i) / num_nodes
                
                # Adjust radius based on node type
                node_radius = base_radius
                if hasattr(self, 'nodes') and node_id in self.nodes:
                    node_type = getattr(self.nodes[node_id].vis_node, 'node_type', '')
                    if node_type == 'menu_container':
                        node_radius = base_radius * 1.4  # Extra space for menu containers
                
                x = center[0] + node_radius * math.cos(angle)
                y = center[1] + node_radius * math.sin(angle)
                positions[node_id] = self._adjust_for_collision(node_id, (x, y))
        
        return positions
    
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