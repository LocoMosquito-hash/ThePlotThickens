#!/usr/bin/env python3
"""
Debug Visualizer with Rendering Diagnostics
==========================================

This creates a debug version of the menu container visualizer that logs
every step of the rendering process to identify why menu nodes aren't appearing.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from menu_container_visualizer import MenuContainerVisualizer
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import networkx as nx
from typing import Dict, Any, List, Tuple
import numpy as np

class DebugMenuContainerVisualizer(MenuContainerVisualizer):
    """Debug version of MenuContainerVisualizer with extensive logging"""
    
    def __init__(self, flow_data: Dict[str, Any]):
        super().__init__(flow_data)
        self.render_log = []
        self.node_render_count = 0
        self.edge_render_count = 0
        
    def debug_log(self, message: str):
        """Log debug messages"""
        print(f"[RENDER] {message}")
        self.render_log.append(message)
        
    def create_graph(self):
        """Override to add debugging"""
        self.debug_log("=== CREATING GRAPH ===")
        graph = super().create_graph()
        
        all_nodes = list(graph.nodes())
        menu_nodes = [n for n in all_nodes if '_menu_' in n]
        label_nodes = [n for n in all_nodes if '_menu_' not in n and not n.startswith('_')]
        
        self.debug_log(f"Graph created with {len(all_nodes)} total nodes")
        self.debug_log(f"Menu nodes: {len(menu_nodes)}")
        self.debug_log(f"Label nodes: {len(label_nodes)}")
        self.debug_log(f"Sample menu nodes: {menu_nodes[:5]}")
        
        # Check edges
        all_edges = list(graph.edges(data=True))
        menu_choice_edges = [e for e in all_edges if e[2].get('type') == 'menu_choice']
        label_to_menu_edges = [e for e in all_edges if e[2].get('type') == 'label_to_menu']
        
        self.debug_log(f"Total edges: {len(all_edges)}")
        self.debug_log(f"Menu choice edges: {len(menu_choice_edges)}")
        self.debug_log(f"Label to menu edges: {len(label_to_menu_edges)}")
        
        return graph
        
    def draw_menu_container(self, ax, node_id: str, choices: List[Dict], 
                          pos: Tuple[float, float], node_size: float = 3000):
        """Override to add debugging"""
        self.debug_log(f"Drawing menu container: {node_id}")
        self.debug_log(f"Position: {pos}")
        self.debug_log(f"Choices: {len(choices)}")
        self.debug_log(f"Node size: {node_size}")
        
        try:
            # Call parent method
            super().draw_menu_container(ax, node_id, choices, pos, node_size)
            self.debug_log(f"✅ Successfully drew menu container: {node_id}")
            self.node_render_count += 1
        except Exception as e:
            self.debug_log(f"❌ Failed to draw menu container {node_id}: {e}")
            import traceback
            self.debug_log(f"Traceback: {traceback.format_exc()}")
            
    def draw_regular_node(self, ax, node_id: str, pos: Tuple[float, float], 
                         node_color: str, node_size: float = 1000):
        """Override to add debugging"""
        self.debug_log(f"Drawing regular node: {node_id}")
        self.debug_log(f"Position: {pos}, Color: {node_color}, Size: {node_size}")
        
        try:
            # Call parent method  
            super().draw_regular_node(ax, node_id, pos, node_color, node_size)
            self.debug_log(f"✅ Successfully drew regular node: {node_id}")
            self.node_render_count += 1
        except Exception as e:
            self.debug_log(f"❌ Failed to draw regular node {node_id}: {e}")
            import traceback
            self.debug_log(f"Traceback: {traceback.format_exc()}")
            
    def draw_edge(self, ax, start_pos: Tuple[float, float], end_pos: Tuple[float, float],
                 edge_type: str, **kwargs):
        """Override to add debugging"""
        self.debug_log(f"Drawing edge: {start_pos} -> {end_pos}, type: {edge_type}")
        
        try:
            # Call parent method
            super().draw_edge(ax, start_pos, end_pos, edge_type, **kwargs)
            self.debug_log(f"✅ Successfully drew edge: {edge_type}")
            self.edge_render_count += 1
        except Exception as e:
            self.debug_log(f"❌ Failed to draw edge: {e}")
            import traceback
            self.debug_log(f"Traceback: {traceback.format_exc()}")
            
    def visualize_with_menu_containers(self, output_file: str = "debug_menu_containers.png",
                                     figsize: Tuple[int, int] = (20, 16), 
                                     focus_node: str = None) -> str:
        """Override main visualization with debugging"""
        self.debug_log("=== STARTING VISUALIZATION ===")
        
        try:
            # Create graph
            graph = self.create_graph()
            
            # Get node positions
            self.debug_log("Calculating node layout...")
            pos = nx.spring_layout(graph, k=3, iterations=50)
            self.debug_log(f"Layout calculated for {len(pos)} nodes")
            
            # Create figure
            fig, ax = plt.subplots(figsize=figsize)
            ax.set_aspect('equal')
            
            # Track what we're about to render
            all_nodes = list(graph.nodes())
            menu_nodes = [n for n in all_nodes if '_menu_' in n]
            label_nodes = [n for n in all_nodes if '_menu_' not in n and not n.startswith('_')]
            
            self.debug_log(f"About to render {len(menu_nodes)} menu nodes")
            self.debug_log(f"About to render {len(label_nodes)} label nodes")
            
            # Draw menu containers first
            self.debug_log("=== DRAWING MENU CONTAINERS ===")
            menu_containers_drawn = 0
            for node_id in menu_nodes:
                if node_id in pos:
                    # Get menu choices for this node
                    choices = self.get_menu_choices(node_id)
                    if choices:
                        self.draw_menu_container(ax, node_id, choices, pos[node_id])
                        menu_containers_drawn += 1
                    else:
                        self.debug_log(f"No choices found for menu node: {node_id}")
                else:
                    self.debug_log(f"No position found for menu node: {node_id}")
                    
            self.debug_log(f"Drew {menu_containers_drawn} menu containers")
            
            # Draw regular nodes
            self.debug_log("=== DRAWING REGULAR NODES ===")
            regular_nodes_drawn = 0
            for node_id in label_nodes:
                if node_id in pos:
                    # Determine node color
                    if node_id.startswith('ch'):
                        node_color = '#4CAF50'  # Green for chapter nodes
                    elif 'choice' in node_id:
                        node_color = '#FF9800'  # Orange for choice nodes
                    else:
                        node_color = '#2196F3'  # Blue for other nodes
                        
                    self.draw_regular_node(ax, node_id, pos[node_id], node_color)
                    regular_nodes_drawn += 1
                else:
                    self.debug_log(f"No position found for regular node: {node_id}")
                    
            self.debug_log(f"Drew {regular_nodes_drawn} regular nodes")
            
            # Draw edges with filtering
            self.debug_log("=== DRAWING EDGES ===")
            edges_drawn = 0
            edges_skipped = 0
            
            # Build set of menu choice edges to filter out
            menu_choice_edges = set()
            for u, v, data in graph.edges(data=True):
                if data.get('type') == 'menu_choice':
                    menu_choice_edges.add((u, v))
                    
            self.debug_log(f"Filtering out {len(menu_choice_edges)} menu choice edges")
            
            for u, v, data in graph.edges(data=True):
                if (u, v) in menu_choice_edges:
                    edges_skipped += 1
                    continue
                    
                if u in pos and v in pos:
                    edge_type = data.get('type', 'default')
                    self.draw_edge(ax, pos[u], pos[v], edge_type)
                    edges_drawn += 1
                else:
                    self.debug_log(f"Missing position for edge: {u} -> {v}")
                    
            self.debug_log(f"Drew {edges_drawn} edges, skipped {edges_skipped}")
            
            # Add title and legend
            plt.title(f"Debug Menu Container Visualization\n"
                     f"Nodes: {self.node_render_count}, Edges: {self.edge_render_count}", 
                     fontsize=16)
            
            # Add debug info to plot
            debug_text = (f"Menu Containers: {menu_containers_drawn}\n"
                         f"Regular Nodes: {regular_nodes_drawn}\n" 
                         f"Edges Drawn: {edges_drawn}\n"
                         f"Edges Skipped: {edges_skipped}")
            
            ax.text(0.02, 0.98, debug_text, transform=ax.transAxes, 
                   verticalalignment='top', fontsize=10,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.8))
            
            # Save and show
            plt.tight_layout()
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            self.debug_log(f"Visualization saved to: {output_file}")
            
            # Print summary
            self.debug_log("=== RENDER SUMMARY ===")
            self.debug_log(f"Total nodes rendered: {self.node_render_count}")
            self.debug_log(f"Total edges rendered: {self.edge_render_count}")
            self.debug_log(f"Menu containers: {menu_containers_drawn}")
            self.debug_log(f"Regular nodes: {regular_nodes_drawn}")
            
            return output_file
            
        except Exception as e:
            self.debug_log(f"❌ CRITICAL VISUALIZATION ERROR: {e}")
            import traceback
            self.debug_log(f"Traceback: {traceback.format_exc()}")
            return ""
            
    def save_debug_log(self, filename: str = "render_debug.log"):
        """Save debug log to file"""
        with open(filename, 'w') as f:
            for entry in self.render_log:
                f.write(entry + '\n')
        print(f"Debug log saved to: {filename}")

def main():
    """Run debug visualization"""
    project_path = r"T:\AG\MySisterMyRoommateV1.69-pc\game"
    
    print("Running Debug Visualization...")
    print("=" * 40)
    
    try:
        # Load flow data
        from flow_visualizer import FlowVisualizer
        visualizer = FlowVisualizer(project_path)
        visualizer.analyze_project()
        flow_data = visualizer.get_flow_graph()
        
        print(f"Loaded flow data for {len(flow_data)} labels")
        
        # Create debug visualizer
        debug_viz = DebugMenuContainerVisualizer(flow_data)
        
        # Run visualization with debugging
        output_file = debug_viz.visualize_with_menu_containers(
            output_file="debug_visualization_output.png",
            figsize=(24, 18)
        )
        
        # Save debug log
        debug_viz.save_debug_log("debug_render.log")
        
        print(f"\nDebug visualization complete!")
        print(f"Output: {output_file}")
        print(f"Debug log: debug_render.log")
        
    except Exception as e:
        print(f"❌ Debug visualization failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main() 