"""
Flow Tracer for Ren'Py Control Flow Analysis

This module provides functionality to trace the narrative flow of Ren'Py projects,
starting from the start label and following the execution path through dialogue,
statements, and flow control commands.
"""

import re
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from pathlib import Path

try:
    # Try relative imports (when used as package)
    from .start_label_finder import StartLabelFinder, StartLabelNotFoundError
    from ..parser import RenpyParser, RenpyLine
    from ..exceptions import RenpyParseError, RenpyProjectError
except ImportError:
    # Fall back to direct imports (when run standalone)
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from control_flow.start_label_finder import StartLabelFinder, StartLabelNotFoundError
    from parser import RenpyParser, RenpyLine
    from exceptions import RenpyParseError, RenpyProjectError


@dataclass
class FlowStep:
    """Represents a single step in the narrative flow."""
    line_number: int
    file_path: str
    content: str
    statement_type: str
    parsed_data: Optional[Dict[str, Any]] = None


@dataclass
class FlowTraceResult:
    """Results from tracing narrative flow."""
    start_location: Tuple[str, int]
    steps: List[FlowStep]
    stop_reason: str
    stop_location: Optional[Tuple[str, int]] = None
    total_lines_traced: int = 0
    flow_control_encountered: Optional[str] = None


class FlowTracer:
    """
    Traces narrative flow in Ren'Py projects starting from the start label.
    
    This tracer follows the sequential execution of a Ren'Py script, parsing
    each line and continuing until it encounters flow control statements like
    jumps, calls, menus, or returns.
    """
    
    def __init__(self, project_path: str):
        """
        Initialize FlowTracer with a Ren'Py project.
        
        Args:
            project_path: Path to the Ren'Py project root directory
            
        Raises:
            RenpyProjectError: If project is invalid
            StartLabelNotFoundError: If start label cannot be found
        """
        self.project_path = project_path
        self.parser = RenpyParser()
        self.start_finder = StartLabelFinder(project_path)
        
        # Get start location
        self.start_location = self.start_finder.get_start_location()
        
        # Cache for parsed files to avoid re-parsing
        self._file_cache: Dict[str, List[RenpyLine]] = {}
        
        # Statement type patterns
        self.statement_patterns = {
            'dialogue': re.compile(r'^\s*".*"', re.IGNORECASE),
            'character_dialogue': re.compile(r'^\s*(\w+)\s+".*"', re.IGNORECASE),
            'jump': re.compile(r'^\s*jump\s+(\w+)', re.IGNORECASE),
            'call': re.compile(r'^\s*call\s+(\w+)', re.IGNORECASE),
            'return': re.compile(r'^\s*return\s*$', re.IGNORECASE),
            'menu': re.compile(r'^\s*menu:', re.IGNORECASE),
            'label': re.compile(r'^\s*label\s+(\w+):', re.IGNORECASE),
            'scene': re.compile(r'^\s*scene\s+', re.IGNORECASE),
            'show': re.compile(r'^\s*show\s+', re.IGNORECASE),
            'hide': re.compile(r'^\s*hide\s+', re.IGNORECASE),
            'play': re.compile(r'^\s*play\s+', re.IGNORECASE),
            'stop': re.compile(r'^\s*stop\s+', re.IGNORECASE),
            'define': re.compile(r'^\s*define\s+', re.IGNORECASE),
            'default': re.compile(r'^\s*default\s+', re.IGNORECASE),
            'python': re.compile(r'^\s*\$\s+', re.IGNORECASE),
            'comment': re.compile(r'^\s*#', re.IGNORECASE),
            'empty': re.compile(r'^\s*$', re.IGNORECASE),
        }
        
        # Flow control statements that stop tracing
        self.flow_control_statements = {'jump', 'call', 'return', 'menu'}
    
    def _get_file_lines(self, file_path: str) -> List[RenpyLine]:
        """
        Get parsed lines from a file, using cache if available.
        
        Args:
            file_path: Relative path to the .rpy file
            
        Returns:
            List of parsed RenpyLine objects
        """
        if file_path in self._file_cache:
            return self._file_cache[file_path]
        
        full_path = Path(self.project_path) / file_path
        if not full_path.exists():
            raise RenpyParseError(f"File not found: {file_path}")
        
        # Parse the file
        parsed_lines = self.parser.parse_file(str(full_path))
        self._file_cache[file_path] = parsed_lines
        
        return parsed_lines
    
    def _classify_statement(self, content: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Classify a statement and extract relevant data.
        
        Args:
            content: The line content to classify
            
        Returns:
            Tuple of (statement_type, parsed_data)
        """
        content = content.strip()
        
        if not content:
            return 'empty', None
        
        # Check each pattern
        for stmt_type, pattern in self.statement_patterns.items():
            match = pattern.match(content)
            if match:
                parsed_data = None
                
                if stmt_type == 'character_dialogue':
                    parsed_data = {'character': match.group(1)}
                elif stmt_type in ['jump', 'call', 'label']:
                    parsed_data = {'target': match.group(1)}
                
                return stmt_type, parsed_data
        
        # Default to unknown statement
        return 'unknown', None
    
    def trace_flow(self, max_steps: int = 100) -> FlowTraceResult:
        """
        Trace the narrative flow starting from the start label.
        
        Args:
            max_steps: Maximum number of steps to trace (prevents infinite loops)
            
        Returns:
            FlowTraceResult with the traced execution path
        """
        start_file, start_line = self.start_location
        steps: List[FlowStep] = []
        
        try:
            # Get the file containing the start label
            current_file_lines = self._get_file_lines(start_file)
            
            # Start from the start label itself (convert to 0-based index)
            current_line_idx = start_line - 1  # start_line is 1-based, convert to 0-based
            current_file = start_file
            
            step_count = 0
            
            while step_count < max_steps:
                # Check if we're still within the current file
                if current_line_idx >= len(current_file_lines):
                    # End of file reached
                    return FlowTraceResult(
                        start_location=self.start_location,
                        steps=steps,
                        stop_reason="end_of_file",
                        stop_location=(current_file, current_line_idx + 1),
                        total_lines_traced=len(steps)
                    )
                
                # Get current line
                current_renpy_line = current_file_lines[current_line_idx]
                content = current_renpy_line.content.strip()
                
                # Classify the statement
                stmt_type, parsed_data = self._classify_statement(content)
                
                # Create flow step
                step = FlowStep(
                    line_number=current_line_idx + 1,
                    file_path=current_file,
                    content=content,
                    statement_type=stmt_type,
                    parsed_data=parsed_data
                )
                steps.append(step)
                
                # Check if this is a flow control statement
                if stmt_type in self.flow_control_statements:
                    return FlowTraceResult(
                        start_location=self.start_location,
                        steps=steps,
                        stop_reason=f"flow_control_{stmt_type}",
                        stop_location=(current_file, current_line_idx + 1),
                        total_lines_traced=len(steps),
                        flow_control_encountered=stmt_type
                    )
                
                # Special case: if this is the start label, continue (don't stop)
                # Move to next line
                current_line_idx += 1
                step_count += 1
            
            # Max steps reached
            return FlowTraceResult(
                start_location=self.start_location,
                steps=steps,
                stop_reason="max_steps_reached",
                stop_location=(current_file, current_line_idx + 1),
                total_lines_traced=len(steps)
            )
            
        except Exception as e:
            return FlowTraceResult(
                start_location=self.start_location,
                steps=steps,
                stop_reason=f"error: {str(e)}",
                total_lines_traced=len(steps)
            )
    
    def get_flow_summary(self, result: FlowTraceResult) -> Dict[str, Any]:
        """
        Generate a summary of the flow trace results.
        
        Args:
            result: FlowTraceResult from trace_flow()
            
        Returns:
            Dictionary with flow analysis summary
        """
        statement_counts = {}
        dialogue_lines = 0
        
        for step in result.steps:
            stmt_type = step.statement_type
            statement_counts[stmt_type] = statement_counts.get(stmt_type, 0) + 1
            
            if stmt_type in ['dialogue', 'character_dialogue']:
                dialogue_lines += 1
        
        return {
            'start_location': result.start_location,
            'total_lines_traced': result.total_lines_traced,
            'stop_reason': result.stop_reason,
            'stop_location': result.stop_location,
            'flow_control_encountered': result.flow_control_encountered,
            'dialogue_lines': dialogue_lines,
            'statement_counts': statement_counts,
            'files_accessed': list(set(step.file_path for step in result.steps))
        }
    
    def trace_from_start(self, max_steps: int = 100) -> FlowTraceResult:
        """
        Convenience method to trace flow from the start label.
        
        Args:
            max_steps: Maximum number of steps to trace
            
        Returns:
            FlowTraceResult with the traced execution path
        """
        return self.trace_flow(max_steps)


class FlowTracerError(RenpyProjectError):
    """Exception raised when FlowTracer encounters an error."""
    pass


def demo_flow_tracer(project_path: str, max_steps: int = 50):
    """
    Demo function to show FlowTracer capabilities.
    
    Args:
        project_path: Path to Ren'Py project
        max_steps: Maximum steps to trace
    """
    try:
        print(f"=== Flow Tracing: {project_path} ===")
        
        tracer = FlowTracer(project_path)
        result = tracer.trace_flow(max_steps)
        summary = tracer.get_flow_summary(result)
        
        print(f"Start: {result.start_location[0]}:{result.start_location[1]}")
        print(f"Lines traced: {result.total_lines_traced}")
        print(f"Stop reason: {result.stop_reason}")
        
        if result.flow_control_encountered:
            print(f"Flow control: {result.flow_control_encountered}")
        
        print(f"\nStatement breakdown:")
        for stmt_type, count in summary['statement_counts'].items():
            print(f"  {stmt_type}: {count}")
        
        print(f"\nFirst 10 steps:")
        for i, step in enumerate(result.steps[:10]):
            print(f"  {i+1}. [{step.statement_type}] {step.content[:60]}...")
        
        if len(result.steps) > 10:
            print(f"  ... and {len(result.steps) - 10} more steps")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # Simple test when run directly
    import sys
    if len(sys.argv) > 1:
        demo_flow_tracer(sys.argv[1])
    else:
        print("Usage: python flow_tracer.py <project_path>") 