# Flow Visualizer POC Refactoring Plan

## 🎯 Objective

Refactor the flow visualizer POC to properly separate parsing concerns from visualization concerns, leveraging the enhanced SDK integration from renpy-source-api.

## 📋 Current State vs Target State

### Current Architecture Issues

1. **Mixed Responsibilities**: Flow visualizer directly imports and uses parsing modules
2. **Tight Coupling**: Direct dependency on renpy-source-api internal structures
3. **Data Conversion**: Complex NetworkX conversion happening in visualizer
4. **SDK Benefits Unused**: Current POC doesn't leverage the new hybrid parser

### Target Architecture Benefits

1. **Clean Separation**: Visualizer only handles graphics and interaction
2. **Standardized Interface**: Well-defined data contracts between components
3. **SDK Enhancement**: Leverages authoritative parsing for complex VNs
4. **Maintainability**: Changes to parsing don't affect visualization

## 🔧 Implementation Phases

### Phase 1: Create Adapter Layer

**File**: `ideas-lab/flow-visualizer-poc/renpy_data_adapter.py`

This adapter implements the `FlowDataProvider` interface and bridges the gap between the renpy-source-api and the standardized visualization interface.

```python
from typing import Dict, List, Any
import sys
from pathlib import Path

# Add renpy-source-api to path
app_dir = Path(__file__).parent.parent.parent / "app"
sys.path.insert(0, str(app_dir / "renpy-source-api"))

from flow_visualizer_interface import FlowDataProvider, VisualizationData, VisualizationNode, VisualizationConnection
from sdk_integration import HybridRenpyParser
from parser import RenpyParser

class RenpyFlowDataAdapter(FlowDataProvider):
    """
    Adapter that converts renpy-source-api data to standardized visualization format.
    """

    def __init__(self, use_hybrid: bool = True):
        self.use_hybrid = use_hybrid
        if use_hybrid:
            self.parser = HybridRenpyParser()
        else:
            self.parser = RenpyParser()
        self.last_analysis_metadata = {}

    def analyze_project(self, project_path: str, use_sdk: bool = False) -> VisualizationData:
        """Convert renpy-source-api analysis to visualization format."""

        # Use the enhanced parser
        if self.use_hybrid:
            overview = self.parser.analyze_project(project_path, force_sdk=use_sdk, verbose=True)

            # Get analysis stats if available
            if hasattr(self.parser, 'get_analysis_stats'):
                self.last_analysis_metadata = self.parser.get_analysis_stats()
        else:
            overview = self.parser.analyze_project(project_path)

        # Build flow graph
        flow_graph = self.parser.build_flow_graph(project_path)

        # Convert to visualization format
        nodes = self._convert_labels_to_nodes(flow_graph)
        connections = self._convert_flows_to_connections(flow_graph)

        # Add menu container nodes
        menu_nodes, menu_connections = self._create_menu_containers(flow_graph)
        nodes.extend(menu_nodes)
        connections.extend(menu_connections)

        return VisualizationData(
            nodes=nodes,
            connections=connections,
            project_info={
                'total_labels': overview.total_labels,
                'total_characters': overview.total_characters,
                'total_menus': overview.total_menus,
                'project_path': project_path
            },
            analysis_metadata=self.last_analysis_metadata
        )

    def _convert_labels_to_nodes(self, flow_graph: Dict) -> List[VisualizationNode]:
        """Convert LabelNode objects to VisualizationNode objects."""
        nodes = []

        for label_name, label_node in flow_graph.items():
            # Skip labels that will be represented by menu containers
            if label_node.has_menu:
                continue

            node_type = self._determine_node_type(label_name, label_node)
            color_hint = self._get_color_for_type(node_type)

            node = VisualizationNode(
                node_id=label_name,
                node_type='label',
                display_name=label_name,
                color_hint=color_hint,
                metadata={
                    'file_path': label_node.file_path,
                    'line_number': label_node.line_number,
                    'has_dialogue': label_node.has_dialogue,
                    'flow_complexity': label_node.flow_complexity,
                    'semantic_type': node_type
                }
            )
            nodes.append(node)

        return nodes

    def _create_menu_containers(self, flow_graph: Dict) -> tuple:
        """Create menu container nodes and choice button nodes."""
        container_nodes = []
        choice_connections = []

        for label_name, label_node in flow_graph.items():
            if not label_node.has_menu:
                continue

            for menu_idx, menu_node in enumerate(label_node.menu_nodes):
                # Create menu container
                container_id = f"{label_name}_menu_{menu_idx}"
                container = VisualizationNode(
                    node_id=container_id,
                    node_type='menu_container',
                    display_name=menu_node.name or f"Menu {menu_idx + 1}",
                    color_hint='yellow',
                    metadata={
                        'parent_label': label_name,
                        'menu_index': menu_idx,
                        'complexity_level': menu_node.complexity_level,
                        'total_choices': menu_node.total_choices,
                        'prompt': menu_node.prompt
                    }
                )
                container_nodes.append(container)

                # Create choice buttons
                for choice_idx, choice in enumerate(menu_node.choices):
                    choice_id = f"{container_id}_choice_{choice_idx}"
                    choice_node = VisualizationNode(
                        node_id=choice_id,
                        node_type='choice_button',
                        display_name=choice.text,
                        color_hint='lightblue',
                        metadata={
                            'parent_container': container_id,
                            'choice_index': choice_idx,
                            'condition': choice.condition,
                            'destination': choice.destination,
                            'action_type': choice.action_type
                        }
                    )
                    container_nodes.append(choice_node)

                    # Create connection from choice to destination
                    if choice.destination and choice.destination != '<return>':
                        connection = VisualizationConnection(
                            connection_id=f"{choice_id}_to_{choice.destination}",
                            source_node_id=choice_id,
                            target_node_id=choice.destination,
                            connection_type='menu_choice',
                            label=choice.text[:20] + "..." if len(choice.text) > 20 else choice.text,
                            condition=choice.condition,
                            metadata={
                                'choice_index': choice_idx,
                                'action_type': choice.action_type
                            }
                        )
                        choice_connections.append(connection)

        return container_nodes, choice_connections
```

