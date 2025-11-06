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
    print("[AST_MENU_PARSER] ✅ Ren'Py AST successfully imported - using true AST parsing")
except ImportError as e:
    HAS_RENPY_AST = False
    print(f"[AST_MENU_PARSER] Warning: Ren'Py AST not available ({e}), falling back to CMAP + enhanced regex parsing")
except SyntaxError as e:
    HAS_RENPY_AST = False
    print(f"[AST_MENU_PARSER] Warning: Ren'Py AST syntax incompatible ({e}), falling back to CMAP + enhanced regex parsing")

# Import CMAP (Custom Menu AST Parser) as alternative to Ren'Py AST
try:
    from .cmap import CMAPParser, MenuNode as CMAPMenuNode
    HAS_CMAP = True
    print("[AST_MENU_PARSER] ✅ CMAP (Custom Menu AST Parser) available - using Lark-based parsing")
except ImportError as e:
    HAS_CMAP = False
    print(f"[AST_MENU_PARSER] Warning: CMAP not available ({e}), using enhanced regex only")


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
    
    # Nested menu support
    nested_menu_structures: List['EnhancedMenuStructure'] = field(default_factory=list)
    
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
    
    # Parent tracking for nested menus
    parent_menu_line: Optional[int] = None
    parent_choice_index: Optional[int] = None
    is_nested: bool = False


