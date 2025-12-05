"""
FlowViz data models, enums, and helper factories.

This module centralizes the Python-side representation of the FlowViz graph
so both the Source Analysis tab and the standalone launcher can share a
consistent data contract.  The definitions mirror the structures documented
in the FlowViz Figma README and the `flowviz_ui_overview.md` notes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class NodeType(str, Enum):
    """Supported FlowViz node categories."""

    VISUAL_START = "visual-start"
    LABEL = "label"
    MENU = "menu"
    SCREEN = "screen"


class EdgeType(str, Enum):
    """Edge channels determine color/stroke styling."""

    NARRATIVE = "narrative"
    MENU = "menu"
    SCREEN = "screen"
    CALL = "call"


@dataclass(slots=True)
class FlowVizPosition:
    """Scene-space coordinate."""

    x: float = 0.0
    y: float = 0.0


@dataclass(slots=True)
class MenuChoice:
    """Single menu choice row."""

    id: str
    text: str
    has_edge: bool = True
    is_broken: bool = False


@dataclass(slots=True)
class ScreenAction:
    """Single screen action row."""

    id: str
    text: str
    has_edge: bool = True
    is_broken: bool = False


@dataclass(slots=True)
class FlowVizNode:
    """Node payload used by the canvas."""

    id: str
    type: NodeType
    title: str
    file: Optional[str] = None
    line: Optional[int] = None
    is_entry: bool = False
    has_outgoing: bool = True
    is_ghost: bool = False
    metadata: Dict[str, str] = field(default_factory=dict)
    choices: List[MenuChoice] = field(default_factory=list)
    actions: List[ScreenAction] = field(default_factory=list)
    position: FlowVizPosition = field(default_factory=FlowVizPosition)


@dataclass(slots=True)
class FlowVizEdge:
    """Directed connection between two nodes."""

    id: str
    source_id: str
    target_id: str
    type: EdgeType
    choice_index: Optional[int] = None  # For menu choices/screen actions


@dataclass(slots=True)
class FlowVizGraph:
    """Container for nodes and edges."""

    nodes: List[FlowVizNode]
    edges: List[FlowVizEdge]

    def node_lookup(self) -> Dict[str, FlowVizNode]:
        """Return mapping for quick lookup."""
        return {node.id: node for node in self.nodes}


class FlowVizGeometry:
    """Provides canonical dimensions for each node type."""

    VISUAL_START_SIZE: Tuple[float, float] = (160.0, 40.0)
    LABEL_SIZE: Tuple[float, float] = (200.0, 80.0)
    MENU_WIDTH: float = 280.0
    SCREEN_WIDTH: float = 280.0
    HEADER_HEIGHT: float = 70.0
    ROW_HEIGHT: float = 37.0
    CONTAINER_VERTICAL_PADDING: float = 24.0  # top + bottom padding

    @classmethod
    def node_dimensions(cls, node: FlowVizNode) -> Tuple[float, float]:
        """Return width/height tuple respecting container rows."""
        if node.type is NodeType.VISUAL_START:
            return cls.VISUAL_START_SIZE
        if node.type is NodeType.LABEL:
            return cls.LABEL_SIZE
        if node.type is NodeType.MENU:
            rows = max(len(node.choices), 1)
            height = (
                cls.HEADER_HEIGHT
                + cls.CONTAINER_VERTICAL_PADDING
                + rows * cls.ROW_HEIGHT
            )
            return cls.MENU_WIDTH, height
        if node.type is NodeType.SCREEN:
            rows = max(len(node.actions), 1)
            height = (
                cls.HEADER_HEIGHT
                + cls.CONTAINER_VERTICAL_PADDING
                + rows * cls.ROW_HEIGHT
            )
            return cls.SCREEN_WIDTH, height
        return cls.LABEL_SIZE


class DummyGraphFactory:
    """
    Provides self-contained demo data so the FlowViz tab can be exercised
    without hitting the slot cache pipeline yet.
    """

    @staticmethod
    def build_morning_routine_graph() -> FlowVizGraph:
        """Return a graph matching the Figma screenshot."""
        nodes: List[FlowVizNode] = [
            FlowVizNode(
                id="visual_start",
                type=NodeType.VISUAL_START,
                title="Visual Start",
            ),
            FlowVizNode(
                id="label_start",
                type=NodeType.LABEL,
                title="start",
                file="script.rpy",
                line=1,
                is_entry=True,
            ),
            FlowVizNode(
                id="bedroom_morning",
                type=NodeType.LABEL,
                title="bedroom_morning",
                file="script.rpy",
                line=45,
            ),
            FlowVizNode(
                id="menu_morning_choice",
                type=NodeType.MENU,
                title="What will you do this morning?",
                metadata={"options": "3"},
                choices=[
                    MenuChoice(id="choice_get_dressed", text="Get dressed and head out"),
                    MenuChoice(id="choice_check_phone", text="Check your phone"),
                    MenuChoice(
                        id="choice_sleep",
                        text="Go back to sleep",
                        is_broken=True,
                        has_edge=False,
                    ),
                ],
            ),
            FlowVizNode(
                id="label_get_dressed",
                type=NodeType.LABEL,
                title="get_dressed",
                file="script.rpy",
                line=123,
            ),
            FlowVizNode(
                id="label_check_phone",
                type=NodeType.LABEL,
                title="check_phone",
                file="script.rpy",
                line=129,
            ),
            FlowVizNode(
                id="screen_navigation",
                type=NodeType.SCREEN,
                title="hud_navigation",
                file="screens.rpy",
                line=14,
                actions=[
                    ScreenAction(id="action_bedroom", text="Bedroom"),
                    ScreenAction(id="action_kitchen", text="Kitchen"),
                    ScreenAction(id="action_exit", text="Go outside", is_broken=True),
                ],
            ),
        ]

        edges: List[FlowVizEdge] = [
            FlowVizEdge(
                id="edge_vs_start",
                source_id="visual_start",
                target_id="label_start",
                type=EdgeType.NARRATIVE,
            ),
            FlowVizEdge(
                id="edge_start_bedroom",
                source_id="label_start",
                target_id="bedroom_morning",
                type=EdgeType.NARRATIVE,
            ),
            FlowVizEdge(
                id="edge_bedroom_menu",
                source_id="bedroom_morning",
                target_id="menu_morning_choice",
                type=EdgeType.MENU,
            ),
            FlowVizEdge(
                id="edge_choice_dressed",
                source_id="menu_morning_choice",
                target_id="label_get_dressed",
                type=EdgeType.NARRATIVE,
                choice_index=0,
            ),
            FlowVizEdge(
                id="edge_choice_phone",
                source_id="menu_morning_choice",
                target_id="label_check_phone",
                type=EdgeType.NARRATIVE,
                choice_index=1,
            ),
            FlowVizEdge(
                id="edge_choice_screen",
                source_id="menu_morning_choice",
                target_id="screen_navigation",
                type=EdgeType.SCREEN,
                choice_index=1,
            ),
            FlowVizEdge(
                id="edge_screen_bedroom",
                source_id="screen_navigation",
                target_id="label_get_dressed",
                type=EdgeType.SCREEN,
                choice_index=0,
            ),
        ]

        return FlowVizGraph(nodes=nodes, edges=edges)

