#!/usr/bin/env python3
"""
AST-based menu parser for Ren'Py projects.

This module uses the actual Ren'Py AST to parse menu structures,
providing more accurate conditional path detection than regex-based approaches.
"""

import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

# Add the Ren'Py SDK to the path
current_dir = Path(__file__).parent
sdk_path = current_dir / "renpy-8.4.0-sdk"
if sdk_path.exists():
    sys.path.insert(0, str(sdk_path))

try:
    import renpy.parser
    import renpy.ast
    from renpy.lexer import Lexer
    HAS_RENPY_AST = True
except ImportError:
    HAS_RENPY_AST = False
    print("[AST_MENU_PARSER] Warning: Ren'Py AST not available, falling back to regex parsing")


@dataclass
class ConditionalPath:
    """Represents a single conditional path within a choice."""
    condition: str
    destination: str
    action_type: str  # 'jump', 'call', 'return', 'pass'
    line_number: int
    complexity: str = "simple"  # simple, complex, dynamic


@dataclass
class EnhancedMenuChoice:
    """Enhanced menu choice with full conditional path analysis."""
    text: str
    line_number: int
    choice_index: int
    
    # Basic choice properties
    is_conditional: bool = False
    primary_condition: Optional[str] = None
    
    # Multi-path conditional support
    conditional_paths: List[ConditionalPath] = field(default_factory=list)
    unconditional_destinations: List[str] = field(default_factory=list)
    
    # Choice block analysis
    has_nested_conditionals: bool = False
    has_variable_changes: bool = False
    variable_changes: List[str] = field(default_factory=list)
    
    # Complexity analysis
    choice_complexity: str = "simple"  # simple, conditional, complex, dynamic
    estimated_paths: int = 1


@dataclass
class EnhancedMenuStructure:
    """Enhanced menu structure with comprehensive conditional analysis."""
    file_path: str
    line_number: int
    menu_name: Optional[str] = None
    menu_set: Optional[str] = None
    prompt: Optional[str] = None
    
    # Enhanced choice analysis
    choices: List[EnhancedMenuChoice] = field(default_factory=list)
    
    # Menu-level analysis
    total_conditional_paths: int = 0
    has_complex_conditionals: bool = False
    has_nested_menus: bool = False
    menu_complexity: str = "simple"  # simple, conditional, complex, expert
    
    # Variable pattern analysis
    referenced_variables: List[str] = field(default_factory=list)
    variable_patterns: Dict[str, List[str]] = field(default_factory=dict)


