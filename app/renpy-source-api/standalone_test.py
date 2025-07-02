#!/usr/bin/env python3
"""
Standalone test script for the Ren'Py Source API.

This script contains all the necessary code inline to avoid import issues.
Use this if the package-based test scripts have import problems.
"""

import os
import sys
import sqlite3
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================

# Primary test VN path - CHANGE THIS to your decompiled Ren'Py game folder
TEST_VN_PATH = r"T:\AG\Savior-0.16c-pc\game"

# Alternative test paths
ALTERNATIVE_PATHS = {
    "accept_the_past": r"T:\AG\AcceptthePast-0.1-pc\game",
    "blairewood": r"T:\AG\Blairewood-1.0-pc\game",
    "the_way": r"T:\AG\TheWay-pc\game",
    "detective_necro": r"T:\AG\DetectiveNecro-0.55-pc\game",
    "grandmas_house": r"T:\AG\GrandmasHouse-V0.11-pc\game",
}

# =============================================================================
# EXCEPTION CLASSES
# =============================================================================

class RenpyAnalysisError(Exception):
    """Base exception for Ren'Py analysis errors."""
    pass

class RenpyParseError(RenpyAnalysisError):
    """Exception raised when parsing .rpy files fails."""
    
    def __init__(self, message: str, filename: str = None, line_number: int = None):
        super().__init__(message)
        self.filename = filename
        self.line_number = line_number

class RenpyProjectError(RenpyAnalysisError):
    """Exception raised when there are issues with the Ren'Py project structure."""
    pass

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class RenpyLine:
    """Represents a parsed line from a .rpy file."""
    file_path: str
    line_number: int
    line_type: str
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
    character_definitions: Dict[str, str]
    label_list: List[str]
    errors: List[str]

# =============================================================================
# PARSER CLASS
# =============================================================================

class RenpyParser:
    """Parser for Ren'Py script files."""
    
    def __init__(self):
        """Initialize the parser with regex patterns."""
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
        """Find all .rpy files in the project directory."""
        project_dir = Path(project_path)
        if not project_dir.exists():
            raise RenpyProjectError(f"Project directory does not exist: {project_path}")
        
        rpy_files = []
        for rpy_file in project_dir.glob("**/*.rpy"):
            relative_path = rpy_file.relative_to(project_dir)
            if relative_path.name not in self.excluded_files:
                rpy_files.append(str(relative_path))
        
        return sorted(rpy_files)
    
    def parse_file(self, file_path: str) -> List[RenpyLine]:
        """Parse a single .rpy file and extract structured information."""
        parsed_lines = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    parsed_line = self._parse_line(file_path, line_num, line)
                    if parsed_line:
                        parsed_lines.append(parsed_line)
        except UnicodeDecodeError:
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
        
        if not stripped:
            return None
        
        for pattern_name, pattern in self.patterns.items():
            match = pattern.match(line)
            if match:
                return self._create_renpy_line(file_path, line_num, line, pattern_name, match)
        
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
        """Analyze a complete Ren'Py project and return an overview."""
        errors = []
        
        try:
            rpy_files = self.find_rpy_files(project_path)
            
            total_lines = 0
            total_dialogue_lines = 0
            total_labels = 0
            total_menus = 0
            character_definitions = {}
            label_list = []
            
            for rpy_file in rpy_files:
                try:
                    file_path = os.path.join(project_path, rpy_file)
                    parsed_lines = self.parse_file(file_path)
                    
                    total_lines += len(parsed_lines)
                    
                    for line in parsed_lines:
                        if line.line_type in ['dialogue', 'narrator']:
                            total_dialogue_lines += 1
                        elif line.line_type == 'label':
                            total_labels += 1
                            if line.label_name:
                                label_list.append(line.label_name)
                        elif line.line_type == 'menu':
                            total_menus += 1
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

# =============================================================================
# CORE PROJECT CLASS
# =============================================================================

