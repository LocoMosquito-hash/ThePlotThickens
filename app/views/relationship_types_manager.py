from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QListWidget, QListWidgetItem,
    QAbstractItemView, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from typing import Dict, List, Any, Optional
import sqlite3

class RelationshipTypesManager(QMainWindow):
    """Window for managing relationship types organized by categories."""
    
    def __init__(self, parent=None, db_conn=None):
        super().__init__(parent)
        self.setWindowTitle("Relationship Types Manager")
        self.resize(500, 600)
        
        # Store database connection
        self.db_conn = db_conn
        
        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(10)
        
        # Header label
        self.header_label = QLabel("Categories / Relationship Types")
        font = QFont()
        font.setPointSize(12)
        self.header_label.setFont(font)
        self.main_layout.addWidget(self.header_label)
        
        # List widget for categories and relationship types
        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # Enable drag and drop for reordering
        self.list_widget.setDragEnabled(True)
        self.list_widget.setAcceptDrops(True)
        self.list_widget.setDropIndicatorShown(True)
        
        self.main_layout.addWidget(self.list_widget)
        
        # New Relationship button
        self.new_relationship_button = QPushButton("New Relationship")
        self.main_layout.addWidget(self.new_relationship_button, alignment=Qt.AlignmentFlag.AlignRight)
        
        # Button layout for Cancel and Save
        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(10)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumWidth(120)
        self.button_layout.addWidget(self.cancel_button)
        
        # Save button
        self.save_button = QPushButton("Save")
        self.save_button.setMinimumWidth(120)
        self.button_layout.addWidget(self.save_button)
        
        self.main_layout.addLayout(self.button_layout)
        
        # Connect signals
        self.cancel_button.clicked.connect(self.close)
        
        # Load data from database, or use mock data if no connection
        if self.db_conn:
            self.load_relationship_data()
        else:
            self.populate_mock_data()
    
    def load_relationship_data(self):
        """Load relationship categories and types from the database."""
        try:
            # Get all categories ordered by display_order
            cursor = self.db_conn.cursor()
            cursor.execute("""
                SELECT id, name 
                FROM relationship_categories 
                ORDER BY display_order, name
            """)
            categories = cursor.fetchall()
            
            # For each category, add the category and its relationship types
            for category_id, category_name in categories:
                self._add_category_item(category_name)
                
                # Get relationship types for this category
                cursor.execute("""
                    SELECT type_id, label, gender_context 
                    FROM relationship_types_new 
                    WHERE category_id = ? 
                    ORDER BY label
                """, (category_id,))
                relationship_types = cursor.fetchall()
                
                # Add relationship types to the list
                for type_id, label, gender_context in relationship_types:
                    self._add_relationship_item(label, type_id, gender_context)
                
                # If no relationship types for this category, add a placeholder
                if not relationship_types:
                    self._add_relationship_item("No relationship types defined", None, None)
            
            # If no categories, show a message
            if not categories:
                item = QListWidgetItem("No relationship categories defined")
                item.setForeground(QColor("#e0e0e0"))
                self.list_widget.addItem(item)
                
        except Exception as e:
            # Log error and revert to mock data
            print(f"Error loading relationship data: {e}")
            self.list_widget.clear()
            self.populate_mock_data()
    
    def populate_mock_data(self):
        """Populate the list with mock data for visualization."""
        # Family category
        self._add_category_item("Family")
        self._add_relationship_item("List item")
        self._add_relationship_item("List item")
        self._add_relationship_item("List item")
        self._add_relationship_item("List item")
        
        # Work category
        self._add_category_item("Work")
        self._add_relationship_item("List item")
        self._add_relationship_item("List item")
        self._add_relationship_item("List item")
        
        # Romantic category
        self._add_category_item("Romantic")
        self._add_relationship_item("List item")
        self._add_relationship_item("List item")
    
    def _add_category_item(self, category_name):
        """Add a category item to the list."""
        item = QListWidgetItem(category_name)
        # Make category items non-selectable
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
        # Style category items
        font = QFont()
        font.setBold(True)
        item.setFont(font)
        item.setBackground(QColor("#5e35b1"))  # Darker purple for categories
        item.setForeground(QColor("#ffffff"))  # White text for contrast
        self.list_widget.addItem(item)
    
    def _add_relationship_item(self, type_name, type_id=None, gender_context=None):
        """Add a relationship type item to the list.
        
        Args:
            type_name: Display name of the relationship type
            type_id: ID of the relationship type (optional)
            gender_context: Gender context of the relationship type (optional)
        """
        # Create indented display text with gender context indicator
        display_text = f"  {type_name}"
        
        # Add gender context indicator if available
        if gender_context:
            if gender_context == 'masculine':
                display_text += " (♂)"
            elif gender_context == 'feminine':
                display_text += " (♀)"
            # Neutral has no indicator
        
        # Create the item
        item = QListWidgetItem(display_text)
        item.setForeground(QColor("#e0e0e0"))  # Light gray text for contrast
        
        # Store type_id as item data for later reference
        if type_id is not None:
            item.setData(Qt.ItemDataRole.UserRole, type_id)
        
        self.list_widget.addItem(item) 