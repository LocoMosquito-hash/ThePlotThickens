#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Decision Points Tab for Timeline Widget in The Plot Thickens application.

This module contains the widget for displaying and managing decision points
within the Timeline tab.
"""

from typing import Dict, Any, List, Optional, Callable

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QListWidget, QListWidgetItem, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction

from app.views.decision_point_dialog import DecisionPointDialog
from app.db_sqlite import (
    get_story_decision_points, get_decision_options, delete_decision_point,
    update_decision_point
)


class DecisionPointItem(QListWidgetItem):
    """A list widget item representing a decision point."""
    
    def __init__(self, decision_point_data: Dict[str, Any]):
        """Initialize the decision point item.
        
        Args:
            decision_point_data: Dictionary containing decision point data
        """
        super().__init__()
        self.decision_point_data = decision_point_data
        self.decision_point_id = decision_point_data['id']
        self.title = decision_point_data['title']
        self.description = decision_point_data.get('description', '')
        
        # Set the item text
        self.setText(self.title)
        self.setToolTip(self.description if self.description else self.title)
        
        # Make the item draggable
        self.setFlags(self.flags() | Qt.ItemFlag.ItemIsDragEnabled)


class DecisionPointsTab(QWidget):
    """Widget for displaying and managing decision points in the timeline."""
    
    decision_points_changed = pyqtSignal()  # Signal emitted when decision points are modified
    
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
        
        main_layout.addLayout(header_layout)
        
        # Decision points list
        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.list_widget.itemDoubleClicked.connect(self.edit_decision_point)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.list_widget.model().rowsMoved.connect(self.on_items_reordered)
        
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
        
        for dp in self.decision_points:
            item = DecisionPointItem(dp)
            self.list_widget.addItem(item)
    
    def add_decision_point(self):
        """Open dialog to add a new decision point."""
        dialog = DecisionPointDialog(self.conn, self.story_id, self)
        result = dialog.exec()
        if result:
            # Refresh the list
            self.load_decision_points()
            self.decision_points_changed.emit()
    
    def edit_decision_point(self, item):
        """Open dialog to edit a decision point.
        
        Args:
            item: The selected DecisionPointItem
        """
        if isinstance(item, DecisionPointItem):
            dialog = DecisionPointDialog(
                self.conn, 
                self.story_id, 
                self,
                decision_point_id=item.decision_point_id
            )
            result = dialog.exec()
            if result:
                # Refresh the list
                self.load_decision_points()
                self.decision_points_changed.emit()
    
    def show_context_menu(self, position):
        """Show context menu for decision points.
        
        Args:
            position: Position where the menu should be shown
        """
        item = self.list_widget.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        
        # Edit action
        edit_action = QAction("Edit Decision Point", self)
        edit_action.triggered.connect(lambda: self.edit_decision_point(item))
        menu.addAction(edit_action)
        
        # Delete action
        delete_action = QAction("Delete Decision Point", self)
        delete_action.triggered.connect(lambda: self.delete_decision_point(item))
        menu.addAction(delete_action)
        
        menu.exec(self.list_widget.mapToGlobal(position))
    
    def delete_decision_point(self, item):
        """Delete a decision point.
        
        Args:
            item: The DecisionPointItem to delete
        """
        if not isinstance(item, DecisionPointItem):
            return
        
        reply = QMessageBox.question(
            self,
            "Delete Decision Point",
            f"Are you sure you want to delete the decision point '{item.title}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = delete_decision_point(self.conn, item.decision_point_id)
                if success:
                    # Remove from the list widget
                    row = self.list_widget.row(item)
                    self.list_widget.takeItem(row)
                    # Refresh the data
                    self.load_decision_points()
                    self.decision_points_changed.emit()
                else:
                    QMessageBox.warning(
                        self,
                        "Delete Failed",
                        "Failed to delete the decision point.",
                        QMessageBox.StandardButton.Ok
                    )
            except Exception as e:
                print(f"Error deleting decision point: {e}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Error deleting decision point: {str(e)}",
                    QMessageBox.StandardButton.Ok
                )
    
    def on_items_reordered(self):
        """Handle reordering of decision points via drag and drop."""
        # This method is called when items are reordered by drag and drop
        # We could update the display_order in the database here if needed
        self.decision_points_changed.emit() 