#!/usr/bin/env python3
"""
Diagnostic Script for SisterlyLust Flow Visualizer Issues
========================================================

This script logs detailed information about node creation and edge formation
for the specific case of SisterlyLust VN, focusing on:

1. Why "Go to the living room" choice is orange instead of lightblue
2. Why day02_living_room_conversation appears as orphan instead of child
3. How label menus are being processed

Issues to investigate:
- day02_l_conversation -> day02_p_room_choices (parent/child)
- day02_p_room_choices -> "Go to the living room" choice (container/choice)  
- "Go to the living room" choice -> day02_living_room_conversation (choice/child menu)
"""

import sys
import os
import json
import importlib.util
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from renpy_data_adapter import RenpyFlowDataAdapter
try:
    from control_flow.analyze_vn_menus import MenuAnalyzer
except ImportError:
    # Fallback if direct import fails
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "analyze_vn_menus", 
        os.path.join(project_root, "app", "renpy-source-api", "control_flow", "analyze_vn_menus.py")
    )
    analyze_vn_menus = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(analyze_vn_menus)
    MenuAnalyzer = analyze_vn_menus.MenuAnalyzer

class SisterlyLustDiagnostic:
    """Diagnostic tool for SisterlyLust flow visualization issues."""
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.log_file = f"diagnostic_sisterly_lust_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # Focus nodes for detailed logging
        self.focus_nodes = [
            "day02_l_conversation",
            "day02_p_room_choices", 
            "day02_living_room_conversation",
            "day02_p_room_choices_menu_0",
            "day02_p_room_choices_menu_0_choice_0"  # "Go to the living room"
        ]
        
        # Initialize logging
        self.log_data = {
            "timestamp": datetime.now().isoformat(),
            "project_path": project_path,
            "focus_investigation": "day02 path - orange choice and missing child relationship",
            "issues": [
                "Why is 'Go to the living room' choice orange instead of lightblue?",
                "Why is day02_living_room_conversation orphaned instead of child?",
                "How are label menus being processed?"
            ],
            "menu_detection": {},
            "node_creation": {},
            "edge_creation": {},
            "color_assignments": {},
            "hierarchy_analysis": {},
            "orphan_detection": {}
        }
    
    def log(self, category: str, message: str, data: Any = None):
        """Log information to both console and log data."""
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        log_entry = f"[{timestamp}] [{category}] {message}"
        
        print(log_entry)
        
        if category not in self.log_data:
            self.log_data[category] = []
        
        entry = {
            "timestamp": timestamp,
            "message": message,
            "data": data
        }
        self.log_data[category].append(entry)
    
    def analyze_menu_detection(self):
        """Analyze how menus are detected in day02.rpy."""
        self.log("MENU_DETECTION", "Starting menu detection analysis for day02.rpy")
        
        try:
            analyzer = MenuAnalyzer()
            day02_file = os.path.join(self.project_path, "day02.rpy")
            
            if not os.path.exists(day02_file):
                self.log("MENU_DETECTION", f"ERROR: day02.rpy not found at {day02_file}")
                return
            
            # Use the correct method signature - pass Path object only
            menus_data = analyzer._analyze_file_menus(Path(day02_file))
            menus = menus_data.get('menus', [])
            
            self.log("MENU_DETECTION", f"Found {len(menus)} menus in day02.rpy")
            
            # Focus on specific menus
            for menu in menus:
                if any(focus in str(menu.label_name) for focus in ["day02_p_room_choices", "day02_living_room_conversation"]):
                    self.log("MENU_DETECTION", f"FOCUS MENU: {menu.label_name}")
                    self.log("MENU_DETECTION", f"  - Line: {menu.line_number}")
                    self.log("MENU_DETECTION", f"  - Choices: {len(menu.choices)}")
                    self.log("MENU_DETECTION", f"  - Nesting Level: {menu.nesting_level}")
                    self.log("MENU_DETECTION", f"  - Label Context: {menu.label_context}")
                    
                    for i, choice in enumerate(menu.choices):
                        if "living room" in choice.text.lower():
                            self.log("MENU_DETECTION", f"  - FOCUS CHOICE {i}: '{choice.text}'")
                            self.log("MENU_DETECTION", f"    - Condition: {choice.condition}")
                            self.log("MENU_DETECTION", f"    - Destination: {choice.destination}")
                            self.log("MENU_DETECTION", f"    - Has Condition: {choice.has_condition}")
                            
                            # This should reveal why it's getting orange color
                            color_hint = 'lightblue' if not choice.condition else 'orange'
                            self.log("COLOR_DETECTION", f"Choice '{choice.text}' gets color: {color_hint}")
                            self.log("COLOR_DETECTION", f"  - Reason: condition={choice.condition}")
            
            self.log_data["menu_detection"]["day02_menus"] = [
                {
                    "label_name": menu.label_name,
                    "line_number": menu.line_number,
                    "choices_count": len(menu.choices),
                    "nesting_level": menu.nesting_level,
                    "choices": [
                        {
                            "text": choice.text,
                            "condition": choice.condition,
                            "destination": choice.destination,
                            "has_condition": choice.has_condition
                        } for choice in menu.choices
                    ]
                } for menu in menus
            ]
            
        except Exception as e:
            self.log("MENU_DETECTION", f"ERROR: {str(e)}")
    
    def analyze_flow_graph_creation(self):
        """Analyze the flow graph creation process."""
        self.log("FLOW_GRAPH", "Starting flow graph analysis")
        
        try:
            adapter = RenpyFlowDataAdapter(use_hybrid=True)
            
            # Hook into the label-to-nodes conversion to log relevant info
            original_method = adapter._convert_labels_to_nodes
            
            def logged_convert_labels_to_nodes(flow_graph, actual_entry_point):
                nodes = original_method(flow_graph, actual_entry_point)
                
                for node in nodes:
                    if any(focus in node.node_id for focus in self.focus_nodes):
                        self.log("NODE_CREATION", f"FOCUS LABEL NODE: {node.node_id}")
                        self.log("NODE_CREATION", f"  - Type: {node.node_type}")
                        self.log("NODE_CREATION", f"  - Color Hint: {node.color_hint}")
                        self.log("NODE_CREATION", f"  - Metadata: {node.metadata}")
                
                return nodes
            
            adapter._convert_labels_to_nodes = logged_convert_labels_to_nodes
            
            # Hook into menu container creation
            original_menu_method = adapter._create_menu_containers
            
            def logged_create_menu_containers(flow_graph):
                container_nodes, choice_connections = original_menu_method(flow_graph)
                
                self.log("MENU_CONTAINERS", f"Created {len(container_nodes)} menu-related nodes")
                
                for node in container_nodes:
                    if any(focus in node.node_id for focus in self.focus_nodes + ["living_room", "room_choices"]):
                        self.log("NODE_CREATION", f"FOCUS MENU NODE: {node.node_id}")
                        self.log("NODE_CREATION", f"  - Type: {node.node_type}")
                        self.log("NODE_CREATION", f"  - Color Hint: {node.color_hint}")
                        self.log("NODE_CREATION", f"  - Display Name: {node.display_name}")
                        self.log("NODE_CREATION", f"  - Metadata: {node.metadata}")
                        
                        # Special logging for the orange choice issue
                        if node.node_type == 'choice_button' and "living room" in node.display_name.lower():
                            self.log("ORANGE_CHOICE_DEBUG", f"FOUND THE ORANGE CHOICE!")
                            self.log("ORANGE_CHOICE_DEBUG", f"  - ID: {node.node_id}")
                            self.log("ORANGE_CHOICE_DEBUG", f"  - Color: {node.color_hint}")
                            self.log("ORANGE_CHOICE_DEBUG", f"  - Condition: {node.metadata.get('condition')}")
                            self.log("ORANGE_CHOICE_DEBUG", f"  - Has Condition: {node.metadata.get('has_condition')}")
                
                self.log("CHOICE_CONNECTIONS", f"Created {len(choice_connections)} choice connections")
                
                for conn in choice_connections:
                    if any(focus in conn.source_node_id or focus in conn.target_node_id for focus in self.focus_nodes + ["living_room"]):
                        self.log("EDGE_CREATION", f"FOCUS CONNECTION: {conn.source_node_id} -> {conn.target_node_id}")
                        self.log("EDGE_CREATION", f"  - Type: {conn.connection_type}")
                        self.log("EDGE_CREATION", f"  - Color: {conn.color_hint}")
                        self.log("EDGE_CREATION", f"  - Label: {conn.label}")
                
                return container_nodes, choice_connections
            
            adapter._create_menu_containers = logged_create_menu_containers
            
            # Now analyze the project
            visualization_data = adapter.analyze_project(self.project_path)
            
            self.log("ANALYSIS_COMPLETE", f"Total nodes: {len(visualization_data.nodes)}")
            self.log("ANALYSIS_COMPLETE", f"Total connections: {len(visualization_data.connections)}")
            
            # Check for orphan nodes
            nodes_with_incoming = set()
            for conn in visualization_data.connections:
                nodes_with_incoming.add(conn.target_node_id)
            
            orphan_nodes = [node for node in visualization_data.nodes if node.node_id not in nodes_with_incoming and node.node_id != "__VISUAL_START__"]
            
            self.log("ORPHAN_ANALYSIS", f"Found {len(orphan_nodes)} orphan nodes")
            
            for node in orphan_nodes:
                if any(focus in node.node_id for focus in self.focus_nodes + ["living_room"]):
                    self.log("ORPHAN_ANALYSIS", f"FOCUS ORPHAN: {node.node_id}")
                    self.log("ORPHAN_ANALYSIS", f"  - Type: {node.node_type}")
                    self.log("ORPHAN_ANALYSIS", f"  - Display: {node.display_name}")
            
            # Store detailed analysis
            self.log_data["final_analysis"] = {
                "total_nodes": len(visualization_data.nodes),
                "total_connections": len(visualization_data.connections),
                "orphan_count": len(orphan_nodes),
                "focus_nodes_found": [node.node_id for node in visualization_data.nodes if any(focus in node.node_id for focus in self.focus_nodes)]
            }
            
        except Exception as e:
            self.log("FLOW_GRAPH", f"ERROR: {str(e)}")
    
    def save_log(self):
        """Save the diagnostic log to file."""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(self.log_data, f, indent=2, ensure_ascii=False)
            
            self.log("SAVE", f"Diagnostic log saved to {self.log_file}")
            
            # Also create a summary report
            summary_file = f"diagnostic_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("SISTERLY LUST DIAGNOSTIC SUMMARY\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Project Path: {self.project_path}\n")
                f.write(f"Analysis Time: {self.log_data['timestamp']}\n\n")
                
                f.write("KEY FINDINGS:\n")
                f.write("-" * 20 + "\n")
                
                # Check if we found the orange choice
                orange_entries = [entry for entry in self.log_data.get('ORANGE_CHOICE_DEBUG', []) if 'FOUND THE ORANGE CHOICE' in entry['message']]
                if orange_entries:
                    f.write("✅ FOUND the orange choice issue\n")
                else:
                    f.write("❌ Did NOT find the orange choice\n")
                
                # Check orphan status
                orphan_entries = [entry for entry in self.log_data.get('ORPHAN_ANALYSIS', []) if 'living_room' in entry['message']]
                if orphan_entries:
                    f.write("✅ FOUND living_room related orphan nodes\n")
                else:
                    f.write("❌ Did NOT find living_room orphan issues\n")
                
                f.write(f"\nFull diagnostic data: {self.log_file}\n")
            
            self.log("SAVE", f"Summary report saved to {summary_file}")
            
        except Exception as e:
            self.log("SAVE", f"ERROR saving log: {str(e)}")

def main():
    """Run the diagnostic analysis."""
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    print("🔍 SISTERLY LUST DIAGNOSTIC ANALYSIS")
    print("=" * 50)
    print(f"Project Path: {project_path}")
    print(f"Focus: day02 path issues")
    print()
    
    diagnostic = SisterlyLustDiagnostic(project_path)
    
    # Run analysis phases
    diagnostic.analyze_menu_detection()
    print()
    diagnostic.analyze_flow_graph_creation()
    print()
    diagnostic.save_log()
    
    print("\n🎯 Diagnostic complete! Check the log files for detailed analysis.")

if __name__ == "__main__":
    main() 