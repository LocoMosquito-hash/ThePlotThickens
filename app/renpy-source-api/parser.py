"""
Ren'Py script parser for extracting project structure and content.

This module provides a lightweight parser for .rpy files that can extract:
- Project structure overview
- Basic dialogue lines
- Character definitions
- Label structure
- Asset references
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime

try:
    # Try relative imports (when used as package)
    from .exceptions import RenpyParseError, RenpyProjectError
except ImportError:
    # Fall back to direct imports (when run standalone)
    from exceptions import RenpyParseError, RenpyProjectError


@dataclass
class RenpyLine:
    """Represents a parsed line from a .rpy file."""
    file_path: str
    line_number: int
    line_type: str  # 'dialogue', 'label', 'menu', 'image', 'scene', 'show', 'play', 'jump', 'call', 'python', 'comment', 'other'
    content: str
    speaker: Optional[str] = None
    dialogue_text: Optional[str] = None
    label_name: Optional[str] = None
    asset_name: Optional[str] = None
    target_label: Optional[str] = None


@dataclass
class ProjectOverview:
    """Summary of a Ren'Py project structure."""
    project_path: str
    total_rpy_files: int
    total_lines: int
    total_dialogue_lines: int
    total_labels: int
    total_menus: int
    total_characters: int
    file_list: List[str]
    character_definitions: Dict[str, str]  # code -> name
    label_list: List[str]
    errors: List[str]


