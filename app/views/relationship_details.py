#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Relationship Details Dialog for The Plot Thickens application.

This module provides a dialog for viewing and editing relationships between characters.
"""

import os
from typing import Optional, Dict, Any, List, Tuple, Set

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QLineEdit, QListWidget, QListWidgetItem,
    QComboBox, QCompleter, QSizePolicy, QWidget, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QCheckBox,
    QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPoint
from PyQt6.QtGui import QPixmap, QIcon, QColor, QPainter, QPen, QAction

# Removed the deprecated import
# from app.db_sqlite import get_relationship_types, get_used_relationship_types


class SearchableComboBox(QComboBox):
    """A ComboBox with search functionality and category support."""
    
    def __init__(self, parent=None):
        """Initialize the searchable combo box.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Make editable to allow searching
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        
        # Enable autocomplete
        self.completer = QCompleter(self.model() or [])
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.setCompleter(self.completer)
        
        # Style the combo box
        self.setMinimumHeight(30)
        
        # Store category info and gender contexts
        self._categories = {}  # Maps item index to category ID
        self._gender_contexts = {}  # Maps item index to gender context
        self._suggested_indices = set()  # Set of indices for suggested items
        self._visible_indices = set()  # Set of currently visible indices
        
    def addCategoryItem(self, category_name: str, category_id: int) -> None:
        """Add a category header item to the combo box.
        
        Args:
            category_name: Name of the category
            category_id: ID of the category
        """
        index = self.count()
        # Add a symbol and make the category name more distinct
        self.addItem(f"▼ {category_name}")
        
        # Guard against None model
        model = self.model()
        if model is None:
            print("Warning: ComboBox model is None")
            return
            
        item = model.item(index)
        if item is None:
            print(f"Warning: Item at index {index} is None")
            return
            
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)  # Make non-selectable
        item.setBackground(QColor("#9932CC"))  # Purple background for categories
        item.setForeground(QColor("#FFFFFF"))  # White text
        
        # Set bold font for categories
        font = item.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 1)  # Make font slightly larger
        item.setFont(font)
        
        # Store category info
        self._categories[index] = category_id
        self._visible_indices.add(index)  # Categories are always visible
        
    def addRelationshipTypeItem(self, label: str, type_id: int, gender_context: str, suggested: bool = False) -> None:
        """Add a relationship type item to the combo box.
        
        Args:
            label: Display label for the relationship type
            type_id: ID of the relationship type
            gender_context: Gender context (masculine, feminine, neutral)
            suggested: Whether this is a suggested relationship type
        """
        index = self.count()
        # Add indentation to relationship types to visually separate from categories
        self.addItem(f"    {label}")
        
        # Set type ID as user data
        self.setItemData(index, type_id, Qt.ItemDataRole.UserRole)
        
        # Get model item for styling
        model = self.model()
        if model is None:
            print("Warning: ComboBox model is None")
            return
            
        item = model.item(index)
        if item is None:
            print(f"Warning: Item at index {index} is None")
            return
            
        # Store gender context
        self._gender_contexts[index] = gender_context
        self._visible_indices.add(index)  # Initially all items are visible
        
        # If this is a suggested relationship, highlight it
        if suggested:
            item.setBackground(QColor("#4682B4"))  # Steel blue background for suggestions
            item.setForeground(QColor("#FFFFFF"))  # White text
            self._suggested_indices.add(index)
            
    def filterByGender(self, gender: str) -> None:
        """Filter relationship types by gender context.
        
        Args:
            gender: Gender to filter by (MALE, FEMALE, or None for no filter)
        """
        # Map gender to gender context
        gender_context_filter = None
        if gender == "MALE":
            gender_context_filter = "masculine"
        elif gender == "FEMALE":
            gender_context_filter = "feminine"
            
        # We'll rebuild the combo box with only the filtered items
        current_text = self.currentText()
        self._visible_indices.clear()
        
        # Store all items temporarily
        items_to_keep = []
        
        for i in range(self.count()):
            if i in self._categories:
                # Always show categories
                items_to_keep.append((i, self.itemText(i), self.itemData(i, Qt.ItemDataRole.UserRole)))
                self._visible_indices.add(i)
            elif i in self._gender_contexts:
                gender_context = self._gender_contexts[i]
                
                # Show if:
                # 1. No filter is applied
                # 2. It matches the filter
                # 3. It's neutral (always shown)
                should_show = (
                    gender_context_filter is None or 
                    gender_context == gender_context_filter or 
                    gender_context == "neutral"
                )
                
                if should_show:
                    items_to_keep.append((i, self.itemText(i), self.itemData(i, Qt.ItemDataRole.UserRole)))
                    self._visible_indices.add(i)
        
        # Remember current selection
        current_type_id = self.getSelectedTypeId()
        
        # Clear and rebuild
        self.clear()
        
        # We need to maintain mapping from old indices to new ones 
        old_to_new_index = {}
        new_index = 0
        
        # Rebuild categories and items
        current_category = None
        for old_index, text, user_data in items_to_keep:
            # Add the item
            self.addItem(text)
            
            # If this was a category header, restore its styling
            if old_index in self._categories:
                current_category = self._categories[old_index]
                
                # Style as category
                model = self.model()
                if model and model.item(new_index):
                    item = model.item(new_index)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                    item.setBackground(QColor("#9932CC"))
                    item.setForeground(QColor("#FFFFFF"))
                    
                    # Restore bold font for categories
                    font = item.font()
                    font.setBold(True)
                    font.setPointSize(font.pointSize() + 1)
                    item.setFont(font)
                    
                # Update category mapping
                self._categories[new_index] = current_category
                if old_index != new_index:
                    del self._categories[old_index]
            else:
                # Set the user data (type_id)
                self.setItemData(new_index, user_data, Qt.ItemDataRole.UserRole)
                
                # Update gender context mapping
                if old_index in self._gender_contexts:
                    self._gender_contexts[new_index] = self._gender_contexts[old_index]
                    if old_index != new_index:
                        del self._gender_contexts[old_index]
                        
                # Update suggestion styling if needed
                if old_index in self._suggested_indices:
                    self._suggested_indices.remove(old_index)
                    self._suggested_indices.add(new_index)
                    
                    model = self.model()
                    if model and model.item(new_index):
                        item = model.item(new_index)
                        item.setBackground(QColor("#2E8B57"))  # Sea Green
                        item.setForeground(QColor("#FFFFFF"))  # White text
                        
                        # Make the font bold
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)
            
            # Map old index to new
            old_to_new_index[old_index] = new_index
            new_index += 1
                
        # Try to restore selection
        if current_type_id is not None:
            for i in range(self.count()):
                if self.itemData(i, Qt.ItemDataRole.UserRole) == current_type_id:
                    self.setCurrentIndex(i)
                    break
        else:
            # Otherwise try to restore by text
            index = self.findText(current_text)
            if index >= 0:
                self.setCurrentIndex(index)
    
    def clearSuggestions(self) -> None:
        """Clear suggestion highlighting from all items."""
        print(f"Clearing {len(self._suggested_indices)} suggestions")
        for index in self._suggested_indices:
            # Make sure index is valid and visible now
            if index < self.count():
                model = self.model()
                if model:
                    item = model.item(index)
                    if item:
                        item.setBackground(QColor())  # Reset background
                        item.setForeground(QColor())  # Reset foreground
                        
                        # Reset font (remove bold)
                        font = item.font()
                        font.setBold(False)
                        item.setFont(font)
        
        self._suggested_indices.clear()
    
    def highlightSuggestions(self, type_ids: List[int]) -> None:
        """Highlight the suggested relationship types.
        
        Args:
            type_ids: List of relationship type IDs to highlight
        """
        # Clear previous suggestions
        self.clearSuggestions()
        
        # Find and highlight new suggestions
        for i in range(self.count()):
            type_id = self.itemData(i, Qt.ItemDataRole.UserRole)
            if type_id in type_ids:
                item = self.model().item(i)
                # Make suggested items more visually distinct with a stronger styling
                item.setBackground(QColor("#2E8B57"))  # Sea Green - more noticeable
                item.setForeground(QColor("#FFFFFF"))  # White text
                
                # Make the font bold to stand out more
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                
                # Store the index as a suggestion
                self._suggested_indices.add(i)
                
                print(f"Highlighted suggestion: {self.itemText(i)} (type_id: {type_id})")
                
    def getSelectedTypeId(self) -> Optional[int]:
        """Get the selected relationship type ID.
        
        Returns:
            Relationship type ID or None if no selection or a category is selected
        """
        if self.currentIndex() == -1:
            return None
            
        return self.currentData(Qt.ItemDataRole.UserRole)


