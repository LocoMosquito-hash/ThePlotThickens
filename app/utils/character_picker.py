#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Character Picker for The Plot Thickens application.

This module provides a widget for selecting characters, using the CharacterBadge system.
"""

from typing import List, Dict, Any, Optional, Callable

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame, 
    QLabel, QLineEdit, QPushButton, QComboBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal

from app.utils.character_badge import CharacterBadge, create_character_badge
from app.utils.icons.icon_manager import icon_manager


class CharacterPicker(QWidget):
    """
    A widget for displaying and selecting characters using CharacterBadges.
    
    This widget can be used in various contexts where character selection is needed,
    such as tagging characters in events, selecting characters for relationships, etc.
    """
    
    # Signals
    character_selected = pyqtSignal(int, dict)  # Emitted when a character is selected (id, data)
    
    def __init__(
        self,
        characters: List[Dict[str, Any]] = None,
        multi_select: bool = False,
        show_filter: bool = True,
        badge_size: str = CharacterBadge.SIZE_MEDIUM,
        badge_style: str = CharacterBadge.STYLE_OUTLINED,
        parent: Optional[QWidget] = None
    ):
        """Initialize the character picker.
        
        Args:
            characters: List of character dictionaries (with at least id, name, and is_main_character)
            multi_select: Whether multiple characters can be selected
            show_filter: Whether to show the filter/search input
            badge_size: Size of the character badges
            badge_style: Style of the character badges
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.characters = characters or []
        self.multi_select = multi_select
        self.show_filter = show_filter
        self.badge_size = badge_size
        self.badge_style = badge_style
        
        # Track selected characters
        self.selected_character_ids = set()
        
        # Track created badges
        self.character_badges = {}
        
        # Initialize UI
        self._init_ui()
        
        # Load characters
        self.set_characters(self.characters)
    
    def _init_ui(self) -> None:
        """Initialize the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)
        
        # Add filter if needed
        if self.show_filter:
            filter_layout = QHBoxLayout()
            filter_layout.setContentsMargins(0, 0, 0, 0)
            filter_layout.setSpacing(4)
            
            # Filter label
            filter_label = QLabel("Filter:")
            filter_layout.addWidget(filter_label)
            
            # Filter input
            self.filter_input = QLineEdit()
            self.filter_input.setPlaceholderText("Filter characters...")
            self.filter_input.textChanged.connect(self._filter_characters)
            filter_layout.addWidget(self.filter_input)
            
            # Add filter layout to main layout
            main_layout.addLayout(filter_layout)
        
        # Create scroll area for character badges
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Container widget for badges
        self.badges_container = QWidget()
        self.badges_layout = QVBoxLayout(self.badges_container)
        self.badges_layout.setContentsMargins(0, 0, 0, 0)
        self.badges_layout.setSpacing(4)
        self.badges_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Add the container to the scroll area
        scroll_area.setWidget(self.badges_container)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)
        
        # Add buttons for multi-select mode
        if self.multi_select:
            buttons_layout = QHBoxLayout()
            buttons_layout.setContentsMargins(0, 0, 0, 0)
            buttons_layout.setSpacing(6)
            
            # Select all button
            self.select_all_button = QPushButton("Select All")
            self.select_all_button.clicked.connect(self.select_all)
            buttons_layout.addWidget(self.select_all_button)
            
            # Clear selection button
            self.clear_button = QPushButton("Clear")
            self.clear_button.clicked.connect(self.clear_selection)
            buttons_layout.addWidget(self.clear_button)
            
            # Add buttons to main layout
            main_layout.addLayout(buttons_layout)
    
    def set_characters(self, characters: List[Dict[str, Any]]) -> None:
        """Set the list of characters to display.
        
        Args:
            characters: List of character dictionaries
        """
        self.characters = characters
        
        # Clear existing badges
        self._clear_badges()
        
        # Create badges for each character
        for character in self.characters:
            self._add_character_badge(character)
        
        # Add a spacer at the end
        self.badges_layout.addStretch()
    
    def _add_character_badge(self, character: Dict[str, Any]) -> None:
        """Add a character badge to the layout.
        
        Args:
            character: Character data dictionary
        """
        character_id = character.get('id')
        if not character_id:
            return
        
        # Create a container for the badge and potential additional widgets
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(4)
        
        # Create the badge
        badge = create_character_badge(
            character_id=character_id,
            character_data=character,
            size=self.badge_size,
            style=self.badge_style,
            show_avatar=True,
            show_name=True,
            show_main_character=True
        )
        
        # Connect badge click handler
        badge.clicked.connect(self._on_badge_clicked)
        
        # Add selection indicator if using multi-select
        if self.multi_select:
            # For multi-select, add a checkbox-like indicator using an icon
            selection_button = QPushButton()
            selection_button.setCheckable(True)
            selection_button.setFixedSize(24, 24)
            selection_button.setIcon(icon_manager.get_icon("circle"))
            selection_button.clicked.connect(
                lambda checked, cid=character_id: self._on_selection_toggled(cid, checked)
            )
            
            # Store the button in the badge for easy access
            badge.selection_button = selection_button
            
            # Add to container layout
            container_layout.addWidget(selection_button)
        
        # Add badge to container
        container_layout.addWidget(badge)
        container_layout.addStretch()
        
        # Add container to main layout
        self.badges_layout.addWidget(container)
        
        # Store badge for later reference
        self.character_badges[character_id] = badge
    
    def _clear_badges(self) -> None:
        """Clear all character badges."""
        # Clear the selected IDs
        self.selected_character_ids.clear()
        
        # Remove all widgets from the layout
        while self.badges_layout.count():
            item = self.badges_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Clear the badges dictionary
        self.character_badges.clear()
    
    def _on_badge_clicked(self, character_id: int) -> None:
        """Handle badge click events.
        
        Args:
            character_id: ID of the clicked character
        """
        if self.multi_select:
            # In multi-select mode, toggle selection
            if character_id in self.selected_character_ids:
                self.selected_character_ids.remove(character_id)
            else:
                self.selected_character_ids.add(character_id)
            
            # Update visual selection state
            self._update_selection_state(character_id)
        else:
            # In single-select mode, emit signal with the character data
            character_data = self._get_character_data(character_id)
            if character_data:
                self.character_selected.emit(character_id, character_data)
    
    def _on_selection_toggled(self, character_id: int, checked: bool) -> None:
        """Handle selection toggle events in multi-select mode.
        
        Args:
            character_id: ID of the character
            checked: Whether the selection was toggled on or off
        """
        if checked:
            self.selected_character_ids.add(character_id)
        else:
            self.selected_character_ids.discard(character_id)
        
        # Update visual selection state
        self._update_selection_state(character_id)
    
    def _update_selection_state(self, character_id: int) -> None:
        """Update the visual selection state for a character.
        
        Args:
            character_id: ID of the character to update
        """
        badge = self.character_badges.get(character_id)
        if not badge:
            return
        
        if self.multi_select and hasattr(badge, 'selection_button'):
            # Update the selection button state
            is_selected = character_id in self.selected_character_ids
            badge.selection_button.setChecked(is_selected)
            
            # Update the icon
            if is_selected:
                badge.selection_button.setIcon(icon_manager.get_icon("circle-check"))
            else:
                badge.selection_button.setIcon(icon_manager.get_icon("circle"))
    
    def _get_character_data(self, character_id: int) -> Optional[Dict[str, Any]]:
        """Get character data by ID.
        
        Args:
            character_id: ID of the character
            
        Returns:
            Character data dictionary or None if not found
        """
        for character in self.characters:
            if character.get('id') == character_id:
                return character
        return None
    
    def _filter_characters(self, filter_text: str = "") -> None:
        """Filter displayed characters based on search text.
        
        Args:
            filter_text: Text to filter by
        """
        filter_text = filter_text.lower().strip()
        
        # Show/hide badges based on filter
        for character_id, badge in self.character_badges.items():
            character_data = self._get_character_data(character_id)
            if not character_data:
                continue
            
            # Get the character name
            name = character_data.get('name', '').lower()
            
            # Get parent container widget (the badge's parent's parent)
            container = badge.parent()
            
            # Check if name contains filter text
            if not filter_text or filter_text in name:
                # Show the badge
                if container:
                    container.setVisible(True)
            else:
                # Hide the badge
                if container:
                    container.setVisible(False)
    
    def select_all(self) -> None:
        """Select all characters (multi-select mode only)."""
        if not self.multi_select:
            return
        
        # Add all character IDs to selected set
        for character in self.characters:
            character_id = character.get('id')
            if character_id:
                self.selected_character_ids.add(character_id)
        
        # Update visual selection state for all badges
        for character_id in self.character_badges.keys():
            self._update_selection_state(character_id)
    
    def clear_selection(self) -> None:
        """Clear all selections (multi-select mode only)."""
        if not self.multi_select:
            return
        
        # Clear the selected IDs set
        self.selected_character_ids.clear()
        
        # Update visual selection state for all badges
        for character_id in self.character_badges.keys():
            self._update_selection_state(character_id)
    
    def get_selected_character_ids(self) -> List[int]:
        """Get IDs of selected characters.
        
        Returns:
            List of selected character IDs
        """
        return list(self.selected_character_ids)
    
    def get_selected_characters(self) -> List[Dict[str, Any]]:
        """Get data for selected characters.
        
        Returns:
            List of selected character dictionaries
        """
        selected_characters = []
        for character_id in self.selected_character_ids:
            character_data = self._get_character_data(character_id)
            if character_data:
                selected_characters.append(character_data)
        return selected_characters


# Example usage
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow
    
    # Sample character data
    sample_characters = [
        {
            "id": 1,
            "name": "John Doe",
            "is_main_character": True,
            "avatar_path": None,
        },
        {
            "id": 2,
            "name": "Jane Smith",
            "is_main_character": False,
            "avatar_path": None,
        },
        {
            "id": 3,
            "name": "Robert Johnson",
            "is_main_character": False,
            "avatar_path": None,
        }
    ]
    
    # Create app
    app = QApplication(sys.argv)
    
    # Create window
    window = QMainWindow()
    window.setWindowTitle("Character Picker Example")
    window.resize(400, 300)
    
    # Create character picker
    picker = CharacterPicker(
        characters=sample_characters,
        multi_select=True,
        show_filter=True
    )
    
    # Set as central widget
    window.setCentralWidget(picker)
    
    # Show window
    window.show()
    
    # Run app
    sys.exit(app.exec()) 