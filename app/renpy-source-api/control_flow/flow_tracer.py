"""
Flow Tracer for Ren'Py Control Flow Analysis

This module provides functionality to trace the narrative flow of Ren'Py projects,
starting from the start label and following the execution path through dialogue,
statements, and flow control commands.
"""

import re
import random
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from pathlib import Path

try:
    # Try relative imports (when used as package)
    from .start_label_finder import StartLabelFinder, StartLabelNotFoundError
    from ..exceptions import RenpyParseError, RenpyProjectError
    # Lazy import to avoid circular dependency
    RenpyParser = None
    RenpyLine = None
except ImportError:
    # Fall back to direct imports (when run standalone)
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from control_flow.start_label_finder import StartLabelFinder, StartLabelNotFoundError
    from exceptions import RenpyParseError, RenpyProjectError
    # Lazy import to avoid circular dependency
    RenpyParser = None
    RenpyLine = None

def _get_parser_classes():
    """Lazy import of parser classes to avoid circular dependency."""
    global RenpyParser, RenpyLine
    if RenpyParser is None:
        try:
            from ..parser import RenpyParser, RenpyLine
        except ImportError:
            from parser import RenpyParser, RenpyLine
    return RenpyParser, RenpyLine


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
    
    def __init__(self, project_path: str, choice_strategy: str = "first", random_seed: Optional[int] = None):
        """
        Initialize FlowTracer with a Ren'Py project.
        
        Args:
            project_path: Path to the Ren'Py project root directory
            choice_strategy: Strategy for menu choice selection ("first" or "random")
            random_seed: Seed for random choice selection (for reproducible results)
            
        Raises:
            RenpyProjectError: If project is invalid
            StartLabelNotFoundError: If start label cannot be found
        """
        self.project_path = project_path
        RenpyParserClass, _ = _get_parser_classes()
        self.parser = RenpyParserClass()
        self.start_finder = StartLabelFinder(project_path)
        
        # Choice selection strategy
        if choice_strategy not in ["first", "random"]:
            raise ValueError("choice_strategy must be 'first' or 'random'")
        self.choice_strategy = choice_strategy
        
        # Set up random seed for reproducible results
        if random_seed is not None:
            random.seed(random_seed)
        
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
            'label': re.compile(r'^\s*label\s+(\w+)\s*(?:\([^)]*\))?\s*:', re.IGNORECASE),
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
        self.flow_control_statements = {'call', 'return'}  # Removed 'jump' and 'menu' to enable following
        
        # Label location cache for jump following
        self._label_cache: Dict[str, Tuple[str, int]] = {}
        self._label_cache_built = False
    
    def _build_label_cache(self) -> None:
        """
        Build a cache of all label locations in the project.
        This enables efficient label lookup for jump following.
        """
        if self._label_cache_built:
            return
            
        try:
            # Find all .rpy files in the project
            from pathlib import Path
            project_root = Path(self.project_path)
            game_dir = project_root / 'game'
            
            if not game_dir.exists():
                # Try project root if game/ doesn't exist
                search_dirs = [project_root]
            else:
                search_dirs = [game_dir]
            
            for search_dir in search_dirs:
                for rpy_file in search_dir.glob('*.rpy'):
                    try:
                        # Use the existing parser instance to get consistent line parsing
                        lines = self.parser.parse_file(str(rpy_file))
                        
                        # Build label cache with first executable line after each label
                        for i, line in enumerate(lines):
                            if line.line_type == 'label' and line.label_name:
                                # Find the next executable line after this label
                                next_executable_idx = i + 1
                                while (next_executable_idx < len(lines) and 
                                       lines[next_executable_idx].line_type in ['comment', 'empty']):
                                    next_executable_idx += 1
                                
                                # Store the relative path and the next executable line index
                                relative_path = rpy_file.relative_to(Path(self.project_path))
                                self._label_cache[line.label_name] = (str(relative_path), next_executable_idx)
                                
                    except Exception as e:
                        # Skip files that can't be parsed
                        continue
            
            self._label_cache_built = True
            
        except Exception as e:
            # Fallback to empty cache if building fails
            self._label_cache = {}
            self._label_cache_built = True
    
    def _find_label_location(self, label_name: str, current_file: Optional[str] = None) -> Optional[Tuple[str, int]]:
        """
        Find the location of a label in the project.
        
        Args:
            label_name: Name of the label to find
            current_file: Current file path for local label resolution
            
        Returns:
            Tuple of (file_path, line_number) if found, None otherwise
        """
        self._build_label_cache()
        
        # Handle local labels (starting with .)
        if label_name.startswith('.') and current_file is not None:
            # Local label - need to find the current global label context
            # For now, we'll try a simple resolution
            local_name = label_name[1:]  # Remove the dot
            
            # Try to find current global label in the current file
            try:
                current_lines = self._get_file_lines(current_file)
                current_global_label = None
                
                for line in current_lines:
                    if line.line_type == 'label' and line.label_name and not line.label_name.startswith('.'):
                        current_global_label = line.label_name
                    elif line.line_type == 'label' and line.label_name == local_name:
                        # Found the local label in current context
                        return (current_file, line.line_number)
                
                # Try global.local format
                if current_global_label:
                    full_label = f"{current_global_label}.{local_name}"
                    if full_label in self._label_cache:
                        return self._label_cache[full_label]
                        
            except Exception:
                pass
        
        # Regular label lookup
        if label_name in self._label_cache:
            return self._label_cache[label_name]
        
        return None

    def _find_next_label_for_implicit_flow(self, current_file: str, current_line_idx: int) -> Optional[Tuple[str, int]]:
        """
        Find the location of the next label in the current file.
        This is used to handle implicit flow when reaching the end of a label.
        """
        current_file_lines = self._get_file_lines(current_file)
        for i in range(current_line_idx + 1, len(current_file_lines)):
            if current_file_lines[i].line_type == 'label':
                return (current_file, i + 1) # Return 1-based line number
        return None

    def _is_explicit_flow_statement(self, stmt_type: str) -> bool:
        """
        Check if a statement type is an explicit flow control statement
        (jump, call, return, menu).
        """
        return stmt_type in self.flow_control_statements or stmt_type == 'menu'

    def _parse_menu_choices(self, current_file_lines: List[RenpyLine], menu_line_idx: int) -> List[Tuple[str, str]]:
        """
        Parse menu choices and return all available choices with their targets.
        
        Args:
            current_file_lines: Lines from the current file
            menu_line_idx: Index of the menu statement line
            
        Returns:
            List of tuples (choice_text, target_action) for all choices found
        """
        choice_pattern = re.compile(r'^\s*"([^"]+)"\s*:', re.IGNORECASE)
        jump_pattern = re.compile(r'^\s*jump\s+(\w+)', re.IGNORECASE)
        label_pattern = re.compile(r'^\s*label\s+(\w+)\s*(?:\([^)]*\))?\s*:', re.IGNORECASE)
        
        choices = []
        i = menu_line_idx + 1
        
        # Get the base indentation level of the menu
        menu_line = current_file_lines[menu_line_idx]
        menu_indent = len(menu_line.content) - len(menu_line.content.lstrip())
        
        # Process lines after the menu
        while i < len(current_file_lines):
            line = current_file_lines[i]
            content = line.content.strip()
            line_indent = len(line.content) - len(line.content.lstrip())
            
            # Stop if we hit a label at the same or lower indentation level than the menu
            # (but continue for nested labels at higher indentation)
            label_match = label_pattern.match(line.content)
            if label_match and line_indent <= menu_indent:
                print(f"STOP: Stopping menu parsing at label '{label_match.group(1)}' (indent {line_indent} <= menu indent {menu_indent})")
                break
            elif label_match and line_indent > menu_indent:
                print(f"LABEL: Found nested label '{label_match.group(1)}' in menu choice (indent {line_indent} > menu indent {menu_indent})")
                # Continue parsing - this is a nested label within a choice
                i += 1
                continue
                
            # Check if this is a choice
            choice_match = choice_pattern.match(content)
            if choice_match:
                choice_text = choice_match.group(1)
                
                # Look for the action on the next line
                if i + 1 < len(current_file_lines):
                    action_line = current_file_lines[i + 1]
                    action_content = action_line.content.strip()
                    
                    # Check for jump statement
                    jump_match = jump_pattern.match(action_content)
                    if jump_match:
                        target = jump_match.group(1)
                        choices.append((choice_text, f"jump {target}"))
                        i += 2  # Skip the action line
                        continue
                    
                    # Check for other actions (return, call, etc.)
                    if action_content.startswith(('return', 'call', 'scene', 'show')):
                        choices.append((choice_text, action_content))
                        i += 2  # Skip the action line
                        continue
                
                # If no valid action found, skip this choice
                i += 1
            else:
                # Not a choice line, move to next
                i += 1
        
        return choices
    
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
        
        # Track visited labels to prevent infinite jump loops
        visited_labels: set = set()
        
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
                    # End of file reached - check for implicit flow to next label
                    next_label_location = self._find_next_label_for_implicit_flow(current_file, current_line_idx)
                    
                    if next_label_location:
                        target_file, target_line = next_label_location
                        
                        # If jumping to a different file, load it  
                        if target_file != current_file:
                            current_file = target_file
                            current_file_lines = self._get_file_lines(current_file)
                        
                        # Jump to the next label (implicit flow)
                        current_line_idx = target_line - 1  # Convert to 0-based index
                        step_count += 1
                        continue
                    else:
                        # No next label found - true end of execution
                        return FlowTraceResult(
                            start_location=self.start_location,
                            steps=steps,
                            stop_reason="end_of_file_no_implicit_flow",
                            stop_location=(current_file, current_line_idx + 1),
                            total_lines_traced=len(steps)
                        )
                
                # Get current line
                current_renpy_line = current_file_lines[current_line_idx]
                content = current_renpy_line.content.strip()
                
                # Check if we've reached a new label while tracing
                if current_renpy_line.line_type == 'label':
                    # We've encountered a new label - check if this is implicit flow
                    if step_count > 0:  # Not the starting label
                        previous_step = steps[-1] if steps else None
                        if previous_step and not self._is_explicit_flow_statement(previous_step.statement_type):
                            # This is implicit flow - add a step to mark it
                            implicit_step = FlowStep(
                                line_number=current_line_idx + 1,
                                file_path=current_file,
                                content=content,
                                statement_type='implicit_flow',
                                parsed_data={'target': current_renpy_line.label_name, 'flow_type': 'implicit'}
                            )
                            steps.append(implicit_step)
                
                # Classify the statement - use both our classifier and the parser's classification
                stmt_type, parsed_data = self._classify_statement(content)
                
                # Handle cases where RenpyParser classified jumps as "choice_jump"
                if current_renpy_line.line_type == 'choice_jump' and stmt_type == 'unknown':
                    stmt_type = 'jump'
                    # Re-parse the jump target
                    jump_match = self.statement_patterns['jump'].match(content)
                    if jump_match:
                        parsed_data = {'target': jump_match.group(1)}
                
                # Also handle return statements that might be classified as "choice_return"
                if current_renpy_line.line_type == 'choice_return' and stmt_type == 'unknown':
                    stmt_type = 'return'
                
                # Create flow step
                step = FlowStep(
                    line_number=current_line_idx + 1,
                    file_path=current_file,
                    content=content,
                    statement_type=stmt_type,
                    parsed_data=parsed_data
                )
                steps.append(step)
                
                # Special handling for jump statements - follow the jump
                if stmt_type == 'jump' and parsed_data and 'target' in parsed_data:
                    target_label = parsed_data['target']
                    
                    # Check for infinite jump loops
                    jump_key = f"{current_file}:{current_line_idx + 1}->{target_label}"
                    if jump_key in visited_labels:
                        return FlowTraceResult(
                            start_location=self.start_location,
                            steps=steps,
                            stop_reason="infinite_jump_loop",
                            stop_location=(current_file, current_line_idx + 1),
                            total_lines_traced=len(steps),
                            flow_control_encountered='jump'
                        )
                    
                    visited_labels.add(jump_key)
                    
                    # Find the target label location
                    target_location = self._find_label_location(target_label, current_file)
                    
                    if target_location is None:
                        # Target label not found - stop tracing
                        return FlowTraceResult(
                            start_location=self.start_location,
                            steps=steps,
                            stop_reason="jump_target_not_found",
                            stop_location=(current_file, current_line_idx + 1),
                            total_lines_traced=len(steps),
                            flow_control_encountered='jump'
                        )
                    
                    # Jump to the target label
                    target_file, target_line = target_location
                    
                    # If jumping to a different file, load it
                    if target_file != current_file:
                        current_file = target_file
                        current_file_lines = self._get_file_lines(current_file)
                    
                    # Jump to the target label line (convert to 0-based index)
                    current_line_idx = target_line - 1
                    step_count += 1
                    continue  # Continue tracing from the jump target
                
                # Special handling for menu statements - follow selected choice
                if stmt_type == 'menu':
                    # Parse all menu choices
                    all_choices = self._parse_menu_choices(current_file_lines, current_line_idx)
                    
                    if not all_choices:
                        # No choices found in menu - stop tracing
                        return FlowTraceResult(
                            start_location=self.start_location,
                            steps=steps,
                            stop_reason="menu_no_choices",
                            stop_location=(current_file, current_line_idx + 1),
                            total_lines_traced=len(steps),
                            flow_control_encountered='menu'
                        )
                    
                    # Select choice based on strategy
                    if self.choice_strategy == "first":
                        selected_choice = all_choices[0]
                    elif self.choice_strategy == "random":
                        selected_choice = random.choice(all_choices)
                    else:
                        # Fallback to first choice
                        selected_choice = all_choices[0]
                    
                    choice_text, action = selected_choice
                    
                    # Add the choice selection as metadata to the current step
                    step.parsed_data = {
                        'choice_selected': choice_text, 
                        'action': action,
                        'strategy': self.choice_strategy,
                        'all_choices': [choice for choice, _ in all_choices],
                        'total_choices': len(all_choices)
                    }
                    
                    # Parse the action to see what to do
                    if action.startswith('jump '):
                        # Extract jump target and handle like a jump
                        jump_target = action.split(' ', 1)[1]
                        
                        # Find the target label location
                        target_location = self._find_label_location(jump_target, current_file)
                        
                        if target_location is None:
                            # Target label not found - stop tracing
                            return FlowTraceResult(
                                start_location=self.start_location,
                                steps=steps,
                                stop_reason="menu_jump_target_not_found",
                                stop_location=(current_file, current_line_idx + 1),
                                total_lines_traced=len(steps),
                                flow_control_encountered='menu'
                            )
                        
                        # Jump to the target label
                        target_file, target_line = target_location
                        
                        # If jumping to a different file, load it
                        if target_file != current_file:
                            current_file = target_file
                            current_file_lines = self._get_file_lines(current_file)
                        
                        # Jump to the target label line (convert to 0-based index)
                        current_line_idx = target_line - 1
                        step_count += 1
                        continue  # Continue tracing from the menu choice target
                    
                    # Handle other actions (return, call, etc.)
                    elif action in ('return', 'call'):
                        return FlowTraceResult(
                            start_location=self.start_location,
                            steps=steps,
                            stop_reason=f"menu_choice_{action}",
                            stop_location=(current_file, current_line_idx + 1),
                            total_lines_traced=len(steps),
                            flow_control_encountered='menu'
                        )
                    
                    # For other actions (scene, show, etc.), continue to next line
                    current_line_idx += 1
                    step_count += 1
                    continue
                
                # Check if this is a flow control statement (excluding jumps and menus, which we handle above)
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