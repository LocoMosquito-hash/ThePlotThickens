#!/usr/bin/env python3
"""
Route 1 Investigation: Container ID Generation Logic Debugging

This script specifically targets the nested container ID generation logic
in renpy_data_adapter.py lines 477-514 to understand the rogue node issue
in Haley's Story ep2cont5.
"""

import sys
from pathlib import Path
import json

# Add renpy-source-api to path
current_dir = Path(__file__).parent
app_dir = current_dir.parent.parent / "app"
sys.path.insert(0, str(app_dir / "renpy-source-api"))

try:
    from renpy_data_adapter import RenpyFlowDataAdapter
    from control_flow.analyze_vn_menus import MenuAnalyzer
    from parser import RenpyParser
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

class ContainerIDDebugger:
    """Debug the container ID generation logic for nested menus."""
    
    def __init__(self):
        self.adapter = RenpyFlowDataAdapter(use_hybrid=True)
        self.menu_analyzer = MenuAnalyzer()
        self.parser = RenpyParser()
        
    def debug_haley_ep2cont5(self, game_path: str):
        """Debug the specific ep2cont5 label that shows rogue nodes."""
        print("🔍 Route 1 Investigation: Container ID Generation Logic")
        print("=" * 60)
        print(f"Target Game: {game_path}")
        print(f"Target Label: ep2cont5")
        print()
        
        # Step 1: Get raw menu analysis for ep2cont5
        print("📋 Step 1: Raw Menu Analysis")
        print("-" * 30)
        
        analysis = self.menu_analyzer.analyze_vn_menus(game_path)
        ep2cont5_menus = []
        
        for menu_struct in analysis.get('menu_structures', []):
            if menu_struct.label_context == 'ep2cont5':
                ep2cont5_menus.append(menu_struct)
                print(f"Found menu in ep2cont5:")
                print(f"  File: {menu_struct.file_path}")
                print(f"  Line: {menu_struct.line_number}")
                print(f"  Nesting Level: {menu_struct.nesting_level}")
                print(f"  Choices: {len(menu_struct.choices)}")
                
                for i, choice in enumerate(menu_struct.choices):
                    print(f"    Choice {i}: '{choice.text}'")
                    print(f"      Has nested menu: {choice.nested_menu}")
                    print(f"      Nested structures: {len(choice.nested_menu_structures)}")
                    if choice.nested_menu_structures:
                        for nested in choice.nested_menu_structures:
                            print(f"        Nested menu nesting_level: {nested.nesting_level}")
                            print(f"        Nested menu choices: {len(nested.choices)}")
                print()
        
        if not ep2cont5_menus:
            print("❌ No menus found in ep2cont5!")
            return
            
        # Step 2: Build flow graph to see raw parsed structure
        print("📋 Step 2: Flow Graph Analysis")
        print("-" * 30)
        
        flow_graph = self.parser.build_flow_graph(game_path)
        
        # Find ep2cont5 related entries
        ep2cont5_entries = {}
        for label_name, label_data in flow_graph.get('labels', {}).items():
            if 'ep2cont5' in label_name:
                ep2cont5_entries[label_name] = label_data
                
        print(f"Found {len(ep2cont5_entries)} ep2cont5-related labels:")
        for label_name in ep2cont5_entries.keys():
            print(f"  - {label_name}")
        print()
        
        # Find menu nodes related to ep2cont5
        ep2cont5_menu_nodes = {}
        for node_id, node_data in flow_graph.get('menu_nodes', {}).items():
            if 'ep2cont5' in node_id:
                ep2cont5_menu_nodes[node_id] = node_data
                
        print(f"Found {len(ep2cont5_menu_nodes)} ep2cont5 menu nodes:")
        for node_id, node_data in ep2cont5_menu_nodes.items():
            print(f"  - {node_id}")
            print(f"    Type: {node_data.get('menu_type', 'unknown')}")
            print(f"    Nesting Level: {node_data.get('nesting_level', 0)}")
            print(f"    Parent Menu ID: {node_data.get('parent_menu_id', 'none')}")
            print()
        
        # Step 3: Trace the container ID generation process
        print("🔍 Step 3: Container ID Generation Tracing")
        print("-" * 40)
        
        self._trace_container_generation(flow_graph, 'ep2cont5')
        
    def _trace_container_generation(self, flow_graph: dict, label_name: str):
        """Trace the exact container ID generation logic."""
        
        # Extract menu nodes for this label
        label_menu_nodes = []
        nested_menus = []
        
        for node_id, node_data in flow_graph.get('menu_nodes', {}).items():
            if node_data.get('parent_label') == label_name:
                if node_data.get('nesting_level', 0) == 0:
                    label_menu_nodes.append((node_id, node_data))
                else:
                    nested_menus.append((node_id, node_data))
        
        print(f"Label: {label_name}")
        print(f"Top-level menus: {len(label_menu_nodes)}")
        print(f"Nested menus: {len(nested_menus)}")
        print()
        
        # Simulate the container ID generation for top-level menus
        print("🔧 Top-level Menu Container Generation:")
        for menu_idx, (node_id, node_data) in enumerate(label_menu_nodes):
            container_id = f"{label_name}_menu_{menu_idx}"
            print(f"  Original node_id: {node_id}")
            print(f"  Generated container_id: {container_id}")
            print(f"  Menu type: {node_data.get('menu_type', 'unknown')}")
            print()
        
        # Simulate the PROBLEMATIC nested container ID generation
        print("🚨 Nested Menu Container Generation (PROBLEMATIC LOGIC):")
        for node_id, node_data in nested_menus:
            print(f"  Original nested_menu.node_id: {node_id}")
            
            # This is the EXACT logic from line 480 that might be problematic
            replacement_pattern = label_name + "_"
            replacement_target = f"{label_name}_nested_"
            nested_container_id = node_id.replace(replacement_pattern, replacement_target)
            
            print(f"  Pattern to replace: '{replacement_pattern}'")
            print(f"  Replacement target: '{replacement_target}'")
            print(f"  Generated nested_container_id: {nested_container_id}")
            
            # Check if this creates the rogue pattern
            if 'nested_menu_1' in nested_container_id and 'choice_1' not in nested_container_id:
                print(f"  ⚠️  POTENTIAL ROGUE NODE: {nested_container_id}")
            
            print(f"  Nesting level: {node_data.get('nesting_level', 0)}")
            print(f"  Parent menu ID: {node_data.get('parent_menu_id', 'none')}")
            print()
            
        # Step 4: Check for pattern conflicts
        print("🔍 Pattern Conflict Analysis:")
        self._analyze_pattern_conflicts(flow_graph, label_name)
        
    def _analyze_pattern_conflicts(self, flow_graph: dict, label_name: str):
        """Analyze potential naming pattern conflicts."""
        
        all_node_ids = []
        
        # Collect all node IDs related to this label
        for node_id, node_data in flow_graph.get('menu_nodes', {}).items():
            if label_name in node_id:
                all_node_ids.append(node_id)
                
        print(f"All {label_name} related node IDs:")
        for node_id in sorted(all_node_ids):
            print(f"  - {node_id}")
            
        # Check for suspicious patterns
        suspicious_patterns = []
        for node_id in all_node_ids:
            if 'nested_menu_1' in node_id and 'choice_1' not in node_id:
                suspicious_patterns.append(node_id)
                
        if suspicious_patterns:
            print(f"\n🚨 Suspicious rogue patterns found:")
            for pattern in suspicious_patterns:
                print(f"  - {pattern} (likely rogue node)")
        else:
            print(f"\n✅ No obvious rogue patterns detected")

def main():
    """Run the container ID generation debugging."""
    
    game_path = "F:\\Bin\\Games\\Haley-1.1-alt-pc\\game"
    
    debugger = ContainerIDDebugger()
    debugger.debug_haley_ep2cont5(game_path)

if __name__ == "__main__":
    main()