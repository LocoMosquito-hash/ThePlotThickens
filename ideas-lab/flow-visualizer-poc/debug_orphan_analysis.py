#!/usr/bin/env python3
"""
Debug Orphan Analysis
=====================

Analyze orphan nodes in Sisterly Lust to find commonalities and potential issues.
"""

import sys
import os
from collections import defaultdict, Counter

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_orphan_analysis():
    """Analyze orphan nodes to find patterns and issues."""
    project_path = r"T:\AG\SisterlyLust-v1.2.1-market-GoG\game"
    
    if not os.path.exists(project_path):
        print(f"ERROR: Project path not found: {project_path}")
        return
    
    print("Analyzing orphan nodes in Sisterly Lust...")
    print("=" * 60)
    
    try:
        from renpy_data_adapter import RenpyFlowDataAdapter
        
        # Load the project
        adapter = RenpyFlowDataAdapter()
        
        print("🔄 Loading project data...")
        visualization_data = adapter.analyze_project(project_path)
        
        nodes = visualization_data.nodes
        connections = visualization_data.connections
        
        print(f"✅ Loaded {len(nodes)} nodes, {len(connections)} connections")
        
        # Build connection mapping for analysis
        incoming_connections = defaultdict(list)
        outgoing_connections = defaultdict(list)
        
        for conn in connections:
            source = conn.source_node_id
            target = conn.target_node_id
            
            outgoing_connections[source].append(conn)
            incoming_connections[target].append(conn)
        
        # Find orphan nodes (nodes with no incoming connections)
        orphan_nodes = []
        connected_nodes = []
        
        for node in nodes:
            if node.node_id in incoming_connections and len(incoming_connections[node.node_id]) > 0:
                connected_nodes.append(node)
            else:
                orphan_nodes.append(node)
        
        print(f"\n📊 ORPHAN ANALYSIS:")
        print(f"  Total nodes: {len(nodes)}")
        print(f"  Connected nodes: {len(connected_nodes)}")
        print(f"  Orphan nodes: {len(orphan_nodes)}")
        print(f"  Orphan percentage: {len(orphan_nodes)/len(nodes)*100:.1f}%")
        
        if len(orphan_nodes) == 0:
            print("🎉 No orphan nodes found!")
            return
        
        # Analyze orphan node types
        print(f"\n🔍 ORPHAN NODE TYPES:")
        print("-" * 40)
        orphan_types = Counter(node.node_type for node in orphan_nodes)
        for node_type, count in orphan_types.most_common():
            print(f"  {node_type}: {count}")
        
        # Analyze orphan node names for patterns
        print(f"\n🔍 ORPHAN NAME PATTERNS:")
        print("-" * 40)
        
        # Common prefixes
        prefix_counter = Counter()
        for node in orphan_nodes:
            if '_' in node.node_id:
                prefix = node.node_id.split('_')[0]
                prefix_counter[prefix] += 1
        
        print("Most common prefixes:")
        for prefix, count in prefix_counter.most_common(10):
            print(f"  {prefix}_*: {count} orphans")
        
        # Nodes that end with common suffixes
        suffix_counter = Counter()
        for node in orphan_nodes:
            if '_' in node.node_id:
                suffix = node.node_id.split('_')[-1]
                suffix_counter[suffix] += 1
        
        print("\nMost common suffixes:")
        for suffix, count in suffix_counter.most_common(10):
            print(f"  *_{suffix}: {count} orphans")
        
        # Check for specific problematic patterns
        print(f"\n🚨 POTENTIAL ISSUES:")
        print("-" * 40)
        
        menu_orphans = [node for node in orphan_nodes if 'menu' in node.node_id.lower()]
        choice_orphans = [node for node in orphan_nodes if node.node_type == 'choice_button']
        container_orphans = [node for node in orphan_nodes if node.node_type == 'menu_container']
        
        print(f"Menu-related orphans: {len(menu_orphans)}")
        print(f"Choice button orphans: {len(choice_orphans)}")
        print(f"Menu container orphans: {len(container_orphans)}")
        
        # Show first 20 orphans for analysis
        print(f"\n📋 FIRST 20 ORPHAN NODES:")
        print("-" * 40)
        for i, node in enumerate(orphan_nodes[:20]):
            # Check if this node has outgoing connections
            outgoing_count = len(outgoing_connections.get(node.node_id, []))
            print(f"  {i+1:2d}. {node.node_id} ({node.node_type}) -> {outgoing_count} outgoing")
        
        # Check for nodes that should have parents
        print(f"\n🔍 SUSPICIOUS ORPHANS (should probably have parents):")
        print("-" * 50)
        
        suspicious_orphans = []
        for node in orphan_nodes:
            # Skip the visual start node
            if node.node_id == '__VISUAL_START__':
                continue
            
            # Menu containers should usually have parents
            if node.node_type == 'menu_container':
                suspicious_orphans.append(node)
            
            # Choice buttons should always have container parents
            elif node.node_type == 'choice_button':
                suspicious_orphans.append(node)
            
            # Labels with specific patterns that suggest they're not entry points
            elif node.node_type == 'label':
                if any(pattern in node.node_id.lower() for pattern in [
                    'choice', 'menu', 'post', 'scene', 'conversation', 'visit'
                ]):
                    suspicious_orphans.append(node)
        
        print(f"Found {len(suspicious_orphans)} suspicious orphans:")
        for i, node in enumerate(suspicious_orphans[:15]):
            outgoing_count = len(outgoing_connections.get(node.node_id, []))
            print(f"  {i+1:2d}. {node.node_id} ({node.node_type}) -> {outgoing_count} outgoing")
        
        if len(suspicious_orphans) > 15:
            print(f"  ... and {len(suspicious_orphans) - 15} more")
        
        # Check for connections that might be missing
        print(f"\n🔍 MISSING CONNECTION ANALYSIS:")
        print("-" * 40)
        
        # Look for nodes that might be parents of orphan containers
        potential_parents = defaultdict(list)
        for node in orphan_nodes:
            if node.node_type == 'menu_container':
                # Look for potential parent labels
                base_name = node.node_id.replace('_menu_', '_').replace('_choices', '')
                
                # Find labels that could be parents
                for other_node in nodes:
                    if (other_node.node_type == 'label' and 
                        other_node.node_id in base_name and
                        other_node.node_id != node.node_id):
                        potential_parents[node.node_id].append(other_node.node_id)
        
        if potential_parents:
            print("Orphan containers with potential parents:")
            for orphan_id, parents in list(potential_parents.items())[:10]:
                print(f"  {orphan_id} <- might connect from: {parents}")
        
        # Summary of findings
        print(f"\n📋 SUMMARY OF FINDINGS:")
        print("-" * 30)
        print(f"  Total orphans: {len(orphan_nodes)}")
        print(f"  Suspicious orphans: {len(suspicious_orphans)}")
        print(f"  Menu containers without parents: {len(container_orphans)}")
        print(f"  Choice buttons without parents: {len(choice_orphans)}")
        print(f"  Most common prefix: {prefix_counter.most_common(1)[0] if prefix_counter else 'None'}")
        
        return {
            'total_orphans': len(orphan_nodes),
            'suspicious_orphans': len(suspicious_orphans),
            'container_orphans': len(container_orphans),
            'choice_orphans': len(choice_orphans),
            'orphan_types': dict(orphan_types),
            'prefix_patterns': dict(prefix_counter.most_common(10)),
            'suffix_patterns': dict(suffix_counter.most_common(10))
        }
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    debug_orphan_analysis() 