#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Decision Point Dialog for The Plot Thickens application.

This module contains the dialog for creating and editing decision points.
"""

import os
from typing import List, Dict, Any, Optional, Tuple, Callable

from PyQt6.QtWidgets import (
    QDialog, QTabWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QRadioButton, QWidget, QScrollArea, QFrame, 
    QSizePolicy, QMessageBox, QInputDialog, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings
from PyQt6.QtGui import QKeySequence, QShortcut, QFont

from app.db_sqlite import (
    create_decision_point, update_decision_point, get_decision_point,
    get_decision_options, add_decision_option, update_decision_option,
    delete_decision_option, get_story_characters
)
from app.utils.ocr_widget import OCRWidget
from app.utils.character_completer import CharacterCompleter


class OptionItem:
    """Class representing a decision option item in the UI."""
    
    def __init__(self, widget: QWidget, text: str, option_id: Optional[int] = None):
        """Initialize the option item.
        
        Args:
            widget: The widget representing this option in the UI
            text: The text of this option
            option_id: Database ID of this option (if existing)
        """
        self.widget = widget
        self.text = text
        self.option_id = option_id
        self.radio_button = None
        self.order_input = None
        self.is_selected = False
        self.played_order = None


class DecisionPointDialog(QDialog):
    """Dialog for creating and editing decision points."""
    
    def __init__(self, db_conn, story_id: int, parent=None, decision_point_id: Optional[int] = None):
        """Initialize the decision point dialog.
        
        Args:
            db_conn: Database connection
            story_id: ID of the story
            parent: Parent widget
            decision_point_id: ID of the decision point to edit (None for new)
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.story_id = story_id
        self.decision_point_id = decision_point_id
        self.is_ordered_list = False
        self.options_list = []  # List of OptionItem objects
        self.radio_button_group = []  # For exclusive radio button behavior
        
        # Set window title based on mode
        if decision_point_id:
            self.setWindowTitle("Edit decision point")
        else:
            self.setWindowTitle("Add decision point")
        
        self.init_ui()
        
        # Load data if editing existing decision point
        if decision_point_id:
            self.load_decision_point_data()
        
        # Load characters for autocompletion
        self.load_characters()
        
        # Setup keyboard shortcuts
        self.setup_shortcuts()
    
    def setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts for the dialog."""
        # Create OCR shortcut (Ctrl+O)
        self.ocr_shortcut = QShortcut(QKeySequence("Ctrl+O"), self)
        self.ocr_shortcut.activated.connect(self.activate_ocr)
    
    def activate_ocr(self) -> None:
        """Activate the OCR tab and focus it."""
        # Switch to OCR tab
        self.tab_widget.setCurrentIndex(1)  # Index 1 is the OCR tab
    
    def load_characters(self) -> None:
        """Load characters for autocompletion."""
        try:
            # Get all characters for this story
            characters = get_story_characters(self.db_conn, self.story_id)
            
            # Set characters in the completer
            self.character_completer.set_characters(characters)
            
        except Exception as e:
            print(f"Error loading characters for autocompletion: {e}")
    
    def on_character_selected(self, character_name: str) -> None:
        """Handle character selection from the completer.
        
        Args:
            character_name: Name of the selected character
        """
        # Insert the character tag at the current cursor position
        self.character_completer.insert_character_tag(character_name)
    
    def init_ui(self) -> None:
        """Initialize the user interface."""
        # Set dialog size
        self.resize(600, 700)
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create Decision Point tab
        decision_point_tab = QWidget()
        decision_point_layout = QVBoxLayout(decision_point_tab)
        
        # Decision point title input
        title_layout = QHBoxLayout()
        title_label = QLabel("Decision point:")
        self.title_edit = QLineEdit()
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.title_edit)
        decision_point_layout.addLayout(title_layout)
        
        # Setup character autocompletion for the title field
        # Users can type "@" followed by character names to get autocompletion suggestions
        # This helps with remembering character names and saves typing time
        self.character_completer = CharacterCompleter()
        self.character_completer.attach_to_widget(self.title_edit)
        self.character_completer.character_selected.connect(self.on_character_selected)
        
        # Add option button
        self.add_option_button = QPushButton("Add option")
        self.add_option_button.clicked.connect(self.on_add_option)
        decision_point_layout.addWidget(self.add_option_button)
        
        # Options label
        options_label = QLabel("Options")
        decision_point_layout.addWidget(options_label)
        
        # Create options area
        self.options_area = QWidget()
        self.options_layout = QVBoxLayout(self.options_area)
        self.options_layout.setContentsMargins(5, 5, 5, 5)
        self.options_layout.setSpacing(5)
        
        # Create scroll area for options
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.options_area)
        scroll_area.setFrameShape(QFrame.Shape.StyledPanel)
        
        # Add scroll area to layout
        decision_point_layout.addWidget(scroll_area)
        
        # Add convert button
        self.convert_button = QPushButton("Convert to ordered list")
        self.convert_button.clicked.connect(self.toggle_ordered_list)
        decision_point_layout.addWidget(self.convert_button)
        
        # Add Decision Point tab to tab widget
        self.tab_widget.addTab(decision_point_tab, "Decision Point")
        
        # Create OCR Tool tab
        ocr_tab = QWidget()
        ocr_layout = QVBoxLayout(ocr_tab)
        
        # Create OCR widget
        self.ocr_widget = OCRWidget(parent=ocr_tab)
        self.ocr_widget.set_on_text_extracted_callback(self.on_text_extracted)
        
        # Add usage instructions
        instructions_label = QLabel(
            "Use Ctrl+O to quickly access OCR. Extract text to add as a new option."
        )
        instructions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ocr_layout.addWidget(instructions_label)
        
        # Add OCR widget to layout
        ocr_layout.addWidget(self.ocr_widget)
        
        # Add OCR tab to tab widget
        self.tab_widget.addTab(ocr_tab, "OCR Tool")
        
        # Create Source Lookup tab
        source_lookup_tab = QWidget()
        source_lookup_layout = QVBoxLayout(source_lookup_tab)
        
        # Create source lookup widget
        self.create_source_lookup_widget(source_lookup_layout)
        
        # Add Source Lookup tab to tab widget
        self.tab_widget.addTab(source_lookup_tab, "Source Lookup")
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        # Save button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        # Add buttons to layout
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        # Add button layout to main layout
        main_layout.addLayout(button_layout)
    
    def on_text_extracted(self, text: str) -> None:
        """Handle text extracted from OCR.
        
        Args:
            text: The extracted text to add as option(s)
        """
        if text.strip():
            # Split text by line breaks and filter out empty lines
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            if len(lines) == 1:
                # Single line: add as one option (same as before)
                self.add_option(lines[0])
                
                # Switch back to the Decision Point tab
                self.tab_widget.setCurrentIndex(0)
                
                # Show confirmation
                QMessageBox.information(
                    self,
                    "Option Added",
                    f"Added new option from OCR text"
                )
            elif len(lines) > 1:
                # Multiple lines: add each line as a separate option
                for line in lines:
                    self.add_option(line)
                
                # Switch back to the Decision Point tab
                self.tab_widget.setCurrentIndex(0)
                
                # Show confirmation with count
                QMessageBox.information(
                    self,
                    "Options Added",
                    f"Added {len(lines)} options from OCR text:\n" + 
                    "\n".join(f"• {line}" for line in lines[:5]) +
                    (f"\n... and {len(lines) - 5} more" if len(lines) > 5 else "")
                )
    
    def on_add_option(self) -> None:
        """Handle add option button click."""
        option_text, ok = QInputDialog.getText(self, "Add Option", "Enter option text:")
        if ok and option_text.strip():
            self.add_option(option_text)
    
    def add_option(self, option_text: str, is_selected: bool = False, 
                  played_order: Optional[int] = None, option_id: Optional[int] = None) -> None:
        """Add an option to the decision point.
        
        Args:
            option_text: Text of the option
            is_selected: Whether the option is selected
            played_order: Order value for ordered lists
            option_id: Database ID of the option (if existing)
        """
        # Create container for option
        option_container = QWidget()
        option_layout = QHBoxLayout(option_container)
        option_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create appropriate UI based on current mode
        if self.is_ordered_list:
            # For ordered lists, show number input and text label
            order_input = QLineEdit()
            order_input.setFixedWidth(30)
            if played_order is not None:
                order_input.setText(str(played_order))
            
            # Create label for the text
            text_label = QLabel(option_text)
            text_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            
            # Add to layout
            option_layout.addWidget(order_input)
            option_layout.addWidget(text_label)
            
            # Create option item
            option_item = OptionItem(option_container, option_text, option_id)
            option_item.order_input = order_input
            option_item.played_order = played_order
        else:
            # For single choice, create radio button
            radio_button = QRadioButton(option_text)
            
            # Add to radio button group for exclusive behavior
            if is_selected and self.radio_button_group:
                # If this one should be selected, deselect others
                for rb in self.radio_button_group:
                    rb.setChecked(False)
            
            radio_button.setChecked(is_selected)
            
            # Connect radio button toggle to handle exclusive selection
            radio_button.toggled.connect(lambda checked: self.handle_radio_toggle(radio_button, checked))
            self.radio_button_group.append(radio_button)
            
            # Add to layout
            option_layout.addWidget(radio_button)
            
            # Create option item
            option_item = OptionItem(option_container, option_text, option_id)
            option_item.radio_button = radio_button
            option_item.is_selected = is_selected
        
        # Add delete button
        delete_button = QPushButton("✖")
        delete_button.setFixedWidth(25)
        delete_button.setFixedHeight(25)
        delete_button.clicked.connect(lambda: self.remove_option(option_item))
        option_layout.addWidget(delete_button)
        
        # Add to options list
        self.options_list.append(option_item)
        
        # Add to UI
        self.options_layout.addWidget(option_container)
    
    def handle_radio_toggle(self, clicked_button: QRadioButton, checked: bool) -> None:
        """Handle radio button toggling to ensure exclusive selection.
        
        Args:
            clicked_button: The radio button that was toggled
            checked: Whether the button was checked or unchecked
        """
        if checked:
            # When a button is checked, uncheck all others
            for radio_button in self.radio_button_group:
                if radio_button != clicked_button:
                    radio_button.setChecked(False)
    
    def remove_option(self, option_item: OptionItem) -> None:
        """Remove an option from the decision point.
        
        Args:
            option_item: The option item to remove
        """
        # Remove from UI
        option_item.widget.setParent(None)
        option_item.widget.deleteLater()
        
        # Remove from list
        self.options_list.remove(option_item)
        
        # Remove from radio button group if applicable
        if option_item.radio_button in self.radio_button_group:
            self.radio_button_group.remove(option_item.radio_button)
    
    def toggle_ordered_list(self) -> None:
        """Toggle between single choice and ordered list modes."""
        # Toggle state
        self.is_ordered_list = not self.is_ordered_list
        
        # Update button text
        if self.is_ordered_list:
            self.convert_button.setText("Convert to single choice")
        else:
            self.convert_button.setText("Convert to ordered list")
        
        # Remember current options data
        options_data = []
        for opt in self.options_list:
            data = {
                "text": opt.text,
                "option_id": opt.option_id
            }
            
            if self.is_ordered_list:
                # Converting to ordered list, get selection state from radio buttons
                data["is_selected"] = opt.radio_button.isChecked() if opt.radio_button else False
                data["played_order"] = None  # No order yet in the new mode
            else:
                # Converting to single choice, get order values from inputs
                if opt.order_input and opt.order_input.text().strip():
                    try:
                        data["played_order"] = int(opt.order_input.text())
                    except ValueError:
                        data["played_order"] = None
                else:
                    data["played_order"] = None
                
                # Default selection to first item
                data["is_selected"] = False
            
            options_data.append(data)
        
        # Clear existing options
        for opt in self.options_list.copy():
            self.remove_option(opt)
        
        # Recreate with new mode
        for data in options_data:
            self.add_option(
                data["text"],
                is_selected=data.get("is_selected", False),
                played_order=data.get("played_order"),
                option_id=data.get("option_id")
            )
        
        # Select first option in single choice mode if nothing selected
        if not self.is_ordered_list and self.options_list:
            any_selected = any(opt.radio_button.isChecked() for opt in self.options_list if opt.radio_button)
            if not any_selected and self.options_list[0].radio_button:
                self.options_list[0].radio_button.setChecked(True)
        
        # Reset radio button group when changing modes
        self.radio_button_group = []
    
    def load_decision_point_data(self) -> None:
        """Load data for an existing decision point."""
        try:
            # Get decision point data
            decision_point = get_decision_point(self.db_conn, self.decision_point_id)
            if not decision_point:
                QMessageBox.critical(self, "Error", "Failed to load decision point data.")
                self.reject()
                return
            
            # Set title
            self.title_edit.setText(decision_point.get("title", ""))
            
            # Set ordered list mode
            self.is_ordered_list = bool(decision_point.get("is_ordered_list", 0))
            if self.is_ordered_list:
                self.convert_button.setText("Convert to single choice")
            
            # Get options
            options = get_decision_options(self.db_conn, self.decision_point_id)
            
            # Add options to UI
            for option in options:
                self.add_option(
                    option.get("text", ""),
                    is_selected=bool(option.get("is_selected", 0)),
                    played_order=option.get("played_order"),
                    option_id=option.get("id")
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading decision point: {str(e)}")
            self.reject()
    
    def accept(self) -> None:
        """Handle dialog acceptance (Save button)."""
        # Validate input
        title = self.title_edit.text().strip()
        if not title:
            # Auto-generate title if none provided
            existing_count = self.get_existing_decision_points_count()
            title = f"Decision Point {existing_count + 1}"
            self.title_edit.setText(title)
        
        # Validate number of options
        if len(self.options_list) < 2:
            QMessageBox.warning(self, "Invalid Input", "Please add at least two options.")
            return
        
        # Validate one option selected in single choice mode
        if not self.is_ordered_list:
            selected_count = sum(1 for opt in self.options_list if opt.radio_button and opt.radio_button.isChecked())
            if selected_count != 1:
                QMessageBox.warning(self, "Invalid Input", "Please select exactly one option.")
                return
        
        # Validate ordered list inputs if needed
        if self.is_ordered_list:
            option_count = len(self.options_list)
            order_values = []
            
            for option in self.options_list:
                if not option.order_input:
                    continue
                
                order_text = option.order_input.text().strip()
                
                # Check for empty textboxes
                if not order_text:
                    QMessageBox.warning(
                        self, 
                        "Invalid Input", 
                        f"Order number for option '{option.text}' cannot be empty."
                    )
                    return
                
                # Check for valid integers
                try:
                    order_value = int(order_text)
                    
                    # Check for positive integers
                    if order_value <= 0:
                        QMessageBox.warning(
                            self, 
                            "Invalid Input", 
                            f"Order number for option '{option.text}' must be a positive integer."
                        )
                        return
                    
                    # Check for values within range (1 to n)
                    if order_value > option_count:
                        QMessageBox.warning(
                            self, 
                            "Invalid Input", 
                            f"Order number for option '{option.text}' must be between 1 and {option_count}."
                        )
                        return
                    
                    # Add to list for checking duplicates
                    order_values.append(order_value)
                    
                except ValueError:
                    QMessageBox.warning(
                        self, 
                        "Invalid Input", 
                        f"Invalid order number for option '{option.text}'. Please enter a valid number."
                    )
                    return
            
            # Check for duplicate values
            if len(order_values) != len(set(order_values)):
                QMessageBox.warning(
                    self, 
                    "Invalid Input", 
                    "Duplicate order numbers detected. Each option must have a unique order number."
                )
                return
                
            # Check that all values from 1 to n are present
            expected_values = set(range(1, option_count + 1))
            if set(order_values) != expected_values:
                QMessageBox.warning(
                    self, 
                    "Invalid Input", 
                    f"Order numbers must include all values from 1 to {option_count} exactly once."
                )
                return
        
        try:
            # Create or update decision point
            if self.decision_point_id:
                # Update existing decision point
                success = update_decision_point(
                    self.db_conn,
                    self.decision_point_id,
                    title=title,
                    is_ordered_list=self.is_ordered_list
                )
                
                if not success:
                    QMessageBox.critical(self, "Error", "Failed to update decision point.")
                    return
            else:
                # Create new decision point
                self.decision_point_id = create_decision_point(
                    self.db_conn,
                    title,
                    self.story_id,
                    is_ordered_list=self.is_ordered_list
                )
                
                if not self.decision_point_id:
                    QMessageBox.critical(self, "Error", "Failed to create decision point.")
                    return
            
            # Handle options
            if self.is_ordered_list:
                # Process ordered list options
                for i, option in enumerate(self.options_list):
                    played_order = None
                    if option.order_input and option.order_input.text().strip():
                        try:
                            played_order = int(option.order_input.text())
                        except ValueError:
                            played_order = i + 1  # Default to index if invalid
                    
                    if option.option_id:
                        # Update existing option
                        update_decision_option(
                            self.db_conn,
                            option.option_id,
                            text=option.text,
                            is_selected=False,  # No selection in ordered list mode
                            display_order=i,
                            played_order=played_order
                        )
                    else:
                        # Add new option
                        add_decision_option(
                            self.db_conn,
                            self.decision_point_id,
                            option.text,
                            is_selected=False,  # No selection in ordered list mode
                            display_order=i,
                            played_order=played_order
                        )
            else:
                # Process single choice options
                for i, option in enumerate(self.options_list):
                    is_selected = option.radio_button.isChecked() if option.radio_button else False
                    
                    if option.option_id:
                        # Update existing option
                        update_decision_option(
                            self.db_conn,
                            option.option_id,
                            text=option.text,
                            is_selected=is_selected,
                            display_order=i,
                            played_order=None  # No order in single choice mode
                        )
                    else:
                        # Add new option
                        add_decision_option(
                            self.db_conn,
                            self.decision_point_id,
                            option.text,
                            is_selected=is_selected,
                            display_order=i,
                            played_order=None  # No order in single choice mode
                        )
            
            # Call parent accept to close the dialog
            super().accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving decision point: {str(e)}")
    
    def get_existing_decision_points_count(self) -> int:
        """Get the count of existing decision points for auto-numbering.
        
        Returns:
            Count of existing decision points
        """
        try:
            cursor = self.db_conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) as count FROM decision_points WHERE story_id = ?", 
                (self.story_id,)
            )
            result = cursor.fetchone()
            return result["count"] if result else 0
        except Exception as e:
            print(f"Error getting decision points count: {e}")
            return 0
    
    def create_source_lookup_widget(self, layout: QVBoxLayout) -> None:
        """Create the source lookup widget.
        
        Args:
            layout: Layout to add the widget to
        """
        # Status section
        status_group = QGroupBox("Source Analysis Status")
        status_layout = QVBoxLayout(status_group)
        
        self.source_status_label = QLabel()
        self.source_status_label.setWordWrap(True)
        status_layout.addWidget(self.source_status_label)
        
        layout.addWidget(status_group)
        
        # Search section
        search_group = QGroupBox("Menu Search")
        search_layout = QVBoxLayout(search_group)
        
        # Search input
        input_layout = QHBoxLayout()
        search_layout.addLayout(input_layout)
        
        input_layout.addWidget(QLabel("Search text:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter dialogue or menu choice text to find nearby menus...")
        input_layout.addWidget(self.search_input)
        
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.perform_source_search)
        input_layout.addWidget(self.search_button)
        
        # Results count
        self.results_count_label = QLabel("0 matches found")
        self.results_count_label.setStyleSheet("color: #666; font-style: italic;")
        search_layout.addWidget(self.results_count_label)
        
        # Results table
        self.results_table = QTableWidget(0, 5)
        self.results_table.setHorizontalHeaderLabels([
            "Label/Scene", "File", "Menu Choices", "Distance", "Menu Type"
        ])
        
        # Configure table
        header = self.results_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Label/Scene
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # File
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)           # Menu Choices
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Distance
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Menu Type
        
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        search_layout.addWidget(self.results_table)
        
        # Add to Options button
        self.add_to_options_button = QPushButton("Add to Options")
        self.add_to_options_button.clicked.connect(self.add_selected_menu_to_options)
        self.add_to_options_button.setEnabled(False)
        search_layout.addWidget(self.add_to_options_button)
        
        layout.addWidget(search_group)
        
        # Connect table selection to enable/disable button
        self.results_table.selectionModel().selectionChanged.connect(
            lambda: self.add_to_options_button.setEnabled(
                len(self.results_table.selectionModel().selectedRows()) > 0
            )
        )
        
        # Initialize UI state
        self.update_source_status()
        self.update_search_ui_state()
    
    def update_source_status(self) -> None:
        """Update the source analysis status indicator."""
        settings = QSettings("ThePlotThickens", "ThePlotThickens")
        source_path = settings.value(f"story_{self.story_id}/source_path", "")
        
        if source_path and source_path.strip():
            import os
            if os.path.exists(source_path):
                # Check for .rpy files
                rpy_count = 0
                try:
                    for root, dirs, files in os.walk(source_path):
                        rpy_count += len([f for f in files if f.endswith('.rpy')])
                except Exception:
                    rpy_count = 0
                
                if rpy_count > 0:
                    self.source_status_label.setText(
                        f"✅ Source analysis available\n"
                        f"📁 Path: {source_path}\n"
                        f"📄 Found {rpy_count} .rpy files"
                    )
                    self.source_status_label.setStyleSheet("color: #2d8f2d; font-weight: bold;")
                    self.source_analysis_available = True
                else:
                    self.source_status_label.setText(
                        f"⚠️ No .rpy files found in configured path\n"
                        f"📁 Path: {source_path}"
                    )
                    self.source_status_label.setStyleSheet("color: #cc7a00; font-weight: bold;")
                    self.source_analysis_available = False
            else:
                self.source_status_label.setText(
                    f"❌ Configured source path does not exist\n"
                    f"📁 Path: {source_path}"
                )
                self.source_status_label.setStyleSheet("color: #cc0000; font-weight: bold;")
                self.source_analysis_available = False
        else:
            self.source_status_label.setText(
                "❌ No source code path configured\n"
                "Please configure source path in the Source Analysis tab"
            )
            self.source_status_label.setStyleSheet("color: #cc0000; font-weight: bold;")
            self.source_analysis_available = False
    
    def update_search_ui_state(self) -> None:
        """Update the search UI based on source analysis availability."""
        has_source = getattr(self, 'source_analysis_available', False)
        self.search_input.setEnabled(has_source)
        self.search_button.setEnabled(has_source)
        
        if not has_source:
            self.search_input.setPlaceholderText("Source analysis not available - configure in Source Analysis tab")
            self.results_count_label.setText("Source analysis required for menu search")
    
    def perform_source_search(self) -> None:
        """Perform the source code search for menus."""
        search_text = self.search_input.text().strip()
        if not search_text:
            QMessageBox.warning(self, "Search", "Please enter text to search for.")
            return
        
        # Clear previous results
        self.results_table.setRowCount(0)
        self.results_count_label.setText("Searching...")
        
        try:
            # Get source path for current story
            settings = QSettings("ThePlotThickens", "ThePlotThickens")
            source_path = settings.value(f"story_{self.story_id}/source_path", "")
            
            if not source_path or not source_path.strip():
                QMessageBox.warning(self, "Search", "No source path configured for this story.")
                return
            
            # Initialize Ren'Py API
            import sys
            import os
            
            # Add the renpy-source-api directory to the Python path
            api_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'renpy-source-api')
            if api_dir not in sys.path:
                sys.path.insert(0, api_dir)
            
            # Import and initialize the API
            from core import RenpyProject
            
            # Create project instance
            project = RenpyProject(source_path)
            
            # Ensure project is analyzed
            if not project.is_analyzed:
                project.analyze()
            
            # Search for matches in dialogue and choices
            dialogue_matches = project.search_dialogue(search_text, case_sensitive=False)
            choice_matches = project.search_choices(search_text, case_sensitive=False)
            
            # Get all menus for proximity analysis
            all_menus = project.get_all_menus()
            
            # Process matches and find nearby menus
            menu_matches = []
            
            # Process dialogue matches
            for dialogue_match in dialogue_matches:
                nearby_menus = self.find_nearby_menus(dialogue_match, all_menus, "dialogue")
                menu_matches.extend(nearby_menus)
            
            # Process choice matches
            for choice_match in choice_matches:
                nearby_menus = self.find_nearby_menus(choice_match, all_menus, "choice")
                menu_matches.extend(nearby_menus)
            
            # Remove duplicates and sort by distance
            unique_matches = self.deduplicate_menu_matches(menu_matches)
            unique_matches.sort(key=lambda x: x['distance'])
            
            # Populate results table
            self.populate_results_table(unique_matches)
            
            # Update results count
            count = len(unique_matches)
            self.results_count_label.setText(f"{count} menu{'s' if count != 1 else ''} found")
            
        except Exception as e:
            QMessageBox.critical(self, "Search Error", f"Error during search: {str(e)}")
            self.results_count_label.setText("Search failed")
            print(f"Search error details: {e}")  # For debugging
    
    def add_selected_menu_to_options(self) -> None:
        """Add the selected menu choices to the options list."""
        # Placeholder for Step 3 implementation
        selected_rows = self.results_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        # TODO: Implement adding menu choices to options in Step 3
        QMessageBox.information(self, "Add to Options", "Add to Options functionality will be implemented in Step 3.")
    
    def find_nearby_menus(self, match: Dict[str, Any], all_menus: List[Any], match_type: str) -> List[Dict[str, Any]]:
        """Find menus near a text match.
        
        Args:
            match: Match data from dialogue or choice search
            all_menus: List of all menus in the project
            match_type: Type of match ('dialogue' or 'choice')
            
        Returns:
            List of nearby menu data
        """
        nearby_menus = []
        
        if match_type == "dialogue":
            match_file = match.get("file", "")
            match_line = match.get("line_number", 0)
        else:  # choice
            match_file = match.get("menu_context", {}).get("file", "")
            match_line = match.get("menu_context", {}).get("line", 0)
        
        if not match_file or not match_line:
            return nearby_menus
        
        # Find menus in the same file
        for menu in all_menus:
            menu_file = getattr(menu, 'file_path', '')
            menu_line = getattr(menu, 'line_number', 0)
            
            # Extract just the filename for comparison
            match_filename = os.path.basename(match_file)
            menu_filename = os.path.basename(menu_file)
            
            if match_filename == menu_filename:
                # Calculate distance
                distance = abs(match_line - menu_line)
                
                # Get menu choices
                choices = []
                if hasattr(menu, 'choices'):
                    choices = [choice.text for choice in menu.choices if hasattr(choice, 'text')]
                
                # Determine menu type
                menu_type = "Menu"
                if hasattr(menu, 'total_choices') and menu.total_choices == 1:
                    menu_type = "Single Choice"
                elif hasattr(menu, 'total_choices') and menu.total_choices > 1:
                    menu_type = "Multiple Choice"
                
                nearby_menus.append({
                    'label': getattr(menu, 'label_context', 'Unknown'),
                    'file': menu_filename,
                    'choices': choices,
                    'distance': distance,
                    'menu_type': menu_type,
                    'match_type': match_type,
                    'match_text': match.get("dialogue" if match_type == "dialogue" else "text", ""),
                    'menu_line': menu_line,
                    'match_line': match_line
                })
        
        return nearby_menus
    
    def deduplicate_menu_matches(self, menu_matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate menu matches.
        
        Args:
            menu_matches: List of menu match dictionaries
            
        Returns:
            List of unique menu matches
        """
        seen = set()
        unique_matches = []
        
        for match in menu_matches:
            # Create a key based on file, menu line, and choices
            key = (match['file'], match['menu_line'], tuple(match['choices']))
            
            if key not in seen:
                seen.add(key)
                unique_matches.append(match)
        
        return unique_matches
    
    def populate_results_table(self, matches: List[Dict[str, Any]]) -> None:
        """Populate the results table with menu matches.
        
        Args:
            matches: List of menu match dictionaries
        """
        self.results_table.setRowCount(len(matches))
        
        for row, match in enumerate(matches):
            # Label/Scene
            label_item = QTableWidgetItem(str(match.get('label', 'Unknown')))
            self.results_table.setItem(row, 0, label_item)
            
            # File
            file_item = QTableWidgetItem(match.get('file', ''))
            self.results_table.setItem(row, 1, file_item)
            
            # Menu Choices
            choices_text = " | ".join(match.get('choices', []))
            if len(choices_text) > 100:  # Truncate long choice lists
                choices_text = choices_text[:97] + "..."
            choices_item = QTableWidgetItem(choices_text)
            choices_item.setToolTip(" | ".join(match.get('choices', [])))  # Full text in tooltip
            self.results_table.setItem(row, 2, choices_item)
            
            # Distance
            distance_text = f"{match.get('distance', 0)} lines"
            distance_item = QTableWidgetItem(distance_text)
            self.results_table.setItem(row, 3, distance_item)
            
            # Menu Type
            menu_type_item = QTableWidgetItem(match.get('menu_type', 'Unknown'))
            self.results_table.setItem(row, 4, menu_type_item)
            
            # Store full match data for later use
            label_item.setData(Qt.ItemDataRole.UserRole, match)