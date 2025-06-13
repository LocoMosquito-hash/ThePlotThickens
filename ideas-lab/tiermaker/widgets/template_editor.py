#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Template editor dialog for Tier Maker.

This module contains the dialog for creating and editing tier templates.
"""

from typing import Optional, List
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QColorDialog, QMessageBox,
    QFrame, QScrollArea, QSizePolicy, QWidget
)

try:
    from pytablericons import TablerIcons
    ICONS_AVAILABLE = True
except ImportError:
    ICONS_AVAILABLE = False

from models.tier_template import TierTemplate, TierTemplateTier
from utils.database import DatabaseManager


class TierEditRow(QWidget):
    """A row for editing a single tier's name and color."""
    
    colorChanged = pyqtSignal(object, str)  # tier, new_color
    nameChanged = pyqtSignal(object, str)   # tier, new_name
    
    def __init__(self, tier: TierTemplateTier, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.tier = tier
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the UI for this tier edit row."""
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # Tier name input
        self.name_input = QLineEdit(self.tier.tier_name)
        self.name_input.setMaxLength(10)  # Keep tier names short
        self.name_input.setFixedWidth(100)
        self.name_input.textChanged.connect(self._on_name_changed)
        self.name_input.setStyleSheet("""
            QLineEdit {
                background-color: #2b2b2b;
                border: 1px solid #555;
                border-radius: 4px;
                color: white;
                padding: 5px;
                font-weight: bold;
            }
            QLineEdit:focus {
                border-color: #42a5f5;
            }
        """)
        layout.addWidget(self.name_input)
        
        # Color preview and button
        self.color_button = QPushButton()
        self.color_button.setFixedSize(60, 30)
        self.color_button.clicked.connect(self._choose_color)
        self._update_color_button()
        layout.addWidget(self.color_button)
        
        # Color hex display
        self.color_label = QLabel(self.tier.tier_color)
        self.color_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-family: monospace;
                font-size: 10px;
            }
        """)
        layout.addWidget(self.color_label)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def _update_color_button(self) -> None:
        """Update the color button's appearance."""
        self.color_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.tier.tier_color};
                border: 1px solid #333;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border-color: #42a5f5;
            }}
        """)
    
    def _choose_color(self) -> None:
        """Open color chooser dialog."""
        current_color = QColor(self.tier.tier_color)
        color = QColorDialog.getColor(current_color, self, "Choose Tier Color")
        
        if color.isValid():
            color_hex = color.name()
            self.tier.tier_color = color_hex
            self.color_label.setText(color_hex)
            self._update_color_button()
            self.colorChanged.emit(self.tier, color_hex)
    
    def _on_name_changed(self, text: str) -> None:
        """Handle tier name changes."""
        self.tier.tier_name = text
        self.nameChanged.emit(self.tier, text)
    
    def get_tier(self) -> TierTemplateTier:
        """Get the current tier data.
        
        Returns:
            The updated tier data
        """
        return self.tier


class TemplateEditorDialog(QDialog):
    """Dialog for creating and editing tier templates."""
    
    def __init__(self, template: Optional[TierTemplate] = None, 
                 db_manager: Optional[DatabaseManager] = None,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.template = template or TierTemplate.create_default_template("New Template")
        self.db_manager = db_manager or DatabaseManager()
        self.tier_edit_rows: List[TierEditRow] = []
        
        self.setWindowTitle("Template Editor")
        self.setModal(True)
        self.resize(500, 400)
        
        self._setup_ui()
        self._load_template()
    
    def _setup_ui(self) -> None:
        """Set up the UI for the template editor."""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Template Editor")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: white;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title_label)
        
        # Template name input
        name_layout = QHBoxLayout()
        name_label = QLabel("Template Name:")
        name_label.setStyleSheet("QLabel { color: white; font-weight: bold; }")
        name_layout.addWidget(name_label)
        
        self.name_input = QLineEdit(self.template.name)
        self.name_input.setStyleSheet("""
            QLineEdit {
                background-color: #2b2b2b;
                border: 1px solid #555;
                border-radius: 4px;
                color: white;
                padding: 8px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #42a5f5;
            }
        """)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # Tiers section
        tiers_label = QLabel("Tiers:")
        tiers_label.setStyleSheet("QLabel { color: white; font-weight: bold; }")
        layout.addWidget(tiers_label)
        
        # Scroll area for tiers
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMaximumHeight(200)
        
        self.tiers_container = QWidget()
        self.tiers_layout = QVBoxLayout()
        self.tiers_layout.setContentsMargins(0, 0, 0, 0)
        self.tiers_layout.setSpacing(5)
        self.tiers_container.setLayout(self.tiers_layout)
        
        self.scroll_area.setWidget(self.tiers_container)
        layout.addWidget(self.scroll_area)
        
        # Style the scroll area
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #1e1e1e;
                border: 1px solid #444;
                border-radius: 4px;
            }
            QScrollBar:vertical {
                background-color: #2b2b2b;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #555;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #666;
            }
        """)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #555;
                border: 1px solid #666;
                border-radius: 4px;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #666;
            }
            QPushButton:pressed {
                background-color: #444;
            }
        """)
        button_layout.addWidget(self.cancel_button)
        
        self.save_button = QPushButton("Save Template")
        self.save_button.clicked.connect(self._save_template)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #42a5f5;
                border: 1px solid #1976d2;
                border-radius: 4px;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Style the dialog
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: white;
            }
        """)
    
    def _load_template(self) -> None:
        """Load the template data into the editor."""
        # Clear existing tier rows
        for row in self.tier_edit_rows:
            row.setParent(None)
        self.tier_edit_rows.clear()
        
        # Create edit rows for each tier
        for tier in sorted(self.template.tiers, key=lambda t: t.tier_order):
            row = TierEditRow(tier)
            row.colorChanged.connect(self._on_tier_changed)
            row.nameChanged.connect(self._on_tier_changed)
            
            self.tier_edit_rows.append(row)
            self.tiers_layout.addWidget(row)
        
        # Add stretch at the end
        self.tiers_layout.addStretch()
    
    def _on_tier_changed(self, tier: TierTemplateTier, value: str) -> None:
        """Handle tier changes."""
        # This is called when tier name or color changes
        # We don't need to do anything special here since the tier object
        # is updated directly by the TierEditRow
        pass
    
    def _save_template(self) -> None:
        """Save the template to the database."""
        # Validate template name
        template_name = self.name_input.text().strip()
        if not template_name:
            QMessageBox.warning(self, "Invalid Name", "Please enter a template name.")
            return
        
        # Check if name already exists (excluding current template if editing)
        if self.db_manager.template_name_exists(template_name, self.template.id):
            QMessageBox.warning(self, "Name Exists", 
                              f"A template named '{template_name}' already exists. Please choose a different name.")
            return
        
        # Validate tier names
        tier_names = []
        for row in self.tier_edit_rows:
            tier = row.get_tier()
            if not tier.tier_name.strip():
                QMessageBox.warning(self, "Invalid Tier", "All tiers must have names.")
                return
            
            if tier.tier_name in tier_names:
                QMessageBox.warning(self, "Duplicate Tier", 
                                  f"Tier name '{tier.tier_name}' is used multiple times. Please use unique names.")
                return
            
            tier_names.append(tier.tier_name)
        
        # Update template
        self.template.name = template_name
        self.template.tiers = [row.get_tier() for row in self.tier_edit_rows]
        
        # Save to database
        try:
            template_id = self.db_manager.save_template(self.template)
            self.template.id = template_id
            
            QMessageBox.information(self, "Success", "Template saved successfully!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save template: {str(e)}")
    
    def get_template(self) -> TierTemplate:
        """Get the edited template.
        
        Returns:
            The template with current edits
        """
        # Update template name
        self.template.name = self.name_input.text().strip()
        
        # Update tiers
        self.template.tiers = [row.get_tier() for row in self.tier_edit_rows]
        
        return self.template 