class RelationshipCard(QFrame):
    """A card displaying a relationship between two characters."""
    
    def __init__(self, source_id: int, source_name: str, target_id: int, 
                 target_name: str, source_avatar: Optional[str] = None, 
                 target_avatar: Optional[str] = None, is_forward: bool = True, 
                 source_gender: str = "NOT_SPECIFIED", target_gender: str = "NOT_SPECIFIED",
                 parent=None):
        """Initialize the relationship card.
        
        Args:
            source_id: ID of the source character
            source_name: Name of the source character
            target_id: ID of the target character
            target_name: Name of the target character
            source_avatar: Path to the source character's avatar
            target_avatar: Path to the target character's avatar
            is_forward: If True, displays source -> target; if False, displays target -> source
            source_gender: Gender of the source character
            target_gender: Gender of the target character
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.source_id = source_id
        self.source_name = source_name
        self.target_id = target_id
        self.target_name = target_name
        self.source_avatar = source_avatar
        self.target_avatar = target_avatar
        self.is_forward = is_forward
        self.source_gender = source_gender
        self.target_gender = target_gender
        self._is_enabled = True
        
        # Set up the frame style
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setStyleSheet("""
            RelationshipCard {
                border-radius: 6px;
                padding: 8px;
            }
        """)
        
        self._init_ui()
    
    def setEnabled(self, enabled: bool) -> None:
        """Enable or disable the card.
        
        Args:
            enabled: Whether the card should be enabled
        """
        self._is_enabled = enabled
        super().setEnabled(enabled)
        
        # Update visual appearance
        if enabled:
            self.setStyleSheet("""
                RelationshipCard {
                    border-radius: 6px;
                    padding: 8px;
                }
            """)
        else:
            self.setStyleSheet("""
                RelationshipCard {
                    border-radius: 6px;
                    padding: 8px;
                    background-color: rgba(30, 30, 30, 180);
                }
            """)
        
        # Also enable/disable the combo box
        if hasattr(self, 'relationship_combo'):
            self.relationship_combo.setEnabled(enabled)
    
    def _init_ui(self) -> None:
        """Initialize the user interface."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)
        
        # Create left side with label and avatars
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        
        # Create label with relationship text
        if self.is_forward:
            label_text = f"{self.source_name} is {self.target_name}'s:"
        else:
            label_text = f"{self.target_name} is {self.source_name}'s:"
        
        relationship_label = QLabel(label_text)
        relationship_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(relationship_label)
        
        # Create avatars container with arrow
        avatars_widget = QWidget()
        avatars_layout = QHBoxLayout(avatars_widget)
        avatars_layout.setContentsMargins(0, 0, 0, 0)
        avatars_layout.setSpacing(10)
        
        # Add avatars and arrow in the correct order
        first_avatar = self._create_avatar(self.source_avatar if self.is_forward else self.target_avatar)
        arrow_label = self._create_arrow()
        second_avatar = self._create_avatar(self.target_avatar if self.is_forward else self.source_avatar)
        
        avatars_layout.addWidget(first_avatar)
        avatars_layout.addWidget(arrow_label)
        avatars_layout.addWidget(second_avatar)
        
        left_layout.addWidget(avatars_widget)
        main_layout.addWidget(left_widget)
        
        # Create right side with searchable combobox
        self.relationship_combo = SearchableComboBox()
        
        # Apply filtering based on gender (will be populated later)
        if self.is_forward:
            gender_for_filtering = self.source_gender
        else:
            gender_for_filtering = self.target_gender
            
        # For the reverse relationship, we show suggestions based on the selected forward relationship
        main_layout.addWidget(self.relationship_combo)
    
    def _create_avatar(self, avatar_path: Optional[str] = None) -> QLabel:
        """Create an avatar label with the character's image.
        
        Args:
            avatar_path: Path to the avatar image
            
        Returns:
            QLabel with the avatar image
        """
        avatar_label = QLabel()
        avatar_label.setFixedSize(64, 64)
        avatar_label.setScaledContents(True)
        
        if avatar_path and os.path.exists(avatar_path):
            pixmap = QPixmap(avatar_path)
        else:
            # Use a default avatar if no avatar is available
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.GlobalColor.lightGray)
        
        avatar_label.setPixmap(pixmap)
        
        # Add a border to the avatar
        avatar_label.setStyleSheet("""
            QLabel {
                border: 1px solid #777777;
                background-color: #333333;
            }
        """)
        
        return avatar_label
    
    def _create_arrow(self) -> QLabel:
        """Create an arrow label pointing from source to target.
        
        Returns:
            QLabel with the arrow image
        """
        arrow_label = QLabel()
        arrow_label.setFixedSize(32, 32)
        
        # Create a pixmap for the arrow
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        # Draw the arrow
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pen = QPen(QColor("#FF0000"))
        pen.setWidth(2)
        painter.setPen(pen)
        
        # Draw arrow line
        painter.drawLine(5, 16, 27, 16)
        
        # Draw arrow head
        painter.drawLine(20, 8, 27, 16)
        painter.drawLine(20, 24, 27, 16)
        
        painter.end()
        
        arrow_label.setPixmap(pixmap)
        return arrow_label
    
    def get_selected_relationship(self) -> Optional[str]:
        """Get the selected relationship type label.
        
        Returns:
            Selected relationship type label or None if none selected
        """
        if self.relationship_combo.currentIndex() == -1:
            return None
            
        return self.relationship_combo.currentText()
        
    def get_selected_relationship_type_id(self) -> Optional[int]:
        """Get the selected relationship type ID.
        
        Returns:
            Selected relationship type ID or None if none selected
        """
        return self.relationship_combo.getSelectedTypeId()
        
    def filterByGender(self, gender: str) -> None:
        """Filter relationship types by gender.
        
        Args:
            gender: Gender to filter by (MALE, FEMALE, or None for no filter)
        """
        self.relationship_combo.filterByGender(gender)
        
    def highlightSuggestions(self, type_ids: List[int]) -> None:
        """Highlight suggested relationship types.
        
        Args:
            type_ids: List of relationship type IDs to highlight as suggestions
        """
        self.relationship_combo.highlightSuggestions(type_ids)


