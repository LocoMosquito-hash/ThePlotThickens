#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tag suggestion dialog for The Plot Thickens gallery.

Provides an interface for suggesting and selecting character tags.
"""

from typing import List, Dict, Any, Tuple, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, 
    QPushButton, QHBoxLayout, QCheckBox, QSpinBox, QDoubleSpinBox,
    QGroupBox, QRadioButton, QSlider, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage

class TagSuggestionDialog(QDialog):
    """Dialog for suggesting character tags based on recognition."""
    
    def __init__(self, db_conn, character_suggestions: List[Dict[str, Any]], 
                image: QImage, parent=None):
        """Initialize the dialog.
        
        Args:
            db_conn: Database connection
            character_suggestions: List of character suggestions with confidence scores
            image: The image to tag
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.character_suggestions = character_suggestions
        self.image = image
        self.selected_character_ids = []
        self.add_to_database = True
        self.tag_positions = True
        self.position_manually = False
        self.tag_size = (0.1, 0.1)  # Default size as percentage of image width/height
        
        self.setWindowTitle("Tag Suggestions")
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(
            "The following characters were recognized in this image. "
            "Select which ones to tag:"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Character list
        self.character_list = QListWidget()
        layout.addWidget(self.character_list)
        
        # Populate the list with character suggestions
        for suggestion in self.character_suggestions:
            character = suggestion['character']
            confidence = suggestion.get('confidence', 0.0)
            
            item = QListWidgetItem(f"{character['name']} ({confidence:.1%})")
            item.setData(Qt.ItemDataRole.UserRole, character['id'])
            item.setCheckState(Qt.CheckState.Checked)
            self.character_list.addItem(item)
        
        # Options group
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()
        
        # Tag positions checkbox
        self.position_checkbox = QCheckBox("Tag character positions in image")
        self.position_checkbox.setChecked(True)
        self.position_checkbox.stateChanged.connect(self.on_position_checkbox_changed)
        options_layout.addWidget(self.position_checkbox)
        
        # Position mode group
        self.position_mode_group = QGroupBox("Position Mode")
        position_mode_layout = QVBoxLayout()
        
        # Auto-position radio button
        self.auto_position_radio = QRadioButton("Auto-position tags")
        self.auto_position_radio.setChecked(True)
        position_mode_layout.addWidget(self.auto_position_radio)
        
        # Manual position radio button
        self.manual_position_radio = QRadioButton("Position tags manually")
        position_mode_layout.addWidget(self.manual_position_radio)
        
        # Tag size controls
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Tag Size:"))
        
        # Width percentage spinbox
        self.width_spinbox = QDoubleSpinBox()
        self.width_spinbox.setRange(0.05, 0.5)
        self.width_spinbox.setSingleStep(0.01)
        self.width_spinbox.setValue(0.1)
        self.width_spinbox.setSuffix(" width")
        size_layout.addWidget(self.width_spinbox)
        
        # Height percentage spinbox
        self.height_spinbox = QDoubleSpinBox()
        self.height_spinbox.setRange(0.05, 0.5)
        self.height_spinbox.setSingleStep(0.01)
        self.height_spinbox.setValue(0.1)
        self.height_spinbox.setSuffix(" height")
        size_layout.addWidget(self.height_spinbox)
        
        position_mode_layout.addLayout(size_layout)
        self.position_mode_group.setLayout(position_mode_layout)
        options_layout.addWidget(self.position_mode_group)
        
        # Add to database checkbox
        self.add_to_db_checkbox = QCheckBox("Add face data to recognition database")
        self.add_to_db_checkbox.setChecked(True)
        options_layout.addWidget(self.add_to_db_checkbox)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        tag_button = QPushButton("Tag Characters")
        tag_button.clicked.connect(self.accept)
        tag_button.setDefault(True)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(tag_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.resize(400, 500)
    
    def on_position_checkbox_changed(self, state):
        """Handle changes to the position checkbox.
        
        Args:
            state: Checkbox state
        """
        self.position_mode_group.setEnabled(state == Qt.CheckState.Checked.value)
    
    def get_selected_character_ids(self) -> List[int]:
        """Get the IDs of selected characters.
        
        Returns:
            List of character IDs
        """
        selected_ids = []
        
        for i in range(self.character_list.count()):
            item = self.character_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                character_id = item.data(Qt.ItemDataRole.UserRole)
                selected_ids.append(character_id)
        
        return selected_ids
    
    def should_tag_positions(self) -> bool:
        """Check if positions should be tagged.
        
        Returns:
            True if positions should be tagged, False otherwise
        """
        return self.position_checkbox.isChecked()
    
    def should_position_manually(self) -> bool:
        """Check if tags should be positioned manually.
        
        Returns:
            True if manual positioning is selected, False for auto-positioning
        """
        return self.manual_position_radio.isChecked()
    
    def get_tag_size(self) -> Tuple[float, float]:
        """Get the tag size as percentage of image dimensions.
        
        Returns:
            Tuple of (width_percentage, height_percentage)
        """
        width_pct = self.width_spinbox.value()
        height_pct = self.height_spinbox.value()
        return (width_pct, height_pct)
    
    def should_add_to_database(self) -> bool:
        """Check if face data should be added to the recognition database.
        
        Returns:
            True if face data should be added to database, False otherwise
        """
        return self.add_to_db_checkbox.isChecked()
