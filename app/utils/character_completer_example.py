#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Example usage of the CharacterCompleter class.

This example demonstrates how to use the CharacterCompleter with both 
QTextEdit and QLineEdit widgets. It also shows how to handle character selection
and convert mentions to character references.

To run this example directly: python -m app.utils.character_completer_example
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTextEdit, QLineEdit, QPushButton, QLabel, QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt

# Import the CharacterCompleter and utility functions
try:
    from app.utils.character_completer import (
        CharacterCompleter, 
        convert_mentions_to_char_refs,
        convert_char_refs_to_mentions,
        extract_character_ids_from_text
    )
except ImportError:
    # If running the example directly without the full app context
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from app.utils.character_completer import (
        CharacterCompleter, 
        convert_mentions_to_char_refs,
        convert_char_refs_to_mentions,
        extract_character_ids_from_text
    )


class CharacterCompleterExample(QMainWindow):
    """Example application demonstrating the CharacterCompleter usage."""
    
    def __init__(self):
        """Initialize the example application."""
        super().__init__()
        
        # Sample character data (in a real app, this would come from a database)
        self.characters = [
            {"id": 1, "name": "Sherlock Holmes", "age": 39},
            {"id": 2, "name": "John Watson", "age": 37},
            {"id": 3, "name": "Mycroft Holmes", "age": 41},
            {"id": 4, "name": "Inspector Lestrade", "age": 45},
            {"id": 5, "name": "Mrs. Hudson", "age": 60},
            {"id": 6, "name": "Irene Adler", "age": 32},
            {"id": 7, "name": "James Moriarty", "age": 40}
        ]
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Character Completer Example")
        self.setGeometry(100, 100, 800, 600)
        
        # Main widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # Instructions
        instructions = QLabel(
            "Type '@' followed by text to trigger character suggestions.\n"
            "You can also press Ctrl+Space to show all character suggestions.\n"
            "Use arrow keys to navigate and Enter/Tab to select."
        )
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(instructions)
        
        # QTextEdit example
        text_edit_group = QGroupBox("QTextEdit Example")
        text_edit_layout = QVBoxLayout(text_edit_group)
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Start typing '@' to tag a character. Try '@ho' to filter for Holmes.")
        text_edit_layout.addWidget(self.text_edit)
        
        # Create and attach completer for QTextEdit
        self.text_completer = CharacterCompleter(self)
        self.text_completer.set_characters(self.characters)
        self.text_completer.character_selected.connect(self.on_text_character_selected)
        self.text_completer.attach_to_widget(
            self.text_edit,
            add_shortcut=True,
            shortcut_key="Ctrl+Space",
            at_trigger=True
        )
        
        # QLineEdit example
        line_edit_group = QGroupBox("QLineEdit Example")
        line_edit_layout = QVBoxLayout(line_edit_group)
        
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("Start typing '@' to tag a character")
        line_edit_layout.addWidget(self.line_edit)
        
        # Create and attach completer for QLineEdit
        self.line_completer = CharacterCompleter(self)
        self.line_completer.set_characters(self.characters)
        self.line_completer.character_selected.connect(self.on_line_character_selected)
        self.line_completer.attach_to_widget(
            self.line_edit,
            add_shortcut=True,
            shortcut_key="Ctrl+Space",
            at_trigger=True
        )
        
        # Conversion example
        conversion_group = QGroupBox("Convert Mentions to Character References")
        conversion_layout = QGridLayout(conversion_group)
        
        self.convert_text_button = QPushButton("Convert Text to [char:ID]")
        self.convert_text_button.clicked.connect(self.convert_text_mentions)
        conversion_layout.addWidget(self.convert_text_button, 0, 0)
        
        self.convert_line_button = QPushButton("Convert Line to [char:ID]")
        self.convert_line_button.clicked.connect(self.convert_line_mentions)
        conversion_layout.addWidget(self.convert_line_button, 0, 1)
        
        self.revert_text_button = QPushButton("Revert Text to @mentions")
        self.revert_text_button.clicked.connect(self.revert_text_mentions)
        conversion_layout.addWidget(self.revert_text_button, 1, 0)
        
        self.revert_line_button = QPushButton("Revert Line to @mentions")
        self.revert_line_button.clicked.connect(self.revert_line_mentions)
        conversion_layout.addWidget(self.revert_line_button, 1, 1)
        
        # Labels to show conversion results
        result_group = QGroupBox("Character IDs in Text")
        result_layout = QVBoxLayout(result_group)
        
        self.result_label = QLabel("Character IDs will appear here")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setWordWrap(True)
        result_layout.addWidget(self.result_label)
        
        # Add all groups to main layout
        main_layout.addWidget(text_edit_group)
        main_layout.addWidget(line_edit_group)
        main_layout.addWidget(conversion_group)
        main_layout.addWidget(result_group)
        
        self.setCentralWidget(central_widget)
    
    def on_text_character_selected(self, character_name):
        """Handle character selection in the QTextEdit."""
        print(f"Character '{character_name}' selected in QTextEdit")
        # Call the completer's insert method to actually insert the tag
        self.text_completer.insert_character_tag(character_name)
    
    def on_line_character_selected(self, character_name):
        """Handle character selection in the QLineEdit."""
        print(f"Character '{character_name}' selected in QLineEdit")
        # Call the completer's insert method to actually insert the tag
        self.line_completer.insert_character_tag(character_name)
    
    def convert_text_mentions(self):
        """Convert @mentions to [char:ID] in the QTextEdit."""
        text = self.text_edit.toPlainText()
        converted = convert_mentions_to_char_refs(text, self.characters)
        self.text_edit.setPlainText(converted)
        self.update_character_ids()
    
    def convert_line_mentions(self):
        """Convert @mentions to [char:ID] in the QLineEdit."""
        text = self.line_edit.text()
        converted = convert_mentions_to_char_refs(text, self.characters)
        self.line_edit.setText(converted)
        self.update_character_ids()
    
    def revert_text_mentions(self):
        """Convert [char:ID] back to @mentions in the QTextEdit."""
        text = self.text_edit.toPlainText()
        converted = convert_char_refs_to_mentions(text, self.characters)
        self.text_edit.setPlainText(converted)
        self.update_character_ids()
    
    def revert_line_mentions(self):
        """Convert [char:ID] back to @mentions in the QLineEdit."""
        text = self.line_edit.text()
        converted = convert_char_refs_to_mentions(text, self.characters)
        self.line_edit.setText(converted)
        self.update_character_ids()
    
    def update_character_ids(self):
        """Extract and display character IDs from the text content."""
        text_ids = extract_character_ids_from_text(self.text_edit.toPlainText())
        line_ids = extract_character_ids_from_text(self.line_edit.text())
        
        message = "<b>Character IDs in QTextEdit:</b> "
        message += ", ".join([str(char_id) for char_id in text_ids]) if text_ids else "None"
        message += "<br><b>Character IDs in QLineEdit:</b> "
        message += ", ".join([str(char_id) for char_id in line_ids]) if line_ids else "None"
        
        self.result_label.setText(message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Create and show the application
    example = CharacterCompleterExample()
    example.show()
    
    sys.exit(app.exec()) 