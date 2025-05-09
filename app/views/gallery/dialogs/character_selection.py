from typing import Optional, Dict, List, Any

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt

class CharacterSelectionDialog(QDialog):
    """Dialog for selecting a character."""
    
    def __init__(self, db_conn, story_id: int, parent=None):
        """Initialize the dialog.
        
        Args:
            db_conn: Database connection
            story_id: ID of the story
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.story_id = story_id
        self.selected_character_id = None
        
        self.setWindowTitle("Select Character")
        self.init_ui()
        self.load_characters()
        
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel("Select a character to tag:")
        layout.addWidget(instructions)
        
        # Character list
        self.character_list = QListWidget()
        self.character_list.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self.character_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        select_button = QPushButton("Select")
        select_button.clicked.connect(self.accept)
        select_button.setDefault(True)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(select_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.resize(300, 400)
        
    def load_characters(self):
        """Load the characters from the database."""
        cursor = self.db_conn.cursor()
        
        # Get all characters in this story
        cursor.execute("""
            SELECT id, name, character_type FROM characters 
            WHERE story_id = ? 
            ORDER BY name
        """, (self.story_id,))
        
        characters = cursor.fetchall()
        
        for character in characters:
            character_id, name, character_type = character
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, character_id)
            self.character_list.addItem(item)
    
    def get_selected_character_id(self) -> Optional[int]:
        """Get the ID of the selected character.
        
        Returns:
            The ID of the selected character, or None if no character is selected
        """
        return self.selected_character_id
    
    def accept(self):
        """Accept the dialog and store the selected character ID."""
        selected_items = self.character_list.selectedItems()
        if selected_items:
            self.selected_character_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        super().accept()