class ASTMenuParser:
    """AST-based menu parser using actual Ren'Py AST structures."""
    
    def __init__(self):
        self.has_ast = HAS_RENPY_AST
        self.variable_patterns = {
            'relationship': ['love', 'trust', 'friendship', 'affection', 'romance'],
            'story_flags': ['completed', 'discovered', 'unlocked', 'seen', 'met'],
            'resources': ['money', 'points', 'items', 'health', 'energy'],
            'counters': ['talk', 'visit', 'count', 'times', 'attempts']
        }
    
    def parse_file_menus(self, file_path: str) -> List[EnhancedMenuStructure]:
        """Parse all menus in a file using AST when available."""
        if self.has_ast:
            return self._parse_with_ast(file_path)
        else:
            return self._parse_with_regex_fallback(file_path)
    
    def _parse_with_ast(self, file_path: str) -> List[EnhancedMenuStructure]:
        """Parse menus using the actual Ren'Py AST."""
        menus = []
        
        try:
            # Read and parse the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Use Ren'Py's lexer and parser
            lexer = Lexer(content, file_path)
            statements = renpy.parser.parse_block(lexer)
            
            # Find menu statements
            for stmt in statements:
                if isinstance(stmt, renpy.ast.Menu):
                    menu = self._analyze_ast_menu(stmt, file_path)
                    menus.append(menu)
                    
        except Exception as e:
            print(f"[AST_MENU_PARSER] Error parsing {file_path} with AST: {e}")
            # Fallback to regex parsing
            return self._parse_with_regex_fallback(file_path)
        
        return menus
    
    def _analyze_ast_menu(self, menu_ast: 'renpy.ast.Menu', file_path: str) -> EnhancedMenuStructure:
        """Analyze a menu AST node for comprehensive conditional paths."""
        menu = EnhancedMenuStructure(
            file_path=file_path,
            line_number=menu_ast.linenumber,
            menu_set=menu_ast.set,
        )
        
        # Extract menu name if available
        if hasattr(menu_ast, 'arguments') and menu_ast.arguments:
            # Named menu handling would go here
            pass
        
        # Analyze each menu item
        for choice_idx, (label, condition, block) in enumerate(menu_ast.items):
            if label is None:  # Skip captions
                continue
                
            choice = self._analyze_menu_choice(
                label, condition, block, choice_idx, menu_ast.linenumber, file_path
            )
            menu.choices.append(choice)
        
        # Compute menu-level statistics
        self._compute_menu_statistics(menu)
        
        return menu
    
    def _analyze_menu_choice(self, label: str, condition: str, block: List['renpy.ast.Node'], 
                           choice_idx: int, menu_line: int, file_path: str) -> EnhancedMenuChoice:
        """Analyze a single menu choice for all conditional paths."""
        
        choice = EnhancedMenuChoice(
            text=label,
            line_number=menu_line,
            choice_index=choice_idx,
            is_conditional=(condition != "True"),
            primary_condition=condition if condition != "True" else None
        )
        
        if block:
            # Analyze the choice block for conditional paths
            self._analyze_choice_block(choice, block, file_path)
        
        # Determine choice complexity
        self._classify_choice_complexity(choice)
        
        return choice
    
    def _analyze_choice_block(self, choice: EnhancedMenuChoice, block: List['renpy.ast.Node'], 
                            file_path: str) -> None:
        """Analyze the statements within a choice block."""
        
        for stmt in block:
            if isinstance(stmt, renpy.ast.Jump):
                # Unconditional jump
                choice.unconditional_destinations.append(stmt.target)
                
            elif isinstance(stmt, renpy.ast.Call):
                # Unconditional call
                choice.unconditional_destinations.append(stmt.label)
                
            elif isinstance(stmt, renpy.ast.If):
                # Conditional statement - this creates multiple paths
                choice.has_nested_conditionals = True
                self._analyze_conditional_statement(choice, stmt, file_path)
                
            elif isinstance(stmt, renpy.ast.Python):
                # Python code block - might contain variable changes
                choice.has_variable_changes = True
                self._extract_variable_changes(choice, stmt.code)
    
    def _analyze_conditional_statement(self, choice: EnhancedMenuChoice, 
                                     if_stmt: 'renpy.ast.If', file_path: str) -> None:
        """Analyze an if/elif/else statement for conditional paths."""
        
        for condition, block in if_stmt.entries:
            # Find destinations in this conditional block
            destinations = self._find_destinations_in_block(block)
            
            for dest, action_type in destinations:
                path = ConditionalPath(
                    condition=condition,
                    destination=dest,
                    action_type=action_type,
                    line_number=if_stmt.linenumber,
                    complexity=self._classify_condition_complexity(condition)
                )
                choice.conditional_paths.append(path)
    
    def _find_destinations_in_block(self, block: List['renpy.ast.Node']) -> List[Tuple[str, str]]:
        """Find all jump/call destinations in a block of statements."""
        destinations = []
        
        for stmt in block:
            if isinstance(stmt, renpy.ast.Jump):
                destinations.append((stmt.target, 'jump'))
            elif isinstance(stmt, renpy.ast.Call):
                destinations.append((stmt.label, 'call'))
            elif isinstance(stmt, renpy.ast.Return):
                destinations.append(('return', 'return'))
        
        return destinations
    
    def _extract_variable_changes(self, choice: EnhancedMenuChoice, python_code: str) -> None:
        """Extract variable assignments from Python code."""
        # Simple regex-based extraction for now
        # In a full implementation, we'd use AST parsing on the Python code too
        
        var_patterns = [
            r'(\w+)\s*=\s*',           # Simple assignment
            r'(\w+)\s*\+=\s*',         # Addition assignment
            r'(\w+)\s*-=\s*',          # Subtraction assignment
            r'(\w+)\.append\s*\(',     # List append
            r'(\w+)\[.+\]\s*=\s*',     # Dictionary/list assignment
        ]
        
        for pattern in var_patterns:
            matches = re.findall(pattern, python_code)
            for match in matches:
                if match not in choice.variable_changes:
                    choice.variable_changes.append(match)
    
    def _classify_condition_complexity(self, condition: str) -> str:
        """Classify the complexity of a condition string."""
        if not condition or condition == "True":
            return "simple"
        
        # Count logical operators
        logical_ops = len(re.findall(r'\b(and|or|not)\b', condition))
        
        # Count comparison operators
        comparisons = len(re.findall(r'[<>=!]=?', condition))
        
        # Count function calls
        function_calls = len(re.findall(r'\w+\s*\(', condition))
        
        if function_calls > 0 or logical_ops > 2:
            return "dynamic"
        elif logical_ops > 0 or comparisons > 1:
            return "complex"
        else:
            return "simple"
    
    def _classify_choice_complexity(self, choice: EnhancedMenuChoice) -> None:
        """Classify the overall complexity of a choice."""
        total_paths = len(choice.conditional_paths) + len(choice.unconditional_destinations)
        
        if choice.has_nested_conditionals and total_paths > 3:
            choice.choice_complexity = "dynamic"
        elif choice.has_nested_conditionals or total_paths > 2:
            choice.choice_complexity = "complex"  
        elif choice.is_conditional:
            choice.choice_complexity = "conditional"
        else:
            choice.choice_complexity = "simple"
        
        choice.estimated_paths = max(1, total_paths)
    
    def _compute_menu_statistics(self, menu: EnhancedMenuStructure) -> None:
        """Compute menu-level statistics and classifications."""
        menu.total_conditional_paths = sum(
            len(choice.conditional_paths) + len(choice.unconditional_destinations) 
            for choice in menu.choices
        )
        
        menu.has_complex_conditionals = any(
            choice.choice_complexity in ["complex", "dynamic"] 
            for choice in menu.choices
        )
        
        # Classify overall menu complexity
        complex_choices = sum(1 for choice in menu.choices 
                            if choice.choice_complexity in ["complex", "dynamic"])
        
        if complex_choices > len(menu.choices) // 2:
            menu.menu_complexity = "expert"
        elif complex_choices > 0 or menu.total_conditional_paths > len(menu.choices) * 2:
            menu.menu_complexity = "complex"
        elif any(choice.is_conditional for choice in menu.choices):
            menu.menu_complexity = "conditional"
        else:
            menu.menu_complexity = "simple"
        
        # Extract referenced variables
        all_vars = set()
        for choice in menu.choices:
            if choice.primary_condition:
                all_vars.update(self._extract_variables_from_condition(choice.primary_condition))
            for path in choice.conditional_paths:
                all_vars.update(self._extract_variables_from_condition(path.condition))
            all_vars.update(choice.variable_changes)
        
        menu.referenced_variables = list(all_vars)
        
        # Classify variable patterns
        menu.variable_patterns = self._classify_variable_patterns(menu.referenced_variables)
    
    def _extract_variables_from_condition(self, condition: str) -> List[str]:
        """Extract variable names from a condition string."""
        # Simple regex-based extraction
        # This could be enhanced with proper Python AST parsing
        variables = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', condition)
        
        # Filter out Python keywords and common functions
        python_keywords = {'and', 'or', 'not', 'if', 'else', 'True', 'False', 'None'}
        common_functions = {'len', 'str', 'int', 'float', 'bool', 'max', 'min'}
        
        return [var for var in variables if var not in python_keywords and var not in common_functions]
    
    def _classify_variable_patterns(self, variables: List[str]) -> Dict[str, List[str]]:
        """Classify variables into common patterns."""
        patterns = {}
        
        for pattern_name, keywords in self.variable_patterns.items():
            matching_vars = []
            for var in variables:
                if any(keyword in var.lower() for keyword in keywords):
                    matching_vars.append(var)
            if matching_vars:
                patterns[pattern_name] = matching_vars
        
        return patterns
    
    def _parse_with_regex_fallback(self, file_path: str) -> List[EnhancedMenuStructure]:
        """Fallback regex-based parsing when AST is not available."""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"[AST_MENU_PARSER] Error reading {file_path}: {e}")
            return []
        
        menus = []
        current_line = 0
        
        while current_line < len(lines):
            line = lines[current_line].strip()
            
            # Look for menu declarations
            if re.match(r'^\s*menu\s*(?:[a-zA-Z_][a-zA-Z0-9_]*)?\s*(?:\([^)]*\))?\s*:', line):
                menu = self._parse_regex_menu(lines, current_line, file_path)
                if menu.choices:  # Only add menus with actual choices
                    menus.append(menu)
                
                # Skip to end of menu
                current_line = self._find_menu_end(lines, current_line)
            
            current_line += 1
        
        return menus
    
    def _parse_regex_menu(self, lines: List[str], start_line: int, file_path: str) -> EnhancedMenuStructure:
        """Parse a single menu using regex patterns."""
        
        menu = EnhancedMenuStructure(
            file_path=file_path,
            line_number=start_line + 1
        )
        
        # Parse menu declaration
        menu_line = lines[start_line].strip()
        
        # Check for named menu
        menu_name_match = re.match(r'^\s*menu\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*:', menu_line)
        if menu_name_match:
            menu.menu_name = menu_name_match.group(1)
        
        # Check for menu set
        menu_set_match = re.match(r'^\s*menu\s*\(([^)]+)\)\s*:', menu_line)
        if menu_set_match:
            menu.menu_set = menu_set_match.group(1)
        
        # Parse choices
        current_line = start_line + 1
        choice_index = 0
        base_indent = None
        
        while current_line < len(lines):
            line = lines[current_line]
            stripped_line = line.strip()
            
            if not stripped_line or stripped_line.startswith('#'):
                current_line += 1
                continue
            
            line_indent = len(line) - len(line.lstrip())
            
            if base_indent is None:
                base_indent = line_indent
            elif line_indent <= base_indent and not stripped_line.startswith('"'):
                # End of menu
                break
            
            # Check for choice patterns
            choice_patterns = [
                (r'^\s*"([^"]+)"\s*:', "basic"),
                (r'^\s*"([^"]+)"\s+if\s+(.+)\s*:', "conditional"),
                (r'^\s*"\[([^\]]+)\]"\s*:', "expression"),
                (r'^\s*"\[([^\]]+)\]"\s+if\s+(.+)\s*:', "conditional_expression"),
            ]
            
            choice_match = None
            choice_type = None
            
            for pattern, ctype in choice_patterns:
                match = re.match(pattern, stripped_line)
                if match:
                    choice_match = match
                    choice_type = ctype
                    break
            
            if choice_match:
                choice_text = choice_match.group(1)
                condition = None
                
                if choice_type in ["conditional", "conditional_expression"] and len(choice_match.groups()) > 1:
                    condition = choice_match.group(2).strip()
                
                choice = EnhancedMenuChoice(
                    text=choice_text,
                    line_number=current_line + 1,
                    choice_index=choice_index,
                    is_conditional=(condition is not None),
                    primary_condition=condition
                )
                
                # Parse choice block for destinations
                self._parse_choice_block_regex(choice, lines, current_line + 1, line_indent)
                
                # Classify choice complexity
                self._classify_choice_complexity(choice)
                
                menu.choices.append(choice)
                choice_index += 1
            
            current_line += 1
        
        # Compute menu statistics
        self._compute_menu_statistics(menu)
        
        return menu
    
    def _parse_choice_block_regex(self, choice: EnhancedMenuChoice, lines: List[str], 
                                 start_line: int, base_indent: int) -> None:
        """Parse a choice block using regex to find destinations."""
        
        current_line = start_line
        
        while current_line < len(lines):
            line = lines[current_line]
            stripped_line = line.strip()
            
            if not stripped_line or stripped_line.startswith('#'):
                current_line += 1
                continue
            
            line_indent = len(line) - len(line.lstrip())
            
            # If we're back to menu level or less, stop
            if line_indent <= base_indent:
                break
            
            # Look for jump/call statements
            jump_match = re.search(r'\b(?:jump|call)\s+([a-zA-Z_][a-zA-Z0-9_]*)', stripped_line)
            if jump_match:
                destination = jump_match.group(1)
                action_type = "jump" if "jump" in stripped_line else "call"
                
                # Check if this is inside a conditional
                if re.match(r'^\s*if\s+', stripped_line):
                    # Extract condition
                    if_match = re.match(r'^\s*if\s+(.+?):', stripped_line)
                    if if_match:
                        condition = if_match.group(1).strip()
                        path = ConditionalPath(
                            condition=condition,
                            destination=destination,
                            action_type=action_type,
                            line_number=current_line + 1,
                            complexity=self._classify_condition_complexity(condition)
                        )
                        choice.conditional_paths.append(path)
                        choice.has_nested_conditionals = True
                else:
                    # Unconditional destination
                    choice.unconditional_destinations.append(destination)
            
            # Look for return statements
            if re.search(r'\breturn\b', stripped_line):
                choice.unconditional_destinations.append('return')
            
            # Look for variable assignments
            var_assignments = re.findall(r'(\w+)\s*[+\-*/]?=\s*', stripped_line)
            for var in var_assignments:
                if var not in choice.variable_changes:
                    choice.variable_changes.append(var)
                    choice.has_variable_changes = True
            
            current_line += 1
    
    def _find_menu_end(self, lines: List[str], start_line: int) -> int:
        """Find the end of a menu block."""
        
        base_indent = None
        current_line = start_line + 1
        
        while current_line < len(lines):
            line = lines[current_line]
            stripped_line = line.strip()
            
            if not stripped_line or stripped_line.startswith('#'):
                current_line += 1
                continue
            
            line_indent = len(line) - len(line.lstrip())
            
            if base_indent is None:
                base_indent = line_indent
            elif line_indent <= base_indent and not stripped_line.startswith('"'):
                # End of menu
                return current_line - 1
            
            current_line += 1
        
        return current_line - 1


