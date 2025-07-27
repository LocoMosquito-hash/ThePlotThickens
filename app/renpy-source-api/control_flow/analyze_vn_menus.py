#!/usr/bin/env python3
"""
Analyze menu patterns and decision points in VN files.

This script analyzes menu structures across VN projects to understand:
- Basic menu patterns
- Conditional choices (if clauses)
- Nested menus
- Menu sets and self-pruning
- Decision tree complexity

🚨 CRITICAL: Menu detection rules documented in:
📖 ideas-lab/flow-visualizer-poc/FLOW_VISUALIZER_ARCHITECTURE.md

Key responsibilities:
- Recursive directory search for .rpy files (CRITICAL FIX)
- Menu structure detection and parsing
- Nested menu hierarchy support
- SDK-compatible menu analysis

❗ Changes here affect menu container creation in the flow visualizer
"""

import sys
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
from dataclasses import dataclass, field

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

# FlowTracer import temporarily removed to avoid circular dependency
# try:
#     from control_flow.flow_tracer import FlowTracer
# except ImportError as e:
#     print(f"Warning: Could not import control flow components: {e}")
#     # Continue without flow tracer if not available


@dataclass
class MenuChoice:
    """Represents a single menu choice."""
    text: str
    condition: Optional[str] = None  # if clause condition
    destination: Optional[str] = None  # jump/call target
    action_type: Optional[str] = None  # 'jump', 'call', 'return', 'pass', 'continue'
    file_path: str = ""
    line_number: int = 0
    has_variables: bool = False  # Contains $ statements
    has_jumps: bool = False
    has_calls: bool = False
    nested_menu: bool = False  # Contains another menu
    nested_labels: List[str] = field(default_factory=list)  # Labels defined within this choice
    nested_menu_structures: List['MenuStructure'] = field(default_factory=list)  # Actual nested menu structures
    subsequent_lines: List[str] = field(default_factory=list)  # Lines that follow this choice


@dataclass 
class MenuStructure:
    """Represents a complete menu structure."""
    file_path: str
    line_number: int
    prompt: Optional[str] = None  # Menu question/prompt
    label_name: Optional[str] = None  # If menu has a label
    choices: List[MenuChoice] = field(default_factory=list)
    has_conditions: bool = False
    has_menu_set: bool = False
    menu_set_variable: Optional[str] = None
    nesting_level: int = 0  # How deep this menu is nested
    parent_choice: Optional[MenuChoice] = None  # Parent choice that contains this menu (for nested menus)
    parent_menu: Optional['MenuStructure'] = None  # Parent menu structure (for nested menus)
    label_context: Optional[str] = None  # Label that contains this menu hierarchy


