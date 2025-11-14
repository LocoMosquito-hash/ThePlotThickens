"""
Conditional Structure Analyzer (CSA)

A standalone module for parsing conditional blocks (if/elif/else) in Ren'Py code.

This module provides centralized conditional parsing logic that can be used by:
- CSAP (Custom Screen AST Parser)
- CMAP (Custom Menu AST Parser)  
- Label Parser
- Any other component that needs to handle conditionals

Key Features:
- Boundary detection: Finds where conditional blocks start and end
- Branch extraction: Separates if/elif/else branches
- Content analysis: Detects what's inside each branch (Phase 2)
- Context awareness: Better detection based on parsing context (Phase 2)

Usage:
    from CSA import ConditionalStructureAnalyzer, ConditionalBlock
    
    analyzer = ConditionalStructureAnalyzer()
    block = analyzer.analyze_conditional(text, start_line=0)
    
    for branch in block.branches:
        print(f"{branch.branch_type}: {branch.condition}")
        print(f"  Lines {branch.start_line}-{branch.end_line}")
"""

from .conditional_structures import ConditionalBranch, ConditionalBlock
from .conditional_analyzer import ConditionalStructureAnalyzer

__version__ = "0.1.0"
__all__ = [
    "ConditionalBranch",
    "ConditionalBlock", 
    "ConditionalStructureAnalyzer"
]

