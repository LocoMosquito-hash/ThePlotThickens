#!/usr/bin/env python3
"""
Test Jump Following functionality against real VN projects.

This script tests our newly implemented Simple Jump Following feature
against a collection of real decompiled Ren'Py visual novels to validate
that it works correctly with real-world projects.
"""

import sys
import os
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from collections import defaultdict

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


# VN Projects optimized for jump testing (medium-small for faster testing)
JUMP_TEST_VNS = {
    # Small/Quick VNs - Good for initial testing
    "TuneInToTheShow": r"T:\AG\Tune in to the Show Episode 6-v0.6-market-STEAM",
    "Tropicali": r"T:\AG\Tropicali_Demo-0.6d-pc", 
    "TheAlphaGender": r"T:\AG\TheAlphaGender-0.3b-pc",
    
    # Medium VNs - Good balance of content and speed
    "MySisterMyRoommate": r"T:\AG\MySisterMyRoommateV1.69-pc",
    "AlisonFalloftheApple": r"T:\AG\AlisonFalloftheApple-1.0-pc",
    "BrightonCityEmpire": r"T:\AG\BrightonCityEmpire-0.04-pc",
    
    # Larger VNs - Comprehensive testing
    "LastCall": r"T:\AG\LastCall-0.4-pc",
    "Savior": r"T:\AG\Savior-0.16c-pc",
}


class JumpTestResult:
    """Results from testing jump following on a VN project."""
    
    def __init__(self, name: str, path: str):
        self.name = name
        self.path = path
        
        # Basic validation
        self.exists = False
        self.has_start_label = False
        self.error: Optional[str] = None
        
        # Flow trace results
        self.flow_result: Optional[FlowTraceResult] = None
        self.trace_time: Optional[float] = None
        
        # Jump-specific analysis
        self.jump_statistics = {
            'total_jumps_found': 0,
            'jumps_followed': 0,
            'jumps_failed': 0,
            'unique_jump_targets': set(),
            'cross_file_jumps': 0,
            'infinite_loops_prevented': 0,
            'jump_target_not_found': 0
        }
        
        # Flow analysis
        self.flow_statistics = {
            'total_steps': 0,
            'dialogue_lines': 0,
            'labels_visited': 0,
            'files_traced': set(),
            'stop_reason': None,
            'flow_control_encountered': None
        }


def analyze_jump_patterns(result: FlowTraceResult) -> Dict[str, Any]:
    """
    Analyze jump patterns and statistics from a flow trace result.
    
    Args:
        result: FlowTraceResult from tracing
        
    Returns:
        Dictionary with detailed jump analysis
    """
    jump_analysis = {
        'total_jumps': 0,
        'jump_targets': [],
        'jump_success_rate': 0.0,
        'average_jump_distance': 0.0,
        'cross_file_jumps': 0,
        'files_involved': set(),
        'jump_chains': [],  # Sequences of jumps
        'most_common_targets': {},
    }
    
    jump_targets = []
    current_chain = []
    target_counts = defaultdict(int)
    
    for i, step in enumerate(result.steps):
        jump_analysis['files_involved'].add(step.file_path)
        
        if step.statement_type == 'jump':
            jump_analysis['total_jumps'] += 1
            
            # Extract jump target from parsed data
            if step.parsed_data and 'target' in step.parsed_data:
                target = step.parsed_data['target']
                jump_targets.append(target)
                target_counts[target] += 1
                current_chain.append(target)
                
                # Check if this is a cross-file jump by looking at next step
                if i + 1 < len(result.steps):
                    next_step = result.steps[i + 1]
                    if next_step.file_path != step.file_path:
                        jump_analysis['cross_file_jumps'] += 1
            else:
                # Chain broken
                if current_chain:
                    jump_analysis['jump_chains'].append(current_chain.copy())
                    current_chain = []
    
    # Final chain
    if current_chain:
        jump_analysis['jump_chains'].append(current_chain)
    
    # Calculate statistics
    jump_analysis['jump_targets'] = jump_targets
    jump_analysis['jump_success_rate'] = (
        len(jump_targets) / max(jump_analysis['total_jumps'], 1) * 100
    )
    jump_analysis['most_common_targets'] = dict(sorted(
        target_counts.items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:5])
    
    return jump_analysis


