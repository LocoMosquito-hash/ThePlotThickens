#!/usr/bin/env python3
"""
Authoritative Hierarchy - Single Source of Truth for Node Relationships

This module implements the authoritative hierarchical structure that replaces
string-based pattern matching with semantic object relationships.

Key Features:
- Direct parent/child object references (no string parsing)
- Content-based stable node IDs (no fragile index dependencies)  
- Built from existing MenuStructure semantic data
- O(1) relationship lookups
- Self-validating structure

Architecture Position:
Parser → AuthoritativeHierarchy → Visualization
         ↑ SINGLE SOURCE OF TRUTH
"""

import hashlib
import json
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from pathlib import Path

# Import visualization interfaces
try:
    from flow_visualizer_interface import VisualizationNode, VisualizationConnection
except ImportError:
    # Fallback if not available
    from typing import NamedTuple
    class VisualizationNode(NamedTuple):
        node_id: str
        node_type: str
        display_name: str
        color_hint: str = 'lightblue'
        size_hint: Tuple[int, int] = (100, 50)
        metadata: Dict[str, Any] = {}
    
    class VisualizationConnection(NamedTuple):
        connection_id: str
        source_node_id: str
        target_node_id: str
        connection_type: str = 'flow'
        color_hint: str = 'gray'
        weight_hint: float = 1.0
        metadata: Dict[str, Any] = {}


@dataclass
class FlowRelationship:
    """
    Represents a narrative flow connection between nodes.
    
    This is separate from hierarchical parent-child relationships and represents
    the actual narrative flow (jumps, calls, returns) between labels.
    """
    target_node: 'HierarchyNode'
    flow_type: str                              # 'jump', 'call', 'menu_choice', etc.
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HierarchyNode:
    """
    A node in the authoritative hierarchy with semantic relationships.
    
    This replaces fragile string-based ID parsing with direct object references.
    Each node knows its parent, children, and semantic context without any
    string manipulation required.
    """
    # Core identity
    content_hash: str                           # Unique content-based ID
    semantic_id: str                           # Human-readable identifier  
    node_type: str                             # 'label', 'menu_container', 'choice', etc.
    
    # Content data
    display_name: str
    content: Dict[str, Any] = field(default_factory=dict)
    
    # Semantic relationships (the key improvement!)
    parent: Optional['HierarchyNode'] = None
    children: List['HierarchyNode'] = field(default_factory=list)
    
    # NEW: Flow relationships (narrative connections)
    outgoing_flows: List[FlowRelationship] = field(default_factory=list)
    incoming_flows: List[FlowRelationship] = field(default_factory=list)
    
    # Additional metadata
    source_file: Optional[str] = None
    source_line: Optional[int] = None
    jump_targets: List[str] = field(default_factory=list)
    
    def add_child(self, child: 'HierarchyNode') -> None:
        """Add a child node and set up bidirectional relationship."""
        if child not in self.children:
            self.children.append(child)
            child.parent = self
    
    def remove_child(self, child: 'HierarchyNode') -> None:
        """Remove a child node and clean up relationship."""
        if child in self.children:
            self.children.remove(child)
            child.parent = None
    
    def add_flow_to(self, target_node: 'HierarchyNode', flow_type: str, metadata: Dict[str, Any] = None) -> None:
        """Add an outgoing flow relationship to another node."""
        if metadata is None:
            metadata = {}
            
        flow = FlowRelationship(
            target_node=target_node,
            flow_type=flow_type,
            metadata=metadata
        )
        
        # Add to outgoing flows (avoid duplicates)
        if not any(f.target_node == target_node and f.flow_type == flow_type for f in self.outgoing_flows):
            self.outgoing_flows.append(flow)
            target_node.incoming_flows.append(flow)
    
    def remove_flow_to(self, target_node: 'HierarchyNode', flow_type: str = None) -> None:
        """Remove flow relationships to a target node."""
        self.outgoing_flows = [
            f for f in self.outgoing_flows 
            if not (f.target_node == target_node and (flow_type is None or f.flow_type == flow_type))
        ]
        
        target_node.incoming_flows = [
            f for f in target_node.incoming_flows 
            if not (f.target_node == self and (flow_type is None or f.flow_type == flow_type))
        ]
    
    def get_ancestors(self) -> List['HierarchyNode']:
        """Get all ancestor nodes (parent, grandparent, etc.)."""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors
    
    def get_descendants(self) -> List['HierarchyNode']:
        """Get all descendant nodes (children, grandchildren, etc.)."""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
    
    def find_child_by_type(self, node_type: str) -> Optional['HierarchyNode']:
        """Find first child of specific type."""
        for child in self.children:
            if child.node_type == node_type:
                return child
        return None
    
    def find_children_by_type(self, node_type: str) -> List['HierarchyNode']:
        """Find all children of specific type."""
        return [child for child in self.children if child.node_type == node_type]


