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
        Get detailed statistics about characters in the project.
        
        Returns:
            Dictionary mapping character codes to their detailed statistics
        """
        if not self.is_analyzed:
            self.analyze()
        
        if not self.overview:
            raise RenpyAnalysisError("No analysis data available")
        
        # Initialize stats with character definitions
        stats = {}
        for char_code, char_name in self.overview.character_definitions.items():
            stats[char_code] = {
                "name": char_name,
                "code": char_code,
                "dialogue_lines": 0,
                "word_count": 0,
                "first_appearance": None,
                "last_appearance": None,
                "labels_appeared_in": set(),
                "files_appeared_in": set(),
                "average_words_per_line": 0.0
            }
        
        # Analyze dialogue to calculate statistics
        try:
            rpy_files = self.parser.find_rpy_files(self.project_path)
            current_label = None
            
            for rpy_file in rpy_files:
                file_path = os.path.join(self.project_path, rpy_file)
                parsed_lines = self.parser.parse_file(file_path)
                
                for line in parsed_lines:
                    # Track current label for context
                    if line.line_type == 'label' and line.label_name:
                        current_label = line.label_name
                    
                    # Process dialogue lines
                    if line.line_type == 'dialogue' and line.speaker and line.dialogue_text:
                        speaker = line.speaker
                        
                        # Initialize stats for speakers not in character definitions
                        if speaker not in stats:
                            stats[speaker] = {
                                "name": speaker,  # Use speaker code as name if not defined
                                "code": speaker,
                                "dialogue_lines": 0,
                                "word_count": 0,
                                "first_appearance": None,
                                "last_appearance": None,
                                "labels_appeared_in": set(),
                                "files_appeared_in": set(),
                                "average_words_per_line": 0.0,
                                "is_undefined": True  # Mark as not formally defined
                            }
                        
                        # Count dialogue and words
                        stats[speaker]["dialogue_lines"] += 1
                        word_count = len(line.dialogue_text.split())
                        stats[speaker]["word_count"] += word_count
                        
                        # Track appearances
                        if stats[speaker]["first_appearance"] is None:
                            stats[speaker]["first_appearance"] = {
                                "file": rpy_file,
                                "line": line.line_number,
                                "label": current_label
                            }
                        
                        stats[speaker]["last_appearance"] = {
                            "file": rpy_file,
                            "line": line.line_number,
                            "label": current_label
                        }
                        
                        # Track contexts
                        stats[speaker]["files_appeared_in"].add(rpy_file)
                        if current_label:
                            stats[speaker]["labels_appeared_in"].add(current_label)
                    
                    # Also count narrator dialogue
                    elif line.line_type == 'narrator' and line.dialogue_text:
                        speaker = 'narrator'
                        
                        if speaker not in stats:
                            stats[speaker] = {
                                "name": "Narrator",
                                "code": "narrator",
                                "dialogue_lines": 0,
                                "word_count": 0,
                                "first_appearance": None,
                                "last_appearance": None,
                                "labels_appeared_in": set(),
                                "files_appeared_in": set(),
                                "average_words_per_line": 0.0,
                                "is_narrator": True
                            }
                        
                        stats[speaker]["dialogue_lines"] += 1
                        word_count = len(line.dialogue_text.split())
                        stats[speaker]["word_count"] += word_count
                        
                        if stats[speaker]["first_appearance"] is None:
                            stats[speaker]["first_appearance"] = {
                                "file": rpy_file,
                                "line": line.line_number,
                                "label": current_label
                            }
                        
                        stats[speaker]["last_appearance"] = {
                            "file": rpy_file,
                            "line": line.line_number,
                            "label": current_label
                        }
                        
                        stats[speaker]["files_appeared_in"].add(rpy_file)
                        if current_label:
                            stats[speaker]["labels_appeared_in"].add(current_label)
            
            # Calculate averages and convert sets to lists
            for char_code, char_stats in stats.items():
                if char_stats["dialogue_lines"] > 0:
                    char_stats["average_words_per_line"] = round(
                        char_stats["word_count"] / char_stats["dialogue_lines"], 2
                    )
                
                # Convert sets to sorted lists for JSON serialization
                char_stats["labels_appeared_in"] = sorted(list(char_stats["labels_appeared_in"]))
                char_stats["files_appeared_in"] = sorted(list(char_stats["files_appeared_in"]))
        
        except Exception as e:
            raise RenpyAnalysisError(f"Failed to calculate character stats: {str(e)}")
        
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
    
    def get_top_characters_by_dialogue(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most talkative characters ranked by dialogue lines.
        
        Args:
            limit: Maximum number of characters to return
            
        Returns:
            List of character stats sorted by dialogue count (descending)
        """
        char_stats = self.get_character_stats()
        
        # Convert to list and sort by dialogue lines
        characters = []
        for code, stats in char_stats.items():
            if stats["dialogue_lines"] > 0:  # Only include characters with dialogue
                characters.append({
                    "code": code,
                    "name": stats["name"],
                    "dialogue_lines": stats["dialogue_lines"],
                    "word_count": stats["word_count"],
                    "average_words_per_line": stats["average_words_per_line"],
                    "labels_count": len(stats["labels_appeared_in"]),
                    "files_count": len(stats["files_appeared_in"])
                })
        
        # Sort by dialogue lines (descending)
        characters.sort(key=lambda x: x["dialogue_lines"], reverse=True)
        
        return characters[:limit]
    
    def get_character_by_name(self, name: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """
        Search for characters by name (fuzzy matching).
        
        Args:
            name: Name to search for
            case_sensitive: Whether to perform case-sensitive search
            
        Returns:
            List of matching characters with their stats
        """
        char_stats = self.get_character_stats()
        matches = []
        
        search_name = name if case_sensitive else name.lower()
        
        for code, stats in char_stats.items():
            char_name = stats["name"] if case_sensitive else stats["name"].lower()
            
            if search_name in char_name or search_name in code.lower():
                matches.append({
                    "code": code,
                    "name": stats["name"],
                    "dialogue_lines": stats["dialogue_lines"],
                    "word_count": stats["word_count"],
                    "average_words_per_line": stats["average_words_per_line"],
                    "first_appearance": stats["first_appearance"],
                    "labels_appeared_in": stats["labels_appeared_in"][:10]  # Limit for display
                })
        
        # Sort by relevance (exact matches first, then by dialogue count)
        matches.sort(key=lambda x: (
            0 if search_name == x["name"].lower() else 1,  # Exact matches first
            -x["dialogue_lines"]  # Then by dialogue count descending
        ))
        
        return matches
    
    def get_dialogue_for_character(self, character_code: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get dialogue lines for a specific character.
        
        Args:
            character_code: Code of the character to get dialogue for
            limit: Maximum number of dialogue lines to return
            
        Returns:
            List of dialogue entries for the character
        """
        if not self.is_analyzed:
            self.analyze()
        
        dialogue_lines = []
        
        try:
            rpy_files = self.parser.find_rpy_files(self.project_path)
            current_label = None
            
            for rpy_file in rpy_files:
                file_path = os.path.join(self.project_path, rpy_file)
                parsed_lines = self.parser.parse_file(file_path)
                
                for line in parsed_lines:
                    # Track current label for context
                    if line.line_type == 'label' and line.label_name:
                        current_label = line.label_name
                    
                    # Find dialogue for this character
                    if (line.line_type == 'dialogue' and line.speaker == character_code and line.dialogue_text) or \
                       (line.line_type == 'narrator' and character_code == 'narrator' and line.dialogue_text):
                        
                        dialogue_lines.append({
                            "file": rpy_file,
                            "line_number": line.line_number,
                            "dialogue": line.dialogue_text,
                            "label": current_label,
                            "word_count": len(line.dialogue_text.split())
                        })
                        
                        # Stop if we've reached the limit
                        if len(dialogue_lines) >= limit:
                            break
                
                # Stop if we've reached the limit
                if len(dialogue_lines) >= limit:
                    break
        
        except Exception as e:
            raise RenpyAnalysisError(f"Failed to get dialogue for character {character_code}: {str(e)}")
        
        return dialogue_lines
    
    def get_character_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all character analysis.
        
        Returns:
            Dictionary with character analysis summary
        """
        char_stats = self.get_character_stats()
        top_characters = self.get_top_characters_by_dialogue(5)
        
        total_dialogue_lines = sum(stats["dialogue_lines"] for stats in char_stats.values())
        total_words = sum(stats["word_count"] for stats in char_stats.values())
        
        defined_characters = [code for code, stats in char_stats.items() 
                            if not stats.get("is_undefined") and not stats.get("is_narrator")]
        undefined_speakers = [code for code, stats in char_stats.items() 
                            if stats.get("is_undefined")]
        
        return {
            "total_characters": len(char_stats),
            "defined_characters": len(defined_characters),
            "undefined_speakers": len(undefined_speakers),
            "narrator_included": "narrator" in char_stats,
            "total_dialogue_lines": total_dialogue_lines,
            "total_words": total_words,
            "average_words_per_line": round(total_words / total_dialogue_lines, 2) if total_dialogue_lines > 0 else 0,
            "top_characters": top_characters,
            "character_codes": {
                "defined": defined_characters,
                "undefined": undefined_speakers
            }
        }
    
    def get_all_assets(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all assets used in the project, organized by category.
        
        Returns:
            Dictionary with assets organized by category (images, audio, video, etc.)
        """
        if not self.is_analyzed:
            self.analyze()
        
        assets_by_category = {
            'images': [],
            'audio': [],
            'video': [],
            'fonts': [],
            'data': [],
            'unknown': []
        }
        
        asset_usage = {}  # Track usage count per asset
        
        try:
            rpy_files = self.parser.find_rpy_files(self.project_path)
            current_label = None
            
            for rpy_file in rpy_files:
                file_path = os.path.join(self.project_path, rpy_file)
                parsed_lines = self.parser.parse_file(file_path)
                
                for line in parsed_lines:
                    # Track current label for context
                    if line.line_type == 'label' and line.label_name:
                        current_label = line.label_name
                    
                    # Extract assets from this line
                    line_assets = self.parser.extract_assets_from_line(line)
                    
                    for asset in line_assets:
                        asset['label'] = current_label or ''
                        category = asset['category']
                        
                        # Track usage count
                        asset_name = asset['name']
                        if asset_name not in asset_usage:
                            asset_usage[asset_name] = {
                                'count': 0,
                                'files': set(),
                                'labels': set(),
                                'usage_types': set(),
                                'category': category
                            }
                        
                        asset_usage[asset_name]['count'] += 1
                        asset_usage[asset_name]['files'].add(rpy_file)
                        if current_label:
                            asset_usage[asset_name]['labels'].add(current_label)
                        asset_usage[asset_name]['usage_types'].add(asset['usage_type'])
                        
                        # Add to category list
                        assets_by_category[category].append(asset)
        
        except Exception as e:
            raise RenpyAnalysisError(f"Failed to analyze assets: {str(e)}")
        
        # Convert sets to lists and add usage stats
        for asset_name, usage in asset_usage.items():
            usage['files'] = sorted(list(usage['files']))
            usage['labels'] = sorted(list(usage['labels']))
            usage['usage_types'] = sorted(list(usage['usage_types']))
        
        # Store usage data for other methods
        self._asset_usage = asset_usage
        
        return assets_by_category
    
    def get_asset_usage_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about asset usage in the project.
        
        Returns:
            Dictionary with asset usage statistics
        """
        assets_by_category = self.get_all_assets()
        
        # Calculate statistics
        stats = {
            'total_assets': 0,
            'by_category': {},
            'most_used_assets': [],
            'usage_patterns': {
                'scene_backgrounds': 0,
                'character_sprites': 0,
                'background_music': 0,
                'sound_effects': 0,
                'image_definitions': 0
            }
        }
        
        # Count by category
        for category, assets in assets_by_category.items():
            unique_assets = set(asset['name'] for asset in assets)
            stats['by_category'][category] = {
                'unique_count': len(unique_assets),
                'total_usages': len(assets)
            }
            stats['total_assets'] += len(unique_assets)
        
        # Get most used assets
        if hasattr(self, '_asset_usage'):
            asset_usage = self._asset_usage
            most_used = sorted(asset_usage.items(), key=lambda x: x[1]['count'], reverse=True)
            
            for asset_name, usage in most_used[:20]:
                stats['most_used_assets'].append({
                    'name': asset_name,
                    'category': usage['category'],
                    'usage_count': usage['count'],
                    'files_count': len(usage['files']),
                    'labels_count': len(usage['labels']),
                    'usage_types': usage['usage_types']
                })
            
            # Analyze usage patterns
            for asset_name, usage in asset_usage.items():
                for usage_type in usage['usage_types']:
                    if usage_type == 'scene':
                        stats['usage_patterns']['scene_backgrounds'] += usage['count']
                    elif usage_type == 'show':
                        stats['usage_patterns']['character_sprites'] += usage['count']
                    elif usage_type in ['play_music', 'queue_music']:
                        stats['usage_patterns']['background_music'] += usage['count']
                    elif usage_type in ['play_sound', 'play_audio']:
                        stats['usage_patterns']['sound_effects'] += usage['count']
                    elif usage_type == 'image_def':
                        stats['usage_patterns']['image_definitions'] += usage['count']
        
        return stats
    
    def search_assets(self, query: str, category: str = None, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """
        Search for assets by name or path.
        
        Args:
            query: Text to search for in asset names
            category: Optional category filter ('images', 'audio', 'video', etc.)
            case_sensitive: Whether to perform case-sensitive search
            
        Returns:
            List of matching assets with usage information
        """
        assets_by_category = self.get_all_assets()
        matches = []
        
        search_term = query if case_sensitive else query.lower()
        
        # Search through specified category or all categories
        categories_to_search = [category] if category else assets_by_category.keys()
        
        for cat in categories_to_search:
            if cat not in assets_by_category:
                continue
                
            for asset in assets_by_category[cat]:
                asset_name = asset['name'] if case_sensitive else asset['name'].lower()
                
                if search_term in asset_name:
                    # Add usage statistics if available
                    if hasattr(self, '_asset_usage') and asset['name'] in self._asset_usage:
                        usage = self._asset_usage[asset['name']]
                        asset_copy = asset.copy()
                        asset_copy.update({
                            'total_usage_count': usage['count'],
                            'files_used_in': usage['files'],
                            'labels_used_in': usage['labels'][:10],  # Limit for display
                            'usage_types': usage['usage_types']
                        })
                        matches.append(asset_copy)
                    else:
                        matches.append(asset)
        
        # Remove duplicates and sort by relevance
        seen = set()
        unique_matches = []
        for match in matches:
            key = (match['name'], match['category'])
            if key not in seen:
                seen.add(key)
                unique_matches.append(match)
        
        # Sort by relevance (exact matches first, then by usage count)
        unique_matches.sort(key=lambda x: (
            0 if search_term == x['name'].lower() else 1,
            -x.get('total_usage_count', 0)
        ))
        
        return unique_matches
    
    def get_assets_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get all assets of a specific category.
        
        Args:
            category: Category to filter by ('images', 'audio', 'video', etc.)
            
        Returns:
            List of assets in the specified category
        """
        assets_by_category = self.get_all_assets()
        return assets_by_category.get(category, [])
    
    def get_most_used_assets(self, limit: int = 20, category: str = None) -> List[Dict[str, Any]]:
        """
        Get the most frequently used assets.
        
        Args:
            limit: Maximum number of assets to return
            category: Optional category filter
            
        Returns:
            List of most used assets with usage statistics
        """
        assets_by_category = self.get_all_assets()
        
        if not hasattr(self, '_asset_usage'):
            return []
        
        asset_usage = self._asset_usage
        
        # Filter by category if specified
        if category:
            filtered_usage = {name: usage for name, usage in asset_usage.items() 
                            if usage['category'] == category}
        else:
            filtered_usage = asset_usage
        
        # Sort by usage count
        most_used = sorted(filtered_usage.items(), key=lambda x: x[1]['count'], reverse=True)
        
        result = []
        for asset_name, usage in most_used[:limit]:
            result.append({
                'name': asset_name,
                'category': usage['category'],
                'usage_count': usage['count'],
                'files_count': len(usage['files']),
                'labels_count': len(usage['labels']),
                'usage_types': usage['usage_types'],
                'files': usage['files'],
                'labels': usage['labels'][:10]  # Limit for display
            })
        
        return result
    
    def get_asset_timeline(self, asset_name: str) -> List[Dict[str, Any]]:
        """
        Get the timeline of usage for a specific asset.
        
        Args:
            asset_name: Name of the asset to track
            
        Returns:
            List of usage instances in chronological order
        """
        if not self.is_analyzed:
            self.analyze()
        
        timeline = []
        
        try:
            rpy_files = self.parser.find_rpy_files(self.project_path)
            current_label = None
            
            for rpy_file in rpy_files:
                file_path = os.path.join(self.project_path, rpy_file)
                parsed_lines = self.parser.parse_file(file_path)
                
                for line in parsed_lines:
                    # Track current label for context
                    if line.line_type == 'label' and line.label_name:
                        current_label = line.label_name
                    
                    # Check if this line uses the asset
                    if line.asset_name == asset_name:
                        timeline.append({
                            'file': rpy_file,
                            'line_number': line.line_number,
                            'label': current_label or '',
                            'usage_type': line.line_type,
                            'context': line.content,
                            'category': self.parser.get_asset_category(asset_name or '')
                        })
        
        except Exception as e:
            raise RenpyAnalysisError(f"Failed to get asset timeline for {asset_name}: {str(e)}")
        
        return timeline
    
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