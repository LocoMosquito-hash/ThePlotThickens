#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Character Input Dialog for The Plot Thickens application.

This module provides a custom input dialog with character auto-completion
for use in the Story Notepad and other parts of the application.
"""

from typing import List, Dict, Any, Optional, Tuple
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QTextEdit, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from app.utils.character_completer import CharacterCompleter


class CharacterInputDialog(QDialog):
    """A custom input dialog with character auto-completion."""
    
    def __init__(self, parent=None, title: str = "Input", label: str = "Enter text:",
                 text: str = "", multiline: bool = False, characters: List[Dict[str, Any]] = None):
        """Initialize the character input dialog.
        
        Args:
            parent: Parent widget
            title: Dialog title
            label: Label text to show above the input
            text: Initial text value
            multiline: Whether to use a multiline text edit
            characters: List of character dictionaries for auto-completion
        """
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self.characters = characters or []
        self.multiline = multiline
        self.result_text = ""
        
        self.init_ui(label, text)
        
    def init_ui(self, label: str, text: str) -> None:
        """Initialize the user interface.
        
        Args:
            label: Label text
            text: Initial text value
        """
        layout = QVBoxLayout(self)
        
        # Label
        label_widget = QLabel(label)
        label_widget.setWordWrap(True)
        layout.addWidget(label_widget)
        
        # Text input (single line or multiline)
        if self.multiline:
            self.text_widget = QTextEdit()
            self.text_widget.setPlainText(text)
            self.text_widget.setMinimumHeight(120)
            self.text_widget.setMaximumHeight(200)
        else:
            self.text_widget = QLineEdit()
            self.text_widget.setText(text)
            self.text_widget.selectAll()
        
        # Set up font
        font = QFont()
        font.setPointSize(10)
        self.text_widget.setFont(font)
        
        layout.addWidget(self.text_widget)
        
        # Character auto-completion
        if self.characters:
            self.completer = CharacterCompleter(self)
            self.completer.set_characters(self.characters)
            self.completer.character_selected.connect(self.on_character_selected)
            self.completer.attach_to_widget(
                self.text_widget,
                add_shortcut=True,
                shortcut_key="Ctrl+Space",
                at_trigger=True
            )
            
            # Add help text
            help_label = QLabel("Tip: Type '@' to tag characters, or press Ctrl+Space for all characters")
            help_label.setStyleSheet("color: gray; font-size: 9px;")
            help_label.setWordWrap(True)
            layout.addWidget(help_label)
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Set focus
        self.text_widget.setFocus()
        
        # Connect Enter key to accept for single line inputs
        if not self.multiline:
            self.text_widget.returnPressed.connect(self.accept)
    
    def on_character_selected(self, character_name: str) -> None:
        """Handle character selection from completer.
        
        Args:
            character_name: Name of the selected character
        """
        self.completer.insert_character_tag(character_name)
    
    def accept(self) -> None:
        """Accept the dialog and store the result."""
        if self.multiline:
            self.result_text = self.text_widget.toPlainText().strip()
        else:
            self.result_text = self.text_widget.text().strip()
        
        if not self.result_text:
            return  # Don't accept empty input
        
        super().accept()
    
    def get_text(self) -> str:
        """Get the entered text.
        
        Returns:
            The text entered by the user
        """
        return self.result_text
    
    @staticmethod
    def get_text_input(parent=None, title: str = "Input", label: str = "Enter text:",
                      text: str = "", characters: List[Dict[str, Any]] = None) -> Tuple[str, bool]:
        """Show a single-line text input dialog with character completion.
        
        Args:
            parent: Parent widget
            title: Dialog title
            label: Label text
            text: Initial text value
            characters: List of character dictionaries for auto-completion
            
        Returns:
            Tuple of (text, ok) where ok indicates if the user accepted the dialog
        """
        dialog = CharacterInputDialog(
            parent=parent,
            title=title,
            label=label,
            text=text,
            multiline=False,
            characters=characters
        )
        
        result = dialog.exec()
        return dialog.get_text(), result == QDialog.DialogCode.Accepted
    
    @staticmethod
    def get_multiline_text_input(parent=None, title: str = "Input", label: str = "Enter text:",
                                 text: str = "", characters: List[Dict[str, Any]] = None) -> Tuple[str, bool]:
        """Show a multi-line text input dialog with character completion.
        
        Args:
            parent: Parent widget
            title: Dialog title
            label: Label text
            text: Initial text value
            characters: List of character dictionaries for auto-completion
            
        Returns:
            Tuple of (text, ok) where ok indicates if the user accepted the dialog
        """
        dialog = CharacterInputDialog(
            parent=parent,
            title=title,
            label=label,
            text=text,
            multiline=True,
            characters=characters
        )
        
        result = dialog.exec()
        return dialog.get_text(), result == QDialog.DialogCode.Accepted 