"""
Ren'Py Source Analysis API

This package provides tools for analyzing Ren'Py visual novel source files (.rpy)
and extracting meaningful information about dialogue, characters, labels, assets, and branching paths.

Main Components:
- RenpyProject: Main class for analyzing a Ren'Py project
- RenpyParser: Parser for .rpy files  
- RenpyDatabase: Database integration for caching analysis results

Usage:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    
    from app.renpy_source_api.core import RenpyProject
    
    project = RenpyProject("/path/to/renpy/game/folder")
    project.analyze()
    
    # Query project structure
    overview = project.get_project_overview()
    
    # Search dialogue
    results = project.search_dialogue("Hello world")
    
    # Get character stats
    stats = project.get_character_stats()
"""

# Import main components
try:
    from .core import RenpyProject
    from .parser import RenpyParser
    from .database_basic import RenpyDatabase
    from .exceptions import RenpyAnalysisError, RenpyParseError, RenpyProjectError
    
    __all__ = [
        "RenpyProject",
        "RenpyParser", 
        "RenpyDatabase",
        "RenpyAnalysisError",
        "RenpyParseError",
        "RenpyProjectError"
    ]
except ImportError as e:
    # Graceful fallback if imports fail
    print(f"Warning: Could not import Ren'Py API components: {e}")
    __all__ = []

__version__ = "0.1.0"
__author__ = "The Plot Thickens Development Team" 