def test_jump_following_on_vn(name: str, path: str, max_steps: int = 100) -> JumpTestResult:
    """
    Test jump following functionality on a single VN project.
    
    Args:
        name: Name of the VN
        path: Path to the VN project
        max_steps: Maximum steps to trace
        
    Returns:
        JumpTestResult with comprehensive results
    """
    result = JumpTestResult(name, path)
    
    # Check if path exists
    if not os.path.exists(path):
        result.error = "Path does not exist"
        return result
    
    result.exists = True
    
    try:
        start_time = time.time()
        
        # Create FlowTracer and test jump following
        tracer = FlowTracer(path)
        result.has_start_label = True
        
        # Trace flow with jump following
        flow_result = tracer.trace_flow(max_steps)
        result.flow_result = flow_result
        result.trace_time = time.time() - start_time
        
        # Analyze basic flow statistics
        result.flow_statistics['total_steps'] = len(flow_result.steps)
        result.flow_statistics['stop_reason'] = flow_result.stop_reason
        result.flow_statistics['flow_control_encountered'] = flow_result.flow_control_encountered
        
        # Count different statement types
        for step in flow_result.steps:
            result.flow_statistics['files_traced'].add(step.file_path)
            
            if step.statement_type in ['dialogue', 'character_dialogue']:
                result.flow_statistics['dialogue_lines'] += 1
            elif step.statement_type == 'label':
                result.flow_statistics['labels_visited'] += 1
            elif step.statement_type == 'jump':
                result.jump_statistics['total_jumps_found'] += 1
                
                # Analyze jump success
                if step.parsed_data and 'target' in step.parsed_data:
                    result.jump_statistics['jumps_followed'] += 1
                    result.jump_statistics['unique_jump_targets'].add(step.parsed_data['target'])
                else:
                    result.jump_statistics['jumps_failed'] += 1
        
        # Detailed jump analysis
        if flow_result.steps:
            jump_analysis = analyze_jump_patterns(flow_result)
            result.jump_statistics['cross_file_jumps'] = jump_analysis['cross_file_jumps']
            
            # Count special stop reasons
            if flow_result.stop_reason == 'jump_target_not_found':
                result.jump_statistics['jump_target_not_found'] += 1
            elif flow_result.stop_reason == 'infinite_jump_loop':
                result.jump_statistics['infinite_loops_prevented'] += 1
        
    except StartLabelNotFoundError as e:
        result.error = f"No start label: {str(e)}"
        
    except RenpyProjectError as e:
        result.error = f"Project error: {str(e)}"
        
    except Exception as e:
        result.error = f"Unexpected error: {str(e)}"
    
    return result


def print_jump_analysis(result: JumpTestResult):
    """Print detailed jump following analysis for a VN."""
    print(f"\n🎮 {result.name}")
    print("=" * 60)
    print(f"📁 Path: {result.path}")
    print(f"⏱️  Trace time: {result.trace_time:.3f}s" if result.trace_time else "⏱️  Trace time: N/A")
    
    if not result.exists:
        print("❌ Path does not exist")
        return
    
    if result.error:
        print(f"❌ Error: {result.error}")
        return
    
    if not result.flow_result:
        print("❌ No flow trace results")
        return
    
    # Basic flow info
    stats = result.flow_statistics
    print(f"\n📊 Flow Statistics:")
    print(f"   • Total steps traced: {stats['total_steps']}")
    print(f"   • Dialogue lines: {stats['dialogue_lines']}")
    print(f"   • Labels visited: {stats['labels_visited']}")
    print(f"   • Files traced: {len(stats['files_traced'])}")
    print(f"   • Stop reason: {stats['stop_reason']}")
    print(f"   • Flow control: {stats['flow_control_encountered'] or 'None'}")
    
    # Jump-specific analysis
    jump_stats = result.jump_statistics
    print(f"\n🎯 Jump Following Analysis:")
    print(f"   • Total jumps found: {jump_stats['total_jumps_found']}")
    print(f"   • Jumps successfully followed: {jump_stats['jumps_followed']}")
    print(f"   • Jump failures: {jump_stats['jumps_failed']}")
    print(f"   • Unique jump targets: {len(jump_stats['unique_jump_targets'])}")
    print(f"   • Cross-file jumps: {jump_stats['cross_file_jumps']}")
    print(f"   • Infinite loops prevented: {jump_stats['infinite_loops_prevented']}")
    print(f"   • Jump targets not found: {jump_stats['jump_target_not_found']}")
    
    if jump_stats['total_jumps_found'] > 0:
        success_rate = (jump_stats['jumps_followed'] / jump_stats['total_jumps_found']) * 100
        print(f"   • Jump success rate: {success_rate:.1f}%")
    
    # Show jump targets
    if jump_stats['unique_jump_targets']:
        targets = list(jump_stats['unique_jump_targets'])[:5]  # Show first 5
        print(f"   • Sample targets: {', '.join(targets)}")
    
    # Detailed analysis if we have good data
    if result.flow_result and len(result.flow_result.steps) > 5:
        detailed = analyze_jump_patterns(result.flow_result)
        if detailed['jump_chains']:
            print(f"   • Jump chains found: {len(detailed['jump_chains'])}")
            if detailed['most_common_targets']:
                print(f"   • Most common targets: {dict(list(detailed['most_common_targets'].items())[:3])}")