class RelationshipDetailsDialog(QDialog):
    """Dialog for editing relationship details between characters."""
    
    def __init__(self, db_conn, source_id: int, source_name: str, target_id: int, 
                 target_name: str, parent=None):
        """Initialize the relationship details dialog.
        
        Args:
            db_conn: Database connection
            source_id: ID of the source character
            source_name: Name of the source character
            target_id: ID of the target character
            target_name: Name of the target character
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.db_conn = db_conn
        self.source_id = source_id
        self.source_name = source_name
        self.target_id = target_id
        self.target_name = target_name
        
        # Initialize operations queue for batch processing
        self.pending_operations = []  # List of operations to execute on Apply
        # Each operation will be a dict with 'type' and necessary data
        # Types: 'add', 'edit', 'delete'
        
        # Edit mode state management
        self.is_edit_mode = False
        self.editing_relationship_data = None  # Store data of relationship being edited
        
        # Apply dark theme if available
        try:
            import qdarktheme
            qdarktheme.setup_theme()
        except ImportError:
            print("PyQtDarkTheme not available. Using default theme.")
        
        # Get avatar paths and genders from the database
        self.source_avatar = self._get_character_avatar_path(source_id)
        self.target_avatar = self._get_character_avatar_path(target_id)
        self.source_gender = self._get_character_gender(source_id)
        self.target_gender = self._get_character_gender(target_id)
        
        # Set up the dialog
        self.setWindowTitle("Relationship Details")
        self.resize(600, 500)
        
        self._init_ui()
        
        # Initially disable the backward card and Add Relationship button
        self.backward_card.setEnabled(False)
        self._update_add_relationship_button_state()
        
        # Connect the forward card combo box's currentTextChanged signal
        self.forward_card.relationship_combo.currentIndexChanged.connect(self._on_forward_relationship_changed)
    
    def _get_character_avatar_path(self, character_id: int) -> Optional[str]:
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
            
            # Try characters.avatar_path first (most likely location)
            cursor.execute("""
                SELECT avatar_path 
                FROM characters 
                WHERE id = ?
            """, (character_id,))
            
            result = cursor.fetchone()
            if result and result[0]:
                avatar_path = result[0]
                if os.path.exists(avatar_path):
                    return avatar_path
                    
            # If not found or doesn't exist, try character_details.avatar_path
            cursor.execute("""
                SELECT avatar_path 
                FROM character_details 
                WHERE character_id = ?
            """, (character_id,))
            
            result = cursor.fetchone()
            if result and result[0]:
                avatar_path = result[0]
                if os.path.exists(avatar_path):
                    return avatar_path
            
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
                                return location
                
        except Exception as e:
            print(f"Error getting character avatar: {e}")
            
        return None
        
    def _get_character_gender(self, character_id: int) -> str:
        """Get the gender of a character.
        
        Args:
            character_id: ID of the character
            
        Returns:
            Gender of the character as a string, or "NOT_SPECIFIED" if not found
        """
        if not character_id:
            return "NOT_SPECIFIED"
            
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT gender FROM characters WHERE id = ?", (character_id,))
            result = cursor.fetchone()
            
            if result and result[0]:
                return result[0]
        except Exception as e:
            print(f"Error getting character gender: {e}")
            
        return "NOT_SPECIFIED"
    
    def _init_ui(self) -> None:
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)
        
        try:
            # Load relationship categories and types
            self.categories = self._load_relationship_categories()
            self.relationship_types = self._load_relationship_types()
            
            # Add existing relationships section
            existing_label = QLabel(f"Existing relationships between {self.source_name} and {self.target_name}:")
            existing_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            main_layout.addWidget(existing_label)
            
            # Create and add the existing relationships table
            self.existing_relationships_table = self._create_existing_relationships_table()
            main_layout.addWidget(self.existing_relationships_table)
            
            # Add Edit Relationship button below the table
            edit_button_layout = QHBoxLayout()
            edit_button_layout.setContentsMargins(0, 5, 0, 5)
            
            self.edit_relationship_button = QPushButton("Edit Relationship")
            self.edit_relationship_button.setToolTip("Edit the selected relationship from the list above")
            self.edit_relationship_button.clicked.connect(self._edit_selected_relationship)
            self.edit_relationship_button.setEnabled(False)  # Initially disabled
            edit_button_layout.addWidget(self.edit_relationship_button)
            edit_button_layout.addStretch()  # Push button to the left
            
            main_layout.addLayout(edit_button_layout)
            
            # Add some spacing
            main_layout.addSpacing(10)
            
            # Add a separator line
            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setFrameShadow(QFrame.Shadow.Sunken)
            main_layout.addWidget(separator)
            
            # Create the forward relationship card (A -> B)
            self.forward_card = RelationshipCard(
                self.source_id, self.source_name, 
                self.target_id, self.target_name,
                self.source_avatar, self.target_avatar,
                True, self.source_gender, self.target_gender
            )
            main_layout.addWidget(self.forward_card)
            
            # Create the backward relationship card (B -> A)
            self.backward_card = RelationshipCard(
                self.source_id, self.source_name, 
                self.target_id, self.target_name,
                self.source_avatar, self.target_avatar,
                False, self.target_gender, self.source_gender
            )
            main_layout.addWidget(self.backward_card)
            
            # Populate relationship type dropdowns
            self._populate_relationship_combos()
            
            # Apply gender-based filtering
            self.forward_card.filterByGender(self.source_gender)
            self.backward_card.filterByGender(self.target_gender)
            
        except Exception as e:
            print(f"Error initializing UI: {e}")
            error_label = QLabel(f"Error loading relationship data: {str(e)}")
            error_label.setStyleSheet("color: red;")
            main_layout.addWidget(error_label)
        
        # Add some spacing after the relationship cards
        main_layout.addSpacing(16)
        
        # Add primary relationship checkbox BEFORE the action buttons
        primary_checkbox_layout = QHBoxLayout()
        primary_checkbox_layout.setContentsMargins(0, 0, 0, 10)
        
        self.primary_relationship_checkbox = QCheckBox("Mark as Primary Relationship")
        self.primary_relationship_checkbox.setToolTip(
            "Mark this relationship pair as the most defining relationship between these characters"
        )
        primary_checkbox_layout.addWidget(self.primary_relationship_checkbox)
        primary_checkbox_layout.addStretch()  # Push checkbox to the left
        
        main_layout.addLayout(primary_checkbox_layout)
        
        # Create action buttons layout (Reset and Add Relationship)
        action_buttons_layout = QHBoxLayout()
        action_buttons_layout.setContentsMargins(0, 0, 0, 0)
        action_buttons_layout.setSpacing(10)
        
        # Create Reset button
        self.reset_button = QPushButton("Reset")
        self.reset_button.setToolTip("Reset both relationship dropdowns to their initial blank state")
        self.reset_button.clicked.connect(self._reset_relationship_cards)
        action_buttons_layout.addWidget(self.reset_button)
        
        # Create Add Relationship button
        self.add_relationship_button = QPushButton("Add Relationship")
        self.add_relationship_button.setToolTip("Add the selected relationship(s) to the pending changes list")
        self.add_relationship_button.clicked.connect(self._add_or_save_relationship)
        self.add_relationship_button.setEnabled(False)  # Initially disabled
        action_buttons_layout.addWidget(self.add_relationship_button)
        
        # Add spacer to center the action buttons
        action_buttons_layout.addStretch()
        
        main_layout.addLayout(action_buttons_layout)
        
        # Add stretch to push everything up
        main_layout.addStretch()
        
        # Add horizontal separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(separator)
        
        # Add some spacing after separator
        main_layout.addSpacing(10)
        
        # Create buttons layout (Cancel and Apply)
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(10)
        
        # Add spacer to push buttons to the right
        buttons_layout.addStretch()
        
        # Create Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        # Create Apply button
        self.apply_button = QPushButton("Apply")
        self.apply_button.setToolTip("Execute all pending relationship changes and close the dialog")
        self.apply_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.apply_button)
        
        main_layout.addLayout(buttons_layout)
    
    def _load_relationship_categories(self) -> List[Dict[str, Any]]:
        """Load relationship categories from the database.
        
        Returns:
            List of relationship category dictionaries
        """
        try:
            cursor = self.db_conn.cursor()
            
            # First check if the table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='relationship_categories'
            """)
            
            if not cursor.fetchone():
                print("relationship_categories table doesn't exist")
                return []
            
            cursor.execute("""
                SELECT id, name, description, display_order 
                FROM relationship_categories 
                ORDER BY display_order
            """)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error loading relationship categories: {e}")
            return []
    
    def _load_relationship_types(self) -> List[Dict[str, Any]]:
        """Load relationship types from the database.
        
        Returns:
            List of relationship type dictionaries
        """
        try:
            cursor = self.db_conn.cursor()
            
            # First check if the table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='relationship_types_new'
            """)
            
            if not cursor.fetchone():
                print("relationship_types_new table doesn't exist")
                return []
            
            cursor.execute("""
                SELECT type_id, name, label, gender_context, category_id
                FROM relationship_types_new 
                ORDER BY category_id, name
            """)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error loading relationship types: {e}")
            return []
    
    def _get_inverse_relationship_types(self, type_id: int) -> List[int]:
        """Get inverse relationship type IDs for a given relationship type.
        
        Args:
            type_id: ID of the relationship type
            
        Returns:
            List of inverse relationship type IDs
        """
        if not type_id:
            print("No type_id provided to _get_inverse_relationship_types")
            return []
            
        try:
            cursor = self.db_conn.cursor()
            
            # First check if the table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='relationship_type_inverses'
            """)
            
            if not cursor.fetchone():
                print("relationship_type_inverses table doesn't exist")
                return []
            
            # For debugging, print all inverse relationships
            cursor.execute("SELECT type_id, inverse_type_id FROM relationship_type_inverses LIMIT 20")
            all_inverses = cursor.fetchall()
            print(f"First 20 inverse relationships: {all_inverses}")
            
            # Now get the specific ones
            cursor.execute("""
                SELECT inverse_type_id 
                FROM relationship_type_inverses 
                WHERE type_id = ?
            """, (type_id,))
            
            result = [row[0] for row in cursor.fetchall()]
            print(f"Found {len(result)} inverse relationship types for type_id {type_id}: {result}")
            
            return result
        except Exception as e:
            print(f"Error getting inverse relationship types: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _populate_relationship_combos(self) -> None:
        """Populate the relationship combo boxes with categorized relationship types."""
        # Group relationship types by category
        types_by_category = {}
        for rel_type in self.relationship_types:
            category_id = rel_type["category_id"]
            if category_id not in types_by_category:
                types_by_category[category_id] = []
            types_by_category[category_id].append(rel_type)
        
        # Populate both combo boxes with categorized relationships
        for combo in [self.forward_card.relationship_combo, self.backward_card.relationship_combo]:
            # Clear any existing items
            combo.clear()
            combo.setPlaceholderText("Select relationship type...")
            
            # Handle empty categories or types
            if not self.categories or not self.relationship_types:
                print("No relationship categories or types found")
                combo.addItem("No relationship types available")
                continue
            
            # Add each category with its relationship types
            for category in self.categories:
                category_id = category["id"]
                combo.addCategoryItem(category["name"], category_id)
                
                # Add relationship types for this category
                if category_id in types_by_category:
                    for rel_type in types_by_category[category_id]:
                        combo.addRelationshipTypeItem(
                            rel_type["label"],
                            rel_type["type_id"],
                            rel_type["gender_context"]
                        )
    
    def get_selected_relationships(self) -> Tuple[Optional[int], Optional[int]]:
        """Get the selected relationship type IDs.
        
        Returns:
            Tuple of (forward_relationship_id, backward_relationship_id)
        """
        forward_relationship_id = self.forward_card.get_selected_relationship_type_id()
        backward_relationship_id = self.backward_card.get_selected_relationship_type_id()
        
        return forward_relationship_id, backward_relationship_id
    
    def _on_forward_relationship_changed(self, index: int) -> None:
        """Handle when the forward relationship type selection changes.
        
        Args:
            index: Current index in the combo box
        """
        # Enable the backward card only if a valid relationship type is selected
        enable_backward = index != -1 and index is not None
        self.backward_card.setEnabled(enable_backward)
        
        # Update Add Relationship button state
        self._update_add_relationship_button_state()
        
        if enable_backward:
            # Get the selected relationship type ID
            forward_type_id = self.forward_card.get_selected_relationship_type_id()
            
            if forward_type_id is not None:
                print(f"Selected forward relationship type ID: {forward_type_id}")
                
                # Get suggested inverse relationship types
                inverse_type_ids = self._get_inverse_relationship_types(forward_type_id)
                print(f"Inverse relationship type IDs: {inverse_type_ids}")
                
                # Highlight the suggested inverse relationships
                self.backward_card.highlightSuggestions(inverse_type_ids)
                
                # Automatically select the first inverse relationship if any exist
                if inverse_type_ids:
                    combo = self.backward_card.relationship_combo
                    
                    # Find the first item in the combo box that matches an inverse relationship
                    for i in range(combo.count()):
                        type_id = combo.itemData(i, Qt.ItemDataRole.UserRole)
                        if type_id in inverse_type_ids:
                            combo.setCurrentIndex(i)
                            print(f"Auto-selected inverse relationship type ID: {type_id}")
                            break
            else:
                print("No valid relationship type ID selected")
                self.backward_card.highlightSuggestions([])
        else:
            # If no forward relationship is selected, clear any suggestions
            self.backward_card.highlightSuggestions([])
            
    def _update_add_relationship_button_state(self) -> None:
        """Update the state of the Add Relationship button based on selections."""
        forward_selected = self.forward_card.get_selected_relationship_type_id() is not None
        
        # Update button text based on edit mode
        if self.is_edit_mode:
            self.add_relationship_button.setText("Save Changes")
            self.add_relationship_button.setToolTip("Save the changes to the relationship being edited")
        else:
            self.add_relationship_button.setText("Add Relationship")
            self.add_relationship_button.setToolTip("Add the selected relationship(s) to the pending changes list")
        
        # Enable button if forward relationship is selected
        self.add_relationship_button.setEnabled(forward_selected)
    
    def _reset_relationship_cards(self) -> None:
        """Reset both relationship cards to their initial blank state."""
        # Clear selections in both combo boxes
        self.forward_card.relationship_combo.setCurrentIndex(-1)
        self.backward_card.relationship_combo.setCurrentIndex(-1)
        
        # Disable the backward card
        self.backward_card.setEnabled(False)
        
        # Exit edit mode and clear editing data
        self.is_edit_mode = False
        self.editing_relationship_data = None
        
        # Reset edit relationship button state
        self.edit_relationship_button.setEnabled(False)
        self.existing_relationships_table.clearSelection()
        
        # Reset primary checkbox
        self.primary_relationship_checkbox.setChecked(False)
        
        # Update Add Relationship button state
        self._update_add_relationship_button_state()
        
        print("Relationship cards reset to initial state")
    
    def _add_or_save_relationship(self) -> None:
        """Add a new relationship or save changes to an existing relationship."""
        if self.is_edit_mode:
            self._save_relationship_changes()
        else:
            self._add_relationship_to_queue()
    
    def _add_relationship_to_queue(self) -> None:
        """Add the currently selected relationship(s) to the pending operations queue."""
        # Get the selected relationship types
        forward_type_id, backward_type_id = self.get_selected_relationships()
        
        if forward_type_id is None:
            QMessageBox.warning(
                self,
                "No Relationship Selected",
                "Please select at least a forward relationship type before adding."
            )
            return
        
        # Create operation data
        operation = {
            'type': 'add',
            'forward_type_id': forward_type_id,
            'backward_type_id': backward_type_id,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'is_primary': self.primary_relationship_checkbox.isChecked(),
            'description': self._get_operation_description(forward_type_id, backward_type_id)
        }
        
        # Add to queue
        self.pending_operations.append(operation)
        
        # Show confirmation message
        QMessageBox.information(
            self,
            "Relationship Added",
            f"Relationship added to pending changes:\n{operation['description']}\n\n"
            f"Total pending operations: {len(self.pending_operations)}\n\n"
            "Click 'Apply' to save all changes to the database."
        )
        
        # Reset the cards for the next relationship
        self._reset_relationship_cards()
        
        print(f"Added relationship to queue: {operation['description']}")
    
    def _get_operation_description(self, forward_type_id: Optional[int], backward_type_id: Optional[int]) -> str:
        """Get a human-readable description of the operation.
        
        Args:
            forward_type_id: ID of the forward relationship type
            backward_type_id: ID of the backward relationship type
            
        Returns:
            Description string for the operation
        """
        forward_label = None
        backward_label = None
        
        # Find the labels for the relationship types
        for rel_type in self.relationship_types:
            if rel_type['type_id'] == forward_type_id:
                forward_label = rel_type['label']
            if rel_type['type_id'] == backward_type_id:
                backward_label = rel_type['label']
        
        if forward_label and backward_label:
            return f"{self.source_name} ({forward_label}) ↔ {self.target_name} ({backward_label})"
        elif forward_label:
            return f"{self.source_name} ({forward_label})"
        else:
            return f"Unknown relationship type (ID: {forward_type_id})"
    
    def save_relationships(self) -> None:
        """Execute all pending relationship operations from the queue.
        
        Processes the pending operations queue and executes all add, edit, and delete operations.
        """
        from app.relationships import create_relationship, create_relationship_pair
        
        if not self.pending_operations:
            print("No pending operations to execute")
            return
        
        # Validate primary relationships before executing
        if not self._validate_primary_relationships():
            return  # Validation failed, don't proceed
        
        try:
            print(f"Executing {len(self.pending_operations)} pending operations...")
            
            for i, operation in enumerate(self.pending_operations):
                print(f"Processing operation {i+1}/{len(self.pending_operations)}: {operation['type']}")
                
                if operation['type'] == 'add':
                    self._execute_add_operation(operation)
                elif operation['type'] == 'edit':
                    self._execute_edit_operation(operation)
                elif operation['type'] == 'delete':
                    # TODO: Implement delete operation
                    print(f"Delete operation not implemented yet: {operation}")
                else:
                    print(f"Unknown operation type: {operation['type']}")
            
            # Commit all changes to the database
            self.db_conn.commit()
            print("All pending operations executed successfully")
            
            # Clear the queue
            self.pending_operations.clear()
            
            # Refresh the existing relationships table
            self._refresh_existing_relationships_table()
            
        except Exception as e:
            print(f"Error executing pending operations: {e}")
            import traceback
            traceback.print_exc()
            
            # Rollback changes
            self.db_conn.rollback()
            
            # Show error message to the user
            QMessageBox.critical(
                self,
                "Error Executing Operations",
                f"An error occurred while executing pending operations: {str(e)}\n\n"
                "All changes have been rolled back."
            )
    
    def _validate_primary_relationships(self) -> bool:
        """Validate primary relationship constraints before executing operations.
        
        Returns:
            True if validation passes, False if validation fails
        """
        # Get current existing relationships
        existing_relationships = self._load_existing_relationships()
        
        # Count how many relationship pairs will exist after all operations
        # Start with existing pairs
        all_pairs = [rel for rel in existing_relationships if rel['type'] == 'pair']
        
        # Add new pairs from pending operations
        for operation in self.pending_operations:
            if operation['type'] == 'add':
                # This will create a new pair
                if operation.get('forward_type_id') and operation.get('backward_type_id'):
                    all_pairs.append({
                        'type': 'pair',
                        'description': operation['description'],
                        'is_primary': operation.get('is_primary', False),
                        'is_pending': True
                    })
                # Note: Single relationships are not considered pairs
        
        # Remove pairs that will be deleted/replaced by edit operations
        for operation in self.pending_operations:
            if operation['type'] == 'edit':
                rel_data = operation['relationship_data']
                # Remove the existing pair being edited
                all_pairs = [pair for pair in all_pairs if pair.get('primary_id') != rel_data['primary_id']]
                
                # Add the edited pair if it will be a pair
                if operation.get('new_forward_type_id') and operation.get('new_backward_type_id'):
                    all_pairs.append({
                        'type': 'pair',
                        'description': operation['description'],
                        'is_primary': operation.get('is_primary', False),
                        'is_pending': True
                    })
        
        # Check if we'll have multiple pairs
        if len(all_pairs) < 2:
            return True  # No validation needed for 0 or 1 pairs
        
        # Count primary relationships
        primary_count = sum(1 for pair in all_pairs if pair.get('is_primary', False))
        
        # Validation rules:
        # 1. Must have exactly one primary if there are 2+ pairs
        if primary_count == 0:
            # No primary set - show dialog to choose one
            return self._show_primary_selection_dialog(all_pairs)
        elif primary_count > 1:
            # Multiple primaries - this shouldn't happen but handle it
            QMessageBox.critical(
                self,
                "Multiple Primary Relationships",
                f"Multiple relationships are marked as primary ({primary_count}). "
                "Only one relationship pair can be marked as primary between two characters.\n\n"
                "Please review your changes and ensure only one relationship is marked as primary."
            )
            return False
        
        # Exactly one primary - validation passes
        return True
    
    def _show_primary_selection_dialog(self, all_pairs: List[Dict[str, Any]]) -> bool:
        """Show dialog to select which relationship should be primary.
        
        Args:
            all_pairs: List of all relationship pairs that will exist after operations
            
        Returns:
            True if user selected a primary, False if cancelled
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Primary Relationship")
        dialog.setModal(True)
        dialog.resize(500, 300)
        
        layout = QVBoxLayout(dialog)
        
        # Instruction label
        instruction = QLabel(
            "Multiple relationship pairs will exist between these characters.\n"
            "Please select which relationship should be marked as the primary (most defining) relationship:"
        )
        instruction.setWordWrap(True)
        layout.addWidget(instruction)
        
        # Radio button group
        button_group = QButtonGroup()
        radio_buttons = []
        
        for i, pair in enumerate(all_pairs):
            radio = QRadioButton(pair['description'])
            if pair.get('is_pending'):
                radio.setText(f"{pair['description']} (NEW)")
            
            button_group.addButton(radio, i)
            radio_buttons.append(radio)
            layout.addWidget(radio)
        
        # Set the first one as default
        if radio_buttons:
            radio_buttons[0].setChecked(True)
        
        # Buttons
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        ok_btn = QPushButton("Set Primary")
        
        cancel_btn.clicked.connect(dialog.reject)
        ok_btn.clicked.connect(dialog.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)
        layout.addLayout(button_layout)
        
        # Show dialog
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get selected index
            selected_id = button_group.checkedId()
            if selected_id >= 0:
                selected_pair = all_pairs[selected_id]
                
                # Update pending operations to mark the selected relationship as primary
                if selected_pair.get('is_pending'):
                    # This is a new/edited relationship - update the operation
                    for operation in self.pending_operations:
                        if operation.get('description') == selected_pair['description'].replace(' (NEW)', ''):
                            operation['is_primary'] = True
                        else:
                            operation['is_primary'] = False
                else:
                    # This is an existing relationship - create an edit operation to mark it as primary
                    # First, unmark all pending operations as primary
                    for operation in self.pending_operations:
                        operation['is_primary'] = False
                    
                    # Then create an edit operation for the existing relationship
                    # Note: This is a simplified approach - in a full implementation,
                    # we'd need to track which existing relationship was selected
                    QMessageBox.information(
                        self,
                        "Manual Update Required",
                        f"Please manually edit the existing relationship '{selected_pair['description']}' "
                        "to mark it as primary, then try this operation again."
                    )
                    return False
                
                return True
        
        return False  # User cancelled
    
    def _execute_add_operation(self, operation: Dict[str, Any]) -> None:
        """Execute an add relationship operation.
        
        Args:
            operation: Operation data dictionary containing relationship details
        """
        from app.relationships import create_relationship, create_relationship_pair
        
        forward_type_id = operation['forward_type_id']
        backward_type_id = operation['backward_type_id']
        source_id = operation['source_id']
        target_id = operation['target_id']
        is_primary = operation.get('is_primary', False)
        
        # If both relationships are selected, create them as a linked pair
        if forward_type_id is not None and backward_type_id is not None:
            print(f"Creating linked relationship pair: forward_type_id={forward_type_id}, backward_type_id={backward_type_id}, primary={is_primary}")
            
            # Clear existing primary relationships if this one is being set as primary
            if is_primary:
                self._clear_existing_primary_relationships()
            
            forward_id, backward_id = create_relationship_pair(
                self.db_conn,
                source_id=source_id,
                target_id=target_id,
                forward_type_id=forward_type_id,
                backward_type_id=backward_type_id,
                is_primary_relationship=is_primary
            )
            print(f"Created linked relationships: forward_id={forward_id}, backward_id={backward_id}")
        else:
            # Clear existing primary relationships if this one is being set as primary
            if is_primary:
                self._clear_existing_primary_relationships()
            
            # Create individual relationships if only one is selected
            if forward_type_id is not None:
                print(f"Creating forward relationship: source_id={source_id}, target_id={target_id}, type_id={forward_type_id}, primary={is_primary}")
                create_relationship(
                    self.db_conn,
                    source_id=source_id,
                    target_id=target_id,
                    relationship_type_id=forward_type_id,
                    is_primary_relationship=is_primary
                )
            
            if backward_type_id is not None:
                print(f"Creating backward relationship: source_id={target_id}, target_id={source_id}, type_id={backward_type_id}, primary={is_primary}")
                create_relationship(
                    self.db_conn,
                    source_id=target_id,
                    target_id=source_id,
                    relationship_type_id=backward_type_id,
                    is_primary_relationship=is_primary
                )
    
    def _clear_existing_primary_relationships(self) -> None:
        """Clear existing primary relationship status for this character pair."""
        cursor = self.db_conn.cursor()
        
        # Clear primary status for all relationships between these two characters
        cursor.execute("""
            UPDATE relationships 
            SET is_primary_relationship = 0 
            WHERE (source_id = ? AND target_id = ?) 
               OR (source_id = ? AND target_id = ?)
        """, (self.source_id, self.target_id, self.target_id, self.source_id))
        
        print(f"Cleared existing primary relationships between {self.source_name} and {self.target_name}")
    
    def _execute_edit_operation(self, operation: Dict[str, Any]) -> None:
        """Execute an edit relationship operation.
        
        Args:
            operation: Operation data dictionary containing relationship details
        """
        from app.relationships import create_relationship, create_relationship_pair
        
        rel_data = operation['relationship_data']
        new_forward_type_id = operation['new_forward_type_id']
        new_backward_type_id = operation['new_backward_type_id']
        is_primary = operation.get('is_primary', False)
        
        print(f"Executing edit operation for relationship {rel_data['description']} (primary: {is_primary})")
        
        try:
            # Get the current relationship details from the database
            relationship_details = self._get_relationship_details(rel_data)
            
            if not relationship_details:
                print(f"Could not load relationship details for editing")
                return
            
            # Update or create the forward relationship
            forward_rel = relationship_details.get('forward')
            backward_rel = relationship_details.get('backward')
            
            # If we have both new type IDs, handle as a pair
            if new_forward_type_id and new_backward_type_id:
                # Clear existing primary relationships if this one is being set as primary
                if is_primary:
                    self._clear_existing_primary_relationships()
                
                # Delete old relationships if they exist
                cursor = self.db_conn.cursor()
                
                if forward_rel:
                    cursor.execute("DELETE FROM relationships WHERE id = ?", (forward_rel['id'],))
                if backward_rel:
                    cursor.execute("DELETE FROM relationships WHERE id = ?", (backward_rel['id'],))
                
                # Create new linked pair
                from app.relationships import create_relationship_pair
                forward_id, backward_id = create_relationship_pair(
                    self.db_conn,
                    source_id=self.source_id,
                    target_id=self.target_id,
                    forward_type_id=new_forward_type_id,
                    backward_type_id=new_backward_type_id,
                    is_primary_relationship=is_primary
                )
                print(f"Created new linked relationship pair: {forward_id}, {backward_id}")
                
            elif new_forward_type_id:
                # Clear existing primary relationships if this one is being set as primary
                if is_primary:
                    self._clear_existing_primary_relationships()
                
                # Only forward relationship selected
                cursor = self.db_conn.cursor()
                
                # Update or create forward relationship
                if forward_rel:
                    cursor.execute("""
                        UPDATE relationships 
                        SET relationship_type_id = ?, inverse_relationship_id = NULL, is_primary_relationship = ?
                        WHERE id = ?
                    """, (new_forward_type_id, 1 if is_primary else 0, forward_rel['id']))
                else:
                    from app.relationships import create_relationship
                    create_relationship(
                        self.db_conn,
                        source_id=self.source_id,
                        target_id=self.target_id,
                        relationship_type_id=new_forward_type_id,
                        is_primary_relationship=is_primary
                    )
                
                # Remove backward relationship if it exists
                if backward_rel:
                    cursor.execute("DELETE FROM relationships WHERE id = ?", (backward_rel['id'],))
                
                print(f"Updated forward relationship to type {new_forward_type_id} (primary: {is_primary})")
            
            print(f"Successfully executed edit operation")
            
        except Exception as e:
            print(f"Error executing edit operation: {e}")
            import traceback
            traceback.print_exc()
            raise  # Re-raise to trigger rollback in the calling method
    
    def _get_relationship_details(self, rel_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get detailed relationship information from the database.
        
        Args:
            rel_data: Basic relationship data from the table
            
        Returns:
            Dictionary with forward and backward relationship details
        """
        try:
            cursor = self.db_conn.cursor()
            
            # Get the primary relationship
            cursor.execute("""
                SELECT id, source_id, target_id, relationship_type_id, strength,
                       inverse_relationship_id, is_custom, custom_label
                FROM relationships
                WHERE id = ?
            """, (rel_data['primary_id'],))
            
            primary_rel = cursor.fetchone()
            if not primary_rel:
                print(f"Primary relationship {rel_data['primary_id']} not found")
                return None
            
            primary_dict = dict(primary_rel)
            
            result = {}
            
            # Determine which relationship is forward and which is backward
            if primary_dict['source_id'] == self.source_id and primary_dict['target_id'] == self.target_id:
                # Primary is forward direction
                result['forward'] = primary_dict
                
                # Get inverse if it exists
                if rel_data['inverse_id']:
                    cursor.execute("""
                        SELECT id, source_id, target_id, relationship_type_id, strength,
                               inverse_relationship_id, is_custom, custom_label
                        FROM relationships
                        WHERE id = ?
                    """, (rel_data['inverse_id'],))
                    
                    inverse_rel = cursor.fetchone()
                    if inverse_rel:
                        result['backward'] = dict(inverse_rel)
                        
            elif primary_dict['source_id'] == self.target_id and primary_dict['target_id'] == self.source_id:
                # Primary is backward direction
                result['backward'] = primary_dict
                
                # Get inverse if it exists (which would be the forward direction)
                if rel_data['inverse_id']:
                    cursor.execute("""
                        SELECT id, source_id, target_id, relationship_type_id, strength,
                               inverse_relationship_id, is_custom, custom_label
                        FROM relationships
                        WHERE id = ?
                    """, (rel_data['inverse_id'],))
                    
                    inverse_rel = cursor.fetchone()
                    if inverse_rel:
                        result['forward'] = dict(inverse_rel)
            else:
                print(f"Relationship direction doesn't match expected characters")
                return None
            
            return result
            
        except Exception as e:
            print(f"Error getting relationship details: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _save_relationship_changes(self) -> None:
        """Save changes to the relationship being edited."""
        if not self.is_edit_mode or not self.editing_relationship_data:
            QMessageBox.warning(
                self,
                "Not in Edit Mode",
                "No relationship is currently being edited."
            )
            return
        
        # Get the current selections
        forward_type_id, backward_type_id = self.get_selected_relationships()
        
        if forward_type_id is None:
            QMessageBox.warning(
                self,
                "No Relationship Selected",
                "Please select at least a forward relationship type."
            )
            return
        
        # Create edit operation
        operation = {
            'type': 'edit',
            'relationship_data': self.editing_relationship_data,
            'new_forward_type_id': forward_type_id,
            'new_backward_type_id': backward_type_id,
            'is_primary': self.primary_relationship_checkbox.isChecked(),
            'description': self._get_operation_description(forward_type_id, backward_type_id) + " (EDITED)"
        }
        
        # Add to queue
        self.pending_operations.append(operation)
        
        # Show confirmation message
        QMessageBox.information(
            self,
            "Relationship Changes Queued",
            f"Relationship changes added to pending operations:\n{operation['description']}\n\n"
            f"Total pending operations: {len(self.pending_operations)}\n\n"
            "Click 'Apply' to save all changes to the database."
        )
        
        # Reset the cards and exit edit mode
        self._reset_relationship_cards()
        
        print(f"Queued relationship edit: {operation['description']}")
    
    def _select_relationship_type_by_id(self, combo: SearchableComboBox, type_id: int) -> bool:
        """Select a relationship type in the combo box by its type ID.
        
        Args:
            combo: The SearchableComboBox to update
            type_id: The relationship type ID to select
            
        Returns:
            True if the type ID was found and selected, False otherwise
        """
        for i in range(combo.count()):
            item_type_id = combo.itemData(i, Qt.ItemDataRole.UserRole)
            if item_type_id == type_id:
                combo.setCurrentIndex(i)
                print(f"Selected relationship type ID {type_id} at index {i}")
                return True
        
        print(f"Relationship type ID {type_id} not found in combo box")
        return False

    def _refresh_existing_relationships_table(self) -> None:
        """Refresh the existing relationships table with current data."""
        if hasattr(self, 'existing_relationships_table'):
            # Clear the current table
            self.existing_relationships_table.setRowCount(0)
            
            # Reload and repopulate
            existing_relationships = self._load_existing_relationships()
            
            # Recalculate optimal table height based on new content
            row_count = len(existing_relationships) if existing_relationships else 1  # At least 1 for empty state
            max_visible_rows = 3  # Maximum number of rows to show without scrolling
            visible_rows = min(row_count, max_visible_rows)
            
            # Calculate height: header + (row height * visible rows) + margins
            header_height = 30  # Approximate header height
            row_height = 35     # Approximate row height with padding
            table_margins = 10  # Small margin for borders
            optimal_height = header_height + (row_height * visible_rows) + table_margins
            
            # Update the table height
            self.existing_relationships_table.setMaximumHeight(optimal_height)
            self.existing_relationships_table.setMinimumHeight(optimal_height)
            
            if existing_relationships:
                self.existing_relationships_table.setRowCount(len(existing_relationships))
                
                for row, rel_data in enumerate(existing_relationships):
                    # Relationship description
                    desc_item = QTableWidgetItem(rel_data['description'])
                    desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    desc_item.setData(Qt.ItemDataRole.UserRole, rel_data)
                    self.existing_relationships_table.setItem(row, 0, desc_item)
                    
                    # Strength
                    strength_item = QTableWidgetItem(str(rel_data['strength']))
                    strength_item.setFlags(strength_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    strength_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.existing_relationships_table.setItem(row, 1, strength_item)
                    
                    # Primary status
                    primary_item = QTableWidgetItem("✓" if rel_data.get('is_primary', False) else "")
                    primary_item.setFlags(primary_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    primary_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.existing_relationships_table.setItem(row, 2, primary_item)
            else:
                # Show empty state
                self.existing_relationships_table.setRowCount(1)
                empty_item = QTableWidgetItem("No existing relationships")
                empty_item.setFlags(empty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                # Make the empty state text slightly dimmed using palette colors
                palette = self.existing_relationships_table.palette()
                placeholder_color = palette.color(palette.ColorRole.PlaceholderText)
                if not placeholder_color.isValid():
                    # Fallback for older Qt versions or themes without PlaceholderText
                    text_color = palette.color(palette.ColorRole.Text)
                    text_color.setAlpha(128)  # Make it 50% transparent
                    empty_item.setForeground(text_color)
                else:
                    empty_item.setForeground(placeholder_color)
                self.existing_relationships_table.setItem(0, 0, empty_item)
                
                # Empty strength cell
                empty_strength = QTableWidgetItem("")
                empty_strength.setFlags(empty_strength.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.existing_relationships_table.setItem(0, 1, empty_strength)
                
                empty_primary = QTableWidgetItem("")
                empty_primary.setFlags(empty_primary.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.existing_relationships_table.setItem(0, 2, empty_primary)
        
        # Connect click event for future functionality
        self.existing_relationships_table.cellClicked.connect(self._on_existing_relationship_clicked)
        
        # Add context menu support
        self.existing_relationships_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.existing_relationships_table.customContextMenuRequested.connect(self._show_relationship_context_menu)
        
        # Connect selection change to enable/disable edit button
        self.existing_relationships_table.itemSelectionChanged.connect(self._on_relationship_selection_changed)
        
    def _on_existing_relationship_clicked(self, row: int, column: int) -> None:
        """Handle clicks on existing relationship table items.
        
        Args:
            row: Row index that was clicked
            column: Column index that was clicked
        """
        # Get the relationship data from the first column
        item = self.existing_relationships_table.item(row, 0)
        if item and item.data(Qt.ItemDataRole.UserRole):
            rel_data = item.data(Qt.ItemDataRole.UserRole)
            print(f"Clicked on relationship: {rel_data['description']} (IDs: {rel_data['primary_id']}, {rel_data['inverse_id']})")
            
            # Enable edit button when a valid relationship is selected
            self.edit_relationship_button.setEnabled(True)
    
    def _on_relationship_selection_changed(self) -> None:
        """Handle when the relationship table selection changes."""
        current_row = self.existing_relationships_table.currentRow()
        has_selection = current_row >= 0
        
        # Enable/disable edit button based on selection
        if has_selection:
            item = self.existing_relationships_table.item(current_row, 0)
            has_valid_data = item and item.data(Qt.ItemDataRole.UserRole) is not None
            self.edit_relationship_button.setEnabled(has_valid_data)
        else:
            self.edit_relationship_button.setEnabled(False)
    
    def _show_relationship_context_menu(self, position) -> None:
        """Show context menu for relationship table.
        
        Args:
            position: Position where the context menu was requested
        """
        item = self.existing_relationships_table.itemAt(position)
        if not item or not item.data(Qt.ItemDataRole.UserRole):
            return
        
        # Create context menu
        context_menu = QMenu(self)
        
        # Add edit action
        edit_action = QAction("Edit Relationship", self)
        edit_action.triggered.connect(self._edit_selected_relationship)
        context_menu.addAction(edit_action)
        
        # Show the menu
        context_menu.exec(self.existing_relationships_table.mapToGlobal(position))
    
    def _edit_selected_relationship(self) -> None:
        """Edit the currently selected relationship from the table."""
        current_row = self.existing_relationships_table.currentRow()
        if current_row < 0:
            QMessageBox.information(
                self,
                "No Relationship Selected",
                "Please select a relationship from the list to edit."
            )
            return
        
        # Get the relationship data from the table
        item = self.existing_relationships_table.item(current_row, 0)
        if not item or not item.data(Qt.ItemDataRole.UserRole):
            QMessageBox.warning(
                self,
                "Invalid Selection",
                "The selected item does not contain valid relationship data."
            )
            return
        
        rel_data = item.data(Qt.ItemDataRole.UserRole)
        self._load_relationship_for_editing(rel_data)
    
    def _load_relationship_for_editing(self, rel_data: Dict[str, Any]) -> None:
        """Load a relationship into the cards for editing.
        
        Args:
            rel_data: Relationship data dictionary from the table
        """
        print(f"Loading relationship for editing: {rel_data}")
        
        # Store the relationship data being edited
        self.editing_relationship_data = rel_data
        
        # Enter edit mode
        self.is_edit_mode = True
        
        try:
            # Get the actual relationship details from the database
            relationship_details = self._get_relationship_details(rel_data)
            
            if not relationship_details:
                QMessageBox.warning(
                    self,
                    "Error Loading Relationship",
                    "Could not load relationship details from the database."
                )
                return
            
            # Load relationship data into the cards
            forward_rel = relationship_details.get('forward')
            backward_rel = relationship_details.get('backward')
            
            # Reset cards first
            self.forward_card.relationship_combo.setCurrentIndex(-1)
            self.backward_card.relationship_combo.setCurrentIndex(-1)
            
            # Load forward relationship
            if forward_rel:
                success = self._select_relationship_type_by_id(
                    self.forward_card.relationship_combo,
                    forward_rel['relationship_type_id']
                )
                if success:
                    # Enable backward card and load backward relationship if exists
                    self.backward_card.setEnabled(True)
                    
                    if backward_rel:
                        self._select_relationship_type_by_id(
                            self.backward_card.relationship_combo,
                            backward_rel['relationship_type_id']
                        )
            
            # Set primary checkbox based on current primary status
            is_primary = rel_data.get('is_primary', False)
            self.primary_relationship_checkbox.setChecked(is_primary)
            
            # Update button states
            self._update_add_relationship_button_state()
            
            print(f"Successfully loaded relationship pair for editing (primary: {is_primary})")
            
        except Exception as e:
            print(f"Error loading relationship for editing: {e}")
            import traceback
            traceback.print_exc()
            
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while loading the relationship: {str(e)}"
            )

    def _load_existing_relationships(self) -> List[Dict[str, Any]]:
        """Load existing relationships between the two characters.
        
        Returns:
            List of relationship pair dictionaries for display
        """
        try:
            cursor = self.db_conn.cursor()
            
            # Get all relationships between these two characters (both directions)
            cursor.execute("""
                SELECT r.id, r.source_id, r.target_id, r.relationship_type_id, 
                       r.relationship_type, r.strength, r.inverse_relationship_id,
                       r.is_custom, r.custom_label, r.created_at, r.is_primary_relationship,
                       rt.label as type_label
                FROM relationships r
                LEFT JOIN relationship_types_new rt ON r.relationship_type_id = rt.type_id
                WHERE (r.source_id = ? AND r.target_id = ?) 
                   OR (r.source_id = ? AND r.target_id = ?)
                ORDER BY r.created_at DESC
            """, (self.source_id, self.target_id, self.target_id, self.source_id))
            
            all_relationships = [dict(row) for row in cursor.fetchall()]
            
            if not all_relationships:
                return []
            
            # Group relationships into pairs and singles
            relationship_pairs = []
            processed_ids = set()
            
            for rel in all_relationships:
                if rel['id'] in processed_ids:
                    continue
                
                # Get the display label
                display_label = rel['custom_label'] if rel['is_custom'] and rel['custom_label'] else rel['type_label']
                if not display_label:
                    display_label = rel['relationship_type']  # Fallback to legacy column
                
                # Check if this relationship has an inverse
                if rel['inverse_relationship_id']:
                    # Find the inverse relationship in our list
                    inverse_rel = None
                    for other_rel in all_relationships:
                        if other_rel['id'] == rel['inverse_relationship_id']:
                            inverse_rel = other_rel
                            break
                    
                    if inverse_rel:
                        # Get the inverse display label
                        inverse_display_label = inverse_rel['custom_label'] if inverse_rel['is_custom'] and inverse_rel['custom_label'] else inverse_rel['type_label']
                        if not inverse_display_label:
                            inverse_display_label = inverse_rel['relationship_type']  # Fallback
                        
                        # Determine the order (source character first)
                        if rel['source_id'] == self.source_id:
                            # rel is source -> target, inverse_rel is target -> source
                            pair_description = f"{self.source_name} ({display_label}) ↔ {self.target_name} ({inverse_display_label})"
                        else:
                            # rel is target -> source, inverse_rel is source -> target
                            pair_description = f"{self.source_name} ({inverse_display_label}) ↔ {self.target_name} ({display_label})"
                        
                        # Check if this is a primary relationship (either relationship in the pair can indicate primary status)
                        is_primary = rel['is_primary_relationship'] or inverse_rel['is_primary_relationship']
                        
                        relationship_pairs.append({
                            'type': 'pair',
                            'description': pair_description,
                            'strength': max(rel['strength'] or 0, inverse_rel['strength'] or 0),  # Use higher strength
                            'primary_id': rel['id'],
                            'inverse_id': inverse_rel['id'],
                            'created_at': rel['created_at'],
                            'is_primary': is_primary
                        })
                        
                        # Mark both as processed
                        processed_ids.add(rel['id'])
                        processed_ids.add(inverse_rel['id'])
                    else:
                        # Inverse relationship ID exists but relationship not found (broken link)
                        # Treat as single relationship
                        if rel['source_id'] == self.source_id:
                            single_description = f"{self.source_name} ({display_label})"
                        else:
                            single_description = f"{self.target_name} ({display_label})"
                        
                        relationship_pairs.append({
                            'type': 'single',
                            'description': single_description,
                            'strength': rel['strength'] or 0,
                            'primary_id': rel['id'],
                            'inverse_id': None,
                            'created_at': rel['created_at'],
                            'is_primary': rel['is_primary_relationship']
                        })
                        
                        processed_ids.add(rel['id'])
                else:
                    # Single relationship (no inverse)
                    if rel['source_id'] == self.source_id:
                        single_description = f"{self.source_name} ({display_label})"
                    else:
                        single_description = f"{self.target_name} ({display_label})"
                    
                    relationship_pairs.append({
                        'type': 'single',
                        'description': single_description,
                        'strength': rel['strength'] or 0,
                        'primary_id': rel['id'],
                        'inverse_id': None,
                        'created_at': rel['created_at'],
                        'is_primary': rel['is_primary_relationship']
                    })
                    
                    processed_ids.add(rel['id'])
            
            return relationship_pairs
            
        except Exception as e:
            print(f"Error loading existing relationships: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _create_existing_relationships_table(self) -> QTableWidget:
        """Create and populate the existing relationships table.
        
        Returns:
            QTableWidget with existing relationships
        """
        table = QTableWidget()
        table.setColumnCount(3)  # Added Primary column
        table.setHorizontalHeaderLabels(["Relationship", "Strength", "Primary"])
        
        # Set table properties for dark theme compatibility
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.verticalHeader().setVisible(False)
        
        # Add dark-theme friendly styling
        table.setStyleSheet("""
            QTableWidget {
                border: 1px solid palette(mid);
                border-radius: 5px;
                background-color: palette(base);
                alternate-background-color: palette(alternate-base);
                selection-background-color: palette(highlight);
                gridline-color: palette(mid);
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: palette(highlight);
                color: palette(highlighted-text);
            }
            QHeaderView::section {
                background-color: palette(button);
                padding: 6px;
                border: 1px solid palette(mid);
                font-weight: bold;
            }
        """)
        
        # Set column widths
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Relationship column stretches
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Strength column fits content
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Primary column fits content
        
        # Load existing relationships first to determine proper table height
        existing_relationships = self._load_existing_relationships()
        
        # Calculate optimal table height based on content
        row_count = len(existing_relationships) if existing_relationships else 1  # At least 1 for empty state
        max_visible_rows = 3  # Maximum number of rows to show without scrolling
        visible_rows = min(row_count, max_visible_rows)
        
        # Calculate height: header + (row height * visible rows) + margins
        header_height = 30  # Approximate header height
        row_height = 35     # Approximate row height with padding
        table_margins = 10  # Small margin for borders
        optimal_height = header_height + (row_height * visible_rows) + table_margins
        
        # Set the calculated height
        table.setMaximumHeight(optimal_height)
        table.setMinimumHeight(optimal_height)
        
        # Populate the table
        if existing_relationships:
            table.setRowCount(len(existing_relationships))
            
            for row, rel_data in enumerate(existing_relationships):
                # Relationship description
                desc_item = QTableWidgetItem(rel_data['description'])
                desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make read-only
                desc_item.setData(Qt.ItemDataRole.UserRole, rel_data)  # Store full data for later use
                table.setItem(row, 0, desc_item)
                
                # Strength
                strength_item = QTableWidgetItem(str(rel_data['strength']))
                strength_item.setFlags(strength_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make read-only
                strength_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, 1, strength_item)
                
                # Primary status
                primary_item = QTableWidgetItem("✓" if rel_data.get('is_primary', False) else "")
                primary_item.setFlags(primary_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make read-only
                primary_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, 2, primary_item)
        else:
            # Show empty state
            table.setRowCount(1)
            empty_item = QTableWidgetItem("No existing relationships")
            empty_item.setFlags(empty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            # Make the empty state text slightly dimmed using palette colors
            palette = table.palette()
            placeholder_color = palette.color(palette.ColorRole.PlaceholderText)
            if not placeholder_color.isValid():
                # Fallback for older Qt versions or themes without PlaceholderText
                text_color = palette.color(palette.ColorRole.Text)
                text_color.setAlpha(128)  # Make it 50% transparent
                empty_item.setForeground(text_color)
            else:
                empty_item.setForeground(placeholder_color)
            table.setItem(0, 0, empty_item)
            
            # Empty strength and primary cells
            empty_strength = QTableWidgetItem("")
            empty_strength.setFlags(empty_strength.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(0, 1, empty_strength)
            
            empty_primary = QTableWidgetItem("")
            empty_primary.setFlags(empty_primary.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(0, 2, empty_primary)
        
        # Connect click event for future functionality
        table.cellClicked.connect(self._on_existing_relationship_clicked)
        
        # Add context menu support
        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        table.customContextMenuRequested.connect(self._show_relationship_context_menu)
        
        # Connect selection change to enable/disable edit button
        table.itemSelectionChanged.connect(self._on_relationship_selection_changed)
        
        return table
    
    def _on_existing_relationship_clicked(self, row: int, column: int) -> None:
        """Handle clicks on existing relationship table items.
        
        Args:
            row: Row index that was clicked
            column: Column index that was clicked
        """
        # Get the relationship data from the first column
        item = self.existing_relationships_table.item(row, 0)
        if item and item.data(Qt.ItemDataRole.UserRole):
            rel_data = item.data(Qt.ItemDataRole.UserRole)
            print(f"Clicked on relationship: {rel_data['description']} (IDs: {rel_data['primary_id']}, {rel_data['inverse_id']})")
            
            # Enable edit button when a valid relationship is selected
            self.edit_relationship_button.setEnabled(True)
    
    def _on_relationship_selection_changed(self) -> None:
        """Handle when the relationship table selection changes."""
        current_row = self.existing_relationships_table.currentRow()
        has_selection = current_row >= 0
        
        # Enable/disable edit button based on selection
        if has_selection:
            item = self.existing_relationships_table.item(current_row, 0)
            has_valid_data = item and item.data(Qt.ItemDataRole.UserRole) is not None
            self.edit_relationship_button.setEnabled(has_valid_data)
        else:
            self.edit_relationship_button.setEnabled(False)
    
    def _show_relationship_context_menu(self, position) -> None:
        """Show context menu for relationship table.
        
        Args:
            position: Position where the context menu was requested
        """
        item = self.existing_relationships_table.itemAt(position)
        if not item or not item.data(Qt.ItemDataRole.UserRole):
            return
        
        # Create context menu
        context_menu = QMenu(self)
        
        # Add edit action
        edit_action = QAction("Edit Relationship", self)
        edit_action.triggered.connect(self._edit_selected_relationship)
        context_menu.addAction(edit_action)
        
        # Show the menu
        context_menu.exec(self.existing_relationships_table.mapToGlobal(position))
    
    def _edit_selected_relationship(self) -> None:
        """Edit the currently selected relationship from the table."""
        current_row = self.existing_relationships_table.currentRow()
        if current_row < 0:
            QMessageBox.information(
                self,
                "No Relationship Selected",
                "Please select a relationship from the list to edit."
            )
            return
        
        # Get the relationship data from the table
        item = self.existing_relationships_table.item(current_row, 0)
        if not item or not item.data(Qt.ItemDataRole.UserRole):
            QMessageBox.warning(
                self,
                "Invalid Selection",
                "The selected item does not contain valid relationship data."
            )
            return
        
        rel_data = item.data(Qt.ItemDataRole.UserRole)
        self._load_relationship_for_editing(rel_data)
    
    def _load_relationship_for_editing(self, rel_data: Dict[str, Any]) -> None:
        """Load a relationship into the cards for editing.
        
        Args:
            rel_data: Relationship data dictionary from the table
        """
        print(f"Loading relationship for editing: {rel_data}")
        
        # Store the relationship data being edited
        self.editing_relationship_data = rel_data
        
        # Enter edit mode
        self.is_edit_mode = True
        
        try:
            # Get the actual relationship details from the database
            relationship_details = self._get_relationship_details(rel_data)
            
            if not relationship_details:
                QMessageBox.warning(
                    self,
                    "Error Loading Relationship",
                    "Could not load relationship details from the database."
                )
                return
            
            # Load relationship data into the cards
            forward_rel = relationship_details.get('forward')
            backward_rel = relationship_details.get('backward')
            
            # Reset cards first
            self.forward_card.relationship_combo.setCurrentIndex(-1)
            self.backward_card.relationship_combo.setCurrentIndex(-1)
            
            # Load forward relationship
            if forward_rel:
                success = self._select_relationship_type_by_id(
                    self.forward_card.relationship_combo,
                    forward_rel['relationship_type_id']
                )
                if success:
                    # Enable backward card and load backward relationship if exists
                    self.backward_card.setEnabled(True)
                    
                    if backward_rel:
                        self._select_relationship_type_by_id(
                            self.backward_card.relationship_combo,
                            backward_rel['relationship_type_id']
                        )
            
            # Set primary checkbox based on current primary status
            is_primary = rel_data.get('is_primary', False)
            self.primary_relationship_checkbox.setChecked(is_primary)
            
            # Update button states
            self._update_add_relationship_button_state()
            
            print(f"Successfully loaded relationship pair for editing (primary: {is_primary})")
            
        except Exception as e:
            print(f"Error loading relationship for editing: {e}")
            import traceback
            traceback.print_exc()
            
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while loading the relationship: {str(e)}"
            )

    def accept(self) -> None:
        """Save the relationship and close the dialog."""
        # Save the relationship(s) to the database
        self.save_relationships()
        
        # Look for any open Story Board and trigger a refresh
        main_window = self.window()
        while main_window and not hasattr(main_window, 'story_board'):
            main_window = main_window.parent() if hasattr(main_window, 'parent') else None
        
        # If we found the main window with a story board, refresh it
        if main_window and hasattr(main_window, 'story_board'):
            main_window.story_board.refresh_board()
        
        # Close the dialog
        super().accept() 