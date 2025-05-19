from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QListWidget, QListWidgetItem,
    QAbstractItemView, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from app.utils.theme_manager import ThemeManager

class RelationshipTypesManager(QMainWindow):
    """Window for managing relationship types organized by categories."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Relationship Types Manager")
        self.resize(500, 600)
        
        # No need to explicitly apply theme - it should be applied application-wide
        # We'll inherit the theme from the parent application
        
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
        
        # For this stage, just populate with mock data
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
    
    def _add_relationship_item(self, type_name):
        """Add a relationship type item to the list."""
        item = QListWidgetItem(f"  {type_name}")  # Indent for visual hierarchy
        item.setForeground(QColor("#e0e0e0"))  # Light gray text for contrast
        self.list_widget.addItem(item) 