from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QListWidget, QListWidgetItem,
    QAbstractItemView, QFrame, QLineEdit, QScrollArea,
    QRadioButton, QButtonGroup, QToolButton, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor, QIcon
from typing import Dict, List, Any, Optional
import sqlite3

class RelationshipTypesManager(QMainWindow):
    """Window for managing relationship types organized by categories."""
    
    def __init__(self, parent=None, db_conn=None):
        super().__init__(parent)
        self.setWindowTitle("Relationship Types Manager")
        self.resize(800, 600)  # Wider window to accommodate the edit section
        
        # Store database connection
        self.db_conn = db_conn
        
        # Track current edit state
        self.current_type_id = None
        self.editing_mode = False
        
        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Use horizontal layout for main sections
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)
        
        # Left section for list view
        self.left_section = QWidget()
        self.left_layout = QVBoxLayout(self.left_section)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setSpacing(10)
        
        # Header label
        self.header_label = QLabel("Categories / Relationship Types")
        font = QFont()
        font.setPointSize(12)
        self.header_label.setFont(font)
        self.left_layout.addWidget(self.header_label)
        
        # List widget for categories and relationship types
        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # Enable drag and drop for reordering
        self.list_widget.setDragEnabled(True)
        self.list_widget.setAcceptDrops(True)
        self.list_widget.setDropIndicatorShown(True)
        
        # Connect double-click event
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        self.left_layout.addWidget(self.list_widget)
        
        # New Relationship button
        self.new_relationship_button = QPushButton("New Relationship")
        self.new_relationship_button.clicked.connect(self.on_new_relationship)
        self.left_layout.addWidget(self.new_relationship_button, alignment=Qt.AlignmentFlag.AlignRight)
        
        # Button layout for Cancel and Save
        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(10)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumWidth(120)
        self.cancel_button.clicked.connect(self.close)
        self.button_layout.addWidget(self.cancel_button)
        
        # Save button
        self.save_button = QPushButton("Save")
        self.save_button.setMinimumWidth(120)
        self.button_layout.addWidget(self.save_button)
        
        self.left_layout.addLayout(self.button_layout)
        
        # Right section for edit view
        self.right_section = QWidget()
        self.right_layout = QVBoxLayout(self.right_section)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(15)
        
        # Create the edit form
        self.create_edit_form()
        
        # Add sections to main layout
        self.main_layout.addWidget(self.left_section, 1)  # 1:1 ratio
        self.main_layout.addWidget(self.right_section, 1)
        
        # Load data from database, or use mock data if no connection
        if self.db_conn:
            self.load_relationship_data()
        else:
            self.populate_mock_data()
            
        # Initially hide the edit section
        self.right_section.setVisible(False)
    
    def create_edit_form(self):
        """Create the form for adding/editing relationship types."""
        # Name input
        name_label = QLabel("Name")
        self.name_input = QLineEdit()
        self.name_input.textChanged.connect(self.validate_name)
        self.right_layout.addWidget(name_label)
        self.right_layout.addWidget(self.name_input)
        
        # Name validation label
        self.name_validation_label = QLabel("")
        self.right_layout.addWidget(self.name_validation_label)
        
        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setFixedHeight(1)
        self.right_layout.addWidget(line)
        
        # Category section
        category_label = QLabel("Category")
        self.right_layout.addWidget(category_label)
        
        # Category input with dropdown
        self.category_input = QLineEdit()
        self.category_input.setReadOnly(True)  # Make it read-only since it's just a display field
        self.right_layout.addWidget(self.category_input)
        
        # Category list
        self.category_list = QListWidget()
        self.category_list.setMaximumHeight(150)
        self.category_list.itemClicked.connect(self.on_category_selected)
        self.right_layout.addWidget(self.category_list)
        
        # Inverse relationship section
        inverse_label = QLabel("Inverse")
        self.right_layout.addWidget(inverse_label)
        
        # Inverse input with search icon
        inverse_input_layout = QHBoxLayout()
        self.inverse_input = QLineEdit()
        self.inverse_input.setReadOnly(True)
        
        # Add search icon button
        search_button = QToolButton()
        search_button.setText("🔍")
        inverse_input_layout.addWidget(self.inverse_input)
        inverse_input_layout.addWidget(search_button)
        self.right_layout.addLayout(inverse_input_layout)
        
        # Inverse list widget
        self.inverse_list = QListWidget()
        self.inverse_list.setMaximumHeight(150)
        self.inverse_list.setEnabled(False)  # Initially disabled until category is selected
        self.inverse_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)  # Enable multi-selection
        self.inverse_list.itemClicked.connect(self.on_inverse_selected)
        self.right_layout.addWidget(self.inverse_list)
        
        # Gender context section
        gender_context_label = QLabel("Gender Context:")
        self.right_layout.addWidget(gender_context_label)
        
        # Gender context buttons
        gender_button_layout = QHBoxLayout()
        
        # Create button group for radio-like behavior
        self.gender_group = QButtonGroup(self)
        
        # Masculine button
        self.masculine_button = QToolButton()
        self.masculine_button.setText("♂")
        self.masculine_button.setToolTip("Masculine")
        self.masculine_button.setCheckable(True)
        self.masculine_button.setFixedSize(40, 40)
        self.gender_group.addButton(self.masculine_button, 1)
        
        # Feminine button
        self.feminine_button = QToolButton()
        self.feminine_button.setText("♀")
        self.feminine_button.setToolTip("Feminine")
        self.feminine_button.setCheckable(True)
        self.feminine_button.setFixedSize(40, 40)
        self.gender_group.addButton(self.feminine_button, 2)
        
        # Neutral button
        self.neutral_button = QToolButton()
        self.neutral_button.setText("⚲")
        self.neutral_button.setToolTip("Neutral")
        self.neutral_button.setCheckable(True)
        self.neutral_button.setFixedSize(40, 40)
        self.gender_group.addButton(self.neutral_button, 3)
        
        # Default to neutral
        self.neutral_button.setChecked(True)
        
        # Add buttons to layout
        gender_button_layout.addWidget(self.masculine_button)
        gender_button_layout.addWidget(self.feminine_button)
        gender_button_layout.addWidget(self.neutral_button)
        gender_button_layout.addStretch(1)  # Add stretch to keep buttons left-aligned
        
        self.right_layout.addLayout(gender_button_layout)
        
        # Separator line
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setFrameShadow(QFrame.Shadow.Sunken)
        line2.setFixedHeight(1)
        self.right_layout.addWidget(line2)
        
        # Action buttons
        action_button_layout = QHBoxLayout()
        
        # Add stretch to push buttons to the right
        action_button_layout.addStretch(1)
        
        # Cancel edit button
        self.cancel_edit_button = QPushButton("Cancel")
        self.cancel_edit_button.setMinimumWidth(100)
        self.cancel_edit_button.clicked.connect(self.cancel_edit)
        action_button_layout.addWidget(self.cancel_edit_button)
        
        # Save edit button
        self.save_edit_button = QPushButton("Save")
        self.save_edit_button.setMinimumWidth(100)
        self.save_edit_button.clicked.connect(self.save_edit)
        action_button_layout.addWidget(self.save_edit_button)
        
        self.right_layout.addLayout(action_button_layout)
        
        # Add spacer at the bottom
        self.right_layout.addStretch(1)
    
    def validate_name(self, text):
        """Validate the relationship type name."""
        if not text:
            self.name_validation_label.setText("")
            return
        
        # Check if name already exists in the database
        if self.db_conn:
            cursor = self.db_conn.cursor()
            query = "SELECT COUNT(*) FROM relationship_types_new WHERE name = ? AND type_id != ?"
            type_id = self.current_type_id if self.current_type_id is not None else -1
            cursor.execute(query, (text.lower(), type_id))
            count = cursor.fetchone()[0]
            
            if count > 0:
                self.name_validation_label.setText("Already exists")
                self.name_validation_label.setStyleSheet("color: #ff5252;")  # Red color
                return False
        
        # If we get here, the name is valid
        self.name_validation_label.setText("Ok")
        self.name_validation_label.setStyleSheet("color: #4caf50;")  # Green color
        return True
    
    def on_category_selected(self, item):
        """Handle category selection."""
        category_name = item.text()
        self.category_input.setText(category_name)
        
        # Enable the inverse list
        self.inverse_list.setEnabled(True)
        
        # Load relationship types for this category
        self.load_inverse_relationships(category_name)
    
    def on_inverse_selected(self, item):
        """Handle inverse relationship selection."""
        # Get all selected items
        selected_items = self.inverse_list.selectedItems()
        inverse_names = [item.text() for item in selected_items]
        
        # Display all selected inverses in the input field
        self.inverse_input.setText(", ".join(inverse_names))
    
    def load_inverse_relationships(self, category_name):
        """Load relationship types for the selected category to populate the inverse list."""
        self.inverse_list.clear()
        
        if not self.db_conn:
            return
            
        try:
            cursor = self.db_conn.cursor()
            
            # First get the category ID
            cursor.execute("SELECT id FROM relationship_categories WHERE name = ?", (category_name,))
            result = cursor.fetchone()
            
            if not result:
                return
                
            category_id = result[0]
            
            # Get relationship types for this category
            cursor.execute("""
                SELECT label FROM relationship_types_new 
                WHERE category_id = ? 
                ORDER BY label
            """, (category_id,))
            
            for row in cursor.fetchall():
                self.inverse_list.addItem(row[0])
                
        except Exception as e:
            print(f"Error loading inverse relationships: {e}")
    
    def on_new_relationship(self):
        """Handle new relationship button click."""
        # Reset the form
        self.current_type_id = None
        self.editing_mode = False
        self.name_input.clear()
        self.name_validation_label.clear()
        self.category_input.clear()
        self.inverse_input.clear()
        self.neutral_button.setChecked(True)
        
        # Show the edit section
        self.right_section.setVisible(True)
        
        # Load categories
        self.load_categories()
        
        # Focus the name input
        self.name_input.setFocus()
    
    def on_item_double_clicked(self, item):
        """Handle double-click on a relationship type item."""
        # Skip if this is a category item (non-selectable)
        if not (item.flags() & Qt.ItemFlag.ItemIsSelectable):
            return
            
        # Get the type_id stored in the item
        type_id = item.data(Qt.ItemDataRole.UserRole)
        
        # If no type_id, this isn't a relationship type item
        if type_id is None:
            return
            
        # Load the relationship type details
        self.load_relationship_type(type_id)
        
        # Show the edit section
        self.right_section.setVisible(True)
    
    def load_relationship_type(self, type_id):
        """Load relationship type details for editing."""
        if not self.db_conn:
            return
            
        try:
            cursor = self.db_conn.cursor()
            
            # Get relationship type details
            cursor.execute("""
                SELECT rt.name, rt.label, rt.gender_context, c.name as category_name, rt.type_id
                FROM relationship_types_new rt
                JOIN relationship_categories c ON rt.category_id = c.id
                WHERE rt.type_id = ?
            """, (type_id,))
            
            result = cursor.fetchone()
            
            if not result:
                return
                
            name, label, gender_context, category_name, type_id = result
            
            # Get inverse relationship(s) if any
            cursor.execute("""
                SELECT rt.label
                FROM relationship_type_inverses rti
                JOIN relationship_types_new rt ON rti.inverse_type_id = rt.type_id
                WHERE rti.type_id = ?
            """, (type_id,))
            
            inverse_results = cursor.fetchall()
            inverse_names = [result[0] for result in inverse_results]
            
            # Set form values
            self.current_type_id = type_id
            self.editing_mode = True
            self.name_input.setText(label)
            self.name_validation_label.clear()  # Clear because we're editing an existing item
            self.category_input.setText(category_name)
            self.inverse_input.setText(", ".join(inverse_names))
            
            # Set gender context
            if gender_context == 'masculine':
                self.masculine_button.setChecked(True)
            elif gender_context == 'feminine':
                self.feminine_button.setChecked(True)
            else:
                self.neutral_button.setChecked(True)
                
            # Load categories and inverses
            self.load_categories()
            self.load_inverse_relationships(category_name)
            self.inverse_list.setEnabled(True)
            
            # Pre-select inverses in the list
            for i in range(self.inverse_list.count()):
                item = self.inverse_list.item(i)
                if item.text() in inverse_names:
                    item.setSelected(True)
            
        except Exception as e:
            print(f"Error loading relationship type: {e}")
    
    def load_categories(self):
        """Load relationship categories into the category list."""
        self.category_list.clear()
        
        if not self.db_conn:
            return
            
        try:
            cursor = self.db_conn.cursor()
            
            # Get all categories
            cursor.execute("""
                SELECT name 
                FROM relationship_categories 
                ORDER BY display_order, name
            """)
            
            for row in cursor.fetchall():
                self.category_list.addItem(row[0])
                
        except Exception as e:
            print(f"Error loading categories: {e}")
    
    def cancel_edit(self):
        """Cancel the relationship type edit."""
        self.right_section.setVisible(False)
        self.current_type_id = None
        self.editing_mode = False
    
    def save_edit(self):
        """Save the relationship type."""
        # Validate inputs
        name = self.name_input.text().strip()
        category = self.category_input.text().strip()
        
        # Get selected inverse relationships
        selected_items = self.inverse_list.selectedItems()
        selected_inverses = [item.text() for item in selected_items]
        
        # Determine gender context
        if self.masculine_button.isChecked():
            gender_context = 'masculine'
        elif self.feminine_button.isChecked():
            gender_context = 'feminine'
        else:
            gender_context = 'neutral'
        
        # Validate required fields
        if not name:
            self.show_error("Name is required")
            return
            
        if not category:
            self.show_error("Category is required")
            return
            
        # Validate name uniqueness
        if not self.validate_name(name):
            self.show_error("Relationship type name already exists")
            return
            
        # Save to database
        if self.db_conn:
            try:
                cursor = self.db_conn.cursor()
                
                # Get category ID
                cursor.execute("SELECT id FROM relationship_categories WHERE name = ?", (category,))
                category_result = cursor.fetchone()
                
                if not category_result:
                    self.show_error("Selected category not found")
                    return
                    
                category_id = category_result[0]
                
                # Get inverse IDs if selected
                inverse_ids = []
                for inverse in selected_inverses:
                    cursor.execute("""
                        SELECT type_id 
                        FROM relationship_types_new 
                        WHERE label = ? AND category_id = ?
                    """, (inverse, category_id))
                    inverse_result = cursor.fetchone()
                    if inverse_result:
                        inverse_ids.append(inverse_result[0])
                
                if self.editing_mode and self.current_type_id:
                    # Update existing relationship type
                    cursor.execute("""
                        UPDATE relationship_types_new
                        SET name = ?, label = ?, gender_context = ?, category_id = ?
                        WHERE type_id = ?
                    """, (name.lower(), name, gender_context, category_id, self.current_type_id))
                    
                    # Handle inverse relationships
                    # Remove any existing inverses
                    cursor.execute("DELETE FROM relationship_type_inverses WHERE type_id = ?", (self.current_type_id,))
                    
                    # Add new inverses
                    for inverse_id in inverse_ids:
                        cursor.execute("""
                            INSERT INTO relationship_type_inverses (type_id, inverse_type_id)
                            VALUES (?, ?)
                        """, (self.current_type_id, inverse_id))
                else:
                    # Insert new relationship type
                    cursor.execute("""
                        INSERT INTO relationship_types_new (name, label, gender_context, category_id)
                        VALUES (?, ?, ?, ?)
                    """, (name.lower(), name, gender_context, category_id))
                    
                    # Get the new type_id
                    cursor.execute("SELECT last_insert_rowid()")
                    new_type_id = cursor.fetchone()[0]
                    
                    # Add inverse relationships if selected
                    for inverse_id in inverse_ids:
                        cursor.execute("""
                            INSERT INTO relationship_type_inverses (type_id, inverse_type_id)
                            VALUES (?, ?)
                        """, (new_type_id, inverse_id))
                
                # Commit changes
                self.db_conn.commit()
                
                # Refresh the list
                self.load_relationship_data()
                
                # Hide the edit section
                self.right_section.setVisible(False)
                
            except Exception as e:
                print(f"Error saving relationship type: {e}")
                self.show_error(f"Error saving: {str(e)}")
    
    def show_error(self, message):
        """Show an error message dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Error")
        layout = QVBoxLayout(dialog)
        label = QLabel(message)
        layout.addWidget(label)
        button = QPushButton("OK")
        button.clicked.connect(dialog.accept)
        layout.addWidget(button)
        dialog.exec()
    
    def load_relationship_data(self):
        """Load relationship categories and types from the database."""
        try:
            # Clear the list
            self.list_widget.clear()
            
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