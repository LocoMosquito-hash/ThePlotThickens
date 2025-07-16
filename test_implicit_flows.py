#!/usr/bin/env python3
"""
Test script to verify implicit flow detection works correctly.

This script tests the enhanced flow detection on the problematic VNs:
- Futa Genesis Unveiled: cs_jump_2 -> line3return
- Savior: home1 -> dinnertalk

Usage: python test_implicit_flows.py
"""

import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / 'app'))
sys.path.insert(0, str(Path(__file__).parent / 'app' / 'renpy-source-api'))

try:
    from parser import RenpyParser
    from core import RenpyProject
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)


def test_vn_implicit_flows(vn_name: str, vn_path: str, expected_connections: list):
    """
    Test implicit flow detection for a specific VN.
    
    Args:
        vn_name: Name of the VN for reporting
        vn_path: Path to the VN's game directory
        expected_connections: List of (source, target) tuples we expect to find
    """
    print(f"\n🎮 Testing {vn_name}")
    print(f"📁 Path: {vn_path}")
    print("=" * 60)
    
    if not os.path.exists(vn_path):
        print(f"❌ VN path does not exist: {vn_path}")
        return False
    
    try:
        # Initialize parser and get flows
        parser = RenpyParser()
        flows = parser.find_all_label_flows(vn_path)
        
        print(f"📊 Total flows detected: {len(flows)}")
        
        # Analyze flows by type
        flow_counts = {}
        implicit_flows = []
        
        for flow in flows:
            flow_type = flow.flow_type
            flow_counts[flow_type] = flow_counts.get(flow_type, 0) + 1
            
            if flow_type == 'implicit':
                implicit_flows.append(flow)
        
        print(f"🔗 Flow types found:")
        for flow_type, count in sorted(flow_counts.items()):
            print(f"   • {flow_type}: {count}")
        
        # Check for expected connections
        print(f"\n🎯 Checking expected implicit connections:")
        for source_label, target_label in expected_connections:
            found = False
            
            for flow in implicit_flows:
                if flow.source_label == source_label and flow.target_label == target_label:
                    found = True
                    print(f"   ✅ {source_label} → {target_label} (implicit)")
                    print(f"      📄 {os.path.basename(flow.file_path)}:{flow.line_number}")
                    print(f"      🔍 Context: {flow.context}")
                    break
            
            if not found:
                print(f"   ❌ {source_label} → {target_label} (NOT FOUND)")
                
                # Look for any flows from the source label
                source_flows = [f for f in flows if f.source_label == source_label]
                if source_flows:
                    print(f"      🔍 Found other flows from {source_label}:")
                    for f in source_flows:
                        print(f"         → {f.target_label} ({f.flow_type})")
                else:
                    print(f"      🔍 No flows found from {source_label}")
        
        # Show sample implicit flows
        if implicit_flows:
            print(f"\n📝 Sample implicit flows (first 5):")
            for i, flow in enumerate(implicit_flows[:5]):
                print(f"   {i+1}. {flow.source_label} → {flow.target_label}")
                print(f"      📄 {os.path.basename(flow.file_path)}:{flow.line_number}")
                print(f"      🔍 {flow.context}")
        
        return len(implicit_flows) > 0
        
    except Exception as e:
        print(f"❌ Error testing {vn_name}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    print("🧪 TESTING IMPLICIT FLOW DETECTION")
    print("=" * 60)
    
    # Test cases based on user's problem description
    test_cases = [
        {
            'name': 'Futa Genesis Unveiled',
            'path': r'T:\AG\FutagenesisUnveiled-v0.06.2-pc\game',
            'expected': [('cs_jump_2', 'line3return')]
        },
        {
            'name': 'Savior',
            'path': r'T:\AG\Savior-0.16c-pc\game', 
            'expected': [('home1', 'dinnertalk')]
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        success = test_vn_implicit_flows(
            test_case['name'],
            test_case['path'], 
            test_case['expected']
        )
        results.append((test_case['name'], success))
    
    # Summary
    print(f"\n📋 SUMMARY")
    print("=" * 60)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {name}")
    
    successful_tests = sum(1 for _, success in results if success)
    total_tests = len(results)
    
    print(f"\n🎯 Results: {successful_tests}/{total_tests} tests passed")
    
    if successful_tests == total_tests:
        print("🎉 All tests passed! Implicit flow detection is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    main() 