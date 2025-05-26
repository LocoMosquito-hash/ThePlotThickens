#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Batch Context Tagging Dialog for The Plot Thickens application.

This module contains the dialog for batch tagging/untagging contexts from multiple images.
"""

from typing import List, Dict, Any, Set
import logging

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox, QProgressDialog,
    QApplication, QWidget, QFrame, QLineEdit, QInputDialog,
    QMenu
)
from PyQt6.QtCore import Qt, QSize, QTimer, QPoint
from PyQt6.QtGui import QFont, QAction

from app.db_sqlite import (
    get_all_image_contexts, create_image_context, update_image_context,
    delete_image_context, add_context_to_image, remove_context_from_image,
    search_image_contexts, get_image_contexts
)


class ContextListItem(QListWidgetItem):
    """Custom list item for displaying contexts with checkboxes."""
    
    def __init__(self, context_data: Dict[str, Any], parent=None):
        """Initialize the context list item.
        
        Args:
            context_data: Context data dictionary
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.context_data = context_data
        self.context_id = context_data["id"]
        self.context_name = context_data["name"]
        
        # Set the display text
        self.setText(self.context_name)
        
        # Store context data
        self.setData(Qt.ItemDataRole.UserRole, context_data)
        
        # Make it checkable
        self.setFlags(self.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        self.setCheckState(Qt.CheckState.Unchecked)


class BatchContextTaggingDialog(QDialog):
    """Dialog for batch tagging/untagging contexts from multiple images."""
    
    def __init__(self, db_conn, selected_image_ids: Set[int], parent=None):
        """Initialize the batch context tagging dialog.
        
        Args:
            db_conn: Database connection
            selected_image_ids: Set of selected image IDs
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.selected_image_ids = selected_image_ids
        self.contexts = []
        self.filtered_contexts = []
        
        # Set up the dialog
        self.setWindowTitle("Batch Context Tagging")
        self.setModal(True)
        self.resize(500, 600)
        
        self.init_ui()
        self.load_contexts()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Header with information
        header_label = QLabel("Batch Context Tagging")
        header_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(header_label)
        
        # Info about selected images
        info_label = QLabel(f"Selected images: {len(self.selected_image_ids)}")
        info_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(info_label)
        
        # Instructions
        instructions = QLabel(
            "Search for contexts below, check the ones you want to apply, "
            "then click Apply to tag all selected images."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 10px;")
        layout.addWidget(instructions)
        
        # Search section
        search_layout = QHBoxLayout()
        
        search_label = QLabel("Search contexts:")
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to search contexts...")
        self.search_input.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_input)
        
        self.add_context_btn = QPushButton("Add to contexts")
        self.add_context_btn.clicked.connect(self.add_new_context)
        search_layout.addWidget(self.add_context_btn)
        
        layout.addLayout(search_layout)
        
        # Context list
        contexts_label = QLabel("Available contexts:")
        contexts_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(contexts_label)
        
        self.contexts_list = QListWidget()
        self.contexts_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.contexts_list.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.contexts_list)
        
        # Results section
        self.results_label = QLabel("Results:")
        self.results_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.results_label.hide()
        layout.addWidget(self.results_label)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        buttons_layout.addStretch()
        
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setDefault(True)
        self.apply_btn.clicked.connect(self.apply_contexts)
        buttons_layout.addWidget(self.apply_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_contexts(self):
        """Load all available contexts from the database."""
        self.contexts = get_all_image_contexts(self.db_conn)
        self.filtered_contexts = self.contexts.copy()
        self.populate_contexts_list()
    
    def populate_contexts_list(self):
        """Populate the contexts list with current filtered contexts."""
        self.contexts_list.clear()
        
        for context in self.filtered_contexts:
            item = ContextListItem(context)
            self.contexts_list.addItem(item)
    
    def on_search_changed(self, text: str):
        """Handle search text changes.
        
        Args:
            text: Search text
        """
        if text.strip():
            # Filter contexts based on search
            self.filtered_contexts = search_image_contexts(self.db_conn, text.strip())
        else:
            # Show all contexts
            self.filtered_contexts = self.contexts.copy()
        
        self.populate_contexts_list()
    
    def add_new_context(self):
        """Add a new context to the database."""
        search_text = self.search_input.text().strip()
        
        # Use search text as default if provided
        default_text = search_text if search_text else ""
        
        text, ok = QInputDialog.getText(
            self, 
            "Add New Context", 
            "Enter context name:",
            text=default_text
        )
        
        if ok and text.strip():
            context_id = create_image_context(self.db_conn, text.strip())
            
            if context_id:
                # Reload contexts and refresh the list
                self.load_contexts()
                
                # Clear search to show the new context
                self.search_input.clear()
                
                QMessageBox.information(
                    self, 
                    "Success", 
                    f"Context '{text.strip().capitalize()}' added successfully!"
                )
            else:
                QMessageBox.warning(
                    self, 
                    "Error", 
                    f"Failed to add context. It may already exist."
                )
    
    def show_context_menu(self, position: QPoint):
        """Show context menu for context items.
        
        Args:
            position: Position where the menu was requested
        """
        item = self.contexts_list.itemAt(position)
        if not item:
            return
        
        context_data = item.data(Qt.ItemDataRole.UserRole)
        
        menu = QMenu(self)
        
        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(lambda: self.edit_context(context_data))
        menu.addAction(edit_action)
        
        remove_action = QAction("Remove", self)
        remove_action.triggered.connect(lambda: self.remove_context(context_data))
        menu.addAction(remove_action)
        
        menu.exec(self.contexts_list.mapToGlobal(position))
    
    def edit_context(self, context_data: Dict[str, Any]):
        """Edit a context name.
        
        Args:
            context_data: Context data dictionary
        """
        current_name = context_data["name"]
        
        text, ok = QInputDialog.getText(
            self, 
            "Edit Context", 
            "Enter new context name:",
            text=current_name
        )
        
        if ok and text.strip() and text.strip() != current_name:
            # Confirm the change
            reply = QMessageBox.question(
                self,
                "Confirm Edit",
                f"Are you sure you want to rename '{current_name}' to '{text.strip().capitalize()}'?\n\n"
                "This will update the context name for all tagged images.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                success = update_image_context(self.db_conn, context_data["id"], text.strip())
                
                if success:
                    # Reload contexts and refresh the list
                    self.load_contexts()
                    
                    QMessageBox.information(
                        self, 
                        "Success", 
                        f"Context renamed to '{text.strip().capitalize()}' successfully!"
                    )
                else:
                    QMessageBox.warning(
                        self, 
                        "Error", 
                        "Failed to rename context. The new name may already exist."
                    )
    
    def remove_context(self, context_data: Dict[str, Any]):
        """Remove a context from the database.
        
        Args:
            context_data: Context data dictionary
        """
        context_name = context_data["name"]
        
        # Confirm the deletion
        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to remove the context '{context_name}'?\n\n"
            "This will remove it from all tagged images and cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success = delete_image_context(self.db_conn, context_data["id"])
            
            if success:
                # Reload contexts and refresh the list
                self.load_contexts()
                
                QMessageBox.information(
                    self, 
                    "Success", 
                    f"Context '{context_name}' removed successfully!"
                )
            else:
                QMessageBox.warning(
                    self, 
                    "Error", 
                    "Failed to remove context."
                )
    
    def apply_contexts(self):
        """Apply selected contexts to all selected images."""
        # Get selected contexts
        selected_contexts = []
        for i in range(self.contexts_list.count()):
            item = self.contexts_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                context_data = item.data(Qt.ItemDataRole.UserRole)
                selected_contexts.append(context_data)
        
        if not selected_contexts:
            QMessageBox.warning(
                self, 
                "No Contexts Selected", 
                "Please select at least one context to apply."
            )
            return
        
        # Show progress dialog
        total_expected_operations = len(self.selected_image_ids) * len(selected_contexts)
        progress = QProgressDialog(
            "Applying contexts to images...",
            "Cancel",
            0,
            total_expected_operations,
            self
        )
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        # Apply contexts to images
        total_operations = 0
        successful_operations = 0
        user_cancelled = False
        
        for image_id in self.selected_image_ids:
            for context in selected_contexts:
                # Check for cancellation before each operation
                if progress.wasCanceled():
                    user_cancelled = True
                    break
                
                success = add_context_to_image(self.db_conn, image_id, context["id"])
                if success:
                    successful_operations += 1
                
                total_operations += 1
                progress.setValue(total_operations)
                QApplication.processEvents()
            
            # Break outer loop if cancelled
            if user_cancelled:
                break
        
        # Close progress dialog
        progress.close()
        
        # Show results based on whether operation completed or was cancelled
        if user_cancelled:
            QMessageBox.information(
                self,
                "Operation Cancelled",
                f"Context tagging was cancelled by user.\n\n"
                f"Applied {successful_operations} context tags before cancellation."
            )
        else:
            # Operation completed successfully
            context_names = [ctx["name"] for ctx in selected_contexts]
            contexts_text = ", ".join(context_names)
            
            QMessageBox.information(
                self,
                "Contexts Applied",
                f"Successfully applied contexts to {len(self.selected_image_ids)} images.\n\n"
                f"Contexts: {contexts_text}\n"
                f"Total operations: {successful_operations}/{total_expected_operations}"
            )
        
        # Close the dialog
        self.accept() 