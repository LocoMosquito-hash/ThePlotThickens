#!/usr/bin/env python3
"""
Standalone VN project analyzer.

This script analyzes Ren'Py projects using comprehensive parsing without requiring
the full Ren'Py runtime environment. It runs with the SDK's Python runtime.
"""

import os
import sys
import json
import argparse
import datetime
import re
from pathlib import Path


def parse_menu_structure(lines, start_line_idx, rel_path):
    """
    Parse a complete menu structure starting from a menu line.
    
    Args:
        lines: List of all lines in the file
        start_line_idx: Index where the menu starts (0-based)
        rel_path: Relative path of the file
        
    Returns:
        Dict with comprehensive menu data
    """
    menu_data = {
        "file": rel_path,
        "line": start_line_idx + 1,  # Convert to 1-based
        "type": "menu_structure",
        "prompt": None,
        "choices": [],
        "has_conditions": False,
        "menu_name": None,
        "menu_set": None,
        "complexity": "simple"
    }
    
    if start_line_idx >= len(lines):
        return menu_data
    
    # Parse the menu declaration line
    menu_line = lines[start_line_idx].strip()
    
    # Check for named menu: menu menu_name:
    menu_name_match = re.match(r'^\s*menu\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*:', menu_line)
    if menu_name_match:
        menu_data["menu_name"] = menu_name_match.group(1)
        menu_data["complexity"] = "named"
    
    # Check for menu set: menu(nvl):
    menu_set_match = re.match(r'^\s*menu\s*\(([^)]+)\)\s*:', menu_line)
    if menu_set_match:
        menu_data["menu_set"] = menu_set_match.group(1)
        menu_data["complexity"] = "set_based"
    
    current_line = start_line_idx + 1
    current_choice = None
    base_indent = None
    choice_indent = None
    
    # Look for menu prompt (dialogue line before choices)
    prompt_search_start = current_line
    while current_line < len(lines) and current_line < start_line_idx + 10:  # Look ahead max 10 lines
        line = lines[current_line].strip()
        
        if not line or line.startswith('#'):
            current_line += 1
            continue
            
        # Check for dialogue line (potential prompt)
        if line.startswith('"') and line.endswith('"') and ':' not in line:
            menu_data["prompt"] = line.strip('"')
            current_line += 1
            break
        elif '"' in line and ':' in line:
            # This is a choice, stop looking for prompt
            break
        
        current_line += 1
    
    # Parse choices
    while current_line < len(lines):
        line = lines[current_line]
        stripped_line = line.strip()
        
        if not stripped_line or stripped_line.startswith('#'):
            current_line += 1
            continue
        
        # Calculate indentation
        line_indent = len(line) - len(line.lstrip())
        
        # Set base indentation from first non-empty line
        if base_indent is None:
            base_indent = line_indent
        
        # Check if we've moved back to menu level or beyond
        if line_indent <= base_indent and current_choice and not stripped_line.startswith('"'):
            # End of menu
            if current_choice:
                menu_data["choices"].append(current_choice)
            break
        
        # Check for menu choice patterns
        choice_patterns = [
            # Basic choice: "Choice text":
            (r'^\s*"([^"]+)"\s*:', "basic"),
            # Conditional choice: "Choice text" if condition:
            (r'^\s*"([^"]+)"\s+if\s+(.+)\s*:', "conditional"),
            # Choice with expression: "[expression]" if condition:
            (r'^\s*"\[([^\]]+)\]"\s*:', "expression"),
            (r'^\s*"\[([^\]]+)\]"\s+if\s+(.+)\s*:', "conditional_expression"),
        ]
        
        choice_match = None
        choice_type = None
        
        for pattern, ctype in choice_patterns:
            match = re.match(pattern, line)
            if match:
                choice_match = match
                choice_type = ctype
                break
        
        if choice_match:
            # Save previous choice if exists
            if current_choice:
                menu_data["choices"].append(current_choice)
            
            # Create new choice
            choice_text = choice_match.group(1)
            current_choice = {
                "text": choice_text,
                "line": current_line + 1,
                "type": choice_type,
                "condition": None,
                "destinations": [],
                "actions": [],
                "has_jumps": False,
                "has_calls": False,
                "has_returns": False,
                "subsequent_lines": []
            }
            
            # Handle conditional choices
            if choice_type in ["conditional", "conditional_expression"] and len(choice_match.groups()) > 1:
                current_choice["condition"] = choice_match.group(2).strip()
                menu_data["has_conditions"] = True
                menu_data["complexity"] = "conditional"
            
            choice_indent = line_indent
            
        elif current_choice and choice_indent is not None and line_indent > choice_indent:
            # This line belongs to the current choice
            current_choice["subsequent_lines"].append(stripped_line)
            
            # Parse choice actions
            action_patterns = [
                (r'^\s*jump\s+([a-zA-Z_][a-zA-Z0-9_]*)', "jump"),
                (r'^\s*call\s+([a-zA-Z_][a-zA-Z0-9_]*)', "call"),
                (r'^\s*return\s*$', "return"),
                (r'^\s*pass\s*$', "pass"),
                (r'^\s*continue\s*$', "continue"),
                (r'^\s*jump\s+expression\s+(.+)', "jump_expression"),
                (r'^\s*call\s+expression\s+(.+)', "call_expression"),
            ]
            
            for action_pattern, action_type in action_patterns:
                action_match = re.match(action_pattern, line)
                if action_match:
                    action_data = {
                        "type": action_type,
                        "line": current_line + 1
                    }
                    
                    if action_type in ["jump", "call"]:
                        destination = action_match.group(1)
                        action_data["destination"] = destination
                        current_choice["destinations"].append(destination)
                        
                        if action_type == "jump":
                            current_choice["has_jumps"] = True
                        else:
                            current_choice["has_calls"] = True
                            
                    elif action_type in ["jump_expression", "call_expression"]:
                        action_data["expression"] = action_match.group(1)
                        menu_data["complexity"] = "dynamic"
                        
                    elif action_type == "return":
                        current_choice["has_returns"] = True
                        current_choice["destinations"].append("<return>")
                    
                    current_choice["actions"].append(action_data)
                    break
        
        current_line += 1
    
    # Add final choice if exists
    if current_choice:
        menu_data["choices"].append(current_choice)
    
    # Determine final complexity
    choice_count = len(menu_data["choices"])
    if choice_count > 6:
        menu_data["complexity"] = "complex"
    elif menu_data["has_conditions"] or menu_data["menu_set"]:
        menu_data["complexity"] = "conditional"
    elif choice_count > 3:
        menu_data["complexity"] = "moderate"
    
    return menu_data


