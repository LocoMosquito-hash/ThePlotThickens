#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Character Dialog for The Plot Thickens application.

This module defines the dialog for editing character data.
"""

import os
import sys
import time
from typing import Optional, Dict, Any, List, Tuple, Set

from PyQt6.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QSpinBox, QCheckBox, QPushButton,
    QFileDialog, QMessageBox, QApplication, QGroupBox, QListWidget, 
    QListWidgetItem, QMenu, QInputDialog, QTextEdit, QFrame
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QBuffer, QByteArray, QSettings, QPoint
from PyQt6.QtGui import QPixmap, QImage, QCloseEvent, QAction, QCursor, QKeyEvent, QTextCursor

from app.db_sqlite import (
    get_character, update_character, get_story, get_character_quick_events,
    create_quick_event, update_quick_event, delete_quick_event, 
    get_next_quick_event_sequence_number, get_quick_event_characters,
    get_story_characters
)


class CharacterTagEditor(QDialog):
    """Dialog for editing quick event text with character tag support."""
    
    def __init__(self, db_conn, character_id: int, text: str = "", parent=None):
        """Initialize the character tag editor.
        
        Args:
            db_conn: Database connection
            character_id: ID of the character the quick event belongs to
            text: Initial text (default empty)
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.character_id = character_id
        self.initial_text = text
        
        # Get the story ID for this character
        character = get_character(db_conn, character_id)
        self.story_id = character.get('story_id') if character else None
        
        # Load available characters
        self.characters = []
        if self.story_id:
            self.characters = get_story_characters(db_conn, self.story_id)
        
        self.init_ui()
        
        # Create character tag completer
        self.tag_completer = CharacterTagCompleter(self)
        self.tag_completer.set_characters(self.characters)
        self.tag_completer.character_selected.connect(self.insert_character_tag)
        self.tag_completer.hide()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Quick Event")
        self.resize(450, 200)
        
        layout = QVBoxLayout(self)
        
        # Text edit
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Enter quick event text. Use @name to tag characters (e.g., @John kissed @Mary)")
        self.text_edit.setText(self.initial_text)
        self.text_edit.textChanged.connect(self.check_for_character_tag)
        layout.addWidget(self.text_edit)
        
        # Available characters
        if self.characters:
            char_names = [f"@{char['name']}" for char in self.characters]
            characters_label = QLabel("Available character tags: " + ", ".join(char_names))
            characters_label.setWordWrap(True)
            characters_label.setStyleSheet("color: #666; font-style: italic;")
            layout.addWidget(characters_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
    def get_text(self) -> str:
        """Get the edited text.
        
        Returns:
            The text from the editor
        """
        return self.text_edit.toPlainText()
        
    def check_for_character_tag(self):
        """Check if the user is typing a character tag and provide suggestions."""
        cursor = self.text_edit.textCursor()
        text = self.text_edit.toPlainText()
        
        # Find the current word being typed
        pos = cursor.position()
        start = max(0, pos - 1)
        
        # Check if we're in the middle of typing a tag
        if start >= 0 and pos <= len(text):
            # Look backward to find the start of the current tag
            tag_start = text.rfind('@', 0, pos)
            
            if tag_start >= 0 and tag_start < pos:
                # We found a @ character before the cursor
                # Extract the partial tag text
                partial_tag = text[tag_start + 1:pos]
                
                # Only show suggestions if we're actively typing a tag
                if tag_start == pos - 1 or partial_tag.strip():
                    # Position the completer popup below the cursor
                    cursor_rect = self.text_edit.cursorRect()
                    global_pos = self.text_edit.mapToGlobal(cursor_rect.bottomLeft())
                    
                    self.tag_completer.set_filter(partial_tag)
                    self.tag_completer.move(global_pos)
                    return
                    
        # Hide the completer if we're not typing a tag
        self.tag_completer.hide()
        
    def insert_character_tag(self, character_name: str):
        """Insert a character tag at the current cursor position.
        
        Args:
            character_name: Name of the character to tag
        """
        cursor = self.text_edit.textCursor()
        text = self.text_edit.toPlainText()
        pos = cursor.position()
        
        # Find the start of the current tag
        tag_start = text.rfind('@', 0, pos)
        
        if tag_start >= 0:
            # Replace the partial tag with the full tag
            cursor.setPosition(tag_start, QTextCursor.MoveMode.MoveAnchor)
            cursor.setPosition(pos, QTextCursor.MoveMode.KeepAnchor)
            cursor.insertText(f"@{character_name}")
            
            # Add a space after the tag
            cursor.insertText(" ")
            
            # Set focus back to the text edit
            self.text_edit.setFocus()


class CharacterTagCompleter(QWidget):
    """Popup widget for character tag autocompletion."""
    
    character_selected = pyqtSignal(str)  # Signal emitted when a character is selected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.characters = []
        self.filtered_characters = []
        self.current_filter = ""
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create a list widget for character suggestions
        self.list_widget = QListWidget()
        self.list_widget.setFrameShape(QFrame.Shape.NoFrame)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.setMaximumHeight(200)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        
        # Style the list widget
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #2D2D30;
                color: #FFFFFF;
                border: 1px solid #3E3E42;
                border-radius: 3px;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #007ACC;
            }
        """)
        
        layout.addWidget(self.list_widget)
        
    def set_characters(self, characters: List[Dict[str, Any]]):
        """Set the available characters for autocompletion.
        
        Args:
            characters: List of character dictionaries
        """
        self.characters = characters
        self.update_suggestions()
        
    def set_filter(self, filter_text: str):
        """Set the filter text for character suggestions.
        
        Args:
            filter_text: Text to filter characters by
        """
        self.current_filter = filter_text.lower()
        self.update_suggestions()
        
    def update_suggestions(self):
        """Update the list of character suggestions based on the current filter."""
        self.list_widget.clear()
        
        if not self.characters:
            self.hide()
            return
            
        # Filter characters based on the current filter
        self.filtered_characters = []
        for char in self.characters:
            name = char['name']
            if self.current_filter in name.lower():
                self.filtered_characters.append(char)
                
                # Create a list item with the character name
                item = QListWidgetItem(name)
                item.setData(Qt.ItemDataRole.UserRole, char['id'])
                
                # Bold for main characters
                if char.get('is_main_character'):
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                    
                self.list_widget.addItem(item)
                
        # Show or hide the widget based on whether there are suggestions
        if self.filtered_characters:
            self.list_widget.setCurrentRow(0)  # Select the first item
            self.show()
        else:
            self.hide()
            
    def on_item_clicked(self, item: QListWidgetItem):
        """Handle item click events.
        
        Args:
            item: The clicked list item
        """
        name = item.text()
        self.character_selected.emit(name)
        self.hide()
        
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events.
        
        Args:
            event: Key event
        """
        key = event.key()
        
        if key == Qt.Key.Key_Escape:
            self.hide()
            event.accept()
        elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            current_item = self.list_widget.currentItem()
            if current_item:
                self.on_item_clicked(current_item)
            event.accept()
        elif key == Qt.Key.Key_Up:
            current_row = self.list_widget.currentRow()
            if current_row > 0:
                self.list_widget.setCurrentRow(current_row - 1)
            event.accept()
        elif key == Qt.Key.Key_Down:
            current_row = self.list_widget.currentRow()
            if current_row < self.list_widget.count() - 1:
                self.list_widget.setCurrentRow(current_row + 1)
            event.accept()
        else:
            super().keyPressEvent(event)


