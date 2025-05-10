#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Decision Point Dialog for The Plot Thickens application.

This module contains the dialog for creating and editing decision points.
"""

from typing import List, Dict, Any, Optional, Tuple, Callable

from PyQt6.QtWidgets import (
    QDialog, QTabWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QRadioButton, QWidget, QScrollArea, QFrame, 
    QSizePolicy, QMessageBox, QInputDialog, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut

from app.db_sqlite import (
    create_decision_point, update_decision_point, get_decision_point,
    get_decision_options, add_decision_option, update_decision_option,
    delete_decision_option
)
from app.utils.ocr_widget import OCRWidget


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
            text: The extracted text to add as a new option
        """
        if text.strip():
            # Add the extracted text as a new option
            self.add_option(text.strip())
            
            # Switch back to the Decision Point tab
            self.tab_widget.setCurrentIndex(0)
            
            # Show confirmation
            QMessageBox.information(
                self,
                "Option Added",
                f"Added new option from OCR text"
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
            for option in self.options_list:
                if not option.order_input:
                    continue
                    
                order_text = option.order_input.text().strip()
                if order_text:
                    try:
                        int(order_text)
                    except ValueError:
                        QMessageBox.warning(
                            self, 
                            "Invalid Input", 
                            f"Invalid order number for option '{option.text}'. Please enter a valid number."
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