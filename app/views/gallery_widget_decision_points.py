#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gallery widget decision points extension.

This module contains the code to extend the GalleryWidget class with
decision points functionality. It is meant to be monkey-patched into
the GalleryWidget class after it is loaded.
"""

from typing import Dict, Any

from PyQt6.QtWidgets import QMessageBox, QPushButton, QHBoxLayout

def apply_to_gallery_widget(GalleryWidget):
    """Apply the decision points functionality to the GalleryWidget class.
    
    Args:
        GalleryWidget: The GalleryWidget class to extend
    """
    def open_decision_point_dialog(self) -> None:
        """Open the decision point dialog."""
        if not self.current_story_id:
            return
        
        try:
            from app.views.decision_point_dialog import DecisionPointDialog
            
            dialog = DecisionPointDialog(self.db_conn, self.current_story_id, self)
            result = dialog.exec()
            if result:
                # Success message
                QMessageBox.information(
                    self,
                    "Success",
                    "Decision point created successfully.",
                    QMessageBox.StandardButton.Ok
                )
        except Exception as e:
            print(f"Error opening decision point dialog: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error opening decision point dialog: {str(e)}",
                QMessageBox.StandardButton.Ok
            )
    
    # Add the method to the class
    GalleryWidget.open_decision_point_dialog = open_decision_point_dialog
    
    # Save the original __init__ method
    original_init = GalleryWidget.__init__
    
    def patched_init(self, *args, **kwargs):
        """Patched version of __init__ that adds the decision points button."""
        # Call the original __init__ method
        original_init(self, *args, **kwargs)
        
        # Add Decision Points button
        def add_decision_points_button():
            # Find the button layout in the main layout
            if hasattr(self, 'layout') and self.layout():
                for i in range(self.layout().count()):
                    item = self.layout().itemAt(i)
                    if item and item.layout() and isinstance(item.layout(), QHBoxLayout):
                        button_layout = item.layout()
                        
                        # Find the right position (after rebuild_recognition_button)
                        insert_pos = 0
                        for j in range(button_layout.count()):
                            widget = button_layout.itemAt(j).widget()
                            if widget and isinstance(widget, QPushButton) and widget.text() == "Rebuild Recognition DB":
                                insert_pos = j + 1
                                break
                        
                        # Create and add the button
                        self.decision_points_button = QPushButton("Decision Points")
                        self.decision_points_button.setToolTip("Manage decision points for the story")
                        self.decision_points_button.clicked.connect(self.open_decision_point_dialog)
                        self.decision_points_button.setEnabled(False)  # Will be enabled when a story is set
                        
                        # Insert at the right position
                        button_layout.insertWidget(insert_pos, self.decision_points_button)
                        return True
            
            return False
        
        # Try to add the button
        if not add_decision_points_button():
            print("Warning: Could not add decision points button, will try again later")
            # Try again after a short delay using a timer
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(500, add_decision_points_button)
    
    # Save the original set_story method
    original_set_story = GalleryWidget.set_story
    
    def patched_set_story(self, story_id, story_data):
        """Patched version of set_story that enables the decision points button."""
        # Call the original set_story method
        original_set_story(self, story_id, story_data)
        
        # Enable the decision points button
        if hasattr(self, 'decision_points_button'):
            self.decision_points_button.setEnabled(True)
    
    # Patch the methods
    GalleryWidget.__init__ = patched_init
    GalleryWidget.set_story = patched_set_story 