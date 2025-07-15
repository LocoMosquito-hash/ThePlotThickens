#!/usr/bin/env python3
"""
Comprehensive Visualization Pipeline Diagnostics
===============================================

This script traces the entire flow from parser → graph → visualizer
to identify exactly why menu nodes aren't appearing and direct edges aren't being filtered.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flow_visualizer import FlowVisualizer, VNFlowVisualizer
from menu_container_visualizer import MenuContainerVisualizer
import networkx as nx
from typing import Dict, Any, List, Tuple
import json

class VisualizationPipelineDiagnostics:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.debug_output = []
        
    def log(self, message: str):
        """Log diagnostic messages"""
        print(f"[DIAG] {message}")
        self.debug_output.append(message)
        
    def analyze_raw_data(self, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the raw flow data from parser"""
        self.log("=== ANALYZING RAW FLOW DATA ===")
        
        stats = {
            'total_labels': len(flow_data),
            'labels_with_menus': 0,
            'total_connections': 0,
            'menu_choice_connections': 0
        }
        
        menu_labels = []
        direct_connections = []
        
        for label_name, label_data in flow_data.items():
            if label_data.get('has_menu', False):
                stats['labels_with_menus'] += 1
                menu_labels.append(label_name)
                
            connections = label_data.get('outgoing_flows', [])
            stats['total_connections'] += len(connections)
            
            for conn in connections:
                if conn.get('type') == 'menu_choice':
                    stats['menu_choice_connections'] += 1
                else:
                    direct_connections.append((label_name, conn.get('target', 'UNKNOWN')))
        
        self.log(f"Raw data stats: {stats}")
        self.log(f"Labels with menus: {menu_labels[:10]}...")  # First 10
        self.log(f"Direct connections (first 10): {direct_connections[:10]}")
        
        return stats
        
    def analyze_networkx_graph(self, graph: nx.DiGraph) -> Dict[str, Any]:
        """Analyze the NetworkX graph structure"""
        self.log("=== ANALYZING NETWORKX GRAPH ===")
        
        all_nodes = list(graph.nodes())
        menu_nodes = [n for n in all_nodes if '_menu_' in n]
        label_nodes = [n for n in all_nodes if '_menu_' not in n and not n.startswith('_')]
        
        stats = {
            'total_nodes': len(all_nodes),
            'menu_nodes': len(menu_nodes),
            'label_nodes': len(label_nodes),
            'total_edges': len(graph.edges()),
        }
        
        self.log(f"Graph stats: {stats}")
        self.log(f"Sample menu nodes: {menu_nodes[:10]}")
        
        # Check specific nodes we care about
        test_node = 'ch4ashbagdone'
        if test_node in graph:
            successors = list(graph.successors(test_node))
            predecessors = list(graph.predecessors(test_node))
            self.log(f"{test_node} successors: {successors}")
            self.log(f"{test_node} predecessors: {predecessors}")
            
            # Check for menu nodes
            menu_successors = [s for s in successors if '_menu_' in s]
            direct_successors = [s for s in successors if '_menu_' not in s]
            self.log(f"{test_node} menu successors: {menu_successors}")
            self.log(f"{test_node} direct successors: {direct_successors}")
        
        return stats
        
    def analyze_layout_positions(self, pos: Dict[str, Tuple[float, float]]) -> Dict[str, Any]:
        """Analyze node positioning"""
        self.log("=== ANALYZING NODE POSITIONS ===")
        
        menu_positions = {k: v for k, v in pos.items() if '_menu_' in k}
        label_positions = {k: v for k, v in pos.items() if '_menu_' not in k}
        
        stats = {
            'positioned_menu_nodes': len(menu_positions),
            'positioned_label_nodes': len(label_positions),
            'total_positioned': len(pos)
        }
        
        self.log(f"Position stats: {stats}")
        
        # Check if our test menu node has a position
        test_menu = 'ch4ashbagdone_menu_1'
        if test_menu in pos:
            self.log(f"{test_menu} position: {pos[test_menu]}")
        else:
            self.log(f"{test_menu} NOT found in positions!")
            
        return stats
        
    def analyze_edge_filtering(self, graph: nx.DiGraph, filtered_edges: List[Tuple]) -> Dict[str, Any]:
        """Analyze which edges are being filtered"""
        self.log("=== ANALYZING EDGE FILTERING ===")
        
        all_edges = list(graph.edges(data=True))
        menu_choice_edges = [e for e in all_edges if e[2].get('type') == 'menu_choice']
        direct_edges = [e for e in all_edges if e[2].get('type') != 'menu_choice']
        
        stats = {
            'total_edges': len(all_edges),
            'menu_choice_edges': len(menu_choice_edges),
            'direct_edges': len(direct_edges),
            'filtered_edges': len(filtered_edges)
        }
        
        self.log(f"Edge filtering stats: {stats}")
        
        # Check specific edges we care about
        test_edges = [e for e in all_edges if e[0] == 'ch4ashbagdone' or e[1] == 'ch4ashbagdone']
        self.log(f"ch4ashbagdone related edges: {test_edges}")
        
        return stats
        
    def analyze_rendering_calls(self, visualizer: MenuContainerVisualizer) -> Dict[str, Any]:
        """Analyze what gets rendered"""
        self.log("=== ANALYZING RENDERING ===")
        
        # Check if visualizer has the data we expect
        if hasattr(visualizer, 'graph'):
            graph_nodes = list(visualizer.graph.nodes())
            menu_nodes_in_graph = [n for n in graph_nodes if '_menu_' in n]
            self.log(f"Menu nodes in visualizer graph: {len(menu_nodes_in_graph)}")
            self.log(f"Sample menu nodes: {menu_nodes_in_graph[:5]}")
        
        # Check the flow data format
        if hasattr(visualizer, 'flow_data'):
            self.log(f"Flow data type: {type(visualizer.flow_data)}")
            if isinstance(visualizer.flow_data, dict):
                if 'labels' in visualizer.flow_data:
                    self.log("Flow data has 'labels' key")
                else:
                    self.log("Flow data missing 'labels' key - using direct format")
                    
        return {}
        
    def run_full_diagnosis(self) -> Dict[str, Any]:
        """Run complete diagnostic pipeline"""
        self.log("Starting comprehensive visualization pipeline diagnosis...")
        
        try:
            # Step 1: Load and analyze raw data
            visualizer = FlowVisualizer(self.project_path)
            visualizer.analyze_project()
            flow_data = visualizer.get_flow_graph()
            
            raw_stats = self.analyze_raw_data(flow_data)
            
            # Step 2: Create and analyze NetworkX graph
            vn_visualizer = VNFlowVisualizer(flow_data)
            graph = vn_visualizer.create_graph()
            
            graph_stats = self.analyze_networkx_graph(graph)
            
            # Step 3: Test menu container visualizer
            menu_visualizer = MenuContainerVisualizer(flow_data)
            menu_graph = menu_visualizer.create_graph()
            
            menu_graph_stats = self.analyze_networkx_graph(menu_graph)
            
            # Step 4: Analyze layout
            try:
                pos = nx.spring_layout(menu_graph, k=3, iterations=50)
                layout_stats = self.analyze_layout_positions(pos)
            except Exception as e:
                self.log(f"Layout creation failed: {e}")
                layout_stats = {}
                
            # Step 5: Analyze edge filtering
            filtered_edges = []
            try:
                # Simulate the filtering process
                menu_choice_edges = set()
                for u, v, data in menu_graph.edges(data=True):
                    if data.get('type') == 'menu_choice':
                        menu_choice_edges.add((u, v))
                        
                filtered_edges = [(u, v) for u, v, data in menu_graph.edges(data=True) 
                                if (u, v) not in menu_choice_edges]
                                
                edge_stats = self.analyze_edge_filtering(menu_graph, filtered_edges)
            except Exception as e:
                self.log(f"Edge filtering analysis failed: {e}")
                edge_stats = {}
                
            # Step 6: Analyze rendering
            rendering_stats = self.analyze_rendering_calls(menu_visualizer)
            
            # Summary
            self.log("=== DIAGNOSIS SUMMARY ===")
            self.log(f"Raw data has {raw_stats.get('labels_with_menus', 0)} labels with menus")
            self.log(f"Graph has {graph_stats.get('menu_nodes', 0)} menu nodes")
            self.log(f"Menu graph has {menu_graph_stats.get('menu_nodes', 0)} menu nodes")
            
            return {
                'raw_stats': raw_stats,
                'graph_stats': graph_stats,
                'menu_graph_stats': menu_graph_stats,
                'layout_stats': layout_stats,
                'edge_stats': edge_stats,
                'rendering_stats': rendering_stats,
                'debug_log': self.debug_output
            }
            
        except Exception as e:
            self.log(f"CRITICAL ERROR in diagnosis: {e}")
            import traceback
            self.log(f"Traceback: {traceback.format_exc()}")
            return {'error': str(e), 'debug_log': self.debug_output}

