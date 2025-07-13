"""
Start Label Finder for Ren'Py Control Flow Analysis

This module provides functionality to locate the 'start' label in Ren'Py projects,
which serves as the primary entry point for story execution when a player begins
a new game.
"""

import os
from typing import Optional, Tuple
from pathlib import Path

try:
    # Try relative imports (when used as package)
    from ..parser import RenpyParser, RenpyLine
    from ..exceptions import RenpyParseError, RenpyProjectError
except ImportError:
    # Fall back to direct imports (when run standalone)
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from parser import RenpyParser, RenpyLine
    from exceptions import RenpyParseError, RenpyProjectError


class StartLabelNotFoundError(RenpyProjectError):
    """Raised when the 'start' label cannot be found in a Ren'Py project."""
    pass


class StartLabelFinder:
    """
    Finds the 'start' label entry point in Ren'Py projects.
    
    The 'start' label is where Ren'Py begins story execution when the player
    clicks "Start Game" from the main menu. This class locates that label
    across all .rpy files in a project.
    """
    
    def __init__(self, project_path: str):
        """
        Initialize the StartLabelFinder.
        
        Args:
            project_path: Path to the Ren'Py project directory (containing .rpy files)
            
        Raises:
            RenpyProjectError: If the project path doesn't exist or isn't a valid Ren'Py project
        """
        self.project_path = str(Path(project_path).resolve())
        self.parser = RenpyParser()
        
        # Validate project path
        if not os.path.exists(self.project_path):
            raise RenpyProjectError(f"Project path does not exist: {self.project_path}")
            
        # Check if this looks like a Ren'Py project
        if not self._is_renpy_project():
            raise RenpyProjectError(f"Directory does not appear to be a Ren'Py project: {self.project_path}")
    
    def _is_renpy_project(self) -> bool:
        """Check if the directory appears to be a Ren'Py project."""
        try:
            rpy_files = self.parser.find_rpy_files(self.project_path)
            return len(rpy_files) > 0
        except Exception:
            return False
    
    def find_start_label(self) -> RenpyLine:
        """
        Find the 'start' label in the Ren'Py project.
        
        Returns:
            RenpyLine: The parsed line containing the 'start' label with full metadata
            
        Raises:
            StartLabelNotFoundError: If no 'start' label is found in any .rpy file
            RenpyParseError: If there are errors parsing .rpy files
        """
        try:
            # Get all .rpy files in the project
            rpy_files = self.parser.find_rpy_files(self.project_path)
            
            if not rpy_files:
                raise StartLabelNotFoundError(f"No .rpy files found in project: {self.project_path}")
            
            # Search through each file for the start label
            for rpy_file in rpy_files:
                file_path = os.path.join(self.project_path, rpy_file)
                
                try:
                    # Parse the file and look for start label
                    parsed_lines = self.parser.parse_file(file_path)
                    
                    for line in parsed_lines:
                        if (line.line_type == 'label' and 
                            line.label_name and 
                            line.label_name.lower() == 'start'):
                            return line
                            
                except Exception as e:
                    # Re-raise parsing errors with context
                    raise RenpyParseError(f"Failed to parse file '{rpy_file}': {str(e)}", file_path)
            
            # If we get here, no start label was found
            raise StartLabelNotFoundError(
                f"No 'start' label found in project '{self.project_path}'. "
                f"Searched {len(rpy_files)} .rpy files: {', '.join(rpy_files)}"
            )
            
        except (StartLabelNotFoundError, RenpyParseError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Wrap unexpected errors
            raise RenpyParseError(f"Unexpected error while searching for start label: {str(e)}")
    
    def get_start_location(self) -> Tuple[str, int]:
        """
        Get the file path and line number of the start label.
        
        Returns:
            Tuple[str, int]: (relative_file_path, line_number)
            
        Raises:
            StartLabelNotFoundError: If no 'start' label is found
        """
        start_line = self.find_start_label()
        
        # Convert absolute path back to relative path
        abs_file_path = start_line.file_path
        try:
            relative_path = os.path.relpath(abs_file_path, self.project_path)
        except ValueError:
            # If relpath fails, use the stored path as-is
            relative_path = abs_file_path
            
        return (relative_path, start_line.line_number)
    
    def validate_start_label(self) -> bool:
        """
        Check if the project has a valid start label.
        
        Returns:
            bool: True if a valid start label exists, False otherwise
        """
        try:
            self.find_start_label()
            return True
        except StartLabelNotFoundError:
            return False
        except Exception:
            # Other errors suggest parsing problems, not just missing start
            return False
    
    def get_project_info(self) -> dict:
        """
        Get basic information about the project and its start label.
        
        Returns:
            dict: Project information including start label location if found
        """
        try:
            rpy_files = self.parser.find_rpy_files(self.project_path)
        except Exception as e:
            rpy_files = []
            
        info = {
            "project_path": self.project_path,
            "total_rpy_files": len(rpy_files),
            "rpy_files": rpy_files,
            "has_start_label": False,
            "start_location": None,
            "start_file": None,
            "start_line": None
        }
        
        try:
            start_line = self.find_start_label()
            relative_path, line_number = self.get_start_location()
            
            info.update({
                "has_start_label": True,
                "start_location": (relative_path, line_number),
                "start_file": relative_path,
                "start_line": line_number
            })
        except Exception:
            # If we can't find start label, info already has has_start_label=False
            pass
            
        return info


# Standalone testing function
def main():
    """Standalone test function for StartLabelFinder."""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python start_label_finder.py <renpy_project_path>")
        sys.exit(1)
    
    project_path = sys.argv[1]
    
    try:
        finder = StartLabelFinder(project_path)
        print(f"Analyzing Ren'Py project: {project_path}")
        
        # Get project info
        info = finder.get_project_info()
        print(f"Found {info['total_rpy_files']} .rpy files")
        
        if info['has_start_label']:
            print(f"✅ Start label found: {info['start_file']}:{info['start_line']}")
            
            # Get the full start label line
            start_line = finder.find_start_label()
            print(f"Content: {start_line.content}")
        else:
            print("❌ No start label found")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 