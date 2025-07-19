"""
Flow Visualizer Interface Definition

This module defines the clean interface between the flow visualizer POC 
and the renpy-source-api, ensuring proper separation of concerns.
"""

from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class VisualizationNode:
    """
    Standardized node data for visualization.
    
    This is the interface between parsing and visualization - 
    all node data should be converted to this format.
    """
    node_id: str
    node_type: str  # 'label', 'menu_container', 'choice_button'
    display_name: str
    
    # Position and styling hints
    suggested_position: Optional[tuple] = None
    color_hint: Optional[str] = None
    size_hint: Optional[tuple] = None
    
    # Metadata for tooltips and context
    metadata: Dict[str, Any] = None
    
    # Connections
    incoming_connections: List[str] = None
    outgoing_connections: List[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.incoming_connections is None:
            self.incoming_connections = []
        if self.outgoing_connections is None:
            self.outgoing_connections = []


@dataclass
class VisualizationConnection:
    """
    Standardized connection data for visualization.
    """
    connection_id: str
    source_node_id: str
    target_node_id: str
    connection_type: str  # 'jump', 'call', 'menu_choice', 'implicit'
    
    # Styling hints
    line_style: Optional[str] = None  # 'solid', 'dashed', 'dotted'
    color_hint: Optional[str] = None
    weight_hint: Optional[float] = None
    
    # Metadata
    label: Optional[str] = None
    condition: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class VisualizationData:
    """
    Complete visualization data package from parser to visualizer.
    """
    nodes: List[VisualizationNode]
    connections: List[VisualizationConnection]
    project_info: Dict[str, Any]
    analysis_metadata: Dict[str, Any]  # SDK usage, complexity info, etc.


class FlowDataProvider(ABC):
    """
    Abstract interface for providing flow data to the visualizer.
    
    The renpy-source-api should implement this interface to provide
    clean, standardized data to the flow visualizer.
    """
    
    @abstractmethod
    def analyze_project(self, project_path: str, use_sdk: bool = False) -> VisualizationData:
        """
        Analyze a Renpy project and return visualization data.
        
        Args:
            project_path: Path to the Renpy project directory
            use_sdk: Whether to use SDK analysis for complex structures
            
        Returns:
            VisualizationData ready for display
        """
        pass
    
    @abstractmethod
    def get_analysis_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the last analysis (SDK usage, performance, etc.)
        """
        pass
    
    @abstractmethod
    def search_nodes(self, query: str) -> List[VisualizationNode]:
        """
        Search for nodes matching a query.
        """
        pass


class FlowVisualizer(ABC):
    """
    Abstract interface for the flow visualizer.
    
    This defines what the visualizer should be able to do without
    caring about how parsing works.
    """
    
    @abstractmethod
    def load_flow_data(self, data: VisualizationData) -> None:
        """
        Load visualization data and create the visual representation.
        """
        pass
    
    @abstractmethod
    def apply_layout(self, layout_type: str) -> None:
        """
        Apply a specific layout algorithm to the current data.
        """
        pass
    
    @abstractmethod
    def highlight_path(self, start_node: str, end_node: str) -> None:
        """
        Highlight a path between two nodes.
        """
        pass
    
    @abstractmethod
    def export_image(self, file_path: str) -> bool:
        """
        Export the current visualization as an image.
        """
        pass 