def main():
    project_path = r"T:\AG\MySisterMyRoommateV1.69-pc\game"
    
    print("Running Visualization Pipeline Diagnostics...")
    print("=" * 50)
    
    diagnostics = VisualizationPipelineDiagnostics(project_path)
    results = diagnostics.run_full_diagnosis()
    
    # Save detailed results
    with open('visualization_diagnosis.json', 'w') as f:
        json.dump(results, f, indent=2)
        
    print("\nDiagnosis complete! Results saved to visualization_diagnosis.json")
    
    # Print key findings
    if 'error' not in results:
        print("\nKEY FINDINGS:")
        print("-" * 30)
        raw_stats = results.get('raw_stats', {})
        graph_stats = results.get('graph_stats', {})
        menu_graph_stats = results.get('menu_graph_stats', {})
        
        print(f"• Raw data: {raw_stats.get('labels_with_menus', 0)} labels with menus")
        print(f"• Standard graph: {graph_stats.get('menu_nodes', 0)} menu nodes")
        print(f"• Menu container graph: {menu_graph_stats.get('menu_nodes', 0)} menu nodes")
        
        if menu_graph_stats.get('menu_nodes', 0) == 0:
            print("❌ PROBLEM: No menu nodes in menu container graph!")
        else:
            print("✅ Menu nodes exist in graph")
            
    else:
        print(f"❌ DIAGNOSIS FAILED: {results['error']}")

if __name__ == "__main__":
    main() 