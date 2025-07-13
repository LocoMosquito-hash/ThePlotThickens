#!/usr/bin/env python3
"""
Test StartLabelFinder against real Ren'Py VN projects.

This script tests the StartLabelFinder implementation against the user's
collection of decompiled Ren'Py visual novels to ensure it works correctly
with real-world projects.
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from control_flow.start_label_finder import StartLabelFinder, StartLabelNotFoundError
    from exceptions import RenpyProjectError, RenpyParseError
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the correct directory")
    sys.exit(1)


# VN Projects from the user's collection
VN_TEST_PATHS = {
    # Preferred to start with
    "LastCall": r"T:\AG\LastCall-0.4-pc\game",
    "MySisterMyRoommate": r"T:\AG\MySisterMyRoommateV1.69-pc\game", 
    "AlisonFalloftheApple": r"T:\AG\AlisonFalloftheApple-1.0-pc\game",
    
    # Small
    "TheAlphaGender": r"T:\AG\TheAlphaGender-0.3b-pc\game",
    
    # Medium  
    "ThisTime": r"T:\AG\ThisTime\game\scripts",
    
    # Large, unfinished
    "DeviantAnomalies": r"T:\AG\DeviantAnomalies-0.9.5-pc\game",
    "Savior": r"T:\AG\Savior-0.16c-pc\game",
    
    # Huge
    "DetectiveNecro": r"T:\AG\DetectiveNecro-0.55-pc\game",
    
    # Additional test cases
    "TuneInToTheShow": r"T:\AG\Tune in to the Show Episode 6-v0.6-market-STEAM\game",
    "Tropicali": r"T:\AG\Tropicali_Demo-0.6d-pc\game",
    "BrightonCityEmpire": r"T:\AG\BrightonCityEmpire-0.04-pc\game\scripts",
    "StarPeriphery": r"T:\AG\StarPeriphery-Release4.5-win\game",
    "ProjectMnemosyne": r"T:\AG\ProjectMnemosyne-0.14.2-pc\game",
    "Mybrotherswife": r"T:\AG\Mybrotherswife-0.9.2-pc\game",
    "DOF": r"T:\AG\DOF-Ep2_V_2_Final-pc\game",
    "MistOfHerBody": r"T:\AG\Mist_of_her_body-1.0-pc\game",
    "NSEvolution": r"T:\AG\NSEvolutionv0.3.9.2Hotfix3\game",
    "WestviewAcademy": r"T:\AG\WestviewAcademy-0.4.1-pc\game",
    "HotSandOfAntarctica": r"T:\AG\HotSandOfAntarctica-0.08-pc\game",
    "Motherless": r"T:\AG\Motherless\game",
    "GuiltyPleasure": r"T:\AG\GuiltyPleasure-0.27-pc\game",
    "NotGoingBack": r"T:\AG\NotGoingBack-1.0-pc\game",
    "RedLucy": r"T:\AG\RedLucy-0.8-pc\game",
    "AFathersSins": r"T:\AG\A_Fathers_Sins-Chapter_20-pc\game",
    "TheEntrepreneur": r"T:\AG\TheEntrepreneur-Episode4_EarlyRelease-pc\game",
    "LetterToMyDream": r"T:\AG\LettertomyDream-0.1.2-pc\game",
    "RedBrim": r"T:\AG\RedBrim-0.1_alpha-pc\game",
    "Duality": r"T:\AG\Duality-v0.1.8-pc\game",
    "BadMemories": r"T:\AG\Bad Memories\game",
    "StarHarem": r"T:\AG\StarHaremEpisode1-pc\game",
    "SOP": r"T:\AG\SOP-1.0-pc\game",
    "TheDeLucaFamily": r"T:\AG\The_DeLuca_Family-0.09.6-pc\game",
    "ColdComforts": r"T:\AG\ColdComforts-v0.1b-pc\game",
    "ReRudy": r"T:\AG\ReRudy-0.5.0-pc\game",
    "Unleashed": r"T:\AG\unleashed-0.6b2-pc\game",
    "FriendsInNeed": r"T:\AG\FriendsinNeed-pc\game",
    "MindSociety": r"T:\AG\MindSociety-0.5-pc\game",
}


class VNTestResult:
    """Results from testing a VN project."""
    
    def __init__(self, name: str, path: str):
        self.name = name
        self.path = path
        self.exists = False
        self.is_valid_project = False
        self.has_start_label = False
        self.start_file: Optional[str] = None
        self.start_line: Optional[int] = None
        self.rpy_file_count = 0
        self.error: Optional[str] = None
        self.parse_time: Optional[float] = None


def test_single_vn(name: str, path: str) -> VNTestResult:
    """
    Test a single VN project with StartLabelFinder.
    
    Args:
        name: Name of the VN
        path: Path to the VN's game directory
        
    Returns:
        VNTestResult: Test results
    """
    result = VNTestResult(name, path)
    
    # Check if path exists
    if not os.path.exists(path):
        result.error = "Path does not exist"
        return result
    
    result.exists = True
    
    try:
        start_time = time.time()
        
        # Try to create StartLabelFinder
        finder = StartLabelFinder(path)
        result.is_valid_project = True
        
        # Get project info
        info = finder.get_project_info()
        result.rpy_file_count = info['total_rpy_files']
        result.has_start_label = info['has_start_label']
        result.start_file = info['start_file']
        result.start_line = info['start_line']
        
        result.parse_time = time.time() - start_time
        
    except StartLabelNotFoundError as e:
        result.is_valid_project = True
        result.has_start_label = False
        result.error = f"No start label: {str(e)}"
        result.parse_time = time.time() - start_time
        
    except RenpyProjectError as e:
        result.error = f"Project error: {str(e)}"
        
    except Exception as e:
        result.error = f"Unexpected error: {str(e)}"
    
    return result


def test_priority_vns() -> List[VNTestResult]:
    """Test the priority VNs first."""
    priority_names = ["LastCall", "MySisterMyRoommate", "AlisonFalloftheApple", "TheAlphaGender"]
    
    results = []
    for name in priority_names:
        if name in VN_TEST_PATHS:
            path = VN_TEST_PATHS[name]
            result = test_single_vn(name, path)
            results.append(result)
            
    return results


def test_all_vns() -> List[VNTestResult]:
    """Test all VNs in the collection."""
    results = []
    
    for name, path in VN_TEST_PATHS.items():
        print(f"Testing {name}...", end=" ")
        result = test_single_vn(name, path)
        
        if result.has_start_label:
            print(f"✅ Found start at {result.start_file}:{result.start_line}")
        elif result.is_valid_project:
            print(f"⚠️  Valid project but no start label")
        elif not result.exists:
            print(f"❌ Path not found")
        else:
            print(f"❌ {result.error}")
            
        results.append(result)
    
    return results


def print_summary(results: List[VNTestResult]):
    """Print a summary of test results."""
    total = len(results)
    existing = sum(1 for r in results if r.exists)
    valid_projects = sum(1 for r in results if r.is_valid_project)
    with_start = sum(1 for r in results if r.has_start_label)
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total VNs tested: {total}")
    print(f"Existing paths: {existing}/{total} ({existing/total*100:.1f}%)")
    print(f"Valid Ren'Py projects: {valid_projects}/{existing} ({valid_projects/existing*100:.1f}% of existing)")
    print(f"Projects with start label: {with_start}/{valid_projects} ({with_start/valid_projects*100:.1f}% of valid)")
    
    # Performance stats
    parse_times = [r.parse_time for r in results if r.parse_time is not None]
    if parse_times:
        avg_time = sum(parse_times) / len(parse_times)
        max_time = max(parse_times)
        print(f"\nPerformance:")
        print(f"Average parse time: {avg_time:.3f}s")
        print(f"Slowest parse time: {max_time:.3f}s")
    
    # Success stories
    successful = [r for r in results if r.has_start_label]
    if successful:
        print(f"\n✅ SUCCESS CASES ({len(successful)}):")
        for result in successful[:10]:  # Show first 10
            time_str = f" ({result.parse_time:.3f}s)" if result.parse_time else ""
            print(f"  {result.name}: {result.start_file}:{result.start_line} [{result.rpy_file_count} files]{time_str}")
        if len(successful) > 10:
            print(f"  ... and {len(successful) - 10} more")
    
    # Problem cases
    problems = [r for r in results if not r.has_start_label and r.exists]
    if problems:
        print(f"\n⚠️  PROBLEM CASES ({len(problems)}):")
        for result in problems[:10]:  # Show first 10
            print(f"  {result.name}: {result.error}")
        if len(problems) > 10:
            print(f"  ... and {len(problems) - 10} more")
    
    # Missing paths
    missing = [r for r in results if not r.exists]
    if missing:
        print(f"\n❌ MISSING PATHS ({len(missing)}):")
        for result in missing[:5]:  # Show first 5
            print(f"  {result.name}: {result.path}")
        if len(missing) > 5:
            print(f"  ... and {len(missing) - 5} more")


def test_specific_vn(vn_name: str):
    """Test a specific VN by name."""
    if vn_name not in VN_TEST_PATHS:
        print(f"VN '{vn_name}' not found in test collection.")
        print(f"Available VNs: {', '.join(sorted(VN_TEST_PATHS.keys()))}")
        return
    
    path = VN_TEST_PATHS[vn_name]
    result = test_single_vn(vn_name, path)
    
    print(f"Testing VN: {vn_name}")
    print(f"Path: {path}")
    print(f"Exists: {result.exists}")
    
    if not result.exists:
        print("❌ Path does not exist")
        return
    
    print(f"Valid Ren'Py project: {result.is_valid_project}")
    
    if not result.is_valid_project:
        print(f"❌ Error: {result.error}")
        return
    
    print(f"RPY files found: {result.rpy_file_count}")
    print(f"Has start label: {result.has_start_label}")
    
    if result.has_start_label:
        print(f"✅ Start label found: {result.start_file}:{result.start_line}")
        if result.parse_time:
            print(f"Parse time: {result.parse_time:.3f}s")
            
        # Try to get the actual start line content
        try:
            finder = StartLabelFinder(path)
            start_line = finder.find_start_label()
            print(f"Content: {start_line.content.strip()}")
        except Exception as e:
            print(f"Error getting start line content: {e}")
    else:
        print(f"⚠️  No start label found")
        if result.error:
            print(f"Error: {result.error}")


def main():
    """Main test function."""
    if len(sys.argv) > 1:
        # Test specific VN
        vn_name = sys.argv[1]
        test_specific_vn(vn_name)
    else:
        # Test all VNs
        print("Testing StartLabelFinder with real VN projects...")
        print("This may take a while for large projects.\n")
        
        results = test_all_vns()
        print_summary(results)
        
        # Save detailed results to file
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"vn_test_results_{timestamp}.txt"
        
        with open(filename, 'w') as f:
            f.write("StartLabelFinder Test Results\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for result in results:
                f.write(f"VN: {result.name}\n")
                f.write(f"Path: {result.path}\n")
                f.write(f"Exists: {result.exists}\n")
                f.write(f"Valid project: {result.is_valid_project}\n")
                f.write(f"Has start label: {result.has_start_label}\n")
                f.write(f"Start location: {result.start_file}:{result.start_line}\n")
                f.write(f"RPY files: {result.rpy_file_count}\n")
                f.write(f"Parse time: {result.parse_time}\n")
                f.write(f"Error: {result.error}\n")
                f.write("-" * 50 + "\n")
        
        print(f"\nDetailed results saved to: {filename}")


if __name__ == "__main__":
    main() 