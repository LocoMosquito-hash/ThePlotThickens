"""
Menu Container Visualizer - Renders menu nodes as visual containers with individual choice connections.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import networkx as nx
import numpy as np
from typing import Dict, List, Tuple, Any
import os

try:
    from flow_visualizer import FlowGraphVisualizer
    from core import RenpyProject
except ImportError as e:
    print(f"Import error: {e}")


class MenuContainerVisualizer(FlowGraphVisualizer):
    """Specialized visualizer that renders menu nodes as visual containers."""
    
    def __init__(self, project: 'RenpyProject'):
        super().__init__(project)
        self.menu_container_style = {
            'facecolor': 'gold',
            'edgecolor': 'orange',
            'linewidth': 2,
            'alpha': 0.8,
            'boxstyle': 'round,pad=0.3'
        }
        self.choice_button_style = {
            'facecolor': 'white',
            'edgecolor': 'darkgray',
            'linewidth': 1,
            'boxstyle': 'round,pad=0.1'
        }
    
    def generate_menu_container_visualization(self, 
                                            output_path: str = "menu_container_flow.png",
                                            focus_label: str = "ch4ashbagdone",
                                            figsize: Tuple[int, int] = (20, 12)) -> str:
        """
        Generate a flow visualization with menu containers.
        
        Args:
            output_path: Path to save the visualization
            focus_label: Label to focus on (and its immediate neighbors)
            figsize: Figure size (width, height)
            
        Returns:
            Path to the generated image
        """
        # Create subgraph around focus label for clarity
        if focus_label in self.graph:
            # Get nodes within 2 hops of focus label
            focus_nodes = set([focus_label])
            focus_nodes.update(self.graph.successors(focus_label))
            focus_nodes.update(self.graph.predecessors(focus_label))
            
            # Add menu nodes and their connections
            menu_nodes = [n for n in focus_nodes if self.graph.nodes[n].get('node_type') == 'menu']
            for menu_node in menu_nodes:
                focus_nodes.update(self.graph.successors(menu_node))
                focus_nodes.update(self.graph.predecessors(menu_node))
            
            subgraph = self.graph.subgraph(focus_nodes)
        else:
            subgraph = self.graph
        
        # Create the visualization
        fig, ax = plt.subplots(1, 1, figsize=figsize)
        fig.suptitle(f'Menu Container Flow Visualization: {focus_label}', 
                     fontsize=16, fontweight='bold')
        
        # Compute layout
        pos = self._compute_menu_container_layout(subgraph, focus_label)
        
        # Render nodes and menu containers
        self._render_menu_containers(ax, subgraph, pos)
        
        # Render edges
        self._render_menu_container_edges(ax, subgraph, pos)
        
        # Set axis properties
        ax.set_xlim(-2, 12)
        ax.set_ylim(-2, 10)
        ax.axis('off')
        
        # Add legend
        self._add_menu_container_legend(ax)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"🎨 Menu container visualization saved: {output_path}")
        return output_path
    
    def _compute_menu_container_layout(self, graph: nx.DiGraph, focus_label: str) -> Dict[str, Tuple[float, float]]:
        """Compute positions optimized for menu container display."""
        pos = {}
        
        # Focus label at center-left
        if focus_label in graph:
            pos[focus_label] = (2, 5)
        
        # Find menu nodes connected to focus label
        menu_nodes = []
        if focus_label in graph:
            for successor in graph.successors(focus_label):
                if graph.nodes[successor].get('node_type') == 'menu':
                    menu_nodes.append(successor)
        
        # Position menu nodes to the right of focus label
        for i, menu_node in enumerate(menu_nodes):
            pos[menu_node] = (5, 5 + i * 3)  # Space out vertically if multiple
        
        # Position destination nodes
        for menu_node in menu_nodes:
            destinations = list(graph.successors(menu_node))
            menu_y = pos[menu_node][1]
            
            # Arrange destinations around the menu
            for j, dest in enumerate(destinations):
                if dest not in pos:  # Avoid repositioning
                    angle = (j / len(destinations)) * 2 * np.pi
                    radius = 3
                    dest_x = pos[menu_node][0] + 4 + radius * np.cos(angle)
                    dest_y = menu_y + radius * np.sin(angle)
                    pos[dest] = (dest_x, dest_y)
        
        # Position any remaining nodes using spring layout
        remaining_nodes = [n for n in graph.nodes() if n not in pos]
        if remaining_nodes:
            remaining_graph = graph.subgraph(remaining_nodes)
            if len(remaining_graph) > 0:
                spring_pos = nx.spring_layout(remaining_graph, k=2, iterations=50)
                for node, (x, y) in spring_pos.items():
                    pos[node] = (x * 3 + 8, y * 3 + 2)
        
        return pos
    
    def _render_menu_containers(self, ax: plt.Axes, graph: nx.DiGraph, pos: Dict[str, Tuple[float, float]]):
        """Render menu nodes as containers with individual choice buttons."""
        
        for node, (x, y) in pos.items():
            node_data = graph.nodes[node]
            
            if node_data.get('node_type') == 'menu':
                # Render menu container
                self._render_single_menu_container(ax, node, node_data, x, y, graph)
            else:
                # Render regular label node
                self._render_regular_label_node(ax, node, node_data, x, y)
    
    def _render_single_menu_container(self, ax: plt.Axes, menu_node: str, 
                                    node_data: Dict[str, Any], x: float, y: float, 
                                    graph: nx.DiGraph):
        """Render a single menu as a container with choice buttons."""
        
        choice_count = node_data.get('choice_count', 4)
        
        # Calculate container size based on choice count
        container_width = 3
        container_height = max(2, choice_count * 0.6 + 0.8)
        
        # Menu container background
        container = FancyBboxPatch(
            (x - container_width/2, y - container_height/2), 
            container_width, container_height,
            **self.menu_container_style
        )
        ax.add_patch(container)
        
        # Menu title
        ax.text(x, y + container_height/2 - 0.3, 'MENU', 
               ha='center', va='center', fontsize=12, fontweight='bold')
        
        # Get choice destinations to create individual buttons
        destinations = list(graph.successors(menu_node))
        
        # Render individual choice buttons
        button_height = 0.4
        start_y = y + container_height/2 - 0.8
        
        for i, dest in enumerate(destinations):
            button_y = start_y - i * (button_height + 0.1)
            button_x = x
            
            # Choice button
            button = FancyBboxPatch(
                (button_x - 1, button_y - button_height/2),
                2, button_height,
                **self.choice_button_style
            )
            ax.add_patch(button)
            
            # Choice text (simplified from destination)
            choice_text = dest.replace('ch4ash', '').replace('ch4', '').title()
            ax.text(button_x, button_y, choice_text, 
                   ha='center', va='center', fontsize=9)
            
            # Store button position for edge drawing
            setattr(self, f'{menu_node}_choice_{i}_pos', (button_x + 1, button_y))
    
    def _render_regular_label_node(self, ax: plt.Axes, node: str, 
                                 node_data: Dict[str, Any], x: float, y: float):
        """Render a regular label node."""
        
        # Different colors for different node types
        if 'start' in node.lower() or node_data.get('node_type') == 'start':
            color = 'lightgreen'
            edge_color = 'green'
        elif node_data.get('has_menu', False):
            color = 'lightblue'
            edge_color = 'blue'
        else:
            color = 'lightgray'
            edge_color = 'gray'
        
        # Node shape
        node_patch = FancyBboxPatch(
            (x - 1, y - 0.4), 2, 0.8,
            boxstyle="round,pad=0.1",
            facecolor=color,
            edgecolor=edge_color,
            linewidth=1.5
        )
        ax.add_patch(node_patch)
        
        # Node text
        display_text = node.replace('ch4', '').replace('ash', '')[:12]
        ax.text(x, y, display_text, ha='center', va='center', 
               fontsize=10, fontweight='bold')
    
    def _render_menu_container_edges(self, ax: plt.Axes, graph: nx.DiGraph, 
                                   pos: Dict[str, Tuple[float, float]]):
        """Render edges with special handling for menu containers."""
        
        for source, target in graph.edges():
            source_data = graph.nodes[source]
            target_data = graph.nodes[target]
            edge_data = graph.edges[source, target]
            
            # Different edge styles based on connection type
            if source_data.get('node_type') == 'menu':
                # Edge from menu choice to destination
                self._render_menu_choice_edge(ax, source, target, pos, edge_data)
            elif target_data.get('node_type') == 'menu':
                # Edge from label to menu container
                self._render_label_to_menu_edge(ax, source, target, pos, edge_data)
            else:
                # Regular label-to-label edge
                self._render_regular_edge(ax, source, target, pos, edge_data)
    
    def _render_menu_choice_edge(self, ax: plt.Axes, menu_node: str, target: str,
                               pos: Dict[str, Tuple[float, float]], edge_data: Dict[str, Any]):
        """Render edge from menu choice button to destination."""
        
        if target not in pos:
            return
            
        # Try to get specific choice button position
        target_index = list(self.graph.successors(menu_node)).index(target)
        choice_pos_attr = f'{menu_node}_choice_{target_index}_pos'
        
        if hasattr(self, choice_pos_attr):
            start_pos = getattr(self, choice_pos_attr)
        else:
            # Fallback to menu node position
            start_pos = pos[menu_node]
        
        end_pos = pos[target]
        
        # Draw arrow from choice button to destination
        ax.annotate('', xy=end_pos, xytext=start_pos,
                   arrowprops=dict(arrowstyle='->', color='darkgreen', lw=2,
                                 connectionstyle="arc3,rad=0.1"))
    
    def _render_label_to_menu_edge(self, ax: plt.Axes, source: str, menu_node: str,
                                 pos: Dict[str, Tuple[float, float]], edge_data: Dict[str, Any]):
        """Render edge from label to menu container."""
        
        if source not in pos or menu_node not in pos:
            return
            
        start_pos = pos[source]
        end_pos = pos[menu_node]
        
        # Draw thick arrow from label to menu
        ax.annotate('', xy=end_pos, xytext=start_pos,
                   arrowprops=dict(arrowstyle='->', color='blue', lw=3,
                                 connectionstyle="arc3,rad=0"))
    
    def _render_regular_edge(self, ax: plt.Axes, source: str, target: str,
                           pos: Dict[str, Tuple[float, float]], edge_data: Dict[str, Any]):
        """Render regular label-to-label edge."""
        
        if source not in pos or target not in pos:
            return
            
        start_pos = pos[source]
        end_pos = pos[target]
        
        # Draw regular arrow
        ax.annotate('', xy=end_pos, xytext=start_pos,
                   arrowprops=dict(arrowstyle='->', color='gray', lw=1,
                                 connectionstyle="arc3,rad=0.2"))
    
    def _add_menu_container_legend(self, ax: plt.Axes):
        """Add legend explaining the menu container visualization."""
        
        legend_elements = [
            plt.Rectangle((0, 0), 1, 1, facecolor='gold', edgecolor='orange', 
                         label='Menu Container'),
            plt.Rectangle((0, 0), 1, 1, facecolor='white', edgecolor='darkgray', 
                         label='Menu Choice'),
            plt.Rectangle((0, 0), 1, 1, facecolor='lightblue', edgecolor='blue',
                         label='Label with Menu'),
            plt.Line2D([0], [0], color='blue', linewidth=3, label='Label → Menu'),
            plt.Line2D([0], [0], color='darkgreen', linewidth=2, label='Choice → Destination'),
            plt.Line2D([0], [0], color='gray', linewidth=1, label='Label → Label')
        ]
        
        ax.legend(handles=legend_elements, loc='upper right', fontsize=10)


def test_menu_container_visualization():
    """Test the menu container visualization."""
    print("🎨 Testing Menu Container Visualization...")
    
    vn_path = r"T:\AG\MySisterMyRoommateV1.69-pc\game"
    
    try:
        project = RenpyProject(vn_path)
        if not project.is_analyzed:
            print("🔄 Analyzing project...")
            project.analyze()
        
        visualizer = MenuContainerVisualizer(project)
        output_path = visualizer.generate_menu_container_visualization(
            focus_label="ch4ashbagdone",
            output_path="ch4ashbagdone_menu_container.png"
        )
        
        print(f"✅ Menu container visualization complete: {output_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_menu_container_visualization() 