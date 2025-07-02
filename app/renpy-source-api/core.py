"""
Core Ren'Py project analysis functionality.

This module provides the main RenpyProject class that coordinates
parsing, analysis, and querying of Ren'Py visual novel projects.
"""

import os
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

try:
    # Try relative imports (when used as package)
    from .parser import RenpyParser, ProjectOverview
    from .database_basic import RenpyDatabase
    from .exceptions import RenpyProjectError, RenpyAnalysisError
except ImportError:
    # Fall back to direct imports (when run standalone)
    from parser import RenpyParser, ProjectOverview
    from database_basic import RenpyDatabase
    from exceptions import RenpyProjectError, RenpyAnalysisError


class RenpyProject:
    """
    Main interface for analyzing and querying Ren'Py visual novel projects.
    
    This class provides a high-level API for:
    - Project structure analysis
    - Dialogue searching
    - Character statistics
    - Asset tracking
    - Label flow analysis
    """
    
    def __init__(self, project_path: str, db_connection: Optional[sqlite3.Connection] = None):
        """
        Initialize a Ren'Py project analyzer.
        
        Args:
            project_path: Path to the Ren'Py game folder (containing .rpy files)
            db_connection: Optional database connection for caching
        """
        self.project_path = str(Path(project_path).resolve())
        
        # Initialize components
        self.parser = RenpyParser()
        self.db = RenpyDatabase(db_connection) if db_connection else None
        
        # Analysis state
        self.is_analyzed = False
        self.overview: Optional[ProjectOverview] = None
        self.project_id: Optional[int] = None
        
        # Validate project path
        if not os.path.exists(self.project_path):
            raise RenpyProjectError(f"Project path does not exist: {self.project_path}")
        
        # Check if this looks like a Ren'Py project
        if not self._is_renpy_project():
            raise RenpyProjectError(f"Directory does not appear to be a Ren'Py project: {self.project_path}")
    
    def _is_renpy_project(self) -> bool:
        """Check if the directory appears to be a Ren'Py project."""
        # Look for .rpy files or typical Ren'Py structure
        project_dir = Path(self.project_path)
        
        # Check for .rpy files
        rpy_files = list(project_dir.glob("*.rpy"))
        if rpy_files:
            return True
        
        # Check for subdirectories with .rpy files
        for subdir in project_dir.iterdir():
            if subdir.is_dir():
                sub_rpy_files = list(subdir.glob("*.rpy"))
                if sub_rpy_files:
                    return True
        
        return False
    
    def analyze(self, force_reanalysis: bool = False) -> ProjectOverview:
        """
        Analyze the Ren'Py project and cache results.
        
        Args:
            force_reanalysis: If True, re-analyze even if cached data exists
            
        Returns:
            ProjectOverview with analysis results
        """
        # Check if we already have analysis data and don't need to re-analyze
        if self.is_analyzed and self.overview and not force_reanalysis:
            return self.overview
        
        try:
            print(f"[RenpyProject] Analyzing project: {self.project_path}")
            
            # Parse the project
            self.overview = self.parser.analyze_project(self.project_path)
            self.is_analyzed = True
            
            # Cache to database if available
            if self.db and self.project_id:
                self._cache_analysis_results()
            
            print(f"[RenpyProject] Analysis complete:")
            print(f"  - {self.overview.total_rpy_files} .rpy files")
            print(f"  - {self.overview.total_lines} total lines")
            print(f"  - {self.overview.total_dialogue_lines} dialogue lines")
            print(f"  - {self.overview.total_labels} labels")
            print(f"  - {self.overview.total_characters} characters")
            
            if self.overview.errors:
                print(f"  - {len(self.overview.errors)} errors occurred")
                for error in self.overview.errors[:3]:  # Show first 3 errors
                    print(f"    • {error}")
                if len(self.overview.errors) > 3:
                    print(f"    • ... and {len(self.overview.errors) - 3} more")
            
            return self.overview
            
        except Exception as e:
            raise RenpyAnalysisError(f"Failed to analyze project: {str(e)}")
    
    def get_project_overview(self) -> Dict[str, Any]:
        """
        Get a summary of the project structure.
        
        Returns:
            Dictionary with project overview information
        """
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
    
    def get_character_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics about characters in the project.
        
        Returns:
            Dictionary mapping character codes to their statistics
        """
        if not self.is_analyzed:
            self.analyze()
        
        if not self.overview:
            raise RenpyAnalysisError("No analysis data available")
        
        # For now, return basic character definitions
        # TODO: Implement dialogue counting per character
        stats = {}
        
        for char_code, char_name in self.overview.character_definitions.items():
            stats[char_code] = {
                "name": char_name,
                "code": char_code,
                "dialogue_lines": 0,  # TODO: Calculate from parsed dialogue
                "word_count": 0,      # TODO: Calculate from parsed dialogue
                "first_appearance": None,  # TODO: Track from parsing
                "labels_appeared_in": []   # TODO: Track from parsing
            }
        
        return stats
    
    def search_dialogue(self, query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """
        Search for dialogue lines containing the specified text.
        
        Args:
            query: Text to search for
            case_sensitive: Whether to perform case-sensitive search
            
        Returns:
            List of matching dialogue entries with context
        """
        if not self.is_analyzed:
            self.analyze()
        
        # For basic implementation, we need to parse files and search
        # TODO: Implement efficient search through parsed dialogue lines
        
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
    
    def get_labels(self) -> List[str]:
        """Get list of all labels in the project."""
        if not self.is_analyzed:
            self.analyze()
        
        return self.overview.label_list if self.overview else []
    
    def get_files(self) -> List[str]:
        """Get list of all .rpy files in the project."""
        if not self.is_analyzed:
            self.analyze()
        
        return self.overview.file_list if self.overview else []
    
    def link_to_story(self, story_id: int) -> None:
        """
        Link this Ren'Py project to a story in the database.
        
        Args:
            story_id: ID of the story in the main stories table
        """
        if not self.db:
            raise RenpyAnalysisError("No database connection available")
        
        try:
            self.project_id = self.db.create_or_update_project(story_id, self.project_path)
            print(f"[RenpyProject] Linked to story {story_id} with project ID {self.project_id}")
        except Exception as e:
            raise RenpyAnalysisError(f"Failed to link to story: {str(e)}")
    
    def _cache_analysis_results(self) -> None:
        """Cache analysis results to the database."""
        if not self.db or not self.project_id or not self.overview:
            return
        
        try:
            # For now, just mark as analyzed
            # TODO: Implement full caching of parsed data
            stats = {
                'total_rpy_files': self.overview.total_rpy_files,
                'total_lines': self.overview.total_lines,
                'total_dialogue_lines': self.overview.total_dialogue_lines,
                'total_labels': self.overview.total_labels,
                'total_menus': self.overview.total_menus,
            }
            
            # Update project record
            cursor = self.db.conn.cursor()
            cursor.execute('''
            UPDATE renpy_projects 
            SET is_analyzed = 1,
                total_rpy_files = ?,
                total_lines = ?,
                total_dialogue_lines = ?,
                total_labels = ?,
                total_menus = ?
            WHERE id = ?
            ''', (
                stats['total_rpy_files'],
                stats['total_lines'],
                stats['total_dialogue_lines'],
                stats['total_labels'],
                stats['total_menus'],
                self.project_id
            ))
            
            self.db.conn.commit()
            
        except Exception as e:
            print(f"[RenpyProject] Warning: Failed to cache results: {e}")
    
    def __str__(self) -> str:
        """String representation of the project."""
        if self.is_analyzed and self.overview:
            return (f"RenpyProject(path='{self.project_path}', "
                   f"files={self.overview.total_rpy_files}, "
                   f"dialogue_lines={self.overview.total_dialogue_lines})")
        else:
            return f"RenpyProject(path='{self.project_path}', not_analyzed)"
    
    def __repr__(self) -> str:
        """Representation of the project."""
        return self.__str__() 