#!/usr/bin/env python3
"""
Test dreams screen through the full integration pipeline.
Following ISOLATED_TESTING_METHODOLOGY.md
"""
import sys
import codecs
from pathlib import Path

# Fix encoding on Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

def test_dreams_full_pipeline():
    """Test dreams screen through the complete pipeline that the visualizer uses."""
    
    game_path = r"T:\AG\LeavingDNA-EpisodeTwo.2-pc"
    target_screen = "dreams"
    
    print("Testing 'dreams' screen through FULL INTEGRATION pipeline")
    print("=" * 70)
    print(f"Game: {game_path}")
    print(f"Screen: {target_screen}")
    print("=" * 70)
    
    try:
        # Import the actual adapter the visualizer uses
        from renpy_data_adapter import RenpyFlowDataAdapter
        
        print("\n[STEP 1] Creating adapter (use_hybrid=True)...")
        adapter = RenpyFlowDataAdapter(use_hybrid=True)
        
        print("\n[STEP 2] Analyzing project...")
        viz_data = adapter.analyze_project(game_path, use_sdk=False)
        
        print(f"\n[STEP 3] Searching for screen '{target_screen}'...")
        # Find the dreams screen node
        dreams_screen = None
        for node in viz_data.nodes:
            if node.display_name and target_screen in node.display_name and 'Screen:' in node.display_name:
                dreams_screen = node
                print(f"  ✅ Found: {node.display_name}")
                print(f"     Node ID: {node.node_id}")
                print(f"     Metadata: {node.metadata}")
                break
        
        if not dreams_screen:
            print(f"  ❌ Screen '{target_screen}' not found in visualization data")
            return 1
        
        print(f"\n[STEP 4] Finding outgoing connections from dreams screen...")
        outgoing_edges = [e for e in viz_data.edges if e.from_node == dreams_screen.node_id]
        print(f"  Total connections: {len(outgoing_edges)}")
        
        start_actions = []
        call_actions = []
        
        for edge in outgoing_edges:
            target = next((n for n in viz_data.nodes if n.node_id == edge.to_node), None)
            if target:
                dest_label = target.display_name
                edge_type = edge.edge_type
                
                # Check if it's a Start or Call action
                if 'bonus_scene_1' in dest_label or 'bonus_scene_2' in dest_label:
                    action_type = 'Start (expected)'
                    start_actions.append(dest_label)
                else:
                    action_type = 'Call'
                    call_actions.append(dest_label)
                
                print(f"    → {dest_label} ({edge_type}) [{action_type}]")
        
        print(f"\n[STEP 5] ANALYSIS:")
        print(f"  Start actions found: {len(start_actions)} (expected 2)")
        for s in start_actions:
            print(f"    - {s}")
        print(f"  Call actions found: {len(call_actions)} (expected 7)")
        for c in call_actions:
            print(f"    - {c}")
        print(f"  Total: {len(outgoing_edges)} (expected 9)")
        
        if len(outgoing_edges) == 9 and len(start_actions) == 2 and len(call_actions) == 7:
            print(f"\n✅ SUCCESS: All 9 elements with correct actions!")
            return 0
        else:
            print(f"\n❌ FAILED: Missing elements")
            print(f"\n[STEP 6] DEBUGGING - Check CSAP integration...")
            
            # Now test CSAP directly on the extracted content
            print(f"\nTesting with CSAP directly...")
            return test_csap_extraction(game_path)
        
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

def test_csap_extraction(game_path):
    """Test CSAP with the exact content that gets extracted."""
    
    print("\n" + "=" * 70)
    print("[CSAP EXTRACTION TEST]")
    print("=" * 70)
    
    try:
        from csap.csap_integration import extract_screen_content
        from csap.csap_parser import CSAPParser
        from csap.csap_compatibility import convert_csap_to_screen_structure
        
        script_file = Path(game_path) / "game" / "setup" / "bonus_scenes_setup.rpy"
        
        if not script_file.exists():
            print(f"❌ Script file not found: {script_file}")
            return 1
        
        print(f"\n[READING FILE] {script_file}")
        content = script_file.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        # Find the dreams screen
        screen_start = None
        for i, line in enumerate(lines):
            if line.strip().startswith('screen dreams():'):
                screen_start = i
                break
        
        if screen_start is None:
            print(f"❌ dreams screen not found in file")
            return 1
        
        print(f"  Found at line {screen_start + 1}")
        
        # Extract the screen manually (same way integration does it)
        screen_lines = []
        base_indent = len(lines[screen_start]) - len(lines[screen_start].lstrip())
        
        for i in range(screen_start, len(lines)):
            line = lines[i]
            
            # Include the screen definition line
            if i == screen_start:
                screen_lines.append(line)
                continue
            
            # Stop if we hit a line at base indentation (or less) that's not empty
            if line.strip():
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= base_indent:
                    break
            
            screen_lines.append(line)
        
        screen_content = '\n'.join(screen_lines)
        
        print(f"\n[EXTRACTED CONTENT] {len(screen_lines)} lines")
        
        # Save to file for inspection
        debug_file = "debug_extracted_dreams.txt"
        Path(debug_file).write_text(screen_content, encoding='utf-8')
        print(f"  Saved to: {debug_file}")
        
        print(f"\n[PARSING WITH CSAP]")
        parser = CSAPParser()
        screen_node = parser.parse_screen_text(screen_content)
        
        print(f"  Screen name: {screen_node.screen_name}")
        print(f"  Top-level elements: {len(screen_node.elements)}")
        
        interactive = screen_node.get_interactive_elements()
        print(f"  Interactive elements: {len(interactive)}")
        
        start_count = 0
        call_count = 0
        
        for i, elem in enumerate(interactive):
            action_type = elem.action.action_type if elem.action else "None"
            destination = elem.action.destination if elem.action else "N/A"
            
            if action_type == 'Start':
                start_count += 1
            elif action_type == 'Call':
                call_count += 1
            
            print(f"    {i+1}. {type(elem).__name__}: {action_type} -> {destination}")
        
        print(f"\n[CONVERTING TO SCREEN STRUCTURE]")
        screen_structure = convert_csap_to_screen_structure(screen_node, str(script_file))
        print(f"  ScreenStructure elements: {len(screen_structure.elements)}")
        
        print(f"\n[FINAL RESULT]")
        print(f"  Start actions: {start_count} (expected 2)")
        print(f"  Call actions: {call_count} (expected 7)")
        print(f"  Total: {len(interactive)} (expected 9)")
        
        if start_count == 2 and call_count == 7:
            print(f"\n✅ CSAP extraction works correctly!")
            print(f"\n⚠️  BUT the visualizer shows only 7 elements.")
            print(f"\nThis means the issue is in the integration layer AFTER CSAP parses.")
            print(f"Check: renpy_data_adapter.py - how it uses CSAP results")
            return 1
        else:
            print(f"\n❌ CSAP extraction also fails!")
            print(f"\nInspect {debug_file} to see what was extracted.")
            return 1
        
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_dreams_full_pipeline())

