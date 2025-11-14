"""
Conditional Structure Analyzer - Core parsing logic.

This module implements the boundary detection algorithm for finding and
parsing if/elif/else conditional blocks in Ren'Py code.

Phase 1: Boundary detection (COMPLETE)
Phase 2: Content analysis (IN PROGRESS)
"""

import re
from typing import List, Tuple, Optional, Dict
from .conditional_structures import ConditionalBranch, ConditionalBlock


class ConditionalStructureAnalyzer:
    """
    Analyzes conditional blocks (if/elif/else) and returns structural metadata.
    
    Purpose: Central authority for conditional structure parsing
    Used by: CSAP, CMAP, Label Parser, any component dealing with conditionals
    
    Phase 1: Boundary detection only
    Phase 2: Content analysis and context awareness
    """
    
    def __init__(self):
        """Initialize the analyzer with regex patterns for conditional detection."""
        # Pattern to match if/elif/else statements
        # Matches: "if condition:", "elif condition:", "else:"
        # Note: These handle single-line conditions; multi-line handled separately
        self.if_pattern = re.compile(r'^(\s*)if\s+(.+):\s*(?:#.*)?$')
        self.elif_pattern = re.compile(r'^(\s*)elif\s+(.+):\s*(?:#.*)?$')
        self.else_pattern = re.compile(r'^(\s*)else\s*:\s*(?:#.*)?$')
        
        # Pattern for multi-line condition start (no colon at end)
        self.if_multiline_start = re.compile(r'^(\s*)if\s+(.+)$')
        self.elif_multiline_start = re.compile(r'^(\s*)elif\s+(.+)$')
    
    def _extract_multiline_condition(
        self,
        lines: List[str],
        start_idx: int,
        keyword: str
    ) -> Tuple[str, int]:
        """
        Extract a multi-line condition that spans multiple lines.
        
        Example:
            if (condition1 and
                condition2):
                
        Args:
            lines: All lines
            start_idx: Index of line with if/elif keyword
            keyword: 'if' or 'elif'
            
        Returns:
            Tuple of (full_condition, last_line_idx)
        """
        condition_parts = []
        current_idx = start_idx
        
        # Get the first line's condition part
        first_line = lines[start_idx].strip()
        if keyword == 'if':
            # Remove 'if ' prefix
            condition_start = first_line[3:].lstrip()
        else:  # elif
            condition_start = first_line[5:].lstrip()
        
        condition_parts.append(condition_start)
        
        # If it already ends with ':', we're done
        if condition_start.rstrip().endswith(':'):
            return condition_start.rstrip()[:-1].strip(), start_idx
        
        # Otherwise, continue reading lines until we find the colon
        current_idx += 1
        while current_idx < len(lines):
            line = lines[current_idx]
            stripped = line.strip()
            
            if not stripped:
                current_idx += 1
                continue
            
            condition_parts.append(stripped)
            
            if stripped.rstrip().endswith(':'):
                # Found the end
                full_condition = ' '.join(condition_parts)
                # Remove the trailing colon
                full_condition = full_condition.rstrip()[:-1].strip()
                return full_condition, current_idx
            
            current_idx += 1
        
        # Didn't find colon - malformed
        raise ValueError(
            f"Multi-line {keyword} condition starting at line {start_idx} "
            "never terminates with ':'"
        )
    
    def analyze_conditional(
        self, 
        text: str, 
        start_line: int = 0,
        context_stack: Optional[List[str]] = None,
        max_depth: int = 10,
        current_depth: int = 0
    ) -> ConditionalBlock:
        """
        Parse a conditional block and return its structure.
        
        This is the main entry point for conditional analysis. It takes text
        that contains a conditional block and returns a structured representation
        of all branches with their boundaries.
        
        Args:
            text: Text containing conditional (may include surrounding code)
            start_line: Line number where text starts (for accurate location)
            context_stack: Stack of parsing contexts (e.g., ['label', 'menu'])
            max_depth: Maximum recursion depth for nested conditionals
            current_depth: Current recursion depth
            
        Returns:
            ConditionalBlock with:
            - branches: List of (condition, content_lines, line_range)
            - end_line: Where conditional ends
            - indentation_level: Base indentation
            - content_summary: What types of elements found
            
        Raises:
            ValueError: If text doesn't contain a valid conditional
            ValueError: If conditional structure is malformed
            ValueError: If nesting is too deep
        """
        if current_depth > max_depth:
            raise ValueError(
                f"Conditional nesting too deep (max {max_depth}). "
                "Possible infinite recursion."
            )
        
        if context_stack is None:
            context_stack = []
        # Normalize line endings and split
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        lines = text.split('\n')
        
        # Find the first if statement
        if_line_idx = None
        for i, line in enumerate(lines):
            if self.if_pattern.match(line) or self.if_multiline_start.match(line):
                if_line_idx = i
                break
        
        if if_line_idx is None:
            raise ValueError("No 'if' statement found in provided text")
        
        # Detect base indentation from the if statement
        base_indent = self._detect_indentation([lines[if_line_idx]])
        
        # Parse all branches starting from the if statement
        branches = []
        current_idx = if_line_idx
        
        while current_idx < len(lines):
            line = lines[current_idx]
            
            # Check if this is a conditional keyword at the base indentation
            if_match = self.if_pattern.match(line)
            elif_match = self.elif_pattern.match(line)
            else_match = self.else_pattern.match(line)
            
            # Determine which type of branch this is
            if if_match:
                indent = len(if_match.group(1))
                if indent == base_indent:
                    # This is our if statement (should be first)
                    condition = if_match.group(2).strip()
                    branch_start = current_idx
                    branch_keyword_end = current_idx  # Track where keyword line ends
                    
                    # Check for multi-line condition
                    if not condition.endswith(':'):
                        condition, branch_keyword_end = self._extract_multiline_condition(
                            lines, current_idx, 'if'
                        )
                    
                    branch = self._parse_branch_multiline(
                        lines, 
                        branch_start,
                        branch_keyword_end,
                        'if',
                        condition,
                        base_indent
                    )
                    branches.append(branch)
                    current_idx = branch.end_line + 1
                elif indent != base_indent and branches:
                    # Different indentation - we're past the conditional
                    break
                else:
                    current_idx += 1
                    
            elif elif_match:
                indent = len(elif_match.group(1))
                if indent == base_indent:
                    condition = elif_match.group(2).strip()
                    branch_start = current_idx
                    branch_keyword_end = current_idx
                    
                    # Check for multi-line condition
                    if not condition.endswith(':'):
                        condition, branch_keyword_end = self._extract_multiline_condition(
                            lines, current_idx, 'elif'
                        )
                    
                    branch = self._parse_branch_multiline(
                        lines,
                        branch_start,
                        branch_keyword_end,
                        'elif',
                        condition,
                        base_indent
                    )
                    branches.append(branch)
                    current_idx = branch.end_line + 1
                else:
                    # Wrong indentation - end of our conditional
                    break
                    
            elif else_match:
                indent = len(else_match.group(1))
                if indent == base_indent:
                    branch = self._parse_branch(
                        lines,
                        current_idx,
                        'else',
                        None,
                        base_indent
                    )
                    branches.append(branch)
                    current_idx = branch.end_line + 1
                    # else is the last branch
                    break
                else:
                    # Wrong indentation - end of our conditional
                    break
            else:
                # Not a conditional keyword - check if we should stop
                if branches:
                    # We've started parsing branches, check if this line
                    # is at or below base indentation (end of conditional)
                    stripped = line.strip()
                    if stripped and not stripped.startswith('#'):
                        line_indent = len(line) - len(line.lstrip())
                        if line_indent <= base_indent:
                            # End of conditional
                            break
                current_idx += 1
        
        if not branches:
            raise ValueError("Failed to parse any branches from conditional")
        
        # Calculate end line (last branch's end line)
        end_line = branches[-1].end_line
        
        return ConditionalBlock(
            branches=branches,
            start_line=start_line + if_line_idx,
            end_line=start_line + end_line,
            base_indentation=base_indent
        )
    
    def _detect_indentation(self, lines: List[str]) -> int:
        """
        Detect base indentation level from lines.
        
        Handles both spaces and tabs. Converts tabs to 4 spaces for consistency.
        
        Args:
            lines: Lines to analyze
            
        Returns:
            Number of spaces for base indentation
        """
        for line in lines:
            stripped = line.lstrip()
            if stripped and not stripped.startswith('#'):
                # Normalize tabs to spaces (1 tab = 4 spaces)
                normalized_line = line.replace('\t', '    ')
                return len(normalized_line) - len(stripped)
        return 0
    
    def _parse_branch(
        self,
        lines: List[str],
        start_idx: int,
        branch_type: str,
        condition: Optional[str],
        base_indent: int
    ) -> ConditionalBranch:
        """
        Parse a single branch (if/elif/else) and extract its content.
        
        Args:
            lines: All lines of text
            start_idx: Index where branch keyword is
            branch_type: 'if', 'elif', or 'else'
            condition: Condition expression (None for else)
            base_indent: Base indentation of the conditional
            
        Returns:
            ConditionalBranch with content and boundaries
        """
        # Expected indentation for branch content
        content_indent = base_indent + 4  # Standard Python indent
        
        # Find the end of this branch
        end_idx = self._get_block_end(lines, start_idx, base_indent)
        
        # Extract content lines (everything between start and end)
        content_lines = []
        for i in range(start_idx + 1, end_idx + 1):
            if i < len(lines):
                content_lines.append(lines[i])
        
        # Analyze branch content (Phase 2)
        content_flags = self._analyze_branch_content(content_lines, context_stack=[])
        
        return ConditionalBranch(
            branch_type=branch_type,
            condition=condition,
            content_lines=content_lines,
            start_line=start_idx,
            end_line=end_idx,
            indentation=base_indent,
            **content_flags  # Unpack content detection flags
        )
    
    def _parse_branch_multiline(
        self,
        lines: List[str],
        start_idx: int,
        keyword_end_idx: int,
        branch_type: str,
        condition: Optional[str],
        base_indent: int
    ) -> ConditionalBranch:
        """
        Parse a branch that may have a multi-line condition.
        
        Args:
            lines: All lines of text
            start_idx: Index where branch keyword starts
            keyword_end_idx: Index where condition ends (may be > start_idx)
            branch_type: 'if', 'elif', or 'else'
            condition: Condition expression (None for else)
            base_indent: Base indentation of the conditional
            
        Returns:
            ConditionalBranch with content and boundaries
        """
        # Find the end of this branch
        end_idx = self._get_block_end(lines, keyword_end_idx, base_indent)
        
        # Extract content lines (everything after condition line)
        content_lines = []
        for i in range(keyword_end_idx + 1, end_idx + 1):
            if i < len(lines):
                content_lines.append(lines[i])
        
        # Analyze branch content (Phase 2)
        content_flags = self._analyze_branch_content(content_lines, context_stack=[])
        
        # Detect nested conditionals (Phase 2)
        nested_conditionals = self._find_nested_conditionals(
            content_lines,
            base_indent,
            context_stack=[],
            max_depth=10,
            current_depth=0
        )
        
        branch = ConditionalBranch(
            branch_type=branch_type,
            condition=condition,
            content_lines=content_lines,
            start_line=start_idx,
            end_line=end_idx,
            indentation=base_indent,
            **content_flags  # Unpack content detection flags
        )
        
        branch.nested_conditionals = nested_conditionals
        return branch
    
    def _analyze_branch_content(
        self,
        lines: List[str],
        context_stack: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Analyze what types of elements are in this branch.
        
        Phase 2 feature: Detects common Ren'Py constructs within branch content.
        
        Args:
            lines: Content lines from the branch
            
        Returns:
            Dictionary with boolean flags for detected content types
        """
        content_str = '\n'.join(lines)
        
        if context_stack is None:
            context_stack = []
        
        return {
            'contains_menu': self._contains_menu(content_str),
            'contains_choice': self._contains_choice(content_str, context_stack),
            'contains_jump': self._contains_jump(content_str),
            'contains_call': self._contains_call(content_str),
            'contains_screen_element': self._contains_screen_element(content_str),
        }
    
    def _find_nested_conditionals(
        self,
        content_lines: List[str],
        parent_indent: int,
        context_stack: Optional[List[str]] = None,
        max_depth: int = 10,
        current_depth: int = 0
    ) -> List[ConditionalBlock]:
        """
        Find and parse nested conditional blocks within branch content.
        
        Args:
            content_lines: Lines to search for nested conditionals
            parent_indent: Indentation of parent block
            context_stack: Parsing context
            max_depth: Maximum nesting depth
            current_depth: Current nesting depth
            
        Returns:
            List of nested ConditionalBlock objects
        """
        if current_depth >= max_depth:
            return []
        
        if context_stack is None:
            context_stack = []
        
        nested = []
        content_text = '\n'.join(content_lines)
        
        # Look for if statements that are MORE indented than parent
        for i, line in enumerate(content_lines):
            stripped = line.strip()
            if stripped.startswith('if '):
                line_indent = len(line) - len(line.lstrip())
                
                # Must be more indented than parent to be nested
                if line_indent > parent_indent:
                    try:
                        # Try to parse as nested conditional
                        remaining = '\n'.join(content_lines[i:])
                        nested_block = self.analyze_conditional(
                            remaining,
                            start_line=i,
                            context_stack=context_stack + ['conditional'],
                            max_depth=max_depth,
                            current_depth=current_depth + 1
                        )
                        nested.append(nested_block)
                    except (ValueError, IndexError):
                        # Not a valid conditional or parsing failed
                        pass
        
        return nested
    
    def _contains_menu(self, content: str) -> bool:
        """Check if content contains menu definition."""
        # Pattern: "menu" keyword followed by optional name and colon
        # Handles both "menu:" and "menu menu_name:"
        return bool(re.search(r'\bmenu\s*(?:[a-zA-Z_][a-zA-Z0-9_]*)?\s*:', content))
    
    def _contains_choice(self, content: str, context_stack: Optional[List[str]] = None) -> bool:
        """
        Check if content contains menu choice text.
        
        Context-aware: Stricter detection when in menu context.
        """
        # Pattern: quoted string followed by colon (choice pattern)
        has_pattern = bool(re.search(r'^\s*"[^"]+"\s*:', content, re.MULTILINE))
        
        # If we're in a menu context, this is more likely to be a choice
        if context_stack and 'menu' in context_stack:
            return has_pattern
        
        # Outside menu context, be more cautious (could be dictionary, label with string, etc.)
        # Check if there's also a jump/call nearby which is typical for choices
        if has_pattern:
            lines_after_quote = content.split('"')[2:4] if '"' in content else []
            nearby_content = ''.join(lines_after_quote)
            has_action = bool(re.search(r'\b(jump|call|return)\b', nearby_content))
            return has_action
        
        return False
    
    def _contains_jump(self, content: str) -> bool:
        """Check if content contains jump statement."""
        # Pattern: "jump" followed by label name or Jump action
        # Handles both: "jump label" and "Jump("label")"
        return bool(re.search(r'\b(jump\s+[a-zA-Z_][a-zA-Z0-9_]*|Jump\s*\()', content))
    
    def _contains_call(self, content: str) -> bool:
        """Check if content contains call statement."""
        # Pattern: "call" followed by label name or Call action
        # Handles both: "call label" and "Call("label")"
        return bool(re.search(r'\b(call\s+[a-zA-Z_][a-zA-Z0-9_]*|Call\s*\()', content))
    
    def _contains_screen_element(self, content: str) -> bool:
        """Check if content contains screen elements."""
        # Pattern: textbutton, imagebutton, hotspot keywords
        element_keywords = r'\b(textbutton|imagebutton|hotspot)\b'
        return bool(re.search(element_keywords, content))
    
    def _get_block_end(
        self, 
        lines: List[str], 
        start_idx: int, 
        base_indent: int
    ) -> int:
        """
        Find where an indented block ends.
        
        A block ends when we encounter a line at or below the base indentation
        that is not blank and not a comment, OR when we hit another branch
        keyword (elif/else) at the same indentation.
        
        Handles empty branches by returning start_idx if no content found.
        
        Args:
            lines: All lines of text
            start_idx: Index where block starts
            base_indent: Base indentation level
            
        Returns:
            Index of the last line in the block
        """
        last_content_line = start_idx
        found_any_content = False
        
        for i in range(start_idx + 1, len(lines)):
            line = lines[i]
            stripped = line.strip()
            
            # Track blank lines and comments but don't use them as last_content_line
            if not stripped or stripped.startswith('#'):
                # Empty or comment - include in block but don't update last_content_line
                # unless we haven't found any content yet
                if found_any_content:
                    last_content_line = i
                continue
            
            # Calculate indentation (normalize tabs)
            normalized_line = line.replace('\t', '    ')
            current_indent = len(normalized_line) - len(normalized_line.lstrip())
            
            # Check if this is a branch keyword at base indentation
            if current_indent == base_indent:
                if (self.elif_pattern.match(line) or 
                    self.else_pattern.match(line) or
                    self.elif_multiline_start.match(line)):
                    # Next branch starts here
                    return last_content_line
                # Any other statement at base indent - block is done
                return last_content_line
            
            # Check if we've dedented past the block
            if current_indent <= base_indent:
                # Block ended
                return last_content_line
            
            # This line is part of the block content
            last_content_line = i
            found_any_content = True
        
        # Reached end of text
        return last_content_line

