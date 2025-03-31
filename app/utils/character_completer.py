#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Character completion module for The Plot Thickens application.

This module provides a reusable character tag autocompletion widget that can be
used throughout the application to maintain consistent behavior and styling.
"""

from typing import List, Dict, Any, Optional, Union, Callable
import re

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QFrame,
    QApplication, QTextEdit, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent, QObject
from PyQt6.QtGui import QKeySequence, QKeyEvent, QTextCursor, QShortcut

# Import the centralized character reference functions
from app.utils.character_references import (
    convert_mentions_to_char_refs as centralized_convert_mentions_to_char_refs,
    convert_char_refs_to_mentions as centralized_convert_char_refs_to_mentions
)


class CharacterCompleter(QWidget):
    """Enhanced popup widget for character tag autocompletion.
    
    This is a centralized implementation that can be used throughout the application
    to provide consistent character tag autocompletion functionality.
    
    Features:
    - Character suggestion filtering
    - Keyboard navigation (arrow keys, Tab, Enter, Escape)
    - Optional keyboard shortcut (Ctrl+Space) to show all suggestions
    - Support for QTextEdit and QLineEdit
    - Customizable styling
    - Bold highlighting for main characters
    - Signal when a character is selected
    """
    
    character_selected = pyqtSignal(str)  # Signal emitted when a character is selected
    
    def __init__(self, parent=None):
        """Initialize the character completer.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Popup | 
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoMousePropagation)
        
        self.characters: List[Dict[str, Any]] = []
        self.filtered_characters: List[Dict[str, Any]] = []
        self.current_filter: str = ""
        self.text_widget: Optional[Union[QTextEdit, QLineEdit]] = None
        self.shortcut: Optional[QShortcut] = None
        self._show_was_requested: bool = False
        
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
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Prevent focus stealing
        
        # Apply default styling
        self.apply_default_style()
        
        layout.addWidget(self.list_widget)
        
    def apply_default_style(self):
        """Apply default styling to the completer."""
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #2D2D30;
                color: #FFFFFF;
                border: 1px solid #3E3E42;
                border-radius: 4px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 6px 10px;
                border-bottom: 1px solid #3E3E42;
            }
            QListWidget::item:selected {
                background-color: #007ACC;
                color: #FFFFFF;
            }
            QListWidget::item:hover {
                background-color: #3E3E42;
            }
        """)
        
    def set_custom_style(self, style_sheet: str):
        """Set a custom style sheet for the completer.
        
        Args:
            style_sheet: CSS style sheet
        """
        self.list_widget.setStyleSheet(style_sheet)
        
    def attach_to_widget(self, 
                         widget: Union[QTextEdit, QLineEdit], 
                         add_shortcut: bool = True,
                         shortcut_key: str = "Ctrl+Space",
                         at_trigger: bool = True):
        """Attach the completer to a text widget.
        
        Args:
            widget: Text widget to attach to (QTextEdit or QLineEdit)
            add_shortcut: Whether to add a keyboard shortcut
            shortcut_key: Keyboard shortcut sequence
            at_trigger: Whether to trigger on @ symbol
        """
        self.text_widget = widget
        
        # Install event filter to capture text changes
        if self.text_widget:
            self.text_widget.installEventFilter(self)
            
            # If this is a QTextEdit, connect to textChanged
            if isinstance(self.text_widget, QTextEdit) and at_trigger:
                self.text_widget.textChanged.connect(self.check_for_character_tag)
            # If this is a QLineEdit, connect to textChanged
            elif isinstance(self.text_widget, QLineEdit) and at_trigger:
                self.text_widget.textChanged.connect(
                    lambda: self.check_for_character_tag_line_edit(self.text_widget.text())
                )
            
            # Add shortcut if requested
            if add_shortcut:
                self.shortcut = QShortcut(QKeySequence(shortcut_key), self.text_widget)
                self.shortcut.activated.connect(self.show_all_suggestions)
                
    def set_characters(self, characters: List[Dict[str, Any]]):
        """Set the available characters for autocompletion.
        
        Args:
            characters: List of character dictionaries
        """
        self.characters = characters
        # Don't call update_suggestions here to avoid showing on startup
        
    def set_filter(self, filter_text: str):
        """Set the filter text for character suggestions.
        
        Args:
            filter_text: Text to filter characters by
        """
        self.current_filter = filter_text.lower() if filter_text else ""
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
        
        # Sort filtered characters alphabetically by name
        self.filtered_characters.sort(key=lambda c: c['name'].lower())
        
        # Add characters to the list widget
        for char in self.filtered_characters:
            # Create a list item with the character name
            item = QListWidgetItem(char['name'])
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
            
            # Adjust the width to fit the content but not be too narrow
            self.list_widget.setMinimumWidth(200)
            
            # Adjust the height based on number of items (up to 10 items)
            items_count = min(10, len(self.filtered_characters))
            item_height = 32  # Approximated from the padding in CSS
            self.list_widget.setFixedHeight(items_count * item_height)
            
            # Show if we have a filter text OR if show was explicitly requested (via @ or shortcut)
            if self._show_was_requested:
                self.position_at_cursor()
                self.show()
            # For backwards compatibility, also show if there's a filter and text widget
            elif self.current_filter and self.text_widget:
                self.position_at_cursor()
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
        
    def show_all_suggestions(self):
        """Show all character suggestions at the cursor position."""
        if self.text_widget:
            # Show all characters without filtering
            self._show_was_requested = True
            self.set_filter("")
            
            # Position at cursor
            self.position_at_cursor()
            
            # Ensure visibility
            self.raise_()
            
    def position_at_cursor(self):
        """Position the completer popup at the cursor position."""
        if not self.text_widget:
            return
        
        # Get cursor position
        if isinstance(self.text_widget, QTextEdit):
            cursor_rect = self.text_widget.cursorRect()
        else:  # QLineEdit
            cursor_rect = self.text_widget.cursorRect()
            
        # Get global position
        global_pos = self.text_widget.mapToGlobal(cursor_rect.bottomLeft())
        
        # Adjust for screen boundaries
        screen = QApplication.primaryScreen().geometry()
        
        # Calculate popup dimensions
        popup_width = self.sizeHint().width()
        popup_height = self.sizeHint().height()
        
        # Check if popup would go off right edge of screen
        if global_pos.x() + popup_width > screen.right():
            global_pos.setX(screen.right() - popup_width)
            
        # Check if popup would go off bottom edge of screen
        if global_pos.y() + popup_height > screen.bottom():
            # Position above cursor
            global_pos = self.text_widget.mapToGlobal(cursor_rect.topLeft())
            global_pos.setY(global_pos.y() - popup_height)
            
        # Move popup to position
        self.move(global_pos)
        
    def check_for_character_tag(self):
        """Check if user is typing a character tag in QTextEdit."""
        if not isinstance(self.text_widget, QTextEdit):
            return
            
        cursor = self.text_widget.textCursor()
        text = self.text_widget.toPlainText()
        pos = cursor.position()
        
        self._check_for_tag(text, pos)
        
    def check_for_character_tag_line_edit(self, text: str):
        """Check if user is typing a character tag in QLineEdit.
        
        Args:
            text: Current text in the line edit
        """
        if not isinstance(self.text_widget, QLineEdit):
            return
            
        pos = self.text_widget.cursorPosition()
        self._check_for_tag(text, pos)
        
    def _check_for_tag(self, text: str, cursor_pos: int):
        """Common logic for checking if user is typing a character tag.
        
        Args:
            text: Text to check
            cursor_pos: Current cursor position
        """
        # Check if we have any text
        if not text or cursor_pos <= 0:
            return
            
        # Look for @ character before cursor
        tag_start = text.rfind('@', 0, cursor_pos)
        
        # If @ is found and it's either at start of text or preceded by whitespace
        if tag_start >= 0 and (tag_start == 0 or text[tag_start - 1].isspace()):
            # Check if there's whitespace between @ and cursor
            whitespace_after = text.find(' ', tag_start, cursor_pos)
            
            if whitespace_after == -1:  # No whitespace, user is still typing the tag
                # Extract the partial tag (excluding @)
                partial_tag = text[tag_start + 1:cursor_pos]
                
                # Set the show requested flag - we want to show the popup even if there's no text after @
                self._show_was_requested = True
                
                # Filter character suggestions
                self.set_filter(partial_tag)
                
                # Position the popup at the cursor
                self.position_at_cursor()
            else:
                # User has completed typing a tag
                self.hide()
        else:
            # No @ found before cursor
            self.hide()
        
    def insert_character_tag(self, character_name: str):
        """Insert selected character tag at the cursor position.
        
        Args:
            character_name: Name of the selected character
        """
        if isinstance(self.text_widget, QTextEdit):
            self._insert_tag_text_edit(character_name)
        elif isinstance(self.text_widget, QLineEdit):
            self._insert_tag_line_edit(character_name)
        
        # Focus back on the text widget
        self.text_widget.setFocus()
        
    def _insert_tag_text_edit(self, character_name: str):
        """Insert character tag into QTextEdit.
        
        Args:
            character_name: Name of the selected character
        """
        if not isinstance(self.text_widget, QTextEdit):
            return
            
        cursor = self.text_widget.textCursor()
        text = self.text_widget.toPlainText()
        pos = cursor.position()
        
        # Look for @ character before cursor
        tag_start = text.rfind('@', 0, pos)
        
        if tag_start >= 0:
            # Remove the partial tag
            cursor.setPosition(tag_start, QTextCursor.MoveMode.MoveAnchor)
            cursor.setPosition(pos, QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
            
            # Insert the full character tag
            cursor.insertText(f"@{character_name}")
            
            # Move cursor after the inserted tag
            cursor.movePosition(QTextCursor.MoveOperation.EndOfWord)
            self.text_widget.setTextCursor(cursor)
            
    def _insert_tag_line_edit(self, character_name: str):
        """Insert character tag into QLineEdit.
        
        Args:
            character_name: Name of the selected character
        """
        if not isinstance(self.text_widget, QLineEdit):
            return
            
        text = self.text_widget.text()
        pos = self.text_widget.cursorPosition()
        
        # Look for @ character before cursor
        tag_start = text.rfind('@', 0, pos)
        
        if tag_start >= 0:
            # Build new text with the character tag inserted
            text_before = text[:tag_start]
            text_after = text[pos:]
            new_text = f"{text_before}@{character_name}{text_after}"
            
            # Calculate new cursor position
            new_pos = tag_start + len(f"@{character_name}")
            
            # Set the new text and cursor position
            self.text_widget.setText(new_text)
            self.text_widget.setCursorPosition(new_pos)
            
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Filter events to handle keyboard navigation.
        
        Args:
            obj: Object that triggered the event
            event: Event that occurred
        
        Returns:
            Whether the event was handled
        """
        if obj == self.text_widget and event.type() == QEvent.Type.KeyPress:
            # The event is already a KeyEvent when event.type() is KeyPress
            key_event = event
            
            # Handle Tab key for selection
            if (key_event.key() == Qt.Key.Key_Tab and self.isVisible() and 
                    self.list_widget.count() > 0):
                # Get currently selected item
                current_item = self.list_widget.currentItem()
                if current_item:
                    # Emit character selected signal with the selected character name
                    self.on_item_clicked(current_item)
                    return True  # Event handled
                    
            # Handle Escape key to hide popup
            if key_event.key() == Qt.Key.Key_Escape and self.isVisible():
                self.hide()
                return True  # Event handled
                
            # Handle arrow keys for navigation
            if self.isVisible():
                if key_event.key() == Qt.Key.Key_Down:
                    self.list_widget.setCurrentRow(
                        min(self.list_widget.currentRow() + 1, self.list_widget.count() - 1)
                    )
                    return True  # Event handled
                    
                if key_event.key() == Qt.Key.Key_Up:
                    self.list_widget.setCurrentRow(
                        max(self.list_widget.currentRow() - 1, 0)
                    )
                    return True  # Event handled
                    
        # Let other events be processed normally
        return super().eventFilter(obj, event)
        
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events.
        
        Args:
            event: Key event
        """
        key = event.key()
        
        # Only handle navigation and selection keys in the completer
        if key == Qt.Key.Key_Escape:
            self.hide()
            event.accept()
        elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter or key == Qt.Key.Key_Tab:
            # Select character with Enter or Tab
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
            # Ignore all other keys so they get processed by the parent text editor
            # This allows typing to continue while the suggestion list is visible
            event.ignore()

    def hide(self):
        """Hide the completer and reset the show request flag."""
        self._show_was_requested = False
        super().hide()


def convert_mentions_to_char_refs(text: str, characters: List[Dict[str, Any]]) -> str:
    """Convert @mentions to [char:ID] format.
    
    Args:
        text: Text containing @mentions
        characters: List of character dictionaries
        
    Returns:
        Text with @mentions converted to [char:ID] format
    """
    # Use the centralized implementation while maintaining the exact same interface
    return centralized_convert_mentions_to_char_refs(text, characters)


def convert_char_refs_to_mentions(text: str, characters: List[Dict[str, Any]]) -> str:
    """Convert [char:ID] references to @mentions.
    
    Args:
        text: Text containing [char:ID] references
        characters: List of character dictionaries
        
    Returns:
        Text with [char:ID] references converted to @mentions
    """
    # Use the centralized implementation while maintaining the exact same interface
    return centralized_convert_char_refs_to_mentions(text, characters)


def extract_character_ids_from_text(text: str) -> List[int]:
    """Extract character IDs from text containing [char:ID] references.
    
    Args:
        text: Text containing [char:ID] references
        
    Returns:
        List of character IDs
    """
    # Define the regex pattern for finding character references
    pattern = r'\[char:(\d+)\]'
    
    # Find all character references
    matches = re.findall(pattern, text)
    
    # Convert to integers and return unique IDs
    return [int(char_id) for char_id in matches] 