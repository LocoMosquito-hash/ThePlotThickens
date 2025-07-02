"""
Flow Graph Visualization Engine for Ren'Py Source API

This module provides comprehensive visualization capabilities for VN flow analysis,
creating interactive and static graphs, branching diagrams, and narrative maps.
"""

import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict, Counter
import colorsys
import math

try:
    from .core import RenpyProject
except ImportError:
    from core import RenpyProject


class FlowGraphVisualizer:
    """Advanced flow graph visualization engine for Ren'Py narrative analysis."""
    
    def __init__(self, renpy_project: RenpyProject):
        """
        Initialize the visualizer with a RenpyProject.
        
        Args:
            renpy_project: Analyzed RenpyProject instance
        """
        self.project = renpy_project
        self.flow_data = None
        self.graph = None
        self._prepare_data()
    
    def _prepare_data(self) -> None:
        """Prepare flow analysis data for visualization."""
        if not self.project.is_analyzed:
            self.project.analyze()
        
        self.flow_data = self.project.get_label_flow_analysis()
        self.graph = self._build_networkx_graph()
    
    def _build_networkx_graph(self) -> nx.DiGraph:
        """Build a NetworkX directed graph from flow analysis data."""
        G = nx.DiGraph()
        
        labels = self.flow_data.get('labels', {})
        
        # Add nodes with attributes
        for label_name, label_data in labels.items():
            G.add_node(label_name, **{
                'file': label_data.get('file', ''),
                'line': label_data.get('line', 0),
                'reachable': label_data.get('reachable', True),
                'incoming_count': len(label_data.get('incoming_connections', [])),
                'outgoing_count': len(label_data.get('outgoing_connections', [])),
                'complexity': len(label_data.get('outgoing_connections', [])),
                'depth': label_data.get('depth', 0)
            })
        
        # Add edges with attributes
        for label_name, label_data in labels.items():
            for connection in label_data.get('outgoing_connections', []):
                target = connection.get('target')
                if target and target in labels:
                    G.add_edge(label_name, target, **{
                        'flow_type': connection.get('type', 'unknown'),
                        'condition': connection.get('condition', ''),
                        'file': connection.get('file', ''),
                        'line': connection.get('line', 0)
                    })
        
        return G
    
    def generate_summary_visualization(self, output_path: str = "flow_summary.png", 
                                     figsize: Tuple[int, int] = (16, 12)) -> str:
        """
        Generate a comprehensive summary visualization of the flow graph.
        
        Args:
            output_path: Path to save the visualization
            figsize: Figure size (width, height)
            
        Returns:
            Path to the generated image
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=figsize)
        fig.suptitle(f'Ren\'Py Flow Analysis: {os.path.basename(self.project.project_path)}', 
                     fontsize=16, fontweight='bold')
        
        # 1. Flow Type Distribution (Top Left)
        flow_types = self.flow_data.get('flow_types', {})
        if flow_types:
            ax1.pie(flow_types.values(), labels=flow_types.keys(), autopct='%1.1f%%', startangle=90)
            ax1.set_title('Flow Type Distribution')
        
        # 2. Connectivity Histogram (Top Right)
        complexities = [data.get('complexity', 0) for data in self.graph.nodes(data=True)]
        ax2.hist(complexities, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax2.set_title('Scene Complexity Distribution')
        ax2.set_xlabel('Outgoing Connections')
        ax2.set_ylabel('Number of Scenes')
        
        # 3. Reachability Analysis (Bottom Left)
        reachable_count = sum(1 for _, data in self.graph.nodes(data=True) if data.get('reachable', True))
        unreachable_count = len(self.graph.nodes()) - reachable_count
        
        ax3.bar(['Reachable', 'Unreachable'], [reachable_count, unreachable_count], 
                color=['green', 'red'], alpha=0.7)
        ax3.set_title('Scene Reachability')
        ax3.set_ylabel('Number of Scenes')
        
        # 4. Quality Metrics (Bottom Right)
        quality_data = {
            'Total Labels': self.flow_data.get('total_labels', 0),
            'Total Flows': self.flow_data.get('total_flows', 0),
            'Entry Points': self.flow_data.get('entry_points', 0),
            'Dead Ends': len(self.flow_data.get('dead_end_labels', [])),
            'Flow Clusters': self.flow_data.get('flow_clusters', 0)
        }
        
        metrics_text = '\n'.join([f'{k}: {v}' for k, v in quality_data.items()])
        ax4.text(0.1, 0.5, metrics_text, transform=ax4.transAxes, fontsize=12,
                verticalalignment='center', bbox=dict(boxstyle='round', facecolor='lightgray'))
        ax4.set_title('Project Metrics')
        ax4.axis('off')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"📊 Flow summary visualization saved: {output_path}")
        return output_path
    
    def generate_interactive_flow_map(self, output_path: str = "interactive_flow_map.html",
                                    max_nodes: int = 100) -> str:
        """
        Generate an interactive flow map using Plotly.
        
        Args:
            output_path: Path to save the HTML file
            max_nodes: Maximum number of nodes to display (for performance)
            
        Returns:
            Path to the generated HTML file
        """
        # Filter to most important nodes if needed
        if len(self.graph.nodes()) > max_nodes:
            # Select nodes with highest connectivity
            node_importance = {}
            for node, data in self.graph.nodes(data=True):
                importance = data.get('incoming_count', 0) + data.get('outgoing_count', 0)
                node_importance[node] = importance
            
            top_nodes = sorted(node_importance.items(), key=lambda x: x[1], reverse=True)[:max_nodes]
            selected_nodes = [node for node, _ in top_nodes]
            subgraph = self.graph.subgraph(selected_nodes)
        else:
            subgraph = self.graph
        
        # Create layout
        pos = nx.spring_layout(subgraph, k=3, iterations=50)
        
        # Extract node and edge data
        node_x = [pos[node][0] for node in subgraph.nodes()]
        node_y = [pos[node][1] for node in subgraph.nodes()]
        node_text = []
        node_colors = []
        node_sizes = []
        
        for node, data in subgraph.nodes(data=True):
            # Node info for hover
            incoming = data.get('incoming_count', 0)
            outgoing = data.get('outgoing_count', 0)
            reachable = data.get('reachable', True)
            
            node_text.append(f"Label: {node}<br>"
                           f"Incoming: {incoming}<br>"
                           f"Outgoing: {outgoing}<br>"
                           f"Reachable: {reachable}<br>"
                           f"File: {data.get('file', 'N/A')}")
            
            # Color by reachability and complexity
            if not reachable:
                node_colors.append('red')
            elif outgoing == 0:
                node_colors.append('orange')  # Dead end
            elif incoming > 10 or outgoing > 10:
                node_colors.append('purple')  # Hub
            else:
                node_colors.append('lightblue')
            
            # Size by total connectivity
            total_connections = incoming + outgoing
            node_sizes.append(max(10, min(50, total_connections * 2)))
        
        # Edge traces
        edge_x = []
        edge_y = []
        
        for edge in subgraph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        # Create the plot
        fig = go.Figure()
        
        # Add edges
        fig.add_trace(go.Scatter(x=edge_x, y=edge_y,
                                line=dict(width=0.5, color='#888'),
                                hoverinfo='none',
                                mode='lines',
                                name='Flow Connections'))
        
        # Add nodes
        fig.add_trace(go.Scatter(x=node_x, y=node_y,
                                mode='markers+text',
                                hoverinfo='text',
                                text=list(subgraph.nodes()),
                                textposition="middle center",
                                textfont=dict(size=8),
                                hovertext=node_text,
                                marker=dict(size=node_sizes,
                                          color=node_colors,
                                          line=dict(width=2, color='black')),
                                name='Scenes'))
        
        fig.update_layout(
            title=dict(text=f'Interactive Flow Map - {os.path.basename(self.project.project_path)}', 
                       font=dict(size=16)),
            showlegend=True,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            annotations=[ 
                dict(
                    text=f"Showing {len(subgraph.nodes())} most connected scenes<br>"
                         f"🔵 Normal • 🟣 Hub • 🟠 Dead End • 🔴 Unreachable",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.005, y=-0.002,
                    xanchor='left', yanchor='bottom',
                    font=dict(size=10)
                )
            ],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white'
        )
        
        fig.write_html(output_path)
        print(f"🌐 Interactive flow map saved: {output_path}")
        return output_path
    
    def generate_branching_analysis(self, output_path: str = "branching_analysis.html") -> str:
        """
        Generate detailed branching analysis with multiple visualizations.
        
        Args:
            output_path: Path to save the HTML file
            
        Returns:
            Path to the generated HTML file
        """
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Branching Complexity', 'Flow Depth Distribution', 
                          'Hub Analysis', 'Critical Path Metrics'),
            specs=[[{"type": "bar"}, {"type": "histogram"}],
                   [{"type": "scatter"}, {"type": "bar"}]]
        )
        
        # 1. Branching Complexity (Top Left)
        nodes_data = list(self.graph.nodes(data=True))
        node_names = [node for node, _ in nodes_data]
        complexities = [data.get('complexity', 0) for _, data in nodes_data]
        
        # Sort by complexity for better visualization
        sorted_data = sorted(zip(node_names, complexities), key=lambda x: x[1], reverse=True)[:20]
        top_nodes, top_complexities = zip(*sorted_data) if sorted_data else ([], [])
        
        fig.add_trace(
            go.Bar(x=list(top_nodes), y=list(top_complexities), 
                   name='Branching Complexity', marker_color='skyblue'),
            row=1, col=1
        )
        
        # 2. Flow Depth Distribution (Top Right)
        depths = [data.get('depth', 0) for _, data in nodes_data]
        fig.add_trace(
            go.Histogram(x=depths, name='Depth Distribution', marker_color='lightgreen'),
            row=1, col=2
        )
        
        # 3. Hub Analysis (Bottom Left)
        hubs = [(node, data.get('incoming_count', 0) + data.get('outgoing_count', 0)) 
                for node, data in nodes_data]
        hubs.sort(key=lambda x: x[1], reverse=True)
        top_hubs = hubs[:15]
        
        if top_hubs:
            hub_names, hub_connections = zip(*top_hubs)
            fig.add_trace(
                go.Scatter(x=list(range(len(hub_names))), y=list(hub_connections),
                          mode='markers+lines', name='Hub Connectivity',
                          text=list(hub_names), marker_size=10),
                row=2, col=1
            )
        
        # 4. Critical Path Metrics (Bottom Right)
        quality_metrics = self.project.get_scene_connectivity().get('narrative_flow_quality', {})
        metric_names = ['Overall Score', 'Reachability', 'Connectivity']
        metric_values = [
            quality_metrics.get('overall_score', 0),
            quality_metrics.get('reachability_score', 0),
            quality_metrics.get('connectivity_score', 0)
        ]
        
        colors = ['gold' if v >= 80 else 'orange' if v >= 60 else 'red' for v in metric_values]
        
        fig.add_trace(
            go.Bar(x=metric_names, y=metric_values, 
                   name='Quality Metrics', marker_color=colors),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            title_text=f"Branching Analysis - {os.path.basename(self.project.project_path)}",
            height=800,
            showlegend=False
        )
        
        # Update x-axis for top charts
        fig.update_xaxes(tickangle=45, row=1, col=1)
        
        fig.write_html(output_path)
        print(f"📈 Branching analysis saved: {output_path}")
        return output_path
    
    def generate_narrative_path_visualization(self, start_label: str = None, 
                                            output_path: str = "narrative_paths.html",
                                            max_paths: int = 50) -> str:
        """
        Generate visualization of narrative paths from a starting point.
        
        Args:
            start_label: Starting label (auto-detect if None)
            output_path: Path to save the HTML file
            max_paths: Maximum number of paths to visualize
            
        Returns:
            Path to the generated HTML file
        """
        # Find starting label if not provided
        if start_label is None:
            # Use the label with most outgoing connections
            outgoing_counts = [(node, data.get('outgoing_count', 0)) 
                             for node, data in self.graph.nodes(data=True)]
            outgoing_counts.sort(key=lambda x: x[1], reverse=True)
            if outgoing_counts:
                start_label = outgoing_counts[0][0]
            elif self.graph.nodes():
                start_label = list(self.graph.nodes())[0]
            else:
                return output_path  # No nodes available
        
        # Get narrative paths
        paths = self.project.find_narrative_paths(start_label, max_depth=8)
        if len(paths) > max_paths:
            paths = paths[:max_paths]
        
        # Create path tree visualization
        fig = go.Figure()
        
        # Build hierarchical structure for paths
        path_nodes = {}
        path_edges = []
        level_positions = defaultdict(list)
        
        # Add root
        path_nodes[start_label] = {'level': 0, 'count': len(paths)}
        level_positions[0].append(start_label)
        
        # Process paths
        for path in paths:
            for i, label in enumerate(path[1:], 1):  # Skip start_label
                node_key = f"{path[i-1]}→{label}"
                if node_key not in path_nodes:
                    path_nodes[node_key] = {'level': i, 'count': 0, 'label': label}
                    level_positions[i].append(node_key)
                path_nodes[node_key]['count'] += 1
                
                if i > 1:
                    prev_key = f"{path[i-2]}→{path[i-1]}"
                    path_edges.append((prev_key, node_key))
                else:
                    path_edges.append((start_label, node_key))
        
        # Calculate positions
        positions = {}
        for level, nodes in level_positions.items():
            for i, node in enumerate(nodes):
                y_pos = level * -50  # Levels go down
                x_spacing = 800 / (len(nodes) + 1)
                x_pos = (i + 1) * x_spacing - 400
                positions[node] = (x_pos, y_pos)
        
        # Draw edges
        edge_x, edge_y = [], []
        for start_node, end_node in path_edges:
            if start_node in positions and end_node in positions:
                x0, y0 = positions[start_node]
                x1, y1 = positions[end_node]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
        
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color='gray'),
            hoverinfo='none',
            mode='lines',
            name='Path Connections'
        ))
        
        # Draw nodes
        node_x = [positions[node][0] for node in path_nodes.keys()]
        node_y = [positions[node][1] for node in path_nodes.keys()]
        node_text = [node.split('→')[-1] if '→' in node else node for node in path_nodes.keys()]
        node_sizes = [min(50, max(10, data['count'] * 3)) for data in path_nodes.values()]
        node_colors = [data['count'] for data in path_nodes.values()]
        
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=node_text,
            textposition="middle center",
            textfont=dict(size=8),
            marker=dict(size=node_sizes, color=node_colors, colorscale='Viridis',
                       line=dict(width=1, color='black'), showscale=True),
            name='Narrative Nodes',
            hovertemplate='%{text}<br>Frequency: %{marker.color}<extra></extra>'
        ))
        
        fig.update_layout(
            title=f'Narrative Paths from "{start_label}" ({len(paths)} paths)',
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            showlegend=False,
            height=max(600, len(level_positions) * 100),
            plot_bgcolor='white'
        )
        
        fig.write_html(output_path)
        print(f"🛤️ Narrative path visualization saved: {output_path}")
        return output_path
    
    def generate_comprehensive_report(self, output_dir: str = "flow_analysis_report") -> str:
        """
        Generate a comprehensive report with all visualizations.
        
        Args:
            output_dir: Directory to save all outputs
            
        Returns:
            Path to the output directory
        """
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"🚀 Generating comprehensive flow analysis report...")
        print(f"📁 Output directory: {output_dir}")
        
        # Generate all visualizations
        summary_path = os.path.join(output_dir, "flow_summary.png")
        interactive_path = os.path.join(output_dir, "interactive_flow_map.html")
        branching_path = os.path.join(output_dir, "branching_analysis.html")
        narrative_path = os.path.join(output_dir, "narrative_paths.html")
        
        # Generate visualizations
        self.generate_summary_visualization(summary_path)
        self.generate_interactive_flow_map(interactive_path)
        self.generate_branching_analysis(branching_path)
        self.generate_narrative_path_visualization(output_path=narrative_path)
        
        # Generate JSON data export
        data_export = {
            'project_path': self.project.project_path,
            'generated_at': datetime.now().isoformat(),
            'flow_analysis': self.flow_data,
            'graph_stats': {
                'total_nodes': len(self.graph.nodes()),
                'total_edges': len(self.graph.edges()),
                'is_connected': nx.is_weakly_connected(self.graph),
                'node_connectivity': nx.node_connectivity(self.graph) if len(self.graph.nodes()) > 1 else 0
            }
        }
        
        json_path = os.path.join(output_dir, "flow_data.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data_export, f, indent=2, ensure_ascii=False)
        
        # Generate HTML index page
        index_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Flow Analysis Report - {os.path.basename(self.project.project_path)}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f8f9fa; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                   color: white; padding: 30px; border-radius: 15px; text-align: center; }}
        .section {{ background: white; margin: 20px 0; padding: 25px; 
                   border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .stats {{ display: flex; justify-content: space-around; margin: 30px 0; }}
        .stat {{ text-align: center; padding: 20px; background: #f8f9fa; 
                border-radius: 10px; min-width: 120px; }}
        .stat h3 {{ margin: 0; color: #495057; font-size: 14px; }}
        .stat p {{ font-size: 28px; font-weight: bold; color: #007bff; margin: 10px 0; }}
        a {{ color: #007bff; text-decoration: none; font-weight: 500; }}
        a:hover {{ text-decoration: underline; }}
        .viz-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
        .viz-item {{ padding: 15px; background: #f8f9fa; border-radius: 8px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎮 Ren'Py Flow Analysis Report</h1>
        <h2>📁 {os.path.basename(self.project.project_path)}</h2>
        <p>📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="stats">
        <div class="stat">
            <h3>🏷️ TOTAL LABELS</h3>
            <p>{self.flow_data.get('total_labels', 0)}</p>
        </div>
        <div class="stat">
            <h3>🌊 TOTAL FLOWS</h3>
            <p>{self.flow_data.get('total_flows', 0):,}</p>
        </div>
        <div class="stat">
            <h3>🎯 REACHABILITY</h3>
            <p>{self.flow_data.get('reachability_ratio', 0):.0%}</p>
        </div>
        <div class="stat">
            <h3>⭐ QUALITY SCORE</h3>
            <p>{self.project.get_scene_connectivity().get('narrative_flow_quality', {}).get('overall_score', 0):.0f}/100</p>
        </div>
    </div>
    
    <div class="section">
        <h3>📊 Visual Analysis</h3>
        <div class="viz-grid">
            <div class="viz-item">
                <h4>📈 Flow Summary Chart</h4>
                <p>Comprehensive overview of flow statistics and distributions</p>
                <a href="flow_summary.png" target="_blank">→ View Chart</a>
            </div>
            <div class="viz-item">
                <h4>🌐 Interactive Flow Map</h4>
                <p>Explore scene connections with interactive navigation</p>
                <a href="interactive_flow_map.html" target="_blank">→ Explore Map</a>
            </div>
        </div>
    </div>
    
    <div class="section">
        <h3>📋 Data & Analysis</h3>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div>
                <h4>🔍 Key Metrics</h4>
                <p><strong>Entry Points:</strong> {self.flow_data.get('entry_points', 0)}</p>
                <p><strong>Dead Ends:</strong> {len(self.flow_data.get('dead_end_labels', []))}</p>
                <p><strong>Flow Clusters:</strong> {self.flow_data.get('flow_clusters', 0)}</p>
                <p><strong>Connectivity Ratio:</strong> {self.flow_data.get('connectivity_ratio', 0):.2f}</p>
            </div>
            <div>
                <h4>📄 Export Options</h4>
                <p><a href="flow_data.json" target="_blank">📊 Complete Flow Data (JSON)</a></p>
                <p>Contains all analysis results, node data, and connectivity information</p>
            </div>
        </div>
    </div>
</body>
</html>
        """
        
        index_path = os.path.join(output_dir, "index.html")
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_html)
        
        print(f"✅ Comprehensive report generated!")
        print(f"🌐 Open {index_path} to view the complete analysis")
        
        return output_dir


def quick_visualize(project_path: str, output_dir: str = "flow_visualization") -> str:
    """
    Quick function to visualize any Ren'Py project.
    
    Args:
        project_path: Path to the Ren'Py project
        output_dir: Output directory for visualizations
        
    Returns:
        Path to the generated report directory
    """
    print(f"🚀 Quick visualization for: {project_path}")
    
    # Create and analyze project
    project = RenpyProject(project_path)
    project.analyze()
    
    # Create visualizer and generate report
    visualizer = FlowGraphVisualizer(project)
    return visualizer.generate_comprehensive_report(output_dir)


if __name__ == "__main__":
    # Example usage
    test_vn_path = "T:/AG/Savior-0.16c-pc/game"  # From our test
    
    if os.path.exists(test_vn_path):
        output_path = quick_visualize(test_vn_path, "savior_flow_analysis")
        print(f"\n✨ Visualization complete! Check: {output_path}")
    else:
        print("❌ Test VN path not found. Update the path in __main__ section.") 