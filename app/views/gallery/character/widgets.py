#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Character-related widgets for The Plot Thickens gallery.

This module contains widgets for character selection, filtering and listing.
"""

from typing import List, Dict, Any, Optional
import os

from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QMenu, QToolTip
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QAction

from app.utils.tooltip_utils import generate_avatar_tooltip_html

class CharacterListWidget(QListWidget):
    """List widget for displaying characters with hover effects and avatar tooltips."""
    
    def __init__(self, db_conn, parent=None):
        """Initialize the character list widget.
        
        Args:
            db_conn: Database connection
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.hoveredItem = None
        self.setMouseTracking(True)
        
    def get_character_avatar_path(self, character_id: int) -> Optional[str]:
        """Get the avatar path for a character.
        
        Args:
            character_id: ID of the character
            
        Returns:
            Path to the avatar image file or None
        """
        if not character_id:
            return None
            
        try:
            cursor = self.db_conn.cursor()
            
            # Debug info
            print(f"Looking for avatar for character ID: {character_id}")
            
            # Try characters.avatar_path first (most likely location)
            cursor.execute("""
                SELECT avatar_path 
                FROM characters 
                WHERE id = ?
            """, (character_id,))
            
            result = cursor.fetchone()
            if result and result[0]:
                avatar_path = result[0]
                print(f"Found avatar in characters table: {avatar_path}")
                if os.path.exists(avatar_path):
                    print(f"Avatar file exists, returning it")
                    return avatar_path
                else:
                    print(f"Avatar file does not exist at {avatar_path}")
                    
            # If not found or doesn't exist, try character_details.avatar_path
            cursor.execute("""
                SELECT avatar_path 
                FROM character_details 
                WHERE character_id = ?
            """, (character_id,))
            
            result = cursor.fetchone()
            if result and result[0]:
                avatar_path = result[0]
                print(f"Found avatar in character_details table: {avatar_path}")
                if os.path.exists(avatar_path):
                    print(f"Avatar file exists, returning it")
                    return avatar_path
                else:
                    print(f"Avatar file does not exist at {avatar_path}")
            
            # If we still haven't found a valid avatar, try checking media folders
            # Look up the story_id for this character
            cursor.execute("SELECT story_id FROM characters WHERE id = ?", (character_id,))
            story_result = cursor.fetchone()
            
            if story_result and story_result[0]:
                story_id = story_result[0]
                
                # Get the character's name for constructing default avatar paths
                cursor.execute("SELECT name FROM characters WHERE id = ?", (character_id,))
                name_result = cursor.fetchone()
                if name_result and name_result[0]:
                    character_name = name_result[0]
                    
                    # Get story folder paths
                    cursor.execute("SELECT * FROM stories WHERE id = ?", (story_id,))
                    story_data = cursor.fetchone()
                    if story_data:
                        # Import here to avoid circular imports
                        from app.db_sqlite import get_story_folder_paths
                        folder_paths = get_story_folder_paths(dict(story_data))
                        
                        # Check common avatar locations
                        possible_locations = [
                            os.path.join(folder_paths.get('characters_folder', ''), f"{character_name}.png"),
                            os.path.join(folder_paths.get('characters_folder', ''), f"{character_name}.jpg"),
                            os.path.join(folder_paths.get('characters_folder', ''), f"avatar_{character_name}.png"),
                            os.path.join(folder_paths.get('characters_folder', ''), f"avatar_{character_name}.jpg"),
                            os.path.join(folder_paths.get('base_folder', ''), "characters", f"{character_name}.png"),
                            os.path.join(folder_paths.get('base_folder', ''), "characters", f"{character_name}.jpg")
                        ]
                        
                        for location in possible_locations:
                            if os.path.exists(location):
                                print(f"Found avatar at common location: {location}")
                                return location
                
        except Exception as e:
            print(f"Error getting character avatar: {e}")
            
        print(f"No avatar found for character ID: {character_id}")
        return None
        
    def extract_character_data(self, item: QListWidgetItem) -> Dict[str, Any]:
        """Extract character data from a list item.
        
        Args:
            item: QListWidgetItem to extract data from
            
        Returns:
            Dictionary with character_id and character_name
        """
        if not item:
            return {}
            
        character_data = item.data(Qt.ItemDataRole.UserRole)
        if not character_data:
            return {}
            
        # Handle different data formats
        character_id = None
        character_name = None
        
        # Case 1: character_data is just an ID (integer)
        if isinstance(character_data, int):
            character_id = character_data
            character_name = item.text()
            
        # Case 2: character_data is a dict with 'id' and 'name' keys
        elif isinstance(character_data, dict):
            # Try different key patterns
            if 'id' in character_data:
                character_id = character_data['id']
                character_name = character_data.get('name', item.text())
            elif 'character_id' in character_data:
                character_id = character_data['character_id']
                character_name = character_data.get('character_name', item.text())
        
        # If we couldn't extract a name, use the item text
        if not character_name:
            character_name = item.text()
            
        return {
            'character_id': character_id,
            'character_name': character_name
        }
        
    def show_avatar_tooltip(self, character_data: Dict[str, Any], position: QPoint) -> None:
        """Show avatar tooltip for a character.
        
        Args:
            character_data: Dictionary with character_id and character_name
            position: Position to show the tooltip
        """
        character_id = character_data.get('character_id')
        character_name = character_data.get('character_name', 'Unknown')
        
        if not character_id:
            return
            
        # Get avatar path
        avatar_path = self.get_character_avatar_path(character_id)
        
        # Generate HTML tooltip with avatar
        tooltip_html = generate_avatar_tooltip_html(character_name, avatar_path)
        
        # Show the tooltip
        QToolTip.showText(self.mapToGlobal(position), tooltip_html)
        
    def mouseMoveEvent(self, event):
        """Handle mouse move events for hover highlighting and avatar tooltips.
        
        Args:
            event: Mouse event
        """
        # Find the item under the cursor
        item = self.itemAt(event.pos())
        
        # If hovering over a valid item
        if item:
            # Only update if hovering over a new item
            if self.hoveredItem != item:
                self.hoveredItem = item
                
                # Extract character data and show avatar tooltip
                character_data = self.extract_character_data(item)
                if character_data:
                    self.show_avatar_tooltip(character_data, event.pos())
            
        else:
            self.hoveredItem = None
            QToolTip.hideText()
        
        # Call the parent class method
        super().mouseMoveEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave events to reset hover state.
        
        Args:
            event: Leave event
        """
        self.hoveredItem = None
        QToolTip.hideText()
        super().leaveEvent(event)

class OnSceneCharacterListWidget(CharacterListWidget):
    """List widget for characters that appear in a scene."""
    
    def __init__(self, db_conn, parent=None):
        """Initialize the on-scene character list widget."""
        super().__init__(db_conn, parent)
        # Implementation will be moved here from gallery_widget.py
    
    def extract_character_data(self, item: QListWidgetItem) -> Dict[str, Any]:
        """Override to handle the OnSceneCharacterListWidget's specific data structure.
        
        Args:
            item: QListWidgetItem to extract data from
            
        Returns:
            Dictionary with character_id and character_name
        """
        if not item:
            return {}
            
        # In OnSceneCharacterListWidget, the UserRole typically contains just the character ID
        character_id = item.data(Qt.ItemDataRole.UserRole)
        if not character_id:
            return {}
            
        # Get character name from item text (removing any checkbox or other UI cruft)
        character_name = item.text()
        
        # Return the standardized data structure
        return {
            'character_id': character_id,
            'character_name': character_name
        }

class GalleryFilterCharacterListWidget(CharacterListWidget):
    """List widget for filtering characters in the gallery."""
    
    def __init__(self, db_conn, parent=None):
        """Initialize the gallery filter character list widget."""
        super().__init__(db_conn, parent)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        
    def load_characters(self, characters: List[Dict[str, Any]], image_counts: Dict[int, int] = None) -> None:
        """Load characters into the list widget with image counts.
        
        Args:
            characters: List of character dictionaries
            image_counts: Optional dictionary mapping character IDs to image counts
        """
        self.clear()
        for character in characters:
            # Get image count for this character
            char_id = character["id"]
            count = image_counts.get(char_id, 0) if image_counts else 0
            
            # Create display text with image count
            display_text = f"{character['name']} ({count})"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, character)
            self.addItem(item)
            
    def get_selected_character(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected character.
        
        Returns:
            Character data dictionary or None if no character is selected
        """
        selected_items = self.selectedItems()
        if selected_items:
            return selected_items[0].data(Qt.ItemDataRole.UserRole)
        return None