class AuthoritativeHierarchy:
    """
    The single source of truth for all node relationships in the narrative flow.
    
    This class builds an authoritative hierarchy directly from semantic MenuStructure
    data, eliminating the need for string-based pattern matching and orphan detection.
    
    Key Responsibilities:
    - Build hierarchy from MenuStructure.parent_choice relationships
    - Generate stable content-based node IDs
    - Provide O(1) parent/child lookups
    - Convert to visualization format without string parsing
    """
    
    def __init__(self, include_helper_labels: bool = False):
        self.root_nodes: List[HierarchyNode] = []
        self.node_index: Dict[str, HierarchyNode] = {}  # content_hash -> node
        self.semantic_index: Dict[str, HierarchyNode] = {}  # semantic_id -> node
        self.node_count = 0
        self.include_helper_labels = include_helper_labels
        
    def build_from_flow_graph(self, flow_graph: Dict[str, Any]) -> None:
        """
        Build the authoritative hierarchy from flow graph data.
        
        This method extracts semantic relationships from MenuStructure objects
        and builds the hierarchy using direct object references instead of
        string pattern matching.
        
        Args:
            flow_graph: Flow graph from parser containing MenuStructure data
        """
        print("[HIERARCHY] Building authoritative hierarchy from semantic data...")
        
        # Phase 1: Create all label nodes (flow_graph keys are label names directly)
        label_nodes = self._create_label_nodes(flow_graph)
        
        # Phase 2: Process menu structures with semantic relationships
        self._process_menu_structures(flow_graph, label_nodes)
        
        # Phase 3: Create flow connections between labels
        self._create_flow_connections(flow_graph)
        
        print(f"[HIERARCHY] Built hierarchy with {len(self.node_index)} nodes")
        self._validate_hierarchy()
    
    def _create_label_nodes(self, flow_graph: Dict[str, Any]) -> Dict[str, HierarchyNode]:
        """Create nodes for all labels in the flow graph."""
        label_nodes = {}
        
        # flow_graph keys are label names directly, not nested under 'labels'
        for label_name, label_data in flow_graph.items():
            if self._should_skip_label_entry(label_name, label_data):
                continue
            # Generate content-based ID for the label
            content_hash = self._generate_content_hash({
                'type': 'label',
                'name': label_name,
                'file': getattr(label_data, 'file_path', 'unknown'),
                'line': getattr(label_data, 'line_number', 0)
            })
            
            # Create hierarchy node
            label_node = HierarchyNode(
                content_hash=content_hash,
                semantic_id=f"label_{label_name}",
                node_type='label',
                display_name=label_name,
                content={
                    'label_name': label_name,
                    'file_path': getattr(label_data, 'file_path', None),
                    'line_number': getattr(label_data, 'line_number', None)
                },
                source_file=getattr(label_data, 'file_path', None),
                source_line=getattr(label_data, 'line_number', None)
            )
            
            # Register in indexes
            self._register_node(label_node)
            label_nodes[label_name] = label_node
            
            # Add to roots (labels are typically root nodes)
            self.root_nodes.append(label_node)
        
        print(f"[HIERARCHY] Created {len(label_nodes)} label nodes")
        return label_nodes

    def _should_skip_label_entry(self, label_name: str, label_data: Any) -> bool:
        if not hasattr(label_data, 'has_dialogue'):
            return True
        if not label_name.startswith('_'):
            return False
        if self.include_helper_labels and label_name.startswith("_call_"):
            return False
        return True
    
    def _process_menu_structures(self, flow_graph: Dict[str, Any], label_nodes: Dict[str, HierarchyNode]) -> None:
        """
        Process MenuStructure objects to build menu hierarchy.
        
        This is the core method that builds relationships from semantic data
        instead of string pattern matching.
        """
        menu_count = 0
        choice_count = 0
        labels_with_menus = 0
        total_labels_checked = 0
        
        # flow_graph keys are label names directly
        for label_name, label_data in flow_graph.items():
            if self._should_skip_label_entry(label_name, label_data):
                continue
            
            total_labels_checked += 1
                
            label_node = label_nodes[label_name]
            
            # Process menu nodes attached to this label
            menu_nodes = getattr(label_data, 'menu_nodes', [])
            
            if menu_nodes:
                labels_with_menus += 1
                if labels_with_menus <= 3:  # Debug first 3 labels with menus
                    print(f"[HIERARCHY DEBUG] Label '{label_name}' has {len(menu_nodes)} menu_nodes")
            
            for menu_idx, menu_node in enumerate(menu_nodes):
                # Create menu container from MenuStructure
                menu_container = self._create_menu_container_from_structure(
                    menu_node, label_node, menu_idx
                )
                
                if menu_container:
                    label_node.add_child(menu_container)
                    menu_count += 1
                    
                    # Process choices in this menu
                    choice_count += self._process_menu_choices(
                        menu_node, menu_container
                    )
        
        print(f"[HIERARCHY] Checked {total_labels_checked} labels, {labels_with_menus} had menu_nodes")
        print(f"[HIERARCHY] Processed {menu_count} menus with {choice_count} choices")
    
    def _create_menu_container_from_structure(self, menu_node: Any, parent_label: HierarchyNode, menu_idx: int) -> Optional[HierarchyNode]:
        """
        Create a menu container node from MenuStructure semantic data.
        
        This replaces the string-based menu container creation logic.
        """
        # Generate stable content-based ID
        content_hash = self._generate_content_hash({
            'type': 'menu_container',
            'parent_label': parent_label.semantic_id,
            'menu_index': menu_idx,
            'prompt': getattr(menu_node, 'prompt', ''),
            'choices': [getattr(choice, 'text', '') for choice in getattr(menu_node, 'choices', [])]
        })
        
        # Create semantic ID
        prompt_hint = getattr(menu_node, 'prompt', '')
        if prompt_hint:
            # Use first few words of prompt for readability
            prompt_words = prompt_hint.split()[:2]
            prompt_suffix = '_'.join(prompt_words).lower()
            semantic_id = f"{parent_label.semantic_id}_menu_{prompt_suffix}#{content_hash[:8]}"
        else:
            semantic_id = f"{parent_label.semantic_id}_menu_{menu_idx}#{content_hash[:8]}"
        
        # Create hierarchy node
        menu_container = HierarchyNode(
            content_hash=content_hash,
            semantic_id=semantic_id,
            node_type='menu_container',
            display_name=getattr(menu_node, 'prompt', f"Menu {menu_idx}"),
            content={
                'menu_index': menu_idx,
                'prompt': getattr(menu_node, 'prompt', ''),
                'total_choices': len(getattr(menu_node, 'choices', [])),
                'complexity_level': getattr(menu_node, 'complexity_level', 'simple'),
                'has_conditions': getattr(menu_node, 'has_conditions', False)
            },
            source_file=getattr(menu_node, 'file_path', None),
            source_line=getattr(menu_node, 'line_number', None)
        )
        
        self._register_node(menu_container)
        return menu_container
    
    def _process_menu_choices(self, menu_node: Any, menu_container: HierarchyNode) -> int:
        """
        Process choices within a menu using semantic relationships.
        
        This method uses the existing nested_menu_structures from MenuChoice
        objects instead of trying to reconstruct relationships from string IDs.
        """
        choices = getattr(menu_node, 'choices', [])
        choice_count = 0
        
        for choice_idx, choice in enumerate(choices):
            # Create choice node
            choice_node = self._create_choice_from_structure(
                choice, menu_container, choice_idx
            )
            
            if choice_node:
                menu_container.add_child(choice_node)
                choice_count += 1
                
                # CRITICAL: Process nested menus using semantic data
                nested_structures = getattr(choice, 'nested_menu_structures', [])
                for nested_idx, nested_menu in enumerate(nested_structures):
                    nested_container = self._create_nested_menu_container(
                        nested_menu, choice_node, nested_idx
                    )
                    
                    if nested_container:
                        choice_node.add_child(nested_container)
                        
                        # Recursively process nested choices
                        choice_count += self._process_menu_choices(
                            nested_menu, nested_container
                        )
                
                # NEW: Process nested labels using semantic data
                nested_labels = getattr(choice, 'nested_labels', [])
                for nested_label_name in nested_labels:
                    nested_label_node = self._create_nested_label_node(
                        nested_label_name, choice_node
                    )
                    
                    if nested_label_node:
                        choice_node.add_child(nested_label_node)
                        choice_count += 1
        
        return choice_count
    
    def _create_choice_from_structure(self, choice: Any, parent_menu: HierarchyNode, choice_idx: int) -> Optional[HierarchyNode]:
        """Create a choice node from MenuChoice semantic data."""
        choice_text = getattr(choice, 'text', f'Choice {choice_idx}')
        destination = getattr(choice, 'destination', '')
        
        # Generate content-based ID
        content_hash = self._generate_content_hash({
            'type': 'choice',
            'parent_menu': parent_menu.content_hash,
            'choice_index': choice_idx,
            'text': choice_text,
            'destination': destination,
            'condition': getattr(choice, 'condition', '')
        })
        
        # Create semantic ID
        text_hint = choice_text.split()[:2] if choice_text else ['choice']
        text_suffix = '_'.join(text_hint).lower()
        semantic_id = f"{parent_menu.semantic_id}_choice_{text_suffix}#{content_hash[:8]}"
        
        # Create hierarchy node
        choice_node = HierarchyNode(
            content_hash=content_hash,
            semantic_id=semantic_id,
            node_type='choice',
            display_name=choice_text[:30] + "..." if len(choice_text) > 30 else choice_text,
            content={
                'choice_index': choice_idx,
                'full_text': choice_text,
                'destination': getattr(choice, 'destination', ''),
                'all_destinations': getattr(choice, 'all_destinations', []),  # NEW: Support multiple conditional destinations
                'condition': getattr(choice, 'condition', ''),
                'action_type': getattr(choice, 'action_type', 'jump'),
                'has_condition': bool(getattr(choice, 'condition', '')),
                'has_nested_menus': len(getattr(choice, 'nested_menu_structures', [])) > 0
            },
            jump_targets=[getattr(choice, 'destination', '')] if getattr(choice, 'destination', '') else []
        )
        
        self._register_node(choice_node)
        return choice_node
    
    def _create_nested_menu_container(self, nested_menu: Any, parent_choice: HierarchyNode, nested_idx: int) -> Optional[HierarchyNode]:
        """
        Create nested menu container using semantic parent relationship.
        
        This method uses the MenuStructure.parent_choice relationship directly
        instead of trying to infer it from string patterns.
        """
        # Generate content-based ID
        content_hash = self._generate_content_hash({
            'type': 'nested_menu_container',
            'parent_choice': parent_choice.content_hash,
            'nested_index': nested_idx,
            'prompt': getattr(nested_menu, 'prompt', ''),
            'nesting_level': getattr(nested_menu, 'nesting_level', 1),
            'choices': [getattr(choice, 'text', '') for choice in getattr(nested_menu, 'choices', [])]
        })
        
        # Create semantic ID that clearly shows hierarchy
        prompt_hint = getattr(nested_menu, 'prompt', '')
        if prompt_hint:
            prompt_words = prompt_hint.split()[:2]
            prompt_suffix = '_'.join(prompt_words).lower()
            semantic_id = f"{parent_choice.semantic_id}_nested_{prompt_suffix}#{content_hash[:8]}"
        else:
            semantic_id = f"{parent_choice.semantic_id}_nested_{nested_idx}#{content_hash[:8]}"
        
        # Create hierarchy node
        nested_container = HierarchyNode(
            content_hash=content_hash,
            semantic_id=semantic_id,
            node_type='menu_container',
            display_name=f"↳ {getattr(nested_menu, 'prompt', f'Nested Menu {nested_idx}')}",
            content={
                'menu_index': nested_idx,
                'prompt': getattr(nested_menu, 'prompt', ''),
                'total_choices': len(getattr(nested_menu, 'choices', [])),
                'is_nested': True,
                'nesting_level': getattr(nested_menu, 'nesting_level', 1),
                'parent_choice_id': parent_choice.content_hash
            }
        )
        
        self._register_node(nested_container)
        return nested_container
    
    def _create_nested_label_node(self, label_name: str, parent_choice: HierarchyNode) -> Optional[HierarchyNode]:
        """
        Create a nested label node using semantic parent relationship.
        
        Nested labels are labels defined within menu choice blocks, making them
        conceptually owned by that specific choice rather than the parent label.
        
        Args:
            label_name: Name of the nested label
            parent_choice: Parent choice node that contains this label
        """
        # Generate content-based ID
        content_hash = self._generate_content_hash({
            'type': 'nested_label',
            'parent_choice': parent_choice.content_hash,
            'label_name': label_name,
            'is_nested': True
        })
        
        # Create semantic ID that clearly shows hierarchy
        semantic_id = f"{parent_choice.semantic_id}_nested_label_{label_name}#{content_hash[:8]}"
        
        # Create hierarchy node
        nested_label_node = HierarchyNode(
            content_hash=content_hash,
            semantic_id=semantic_id,
            node_type='label',
            display_name=f"↳ {label_name}",  # Arrow indicates it's nested
            content={
                'label_name': label_name,
                'is_nested': True,
                'label_type': 'nested_within_choice',
                'parent_choice_id': parent_choice.content_hash
            },
            source_file=None,  # Could be enhanced to track source file
            source_line=None   # Could be enhanced to track source line
        )
        
        print(f"[HIERARCHY] Created nested label node: {semantic_id}")
        self._register_node(nested_label_node)
        return nested_label_node
    
    def get_nested_label_names(self) -> Set[str]:
        """
        Get all label names that are handled as nested labels by the AHS.
        
        This is used to prevent duplicate node creation by the regular label processing.
        
        Returns:
            Set of label names that are nested labels
        """
        nested_label_names = set()
        
        for node in self.node_index.values():
            if (node.node_type == 'label' and 
                node.content.get('is_nested', False)):
                label_name = node.content.get('label_name')
                if label_name:
                    nested_label_names.add(label_name)
                    
        print(f"[HIERARCHY] Found {len(nested_label_names)} nested labels: {nested_label_names}")
        return nested_label_names
    
    def _create_flow_connections(self, flow_graph: Dict[str, Any]) -> None:
        """Create flow connections between labels based on jumps/calls."""
        print("[HIERARCHY] Creating flow connections between labels...")
        
        # CRITICAL: Build set of destinations handled by menu choices to avoid duplicates
        menu_choice_destinations = self._get_menu_choice_destinations_from_hierarchy(flow_graph)
        
        for label_name, label_node in flow_graph.items():
            if self._should_skip_label_entry(label_name, label_node):
                continue
                
            source_node = self.get_node_by_label_name(label_name)
            if not source_node:
                continue  # Skip if label node doesn't exist in hierarchy
                
            # Process outgoing flows from this label
            outgoing_flows = getattr(label_node, 'outgoing_flows', [])
            for flow in outgoing_flows:
                target_label = getattr(flow, 'target_label', None)
                flow_type = getattr(flow, 'flow_type', 'jump')
                
                if target_label and target_label != '<return>':
                    # INTELLIGENT FILTERING: Only skip flows that would truly duplicate menu choice functionality
                    should_filter_flow = self._should_filter_flow(label_name, target_label, flow_type, menu_choice_destinations, flow_graph)
                    if should_filter_flow:
                        print(f"[FLOW FILTER] Skipping label-to-label flow {label_name} -> {target_label} (truly handled by menu choice from same source)")
                        continue
                        
                    target_node = self.get_node_by_label_name(target_label)
                    if target_node:
                        # Create flow relationship
                        flow_metadata = {
                            'source_label': label_name,
                            'target_label': target_label,
                            'original_flow_type': flow_type,
                            'source_file': getattr(flow, 'source_file', None),
                            'source_line': getattr(flow, 'source_line', None)
                        }
                        
                        source_node.add_flow_to(target_node, flow_type, flow_metadata)
                        print(f"[FLOW] Created {flow_type} connection: {label_name} -> {target_label}")
        
        print(f"[HIERARCHY] Flow connections created successfully")
    
    def _should_filter_flow(self, source_label: str, target_label: str, flow_type: str, 
                           menu_choice_destinations: Set[str], flow_graph: Dict[str, Any]) -> bool:
        """
        Intelligent flow filtering - only filter flows that would truly duplicate menu choice functionality.
        
        A flow should be filtered ONLY if:
        1. The target is a menu choice destination, AND
        2. The source label has a menu with a choice to the same target, AND
        3. The flow is not an implicit flow (implicit flows should never be filtered)
        
        Args:
            source_label: Label where the flow originates
            target_label: Label where the flow goes
            flow_type: Type of flow ('jump', 'call', 'implicit', etc.)
            menu_choice_destinations: Set of all destinations handled by menu choices
            flow_graph: Full flow graph for context
            
        Returns:
            True if the flow should be filtered, False otherwise
        """
        # Rule 1: If target is not a menu choice destination, never filter
        if target_label not in menu_choice_destinations:
            return False
            
        # Rule 2: NEVER filter implicit flows - they represent legitimate fall-through behavior
        if flow_type == 'implicit':
            print(f"[FLOW FILTER] Preserving implicit flow: {source_label} -> {target_label}")
            return False
            
        # Rule 3: Only filter if the SAME source label has a menu choice to the SAME target
        source_label_node = flow_graph.get(source_label)
        if not source_label_node:
            return False
            
        # Check if the source label has menus
        menu_nodes = getattr(source_label_node, 'menu_nodes', [])
        if not menu_nodes:
            # No menus in source label, so this flow is not duplicating menu functionality
            return False
            
        # Check if any menu in the source label has a choice to the target
        for menu_node in menu_nodes:
            choices = getattr(menu_node, 'choices', [])
            for choice in choices:
                choice_destination = getattr(choice, 'destination', '')
                if choice_destination == target_label:
                    # Found a menu choice from the same source to the same target - this is a true duplicate
                    print(f"[FLOW FILTER] Found duplicate: {source_label} has menu choice -> {target_label}")
                    return True
                    
        # No menu choice from this source to this target found - preserve the flow
        print(f"[FLOW FILTER] Preserving flow: {source_label} -> {target_label} (no duplicate menu choice from same source)")
        return False
    
    def _get_menu_choice_destinations_from_hierarchy(self, flow_graph: Dict[str, Any]) -> Set[str]:
        """
        Get all destinations that are handled by menu choices in the hierarchy.
        These should not have competing label-to-label flows.
        """
        menu_destinations = set()
        
        # Scan through all choice nodes in the hierarchy
        for node in self.node_index.values():
            if node.node_type == 'choice':
                destination = node.content.get('destination', '')
                if destination:
                    menu_destinations.add(destination)
                    
                # Also add nested labels within choices
                nested_labels = node.content.get('nested_labels', [])
                for nested_label in nested_labels:
                    menu_destinations.add(nested_label)
        
        print(f"[FLOW FILTER] Found {len(menu_destinations)} menu choice destinations: {menu_destinations}")
        return menu_destinations
    
    def _generate_content_hash(self, content: Dict[str, Any]) -> str:
        """
        Generate a stable content-based hash for a node.
        
        This replaces fragile string-based IDs with content-addressable identifiers.
        """
        # Sort keys for deterministic hashing
        content_str = json.dumps(content, sort_keys=True, ensure_ascii=True)
        hash_obj = hashlib.sha256(content_str.encode('utf-8'))
        return hash_obj.hexdigest()[:16]  # Use first 16 chars for brevity
    
    def _register_node(self, node: HierarchyNode) -> None:
        """Register a node in the lookup indexes."""
        self.node_index[node.content_hash] = node
        self.semantic_index[node.semantic_id] = node
        self.node_count += 1
    
    def _validate_hierarchy(self) -> None:
        """Validate the hierarchy structure for consistency."""
        print("[HIERARCHY] Validating hierarchy structure...")
        
        orphan_count = 0
        for node in self.node_index.values():
            if node.parent is None and node not in self.root_nodes:
                print(f"[HIERARCHY WARNING] Orphan node detected: {node.semantic_id}")
                orphan_count += 1
        
        if orphan_count == 0:
            print("[HIERARCHY] ✅ Hierarchy validation passed - no orphan nodes")
        else:
            print(f"[HIERARCHY] ⚠️ Found {orphan_count} orphan nodes")
    
    def get_node(self, node_id: str) -> Optional[HierarchyNode]:
        """Get node by content hash or semantic ID. O(1) lookup."""
        return self.node_index.get(node_id) or self.semantic_index.get(node_id)
    
    def get_node_by_label_name(self, label_name: str) -> Optional[HierarchyNode]:
        """Get a label node by its label name. O(1) lookup."""
        # Label nodes have semantic IDs like "label_{label_name}#hash"
        label_semantic_id = f"label_{label_name}"
        
        # Check if exact match exists in semantic index
        for semantic_id, node in self.semantic_index.items():
            if (node.node_type == 'label' and 
                semantic_id.startswith(label_semantic_id) and 
                node.content.get('label_name') == label_name):
                return node
        
        return None
    
    def search_nodes(self, query: str) -> List[HierarchyNode]:
        """
        Search for nodes matching a query string.
        
        Searches through:
        - Label names (for label nodes)
        - Display names
        - Semantic IDs
        - Content hash (partial match)
        
        Args:
            query: Search query string (case insensitive)
            
        Returns:
            List of matching nodes, with exact matches first
        """
        query = query.lower().strip()
        if not query:
            return []
        
        exact_matches = []
        partial_matches = []
        
        for node in self.node_index.values():
            # For label nodes, check the actual label name
            if node.node_type == 'label':
                label_name = node.content.get('label_name', '').lower()
                if query == label_name:
                    exact_matches.append(node)
                    continue
                elif query in label_name:
                    partial_matches.append(node)
                    continue
            
            # Check display name (with null check)
            if node.display_name:
                display_name = node.display_name.lower()
                if query == display_name:
                    exact_matches.append(node)
                    continue
                elif query in display_name:
                    partial_matches.append(node)
                    continue
            
            # Check semantic ID (without hash part for cleaner matching)
            if node.semantic_id:
                semantic_id = node.semantic_id.lower()
                if '#' in semantic_id:
                    clean_semantic_id = semantic_id.split('#')[0]
                else:
                    clean_semantic_id = semantic_id
                    
                if query == clean_semantic_id:
                    exact_matches.append(node)
                    continue
                elif query in clean_semantic_id:
                    partial_matches.append(node)
                    continue
            
            # Check content hash (partial match)
            if node.content_hash and query in node.content_hash.lower():
                partial_matches.append(node)
        
        # Return exact matches first, then partial matches
        return exact_matches + partial_matches
    
    def find_parent(self, node_id: str) -> Optional[HierarchyNode]:
        """Find parent of a node. O(1) lookup using object reference."""
        node = self.get_node(node_id)
        return node.parent if node else None
    
    def find_children(self, node_id: str) -> List[HierarchyNode]:
        """Find children of a node. O(1) lookup using object reference."""
        node = self.get_node(node_id)
        return node.children if node else []
    
    def get_visualization_data(self) -> Tuple[List[VisualizationNode], List[VisualizationConnection]]:
        """
        Convert authoritative hierarchy to visualization format.
        
        This method replaces the string-based _create_menu_containers() logic
        with direct traversal of the object hierarchy.
        """
        print("[HIERARCHY] Converting to visualization format...")
        
        visualization_nodes = []
        visualization_connections = []
        
        # Convert all hierarchy nodes to visualization nodes
        for node in self.node_index.values():
            viz_node = self._convert_to_visualization_node(node)
            visualization_nodes.append(viz_node)
        
        # Create connections based on parent-child relationships
        for node in self.node_index.values():
            for child in node.children:
                connection = self._create_hierarchy_connection(node, child)
                visualization_connections.append(connection)
        
        # Add flow connections for jumps between labels
        flow_connections = self._create_flow_connections_for_visualization()
        visualization_connections.extend(flow_connections)
        
        print(f"[HIERARCHY] Generated {len(visualization_nodes)} nodes and {len(visualization_connections)} connections")
        return visualization_nodes, visualization_connections
    
    def _convert_to_visualization_node(self, node: HierarchyNode) -> VisualizationNode:
        """Convert a hierarchy node to a visualization node."""
        # Determine color based on node type
        color_map = {
            'label': '#87CEEB',           # Sky blue
            'menu_container': '#FFA500',  # Orange  
            'choice': '#98FB98'           # Pale green
        }
        
        return VisualizationNode(
            node_id=node.content_hash,  # Use stable content hash as ID
            node_type=node.node_type,
            display_name=node.display_name,
            color_hint=color_map.get(node.node_type, '#D3D3D3'),
            size_hint=(200, 50) if node.node_type == 'menu_container' else (150, 30),
            metadata={
                'semantic_id': node.semantic_id,
                'content': node.content,
                'parent_id': node.parent.content_hash if node.parent else None,
                'children_count': len(node.children),
                'source_file': node.source_file,
                'source_line': node.source_line
            }
        )
    
    def _create_hierarchy_connection(self, parent: HierarchyNode, child: HierarchyNode) -> VisualizationConnection:
        """Create a visualization connection between parent and child nodes."""
        connection_type_map = {
            ('label', 'menu_container'): 'label_to_menu',
            ('menu_container', 'choice'): 'container_to_choice',
            ('choice', 'menu_container'): 'choice_to_nested_menu'
        }
        
        connection_type = connection_type_map.get(
            (parent.node_type, child.node_type), 
            'hierarchy'
        )
        
        return VisualizationConnection(
            connection_id=f"{parent.content_hash}_to_{child.content_hash}",
            source_node_id=parent.content_hash,
            target_node_id=child.content_hash,
            connection_type=connection_type,
            color_hint='blue' if connection_type == 'container_to_choice' else 'orange',
            weight_hint=1.0,
            metadata={
                'parent_semantic_id': parent.semantic_id,
                'child_semantic_id': child.semantic_id
            }
        )
    
    def _create_flow_connections_for_visualization(self) -> List[VisualizationConnection]:
        """Create flow connections for jumps between labels using flow relationships."""
        flow_connections = []
        
        for node in self.node_index.values():
            # Use the new flow relationships instead of jump_targets
            for flow in node.outgoing_flows:
                target_node = flow.target_node
                
                # Determine connection type based on flow type
                if flow.flow_type == 'menu_choice':
                    connection_type = 'choice_to_label'
                    color_hint = 'orange'
                elif flow.flow_type == 'call':
                    connection_type = 'label_to_call'
                    color_hint = 'blue'
                else:  # jump or other
                    connection_type = 'label_to_label'
                    color_hint = 'orange'
                
                connection = VisualizationConnection(
                    connection_id=f"flow_{node.content_hash}_to_{target_node.content_hash}",
                    source_node_id=node.content_hash,
                    target_node_id=target_node.content_hash,
                    connection_type=connection_type,
                    color_hint=color_hint,
                    weight_hint=1.5,
                    metadata={
                        'flow_type': flow.flow_type,
                        'source_label': flow.metadata.get('source_label'),
                        'target_label': flow.metadata.get('target_label'),
                        'generated_by': 'authoritative_hierarchy_flows'
                    }
                )
                flow_connections.append(connection)
        
        return flow_connections
    
    def create_all_flow_connections_for_visualization(self) -> List[VisualizationConnection]:
        """Create all flow connections (label-to-label) for visualization - REPLACES OLD SYSTEM."""
        print("[HIERARCHY] Creating all flow connections for visualization...")
        flow_connections = self._create_flow_connections_for_visualization()
        print(f"[HIERARCHY] Created {len(flow_connections)} flow connections")
        return flow_connections
    
    def print_hierarchy(self, node: Optional[HierarchyNode] = None, depth: int = 0) -> None:
        """Print the hierarchy structure for debugging."""
        if node is None:
            print("[HIERARCHY] Structure:")
            for root in self.root_nodes:
                self.print_hierarchy(root, 0)
            return
        
        indent = "  " * depth
        children_info = f" ({len(node.children)} children)" if node.children else ""
        print(f"{indent}{node.semantic_id} [{node.node_type}]{children_info}")
        
        for child in node.children:
            self.print_hierarchy(child, depth + 1)


def test_authoritative_hierarchy():
    """Test the authoritative hierarchy with sample data."""
    hierarchy = AuthoritativeHierarchy()
    
    # Create sample flow graph data (simplified)
    sample_flow_graph = {
        'labels': {
            'start': type('LabelData', (), {
                'file_path': 'script.rpy',
                'line_number': 1,
                'menu_nodes': []
            })(),
            'ep2cont5': type('LabelData', (), {
                'file_path': 'ep2.rpy', 
                'line_number': 100,
                'menu_nodes': []
            })()
        }
    }
    
    hierarchy.build_from_flow_graph(sample_flow_graph)
    hierarchy.print_hierarchy()
    
    nodes, connections = hierarchy.get_visualization_data()
    print(f"\nGenerated {len(nodes)} visualization nodes")
    print(f"Generated {len(connections)} visualization connections")


if __name__ == "__main__":
    test_authoritative_hierarchy()