def analyze_rpy_file(rpy_file_path, project_root):
    """
    Analyze a single .rpy file using comprehensive parsing.
    
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
    
    # Calculate relative path first (before any potential exceptions)
    rel_path = os.path.relpath(rpy_file_path, project_root)
    
    # Check if it's actually a file, not a directory
    if not os.path.isfile(rpy_file_path):
        if os.path.isdir(rpy_file_path):
            results["errors"].append(f"Skipping .rpy directory: {rel_path}")
            print(f"[WARNING] Skipping .rpy directory: {rel_path}")
        else:
            results["errors"].append(f"Path does not exist or is not a file: {rel_path}")
        return results
    
    try:
        with open(rpy_file_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        
        line_num = 0
        while line_num < len(lines):
            line = lines[line_num]
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith('#'):
                line_num += 1
                continue
            
            # Label detection
            if stripped.startswith('label ') and ':' in stripped:
                label_name = stripped.split('label ')[1].split(':')[0].strip()
                results["labels"].append({
                    "name": label_name,
                    "file": rel_path,
                    "line": line_num + 1
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
                            "line": line_num + 1,
                            "definition": stripped
                        })
                except Exception:
                    pass  # Skip malformed definitions
            
            # Enhanced menu detection and parsing
            elif stripped.startswith('menu'):
                try:
                    menu_data = parse_menu_structure(lines, line_num, rel_path)
                    results["menus"].append(menu_data)
                    
                    # Skip ahead past the menu structure to avoid double-parsing
                    # Find the end of this menu by looking for choices
                    skip_lines = 1
                    temp_line = line_num + 1
                    while temp_line < len(lines):
                        temp_stripped = lines[temp_line].strip()
                        if (temp_stripped.startswith('"') and ':' in temp_stripped) or \
                           (temp_stripped and not temp_stripped.startswith(' ') and 
                            not temp_stripped.startswith('\t') and 
                            not temp_stripped.startswith('#') and
                            not temp_stripped.startswith('"')):
                            break
                        skip_lines += 1
                        temp_line += 1
                    
                    line_num += max(skip_lines, len(menu_data["choices"]) * 2)  # Conservative skip
                    continue
                    
                except Exception as e:
                    results["errors"].append(f"Error parsing menu at {rel_path}:{line_num + 1}: {str(e)}")
            
            # Asset detection (images, sounds, etc.)
            elif any(keyword in stripped.lower() for keyword in ['scene ', 'show ', 'play music', 'play sound']):
                # Enhanced asset detection
                asset_patterns = [
                    (r'scene\s+([^\s]+)', "background"),
                    (r'show\s+([^\s]+)', "sprite"),
                    (r'play\s+music\s+"([^"]+)"', "music"),
                    (r'play\s+sound\s+"([^"]+)"', "sound"),
                    (r'play\s+audio\s+"([^"]+)"', "audio"),
                ]
                
                for pattern, asset_type in asset_patterns:
                    match = re.search(pattern, stripped, re.IGNORECASE)
                    if match:
                        asset_name = match.group(1).strip('"\'')
                        results["assets"].append({
                            "name": asset_name,
                            "type": asset_type,
                            "file": rel_path,
                            "line": line_num + 1,
                            "context": stripped
                        })
                        break
                
                # Fallback: basic extension-based detection
                for ext in ['.png', '.jpg', '.jpeg', '.gif', '.mp3', '.ogg', '.wav']:
                    if ext in stripped.lower():
                        words = stripped.split()
                        for word in words:
                            if ext in word.lower():
                                results["assets"].append({
                                    "name": word.strip('"\''),
                                    "type": "reference",
                                    "file": rel_path,
                                    "line": line_num + 1,
                                    "context": stripped
                                })
                                break
            
            line_num += 1
    
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
            "analyzer_version": "2.0",
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
    
    # Find all .rpy files (filter out directories)
    rpy_files = []
    rpy_directories = []
    for rpy_path in project_root.glob("**/*.rpy"):
        if rpy_path.is_file():
            rpy_files.append(rpy_path)
        elif rpy_path.is_dir():
            rpy_directories.append(rpy_path)
            print(f"[WARNING] Found .rpy directory (will skip): {rpy_path.relative_to(project_root)}")
    
    results["project_info"]["rpy_files"] = len(rpy_files)
    results["project_info"]["rpy_directories"] = len(rpy_directories)
    results["project_info"]["file_list"] = [
        str(f.relative_to(project_root)) for f in rpy_files
    ]
    results["project_info"]["directory_list"] = [
        str(d.relative_to(project_root)) for d in rpy_directories
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
    
    # Calculate enhanced statistics
    results["project_info"]["total_labels"] = len(results["labels"])
    results["project_info"]["total_characters"] = len(results["characters"])
    results["project_info"]["total_menus"] = len(results["menus"])
    results["project_info"]["total_assets"] = len(results["assets"])
    results["project_info"]["total_errors"] = len(results["errors"])
    
    # Menu analysis statistics
    menu_complexities = {}
    total_choices = 0
    conditional_menus = 0
    
    for menu in results["menus"]:
        complexity = menu.get("complexity", "simple")
        menu_complexities[complexity] = menu_complexities.get(complexity, 0) + 1
        total_choices += len(menu.get("choices", []))
        if menu.get("has_conditions", False):
            conditional_menus += 1
    
    results["project_info"]["menu_statistics"] = {
        "complexities": menu_complexities,
        "total_choices": total_choices,
        "conditional_menus": conditional_menus,
        "average_choices_per_menu": total_choices / len(results["menus"]) if results["menus"] else 0
    }
    
    # Save results if output path specified
    if output_path:
        output_file = Path(output_path)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Results saved to: {output_file}")
    
    return results


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description="Analyze Ren'Py project structure (Enhanced)")
    parser.add_argument("project_path", help="Path to the Ren'Py project's game directory")
    parser.add_argument("-o", "--output", help="Path to save JSON results")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Analyze the project
    results = analyze_project(args.project_path, args.output)
    
    # Print summary
    print("\n" + "="*50)
    print("ENHANCED ANALYSIS COMPLETE")
    print("="*50)
    print(f"Files analyzed: {results['project_info']['rpy_files']}")
    print(f"Labels found: {results['project_info']['total_labels']}")
    print(f"Characters found: {results['project_info']['total_characters']}")
    print(f"Menus found: {results['project_info']['total_menus']}")
    print(f"Assets referenced: {results['project_info']['total_assets']}")
    print(f"Errors encountered: {results['project_info']['total_errors']}")
    
    # Enhanced menu statistics
    menu_stats = results["project_info"].get("menu_statistics", {})
    if menu_stats:
        print(f"\nMENU ANALYSIS:")
        print(f"Total choices: {menu_stats['total_choices']}")
        print(f"Conditional menus: {menu_stats['conditional_menus']}")
        print(f"Average choices per menu: {menu_stats['average_choices_per_menu']:.1f}")
        
        complexities = menu_stats.get("complexities", {})
        if complexities:
            print(f"Menu complexities:")
            for complexity, count in complexities.items():
                print(f"  - {complexity}: {count}")
    
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
    
    # Show menu samples
    if results["menus"] and args.verbose:
        print(f"\nSample menus (first 3):")
        for i, menu in enumerate(results["menus"][:3]):
            choice_count = len(menu.get("choices", []))
            complexity = menu.get("complexity", "simple")
            print(f"  {i+1}. Menu in {menu['file']}:{menu['line']} ({choice_count} choices, {complexity})")
            
            if menu.get("prompt"):
                print(f"     Prompt: \"{menu['prompt']}\"")
            
            for j, choice in enumerate(menu.get("choices", [])[:3]):
                choice_text = choice.get("text", "No text")
                destinations = choice.get("destinations", [])
                dest_str = f" -> {', '.join(destinations)}" if destinations else ""
                print(f"     Choice {j+1}: \"{choice_text}\"{dest_str}")


if __name__ == "__main__":
    main() 