def test_ast_parser():
    """Test the AST parser on a sample file."""
    parser = ASTMenuParser()
    
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        if os.path.exists(test_file):
            menus = parser.parse_file_menus(test_file)
            
            print(f"\n=== AST Menu Analysis Results ===")
            print(f"File: {test_file}")
            print(f"Found {len(menus)} menus")
            
            for i, menu in enumerate(menus):
                print(f"\nMenu {i+1} (Line {menu.line_number}):")
                print(f"  Complexity: {menu.menu_complexity}")
                print(f"  Total Paths: {menu.total_conditional_paths}")
                print(f"  Choices: {len(menu.choices)}")
                
                if menu.referenced_variables:
                    print(f"  Variables: {', '.join(menu.referenced_variables[:5])}")
                
                for j, choice in enumerate(menu.choices):
                    print(f"    Choice {j+1}: '{choice.text[:30]}...'")
                    print(f"      Complexity: {choice.choice_complexity}")
                    print(f"      Paths: {choice.estimated_paths}")
                    if choice.conditional_paths:
                        print(f"      Conditional paths: {len(choice.conditional_paths)}")
        else:
            print(f"File not found: {test_file}")
    else:
        print("Usage: python ast_menu_parser.py <renpy_file.rpy>")


if __name__ == "__main__":
    test_ast_parser()
