"""
Control Flow Analysis Module for Ren'Py Source API

This module provides tools for analyzing the narrative control flow of Ren'Py
visual novels, including entry point detection, label flow mapping, and
decision point analysis.

Main Components:
- StartLabelFinder: Locates the story entry point (start label)
- FlowTracer: Follows narrative paths through jumps and calls (planned)
- BranchMapper: Maps all possible story branches (planned)
- MenuAnalyzer: Analyzes decision points and choices (planned)

Usage:
    from app.renpy_source_api.control_flow import StartLabelFinder
    
    finder = StartLabelFinder(project_path)
    start_location = finder.find_start_label()
"""

try:
    from .start_label_finder import StartLabelFinder
    
    __all__ = [
        "StartLabelFinder",
    ]
except ImportError as e:
    # Graceful fallback if imports fail
    print(f"Warning: Could not import control flow components: {e}")
    __all__ = []

__version__ = "0.1.0"
__author__ = "The Plot Thickens Development Team" 