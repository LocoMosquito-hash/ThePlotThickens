#!/usr/bin/env python3
"""
CSAP Integration Layer

Provides drop-in replacement methods for regex-based screen parsing.
This allows CSAP to be integrated into the existing flow visualizer
without changing the main architecture.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

try:
    from .csap_parser import CSAPParser
    from .csap_compatibility import convert_csap_to_screen_structure
    from .csap_exceptions import CSAPError
except ImportError:
    from csap_parser import CSAPParser
    from csap_compatibility import convert_csap_to_screen_structure
    from csap_exceptions import CSAPError

# Delay imports to avoid circular import issues
ScreenStructure = None
ScreenElement = None

def _get_parser_classes():
    """Get parser classes with delayed import to avoid circular imports."""
    global ScreenStructure, ScreenElement
    
    if ScreenStructure is None:
        try:
            import sys
            current_dir = Path(__file__).parent
            app_dir = current_dir.parent.parent.parent / "app" / "renpy-source-api"
            
            # Only add to path temporarily
            if str(app_dir) not in sys.path:
                sys.path.insert(0, str(app_dir))
                
            from parser import ScreenStructure as SS, ScreenElement as SE
            ScreenStructure = SS
            ScreenElement = SE
        except ImportError:
            # Fallback for testing
            try:
                from csap_compatibility import ScreenStructure as SS, ScreenElement as SE
                ScreenStructure = SS
                ScreenElement = SE
            except ImportError:
                # Create minimal dummy classes
                class DummyScreenStructure:
                    def __init__(self, **kwargs):
                        for k, v in kwargs.items():
                            setattr(self, k, v)
                
                class DummyScreenElement:
                    def __init__(self, **kwargs):
                        for k, v in kwargs.items():
                            setattr(self, k, v)
                
                ScreenStructure = DummyScreenStructure
                ScreenElement = DummyScreenElement
    
    return ScreenStructure, ScreenElement


class CSAPIntegratedParser:
    """
    Enhanced parser that uses CSAP for screen parsing while maintaining
    compatibility with existing regex-based parsing for other elements.
    
    This class can be used as a drop-in replacement for RenpyParser
    for screen-related functionality.
    """
    
    def __init__(self):
        """Initialize the integrated parser."""
        self.csap_parser = CSAPParser()
        self.screen_definition_pattern = re.compile(r'^\s*screen\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\([^)]*\))?\s*:', re.IGNORECASE)
        
        # Performance tracking
        self.csap_successes = 0
        self.csap_failures = 0
        self.fallback_uses = 0
    
    def parse_screen_structure(self, file_path: str, start_line: int, lines: List[str], screen_name: str) -> ScreenStructure:
        """
        Parse a screen structure using CSAP with regex fallback.
        
        This is a drop-in replacement for the original parse_screen_structure method.
        
        Args:
            file_path: Path to the file containing the screen
            start_line: Line number where the screen starts (1-indexed)
            lines: List of all lines in the file
            screen_name: Name of the screen
            
        Returns:
            ScreenStructure object with all interactive elements
        """
        try:
            # Extract the screen content from lines
            screen_content = self._extract_screen_content(lines, start_line, screen_name)
            
            if not screen_content.strip():
                # Empty screen - return empty structure
                ScreenStructure, _ = _get_parser_classes()
                return ScreenStructure(
                    screen_name=screen_name,
                    file_path=file_path,
                    line_number=start_line,
                    elements=[],
                    total_elements=0,
                    interactive_elements=0
                )
            
            # Try CSAP parsing first
            try:
                screen_node = self.csap_parser.parse_screen_text(screen_content)
                screen_structure = convert_csap_to_screen_structure(screen_node, file_path)
                
                # Ensure correct metadata
                screen_structure.screen_name = screen_name
                screen_structure.file_path = file_path
                screen_structure.line_number = start_line
                
                self.csap_successes += 1
                print(f"[CSAP SUCCESS] Parsed screen '{screen_name}' with {len(screen_structure.elements)} elements")
                return screen_structure
                
            except CSAPError as e:
                # CSAP parsing failed - log and fall back to regex
                print(f"[CSAP FALLBACK] Screen '{screen_name}': {e}")
                self.csap_failures += 1
                return self._regex_fallback_parse_screen(file_path, start_line, lines, screen_name)
                
        except Exception as e:
            # Unexpected error - fall back to regex
            print(f"[CSAP ERROR] Unexpected error parsing screen '{screen_name}': {e}")
            self.csap_failures += 1
            return self._regex_fallback_parse_screen(file_path, start_line, lines, screen_name)
    
    def _extract_screen_content(self, lines: List[str], start_line: int, screen_name: str) -> str:
        """Extract the complete screen content from lines."""
        
        debug_this_screen = False  # Set to True for debugging specific screens
        
        # Find the screen definition line
        screen_def_line = None
        for i, line in enumerate(lines):
            if i + 1 == start_line:  # Convert to 0-based indexing
                screen_def_line = i
                break
        
        if screen_def_line is None:
            return ""
        
        # Extract screen content including the definition line
        screen_lines = []
        current_line = screen_def_line
        base_indent = None
        
        if debug_this_screen:
            print(f"[EXTRACT DEBUG] Starting extraction for '{screen_name}' at line {start_line}")
        
        while current_line < len(lines):
            line = lines[current_line]
            
            if debug_this_screen:
                print(f"[EXTRACT DEBUG]   Line {current_line + 1}: '{line[:60]}...' (indent={len(line) - len(line.lstrip())})")
            
            # Skip empty lines
            if not line.strip():
                screen_lines.append(line)
                current_line += 1
                if debug_this_screen:
                    print(f"[EXTRACT DEBUG]     -> Added empty line")
                continue
            
            # Get indentation level
            indent_level = len(line) - len(line.lstrip())
            
            # If this is the first non-empty line, set base indentation
            if base_indent is None:
                base_indent = indent_level
                screen_lines.append(line)
                current_line += 1
                if debug_this_screen:
                    print(f"[EXTRACT DEBUG]     -> Added as first line, base_indent={base_indent}")
                continue
            
            # If we're back to base indentation or less, check if we should stop
            if indent_level <= base_indent and line.strip():
                # Stop if it's a comment at base level or a new top-level construct
                if line.strip().startswith('#'):
                    if debug_this_screen:
                        print(f"[EXTRACT DEBUG]     -> BREAK: Found comment at base level")
                    break
                # Check if this starts a new top-level construct
                if (re.match(r'^\s*(label|screen|init|define|default)\s+', line, re.IGNORECASE) or
                    re.match(r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s+"', line)):  # Character dialogue
                    if debug_this_screen:
                        print(f"[EXTRACT DEBUG]     -> BREAK: Found new top-level construct")
                    break
            
            screen_lines.append(line)
            current_line += 1
            if debug_this_screen:
                print(f"[EXTRACT DEBUG]     -> Added line (total: {len(screen_lines)})")
        
        if debug_this_screen:
            print(f"[EXTRACT DEBUG] Extraction complete, collected {len(screen_lines)} lines")
        
        # Join without adding newlines since readlines() already includes them
        return ''.join(screen_lines)
    
    def _regex_fallback_parse_screen(self, file_path: str, start_line: int, lines: List[str], screen_name: str) -> ScreenStructure:
        """
        Fallback to basic regex parsing when CSAP fails.
        
        This provides a minimal implementation to ensure compatibility.
        """
        self.fallback_uses += 1
        
        # Create basic screen structure
        ScreenStructure, _ = _get_parser_classes()
        screen = ScreenStructure(
            screen_name=screen_name,
            file_path=file_path,
            line_number=start_line,
            elements=[],
            total_elements=0,
            interactive_elements=0
        )
        
        # Basic regex patterns for fallback
        textbutton_pattern = re.compile(r'^\s*textbutton\s+"([^"]+)".*?action\s+(Jump|Call)\s*\(\s*["\']([^"\']+)["\']\s*\)', re.IGNORECASE)
        hotspot_pattern = re.compile(r'^\s*hotspot\s*\(([^)]+)\)\s*action\s+(Jump|Call)\s*\(\s*["\']([^"\']+)["\']\s*\)', re.IGNORECASE)
        imagebutton_pattern = re.compile(r'^\s*imagebutton\s+.*?action\s+(Jump|Call)\s*\(\s*["\']([^"\']+)["\']\s*\)', re.IGNORECASE)
        
        element_index = 0
        current_line = start_line
        
        while current_line < len(lines) and current_line - start_line < 50:  # Limit search
            line = lines[current_line]
            
            # Try textbutton
            match = textbutton_pattern.match(line)
            if match:
                element = ScreenElement(
                    element_type='textbutton',
                    text=match.group(1),
                    destination=match.group(3),
                    action_type=match.group(2).lower(),
                    file_path=file_path,
                    line_number=current_line + 1,
                    element_index=element_index
                )
                screen.elements.append(element)
                element_index += 1
                current_line += 1
                continue
            
            # Try hotspot
            match = hotspot_pattern.match(line)
            if match:
                # Parse coordinates
                coords_str = match.group(1)
                try:
                    coords = tuple(map(int, coords_str.split(',')))
                    if len(coords) >= 4:
                        element = ScreenElement(
                            element_type='hotspot',
                            coordinates=coords[:4],
                            destination=match.group(3),
                            action_type=match.group(2).lower(),
                            file_path=file_path,
                            line_number=current_line + 1,
                            element_index=element_index
                        )
                        screen.elements.append(element)
                        element_index += 1
                except ValueError:
                    pass  # Skip invalid coordinates
                current_line += 1
                continue
            
            # Try imagebutton
            match = imagebutton_pattern.match(line)
            if match:
                element = ScreenElement(
                    element_type='imagebutton',
                    destination=match.group(2),
                    action_type=match.group(1).lower(),
                    file_path=file_path,
                    line_number=current_line + 1,
                    element_index=element_index
                )
                screen.elements.append(element)
                element_index += 1
            
            current_line += 1
        
        # Update metadata
        screen.total_elements = len(screen.elements)
        screen.interactive_elements = len([e for e in screen.elements if e.destination])
        
        print(f"[REGEX FALLBACK] Parsed screen '{screen_name}' with {len(screen.elements)} elements")
        return screen
    
    def find_all_screens(self, project_path: str) -> List[ScreenStructure]:
        """
        Find and parse all screen structures in the project using CSAP.
        
        This is a drop-in replacement for the original find_all_screens method.
        """
        screens = []
        
        try:
            # Find all .rpy files
            rpy_files = []
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    if file.endswith('.rpy'):
                        file_path = os.path.join(root, file)
                        if os.path.isfile(file_path):  # Ensure it's actually a file
                            rpy_files.append(file_path)
            
            print(f"[CSAP INTEGRATION] Processing {len(rpy_files)} .rpy files for screens")
            
            # Process each file
            for file_path in rpy_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                except UnicodeDecodeError:
                    try:
                        with open(file_path, 'r', encoding='latin-1') as f:
                            lines = f.readlines()
                    except Exception as e:
                        print(f"[CSAP INTEGRATION] Could not read {file_path}: {e}")
                        continue
                except Exception as e:
                    print(f"[CSAP INTEGRATION] Could not read {file_path}: {e}")
                    continue
                
                # Find screen definitions
                for i, line in enumerate(lines):
                    match = self.screen_definition_pattern.match(line)
                    if match:
                        screen_name = match.group(1)
                        start_line = i + 1  # Convert to 1-based indexing
                        
                        # Parse the screen
                        screen_structure = self.parse_screen_structure(file_path, start_line, lines, screen_name)
                        
                        # Apply system screen filter
                        if self._should_include_screen(screen_structure, file_path):
                            screens.append(screen_structure)
                        else:
                            print(f"[SYSTEM SCREEN FILTER] Excluded '{screen_name}' from {os.path.basename(file_path)} (system screen with no story flow elements)")
            
            print(f"[CSAP INTEGRATION] Found {len(screens)} screens total")
            self._print_performance_stats()
            
        except Exception as e:
            print(f"[CSAP INTEGRATION] Error in find_all_screens: {e}")
        
        return screens
    
    def _should_include_screen(self, screen_structure: ScreenStructure, file_path: str) -> bool:
        """
        Determine if a screen should be included in the flow visualization.
        
        Rule: Exclude default system screens from screens.rpy unless they contain
        story flow elements (Jump/Call actions).
        
        Args:
            screen_structure: The parsed screen structure
            file_path: Path to the file containing the screen
            
        Returns:
            bool: True if screen should be included, False to filter out
        """
        # Only apply filter to screens.rpy files
        if not file_path.endswith('screens.rpy'):
            return True  # Include all screens from non-screens.rpy files
        
        # List of default system screen names (case-insensitive)
        default_system_screens = {
            'say', 'input', 'choice', 'quick_menu', 'navigation', 'main_menu',
            'game_menu', 'save', 'load', 'file_slots', 'preferences', 'about',
            'help', 'keyboard_help', 'mouse_help', 'gamepad_help', 'confirm',
            'skip_indicator', 'notify', 'nvl', 'nvl_dialogue', 'history'
        }
        
        screen_name = screen_structure.screen_name.lower()
        
        # If it's not a default system screen, always include it
        if screen_name not in default_system_screens:
            return True
        
        # For system screens, check if they have story flow elements
        has_story_flow = any(
            element.destination and element.action_type in ['jump', 'call']
            for element in screen_structure.elements
            if element.destination  # Must have a destination
        )
        
        if has_story_flow:
            print(f"[SYSTEM SCREEN FILTER] Including system screen '{screen_structure.screen_name}' (has {screen_structure.interactive_elements} story flow elements)")
            return True
        else:
            # System screen with no story flow elements - exclude it
            return False
    
    def _print_performance_stats(self):
        """Print CSAP performance statistics."""
        total = self.csap_successes + self.csap_failures
        if total > 0:
            success_rate = (self.csap_successes / total) * 100
            print(f"[CSAP STATS] Success: {self.csap_successes}, Failures: {self.csap_failures}, Fallbacks: {self.fallback_uses}")
            print(f"[CSAP STATS] Success Rate: {success_rate:.1f}%")
    
    def get_parsing_stats(self) -> Dict[str, int]:
        """Get parsing performance statistics."""
        return {
            'csap_successes': self.csap_successes,
            'csap_failures': self.csap_failures,
            'fallback_uses': self.fallback_uses,
            'total_attempts': self.csap_successes + self.csap_failures
        }
