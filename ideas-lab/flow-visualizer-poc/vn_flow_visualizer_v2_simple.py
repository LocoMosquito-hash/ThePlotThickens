"""
VN Flow Visualizer V2 - Simple Working Version

A simplified but working demonstration of the clean interface approach.
This shows how the visualizer can use VisualizationData without direct renpy-source-api dependencies.
"""

from typing import Dict, Any, Optional, List
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPen, QBrush, QColor, QFont

from flow_visualizer_interface import VisualizationData, VisualizationNode, VisualizationConnection
from renpy_data_adapter import RenpyFlowDataAdapter


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
            width, height = 150, 40
        else:  # label
            width, height = 120, 40
            
        self.setRect(0, 0, width, height)
        
        # Set color based on hint
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
        
        color = color_map.get(vis_node.color_hint, QColor(100, 150, 250))
        self.setBrush(QBrush(color))
        self.setPen(QPen(color.darker(150), 2))
        
        # Add text
        self.text_item = QGraphicsTextItem(vis_node.display_name, self)
        self.text_item.setPos(5, 5)
        self.text_item.setFont(QFont("Arial", 9))
        
        # Make interactive
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable)
        
        # Tooltip
        tooltip_lines = [f"ID: {vis_node.node_id}", f"Type: {vis_node.node_type}"]
        if vis_node.metadata:
            for key, value in list(vis_node.metadata.items())[:3]:
                tooltip_lines.append(f"{key}: {value}")
        self.setToolTip("\n".join(tooltip_lines))


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
        
        # View settings
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        
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
        
        # Create visual nodes
        y_offset = 0
        x_offset = 0
        
        for i, node_data in enumerate(data.nodes):
            visual_node = SimpleVisualNode(node_data)
            
            # Simple layout - arrange in grid
            x = (i % 5) * 250
            y = (i // 5) * 200
            visual_node.setPos(x, y)
            
            self.scene.addItem(visual_node)
            self.nodes[node_data.node_id] = visual_node
        
        # For this simple version, we'll skip connections to focus on the interface
        print(f"✅ Created {len(self.nodes)} visual nodes")
        
        # Fit view to content
        self.fit_view_to_content()
    
    def clear_visualization(self):
        """Clear the current visualization."""
        self.scene.clear()
        self.nodes.clear()
    
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
    
    def apply_layout(self, layout_type: str):
        """Apply a layout algorithm (simplified for demo)."""
        # For now, just do a simple grid layout
        if not self.nodes:
            return
            
        nodes = list(self.nodes.values())
        cols = int(len(nodes) ** 0.5) + 1
        
        for i, node in enumerate(nodes):
            row = i // cols
            col = i % cols
            x = col * 250
            y = row * 200
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