### Phase 2: Refactor Flow Visualizer

**File**: `ideas-lab/flow-visualizer-poc/vn_flow_visualizer_v2.py`

Create a new version of the flow visualizer that uses the standardized interface:

```python
# Remove direct imports of renpy-source-api modules
# Replace with interface imports
from flow_visualizer_interface import FlowVisualizer, VisualizationData, VisualizationNode
from renpy_data_adapter import RenpyFlowDataAdapter

class VNFlowVisualizerV2(QGraphicsView, FlowVisualizer):
    """
    Enhanced flow visualizer with clean separation of concerns.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Initialize graphics components (unchanged)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        # Data provider (replaces direct parser usage)
        self.data_provider = RenpyFlowDataAdapter(use_hybrid=True)

        # Current visualization state
        self.current_data: Optional[VisualizationData] = None
        self.nodes: Dict[str, QGraphicsObject] = {}
        self.connections: List[QGraphicsObject] = []

    def load_project(self, project_path: str, use_sdk: bool = False) -> None:
        """
        Load and visualize a project using the data provider.
        """
        try:
            # Get visualization data from provider
            self.current_data = self.data_provider.analyze_project(project_path, use_sdk)

            # Load the data into visualization
            self.load_flow_data(self.current_data)

        except Exception as e:
            print(f"❌ Failed to load project: {e}")

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
            self.scene.addItem(visual_node)
            self.nodes[node_data.node_id] = visual_node

        # Create visual connections
        for conn_data in data.connections:
            visual_conn = self._create_visual_connection(conn_data)
            if visual_conn:
                self.scene.addItem(visual_conn)
                self.connections.append(visual_conn)

        # Apply default layout
        self.apply_layout('narrative_hierarchical')

    def _create_visual_node(self, node_data: VisualizationNode) -> QGraphicsObject:
        """Create appropriate visual node based on type."""

        if node_data.node_type == 'label':
            return VNLabelNode(
                node_id=node_data.node_id,
                node_data=node_data.metadata,
                semantic_classification=node_data.metadata.get('semantic_type', 'linear')
            )
        elif node_data.node_type == 'menu_container':
            return MenuContainerGraphicsItem(
                container_id=node_data.node_id,
                display_name=node_data.display_name,
                metadata=node_data.metadata
            )
        elif node_data.node_type == 'choice_button':
            return ChoiceButtonGraphicsItem(
                choice_id=node_data.node_id,
                choice_text=node_data.display_name,
                metadata=node_data.metadata
            )
        else:
            # Fallback to label node
            return VNLabelNode(node_data.node_id, node_data.metadata)
```

