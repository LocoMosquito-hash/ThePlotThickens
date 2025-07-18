#!/usr/bin/env python3
"""
Standalone VN project analyzer.

This script analyzes Ren'Py projects using basic file parsing without requiring
the full Ren'Py runtime environment. It runs with the SDK's Python runtime.
"""

import os
import sys
import json
import argparse
import datetime
from pathlib import Path


def analyze_rpy_file(rpy_file_path, project_root):
    """
    Analyze a single .rpy file using basic parsing.
    
    Args:
        rpy_file_path: Path to the .rpy file
        project_root: Root path of the project
        
    Returns:
        Dict with analysis results for this file
    """
    results = {
        "labels": [],
        "characters": [],
        "menus": [],
        "assets": [],
        "errors": []
    }
    
    try:
        with open(rpy_file_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        
        rel_path = os.path.relpath(rpy_file_path, project_root)
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith('#'):
                continue
            
            # Label detection
            if stripped.startswith('label ') and ':' in stripped:
                label_name = stripped.split('label ')[1].split(':')[0].strip()
                results["labels"].append({
                    "name": label_name,
                    "file": rel_path,
                    "line": line_num
                })
            
            # Character definition detection
            elif stripped.startswith('define ') and 'Character(' in stripped:
                try:
                    char_def = stripped.split('define ')[1]
                    if '=' in char_def:
                        char_name = char_def.split('=')[0].strip()
                        results["characters"].append({
                            "name": char_name,
                            "file": rel_path,
                            "line": line_num,
                            "definition": stripped
                        })
                except Exception:
                    pass  # Skip malformed definitions
            
            # Menu detection
            elif stripped.startswith('menu'):
                results["menus"].append({
                    "file": rel_path,
                    "line": line_num,
                    "type": "menu_start"
                })
            
            # Asset detection (images, sounds, etc.)
            elif any(keyword in stripped.lower() for keyword in ['scene ', 'show ', 'play music', 'play sound']):
                # Basic asset detection
                for ext in ['.png', '.jpg', '.jpeg', '.gif', '.mp3', '.ogg', '.wav']:
                    if ext in stripped.lower():
                        # Extract potential asset name
                        words = stripped.split()
                        for word in words:
                            if ext in word.lower():
                                results["assets"].append({
                                    "name": word.strip('"\''),
                                    "type": "reference",
                                    "file": rel_path,
                                    "line": line_num
                                })
                                break
    
    except Exception as e:
        results["errors"].append(f"Error parsing {rel_path}: {str(e)}")
    
    return results


def analyze_project(project_path, output_path=None):
    """
    Analyze a complete Ren'Py project.
    
    Args:
        project_path: Path to the project's game directory
        output_path: Optional path to save JSON results
        
    Returns:
        Dict with complete analysis results
    """
    project_root = Path(project_path)
    
    # Overall results structure
    results = {
        "metadata": {
            "analyzer_version": "1.0",
            "analysis_timestamp": datetime.datetime.now().isoformat(),
            "target_project": str(project_root),
        },
        "project_info": {},
        "labels": [],
        "characters": [],
        "menus": [],
        "assets": [],
        "errors": []
    }
    
    if not project_root.exists():
        results["errors"].append(f"Project path does not exist: {project_root}")
        return results
    
    # Find all .rpy files
    rpy_files = []
    for rpy_file in project_root.glob("**/*.rpy"):
        rpy_files.append(rpy_file)
    
    results["project_info"]["rpy_files"] = len(rpy_files)
    results["project_info"]["file_list"] = [
        str(f.relative_to(project_root)) for f in rpy_files
    ]
    
    print(f"Found {len(rpy_files)} .rpy files in {project_root}")
    
    # Analyze each file
    for rpy_file in rpy_files:
        print(f"Analyzing: {rpy_file.relative_to(project_root)}")
        file_results = analyze_rpy_file(rpy_file, project_root)
        
        # Merge results
        results["labels"].extend(file_results["labels"])
        results["characters"].extend(file_results["characters"])
        results["menus"].extend(file_results["menus"])
        results["assets"].extend(file_results["assets"])
        results["errors"].extend(file_results["errors"])
    
    # Add summary info
    results["project_info"]["total_labels"] = len(results["labels"])
    results["project_info"]["total_characters"] = len(results["characters"])
    results["project_info"]["total_menus"] = len(results["menus"])
    results["project_info"]["total_assets"] = len(results["assets"])
    results["project_info"]["total_errors"] = len(results["errors"])
    
    # Save results if output path specified
    if output_path:
        output_file = Path(output_path)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Results saved to: {output_file}")
    
    return results


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description="Analyze Ren'Py project structure")
    parser.add_argument("project_path", help="Path to the Ren'Py project's game directory")
    parser.add_argument("-o", "--output", help="Path to save JSON results")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Analyze the project
    results = analyze_project(args.project_path, args.output)
    
    # Print summary
    print("\n" + "="*50)
    print("ANALYSIS COMPLETE")
    print("="*50)
    print(f"Files analyzed: {results['project_info']['rpy_files']}")
    print(f"Labels found: {results['project_info']['total_labels']}")
    print(f"Characters found: {results['project_info']['total_characters']}")
    print(f"Menus found: {results['project_info']['total_menus']}")
    print(f"Assets referenced: {results['project_info']['total_assets']}")
    print(f"Errors encountered: {results['project_info']['total_errors']}")
    
    if args.verbose and results["errors"]:
        print(f"\nErrors:")
        for error in results["errors"]:
            print(f"  - {error}")
    
    # Show some sample results
    if results["labels"] and args.verbose:
        print(f"\nSample labels (first 5):")
        for label in results["labels"][:5]:
            print(f"  - {label['name']} (in {label['file']}:{label['line']})")
    
    if results["characters"] and args.verbose:
        print(f"\nCharacters found:")
        for char in results["characters"]:
            print(f"  - {char['name']} (in {char['file']}:{char['line']})")


if __name__ == "__main__":
    main() 