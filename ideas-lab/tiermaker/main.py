#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main application for Tier Maker.

This module contains the main window and application entry point for the
standalone tier maker application.
"""

import sys
import os
from typing import Optional, List, Tuple
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QSpinBox, QMessageBox,
    QSplitter, QFrame, QGroupBox, QDialog, QListWidget, QDialogButtonBox
)

try:
    import qdarktheme
    DARK_THEME_AVAILABLE = True
except ImportError:
    DARK_THEME_AVAILABLE = False

try:
    from pytablericons import TablerIcons, OutlineIcon
    ICONS_AVAILABLE = True
except ImportError:
    ICONS_AVAILABLE = False

from models.tier_template import TierTemplate
from models.rankable_item import RankableItem
from utils.database import DatabaseManager
from widgets.tier_table import TierTable
from widgets.template_editor import TemplateEditorDialog
from widgets.rankable_items_area import RankableItemsArea


def _pil_to_qicon(pil_image) -> QIcon:
    """Convert PIL Image to QIcon."""
    # Convert PIL Image to bytes
    from io import BytesIO
    buffer = BytesIO()
    pil_image.save(buffer, format='PNG')
    buffer.seek(0)
    
    # Create QPixmap from bytes
    pixmap = QPixmap()
    pixmap.loadFromData(buffer.getvalue())
    
    return QIcon(pixmap)


class TierMakerWindow(QMainWindow):
    """Main window for the Tier Maker application."""
    
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.current_template: Optional[TierTemplate] = None
        self.current_story_id: Optional[int] = None
        
        self.setWindowTitle("The Plot Thickens - Tier Maker")
        self.setMinimumSize(1200, 800)
        
        self._setup_ui()
        self._load_initial_data()
    
    def _setup_ui(self) -> None:
        """Set up the main UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Title
        title_label = QLabel("Tier Maker")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: white;
                padding: 10px;
                background-color: #2b2b2b;
                border-radius: 8px;
                margin-bottom: 10px;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Controls section
        controls_frame = self._create_controls_section()
        main_layout.addWidget(controls_frame)
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Tier table (top)
        self.tier_table = TierTable()
        self.tier_table.tierSettingsClicked.connect(self._on_tier_settings_clicked)
        splitter.addWidget(self.tier_table)
        
        # Rankable items area (bottom)
        self.items_area = RankableItemsArea()
        splitter.addWidget(self.items_area)
        
        # Set splitter proportions (tier table gets more space)
        splitter.setSizes([500, 300])
        main_layout.addWidget(splitter)
        
        central_widget.setLayout(main_layout)
        
        # Style the main window
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: white;
            }
        """)
    
    def _create_controls_section(self) -> QFrame:
        """Create the controls section with buttons and filters."""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        frame.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Template controls row
        template_row = QHBoxLayout()
        
        # New Template button
        self.new_template_btn = QPushButton("New Template")
        if ICONS_AVAILABLE:
            icon_image = TablerIcons.load(OutlineIcon.PLUS)
            self.new_template_btn.setIcon(_pil_to_qicon(icon_image))
        self.new_template_btn.clicked.connect(self._create_new_template)
        self._style_button(self.new_template_btn, "#4caf50")
        template_row.addWidget(self.new_template_btn)
        
        # Load Template button
        self.load_template_btn = QPushButton("Load Template")
        if ICONS_AVAILABLE:
            icon_image = TablerIcons.load(OutlineIcon.FOLDER_OPEN)
            self.load_template_btn.setIcon(_pil_to_qicon(icon_image))
        self.load_template_btn.clicked.connect(self._load_template)
        self._style_button(self.load_template_btn, "#2196f3")
        template_row.addWidget(self.load_template_btn)
        
        # Reset button
        self.reset_btn = QPushButton("Reset")
        if ICONS_AVAILABLE:
            icon_image = TablerIcons.load(OutlineIcon.REFRESH)
            self.reset_btn.setIcon(_pil_to_qicon(icon_image))
        self.reset_btn.clicked.connect(self._reset_rankings)
        self.reset_btn.setEnabled(False)
        self._style_button(self.reset_btn, "#ff9800")
        template_row.addWidget(self.reset_btn)
        
        template_row.addStretch()
        layout.addLayout(template_row)
        
        # Filters row
        filters_row = QHBoxLayout()
        
        # Story selection
        story_label = QLabel("Story:")
        story_label.setStyleSheet("QLabel { color: white; font-weight: bold; }")
        filters_row.addWidget(story_label)
        
        self.story_combo = QComboBox()
        self.story_combo.currentIndexChanged.connect(self._on_story_changed)
        self._style_combo(self.story_combo)
        filters_row.addWidget(self.story_combo)
        
        # Item type (for future expansion)
        type_label = QLabel("Item Type:")
        type_label.setStyleSheet("QLabel { color: white; font-weight: bold; }")
        filters_row.addWidget(type_label)
        
        self.item_type_combo = QComboBox()
        self.item_type_combo.addItem("Characters")
        self.item_type_combo.setEnabled(False)  # Only characters for now
        self._style_combo(self.item_type_combo)
        filters_row.addWidget(self.item_type_combo)
        
        filters_row.addStretch()
        layout.addLayout(filters_row)
        
        # Character filters row
        char_filters_row = QHBoxLayout()
        
        # Gender filter
        gender_label = QLabel("Gender:")
        gender_label.setStyleSheet("QLabel { color: white; font-weight: bold; }")
        char_filters_row.addWidget(gender_label)
        
        self.gender_combo = QComboBox()
        self.gender_combo.addItem("All", None)
        self.gender_combo.currentIndexChanged.connect(self._on_filters_changed)
        self._style_combo(self.gender_combo)
        char_filters_row.addWidget(self.gender_combo)
        
        # Love interest filter
        love_label = QLabel("Min Love Interest:")
        love_label.setStyleSheet("QLabel { color: white; font-weight: bold; }")
        char_filters_row.addWidget(love_label)
        
        self.love_interest_spin = QSpinBox()
        self.love_interest_spin.setRange(0, 10)
        self.love_interest_spin.setValue(0)
        self.love_interest_spin.valueChanged.connect(self._on_filters_changed)
        self._style_spinbox(self.love_interest_spin)
        char_filters_row.addWidget(self.love_interest_spin)
        
        # Load Items button
        self.load_items_btn = QPushButton("Load Items")
        if ICONS_AVAILABLE:
            icon_image = TablerIcons.load(OutlineIcon.DOWNLOAD)
            self.load_items_btn.setIcon(_pil_to_qicon(icon_image))
        self.load_items_btn.clicked.connect(self._load_items)
        self.load_items_btn.setEnabled(False)
        self._style_button(self.load_items_btn, "#9c27b0")
        char_filters_row.addWidget(self.load_items_btn)
        
        char_filters_row.addStretch()
        layout.addLayout(char_filters_row)
        
        frame.setLayout(layout)
        return frame
    
    def _style_button(self, button: QPushButton, color: str) -> None:
        """Apply consistent styling to buttons."""
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: none;
                border-radius: 6px;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {color}dd;
            }}
            QPushButton:pressed {{
                background-color: {color}bb;
            }}
            QPushButton:disabled {{
                background-color: #555;
                color: #888;
            }}
        """)
    
    def _style_combo(self, combo: QComboBox) -> None:
        """Apply consistent styling to combo boxes."""
        combo.setStyleSheet("""
            QComboBox {
                background-color: #3b3b3b;
                border: 1px solid #555;
                border-radius: 4px;
                color: white;
                padding: 5px;
                min-width: 120px;
            }
            QComboBox:hover {
                border-color: #42a5f5;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #3b3b3b;
                border: 1px solid #555;
                color: white;
                selection-background-color: #42a5f5;
            }
        """)
    
    def _style_spinbox(self, spinbox: QSpinBox) -> None:
        """Apply consistent styling to spin boxes."""
        spinbox.setStyleSheet("""
            QSpinBox {
                background-color: #3b3b3b;
                border: 1px solid #555;
                border-radius: 4px;
                color: white;
                padding: 5px;
                min-width: 60px;
            }
            QSpinBox:hover {
                border-color: #42a5f5;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #555;
                border: none;
                width: 16px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #666;
            }
        """)
    
    def _load_initial_data(self) -> None:
        """Load initial data for the application."""
        # Load stories
        stories = self.db_manager.get_stories()
        self.story_combo.clear()
        self.story_combo.addItem("Select a story...", None)
        
        for story_id, title in stories:
            self.story_combo.addItem(title, story_id)
    
    def _create_new_template(self) -> None:
        """Create a new template."""
        dialog = TemplateEditorDialog(db_manager=self.db_manager, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            template = dialog.get_template()
            self.current_template = template
            self.tier_table.load_template(template)
            self.tier_table.set_template_mode(False)  # Enable ranking mode
            self.reset_btn.setEnabled(True)
            
            QMessageBox.information(self, "Success", f"Template '{template.name}' created and loaded!")
    
    def _load_template(self) -> None:
        """Load an existing template."""
        templates = self.db_manager.list_templates()
        if not templates:
            QMessageBox.information(self, "No Templates", "No templates found. Create a new template first.")
            return
        
        # Create a simple selection dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Load Template")
        dialog.setModal(True)
        dialog.resize(400, 300)
        
        layout = QVBoxLayout()
        
        list_widget = QListWidget()
        for template_id, name in templates:
            list_widget.addItem(name)
            list_widget.item(list_widget.count() - 1).setData(Qt.ItemDataRole.UserRole, template_id)
        
        layout.addWidget(QLabel("Select a template:"))
        layout.addWidget(list_widget)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            current_item = list_widget.currentItem()
            if current_item:
                template_id = current_item.data(Qt.ItemDataRole.UserRole)
                template = self.db_manager.load_template(template_id)
                if template:
                    self.current_template = template
                    self.tier_table.load_template(template)
                    self.tier_table.set_template_mode(False)  # Enable ranking mode
                    self.reset_btn.setEnabled(True)
                    
                    QMessageBox.information(self, "Success", f"Template '{template.name}' loaded!")
    
    def _reset_rankings(self) -> None:
        """Reset all tier rankings."""
        if self.current_template:
            reply = QMessageBox.question(self, "Reset Rankings", 
                                       "Are you sure you want to clear all tier rankings?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                self.tier_table.reset_rankings()
    
    def _on_story_changed(self) -> None:
        """Handle story selection changes."""
        story_id = self.story_combo.currentData()
        if story_id:
            self.current_story_id = story_id
            
            # Load genders for this story
            genders = self.db_manager.get_genders_for_story(story_id)
            self.gender_combo.clear()
            self.gender_combo.addItem("All", None)
            for gender in genders:
                self.gender_combo.addItem(gender, gender)
            
            self.load_items_btn.setEnabled(True)
        else:
            self.current_story_id = None
            self.gender_combo.clear()
            self.gender_combo.addItem("All", None)
            self.load_items_btn.setEnabled(False)
            self.items_area.clear_items()
    
    def _on_filters_changed(self) -> None:
        """Handle filter changes."""
        # Auto-reload items if a story is selected
        if self.current_story_id:
            self._load_items()
    
    def _load_items(self) -> None:
        """Load rankable items based on current filters."""
        if not self.current_story_id:
            QMessageBox.warning(self, "No Story", "Please select a story first.")
            return
        
        # Get filter values
        gender_filter = self.gender_combo.currentData()
        min_love_interest = self.love_interest_spin.value()
        
        # Load characters
        characters = self.db_manager.get_characters(
            self.current_story_id, 
            gender_filter, 
            min_love_interest
        )
        
        # Update items area
        self.items_area.set_items(characters)
        
        if characters:
            QMessageBox.information(self, "Items Loaded", f"Loaded {len(characters)} characters.")
        else:
            QMessageBox.information(self, "No Items", "No characters match the current filters.")
    
    def _on_tier_settings_clicked(self, tier) -> None:
        """Handle tier settings button clicks."""
        # For now, just show a message that this is a placeholder
        QMessageBox.information(self, "Tier Settings", 
                              f"Settings for tier '{tier.tier_name}' - Coming soon!")


def main():
    """Main entry point for the Tier Maker application."""
    app = QApplication(sys.argv)
    
    # Apply dark theme if available
    if DARK_THEME_AVAILABLE:
        qdarktheme.setup_theme("dark")
    
    # Create and show the main window
    window = TierMakerWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 