def test_jump_following_suite():
    """Run comprehensive jump following tests on multiple VNs."""
    print("🎯 JUMP FOLLOWING TEST SUITE")
    print("=" * 70)
    print("Testing our Simple Jump Following implementation on real VN projects")
    print("=" * 70)
    
    results = []
    successful_tests = 0
    total_jumps_tested = 0
    total_jumps_followed = 0
    
    # Test each VN
    for name, path in JUMP_TEST_VNS.items():
        print(f"\n🧪 Testing {name}...")
        result = test_jump_following_on_vn(name, path, max_steps=50)
        results.append(result)
        
        if result.flow_result:
            successful_tests += 1
            total_jumps_tested += result.jump_statistics['total_jumps_found']
            total_jumps_followed += result.jump_statistics['jumps_followed']
            print(f"   ✅ {result.jump_statistics['total_jumps_found']} jumps, {result.jump_statistics['jumps_followed']} followed")
        else:
            print(f"   ❌ {result.error or 'Failed'}")
    
    # Print detailed results
    print("\n" + "=" * 70)
    print("DETAILED JUMP FOLLOWING ANALYSIS")
    print("=" * 70)
    
    for result in results:
        print_jump_analysis(result)
    
    # Summary statistics
    print("\n" + "=" * 70)
    print("📈 JUMP FOLLOWING TEST SUMMARY")
    print("=" * 70)
    print(f"VNs tested: {len(results)}")
    print(f"Successful traces: {successful_tests}")
    print(f"Success rate: {successful_tests/len(results)*100:.1f}%")
    
    if total_jumps_tested > 0:
        jump_success_rate = (total_jumps_followed / total_jumps_tested) * 100
        print(f"Total jumps found: {total_jumps_tested}")
        print(f"Total jumps followed: {total_jumps_followed}")
        print(f"Overall jump success rate: {jump_success_rate:.1f}%")
    
    # Analysis by stop reason
    stop_reasons = defaultdict(int)
    for result in results:
        if result.flow_result:
            stop_reasons[result.flow_result.stop_reason] += 1
    
    if stop_reasons:
        print(f"\nStop reasons:")
        for reason, count in sorted(stop_reasons.items()):
            print(f"   • {reason}: {count} VNs")
    
    print(f"\n🎉 Jump Following Test Suite Complete!")
    
    return results


def test_specific_vn_jumps(vn_name: str):
    """Test jump following on a specific VN with verbose output."""
    if vn_name not in JUMP_TEST_VNS:
        print(f"VN '{vn_name}' not found in test collection.")
        print(f"Available VNs: {', '.join(sorted(JUMP_TEST_VNS.keys()))}")
        return
    
    path = JUMP_TEST_VNS[vn_name]
    print(f"🎯 DETAILED JUMP FOLLOWING TEST: {vn_name}")
    print("=" * 70)
    
    result = test_jump_following_on_vn(vn_name, path, max_steps=100)
    print_jump_analysis(result)
    
    # Show actual jump trace if successful
    if result.flow_result and result.jump_statistics['total_jumps_found'] > 0:
        print(f"\n🔍 JUMP TRACE DETAILS:")
        print("-" * 40)
        
        jump_count = 0
        for i, step in enumerate(result.flow_result.steps):
            if step.statement_type == 'jump':
                jump_count += 1
                target = step.parsed_data.get('target', 'unknown') if step.parsed_data else 'unknown'
                
                print(f"Jump #{jump_count}: Line {step.line_number} in {step.file_path}")
                print(f"   Content: {step.content}")
                print(f"   Target: {target}")
                
                # Show where we jumped to
                if i + 1 < len(result.flow_result.steps):
                    next_step = result.flow_result.steps[i + 1]
                    print(f"   → Jumped to: Line {next_step.line_number} in {next_step.file_path}")
                    if next_step.file_path != step.file_path:
                        print(f"   📁 Cross-file jump!")
                print()


def main():
    """Main function to run jump following tests."""
    if len(sys.argv) > 1:
        # Test specific VN
        vn_name = sys.argv[1]
        test_specific_vn_jumps(vn_name)
    else:
        # Run full test suite
        try:
            results = test_jump_following_suite()
        except KeyboardInterrupt:
            print("\n\n⚠️ Testing interrupted by user")
        except Exception as e:
            print(f"\n❌ Error during testing: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main() 