"""
Renpy Flow Data Adapter

This adapter implements the FlowDataProvider interface and bridges the gap 
between the renpy-source-api and the standardized visualization interface.

This is Phase 1 of the flow visualizer refactoring to achieve clean separation
of concerns between parsing and visualization.

🚨 CRITICAL: This file implements core architectural rules documented in:
📖 FLOW_VISUALIZER_ARCHITECTURE.md
   
Key responsibilities:
- Container-to-choice connection creation (CRITICAL FIX)
- Menu system hierarchy management  
- Flow filtering for menu choices
- SDK-based parsing integration

❗ Always refer to FLOW_VISUALIZER_ARCHITECTURE.md before making changes
"""

from typing import Dict, List, Any, Optional, Tuple, Set
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
            
            # PHASE 1: Detect actual entry point using SDK as source of truth
            actual_entry_point = self._detect_actual_entry_point(project_path)
            
            # Convert to visualization format (entry point detection affects node classification)
            nodes = self._convert_labels_to_nodes(flow_graph, actual_entry_point)
            connections = self._convert_flows_to_connections(flow_graph)
            
            # Add visual Start node and its connection to actual entry point
            visual_start_node, start_connection = self._create_visual_start_node(actual_entry_point)
            nodes.insert(0, visual_start_node)  # Add Start node at beginning
            if start_connection:
                connections.insert(0, start_connection)  # Add Start connection first
            
            # Add menu container nodes and connections
            menu_nodes, menu_connections = self._create_menu_containers(flow_graph)
            nodes.extend(menu_nodes)
            connections.extend(menu_connections)
            
            # Add connections from labels to their menu containers
            label_to_menu_connections = self._create_label_to_menu_connections(flow_graph)
            connections.extend(label_to_menu_connections)
            
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
    
    def _convert_labels_to_nodes(self, flow_graph: Dict[str, Any], actual_entry_point: Optional[str] = None) -> List[VisualizationNode]:
        """
        Convert LabelNode objects to VisualizationNode objects.
        
        Args:
            flow_graph: Dictionary mapping label names to LabelNode objects
            actual_entry_point: The actual entry point label detected by SDK (used to avoid double-classification)
            
        Returns:
            List of VisualizationNode objects for labels
        """
        nodes = []
        
        for label_name, label_node in flow_graph.items():
            # Always include labels, even if they have menus
            # Labels represent entry points and any content before the menu
                
            node_type = self._determine_node_type(label_name, label_node, actual_entry_point)
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
        # DEDUPLICATION: Track created connections to prevent duplicates
        created_connections = set()  # Track (source, target) pairs
        
        # SMART FILTERING: Build set of destinations claimed by menu choices
        menu_choice_destinations = self._get_menu_choice_destinations(flow_graph)
        
        for label_name, label_node in flow_graph.items():
            # Process all flows from all labels (including those with menus)
            for flow in label_node.outgoing_flows:
                source_label = flow.source_label
                target_label = flow.target_label
                
                # Skip return flows and flows to non-existent labels
                if not target_label or target_label == '<return>' or target_label not in flow_graph:
                    continue
                
                # SMART FILTERING: Filter flows strategically
                if flow.flow_type == 'menu_choice':
                    # Skip menu_choice flows - handled by menu containers
                    print(f"[FLOW FILTER] Skipping menu_choice flow: {source_label} → {target_label}")
                    continue
                elif target_label in menu_choice_destinations:
                    # Filter out any direct flows to menu choice destinations from labels that have menus
                    # This prevents competing flows: label → destination vs choice → destination
                    if hasattr(flow_graph.get(source_label, {}), 'menu_nodes') and flow_graph[source_label].menu_nodes:
                        print(f"[FLOW FILTER] Skipping competing flow from menu label: {source_label} → {target_label}")
                        continue
                    else:
                        print(f"[FLOW FILTER] Keeping flow from non-menu label: {source_label} → {target_label}")
                
                # Create the connection if it passes all filters
                # DEDUPLICATION: Check if we already created this connection
                connection_key = (source_label, target_label)
                if connection_key in created_connections:
                    continue
                
                # Mark this connection as created
                created_connections.add(connection_key)
                
                connection_id = f"{source_label}_to_{target_label}_{flow.flow_type}"
                line_style = self._get_line_style_for_flow_type(flow.flow_type)
                color_hint = self._get_color_for_flow_type(flow.flow_type)
                
                connection = VisualizationConnection(
                    connection_id=connection_id,
                    source_node_id=source_label,
                    target_node_id=target_label,
                    connection_type=flow.flow_type,
                    line_style=line_style,
                    color_hint=color_hint,
                    label=flow.context if flow.context else None,
                    condition=flow.condition if flow.condition else None,
                    metadata={
                        'file_path': flow.file_path,
                        'line_number': flow.line_number,
                        'flow_type': flow.flow_type,
                        'connects_to_menu_label': flow_graph[target_label].has_menu if target_label in flow_graph else False
                    }
                )
                connections.append(connection)
        
        return connections
    
    def _get_menu_choice_destinations(self, flow_graph: Dict[str, Any]) -> Set[str]:
        """
        Build set of all destinations that are claimed by menu choices.
        These should not have competing direct flows from labels.
        
        Returns:
            Set of label names that are destinations of menu choices
        """
        menu_destinations = set()
        
        for label_name, label_node in flow_graph.items():
            # Check if label has menus
            if hasattr(label_node, 'menu_nodes') and label_node.menu_nodes:
                for menu_node in label_node.menu_nodes:
                    for choice in menu_node.choices:
                        # Add regular choice destinations (jumps/calls)
                        if choice.destination:
                            menu_destinations.add(choice.destination)
                            print(f"[DESTINATION FILTER] Added choice destination: {choice.destination}")
                        
                        # Add nested labels within choices  
                        for nested_label in choice.nested_labels:
                            menu_destinations.add(nested_label)
                            print(f"[DESTINATION FILTER] Added nested label destination: {nested_label}")
        
        print(f"[DESTINATION FILTER] Total menu choice destinations: {len(menu_destinations)}")
        return menu_destinations
    
    def _create_menu_containers(self, flow_graph: Dict[str, Any]) -> Tuple[List[VisualizationNode], List[VisualizationConnection]]:
        """
        Create menu container nodes and choice button nodes with their connections.
        Now supports hierarchical nested menus while preserving flat menu behavior.
        
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
            
            # Separate top-level and nested MenuNodes
            top_level_menus = [menu for menu in label_node.menu_nodes if not menu.is_nested]
            nested_menus = [menu for menu in label_node.menu_nodes if menu.is_nested]
            
            # Process top-level menus exactly as before (no changes to existing behavior)
            for menu_idx, menu_node in enumerate(top_level_menus):
                container_id = f"{label_name}_menu_{menu_idx}"
                # Prioritize menu prompt for display name, fallback to generic name
                if menu_node.prompt:
                    container_name = menu_node.prompt
                else:
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
                        'story_significance': menu_node.story_significance,
                        'is_nested': False,  # Mark as top-level
                        'nesting_level': 0
                    }
                )
                container_nodes.append(container)
                
                # Process choices for top-level menu (existing logic)
                self._create_choice_buttons_and_connections(
                    menu_node, container_id, label_name, container_nodes, choice_connections
                )
            
            # Process nested menus with hierarchical positioning
            for nested_menu in nested_menus:
                # Create unique container ID that reflects the hierarchy
                nested_container_id = nested_menu.node_id.replace(label_name + "_", f"{label_name}_nested_")
                
                # Create display name that indicates it's nested
                if nested_menu.prompt:
                    nested_container_name = f"↳ {nested_menu.prompt}"
                else:
                    nested_container_name = f"↳ Nested Menu (Level {nested_menu.nesting_level})"
                
                nested_container = VisualizationNode(
                    node_id=nested_container_id,
                    node_type='menu_container',
                    display_name=nested_container_name,
                    color_hint='lightyellow',  # Slightly different color for nested
                    size_hint=(180, 130),  # Slightly smaller for nested menus
                    metadata={
                        'parent_label': label_name,
                        'menu_index': -1,  # Not a top-level menu
                        'complexity_level': nested_menu.complexity_level,
                        'total_choices': nested_menu.total_choices,
                        'prompt': nested_menu.prompt,
                        'menu_type': nested_menu.menu_type,
                        'has_conditions': nested_menu.has_conditions,
                        'story_significance': nested_menu.story_significance,
                        'is_nested': True,  # Mark as nested
                        'nesting_level': nested_menu.nesting_level,
                        'parent_menu_id': nested_menu.parent_menu_id,
                        'original_node_id': nested_menu.node_id  # Keep original for reference
                    }
                )
                container_nodes.append(nested_container)
                
                # Process choices for nested menu
                self._create_choice_buttons_and_connections(
                    nested_menu, nested_container_id, label_name, container_nodes, choice_connections
                )
        
        # PHASE 2: Create hierarchy connections after all containers exist
        self._create_hierarchy_connections(flow_graph, container_nodes, choice_connections)
        
        return container_nodes, choice_connections
    
    def _create_hierarchy_connections(self, flow_graph: Dict[str, Any], container_nodes: List, choice_connections: List):
        """
        Create hierarchy connections between parent choices and their nested menu containers.
        This runs after all containers are created to ensure nested containers exist.
        FIXED: Now processes ALL menu levels recursively, not just top-level menus.
        CRITICAL FIX: Also creates missing connections from menu containers to their choice buttons.
        
        🚨 CRITICAL ARCHITECTURE RULE (see FLOW_VISUALIZER_ARCHITECTURE.md):
        Menu choices MUST be connected to their containers to prevent them from appearing
        as orphan nodes on the first level. This fix solved the "489 nodes on first level" issue.
        
        ❗ DO NOT REMOVE the container-to-choice connection creation logic below!
        """
        # Create lookup for quick container access
        container_lookup = {node.node_id: node for node in container_nodes if node.node_type == 'menu_container'}
        choice_lookup = {node.node_id: node for node in container_nodes if node.node_type == 'choice_button'}
        
        # CRITICAL FIX: Create missing connections from menu containers to their choice buttons
        print(f"[CRITICAL FIX] Creating container-to-choice connections...")
        for container_node in container_nodes:
            if container_node.node_type != 'menu_container':
                continue
                
            container_id = container_node.node_id
            
            # Find all choice buttons that belong to this container
            container_choices = [choice for choice in container_nodes 
                               if (choice.node_type == 'choice_button' and 
                                   choice.metadata.get('parent_container') == container_id)]
            
            # Create connections from container to each of its choices
            for choice_node in container_choices:
                choice_id = choice_node.node_id
                connection_id = f"{container_id}_to_{choice_id}"
                
                connection = VisualizationConnection(
                    connection_id=connection_id,
                    source_node_id=container_id,
                    target_node_id=choice_id,
                    connection_type='container_to_choice',
                    line_style='solid',
                    color_hint='darkblue',  # Container-to-choice connections
                    weight_hint=1.0,
                    label=None,  # No label needed for structural connections
                    metadata={
                        'connection_nature': 'container_structure',
                        'choice_index': choice_node.metadata.get('choice_index'),
                        'is_structural': True  # Mark as structural connection
                    }
                )
                choice_connections.append(connection)
                print(f"[CRITICAL FIX] Connected container {container_id} -> choice {choice_id}")
        
        print(f"[CRITICAL FIX] Container-to-choice connections complete.")
        
        # EXISTING CODE: Create hierarchy connections for nested menus
        for label_name, label_node in flow_graph.items():
            if not label_node.has_menu:
                continue
            
            # FIXED: Process ALL menu nodes (top-level AND nested) instead of just top-level
            for menu_node in label_node.menu_nodes:
                # Determine the container ID based on whether this is a nested menu or not
                if menu_node.is_nested:
                    # For nested menus, use the nested container ID pattern
                    container_id = menu_node.node_id.replace(label_name + "_", f"{label_name}_nested_")
                else:
                    # For top-level menus, use the standard pattern
                    container_id = f"{label_name}_menu_{menu_node.menu_index}"
                
                for choice_idx, choice in enumerate(menu_node.choices):
                    choice_id = f"{container_id}_choice_{choice_idx}"
                    
                    # Check if this choice should connect to a nested menu
                    if not choice.destination or choice.destination == '<return>':
                        # Look for corresponding nested menu container
                        expected_nested_id = f"{menu_node.node_id}_choice_{choice_idx}_menu_1"
                        nested_container_id = expected_nested_id.replace(label_name + "_", f"{label_name}_nested_")
                        
                        # Check if both choice and nested container exist
                        if choice_id in choice_lookup and nested_container_id in container_lookup:
                            # Create hierarchy connection: parent choice -> nested menu container
                            connection_id = f"{choice_id}_to_nested_menu"
                            
                            connection = VisualizationConnection(
                                connection_id=connection_id,
                                source_node_id=choice_id,
                                target_node_id=nested_container_id,
                                connection_type='choice_to_nested_menu',
                                line_style='solid',
                                color_hint='green',  # Distinct color for hierarchy connections
                                weight_hint=2.0,     # Thicker for hierarchy emphasis
                                label=f"→ Nested Menu",
                                condition=choice.condition,
                                metadata={
                                    'choice_index': choice_idx,
                                    'action_type': 'hierarchy',
                                    'parent_menu': container_id,
                                    'nested_menu': nested_container_id,
                                    'connection_nature': 'parent_to_child_menu',
                                    'menu_level': menu_node.nesting_level
                                }
                            )
                            choice_connections.append(connection)
                            print(f"[HIERARCHY] Created L{menu_node.nesting_level} connection: {choice_id} -> {nested_container_id}")
    
    def _create_choice_buttons_and_connections(self, menu_node, container_id: str, label_name: str, 
                                             container_nodes: List, choice_connections: List):
        """
        Helper method to create choice buttons and connections for a menu container.
        Extracted to avoid code duplication between top-level and nested menu processing.
        """
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
            
            # Create connections from choice to nested labels
            for nested_label in choice.nested_labels:
                connection_id = f"{choice_id}_to_{nested_label}"
                
                connection = VisualizationConnection(
                    connection_id=connection_id,
                    source_node_id=choice_id,
                    target_node_id=nested_label,
                    connection_type='choice_to_nested_label',
                    line_style='solid',
                    color_hint='purple',  # Distinct color for nested label connections
                    weight_hint=1.5,
                    label=f"Contains: {nested_label}",
                    condition=choice.condition,
                    metadata={
                        'choice_index': choice_idx,
                        'action_type': 'nested_label',
                        'parent_menu': container_id,
                        'nested_label': nested_label
                    }
                )
                choice_connections.append(connection)
    
    def _create_label_to_menu_connections(self, flow_graph: Dict[str, Any]) -> List[VisualizationConnection]:
        """
        Create connections from labels to their menu containers.
        
        Args:
            flow_graph: Dictionary mapping label names to LabelNode objects
            
        Returns:
            List of VisualizationConnection objects for label-to-menu flows
        """
        connections = []
        
        for label_name, label_node in flow_graph.items():
            # Only create connections for labels that have menus
            if not label_node.has_menu:
                continue
                
            # Create connection from label to its first menu container
            for menu_idx, menu_node in enumerate(label_node.menu_nodes):
                container_id = f"{label_name}_menu_{menu_idx}"  # Fixed: should be menu_idx, not menu_idx + 1
                connection_id = f"{label_name}_to_{container_id}"
                
                connection = VisualizationConnection(
                    connection_id=connection_id,
                    source_node_id=label_name,
                    target_node_id=container_id,
                    connection_type='label_to_menu',
                    line_style='solid',
                    color_hint='blue',
                    weight_hint=2.0,  # Slightly thicker for label-to-menu connections
                    label=f"Menu {menu_idx + 1}" if len(label_node.menu_nodes) > 1 else None,
                    metadata={
                        'menu_index': menu_idx,
                        'menu_prompt': menu_node.prompt,
                        'choice_count': menu_node.total_choices,
                        'complexity_level': menu_node.complexity_level
                    }
                )
                connections.append(connection)
        
        return connections
    
    def _detect_actual_entry_point(self, project_path: str) -> Optional[str]:
        """
        Detect the actual entry point label using SDK as source of truth.
        
        Args:
            project_path: Path to the Renpy project directory
            
        Returns:
            Name of the actual entry point label, or None if not found
        """
        try:
            # Try to use SDK to find the actual entry point
            # Add the renpy-source-api path dynamically
            import sys
            sys.path.insert(0, str(app_dir / "renpy-source-api"))
            from control_flow.start_label_finder import StartLabelFinder
            
            finder = StartLabelFinder(project_path)
            start_line = finder.find_start_label()
            actual_entry_point = start_line.label_name
            
            print(f"🎯 SDK detected actual entry point: '{actual_entry_point}'")
            return actual_entry_point
            
        except Exception as e:
            print(f"⚠️  Could not detect entry point via SDK: {e}")
            # Fallback to common entry point names
            fallback_names = ['start', 'main', 'begin', 'intro']
            print(f"🔄 Using fallback detection for: {', '.join(fallback_names)}")
            return 'start'  # Most common fallback
    
    def _create_visual_start_node(self, actual_entry_point: Optional[str]) -> Tuple[VisualizationNode, Optional[VisualizationConnection]]:
        """
        Create the visual "Start" node and its connection to the actual entry point.
        
        Args:
            actual_entry_point: Name of the actual entry point label
            
        Returns:
            Tuple of (visual_start_node, connection_to_entry_point)
        """
        # Create the visual Start node (always green, always present)
        visual_start_node = VisualizationNode(
            node_id="__VISUAL_START__",  # Special ID to avoid conflicts
            node_type='start',  # This will get green color
            display_name="Start",
            color_hint='green',
            size_hint=(100, 50),
            metadata={
                'is_visual_node': True,  # Flag to identify this as visual-only
                'represents_entry_point': actual_entry_point,
                'semantic_type': 'visual_start',
                'description': 'Visual entry point - always shows where the story begins'
            },
            incoming_connections=[],  # Start node has no incoming connections
            outgoing_connections=[actual_entry_point] if actual_entry_point else []
        )
        
        # Create connection from visual Start to actual entry point
        start_connection = None
        if actual_entry_point:
            start_connection = VisualizationConnection(
                connection_id="__START_TO_ENTRY__",
                source_node_id="__VISUAL_START__",
                target_node_id=actual_entry_point,
                connection_type='visual_start',
                line_style='solid',
                color_hint='green',
                weight_hint=2.5,  # Thicker line to emphasize importance
                label="Entry Point",
                metadata={
                    'is_visual_connection': True,
                    'represents': 'game_entry_flow',
                    'description': f'Visual flow from Start to actual entry point: {actual_entry_point}'
                }
            )
        
        return visual_start_node, start_connection
    
    def _determine_node_type(self, label_name: str, label_node, actual_entry_point: Optional[str] = None) -> str:
        """
        Determine the semantic type of a node for color coding.
        
        Args:
            label_name: Name of the label
            label_node: LabelNode object
            actual_entry_point: The actual entry point label (to avoid marking as 'start' since we have visual Start)
            
        Returns:
            Node type string ('entry_point', 'ending', 'hub', 'regular')
        """
        # NEVER mark any actual label as 'start' type since we have a visual Start node
        # Instead, mark the actual entry point as 'entry_point' type for special styling
        if actual_entry_point and label_name == actual_entry_point:
            return 'entry_point'
            
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
            'start': 'green',           # Visual Start node only
            'entry_point': 'lightgreen', # Actual entry point label (slightly different from visual Start)
            'ending': 'red',
            'hub': 'purple',
            'regular': 'lightblue'
        }
        return color_map.get(node_type, 'lightblue')
    
    def _get_line_style_for_flow_type(self, flow_type: str) -> str:
        """Get line style for flow type."""
        # Line styles by flow type
        line_styles = {
            'jump': 'solid',
            'call': 'dashed',
            'return': 'dotted',
            'menu_choice': 'solid',
            'menu_choice_nested_label': 'solid',
            'conditional': 'solid'
        }
        
        # Color hints by flow type
        color_hints = {
            'jump': 'blue',
            'call': 'green',
            'return': 'gray',
            'menu_choice': 'orange',
            'menu_choice_nested_label': 'purple',
            'conditional': 'red'
        }
        return line_styles.get(flow_type, 'solid')
    
    def _get_color_for_flow_type(self, flow_type: str) -> str:
        """Get color hint for flow type."""
        # Color hints by flow type
        color_hints = {
            'jump': 'blue',
            'call': 'green',
            'return': 'gray',
            'menu_choice': 'orange',
            'menu_choice_nested_label': 'purple',
            'conditional': 'red'
        }
        return color_hints.get(flow_type, 'gray') 