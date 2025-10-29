"""
CMAP - Custom Menu AST Parser

A Lark-based AST parser for Ren'Py menu structures that handles:
- Basic menu choices
- Conditional choices (if statements)
- Nested menus
- Complex conditional expressions
- Proper indentation handling

This is an alternative to regex-based parsing that provides true semantic understanding
of menu structures without requiring Ren'Py SDK dependencies.
"""

from .cmap_parser import CMAPParser
from .cmap_ast import (
    MenuNode,
    MenuChoiceNode,
    ConditionalMenuItemNode,
    ConditionalExpressionNode,
    JumpStatementNode,
    CallStatementNode,
    ReturnStatementNode,
    PassStatementNode,
    PythonStatementNode,
    DialogueStatementNode,
    VariableAssignmentNode,
    NestedMenuNode
)

__all__ = [
    'CMAPParser',
    'MenuNode',
    'MenuChoiceNode', 
    'ConditionalMenuItemNode',
    'ConditionalExpressionNode',
    'JumpStatementNode',
    'CallStatementNode',
    'ReturnStatementNode',
    'PassStatementNode',
    'PythonStatementNode',
    'DialogueStatementNode',
    'VariableAssignmentNode',
    'NestedMenuNode'
]

__version__ = "1.0.0"
__author__ = "The Plot Thickens Development Team"
