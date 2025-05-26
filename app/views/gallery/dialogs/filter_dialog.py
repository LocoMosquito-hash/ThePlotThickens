#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gallery Filter Dialog for The Plot Thickens application.

This module contains the dialog for filtering gallery images by characters.
"""

from typing import List, Dict, Any, Optional, Tuple

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTabWidget, QGroupBox, QWidget,
    QLineEdit
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QIcon

from app.views.gallery.character.widgets import (
    GalleryFilterCharacterListWidget,
    FilterCharacterListWidget
)

from app.db_sqlite import (
    get_story_characters,
    get_character_image_counts_by_story,
    get_all_image_contexts,
    search_image_contexts
)


class GalleryFilterDialog(QDialog):
    """Dialog for filtering gallery images."""
    
    def __init__(self, db_conn, story_id: int, parent=None):
        """Initialize the gallery filter dialog.
        
        Args:
            db_conn: Database connection
            story_id: ID of the story
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.story_id = story_id
        
        # Character filters (character_id, include)
        self.character_filters = []
        
        # Context filters (context_id, include)
        self.context_filters = []
        
        self.setWindowTitle("Gallery Filters")
        self.resize(600, 400)
        
        self.init_ui()
        self.load_characters()
        self.load_contexts()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Tabs for different filter types
        tabs = QTabWidget()
        
        # Character filters tab
        character_tab = QWidget()
        character_layout = QVBoxLayout(character_tab)
        
        # Create a horizontal layout for the two groups
        side_by_side_layout = QHBoxLayout()
        
        # Character selection group
        character_group = QGroupBox("Characters")
        character_group_layout = QVBoxLayout(character_group)
        
        # Character list (scrollable)
        self.character_list = GalleryFilterCharacterListWidget(self.db_conn, self)
        character_group_layout.addWidget(self.character_list)
        
        # Include/exclude buttons
        button_layout = QHBoxLayout()
        
        self.include_btn = QPushButton("Include Selected")
        self.include_btn.clicked.connect(lambda: self.add_character_filter(self.character_list.get_selected_character(), True))
        button_layout.addWidget(self.include_btn)
        
        self.exclude_btn = QPushButton("Exclude Selected")
        self.exclude_btn.clicked.connect(lambda: self.add_character_filter(self.character_list.get_selected_character(), False))
        button_layout.addWidget(self.exclude_btn)
        
        character_group_layout.addLayout(button_layout)
        
        # Add character group to side-by-side layout
        side_by_side_layout.addWidget(character_group)
        
        # Active filters group
        filters_group = QGroupBox("Active Filters")
        filters_group_layout = QVBoxLayout(filters_group)
        
        # Filter list
        self.filter_list = FilterCharacterListWidget(self.db_conn, self)
        filters_group_layout.addWidget(self.filter_list)
        
        # Remove filter button
        remove_btn = QPushButton("Remove Selected Filters")
        remove_btn.clicked.connect(self.remove_selected_filters)
        filters_group_layout.addWidget(remove_btn)
        
        # Add filters group to side-by-side layout
        side_by_side_layout.addWidget(filters_group)
        
        # Add the side-by-side layout to the character layout
        character_layout.addLayout(side_by_side_layout)
        
        # Add a separator and context filters section
        character_layout.addWidget(QLabel())  # Spacer
        
        # Context filters section
        context_group = QGroupBox("Image Contexts")
        context_layout = QVBoxLayout(context_group)
        
        # Search box for contexts
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.context_search = QLineEdit()
        self.context_search.setPlaceholderText("Type to search contexts...")
        self.context_search.textChanged.connect(self.filter_contexts)
        search_layout.addWidget(self.context_search)
        context_layout.addLayout(search_layout)
        
        # Context list
        self.context_list = QListWidget()
        self.context_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        context_layout.addWidget(self.context_list)
        
        # Include/exclude buttons for contexts
        context_button_layout = QHBoxLayout()
        
        self.context_include_btn = QPushButton("Include Selected")
        self.context_include_btn.clicked.connect(lambda: self.add_context_filter(self.get_selected_context(), True))
        context_button_layout.addWidget(self.context_include_btn)
        
        self.context_exclude_btn = QPushButton("Exclude Selected")
        self.context_exclude_btn.clicked.connect(lambda: self.add_context_filter(self.get_selected_context(), False))
        context_button_layout.addWidget(self.context_exclude_btn)
        
        context_layout.addLayout(context_button_layout)
        
        character_layout.addWidget(context_group)
        
        tabs.addTab(character_tab, "Filters")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply Filters")
        apply_btn.clicked.connect(self.accept)
        button_layout.addWidget(apply_btn)
        
        layout.addLayout(button_layout)
    
    def load_characters(self):
        """Load characters for the filter list."""
        # Get characters from database
        characters = get_story_characters(self.db_conn, self.story_id)
        
        # Get image counts for each character
        image_counts = get_character_image_counts_by_story(self.db_conn, self.story_id)
        
        # Set characters in the list widget with image counts
        self.character_list.load_characters(characters, image_counts)
        
        # Create a map of characters by ID for quick lookup
        self.characters_by_id = {character["id"]: character for character in characters}
        
        # Populate the filter list with existing filters
        self.populate_filter_list()
    
    def load_contexts(self):
        """Load contexts for the filter list."""
        # Get all contexts from database
        self.all_contexts = get_all_image_contexts(self.db_conn)
        
        # Create a map of contexts by ID for quick lookup
        self.contexts_by_id = {context["id"]: context for context in self.all_contexts}
        
        # Initially show all contexts
        self.display_contexts(self.all_contexts)
    
    def display_contexts(self, contexts):
        """Display contexts in the list widget.
        
        Args:
            contexts: List of context dictionaries to display
        """
        self.context_list.clear()
        for context in contexts:
            item = QListWidgetItem(context["name"])
            item.setData(Qt.ItemDataRole.UserRole, context)
            self.context_list.addItem(item)
    
    def filter_contexts(self):
        """Filter contexts based on search text."""
        search_text = self.context_search.text().strip()
        
        if not search_text:
            # Show all contexts if search is empty
            self.display_contexts(self.all_contexts)
        else:
            # Filter contexts by search text (case-insensitive partial matching)
            filtered_contexts = [
                context for context in self.all_contexts
                if search_text.lower() in context["name"].lower()
            ]
            self.display_contexts(filtered_contexts)
    
    def get_selected_context(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected context.
        
        Returns:
            Context data dictionary or None if no context is selected
        """
        selected_items = self.context_list.selectedItems()
        if selected_items:
            return selected_items[0].data(Qt.ItemDataRole.UserRole)
        return None
    
    def populate_filter_list(self) -> None:
        """Populate the filter list with current filters."""
        # Clear the filter list first
        self.filter_list.clear()
        
        # Add each active character filter to the list (without modifying self.character_filters)
        for character_id, include in self.character_filters:
            character = self.characters_by_id.get(character_id)
            if character:
                self._add_character_filter_to_ui_only(character, include)
        
        # Add each active context filter to the list (without modifying self.context_filters)
        for context_id, include in self.context_filters:
            context = self.contexts_by_id.get(context_id)
            if context:
                self._add_context_filter_to_ui_only(context, include)
    
    def add_character_filter(self, character: Dict[str, Any], include: bool):
        """Add a character filter.
        
        Args:
            character: Character data
            include: Whether to include or exclude images with this character
        """
        if not character:
            return
        
        character_id = character["id"]
        
        # Check if this character is already in the character_filters list
        for i, (char_id, inc) in enumerate(self.character_filters):
            if char_id == character_id:
                # Update existing filter
                self.character_filters[i] = (char_id, include)
                self._update_filter_in_ui(character, include)
                return
        
        # Add new filter to the list
        self.character_filters.append((character_id, include))
        self._add_character_filter_to_ui_only(character, include)
    
    def _add_character_filter_to_ui_only(self, character: Dict[str, Any], include: bool):
        """Add a filter to the UI only (without modifying character_filters list).
        
        Args:
            character: Character data
            include: Whether to include or exclude images with this character
        """
        # Create a new filter item with "Character:" prefix
        item_text = f"Character: {character['name']} - {'Include' if include else 'Exclude'}"
        item = QListWidgetItem(item_text)
        
        # Store character data
        item.setData(Qt.ItemDataRole.UserRole, {
            "type": "character",
            "character_id": character["id"],
            "character_name": character["name"],
            "include": include
        })
        
        # Set icon
        icon = QIcon("resources/icons/include.png" if include else "resources/icons/exclude.png")
        if icon.isNull():
            # Fallback icon text
            icon_text = "✓" if include else "✗"
            item_text = f"{icon_text} Character: {character['name']}"
            item.setText(item_text)
        else:
            item.setIcon(icon)
        
        # Add to list
        self.filter_list.addItem(item)
    
    def add_context_filter(self, context: Dict[str, Any], include: bool):
        """Add a context filter.
        
        Args:
            context: Context data
            include: Whether to include or exclude images with this context
        """
        if not context:
            return
        
        context_id = context["id"]
        
        # Check if this context is already in the context_filters list
        for i, (ctx_id, inc) in enumerate(self.context_filters):
            if ctx_id == context_id:
                # Update existing filter
                self.context_filters[i] = (ctx_id, include)
                self._update_context_filter_in_ui(context, include)
                return
        
        # Add new filter to the list
        self.context_filters.append((context_id, include))
        self._add_context_filter_to_ui_only(context, include)
    
    def _add_context_filter_to_ui_only(self, context: Dict[str, Any], include: bool):
        """Add a context filter to the UI only (without modifying context_filters list).
        
        Args:
            context: Context data
            include: Whether to include or exclude images with this context
        """
        # Create a new filter item with "Context:" prefix
        item_text = f"Context: {context['name']} - {'Include' if include else 'Exclude'}"
        item = QListWidgetItem(item_text)
        
        # Store context data
        item.setData(Qt.ItemDataRole.UserRole, {
            "type": "context",
            "context_id": context["id"],
            "context_name": context["name"],
            "include": include
        })
        
        # Set icon
        icon = QIcon("resources/icons/include.png" if include else "resources/icons/exclude.png")
        if icon.isNull():
            # Fallback icon text
            icon_text = "✓" if include else "✗"
            item_text = f"{icon_text} Context: {context['name']}"
            item.setText(item_text)
        else:
            item.setIcon(icon)
        
        # Add to list
        self.filter_list.addItem(item)
    
    def _update_filter_in_ui(self, character: Dict[str, Any], include: bool):
        """Update an existing filter in the UI.
        
        Args:
            character: Character data
            include: Whether to include or exclude images with this character
        """
        # Find and update the existing item
        for i in range(self.filter_list.count()):
            item = self.filter_list.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            
            if data["character_id"] == character["id"]:
                # Update the filter data
                data["include"] = include
                item.setData(Qt.ItemDataRole.UserRole, data)
                
                # Update the item text
                item_text = f"Character: {character['name']} - {'Include' if include else 'Exclude'}"
                item.setText(item_text)
                
                # Update the item icon
                icon = QIcon("resources/icons/include.png" if include else "resources/icons/exclude.png")
                if icon.isNull():
                    # Fallback icon text
                    icon_text = "✓" if include else "✗"
                    item_text = f"{icon_text} Character: {character['name']}"
                    item.setText(item_text)
                else:
                    item.setIcon(icon)
                
                break
    
    def _update_context_filter_in_ui(self, context: Dict[str, Any], include: bool):
        """Update an existing context filter in the UI.
        
        Args:
            context: Context data
            include: Whether to include or exclude images with this context
        """
        # Find and update the existing item
        for i in range(self.filter_list.count()):
            item = self.filter_list.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            
            if data.get("type") == "context" and data["context_id"] == context["id"]:
                # Update the filter data
                data["include"] = include
                item.setData(Qt.ItemDataRole.UserRole, data)
                
                # Update the item text
                item_text = f"Context: {context['name']} - {'Include' if include else 'Exclude'}"
                item.setText(item_text)
                
                # Update the item icon
                icon = QIcon("resources/icons/include.png" if include else "resources/icons/exclude.png")
                if icon.isNull():
                    # Fallback icon text
                    icon_text = "✓" if include else "✗"
                    item_text = f"{icon_text} Context: {context['name']}"
                    item.setText(item_text)
                else:
                    item.setIcon(icon)
                
                break
    
    def remove_selected_filters(self):
        """Remove selected filters from the list."""
        selected_items = self.filter_list.selectedItems()
        
        # Collect IDs to remove
        character_ids_to_remove = []
        context_ids_to_remove = []
        
        for item in selected_items:
            data = item.data(Qt.ItemDataRole.UserRole)
            
            if data.get("type") == "character":
                character_ids_to_remove.append(data["character_id"])
            elif data.get("type") == "context":
                context_ids_to_remove.append(data["context_id"])
            
            # Remove from the list widget
            self.filter_list.takeItem(self.filter_list.row(item))
        
        # Remove from the character filters list (iterate backwards to avoid index issues)
        for i in range(len(self.character_filters) - 1, -1, -1):
            char_id, include = self.character_filters[i]
            if char_id in character_ids_to_remove:
                self.character_filters.pop(i)
        
        # Remove from the context filters list (iterate backwards to avoid index issues)
        for i in range(len(self.context_filters) - 1, -1, -1):
            ctx_id, include = self.context_filters[i]
            if ctx_id in context_ids_to_remove:
                self.context_filters.pop(i)
    
    def get_character_filters(self) -> List[Tuple[int, bool]]:
        """Get the character filters.
        
        Returns:
            List of tuples (character_id, include)
        """
        return self.character_filters
    
    def get_context_filters(self) -> List[Tuple[int, bool]]:
        """Get the context filters.
        
        Returns:
            List of tuples (context_id, include)
        """
        return self.context_filters
        
    def clear_all_filters(self) -> None:
        """Clear all filters."""
        self.filter_list.clear()
        self.character_filters.clear()
        self.context_filters.clear()