### Phase 3: Update Integration Points

**File**: `ideas-lab/flow-visualizer-poc/renpy_flow_visualizer.py`

Update the main application to use the new architecture:

```python
class RenpyFlowMapper(QMainWindow):
    """Updated main application using new architecture."""

    def __init__(self):
        super().__init__()

        # Use new visualizer
        self.visualizer = VNFlowVisualizerV2()

        # Rest of initialization...

    def load_and_analyze_project(self):
        """Load project using enhanced parsing."""
        project_path = self.get_project_path()

        if not project_path:
            return

        # Show option for SDK analysis
        use_sdk = self._should_use_sdk_analysis(project_path)

        # Load project
        self.visualizer.load_project(project_path, use_sdk=use_sdk)

        # Update UI with analysis metadata
        metadata = self.visualizer.data_provider.get_analysis_metadata()
        self._update_analysis_info(metadata)

    def _should_use_sdk_analysis(self, project_path: str) -> bool:
        """Ask user if they want to use SDK analysis for complex VNs."""
        # Could integrate the ComplexityDetector here
        from sdk_integration import ComplexityDetector

        detector = ComplexityDetector()
        needs_sdk, reasons = detector.needs_sdk_analysis(project_path)

        if needs_sdk:
            reply = QMessageBox.question(
                self,
                "Complex VN Detected",
                f"This VN has complex structures that may benefit from SDK analysis:\n\n" +
                "\n".join(f"• {reason}" for reason in reasons[:3]) +
                "\n\nUse enhanced SDK analysis? (slower but more accurate)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            return reply == QMessageBox.StandardButton.Yes

        return False
```

## 🚀 Benefits of This Refactoring

### 1. **Clean Separation of Concerns**

- Flow visualizer only handles graphics and user interaction
- All parsing logic contained in renpy-source-api
- Clear, well-defined interfaces between components

### 2. **SDK Integration Benefits**

- Automatic detection of complex VN structures
- Authoritative parsing for circular references and implicit flows
- Better handling of Python code in menu choices
- Future-proof against new Ren'Py features

### 3. **Improved Maintainability**

- Changes to parsing don't affect visualization code
- Easy to add new node types or visualization features
- Clean testing boundaries
- Standardized data formats

### 4. **Enhanced User Experience**

- Option to use SDK analysis for complex VNs
- Better accuracy for creatively-coded VNs
- Clear feedback about analysis method used
- Performance optimizations through caching

## 📅 Implementation Timeline

1. **Week 1**: Create interface definitions and adapter layer
2. **Week 2**: Refactor flow visualizer to use new interface
3. **Week 3**: Update main application and integration points
4. **Week 4**: Testing, optimization, and documentation

## 🧪 Testing Strategy

1. **Unit Tests**: Test adapter conversion logic
2. **Integration Tests**: Test visualizer with different VN types
3. **Regression Tests**: Ensure existing functionality still works
4. **Performance Tests**: Compare SDK vs regex analysis performance
5. **User Testing**: Test with complex VNs that previously had issues

This refactoring will resolve the circular development issues mentioned and provide a solid foundation for handling complex VN structures accurately.
