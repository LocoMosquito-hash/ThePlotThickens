"""
Data structures for representing conditional blocks.

These dataclasses provide a clean interface for representing parsed
conditional structures (if/elif/else blocks) with their metadata.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ConditionalBranch:
    """
    Represents one branch of a conditional (if/elif/else).
    
    This structure contains all information about a single branch including
    its type, condition, content, and location in the source file.
    
    Attributes:
        branch_type: Type of branch - 'if', 'elif', or 'else'
        condition: The condition expression (None for 'else' branches)
        content_lines: Raw lines of code inside this branch
        start_line: Line number where this branch starts (0-indexed)
        end_line: Line number where this branch ends (0-indexed, inclusive)
        indentation: Number of spaces/tabs for base indentation
        
        # Content analysis flags (Phase 2)
        contains_menu: Whether branch contains a menu definition
        contains_choice: Whether branch contains menu choice text
        contains_jump: Whether branch contains jump statement(s)
        contains_call: Whether branch contains call statement(s)
        contains_screen_element: Whether branch contains screen elements
        
        # Nested structure support (Phase 2)
        nested_conditionals: List of nested ConditionalBlock objects
    """
    branch_type: str  # 'if', 'elif', 'else'
    condition: Optional[str]  # None for 'else'
    content_lines: List[str]
    start_line: int
    end_line: int
    indentation: int
    
    # Content analysis (Phase 2 - defaults for Phase 1)
    contains_menu: bool = False
    contains_choice: bool = False
    contains_jump: bool = False
    contains_call: bool = False
    contains_screen_element: bool = False
    
    # Nested conditionals (Phase 2)
    nested_conditionals: List['ConditionalBlock'] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate branch data after initialization."""
        valid_types = ['if', 'elif', 'else']
        if self.branch_type not in valid_types:
            raise ValueError(
                f"Invalid branch_type '{self.branch_type}'. "
                f"Must be one of: {valid_types}"
            )
        
        if self.branch_type == 'else' and self.condition is not None:
            raise ValueError("'else' branches cannot have a condition")
        
        if self.branch_type in ['if', 'elif'] and self.condition is None:
            raise ValueError(f"'{self.branch_type}' branches must have a condition")


@dataclass
class ConditionalBlock:
    """
    Complete conditional structure with all branches.
    
    Represents a full if/elif/else conditional block with metadata about
    all branches and their boundaries.
    
    Attributes:
        branches: List of all branches (if, elif, else) in order
        start_line: Line number where the conditional starts (0-indexed)
        end_line: Line number where the conditional ends (0-indexed, inclusive)
        base_indentation: Base indentation level of the conditional
    """
    branches: List[ConditionalBranch]
    start_line: int
    end_line: int
    base_indentation: int
    
    def __post_init__(self):
        """Validate block structure after initialization."""
        if not self.branches:
            raise ValueError("ConditionalBlock must have at least one branch")
        
        # First branch must be 'if'
        if self.branches[0].branch_type != 'if':
            raise ValueError(
                f"First branch must be 'if', got '{self.branches[0].branch_type}'"
            )
        
        # Validate branch order: if -> elif* -> else?
        seen_else = False
        for i, branch in enumerate(self.branches):
            if seen_else:
                raise ValueError(
                    f"No branches allowed after 'else' (found '{branch.branch_type}' "
                    f"at branch {i})"
                )
            
            if branch.branch_type == 'else':
                seen_else = True
            elif branch.branch_type == 'elif' and i == 0:
                raise ValueError("Cannot start conditional with 'elif'")
    
    def get_all_content(self) -> List[str]:
        """
        Get all content from all branches combined.
        
        Useful for "show all paths" mode where you want to see what could
        possibly happen across all conditional branches.
        
        Returns:
            List of all content lines from all branches
        """
        all_lines = []
        for branch in self.branches:
            all_lines.extend(branch.content_lines)
        return all_lines
    
    def get_branch_count(self) -> int:
        """
        Get the number of branches in this conditional.
        
        Returns:
            Number of branches (if/elif/else)
        """
        return len(self.branches)
    
    def has_jump_in_branch(self, branch_index: int) -> bool:
        """
        Check if a specific branch contains a jump statement.
        
        Args:
            branch_index: Index of the branch to check (0-based)
            
        Returns:
            True if the branch contains at least one jump statement
            
        Raises:
            IndexError: If branch_index is out of range
        """
        if branch_index < 0 or branch_index >= len(self.branches):
            raise IndexError(
                f"Branch index {branch_index} out of range "
                f"(0-{len(self.branches)-1})"
            )
        return self.branches[branch_index].contains_jump
    
    def get_branch(self, branch_type: str) -> Optional[ConditionalBranch]:
        """
        Get the first branch of a specific type.
        
        Args:
            branch_type: Type of branch to find ('if', 'elif', 'else')
            
        Returns:
            First branch of the specified type, or None if not found
        """
        for branch in self.branches:
            if branch.branch_type == branch_type:
                return branch
        return None
    
    def get_all_branches_by_type(self, branch_type: str) -> List[ConditionalBranch]:
        """
        Get all branches of a specific type.
        
        Useful for getting all 'elif' branches when there are multiple.
        
        Args:
            branch_type: Type of branch to find ('if', 'elif', 'else')
            
        Returns:
            List of all branches of the specified type
        """
        return [b for b in self.branches if b.branch_type == branch_type]

