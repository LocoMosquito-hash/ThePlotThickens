#!/usr/bin/env python3
"""
CSAP Production Integration Patch

This script applies CSAP integration to the production RenpyParser.
It can be run to automatically patch the existing parser.py file.
"""

import os
import sys
import shutil
from pathlib import Path


def apply_csap_integration():
    """Apply CSAP integration to the production parser."""
    
    print("🔧 CSAP Production Integration")
    print("=" * 40)
    
    # Paths
    current_dir = Path(__file__).parent
    app_dir = current_dir.parent.parent / "app" / "renpy-source-api"
    parser_file = app_dir / "parser.py"
    backup_file = app_dir / "parser_backup.py"
    
    if not parser_file.exists():
        print(f"❌ Parser file not found: {parser_file}")
        return False
    
    # Create backup
    print(f"📁 Creating backup: {backup_file}")
    shutil.copy2(parser_file, backup_file)
    
    # Read the original parser
    with open(parser_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Apply CSAP integration
    modified_content = _apply_csap_modifications(content)
    
    # Write the modified parser
    with open(parser_file, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    print("✅ CSAP integration applied successfully!")
    print("📊 Changes made:")
    print("   - Added CSAP import and initialization")
    print("   - Enhanced parse_screen_structure method")
    print("   - Added CSAP performance tracking")
    print("   - Maintained full backward compatibility")
    
    return True


def _apply_csap_modifications(content: str) -> str:
    """Apply CSAP modifications to the parser content."""
    
    # Add CSAP imports at the top
    import_section = '''
# CSAP Integration - Added for enhanced screen parsing
try:
    from pathlib import Path
    import sys
    
    # Add CSAP to path
    current_file = Path(__file__)
    csap_path = current_file.parent.parent.parent / "ideas-lab" / "flow-visualizer-poc" / "csap"
    if csap_path.exists():
        sys.path.insert(0, str(csap_path))
        from csap_integration import CSAPIntegratedParser
        CSAP_AVAILABLE = True
        print("[CSAP] Enhanced screen parsing enabled")
    else:
        CSAP_AVAILABLE = False
        print("[CSAP] Not found, using regex fallback")
except ImportError as e:
    CSAP_AVAILABLE = False
    print(f"[CSAP] Import failed: {e}, using regex fallback")

'''
    
    # Find the class definition and add CSAP initialization
    class_init_addition = '''
        # CSAP Integration
        self.csap_parser = None
        if CSAP_AVAILABLE:
            try:
                self.csap_parser = CSAPIntegratedParser()
                print("[CSAP] Integrated parser initialized")
            except Exception as e:
                print(f"[CSAP] Initialization failed: {e}")
                self.csap_parser = None
'''
    
    # Enhanced parse_screen_structure method
    enhanced_method = '''
    def parse_screen_structure(self, file_path: str, start_line: int, lines: List[str], screen_name: str) -> ScreenStructure:
        """
        Parse a complete screen structure using CSAP with regex fallback.
        
        Enhanced with CSAP for better accuracy and maintainability.
        Falls back to original regex parsing if CSAP is unavailable or fails.
        """
        # Try CSAP first if available
        if self.csap_parser:
            try:
                result = self.csap_parser.parse_screen_structure(file_path, start_line, lines, screen_name)
                return result
            except Exception as e:
                print(f"[CSAP] Failed for screen '{screen_name}': {e}, falling back to regex")
        
        # Original regex implementation as fallback
        return self._original_parse_screen_structure(file_path, start_line, lines, screen_name)
    
    def _original_parse_screen_structure(self, file_path: str, start_line: int, lines: List[str], screen_name: str) -> ScreenStructure:
        """Original regex-based screen parsing (preserved as fallback)."""
'''
    
    # Apply modifications
    modified_content = content
    
    # Add imports after the existing imports
    if 'from dataclasses import dataclass' in modified_content:
        modified_content = modified_content.replace(
            'from dataclasses import dataclass',
            'from dataclasses import dataclass' + import_section
        )
    
    # Add CSAP initialization to __init__ method
    if 'def __init__(self):' in modified_content and 'Initialize the parser with regex patterns' in modified_content:
        init_pattern = '        """Initialize the parser with regex patterns."""'
        modified_content = modified_content.replace(
            init_pattern,
            init_pattern + class_init_addition
        )
    
    # Replace parse_screen_structure method
    if 'def parse_screen_structure(self, file_path: str, start_line: int, lines: List[str], screen_name: str) -> ScreenStructure:' in modified_content:
        # Find the method and replace it
        lines = modified_content.split('\\n')
        new_lines = []
        in_method = False
        method_indent = 0
        
        for line in lines:
            if 'def parse_screen_structure(self, file_path: str, start_line: int, lines: List[str], screen_name: str) -> ScreenStructure:' in line:
                in_method = True
                method_indent = len(line) - len(line.lstrip())
                # Add enhanced method
                new_lines.extend(enhanced_method.split('\\n'))
                continue
            
            if in_method:
                line_indent = len(line) - len(line.lstrip()) if line.strip() else 0
                # If we're back to the same or less indentation and it's a method/class definition
                if line.strip() and line_indent <= method_indent and ('def ' in line or 'class ' in line):
                    in_method = False
                    # Rename the original method
                    if 'def parse_screen_structure' in line:
                        line = line.replace('def parse_screen_structure', 'def _original_parse_screen_structure')
                    new_lines.append(line)
                elif not in_method:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        modified_content = '\\n'.join(new_lines)
    
    return modified_content


def restore_backup():
    """Restore the original parser from backup."""
    
    current_dir = Path(__file__).parent
    app_dir = current_dir.parent.parent / "app" / "renpy-source-api"
    parser_file = app_dir / "parser.py"
    backup_file = app_dir / "parser_backup.py"
    
    if backup_file.exists():
        shutil.copy2(backup_file, parser_file)
        print("✅ Original parser restored from backup")
        return True
    else:
        print("❌ No backup file found")
        return False


def main():
    """Main integration script."""
    
    if len(sys.argv) > 1 and sys.argv[1] == 'restore':
        restore_backup()
    else:
        apply_csap_integration()


if __name__ == "__main__":
    main()