class MenuAnalyzer:
    """Analyzes menu patterns in Renpy VN files."""
    
    def __init__(self):
        self.menu_patterns = {
            'menu_start': re.compile(r'^\s*menu\s*([a-zA-Z_][a-zA-Z0-9_]*)?\s*(\([^)]*\))?\s*:', re.IGNORECASE),
            'menu_set': re.compile(r'^\s*set\s+([a-zA-Z_][a-zA-Z0-9_]*)', re.IGNORECASE),
            'choice': re.compile(r'^\s*"([^"]+)"\s*(\([^)]*\))?\s*(if\s+[^:]+)?\s*:', re.IGNORECASE),
            'jump_call': re.compile(r'^\s*(jump|call)\s+([a-zA-Z_][a-zA-Z0-9_\.]*)', re.IGNORECASE),
            'variable': re.compile(r'^\s*\$\s+', re.IGNORECASE),
            'label': re.compile(r'^\s*label\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*:', re.IGNORECASE),
        }
    
    def analyze_vn_menus(self, vn_path: str) -> Dict[str, Any]:
        """
        Analyze all menu structures in a VN project.
        
        Args:
            vn_path: Path to VN project
            
        Returns:
            Dictionary with comprehensive menu analysis
        """
        analysis = {
            'total_files': 0,
            'total_lines': 0,
            'total_menus': 0,
            'menu_structures': [],
            'menu_complexity': {
                'simple_menus': 0,  # 2-3 choices, no conditions
                'conditional_menus': 0,  # Has if clauses
                'complex_menus': 0,  # 4+ choices or nested
                'menu_sets_used': 0,
                'nested_menus': 0,
            },
            'choice_patterns': {
                'total_choices': 0,
                'conditional_choices': 0,
                'jump_choices': 0,
                'call_choices': 0,
                'variable_choices': 0,
                'inline_choices': 0,  # Choices that don't jump/call
            },
            'files_with_menus': [],
            'menu_locations': [],  # (file, line, complexity)
            'nesting_examples': [],  # Examples of nested menu structures
        }
        
        if not os.path.exists(vn_path):
            analysis['error'] = 'Path does not exist'
            return analysis
        
        try:
            # Find all .rpy files (search recursively in subdirectories)
            game_dir = Path(vn_path) / 'game' if (Path(vn_path) / 'game').exists() else Path(vn_path)
            rpy_files = list(game_dir.rglob('*.rpy'))
            
            analysis['total_files'] = len(rpy_files)
            
            for rpy_file in rpy_files:
                try:
                    file_menus = self._analyze_file_menus(rpy_file)
                    analysis['total_lines'] += file_menus['line_count']
                    analysis['total_menus'] += len(file_menus['menus'])
                    
                    if file_menus['menus']:
                        analysis['files_with_menus'].append((str(rpy_file.name), len(file_menus['menus'])))
                        analysis['menu_structures'].extend(file_menus['menus'])
                        
                        # Add locations for mapping
                        for menu in file_menus['menus']:
                            complexity = self._calculate_menu_complexity(menu)
                            analysis['menu_locations'].append((str(rpy_file.name), menu.line_number, complexity))
                            
                except Exception as e:
                    continue  # Skip problematic files
            
            # Analyze collected menu structures
            self._analyze_menu_patterns(analysis)
            
        except Exception as e:
            analysis['error'] = str(e)
        
        return analysis
    
    def _analyze_file_menus(self, rpy_file: Path) -> Dict[str, Any]:
        """Analyze menus in a single file."""
        result = {
            'line_count': 0,
            'menus': [],
            'file_path': str(rpy_file)
        }
        
        try:
            with open(rpy_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            result['line_count'] = len(lines)
            
            i = 0
            current_label = None
            
            while i < len(lines):
                line = lines[i].strip()
                
                # Track current label for context
                label_match = self.menu_patterns['label'].match(line)
                if label_match:
                    current_label = label_match.group(1)
                    i += 1
                    continue
                
                # Look for menu statements
                menu_match = self.menu_patterns['menu_start'].match(line)
                if menu_match:
                    menu, lines_consumed = self._parse_menu_structure(lines, i, str(rpy_file.name), 0, current_label)
                    if menu:
                        result['menus'].append(menu)
                    i += lines_consumed
                else:
                    i += 1
                    
        except Exception as e:
            pass  # Skip files that can't be read
            
        return result
    
    def _parse_menu_structure(self, lines: List[str], start_idx: int, file_name: str, nesting_level: int = 0, label_context: str = None) -> Tuple[Optional[MenuStructure], int]:
        """Parse a complete menu structure starting from a menu line."""
        menu_line = lines[start_idx].strip()
        menu_match = self.menu_patterns['menu_start'].match(menu_line)
        
        if not menu_match:
            return None, 1
        
        menu = MenuStructure(
            file_path=file_name,
            line_number=start_idx + 1,
            label_name=menu_match.group(1) if menu_match.group(1) else None,
            nesting_level=nesting_level,
            label_context=label_context
        )
        
        i = start_idx + 1
        base_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())
        
        # Look for menu prompt and choices
        while i < len(lines):
            line = lines[i]
            line_stripped = line.strip()
            current_indent = len(line) - len(line.lstrip())
            
            # Stop if we've gone back to the base indentation level
            if line_stripped and current_indent <= base_indent:
                break
            
            # Skip empty lines and comments
            if not line_stripped or line_stripped.startswith('#'):
                i += 1
                continue
            
            # Check for menu set
            set_match = self.menu_patterns['menu_set'].match(line_stripped)
            if set_match:
                menu.has_menu_set = True
                menu.menu_set_variable = set_match.group(1)
                i += 1
                continue
            
            # Check for menu prompt (dialogue line before choices)
            if line_stripped.startswith('"') and ':' not in line_stripped:
                if not menu.choices:  # Only set if no choices found yet
                    menu.prompt = line_stripped.strip('"')
                i += 1
                continue
            
            # Check for menu choice
            choice_match = self.menu_patterns['choice'].match(line_stripped)
            if choice_match:
                choice = MenuChoice(
                    text=choice_match.group(1),
                    condition=choice_match.group(3).strip() if choice_match.group(3) else None,
                    line_number=i + 1
                )
                
                if choice.condition:
                    menu.has_conditions = True
                
                # Parse choice block
                choice_lines_consumed = self._parse_choice_block(lines, i + 1, choice, current_indent, menu.nesting_level + 1, file_name, menu)
                menu.choices.append(choice)
                i += choice_lines_consumed + 1
                continue
            
            i += 1
        
        lines_consumed = i - start_idx
        return menu, lines_consumed
    
    def _parse_choice_block(self, lines: List[str], start_idx: int, choice: MenuChoice, base_indent: int, nesting_level: int, file_name: str, parent_menu: 'MenuStructure') -> int:
        """Parse the block of code following a menu choice."""
        i = start_idx
        
        while i < len(lines):
            line = lines[i]
            line_stripped = line.strip()
            current_indent = len(line) - len(line.lstrip())
            
            # Stop if we've gone back to the base indentation level or lower
            if line_stripped and current_indent <= base_indent:
                break
            
            # Skip empty lines and comments
            if not line_stripped or line_stripped.startswith('#'):
                i += 1
                continue
            
            # Check for nested labels
            label_match = self.menu_patterns['label'].match(line_stripped)
            if label_match:
                label_name = label_match.group(1)
                choice.nested_labels.append(label_name)
                print(f"NESTED: Found nested label '{label_name}' in choice '{choice.text}'")
                i += 1
                continue
            
            # Check for jumps/calls
            jump_call_match = self.menu_patterns['jump_call'].match(line_stripped)
            if jump_call_match:
                action = jump_call_match.group(1).lower()
                target = jump_call_match.group(2)
                choice.destination = target
                
                if action == 'jump':
                    choice.has_jumps = True
                elif action == 'call':
                    choice.has_calls = True
                    
                i += 1
                continue
            
            # Check for variable assignments
            if self.menu_patterns['variable'].match(line_stripped):
                choice.has_variables = True
                i += 1
                continue
            
            # Check for nested menus
            if self.menu_patterns['menu_start'].match(line_stripped):
                choice.nested_menu = True
                
                # Recursively parse the nested menu instead of skipping
                nested_menu, nested_lines_consumed = self._parse_menu_structure(lines, i, file_name, nesting_level, parent_menu.label_context)
                
                if nested_menu:
                    # Set up parent-child relationships
                    nested_menu.parent_choice = choice
                    nested_menu.parent_menu = parent_menu
                    
                    # Store the nested menu in the choice
                    choice.nested_menu_structures.append(nested_menu)
                    
                    print(f"NESTED MENU: Found nested menu at line {i + 1} in choice '{choice.text}', nesting level {nested_menu.nesting_level}, label context: {nested_menu.label_context}")
                
                # Advance past the nested menu
                i += nested_lines_consumed
                continue
            
            i += 1
        
        return i - start_idx
    
    def _calculate_menu_complexity(self, menu: MenuStructure) -> str:
        """Calculate the complexity rating of a menu."""
        choice_count = len(menu.choices)
        
        if choice_count <= 1:
            return 'broken'
        elif choice_count <= 3 and not menu.has_conditions and not any(c.nested_menu for c in menu.choices):
            return 'simple'
        elif menu.has_conditions or menu.has_menu_set:
            return 'conditional'
        elif choice_count >= 4 or any(c.nested_menu for c in menu.choices):
            return 'complex'
        else:
            return 'moderate'
    
    def _analyze_menu_patterns(self, analysis: Dict[str, Any]):
        """Analyze patterns in the collected menu structures."""
        for menu in analysis['menu_structures']:
            complexity = self._calculate_menu_complexity(menu)
            
            # Update complexity counts
            if complexity == 'simple':
                analysis['menu_complexity']['simple_menus'] += 1
            elif complexity == 'conditional':
                analysis['menu_complexity']['conditional_menus'] += 1
            elif complexity in ['complex', 'moderate']:
                analysis['menu_complexity']['complex_menus'] += 1
            
            if menu.has_menu_set:
                analysis['menu_complexity']['menu_sets_used'] += 1
            
            # Analyze choices
            for choice in menu.choices:
                analysis['choice_patterns']['total_choices'] += 1
                
                if choice.condition:
                    analysis['choice_patterns']['conditional_choices'] += 1
                if choice.has_jumps:
                    analysis['choice_patterns']['jump_choices'] += 1
                if choice.has_calls:
                    analysis['choice_patterns']['call_choices'] += 1
                if choice.has_variables:
                    analysis['choice_patterns']['variable_choices'] += 1
                if choice.nested_menu:
                    analysis['menu_complexity']['nested_menus'] += 1
                    # Add to nesting examples
                    if len(analysis['nesting_examples']) < 5:
                        analysis['nesting_examples'].append({
                            'file': menu.file_path,
                            'line': menu.line_number,
                            'choice_text': choice.text,
                            'choice_line': choice.line_number
                        })
                
                # Count inline choices (don't jump/call)
                if not choice.has_jumps and not choice.has_calls:
                    analysis['choice_patterns']['inline_choices'] += 1


