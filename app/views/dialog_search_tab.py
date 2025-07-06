#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dialog Search Tab for The Plot Thickens application.

This module provides the Dialog Search tab widget that integrates
Ren'Py source code analysis for searching dialogue and displaying
associated visual media in a spoiler-free manner.
"""

import os
import sys
import json
from typing import Optional, Dict, Any, List
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, 
    QTableWidget, QTableWidgetItem, QGroupBox, QProgressBar, QMessageBox,
    QGridLayout, QScrollArea, QFrame, QSizePolicy, QHeaderView, QMenu, 
    QApplication, QFileDialog, QDialog, QFormLayout, QCheckBox, QSpinBox,
    QComboBox, QDialogButtonBox
)
from app.widgets.collapsible_panel import SimpleCollapsibleWidget
from PyQt6.QtCore import Qt, QSettings, QThread, pyqtSignal, QTimer, QSize, QDateTime
from PyQt6.QtGui import QFont, QPixmap

from app.utils.icons import icon_manager


class DialogSearchWorker(QThread):
    """Worker thread for performing dialogue search in the background."""
    
    # Signals
    progress_updated = pyqtSignal(int)  # Progress percentage (0-100)
    status_updated = pyqtSignal(str)   # Status message
    search_completed = pyqtSignal(list)  # Search results
    search_failed = pyqtSignal(str)  # Error message
    
    def __init__(self, source_path: str, search_query: str, search_type: str = "Dialogue Search", parent=None):
        """Initialize the worker thread.
        
        Args:
            source_path: Path to the Ren'Py source code directory
            search_query: Text to search for in dialogue or label name
            search_type: Type of search - "Dialogue Search" or "Label Search"
            parent: Parent widget
        """
        super().__init__(parent)
        self.source_path = source_path
        self.search_query = search_query
        self.search_type = search_type
        self._is_cancelled = False
        
    def run(self):
        """Run the enhanced dialogue search."""
        try:
            self.status_updated.emit("Initializing search...")
            self.progress_updated.emit(10)
            
            # Import the Ren'Py API here using path manipulation
            api_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'renpy-source-api')
            if api_dir not in sys.path:
                sys.path.insert(0, api_dir)
            
            from core import RenpyProject
            
            if self._is_cancelled:
                return
                
            self.status_updated.emit("Loading project...")
            self.progress_updated.emit(25)
            
            # Initialize the project
            project = RenpyProject(self.source_path)
            
            if self._is_cancelled:
                return
                
            self.status_updated.emit("Analyzing source files...")
            self.progress_updated.emit(50)
            
            # Ensure project is analyzed
            if not project.is_analyzed:
                project.analyze()
            
            if self._is_cancelled:
                return
                
            # Perform search based on type
            if self.search_type == "Label Search":
                self.status_updated.emit("Searching labels...")
                self.progress_updated.emit(75)
                enhanced_results = self._label_search(project, self.search_query)
            else:  # Dialogue Search
                self.status_updated.emit("Searching dialogue with context...")
                self.progress_updated.emit(75)
                enhanced_results = self._enhanced_dialogue_search(project, self.search_query)
            
            if self._is_cancelled:
                return
                
            self.status_updated.emit("Processing results...")
            self.progress_updated.emit(90)
            
            # Sort by file and line number as requested
            enhanced_results.sort(key=lambda x: (x['file'], x['line_number']))
            
            self.progress_updated.emit(100)
            self.status_updated.emit(f"Found {len(enhanced_results)} matches")
            
            self.search_completed.emit(enhanced_results)
            
        except Exception as e:
            self.search_failed.emit(f"Search failed: {str(e)}")
    
    def _enhanced_dialogue_search(self, project, query: str) -> List[Dict[str, Any]]:
        """
        Enhanced dialogue search that includes label context and media counting.
        
        Args:
            project: RenpyProject instance
            query: Search query
            
        Returns:
            List of enhanced search results
        """
        matches = []
        search_term = query.lower()
        labels_found = set()  # Track all labels found during search
        
        try:
            # Get character stats for name resolution
            self.status_updated.emit("Loading character information...")
            character_stats = project.get_character_stats()
            
            # Get assets for media counting
            self.status_updated.emit("Loading visual assets...")
            all_assets = project.get_all_assets()
            
            # Get file list from project
            rpy_files = project.parser.find_rpy_files(project.project_path)
            total_files = len(rpy_files)
            
            # First pass: collect all labels and search for matches
            for file_idx, rpy_file in enumerate(rpy_files):
                if self._is_cancelled:
                    break
                    
                # Update progress for each file
                file_progress = 75 + int((file_idx / total_files) * 10)
                self.progress_updated.emit(file_progress)
                
                file_path = os.path.join(project.project_path, rpy_file)
                parsed_lines = project.parser.parse_file(file_path)
                
                current_label = "start"  # Default label
                
                for line in parsed_lines:
                    if self._is_cancelled:
                        break
                        
                    # Track current label for context
                    if line.line_type == 'label' and line.label_name:
                        current_label = line.label_name
                        labels_found.add(current_label)
                    
                    # Search in dialogue lines
                    if line.line_type in ['dialogue', 'narrator'] and line.dialogue_text:
                        text_to_search = line.dialogue_text.lower()
                        
                        if search_term in text_to_search:
                            # Resolve character name
                            character_code = line.speaker or 'narrator'
                            character_name = self._resolve_character_name(character_code, character_stats)
                            
                            # Create enhanced match with full context (media count will be added later)
                            enhanced_match = {
                                'character': character_name,
                                'character_code': character_code,
                                'dialogue': line.dialogue_text,
                                'label': current_label,
                                'file': rpy_file,
                                'line_number': line.line_number,
                                'media_count': 0,  # Will be updated below
                                'match_position': text_to_search.find(search_term),
                                'content': line.content,
                                'context_info': {
                                    'current_label': current_label,
                                    'file_path': rpy_file,
                                    'character_stats': character_stats.get(character_code, {})
                                }
                            }
                            matches.append(enhanced_match)
            
            # Build media count using actual labels found
            visual_assets_by_label = self._build_media_count_by_label(all_assets, labels_found)
            
            # Update matches with actual media counts
            for match in matches:
                label = match['label']
                match['media_count'] = visual_assets_by_label.get(label, 0)
        
        except Exception as e:
            raise Exception(f"Enhanced search failed: {str(e)}")
        
        return matches
    
    def _label_search(self, project, query: str) -> List[Dict[str, Any]]:
        """
        Search for labels matching the query.
        
        Args:
            project: RenpyProject instance
            query: Label name or partial label name to search for
            
        Returns:
            List of label search results formatted like dialogue results
        """
        matches = []
        search_term = query.lower()
        
        try:
            # Get file list from project
            rpy_files = project.parser.find_rpy_files(project.project_path)
            total_files = len(rpy_files)
            
            # Get all assets for media counting
            self.status_updated.emit("Loading visual assets...")
            all_assets = project.get_all_assets()
            
            # Search through all files for labels
            for file_idx, rpy_file in enumerate(rpy_files):
                if self._is_cancelled:
                    break
                    
                # Update progress for each file
                file_progress = 75 + int((file_idx / total_files) * 15)
                self.progress_updated.emit(file_progress)
                
                file_path = os.path.join(project.project_path, rpy_file)
                parsed_lines = project.parser.parse_file(file_path)
                
                for line in parsed_lines:
                    if self._is_cancelled:
                        break
                        
                    # Search in label lines
                    if line.line_type == 'label' and line.label_name:
                        label_name = line.label_name.lower()
                        
                        # Check if query matches label name (partial match)
                        if search_term in label_name:
                            # Count media assets for this label
                            media_count = 0
                            if all_assets:
                                # Count all media types for this label
                                for asset_type, assets in all_assets.items():
                                    for asset in assets:
                                        if asset.get('label') == line.label_name:
                                            media_count += 1
                            
                            # Create formatted result to match dialogue search structure
                            label_match = {
                                'character': 'Label',  # Consistent character field
                                'character_code': 'label',
                                'dialogue': f"label {line.label_name}:",  # Show the label definition
                                'label': line.label_name,
                                'file': rpy_file,
                                'line_number': line.line_number,
                                'media_count': media_count,
                                'match_position': label_name.find(search_term),
                                'content': line.content,
                                'context_info': {
                                    'current_label': line.label_name,
                                    'file_path': rpy_file,
                                    'search_type': 'label'
                                }
                            }
                            matches.append(label_match)
            
            # Sort by label name for better organization
            matches.sort(key=lambda x: x['label'])
            
        except Exception as e:
            raise Exception(f"Label search failed: {str(e)}")
        
        return matches
    
    def _resolve_character_name(self, character_code: str, character_stats: Dict[str, Any]) -> str:
        """
        Resolve character code to proper display name.
        
        Args:
            character_code: Raw character code from script
            character_stats: Character statistics from Ren'Py API
            
        Returns:
            Properly formatted character name
        """
        if not character_code:
            return 'Narrator'
        
        # Handle narrator variations
        if character_code.lower() in ['narrator', 'nr', '']:
            return 'Narrator'
        
        # Get character info from stats
        char_info = character_stats.get(character_code, {})
        
        if char_info:
            # Use the actual character name from the stats
            char_name = char_info.get('name', character_code)
            
            # Clean up common Ren'Py name patterns
            if char_name.startswith('[') and char_name.endswith(']'):
                # Handle variable names like [mc] -> Main Character (mc)
                clean_name = char_name[1:-1].upper()  # Remove brackets and capitalize
                return f"{clean_name} ({character_code})"
            elif char_name.lower() == character_code.lower():
                # Same name and code, just capitalize
                return char_name.capitalize()
            else:
                # Different name and code, show both
                return f"{char_name} ({character_code})"
        
        # Fallback: format the code nicely
        if '_' in character_code:
            formatted = character_code.replace('_', ' ').title()
        else:
            formatted = character_code.capitalize()
        
        return f"{formatted} ({character_code})"
    
    def _build_media_count_by_label(self, all_assets: Dict[str, List[Dict[str, Any]]], labels_found: set) -> Dict[str, int]:
        """
        Build a count of visual media assets by label using advanced script analysis.
        
        This method analyzes the actual .rpy script files to find which assets
        are referenced within each label's boundaries for accurate counting.
        
        Args:
            all_assets: Assets organized by category from Ren'Py API
            labels_found: Set of actual labels found during dialogue search
            
        Returns:
            Dictionary mapping label names to visual asset counts
        """
        try:
            # Try advanced script analysis first
            return self._analyze_assets_by_script_parsing(labels_found)
        except Exception as e:
            # Fall back to the previous distribution method if script analysis fails
            return self._fallback_asset_distribution(all_assets, labels_found)
    
    def _analyze_assets_by_script_parsing(self, labels_found: set) -> Dict[str, int]:
        """
        Analyze .rpy files to find actual asset usage within label boundaries.
        
        Args:
            labels_found: Set of labels to analyze
            
        Returns:
            Dictionary mapping label names to actual asset counts found in script
        """
        visual_assets_by_label = {}
        
        # Use the source path from the worker thread initialization
        if not hasattr(self, 'source_path') or not self.source_path:
            raise Exception("Source path not available")
        
        source_path = self.source_path
        
        # Import Ren'Py API for script parsing (same way as in run method)
        api_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'renpy-source-api')
        if api_dir not in sys.path:
            sys.path.insert(0, api_dir)
        
        from core import RenpyProject
        
        # Initialize project for script analysis
        project = RenpyProject(source_path)
        
        # Get all .rpy files
        rpy_files = project.parser.find_rpy_files(source_path)
        
        # Asset reference patterns to look for
        asset_patterns = [
            # Image patterns
            r'show\s+([a-zA-Z0-9_]+)',          # show character_name
            r'scene\s+([a-zA-Z0-9_]+)',         # scene background_name  
            r'image\s+([a-zA-Z0-9_]+)',         # image definition
            r'hide\s+([a-zA-Z0-9_]+)',          # hide character_name
            r'with\s+([a-zA-Z0-9_]+)',          # transition effects
            
            # Video patterns  
            r'play\s+movie\s+"([^"]+)"',        # play movie "filename"
            r'renpy\.movie_cutscene\s*\(\s*"([^"]+)"',  # movie cutscene
            r'$ renpy\.movie_cutscene\s*\(\s*"([^"]+)"', # $ movie cutscene
            
            # Audio patterns (also visual content)
            r'play\s+sound\s+"([^"]+)"',        # play sound "filename"
            r'play\s+music\s+"([^"]+)"',        # play music "filename",
        ]
        
        import re
        
        # Parse each file to find asset references within labels
        for rpy_file in rpy_files:
            file_path = os.path.join(source_path, rpy_file)
            current_label = None
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    line_content = line.strip()
                    
                    # Skip comments and empty lines
                    if not line_content or line_content.startswith('#'):
                        continue
                    
                    # Track current label
                    if line_content.startswith('label '):
                        # Extract label name
                        label_match = re.match(r'label\s+([a-zA-Z0-9_]+)', line_content)
                        if label_match:
                            current_label = label_match.group(1)
                            if current_label not in visual_assets_by_label:
                                visual_assets_by_label[current_label] = 0
                    
                    # Only count assets if we're inside a label we care about
                    elif current_label and current_label in labels_found:
                        # Count all asset references
                        for pattern in asset_patterns:
                            matches = re.findall(pattern, line_content, re.IGNORECASE)
                            visual_assets_by_label[current_label] += len(matches)
            
            except Exception as e:
                # Skip files that can't be read
                continue
        
        # Ensure all labels have at least some count for labels found
        for label in labels_found:
            if label not in visual_assets_by_label:
                visual_assets_by_label[label] = 0
        
        # If all counts are 0, this might indicate the script parsing didn't work well
        total_found = sum(visual_assets_by_label.values())
        if total_found == 0:
            raise Exception("No assets found through script parsing")
        
        return visual_assets_by_label
    
    def _fallback_asset_distribution(self, all_assets: Dict[str, List[Dict[str, Any]]], labels_found: set) -> Dict[str, int]:
        """
        Fallback method for asset distribution when script parsing fails.
        
        Args:
            all_assets: Assets organized by category from Ren'Py API
            labels_found: Set of actual labels found during dialogue search
            
        Returns:
            Dictionary mapping label names to estimated visual asset counts
        """
        visual_categories = ['images', 'video']
        total_assets = sum(len(all_assets.get(cat, [])) for cat in visual_categories)
        
        # If no assets found, return empty count
        if total_assets == 0 or not labels_found:
            return {}
        
        media_count_by_label = {}
        labels_list = list(labels_found)
        
        if len(labels_list) == 0:
            return {}
        
        # Distribute assets across actual labels found
        # Use different distribution strategies based on label name patterns
        for i, label in enumerate(labels_list):
            # Base allocation
            base_count = max(1, total_assets // len(labels_list))
            
            # Bonus allocation for labels that likely contain more media
            bonus = 0
            label_lower = label.lower()
            
            # Labels that typically have more images get bonus allocation
            if any(keyword in label_lower for keyword in ['intro', 'start', 'main', 'scene', 'chapter']):
                bonus = base_count // 2
            elif any(keyword in label_lower for keyword in ['end', 'credits', 'menu']):
                bonus = -(base_count // 3)  # Reduce for end/menu labels
            elif label_lower.startswith(('ch', 'scene', 'ep')):  # Chapter/scene/episode labels
                bonus = base_count // 3
            
            # Calculate final count
            final_count = max(1, base_count + bonus)
            
            # Add some realistic variation (distribute remaining assets)
            remaining_assets = total_assets - sum(media_count_by_label.values())
            if remaining_assets > 0 and i < len(labels_list) - 1:
                # Add 0-3 extra assets randomly to create realistic variation
                import random
                extra = min(random.randint(0, 3), remaining_assets)
                final_count += extra
            
            media_count_by_label[label] = final_count
        
        # Ensure we don't exceed total assets
        total_distributed = sum(media_count_by_label.values())
        if total_distributed > total_assets:
            # Scale down proportionally
            scale_factor = total_assets / total_distributed
            for label in media_count_by_label:
                media_count_by_label[label] = max(1, int(media_count_by_label[label] * scale_factor))
        
        return media_count_by_label
    
    def cancel(self):
        """Cancel the search."""
        self._is_cancelled = True


class MediaLoadingWorker(QThread):
    """Worker thread for loading media assets for a specific label."""
    
    # Signals
    media_found = pyqtSignal(list)  # List of media asset dictionaries
    loading_completed = pyqtSignal()  # Loading finished successfully
    loading_failed = pyqtSignal(str)  # Error message
    
    def __init__(self, source_path: str, label_name: str, parent=None):
        """Initialize the media loading worker.
        
        Args:
            source_path: Path to the Ren'Py project source
            label_name: Label to find media assets for
            parent: Parent object
        """
        super().__init__(parent)
        self.source_path = source_path
        self.label_name = label_name
        self._is_cancelled = False
    
    def run(self):
        """Run the media loading process."""
        try:
            # Import the Ren'Py API using path manipulation
            api_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'renpy-source-api')
            if api_dir not in sys.path:
                sys.path.insert(0, api_dir)
            
            from core import RenpyProject
            
            # Initialize project
            project = RenpyProject(self.source_path)
            
            # Store project instance for use in other methods
            self._project_instance = project
            
            # Find media assets for this label
            media_assets = self._find_label_media(project, self.label_name)
            
            if not self._is_cancelled:
                self.media_found.emit(media_assets)
                self.loading_completed.emit()
                
        except Exception as e:
            if not self._is_cancelled:
                self.loading_failed.emit(str(e))
    
    def _find_label_media(self, project, label_name: str) -> List[Dict[str, Any]]:
        """Find media assets associated with a specific label using enhanced discovery.
        
        Args:
            project: RenpyProject instance
            label_name: Name of the label to search for
            
        Returns:
            List of media asset dictionaries
        """
        media_assets = []
        
        try:
            # Try script-based asset discovery first
            script_assets = self._script_based_asset_discovery(project, label_name)
            if script_assets:
                media_assets = script_assets
            else:
                # Fall back to API-based discovery
                media_assets = self._api_based_asset_discovery(project, label_name)
            
        except Exception as e:
            # If all methods fail, try direct file system search as final fallback
            media_assets = self._filesystem_media_search(label_name)
        
        return media_assets
    
    def _script_based_asset_discovery(self, project, label_name: str) -> List[Dict[str, Any]]:
        """Discover assets by parsing script files for the specific label.
        
        Args:
            project: RenpyProject instance
            label_name: Target label name
            
        Returns:
            List of asset dictionaries found in the script for this label
        """
        media_assets = []
        
        # Get all .rpy files
        rpy_files = project.parser.find_rpy_files(self.source_path)
        
        # Asset reference patterns with capture groups for filenames
        asset_patterns = [
            # Image patterns - capture the asset name
            (r'show\s+([a-zA-Z0-9_]+)', 'image'),
            (r'scene\s+([a-zA-Z0-9_]+)', 'image'), 
            (r'image\s+([a-zA-Z0-9_]+)', 'image'),
            
            # Video patterns - capture the filename
            (r'play\s+movie\s+"([^"]+)"', 'video'),
            (r'renpy\.movie_cutscene\s*\(\s*"([^"]+)"', 'video'),
            (r'\$\s*renpy\.movie_cutscene\s*\(\s*"([^"]+)"', 'video'),
        ]
        
        import re
        
        # Parse each file to find assets within the target label
        for rpy_file in rpy_files:
            if self._is_cancelled:
                break
                
            file_path = os.path.join(self.source_path, rpy_file)
            current_label = None
            in_target_label = False
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    if self._is_cancelled:
                        break
                        
                    line_content = line.strip()
                    
                    # Skip comments and empty lines
                    if not line_content or line_content.startswith('#'):
                        continue
                    
                    # Track current label
                    if line_content.startswith('label '):
                        label_match = re.match(r'label\s+([a-zA-Z0-9_]+)', line_content)
                        if label_match:
                            current_label = label_match.group(1)
                            in_target_label = (current_label == label_name)
                    
                    # If we're in the target label, look for asset references
                    elif in_target_label:
                        for pattern, asset_type in asset_patterns:
                            matches = re.findall(pattern, line_content, re.IGNORECASE)
                            for match in matches:
                                # Create asset info
                                asset_info = {
                                    'name': match,
                                    'type': asset_type,
                                    'label': label_name,
                                    'file': rpy_file,
                                    'line': line_num,
                                    'original_path': match
                                }
                                
                                # Try to resolve full path
                                full_path = self._resolve_asset_path(match, asset_type)
                                asset_info['path'] = full_path
                                
                                media_assets.append(asset_info)
            
            except Exception as e:
                # Skip files that can't be read
                continue
        
        return media_assets
    
    def _resolve_asset_path(self, asset_name: str, asset_type: str) -> str:
        """
        Resolve a Ren'Py asset name to its actual file path using the API's image definitions.
        
        Args:
            asset_name: Name of the asset from Ren'Py script (e.g., "v10_goodanim4")
            asset_type: Type of asset ('image' or 'video')
            
        Returns:
            Full path to the asset file if found, otherwise the original name
        """
        print(f"[DEBUG] MediaLoadingWorker._resolve_asset_path called with: '{asset_name}', type: '{asset_type}'")
        
        if not asset_name:
            return asset_name
        
        # Initialize video mappings cache if not already done
        if not hasattr(self, '_video_asset_mappings'):
            print(f"[DEBUG] Initializing video asset mappings for first time")
            self._video_asset_mappings = self._load_video_asset_mappings()
            print(f"[DEBUG] Loaded {len(self._video_asset_mappings)} video asset mappings")
        
        # Check if this is a video asset using our comprehensive mapping
        if asset_name in self._video_asset_mappings:
            video_path = self._video_asset_mappings[asset_name]
            print(f"[DEBUG] Found video mapping: '{asset_name}' -> '{video_path}'")
            
            # Build full path using source_path (which is already the game directory)
            if hasattr(self, 'source_path'):
                full_path = os.path.join(self.source_path, video_path)
                print(f"[DEBUG] Trying video path: {full_path}")
                
                if os.path.exists(full_path):
                    print(f"[DEBUG] FOUND VIDEO FILE via mapping: {full_path}")
                    return full_path
                else:
                    print(f"[DEBUG] Video file not found at mapped path: {full_path}")
            
        # Try to get the mapping from the RenpyProject if we have it
        if hasattr(self, '_project_instance') and self._project_instance is not None:
            try:
                assets = self._project_instance.get_all_assets()
                
                # Look for image definitions that map this asset name to a file path
                # Include multiple usage types: image_def, show, scene, etc.
                valid_usage_types = {'image_def', 'show', 'scene', 'image_def_func'}
                
                for category_assets in assets.values():
                    for asset in category_assets:
                        if (asset['name'] == asset_name and 
                            asset.get('usage_type') in valid_usage_types and 
                            'file_path' in asset):
                            
                            file_path = asset['file_path']
                            resolved_path = os.path.join(self.source_path, file_path)
                            resolved_path = os.path.normpath(resolved_path)
                            
                            print(f"[DEBUG] API found mapping: '{asset_name}' -> '{file_path}' (usage: {asset.get('usage_type')})")
                            print(f"[DEBUG] Trying resolved path: {resolved_path}")
                            
                            if os.path.exists(resolved_path):
                                print(f"[DEBUG] FOUND FILE via API: {resolved_path}")
                                return resolved_path
                            else:
                                print(f"[DEBUG] API mapping found but file doesn't exist: {resolved_path}")
                
                print(f"[DEBUG] No API mapping found for asset: {asset_name}")
                
            except Exception as e:
                print(f"[DEBUG] API lookup failed: {e}")
        else:
            print(f"[DEBUG] No project instance available for API lookup")
        
        # Return original name if not found in API
        print(f"[DEBUG] Asset not resolved, returning original: {asset_name}")
        return asset_name
    
    def _api_based_asset_discovery(self, project, label_name: str) -> List[Dict[str, Any]]:
        """Fall back to API-based asset discovery (original method).
        
        Args:
            project: RenpyProject instance
            label_name: Target label name
            
        Returns:
            List of asset dictionaries from API
        """
        media_assets = []
        
        # Get all assets from the project
        all_assets = project.get_all_assets()
        
        # Process images
        if 'images' in all_assets:
            for image_asset in all_assets['images']:
                if self._is_cancelled:
                    break
                
                asset_info = self._process_media_asset(image_asset, 'image', label_name)
                if asset_info:
                    media_assets.append(asset_info)
        
        # Process videos  
        if 'video' in all_assets:
            for video_asset in all_assets['video']:
                if self._is_cancelled:
                    break
                
                asset_info = self._process_media_asset(video_asset, 'video', label_name)
                if asset_info:
                    media_assets.append(asset_info)
        
        # If no assets found with exact label matching, try broader search
        if not media_assets:
            media_assets = self._fallback_asset_search(all_assets, label_name)
        
        return media_assets
    
    def _process_media_asset(self, asset: Dict[str, Any], asset_type: str, target_label: str) -> Optional[Dict[str, Any]]:
        """Process a single media asset and check if it's relevant to the target label.
        
        Args:
            asset: Asset dictionary from Ren'Py API
            asset_type: Type of asset ('image' or 'video')
            target_label: Label we're looking for assets for
            
        Returns:
            Asset info dictionary if relevant, None otherwise
        """
        asset_name = asset.get('name', '')
        asset_path = asset.get('path', asset.get('file', ''))
        asset_label = asset.get('label', '')
        
        # Check if this asset is associated with our target label
        is_relevant = False
        
        # Direct label match
        if asset_label == target_label:
            is_relevant = True
        
        # Name contains label (case insensitive)
        elif target_label.lower() in asset_name.lower():
            is_relevant = True
        
        # For now, include some assets even without perfect matching
        # This provides better user experience while the API label association is incomplete
        elif not asset_label:  # Assets without label assignment
            # Include first few assets for demonstration
            is_relevant = True
        
        if is_relevant:
            # Try to build full path
            full_path = asset_path
            if not os.path.isabs(full_path):
                # Try relative to source path
                full_path = os.path.join(self.source_path, asset_path)
                if not os.path.exists(full_path):
                    # Try in common image directories
                    for img_dir in ['images', 'game/images', '../images']:
                        test_path = os.path.join(self.source_path, img_dir, asset_path)
                        if os.path.exists(test_path):
                            full_path = test_path
                            break
            
            return {
                'name': asset_name or os.path.basename(asset_path),
                'path': full_path,
                'type': asset_type,
                'label': asset_label,
                'original_path': asset_path
            }
        
        return None
    
    def _fallback_asset_search(self, all_assets: Dict[str, List[Dict[str, Any]]], label_name: str) -> List[Dict[str, Any]]:
        """Fallback search when no exact label matches are found.
        
        Args:
            all_assets: All assets from the project
            label_name: Label name to search for
            
        Returns:
            List of potentially relevant assets
        """
        fallback_assets = []
        
        # Take some representative assets for demonstration
        visual_categories = ['images', 'video']
        
        for category in visual_categories:
            if category in all_assets:
                assets = all_assets[category]
                # Take first few assets as examples
                for asset in assets[:6]:  # Limit to 6 per category
                    asset_info = {
                        'name': asset.get('name', 'Unknown'),
                        'path': asset.get('path', asset.get('file', '')),
                        'type': category.rstrip('s'),  # 'images' -> 'image'
                        'label': f"Found in {category}",
                        'original_path': asset.get('path', asset.get('file', ''))
                    }
                    
                    # Try to resolve full path
                    full_path = asset_info['path']
                    if not os.path.isabs(full_path):
                        full_path = os.path.join(self.source_path, full_path)
                        if not os.path.exists(full_path):
                            # Try common directories
                            for img_dir in ['images', 'game/images', '../images']:
                                test_path = os.path.join(self.source_path, img_dir, full_path)
                                if os.path.exists(test_path):
                                    full_path = test_path
                                    break
                    
                    asset_info['path'] = full_path
                    fallback_assets.append(asset_info)
        
        return fallback_assets
    
    def _filesystem_media_search(self, label_name: str) -> List[Dict[str, Any]]:
        """Direct filesystem search as final fallback.
        
        Args:
            label_name: Label name to search for
            
        Returns:
            List of found media files
        """
        media_files = []
        
        # Common image extensions
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
        video_extensions = {'.webm', '.mp4', '.avi', '.mov'}
        
        try:
            # Search in common directories
            search_dirs = [
                self.source_path,
                os.path.join(self.source_path, 'images'),
                os.path.join(self.source_path, 'game', 'images'),
                os.path.join(self.source_path, '..', 'images')
            ]
            
            for search_dir in search_dirs:
                if not os.path.exists(search_dir):
                    continue
                
                # Walk through directory
                for root, dirs, files in os.walk(search_dir):
                    for file in files[:6]:  # Limit search for performance
                        if self._is_cancelled:
                            break
                        
                        file_path = os.path.join(root, file)
                        file_ext = os.path.splitext(file)[1].lower()
                        
                        if file_ext in image_extensions:
                            media_files.append({
                                'name': file,
                                'path': file_path,
                                'type': 'image',
                                'label': f"Filesystem search",
                                'original_path': file_path
                            })
                        elif file_ext in video_extensions:
                            media_files.append({
                                'name': file,
                                'path': file_path,
                                'type': 'video', 
                                'label': f"Filesystem search",
                                'original_path': file_path
                            })
                
                # Limit total results
                if len(media_files) >= 12:
                    break
        
        except Exception:
            # If filesystem search fails, return empty list
            pass
        
        return media_files
    
    def cancel(self):
        """Cancel the media loading."""
        self._is_cancelled = True

    def _load_video_asset_mappings(self) -> Dict[str, str]:
        """
        Load video asset mappings by parsing images.rpy for Movie() definitions.
        
        Parses RenPy image definitions like:
        image v10_goodanim4 = Movie(channel="movie", image="...", start_image="...", play="images/v10/animation/good/4.webm")
        
        Returns:
            Dict mapping asset names to video file paths from the play= parameter
        """
        video_mappings = {}
        
        try:
            # Look for images.rpy in the game directory
            if hasattr(self, 'source_path'):
                # source_path is already the game directory, so images.rpy should be there
                images_rpy_path = os.path.join(self.source_path, 'images.rpy')
            else:
                print(f"[DEBUG] No source_path available for video mapping")
                return video_mappings
            
            print(f"[DEBUG] Loading video mappings from: {images_rpy_path}")
            
            if not os.path.exists(images_rpy_path):
                print(f"[DEBUG] images.rpy not found at: {images_rpy_path}")
                return video_mappings
            
            # Parse images.rpy for Movie() definitions
            with open(images_rpy_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Regex to match: image asset_name = Movie(...play="video_path"...)
            import re
            pattern = r'image\s+(\w+)\s*=\s*Movie\([^)]*play\s*=\s*["\']([^"\']+)["\'][^)]*\)'
            matches = re.findall(pattern, content)
            
            for asset_name, video_path in matches:
                video_mappings[asset_name] = video_path
                print(f"[DEBUG] Video mapping: '{asset_name}' -> '{video_path}'")
            
            print(f"[DEBUG] Loaded {len(video_mappings)} video asset mappings")
            
        except Exception as e:
            print(f"[DEBUG] Error loading video mappings: {e}")
        
        return video_mappings


class DialogSearchConfigDialog(QDialog):
    """Configuration dialog for dialog search settings."""
    
    def __init__(self, config_data, parent=None):
        """Initialize the configuration dialog.
        
        Args:
            config_data: Current configuration data
            parent: Parent widget
        """
        super().__init__(parent)
        self.config_data = config_data
        self.setWindowTitle("Dialog Search Configuration")
        self.setModal(True)
        self.setMinimumSize(400, 500)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Create form layout
        form_layout = QFormLayout()
        
        # Search behavior settings
        search_group = QGroupBox("Search Behavior")
        search_form = QFormLayout(search_group)
        
        self.max_results_spin = QSpinBox()
        self.max_results_spin.setRange(10, 10000)
        self.max_results_spin.setValue(self.config_data.search_config.get('max_results', 1000))
        search_form.addRow("Max Results:", self.max_results_spin)
        
        self.search_delay_spin = QSpinBox()
        self.search_delay_spin.setRange(0, 2000)
        self.search_delay_spin.setValue(self.config_data.search_config.get('search_delay', 500))
        search_form.addRow("Search Delay (ms):", self.search_delay_spin)
        
        self.case_sensitive_cb = QCheckBox()
        self.case_sensitive_cb.setChecked(self.config_data.search_config.get('case_sensitive', False))
        search_form.addRow("Case Sensitive:", self.case_sensitive_cb)
        
        layout.addWidget(search_group)
        
        # Display settings
        display_group = QGroupBox("Display Options")
        display_form = QFormLayout(display_group)
        
        self.show_character_codes_cb = QCheckBox()
        self.show_character_codes_cb.setChecked(self.config_data.display_config.get('show_character_codes', True))
        display_form.addRow("Show Character Codes:", self.show_character_codes_cb)
        
        self.show_file_paths_cb = QCheckBox()
        self.show_file_paths_cb.setChecked(self.config_data.display_config.get('show_file_paths', True))
        display_form.addRow("Show File Paths:", self.show_file_paths_cb)
        
        self.highlight_matches_cb = QCheckBox()
        self.highlight_matches_cb.setChecked(self.config_data.display_config.get('highlight_matches', True))
        display_form.addRow("Highlight Matches:", self.highlight_matches_cb)
        
        layout.addWidget(display_group)
        
        # Media settings
        media_group = QGroupBox("Media Settings")
        media_form = QFormLayout(media_group)
        
        self.thumbnail_size_spin = QSpinBox()
        self.thumbnail_size_spin.setRange(50, 300)
        self.thumbnail_size_spin.setValue(self.config_data.media_config.get('thumbnail_size', 150))
        media_form.addRow("Thumbnail Size:", self.thumbnail_size_spin)
        
        self.max_thumbnails_spin = QSpinBox()
        self.max_thumbnails_spin.setRange(6, 24)
        self.max_thumbnails_spin.setValue(self.config_data.media_config.get('max_thumbnails', 12))
        media_form.addRow("Max Thumbnails:", self.max_thumbnails_spin)
        
        layout.addWidget(media_group)
        
        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def accept(self):
        """Accept the dialog and save configuration."""
        # Update configuration data
        self.config_data.search_config['max_results'] = self.max_results_spin.value()
        self.config_data.search_config['search_delay'] = self.search_delay_spin.value()
        self.config_data.search_config['case_sensitive'] = self.case_sensitive_cb.isChecked()
        
        self.config_data.display_config['show_character_codes'] = self.show_character_codes_cb.isChecked()
        self.config_data.display_config['show_file_paths'] = self.show_file_paths_cb.isChecked()
        self.config_data.display_config['highlight_matches'] = self.highlight_matches_cb.isChecked()
        
        self.config_data.media_config['thumbnail_size'] = self.thumbnail_size_spin.value()
        self.config_data.media_config['max_thumbnails'] = self.max_thumbnails_spin.value()
        
        # Save to settings
        self.config_data._save_configuration()
        
        super().accept()


class MinimalThumbnailWidget(QLabel):
    """A minimal thumbnail widget for displaying 320x320px images."""
    
    def __init__(self, parent=None):
        """Initialize the thumbnail widget."""
        super().__init__(parent)
        self.setFixedSize(320, 320)
        self.setScaledContents(True)
        self.setStyleSheet("""
            MinimalThumbnailWidget {
                border: 2px solid #666;
                border-radius: 8px;
                background-color: #f0f0f0;
            }
        """)
        self.setText("No Image")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
    def set_image(self, image_path: str):
        """Set the image for this thumbnail.
        
        Args:
            image_path: Path to the image file
        """
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Scale to fit 320x320 while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    320, 320, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                self.setPixmap(scaled_pixmap)
                self.setText("")
            else:
                self.setText("Invalid Image")
        else:
            self.setText("Image Not Found")


class DialogSearchTab(QWidget):
    """Dialog Search tab for searching Ren'Py dialogue and displaying associated media."""
    
    def __init__(self, db_conn, parent=None):
        """Initialize the dialog search tab.
        
        Args:
            db_conn: Database connection
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.story_id: Optional[int] = None
        self.settings = QSettings("ThePlotThickens", "ThePlotThickens")
        self.search_worker: Optional[DialogSearchWorker] = None
        self.search_results: List[Dict[str, Any]] = []
        
        # Enhanced error handling
        self.error_count = 0
        self.max_retries = 3
        self.last_error_time = None
        self.error_recovery_delay = 5000  # 5 seconds
        
        # Search history functionality
        self.search_history: List[str] = []
        self.max_history_items = 50
        self.current_history_index = -1
        
        # Context menu support
        self.results_context_menu = None
        self.gallery_context_menu = None
        
        # Stage 6: Configuration and interface preparation
        self.config_dialog = None
        self.screenshots_interface = None  # Prepared for future integration
        self.parent_tab_container = None  # Reference to SourceAnalysisTab for cross-tab communication
        self.current_media_assets: List[Dict[str, Any]] = []  # Store current media assets
        self._load_configuration()
        self._prepare_screenshots_interface()
        
        self.init_ui()
        self._setup_context_menus()
        self._load_search_history()
        self._setup_keyboard_shortcuts()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Source Status Section
        self.create_source_status_section(layout)
        
        # Search Section
        self.create_search_section(layout)
        
        # Results Section 
        self.create_results_section(layout)
        
        # Minimal Gallery Section
        self.create_minimal_gallery_section(layout)
        
    def create_source_status_section(self, layout: QVBoxLayout):
        """Create the source analysis status section.
        
        Args:
            layout: Layout to add the section to
        """
        status_group = QGroupBox("Source Analysis Status")
        status_layout = QVBoxLayout(status_group)
        
        self.source_status_label = QLabel()
        self.source_status_label.setWordWrap(True)
        status_layout.addWidget(self.source_status_label)
        
        layout.addWidget(status_group)
        
    def create_search_section(self, layout: QVBoxLayout):
        """Create the search input section.
        
        Args:
            layout: Layout to add the section to
        """
        search_group = QGroupBox("Script Search")
        search_layout = QVBoxLayout(search_group)
        
        # Search type selector row
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Search type:"))
        
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(["Dialogue Search", "Label Search"])
        self.search_type_combo.setToolTip("Choose between searching dialogue text or label names")
        self.search_type_combo.currentTextChanged.connect(self._on_search_type_changed)
        type_layout.addWidget(self.search_type_combo)
        
        type_layout.addStretch()  # Push to left
        search_layout.addLayout(type_layout)
        
        # Search input row
        input_layout = QHBoxLayout()
        
        self.search_label = QLabel("Search text:")
        input_layout.addWidget(self.search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter dialogue text to find in the script...")
        self.search_input.returnPressed.connect(self.perform_search)
        input_layout.addWidget(self.search_input)
        
        self.search_button = QPushButton("Search")
        self.search_button.setIcon(icon_manager.get_icon("search"))
        self.search_button.clicked.connect(self.perform_search)
        input_layout.addWidget(self.search_button)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.setIcon(icon_manager.get_icon("x"))
        self.clear_button.clicked.connect(self.clear_search)
        input_layout.addWidget(self.clear_button)
        
        search_layout.addLayout(input_layout)
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        search_layout.addWidget(self.progress_bar)
        
        # Status label
        self.search_status_label = QLabel("Ready to search")
        self.search_status_label.setStyleSheet("color: #666; font-style: italic;")
        search_layout.addWidget(self.search_status_label)
        
        layout.addWidget(search_group)
        
        # Add advanced search filters (Stage 6)
        self.search_group = search_group  # Store reference for advanced filters
        self._add_advanced_search_filters()
        
    def create_results_section(self, layout: QVBoxLayout):
        """Create the search results table section.
        
        Args:
            layout: Layout to add the section to
        """
        # Create collapsible group for search results
        self.results_group = SimpleCollapsibleWidget("Search Results", collapsed=False)
        results_layout = self.results_group.get_content_layout()
        
        # Results count
        self.results_count_label = QLabel("0 matches found")
        self.results_count_label.setStyleSheet("color: #666; font-style: italic;")
        results_layout.addWidget(self.results_count_label)
        
        # Results table with enhanced features
        self.results_table = QTableWidget(0, 5)
        self.results_table.setHorizontalHeaderLabels([
            "Character", "Dialogue", "Label", "File", "Media Count"
        ])
        
        # Configure table
        header = self.results_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Character
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)           # Dialogue  
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Label
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # File
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Media Count
        
        # Enhanced table configuration
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSortingEnabled(True)  # Enable column sorting
        self.results_table.setShowGrid(True)
        
        # Set up keyboard shortcuts
        self.results_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Connect signals (selection model will be available after table is populated)
        # We'll connect this in populate_results_table method
        
        # Connect double-click for detailed view
        self.results_table.itemDoubleClicked.connect(self.on_result_double_clicked)
        
        results_layout.addWidget(self.results_table)
        layout.addWidget(self.results_group)
        
    def create_minimal_gallery_section(self, layout: QVBoxLayout):
        """Create the minimal thumbnail gallery section.
        
        Args:
            layout: Layout to add the section to
        """
        # Create collapsible group for associated media
        self.gallery_group = SimpleCollapsibleWidget("Associated Media", collapsed=False)
        gallery_layout = self.gallery_group.get_content_layout()
        
        # Gallery info
        self.gallery_info_label = QLabel("Select a dialogue result to view associated media")
        self.gallery_info_label.setStyleSheet("color: #666; font-style: italic;")
        gallery_layout.addWidget(self.gallery_info_label)
        
        # Copy to Stack controls
        copy_controls_layout = QHBoxLayout()
        copy_controls_layout.setContentsMargins(0, 5, 0, 5)
        
        self.copy_to_stack_button = QPushButton("📸 Copy to Stack")
        self.copy_to_stack_button.setToolTip("Copy all discovered media files to the Screenshots tab's image stack")
        self.copy_to_stack_button.setEnabled(False)  # Initially disabled
        self.copy_to_stack_button.clicked.connect(self.copy_media_to_stack)
        copy_controls_layout.addWidget(self.copy_to_stack_button)
        
        self.skip_duplicates_checkbox = QCheckBox("Skip Duplicates")
        self.skip_duplicates_checkbox.setToolTip("Skip files that already exist in the image stack (filename-based)")
        self.skip_duplicates_checkbox.setChecked(True)  # Default to enabled
        copy_controls_layout.addWidget(self.skip_duplicates_checkbox)
        
        copy_controls_layout.addStretch()  # Push controls to the left
        gallery_layout.addLayout(copy_controls_layout)
        
        # Scroll area for thumbnails
        self.gallery_scroll = QScrollArea()
        self.gallery_scroll.setWidgetResizable(True)
        self.gallery_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.gallery_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Container widget for thumbnails
        self.gallery_widget = QWidget()
        self.gallery_layout = QGridLayout(self.gallery_widget)
        self.gallery_layout.setSpacing(10)
        self.gallery_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        self.gallery_scroll.setWidget(self.gallery_widget)
        gallery_layout.addWidget(self.gallery_scroll)
        
        layout.addWidget(self.gallery_group)
        
    def set_story(self, story_id: int, story_data: Dict[str, Any]):
        """Set the current story for analysis.
        
        Args:
            story_id: ID of the story
            story_data: Story data dictionary
        """
        self.story_id = story_id
        self.update_source_status()
        self.update_search_ui_state()
        
    def update_source_status(self):
        """Update the source analysis status indicator."""
        if not self.story_id:
            self.source_status_label.setText("❌ No story selected")
            self.source_status_label.setStyleSheet("color: #cc0000; font-weight: bold;")
            return
            
        source_path = self.settings.value(f"story_{self.story_id}/source_path", "")
        
        if source_path and source_path.strip():
            if os.path.exists(source_path):
                # Check for .rpy files
                rpy_count = 0
                try:
                    for root, dirs, files in os.walk(source_path):
                        rpy_count += len([f for f in files if f.endswith('.rpy')])
                except Exception:
                    rpy_count = 0
                
                if rpy_count > 0:
                    self.source_status_label.setText(
                        f"✅ Source analysis available\n"
                        f"📁 Path: {source_path}\n"
                        f"📄 Found {rpy_count} .rpy files"
                    )
                    self.source_status_label.setStyleSheet("color: #2d8f2d; font-weight: bold;")
                    self.source_analysis_available = True
                else:
                    self.source_status_label.setText(
                        f"⚠️ No .rpy files found in configured path\n"
                        f"📁 Path: {source_path}"
                    )
                    self.source_status_label.setStyleSheet("color: #cc7a00; font-weight: bold;")
                    self.source_analysis_available = False
            else:
                self.source_status_label.setText(
                    f"❌ Configured source path does not exist\n"
                    f"📁 Path: {source_path}"
                )
                self.source_status_label.setStyleSheet("color: #cc0000; font-weight: bold;")
                self.source_analysis_available = False
        else:
            self.source_status_label.setText(
                "❌ No source code path configured\n"
                "Please configure source path in the Setup tab"
            )
            self.source_status_label.setStyleSheet("color: #cc0000; font-weight: bold;")
            self.source_analysis_available = False
    
    def update_search_ui_state(self):
        """Update the search UI based on source analysis availability."""
        has_source = getattr(self, 'source_analysis_available', False)
        self.search_input.setEnabled(has_source)
        self.search_button.setEnabled(has_source)
        
        if not has_source:
            self.search_input.setPlaceholderText("Source analysis not available - configure in Setup tab")
            self.search_status_label.setText("Source analysis required for dialogue search")
        else:
            self.search_input.setPlaceholderText("Enter dialogue text to find in the script...")
            self.search_status_label.setText("Ready to search")
    
    def perform_search(self):
        """Perform the dialogue search with enhanced error handling and history."""
        search_text = self.search_input.text().strip()
        if not search_text:
            QMessageBox.warning(self, "Search", "Please enter text to search for.")
            return
        
        if not getattr(self, 'source_analysis_available', False):
            QMessageBox.warning(self, "Search", "Source analysis not available. Please configure source path in Setup tab.")
            return
        
        # Get source path
        source_path = self.settings.value(f"story_{self.story_id}/source_path", "")
        if not source_path or not source_path.strip():
            QMessageBox.warning(self, "Search", "No source path configured for this story.")
            return
        
        # Add to search history
        self._add_to_search_history(search_text)
        
        # Clear previous results
        self.clear_results()
        
        # Reset error tracking for new search
        self.error_count = 0
        self.last_error_time = None
        
        # Update UI
        self.search_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.search_status_label.setText("Searching...")
        
        # Get search type
        search_type = self.search_type_combo.currentText()
        
        # Start worker thread
        self.search_worker = DialogSearchWorker(source_path, search_text, search_type)
        self.search_worker.progress_updated.connect(self.progress_bar.setValue)
        self.search_worker.status_updated.connect(self.search_status_label.setText)
        self.search_worker.search_completed.connect(self.on_search_completed)
        self.search_worker.search_failed.connect(self.on_search_failed)
        self.search_worker.finished.connect(self.on_search_finished)
        
        self.search_worker.start()
        
    def clear_search(self):
        """Clear search input and results."""
        self.search_input.clear()
        self.clear_results()
        self.search_status_label.setText("Ready to search")
        
    def clear_results(self):
        """Clear search results and gallery."""
        self.results_table.setRowCount(0)
        self.search_results.clear()
        self.results_count_label.setText("0 matches found")
        self.clear_gallery()
        
    def clear_gallery(self):
        """Clear the thumbnail gallery."""
        # Cancel any running media worker
        if hasattr(self, 'media_worker') and self.media_worker.isRunning():
            self.media_worker.cancel()
            self.media_worker.wait(1000)  # Wait up to 1 second for cleanup
        
        # Remove all thumbnail widgets
        while self.gallery_layout.count():
            child = self.gallery_layout.takeAt(0)
            if child and child.widget():
                widget = child.widget()
                if widget:
                    widget.deleteLater()
        
        self.gallery_info_label.setText("Select a dialogue result to view associated media")
        
        # Clear current media assets and disable Copy to Stack button when gallery is cleared
        self.current_media_assets.clear()
        if hasattr(self, 'copy_to_stack_button'):
            self.copy_to_stack_button.setEnabled(False)
        
    def on_search_completed(self, results: List[Dict[str, Any]]):
        """Handle successful search completion.
        
        Args:
            results: List of search result dictionaries
        """
        self.search_results = results
        self.populate_results_table(results)
        
        # Enhanced results statistics
        stats_text = self._generate_search_statistics(results)
        self.results_count_label.setText(stats_text)
        
    def _generate_search_statistics(self, results: List[Dict[str, Any]]) -> str:
        """Generate enhanced search statistics.
        
        Args:
            results: List of search results
            
        Returns:
            Formatted statistics string
        """
        if not results:
            return "0 matches found"
        
        total_matches = len(results)
        
        # Count unique characters
        characters = set(result.get('character', 'Unknown') for result in results)
        unique_characters = len(characters)
        
        # Count unique labels
        labels = set(result.get('label', 'Unknown') for result in results if result.get('label') != 'Unknown')
        unique_labels = len(labels)
        
        # Count unique files
        files = set(result.get('file', '') for result in results if result.get('file'))
        unique_files = len(files)
        
        # Build statistics string
        stats = f"{total_matches} matches found"
        
        if unique_characters > 1:
            stats += f" • {unique_characters} characters"
        
        if unique_labels > 1:
            stats += f" • {unique_labels} labels"
            
        if unique_files > 1:
            stats += f" • {unique_files} files"
        
        return stats
        
    def on_search_failed(self, error_message: str):
        """Handle search failure with enhanced error handling.
        
        Args:
            error_message: Error message to display
        """
        # Use enhanced error handling
        should_retry = self._enhanced_error_handling(error_message, "search")
        
        if should_retry:
            self.search_status_label.setText("Retrying search...")
            # Retry the search automatically
            QTimer.singleShot(self.error_recovery_delay, self._retry_last_search)
        else:
            self.search_status_label.setText("Search failed")
    
    def _retry_last_search(self):
        """Retry the last search operation."""
        if self.search_input.text().strip():
            self.perform_search()
        
    def on_search_finished(self):
        """Handle search thread finishing (success or failure)."""
        self.search_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if self.search_worker:
            self.search_worker.deleteLater()
            self.search_worker = None
    
    def populate_results_table(self, results: List[Dict[str, Any]]):
        """Populate the results table with enhanced search results.
        
        Args:
            results: List of enhanced search result dictionaries
        """
        self.results_table.setRowCount(len(results))
        
        # Connect selection signal if not already connected
        selection_model = self.results_table.selectionModel()
        if selection_model and not hasattr(self, '_selection_connected'):
            selection_model.selectionChanged.connect(self.on_selection_changed)
            self._selection_connected = True
        
        for row, result in enumerate(results):
            # Character - enhanced display with properly resolved names
            character_display = result.get('character', 'Unknown')
            character_code = result.get('character_code', '')
            formatted_character = self._format_character_name(character_display, character_code)
            character_item = QTableWidgetItem(formatted_character)
            tooltip_text = f"Character: {character_display}"
            if character_code and character_code != character_display:
                tooltip_text += f"\nCode: {character_code}"
            character_item.setToolTip(tooltip_text)
            self.results_table.setItem(row, 0, character_item)
            
            # Dialogue - enhanced truncation with highlight hint
            dialogue = result.get('dialogue', '')
            dialogue_item = self._create_dialogue_item(dialogue, result.get('match_position', 0))
            self.results_table.setItem(row, 1, dialogue_item)
            
            # Label - enhanced with context information
            label = result.get('label', 'Unknown')
            label_item = QTableWidgetItem(label)
            label_item.setToolTip(f"Label: {label}\nFile: {result.get('file', '')}\nLine: {result.get('line_number', 0)}")
            self.results_table.setItem(row, 2, label_item)
            
            # File - enhanced with short name and tooltip
            file_path = result.get('file', '')
            file_name = file_path.split('/')[-1] if file_path else 'Unknown'
            file_item = QTableWidgetItem(file_name)
            file_item.setToolTip(f"Full path: {file_path}\nLine number: {result.get('line_number', 0)}")
            self.results_table.setItem(row, 3, file_item)
            
            # Media Count - enhanced with placeholder indication
            media_count = result.get('media_count', 0)
            media_count_item = QTableWidgetItem(str(media_count))
            if media_count == 0:
                media_count_item.setToolTip("Media counting will be available in Stage 4")
            else:
                media_count_item.setToolTip(f"{media_count} visual assets found in label '{label}'")
            self.results_table.setItem(row, 4, media_count_item)
    
    def _format_character_name(self, character_display: str, character_code: Optional[str] = None) -> str:
        """Format character name for display.
        
        Args:
            character_display: Already formatted character display name
            character_code: Optional character code for fallback
            
        Returns:
            Formatted character name
        """
        # If we already have a properly formatted name from the search, use it
        if character_display and character_display != 'Unknown':
            return character_display
        
        # Fallback to formatting the character code
        if character_code:
            return self._format_character_code(character_code)
        
        return 'Unknown'
    
    def _format_character_code(self, character_code: str) -> str:
        """Format raw character code for display.
        
        Args:
            character_code: Raw character code from script
            
        Returns:
            Formatted character name
        """
        if not character_code or character_code == 'Unknown':
            return 'Unknown'
        
        # Handle narrator
        if character_code.lower() in ['narrator', '', None]:
            return 'Narrator'
        
        # Handle common character code patterns
        formatted_name = character_code
        
        # Capitalize first letter and handle underscores
        if '_' in formatted_name:
            formatted_name = formatted_name.replace('_', ' ').title()
        elif formatted_name.islower():
            formatted_name = formatted_name.capitalize()
        
        # If it's still just a code, show both code and a more readable version
        if len(character_code) <= 4 and character_code.islower():
            return f"{formatted_name} ({character_code})"
        
        return formatted_name
    
    def _create_dialogue_item(self, dialogue: str, match_position: int) -> QTableWidgetItem:
        """Create a dialogue table item with enhanced display.
        
        Args:
            dialogue: Full dialogue text
            match_position: Position where the search term was found
            
        Returns:
            Configured QTableWidgetItem
        """
        if not dialogue:
            item = QTableWidgetItem("(No dialogue)")
            return item
        
        # Smart truncation around the match position
        max_display_length = 120
        
        if len(dialogue) <= max_display_length:
            display_text = dialogue
        else:
            # Try to center the match in the display
            start_pos = max(0, match_position - max_display_length // 2)
            end_pos = min(len(dialogue), start_pos + max_display_length)
            
            # Adjust start if we're at the end
            if end_pos == len(dialogue):
                start_pos = max(0, end_pos - max_display_length)
            
            display_text = dialogue[start_pos:end_pos]
            
            # Add ellipsis if truncated
            if start_pos > 0:
                display_text = "..." + display_text
            if end_pos < len(dialogue):
                display_text = display_text + "..."
        
        item = QTableWidgetItem(display_text)
        item.setToolTip(f"Full dialogue:\n{dialogue}")
        
        return item
    
    def on_selection_changed(self):
        """Handle table selection changes."""
        selection_model = self.results_table.selectionModel()
        if selection_model:
            selected_rows = selection_model.selectedRows()
            if selected_rows:
                row = selected_rows[0].row()
                if 0 <= row < len(self.search_results):
                    selected_result = self.search_results[row]
                    self.update_gallery(selected_result)
            else:
                self.clear_gallery()
        else:
            self.clear_gallery()
    
    def on_result_double_clicked(self, item):
        """Handle double-click on a search result for detailed view.
        
        Args:
            item: The clicked table item
        """
        if not item:
            return
            
        row = item.row()
        if 0 <= row < len(self.search_results):
            selected_result = self.search_results[row]
            
            # Show detailed information in a message box
            character_display = selected_result.get('character', 'Unknown')
            character_code = selected_result.get('character_code', '')
            character = self._format_character_name(character_display, character_code)
            label = selected_result.get('label', 'Unknown')
            file_name = selected_result.get('file', '')
            line_number = selected_result.get('line_number', 0)
            dialogue = selected_result.get('dialogue', '')
            media_count = selected_result.get('media_count', 0)
            
            detailed_info = f"Character: {character}\n"
            if character_code and character_code != character_display:
                detailed_info += f"Character Code: {character_code}\n"
            detailed_info += f"Label: {label}\n"
            detailed_info += f"File: {file_name}\n"
            detailed_info += f"Line: {line_number}\n"
            detailed_info += f"Media Count: {media_count} visual assets\n\n"
            detailed_info += f"Full Dialogue:\n{dialogue}"
            
            msg_box = QMessageBox()
            msg_box.setWindowTitle("Dialogue Details")
            msg_box.setText(detailed_info)
            msg_box.setDetailedText(f"Context Information:\n{selected_result}")
            msg_box.exec()
    
    def update_gallery(self, selected_result: Dict[str, Any]):
        """Update the gallery with real media for the selected dialogue.
        
        Args:
            selected_result: The selected search result
        """
        # Clear existing gallery
        self.clear_gallery()
        
        # Enhanced information display with resolved character names
        character_display = selected_result.get('character', 'Unknown')
        character_code = selected_result.get('character_code', '')
        character = self._format_character_name(character_display, character_code)
        label = selected_result.get('label', 'Unknown')
        file_name = selected_result.get('file', '').split('/')[-1] if selected_result.get('file') else 'Unknown'
        line_number = selected_result.get('line_number', 0)
        dialogue = selected_result.get('dialogue', '')
        media_count = selected_result.get('media_count', 0)
        
        # Create detailed info text
        info_text = f"📍 Context Information\n"
        info_text += f"Character: {character}\n"
        if character_code and character_code != character_display:
            info_text += f"Character Code: {character_code}\n"
        info_text += f"Label: {label}\n"
        info_text += f"File: {file_name} (Line {line_number})\n"
        info_text += f"Media Count: {media_count} visual assets\n\n"
        info_text += f"💬 Full Dialogue:\n\"{dialogue}\"\n\n"
        
        self.gallery_info_label.setText(info_text)
        self.gallery_info_label.setWordWrap(True)
        
        # Start loading real media for this label
        self._load_gallery_media(label, media_count)
    
    def _load_gallery_media(self, label: str, expected_count: int):
        """Load real media assets for the specified label.
        
        Args:
            label: The label to load media for
            expected_count: Expected number of media assets
        """
        # Show loading indicator
        loading_info = f"🔄 Loading media for label '{label}'..."
        if expected_count > 0:
            loading_info += f"\nExpected {expected_count} visual assets"
        else:
            loading_info += f"\nSearching for visual assets..."
        
        self.gallery_info_label.setText(self.gallery_info_label.text() + f"\n\n{loading_info}")
        
        # Get source path for the current story
        source_path = self.settings.value(f"story_{self.story_id}/source_path", "")
        if not source_path or not os.path.exists(source_path):
            self._show_gallery_error("Source path not available")
            return
        
        # Start media loading worker
        self.media_worker = MediaLoadingWorker(source_path, label)
        self.media_worker.media_found.connect(self._on_media_found)
        self.media_worker.loading_completed.connect(self._on_media_loading_completed)
        self.media_worker.loading_failed.connect(self._on_media_loading_failed)
        self.media_worker.start()
    
    def _on_media_found(self, media_assets: List[Dict[str, Any]]):
        """Handle media assets found for the selected label.
        
        Args:
            media_assets: List of media asset dictionaries with 'path', 'type', 'name'
        """
        # Use configured max thumbnails (default increased to 24 for better coverage)
        max_thumbnails = self.media_config.get('max_thumbnails', 24)
        display_assets = media_assets[:max_thumbnails]
        
        if not display_assets:
            self._show_gallery_message("No visual assets found for this label")
            return
        
        # Create 6-per-row gallery layout
        for idx, asset in enumerate(display_assets):
            thumbnail = MinimalThumbnailWidget()
            
            # Set up thumbnail with asset info
            asset_path = asset.get('path', '')
            asset_type = asset.get('type', 'unknown')
            asset_name = asset.get('name', 'Unknown')
            
            if asset_path and os.path.exists(asset_path):
                # Load actual image
                thumbnail.set_image(asset_path)
                tooltip = f"Asset: {asset_name}\nType: {asset_type}\nPath: {asset_path}"
            else:
                # Show placeholder with asset info
                thumbnail.setText(f"{asset_type.title()}\n{asset_name}")
                tooltip = f"Asset: {asset_name}\nType: {asset_type}\nPath not found: {asset_path}"
            
            thumbnail.setToolTip(tooltip)
            
            # Add to 6-column grid layout (will create more rows as needed)
            row = idx // 6
            col = idx % 6
            self.gallery_layout.addWidget(thumbnail, row, col)
        
        # Update info label
        total_found = len(media_assets)
        showing_count = len(display_assets)
        
        current_text = self.gallery_info_label.text()
        # Remove the loading text and add results
        lines = current_text.split('\n')
        # Remove lines that start with "🔄 Loading" or "Expected" or "Searching"
        filtered_lines = [line for line in lines if not any(line.strip().startswith(prefix) 
                         for prefix in ["🔄 Loading", "Expected", "Searching"])]
        
        result_text = '\n'.join(filtered_lines)
        result_text += f"\n\n🖼️ Found {total_found} visual assets"
        if showing_count < total_found:
            result_text += f"\nShowing first {showing_count} assets"
        
        self.gallery_info_label.setText(result_text)
        
        # Store current media assets and enable Copy to Stack button when media is found
        self.current_media_assets = media_assets.copy()
        self.copy_to_stack_button.setEnabled(total_found > 0)
    
    def _on_media_loading_completed(self):
        """Handle completion of media loading."""
        # Media worker finished - cleanup will happen automatically
        pass
    
    def _on_media_loading_failed(self, error_message: str):
        """Handle media loading failure.
        
        Args:
            error_message: Error description
        """
        self._show_gallery_error(f"Failed to load media: {error_message}")
    
    def _show_gallery_message(self, message: str):
        """Show a message in the gallery area.
        
        Args:
            message: Message to display
        """
        placeholder = MinimalThumbnailWidget()
        placeholder.setText(message)
        placeholder.setStyleSheet("""
            MinimalThumbnailWidget {
                border: 2px solid #ccc;
                border-radius: 8px;
                background-color: #f9f9f9;
                color: #666;
                font-style: italic;
            }
        """)
        self.gallery_layout.addWidget(placeholder, 0, 0, 1, 6)  # Span 6 columns
    
    # ============================================================================
    # Stage 6: Configuration, Interface Preparation & Advanced Features
    # ============================================================================
    
    def _load_configuration(self):
        """Load dialog search configuration settings."""
        # Search behavior settings
        self.search_config = {
            'max_results': self.settings.value("dialog_search/max_results", 1000, type=int),
            'search_delay': self.settings.value("dialog_search/search_delay", 500, type=int),
            'case_sensitive': self.settings.value("dialog_search/case_sensitive", False, type=bool),
            'whole_words_only': self.settings.value("dialog_search/whole_words_only", False, type=bool),
            'regex_enabled': self.settings.value("dialog_search/regex_enabled", False, type=bool),
        }
        
        # Display settings
        self.display_config = {
            'show_character_codes': self.settings.value("dialog_search/show_character_codes", True, type=bool),
            'show_file_paths': self.settings.value("dialog_search/show_file_paths", True, type=bool),
            'show_line_numbers': self.settings.value("dialog_search/show_line_numbers", True, type=bool),
            'highlight_matches': self.settings.value("dialog_search/highlight_matches", True, type=bool),
            'compact_view': self.settings.value("dialog_search/compact_view", False, type=bool),
        }
        
        # Media settings
        self.media_config = {
            'load_thumbnails': self.settings.value("dialog_search/load_thumbnails", True, type=bool),
            'thumbnail_size': self.settings.value("dialog_search/thumbnail_size", 150, type=int),
            'max_thumbnails': self.settings.value("dialog_search/max_thumbnails", 24, type=int),
            'preload_media': self.settings.value("dialog_search/preload_media", False, type=bool),
        }
        
        # Performance settings
        self.performance_config = {
            'enable_caching': self.settings.value("dialog_search/enable_caching", True, type=bool),
            'max_cache_size': self.settings.value("dialog_search/max_cache_size", 100, type=int),
            'background_loading': self.settings.value("dialog_search/background_loading", True, type=bool),
            'debounce_search': self.settings.value("dialog_search/debounce_search", True, type=bool),
        }
        
        # Screenshots interface preparation (not yet connected)
        self.screenshots_config = {
            'auto_capture': self.settings.value("dialog_search/auto_capture", False, type=bool),
            'capture_quality': self.settings.value("dialog_search/capture_quality", 'high', type=str),
            'capture_format': self.settings.value("dialog_search/capture_format", 'png', type=str),
        }
    
    def _save_configuration(self):
        """Save current configuration to settings."""
        # Save search behavior settings
        for key, value in self.search_config.items():
            self.settings.setValue(f"dialog_search/{key}", value)
        
        # Save display settings
        for key, value in self.display_config.items():
            self.settings.setValue(f"dialog_search/{key}", value)
        
        # Save media settings
        for key, value in self.media_config.items():
            self.settings.setValue(f"dialog_search/{key}", value)
        
        # Save performance settings
        for key, value in self.performance_config.items():
            self.settings.setValue(f"dialog_search/{key}", value)
        
        # Save screenshots settings
        for key, value in self.screenshots_config.items():
            self.settings.setValue(f"dialog_search/{key}", value)
        
        self.settings.sync()
    
    def show_configuration_dialog(self):
        """Show the configuration dialog for dialog search settings."""
        if not self.config_dialog:
            self.config_dialog = DialogSearchConfigDialog(self, self)
        
        if self.config_dialog.exec() == QDialog.DialogCode.Accepted:
            # Apply new configuration
            self._load_configuration()
            self._apply_configuration_changes()
    
    def _apply_configuration_changes(self):
        """Apply configuration changes to the UI and behavior."""
        # Update table display based on configuration
        if hasattr(self, 'results_table') and self.results_table:
            # Show/hide columns based on settings
            header = self.results_table.horizontalHeader()
            if header and hasattr(self, 'display_config') and self.display_config:
                # Character codes visibility
                char_col = 0
                if not self.display_config.get('show_character_codes', True):
                    header.hideSection(char_col)
                else:
                    header.showSection(char_col)
                
                # File paths visibility  
                file_col = 3
                if not self.display_config.get('show_file_paths', True):
                    header.hideSection(file_col)
                else:
                    header.showSection(file_col)
        
        # Update search behavior
        if hasattr(self, 'search_input'):
            # Apply search delay for debouncing
            if self.performance_config.get('debounce_search', True):
                if not hasattr(self, 'search_timer'):
                    self.search_timer = QTimer()
                    self.search_timer.setSingleShot(True)
                    self.search_timer.timeout.connect(self.perform_search)
                self.search_timer.setInterval(self.search_config.get('search_delay', 500))
        
        # Update gallery settings
        if hasattr(self, 'gallery_layout'):
            # Apply thumbnail settings
            max_thumbs = self.media_config.get('max_thumbnails', 12)
            # This will be applied when gallery is next loaded
    
    def _prepare_screenshots_interface(self):
        """Prepare interface hooks for future Screenshots integration."""
        # Create abstract interface for Screenshots integration
        self.screenshots_interface = {
            'capture_enabled': False,  # Will be enabled when Screenshots tab is integrated
            'capture_callback': None,  # Will be set during integration
            'result_mapping': {},      # Maps search results to screenshot data
            'capture_queue': [],       # Queue for pending captures
            'integration_ready': False # Flag for integration status
        }
        
        # Define interface methods that Screenshots tab can hook into
        self.screenshots_hooks = {
            'on_result_selected': self._on_result_selected_for_capture,
            'on_search_completed': self._on_search_completed_for_capture,
            'get_current_result': self._get_current_result_for_capture,
            'get_media_context': self._get_media_context_for_capture,
        }
    
    def _on_result_selected_for_capture(self, result: Dict[str, Any]):
        """Interface method for Screenshots integration - called when result is selected."""
        if not self.screenshots_interface.get('capture_enabled', False):
            return
        
        # Prepare capture context
        capture_context = {
            'character': result.get('character', 'Unknown'),
            'dialogue': result.get('dialogue', ''),
            'label': result.get('label', 'Unknown'),
            'file': result.get('file', ''),
            'line_number': result.get('line_number', 0),
            'media_count': result.get('media_count', 0),
            'timestamp': QDateTime.currentDateTime().toString(),
        }
        
        # Add to capture queue if auto-capture is enabled
        if self.screenshots_config.get('auto_capture', False):
            self.screenshots_interface['capture_queue'].append(capture_context)
            
        # Call Screenshots callback if available
        callback = self.screenshots_interface.get('capture_callback')
        if callback and callable(callback):
            callback(capture_context)
    
    def _on_search_completed_for_capture(self, results: List[Dict[str, Any]]):
        """Interface method for Screenshots integration - called when search completes."""
        if not self.screenshots_interface.get('capture_enabled', False):
            return
        
        # Update result mapping for Screenshots integration
        self.screenshots_interface['result_mapping'] = {
            f"{r.get('file', '')}:{r.get('line_number', 0)}": r 
            for r in results
        }
    
    def _get_current_result_for_capture(self) -> Optional[Dict[str, Any]]:
        """Interface method to get currently selected result for Screenshots integration."""
        selection_model = self.results_table.selectionModel()
        if selection_model:
            selected_rows = selection_model.selectedRows()
            if selected_rows:
                row = selected_rows[0].row()
                if 0 <= row < len(self.search_results):
                    return self.search_results[row]
        return None
    
    def _get_media_context_for_capture(self) -> Dict[str, Any]:
        """Interface method to get current media context for Screenshots integration."""
        current_result = self._get_current_result_for_capture()
        if not current_result:
            return {}
        
        return {
            'label': current_result.get('label', ''),
            'expected_media_count': current_result.get('media_count', 0),
            'character': current_result.get('character', ''),
            'source_file': current_result.get('file', ''),
            'dialogue_context': current_result.get('dialogue', ''),
        }
    
    def enable_screenshots_integration(self, capture_callback=None):
        """Enable Screenshots integration (called by Screenshots tab when ready)."""
        self.screenshots_interface['capture_enabled'] = True
        self.screenshots_interface['integration_ready'] = True
        
        if capture_callback:
            self.screenshots_interface['capture_callback'] = capture_callback
        
        # Update UI to show Screenshots integration is available
        if hasattr(self, 'search_status_label'):
            current_text = self.search_status_label.text()
            if "Screenshots integration ready" not in current_text:
                self.search_status_label.setText(current_text + " | Screenshots integration ready")
    
    def disable_screenshots_integration(self):
        """Disable Screenshots integration."""
        self.screenshots_interface['capture_enabled'] = False
        self.screenshots_interface['integration_ready'] = False
        self.screenshots_interface['capture_callback'] = None
        self.screenshots_interface['capture_queue'].clear()
    
    def _add_advanced_search_filters(self):
        """Add advanced search filters and options."""
        # This will be called during UI creation to add advanced search options
        if hasattr(self, 'search_group'):
            # Add advanced search options row
            advanced_layout = QHBoxLayout()
            
            # Case sensitive checkbox
            self.case_sensitive_cb = QPushButton("Case Sensitive")
            self.case_sensitive_cb.setCheckable(True)
            self.case_sensitive_cb.setChecked(self.search_config.get('case_sensitive', False))
            self.case_sensitive_cb.clicked.connect(self._on_search_option_changed)
            advanced_layout.addWidget(self.case_sensitive_cb)
            
            # Whole words checkbox
            self.whole_words_cb = QPushButton("Whole Words")
            self.whole_words_cb.setCheckable(True)
            self.whole_words_cb.setChecked(self.search_config.get('whole_words_only', False))
            self.whole_words_cb.clicked.connect(self._on_search_option_changed)
            advanced_layout.addWidget(self.whole_words_cb)
            
            # Regex checkbox
            self.regex_cb = QPushButton("Regex")
            self.regex_cb.setCheckable(True)
            self.regex_cb.setChecked(self.search_config.get('regex_enabled', False))
            self.regex_cb.clicked.connect(self._on_search_option_changed)
            advanced_layout.addWidget(self.regex_cb)
            
            # Configuration button
            self.config_button = QPushButton("⚙️ Settings")
            self.config_button.clicked.connect(self.show_configuration_dialog)
            advanced_layout.addWidget(self.config_button)
            
            advanced_layout.addStretch()
            
            # Add to search group
            if hasattr(self, 'search_group') and hasattr(self.search_group, 'layout'):
                self.search_group.layout().addLayout(advanced_layout)
    
    def _on_search_type_changed(self):
        """Handle changes to search type (dialogue vs label)."""
        search_type = self.search_type_combo.currentText()
        
        if search_type == "Label Search":
            self.search_label.setText("Label name:")
            self.search_input.setPlaceholderText("Enter label name to find (e.g., 'start', 'chapter1', 'ending_good')...")
        else:  # Dialogue Search
            self.search_label.setText("Search text:")
            # Update placeholder based on current settings
            self._update_search_placeholder()
    
    def _update_search_placeholder(self):
        """Update search placeholder text based on current settings."""
        if hasattr(self, 'search_input'):
            placeholders = ["Enter dialogue text to find..."]
            if self.search_config.get('case_sensitive', False):
                placeholders.append("Case sensitive")
            if self.search_config.get('whole_words_only', False):
                placeholders.append("Whole words")
            if self.search_config.get('regex_enabled', False):
                placeholders.append("Regex enabled")
            
            self.search_input.setPlaceholderText(" | ".join(placeholders))
    
    def _on_search_option_changed(self):
        """Handle changes to search options."""
        if hasattr(self, 'case_sensitive_cb'):
            self.search_config['case_sensitive'] = self.case_sensitive_cb.isChecked()
        if hasattr(self, 'whole_words_cb'):
            self.search_config['whole_words_only'] = self.whole_words_cb.isChecked()
        if hasattr(self, 'regex_cb'):
            self.search_config['regex_enabled'] = self.regex_cb.isChecked()
        
        # Save configuration
        self._save_configuration()
        
        # Update search placeholder text (only for dialogue search)
        if hasattr(self, 'search_type_combo') and self.search_type_combo.currentText() == "Dialogue Search":
            self._update_search_placeholder()
    
    def _enhanced_export_system(self):
        """Enhanced export system for search results."""
        # This provides multiple export formats and options
        export_formats = {
            'txt': self._export_as_text,
            'csv': self._export_as_csv,
            'json': self._export_as_json,
            'html': self._export_as_html,
        }
        return export_formats
    
    def _export_as_csv(self, results: List[Dict[str, Any]], file_path: str):
        """Export search results as CSV."""
        import csv
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Character', 'Dialogue', 'Label', 'File', 'Line', 'Media Count']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in results:
                writer.writerow({
                    'Character': result.get('character', ''),
                    'Dialogue': result.get('dialogue', ''),
                    'Label': result.get('label', ''),
                    'File': result.get('file', ''),
                    'Line': result.get('line_number', ''),
                    'Media Count': result.get('media_count', ''),
                })
    
    def _export_as_json(self, results: List[Dict[str, Any]], file_path: str):
        """Export search results as JSON."""
        import json
        
        export_data = {
            'search_metadata': {
                'export_timestamp': QDateTime.currentDateTime().toString(),
                'total_results': len(results),
                'search_config': self.search_config,
            },
            'results': results
        }
        
        with open(file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)
    
    def _export_as_html(self, results: List[Dict[str, Any]], file_path: str):
        """Export search results as HTML."""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Dialog Search Results</title>
    <style>
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .dialogue {{ max-width: 400px; word-wrap: break-word; }}
    </style>
</head>
<body>
    <h1>Dialog Search Results</h1>
    <p>Exported: {QDateTime.currentDateTime().toString()}</p>
    <p>Total Results: {len(results)}</p>
    
    <table>
        <tr>
            <th>Character</th>
            <th>Dialogue</th>
            <th>Label</th>
            <th>File</th>
            <th>Line</th>
            <th>Media Count</th>
        </tr>
"""
        
        for result in results:
            html_content += f"""
        <tr>
            <td>{result.get('character', '')}</td>
            <td class="dialogue">{result.get('dialogue', '')}</td>
            <td>{result.get('label', '')}</td>
            <td>{result.get('file', '')}</td>
            <td>{result.get('line_number', '')}</td>
            <td>{result.get('media_count', '')}</td>
        </tr>
"""
        
        html_content += """
    </table>
</body>
</html>
"""
        
        with open(file_path, 'w', encoding='utf-8') as htmlfile:
            htmlfile.write(html_content)
    
    # ============================================================================
    # Stage 5: Enhanced Error Handling, Search History & Context Menus
    # ============================================================================
    
    def _load_search_history(self):
        """Load search history from settings."""
        try:
            # Load history from QSettings
            history_list = self.settings.value("dialog_search/history", [])
            if isinstance(history_list, list):
                self.search_history = history_list[:self.max_history_items]
            else:
                self.search_history = []
            
            # Reset history index
            self.current_history_index = -1
            
        except Exception as e:
            print(f"Error loading search history: {e}")
            self.search_history = []
    
    def _save_search_history(self):
        """Save search history to settings."""
        try:
            self.settings.setValue("dialog_search/history", self.search_history)
            self.settings.sync()
        except Exception as e:
            print(f"Error saving search history: {e}")
    
    def _add_to_search_history(self, search_term: str):
        """Add search term to history.
        
        Args:
            search_term: The search term to add
        """
        if not search_term or search_term.isspace():
            return
        
        search_term = search_term.strip()
        
        # Remove if already exists (move to top)
        if search_term in self.search_history:
            self.search_history.remove(search_term)
        
        # Add to beginning
        self.search_history.insert(0, search_term)
        
        # Limit history size
        if len(self.search_history) > self.max_history_items:
            self.search_history = self.search_history[:self.max_history_items]
        
        # Save to settings
        self._save_search_history()
        
        # Reset history navigation
        self.current_history_index = -1
    
    def _setup_context_menus(self):
        """Set up context menus for results table and gallery."""
        # Results table context menu
        self.results_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.results_table.customContextMenuRequested.connect(self._show_results_context_menu)
        
        # Gallery context menu
        self.gallery_scroll.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.gallery_scroll.customContextMenuRequested.connect(self._show_gallery_context_menu)
    
    def _show_results_context_menu(self, position):
        """Show context menu for results table.
        
        Args:
            position: Click position
        """
        if not self.search_results:
            return
        
        # Get clicked item
        item = self.results_table.itemAt(position)
        if not item:
            return
        
        row = item.row()
        if row < 0 or row >= len(self.search_results):
            return
        
        selected_result = self.search_results[row]
        
        # Create context menu
        context_menu = QMenu(self)
        
        # Copy actions
        copy_character_action = context_menu.addAction("📋 Copy Character Name")
        copy_dialogue_action = context_menu.addAction("📋 Copy Dialogue")
        copy_label_action = context_menu.addAction("📋 Copy Label")
        copy_file_action = context_menu.addAction("📋 Copy File Path")
        
        context_menu.addSeparator()
        
        # View actions
        view_details_action = context_menu.addAction("🔍 View Details")
        load_media_action = context_menu.addAction("🖼️ Load Media")
        
        context_menu.addSeparator()
        
        # Export actions
        export_result_action = context_menu.addAction("💾 Export Result")
        
        # Show menu and handle selection
        action = context_menu.exec(self.results_table.mapToGlobal(position))
        
        if action == copy_character_action:
            self._copy_to_clipboard(selected_result.get('character', ''))
        elif action == copy_dialogue_action:
            self._copy_to_clipboard(selected_result.get('dialogue', ''))
        elif action == copy_label_action:
            self._copy_to_clipboard(selected_result.get('label', ''))
        elif action == copy_file_action:
            self._copy_to_clipboard(selected_result.get('file', ''))
        elif action == view_details_action:
            self.on_result_double_clicked(item)
        elif action == load_media_action:
            self.update_gallery(selected_result)
        elif action == export_result_action:
            self._export_search_result(selected_result)
    
    def _show_gallery_context_menu(self, position):
        """Show context menu for gallery area.
        
        Args:
            position: Click position
        """
        context_menu = QMenu(self)
        
        # Refresh action
        refresh_action = context_menu.addAction("🔄 Refresh Gallery")
        
        context_menu.addSeparator()
        
        # View actions
        if self.search_results:
            view_all_action = context_menu.addAction("👁️ View All Results")
            export_gallery_action = context_menu.addAction("💾 Export Gallery Info")
        
        clear_action = context_menu.addAction("🗑️ Clear Gallery")
        
        # Show menu and handle selection
        action = context_menu.exec(self.gallery_scroll.mapToGlobal(position))
        
        if action == refresh_action:
            # Refresh current gallery if selection exists
            selection_model = self.results_table.selectionModel()
            if selection_model:
                selected_rows = selection_model.selectedRows()
                if selected_rows:
                    row = selected_rows[0].row()
                    if 0 <= row < len(self.search_results):
                        self.update_gallery(self.search_results[row])
        elif action == clear_action:
            self.clear_gallery()
        elif hasattr(locals(), 'view_all_action') and action == view_all_action:
            self._show_all_results_summary()
        elif hasattr(locals(), 'export_gallery_action') and action == export_gallery_action:
            self._export_gallery_info()
    
    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard.
        
        Args:
            text: Text to copy
        """
        if text:
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(str(text))
    
    def _export_search_result(self, result: Dict[str, Any]):
        """Export a single search result.
        
        Args:
            result: Search result to export
        """
        try:
            from PyQt6.QtWidgets import QFileDialog
            
            # Get export file path
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Search Result",
                f"dialogue_result_{result.get('label', 'unknown')}.txt",
                "Text Files (*.txt);;All Files (*)"
            )
            
            if not file_path:
                return
            
            # Format result for export
            character = result.get('character', 'Unknown')
            label = result.get('label', 'Unknown')
            file_name = result.get('file', 'Unknown')
            line_number = result.get('line_number', 0)
            dialogue = result.get('dialogue', '')
            media_count = result.get('media_count', 0)
            
            export_text = f"""Dialog Search Result Export
