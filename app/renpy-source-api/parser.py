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
    from .control_flow.analyze_vn_menus import MenuStructure, MenuChoice as MenuAnalysisChoice, MenuAnalyzer
except ImportError:
    # Fall back to direct imports (when run standalone)
    from exceptions import RenpyParseError, RenpyProjectError
    from control_flow.analyze_vn_menus import MenuStructure, MenuChoice as MenuAnalysisChoice, MenuAnalyzer


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
    nested_labels: List[str] = field(default_factory=list)  # Labels defined within this choice
    
    # Enhanced metadata for app consumption
    choice_index: int = 0  # Order within the menu (0-based)
    has_condition: bool = False  # Computed from condition field
    leads_to_label: bool = False  # True if destination is a label
    leads_to_return: bool = False  # True if action_type is return
    contains_media_references: List[str] = field(default_factory=list)  # Assets referenced in choice block
    contains_variable_changes: List[str] = field(default_factory=list)  # Variables modified in choice block
    estimated_story_impact: str = "unknown"  # "major", "minor", "cosmetic", "unknown"
    
    def __post_init__(self):
        """Compute derived fields after initialization."""
        self.has_condition = bool(self.condition)
        self.leads_to_label = bool(self.destination and self.action_type in ['jump', 'call'])
        self.leads_to_return = bool(self.action_type == 'return')


@dataclass
class MenuNode:
    """
    Represents a menu node in the flow graph with comprehensive metadata.
    This serves as a rich data source for the entire application.
    """
    # Core identification
    node_id: str  # Unique identifier for graph (e.g., "ch4ashbagdone_menu_1")
    name: str  # Display name (descriptive, kept short)
    parent_label: str  # Label that contains this menu
    menu_index: int = 0  # Index if label has multiple menus (0-based)
    
    # Source location
    file_path: str = ""
    line_number: int = 0
    
    # Menu content and structure
    prompt: Optional[str] = None  # Menu question/prompt text
    choices: List[MenuChoice] = field(default_factory=list)
    total_choices: int = 0
    
    # Enhanced metadata for app consumption
    menu_type: str = "standard"  # "standard", "conditional", "nested", "set_based"
    complexity_level: str = "simple"  # "simple", "moderate", "complex", "expert"
    branching_factor: int = 0  # Number of unique destinations
    
    # Conditional and set-based menu features
    has_conditions: bool = False
    has_menu_set: bool = False
    menu_set_variable: Optional[str] = None
    
    # Nesting and hierarchy
    is_nested: bool = False
    nesting_level: int = 0
    parent_menu_id: Optional[str] = None  # If this is a nested menu
    nested_menu_ids: List[str] = field(default_factory=list)  # Child menus
    
    # Story and flow analysis
    story_significance: str = "unknown"  # "critical", "major", "minor", "cosmetic"
    choice_destinations: List[str] = field(default_factory=list)  # All unique destinations
    creates_branches: bool = True  # Whether this menu creates meaningful story branches
    can_create_loops: bool = False  # Whether choices might loop back
    
    # Media and asset references
    referenced_assets: List[str] = field(default_factory=list)  # All assets used in menu/choices
    asset_categories: List[str] = field(default_factory=list)  # Types of assets (images, audio, etc.)
    
    # Technical metadata
    estimated_play_time: int = 0  # Estimated seconds to read and choose
    choice_complexity_scores: List[float] = field(default_factory=list)  # Per-choice complexity
    
    def __post_init__(self):
        """Compute derived fields after initialization."""
        self.total_choices = len(self.choices)
        self.has_conditions = any(choice.has_condition for choice in self.choices)
        self.choice_destinations = list(set(
            choice.destination for choice in self.choices 
            if choice.destination and choice.destination != '<return>'
        ))
        self.branching_factor = len(self.choice_destinations)
        
        # Determine complexity level
        if self.total_choices <= 2 and not self.has_conditions:
            self.complexity_level = "simple"
        elif self.total_choices <= 4 and not self.has_menu_set:
            self.complexity_level = "moderate"
        elif self.has_menu_set or self.total_choices > 4 or self.has_conditions:
            self.complexity_level = "complex"
        else:
            self.complexity_level = "expert"
        
        # Generate descriptive name if not provided
        if not self.name:
            self.name = self._generate_descriptive_name()
    
    def _generate_descriptive_name(self) -> str:
        """Generate a descriptive but short name for the menu."""
        if self.prompt:
            # Extract key words from prompt
            words = self.prompt.replace('"', '').split()
            key_words = [w for w in words if len(w) > 3 and w.lower() not in ['what', 'where', 'when', 'should', 'would']]
            if key_words:
                return f"Menu: {' '.join(key_words[:2])}"
        
        # Fallback based on choices
        if self.total_choices == 2:
            return "Binary Choice"
        elif self.total_choices <= 4:
            return f"{self.total_choices}-Way Choice"
        else:
            return f"Complex ({self.total_choices} options)"
    
    def get_choice_by_text(self, text: str) -> Optional[MenuChoice]:
        """Find a choice by its text content."""
        for choice in self.choices:
            if choice.text == text:
                return choice
        return None
    
    def get_choices_leading_to(self, destination: str) -> List[MenuChoice]:
        """Get all choices that lead to a specific destination."""
        return [choice for choice in self.choices if choice.destination == destination]
    
    def has_circular_references(self) -> bool:
        """Check if any choices might create circular references."""
        return self.parent_label in self.choice_destinations
    
    def get_asset_summary(self) -> Dict[str, int]:
        """Get a summary of assets referenced by category."""
        from collections import Counter
        return dict(Counter(self.asset_categories))