def print_menu_analysis(vn_name: str, vn_path: str):
    """Print detailed menu analysis for a VN."""
    print(f"\n🍽️ MENU ANALYSIS: {vn_name}")
    print("=" * 60)
    print(f"📁 Path: {vn_path}")
    
    analyzer = MenuAnalyzer()
    analysis = analyzer.analyze_vn_menus(vn_path)
    
    if 'error' in analysis:
        print(f"❌ Error: {analysis['error']}")
        return analysis
    
    print(f"\n📊 File Statistics:")
    print(f"   • Total .rpy files: {analysis['total_files']}")
    print(f"   • Total lines: {analysis['total_lines']:,}")
    print(f"   • Files with menus: {len(analysis['files_with_menus'])}")
    
    print(f"\n🍽️ Menu Statistics:")
    print(f"   • Total menus found: {analysis['total_menus']}")
    if analysis['total_lines'] > 0:
        menu_density = (analysis['total_menus'] / analysis['total_lines']) * 100
        print(f"   • Menu density: {menu_density:.3f}% (menus per 100 lines)")
    
    # Complexity breakdown
    complexity = analysis['menu_complexity']
    print(f"\n🎯 Menu Complexity:")
    print(f"   • Simple menus: {complexity['simple_menus']}")
    print(f"   • Conditional menus: {complexity['conditional_menus']}")
    print(f"   • Complex menus: {complexity['complex_menus']}")
    print(f"   • Menus with sets: {complexity['menu_sets_used']}")
    print(f"   • Nested menus: {complexity['nested_menus']}")
    
    # Choice patterns
    choices = analysis['choice_patterns']
    print(f"\n🎮 Choice Patterns:")
    print(f"   • Total choices: {choices['total_choices']}")
    print(f"   • Conditional choices: {choices['conditional_choices']}")
    print(f"   • Jump choices: {choices['jump_choices']}")
    print(f"   • Call choices: {choices['call_choices']}")
    print(f"   • Variable choices: {choices['variable_choices']}")
    print(f"   • Inline choices: {choices['inline_choices']}")
    
    if choices['total_choices'] > 0:
        conditional_rate = (choices['conditional_choices'] / choices['total_choices']) * 100
        print(f"   • Conditional rate: {conditional_rate:.1f}%")
    
    # Show files with most menus
    if analysis['files_with_menus']:
        print(f"\n📄 Files with most menus:")
        sorted_files = sorted(analysis['files_with_menus'], key=lambda x: x[1], reverse=True)
        for file_name, menu_count in sorted_files[:5]:
            print(f"   • {file_name}: {menu_count} menus")
    
    # Show nesting examples
    if analysis['nesting_examples']:
        print(f"\n🔄 Nested Menu Examples:")
        for example in analysis['nesting_examples']:
            print(f"   • {example['file']}:{example['line']} - Choice: \"{example['choice_text']}\"")
    
    # Show some example menu locations
    if analysis['menu_locations']:
        print(f"\n📝 Example menu locations:")
        for file_name, line_num, complexity in analysis['menu_locations'][:5]:
            print(f"   • {file_name}:{line_num} ({complexity})")
    
    return analysis


