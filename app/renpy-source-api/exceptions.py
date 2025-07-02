"""
Exception classes for Ren'Py source analysis.

This module defines custom exceptions used throughout the Ren'Py analysis API.
"""

class RenpyAnalysisError(Exception):
    """Base exception for Ren'Py analysis errors."""
    pass


class RenpyParseError(RenpyAnalysisError):
    """Exception raised when parsing .rpy files fails."""
    
    def __init__(self, message: str, filename: str = None, line_number: int = None):
        super().__init__(message)
        self.filename = filename
        self.line_number = line_number
        
    def __str__(self):
        base_message = super().__str__()
        if self.filename:
            if self.line_number:
                return f"{base_message} (in {self.filename}:{self.line_number})"
            else:
                return f"{base_message} (in {self.filename})"
        return base_message


class RenpyProjectError(RenpyAnalysisError):
    """Exception raised when there are issues with the Ren'Py project structure."""
    pass


class RenpyDatabaseError(RenpyAnalysisError):
    """Exception raised when there are database-related issues."""
    pass


class RenpyConfigError(RenpyAnalysisError):
    """Exception raised when there are configuration issues."""
    pass 