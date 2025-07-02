#!/usr/bin/env python3
"""
Standalone test for Ren'Py API - no imports needed!
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

# Configuration 
TEST_VN_PATH = r"T:\AG\Savior-0.16c-pc\game"

@dataclass
class RenpyLine:
    file_path: str
    line_number: int
    line_type: str
    content: str
    speaker: Optional[str] = None
    dialogue_text: Optional[str] = None
    label_name: Optional[str] = None

@dataclass
class ProjectOverview:
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

class SimpleRenpyParser:
    def __init__(self):
        self.patterns = {
            'label': re.compile(r'^\s*label\s+([a-zA-Z_][a-zA-Z0-9_]*):', re.IGNORECASE),
            'character_def': re.compile(r'^\s*define\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*Character\s*\(\s*"([^"]*)"', re.IGNORECASE),
            'dialogue': re.compile(r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s+"([^"]+)"', re.IGNORECASE),
            'narrator': re.compile(r'^\s*"([^"]+)"'),
            'menu': re.compile(r'^\s*menu:', re.IGNORECASE),
        }
        
        self.excluded_files = {
            'screens.rpy', 'gui.rpy', 'options.rpy'
        }
    
    def find_rpy_files(self, project_path: str) -> List[str]:
        project_dir = Path(project_path)
        rpy_files = []
        for rpy_file in project_dir.glob("**/*.rpy"):
            relative_path = rpy_file.relative_to(project_dir)
            if relative_path.name not in self.excluded_files:
                rpy_files.append(str(relative_path))
        return sorted(rpy_files)
    
    def parse_file(self, file_path: str) -> List[RenpyLine]:
        parsed_lines = []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    parsed_line = self._parse_line(file_path, line_num, line)
                    if parsed_line:
                        parsed_lines.append(parsed_line)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
        return parsed_lines
    
    def _parse_line(self, file_path: str, line_num: int, line: str) -> Optional[RenpyLine]:
        stripped = line.strip()
        if not stripped:
            return None
        
        for pattern_name, pattern in self.patterns.items():
            match = pattern.match(line)
            if match:
                base_line = RenpyLine(
                    file_path=file_path,
                    line_number=line_num,
                    line_type=pattern_name,
                    content=stripped
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
                
                return base_line
        
        return None
    
    def analyze_project(self, project_path: str) -> ProjectOverview:
        errors = []
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

def test_standalone():
    print("=" * 60)
    print("STANDALONE REN'PY API TEST")
    print("=" * 60)
    
    # Check path exists
    if not os.path.exists(TEST_VN_PATH):
        print(f"❌ Path doesn't exist: {TEST_VN_PATH}")
        print("Edit TEST_VN_PATH in this script to point to your VN folder")
        return False
    
    print(f"📁 Testing VN: {TEST_VN_PATH}")
    
    try:
        parser = SimpleRenpyParser()
        overview = parser.analyze_project(TEST_VN_PATH)
        
        print("\n✅ Analysis Results:")
        print(f"   📄 .rpy files: {overview.total_rpy_files}")
        print(f"   📝 Total lines: {overview.total_lines}")
        print(f"   💬 Dialogue lines: {overview.total_dialogue_lines}")
        print(f"   🏷️  Labels: {overview.total_labels}")
        print(f"   📋 Menus: {overview.total_menus}")
        print(f"   👥 Characters: {overview.total_characters}")
        
        if overview.character_definitions:
            print(f"\n👥 Character Definitions:")
            for code, name in list(overview.character_definitions.items())[:5]:
                print(f"   • {code} = \"{name}\"")
        
        if overview.label_list:
            print(f"\n🏷️  Sample Labels:")
            for label in overview.label_list[:10]:
                print(f"   • {label}")
        
        if overview.errors:
            print(f"\n⚠️  Errors: {len(overview.errors)}")
            for error in overview.errors[:3]:
                print(f"   • {error}")
        
        print("\n🎉 STANDALONE TEST PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_standalone() 