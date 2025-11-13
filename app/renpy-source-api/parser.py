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
    # Import MenuStructure and related classes without circular dependency
    try:
        from .control_flow.analyze_vn_menus import MenuStructure, MenuChoice as MenuAnalysisChoice, MenuAnalyzer
    except ImportError:
        # If circular import, define minimal classes here temporarily
        from dataclasses import dataclass, field
        from typing import List, Optional, Any, Dict
        
        @dataclass
        class MenuAnalysisChoice:
            text: str
            line_number: int
            condition: Optional[str] = None
            destinations: List[str] = field(default_factory=list)
        
        @dataclass 
        class MenuStructure:
            file_path: str
            line_number: int
            label_name: Optional[str] = None
            choices: List[MenuAnalysisChoice] = field(default_factory=list)
            
        class MenuAnalyzer:
            pass
            
except ImportError:
    # Fall back to direct imports (when run standalone)
    from exceptions import RenpyParseError, RenpyProjectError
    try:
        from control_flow.analyze_vn_menus import MenuStructure, MenuChoice as MenuAnalysisChoice, MenuAnalyzer
    except ImportError:
        # If circular import, define minimal classes here temporarily
        from dataclasses import dataclass, field
        from typing import List, Optional, Any, Dict
        
        @dataclass
        class MenuAnalysisChoice:
            text: str
            line_number: int
            condition: Optional[str] = None
            destinations: List[str] = field(default_factory=list)
        
        @dataclass 
        class MenuStructure:
            file_path: str
            line_number: int
            label_name: Optional[str] = None
            choices: List[MenuAnalysisChoice] = field(default_factory=list)
            
        class MenuAnalyzer:
            pass


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
    destination: Optional[str] = None  # Primary jump/call target (for backwards compatibility)
    action_type: Optional[str] = None  # 'jump', 'call', 'return', 'pass', 'continue'
    file_path: str = ""
    line_number: int = 0
    subsequent_lines: List[str] = field(default_factory=list)  # Lines that follow this choice
    nested_labels: List[str] = field(default_factory=list)  # Labels defined within this choice
    
    # NEW: Support for multiple conditional destinations
    all_destinations: List[str] = field(default_factory=list)  # All jump/call targets found in this choice
    destination_conditions: List[str] = field(default_factory=list)  # Conditions for each destination
    
    # Enhanced metadata for app consumption
    choice_index: int = 0  # Order within the menu (0-based)
    has_condition: bool = False  # Computed from condition field
    leads_to_label: bool = False  # True if destination is a label
    leads_to_return: bool = False  # True if action_type is return
    contains_media_references: List[str] = field(default_factory=list)  # Assets referenced in choice block
    contains_variable_changes: List[str] = field(default_factory=list)  # Variables modified in choice block
    estimated_story_impact: str = "unknown"  # "major", "minor", "cosmetic", "unknown"
    
    # CRITICAL: Nested menu support for authoritative hierarchy
    nested_menu_structures: List = field(default_factory=list)  # MenuStructures nested within this choice
    
    def __post_init__(self):
        """Compute derived fields after initialization."""
        self.has_condition = bool(self.condition)
        self.leads_to_label = bool(self.destination and self.action_type in ['jump', 'call'])
        self.leads_to_return = bool(self.action_type == 'return')


@dataclass
class ScreenElement:
    """Represents an interactive element within a screen (hotspot, button, etc.)."""
    element_type: str  # 'hotspot', 'textbutton', 'imagebutton', etc.
    text: Optional[str] = None  # Display text for buttons
    coordinates: Optional[Tuple[int, int, int, int]] = None  # (x, y, width, height) for hotspots
    destination: Optional[str] = None  # jump/call target
    action_type: Optional[str] = None  # 'jump', 'call', 'return', etc.
    file_path: str = ""
    line_number: int = 0
    
    # Enhanced metadata
    element_index: int = 0  # Order within the screen (0-based)
    has_condition: bool = False  # If element has conditional display
    condition: Optional[str] = None
    
    def __post_init__(self):
        """Compute derived fields after initialization."""
        self.has_condition = bool(self.condition)


