#!/usr/bin/env python3

import sys
import os

# Add the path to the renpy-source-api
sys.path.append('app/renpy-source-api')

from parser import RenpyParser

def test_parser():
    print("[STANDALONE] Testing parser directly...")
    
    # Set the project path to the VN
    project_path = "T:/AG/MySisterMyRoommateV1.69-pc"
    
    print(f"[STANDALONE] Project path: {project_path}")
    
    # Create parser instance
    parser = RenpyParser()
    
    print("[STANDALONE] Created parser instance")
    
    try:
        # Call the method directly
        print("[STANDALONE] Calling _find_explicit_flows...")
        flows = parser._find_explicit_flows(project_path)
        
        print(f"[STANDALONE] Found {len(flows)} flows total")
        
        # Check for afternikkidate specifically
        afternikkidate_flows = [f for f in flows if f.source_label == 'afternikkidate' or f.target_label == 'afternikkidate']
        
        print(f"[STANDALONE] Found {len(afternikkidate_flows)} flows involving afternikkidate:")
        for flow in afternikkidate_flows:
            print(f"  {flow.source_label} -> {flow.target_label} ({flow.flow_type})")
    
    except Exception as e:
        print(f"[STANDALONE ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_parser() 