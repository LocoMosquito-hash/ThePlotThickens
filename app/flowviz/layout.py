"""
Layered layout engine for FlowViz.

The implementation mirrors the simplified Sugiyama flow described in the
FlowViz README: assign layers via topological ordering, keep siblings spaced
evenly, and normalize coordinates so the graph anchors near the top/center
of the scene.  The output mutates the supplied graph in-place so downstream
widgets can render immediately.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, List

from .models import (
    FlowVizEdge,
    FlowVizGraph,
    FlowVizNode,
    FlowVizPosition,
    FlowVizGeometry,
)


class LayeredLayoutEngine:
    """Calculates deterministic node coordinates for the FlowViz canvas."""

    def __init__(
        self,
        vertical_spacing: float = 180.0,
        horizontal_padding: float = 120.0,
        top_margin: float = 40.0,
    ) -> None:
        self.vertical_spacing = vertical_spacing
        self.horizontal_padding = horizontal_padding
        self.top_margin = top_margin

    def apply(self, graph: FlowVizGraph) -> FlowVizGraph:
        """
        Mutate node positions using a layered layout.

        Args:
            graph: FlowViz graph to position.

        Returns:
            FlowVizGraph: the same instance, positioned.
        """
        node_map = graph.node_lookup()
        layers = self._assign_layers(graph.nodes, graph.edges)
        ordered_layers = self._order_layers(layers, graph.edges)
        self._assign_coordinates(ordered_layers, node_map)
        self._normalize_positions(node_map)
        return graph

    def _assign_layers(
        self, nodes: List[FlowVizNode], edges: List[FlowVizEdge]
    ) -> List[List[str]]:
        """Return node IDs grouped by layered depth."""
        adjacency: Dict[str, List[str]] = defaultdict(list)
        indegree: Dict[str, int] = {node.id: 0 for node in nodes}

        for edge in edges:
            adjacency[edge.source_id].append(edge.target_id)
            indegree[edge.target_id] += 1

        queue: deque[str] = deque()
        layer_map: Dict[str, int] = {}

        for node in nodes:
            if indegree[node.id] == 0:
                queue.append(node.id)
                layer_map[node.id] = 0

        while queue:
            current = queue.popleft()
            current_layer = layer_map[current]
            for child in adjacency[current]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    layer_map[child] = current_layer + 1
                    queue.append(child)

        # Ensure disconnected nodes still appear.
        max_layer = max(layer_map.values(), default=0)
        for node in nodes:
            if node.id not in layer_map:
                max_layer += 1
                layer_map[node.id] = max_layer

        layers: List[List[str]] = []
        for node_id, layer_index in sorted(layer_map.items(), key=lambda item: item[1]):
            while len(layers) <= layer_index:
                layers.append([])
            layers[layer_index].append(node_id)

        return layers

    def _order_layers(
        self, layers: List[List[str]], edges: List[FlowVizEdge]
    ) -> List[List[str]]:
        """
        Apply a lightweight barycenter heuristic so nodes roughly align with
        their parents/children.  The algorithm intentionally remains simple to
        keep the implementation approachable for contributors.
        """
        adjacency = defaultdict(list)
        reverse_adjacency = defaultdict(list)
        for edge in edges:
            adjacency[edge.source_id].append(edge.target_id)
            reverse_adjacency[edge.target_id].append(edge.source_id)

        for _ in range(2):
            # Forward pass: rely on parent barycenters.
            for idx in range(1, len(layers)):
                layer = layers[idx]
                scores = {
                    node_id: self._avg_position(
                        reverse_adjacency.get(node_id, []), layers[idx - 1]
                    )
                    for node_id in layer
                }
                layer.sort(key=lambda nid: scores.get(nid, float("inf")))

            # Backward pass: rely on child barycenters.
            for idx in range(len(layers) - 2, -1, -1):
                layer = layers[idx]
                scores = {
                    node_id: self._avg_position(
                        adjacency.get(node_id, []), layers[idx + 1]
                    )
                    for node_id in layer
                }
                layer.sort(key=lambda nid: scores.get(nid, float("inf")))

        return layers

    def _avg_position(self, neighbors: List[str], reference_layer: List[str]) -> float:
        """Return average neighbor index within reference layer."""
        if not neighbors:
            return float("inf")
        index_map = {node_id: idx for idx, node_id in enumerate(reference_layer)}
        positions = [index_map.get(neighbor, 0) for neighbor in neighbors]
        return sum(positions) / len(positions)

    def _assign_coordinates(
        self, layers: List[List[str]], node_map: Dict[str, FlowVizNode]
    ) -> None:
        """Compute concrete coordinates for each node."""
        for layer_index, layer in enumerate(layers):
            y = self.top_margin + layer_index * self.vertical_spacing
            widths = [FlowVizGeometry.node_dimensions(node_map[node_id])[0] for node_id in layer]
            total_spacing = self.horizontal_padding * max(len(layer) - 1, 0)
            layer_width = sum(widths) + total_spacing
            current_x = -layer_width / 2.0

            for node_id, width in zip(layer, widths):
                node = node_map[node_id]
                node.position = FlowVizPosition(x=current_x, y=y)
                current_x += width + self.horizontal_padding

    def _normalize_positions(self, node_map: Dict[str, FlowVizNode]) -> None:
        """Shift nodes so the minimum x/y anchors at zero."""
        if not node_map:
            return
        min_x = min(node.position.x for node in node_map.values())
        min_y = min(node.position.y for node in node_map.values())
        offset_x = abs(min_x) + 40.0 if min_x < 0 else 0.0
        offset_y = abs(min_y) + 40.0 if min_y < 0 else 0.0
        if offset_x == 0.0 and offset_y == 0.0:
            return
        for node in node_map.values():
            node.position = FlowVizPosition(
                x=node.position.x + offset_x, y=node.position.y + offset_y
            )

