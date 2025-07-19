"""
Renpy Flow Data Adapter

This adapter implements the FlowDataProvider interface and bridges the gap 
between the renpy-source-api and the standardized visualization interface.

This is Phase 1 of the flow visualizer refactoring to achieve clean separation
of concerns between parsing and visualization.
"""

from typing import Dict, List, Any, Optional, Tuple
import sys
from pathlib import Path

# Add renpy-source-api to path
app_dir = Path(__file__).parent.parent.parent / "app"
sys.path.insert(0, str(app_dir / "renpy-source-api"))

from flow_visualizer_interface import (
    FlowDataProvider, VisualizationData, VisualizationNode, 
    VisualizationConnection
)

try:
    from sdk_integration import HybridRenpyParser, ComplexityDetector
    from parser import RenpyParser
    SDK_AVAILABLE = True
except ImportError as e:
    print(f"Warning: SDK integration not available: {e}")
    from parser import RenpyParser
    SDK_AVAILABLE = False


class RenpyFlowDataAdapter(FlowDataProvider):
    """
    Adapter that converts renpy-source-api data to standardized visualization format.
    
    This adapter provides clean separation between parsing logic and visualization,
    leveraging the enhanced SDK integration when available.
    """
    
    def __init__(self, use_hybrid: bool = True):
        """
        Initialize the adapter.
        
        Args:
            use_hybrid: Whether to use hybrid parser (regex + SDK) or just regex
        """
        self.use_hybrid = use_hybrid and SDK_AVAILABLE
        
        if self.use_hybrid:
            self.parser = HybridRenpyParser()
            self.complexity_detector = ComplexityDetector()
        else:
            self.parser = RenpyParser()
            self.complexity_detector = None
            
        self.last_analysis_metadata = {}
        self.last_project_path = None
    
    def analyze_project(self, project_path: str, use_sdk: bool = False) -> VisualizationData:
        """
        Analyze a Renpy project and return visualization data.
        
        Args:
            project_path: Path to the Renpy project directory
            use_sdk: Whether to force use of SDK analysis for complex structures
            
        Returns:
            VisualizationData ready for display
        """
        self.last_project_path = project_path
        
        try:
            # Use the enhanced parser if available
            if self.use_hybrid:
                overview = self.parser.analyze_project(
                    project_path, 
                    force_sdk=use_sdk, 
                    verbose=True
                )
                
                # Get analysis stats if available
                if hasattr(self.parser, 'get_analysis_stats'):
                    self.last_analysis_metadata = self.parser.get_analysis_stats()
                    
                # Add complexity detection info
                if self.complexity_detector:
                    needs_sdk, reasons = self.complexity_detector.needs_sdk_analysis(project_path, overview)
                    self.last_analysis_metadata.update({
                        'complexity_detected': needs_sdk,
                        'complexity_reasons': reasons,
                        'parser_type': 'hybrid'
                    })
            else:
                overview = self.parser.analyze_project(project_path)
                self.last_analysis_metadata = {
                    'parser_type': 'regex_only',
                    'sdk_available': False
                }
            
            # Build flow graph using parser
            flow_graph = self.parser.build_flow_graph(project_path)
            
            # Convert to visualization format
            nodes = self._convert_labels_to_nodes(flow_graph)
            connections = self._convert_flows_to_connections(flow_graph)
            
            # Add menu container nodes and connections
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
                    'total_files': overview.total_rpy_files,
                    'project_path': project_path,
                    'file_list': overview.file_list
                },
                analysis_metadata=self.last_analysis_metadata
            )
            
        except Exception as e:
            # Return minimal data on error
            return VisualizationData(
                nodes=[],
                connections=[],
                project_info={'project_path': project_path, 'error': str(e)},
                analysis_metadata={'error': str(e), 'parser_type': 'failed'}
            )
    
    def get_analysis_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the last analysis (SDK usage, performance, etc.)
        """
        return self.last_analysis_metadata
    
    def search_nodes(self, query: str) -> List[VisualizationNode]:
        """
        Search for nodes matching a query.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching nodes
        """
        # This would implement search functionality
        # For now, return empty list as placeholder
        return []
    
    def _convert_labels_to_nodes(self, flow_graph: Dict[str, Any]) -> List[VisualizationNode]:
        """
        Convert LabelNode objects to VisualizationNode objects.
        
        Args:
            flow_graph: Dictionary mapping label names to LabelNode objects
            
        Returns:
            List of VisualizationNode objects for labels (excluding those with menus)
        """
        nodes = []
        
        for label_name, label_node in flow_graph.items():
            # Skip labels that will be represented by menu containers
            if label_node.has_menu:
                continue
                
            node_type = self._determine_node_type(label_name, label_node)
            color_hint = self._get_color_for_type(node_type)
            
            # Create connections lists
            incoming_connections = [
                flow.source_label for flow in label_node.incoming_flows 
                if flow.source_label
            ]
            outgoing_connections = [
                flow.target_label for flow in label_node.outgoing_flows 
                if flow.target_label and flow.target_label != '<return>'
            ]
            
            node = VisualizationNode(
                node_id=label_name,
                node_type='label',
                display_name=label_name,
                color_hint=color_hint,
                metadata={
                    'file_path': label_node.file_path,
                    'line_number': label_node.line_number,
                    'has_dialogue': label_node.has_dialogue,
                    'is_reachable': label_node.is_reachable,
                    'is_dead_end': label_node.is_dead_end,
                    'flow_complexity': label_node.flow_complexity,
                    'semantic_type': node_type,
                    'incoming_count': len(incoming_connections),
                    'outgoing_count': len(outgoing_connections)
                },
                incoming_connections=incoming_connections,
                outgoing_connections=outgoing_connections
            )
            nodes.append(node)
        
        return nodes
    
    def _convert_flows_to_connections(self, flow_graph: Dict[str, Any]) -> List[VisualizationConnection]:
        """
        Convert flow data to VisualizationConnection objects.
        
        Args:
            flow_graph: Dictionary mapping label names to LabelNode objects
            
        Returns:
            List of VisualizationConnection objects for label-to-label flows
        """
        connections = []
        
        for label_name, label_node in flow_graph.items():
            # Skip labels with menus - their connections will be handled by menu containers
            if label_node.has_menu:
                continue
                
            for flow in label_node.outgoing_flows:
                target_label = flow.target_label
                
                # Skip return flows and flows to non-existent labels
                if not target_label or target_label == '<return>' or target_label not in flow_graph:
                    continue
                
                # Skip flows that go to labels with menus (will be handled by menu container)
                if flow_graph[target_label].has_menu:
                    continue
                
                connection_id = f"{label_name}_to_{target_label}_{flow.flow_type}"
                line_style = self._get_line_style_for_flow_type(flow.flow_type)
                color_hint = self._get_color_for_flow_type(flow.flow_type)
                
                connection = VisualizationConnection(
                    connection_id=connection_id,
                    source_node_id=label_name,
                    target_node_id=target_label,
                    connection_type=flow.flow_type,
                    line_style=line_style,
                    color_hint=color_hint,
                    label=flow.context if flow.context else None,
                    condition=flow.condition if flow.condition else None,
                    metadata={
                        'file_path': flow.file_path,
                        'line_number': flow.line_number,
                        'flow_type': flow.flow_type
                    }
                )
                connections.append(connection)
        
        return connections
    
    def _create_menu_containers(self, flow_graph: Dict[str, Any]) -> Tuple[List[VisualizationNode], List[VisualizationConnection]]:
        """
        Create menu container nodes and choice button nodes with their connections.
        
        Args:
            flow_graph: Dictionary mapping label names to LabelNode objects
            
        Returns:
            Tuple of (container_nodes, choice_connections)
        """
        container_nodes = []
        choice_connections = []
        
        for label_name, label_node in flow_graph.items():
            if not label_node.has_menu:
                continue
                
            for menu_idx, menu_node in enumerate(label_node.menu_nodes):
                # Create menu container
                container_id = f"{label_name}_menu_{menu_idx}"
                container_name = menu_node.name or f"Menu {menu_idx + 1}"
                
                container = VisualizationNode(
                    node_id=container_id,
                    node_type='menu_container',
                    display_name=container_name,
                    color_hint='yellow',
                    size_hint=(200, 150),  # Larger size for containers
                    metadata={
                        'parent_label': label_name,
                        'menu_index': menu_idx,
                        'complexity_level': menu_node.complexity_level,
                        'total_choices': menu_node.total_choices,
                        'prompt': menu_node.prompt,
                        'menu_type': menu_node.menu_type,
                        'has_conditions': menu_node.has_conditions,
                        'story_significance': menu_node.story_significance
                    }
                )
                container_nodes.append(container)
                
                # Create choice buttons
                for choice_idx, choice in enumerate(menu_node.choices):
                    choice_id = f"{container_id}_choice_{choice_idx}"
                    
                    # Truncate long choice text for display
                    display_text = choice.text
                    if len(display_text) > 30:
                        display_text = display_text[:27] + "..."
                    
                    choice_node = VisualizationNode(
                        node_id=choice_id,
                        node_type='choice_button',
                        display_name=display_text,
                        color_hint='lightblue' if not choice.condition else 'orange',
                        size_hint=(150, 40),  # Button size
                        metadata={
                            'parent_container': container_id,
                            'choice_index': choice_idx,
                            'full_text': choice.text,
                            'condition': choice.condition,
                            'destination': choice.destination,
                            'action_type': choice.action_type,
                            'has_condition': choice.has_condition,
                            'estimated_story_impact': choice.estimated_story_impact,
                            'contains_media_references': choice.contains_media_references,
                            'contains_variable_changes': choice.contains_variable_changes
                        }
                    )
                    container_nodes.append(choice_node)
                    
                    # Create connection from choice to destination
                    if choice.destination and choice.destination != '<return>':
                        connection_id = f"{choice_id}_to_{choice.destination}"
                        
                        # Determine connection style based on action type and condition
                        line_style = 'dashed' if choice.condition else 'solid'
                        color_hint = 'orange' if choice.condition else 'gray'
                        if choice.action_type == 'call':
                            color_hint = 'blue'
                        elif choice.action_type == 'return':
                            color_hint = 'red'
                        
                        connection = VisualizationConnection(
                            connection_id=connection_id,
                            source_node_id=choice_id,
                            target_node_id=choice.destination,
                            connection_type='menu_choice',
                            line_style=line_style,
                            color_hint=color_hint,
                            weight_hint=1.5,  # Slightly thicker for menu choices
                            label=display_text,
                            condition=choice.condition,
                            metadata={
                                'choice_index': choice_idx,
                                'action_type': choice.action_type,
                                'parent_menu': container_id,
                                'estimated_impact': choice.estimated_story_impact
                            }
                        )
                        choice_connections.append(connection)
        
        return container_nodes, choice_connections
    
    def _determine_node_type(self, label_name: str, label_node) -> str:
        """
        Determine the semantic type of a node for color coding.
        
        Args:
            label_name: Name of the label
            label_node: LabelNode object
            
        Returns:
            Node type string ('start', 'ending', 'regular')
        """
        # Check for start label
        if label_name.lower() in ['start', 'main', 'begin', 'intro']:
            return 'start'
            
        # Check for ending labels (dead ends with no outgoing flows)
        if label_node.is_dead_end or not label_node.outgoing_flows:
            return 'ending'
            
        # Check for high-traffic labels (many incoming flows)
        if len(label_node.incoming_flows) > 3:
            return 'hub'
            
        # Default to regular label
        return 'regular'
    
    def _get_color_for_type(self, node_type: str) -> str:
        """Get color hint for node type."""
        color_map = {
            'start': 'green',
            'ending': 'red',
            'hub': 'purple',
            'regular': 'lightblue'
        }
        return color_map.get(node_type, 'lightblue')
    
    def _get_line_style_for_flow_type(self, flow_type: str) -> str:
        """Get line style for flow type."""
        style_map = {
            'jump': 'solid',
            'call': 'solid', 
            'return': 'dotted',
            'implicit': 'dashed',
            'menu_choice': 'solid'
        }
        return style_map.get(flow_type, 'solid')
    
    def _get_color_for_flow_type(self, flow_type: str) -> str:
        """Get color hint for flow type."""
        color_map = {
            'jump': 'gray',
            'call': 'blue',
            'return': 'red', 
            'implicit': 'lightgray',
            'menu_choice': 'orange'
        }
        return color_map.get(flow_type, 'gray') 