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
from dataclasses import dataclass, field
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
    condition: Optional[str] = None  # For conditional choices


@dataclass
class MenuChoice:
    """Represents a choice within a menu."""
    text: str
    condition: Optional[str] = None
    destination: Optional[str] = None  # jump/call target
    action_type: Optional[str] = None  # 'jump', 'call', 'return', 'pass', 'continue'
    file_path: str = ""
    line_number: int = 0
    subsequent_lines: List[str] = field(default_factory=list)  # Lines that follow this choice


@dataclass
class MenuStructure:
    """Represents a complete menu structure."""
    name: Optional[str] = None
    file_path: str = ""
    line_number: int = 0
    label_context: Optional[str] = None
    choices: List[MenuChoice] = field(default_factory=list)
    total_choices: int = 0


@dataclass
class LabelFlow:
    """Represents navigation flow between labels."""
    source_label: Optional[str] = None
    target_label: str = ""
    flow_type: str = ""  # 'jump', 'call', 'return', 'menu_choice'
    file_path: str = ""
    line_number: int = 0
    context: Optional[str] = None  # Additional context (e.g., choice text for menu flows)
    condition: Optional[str] = None  # Condition if it's a conditional flow


@dataclass
class LabelNode:
    """Represents a label with its connections and metadata."""
    name: str
    file_path: str = ""
    line_number: int = 0
    incoming_flows: List[LabelFlow] = field(default_factory=list)
    outgoing_flows: List[LabelFlow] = field(default_factory=list)
    has_menu: bool = False
    has_dialogue: bool = False
    is_reachable: bool = False
    is_dead_end: bool = False
    flow_complexity: int = 0  # Number of possible paths from this label


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
        self.patterns = {
            # Existing patterns
            'label': re.compile(r'^\s*label\s+([a-zA-Z_][a-zA-Z0-9_]*):', re.IGNORECASE),
            'character_def': re.compile(r'^\s*define\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*Character\s*\(\s*"([^"]*)"', re.IGNORECASE),
            'dialogue': re.compile(r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s+"([^"]+)"', re.IGNORECASE),
            'narrator': re.compile(r'^\s*"([^"]+)"'),
            'menu': re.compile(r'^\s*menu:', re.IGNORECASE),
            'menu_choice': re.compile(r'^\s*"([^"]+)":'),
            
            # Enhanced menu and choice patterns
            'menu_with_name': re.compile(r'^\s*menu\s+([a-zA-Z_][a-zA-Z0-9_]*):', re.IGNORECASE),
            'choice_with_condition': re.compile(r'^\s*"([^"]+)"\s+if\s+(.+):', re.IGNORECASE),
            'choice_jump': re.compile(r'^\s*jump\s+([a-zA-Z_][a-zA-Z0-9_]*)', re.IGNORECASE),
            'choice_call': re.compile(r'^\s*call\s+([a-zA-Z_][a-zA-Z0-9_]*)', re.IGNORECASE),
            'choice_return': re.compile(r'^\s*return', re.IGNORECASE),
            'choice_pass': re.compile(r'^\s*pass', re.IGNORECASE),
            
            # Enhanced asset patterns
            'scene': re.compile(r'^\s*scene\s+([a-zA-Z_][a-zA-Z0-9_\s\-\.]*)', re.IGNORECASE),
            'show': re.compile(r'^\s*show\s+([a-zA-Z_][a-zA-Z0-9_\s\-\.]*)', re.IGNORECASE),
            'hide': re.compile(r'^\s*hide\s+([a-zA-Z_][a-zA-Z0-9_\s\-\.]*)', re.IGNORECASE),
            
            # Image definitions and references
            'image_def': re.compile(r'^\s*image\s+([a-zA-Z_][a-zA-Z0-9_\s\-\.]*)\s*=\s*"([^"]*)"', re.IGNORECASE),
            'image_def_func': re.compile(r'^\s*image\s+([a-zA-Z_][a-zA-Z0-9_\s\-\.]*)\s*=\s*([a-zA-Z_][a-zA-Z0-9_\.]*)\s*\(', re.IGNORECASE),
            
            # Audio patterns
            'play_music': re.compile(r'^\s*play\s+music\s+"([^"]*)"', re.IGNORECASE),
            'play_sound': re.compile(r'^\s*play\s+sound\s+"([^"]*)"', re.IGNORECASE),
            'play_audio': re.compile(r'^\s*play\s+audio\s+"([^"]*)"', re.IGNORECASE),
            'stop_music': re.compile(r'^\s*stop\s+music', re.IGNORECASE),
            'stop_sound': re.compile(r'^\s*stop\s+sound', re.IGNORECASE),
            'stop_audio': re.compile(r'^\s*stop\s+audio', re.IGNORECASE),
            'queue_music': re.compile(r'^\s*queue\s+music\s+"([^"]*)"', re.IGNORECASE),
            'queue_sound': re.compile(r'^\s*queue\s+sound\s+"([^"]*)"', re.IGNORECASE),
            
            # Video patterns
            'play_movie': re.compile(r'^\s*play\s+movie\s+"([^"]*)"', re.IGNORECASE),
            'show_movie': re.compile(r'^\s*show\s+movie\s+"([^"]*)"', re.IGNORECASE),
            
            # Transform and effect patterns
            'transform': re.compile(r'^\s*transform\s+([a-zA-Z_][a-zA-Z0-9_]*)', re.IGNORECASE),
            'with_transition': re.compile(r'^\s*with\s+([a-zA-Z_][a-zA-Z0-9_]*)', re.IGNORECASE),
            
            # Navigation patterns
            'jump': re.compile(r'^\s*jump\s+([a-zA-Z_][a-zA-Z0-9_]*)', re.IGNORECASE),
            'call': re.compile(r'^\s*call\s+([a-zA-Z_][a-zA-Z0-9_]*)', re.IGNORECASE),
            'return': re.compile(r'^\s*return', re.IGNORECASE),
            
            # Special patterns
            'python': re.compile(r'^\s*python:', re.IGNORECASE),
            'comment': re.compile(r'^\s*#'),
            'init': re.compile(r'^\s*init\s+(-?\d+)', re.IGNORECASE),
            
            # Asset references in strings (for comprehensive detection)
            'asset_reference': re.compile(r'"([^"]*\.(png|jpg|jpeg|gif|bmp|webp|mp3|wav|ogg|mp4|webm|avi))"', re.IGNORECASE),
            
            # Additional choice/flow patterns
            'if_statement': re.compile(r'^\s*if\s+(.+):', re.IGNORECASE),
            'elif_statement': re.compile(r'^\s*elif\s+(.+):', re.IGNORECASE),
            'else_statement': re.compile(r'^\s*else:', re.IGNORECASE),
            'while_loop': re.compile(r'^\s*while\s+(.+):', re.IGNORECASE),
        }
        
        # File extensions by category
        self.asset_extensions = {
            'images': {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tga'},
            'audio': {'.mp3', '.wav', '.ogg', '.m4a', '.aac'},
            'video': {'.mp4', '.webm', '.avi', '.mov', '.mkv'},
            'fonts': {'.ttf', '.otf', '.woff', '.woff2'},
            'data': {'.json', '.txt', '.csv', '.xml'}
        }
        
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
            base_line.speaker = match.group(1)
            base_line.dialogue_text = match.group(2)
        elif pattern_name == 'dialogue':
            base_line.speaker = match.group(1)
            base_line.dialogue_text = match.group(2)
        elif pattern_name == 'narrator':
            base_line.speaker = 'narrator'
            base_line.dialogue_text = match.group(1)
        elif pattern_name == 'menu_with_name':
            base_line.label_name = match.group(1)  # Menu name
        elif pattern_name == 'menu_choice':
            base_line.dialogue_text = match.group(1)  # Choice text
        elif pattern_name == 'choice_with_condition':
            base_line.dialogue_text = match.group(1)  # Choice text
            base_line.condition = match.group(2)  # Condition
        elif pattern_name in ['scene', 'show', 'hide']:
            base_line.asset_name = match.group(1).strip()
        elif pattern_name == 'image_def':
            base_line.asset_name = match.group(1).strip()
            if len(match.groups()) > 1:
                # Store the file path as additional info
                base_line.dialogue_text = match.group(2)  # Reusing this field for file path
        elif pattern_name == 'image_def_func':
            base_line.asset_name = match.group(1).strip()
            base_line.dialogue_text = match.group(2)  # Function name
        elif pattern_name in ['play_music', 'play_sound', 'play_audio', 'queue_music', 'queue_sound']:
            base_line.asset_name = match.group(1)
        elif pattern_name in ['play_movie', 'show_movie']:
            base_line.asset_name = match.group(1)
        elif pattern_name in ['transform', 'with_transition']:
            base_line.asset_name = match.group(1)
        elif pattern_name in ['jump', 'call', 'choice_jump', 'choice_call']:
            base_line.target_label = match.group(1)
        elif pattern_name == 'init':
            base_line.dialogue_text = match.group(1)  # Store priority level
        elif pattern_name == 'asset_reference':
            base_line.asset_name = match.group(1)
        elif pattern_name in ['if_statement', 'elif_statement', 'while_loop']:
            base_line.condition = match.group(1)
        
        return base_line
    
    def get_asset_category(self, asset_path: str) -> str:
        """
        Determine the category of an asset based on its file extension.
        
        Args:
            asset_path: Path or name of the asset
            
        Returns:
            Category string ('images', 'audio', 'video', 'fonts', 'data', 'unknown')
        """
        if not asset_path:
            return 'unknown'
        
        # Extract extension
        asset_lower = asset_path.lower()
        
        for category, extensions in self.asset_extensions.items():
            for ext in extensions:
                if asset_lower.endswith(ext):
                    return category
        
        return 'unknown'
    
    def extract_assets_from_line(self, line: RenpyLine) -> List[Dict[str, Any]]:
        """
        Extract asset information from a parsed line.
        
        Args:
            line: Parsed RenpyLine object
            
        Returns:
            List of asset dictionaries with metadata
        """
        assets = []
        
        if not line.asset_name:
            return assets
        
        asset_info = {
            'name': line.asset_name,
            'category': self.get_asset_category(line.asset_name),
            'usage_type': line.line_type,
            'file': line.file_path,
            'line_number': line.line_number,
            'context': line.content
        }
        
        # Add specific metadata based on usage type
        if line.line_type == 'image_def' and line.dialogue_text:
            asset_info['file_path'] = line.dialogue_text
        elif line.line_type == 'image_def_func' and line.dialogue_text:
            asset_info['function'] = line.dialogue_text
        
        assets.append(asset_info)
        
        # Also extract any asset references from the content using regex
        asset_refs = self.patterns['asset_reference'].findall(line.content)
        for asset_ref, ext in asset_refs:
            if asset_ref != line.asset_name:  # Avoid duplicates
                ref_info = {
                    'name': asset_ref,
                    'category': self.get_asset_category(asset_ref),
                    'usage_type': 'reference',
                    'file': line.file_path,
                    'line_number': line.line_number,
                    'context': line.content
                }
                assets.append(ref_info)
        
        return assets
    
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
    
    def parse_menu_structure(self, file_path: str, start_line: int, lines: List[str]) -> MenuStructure:
        """
        Parse a complete menu structure starting from a menu line.
        
        Args:
            file_path: Path to the file containing the menu
            start_line: Line number where the menu starts (1-indexed)
            lines: List of all lines in the file
            
        Returns:
            MenuStructure object with all choices and their destinations
        """
        menu = MenuStructure(
            file_path=file_path,
            line_number=start_line
        )
        
        if start_line - 1 >= len(lines):
            return menu
        
        # Check if this is a named menu
        menu_line = lines[start_line - 1].strip()
        menu_with_name_match = self.patterns['menu_with_name'].match(menu_line)
        if menu_with_name_match:
            menu.name = menu_with_name_match.group(1)
        
        # Parse choices and their actions
        current_line = start_line
        current_choice = None
        indent_level = 0
        
        while current_line < len(lines):
            line = lines[current_line]
            stripped_line = line.strip()
            
            if not stripped_line:
                current_line += 1
                continue
            
            # Calculate indentation to understand structure
            line_indent = len(line) - len(line.lstrip())
            
            # Check for menu choice
            choice_match = self.patterns['menu_choice'].match(line)
            choice_cond_match = self.patterns['choice_with_condition'].match(line)
            
            if choice_match:
                # Save previous choice if exists
                if current_choice:
                    menu.choices.append(current_choice)
                
                # Create new choice
                current_choice = MenuChoice(
                    text=choice_match.group(1),
                    file_path=file_path,
                    line_number=current_line + 1
                )
                indent_level = line_indent
                
            elif choice_cond_match:
                # Save previous choice if exists
                if current_choice:
                    menu.choices.append(current_choice)
                
                # Create new conditional choice
                current_choice = MenuChoice(
                    text=choice_cond_match.group(1),
                    condition=choice_cond_match.group(2),
                    file_path=file_path,
                    line_number=current_line + 1
                )
                indent_level = line_indent
                
            elif current_choice and line_indent > indent_level:
                # This line belongs to the current choice
                parsed_line = self._parse_line(file_path, current_line + 1, line)
                
                if parsed_line:
                    current_choice.subsequent_lines.append(stripped_line)
                    
                    # Check for action types
                    if parsed_line.line_type in ['jump', 'choice_jump']:
                        current_choice.action_type = 'jump'
                        current_choice.destination = parsed_line.target_label
                    elif parsed_line.line_type in ['call', 'choice_call']:
                        current_choice.action_type = 'call'
                        current_choice.destination = parsed_line.target_label
                    elif parsed_line.line_type in ['return', 'choice_return']:
                        current_choice.action_type = 'return'
                    elif parsed_line.line_type in ['choice_pass']:
                        current_choice.action_type = 'pass'
                        
            elif line_indent <= indent_level and current_choice:
                # We've moved back to menu level or beyond, end current choice
                menu.choices.append(current_choice)
                current_choice = None
                
                # Check if we're out of the menu entirely
                if not stripped_line.startswith('"') and not stripped_line.startswith('menu'):
                    break
            
            current_line += 1
        
        # Add final choice if it exists
        if current_choice:
            menu.choices.append(current_choice)
        
        menu.total_choices = len(menu.choices)
        return menu
    
    def find_all_menus(self, project_path: str) -> List[MenuStructure]:
        """
        Find and parse all menu structures in the project.
        
        Args:
            project_path: Path to the Ren'Py project
            
        Returns:
            List of all MenuStructure objects found
        """
        menus = []
        current_label = None
        
        try:
            rpy_files = self.find_rpy_files(project_path)
            
            for rpy_file in rpy_files:
                file_path = os.path.join(project_path, rpy_file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        lines = file.readlines()
                except UnicodeDecodeError:
                    try:
                        with open(file_path, 'r', encoding='latin-1') as file:
                            lines = file.readlines()
                    except Exception:
                        continue  # Skip problematic files
                
                for line_num, line in enumerate(lines, 1):
                    stripped_line = line.strip()
                    
                    # Track current label for context
                    label_match = self.patterns['label'].match(line)
                    if label_match:
                        current_label = label_match.group(1)
                    
                    # Check for menu start
                    if (self.patterns['menu'].match(line) or 
                        self.patterns['menu_with_name'].match(line)):
                        
                        menu = self.parse_menu_structure(file_path, line_num, lines)
                        menu.label_context = current_label
                        menus.append(menu)
        
        except Exception as e:
            raise RenpyParseError(f"Failed to find menus: {str(e)}")
        
        return menus
    
    def find_all_label_flows(self, project_path: str) -> List[LabelFlow]:
        """
        Find all navigation flows between labels (jumps, calls, returns).
        
        Args:
            project_path: Path to the Ren'Py project
            
        Returns:
            List of all LabelFlow objects found
        """
        flows = []
        current_label = None
        
        try:
            rpy_files = self.find_rpy_files(project_path)
            
            for rpy_file in rpy_files:
                file_path = os.path.join(project_path, rpy_file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        lines = file.readlines()
                except UnicodeDecodeError:
                    try:
                        with open(file_path, 'r', encoding='latin-1') as file:
                            lines = file.readlines()
                    except Exception:
                        continue  # Skip problematic files
                
                for line_num, line in enumerate(lines, 1):
                    stripped_line = line.strip()
                    
                    # Track current label for context
                    label_match = self.patterns['label'].match(line)
                    if label_match:
                        current_label = label_match.group(1)
                        continue
                    
                    # Find direct jumps and calls
                    jump_match = self.patterns['jump'].match(line)
                    if jump_match:
                        flows.append(LabelFlow(
                            source_label=current_label,
                            target_label=jump_match.group(1),
                            flow_type='jump',
                            file_path=file_path,
                            line_number=line_num
                        ))
                    
                    call_match = self.patterns['call'].match(line)
                    if call_match:
                        flows.append(LabelFlow(
                            source_label=current_label,
                            target_label=call_match.group(1),
                            flow_type='call',
                            file_path=file_path,
                            line_number=line_num
                        ))
                    
                    # Find return statements
                    if self.patterns['return'].match(line):
                        flows.append(LabelFlow(
                            source_label=current_label,
                            target_label='<return>',
                            flow_type='return',
                            file_path=file_path,
                            line_number=line_num
                        ))
                
                # Add flows from menu choices
                menus = self.find_all_menus(project_path)
                for menu in menus:
                    for choice in menu.choices:
                        if choice.destination:
                            flows.append(LabelFlow(
                                source_label=menu.label_context,
                                target_label=choice.destination,
                                flow_type='menu_choice',
                                file_path=choice.file_path,
                                line_number=choice.line_number,
                                context=choice.text,
                                condition=choice.condition
                            ))
        
        except Exception as e:
            raise RenpyParseError(f"Failed to find label flows: {str(e)}")
        
        return flows
    
    def build_flow_graph(self, project_path: str) -> Dict[str, LabelNode]:
        """
        Build a complete flow graph of all labels and their connections.
        
        Args:
            project_path: Path to the Ren'Py project
            
        Returns:
            Dictionary mapping label names to LabelNode objects
        """
        # Get all labels first
        all_lines = []
        label_definitions = {}
        
        try:
            rpy_files = self.find_rpy_files(project_path)
            
            # First pass: collect all label definitions
            for rpy_file in rpy_files:
                file_path = os.path.join(project_path, rpy_file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        lines = file.readlines()
                except UnicodeDecodeError:
                    try:
                        with open(file_path, 'r', encoding='latin-1') as file:
                            lines = file.readlines()
                    except Exception:
                        continue
                
                for line_num, line in enumerate(lines, 1):
                    all_lines.append((file_path, line_num, line))
                    
                    label_match = self.patterns['label'].match(line)
                    if label_match:
                        label_name = label_match.group(1)
                        label_definitions[label_name] = (file_path, line_num)
        
        except Exception as e:
            raise RenpyParseError(f"Failed to collect labels: {str(e)}")
        
        # Initialize all label nodes
        graph = {}
        for label_name, (file_path, line_num) in label_definitions.items():
            graph[label_name] = LabelNode(
                name=label_name,
                file_path=file_path,
                line_number=line_num
            )
        
        # Get all flows and populate the graph
        flows = self.find_all_label_flows(project_path)
        
        for flow in flows:
            # Add to source node's outgoing flows
            if flow.source_label and flow.source_label in graph:
                graph[flow.source_label].outgoing_flows.append(flow)
            
            # Add to target node's incoming flows (if target exists)
            if flow.target_label in graph:
                graph[flow.target_label].incoming_flows.append(flow)
        
        # Analyze label properties
        menus = self.find_all_menus(project_path)
        menu_labels = set(menu.label_context for menu in menus if menu.label_context)
        
        dialogue_lines = []
        for file_path, line_num, line in all_lines:
            parsed_line = self._parse_line(file_path, line_num, line)
            if parsed_line and parsed_line.line_type in ['dialogue', 'narrator']:
                dialogue_lines.append(parsed_line)
        
        dialogue_labels = set()
        current_label = None
        for file_path, line_num, line in all_lines:
            label_match = self.patterns['label'].match(line)
            if label_match:
                current_label = label_match.group(1)
            elif current_label and any(parsed.line_type in ['dialogue', 'narrator'] 
                                     for parsed in [self._parse_line(file_path, line_num, line)] 
                                     if parsed):
                dialogue_labels.add(current_label)
        
        # Set label properties
        for label_name, node in graph.items():
            node.has_menu = label_name in menu_labels
            node.has_dialogue = label_name in dialogue_labels
            node.is_dead_end = len(node.outgoing_flows) == 0
            node.flow_complexity = len(node.outgoing_flows)
        
        # Analyze reachability from common starting points
        start_labels = ['start', 'main', 'scene1', 'intro', 'begin']
        reachable = set()
        
        def mark_reachable(label_name: str, visited: Optional[set] = None):
            if visited is None:
                visited = set()
            
            if label_name in visited or label_name not in graph:
                return
            
            visited.add(label_name)
            reachable.add(label_name)
            
            for flow in graph[label_name].outgoing_flows:
                if flow.target_label != '<return>':
                    mark_reachable(flow.target_label, visited)
        
        # Mark reachability from all possible starting points
        for start_label in start_labels:
            if start_label in graph:
                mark_reachable(start_label)
        
        # Also mark from labels with no incoming flows (potential entry points)
        for label_name, node in graph.items():
            if len(node.incoming_flows) == 0:
                mark_reachable(label_name)
        
        # Set reachability flags
        for label_name, node in graph.items():
            node.is_reachable = label_name in reachable
        
        return graph
    
    def analyze_flow_patterns(self, project_path: str) -> Dict[str, Any]:
        """
        Analyze flow patterns and narrative structure.
        
        Args:
            project_path: Path to the Ren'Py project
            
        Returns:
            Dictionary with flow analysis and statistics
        """
        graph = self.build_flow_graph(project_path)
        flows = self.find_all_label_flows(project_path)
        
        # Count flow types
        flow_type_counts = {}
        for flow in flows:
            flow_type = flow.flow_type
            if flow_type not in flow_type_counts:
                flow_type_counts[flow_type] = 0
            flow_type_counts[flow_type] += 1
        
        # Analyze label categories
        reachable_labels = [name for name, node in graph.items() if node.is_reachable]
        unreachable_labels = [name for name, node in graph.items() if not node.is_reachable]
        dead_end_labels = [name for name, node in graph.items() if node.is_dead_end]
        entry_points = [name for name, node in graph.items() if len(node.incoming_flows) == 0]
        high_complexity = [name for name, node in graph.items() if node.flow_complexity > 3]
        
        # Find most connected labels
        most_incoming = sorted(graph.items(), key=lambda x: len(x[1].incoming_flows), reverse=True)
        most_outgoing = sorted(graph.items(), key=lambda x: len(x[1].outgoing_flows), reverse=True)
        
        # Calculate connectivity metrics
        total_labels = len(graph)
        total_flows = len(flows)
        avg_complexity = sum(node.flow_complexity for node in graph.values()) / total_labels if total_labels > 0 else 0
        
        # Find flow clusters (highly connected groups)
        clusters = self._find_flow_clusters(graph)
        
        analysis = {
            'total_labels': total_labels,
            'total_flows': total_flows,
            'flow_types': flow_type_counts,
            'reachable_labels': len(reachable_labels),
            'unreachable_labels': len(unreachable_labels),
            'dead_end_labels': len(dead_end_labels),
            'entry_points': len(entry_points),
            'high_complexity_labels': len(high_complexity),
            'average_complexity': round(avg_complexity, 2),
            'connectivity_ratio': round(total_flows / total_labels, 2) if total_labels > 0 else 0,
            'reachability_ratio': round(len(reachable_labels) / total_labels, 2) if total_labels > 0 else 0,
            'most_incoming': [(name, len(node.incoming_flows)) for name, node in most_incoming[:10]],
            'most_outgoing': [(name, len(node.outgoing_flows)) for name, node in most_outgoing[:10]],
            'entry_point_labels': entry_points[:10],
            'dead_end_labels': dead_end_labels[:10],
            'unreachable_labels': unreachable_labels[:10],
            'high_complexity_labels': high_complexity[:10],
            'flow_clusters': len(clusters),
            'largest_cluster_size': max(len(cluster) for cluster in clusters) if clusters else 0
        }
        
        return analysis
    
    def _find_flow_clusters(self, graph: Dict[str, LabelNode]) -> List[List[str]]:
        """Find clusters of highly connected labels."""
        visited = set()
        clusters = []
        
        def dfs_cluster(label_name: str, current_cluster: List[str]):
            if label_name in visited or label_name not in graph:
                return
            
            visited.add(label_name)
            current_cluster.append(label_name)
            
            # Follow all outgoing flows
            for flow in graph[label_name].outgoing_flows:
                if flow.target_label != '<return>':
                    dfs_cluster(flow.target_label, current_cluster)
            
            # Follow all incoming flows (bidirectional clustering)
            for flow in graph[label_name].incoming_flows:
                if flow.source_label:
                    dfs_cluster(flow.source_label, current_cluster)
        
        for label_name in graph:
            if label_name not in visited:
                cluster = []
                dfs_cluster(label_name, cluster)
                if cluster:
                    clusters.append(cluster)
        
        return clusters 