def analyze_multiple_vns():
    """Analyze menu patterns across multiple VNs."""
    vns_to_test = {
        "Savior": r"T:\AG\Savior-0.16c-pc",
        "MySisterMyRoommate": r"T:\AG\MySisterMyRoommateV1.69-pc",
        "TheAlphaGender": r"T:\AG\TheAlphaGender-0.3b-pc",
        "AlisonFalloftheApple": r"T:\AG\AlisonFalloftheApple-1.0-pc",
    }
    
    print("🍽️ VN MENU PATTERN ANALYSIS")
    print("=" * 70)
    print("Analyzing menu structures and decision points across multiple VN projects")
    print("=" * 70)
    
    all_results = {}
    
    for vn_name, vn_path in vns_to_test.items():
        if os.path.exists(vn_path):
            analysis = print_menu_analysis(vn_name, vn_path)
            all_results[vn_name] = analysis
        else:
            print(f"\n❌ {vn_name}: Path not found - {vn_path}")
    
    # Summary comparison
    print(f"\n" + "=" * 70)
    print("📊 COMPARATIVE MENU ANALYSIS")
    print("=" * 70)
    
    if all_results:
        print(f"{'VN Name':<20} {'Files':<8} {'Menus':<8} {'Choices':<8} {'Nested':<8} {'Conditional':<12}")
        print("-" * 70)
        
        for vn_name, analysis in all_results.items():
            if 'error' not in analysis:
                print(f"{vn_name:<20} {analysis['total_files']:<8} "
                      f"{analysis['total_menus']:<8} {analysis['choice_patterns']['total_choices']:<8} "
                      f"{analysis['menu_complexity']['nested_menus']:<8} "
                      f"{analysis['choice_patterns']['conditional_choices']:<12}")
        
        # Overall stats
        total_menus = sum(a['total_menus'] for a in all_results.values() if 'error' not in a)
        total_choices = sum(a['choice_patterns']['total_choices'] for a in all_results.values() if 'error' not in a)
        total_nested = sum(a['menu_complexity']['nested_menus'] for a in all_results.values() if 'error' not in a)
        total_conditional = sum(a['choice_patterns']['conditional_choices'] for a in all_results.values() if 'error' not in a)
        
        print(f"\n📈 Overall Statistics:")
        print(f"   • Total menus across all VNs: {total_menus}")
        print(f"   • Total choices analyzed: {total_choices}")
        print(f"   • Total nested menus: {total_nested}")
        print(f"   • Total conditional choices: {total_conditional}")
        
        if total_choices > 0:
            conditional_rate = (total_conditional / total_choices) * 100
            nested_rate = (total_nested / total_menus) * 100 if total_menus > 0 else 0
            print(f"   • Overall conditional rate: {conditional_rate:.1f}%")
            print(f"   • Overall nesting rate: {nested_rate:.1f}%")


def main():
    """Main function."""
    if len(sys.argv) > 1:
        vn_name = sys.argv[1]
        # You can add specific VN paths here
        vn_paths = {
            "Savior": r"T:\AG\Savior-0.16c-pc",
            "MySisterMyRoommate": r"T:\AG\MySisterMyRoommateV1.69-pc",
            "TheAlphaGender": r"T:\AG\TheAlphaGender-0.3b-pc",
            "AlisonFalloftheApple": r"T:\AG\AlisonFalloftheApple-1.0-pc",
        }
        
        if vn_name in vn_paths:
            print_menu_analysis(vn_name, vn_paths[vn_name])
        else:
            print(f"VN '{vn_name}' not found. Available: {', '.join(vn_paths.keys())}")
    else:
        analyze_multiple_vns()


if __name__ == "__main__":
    main() 