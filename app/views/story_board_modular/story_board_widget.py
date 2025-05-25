#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Story Board Widget for The Plot Thickens application.

This module contains the main StoryBoardWidget class that provides the complete
story board interface including toolbar, view management, and scene integration.
"""

import os
import sys
import json
import math
from typing import Optional, List, Dict, Any, Tuple

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QMenu, QInputDialog, QMessageBox, QToolBar, 
    QCheckBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSettings
from PyQt6.QtGui import QTransform

from app.db_sqlite import (
    get_story, get_story_characters, get_character_relationships,
    get_story_board_views, get_story_board_view, create_story_board_view,
    update_story_board_view_layout, get_relationship_types, create_relationship,
    get_story_relationships, get_used_relationship_types, delete_character,
    get_character
)

from .scene_view import StoryBoardScene, StoryBoardView
from .utils import create_vertical_line, calculate_grid_layout


class StoryBoardWidget(QWidget):
    """Widget for the story board visualization."""
    
    character_selected = pyqtSignal(int, dict)  # Signal emitted when a single character is selected
    selection_changed = pyqtSignal(list)  # Signal emitted with list of selected character data
    
    def __init__(self, db_conn) -> None:
        """Initialize the story board widget.
        
        Args:
            db_conn: Database connection
        """
        super().__init__()
        
        self.db_conn = db_conn
        self.current_story_id = None
        self.current_story_data = None
        self.current_view_id = None
        self.currently_selected_character_ids = []  # Track multiple selected characters
        
        # Initialize QSettings
        self.settings = QSettings("ThePlotThickens", "ThePlotThickens")
        
        self.init_ui()
    
    def init_ui(self) -> None:
        """Set up the user interface."""
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create toolbar
        toolbar = QToolBar()
        
        # Add view selector
        self.view_selector = QComboBox()
        self.view_selector.setMinimumWidth(200)
        self.view_selector.currentIndexChanged.connect(self.on_view_selected)
        toolbar.addWidget(QLabel("View:"))
        toolbar.addWidget(self.view_selector)
        
        # Add view management buttons
        self.add_view_button = QPushButton("New View")
        self.add_view_button.clicked.connect(self.on_add_view)
        toolbar.addWidget(self.add_view_button)
        
        self.rename_view_button = QPushButton("Rename")
        self.rename_view_button.clicked.connect(self.on_rename_view)
        toolbar.addWidget(self.rename_view_button)
        
        self.save_view_button = QPushButton("Save View")
        self.save_view_button.clicked.connect(self.on_save_view)
        toolbar.addWidget(self.save_view_button)
        
        self.delete_view_button = QPushButton("Delete")
        self.delete_view_button.clicked.connect(self.on_delete_view)
        toolbar.addWidget(self.delete_view_button)
        
        toolbar.addSeparator()
        
        # Add zoom controls
        self.zoom_in_button = QPushButton("Zoom In")
        self.zoom_in_button.clicked.connect(self.on_zoom_in)
        toolbar.addWidget(self.zoom_in_button)
        
        self.zoom_out_button = QPushButton("Zoom Out")
        self.zoom_out_button.clicked.connect(self.on_zoom_out)
        toolbar.addWidget(self.zoom_out_button)
        
        self.reset_zoom_button = QPushButton("Reset Zoom")
        self.reset_zoom_button.clicked.connect(self.on_reset_zoom)
        toolbar.addWidget(self.reset_zoom_button)
        
        toolbar.addSeparator()
        
        # Add relationship types manager button
        self.manage_relationship_types_button = QPushButton("Manage Relationship Types")
        self.manage_relationship_types_button.clicked.connect(self.on_manage_relationship_types)
        toolbar.addWidget(self.manage_relationship_types_button)
        
        toolbar.addSeparator()
        
        # Add grid snapping controls
        self.grid_snap_checkbox = QCheckBox("Snap to Grid")
        self.grid_snap_checkbox.setChecked(self.settings.value("storyboard/grid_snap", False, type=bool))
        self.grid_snap_checkbox.stateChanged.connect(self.on_grid_snap_changed)
        toolbar.addWidget(self.grid_snap_checkbox)
        
        self.grid_visible_checkbox = QCheckBox("Show Grid")
        self.grid_visible_checkbox.setChecked(self.settings.value("storyboard/grid_visible", False, type=bool))
        self.grid_visible_checkbox.stateChanged.connect(self.on_grid_visible_changed)
        toolbar.addWidget(self.grid_visible_checkbox)
        
        self.grid_size_label = QLabel("Grid Size:")
        toolbar.addWidget(self.grid_size_label)
        
        self.grid_size_combo = QComboBox()
        self.grid_size_combo.addItems(["25", "50", "75", "100"])
        saved_grid_size = self.settings.value("storyboard/grid_size", "50", type=str)
        index = self.grid_size_combo.findText(saved_grid_size)
        self.grid_size_combo.setCurrentIndex(index if index != -1 else 1)  # Default to 50 if not found
        self.grid_size_combo.currentIndexChanged.connect(self.on_grid_size_changed)
        toolbar.addWidget(self.grid_size_combo)
        
        toolbar.addSeparator()
        
        # Add layout controls
        self.reset_positions_button = QPushButton("Reset Positions")
        self.reset_positions_button.clicked.connect(self.reset_character_positions)
        toolbar.addWidget(self.reset_positions_button)
        
        # Create position cards button
        self.position_cards_button = QPushButton("Position Cards")
        self.position_cards_button.clicked.connect(self.position_cards)
        self.position_cards_button.setToolTip("Position cards according to saved layout")
        toolbar.addWidget(self.position_cards_button)
        
        main_layout.addWidget(toolbar)
        
        # Create graphics view
        self.view = StoryBoardView()
        main_layout.addWidget(self.view)
        
        # Create scene
        self.scene = StoryBoardScene(self, self.db_conn)
        self.view.setScene(self.scene)
        
        # Connect signals - ensure proper typing for selection_changed
        self.scene.layout_changed.connect(self.on_layout_changed)
        self.scene.character_selected.connect(self.on_character_selected)
        self.scene.selection_changed.connect(self.on_selection_changed)  # This should handle List[int]
        
        # Disable controls initially
        self.view_selector.setEnabled(False)
        self.add_view_button.setEnabled(False)
        self.rename_view_button.setEnabled(False)
        self.save_view_button.setEnabled(False)
        self.delete_view_button.setEnabled(False)
        self.zoom_in_button.setEnabled(False)
        self.zoom_out_button.setEnabled(False)
        self.reset_zoom_button.setEnabled(False)
        self.reset_positions_button.setEnabled(False)
        self.position_cards_button.setEnabled(False)
        self.grid_snap_checkbox.setEnabled(False)
        self.grid_visible_checkbox.setEnabled(False)
        self.grid_size_combo.setEnabled(False)
        self.manage_relationship_types_button.setEnabled(False)
        
        # Auto-save timer
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.setInterval(2000)  # 2 seconds
        self.auto_save_timer.timeout.connect(self.save_current_view)
        self.auto_save_timer.setSingleShot(True)
    
    def set_story(self, story_id: int, story_data: Dict[str, Any]) -> None:
        """Set the current story.
        
        Args:
            story_id: ID of the story
            story_data: Story data
        """
        self.current_story_id = story_id
        self.current_story_data = story_data
        
        # Enable UI controls
        self.view_selector.setEnabled(True)
        self.add_view_button.setEnabled(True)
        self.rename_view_button.setEnabled(True)
        self.save_view_button.setEnabled(True)
        self.delete_view_button.setEnabled(True)
        self.zoom_in_button.setEnabled(True)
        self.zoom_out_button.setEnabled(True)
        self.reset_zoom_button.setEnabled(True)
        self.reset_positions_button.setEnabled(True)
        self.position_cards_button.setEnabled(True)
        self.grid_snap_checkbox.setEnabled(True)
        self.grid_visible_checkbox.setEnabled(True)
        self.grid_size_combo.setEnabled(True)
        self.manage_relationship_types_button.setEnabled(True)
        
        # Apply saved grid settings to the scene
        self.apply_grid_settings()
        
        # Load views
        self.load_views()
    
    def load_views(self) -> None:
        """Load all views for the current story."""
        if not self.current_story_id:
            return
        
        # Clear the view selector
        self.view_selector.clear()
        
        # Get views from database
        views = get_story_board_views(self.db_conn, self.current_story_id)
        
        # Add views to selector
        for view in views:
            self.view_selector.addItem(view['name'], view['id'])
        
        # If no views exist, create a default one
        if not views:
            self.create_default_view()
        else:
            # Load the first view
            self.view_selector.setCurrentIndex(0)
            self.load_view(views[0]['id'])
    
    def create_default_view(self) -> None:
        """Create a default 'Main' view for the story."""
        if not self.current_story_id:
            return
            
        # Create empty layout with characters dictionary
        layout = {"characters": {}}
        
        # Get all characters
        characters = get_story_characters(self.db_conn, self.current_story_id)
        
        # Add characters to layout with default positions
        for i, character in enumerate(characters):
            # Arrange characters in a grid
            cols = max(1, int(math.sqrt(len(characters))))
            row = i // cols
            col = i % cols
            
            character_id = character['id']
            x = 100 + col * 200
            y = 100 + row * 250
            
            layout["characters"][str(character_id)] = {"x": x, "y": y}
        
        # Create view
        view_id = create_story_board_view(
                        self.db_conn,
            name="Main",
            story_id=self.current_story_id,
            layout_data=json.dumps(layout)
        )
        
        # Add to selector and select it
        self.view_selector.addItem("Main", view_id)
        self.view_selector.setCurrentIndex(0)
        
        # Load the view
        self.load_view(view_id)
    
    def load_view(self, view_id: int) -> None:
        """Load a view from the database.
        
        Args:
            view_id: ID of the view to load
        """
        print(f"LOAD VIEW: Loading view {view_id}")
        
        if not self.current_story_id:
            return
        
        # Store current positions before clearing
        current_positions = {}
        if self.scene and hasattr(self.scene, 'character_cards'):
            for character_id, card in self.scene.character_cards.items():
                pos = card.pos()
                current_positions[character_id] = (pos.x(), pos.y())
        
        # Get view data
        view_data = get_story_board_view(self.db_conn, view_id)
        if not view_data:
            print("DEBUG: Could not find view data")
            return
        
        # Update current view
        self.current_view_id = view_id
        
        # Log card count before clearing
        print(f"LOAD VIEW: Before clearing - {len(self.scene.character_cards)} cards in scene")
        
        # Clear the scene
        self.scene.clear_board()
        
        # Parse layout data
        try:
            layout_data = json.loads(view_data['layout_data'])
        except json.JSONDecodeError:
            layout_data = {}
        
        # Get characters
        characters = get_story_characters(self.db_conn, self.current_story_id)
        print(f"LOAD VIEW: Found {len(characters)} characters in database for story {self.current_story_id}")
        
        # Add character cards to the scene
        for character in characters:
            character_id = character['id']
            
            # Get position from layout data or current positions
            x, y = 0, 0
            if str(character_id) in current_positions:
                # Use current position if available
                x, y = current_positions[str(character_id)]
            elif 'characters' in layout_data and str(character_id) in layout_data['characters']:
                # Fall back to layout data
                char_pos = layout_data['characters'][str(character_id)]
                x = float(char_pos['x'])
                y = float(char_pos['y'])
            
            # Add character card with position suppression
            card = self.scene.add_character_card(character_id, character, x, y)
            if card:
                card.suppress_position_updates = True
                card.setPos(x, y)
                card.suppress_position_updates = False
        
        # Get relationships for this story
        relationships = get_story_relationships(self.db_conn, self.current_story_id)
        
        # Add relationship lines to the scene
        for relationship in relationships:
            relationship_id = relationship['id']
            source_id = relationship['source_id']
            target_id = relationship['target_id']
            
            # Create relationship data
            relationship_data = {
                'relationship_type': relationship['relationship_type'],
                'color': relationship['color'],
                'width': relationship['width']
            }
            
            # Add relationship line - this will automatically group with existing lines
            self.scene.add_relationship_line(relationship_id, relationship_data, source_id, target_id)
        
        # Log card count after loading
        print(f"LOAD VIEW: After loading - {len(self.scene.character_cards)} cards in scene")
        
        # Ensure all bendpoints are initially hidden
        self.scene._update_bendpoint_visibility()
        
        # Only center if this is the first load (no current positions)
        if not current_positions:
            self.view.center_on_characters()
    
    def on_view_selected(self, index: int) -> None:
        """Handle view selection change.
        
        Args:
            index: Selected index
        """
        if index < 0 or not self.current_story_id:
            return
        
        # Get the view ID
        view_id = self.view_selector.itemData(index)
        
        # Load the view
        self.load_view(view_id)
    
    def on_add_view(self) -> None:
        """Handle new view button click."""
        if not self.current_story_id:
            return
            
        # Get view name
        name, ok = QInputDialog.getText(self, "New View", "Enter view name:")
        if not ok or not name:
                return
            
        # Create empty layout with characters dictionary
        layout = {"characters": {}}
        
        # Get all characters
        characters = get_story_characters(self.db_conn, self.current_story_id)
        
        # Add characters to layout with default positions
        for i, character in enumerate(characters):
            # Arrange characters in a grid
            cols = max(1, int(math.sqrt(len(characters))))
            row = i // cols
            col = i % cols
            
            character_id = character['id']
            x = 100 + col * 200
            y = 100 + row * 250
            
            layout["characters"][str(character_id)] = {"x": x, "y": y}
        
        # Create view
        view_id = create_story_board_view(
                        self.db_conn,
            name=name,
            story_id=self.current_story_id,
            layout_data=json.dumps(layout)
        )
        
        # Add to selector and select it
        self.view_selector.addItem(name, view_id)
        self.view_selector.setCurrentIndex(self.view_selector.count() - 1)
        
        # Load the view
        self.load_view(view_id)
    
    def on_rename_view(self) -> None:
        """Handle rename view button click."""
        # TODO: Implement rename view functionality
        QMessageBox.information(self, "Not Implemented", "Rename view functionality is not yet implemented.")
    
    def on_save_view(self) -> None:
        """Handle save view button click."""
        if not self.current_story_id or not self.current_view_id:
                    return
        
        # Get layout data
        layout_data = self.scene.get_layout_data()
        
        # Update view
        update_story_board_view_layout(
            self.db_conn,
            self.current_view_id,
            json.dumps(layout_data)
        )
        
        QMessageBox.information(self, "Success", "View saved successfully.")
    
    def on_delete_view(self) -> None:
        """Handle delete view button click."""
        # TODO: Implement delete view functionality
        QMessageBox.information(self, "Not Implemented", "Delete view functionality is not yet implemented.")
    
    def on_manage_relationship_types(self) -> None:
        """Open the relationship types manager window."""
        from app.views.relationship_types_manager import RelationshipTypesManager
        manager = RelationshipTypesManager(self, db_conn=self.db_conn)
        manager.show()
    
    def on_zoom_in(self) -> None:
        """Handle zoom in button click."""
        self.view.current_zoom *= self.view.zoom_factor
        if self.view.current_zoom > self.view.max_zoom:
            self.view.current_zoom = self.view.max_zoom
        self.view.setTransform(QTransform().scale(self.view.current_zoom, self.view.current_zoom))
    
    def on_zoom_out(self) -> None:
        """Handle zoom out button click."""
        self.view.current_zoom /= self.view.zoom_factor
        if self.view.current_zoom < self.view.min_zoom:
            self.view.current_zoom = self.view.min_zoom
        self.view.setTransform(QTransform().scale(self.view.current_zoom, self.view.current_zoom))
    
    def on_reset_zoom(self) -> None:
        """Handle reset zoom button click."""
        self.view.current_zoom = 1.0
        self.view.setTransform(QTransform()) 
    
    def on_layout_changed(self) -> None:
        """Handle layout changed signal."""
        # Only start auto-save timer if it's not already running
        if not self.auto_save_timer.isActive():
            self.auto_save_timer.start()
    
    def save_current_view(self) -> None:
        """Save the current view layout."""
        print(f"SAVE VIEW: Saving view {self.current_view_id}")
        
        if not self.current_story_id or not self.current_view_id:
            return
            
        # Get layout data
        layout_data = self.scene.get_layout_data()
        
        # Update view
        update_story_board_view_layout(
            self.db_conn,
            self.current_view_id,
            json.dumps(layout_data)
        )
        
        print(f"SAVE VIEW: View {self.current_view_id} saved successfully")
        
        # Show a brief status message
        main_window = self.window()
        if hasattr(main_window, 'status_bar'):
            main_window.status_bar.showPermanentMessage("View layout saved")
    
    def on_character_updated(self, character_id: int, character_data: Dict[str, Any]) -> None:
        """Handle character update in the scene.
        
        Args:
            character_id: ID of the updated character
            character_data: Updated character data
        """
        # Log card count before update
        print(f"CARD COUNT: Before character update - {len(self.scene.character_cards)} cards in scene")
        
        # Find the card
        old_card = self.scene.character_cards.get(character_id)
        if not old_card:
            return
            
        # Store current position
        current_pos = old_card.pos()
        print(f"DEBUG: Stored position for character {character_id}: ({current_pos.x()}, {current_pos.y()})")
        
        # Store relationships
        relationships = old_card.relationships.copy()
        
        # Remove the old card from the scene's tracking dictionary FIRST
        # This is important to prevent any references to the old card
        del self.scene.character_cards[character_id]
        
        # Remove the old card from the scene
        self.scene.removeItem(old_card)
        
        # Force a scene update to ensure the old card is completely removed
        self.scene.update()
        
        # Create a new card at the same position
        from .graphics_components import CharacterCard
        new_card = CharacterCard(character_id, character_data, current_pos.x(), current_pos.y())
        
        # Add the new card to the scene
        self.scene.addItem(new_card)
        
        # Update the scene's tracking of character cards
        self.scene.character_cards[character_id] = new_card
        
        # Connect to position changed signal
        new_card.position_changed.connect(self.scene.on_character_position_changed)
        
        # Update relationships
        for relationship in relationships:
            # Update the relationship to use the new card
            if relationship.source_card == old_card:
                relationship.source_card = new_card
                new_card.add_relationship(relationship)
            elif relationship.target_card == old_card:
                relationship.target_card = new_card
                new_card.add_relationship(relationship)
            
            # Update the relationship position
            relationship.update_position()
        
        # Verify the new card's position
        new_pos = new_card.pos()
        print(f"DEBUG: New card position for character {character_id}: ({new_pos.x()}, {new_pos.y()})")
        
        # Save the view without reloading
        self.save_current_view()
        
        # Log card count after update
        print(f"CARD COUNT: After character update - {len(self.scene.character_cards)} cards in scene")
        
        # Force the view to update
        self.view.viewport().update()
    
    def reset_character_positions(self) -> None:
        """Reset character positions to a default layout.
        
        This is useful when characters are placed too far apart or outside the visible area.
        """
        if not self.scene or not hasattr(self.scene, 'character_cards') or not self.scene.character_cards:
            return
        
        # Get the number of characters
        num_characters = len(self.scene.character_cards)
        
        # Calculate grid dimensions
        cols = max(1, int(math.sqrt(num_characters)))
        rows = (num_characters + cols - 1) // cols  # Ceiling division
        
        # Calculate spacing
        spacing_x = 200
        spacing_y = 250
        
        # Start position
        start_x = 100
        start_y = 100
        
        # Arrange characters in a grid
        for i, (character_id, card) in enumerate(self.scene.character_cards.items()):
            row = i // cols
            col = i % cols
            
            # Calculate new position
            new_x = start_x + col * spacing_x
            new_y = start_y + row * spacing_y
            
            # Set new position
            card.setPos(new_x, new_y)
        
        # Center on the characters
        self.view.center_on_characters()
        
        # Save the new layout
        self.save_current_view()
        
        # Force the view to update
        self.view.viewport().update()
    
    def apply_grid_settings(self) -> None:
        """Apply the saved grid settings to the scene."""
        if self.scene:
            # Apply grid snap
            self.scene.set_grid_snap(self.grid_snap_checkbox.isChecked())
            
            # Apply grid visibility
            self.scene.set_grid_visible(self.grid_visible_checkbox.isChecked())
            
            # Apply grid size
            grid_size = int(self.grid_size_combo.currentText())
            self.scene.set_grid_size(grid_size)
    
    def on_grid_snap_changed(self, state: int) -> None:
        """Handle grid snap checkbox state change.
        
        Args:
            state: Checkbox state
        """
        if self.scene:
            is_checked = state == Qt.CheckState.Checked.value
            self.scene.set_grid_snap(is_checked)
            # Save setting
            self.settings.setValue("storyboard/grid_snap", is_checked)
    
    def on_grid_visible_changed(self, state: int) -> None:
        """Handle grid visibility checkbox state change.
        
        Args:
            state: Checkbox state
        """
        if self.scene:
            is_checked = state == Qt.CheckState.Checked.value
            self.scene.set_grid_visible(is_checked)
            # Save setting
            self.settings.setValue("storyboard/grid_visible", is_checked)
    
    def on_grid_size_changed(self, index: int) -> None:
        """Handle grid size combo box change.
        
        Args:
            index: Selected index
        """
        if self.scene:
            grid_size = int(self.grid_size_combo.currentText())
            self.scene.set_grid_size(grid_size)
            # Save setting
            self.settings.setValue("storyboard/grid_size", self.grid_size_combo.currentText())
    
    def position_cards(self) -> None:
        """Position cards according to saved layout and show debug info."""
        if not self.current_story_id or not self.current_view_id:
            print("DEBUG: No current story or view")
            return
            
        # Get the current view data
        view = get_story_board_view(self.db_conn, self.current_view_id)
        if not view:
            print("DEBUG: Could not find view data")
            return
            
        print(f"\nDEBUG: Retrieved view data: {view}")
        
        # Load layout
        layout = json.loads(view['layout_data'])
        print(f"\nDEBUG: Parsed layout data: {layout}")
        
        # Get all characters
        characters = get_story_characters(self.db_conn, self.current_story_id)
        print(f"\nDEBUG: Found {len(characters)} characters")
        
        # Position each character
        for character in characters:
            character_id = character['id']
            card = self.scene.character_cards.get(character_id)
            
            if not card:
                print(f"DEBUG: No card found for character {character_id}")
                continue
            
            # Get saved position
            if 'characters' in layout and str(character_id) in layout['characters']:
                position = layout['characters'][str(character_id)]
                x = position.get('x', 0)
                y = position.get('y', 0)
                print(f"DEBUG: Setting character {character_id} position to ({x}, {y})")
                
                # Set new position
                card.setPos(x, y)
            else:
                print(f"DEBUG: No position data found for character {character_id}")
        
        # Center on the characters
        self.view.center_on_characters()
        
        # Force the view to update
        self.view.viewport().update() 
    
    def on_character_selected(self, character_id: int) -> None:
        """Handle single character selection.
        
        Args:
            character_id: ID of the selected character
        """
        # Ensure the character ID is in the selected list
        if character_id not in self.currently_selected_character_ids:
            self.currently_selected_character_ids = [character_id]
        
        # Get character data
        character_data = None
        if character_id in self.scene.character_cards:
            character_data = self.scene.character_cards[character_id].character_data
        
        # Emit the character selected signal with ID and data
        if character_data:
            self.character_selected.emit(character_id, character_data)
            
            # Display a status message
            main_window = self.window()
            if hasattr(main_window, 'status_bar'):
                main_window.status_bar.showPermanentMessage(f"Selected character: {character_data['name']}")
    
    def on_selection_changed(self, selected_ids: List[int]) -> None:
        """Handle multiple character selection.
        
        Args:
            selected_ids: List of IDs of the selected characters
        """
        self.currently_selected_character_ids = selected_ids
        
        # Get character data for all selected characters
        selected_data = []
        for char_id in selected_ids:
            if char_id in self.scene.character_cards:
                selected_data.append(self.scene.character_cards[char_id].character_data)
        
        # Emit the selection changed signal with list of character data
        self.selection_changed.emit(selected_data)
        
        # Display a status message
        main_window = self.window()
        if hasattr(main_window, 'status_bar'):
            if len(selected_ids) > 1:
                main_window.status_bar.showPermanentMessage(f"Selected {len(selected_ids)} characters")
            elif len(selected_ids) == 0:
                main_window.status_bar.showPermanentMessage("No characters selected")
    
    def get_selected_characters(self) -> List[Dict[str, Any]]:
        """Get data for all selected characters.
        
        Returns:
            List of character data dictionaries
        """
        return self.scene.get_selected_characters()
    
    def select_characters_by_ids(self, character_ids: List[int]) -> None:
        """Select characters by their IDs.
        
        Args:
            character_ids: List of character IDs to select
        """
        self.scene.select_characters_by_ids(character_ids)
    
    def refresh_board(self) -> None:
        """Refresh the story board to show updated data.
        
        This method reloads the current view to reflect any database changes,
        particularly useful when relationships are added or modified elsewhere.
        """
        if self.current_view_id:
            self.load_view(self.current_view_id)
            # Show a brief status message
            main_window = self.window()
            if hasattr(main_window, 'status_bar'):
                main_window.status_bar.showPermanentMessage("Story Board refreshed") 