class RenpyProject:
    """Main interface for analyzing and querying Ren'Py visual novel projects."""
    
    def __init__(self, project_path: str):
        """Initialize a Ren'Py project analyzer."""
        self.project_path = str(Path(project_path).resolve())
        self.parser = RenpyParser()
        self.is_analyzed = False
        self.overview: Optional[ProjectOverview] = None
        
        if not os.path.exists(self.project_path):
            raise RenpyProjectError(f"Project path does not exist: {self.project_path}")
        
        if not self._is_renpy_project():
            raise RenpyProjectError(f"Directory does not appear to be a Ren'Py project: {self.project_path}")
    
    def _is_renpy_project(self) -> bool:
        """Check if the directory appears to be a Ren'Py project."""
        project_dir = Path(self.project_path)
        
        rpy_files = list(project_dir.glob("*.rpy"))
        if rpy_files:
            return True
        
        for subdir in project_dir.iterdir():
            if subdir.is_dir():
                sub_rpy_files = list(subdir.glob("*.rpy"))
                if sub_rpy_files:
                    return True
        
        return False
    
    def analyze(self, force_reanalysis: bool = False) -> ProjectOverview:
        """Analyze the Ren'Py project."""
        if self.is_analyzed and self.overview and not force_reanalysis:
            return self.overview
        
        try:
            print(f"[RenpyProject] Analyzing project: {self.project_path}")
            self.overview = self.parser.analyze_project(self.project_path)
            self.is_analyzed = True
            
            print(f"[RenpyProject] Analysis complete:")
            print(f"  - {self.overview.total_rpy_files} .rpy files")
            print(f"  - {self.overview.total_lines} total lines")
            print(f"  - {self.overview.total_dialogue_lines} dialogue lines")
            print(f"  - {self.overview.total_labels} labels")
            print(f"  - {self.overview.total_characters} characters")
            
            if self.overview.errors:
                print(f"  - {len(self.overview.errors)} errors occurred")
                for error in self.overview.errors[:3]:
                    print(f"    • {error}")
                if len(self.overview.errors) > 3:
                    print(f"    • ... and {len(self.overview.errors) - 3} more")
            
            return self.overview
            
        except Exception as e:
            raise RenpyAnalysisError(f"Failed to analyze project: {str(e)}")
    
    def get_project_overview(self) -> Dict[str, Any]:
        """Get a summary of the project structure."""
        if not self.is_analyzed:
            self.analyze()
        
        if not self.overview:
            raise RenpyAnalysisError("No analysis data available")
        
        return {
            "project_path": self.overview.project_path,
            "statistics": {
                "total_rpy_files": self.overview.total_rpy_files,
                "total_lines": self.overview.total_lines,
                "total_dialogue_lines": self.overview.total_dialogue_lines,
                "total_labels": self.overview.total_labels,
                "total_menus": self.overview.total_menus,
                "total_characters": self.overview.total_characters,
            },
            "files": self.overview.file_list,
            "characters": self.overview.character_definitions,
            "labels": self.overview.label_list,
            "errors": self.overview.errors,
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def search_dialogue(self, query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Search for dialogue lines containing the specified text."""
        if not self.is_analyzed:
            self.analyze()
        
        matches = []
        search_term = query if case_sensitive else query.lower()
        
        try:
            rpy_files = self.parser.find_rpy_files(self.project_path)
            
            for rpy_file in rpy_files:
                file_path = os.path.join(self.project_path, rpy_file)
                parsed_lines = self.parser.parse_file(file_path)
                
                for line in parsed_lines:
                    if line.line_type in ['dialogue', 'narrator'] and line.dialogue_text:
                        text_to_search = line.dialogue_text if case_sensitive else line.dialogue_text.lower()
                        
                        if search_term in text_to_search:
                            matches.append({
                                "file": rpy_file,
                                "line_number": line.line_number,
                                "speaker": line.speaker,
                                "dialogue": line.dialogue_text,
                                "content": line.content,
                                "match_position": text_to_search.find(search_term)
                            })
        
        except Exception as e:
            raise RenpyAnalysisError(f"Failed to search dialogue: {str(e)}")
        
        return matches

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_test_vn_path() -> str:
    """Get the best available test VN path."""
    if os.path.exists(TEST_VN_PATH):
        return TEST_VN_PATH
    
    for name, path in ALTERNATIVE_PATHS.items():
        if os.path.exists(path):
            print(f"Using fallback VN: {name} at {path}")
            return path
    
    return TEST_VN_PATH

def validate_vn_path(path: str) -> Tuple[bool, str]:
    """Validate that a path looks like a valid Ren'Py game directory."""
    if not os.path.exists(path):
        return False, f"Directory does not exist: {path}"
    
    if not os.path.isdir(path):
        return False, f"Path is not a directory: {path}"
    
    rpy_files = list(Path(path).glob("*.rpy"))
    if not rpy_files:
        for subdir in Path(path).iterdir():
            if subdir.is_dir():
                sub_rpy_files = list(subdir.glob("*.rpy"))
                if sub_rpy_files:
                    rpy_files.extend(sub_rpy_files)
                    break
    
    if not rpy_files:
        return False, f"No .rpy files found in directory: {path}"
    
    return True, f"Valid Ren'Py directory with {len(rpy_files)} .rpy files"

# =============================================================================
# MAIN TEST FUNCTION
# =============================================================================

def run_standalone_test():
    """Run the standalone Ren'Py API test."""
    print("=" * 60)
    print("REN'PY SOURCE API STANDALONE TEST")
    print("=" * 60)
    
    # Get test VN path
    test_vn_path = get_test_vn_path()
    
    # Validate the test path
    is_valid, message = validate_vn_path(test_vn_path)
    if not is_valid:
        print(f"❌ {message}")
        return False
    
    print(f"📁 Testing with VN path: {test_vn_path}")
    print(f"✅ {message}")
    
    try:
        # Test 1: Project initialization
        print("\n🔧 Test 1: Project Initialization")
        print("-" * 30)
        
        project = RenpyProject(test_vn_path)
        print(f"✅ Project created successfully")
        print(f"   Path: {project.project_path}")
        
        # Test 2: Project analysis
        print("\n📊 Test 2: Project Analysis")
        print("-" * 30)
        
        overview = project.analyze()
        print("✅ Analysis completed successfully")
        print(f"   📄 .rpy files: {overview.total_rpy_files}")
        print(f"   📝 Total lines: {overview.total_lines}")
        print(f"   💬 Dialogue lines: {overview.total_dialogue_lines}")
        print(f"   🏷️  Labels: {overview.total_labels}")
        print(f"   📋 Menus: {overview.total_menus}")
        print(f"   👥 Characters: {overview.total_characters}")
        
        if overview.errors:
            print(f"   ⚠️  Errors: {len(overview.errors)}")
        
        # Test 3: Character definitions
        print("\n👥 Test 3: Character Definitions")
        print("-" * 30)
        
        overview_data = project.get_project_overview()
        char_data = overview_data['characters']
        print(f"✅ Character definitions retrieved")
        print(f"   👤 Characters found: {len(char_data)}")
        
        if char_data:
            print("   📝 Character definitions:")
            for code, name in list(char_data.items())[:5]:
                print(f"     • {code} = \"{name}\"")
            if len(char_data) > 5:
                print(f"     • ... and {len(char_data) - 5} more")
        
        # Test 4: Dialogue search
        print("\n🔍 Test 4: Dialogue Search")
        print("-" * 30)
        
        search_results = project.search_dialogue("the", case_sensitive=False)
        print(f"✅ Dialogue search completed")
        print(f"   🔍 Results for 'the': {len(search_results)} matches")
        
        if search_results:
            print("   📝 Sample matches:")
            for result in search_results[:3]:
                speaker = result['speaker'] or 'narrator'
                dialogue = result['dialogue'][:50] + "..." if len(result['dialogue']) > 50 else result['dialogue']
                print(f"     • {speaker}: \"{dialogue}\" ({result['file']}:{result['line_number']})")
        
        print("\n" + "=" * 60)
        print("🎉 ALL STANDALONE TESTS PASSED!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("🚀 Starting standalone Ren'Py API test...\n")
    
    success = run_standalone_test()
    
    if success:
        # Export sample data
        try:
            test_vn_path = get_test_vn_path()
            project = RenpyProject(test_vn_path)
            overview_data = project.get_project_overview()
            
            output_file = "renpy_analysis_standalone.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(overview_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n📤 Sample data exported to: {output_file}")
        except Exception as e:
            print(f"❌ Export failed: {e}")
    
    print("\n🔚 Standalone test finished.") 