class ASTMenuParser:
    """AST-based menu parser using actual Ren'Py AST structures."""
    
    def __init__(self):
        """Initialize the AST Menu Parser with subprocess-based true AST parsing."""
        self.has_ast = HAS_RENPY_AST
        self.has_cmap = HAS_CMAP
        self.cmap_parser = None
        
        if self.has_cmap:
            # Initialize CMAP parser
            try:
                self.cmap_parser = CMAPParser()
                print("[AST_MENU_PARSER] ✅ CMAP parser initialized successfully")
            except Exception as e:
                print(f"[AST_MENU_PARSER] ⚠️ CMAP parser initialization failed: {e}")
                self.has_cmap = False
                self.cmap_parser = None
        
        self.variable_patterns = {
            'relationship': ['love', 'trust', 'friendship', 'affection', 'romance'],
            'story_flags': ['completed', 'discovered', 'unlocked', 'seen', 'met'],
            'resources': ['money', 'points', 'items', 'health', 'energy'],
            'counters': ['talk', 'visit', 'count', 'times', 'attempts']
        }
    
    def parse_file_menus(self, file_path: str) -> List[EnhancedMenuStructure]:
        """Parse all menus in a file using the best available method."""
        if self.has_ast:
            return self._parse_with_ast(file_path)
        elif self.has_cmap:
            return self._parse_with_cmap(file_path)
        else:
            return self._parse_with_regex_fallback(file_path)
    
    def _parse_with_ast(self, file_path: str) -> List[EnhancedMenuStructure]:
        """Parse menus using true Ren'Py AST via subprocess."""
        if not self.has_ast:
            return self._parse_with_regex_fallback(file_path)
        
        try:
            return self._parse_with_renpy_subprocess(file_path)
        except Exception as e:
            print(f"[AST_MENU_PARSER] AST subprocess failed ({e}), falling back to regex")
            return self._parse_with_regex_fallback(file_path)
    
    def _parse_with_renpy_subprocess(self, file_path: str) -> List[EnhancedMenuStructure]:
        """Use Ren'Py's Python interpreter to parse AST via subprocess."""
        import subprocess
        import json
        import shutil
        from pathlib import Path
        
        # Path to Ren'Py executable and our AST parser script  
        renpy_sdk_dir = Path(__file__).parent / "renpy-8.4.0-sdk"
        renpy_python_exe = renpy_sdk_dir / "lib" / "py3-windows-x86_64" / "python.exe"
        ast_parser_script = Path(__file__).parent / "ast_parser_with_renpy.py"
        
        if not renpy_python_exe.exists():
            raise FileNotFoundError(f"Ren'Py Python executable not found: {renpy_python_exe}")
        
        if not ast_parser_script.exists():
            raise FileNotFoundError(f"AST parser script not found: {ast_parser_script}")
        
        try:
            # Run Ren'Py's standalone Python with our AST parser script
            cmd = [str(renpy_python_exe), str(ast_parser_script), str(file_path)]
            
            print(f"[AST_MENU_PARSER] 🚀 Running true AST parsing with Ren'Py...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(renpy_sdk_dir)
            )
            
            # Print debug messages from stderr (they won't interfere with JSON)
            if result.stderr.strip():
                print(f"[AST_MENU_PARSER] Debug output from Ren'Py AST:")
                for line in result.stderr.strip().split('\n'):
                    if line.strip():
                        print(f"  {line}")
            
            if result.returncode != 0:
                print(f"[AST_MENU_PARSER] Ren'Py Python process failed with return code {result.returncode}")
                print(f"[AST_MENU_PARSER] stderr: {result.stderr}")
                print(f"[AST_MENU_PARSER] stdout: {result.stdout}")
                raise RuntimeError(f"Ren'Py Python process failed: {result.stderr}")
            
            # Parse JSON output from stdout (now clean of debug messages)
            try:
                ast_data = json.loads(result.stdout)
                print(f"[AST_MENU_PARSER] ✅ Successfully parsed JSON from AST subprocess")
                
                if ast_data.get('success'):
                    menus = self._convert_ast_to_enhanced_menus(ast_data, file_path)
                    print(f"[AST_MENU_PARSER] ✅ True AST parsing successful: {len(menus)} menus found")
                    return menus
                else:
                    error_msg = ast_data.get('error', 'Unknown error')
                    print(f"[AST_MENU_PARSER] AST parsing reported failure: {error_msg}")
                    raise RuntimeError(f"AST parsing failed: {error_msg}")
            except json.JSONDecodeError as e:
                print(f"[AST_MENU_PARSER] Failed to parse JSON: {e}")
                print(f"[AST_MENU_PARSER] Raw stdout: {result.stdout[:500]}...")
                print(f"[AST_MENU_PARSER] Raw stderr: {result.stderr[:500]}...")
                raise RuntimeError("Invalid JSON output from Ren'Py AST parser")
        
        except Exception as e:
            print(f"[AST_MENU_PARSER] Subprocess error: {e}")
            raise
    
    def _convert_ast_to_enhanced_menus(self, ast_data: dict, file_path: str) -> List[EnhancedMenuStructure]:
        """Convert AST data to EnhancedMenuStructure objects."""
        menus = []
        
        for stmt in ast_data.get('statements', []):
            if stmt.get('type') == 'Menu':
                menu = EnhancedMenuStructure(
                    file_path=file_path,
                    line_number=stmt.get('line', 0),
                    menu_set=stmt.get('set'),
                    with_statement=stmt.get('with_')
                )
                
                for item_data in stmt.get('items', []):
                    if item_data.get('label'):  # Only process choices with labels
                        choice = EnhancedMenuChoice(
                            text=item_data['label'],
                            line_number=stmt.get('line', 0),
                            choice_index=len(menu.choices),
                            is_conditional=bool(item_data.get('condition')),
                            primary_condition=item_data.get('condition')
                        )
                        
                        # Add destinations from AST analysis
                        for dest in item_data.get('destinations', []):
                            if dest['type'] == 'jump':
                                choice.unconditional_destinations.append(dest['target'])
                        
                        # Analyze condition if present
                        if choice.is_conditional:
                            choice.condition_complexity = self._classify_condition_complexity(choice.primary_condition)
                            choice.referenced_variables = self._extract_variables_from_condition(choice.primary_condition)
                        
                        # Classify choice complexity
                        self._classify_choice_complexity(choice)
                        
                        menu.choices.append(choice)
                
                # Compute menu statistics
                self._compute_menu_statistics(menu)
                
                if menu.choices:  # Only add menus with choices
                    menus.append(menu)
        
        return menus
    
    def _parse_with_ast_old(self, file_path: str) -> List[EnhancedMenuStructure]:
        """Old direct AST parsing method (kept for reference)."""
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
    
    def _parse_with_cmap(self, file_path: str) -> List[EnhancedMenuStructure]:
        """Parse menus using CMAP (Custom Menu AST Parser)."""
        if not self.has_cmap or not self.cmap_parser:
            return self._parse_with_regex_fallback(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"[CMAP] Failed to read file {file_path}: {e}")
            return []
        
        menus = []
        menu_stack = []  # Stack to track menu hierarchy: [(menu_obj, line, indent, end_line)]
        
        # Find all menu definitions in the file
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Check if this is a label definition - if so, clear the menu stack
            # since menus can't be nested across label boundaries
            if line_stripped.startswith('label ') and ':' in line_stripped:
                menu_stack.clear()
            
            if line_stripped.startswith('menu') and ':' in line_stripped:
                # Calculate indentation
                indent_level = len(line) - len(line.lstrip())
                
                # Pop menus from stack that we've exited
                # A menu should be popped if:
                # 1. We're at the same or lower indentation level, OR
                # 2. We've moved past the estimated end line of the menu
                while menu_stack:
                    parent_menu, parent_line, parent_indent, parent_end = menu_stack[-1]
                    # If we're past the parent menu's estimated end, it's not a parent anymore
                    if (i + 1) > parent_end or indent_level <= parent_indent:
                        menu_stack.pop()
                    else:
                        break
                
                # Found a menu definition
                try:
                    cmap_menu = self.cmap_parser.parse_menu_from_lines(lines, i + 1)
                    if cmap_menu:
                        # Convert CMAP menu to EnhancedMenuStructure
                        enhanced_menu = self._convert_cmap_to_enhanced(cmap_menu, file_path, i + 1)
                        
                        # Check if this menu is nested inside another menu's choice
                        if menu_stack:
                            parent_menu, parent_line, parent_indent, parent_end = menu_stack[-1]
                            # This menu is nested - need to find which choice it belongs to
                            choice_idx = self._find_parent_choice_for_nested_menu(
                                parent_menu, i + 1, indent_level, lines
                            )
                            if choice_idx is not None:
                                enhanced_menu.is_nested = True
                                enhanced_menu.parent_menu_line = parent_line
                                enhanced_menu.parent_choice_index = choice_idx
                                # Add to parent choice's nested menus
                                if choice_idx < len(parent_menu.choices):
                                    parent_menu.choices[choice_idx].nested_menu_structures.append(enhanced_menu)
                                    parent_menu.has_nested_menus = True
                                    print(f"[CMAP] ✅ Detected nested menu at line {i + 1} (parent choice {choice_idx} in menu at line {parent_line})")
                        
                        menus.append(enhanced_menu)
                        
                        # Estimate end line for this menu (for stack tracking)
                        end_line = self._estimate_menu_end_line(lines, i, indent_level)
                        menu_stack.append((enhanced_menu, i + 1, indent_level, end_line))
                        
                        print(f"[CMAP] ✅ Parsed menu at line {i + 1} with {len(enhanced_menu.choices)} choices")
                    else:
                        # Show the actual line content where parsing failed
                        problem_line = lines[i].rstrip() if i < len(lines) else "(line not found)"
                        print(f"[CMAP] ⚠️ Failed to parse menu at line {i + 1}, falling back to regex")
                        print(f"[CMAP] Problem line: {problem_line}")
                        # Fall back to regex for this specific menu
                        regex_menu = self._parse_single_menu_regex(lines, i + 1, file_path)
                        if regex_menu:
                            # Check if this menu is nested (same logic as CMAP)
                            if menu_stack:
                                parent_menu, parent_line, parent_indent, parent_end = menu_stack[-1]
                                choice_idx = self._find_parent_choice_for_nested_menu(
                                    parent_menu, i + 1, indent_level, lines
                                )
                                if choice_idx is not None:
                                    regex_menu.is_nested = True
                                    regex_menu.parent_menu_line = parent_line
                                    regex_menu.parent_choice_index = choice_idx
                                    # Add to parent choice's nested menus
                                    if choice_idx < len(parent_menu.choices):
                                        parent_menu.choices[choice_idx].nested_menu_structures.append(regex_menu)
                                        parent_menu.has_nested_menus = True
                                        print(f"[CMAP/REGEX] ✅ Detected nested menu at line {i + 1} (parent choice {choice_idx} in menu at line {parent_line})")
                            
                            menus.append(regex_menu)
                            
                            # Add to stack for tracking
                            end_line = self._estimate_menu_end_line(lines, i, indent_level)
                            menu_stack.append((regex_menu, i + 1, indent_level, end_line))
                except Exception as e:
                    print(f"[CMAP] Error parsing menu at line {i + 1}: {e}")
                    # Fall back to regex for this specific menu
                    try:
                        regex_menu = self._parse_single_menu_regex(lines, i + 1, file_path)
                        if regex_menu:
                            # Check if this menu is nested (same logic as CMAP)
                            if menu_stack:
                                parent_menu, parent_line, parent_indent, parent_end = menu_stack[-1]
                                choice_idx = self._find_parent_choice_for_nested_menu(
                                    parent_menu, i + 1, indent_level, lines
                                )
                                if choice_idx is not None:
                                    regex_menu.is_nested = True
                                    regex_menu.parent_menu_line = parent_line
                                    regex_menu.parent_choice_index = choice_idx
                                    # Add to parent choice's nested menus
                                    if choice_idx < len(parent_menu.choices):
                                        parent_menu.choices[choice_idx].nested_menu_structures.append(regex_menu)
                                        parent_menu.has_nested_menus = True
                                        print(f"[CMAP/REGEX] ✅ Detected nested menu at line {i + 1} (parent choice {choice_idx} in menu at line {parent_line})")
                            
                            menus.append(regex_menu)
                            
                            # Add to stack for tracking
                            end_line = self._estimate_menu_end_line(lines, i, indent_level)
                            menu_stack.append((regex_menu, i + 1, indent_level, end_line))
                    except Exception as regex_e:
                        print(f"[CMAP] Regex fallback also failed: {regex_e}")
        
        print(f"[CMAP] Parsed {len(menus)} menus from {file_path}")
        return menus
    
    def _find_parent_choice_for_nested_menu(self, parent_menu: EnhancedMenuStructure, 
                                           nested_menu_line: int, nested_indent: int, 
                                           lines: List[str]) -> Optional[int]:
        """
        Find which choice in the parent menu contains this nested menu.
        
        Args:
            parent_menu: The parent EnhancedMenuStructure
            nested_menu_line: Line number of the nested menu (1-indexed)
            nested_indent: Indentation level of the nested menu
            lines: All lines in the file
            
        Returns:
            Index of the parent choice, or None if not found
        """
        # Look backwards from the nested menu to find the most recent choice
        # that could contain it (based on line numbers and indentation)
        for choice_idx, choice in enumerate(parent_menu.choices):
            choice_line = choice.line_number
            
            # The nested menu should come after the choice line
            if choice_line < nested_menu_line:
                # Check if this is the closest choice before the nested menu
                # by checking if there's no other choice between them
                is_closest = True
                for other_choice in parent_menu.choices[choice_idx + 1:]:
                    if choice_line < other_choice.line_number < nested_menu_line:
                        is_closest = False
                        break
                
                if is_closest:
                    return choice_idx
        
        # Fallback: return first choice if no better match found
        return 0 if parent_menu.choices else None
    
    def _estimate_menu_end_line(self, lines: List[str], menu_start_idx: int, menu_indent: int) -> int:
        """
        Estimate the end line of a menu based on indentation.
        
        Args:
            lines: All lines in the file
            menu_start_idx: 0-indexed line where menu starts
            menu_indent: Indentation level of the menu statement
            
        Returns:
            Estimated end line (1-indexed)
        """
        current_line = menu_start_idx + 1
        
        while current_line < len(lines):
            line = lines[current_line]
            stripped_line = line.strip()
            
            # Skip empty lines and comments
            if not stripped_line or stripped_line.startswith('#'):
                current_line += 1
                continue
            
            # Check indentation
            line_indent = len(line) - len(line.lstrip())
            
            # If we're back to menu indentation or less, we've exited the menu
            if line_indent <= menu_indent:
                return current_line  # 0-indexed, but we'll use as approximation
            
            current_line += 1
        
        return len(lines)
    
    def _convert_cmap_to_enhanced(self, cmap_menu: 'CMAPMenuNode', file_path: str, line_number: int) -> EnhancedMenuStructure:
        """Convert CMAP MenuNode to EnhancedMenuStructure."""
        enhanced_choices = []
        
        # Convert CMAP choices to enhanced choices
        for choice in cmap_menu.choices:
            # Extract destinations from choice body
            destinations = []
            for statement in choice.body:
                if hasattr(statement, 'target'):  # Jump/Call statements
                    destinations.append(statement.target)
            
            # Analyze condition if present
            condition_text = None
            condition_complexity = "simple"
            if choice.condition:
                condition_text = self._cmap_condition_to_text(choice.condition)
                condition_complexity = self._classify_condition_complexity(condition_text)
            
            enhanced_choice = EnhancedMenuChoice(
                text=choice.text,
                line_number=choice.line_number,
                choice_index=len(enhanced_choices),  # Current index in the list
                is_conditional=choice.is_conditional,
                primary_condition=condition_text,
                unconditional_destinations=destinations,
                conditional_paths=[],  # TODO: Implement if needed
                choice_complexity=condition_complexity
            )
            enhanced_choices.append(enhanced_choice)
        
        # Analyze menu-level properties
        total_paths = sum(len(choice.conditional_paths) + (1 if choice.unconditional_destinations else 0) for choice in enhanced_choices)
        has_complex = any(choice.choice_complexity in ["complex", "dynamic"] for choice in enhanced_choices)
        # Check for nested menus (simplified for now)
        has_nested = False  # TODO: Implement nested menu detection from CMAP
        
        # Determine menu complexity
        if has_complex:
            menu_complexity = "complex"
        elif any(choice.is_conditional for choice in enhanced_choices):
            menu_complexity = "conditional"
        else:
            menu_complexity = "simple"
        
        # Extract referenced variables
        # Extract variables from conditions (simplified for now)
        all_variables = []
        for choice in enhanced_choices:
            if choice.primary_condition:
                variables = self._extract_variables_from_condition(choice.primary_condition)
                all_variables.extend(variables)
        
        return EnhancedMenuStructure(
            file_path=file_path,
            line_number=line_number,
            menu_name=cmap_menu.name,
            menu_set=cmap_menu.set_variable,
            choices=enhanced_choices,
            total_conditional_paths=total_paths,
            has_complex_conditionals=has_complex,
            has_nested_menus=has_nested,
            menu_complexity=menu_complexity,
            referenced_variables=list(set(all_variables))
        )
    
    def _cmap_condition_to_text(self, condition: 'ConditionalExpressionNode') -> str:
        """Convert CMAP conditional expression to text."""
        if condition.is_negated:
            result = f"not {condition.variable}"
        elif condition.operator:
            result = f"{condition.variable} {condition.operator} {condition.value}"
        else:
            result = condition.variable
        
        # Handle chained conditions
        if condition.next_condition:
            next_text = self._cmap_condition_to_text(condition.next_condition)
            result += f" {condition.logical_operator} {next_text}"
        
        return result
    
    def _parse_single_menu_regex(self, lines: List[str], start_line: int, file_path: str) -> Optional[EnhancedMenuStructure]:
        """Parse a single menu using regex (helper for CMAP fallback)."""
        # Use the existing regex parsing method
        # start_line is 1-indexed (from the caller), but _parse_regex_menu expects 0-indexed
        menu = self._parse_regex_menu(lines, start_line - 1, file_path)
        return menu if menu.choices else None
    
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
        menu_indent = len(lines[start_line]) - len(lines[start_line].lstrip())
        
        in_nested_menu = False
        nested_menu_base_indent = None
        
        while current_line < len(lines):
            line = lines[current_line]
            stripped_line = line.strip()
            
            if not stripped_line or stripped_line.startswith('#'):
                current_line += 1
                continue
            
            line_indent = len(line) - len(line.lstrip())
            
            # Check if we're entering a nested menu
            if re.match(r'^\s*menu\s*(?:[a-zA-Z_][a-zA-Z0-9_]*)?\s*(?:\([^)]*\))?\s*:', stripped_line):
                if line_indent > menu_indent and not in_nested_menu:
                    # Entering a nested menu - start skipping
                    in_nested_menu = True
                    nested_menu_base_indent = line_indent
                    current_line += 1
                    continue
            
            # If we're in a nested menu, skip until we're back to the base indent
            if in_nested_menu:
                if line_indent <= nested_menu_base_indent and stripped_line:
                    # Exited nested menu
                    in_nested_menu = False
                    nested_menu_base_indent = None
                    # Don't increment current_line - process this line
                else:
                    # Still in nested menu - skip
                    current_line += 1
                    continue
            
            if base_indent is None:
                base_indent = line_indent
            elif line_indent <= menu_indent and not stripped_line.startswith('"'):
                # End of menu (back to same or lower indentation than menu declaration)
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
        """Find the end of a menu block, respecting nested menus."""
        
        base_indent = None
        current_line = start_line + 1
        menu_indent = len(lines[start_line]) - len(lines[start_line].lstrip())
        
        while current_line < len(lines):
            line = lines[current_line]
            stripped_line = line.strip()
            
            if not stripped_line or stripped_line.startswith('#'):
                current_line += 1
                continue
            
            line_indent = len(line) - len(line.lstrip())
            
            # Check if we've encountered a nested menu
            if re.match(r'^\s*menu\s*(?:[a-zA-Z_][a-zA-Z0-9_]*)?\s*(?:\([^)]*\))?\s*:', stripped_line):
                if line_indent > menu_indent:
                    # This is a nested menu - don't skip it, let it be parsed separately
                    return current_line - 1
            
            if base_indent is None:
                base_indent = line_indent
            elif line_indent <= menu_indent and not stripped_line.startswith('"'):
                # End of menu (back to same or lower indentation than menu declaration)
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
