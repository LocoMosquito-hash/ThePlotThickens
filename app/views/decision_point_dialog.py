#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Decision Point Dialog for The Plot Thickens application.

This dialog allows users to create and manage decision points for visual novels.
"""

from typing import List, Dict, Any, Optional, Tuple

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QGroupBox, QScrollArea, QWidget, QRadioButton,
    QInputDialog, QMessageBox
)
from PyQt6.QtCore import Qt

class DecisionPointDialog(QDialog):
    """Dialog for managing decision points."""
    
    def __init__(self, db_conn, story_id: int, parent=None):
        """Initialize the decision point dialog.
        
        Args:
            db_conn: Database connection
            story_id: ID of the story
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.story_id = story_id
        self.decision_point_id = None
        self.options_list = []
        
        self.setWindowTitle("Add decision point")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        self.init_ui()
    
    def init_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Decision point title
        title_layout = QHBoxLayout()
        title_label = QLabel("Decision point:")
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Enter decision point title")
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.title_edit)
        main_layout.addLayout(title_layout)
        
        # Add option button
        self.add_option_button = QPushButton("Add option")
        self.add_option_button.clicked.connect(self.on_add_option)
        main_layout.addWidget(self.add_option_button)
        
        # Options group
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)
        
        # Options list (with radio buttons)
        self.options_container = QWidget()
        self.options_container_layout = QVBoxLayout(self.options_container)
        self.options_container_layout.setContentsMargins(0, 0, 0, 0)
        self.options_container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Add options container to a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.options_container)
        
        options_layout.addWidget(scroll_area)
        main_layout.addWidget(options_group)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Add save button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.save_button)
        
        # Add cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(buttons_layout)
    
    def on_add_option(self):
        """Handle add option button click."""
        option_text, ok = QInputDialog.getText(self, "Add Option", "Enter option text:")
        if ok and option_text.strip():
            self.add_option(option_text)
    
    def add_option(self, option_text: str, is_selected: bool = False):
        """Add an option to the list.
        
        Args:
            option_text: Text of the option
            is_selected: Whether the option is selected
        """
        # Create a container for the option and its radio button
        option_container = QWidget()
        option_layout = QHBoxLayout(option_container)
        option_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create a radio button for the option
        radio_button = QRadioButton(option_text)
        radio_button.setChecked(is_selected)
        option_layout.addWidget(radio_button)
        
        # Add the container to the options layout
        self.options_container_layout.addWidget(option_container)
        
        # Add the option to the list
        self.options_list.append({
            "text": option_text,
            "radio_button": radio_button,
            "container": option_container,
            "is_selected": is_selected
        })
    
    def get_selected_option_index(self) -> int:
        """Get the index of the selected option.
        
        Returns:
            Index of the selected option, or -1 if none is selected
        """
        for i, option in enumerate(self.options_list):
            if option["radio_button"].isChecked():
                return i
        return -1
    
    def get_next_decision_point_number(self) -> int:
        """Get the next sequential decision point number for the current story.
        
        Returns:
            Next sequential number for a default decision point title
        """
        from app.db_sqlite import get_story_decision_points
        
        try:
            # Get all decision points for the story
            decision_points = get_story_decision_points(self.db_conn, self.story_id)
            
            # Find the highest number used in a default title
            default_prefix = "Decision Point "
            max_number = 0
            
            for dp in decision_points:
                title = dp.get("title", "")
                if title.startswith(default_prefix):
                    try:
                        num_str = title[len(default_prefix):]
                        num = int(num_str)
                        max_number = max(max_number, num)
                    except ValueError:
                        # Not a numbered decision point
                        pass
            
            # Return the next number in sequence
            return max_number + 1
        except Exception as e:
            print(f"Error getting next decision point number: {e}")
            return 1  # Start with 1 if there's any error
    
    def accept(self):
        """Handle dialog acceptance (save)."""
        title = self.title_edit.text().strip()
        if not title:
            # Generate a default title with sequential numbering
            next_number = self.get_next_decision_point_number()
            title = f"Decision Point {next_number}"
        
        if not self.options_list:
            QMessageBox.warning(self, "Error", "Please add at least one option.")
            return
        
        selected_index = self.get_selected_option_index()
        if selected_index == -1:
            QMessageBox.warning(self, "Error", "Please select one of the options.")
            return
        
        # Save the decision point and options to the database
        try:
            from app.db_sqlite import (
                create_decision_point, add_decision_option, select_decision_option
            )
            
            # Create the decision point
            decision_point_id = create_decision_point(self.db_conn, title, self.story_id)
            
            # Add the options
            for i, option in enumerate(self.options_list):
                option_id = add_decision_option(
                    self.db_conn, 
                    decision_point_id, 
                    option["text"],
                    option["radio_button"].isChecked(),
                    i
                )
            
            # Store the decision point ID
            self.decision_point_id = decision_point_id
            
            # Close the dialog
            super().accept()
            
        except Exception as e:
            print(f"Error saving decision point: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save decision point: {str(e)}") 