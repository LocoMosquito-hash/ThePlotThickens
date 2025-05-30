#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Decision Points Tab for The Plot Thickens application.

This module contains the tab for viewing and managing decision points in a story.
"""

from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox, QMenu, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal

from app.db_sqlite import (
    get_story_decision_points,
    get_decision_options,
    delete_decision_point
)
from app.views.decision_point_dialog import DecisionPointDialog


class DecisionPointItem(QListWidgetItem):
    """A list widget item representing a decision point."""
    
    def __init__(self, decision_point_data: Dict[str, Any], db_conn=None, index: Optional[int] = None):
        """Initialize the decision point item.
        
        Args:
            decision_point_data: Dictionary with decision point data
            db_conn: Database connection (optional)
            index: Index number for display (optional)
        """
        super().__init__()
        self.decision_point_data = decision_point_data
        self.decision_point_id = decision_point_data['id']
        self.title = decision_point_data['title']
        self.description = decision_point_data.get('description', '')
        self.is_ordered_list = bool(decision_point_data.get('is_ordered_list', 0))
        self.db_conn = db_conn
        self.index = index
        
        # Get options data for display
        self.options = self.get_options()
        
        # Set the item text with a summary
        item_text = self.title
        
        # Add number prefix if index is provided
        if self.index is not None:
            item_text = f"{self.index}. {item_text}"
        
        if self.options:
            # Add a count of options to the display text
            type_indicator = "📋" if self.is_ordered_list else "🔘"
            item_text += f" {type_indicator} ({len(self.options)})"
        self.setText(item_text)
        
        # Set tooltip with more details
        tooltip_text = f"{self.title}"
        if self.description:
            tooltip_text += f"\n\n{self.description}"
            
        tooltip_text += f"\n\nType: {'Ordered List' if self.is_ordered_list else 'Single Choice'}"
        
        # Add options to tooltip
        if self.options:
            tooltip_text += "\n\nOptions:"
            for i, option in enumerate(self.options):
                option_text = option.get('text', '')
                
                # Add indicator for selected option in single choice mode
                if not self.is_ordered_list and option.get('is_selected'):
                    tooltip_text += f"\n✓ {option_text}"
                # Add order number for ordered lists
                elif self.is_ordered_list and option.get('played_order') is not None:
                    tooltip_text += f"\n{option.get('played_order')}. {option_text}"
                else:
                    tooltip_text += f"\n• {option_text}"
                    
        self.setToolTip(tooltip_text)
        
        # Make the item draggable
        self.setFlags(self.flags() | Qt.ItemFlag.ItemIsDragEnabled)
    
    def get_options(self) -> List[Dict[str, Any]]:
        """Get all options for this decision point.
        
        Returns:
            List of option dictionaries
        """
        if not self.db_conn:
            return []
            
        from app.db_sqlite import get_decision_options
        
        try:
            return get_decision_options(self.db_conn, self.decision_point_id)
        except Exception as e:
            print(f"Error getting options: {e}")
            return []
    
    def get_options_count(self) -> int:
        """Get the number of options for this decision point.
        
        Returns:
            Count of options
        """
        return len(self.options)


class DecisionPointsTab(QWidget):
    """Tab for viewing and managing decision points in a story."""
    
    # Signal emitted when decision points are modified
    decision_points_changed = pyqtSignal()
    
    def __init__(self, conn, story_id: int, parent=None):
        """Initialize the decision points tab.
        
        Args:
            conn: Database connection
            story_id: ID of the story
            parent: Parent widget
        """
        super().__init__(parent)
        self.conn = conn
        self.story_id = story_id
        self.decision_points = []
        
        self.init_ui()
        self.load_decision_points()
    
    def init_ui(self):
        """Set up the user interface."""
        main_layout = QVBoxLayout(self)
        
        # Header with title and add button
        header_layout = QHBoxLayout()
        title_label = QLabel("Decision Points")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(title_label)
        
        # Add decision point button
        self.add_button = QPushButton("Add Decision Point")
        self.add_button.clicked.connect(self.add_decision_point)
        header_layout.addWidget(self.add_button)
        
        header_layout.addStretch()
        main_layout.addLayout(header_layout)
        
        # Decision points list
        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.list_widget.itemDoubleClicked.connect(self.edit_decision_point)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.list_widget.model().rowsMoved.connect(self.on_items_reordered)
        
        # Make the list more compact
        self.list_widget.setSpacing(1)  # Reduce spacing between items
        self.list_widget.setStyleSheet("""
            QListWidget {
                font-size: 11pt;
            }
            QListWidget::item {
                padding: 2px 4px;
                border-bottom: 1px solid #e0e0e0;
            }
        """)
        
        main_layout.addWidget(self.list_widget)
    
    def load_decision_points(self):
        """Load decision points from the database."""
        try:
            self.decision_points = get_story_decision_points(self.conn, self.story_id)
            self.update_list()
        except Exception as e:
            print(f"Error loading decision points: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error loading decision points: {str(e)}",
                QMessageBox.StandardButton.Ok
            )
    
    def update_list(self):
        """Update the list widget with decision points."""
        self.list_widget.clear()
        
        for i, dp in enumerate(self.decision_points, 1):  # Start numbering from 1
            item = DecisionPointItem(dp, self.conn, index=i)
            self.list_widget.addItem(item)
    
    def add_decision_point(self):
        """Open dialog to add a new decision point."""
        dialog = DecisionPointDialog(self.conn, self.story_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Refresh the list
            self.load_decision_points()
            # Emit signal that decision points changed
            self.decision_points_changed.emit()
    
    def edit_decision_point(self, item: Optional[DecisionPointItem] = None):
        """Open dialog to edit an existing decision point.
        
        Args:
            item: The decision point item to edit (optional, will use selected item if None)
        """
        # Get the item to edit
        if not item:
            current_item = self.list_widget.currentItem()
            if not current_item:
                return
            item = current_item
        
        # Ensure item is a DecisionPointItem
        if not isinstance(item, DecisionPointItem):
            return
        
        # Open the dialog for editing
        dialog = DecisionPointDialog(self.conn, self.story_id, self, item.decision_point_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Refresh the list
            self.load_decision_points()
            # Emit signal that decision points changed
            self.decision_points_changed.emit()
    
    def delete_decision_point(self, item: Optional[DecisionPointItem] = None):
        """Delete a decision point.
        
        Args:
            item: The decision point item to delete (optional, will use selected item if None)
        """
        # Get the item to delete
        if not item:
            current_item = self.list_widget.currentItem()
            if not current_item:
                return
            item = current_item
        
        # Ensure item is a DecisionPointItem
        if not isinstance(item, DecisionPointItem):
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the decision point '{item.title}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Delete from database
        success = delete_decision_point(self.conn, item.decision_point_id)
        
        if success:
            # Remove from UI
            row = self.list_widget.row(item)
            self.list_widget.takeItem(row)
            
            # Refresh the list
            self.load_decision_points()
            
            # Emit signal that decision points changed
            self.decision_points_changed.emit()
        else:
            QMessageBox.critical(
                self,
                "Error",
                "Failed to delete decision point.",
                QMessageBox.StandardButton.Ok
            )
    
    def show_context_menu(self, position):
        """Show context menu for decision points list.
        
        Args:
            position: Position where to show the menu
        """
        item = self.list_widget.itemAt(position)
        if not item:
            return
            
        # Create menu
        menu = QMenu(self)
        
        # Add actions
        edit_action = menu.addAction("Edit")
        edit_action.triggered.connect(lambda: self.edit_decision_point(item))
        
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self.delete_decision_point(item))
        
        # Show menu at cursor position
        menu.exec(self.list_widget.mapToGlobal(position))
    
    def on_items_reordered(self):
        """Handle items being reordered through drag-and-drop."""
        # TODO: Implement reordering in database if needed
        # For now, just refresh the list
        self.load_decision_points()
    
    def set_story_id(self, story_id: int):
        """Change the current story.
        
        Args:
            story_id: ID of the story
        """
        if self.story_id != story_id:
            self.story_id = story_id
            self.load_decision_points() 