class FilterCharacterListWidget(CharacterListWidget):
    """List widget for character filtering with context menu options."""
    
    def __init__(self, db_conn, parent=None):
        """Initialize the filter character list widget."""
        super().__init__(db_conn, parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
    def get_selected_character(self) -> Optional[Dict[str, Any]]:
        """Get the selected character data.
        
        Returns:
            Character data dictionary or None if no character is selected
        """
        selected_items = self.selectedItems()
        if selected_items:
            return self.extract_character_data(selected_items[0])
        return None
        
    def show_context_menu(self, position: QPoint):
        """Show a context menu for the character list.
        
        Args:
            position: Position to show the menu
        """
        item = self.itemAt(position)
        if not item:
            return
            
        character_data = self.extract_character_data(item)
        if not character_data:
            return
            
        # Create a context menu
        menu = QMenu(self)
        
        # Add actions for including and excluding characters
        include_action = QAction("➕ Include in filters", self)
        include_action.triggered.connect(
            lambda: self.parent().add_character_filter(character_data, True)
        )
        menu.addAction(include_action)
        
        exclude_action = QAction("➖ Exclude from filters", self)
        exclude_action.triggered.connect(
            lambda: self.parent().add_character_filter(character_data, False)
        )
        menu.addAction(exclude_action)
        
        # Show the menu
        menu.exec(self.mapToGlobal(position))

class RecognitionResultsListWidget(CharacterListWidget):
    """List widget for displaying character recognition results with avatar tooltips."""
    
    def __init__(self, db_conn, parent=None):
        """Initialize the recognition results list widget."""
        super().__init__(db_conn, parent)
        
    def extract_character_data(self, item: QListWidgetItem) -> Dict[str, Any]:
        """Override to handle the specific data structure of recognition results.
        
        Args:
            item: QListWidgetItem to extract data from
            
        Returns:
            Dictionary with character_id and character_name
        """
        if not item:
            return {}
            
        # Handle non-selectable headers and separators
        if not item.flags() & Qt.ItemFlag.ItemIsSelectable:
            return {}
            
        # Get the character ID from UserRole
        character_id = item.data(Qt.ItemDataRole.UserRole)
        if not character_id:
            return {}
            
        # Extract character name from text (remove the match percentage)
        text = item.text()
        character_name = text.split(" (")[0] if " (" in text else text
        
        return {
            'character_id': character_id,
            'character_name': character_name
        }
