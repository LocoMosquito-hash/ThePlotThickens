"""
Control Flow Analysis Module for Ren'Py Source API

This module provides tools for analyzing the narrative control flow of Ren'Py
visual novels, including entry point detection, label flow mapping, and
decision point analysis.

Main Components:
- StartLabelFinder: Locates the story entry point (start label)
- FlowTracer: Follows narrative paths through sequential execution
- BranchMapper: Maps all possible story branches (planned)
- MenuAnalyzer: Analyzes decision points and choices (planned)

Usage:
    from app.renpy_source_api.control_flow import StartLabelFinder, FlowTracer
    
    finder = StartLabelFinder(project_path)
    start_location = finder.find_start_label()
    
    tracer = FlowTracer(project_path)
    flow_result = tracer.trace_from_start()
"""

try:
    from .start_label_finder import StartLabelFinder
    from .flow_tracer import FlowTracer, FlowStep, FlowTraceResult
    
    __all__ = [
        "StartLabelFinder",
        "FlowTracer",
        "FlowStep", 
        "FlowTraceResult",
    ]
except ImportError as e:
    # Graceful fallback if imports fail
    print(f"Warning: Could not import control flow components: {e}")
    __all__ = []

__version__ = "0.1.0"
__author__ = "The Plot Thickens Development Team" 