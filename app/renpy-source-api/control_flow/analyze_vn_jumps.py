#!/usr/bin/env python3
"""
Analyze jump patterns in VN files to understand jump usage.

This script scans VN files to find all jump statements and analyze
patterns to help us understand if our flow tracer is reaching 
jump-heavy sections or if jumps are less common in these VNs.
"""

import sys
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from parser import RenpyParser
    from control_flow.flow_tracer import FlowTracer
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


def analyze_jumps_in_vn(vn_path: str) -> Dict:
    """
    Analyze all jump statements in a VN project.
    
    Args:
        vn_path: Path to VN project
        
    Returns:
        Dictionary with jump analysis
    """
    analysis = {
        'total_files': 0,
        'total_lines': 0,
        'total_jumps': 0,
        'jump_density': 0.0,
        'jump_targets': [],
        'jump_patterns': defaultdict(int),
        'files_with_jumps': [],
        'jump_locations': [],  # (file, line, target)
    }
    
    if not os.path.exists(vn_path):
        analysis['error'] = 'Path does not exist'
        return analysis
    
    try:
        # Find all .rpy files
        game_dir = Path(vn_path) / 'game' if (Path(vn_path) / 'game').exists() else Path(vn_path)
        rpy_files = list(game_dir.glob('*.rpy'))
        
        analysis['total_files'] = len(rpy_files)
        
        jump_pattern = re.compile(r'^\s*jump\s+([a-zA-Z_][a-zA-Z0-9_\.]*)', re.IGNORECASE)
        
        for rpy_file in rpy_files:
            try:
                with open(rpy_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    
                analysis['total_lines'] += len(lines)
                file_jumps = 0
                
                for line_num, line in enumerate(lines, 1):
                    match = jump_pattern.match(line.strip())
                    if match:
                        target = match.group(1)
                        analysis['total_jumps'] += 1
                        analysis['jump_targets'].append(target)
                        analysis['jump_locations'].append((str(rpy_file.name), line_num, target))
                        file_jumps += 1
                        
                        # Analyze jump patterns
                        if '.' in target:
                            analysis['jump_patterns']['local_jumps'] += 1
                        else:
                            analysis['jump_patterns']['global_jumps'] += 1
                            
                if file_jumps > 0:
                    analysis['files_with_jumps'].append((str(rpy_file.name), file_jumps))
                    
            except Exception as e:
                continue  # Skip problematic files
        
        # Calculate density
        if analysis['total_lines'] > 0:
            analysis['jump_density'] = (analysis['total_jumps'] / analysis['total_lines']) * 100
            
    except Exception as e:
        analysis['error'] = str(e)
    
    return analysis


def print_jump_analysis(vn_name: str, vn_path: str):
    """Print detailed jump analysis for a VN."""
    print(f"\n🎯 JUMP ANALYSIS: {vn_name}")
    print("=" * 60)
    print(f"📁 Path: {vn_path}")
    
    analysis = analyze_jumps_in_vn(vn_path)
    
    if 'error' in analysis:
        print(f"❌ Error: {analysis['error']}")
        return
    
    print(f"\n📊 File Statistics:")
    print(f"   • Total .rpy files: {analysis['total_files']}")
    print(f"   • Total lines: {analysis['total_lines']:,}")
    print(f"   • Files with jumps: {len(analysis['files_with_jumps'])}")
    
    print(f"\n🎯 Jump Statistics:")
    print(f"   • Total jumps found: {analysis['total_jumps']}")
    print(f"   • Jump density: {analysis['jump_density']:.3f}% (jumps per 100 lines)")
    print(f"   • Global jumps: {analysis['jump_patterns']['global_jumps']}")
    print(f"   • Local jumps: {analysis['jump_patterns']['local_jumps']}")
    
    if analysis['files_with_jumps']:
        print(f"\n📄 Files with most jumps:")
        sorted_files = sorted(analysis['files_with_jumps'], key=lambda x: x[1], reverse=True)
        for file_name, jump_count in sorted_files[:5]:
            print(f"   • {file_name}: {jump_count} jumps")
    
    if analysis['jump_targets']:
        # Most common targets
        target_counts = defaultdict(int)
        for target in analysis['jump_targets']:
            target_counts[target] += 1
        
        common_targets = sorted(target_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        if common_targets:
            print(f"\n🎯 Most common jump targets:")
            for target, count in common_targets:
                print(f"   • {target}: {count} times")
    
    # Show some example jumps
    if analysis['jump_locations']:
        print(f"\n📝 Example jumps:")
        for file_name, line_num, target in analysis['jump_locations'][:5]:
            print(f"   • {file_name}:{line_num} → {target}")
    
    return analysis


def analyze_multiple_vns():
    """Analyze jump patterns across multiple VNs."""
    vns_to_test = {
        "Savior": r"T:\AG\Savior-0.16c-pc",
        "MySisterMyRoommate": r"T:\AG\MySisterMyRoommateV1.69-pc",
        "TheAlphaGender": r"T:\AG\TheAlphaGender-0.3b-pc",
        "LastCall": r"T:\AG\LastCall-0.4-pc",
    }
    
    print("🔍 VN JUMP PATTERN ANALYSIS")
    print("=" * 70)
    print("Analyzing jump usage patterns across multiple VN projects")
    print("=" * 70)
    
    all_results = {}
    
    for vn_name, vn_path in vns_to_test.items():
        if os.path.exists(vn_path):
            analysis = print_jump_analysis(vn_name, vn_path)
            all_results[vn_name] = analysis
        else:
            print(f"\n❌ {vn_name}: Path not found - {vn_path}")
    
    # Summary comparison
    print(f"\n" + "=" * 70)
    print("📊 COMPARATIVE ANALYSIS")
    print("=" * 70)
    
    if all_results:
        print(f"{'VN Name':<20} {'Files':<8} {'Lines':<8} {'Jumps':<8} {'Density':<10}")
        print("-" * 60)
        
        for vn_name, analysis in all_results.items():
            if 'error' not in analysis:
                print(f"{vn_name:<20} {analysis['total_files']:<8} "
                      f"{analysis['total_lines']:<8,} {analysis['total_jumps']:<8} "
                      f"{analysis['jump_density']:<10.3f}%")
        
        # Overall stats
        total_jumps = sum(a['total_jumps'] for a in all_results.values() if 'error' not in a)
        total_lines = sum(a['total_lines'] for a in all_results.values() if 'error' not in a)
        
        if total_lines > 0:
            overall_density = (total_jumps / total_lines) * 100
            print(f"\n📈 Overall Statistics:")
            print(f"   • Total jumps across all VNs: {total_jumps}")
            print(f"   • Total lines analyzed: {total_lines:,}")
            print(f"   • Overall jump density: {overall_density:.3f}%")


def main():
    """Main function."""
    if len(sys.argv) > 1:
        vn_name = sys.argv[1]
        # You can add specific VN paths here
        vn_paths = {
            "Savior": r"T:\AG\Savior-0.16c-pc",
            "MySisterMyRoommate": r"T:\AG\MySisterMyRoommateV1.69-pc",
        }
        
        if vn_name in vn_paths:
            print_jump_analysis(vn_name, vn_paths[vn_name])
        else:
            print(f"VN '{vn_name}' not found. Available: {', '.join(vn_paths.keys())}")
    else:
        analyze_multiple_vns()


if __name__ == "__main__":
    main() 