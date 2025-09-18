"""
CSAP Exception Classes

Comprehensive error handling for the Custom Screen AST Parser.
Provides detailed error messages with line/column information.
"""

from typing import Optional


class CSAPError(Exception):
    """Base exception for all CSAP-related errors."""
    
    def __init__(self, message: str, line: Optional[int] = None, column: Optional[int] = None, context: Optional[str] = None):
        self.message = message
        self.line = line
        self.column = column
        self.context = context
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Format the error message with location information."""
        base_msg = f"CSAP Error: {self.message}"
        
        if self.line is not None:
            base_msg += f" (line {self.line}"
            if self.column is not None:
                base_msg += f", column {self.column}"
            base_msg += ")"
        
        if self.context:
            base_msg += f"\nContext: {self.context}"
        
        return base_msg


class CSAPParseError(CSAPError):
    """Error during parsing of screen content."""
    
    def __init__(self, message: str, line: Optional[int] = None, column: Optional[int] = None, 
                 context: Optional[str] = None, expected: Optional[str] = None):
        self.expected = expected
        
        if expected:
            message += f" (expected: {expected})"
        
        super().__init__(message, line, column, context)


class CSAPGrammarError(CSAPError):
    """Error in the grammar definition or parsing rules."""
    pass


class CSAPTransformError(CSAPError):
    """Error during AST transformation."""
    
    def __init__(self, message: str, node_type: Optional[str] = None, **kwargs):
        self.node_type = node_type
        
        if node_type:
            message = f"Transform error for {node_type}: {message}"
        
        super().__init__(message, **kwargs)


class CSAPValidationError(CSAPError):
    """Error during semantic validation of the AST."""
    
    def __init__(self, message: str, validation_type: str, **kwargs):
        self.validation_type = validation_type
        message = f"Validation error ({validation_type}): {message}"
        super().__init__(message, **kwargs)


class CSAPRegressionError(CSAPError):
    """Error indicating a regression from previous regex behavior."""
    
    def __init__(self, message: str, test_case: str, regex_result: str, csap_result: str):
        self.test_case = test_case
        self.regex_result = regex_result
        self.csap_result = csap_result
        
        full_message = (
            f"Regression detected: {message}\n"
            f"Test case: {test_case}\n"
            f"Regex result: {regex_result}\n"
            f"CSAP result: {csap_result}"
        )
        
        super().__init__(full_message)