# MenuStructure is now imported from control_flow.analyze_vn_menus


@dataclass
class LabelFlow:
    """Represents navigation flow between labels."""
    source_label: Optional[str] = None
    target_label: str = ""
    flow_type: str = ""  # 'jump', 'call', 'return', 'menu_choice', 'implicit'
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
    
    # Enhanced menu tracking
    menu_structures: List[MenuStructure] = field(default_factory=list)  # Original MenuStructure objects
    menu_nodes: List[MenuNode] = field(default_factory=list)  # Enhanced MenuNode objects
    menu_count: int = 0  # Number of menus in this label
    
    def __post_init__(self):
        """Compute derived fields after initialization."""
        self.has_menu = len(self.menu_structures) > 0 or len(self.menu_nodes) > 0
        self.menu_count = max(len(self.menu_structures), len(self.menu_nodes))
    
    def get_menu_by_index(self, index: int) -> Optional[MenuNode]:
        """Get a menu node by its index within this label."""
        if 0 <= index < len(self.menu_nodes):
            return self.menu_nodes[index]
        return None
    
    def get_all_menu_destinations(self) -> List[str]:
        """Get all destinations from all menus in this label."""
        destinations = []
        for menu_node in self.menu_nodes:
            destinations.extend(menu_node.choice_destinations)
        return list(set(destinations))


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
            'menu_choice': re.compile(r'^\s*"([^"]+)"\s*:'),
            
            # Enhanced menu and choice patterns
            'menu_with_name': re.compile(r'^\s*menu\s+([a-zA-Z_][a-zA-Z0-9_]*):', re.IGNORECASE),
            'choice_with_condition': re.compile(r'^\s*"([^"]+)"\s+if\s+(.+)\s*:', re.IGNORECASE),
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
            menu.label_name = menu_with_name_match.group(1)
        
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
                    
                    # Check for nested labels first
                    if parsed_line.line_type == 'label':
                        nested_label_name = parsed_line.label_name
                        current_choice.nested_labels.append(nested_label_name)
                        print(f"Parser found nested label '{nested_label_name}' in choice '{current_choice.text}'")
                    
                    # Check for action types
                    elif parsed_line.line_type in ['jump', 'choice_jump']:
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
        
        return menu
    
    def _create_menu_node_from_structure(self, menu_structure: MenuStructure, menu_index: int = 0, parent_choice_index: int = None, parent_node_id: str = None) -> MenuNode:
        """
        Create a MenuNode with rich metadata from a MenuStructure.
        
        Args:
            menu_structure: The original MenuStructure to convert
            menu_index: Index of this menu within its parent label (0-based)
            parent_choice_index: Index of parent choice if this is a nested menu
            parent_node_id: Full node ID of parent menu for hierarchical ID generation
            
        Returns:
            MenuNode with comprehensive metadata
        """
        parent_label = menu_structure.label_context or "unknown"
        
        # Generate hierarchical node ID for nested menus
        if parent_choice_index is not None and parent_node_id is not None:
            # Build hierarchical ID by extending parent's ID
            node_id = f"{parent_node_id}_choice_{parent_choice_index}_menu_1"
        elif parent_choice_index is not None:
            # Fallback for backward compatibility (shouldn't happen with new code)
            node_id = f"{parent_label}_menu_{menu_index + 1}_choice_{parent_choice_index}_menu_1"
        else:
            # Top-level menu
            node_id = f"{parent_label}_menu_{menu_index + 1}"
        
        # Create enhanced MenuChoice objects
        enhanced_choices = []
        nested_menu_nodes = []  # Track nested MenuNodes created from this menu
        
        for i, choice in enumerate(menu_structure.choices):
            enhanced_choice = MenuChoice(
                text=choice.text,
                condition=choice.condition,
                destination=choice.destination,
                action_type=choice.action_type,
                file_path=choice.file_path,
                line_number=choice.line_number,
                subsequent_lines=choice.subsequent_lines,
                nested_labels=choice.nested_labels,  # Preserve nested labels from parsing
                choice_index=i
            )
            
            # Analyze choice for metadata
            self._enhance_choice_metadata(enhanced_choice)
            enhanced_choices.append(enhanced_choice)
            
            # Recursively create MenuNodes for nested menus
            for nested_menu_structure in choice.nested_menu_structures:
                nested_menu_node = self._create_menu_node_from_structure(
                    nested_menu_structure, 
                    0,  # Nested menus start at index 0 within their choice
                    i,  # Parent choice index
                    node_id  # Pass current node_id as parent for hierarchical ID generation
                )
                
                # Set up hierarchical relationships
                nested_menu_node.parent_menu_id = node_id
                nested_menu_node.is_nested = True
                nested_menu_node.nesting_level = menu_structure.nesting_level + 1
                
                nested_menu_nodes.append(nested_menu_node)
        
        # Determine menu type
        menu_type = "standard"
        if any(choice.condition for choice in enhanced_choices):
            menu_type = "conditional"
        if nested_menu_nodes:
            menu_type = "nested"
        # Additional type determination can be added here
        
        # Create the MenuNode
        menu_node = MenuNode(
            node_id=node_id,
            name="",  # Will be generated in __post_init__
            parent_label=parent_label,
            menu_index=menu_index,
            file_path=menu_structure.file_path,
            line_number=menu_structure.line_number,
            choices=enhanced_choices,
            menu_type=menu_type,
            is_nested=menu_structure.nesting_level > 0,
            nesting_level=menu_structure.nesting_level,
            nested_menu_ids=[nested.node_id for nested in nested_menu_nodes]
        )
        
        # Extract prompt from menu structure if available
        # Look for dialogue lines right before choices in the original structure
        if menu_structure.prompt:
            menu_node.prompt = menu_structure.prompt
        elif menu_structure.choices:
            # Try to find a prompt by looking at the first few lines before the menu
            try:
                with open(menu_structure.file_path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
                    menu_line_idx = menu_structure.line_number - 1  # Convert to 0-based
                    
                    # Look for a dialogue line in the few lines after the menu statement
                    for i in range(menu_line_idx + 1, min(menu_line_idx + 5, len(lines))):
                        line = lines[i].strip()
                        if line.startswith('"') and not ':' in line:
                            # This looks like a prompt
                            menu_node.prompt = line.strip('"')
                            break
            except Exception:
                pass  # If we can't read the file, skip prompt detection
        
        # Analyze for asset references and other metadata
        self._enhance_menu_metadata(menu_node)
        
        # Return the main menu node and store nested nodes for later collection
        menu_node._nested_menu_nodes = nested_menu_nodes  # Temporary storage
        return menu_node
    
    def _collect_all_menu_nodes(self, main_menu_node: MenuNode) -> List[MenuNode]:
        """
        Collect all MenuNodes from a hierarchical structure including nested ones.
        
        Args:
            main_menu_node: The main MenuNode that may contain nested menus
            
        Returns:
            List of all MenuNodes (main + all nested ones flattened)
        """
        all_nodes = [main_menu_node]
        
        # Get nested nodes if they exist
        if hasattr(main_menu_node, '_nested_menu_nodes'):
            nested_nodes = main_menu_node._nested_menu_nodes
            for nested_node in nested_nodes:
                # Recursively collect nested nodes from each nested menu
                all_nodes.extend(self._collect_all_menu_nodes(nested_node))
            
            # Clean up temporary storage
            delattr(main_menu_node, '_nested_menu_nodes')
        
        return all_nodes
    
    def _enhance_choice_metadata(self, choice: MenuChoice) -> None:
        """
        Enhance a MenuChoice with additional metadata analysis.
        
        Args:
            choice: The MenuChoice to enhance
        """
        # Analyze subsequent lines for media references and variable changes
        for line in choice.subsequent_lines:
            line_lower = line.lower()
            
            # Look for asset references
            for category, extensions in self.asset_extensions.items():
                for ext in extensions:
                    if ext in line_lower:
                        # Found potential asset reference
                        words = line.split()
                        for word in words:
                            if ext in word.lower():
                                choice.contains_media_references.append(word.strip('"\''))
                                break
            
            # Look for variable assignments
            if line.strip().startswith('$') or ' = ' in line:
                # This line modifies variables
                var_match = re.search(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*[=\+\-\*\/]', line)
                if var_match:
                    choice.contains_variable_changes.append(var_match.group(1))
        
        # Estimate story impact based on destination and content
        if choice.action_type == 'return':
            choice.estimated_story_impact = "major"  # Ending the story
        elif choice.destination and choice.destination.lower() in ['end', 'ending', 'finale']:
            choice.estimated_story_impact = "major"
        elif len(choice.contains_variable_changes) > 2:
            choice.estimated_story_impact = "major"  # Many variable changes
        elif choice.contains_media_references:
            choice.estimated_story_impact = "minor"  # Has some media content
        else:
            choice.estimated_story_impact = "cosmetic"
    
    def _enhance_menu_metadata(self, menu_node: MenuNode) -> None:
        """
        Enhance a MenuNode with additional metadata analysis.
        
        Args:
            menu_node: The MenuNode to enhance
        """
        # Collect all assets referenced in choices
        all_assets = []
        for choice in menu_node.choices:
            all_assets.extend(choice.contains_media_references)
        
        menu_node.referenced_assets = list(set(all_assets))
        
        # Categorize assets
        categories = set()
        for asset in menu_node.referenced_assets:
            category = self.get_asset_category(asset)
            if category != 'unknown':
                categories.add(category)
        menu_node.asset_categories = list(categories)
        
        # Check for potential circular references
        menu_node.can_create_loops = menu_node.has_circular_references()
        
        # Estimate story significance based on choices
        impact_scores = {'major': 3, 'minor': 2, 'cosmetic': 1, 'unknown': 0}
        total_impact = sum(impact_scores.get(choice.estimated_story_impact, 0) for choice in menu_node.choices)
        avg_impact = total_impact / len(menu_node.choices) if menu_node.choices else 0
        
        if avg_impact >= 2.5:
            menu_node.story_significance = "critical"
        elif avg_impact >= 2.0:
            menu_node.story_significance = "major"
        elif avg_impact >= 1.0:
            menu_node.story_significance = "minor"
        else:
            menu_node.story_significance = "cosmetic"
        
        # Estimate play time (rough calculation)
        # Base time: 5 seconds per choice to read + 3 seconds to decide
        base_time = len(menu_node.choices) * 5 + 3
        if menu_node.prompt:
            base_time += len(menu_node.prompt.split()) * 0.5  # ~0.5 seconds per word
        menu_node.estimated_play_time = int(base_time)

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
        Find all navigation flows between labels (jumps, calls, returns, and implicit flows).
        
        Enhanced to detect Ren'Py's implicit flow behavior where labels without 
        explicit flow control automatically continue to the next statement/label.
        
        Args:
            project_path: Path to the Ren'Py project
            
        Returns:
            List of all LabelFlow objects found (explicit + implicit)
        """
        flows = []
        
        try:
            # PHASE 1: Collect all labels with their positions for implicit flow detection
            all_labels_with_positions = self._collect_all_labels_with_positions(project_path)
            
            # PHASE 2: Detect explicit flows (existing logic)
            explicit_flows = self._find_explicit_flows(project_path)
            flows.extend(explicit_flows)
            
            # DEBUG: Count conditional flows in explicit flows
            conditional_flows_count = sum(1 for flow in explicit_flows if flow.context == "conditional_jump")
            afternikkidate_flows = [flow for flow in explicit_flows if flow.source_label == 'afternikkidate']
            print(f"[FLOW DEBUG] Total explicit flows: {len(explicit_flows)}")
            print(f"[FLOW DEBUG] Conditional flows: {conditional_flows_count}")
            print(f"[FLOW DEBUG] afternikkidate flows: {len(afternikkidate_flows)}")
            for flow in afternikkidate_flows:
                print(f"  → {flow.source_label} → {flow.target_label} (type: {flow.flow_type}, context: {flow.context})")
            
            # PHASE 3: Detect implicit flows (NEW)
            implicit_flows = self._find_implicit_flows(project_path, all_labels_with_positions, explicit_flows)
            flows.extend(implicit_flows)
            
        except Exception as e:
            raise RenpyParseError(f"Failed to find label flows: {str(e)}")
        
        return flows
    
    def _collect_all_labels_with_positions(self, project_path: str) -> List[Dict]:
        """
        Collect all labels with their file positions in execution order.
        
        Returns:
            List of label info dictionaries sorted by file order, then line number
        """
        all_labels = []
        
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
                label_match = self.patterns['label'].match(line)
                if label_match:
                    label_name = label_match.group(1)
                    all_labels.append({
                        'name': label_name,
                        'file_path': file_path,
                        'file_name': rpy_file,
                        'line_number': line_num,
                        'file_order': rpy_files.index(rpy_file)  # Order in file list
                    })
        
        # Sort by file order, then by line number within each file
        all_labels.sort(key=lambda x: (x['file_order'], x['line_number']))
        
        return all_labels
    
    def _find_explicit_flows(self, project_path: str) -> List[LabelFlow]:
        """
        Find explicit flows (jumps, calls, returns, menu choices) - enhanced with conditional jump detection.
        """
        flows = []
        current_label = None
        current_label_start_line = None
        current_file_path = None
        
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
                except Exception as e:
                    print(f"Failed to read {rpy_file}: {e}")
                    continue  # Skip problematic files
            
            # Simple debug check for v14point5.rpy
            if 'v14point5' in rpy_file:
                print(f"[DEBUG] Processing v14point5.rpy with {len(lines)} lines")
                afternikkidate_found = False
                for line_num, line in enumerate(lines, 1):
                    if 'label afternikkidate' in line:
                        print(f"[BINGO] Found 'label afternikkidate' at line {line_num} in v14point5.rpy!")
                        afternikkidate_found = True
                if not afternikkidate_found:
                    print(f"[PROBLEM] afternikkidate label NOT found in v14point5.rpy")
            
            for line_num, line in enumerate(lines, 1):
                stripped_line = line.strip()
                
                # Track current label for context
                label_match = self.patterns['label'].match(line)
                if label_match:
                    label_name = label_match.group(1)
                    
                    # Before switching to new label, extract conditional jumps from previous label
                    if current_label and current_label_start_line and current_file_path:
                        conditional_flows = self._extract_conditional_jumps(
                            current_label, current_file_path, current_label_start_line
                        )
                        flows.extend(conditional_flows)
                    
                    # Set new current label
                    current_label = label_name
                    current_label_start_line = line_num - 1  # Convert to 0-based for _extract_conditional_jumps
                    current_file_path = file_path
                    continue
                
                # Find direct jumps and calls (existing logic)
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
            
            # Handle the last label in the file
            if current_label and current_label_start_line and current_file_path:
                conditional_flows = self._extract_conditional_jumps(
                    current_label, current_file_path, current_label_start_line
                )
                flows.extend(conditional_flows)
        
        # Add flows from menu choices
        menus = self.find_all_menus(project_path)
        for menu in menus:
            for choice in menu.choices:
                # Add flows for standard choice destinations (jumps/calls)
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
                
                # NOTE: Nested labels are now handled by choice button connections in the visualizer
                # This prevents competing flows: label -> nested_label vs choice -> nested_label
                # for nested_label in choice.nested_labels:
                #     flows.append(LabelFlow(
                #         source_label=menu.label_context,
                #         target_label=nested_label,
                #         flow_type='menu_choice_nested_label',
                #         file_path=choice.file_path,
                #         line_number=choice.line_number,
                #         context=f"Choice: {choice.text} -> {nested_label}",
                #         condition=choice.condition
                #     ))
                #     print(f"Added flow: choice '{choice.text}' -> nested label '{nested_label}'")
        
        return flows

    def _extract_conditional_jumps(self, label_name: str, file_path: str, start_line: int) -> List[LabelFlow]:
        """
        CONDITIONAL JUMP DETECTOR: Extract ALL possible jump targets from conditional blocks.
        
        This method performs static analysis to find jump statements in if/elif/else blocks,
        creating flows for all possible execution paths regardless of variable values.
        
        Args:
            label_name: Name of the label being analyzed
            file_path: Path to the .rpy file
            start_line: Starting line number for the label
            
        Returns:
            List of LabelFlow objects for all conditional jumps found
        """
        conditional_flows = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            # Find the end of this label (next label or end of file)
            label_end_line = len(lines)
            for i in range(start_line, len(lines)):
                line = lines[i].strip()
                if line.startswith('label ') and i > start_line:
                    label_end_line = i
                    break
            
            # SIMPLIFIED CONDITIONAL JUMP DETECTION
            # Scan through the label content for jump statements in conditional blocks
            i = start_line
            while i < label_end_line:
                line = lines[i].strip()
                
                # Look for jump statements preceded by if/elif/else  
                if re.match(r'^\s*jump\s+([a-zA-Z_][a-zA-Z0-9_]*)', line, re.IGNORECASE):
                    jump_match = re.match(r'^\s*jump\s+([a-zA-Z_][a-zA-Z0-9_]*)', line, re.IGNORECASE)
                    if jump_match:
                        target_label = jump_match.group(1)
                        
                        # Check if this jump is within a conditional block by looking backwards
                        is_conditional = False
                        for j in range(max(0, i - 20), i):  # Look back up to 20 lines
                            prev_line = lines[j].strip()
                            if re.match(r'^\s*if\s+', prev_line, re.IGNORECASE):
                                is_conditional = True
                                break
                            elif re.match(r'^\s*elif\s+', prev_line, re.IGNORECASE):
                                is_conditional = True
                                break
                            elif re.match(r'^\s*else\s*:', prev_line, re.IGNORECASE):
                                is_conditional = True
                                break
                        
                        if is_conditional:
                            conditional_flows.append(LabelFlow(
                                source_label=label_name,
                                target_label=target_label,
                                flow_type='jump',
                                file_path=file_path,
                                line_number=i + 1,
                                context="conditional_jump",
                                condition="conditional_statement"
                            ))
                            print(f"CONDITIONAL JUMP DETECTED: {label_name} -> {target_label} (simplified detection)")
                
                i += 1
            
        except Exception as e:
            print(f"WARNING: Error extracting conditional jumps from {label_name}: {e}")
        
        return conditional_flows

    def _find_implicit_flows(self, project_path: str, all_labels: List[Dict], explicit_flows: List[LabelFlow]) -> List[LabelFlow]:
        """
        Find implicit flows - labels that fall through to the next label.
        
        Enhanced to handle conditionals properly - labels with only conditional 
        or invalid explicit flows can still have implicit flows.
        
        Args:
            project_path: Path to the Ren'Py project
            all_labels: List of all labels sorted by execution order
            explicit_flows: Already detected explicit flows
            
        Returns:
            List of implicit flow objects
        """
        implicit_flows = []
        
        # Build more sophisticated analysis of label flow completeness
        label_flow_analysis = self._analyze_label_flow_completeness(project_path, explicit_flows)
        
        # Build set of labels that have menus (which provide their own flow)
        labels_with_menus = set()
        menus = self.find_all_menus(project_path)
        for menu in menus:
            if menu.label_context:
                labels_with_menus.add(menu.label_context)
        
        # For each label, check if it needs an implicit flow
        for i, current_label_info in enumerate(all_labels):
            current_label = current_label_info['name']
            
            # Skip if this label has menus (they handle their own flow)
            if current_label in labels_with_menus:
                continue
            
            # Check if this label has guaranteed outgoing flow
            flow_analysis = label_flow_analysis.get(current_label, {})
            has_guaranteed_outgoing_flow = flow_analysis.get('has_guaranteed_outgoing_flow', False)
            
            # Add implicit flow if no guaranteed outgoing flow exists
            if not has_guaranteed_outgoing_flow:
                # Find the next label to connect to
                next_label_info = self._find_next_sequential_label(all_labels, i)
                
                if next_label_info:
                    # Create implicit flow to next label
                    implicit_flows.append(LabelFlow(
                        source_label=current_label,
                        target_label=next_label_info['name'],
                        flow_type='implicit',  # NEW flow type for implicit flows
                        file_path=current_label_info['file_path'],
                        line_number=current_label_info['line_number'],
                        context=f"implicit_flow:{flow_analysis.get('reason', 'no_explicit_flow')}",  # Debug info
                        condition=None
                    ))
        
        return implicit_flows
    
    def _analyze_label_flow_completeness(self, project_path: str, explicit_flows: List[LabelFlow]) -> Dict[str, Dict]:
        """
        Analyze each label to determine if it has guaranteed outgoing flow.
        
        A label has guaranteed outgoing flow if:
        1. It has unconditional return statement
        2. It has unconditional jump/call statement  
        3. It has menu choices that cover all cases
        
        Args:
            project_path: Path to the Ren'Py project
            explicit_flows: All explicit flows detected
            
        Returns:
            Dict mapping label names to analysis results
        """
        analysis = {}
        
        # Group flows by source label
        flows_by_label = {}
        for flow in explicit_flows:
            if flow.source_label:
                if flow.source_label not in flows_by_label:
                    flows_by_label[flow.source_label] = []
                flows_by_label[flow.source_label].append(flow)
        
        # Analyze each label that has explicit flows
        for label_name, flows in flows_by_label.items():
            analysis[label_name] = self._analyze_single_label_flows(label_name, flows, project_path)
        
        return analysis
    
    def _analyze_single_label_flows(self, label_name: str, flows: List[LabelFlow], project_path: str) -> Dict:
        """
        Analyze a single label's flows to determine if they guarantee execution control.
        
        Args:
            label_name: Name of the label to analyze
            flows: All flows from this label
            project_path: Path to the project
            
        Returns:
            Analysis dict with 'has_guaranteed_outgoing_flow' and 'reason'
        """
        # Check for unconditional control flows
        unconditional_flows = []
        conditional_flows = []
        
        for flow in flows:
            if flow.flow_type in ['jump', 'call', 'return']:
                # Check if this flow is conditional by examining the source
                is_conditional = self._is_flow_conditional(flow, project_path)
                
                if is_conditional:
                    conditional_flows.append(flow)
                else:
                    unconditional_flows.append(flow)
        
        # If there are unconditional flows, control is guaranteed to transfer
        if unconditional_flows:
            return {
                'has_guaranteed_outgoing_flow': True,
                'reason': f'unconditional_{unconditional_flows[0].flow_type}',
                'unconditional_flows': len(unconditional_flows),
                'conditional_flows': len(conditional_flows)
            }
        
        # If only conditional flows, check if they're comprehensive
        if conditional_flows:
            # For now, assume conditional flows don't guarantee control transfer
            # This could be enhanced to analyze if conditions cover all cases
            return {
                'has_guaranteed_outgoing_flow': False,
                'reason': 'only_conditional_flows',
                'unconditional_flows': 0,
                'conditional_flows': len(conditional_flows)
            }
        
        # No flows found
        return {
            'has_guaranteed_outgoing_flow': False,
            'reason': 'no_explicit_flows',
            'unconditional_flows': 0,
            'conditional_flows': 0
        }
    
    def _is_flow_conditional(self, flow: LabelFlow, project_path: str) -> bool:
        """
        Check if a flow is inside a conditional block (if/elif/else).
        
        This is a simplified implementation that looks for common conditional patterns.
        A more sophisticated version would parse the full AST structure.
        
        Args:
            flow: The flow to check
            project_path: Path to the project
            
        Returns:
            True if the flow appears to be conditional
        """
        try:
            # Read the file and examine the context around the flow
            with open(flow.file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            flow_line_idx = flow.line_number - 1  # Convert to 0-based
            
            if flow_line_idx < 0 or flow_line_idx >= len(lines):
                return False
            
            # Look backwards from the flow line to find if we're in a conditional block
            for i in range(max(0, flow_line_idx - 10), flow_line_idx + 1):
                line = lines[i].strip()
                
                # Check for conditional keywords with proper indentation context
                if re.match(r'^\s*if\s+', line, re.IGNORECASE):
                    return True
                elif re.match(r'^\s*elif\s+', line, re.IGNORECASE):
                    return True
                elif re.match(r'^\s*else\s*:', line, re.IGNORECASE):
                    return True
            
            return False
            
        except Exception:
            # If we can't determine, assume it's not conditional
            return False
    
    def _find_next_sequential_label(self, all_labels: List[Dict], current_index: int) -> Optional[Dict]:
        """
        Find the next label that would be executed after the current label.
        
        Args:
            all_labels: List of all labels sorted by execution order
            current_index: Index of current label in the list
            
        Returns:
            Next label info dict or None if no next label exists
        """
        if current_index + 1 < len(all_labels):
            return all_labels[current_index + 1]
        return None
    
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
        
        # DEBUG: Track conditional flows being added to graph
        conditional_flows_in_graph = [flow for flow in flows if flow.context == "conditional_jump"]
        afternikkidate_flows_in_graph = [flow for flow in flows if flow.source_label == 'afternikkidate']
        print(f"[GRAPH DEBUG] Total flows to add to graph: {len(flows)}")
        print(f"[GRAPH DEBUG] Conditional flows in graph: {len(conditional_flows_in_graph)}")
        print(f"[GRAPH DEBUG] afternikkidate flows in graph: {len(afternikkidate_flows_in_graph)}")
        
        for flow in flows:
            # Add to source node's outgoing flows
            if flow.source_label and flow.source_label in graph:
                graph[flow.source_label].outgoing_flows.append(flow)
                
                # DEBUG: Track afternikkidate flows being added
                if flow.source_label == 'afternikkidate':
                    print(f"[GRAPH DEBUG] Added outgoing flow: {flow.source_label} → {flow.target_label} (context: {flow.context})")
            
            # Add to target node's incoming flows (if target exists)
            if flow.target_label in graph:
                graph[flow.target_label].incoming_flows.append(flow)
                
                # DEBUG: Track v14beforecourt flows being added
                if flow.target_label == 'v14beforecourt':
                    print(f"[GRAPH DEBUG] Added incoming flow: {flow.source_label} → {flow.target_label} (context: {flow.context})")
        
        # Analyze label properties and create menu nodes using MenuAnalyzer for nested support
        menu_analyzer = MenuAnalyzer()
        menu_analysis = menu_analyzer.analyze_vn_menus(project_path)
        menus = menu_analysis.get('menu_structures', [])
        
        # Group menus by their label context for processing
        menus_by_label = {}
        for menu in menus:
            if menu.label_context:
                if menu.label_context not in menus_by_label:
                    menus_by_label[menu.label_context] = []
                menus_by_label[menu.label_context].append(menu)
        
        # Create MenuNode objects and associate them with labels
        for label_name, label_menus in menus_by_label.items():
            if label_name in graph:
                node = graph[label_name]
                
                # Store original MenuStructure objects
                node.menu_structures = label_menus
                
                # Create enhanced MenuNode objects with hierarchical support
                all_menu_nodes = []  # Collect all MenuNodes including nested ones
                
                for i, menu_structure in enumerate(label_menus):
                    # Create the main MenuNode (which may contain nested ones)
                    main_menu_node = self._create_menu_node_from_structure(menu_structure, i)
                    
                    # Collect all MenuNodes from the hierarchy (main + nested)
                    hierarchy_nodes = self._collect_all_menu_nodes(main_menu_node)
                    all_menu_nodes.extend(hierarchy_nodes)
                    
                    print(f"Created menu hierarchy for {label_name}: {len(hierarchy_nodes)} total MenuNodes (main + nested)")
                
                # Add all MenuNodes (top-level and nested) to the label
                node.menu_nodes.extend(all_menu_nodes)
                
                # Update computed fields after adding menu data
                node.has_menu = len(node.menu_structures) > 0 or len(node.menu_nodes) > 0
                node.menu_count = max(len(node.menu_structures), len(node.menu_nodes))
        
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
            node.has_dialogue = label_name in dialogue_labels
            node.is_dead_end = len(node.outgoing_flows) == 0
            node.flow_complexity = len(node.outgoing_flows)
            # has_menu and menu_count are now computed in LabelNode.__post_init__()
        
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
    
    def get_all_menu_nodes(self, project_path: str) -> List[MenuNode]:
        """
        Get all MenuNode objects from the project with rich metadata.
        
        Args:
            project_path: Path to the Ren'Py project
            
        Returns:
            List of all MenuNode objects found in the project
        """
        graph = self.build_flow_graph(project_path)
        menu_nodes = []
        
        for label_name, label_node in graph.items():
            menu_nodes.extend(label_node.menu_nodes)
        
        return menu_nodes
    
    def get_menu_nodes_by_label(self, project_path: str) -> Dict[str, List[MenuNode]]:
        """
        Get MenuNode objects grouped by their parent label.
        
        Args:
            project_path: Path to the Ren'Py project
            
        Returns:
            Dictionary mapping label names to their MenuNode objects
        """
        graph = self.build_flow_graph(project_path)
        menu_nodes_by_label = {}
        
        for label_name, label_node in graph.items():
            if label_node.menu_nodes:
                menu_nodes_by_label[label_name] = label_node.menu_nodes
        
        return menu_nodes_by_label

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