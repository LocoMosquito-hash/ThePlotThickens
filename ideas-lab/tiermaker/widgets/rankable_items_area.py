#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rankable items area widget for Tier Maker.

This module contains the widget that displays rankable items (characters)
in a scrollable grid layout.
"""

from typing import List, Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, 
    QLabel, QFrame, QSizePolicy
)

from models.rankable_item import RankableItem
from widgets.drag_drop_widgets import CharacterDragItem


class RankableItemsGrid(QWidget):
    """Grid widget that arranges rankable items in rows."""
    
    def __init__(self, items_per_row: int = 6, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.items_per_row = items_per_row
        self.items: List[RankableItem] = []
        self.item_widgets: List[CharacterDragItem] = []
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the UI for the grid."""
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        self.setLayout(self.main_layout)
        
        # Style the grid container
        self.setStyleSheet("""
            RankableItemsGrid {
                background-color: #1e1e1e;
                border-radius: 4px;
            }
        """)
    
    def set_items(self, items: List[RankableItem]) -> None:
        """Set the items to display in the grid.
        
        Args:
            items: List of rankable items to display
        """
        self.clear_items()
        self.items = items
        self._create_item_widgets()
        self._arrange_items()
    
    def clear_items(self) -> None:
        """Remove all items from the grid."""
        for widget in self.item_widgets:
            widget.setParent(None)
        
        self.item_widgets.clear()
        self.items.clear()
        
        # Clear all layouts
        while self.main_layout.count():
            child = self.main_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
    
    def _create_item_widgets(self) -> None:
        """Create widgets for all items."""
        for item in self.items:
            widget = CharacterDragItem(item)
            self.item_widgets.append(widget)
    
    def _arrange_items(self) -> None:
        """Arrange items in rows based on items_per_row."""
        if not self.item_widgets:
            return
        
        current_row_layout = None
        items_in_current_row = 0
        
        for widget in self.item_widgets:
            # Create new row if needed
            if current_row_layout is None or items_in_current_row >= self.items_per_row:
                current_row_layout = QHBoxLayout()
                current_row_layout.setSpacing(10)
                current_row_layout.setContentsMargins(0, 0, 0, 0)
                
                row_widget = QWidget()
                row_widget.setLayout(current_row_layout)
                self.main_layout.addWidget(row_widget)
                
                items_in_current_row = 0
            
            # Add widget to current row
            current_row_layout.addWidget(widget)
            items_in_current_row += 1
        
        # Add stretch to the last row if it's not full
        if current_row_layout and items_in_current_row < self.items_per_row:
            current_row_layout.addStretch()
        
        # Add stretch at the bottom
        self.main_layout.addStretch()
    
    def get_item_count(self) -> int:
        """Get the number of items in the grid.
        
        Returns:
            Number of items
        """
        return len(self.items)


class RankableItemsArea(QWidget):
    """Widget that displays rankable items in a scrollable area."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.items_grid: Optional[RankableItemsGrid] = None
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the UI for the rankable items area."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Title label
        self.title_label = QLabel("Rankable Items")
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: white;
                padding: 5px;
                background-color: #2b2b2b;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.title_label)
        
        # Create scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setMaximumHeight(300)  # Limit height to show 3-4 rows
        
        # Create the items grid
        self.items_grid = RankableItemsGrid()
        self.scroll_area.setWidget(self.items_grid)
        
        layout.addWidget(self.scroll_area)
        
        # Empty state label (hidden by default)
        self.empty_label = QLabel("No items to display.\nSelect a story and apply filters to load characters.")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-style: italic;
                padding: 20px;
                background-color: #2b2b2b;
                border: 1px dashed #555;
                border-radius: 4px;
            }
        """)
        self.empty_label.hide()
        layout.addWidget(self.empty_label)
        
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
            QScrollBar:horizontal {
                background-color: #2b2b2b;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: #555;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #666;
            }
        """)
    
    def set_items(self, items: List[RankableItem]) -> None:
        """Set the items to display.
        
        Args:
            items: List of rankable items to display
        """
        if items:
            self.items_grid.set_items(items)
            self.scroll_area.show()
            self.empty_label.hide()
            
            # Update title with count
            count = len(items)
            self.title_label.setText(f"Rankable Items ({count})")
        else:
            self.items_grid.clear_items()
            self.scroll_area.hide()
            self.empty_label.show()
            self.title_label.setText("Rankable Items")
    
    def clear_items(self) -> None:
        """Clear all items from the area."""
        self.set_items([])
    
    def get_item_count(self) -> int:
        """Get the number of items currently displayed.
        
        Returns:
            Number of items
        """
        if self.items_grid:
            return self.items_grid.get_item_count()
        return 0
    
    def set_items_per_row(self, count: int) -> None:
        """Set the number of items per row.
        
        Args:
            count: Number of items per row
        """
        if self.items_grid:
            self.items_grid.items_per_row = count
            # Re-arrange existing items
            if self.items_grid.items:
                self.items_grid._arrange_items() 