@dataclass
class ScreenStructure:
    """Represents a complete screen structure."""
    screen_name: str
    file_path: str
    line_number: int
    elements: List[ScreenElement] = field(default_factory=list)
    screen_type: str = "standard"  # 'imagemap', 'standard', 'complex'
    has_imagemap: bool = False
    imagemap_ground: Optional[str] = None  # Ground image for imagemap
    imagemap_hover: Optional[str] = None   # Hover image for imagemap
    label_context: Optional[str] = None    # Label that contains screen calls
    
    # Screen metadata
    total_elements: int = 0
    interactive_elements: int = 0  # Elements with actions
    
    def __post_init__(self):
        """Compute derived fields after initialization."""
        self.total_elements = len(self.elements)
        self.interactive_elements = sum(1 for elem in self.elements if elem.destination)
        if any(elem.element_type == 'hotspot' for elem in self.elements):
            self.has_imagemap = True
            self.screen_type = 'imagemap'


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
    label_name: Optional[str] = None  # If this is a label menu (e.g., "menu day02_p_room_choices:")
    
    # Source location
    file_path: str = ""
    line_number: int = 0
    
    # Menu content and structure
    prompt: Optional[str] = None  # Menu question/prompt text
    choices: List[MenuChoice] = field(default_factory=list)
    total_choices: int = 0
    
    # Nested menu support
    is_nested: bool = False  # True if this menu is nested inside a choice
    
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
    flow_type: str = ""  # 'jump', 'call', 'return', 'menu_choice', 'implicit', 'screen_call', 'screen_action'
    file_path: str = ""
    line_number: int = 0
    context: Optional[str] = None  # Additional context (e.g., choice text, screen element info)
    condition: Optional[str] = None  # Condition if it's a conditional flow
    screen_info: Optional[Dict[str, str]] = None  # For screen-related flows (screen name, element type, etc.)


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
    
    # Screen tracking
    screen_calls: List[str] = field(default_factory=list)  # Screen names called from this label
    has_screen_calls: bool = False
    
    def __post_init__(self):
        """Compute derived fields after initialization."""
        self.has_menu = len(self.menu_structures) > 0 or len(self.menu_nodes) > 0
        self.menu_count = max(len(self.menu_structures), len(self.menu_nodes))
        self.has_screen_calls = len(self.screen_calls) > 0
    
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
    enhanced_menus: List[Dict[str, Any]] = field(default_factory=list)  # Enhanced AST menu analysis


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
            'label': re.compile(r'^\s*label\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\([^)]*\))?\s*:', re.IGNORECASE),
            'character_def': re.compile(r'^\s*define\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*Character\s*\(\s*"([^"]*)"', re.IGNORECASE),
            'dialogue': re.compile(r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s+"([^"]+)"', re.IGNORECASE),
            'narrator': re.compile(r'^\s*"([^"]+)"'),
            'menu': re.compile(r'^\s*menu:', re.IGNORECASE),
            'menu_choice': re.compile(r'^\s*"([^"]+)"\s*(?:\([^)]*\))?\s*:'),
            
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
            
            # Screen patterns
            'screen_definition': re.compile(r'^\s*screen\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\([^)]*\))?\s*:', re.IGNORECASE),
            'call_screen': re.compile(r'^\s*call\s+screen\s+([a-zA-Z_][a-zA-Z0-9_]*)', re.IGNORECASE),
            'show_screen': re.compile(r'^\s*show\s+screen\s+([a-zA-Z_][a-zA-Z0-9_]*)', re.IGNORECASE),
            'imagemap': re.compile(r'^\s*imagemap\s*:', re.IGNORECASE),
            'imagemap_ground': re.compile(r'^\s*ground\s+"([^"]*)"', re.IGNORECASE),
            'imagemap_hover': re.compile(r'^\s*hover\s+"([^"]*)"', re.IGNORECASE),
            'hotspot': re.compile(r'^\s*hotspot\s*\(([^)]+)\)\s*action\s+(Jump|Call)\s*\(\s*"([^"]+)"\s*\)', re.IGNORECASE),
            'textbutton': re.compile(r'^\s*textbutton\s+"([^"]+)".*?action\s+(Jump|Call)\s*\(\s*"([^"]+)"\s*\)', re.IGNORECASE),
            'imagebutton': re.compile(r'^\s*imagebutton\s+.*?action\s+(Jump|Call)\s*\(\s*"([^"]+)"\s*\)', re.IGNORECASE),
            
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
        rpy_directories_found = []
        
        # Search for .rpy files recursively
        for rpy_path in project_dir.glob("**/*.rpy"):
            # Check if it's actually a file, not a directory
            if rpy_path.is_file():
                # Get relative path from project root
                relative_path = rpy_path.relative_to(project_dir)
                
                # Skip excluded system files
                if relative_path.name not in self.excluded_files:
                    rpy_files.append(str(relative_path))
            elif rpy_path.is_dir():
                # Log .rpy directories for debugging
                relative_path = rpy_path.relative_to(project_dir)
                rpy_directories_found.append(str(relative_path))
                print(f"[WARNING] Found .rpy directory (skipping): {relative_path}")
                
                # Optionally scan inside .rpy directories for actual .rpy files
                for nested_rpy in rpy_path.glob("**/*.rpy"):
                    if nested_rpy.is_file():
                        nested_relative = nested_rpy.relative_to(project_dir)
                        if nested_relative.name not in self.excluded_files:
                            rpy_files.append(str(nested_relative))
                            print(f"[INFO] Found nested .rpy file: {nested_relative}")
        
        if rpy_directories_found:
            print(f"[INFO] Skipped {len(rpy_directories_found)} .rpy directories, found {len(rpy_files)} actual .rpy files")
        
        return sorted(rpy_files)
    
    def validate_and_normalize_encoding(self, file_path: str) -> Tuple[str, str]:
        """
        Validate file encoding and detect/handle BOM issues before parsing.
        
        Args:
            file_path: Path to the .rpy file
            
        Returns:
            Tuple of (detected_encoding, normalized_content)
            
        Raises:
            RenpyParseError: If file cannot be read with any supported encoding
        """
        # Common BOMs to detect
        boms = [
            (b'\xef\xbb\xbf', 'utf-8-sig'),  # UTF-8 BOM
            (b'\xff\xfe', 'utf-16-le'),      # UTF-16 LE BOM
            (b'\xfe\xff', 'utf-16-be'),      # UTF-16 BE BOM
            (b'\xff\xfe\x00\x00', 'utf-32-le'),  # UTF-32 LE BOM
            (b'\x00\x00\xfe\xff', 'utf-32-be'),  # UTF-32 BE BOM
        ]
        
        # Encodings to try in order of preference
        encodings_to_try = [
            'utf-8',
            'utf-8-sig',  # UTF-8 with BOM
            'cp1252',     # Windows-1252 (common for Windows)
            'latin-1',    # ISO-8859-1 (fallback)
        ]
        
        try:
            # First, read the raw bytes to detect BOM
            with open(file_path, 'rb') as file:
                raw_bytes = file.read()
            
            if not raw_bytes:
                return 'utf-8', ''
            
            # Check for BOM
            detected_encoding = None
            content_start = 0
            
            for bom_bytes, encoding in boms:
                if raw_bytes.startswith(bom_bytes):
                    detected_encoding = encoding
                    content_start = len(bom_bytes)
                    print(f"[ENCODING] Detected {encoding} BOM in {file_path}")
                    break
            
            # If BOM detected, decode with the appropriate encoding
            if detected_encoding:
                try:
                    # Remove BOM and decode
                    content_bytes = raw_bytes[content_start:]
                    content = content_bytes.decode(detected_encoding.replace('-sig', ''))
                    return detected_encoding, content
                except UnicodeDecodeError as e:
                    print(f"[ENCODING] Warning: BOM detected but decoding failed with {detected_encoding}: {e}")
            
            # No BOM detected, try different encodings
            for encoding in encodings_to_try:
                try:
                    content = raw_bytes.decode(encoding)
                    # Successful decode - validate it makes sense
                    if content and len(content.strip()) > 0:
                        return encoding, content
                except (UnicodeDecodeError, UnicodeError):
                    continue
            
            # If all encodings fail, raise error
            raise RenpyParseError(f"Could not decode file with any supported encoding: {encodings_to_try}", file_path)
            
        except IOError as e:
            raise RenpyParseError(f"Could not read file: {e}", file_path)
    
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
            # Use encoding validation and BOM detection
            detected_encoding, content = self.validate_and_normalize_encoding(file_path)
            
            # Parse the normalized content line by line
            lines = content.splitlines()
            for line_num, line in enumerate(lines, 1):
                parsed_line = self._parse_line(file_path, line_num, line)
                if parsed_line:
                    parsed_lines.append(parsed_line)
                    
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
    
    def parse_menu_structure(self, file_path: str, start_line: int, lines: List[str], parent_indent: Optional[int] = None) -> MenuStructure:
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
                # NESTED MENU BOUNDARY: Check if this choice belongs to parent menu before processing
                if parent_indent is not None and line_indent <= parent_indent:
                    # This choice belongs to the parent menu, not this nested menu - stop parsing
                    if current_choice:
                        menu.choices.append(current_choice)
                        current_choice = None  # Clear to prevent double-adding
                    break
                
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
                # NESTED MENU BOUNDARY: Check if this choice belongs to parent menu before processing
                if parent_indent is not None and line_indent <= parent_indent:
                    # This choice belongs to the parent menu, not this nested menu - stop parsing
                    if current_choice:
                        menu.choices.append(current_choice)
                        current_choice = None  # Clear to prevent double-adding
                    break
                
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
                
                # Check if this is a nested menu - if so, skip over it but continue parsing parent menu
                if (self.patterns['menu'].match(line) or self.patterns['menu_with_name'].match(line)):
                    # We've hit a nested menu, skip over its content and continue with parent menu
                    current_line = self._skip_nested_menu_content(current_line, lines, line_indent)
                    continue
                
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
                        # Set primary destination (backwards compatibility)
                        if not current_choice.destination:
                            current_choice.action_type = 'jump'
                            current_choice.destination = parsed_line.target_label
                        
                        # Add to all destinations list
                        if parsed_line.target_label not in current_choice.all_destinations:
                            current_choice.all_destinations.append(parsed_line.target_label)
                            current_choice.destination_conditions.append(f"Line {current_line + 1}")
                            
                    elif parsed_line.line_type in ['call', 'choice_call']:
                        # Set primary destination (backwards compatibility)
                        if not current_choice.destination:
                            current_choice.action_type = 'call'
                            current_choice.destination = parsed_line.target_label
                        
                        # Add to all destinations list
                        if parsed_line.target_label not in current_choice.all_destinations:
                            current_choice.all_destinations.append(parsed_line.target_label)
                            current_choice.destination_conditions.append(f"Line {current_line + 1}")
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
    
    def _is_actual_label_menu(self, menu_structure: MenuStructure) -> bool:
        """
        Determine if a MenuStructure represents an actual label menu vs a named menu within a label.
        
        Actual label menu: label some_label: followed by menu:
        Named menu within label: menu MenuName: within an existing label
        
        Args:
            menu_structure: MenuStructure to analyze
            
        Returns:
            True if this is an actual label menu, False if it's a named menu within a label
        """
        if not menu_structure.label_name:
            return False
            
        # If the menu has a label_context that's different from its label_name,
        # then it's a named menu within that label
        if (menu_structure.label_context and 
            menu_structure.label_context != menu_structure.label_name):
            return False
            
        # If label_context equals label_name, it's likely an actual label menu
        # (the menu IS the label)
        return True
    
    def _resolve_named_menu_jumps(self, graph: Dict[str, LabelNode], named_menu_registry: Dict[str, str]) -> None:
        """
        Resolve jumps to named menus by redirecting them to the containing labels.
        
        Args:
            graph: The flow graph with label nodes
            named_menu_registry: Dictionary mapping named menu names to their containing labels
        """
        if not named_menu_registry:
            return
        
        print(f"[NAMED MENU FIX] Resolving jumps to {len(named_menu_registry)} named menus")
        
        # Collect all flows that target named menus
        flows_to_fix = []
        
        for label_name, label_node in graph.items():
            if label_name.startswith('_'):  # Skip special keys like _named_menu_registry
                continue
                
            # Check outgoing flows
            for flow in label_node.outgoing_flows:
                if flow.target_label in named_menu_registry:
                    flows_to_fix.append((label_node, flow, 'outgoing'))
            
            # Check incoming flows  
            for flow in label_node.incoming_flows:
                if flow.target_label in named_menu_registry:
                    flows_to_fix.append((label_node, flow, 'incoming'))
        
        # Fix the flows
        for label_node, flow, flow_direction in flows_to_fix:
            original_target = flow.target_label
            containing_label = named_menu_registry[original_target]
            
            # Update the flow target
            flow.target_label = containing_label
            flow.context = f"named_menu_jump_to_{original_target}"
            
            print(f"[NAMED MENU FIX] Redirected {flow.source_label} -> {original_target} to {flow.source_label} -> {containing_label}")
            
            # If this was an incoming flow, we need to move it to the correct target node
            if flow_direction == 'incoming' and containing_label in graph:
                # Remove from current node's incoming flows
                if flow in label_node.incoming_flows:
                    label_node.incoming_flows.remove(flow)
                
                # Add to the correct target node's incoming flows
                if flow not in graph[containing_label].incoming_flows:
                    graph[containing_label].incoming_flows.append(flow)
    
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
            # Check if this is a label menu (has its own label name)
            if menu_structure.label_name:
                # Use the actual label name for label menus
                node_id = menu_structure.label_name
            else:
                # Top-level menu with generic naming
                node_id = f"{parent_label}_menu_{menu_index + 1}"
        
        # Create enhanced MenuChoice objects
        enhanced_choices = []
        
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
            
            # CRITICAL FIX: Preserve nested_menu_structures for the authoritative hierarchy
            if hasattr(choice, 'nested_menu_structures'):
                enhanced_choice.nested_menu_structures = choice.nested_menu_structures
            else:
                enhanced_choice.nested_menu_structures = []
            
            # Analyze choice for metadata
            self._enhance_choice_metadata(enhanced_choice)
            enhanced_choices.append(enhanced_choice)
            
            # Note: Nested menus are now preserved in choice.nested_menu_structures
            # The authoritative hierarchy will handle creating the nested visualization nodes
        
        # Determine menu type
        menu_type = "standard"
        if any(choice.condition for choice in enhanced_choices):
            menu_type = "conditional"
        if any(choice.nested_menu_structures for choice in enhanced_choices):
            menu_type = "nested"
        # Additional type determination can be added here
        
        # Create the MenuNode
        menu_node = MenuNode(
            node_id=node_id,
            name="",  # Will be generated in __post_init__
            parent_label=parent_label,
            menu_index=menu_index,
            label_name=menu_structure.label_name,  # Transfer label name from MenuStructure
            file_path=menu_structure.file_path,
            line_number=menu_structure.line_number,
            choices=enhanced_choices,
            menu_type=menu_type,
            is_nested=menu_structure.nesting_level > 0 and not menu_structure.label_name,  # Label menus are never nested
            nesting_level=menu_structure.nesting_level,
            nested_menu_ids=[]  # Will be populated by authoritative hierarchy if needed
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
        
        # Return the main menu node (nested menus preserved in choice.nested_menu_structures)
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
        Find and parse all menu structures in the project with proper nested menu handling.
        
        Args:
            project_path: Path to the Ren'Py project
            
        Returns:
            List of all MenuStructure objects found
        """
        menus = []
        current_label = None
        menu_stack = []  # Track nested menu context
        
        try:
            rpy_files = self.find_rpy_files(project_path)
            
            for rpy_file in rpy_files:
                file_path = os.path.join(project_path, rpy_file)
                
                try:
                    # Use the new encoding validation and BOM detection
                    detected_encoding, content = self.validate_and_normalize_encoding(file_path)
                    lines = content.splitlines()
                except Exception as e:
                    print(f"[ENCODING] Warning: Could not process {file_path} for menu parsing: {e}")
                    continue
                
                for line_num, line in enumerate(lines, 1):
                    stripped_line = line.strip()
                    
                    # Track current label for context
                    label_match = self.patterns['label'].match(line)
                    if label_match:
                        current_label = label_match.group(1)
                        menu_stack = []  # Reset menu stack for new label
                    
                    # Check for menu start
                    if (self.patterns['menu'].match(line) or 
                        self.patterns['menu_with_name'].match(line)):
                        
                        # Determine nesting level and parent choice based on context
                        line_indent = len(line) - len(line.lstrip())
                        nesting_level = self._calculate_menu_nesting_level(line_num, lines, menu_stack)
                        
                        # For nested menus, determine parent indentation to limit parsing scope
                        parent_indent = None
                        if nesting_level > 0 and len(menu_stack) > 0:
                            # Find the parent choice that contains this nested menu
                            parent_choice = self._find_parent_choice_for_nested_menu(line_num, lines, menu_stack)
                            if parent_choice:
                                # Use the parent choice indentation level to limit nested menu parsing
                                parent_indent = self._get_choice_indentation(parent_choice, lines)
                        
                        menu = self.parse_menu_structure(file_path, line_num, lines, parent_indent)
                        menu.label_context = current_label
                        menu.nesting_level = nesting_level
                        
                        # If this is a nested menu, find the parent choice and attach it
                        if menu.nesting_level > 0 and len(menu_stack) > 0:
                            parent_choice = self._find_parent_choice_for_nested_menu(line_num, lines, menu_stack)
                            if parent_choice:
                                if not hasattr(parent_choice, 'nested_menu_structures'):
                                    parent_choice.nested_menu_structures = []
                                parent_choice.nested_menu_structures.append(menu)
                                print(f"[NESTED MENU] Attached nested menu at line {line_num} to choice '{parent_choice.text}'")
                                
                                # Clear the destination for the parent choice since it leads to a nested menu
                                parent_choice.destination = None
                                parent_choice.action_type = 'nested_menu'
                        
                        menus.append(menu)
                        
                        # Update menu stack for potential further nesting
                        if menu.nesting_level == 0:
                            menu_stack = [(menu, -1)]  # Reset stack for top-level menu
                        else:
                            menu_stack.append((menu, -1))
        
        except Exception as e:
            raise RenpyParseError(f"Failed to find menus: {str(e)}")
        
        return menus
    
    def _calculate_menu_nesting_level(self, menu_line_num: int, lines: List[str], menu_stack: List) -> int:
        """
        Calculate the nesting level of a menu based on indentation and context.
        
        Args:
            menu_line_num: Line number of the menu (1-indexed)
            lines: All lines in the file
            menu_stack: Current menu stack for context
            
        Returns:
            Nesting level (0 for top-level, 1+ for nested)
        """
        if menu_line_num - 1 >= len(lines):
            return 0
        
        menu_line = lines[menu_line_num - 1]
        menu_indent = len(menu_line) - len(menu_line.lstrip())
        
        # If no menus in stack, this is top-level
        if not menu_stack:
            return 0
        
        # Look backwards to find the most recent choice that could contain this menu
        for i in range(menu_line_num - 2, -1, -1):
            line = lines[i]
            line_indent = len(line) - len(line.lstrip())
            stripped = line.strip()
            
            # If we find a choice line that's less indented than the menu,
            # and the menu is more indented, it's likely nested
            if stripped.startswith('"') and ':' in stripped and line_indent < menu_indent:
                return 1  # Nested menu
            
            # If we hit a less-indented menu or label, stop looking
            if (line_indent < menu_indent and 
                (stripped.startswith('menu') or stripped.startswith('label'))):
                break
        
        return 0
    
    def _find_parent_choice_for_nested_menu(self, menu_line_num: int, lines: List[str], menu_stack: List) -> Optional[MenuChoice]:
        """
        Find the parent choice that contains a nested menu.
        
        Args:
            menu_line_num: Line number of the nested menu (1-indexed)
            lines: All lines in the file
            menu_stack: Current menu stack for context
            
        Returns:
            The parent MenuChoice object, or None if not found
        """
        if not menu_stack or menu_line_num - 1 >= len(lines):
            return None
        
        parent_menu, _ = menu_stack[-1]
        menu_line = lines[menu_line_num - 1]
        menu_indent = len(menu_line) - len(menu_line.lstrip())
        
        # Look backwards to find the choice that this menu belongs to
        for i in range(menu_line_num - 2, -1, -1):
            line = lines[i]
            line_indent = len(line) - len(line.lstrip())
            stripped = line.strip()
            
            # Check if this is a choice line
            if stripped.startswith('"') and ':' in stripped:
                # Extract choice text
                choice_text = stripped.split('"')[1] if '"' in stripped else stripped
                
                # Find matching choice in parent menu
                for choice in parent_menu.choices:
                    if choice.text == choice_text and line_indent < menu_indent:
                        return choice
            
            # Stop if we hit a less-indented menu or label
            if (line_indent <= menu_indent and 
                (stripped.startswith('menu') or stripped.startswith('label'))):
                break
        
        return None
    
    def _get_choice_indentation(self, choice: MenuChoice, lines: List[str]) -> int:
        """
        Get the indentation level of a choice based on its line number.
        
        Args:
            choice: The MenuChoice object
            lines: All lines in the file
            
        Returns:
            Indentation level of the choice
        """
        if choice.line_number > 0 and choice.line_number <= len(lines):
            choice_line = lines[choice.line_number - 1]  # Convert to 0-based index
            return len(choice_line) - len(choice_line.lstrip())
        return 0
    
    def _skip_nested_menu_content(self, menu_start_line: int, lines: List[str], parent_indent: int) -> int:
        """
        Skip over nested menu content and return the line number after the nested menu ends.
        
        Args:
            menu_start_line: Line number where the nested menu starts (0-based)
            lines: All lines in the file
            parent_indent: Indentation level of the parent choice containing this nested menu
            
        Returns:
            Line number after the nested menu ends (0-based)
        """
        current_line = menu_start_line + 1
        nested_menu_indent = len(lines[menu_start_line]) - len(lines[menu_start_line].lstrip())
        
        while current_line < len(lines):
            line = lines[current_line]
            line_indent = len(line) - len(line.lstrip())
            stripped_line = line.strip()
            
            # If we're back to or less than the parent choice level, we've exited the nested menu
            if stripped_line and line_indent <= parent_indent:
                # Don't consume this line, let the parent parser handle it
                return current_line - 1
            
            current_line += 1
        
        # Reached end of file
        return current_line - 1
    
    def _process_nested_menu_structures(self, parent_menu_node: MenuNode, parent_menu_structure: MenuStructure):
        """
        Process nested menu structures and attach them to parent choices.
        
        Args:
            parent_menu_node: The parent MenuNode to process
            parent_menu_structure: The parent MenuStructure containing nested menus
        """
        for choice in parent_menu_node.choices:
            if hasattr(choice, 'nested_menu_structures') and choice.nested_menu_structures:
                # Mark this choice as having nested menus
                choice.action_type = 'nested_menu'
                choice.destination = None  # Clear any jump destination
                
                # Set up nested menu hierarchy
                for nested_menu_structure in choice.nested_menu_structures:
                    nested_menu_node = self._create_menu_node_from_structure(
                        nested_menu_structure, 
                        menu_index=0,  # Reset index for nested menu
                        parent_choice_index=choice.choice_index,
                        parent_node_id=parent_menu_node.node_id
                    )
                    
                    # Set nested menu properties
                    nested_menu_node.is_nested = True
                    nested_menu_node.nesting_level = nested_menu_structure.nesting_level
                    nested_menu_node.parent_menu_id = parent_menu_node.node_id
                    
                    # Add to parent's nested menu list
                    parent_menu_node.nested_menu_ids.append(nested_menu_node.node_id)
                    
                    print(f"[NESTED MENU] Created nested menu {nested_menu_node.node_id} for choice '{choice.text}'")
                    
                    # Recursively process further nested menus
                    self._process_nested_menu_structures(nested_menu_node, nested_menu_structure)
    
    def find_all_screens(self, project_path: str) -> List[ScreenStructure]:
        """
        Find and parse all screen structures in the project.
        
        Args:
            project_path: Path to the Ren'Py project
            
        Returns:
            List of all ScreenStructure objects found
        """
        screens = []
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
                    
                    # Check for screen definition
                    screen_match = self.patterns['screen_definition'].match(line)
                    if screen_match:
                        screen_name = screen_match.group(1)
                        screen = self.parse_screen_structure(file_path, line_num, lines, screen_name)
                        screen.label_context = current_label
                        screens.append(screen)
        
        except Exception as e:
            raise RenpyParseError(f"Failed to find screens: {str(e)}")
        
        return screens
    
    def find_screen_calls(self, project_path: str) -> Dict[str, List[str]]:
        """
        Find all 'call screen' and 'show screen' statements in the project.
        
        Args:
            project_path: Path to the Ren'Py project
            
        Returns:
            Dictionary mapping label names to lists of called screen names
        """
        screen_calls = {}
        current_label = None
        
        try:
            rpy_files = self.find_rpy_files(project_path)
            
            for rpy_file in rpy_files:
                file_path = os.path.join(project_path, rpy_file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for i, line in enumerate(lines):
                    line_number = i + 1
                    
                    # Track current label context
                    label_match = self.patterns['label'].match(line)
                    if label_match:
                        current_label = label_match.group(1)
                        continue
                    
                    # Find call screen statements
                    call_screen_match = self.patterns['call_screen'].match(line)
                    if call_screen_match and current_label:
                        screen_name = call_screen_match.group(1)
                        if current_label not in screen_calls:
                            screen_calls[current_label] = []
                        screen_calls[current_label].append(screen_name)
                        print(f"[SCREEN CALL] Found 'call screen {screen_name}' in label '{current_label}' at {rpy_file}:{line_number}")
                        continue
                    
                    # Find show screen statements
                    show_screen_match = self.patterns['show_screen'].match(line)
                    if show_screen_match and current_label:
                        screen_name = show_screen_match.group(1)
                        if current_label not in screen_calls:
                            screen_calls[current_label] = []
                        screen_calls[current_label].append(screen_name)
                        print(f"[SCREEN CALL] Found 'show screen {screen_name}' in label '{current_label}' at {rpy_file}:{line_number}")
                        continue
        
        except Exception as e:
            raise RenpyParseError(f"Failed to find screen calls: {str(e)}")
        
        return screen_calls
    
    def _generate_screen_element_flows(self, project_path: str) -> List[LabelFlow]:
        """
        Generate flows from screen elements (hotspots, buttons) to their destinations.
        
        Args:
            project_path: Path to the Ren'Py project
            
        Returns:
            List of LabelFlow objects representing screen element interactions
        """
        flows = []
        screens = self.find_all_screens(project_path)
        
        for screen in screens:
            for element in screen.elements:
                if element.destination and element.action_type:
                    flows.append(LabelFlow(
                        source_label=f"screen_{screen.screen_name}",  # Screen as source
                        target_label=element.destination,
                        flow_type='screen_action',
                        file_path=element.file_path,
                        line_number=element.line_number,
                        context=f"{element.element_type}: {element.text or element.coordinates}",
                        screen_info={
                            'screen_name': screen.screen_name,
                            'element_type': element.element_type,
                            'element_text': element.text or '',
                            'action_type': element.action_type,
                            'coordinates': str(element.coordinates) if element.coordinates else ''
                        }
                    ))
                    print(f"[SCREEN ELEMENT FLOW] {screen.screen_name} -> {element.destination} via {element.element_type}")
        
        return flows
    
    def parse_screen_structure(self, file_path: str, start_line: int, lines: List[str], screen_name: str) -> ScreenStructure:
        """
        Parse a complete screen structure starting from a screen definition line.
        
        Args:
            file_path: Path to the file containing the screen
            start_line: Line number where the screen starts (1-indexed)
            lines: List of all lines in the file
            screen_name: Name of the screen
            
        Returns:
            ScreenStructure object with all interactive elements
        """
        screen = ScreenStructure(
            screen_name=screen_name,
            file_path=file_path,
            line_number=start_line
        )
        
        if start_line - 1 >= len(lines):
            return screen
        
        # Parse screen elements
        current_line = start_line
        in_imagemap = False
        element_index = 0
        
        while current_line < len(lines):
            line = lines[current_line - 1]
            stripped_line = line.strip()
            
            # Stop parsing at next screen, label, or top-level statement
            if (current_line > start_line and 
                (self.patterns['screen_definition'].match(line) or
                 self.patterns['label'].match(line) or
                 (not line.startswith(' ') and not line.startswith('\t') and stripped_line and not stripped_line.startswith('#')))):
                break
            
            # Check for imagemap
            if self.patterns['imagemap'].match(line):
                in_imagemap = True
                screen.has_imagemap = True
                screen.screen_type = 'imagemap'
            
            # Check for imagemap ground and hover images
            ground_match = self.patterns['imagemap_ground'].match(line)
            if ground_match:
                screen.imagemap_ground = ground_match.group(1)
            
            hover_match = self.patterns['imagemap_hover'].match(line)
            if hover_match:
                screen.imagemap_hover = hover_match.group(1)
            
            # Check for interactive elements
            # Hotspot with Jump/Call action
            hotspot_match = self.patterns['hotspot'].match(line)
            if hotspot_match:
                coords_str = hotspot_match.group(1)
                action_type = hotspot_match.group(2).lower()  # 'Jump' or 'Call' -> 'jump' or 'call'
                destination = hotspot_match.group(3)
                
                # Parse coordinates (x, y, width, height)
                try:
                    coords = tuple(map(int, coords_str.split(', ')))
                    if len(coords) == 4:
                        element = ScreenElement(
                            element_type='hotspot',
                            coordinates=coords,
                            destination=destination,
                            action_type=action_type,
                            file_path=file_path,
                            line_number=current_line,
                            element_index=element_index
                        )
                        screen.elements.append(element)
                        element_index += 1
                        print(f"[HOTSPOT PARSED] {screen_name}: {coords} -> {destination} via {action_type}")
                except ValueError:
                    # Skip malformed coordinates
                    pass
            
            # Textbutton with Jump/Call action
            textbutton_match = self.patterns['textbutton'].match(line)
            if textbutton_match:
                button_text = textbutton_match.group(1)
                action_type = textbutton_match.group(2).lower()  # 'Jump' or 'Call' -> 'jump' or 'call'
                destination = textbutton_match.group(3)
                
                element = ScreenElement(
                    element_type='textbutton',
                    text=button_text,
                    destination=destination,
                    action_type=action_type,
                    file_path=file_path,
                    line_number=current_line,
                    element_index=element_index
                )
                screen.elements.append(element)
                element_index += 1
                print(f"[TEXTBUTTON PARSED] {screen_name}: '{button_text}' -> {destination} via {action_type}")
            
            # Imagebutton with Jump/Call action (basic single-line detection)
            imagebutton_match = self.patterns['imagebutton'].match(line)
            if imagebutton_match:
                action_type = imagebutton_match.group(1).lower()
                destination = imagebutton_match.group(2)
                
                element = ScreenElement(
                    element_type='imagebutton',
                    destination=destination,
                    action_type=action_type,
                    file_path=file_path,
                    line_number=current_line,
                    element_index=element_index
                )
                screen.elements.append(element)
                element_index += 1
            
            # Multi-line imagebutton detection (Enhanced for complex syntax)
            elif line.strip().startswith('imagebutton') and line.strip().endswith(':'):
                # Found imagebutton start (handles both simple and complex syntax)
                # Examples: 
                # - imagebutton:
                # - imagebutton anchor (0.5, 0.5):
                imagebutton_start_line = current_line
                action_found = False
                
                # Look ahead for action statement (up to 10 lines)
                for look_ahead in range(1, 11):
                    if current_line - 1 + look_ahead >= len(lines):
                        break
                        
                    future_line = lines[current_line - 1 + look_ahead].strip()
                    
                    # Check for action Jump() or action Call() with both single and double quotes
                    action_jump_match = re.match(r'action\s+Jump\s*\(\s*["\']([^"\']+)["\']\s*\)', future_line, re.IGNORECASE)
                    action_call_match = re.match(r'action\s+Call\s*\(\s*["\']([^"\']+)["\']\s*\)', future_line, re.IGNORECASE)
                    
                    if action_jump_match:
                        destination = action_jump_match.group(1)
                        action_type = 'jump'
                        action_found = True
                        break
                    elif action_call_match:
                        destination = action_call_match.group(1)
                        action_type = 'call'
                        action_found = True
                        break
                    
                    # Stop if we hit another imagebutton or screen element
                    if any(keyword in future_line for keyword in ['imagebutton', 'textbutton:', 'hotspot', 'screen ']):
                        break
                
                if action_found:
                    element = ScreenElement(
                        element_type='imagebutton',
                        destination=destination,
                        action_type=action_type,
                        file_path=file_path,
                        line_number=imagebutton_start_line,
                        element_index=element_index
                    )
                    screen.elements.append(element)
                    element_index += 1
                    print(f"[MULTI-LINE IMAGEBUTTON] Found: {destination} via {action_type} (line {imagebutton_start_line})")
            
            current_line += 1
        
        return screen
    
    def find_screen_calls(self, project_path: str) -> Dict[str, List[str]]:
        """
        Find all screen calls in the project and map them to their containing labels.
        
        Args:
            project_path: Path to the Ren'Py project
            
        Returns:
            Dictionary mapping label names to lists of screen names they call
        """
        screen_calls = {}
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
                        continue
                
                for line_num, line in enumerate(lines, 1):
                    # Track current label
                    label_match = self.patterns['label'].match(line)
                    if label_match:
                        current_label = label_match.group(1)
                        if current_label not in screen_calls:
                            screen_calls[current_label] = []
                    
                    # Check for call screen statements
                    call_screen_match = self.patterns['call_screen'].match(line)
                    if call_screen_match and current_label:
                        screen_name = call_screen_match.group(1)
                        screen_calls[current_label].append(screen_name)
                        print(f"[SCREEN DEBUG] Found call screen: {current_label} → {screen_name}")
        
        except Exception as e:
            raise RenpyParseError(f"Failed to find screen calls: {str(e)}")
        
        return screen_calls
    
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
            
            # PHASE 4: Generate screen element flows (NEW)
            screen_element_flows = self._generate_screen_element_flows(project_path)
            flows.extend(screen_element_flows)
            
            print(f"[SCREEN FLOWS] Added {len(screen_element_flows)} screen element flows")
            
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
        
        Enhanced to filter out flows that are already handled by menu choices to prevent
        duplicate flows from label to destination.
        
        CRITICAL: This method now EXCLUDES any jump/call statements that are inside menu blocks,
        as those flows belong to the menu choices, not the label's immediate scope.
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
            
            # Track menu blocks to exclude their content from label flow detection
            inside_menu = False
            menu_indent = 0
            
            for line_num, line in enumerate(lines, 1):
                stripped_line = line.strip()
                current_indent = len(line) - len(line.lstrip())
                
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
                    inside_menu = False  # Reset menu tracking
                    continue
                
                # Detect menu start
                menu_match = self.patterns['menu'].match(line) or self.patterns['menu_with_name'].match(line)
                if menu_match and current_label:
                    inside_menu = True
                    menu_indent = current_indent
                    continue
                
                # Check if we've exited the menu block
                if inside_menu and stripped_line and current_indent <= menu_indent:
                    inside_menu = False
                
                # Skip flow detection if we're inside a menu block
                if inside_menu:
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
                
                # Find screen calls
                call_screen_match = self.patterns['call_screen'].match(line)
                if call_screen_match and current_label:
                    screen_name = call_screen_match.group(1)
                    flows.append(LabelFlow(
                        source_label=current_label,
                        target_label=screen_name,
                        flow_type='screen_call',
                        file_path=file_path,
                        line_number=line_num,
                        context=f"call screen {screen_name}",
                        screen_info={'screen_name': screen_name, 'call_type': 'call'}
                    ))
                
                # Find show screen statements
                show_screen_match = self.patterns['show_screen'].match(line)
                if show_screen_match and current_label:
                    screen_name = show_screen_match.group(1)
                    flows.append(LabelFlow(
                        source_label=current_label,
                        target_label=screen_name,
                        flow_type='screen_call',
                        file_path=file_path,
                        line_number=line_num,
                        context=f"show screen {screen_name}",
                        screen_info={'screen_name': screen_name, 'call_type': 'show'}
                    ))
            
            # Handle the last label in the file
            if current_label and current_label_start_line and current_file_path:
                conditional_flows = self._extract_conditional_jumps(
                    current_label, current_file_path, current_label_start_line
                )
                flows.extend(conditional_flows)
        
        # REMOVED: Menu choice flows are now handled by the AHS system
        # The AHS creates flows from choice nodes to destinations, not from parent labels
        # This prevents duplicate/incorrect flows from parent labels to destinations
        
        # Add flows from menu choices - DISABLED in favor of AHS choice-to-destination flows
        # menus = self.find_all_menus(project_path)
        # for menu in menus:
        #     for choice in menu.choices:
        #         # Add flows for standard choice destinations (jumps/calls)
        #         if choice.destination:
        #             flows.append(LabelFlow(
        #                 source_label=menu.label_context,  # This was WRONG - creates intro -> d01_intro_comein
        #                 target_label=choice.destination,
        #                 flow_type='menu_choice',
        #                 file_path=choice.file_path,
        #                 line_number=choice.line_number,
        #                 context=choice.text,
        #                 condition=choice.condition
        #             ))
                
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
        
        # ENHANCED: Filter out explicit flows that are already handled by menu choices
        filtered_flows = self._filter_duplicate_explicit_flows(flows, project_path)
        
        return filtered_flows
    
    def _filter_duplicate_explicit_flows(self, flows: List[LabelFlow], project_path: str) -> List[LabelFlow]:
        """
        Filter out explicit flows (jumps/calls) that are already handled by menu choices.
        
        This prevents duplicate flows where a jump inside a menu choice is incorrectly
        attributed to the parent label instead of the choice.
        
        Args:
            flows: List of all detected explicit flows
            project_path: Path to the project
            
        Returns:
            Filtered list of flows with duplicates removed
        """
        # Get all menu choice destinations to identify potential duplicates
        all_menus = self.find_all_menus(project_path)
        menu_choice_destinations = set()
        
        for menu in all_menus:
            if hasattr(menu, 'choices'):
                for choice in menu.choices:
                    if hasattr(choice, 'destination') and choice.destination:
                        # Store both the destination and the source label for context
                        menu_choice_destinations.add((menu.label_context, choice.destination))
        
        filtered_flows = []
        
        for flow in flows:
            # Skip filtering for menu_choice flows - these are always valid
            if flow.flow_type == 'menu_choice':
                filtered_flows.append(flow)
                continue
            
            # Check if this explicit flow duplicates a menu choice flow
            flow_key = (flow.source_label, flow.target_label)
            
            if flow_key in menu_choice_destinations:
                # This explicit flow (jump/call) is already handled by a menu choice
                print(f"[EXPLICIT FLOW FILTER] Filtering duplicate explicit flow: {flow.source_label} -> {flow.target_label} ({flow.flow_type}) - handled by menu choice")
                continue
            
            # Keep the flow if it's not a duplicate
            filtered_flows.append(flow)
        
        print(f"[EXPLICIT FLOW FILTER] Filtered {len(flows) - len(filtered_flows)} duplicate explicit flows")
        return filtered_flows

    def _extract_conditional_jumps(self, label_name: str, file_path: str, start_line: int) -> List[LabelFlow]:
        """
        CONDITIONAL JUMP DETECTOR: Extract ALL possible jump targets from conditional blocks.
        
        This method performs static analysis to find jump statements in if/elif/else blocks,
        creating flows for all possible execution paths regardless of variable values.
        
        CRITICAL: This method now EXCLUDES any jump/call statements that are inside menu blocks,
        as those flows belong to the menu choices, not the label's immediate scope.
        
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
            
            # Track menu blocks to exclude their content
            inside_menu = False
            menu_indent = 0
            
            # SIMPLIFIED CONDITIONAL JUMP DETECTION
            # Scan through the label content for jump statements in conditional blocks
            i = start_line
            while i < label_end_line:
                line = lines[i]
                stripped_line = line.strip()
                current_indent = len(line) - len(line.lstrip())
                
                # Detect menu start
                menu_match = self.patterns['menu'].match(line) or self.patterns['menu_with_name'].match(line)
                if menu_match:
                    inside_menu = True
                    menu_indent = current_indent
                    i += 1
                    continue
                
                # Check if we've exited the menu block
                if inside_menu and stripped_line and current_indent <= menu_indent:
                    inside_menu = False
                
                # Skip flow detection if we're inside a menu block
                if inside_menu:
                    i += 1
                    continue
                
                # Look for jump statements preceded by if/elif/else  
                if re.match(r'^\s*jump\s+([a-zA-Z_][a-zA-Z0-9_]*)', stripped_line, re.IGNORECASE):
                    jump_match = re.match(r'^\s*jump\s+([a-zA-Z_][a-zA-Z0-9_]*)', stripped_line, re.IGNORECASE)
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
            
            # ENHANCED LOGIC: Don't blanket-skip labels with menus
            # Instead, check if the label (including its menus) provides guaranteed control transfer
            flow_analysis = label_flow_analysis.get(current_label, {})
            has_guaranteed_outgoing_flow = flow_analysis.get('has_guaranteed_outgoing_flow', False)
            
            # For labels with menus, check if menus provide guaranteed control transfer
            if current_label in labels_with_menus and not has_guaranteed_outgoing_flow:
                # Analyze if the menu choices provide comprehensive flow coverage
                menu_provides_guaranteed_flow = self._does_menu_provide_guaranteed_flow(current_label, menus, project_path)
                if menu_provides_guaranteed_flow:
                    has_guaranteed_outgoing_flow = True
            
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
    
    def _does_menu_provide_guaranteed_flow(self, label_name: str, menus: List[MenuStructure], project_path: str) -> bool:
        """
        Analyze if menus within a label provide guaranteed control transfer.
        
        A menu provides guaranteed flow if ALL execution paths through the label's 
        menu system lead to control transfer. This includes handling cases where
        multiple menus work together (e.g., nested menus parsed as separate menus).
        
        Args:
            label_name: Name of the label containing menus
            menus: All menu structures in the project
            project_path: Path to the project
            
        Returns:
            True if menus guarantee control transfer, False otherwise
        """
        label_menus = [menu for menu in menus if menu.label_context == label_name]
        
        if not label_menus:
            return False  # No menus found for this label
        
        # ENHANCED LOGIC: Check if the menu system as a whole provides guaranteed flow
        # This handles cases where nested menus are parsed as separate menus
        return self._analyze_menu_system_flow_coverage(label_menus, label_name)
    
    def _analyze_menu_system_flow_coverage(self, label_menus: List, label_name: str) -> bool:
        """
        Analyze if a system of menus provides complete flow coverage.
        
        This method handles cases where nested menus are parsed as separate menus
        but still work together to provide guaranteed control transfer.
        
        Args:
            label_menus: List of MenuStructure objects for this label
            label_name: Name of the label containing these menus
            
        Returns:
            True if the menu system provides guaranteed control transfer
        """
        if not label_menus:
            return False
        
        # Strategy: Check if there's a "flow path" through the menu system that
        # guarantees all execution leads to control transfer
        
        # Case 1: Single menu with all choices providing control transfer
        if len(label_menus) == 1:
            menu = label_menus[0]
            if not hasattr(menu, 'choices') or not menu.choices:
                return False
                
            # Check if ALL choices provide control transfer
            for choice in menu.choices:
                if not self._choice_provides_guaranteed_flow(choice, label_name):
                    return False
            return True
        
        # Case 2: Multiple menus - check if they form a complete flow system
        # This handles the My Milly case where nested menus are parsed separately
        return self._analyze_multi_menu_flow_system(label_menus, label_name)
    
    def _analyze_multi_menu_flow_system(self, label_menus: List, label_name: str) -> bool:
        """
        Analyze if multiple menus in a label form a complete flow system.
        
        This handles cases like My Milly where:
        - Menu 1: "Open the door" (no destination, continues to Menu 2)
        - Menu 2: "Come on in" (has destination, provides control transfer)
        
        CRITICAL: A menu system only provides guaranteed flow if ALL execution paths
        lead to explicit control transfer. If ANY path can fall through, implicit flow
        is needed.
        
        Args:
            label_menus: List of MenuStructure objects for this label
            label_name: Name of the label containing these menus
            
        Returns:
            True if the multi-menu system provides guaranteed control transfer
        """
        if not label_menus:
            return False
        
        # Check if ALL menus in the system provide guaranteed control transfer
        # A menu system can only guarantee flow if every menu guarantees it
        all_menus_provide_guaranteed_flow = True
        
        for menu in label_menus:
            if not hasattr(menu, 'choices') or not menu.choices:
                # Empty menu cannot provide guaranteed flow
                all_menus_provide_guaranteed_flow = False
                continue
            
            # Check if ALL choices in this menu provide guaranteed control transfer
            menu_provides_guaranteed_flow = True
            for choice in menu.choices:
                if not self._choice_provides_guaranteed_flow(choice, label_name):
                    menu_provides_guaranteed_flow = False
                    break
            
            if not menu_provides_guaranteed_flow:
                all_menus_provide_guaranteed_flow = False
        
        # FIXED LOGIC: Only return True if ALL menus provide guaranteed flow
        # If even ONE menu can fall through, the label needs implicit flow
        if all_menus_provide_guaranteed_flow and len(label_menus) > 0:
            print(f"[MENU ANALYSIS] Multi-menu system in '{label_name}' provides guaranteed flow")
            return True
        
        return False
    
    def _choice_provides_guaranteed_flow(self, choice, source_label_name: str) -> bool:
        """
        Analyze if a single choice provides guaranteed control transfer.
        
        A choice provides guaranteed flow if:
        1. It has a direct destination that transfers control away, OR
        2. It has nested menus where ALL paths lead to control transfer
        
        Args:
            choice: MenuChoice object to analyze
            source_label_name: Name of the label containing this choice
            
        Returns:
            True if choice guarantees control transfer, False otherwise
        """
        # Check for direct destination
        choice_destination = getattr(choice, 'destination', None)
        
        if choice_destination:
            # If choice destination is the same label, it's a loop (no control transfer out)
            if choice_destination == source_label_name:
                return False
            # Direct destination to another label = guaranteed control transfer
            return True
        
        # Check for nested menu structures
        nested_menus = getattr(choice, 'nested_menu_structures', [])
        
        if not nested_menus:
            # No destination and no nested menus = continues in same label (no control transfer)
            return False
        
        # Analyze nested menus - ALL must provide guaranteed control transfer
        for nested_menu in nested_menus:
            if not hasattr(nested_menu, 'choices') or not nested_menu.choices:
                continue  # Skip empty nested menus
            
            # Check if ALL choices in the nested menu provide control transfer
            for nested_choice in nested_menu.choices:
                if not self._choice_provides_guaranteed_flow(nested_choice, source_label_name):
                    return False  # Found a path that doesn't guarantee control transfer
        
        # All nested menu paths provide guaranteed control transfer
        return True
    
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
            # CRITICAL FIX: 'call' statements do NOT provide guaranteed control transfer
            # because they return to continue execution in the same label
            if flow.flow_type in ['jump', 'return']:
                # Check if this flow is conditional by examining the source
                is_conditional = self._is_flow_conditional(flow, project_path)
                
                if is_conditional:
                    conditional_flows.append(flow)
                else:
                    unconditional_flows.append(flow)
            elif flow.flow_type == 'call':
                # Call statements are always treated as non-guaranteed flow
                # because they return to continue execution
                conditional_flows.append(flow)
        
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
        Check if a flow is inside a conditional block (if/elif/else/menu choice).
        
        Enhanced to detect menu choices as conditional contexts, which was missing
        and causing implicit flow detection bugs.
        
        Args:
            flow: The flow to check
            project_path: Path to the project
            
        Returns:
            True if the flow appears to be conditional
        """
        try:
            # Use the same encoding validation as the rest of the parser
            detected_encoding, content = self.validate_and_normalize_encoding(flow.file_path)
            lines = content.splitlines()
            
            flow_line_idx = flow.line_number - 1  # Convert to 0-based
            
            if flow_line_idx < 0 or flow_line_idx >= len(lines):
                return False
            
            # Get the indentation level of the flow line
            flow_line = lines[flow_line_idx]
            flow_indent = len(flow_line) - len(flow_line.lstrip())
            
            # Look backwards from the flow line to find controlling structures
            # Check a reasonable range backwards (up to 100 lines or start of file)
            # Increased from 50 to 100 to handle cases like 23 Sisters where menu choices
            # can be 56+ lines away from their return statements
            search_start = max(0, flow_line_idx - 100)
            
            for i in range(flow_line_idx - 1, search_start - 1, -1):
                line = lines[i]
                line_stripped = line.strip()
                line_indent = len(line) - len(line.lstrip())
                
                # Only consider lines with less indentation (potential controllers)
                if line_indent < flow_indent:
                    # Check for if/elif/else statements
                    if re.match(r'^\s*if\s+', line_stripped, re.IGNORECASE):
                        return True
                    elif re.match(r'^\s*elif\s+', line_stripped, re.IGNORECASE):
                        return True
                    elif re.match(r'^\s*else\s*:', line_stripped, re.IGNORECASE):
                        return True
                    
                    # ENHANCED: Check for menu choices (this was the missing piece!)
                    elif re.match(r'^\s*"[^"]*"\s*(?:\([^)]*\))?\s*:', line_stripped):
                        # This is a menu choice - flows inside it are conditional
                        return True
                    
                    # Check for menu start (for context)
                    elif line_stripped.startswith('menu'):
                        # Continue looking - the choice itself makes it conditional
                        continue
                    
                    # Check for label boundary - stop searching if we hit another label
                    elif line_stripped.startswith('label '):
                        break
            
            return False
            
        except Exception as e:
            # If we can't determine, assume it's not conditional
            # Log the error for debugging
            print(f"[FLOW CONDITIONAL] Warning: Could not analyze flow at {flow.file_path}:{flow.line_number}: {e}")
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
                    # Use the new encoding validation and BOM detection
                    detected_encoding, content = self.validate_and_normalize_encoding(file_path)
                    lines = content.splitlines()
                    
                    for line_num, line in enumerate(lines, 1):
                        all_lines.append((file_path, line_num, line))
                        
                        label_match = self.patterns['label'].match(line)
                        if label_match:
                            label_name = label_match.group(1)
                            label_definitions[label_name] = (file_path, line_num)
                            
                except Exception as e:
                    print(f"[ENCODING] Warning: Could not process {file_path}: {e}")
                    continue
        
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
        
        # Analyze label properties and create menu nodes using the working menu detection
        # FIXED: Use find_all_menus instead of MenuAnalyzer which was missing day5 menus
        menus = self.find_all_menus(project_path)
        
        # Create a named menu registry for handling jumps to named menus
        named_menu_registry = {}  # {menu_name: containing_label}
        
        # CRITICAL FIX: Add label menus to flow graph as valid jump targets
        # BUT: Only create label nodes for actual label menus, not named menus within labels
        for menu_structure in menus:
            if menu_structure.label_name and menu_structure.label_name not in graph:
                # Check if this is an actual label menu (label followed by menu) 
                # vs a named menu within a label (menu MenuName: within a label)
                is_actual_label_menu = self._is_actual_label_menu(menu_structure)
                
                if is_actual_label_menu:
                    # Create a LabelNode for the actual label menu
                    graph[menu_structure.label_name] = LabelNode(
                        name=menu_structure.label_name,
                        file_path=menu_structure.file_path,
                        line_number=menu_structure.line_number
                    )
                    print(f"[LABEL MENU FIX] Added label menu '{menu_structure.label_name}' to flow graph")
                else:
                    # Register the named menu for jump resolution
                    named_menu_registry[menu_structure.label_name] = menu_structure.label_context
                    print(f"[NAMED MENU] Skipping named menu '{menu_structure.label_name}' within label '{menu_structure.label_context}' - not creating separate label node")
        
        # Store named menu registry in the graph for flow resolution
        graph['_named_menu_registry'] = named_menu_registry
        
        # NAMED MENU FIX: Resolve jumps to named menus by redirecting them to containing labels
        self._resolve_named_menu_jumps(graph, named_menu_registry)
        
        # Process screen structures and screen calls
        screens = self.find_all_screens(project_path)
        screen_calls = self.find_screen_calls(project_path)
        
        # Add screen calls to label nodes
        for label_name, called_screens in screen_calls.items():
            if label_name in graph:
                graph[label_name].screen_calls = called_screens
                graph[label_name].has_screen_calls = len(called_screens) > 0
                print(f"[SCREEN CALLS] Label '{label_name}' calls screens: {called_screens}")
        
        # Store screen structures in the graph for AHS access
        # We'll add them as a special _screen_structures key
        if screens:
            graph['_screen_structures'] = {screen.screen_name: screen for screen in screens}
            print(f"[SCREEN STRUCTURES] Added {len(screens)} screen structures to flow graph")
        
        # Group menus by their label context for processing
        menus_by_label = {}
        menus_without_context = []
        for menu in menus:
            if menu.label_context:
                if menu.label_context not in menus_by_label:
                    menus_by_label[menu.label_context] = []
                menus_by_label[menu.label_context].append(menu)
            else:
                menus_without_context.append((menu.file_path, menu.line_number))
        
        print(f"[MENU GROUPING] Grouped {len(menus)} menus:")
        print(f"[MENU GROUPING]   - {sum(len(v) for v in menus_by_label.values())} menus with label_context")
        print(f"[MENU GROUPING]   - {len(menus_without_context)} menus WITHOUT label_context")
        if menus_without_context:
            print(f"[MENU GROUPING] First 5 menus without context: {menus_without_context[:5]}")
                
        
        # Create MenuNode objects and associate them with labels
        for label_name, label_menus in menus_by_label.items():
                
            if label_name in graph:
                node = graph[label_name]
                
                # Store original MenuStructure objects
                node.menu_structures = label_menus
                
                # Create enhanced MenuNode objects with hierarchical support
                all_menu_nodes = []  # Collect all MenuNodes including nested ones
                
                for i, menu_structure in enumerate(label_menus):
                    # Only create MenuNodes for truly top-level menus (nesting_level == 0)
                    # Nested menus are now stored in their parent choice's nested_menu_structures
                    if menu_structure.nesting_level == 0:  # Only process top-level menus
                        main_menu_node = self._create_menu_node_from_structure(menu_structure, i)
                        
                        # Process nested menus recursively
                        self._process_nested_menu_structures(main_menu_node, menu_structure)
                        
                        # Clean up any temporary nested nodes storage
                        if hasattr(main_menu_node, '_nested_menu_nodes'):
                            delattr(main_menu_node, '_nested_menu_nodes')
                        
                        all_menu_nodes.append(main_menu_node)
                        print(f"Created top-level menu for {label_name}: {main_menu_node.node_id}")
                    else:
                        print(f"Skipping nested menu at level {menu_structure.nesting_level} for {label_name} - handled by parent choice")
                
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
            # Skip non-LabelNode entries (like _screen_structures)
            if label_name.startswith('_') or not hasattr(node, 'has_dialogue'):
                continue
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
            # Skip non-LabelNode entries (like _screen_structures)
            if label_name.startswith('_') or not hasattr(node, 'incoming_flows'):
                continue
            if len(node.incoming_flows) == 0:
                mark_reachable(label_name)
        
        # Set reachability flags
        for label_name, node in graph.items():
            # Skip non-LabelNode entries (like _screen_structures)
            if label_name.startswith('_') or not hasattr(node, 'is_reachable'):
                continue
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