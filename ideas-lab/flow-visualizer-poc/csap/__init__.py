"""
Custom Screen AST Parser (CSAP) for Ren'Py Screen Elements

CSAP provides robust, maintainable parsing of Ren'Py screen clickable elements
using token-based AST parsing instead of fragile regex patterns.

Key Features:
- Accurate parsing of complex screen structures
- Support for all VN syntax variations encountered
- Built-in regression testing
- Extensible grammar for new VN patterns
- Detailed error reporting

Architecture:
- Lark-based grammar definition
- AST node classes for type safety  
- Transformation layer to existing ScreenElement/ScreenStructure
- Comprehensive test suite with VN samples

Usage:
    from csap import CSAPParser
    
    parser = CSAPParser()
    screen_structure = parser.parse_screen_file("path/to/screen.rpy")
"""

__version__ = "1.0.0"
__author__ = "Flow Visualizer Development Team"

try:
    from .csap_parser import CSAPParser
    from .csap_ast import *
    from .csap_exceptions import *
except ImportError:
    from csap_parser import CSAPParser
    from csap_ast import *
    from csap_exceptions import *

__all__ = [
    'CSAPParser',
    'CSAPError',
    'CSAPParseError', 
    'CSAPGrammarError',
    'ScreenNode',
    'ScreenElementNode',
    'TextButtonNode',
    'ImageButtonNode',
    'HotspotNode',
    'ActionNode'
]