class RenpyParser:
    """
    Parser for Ren'Py script files.
    
    This parser provides basic analysis of .rpy files without requiring
    the full Ren'Py SDK. It uses regex patterns to identify common
    Ren'Py statements and structures.
    """
    
    def __init__(self):
        """Initialize the parser with regex patterns."""
        # Regex patterns for different Ren'Py statements
        self.patterns = {
            'label': re.compile(r'^\s*label\s+([a-zA-Z_][a-zA-Z0-9_]*):', re.IGNORECASE),
            'character_def': re.compile(r'^\s*define\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*Character\s*\(\s*"([^"]*)"', re.IGNORECASE),
            'dialogue': re.compile(r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s+"([^"]+)"', re.IGNORECASE),
            'narrator': re.compile(r'^\s*"([^"]+)"'),
            'menu': re.compile(r'^\s*menu:', re.IGNORECASE),
            'menu_choice': re.compile(r'^\s*"([^"]+)":'),
            'scene': re.compile(r'^\s*scene\s+([a-zA-Z_][a-zA-Z0-9_\s]*)', re.IGNORECASE),
            'show': re.compile(r'^\s*show\s+([a-zA-Z_][a-zA-Z0-9_\s]*)', re.IGNORECASE),
            'image_def': re.compile(r'^\s*image\s+([a-zA-Z_][a-zA-Z0-9_\s]*)\s*=\s*"([^"]*)"', re.IGNORECASE),
            'play_music': re.compile(r'^\s*play\s+music\s+"([^"]*)"', re.IGNORECASE),
            'play_sound': re.compile(r'^\s*play\s+sound\s+"([^"]*)"', re.IGNORECASE),
            'jump': re.compile(r'^\s*jump\s+([a-zA-Z_][a-zA-Z0-9_]*)', re.IGNORECASE),
            'call': re.compile(r'^\s*call\s+([a-zA-Z_][a-zA-Z0-9_]*)', re.IGNORECASE),
            'python': re.compile(r'^\s*python:', re.IGNORECASE),
            'comment': re.compile(r'^\s*#'),
        }
        
        # Files to exclude from analysis (UI/system files)
        self.excluded_files = {
            'screens.rpy', 'gui.rpy', 'options.rpy', '00keymap.rpy', 
            '00action_file.rpy', '00accessibility.rpy', '00auto.rpy',
            '00barvalues.rpy', '00build.rpy', '00console.rpy',
            '00defaults.rpy', '00definitions.rpy', '00director.rpy',
            '00functions.rpy', '00gallery.rpy', '00gltest.rpy',
            '00iap.rpy', '00icon.rpy', '00images.rpy', '00musicroom.rpy',
            '00nvl_mode.rpy', '00preferences.rpy', '00speech.rpy',
            '00splines.rpy', '00start.rpy', '00steam.rpy', '00style.rpy',
            '00themes.rpy', '00updater.rpy', '00voice.rpy'
        }
    
    def find_rpy_files(self, project_path: str) -> List[str]:
        """
        Find all .rpy files in the project directory.
        
        Args:
            project_path: Path to the Ren'Py project (usually the 'game' folder)
            
        Returns:
            List of .rpy file paths relative to the project
        """
        project_dir = Path(project_path)
        if not project_dir.exists():
            raise RenpyProjectError(f"Project directory does not exist: {project_path}")
        
        rpy_files = []
        
        # Search for .rpy files recursively
        for rpy_file in project_dir.glob("**/*.rpy"):
            # Get relative path from project root
            relative_path = rpy_file.relative_to(project_dir)
            
            # Skip excluded system files
            if relative_path.name not in self.excluded_files:
                rpy_files.append(str(relative_path))
        
        return sorted(rpy_files)
    
    def parse_file(self, file_path: str) -> List[RenpyLine]:
        """
        Parse a single .rpy file and extract structured information.
        
        Args:
            file_path: Path to the .rpy file
            
        Returns:
            List of parsed lines with metadata
        """
        parsed_lines = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    parsed_line = self._parse_line(file_path, line_num, line)
                    if parsed_line:
                        parsed_lines.append(parsed_line)
        except UnicodeDecodeError:
            # Try alternative encodings
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    for line_num, line in enumerate(file, 1):
                        parsed_line = self._parse_line(file_path, line_num, line)
                        if parsed_line:
                            parsed_lines.append(parsed_line)
            except Exception as e:
                raise RenpyParseError(f"Failed to read file with any encoding: {e}", file_path)
        except Exception as e:
            raise RenpyParseError(f"Failed to parse file: {e}", file_path)
        
        return parsed_lines
    
    def _parse_line(self, file_path: str, line_num: int, line: str) -> Optional[RenpyLine]:
        """Parse a single line and determine its type and content."""
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            return None
        
        # Check each pattern type
        for pattern_name, pattern in self.patterns.items():
            match = pattern.match(line)
            if match:
                return self._create_renpy_line(file_path, line_num, line, pattern_name, match)
        
        # If no pattern matches, classify as 'other'
        return RenpyLine(
            file_path=file_path,
            line_number=line_num,
            line_type='other',
            content=stripped
        )
    
    def _create_renpy_line(self, file_path: str, line_num: int, line: str, 
                          pattern_name: str, match: re.Match) -> RenpyLine:
        """Create a RenpyLine object based on the pattern match."""
        
        base_line = RenpyLine(
            file_path=file_path,
            line_number=line_num,
            line_type=pattern_name,
            content=line.strip()
        )
        
        if pattern_name == 'label':
            base_line.label_name = match.group(1)
        
        elif pattern_name == 'character_def':
            base_line.speaker = match.group(1)  # Character code
            base_line.dialogue_text = match.group(2)  # Character name
        
        elif pattern_name == 'dialogue':
            base_line.speaker = match.group(1)
            base_line.dialogue_text = match.group(2)
        
        elif pattern_name == 'narrator':
            base_line.speaker = 'narrator'
            base_line.dialogue_text = match.group(1)
        
        elif pattern_name in ['scene', 'show', 'image_def']:
            base_line.asset_name = match.group(1).strip()
        
        elif pattern_name in ['play_music', 'play_sound']:
            base_line.asset_name = match.group(1)
        
        elif pattern_name in ['jump', 'call']:
            base_line.target_label = match.group(1)
        
        elif pattern_name == 'menu_choice':
            base_line.dialogue_text = match.group(1)
        
        return base_line
    
    def analyze_project(self, project_path: str) -> ProjectOverview:
        """
        Analyze a complete Ren'Py project and return an overview.
        
        Args:
            project_path: Path to the Ren'Py project directory
            
        Returns:
            ProjectOverview with summary statistics and structure
        """
        errors = []
        
        try:
            # Find all .rpy files
            rpy_files = self.find_rpy_files(project_path)
            
            # Initialize counters
            total_lines = 0
            total_dialogue_lines = 0
            total_labels = 0
            total_menus = 0
            character_definitions = {}
            label_list = []
            
            # Process each file
            for rpy_file in rpy_files:
                try:
                    file_path = os.path.join(project_path, rpy_file)
                    parsed_lines = self.parse_file(file_path)
                    
                    total_lines += len(parsed_lines)
                    
                    for line in parsed_lines:
                        # Count dialogue lines
                        if line.line_type in ['dialogue', 'narrator']:
                            total_dialogue_lines += 1
                        
                        # Count labels
                        elif line.line_type == 'label':
                            total_labels += 1
                            if line.label_name:
                                label_list.append(line.label_name)
                        
                        # Count menus
                        elif line.line_type == 'menu':
                            total_menus += 1
                        
                        # Collect character definitions
                        elif line.line_type == 'character_def':
                            if line.speaker and line.dialogue_text:
                                character_definitions[line.speaker] = line.dialogue_text
                
                except Exception as e:
                    errors.append(f"Error parsing {rpy_file}: {str(e)}")
            
            return ProjectOverview(
                project_path=project_path,
                total_rpy_files=len(rpy_files),
                total_lines=total_lines,
                total_dialogue_lines=total_dialogue_lines,
                total_labels=total_labels,
                total_menus=total_menus,
                total_characters=len(character_definitions),
                file_list=rpy_files,
                character_definitions=character_definitions,
                label_list=sorted(label_list),
                errors=errors
            )
            
        except Exception as e:
            raise RenpyProjectError(f"Failed to analyze project: {str(e)}") 