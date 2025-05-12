#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Character Badge Example for The Plot Thickens application.

This module demonstrates how to use the CharacterBadge class in different
contexts and configurations.
"""

import sys
import os
from typing import Dict, Any, List

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QScrollArea, QGroupBox, QFrame, QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from app.utils.character_badge import CharacterBadge, create_character_badge
from app.utils.icons.icon_manager import icon_manager


# Sample character data for demonstration
SAMPLE_CHARACTERS = [
    {
        "id": 1,
        "name": "John Doe",
        "is_main_character": True,
        "avatar_path": None,  # Will use initials
        "gender": "Male",
        "age_category": "Adult",
        "is_deceased": False,
        "is_archived": False,
    },
    {
        "id": 2,
        "name": "Jane Smith",
        "is_main_character": False,
        "avatar_path": None,  # Will use initials
        "gender": "Female",
        "age_category": "Young",
        "is_deceased": False,
        "is_archived": False,
    },
    {
        "id": 3,
        "name": "Robert Johnson",
        "is_main_character": False,
        "avatar_path": None,  # Will use initials
        "gender": "Male",
        "age_category": "Mature",
        "is_deceased": True,
        "is_archived": False,
    },
    {
        "id": 4,
        "name": "Emily Wilson",
        "is_main_character": False,
        "avatar_path": None,  # Will use initials
        "gender": "Female",
        "age_category": "Teen",
        "is_deceased": False,
        "is_archived": True,
    }
]


class CharacterBadgeExampleWindow(QMainWindow):
    """Window for demonstrating the CharacterBadge widget."""
    
    def __init__(self):
        """Initialize the example window."""
        super().__init__()
        
        self.setWindowTitle("Character Badge Examples")
        self.resize(800, 600)
        
        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Add introductory label
        intro_label = QLabel(
            "Character Badge Examples - The Plot Thickens\n"
            "This example shows different badge configurations and uses."
        )
        intro_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(intro_label)
        
        # Create a scroll area for the examples
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        # Add example sections
        scroll_layout.addWidget(self.create_size_examples())
        scroll_layout.addWidget(self.create_style_examples())
        scroll_layout.addWidget(self.create_status_examples())
        scroll_layout.addWidget(self.create_interaction_examples())
        
        # Add spacer at the bottom
        scroll_layout.addStretch()
    
    def create_size_examples(self) -> QGroupBox:
        """Create examples of different badge sizes.
        
        Returns:
            GroupBox containing the examples
        """
        group_box = QGroupBox("Badge Sizes")
        layout = QVBoxLayout(group_box)
        
        sizes_layout = QHBoxLayout()
        sizes_layout.setSpacing(20)
        
        # Create badges in different sizes
        sizes = [
            ("Tiny", CharacterBadge.SIZE_TINY),
            ("Small", CharacterBadge.SIZE_SMALL),
            ("Medium", CharacterBadge.SIZE_MEDIUM),
            ("Large", CharacterBadge.SIZE_LARGE),
            ("X-Large", CharacterBadge.SIZE_XLARGE),
        ]
        
        for label_text, size in sizes:
            size_layout = QVBoxLayout()
            
            # Add label
            label = QLabel(label_text)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            size_layout.addWidget(label)
            
            # Add badge
            badge = create_character_badge(
                SAMPLE_CHARACTERS[0]["id"],
                SAMPLE_CHARACTERS[0],
                size=size,
                style=CharacterBadge.STYLE_OUTLINED
            )
            size_layout.addWidget(badge)
            
            sizes_layout.addLayout(size_layout)
        
        layout.addLayout(sizes_layout)
        return group_box
    
    def create_style_examples(self) -> QGroupBox:
        """Create examples of different badge styles.
        
        Returns:
            GroupBox containing the examples
        """
        group_box = QGroupBox("Badge Styles")
        layout = QVBoxLayout(group_box)
        
        styles_layout = QHBoxLayout()
        styles_layout.setSpacing(20)
        
        # Create badges in different styles
        styles = [
            ("Flat", CharacterBadge.STYLE_FLAT),
            ("Outlined", CharacterBadge.STYLE_OUTLINED),
            ("Filled", CharacterBadge.STYLE_FILLED),
            ("Shadowed", CharacterBadge.STYLE_SHADOWED),
        ]
        
        for label_text, style in styles:
            style_layout = QVBoxLayout()
            
            # Add label
            label = QLabel(label_text)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            style_layout.addWidget(label)
            
            # Add badge
            badge = create_character_badge(
                SAMPLE_CHARACTERS[1]["id"],
                SAMPLE_CHARACTERS[1],
                size=CharacterBadge.SIZE_MEDIUM,
                style=style
            )
            style_layout.addWidget(badge)
            
            styles_layout.addLayout(style_layout)
        
        layout.addLayout(styles_layout)
        return group_box
    
    def create_status_examples(self) -> QGroupBox:
        """Create examples showing status icons.
        
        Returns:
            GroupBox containing the examples
        """
        group_box = QGroupBox("Status Icons")
        layout = QVBoxLayout(group_box)
        
        status_layout = QHBoxLayout()
        status_layout.setSpacing(20)
        
        # Deceased character with ghost icon
        deceased_badge = create_character_badge(
            SAMPLE_CHARACTERS[2]["id"],
            SAMPLE_CHARACTERS[2],
            size=CharacterBadge.SIZE_LARGE,
            style=CharacterBadge.STYLE_OUTLINED
        )
        deceased_badge.add_status_icon(
            "ghost", 
            "Deceased", 
            color="#777777"
        )
        
        # Archived character with archive icon
        archived_badge = create_character_badge(
            SAMPLE_CHARACTERS[3]["id"],
            SAMPLE_CHARACTERS[3],
            size=CharacterBadge.SIZE_LARGE,
            style=CharacterBadge.STYLE_OUTLINED
        )
        archived_badge.add_status_icon(
            "archive", 
            "Archived Character", 
            color="#555555"
        )
        
        # Character with multiple status icons
        multi_status_badge = create_character_badge(
            SAMPLE_CHARACTERS[0]["id"],
            SAMPLE_CHARACTERS[0],
            size=CharacterBadge.SIZE_LARGE,
            style=CharacterBadge.STYLE_FILLED
        )
        
        # Add multiple status icons
        multi_status_badge.add_status_icon(
            "user", 
            "Main Character", 
            color="#FFD700"
        )
        multi_status_badge.add_status_icon(
            "award", 
            "Award-Winning Character", 
            color="#2962FF"
        )
        multi_status_badge.add_status_icon(
            "bookmark", 
            "Bookmarked", 
            color="#FF6D00"
        )
        
        # Add the badges to the layout
        for badge, title in [
            (deceased_badge, "Deceased"),
            (archived_badge, "Archived"),
            (multi_status_badge, "Multiple Status Icons")
        ]:
            badge_layout = QVBoxLayout()
            label = QLabel(title)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge_layout.addWidget(label)
            badge_layout.addWidget(badge)
            status_layout.addLayout(badge_layout)
        
        layout.addLayout(status_layout)
        return group_box
    
    def create_interaction_examples(self) -> QGroupBox:
        """Create examples showing interaction.
        
        Returns:
            GroupBox containing the examples
        """
        group_box = QGroupBox("Interactive Examples")
        layout = QVBoxLayout(group_box)
        
        # Add information text
        info_text = (
            "The badges below demonstrate interactive features.\n"
            "Click on a badge or its icons to see the response in the console."
        )
        info_label = QLabel(info_text)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)
        
        # Container for interactive badges
        interactive_layout = QHBoxLayout()
        interactive_layout.setSpacing(30)
        
        # Simple clickable badge
        clickable_badge = create_character_badge(
            SAMPLE_CHARACTERS[0]["id"],
            SAMPLE_CHARACTERS[0],
            size=CharacterBadge.SIZE_LARGE,
            style=CharacterBadge.STYLE_SHADOWED
        )
        clickable_badge.clicked.connect(self.on_badge_clicked)
        
        # Badge with clickable icons
        icon_badge = create_character_badge(
            SAMPLE_CHARACTERS[1]["id"],
            SAMPLE_CHARACTERS[1],
            size=CharacterBadge.SIZE_LARGE,
            style=CharacterBadge.STYLE_OUTLINED
        )
        
        # Add clickable icons
        edit_icon = icon_badge.add_status_icon(
            "edit", 
            "Edit Character", 
            color="#007BFF"
        )
        if edit_icon and edit_icon.button:
            edit_icon.button.clicked.connect(
                lambda: self.on_icon_clicked(SAMPLE_CHARACTERS[1]["id"], "edit")
            )
        
        delete_icon = icon_badge.add_status_icon(
            "trash", 
            "Delete Character", 
            color="#DC3545"
        )
        if delete_icon and delete_icon.button:
            delete_icon.button.clicked.connect(
                lambda: self.on_icon_clicked(SAMPLE_CHARACTERS[1]["id"], "trash")
            )
        
        # Add the badges to the layout
        for badge, title in [
            (clickable_badge, "Click the Badge"),
            (icon_badge, "Click the Icons")
        ]:
            badge_layout = QVBoxLayout()
            label = QLabel(title)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge_layout.addWidget(label)
            badge_layout.addWidget(badge)
            badge_layout.addStretch()
            interactive_layout.addLayout(badge_layout)
        
        interactive_layout.addStretch()
        layout.addLayout(interactive_layout)
        
        # Add a section to dynamically update a badge
        update_section = QGroupBox("Dynamic Badge Updates")
        update_layout = QVBoxLayout(update_section)
        
        # Create a badge that we'll update
        self.updatable_character = SAMPLE_CHARACTERS[0].copy()
        self.updatable_badge = create_character_badge(
            self.updatable_character["id"],
            self.updatable_character,
            size=CharacterBadge.SIZE_LARGE,
            style=CharacterBadge.STYLE_FILLED
        )
        
        update_layout.addWidget(self.updatable_badge)
        
        # Add controls to update the badge
        controls_layout = QHBoxLayout()
        
        # Toggle main character status
        toggle_mc_button = QPushButton("Toggle Main Character")
        toggle_mc_button.clicked.connect(self.toggle_main_character)
        controls_layout.addWidget(toggle_mc_button)
        
        # Toggle deceased status
        toggle_deceased_button = QPushButton("Toggle Deceased")
        toggle_deceased_button.clicked.connect(self.toggle_deceased)
        controls_layout.addWidget(toggle_deceased_button)
        
        # Change name
        rename_button = QPushButton("Rename")
        rename_button.clicked.connect(self.rename_character)
        controls_layout.addWidget(rename_button)
        
        update_layout.addLayout(controls_layout)
        layout.addWidget(update_section)
        
        return group_box
    
    def on_badge_clicked(self, character_id: int) -> None:
        """Handle badge click event.
        
        Args:
            character_id: ID of the clicked character
        """
        print(f"Badge clicked: Character ID {character_id}")
    
    def on_icon_clicked(self, character_id: int, icon_name: str) -> None:
        """Handle icon click event.
        
        Args:
            character_id: ID of the character
            icon_name: Name of the clicked icon
        """
        print(f"Icon '{icon_name}' clicked for Character ID {character_id}")
    
    def toggle_main_character(self) -> None:
        """Toggle the main character status for the updatable badge."""
        self.updatable_character["is_main_character"] = not self.updatable_character.get("is_main_character", False)
        self.updatable_badge.update_from_data(self.updatable_character)
        print(f"Main character status: {self.updatable_character['is_main_character']}")
    
    def toggle_deceased(self) -> None:
        """Toggle the deceased status for the updatable badge."""
        self.updatable_character["is_deceased"] = not self.updatable_character.get("is_deceased", False)
        
        # Update the badge
        self.updatable_badge.update_from_data(self.updatable_character)
        
        # Add or remove the ghost icon based on deceased status
        if self.updatable_character["is_deceased"]:
            if not self.updatable_badge.get_status_icon("ghost"):
                self.updatable_badge.add_status_icon("ghost", "Deceased", color="#777777")
        else:
            self.updatable_badge.remove_status_icon("ghost")
        
        print(f"Deceased status: {self.updatable_character['is_deceased']}")
    
    def rename_character(self) -> None:
        """Rename the character for the updatable badge."""
        current_name = self.updatable_character.get("name", "Unknown")
        if current_name == "John Doe":
            new_name = "Johnny D."
        else:
            new_name = "John Doe"
        
        self.updatable_character["name"] = new_name
        self.updatable_badge.update_from_data(self.updatable_character)
        print(f"Character renamed to: {new_name}")


def run_example():
    """Run the character badge example application."""
    # Check if we're already running in an application
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    window = CharacterBadgeExampleWindow()
    window.show()
    
    # Return the window so the caller can control it
    return window


if __name__ == "__main__":
    window = run_example()
    sys.exit(QApplication.instance().exec()) 