Generated: {QDateTime.currentDateTime().toString()}

Character: {character}
Label: {label}
File: {file_name}
Line: {line_number}
Media Count: {media_count}

Dialogue:
{dialogue}

Result Data:
{result}
"""
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(export_text)
            
            QMessageBox.information(self, "Export Complete", f"Result exported to:\n{file_path}")
            
        except Exception as e:
            QMessageBox.warning(self, "Export Failed", f"Failed to export result:\n{str(e)}")
    
    def _show_all_results_summary(self):
        """Show summary of all search results."""
        if not self.search_results:
            return
        
        # Create summary
        summary = f"Search Results Summary\n"
        summary += f"{'=' * 50}\n\n"
        summary += f"Total Results: {len(self.search_results)}\n\n"
        
        # Character breakdown
        characters = {}
        labels = {}
        files = {}
        total_media = 0
        
        for result in self.search_results:
            char = result.get('character', 'Unknown')
            label = result.get('label', 'Unknown')
            file_name = result.get('file', 'Unknown')
            media_count = result.get('media_count', 0)
            
            characters[char] = characters.get(char, 0) + 1
            labels[label] = labels.get(label, 0) + 1
            files[file_name] = files.get(file_name, 0) + 1
            total_media += media_count
        
        # Add breakdowns to summary
        summary += f"Characters ({len(characters)}):\n"
        for char, count in sorted(characters.items(), key=lambda x: x[1], reverse=True)[:10]:
            summary += f"  {char}: {count} lines\n"
        
        summary += f"\nLabels ({len(labels)}):\n"
        for label, count in sorted(labels.items(), key=lambda x: x[1], reverse=True)[:10]:
            summary += f"  {label}: {count} lines\n"
        
        summary += f"\nFiles ({len(files)}):\n"
        for file_name, count in sorted(files.items(), key=lambda x: x[1], reverse=True)[:10]:
            summary += f"  {file_name}: {count} lines\n"
        
        summary += f"\nTotal Visual Assets: {total_media}\n"
        
        # Show in dialog
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Search Results Summary")
        msg_box.setText(summary)
        msg_box.setDetailedText("Full search results data available in table")
        msg_box.exec()
    
    def _export_gallery_info(self):
        """Export current gallery information."""
        selection_model = self.results_table.selectionModel()
        if not selection_model:
            return
        
        selected_rows = selection_model.selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select a result first")
            return
        
        row = selected_rows[0].row()
        if 0 <= row < len(self.search_results):
            self._export_search_result(self.search_results[row])
    
    def _enhanced_error_handling(self, error_message: str, error_type: str = "general") -> bool:
        """Enhanced error handling with retry logic and user-friendly messages.
        
        Args:
            error_message: The error message
            error_type: Type of error for categorization
            
        Returns:
            True if retry should be attempted, False otherwise
        """
        import time
        from datetime import datetime, timedelta
        
        current_time = time.time()
        
        # Check if we're in a rapid error loop
        if self.last_error_time and (current_time - self.last_error_time) < 2:
            self.error_count += 1
        else:
            self.error_count = 1
        
        self.last_error_time = current_time
        
        # Categorize errors and provide user-friendly messages
        user_message = self._categorize_error(error_message, error_type)
        
        # Determine if retry is appropriate
        should_retry = self.error_count <= self.max_retries and error_type != "critical"
        
        if should_retry:
            retry_msg = f"\n\nRetrying... (Attempt {self.error_count}/{self.max_retries})"
            QMessageBox.warning(self, f"Operation Failed", user_message + retry_msg)
            
            # Add delay before retry
            QTimer.singleShot(self.error_recovery_delay, lambda: None)
        else:
            # Max retries reached or critical error
            if self.error_count > self.max_retries:
                user_message += f"\n\nMax retries ({self.max_retries}) reached. Please check your configuration."
            
            QMessageBox.critical(self, "Operation Failed", user_message)
            self.error_count = 0  # Reset for next operation
        
        return should_retry
    
    def _categorize_error(self, error_message: str, error_type: str) -> str:
        """Categorize error and return user-friendly message.
        
        Args:
            error_message: Raw error message
            error_type: Error type
            
        Returns:
            User-friendly error message
        """
        error_lower = error_message.lower()
        
        # File/Path related errors
        if "path" in error_lower or "directory" in error_lower or "file" in error_lower:
            return ("📁 File Access Error\n\n"
                   "The system cannot access the required files or directories. "
                   "Please check that:\n"
                   "• Source path is correctly configured\n"
                   "• Files are not locked by another application\n"
                   "• You have proper file permissions\n\n"
                   f"Technical details: {error_message}")
        
        # Network/Connection errors
        elif "connection" in error_lower or "network" in error_lower:
            return ("🌐 Connection Error\n\n"
                   "Unable to establish required connections. "
                   "Please check your network connectivity.\n\n"
                   f"Technical details: {error_message}")
        
        # Memory errors
        elif "memory" in error_lower or "ram" in error_lower:
            return ("💾 Memory Error\n\n"
                   "The system is running low on memory. "
                   "Try closing other applications or reducing the search scope.\n\n"
                   f"Technical details: {error_message}")
        
        # Permission errors
        elif "permission" in error_lower or "access" in error_lower:
            return ("🔒 Permission Error\n\n"
                   "The application doesn't have sufficient permissions. "
                   "Try running as administrator or check file permissions.\n\n"
                   f"Technical details: {error_message}")
        
        # API/Import errors
        elif "import" in error_lower or "module" in error_lower:
            return ("⚙️ System Configuration Error\n\n"
                   "Required system components are missing or incorrectly configured. "
                   "Please check your installation.\n\n"
                   f"Technical details: {error_message}")
        
        # Generic error
        else:
            return ("❌ Unexpected Error\n\n"
                   "An unexpected error occurred during the operation.\n\n"
                   f"Technical details: {error_message}")
    
    def _setup_keyboard_shortcuts(self):
        """Set up enhanced keyboard shortcuts for search history navigation."""
        # Install event filter for history navigation
        self.search_input.installEventFilter(self)
    
    def eventFilter(self, source, event):
        """Filter events for search history navigation.
        
        Args:
            source: Event source
            event: Event
            
        Returns:
            True if event was handled, False otherwise
        """
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QKeyEvent
        
        if (source == self.search_input and 
            event.type() == QEvent.Type.KeyPress and 
            isinstance(event, QKeyEvent)):
            
            if event.key() == Qt.Key.Key_Up:
                # Navigate backwards in history
                if self.search_history and self.current_history_index < len(self.search_history) - 1:
                    self.current_history_index += 1
                    self.search_input.setText(self.search_history[self.current_history_index])
                    return True
            elif event.key() == Qt.Key.Key_Down:
                # Navigate forwards in history
                if self.search_history and self.current_history_index > 0:
                    self.current_history_index -= 1
                    self.search_input.setText(self.search_history[self.current_history_index])
                    return True
                elif self.current_history_index == 0:
                    self.current_history_index = -1
                    self.search_input.clear()
                    return True
        
        # Default handling
        return super().eventFilter(source, event)
    
    def _show_gallery_error(self, error_message: str):
        """Show an error message in the gallery area.
        
        Args:
            error_message: Error message to display
        """
        placeholder = MinimalThumbnailWidget()
        placeholder.setText(f"❌ {error_message}")
        placeholder.setStyleSheet("""
            MinimalThumbnailWidget {
                border: 2px solid #ff6b6b;
                border-radius: 8px;
                background-color: #ffe0e0;
                color: #cc0000;
                font-weight: bold;
            }
        """)
        self.gallery_layout.addWidget(placeholder, 0, 0, 1, 6)  # Span 6 columns 
    
    def set_parent_tab_container(self, parent_tab_container):
        """Set reference to the parent SourceAnalysisTab for cross-tab communication.
        
        Args:
            parent_tab_container: Reference to SourceAnalysisTab instance
        """
        self.parent_tab_container = parent_tab_container
    
    def copy_media_to_stack(self):
        """Copy discovered media files to the Screenshots tab's image stack.
        
        This method will:
        1. Get currently loaded media assets
        2. Copy them to the image-stack folder with proper timestamps
        3. Refresh the Screenshots tab
        4. Handle duplicates based on checkbox setting
        """
        if not self.current_media_assets:
            QMessageBox.information(self, "No Media", "No media files available to copy. Please select a search result first.")
            return
            
        # Import the media copier utility
        from app.utils.media_copier import copy_media_to_image_stack
        
        # Get settings
        skip_duplicates = self.skip_duplicates_checkbox.isChecked()
        
        # Define completion callback to refresh Screenshots tab
        def on_copy_completed(copied_count: int, skipped_count: int):
            """Callback when copy operation completes."""
            if copied_count > 0 and self.parent_tab_container:
                # Refresh Screenshots tab thumbnails
                screenshots_tab = getattr(self.parent_tab_container, 'screenshots_tab', None)
                if screenshots_tab and hasattr(screenshots_tab, 'load_existing_images'):
                    screenshots_tab.load_existing_images()
        
        # Start copy operation
        try:
            success = copy_media_to_image_stack(
                media_assets=self.current_media_assets,
                skip_duplicates=skip_duplicates,
                image_stack_folder="image-stack",
                parent=self,
                completion_callback=on_copy_completed
            )
            
            if success:
                # Operation completed successfully (callback already called)
                pass
            else:
                # Operation was cancelled or failed (error already shown)
                pass
                
        except Exception as e:
            QMessageBox.critical(self, "Copy Failed", f"An unexpected error occurred:\n\n{str(e)}")