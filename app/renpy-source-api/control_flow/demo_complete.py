#!/usr/bin/env python3
"""
Complete Demo: StartLabelFinder + FlowTracer
Showcasing the full control flow analysis capabilities.
"""

import sys
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from app.renpy_source_api.control_flow import StartLabelFinder, FlowTracer
    print("✅ Successfully imported control flow analysis components")
except ImportError:
    # Fallback for standalone usage
    import sys
    sys.path.append('..')
    from start_label_finder import StartLabelFinder
    from flow_tracer import FlowTracer
    print("✅ Successfully imported control flow components (standalone)")


def analyze_vn_narrative_flow(project_path: str, max_steps: int = 25):
    """
    Complete narrative flow analysis of a VN project.
    
    Args:
        project_path: Path to Ren'Py project
        max_steps: Maximum flow steps to trace
    """
    print(f"🎮 Analyzing VN Narrative Flow")
    print(f"📁 Project: {project_path}")
    print("=" * 60)
    
    try:
        # Stage 1: Find Entry Point
        print("🔍 Stage 1: Finding Story Entry Point...")
        start_finder = StartLabelFinder(project_path)
        start_location = start_finder.get_start_location()
        project_info = start_finder.get_project_info()
        
        print(f"  ✅ Entry point: {start_location[0]}:{start_location[1]}")
        print(f"  📊 Project: {project_info['total_rpy_files']} .rpy files")
        
        # Stage 2: Trace Narrative Flow
        print(f"\n🚀 Stage 2: Tracing Narrative Flow...")
        tracer = FlowTracer(project_path)
        flow_result = tracer.trace_flow(max_steps)
        flow_summary = tracer.get_flow_summary(flow_result)
        
        print(f"  ✅ Traced: {flow_result.total_lines_traced} steps")
        print(f"  🛑 Stopped: {flow_result.stop_reason}")
        
        if flow_result.flow_control_encountered:
            print(f"  🔄 Flow control: {flow_result.flow_control_encountered}")
        
        # Stage 3: Narrative Analysis
        print(f"\n📈 Stage 3: Narrative Analysis...")
        dialogue_lines = flow_summary['dialogue_lines']
        characters = set()
        
        # Extract character information
        for step in flow_result.steps:
            if step.statement_type == 'character_dialogue' and step.parsed_data:
                characters.add(step.parsed_data.get('character', 'unknown'))
        
        print(f"  💬 Dialogue lines: {dialogue_lines}")
        print(f"  👥 Characters introduced: {len(characters)}")
        if characters:
            print(f"     Characters: {', '.join(sorted(characters))}")
        
        print(f"  🎭 Statement types: {len(flow_summary['statement_counts'])}")
        for stmt_type, count in flow_summary['statement_counts'].items():
            print(f"     {stmt_type}: {count}")
        
        # Stage 4: Opening Sequence Preview
        print(f"\n📝 Stage 4: Opening Sequence Preview...")
        print("First 10 steps of the narrative:")
        
        for i, step in enumerate(flow_result.steps[:10]):
            # Format content preview
            content = step.content[:50] + "..." if len(step.content) > 50 else step.content
            step_info = f"[{step.statement_type}]"
            
            # Add character info for dialogue
            if step.statement_type == 'character_dialogue' and step.parsed_data:
                step_info += f" {step.parsed_data['character']}:"
            
            print(f"  {i+1:2}. Line {step.line_number}: {step_info} {content}")
        
        if len(flow_result.steps) > 10:
            print(f"     ... and {len(flow_result.steps) - 10} more steps")
        
        # Summary
        print(f"\n🎯 Analysis Complete!")
        complexity = "Simple" if len(flow_summary['statement_counts']) <= 3 else "Complex"
        print(f"   Narrative complexity: {complexity}")
        print(f"   Ready for deeper analysis: Jump following, branch mapping, etc.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False


def demo_multiple_vns():
    """Demo the control flow analysis on multiple VN projects."""
    # Test projects (adjust paths as needed)
    test_projects = [
        r"T:\AG\Tune in to the Show Episode 6-v0.6-market-STEAM",
        r"T:\AG\TheAlphaGender-0.3b-pc", 
        r"T:\AG\AlisonFalloftheApple-1.0-pc",
    ]
    
    print("🌟 Multi-VN Control Flow Analysis Demo")
    print("=" * 70)
    
    successful = 0
    total = len(test_projects)
    
    for i, project_path in enumerate(test_projects):
        print(f"\n📁 VN {i+1}/{total}: {Path(project_path).name}")
        print("-" * 50)
        
        if Path(project_path).exists():
            success = analyze_vn_narrative_flow(project_path, max_steps=15)
            if success:
                successful += 1
        else:
            print(f"⚠️  Project path not found: {project_path}")
        
        if i < total - 1:  # Not the last project
            print("\n" + "🔄" + " " * 60)
    
    # Final summary
    print(f"\n{'='*70}")
    print(f"🏆 DEMO SUMMARY")
    print(f"{'='*70}")
    print(f"Projects analyzed: {total}")
    print(f"Successful analyses: {successful}")
    print(f"Success rate: {successful/total*100:.1f}%")
    print(f"\n✨ Control flow analysis system ready for production use!")


def main():
    """Main demo function."""
    print("🎯 StartLabelFinder + FlowTracer Complete Demo")
    print("🚀 Ren'Py Control Flow Analysis System")
    print()
    
    # Check if user provided a specific project path
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
        print(f"🎮 Single Project Analysis Mode")
        analyze_vn_narrative_flow(project_path)
    else:
        print(f"🎮 Multi-Project Demo Mode")
        demo_multiple_vns()


if __name__ == "__main__":
    main() 