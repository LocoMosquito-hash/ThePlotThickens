#!/usr/bin/env python3
"""
Test FlowTracer against real VN projects to validate practical functionality.
"""

import sys
import os
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from control_flow.flow_tracer import FlowTracer, FlowTraceResult
    from control_flow.start_label_finder import StartLabelNotFoundError
    from exceptions import RenpyProjectError, RenpyParseError
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the correct directory")
    sys.exit(1)


# Sample of VN projects for testing (smaller ones first)
VN_TEST_PROJECTS = {
    # Small projects - good for initial testing
    "TuneInToTheShow": r"T:\AG\Tune in to the Show Episode 6-v0.6-market-STEAM",
    "Tropicali": r"T:\AG\Tropicali_Demo-0.6d-pc", 
    "TheAlphaGender": r"T:\AG\TheAlphaGender-0.3b-pc",
    
    # Medium projects 
    "MySisterMyRoommate": r"T:\AG\MySisterMyRoommateV1.69-pc",
    "AlisonFalloftheApple": r"T:\AG\AlisonFalloftheApple-1.0-pc",
    "BrightonCityEmpire": r"T:\AG\BrightonCityEmpire-0.04-pc",
    
    # Larger projects
    "LastCall": r"T:\AG\LastCall-0.4-pc",
    "Savior": r"T:\AG\Savior-0.16c-pc",
}


class VNFlowTestResult:
    """Results from testing FlowTracer on a VN project."""
    
    def __init__(self, name: str, path: str):
        self.name = name
        self.path = path
        self.exists = False
        self.has_start_label = False
        self.start_location: Optional[Tuple[str, int]] = None
        self.flow_result: Optional[FlowTraceResult] = None
        self.error: Optional[str] = None
        self.trace_time: Optional[float] = None


def test_flow_tracer_on_vn(name: str, path: str, max_steps: int = 50) -> VNFlowTestResult:
    """
    Test FlowTracer on a single VN project.
    
    Args:
        name: Name of the VN
        path: Path to the VN project
        max_steps: Maximum steps to trace
        
    Returns:
        VNFlowTestResult with results
    """
    result = VNFlowTestResult(name, path)
    
    # Check if path exists
    if not os.path.exists(path):
        result.error = "Path does not exist"
        return result
    
    result.exists = True
    
    try:
        start_time = time.time()
        
        # Create FlowTracer
        tracer = FlowTracer(path)
        result.has_start_label = True
        result.start_location = tracer.start_location
        
        # Trace flow
        flow_result = tracer.trace_flow(max_steps)
        result.flow_result = flow_result
        
        result.trace_time = time.time() - start_time
        
    except StartLabelNotFoundError as e:
        result.error = f"No start label: {str(e)}"
        result.trace_time = time.time() - start_time
        
    except RenpyProjectError as e:
        result.error = f"Project error: {str(e)}"
        
    except Exception as e:
        result.error = f"Unexpected error: {str(e)}"
    
    return result


def analyze_flow_result(flow_result: FlowTraceResult) -> Dict[str, Any]:
    """Analyze a flow trace result and return insights."""
    if not flow_result:
        return {}
    
    # Count statement types
    statement_counts = {}
    dialogue_lines = 0
    characters_seen = set()
    
    for step in flow_result.steps:
        stmt_type = step.statement_type
        statement_counts[stmt_type] = statement_counts.get(stmt_type, 0) + 1
        
        if stmt_type in ['dialogue', 'character_dialogue']:
            dialogue_lines += 1
            
        if stmt_type == 'character_dialogue' and step.parsed_data:
            characters_seen.add(step.parsed_data.get('character', 'unknown'))
    
    return {
        'total_steps': len(flow_result.steps),
        'stop_reason': flow_result.stop_reason,
        'flow_control_encountered': flow_result.flow_control_encountered,
        'dialogue_lines': dialogue_lines,
        'characters_introduced': len(characters_seen),
        'character_names': list(characters_seen),
        'statement_counts': statement_counts,
        'narrative_complexity': 'simple' if len(statement_counts) <= 3 else 'complex'
    }


def print_flow_analysis(result: VNFlowTestResult):
    """Print detailed analysis of a flow trace result."""
    print(f"\n=== {result.name} ===")
    print(f"Path: {result.path}")
    
    if not result.exists:
        print("❌ Project path not found")
        return
    
    if not result.has_start_label:
        print(f"⚠️  {result.error}")
        return
    
    if not result.flow_result:
        print(f"❌ Flow tracing failed: {result.error}")
        return
    
    flow = result.flow_result
    analysis = analyze_flow_result(flow)
    
    if result.start_location:
        print(f"✅ Start: {result.start_location[0]}:{result.start_location[1]}")
    if result.trace_time is not None:
        print(f"📊 Traced {analysis['total_steps']} steps in {result.trace_time:.3f}s")
    print(f"🛑 Stop reason: {analysis['stop_reason']}")
    
    if analysis['flow_control_encountered']:
        print(f"🔄 Flow control: {analysis['flow_control_encountered']}")
    
    print(f"💬 Dialogue lines: {analysis['dialogue_lines']}")
    
    if analysis['characters_introduced'] > 0:
        print(f"👥 Characters: {', '.join(analysis['character_names'])}")
    
    print(f"📈 Complexity: {analysis['narrative_complexity']}")
    
    # Show first few steps
    print(f"\n📝 Opening sequence:")
    for i, step in enumerate(flow.steps[:5]):
        content_preview = step.content[:60] + "..." if len(step.content) > 60 else step.content
        print(f"  {i+1}. [{step.statement_type}] {content_preview}")
    
    if len(flow.steps) > 5:
        print(f"  ... and {len(flow.steps) - 5} more steps")


def test_priority_vns():
    """Test FlowTracer on a selection of VN projects."""
    print("🎮 Testing FlowTracer on Real VN Projects")
    print("=" * 60)
    
    results = []
    
    for name, path in list(VN_TEST_PROJECTS.items())[:5]:  # Test first 5
        print(f"\nTesting {name}...")
        result = test_flow_tracer_on_vn(name, path, max_steps=30)
        results.append(result)
        
        if result.flow_result:
            analysis = analyze_flow_result(result.flow_result)
            print(f"  ✅ {analysis['total_steps']} steps, {analysis['dialogue_lines']} dialogue lines")
        else:
            print(f"  ❌ {result.error}")
    
    # Print detailed analysis
    print("\n" + "=" * 60)
    print("DETAILED FLOW ANALYSIS")
    print("=" * 60)
    
    for result in results:
        print_flow_analysis(result)
    
    return results


def main():
    """Main function to run FlowTracer tests."""
    try:
        results = test_priority_vns()
        
        # Summary
        successful = [r for r in results if r.flow_result is not None]
        print(f"\n📈 SUMMARY:")
        print(f"Projects tested: {len(results)}")
        print(f"Successful traces: {len(successful)}")
        print(f"Success rate: {len(successful)/len(results)*100:.1f}%")
        
        if successful:
            avg_steps = sum(len(r.flow_result.steps) for r in successful) / len(successful)
            avg_time = sum(r.trace_time for r in successful) / len(successful)
            print(f"Average steps traced: {avg_steps:.1f}")
            print(f"Average trace time: {avg_time:.3f}s")
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 