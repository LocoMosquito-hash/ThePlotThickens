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
from authoritative_hierarchy import AuthoritativeHierarchy

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
        print(f"[DEBUG MAIN] Starting analyze_project for: {project_path}")
        
        # Write debug to file
        with open("debug_adapter.log", "a") as f:
            f.write(f"[DEBUG MAIN] Starting analyze_project for: {project_path}\n")
            f.flush()
        
        self.last_project_path = project_path
        
        if self.use_hybrid:
            overview = self.parser.analyze_project(
                project_path, 
                force_sdk=False, 
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
        
        # PHASE 1: Build authoritative hierarchy (NEW!)
        print(f"[ADAPTER] Building authoritative hierarchy alongside current system...")
        hierarchy = AuthoritativeHierarchy()
        hierarchy.build_from_flow_graph(flow_graph)
        
        # Store hierarchy for comparison/debugging  
        self._authoritative_hierarchy = hierarchy
        
        # PHASE 2: Detect actual entry point using SDK as source of truth
        actual_entry_point = self._detect_actual_entry_point(project_path)
        
        # Convert to visualization format (entry point detection affects node classification)
        nodes = self._convert_labels_to_nodes(flow_graph, actual_entry_point)
        connections = self._convert_flows_to_connections(flow_graph)
        
        # Add visual Start node and its connection to actual entry point
        visual_start_node, start_connection = self._create_visual_start_node(actual_entry_point)
        nodes.insert(0, visual_start_node)  # Add Start node at beginning
        if start_connection:
            connections.insert(0, start_connection)  # Add Start connection first
        
        # PHASE 2: Use authoritative hierarchy instead of string-based logic
        if hasattr(self, '_authoritative_hierarchy'):
            print("[PHASE 2] Using authoritative hierarchy for menu containers...")
            menu_nodes, menu_connections = self._create_menu_containers_from_hierarchy()
        else:
            print("[FALLBACK] Using old string-based menu container logic...")
            menu_nodes, menu_connections = self._create_menu_containers(flow_graph)
        
        nodes.extend(menu_nodes)
        connections.extend(menu_connections)
        
        # Add connections from labels to their menu containers
        if hasattr(self, '_authoritative_hierarchy'):
            print("[PHASE 2] Creating label-to-menu connections from hierarchy...")
            label_to_menu_connections = self._create_label_to_menu_connections_from_hierarchy()
        else:
            label_to_menu_connections = self._create_label_to_menu_connections(flow_graph)
        connections.extend(label_to_menu_connections)
        
        # Add choice-to-destination connections from hierarchy (NEW!)
        if hasattr(self, '_authoritative_hierarchy'):
            print("[PHASE 2] Creating choice-to-destination connections from hierarchy...")
            choice_destination_connections = self._create_choice_destination_connections_from_hierarchy()
            connections.extend(choice_destination_connections)
        
        # Add label-to-label flow connections (CRITICAL: This was missing!)
        flow_connections = self._convert_flows_to_connections(flow_graph)
        connections.extend(flow_connections)
        
        # Store flow graph for debugging purposes
        self._last_flow_graph = flow_graph
        
        # PHASE 3: Compare old vs new system (DEBUG)
        self._compare_hierarchy_systems(nodes, connections)
        
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
        
        # CRITICAL FIX: Get nested label names from AHS to prevent duplicates
        nested_label_names = set()
        if hasattr(self, '_authoritative_hierarchy'):
            nested_label_names = self._authoritative_hierarchy.get_nested_label_names()
        
        for label_name, label_node in flow_graph.items():
            # CRITICAL FIX: Skip labels that are handled as nested labels by AHS
            if label_name in nested_label_names:
                print(f"[LABEL PROCESSING] Skipping '{label_name}' - handled as nested label by AHS")
                continue
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
        print(f"[DEBUG CONVERT] Starting _convert_flows_to_connections with {len(flow_graph)} labels")
        
        # Write debug to file as well
        with open("debug_adapter.log", "a") as f:
            f.write(f"[DEBUG CONVERT] Starting _convert_flows_to_connections with {len(flow_graph)} labels\n")
            f.flush()
        
        connections = []
        # DEDUPLICATION: Track created connections to prevent duplicates
        # MODIFIED: Allow multiple connections to label menus for Phase 2 implementation
        created_connections = set()  # Track (source, target) pairs
        
        # SMART FILTERING: Build set of destinations claimed by menu choices
        # MODIFIED: Exclude label menus from this filtering to allow multiple parents
        menu_choice_destinations = self._get_menu_choice_destinations(flow_graph)
        
        # Build set of label menus that should allow multiple parents
        label_menu_names = self._get_label_menu_names(flow_graph)
        
        for label_name, label_node in flow_graph.items():
            # Process all flows from all labels (including those with menus)
            for flow in label_node.outgoing_flows:
                source_label = flow.source_label
                target_label = flow.target_label
                
                # DEBUG: Track day02 flows from the beginning
                if source_label == 'day02_l_conversation' and target_label == 'day02_p_room_choices':
                    print(f"[DEBUG EARLY] Found day02 flow: {source_label} -> {target_label}")
                    print(f"[DEBUG EARLY]   Type: {flow.flow_type}")
                    print(f"[DEBUG EARLY]   Target exists: {target_label in flow_graph}")
                    
                    # Write to file as well
                    with open("debug_adapter.log", "a") as f:
                        f.write(f"[DEBUG EARLY] Found day02 flow: {source_label} -> {target_label}\n")
                        f.write(f"[DEBUG EARLY]   Type: {flow.flow_type}\n")
                        f.write(f"[DEBUG EARLY]   Target exists: {target_label in flow_graph}\n")
                        f.flush()
                
                # Skip return flows and flows to non-existent labels
                if not target_label or target_label == '<return>' or target_label not in flow_graph:
                    if source_label == 'day02_l_conversation' and target_label == 'day02_p_room_choices':
                        print(f"[DEBUG EARLY] SKIPPING day02 flow due to missing target!")
                    continue
                
                # SMART FILTERING: Filter flows strategically
                if flow.flow_type == 'menu_choice':
                    # Allow menu_choice flows to label menus (for multiple parent support)
                    if target_label in label_menu_names:
                        print(f"[FLOW FILTER] Allowing menu_choice flow to label menu: {source_label} → {target_label}")
                    else:
                        # Skip other menu_choice flows - handled by menu containers
                        print(f"[FLOW FILTER] Skipping menu_choice flow: {source_label} → {target_label}")
                        continue
                elif target_label in menu_choice_destinations and target_label not in label_menu_names:
                    # Filter out competing flows EXCEPT for label menus (which can have multiple parents)
                    if hasattr(flow_graph.get(source_label, {}), 'menu_nodes') and flow_graph[source_label].menu_nodes:
                        print(f"[FLOW FILTER] Skipping competing flow from menu label: {source_label} → {target_label}")
                        continue
                    else:
                        print(f"[FLOW FILTER] Keeping flow from non-menu label: {source_label} → {target_label}")
                        
                # DEBUG: Special tracking for day02 flows
                if source_label == 'day02_l_conversation' and target_label == 'day02_p_room_choices':
                    print(f"[DEBUG DAY02] Processing flow: {source_label} → {target_label}")
                    print(f"[DEBUG DAY02]   Type: {flow.flow_type}")
                    print(f"[DEBUG DAY02]   In menu_choice_destinations: {target_label in menu_choice_destinations}")
                    print(f"[DEBUG DAY02]   In label_menu_names: {target_label in label_menu_names}")
                    print(f"[DEBUG DAY02]   Source has menu_nodes: {hasattr(flow_graph.get(source_label, {}), 'menu_nodes') and flow_graph[source_label].menu_nodes}")
                    print(f"[DEBUG DAY02]   Will create connection: TRUE")
                
                # MODIFIED DEDUPLICATION: Allow multiple connections to label menus
                connection_key = (source_label, target_label)
                if connection_key in created_connections and target_label not in label_menu_names:
                    # Only deduplicate non-label-menu targets
                    continue
                
                # Mark this connection as created (but allow duplicates for label menus)
                if target_label not in label_menu_names:
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
    
    def _get_label_menu_names(self, flow_graph: Dict[str, Any]) -> Set[str]:
        """
        Build set of label menu names that can be jumped to directly.
        These should be exempt from competing flow filtering to allow multiple parents.
        
        Returns:
            Set of label menu names (e.g., 'day02_p_room_choices')
        """
        label_menu_names = set()
        print(f"[LABEL MENUS] Starting search across {len(flow_graph)} labels")
        
        for label_name, label_node in flow_graph.items():
            print(f"[LABEL MENUS] Checking label: {label_name}")
            if hasattr(label_node, 'menu_nodes'):
                print(f"[LABEL MENUS]   Has menu_nodes: {bool(label_node.menu_nodes)}")
                if label_node.menu_nodes:
                    for i, menu_node in enumerate(label_node.menu_nodes):
                        print(f"[LABEL MENUS]   Menu {i}: label_name='{menu_node.label_name}'")
                        if menu_node.label_name:
                            # Add the actual label menu name, not the parent label
                            label_menu_names.add(menu_node.label_name)
                            print(f"[LABEL MENUS]   Added label menu: {menu_node.label_name}")
            else:
                print(f"[LABEL MENUS]   No menu_nodes attribute")
        
        print(f"[LABEL MENUS] Found label menus: {label_menu_names}")
        return label_menu_names
    
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
                # Check if this is a label menu (has its own label name)
                if menu_node.label_name:
                    # Label menu - use actual label name and goldish color
                    container_id = menu_node.label_name
                    container_name = menu_node.label_name
                    container_color = 'orange'  # Orange color for label menus (goldish appearance)
                    is_label_menu = True
                else:
                    # Regular menu - use generic naming
                    container_id = f"{label_name}_menu_{menu_idx}"
                    # Prioritize menu prompt for display name, fallback to generic name
                    if menu_node.prompt:
                        container_name = menu_node.prompt
                    else:
                        container_name = menu_node.name or f"Menu {menu_idx + 1}"
                    container_color = 'yellow'  # Regular yellow for normal menus
                    is_label_menu = False
                
                container = VisualizationNode(
                    node_id=container_id,
                    node_type='menu_container',
                    display_name=container_name,
                    color_hint=container_color,
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
                        'nesting_level': 0,
                        'is_label_menu': is_label_menu,  # Mark label menus
                        'label_name': menu_node.label_name  # Store original label name
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
        NEW FIX: Creates choice-to-nested-menu connections for proper visualization hierarchy.
        
        🚨 CRITICAL ARCHITECTURE RULE (see FLOW_VISUALIZER_ARCHITECTURE.md):
        Menu choices MUST be connected to their containers to prevent them from appearing
        as orphan nodes on the first level. This fix solved the "489 nodes on first level" issue.
        
        ❗ DO NOT REMOVE the container-to-choice connection creation logic below!
        """
        # METHOD START TEST: This should always appear
        print("[METHOD START] _create_hierarchy_connections method called")
        
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
        
        # COMPREHENSIVE FIX: Create missing intermediate containers AND choice buttons
        print(f"[HIERARCHY FIX] Creating complete missing hierarchy (containers + choices)...")
        
        # Find orphan containers that need parents
        container_targets = set()
        for conn in choice_connections:
            if hasattr(conn, 'target_node_id'):
                container_targets.add(conn.target_node_id)
        
        orphan_containers = []
        for container in container_nodes:
            if (container.node_type == 'menu_container' and 
                container.node_id not in container_targets and
                '_nested_menu_' in container.node_id and 
                container.node_id.endswith('_menu_1')):
                orphan_containers.append(container)
        
        print(f"[HIERARCHY FIX] Found {len(orphan_containers)} orphan containers needing complete hierarchy")
        
        created_intermediate_containers = 0
        created_intermediate_choices = 0
        
        for orphan in orphan_containers:
            orphan_id = orphan.node_id
            
            # Extract expected parent choice button name: remove "_menu_1"
            if orphan_id.endswith('_menu_1'):
                expected_parent_choice_id = orphan_id[:-7]  # Remove "_menu_1"
                
                # Check if this choice button already exists
                choice_exists = any(node.node_id == expected_parent_choice_id 
                                  for node in container_nodes if node.node_type == 'choice_button')
                
                if not choice_exists and '_choice_' in expected_parent_choice_id:
                    # Extract the parent container this choice should belong to
                    # e.g., day01_p_room_action_menu_nested_menu_1_choice_1 → day01_p_room_action_menu_nested_menu_1
                    parent_container_id = expected_parent_choice_id.rsplit('_choice_', 1)[0]
                    
                    # Check if parent container exists
                    parent_container_exists = any(node.node_id == parent_container_id 
                                                for node in container_nodes if node.node_type == 'menu_container')
                    
                    if not parent_container_exists:
                        # Create the missing intermediate container first
                        missing_container = VisualizationNode(
                            node_id=parent_container_id,
                            node_type='menu_container',
                            display_name=f"Nested Menu {parent_container_id.split('_nested_menu_')[-1]}",
                            color_hint='#FFA500'  # Orange for menu containers
                        )
                        container_nodes.append(missing_container)
                        created_intermediate_containers += 1
                        
                        # Try to connect this intermediate container to ITS parent
                        # Pattern: day01_p_room_action_menu_nested_menu_1 should connect to 
                        # a choice in day01_p_room_action_menu
                        if '_nested_menu_' in parent_container_id:
                            grandparent_label = parent_container_id.split('_nested_menu_')[0]
                            
                            # Look for existing choice buttons in the grandparent that could be the parent
                            potential_parent_choices = [n for n in container_nodes 
                                                      if (n.node_type == 'choice_button' and 
                                                          n.node_id.startswith(grandparent_label) and
                                                          not '_nested_menu_' in n.node_id)]
                            
                            if potential_parent_choices:
                                # Connect to the first suitable parent choice found
                                parent_choice = potential_parent_choices[0]
                                grandparent_conn = VisualizationConnection(
                                    connection_id=f"{parent_choice.node_id}_to_{parent_container_id}",
                                    source_node_id=parent_choice.node_id,
                                    target_node_id=parent_container_id,
                                    connection_type='choice_to_menu',
                                    color_hint='orange',
                                    weight_hint=1.5
                                )
                                choice_connections.append(grandparent_conn)
                                print(f"[HIERARCHY FIX] Connected grandparent: {parent_choice.node_id} → {parent_container_id}")
                    
                    # Now create the missing intermediate choice button
                    missing_choice = VisualizationNode(
                        node_id=expected_parent_choice_id,
                        node_type='choice_button',
                        display_name=f"Choice {expected_parent_choice_id.split('_choice_')[-1]}",
                        color_hint='#87CEEB'  # Sky blue for intermediate choices
                    )
                    container_nodes.append(missing_choice)
                    
                    # Create connection: parent container → intermediate choice
                    container_to_choice_conn = VisualizationConnection(
                        connection_id=f"{parent_container_id}_to_{expected_parent_choice_id}",
                        source_node_id=parent_container_id,
                        target_node_id=expected_parent_choice_id,
                        connection_type='container_to_choice',
                        color_hint='blue',
                        weight_hint=1.0
                    )
                    choice_connections.append(container_to_choice_conn)
                    
                    # Create connection: intermediate choice → orphan container
                    choice_to_menu_conn = VisualizationConnection(
                        connection_id=f"{expected_parent_choice_id}_to_{orphan_id}",
                        source_node_id=expected_parent_choice_id,
                        target_node_id=orphan_id,
                        connection_type='choice_to_menu',
                        color_hint='orange',
                        weight_hint=1.5
                    )
                    choice_connections.append(choice_to_menu_conn)
                    
                    created_intermediate_choices += 1
                    print(f"[HIERARCHY FIX] Created complete hierarchy: {parent_container_id} → {expected_parent_choice_id} → {orphan_id}")
        
        print(f"[HIERARCHY FIX] Created {created_intermediate_containers} containers and {created_intermediate_choices} choice buttons")
        print("[FIX] Successfully completed hierarchy connections.")
        
        # Track processed containers to avoid duplicates
        nested_containers_processed = set()
        
        for choice_node in container_nodes:
            if choice_node.node_type != 'choice_button':
                continue
                
            choice_id = choice_node.node_id
            
            # Look for nested menu containers that belong to this choice
            # CORRECTED Pattern: {choice_id}_menu_{menu_index}
            # This handles cases like: day01_p_room_action_menu_nested_menu_1_choice_1 -> day01_p_room_action_menu_nested_menu_1_choice_1_menu_1
            nested_containers = [container for container in container_nodes 
                               if (container.node_type == 'menu_container' and 
                                   container.node_id.startswith(choice_id + '_menu_') and
                                   container.node_id not in nested_containers_processed)]
            
            # Create connections from choice to each of its nested menu containers
            for nested_container in nested_containers:
                nested_container_id = nested_container.node_id
                connection_id = f"{choice_id}_to_{nested_container_id}"
                nested_containers_processed.add(nested_container_id)
                
                connection = VisualizationConnection(
                    connection_id=connection_id,
                    source_node_id=choice_id,
                    target_node_id=nested_container_id,
                    connection_type='choice_to_menu',
                    line_style='solid',
                    color_hint='orange',  # Choice-to-menu connections
                    weight_hint=1.5,
                    label=None,  # No label needed for structural connections
                    metadata={
                        'connection_nature': 'choice_to_nested_menu',
                        'choice_parent': choice_node.metadata.get('parent_container'),
                        'is_hierarchical': True  # Mark as hierarchical connection
                    }
                )
                choice_connections.append(connection)
                print(f"[FIXED] Connected choice {choice_id} -> nested menu {nested_container_id}")
        
        # ADDITIONAL FIX: Handle orphan containers with alternative naming patterns
        print(f"[ADDITIONAL FIX] Connecting remaining orphan containers...")
        
        # Find containers that are still orphans after the above logic
        connected_containers = {conn.target_node_id for conn in choice_connections if conn.connection_type == 'choice_to_menu'}
        orphan_containers = [container for container in container_nodes 
                           if (container.node_type == 'menu_container' and 
                               container.node_id not in connected_containers and
                               ('nested' in container.node_id or '_menu_1' in container.node_id))]
        
        print(f"[ADDITIONAL FIX] Found {len(orphan_containers)} remaining orphan containers")
        
        for orphan_container in orphan_containers:
            container_id = orphan_container.node_id
            
            # Try alternative patterns to find the parent choice
            # Pattern 1: Remove '_menu_1' suffix to get parent choice
            if container_id.endswith('_menu_1'):
                potential_parent = container_id[:-7]  # Remove '_menu_1'
                
                # Find this choice
                parent_choice = next((choice for choice in container_nodes 
                                    if choice.node_type == 'choice_button' and choice.node_id == potential_parent), None)
                
                if parent_choice:
                    connection_id = f"{potential_parent}_to_{container_id}"
                    connection = VisualizationConnection(
                        connection_id=connection_id,
                        source_node_id=potential_parent,
                        target_node_id=container_id,
                        connection_type='choice_to_menu',
                        line_style='solid',
                        color_hint='orange',
                        weight_hint=1.5,
                        label=None,
                        metadata={
                            'connection_nature': 'choice_to_nested_menu',
                            'is_hierarchical': True,
                            'fix_type': 'alternative_pattern'
                        }
                    )
                    choice_connections.append(connection)
                    print(f"[ADDITIONAL FIX] Connected {potential_parent} -> {container_id}")
                else:
                    print(f"[ADDITIONAL FIX] No parent found for orphan: {container_id}")
        
        print(f"[NEW FIX] Choice-to-nested-menu connections complete.")
        
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
                    # REMOVED: Duplicate connection logic - now handled by _create_hierarchy_connections()
                    # This was creating redundant choice_to_nested_menu connections
                    # when _create_hierarchy_connections() already creates choice_to_menu connections
                    # 
                    # Following industry best practice: "avoid more than one level of hierarchy"
                    # and "use consistent interaction patterns" - we now use only choice_to_menu
                    pass
    
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
        Create connections from labels to their top-level menu containers.
        
        Args:
            flow_graph: Dictionary mapping label names to LabelNode objects
            
        Returns:
            List of VisualizationConnection objects for label-to-menu flows
        """
        print(f"[DEBUG LABEL_TO_MENU] Starting _create_label_to_menu_connections")
        
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
    
    def _create_menu_containers_from_hierarchy(self) -> Tuple[List[VisualizationNode], List[VisualizationConnection]]:
        """
        Create menu containers and connections using the authoritative hierarchy.
        
        This method replaces the old string-based _create_menu_containers() logic
        with direct traversal of the semantic hierarchy.
        
        Returns:
            Tuple of (visualization_nodes, visualization_connections)
        """
        print("[PHASE 2] Building visualization from authoritative hierarchy...")
        
        if not hasattr(self, '_authoritative_hierarchy'):
            print("[ERROR] No authoritative hierarchy available!")
            return [], []
        
        visualization_nodes = []
        visualization_connections = []
        
        # Get all nodes from the hierarchy (excluding regular label nodes which are handled separately)
        for node in self._authoritative_hierarchy.node_index.values():
            if node.node_type == 'label':
                # CRITICAL FIX: Include nested labels but skip regular labels
                is_nested = node.content.get('is_nested', False)
                if not is_nested:
                    continue  # Regular labels are handled by _convert_labels_to_nodes
                # Nested labels will be processed below
                
            # Create visualization nodes for menu containers, choice buttons, AND nested labels
            viz_node = self._convert_hierarchy_node_to_visualization(node)
            if viz_node:  # Check for None (regular labels return None)
                visualization_nodes.append(viz_node)
        
        # Create connections based on hierarchy relationships
        # CRITICAL: Follow FLOW_VISUALIZER_ARCHITECTURE.md rules:
        # - Menu containers do NOT have outgoing edges (choices handle the flow)
        # - Container-to-choice connections exist for LAYOUT but are marked for VISUAL CONTAINMENT
        # - Choices DO have outgoing edges to their destination labels
        for node in self._authoritative_hierarchy.node_index.values():
            for child in node.children:
                # Create container-to-choice connections for layout algorithm, but mark for visual containment
                if node.node_type == 'menu_container' and child.node_type == 'choice':
                    connection = self._create_hierarchy_connection_from_nodes(node, child)
                    # Mark this connection for visual containment (not rendered as edge)
                    connection.metadata['visual_containment'] = True
                    connection.metadata['render_as_edge'] = False
                    connection.line_style = 'none'  # No visible line
                    visualization_connections.append(connection)
                    print(f"[ARCHITECTURE] Created container->choice connection for layout: {node.semantic_id} -> {child.semantic_id} (visual containment)")
                    continue
                    
                # Skip label-to-label connections (handled by flow graph)
                if node.node_type == 'label' and child.node_type == 'label':
                    continue
                    
                # Create other valid connections
                connection = self._create_hierarchy_connection_from_nodes(node, child)
                visualization_connections.append(connection)
        
        print(f"[PHASE 2] Generated {len(visualization_nodes)} nodes and {len(visualization_connections)} connections from hierarchy")
        return visualization_nodes, visualization_connections
    
    def _convert_hierarchy_node_to_visualization(self, hierarchy_node) -> VisualizationNode:
        """
        Convert a hierarchy node to a visualization node.
        
        This method creates visualization nodes with proper metadata without
        relying on string-based ID patterns.
        
        CRITICAL: Only menu containers are converted to visualization nodes.
        Choices are embedded within container metadata for visual containment.
        """
        # Handle both menu containers and choice buttons
        if hierarchy_node.node_type == 'menu_container':
            # Determine color and size based on nesting
            if hierarchy_node.content.get('is_nested', False):
                color_hint = 'lightyellow'
                size_hint = (180, 130)
            else:
                color_hint = 'yellow'
                size_hint = (200, 150)
            
            viz_node = VisualizationNode(
                node_id=hierarchy_node.content_hash,
                node_type='menu_container',
                display_name=hierarchy_node.display_name,
                color_hint=color_hint,
                size_hint=size_hint,
                metadata={
                    'semantic_id': hierarchy_node.semantic_id,
                    'parent_id': hierarchy_node.parent.content_hash if hierarchy_node.parent else None,
                    'children_count': len(hierarchy_node.children),
                    'content': hierarchy_node.content,
                    'source_file': hierarchy_node.source_file,
                    'source_line': hierarchy_node.source_line,
                    'menu_index': hierarchy_node.content.get('menu_index', -1),
                    'is_nested': hierarchy_node.content.get('is_nested', False),
                    'nesting_level': hierarchy_node.content.get('nesting_level', 0),
                    'prompt': hierarchy_node.content.get('prompt', ''),
                    'generated_by': 'authoritative_hierarchy',
                    'hierarchy_valid': True
                }
            )
            
        elif hierarchy_node.node_type == 'choice':
            # Map hierarchy node types to visualization node types for compatibility
            viz_node = VisualizationNode(
                node_id=hierarchy_node.content_hash,
                node_type='choice_button',  # Standard type for choice visualization
                display_name=hierarchy_node.display_name,
                color_hint='lightgreen',
                size_hint=(150, 30),
                metadata={
                    'semantic_id': hierarchy_node.semantic_id,
                    'parent_container': hierarchy_node.parent.content_hash if hierarchy_node.parent else None,
                    'content': hierarchy_node.content,
                    'source_file': hierarchy_node.source_file,
                    'source_line': hierarchy_node.source_line,
                    
                    # Choice-specific metadata  
                    'choice_index': hierarchy_node.content.get('choice_index', -1),
                    'full_text': hierarchy_node.content.get('full_text', ''),
                    'destination': hierarchy_node.content.get('destination', ''),
                    'has_condition': hierarchy_node.content.get('has_condition', False),
                    'condition': hierarchy_node.content.get('condition', ''),
                    
                    # Mark as hierarchy-generated
                    'generated_by': 'authoritative_hierarchy',
                    'hierarchy_valid': True
                }
            )
        
        elif hierarchy_node.node_type == 'label':
            # CRITICAL FIX: Support nested label nodes from AHS
            # Check if this is a nested label (created by AHS nested label processing)
            is_nested = hierarchy_node.content.get('is_nested', False)
            
            if is_nested:
                # This is a nested label - create a special visualization node
                viz_node = VisualizationNode(
                    node_id=hierarchy_node.content_hash,
                    node_type='nested_label',  # Special type for nested labels
                    display_name=hierarchy_node.display_name,  # Already has ↳ prefix from AHS
                    color_hint='lightcyan',  # Distinct color for nested labels
                    size_hint=(120, 40),
                    metadata={
                        'semantic_id': hierarchy_node.semantic_id,
                        'parent_choice': hierarchy_node.content.get('parent_choice_id'),
                        'content': hierarchy_node.content,
                        'source_file': hierarchy_node.source_file,
                        'source_line': hierarchy_node.source_line,
                        
                        # Nested label specific metadata
                        'label_name': hierarchy_node.content.get('label_name', ''),
                        'label_type': hierarchy_node.content.get('label_type', 'nested_within_choice'),
                        'is_nested': True,
                        
                        # Mark as hierarchy-generated
                        'generated_by': 'authoritative_hierarchy',
                        'hierarchy_valid': True
                    }
                )
            else:
                # This is a regular label node from AHS - skip it (handled by _convert_labels_to_nodes)
                return None
        
        else:
            raise ValueError(f"Unsupported node type for visualization: {hierarchy_node.node_type}")
        
        return viz_node
    
    def _create_hierarchy_connection_from_nodes(self, parent_node, child_node) -> VisualizationConnection:
        """
        Create a visualization connection between hierarchy nodes.
        
        This method creates connections based on semantic relationships
        instead of string pattern matching.
        """
        # Determine connection type based on node types
        connection_type_map = {
            ('label', 'menu_container'): 'label_to_menu',
            ('menu_container', 'choice'): 'container_to_choice', 
            ('choice', 'menu_container'): 'choice_to_nested_menu',
            ('choice', 'label'): 'choice_to_label'
        }
        
        # Special handling for nested labels
        if parent_node.node_type == 'choice' and child_node.node_type == 'label':
            if child_node.content.get('is_nested', False):
                connection_type_map[('choice', 'label')] = 'choice_to_nested_label'
        
        connection_type = connection_type_map.get(
            (parent_node.node_type, child_node.node_type),
            'hierarchy'
        )
        
        # Determine connection styling
        if connection_type == 'container_to_choice':
            color_hint = 'darkblue'
            line_style = 'solid'
        elif connection_type == 'choice_to_nested_menu':
            color_hint = 'purple'
            line_style = 'dashed'
        elif connection_type == 'choice_to_nested_label':
            color_hint = 'purple'  # Purple for nested labels (matching documentation)
            line_style = 'solid'
        elif connection_type == 'label_to_menu':
            color_hint = 'orange'
            line_style = 'solid'
        else:
            color_hint = 'gray'
            line_style = 'solid'
        
        connection = VisualizationConnection(
            connection_id=f"{parent_node.content_hash}_to_{child_node.content_hash}",
            source_node_id=parent_node.content_hash,
            target_node_id=child_node.content_hash,
            connection_type=connection_type,
            line_style=line_style,
            color_hint=color_hint,
            weight_hint=1.0,
            label=None,
            metadata={
                'parent_semantic_id': parent_node.semantic_id,
                'child_semantic_id': child_node.semantic_id,
                'connection_nature': 'semantic_hierarchy',
                'is_structural': True,
                'generated_by': 'authoritative_hierarchy'
            }
        )
        
        return connection
    
    def _create_label_to_menu_connections_from_hierarchy(self) -> List[VisualizationConnection]:
        """
        Create connections from labels to their menu containers using the authoritative hierarchy.
        
        This method replaces string-based label-to-menu connection logic.
        """
        connections = []
        
        # Find all label nodes that have menu container children
        for label_node in self._authoritative_hierarchy.root_nodes:
            if label_node.node_type != 'label':
                continue
                
            # Find menu container children
            menu_containers = [child for child in label_node.children if child.node_type == 'menu_container']
            
            for menu_container in menu_containers:
                # Use the correct label node ID format (simple label name, not content hash)
                label_name = label_node.semantic_id.replace('label_', '')
                connection = VisualizationConnection(
                    connection_id=f"label_{label_name}_to_menu_{menu_container.content_hash}",
                    source_node_id=label_name,  # Use simple label name to match visualization nodes
                    target_node_id=menu_container.content_hash,
                    connection_type='label_to_menu',
                    line_style='solid',
                    color_hint='orange',
                    weight_hint=1.0,
                    label=None,
                    metadata={
                        'connection_nature': 'label_to_menu_semantic',
                        'label_name': label_node.semantic_id.replace('label_', ''),
                        'menu_semantic_id': menu_container.semantic_id,
                        'generated_by': 'authoritative_hierarchy'
                    }
                )
                connections.append(connection)
        
        print(f"[PHASE 2] Created {len(connections)} label-to-menu connections from hierarchy")
        return connections
    
    def _create_choice_destination_connections_from_hierarchy(self) -> List[VisualizationConnection]:
        """
        Create connections from choice buttons to their destination labels using the authoritative hierarchy.
        
        CRITICAL: Choice buttons handle the outgoing flow, NOT menu containers.
        This creates connections directly from choice nodes to their destinations.
        """
        connections = []
        
        # Find all choice nodes and their destinations
        for choice_node in self._authoritative_hierarchy.node_index.values():
            if choice_node.node_type != 'choice':
                continue
                
            # Get destination from choice content
            destination = choice_node.content.get('destination', '')
            if not destination:
                print(f"[CHOICE DESTINATION] Warning: Choice {choice_node.semantic_id} has no destination")
                continue
                
            # Create connection from choice button to destination label
            connection = VisualizationConnection(
                connection_id=f"choice_{choice_node.content_hash}_to_label_{destination}",
                source_node_id=choice_node.content_hash,  # Source is the choice button
                target_node_id=destination,  # Target is the destination label
                connection_type='choice_to_label',
                line_style='solid',
                color_hint='green',  # Green for choice connections
                weight_hint=1.0,
                label=None,  # No label needed on edge
                metadata={
                    'connection_nature': 'choice_destination',
                    'choice_semantic_id': choice_node.semantic_id,
                    'choice_text': choice_node.content.get('full_text', choice_node.display_name),
                    'destination_label': destination,
                    'generated_by': 'authoritative_hierarchy'
                }
            )
            connections.append(connection)
            print(f"[CHOICE DESTINATION] Connected choice {choice_node.semantic_id} -> {destination}")
        
        print(f"[PHASE 2] Created {len(connections)} choice-to-destination connections from hierarchy")
        return connections
    
    def _compare_hierarchy_systems(self, old_nodes: List[VisualizationNode], old_connections: List[VisualizationConnection]) -> None:
        """
        Compare the old string-based system with the new authoritative hierarchy.
        
        This method helps debug and validate the new hierarchy system by showing
        differences between the two approaches.
        """
        if not hasattr(self, '_authoritative_hierarchy'):
            print("[COMPARE] No authoritative hierarchy available for comparison")
            return
            
        print(f"\n[COMPARE] Comparing old vs new hierarchy systems")
        print("=" * 60)
        
        # Get data from new hierarchy system
        new_nodes, new_connections = self._authoritative_hierarchy.get_visualization_data()
        
        # Compare node counts
        old_count = len(old_nodes)
        new_count = len(new_nodes)
        print(f"📊 Node counts: Old={old_count}, New={new_count}, Diff={new_count - old_count}")
        
        # Compare connection counts
        old_conn_count = len(old_connections)
        new_conn_count = len(new_connections)
        print(f"📊 Connection counts: Old={old_conn_count}, New={new_conn_count}, Diff={new_conn_count - old_conn_count}")
        
        # Find ep2cont5 specific differences (our test case)
        old_ep2cont5 = [node for node in old_nodes if 'ep2cont5' in node.node_id]
        new_ep2cont5 = [node for node in new_nodes if 'ep2cont5' in (node.display_name or '') or 
                        'ep2cont5' in (node.metadata.get('semantic_id', '') if node.metadata else '')]
        
        if old_ep2cont5 or new_ep2cont5:
            print(f"\n🔍 ep2cont5 comparison:")
            print(f"   Old system: {len(old_ep2cont5)} nodes")
            for node in old_ep2cont5:
                print(f"     - {node.node_id} ({node.node_type})")
                
            print(f"   New system: {len(new_ep2cont5)} nodes")
            for node in new_ep2cont5:
                semantic_id = node.metadata.get('semantic_id', 'unknown')
                print(f"     - {semantic_id} ({node.node_type})")
        
        # Look for potential rogue nodes in old system
        rogue_patterns = ['_nested_menu_1', '_nested_menu_1_choice_1']
        rogue_nodes = []
        for node in old_nodes:
            for pattern in rogue_patterns:
                if pattern in node.node_id and 'ep2cont5' in node.node_id:
                    rogue_nodes.append(node)
        
        if rogue_nodes:
            print(f"\n🚨 Potential rogue nodes in old system:")
            for node in rogue_nodes:
                print(f"     - {node.node_id} ({node.node_type})")
        else:
            print(f"\n✅ No rogue nodes detected in old system")
        
        # Print hierarchy structure from new system
        print(f"\n🏗️ New hierarchy structure for ep2cont5:")
        for root in self._authoritative_hierarchy.root_nodes:
            if 'ep2cont5' in root.semantic_id:
                self._authoritative_hierarchy.print_hierarchy(root) 