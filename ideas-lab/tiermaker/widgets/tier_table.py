#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tier table widget for Tier Maker.

This module contains the main tier ranking interface with tier names,
drop zones, and settings buttons.
"""

from typing import List, Optional, Dict, Any
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QSizePolicy
)

try:
    from pytablericons import TablerIcons, OutlineIcon
    ICONS_AVAILABLE = True
except ImportError:
    ICONS_AVAILABLE = False

from models.tier_template import TierTemplate, TierTemplateTier
from models.rankable_item import RankableItem
from widgets.drag_drop_widgets import DragWidget, CharacterDragItem


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


class TierRow(QWidget):
    """A single tier row with name, drop zone, and settings button."""
    
    settingsClicked = pyqtSignal(object)  # Emits the tier object
    
    def __init__(self, tier: TierTemplateTier, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.tier = tier
        self.is_template_mode = False  # Whether we're in template editing mode
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the UI for this tier row."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Tier name label (first column)
        self.name_label = QLabel(self.tier.tier_name)
        self.name_label.setFixedWidth(100)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet(f"""
            QLabel {{
                background-color: {self.tier.tier_color};
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 10px;
            }}
        """)
        layout.addWidget(self.name_label)
        
        # Drop zone (second column) - expandable
        self.drop_zone = DragWidget(Qt.Orientation.Horizontal)
        self.drop_zone.setMinimumHeight(80)
        self.drop_zone.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.drop_zone.setStyleSheet("""
            DragWidget {
                background-color: #2b2b2b;
                border: 2px dashed #555;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.drop_zone, 1)  # Give it stretch factor of 1
        
        # Settings button (third column)
        self.settings_button = QPushButton()
        self.settings_button.setFixedSize(40, 40)
        self.settings_button.clicked.connect(lambda: self.settingsClicked.emit(self.tier))
        
        if ICONS_AVAILABLE:
            icon_image = TablerIcons.load(OutlineIcon.SETTINGS)
            self.settings_button.setIcon(_pil_to_qicon(icon_image))
        else:
            self.settings_button.setText("⚙")
        
        self.settings_button.setStyleSheet("""
            QPushButton {
                background-color: #3b3b3b;
                border: 1px solid #555;
                border-radius: 4px;
                color: white;
            }
            QPushButton:hover {
                background-color: #4b4b4b;
                border-color: #42a5f5;
            }
            QPushButton:pressed {
                background-color: #2b2b2b;
            }
        """)
        layout.addWidget(self.settings_button)
        
        self.setLayout(layout)
        self.setFixedHeight(90)
    
    def set_template_mode(self, enabled: bool) -> None:
        """Enable or disable template editing mode.
        
        Args:
            enabled: Whether template editing is enabled
        """
        self.is_template_mode = enabled
        self.drop_zone.setEnabled(not enabled)
        
        if enabled:
            # In template mode, drop zone is disabled
            self.drop_zone.setStyleSheet("""
                DragWidget {
                    background-color: #1a1a1a;
                    border: 2px dashed #333;
                    border-radius: 4px;
                }
            """)
        else:
            # In ranking mode, drop zone is active
            self.drop_zone.setStyleSheet("""
                DragWidget {
                    background-color: #2b2b2b;
                    border: 2px dashed #555;
                    border-radius: 4px;
                }
            """)
    
    def update_tier_display(self, tier: TierTemplateTier) -> None:
        """Update the display with new tier data.
        
        Args:
            tier: The updated tier data
        """
        self.tier = tier
        self.name_label.setText(tier.tier_name)
        self.name_label.setStyleSheet(f"""
            QLabel {{
                background-color: {tier.tier_color};
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 10px;
            }}
        """)
    
    def add_character(self, character: RankableItem) -> None:
        """Add a character to this tier's drop zone.
        
        Args:
            character: The character to add
        """
        if not self.is_template_mode:
            character_widget = CharacterDragItem(character)
            self.drop_zone.add_item(character_widget)
    
    def clear_characters(self) -> None:
        """Remove all characters from this tier."""
        self.drop_zone.clear_items()
    
    def get_characters(self) -> List[RankableItem]:
        """Get all characters in this tier.
        
        Returns:
            List of RankableItem objects
        """
        return self.drop_zone.get_item_data()


class TierTable(QWidget):
    """The main tier table widget showing all tiers with their drop zones."""
    
    tierSettingsClicked = pyqtSignal(object)  # Emits the tier object
    tierOrderChanged = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.tier_rows: List[TierRow] = []
        self.current_template: Optional[TierTemplate] = None
        self.is_template_mode = False
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the UI for the tier table."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Create scroll area for the tiers
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Container widget for the tiers
        self.tiers_container = QWidget()
        self.tiers_layout = QVBoxLayout()
        self.tiers_layout.setContentsMargins(0, 0, 0, 0)
        self.tiers_layout.setSpacing(5)
        self.tiers_container.setLayout(self.tiers_layout)
        
        self.scroll_area.setWidget(self.tiers_container)
        layout.addWidget(self.scroll_area)
        
        self.setLayout(layout)
        
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
    
    def load_template(self, template: TierTemplate) -> None:
        """Load a tier template into the table.
        
        Args:
            template: The template to load
        """
        self.current_template = template
        self.clear_tiers()
        
        # Create tier rows for each tier in the template
        for tier in sorted(template.tiers, key=lambda t: t.tier_order):
            tier_row = TierRow(tier)
            tier_row.settingsClicked.connect(self.tierSettingsClicked.emit)
            tier_row.drop_zone.orderChanged.connect(self.tierOrderChanged.emit)
            
            self.tier_rows.append(tier_row)
            self.tiers_layout.addWidget(tier_row)
        
        # Add stretch at the end
        self.tiers_layout.addStretch()
    
    def clear_tiers(self) -> None:
        """Remove all tier rows from the table."""
        for tier_row in self.tier_rows:
            self.tiers_layout.removeWidget(tier_row)
            tier_row.setParent(None)
        
        self.tier_rows.clear()
    
    def set_template_mode(self, enabled: bool) -> None:
        """Enable or disable template editing mode.
        
        Args:
            enabled: Whether template editing is enabled
        """
        self.is_template_mode = enabled
        for tier_row in self.tier_rows:
            tier_row.set_template_mode(enabled)
    
    def reset_rankings(self) -> None:
        """Clear all character rankings from all tiers."""
        for tier_row in self.tier_rows:
            tier_row.clear_characters()
    
    def get_tier_rankings(self) -> Dict[str, List[RankableItem]]:
        """Get the current rankings for all tiers.
        
        Returns:
            Dictionary mapping tier names to lists of characters
        """
        rankings = {}
        for tier_row in self.tier_rows:
            tier_name = tier_row.tier.tier_name
            characters = tier_row.get_characters()
            rankings[tier_name] = characters
        
        return rankings
    
    def add_character_to_tier(self, tier_name: str, character: RankableItem) -> bool:
        """Add a character to a specific tier.
        
        Args:
            tier_name: The name of the tier to add to
            character: The character to add
            
        Returns:
            True if the character was added successfully
        """
        for tier_row in self.tier_rows:
            if tier_row.tier.tier_name == tier_name:
                tier_row.add_character(character)
                return True
        return False 