class QuickEventItem(QListWidgetItem):
    """List widget item representing a quick event."""
    
    def __init__(self, event_data: Dict[str, Any], tagged_characters: List[Dict[str, Any]] = None):
        """Initialize a quick event item.
        
        Args:
            event_data: Quick event data dictionary
            tagged_characters: List of tagged character dictionaries
        """
        super().__init__()
        self.event_data = event_data
        self.event_id = event_data['id']
        self.text = event_data['text']
        self.tagged_characters = tagged_characters or []
        
        # Set display text
        self.setText(self.text)
        
        # Add character tags to tooltip
        tooltip = self.text
        if self.tagged_characters:
            char_names = [char['name'] for char in self.tagged_characters]
            tooltip += f"\n\nTagged characters: {', '.join(char_names)}"
        self.setToolTip(tooltip)


class QuickEventsTab(QWidget):
    """Tab for managing character quick events."""
    
    def __init__(self, db_conn, character_id: int, parent=None):
        """Initialize the quick events tab.
        
        Args:
            db_conn: Database connection
            character_id: ID of the character
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.character_id = character_id
        self.quick_events = []
        
        self.init_ui()
        self.load_quick_events()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Header with explanation
        header_label = QLabel(
            "Quick events are simple actions or moments related to this character. "
            "Use @name to tag other characters involved in the event."
        )
        header_label.setWordWrap(True)
        layout.addWidget(header_label)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        self.add_event_button = QPushButton("Add Quick Event")
        self.add_event_button.clicked.connect(self.add_quick_event)
        toolbar_layout.addWidget(self.add_event_button)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # Quick events list
        self.events_list = QListWidget()
        self.events_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.events_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.events_list.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.events_list)
        
    def load_quick_events(self):
        """Load quick events for the character."""
        try:
            self.quick_events = get_character_quick_events(self.db_conn, self.character_id)
            self.update_events_list()
        except Exception as e:
            print(f"Error loading quick events: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load quick events: {str(e)}")
    
    def update_events_list(self):
        """Update the events list widget with current quick events."""
        self.events_list.clear()
        
        if not self.quick_events:
            empty_item = QListWidgetItem("No quick events yet. Click 'Add Quick Event' to create one.")
            empty_item.setFlags(Qt.ItemFlag.NoItemFlags)  # Make non-selectable
            self.events_list.addItem(empty_item)
            return
        
        for event in self.quick_events:
            # Get tagged characters
            try:
                tagged_characters = get_quick_event_characters(self.db_conn, event['id'])
            except Exception as e:
                print(f"Error getting tagged characters: {e}")
                tagged_characters = []
                
            item = QuickEventItem(event, tagged_characters)
            self.events_list.addItem(item)
    
    def add_quick_event(self):
        """Add a new quick event."""
        dialog = CharacterTagEditor(self.db_conn, self.character_id, parent=self)
        
        if dialog.exec():
            text = dialog.get_text()
            
            if not text.strip():
                QMessageBox.warning(self, "Error", "Quick event text cannot be empty.")
                return
                
            try:
                # Get the next sequence number to place the event at the end
                sequence_number = get_next_quick_event_sequence_number(self.db_conn, self.character_id)
                
                # Create the quick event
                quick_event_id = create_quick_event(
                    self.db_conn,
                    text,
                    self.character_id,
                    sequence_number
                )
                
                if quick_event_id:
                    # Reload the events
                    self.load_quick_events()
                else:
                    QMessageBox.warning(self, "Error", "Failed to create quick event.")
            except Exception as e:
                print(f"Error adding quick event: {e}")
                QMessageBox.warning(self, "Error", f"Failed to add quick event: {str(e)}")
    
    def edit_quick_event(self, event_id: int):
        """Edit an existing quick event.
        
        Args:
            event_id: ID of the quick event to edit
        """
        # Find the event in the list
        event = next((e for e in self.quick_events if e['id'] == event_id), None)
        if not event:
            return
            
        dialog = CharacterTagEditor(self.db_conn, self.character_id, event['text'], parent=self)
        
        if dialog.exec():
            text = dialog.get_text()
            
            if not text.strip():
                QMessageBox.warning(self, "Error", "Quick event text cannot be empty.")
                return
                
            try:
                # Update the quick event
                success = update_quick_event(
                    self.db_conn,
                    event_id,
                    text=text
                )
                
                if success:
                    # Reload the events
                    self.load_quick_events()
                else:
                    QMessageBox.warning(self, "Error", "Failed to update quick event.")
            except Exception as e:
                print(f"Error updating quick event: {e}")
                QMessageBox.warning(self, "Error", f"Failed to update quick event: {str(e)}")
    
    def delete_quick_event(self, event_id: int):
        """Delete a quick event.
        
        Args:
            event_id: ID of the quick event to delete
        """
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this quick event?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                success = delete_quick_event(self.db_conn, event_id)
                
                if success:
                    # Reload the events
                    self.load_quick_events()
                else:
                    QMessageBox.warning(self, "Error", "Failed to delete quick event.")
            except Exception as e:
                print(f"Error deleting quick event: {e}")
                QMessageBox.warning(self, "Error", f"Failed to delete quick event: {str(e)}")
    
    def show_context_menu(self, position: QPoint):
        """Show context menu for a quick event.
        
        Args:
            position: Position where the menu should be displayed
        """
        item = self.events_list.itemAt(position)
        
        if not item or not isinstance(item, QuickEventItem):
            return
            
        event_id = item.event_id
        
        menu = QMenu(self)
        
        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(lambda: self.edit_quick_event(event_id))
        menu.addAction(edit_action)
        
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.delete_quick_event(event_id))
        menu.addAction(delete_action)
        
        # Show the menu
        menu.exec(QCursor.pos())


class CharacterDialog(QDialog):
    """Dialog for creating and editing characters."""
    
    # Signal emitted when a character is updated
    character_updated = pyqtSignal(int, dict)
    
    def __init__(self, db_conn, story_id: int, character_id: Optional[int] = None, parent=None) -> None:
        """Initialize the character dialog.
        
        Args:
            db_conn: Database connection
            story_id: ID of the story
            character_id: ID of the character to edit (None for new character)
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.db_conn = db_conn
        self.story_id = story_id
        self.character_id = character_id
        self.avatar_path = None
        self.avatar_changed = False
        self.has_unsaved_changes = False
        
        # Initialize character data
        self.character_data = {
            'id': character_id,
            'name': '',
            'story_id': story_id,
            'aliases': '',
            'is_main_character': False,
            'age_value': None,
            'age_category': None,
            'gender': 'NOT_SPECIFIED',
            'avatar_path': None
        }
        
        # If editing an existing character, load its data
        if character_id is not None:
            character = get_character(db_conn, character_id)
            if character:
                self.character_data = character
                self.avatar_path = character['avatar_path']
        
        self.init_ui()
        self.load_character_data()
        
        # Connect signals
        self.connect_signals()
        
        # Set window properties
        self.setWindowTitle("Character Details")
        self.resize(800, 600)
    
    def init_ui(self) -> None:
        """Initialize the user interface."""
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create summary tab
        self.summary_tab = QWidget()
        self.tab_widget.addTab(self.summary_tab, "Summary")
        
        # Create relationships tab (placeholder)
        self.relationships_tab = QWidget()
        relationships_layout = QVBoxLayout(self.relationships_tab)
        relationships_layout.addWidget(QLabel("Relationships will be implemented later."))
        self.tab_widget.addTab(self.relationships_tab, "Relationships")
        
        # Create quick events tab
        if self.character_id is not None:  # Only show for existing characters
            self.quick_events_tab = QuickEventsTab(self.db_conn, self.character_id)
            self.tab_widget.addTab(self.quick_events_tab, "Quick Events")
        
        # Create gallery tab (placeholder)
        self.gallery_tab = QWidget()
        gallery_layout = QVBoxLayout(self.gallery_tab)
        gallery_layout.addWidget(QLabel("Gallery will be implemented later."))
        self.tab_widget.addTab(self.gallery_tab, "Gallery")
        
        # Create summary tab layout
        self.create_summary_tab()
        
        # Create buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_character)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
    
    def create_summary_tab(self) -> None:
        """Create the summary tab."""
        layout = QVBoxLayout(self.summary_tab)
        
        # Create form layout for basic info
        form_layout = QFormLayout()
        
        # Name field
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Optional - will generate 'Unnamed X' if empty")
        self.name_edit.textChanged.connect(self.on_field_changed)
        form_layout.addRow("Name:", self.name_edit)
        
        # Avatar section
        avatar_group = QGroupBox("Avatar")
        avatar_layout = QVBoxLayout(avatar_group)
        
        # Avatar preview
        self.avatar_preview = QLabel()
        self.avatar_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_preview.setMinimumSize(180, 180)
        self.avatar_preview.setMaximumSize(300, 300)
        self.avatar_preview.setScaledContents(False)
        avatar_layout.addWidget(self.avatar_preview)
        
        # Avatar buttons
        avatar_buttons = QHBoxLayout()
        
        self.edit_avatar_button = QPushButton("Browse...")
        self.edit_avatar_button.setToolTip("Select an image file for the avatar")
        self.edit_avatar_button.clicked.connect(self.edit_avatar)
        
        self.paste_avatar_button = QPushButton("Paste")
        self.paste_avatar_button.setToolTip("Paste an image from the clipboard")
        self.paste_avatar_button.clicked.connect(self.paste_avatar)
        
        self.delete_avatar_button = QPushButton("Delete")
        self.delete_avatar_button.setToolTip("Remove the avatar")
        self.delete_avatar_button.clicked.connect(self.delete_avatar)
        
        avatar_buttons.addWidget(self.edit_avatar_button)
        avatar_buttons.addWidget(self.paste_avatar_button)
        avatar_buttons.addWidget(self.delete_avatar_button)
        avatar_layout.addLayout(avatar_buttons)
        
        # Add avatar group to layout
        layout.addLayout(form_layout)
        layout.addWidget(avatar_group)
        
        # Continue with form layout
        form_layout2 = QFormLayout()
        
        # Aliases field
        self.aliases_edit = QLineEdit()
        self.aliases_edit.setPlaceholderText("Comma-separated list of aliases")
        self.aliases_edit.textChanged.connect(self.on_field_changed)
        form_layout2.addRow("Aliases:", self.aliases_edit)
        
        # Main character checkbox
        self.mc_checkbox = QCheckBox("Main Character")
        self.mc_checkbox.stateChanged.connect(self.on_field_changed)
        form_layout2.addRow("", self.mc_checkbox)
        
        # Age section
        age_layout = QHBoxLayout()
        
        # Age value
        self.age_value_spin = QSpinBox()
        self.age_value_spin.setRange(0, 999)
        self.age_value_spin.setSpecialValueText("Not specified")
        self.age_value_spin.valueChanged.connect(self.on_field_changed)
        
        # Age category
        self.age_category_combo = QComboBox()
        self.age_category_combo.addItem("Not specified", None)
        self.age_category_combo.addItem("Minor", "MINOR")
        self.age_category_combo.addItem("Teen", "TEEN")
        self.age_category_combo.addItem("Young", "YOUNG")
        self.age_category_combo.addItem("Adult", "ADULT")
        self.age_category_combo.addItem("Middle-aged", "MIDDLE_AGED")
        self.age_category_combo.addItem("Mature", "MATURE")
        self.age_category_combo.addItem("Old", "OLD")
        self.age_category_combo.currentIndexChanged.connect(self.on_field_changed)
        
        age_layout.addWidget(QLabel("Value:"))
        age_layout.addWidget(self.age_value_spin)
        age_layout.addWidget(QLabel("Category:"))
        age_layout.addWidget(self.age_category_combo)
        
        form_layout2.addRow("Age:", age_layout)
        
        # Gender field
        self.gender_combo = QComboBox()
        self.gender_combo.addItem("Not specified", "NOT_SPECIFIED")
        self.gender_combo.addItem("Male", "MALE")
        self.gender_combo.addItem("Female", "FEMALE")
        self.gender_combo.addItem("Futa", "FUTA")
        self.gender_combo.currentIndexChanged.connect(self.on_field_changed)
        form_layout2.addRow("Gender:", self.gender_combo)
        
        layout.addLayout(form_layout2)
        layout.addStretch()
    
    def load_character_data(self) -> None:
        """Load character data into the form."""
        # Set name
        self.name_edit.setText(self.character_data['name'])
        
        # Set avatar
        if self.character_data['avatar_path']:
            avatar_path = self.character_data['avatar_path']
            print(f"DEBUG: Loading avatar from path: {avatar_path}")
            
            # Try to load the avatar
            pixmap = QPixmap(avatar_path)
            
            # If the pixmap is null, try to resolve the path
            if pixmap.isNull():
                # Try absolute path
                if not os.path.isabs(avatar_path):
                    abs_path = os.path.abspath(avatar_path)
                    print(f"DEBUG: Trying absolute path: {abs_path}")
                    pixmap = QPixmap(abs_path)
                
                # If still null, try to get the story folder path and construct the path
                if pixmap.isNull():
                    try:
                        # Get the story folder path from the database
                        story_data = get_story(self.db_conn, self.story_id)
                        story_folder = story_data['folder_path']
                        
                        # Extract the filename from the avatar path
                        filename = os.path.basename(avatar_path)
                        
                        # Construct the new path
                        new_path = os.path.join(story_folder, "images", filename)
                        print(f"DEBUG: Trying path with story folder: {new_path}")
                        pixmap = QPixmap(new_path)
                    except Exception as e:
                        print(f"DEBUG: Error resolving avatar path: {str(e)}")
            
            if not pixmap.isNull():
                scaled_pixmap = self._scale_pixmap_for_avatar(pixmap)
                self.avatar_preview.setPixmap(scaled_pixmap)
                print(f"DEBUG: Avatar loaded successfully")
            else:
                self.avatar_preview.setText("No Avatar")
                print(f"DEBUG: Failed to load avatar from path: {avatar_path}")
        else:
            self.avatar_preview.setText("No Avatar")
            print(f"DEBUG: No avatar path specified")
        
        # Set aliases
        if self.character_data['aliases']:
            self.aliases_edit.setText(self.character_data['aliases'])
        
        # Set main character checkbox
        self.mc_checkbox.setChecked(bool(self.character_data['is_main_character']))
        
        # Set age value
        if self.character_data['age_value'] is not None:
            self.age_value_spin.setValue(self.character_data['age_value'])
        
        # Set age category
        if self.character_data['age_category']:
            index = self.age_category_combo.findData(self.character_data['age_category'])
            if index >= 0:
                self.age_category_combo.setCurrentIndex(index)
        
        # Set gender
        index = self.gender_combo.findData(self.character_data['gender'])
        if index >= 0:
            self.gender_combo.setCurrentIndex(index)
    
    def connect_signals(self) -> None:
        """Connect signals to slots."""
        # Field change signals are already connected in create_summary_tab
        # Button signals are already connected in init_ui
        # This method is provided for consistency and future expansion
        pass
    
    def on_field_changed(self) -> None:
        """Handle field changes."""
        self.has_unsaved_changes = True
        self.save_button.setEnabled(True)
    
    def edit_avatar(self) -> None:
        """Open a file dialog to select a new avatar."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Avatar Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                scaled_pixmap = self._scale_pixmap_for_avatar(pixmap)
                self.avatar_preview.setPixmap(scaled_pixmap)
                self.avatar_path = file_path
                self.avatar_changed = True
                self.on_field_changed()
    
    def paste_avatar(self) -> None:
        """Paste an image from the clipboard as the avatar."""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasImage():
            print("DEBUG: Found image in clipboard")
            image = QImage(clipboard.image())
            if not image.isNull():
                pixmap = QPixmap.fromImage(image)
                scaled_pixmap = self._scale_pixmap_for_avatar(pixmap)
                self.avatar_preview.setPixmap(scaled_pixmap)
                # We set avatar_path to None to indicate it's a pasted image
                # but we'll still have the pixmap in avatar_preview
                self.avatar_path = None
                self.avatar_changed = True
                self.on_field_changed()
                print("DEBUG: Set pasted image as avatar")
            else:
                print("DEBUG: Image from clipboard is null")
        else:
            print("DEBUG: No image found in clipboard")
            QMessageBox.warning(self, "Paste Failed", "No image found in clipboard.")
    
    def delete_avatar(self) -> None:
        """Delete the avatar."""
        self.avatar_preview.clear()
        self.avatar_preview.setText("No Avatar")
        self.avatar_path = None
        self.avatar_changed = True
        self.on_field_changed()
    
    def save_avatar(self) -> str:
        """Save the avatar image to the story folder.
        
        Returns:
            Path to the saved avatar image, or empty string if no avatar
        """
        if not self.avatar_changed:
            print("DEBUG: Avatar not changed, returning existing path")
            return self.character_data.get('avatar_path', '')
        
        # If avatar was deleted, return empty string
        if self.avatar_changed and self.avatar_preview.pixmap() is None:
            print("DEBUG: Avatar was deleted, returning empty string")
            return ""
        
        # Get the story folder
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT folder_path FROM stories WHERE id = ?", (self.story_id,))
        story_folder = cursor.fetchone()['folder_path']
        
        # Ensure the avatars folder exists
        avatars_folder = os.path.join(story_folder, "avatars")
        os.makedirs(avatars_folder, exist_ok=True)
        
        # Get absolute paths for debugging
        abs_story_folder = os.path.abspath(story_folder)
        abs_avatars_folder = os.path.abspath(avatars_folder)
        print(f"DEBUG: Story folder absolute path: {abs_story_folder}")
        print(f"DEBUG: Avatars folder absolute path: {abs_avatars_folder}")
        
        # Generate a filename for the avatar
        filename = f"avatar_temp_{int(time.time())}.png" if self.character_id is None else f"avatar_{self.character_id}.png"
        avatar_path = os.path.join(avatars_folder, filename)
        abs_avatar_path = os.path.abspath(avatar_path)
        print(f"DEBUG: Avatar will be saved to: {avatar_path}")
        print(f"DEBUG: Avatar absolute path: {abs_avatar_path}")
        
        # If new avatar was selected from file, copy it
        if self.avatar_path and os.path.exists(self.avatar_path):
            print(f"DEBUG: Copying avatar from {self.avatar_path}")
            pixmap = QPixmap(self.avatar_path)
            saved = pixmap.save(avatar_path, "PNG")
            print(f"DEBUG: Avatar saved successfully: {saved}")
            print(f"DEBUG: Final avatar path stored in DB: {abs_avatar_path}")
            return abs_avatar_path
        
        # If avatar was pasted from clipboard (or set programmatically)
        pixmap = self.avatar_preview.pixmap()
        if pixmap and not pixmap.isNull():
            print("DEBUG: Saving pixmap from avatar_preview")
            saved = pixmap.save(avatar_path, "PNG")
            print(f"DEBUG: Avatar saved successfully: {saved}")
            print(f"DEBUG: Final avatar path stored in DB: {abs_avatar_path}")
            return abs_avatar_path
        
        # If we get here, no valid avatar to save
        print("DEBUG: No valid avatar to save, returning empty string")
        return ""
    
    def save_character(self) -> None:
        """Save the character data."""
        # Get the character data from the form
        character_data = self.get_character_data()
        
        # Generate a default name if none is provided
        if not character_data['name']:
            # Get the count of unnamed characters in this story to generate a unique name
            cursor = self.db_conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) as count FROM characters WHERE story_id = ? AND name LIKE 'Unnamed %'",
                (self.story_id,)
            )
            count = cursor.fetchone()['count']
            
            # Generate a name like "Unnamed 1", "Unnamed 2", etc.
            character_data['name'] = f"Unnamed {count + 1}"
            print(f"DEBUG: Generated default name: {character_data['name']}")
        
        # Print debug info
        print(f"DEBUG: Initial character data: {character_data}")
        
        # Save the avatar if needed and update the avatar path
        if self.avatar_changed:
            saved_avatar_path = self.save_avatar()
            character_data['avatar_path'] = saved_avatar_path
            print(f"DEBUG: Updated avatar path in character data: {saved_avatar_path}")
        
        # Print final character data
        print(f"DEBUG: Final character data to be saved: {character_data}")
        
        # If this is a new character, create it
        if self.character_id is None:
            print(f"DEBUG: Creating new character for story {self.story_id}")
            from app.db_sqlite import create_character
            
            self.character_id = create_character(
                self.db_conn,
                name=character_data['name'],
                story_id=self.story_id,
                aliases=character_data['aliases'],
                is_main_character=character_data['is_main_character'],
                age_value=character_data['age_value'],
                age_category=character_data['age_category'],
                gender=character_data['gender'],
                avatar_path=character_data['avatar_path']
            )
            
            print(f"DEBUG: Created character with ID {self.character_id}")
        else:
            # Update existing character
            print(f"DEBUG: Updating existing character {self.character_id}")
            from app.db_sqlite import update_character
            
            update_character(
                self.db_conn,
                self.character_id,
                name=character_data['name'],
                aliases=character_data['aliases'],
                is_main_character=character_data['is_main_character'],
                age_value=character_data['age_value'],
                age_category=character_data['age_category'],
                gender=character_data['gender'],
                avatar_path=character_data['avatar_path']
            )
            print(f"DEBUG: Character {self.character_id} updated successfully")
        
        # Emit the character_updated signal
        self.character_updated.emit(self.character_id, character_data)
        
        # Reset unsaved changes flag
        self.has_unsaved_changes = False
        
        # Close dialog
        self.accept()
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle close event.
        
        Args:
            event: Close event
        """
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            
            if reply == QMessageBox.StandardButton.Save:
                self.save_character()
                event.accept()
            elif reply == QMessageBox.StandardButton.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def get_character_data(self) -> Dict[str, Any]:
        """Get the character data from the form.
        
        Returns:
            Dictionary of character data
        """
        # Get name (can be empty, will generate a default name later if needed)
        name = self.name_edit.text().strip()
        
        # Get aliases
        aliases = self.aliases_edit.text().strip()
        
        # Get main character flag
        is_main_character = self.mc_checkbox.isChecked()
        
        # Get age value
        age_value = self.age_value_spin.value()
        if age_value == 0:  # Special value
            age_value = None
        
        # Get age category
        age_category = self.age_category_combo.currentData()
        
        # Get gender
        gender = self.gender_combo.currentData()
        
        # Get avatar path - preserve existing path if not changed
        if self.avatar_changed:
            avatar_path = self.avatar_path
        else:
            avatar_path = self.character_data.get('avatar_path', None)
        
        # Return the data
        return {
            'name': name,
            'aliases': aliases,
            'is_main_character': is_main_character,
            'age_value': age_value,
            'age_category': age_category,
            'gender': gender,
            'avatar_path': avatar_path
        } 

    def _scale_pixmap_for_avatar(self, pixmap: QPixmap) -> QPixmap:
        """Scale a pixmap to fit the avatar preview while maintaining aspect ratio.
        
        Args:
            pixmap: The original pixmap
            
        Returns:
            Scaled pixmap
        """
        if pixmap.isNull():
            return pixmap
            
        # Get the size of the avatar preview
        preview_size = self.avatar_preview.size()
        max_width = preview_size.width()
        max_height = preview_size.height()
        
        # If the pixmap is smaller than the preview, no need to scale
        if pixmap.width() <= max_width and pixmap.height() <= max_height:
            return pixmap
            
        # Scale the pixmap to fit the preview while maintaining aspect ratio
        return pixmap.scaled(
            max_width, 
            max_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ) 