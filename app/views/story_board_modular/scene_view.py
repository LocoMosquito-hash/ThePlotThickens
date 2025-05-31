#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scene and view components for the story board.

This module contains the StoryBoardScene and StoryBoardView classes.
"""

import json
from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QGraphicsScene, QGraphicsView, QGraphicsSceneMouseEvent, QGraphicsSceneContextMenuEvent,
    QGraphicsTextItem, QGraphicsRectItem, QMenu, QDialog
)
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal, QTimer
from PyQt6.QtGui import (
    QColor, QPen, QBrush, QFont, QPainter, QTransform, QWheelEvent
)

from app.db_sqlite import (
    get_story_characters, get_character
)

from .graphics_components import CharacterCard, RelationshipLine, BendPoint, load_bendpoints
from .utils import CARD_WIDTH, CARD_HEIGHT


class StoryBoardScene(QGraphicsScene):
    """Custom graphics scene for the story board."""
    
    layout_changed = pyqtSignal()  # Signal emitted when layout changes
    character_selected = pyqtSignal(int)  # Signal emitted when a single character is selected
    character_moved = pyqtSignal(int)  # Signal for when a character card position changes
    selection_changed = pyqtSignal(list)  # Signal emitted with list of selected character IDs
    relationship_selected = pyqtSignal(int, int, str)  # Signal for when a relationship is selected
    
    def __init__(self, parent=None, db_conn=None) -> None:
        """Initialize the scene.
        
        Args:
            parent: Parent widget
            db_conn: Database connection
        """
        super().__init__(parent)
        
        # Store database connection
        self.db_conn = db_conn
        
        # Track character cards and relationship lines
        self.character_cards: Dict[int, CharacterCard] = {}
        self.relationship_lines: Dict[int, RelationshipLine] = {}
        
        # Track shadow rectangles to clean up on scene clear
        self.shadow_rects: List[QGraphicsRectItem] = []
        
        # Track selected characters
        self.selected_character_ids: List[int] = []
        
        # Selection mode flags
        self._in_multi_selection = False
        
        # Relationship addition state
        self.relationship_mode = False
        self.relationship_source_card = None
        
        # Grid snapping settings
        self.grid_snap_enabled = False
        self.grid_size = 50
        self.grid_visible = False
        
        # Set scene size
        self.setSceneRect(0, 0, 10000, 10000)
        
        # Enable key events for the scene
        self.setFocusOnTouch(True)
        
        # Connect signals
        self.selectionChanged.connect(self.on_qt_selection_changed)
        
        # Connect to scene changes to preserve relationship styling
        self.changed.connect(self.on_scene_changed)
        
        # Selection indicator
        self.selection_indicator = QGraphicsTextItem()
        self.selection_indicator.setPos(20, 20)
        self.selection_indicator.setDefaultTextColor(QColor(255, 255, 255))
        self.selection_indicator.setZValue(100)  # Make sure it's always on top
        self.selection_indicator.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        # Add background for selection indicator
        self.selection_indicator_bg = QGraphicsRectItem()
        self.selection_indicator_bg.setBrush(QBrush(QColor(42, 42, 42, 200)))
        self.selection_indicator_bg.setPen(QPen(Qt.PenStyle.NoPen))
        self.selection_indicator_bg.setZValue(99)  # Just below the text
        
        # Add items to scene
        self.addItem(self.selection_indicator_bg)
        self.addItem(self.selection_indicator)
        
        # Initial state - hidden
        self.selection_indicator.setVisible(False)
        self.selection_indicator_bg.setVisible(False)
    
    def draw_grid(self):
        """Draw grid lines on the scene."""
        # Set up the pen for grid lines
        grid_pen = QPen(QColor(200, 200, 200, 100), 1, Qt.PenStyle.DotLine)
        self.addItem(grid_pen)
        
        # Calculate grid boundaries
        left = int(self.sceneRect().left())
        top = int(self.sceneRect().top())
        right = int(self.sceneRect().right())
        bottom = int(self.sceneRect().bottom())
        
        # Draw vertical grid lines
        for x in range(left, right + 1, 50):
            self.addLine(x, top, x, bottom, grid_pen)
        
        # Draw horizontal grid lines
        for y in range(top, bottom + 1, 50):
            self.addLine(left, y, right, y, grid_pen)
    
    def on_scene_changed(self, changed_items) -> None:
        """Handle scene changes to ensure relationship styling is preserved.
        
        Args:
            changed_items: List of changed items
        """
        # Only proceed if we have relationship lines
        if not self.relationship_lines:
            return
            
        # Check if we need to refresh relationship line styling
        need_refresh = False
        for item in changed_items:
            # If any character card moved or any relationship line changed
            if isinstance(item, CharacterCard) or isinstance(item, RelationshipLine):
                need_refresh = True
                break
        
        # If needed, refresh all relationship lines
        if need_refresh:
            self.refresh_relationship_styling()
    
    def refresh_relationship_styling(self) -> None:
        """Refresh the styling of all relationship lines in the scene."""
        for relationship_id, line in self.relationship_lines.items():
            # Ensure the z-ordering and styling are preserved
            # Set the line z-value to stay behind character cards
            if not line.is_hovered:
                line.setZValue(-10)  # Behind character cards when not hovered
            else:
                line.setZValue(-5)   # Still behind character cards but more visible when hovered
            
            # Ensure label z-ordering within the relationship line
            line.label_background.setZValue(-1)
            line.label.setZValue(1)
            
            # If line is not hovered, ensure proper color
            if not line.is_hovered:
                # Apply bright text color
                bright_text_color = QColor(line.normal_color)
                bright_text_color.setRed(min(bright_text_color.red() + 50, 255))
                line.label.setDefaultTextColor(bright_text_color)
                
                # Ensure proper font
                doc = line.label.document()
                doc.setDefaultFont(QFont("Courier New", 21, QFont.Weight.Bold))
                
        # Also update bendpoint visibility
        self._update_bendpoint_visibility()
        
    def _update_bendpoint_visibility(self) -> None:
        """Update the visibility of all bendpoints based on selection state."""
        # Get all selected relationship lines
        selected_lines = [item for item in self.selectedItems() if isinstance(item, RelationshipLine)]
        
        # Get all selected bendpoints
        selected_bendpoints = [item for item in self.selectedItems() if isinstance(item, BendPoint)]
        
        # First hide all bendpoints except selected ones
        for relationship_id, line in self.relationship_lines.items():
            for bendpoint in line.bendpoints:
                # Only hide if not selected and parent line not selected
                if bendpoint not in selected_bendpoints:
                    bendpoint.setVisible(line in selected_lines)
                    
        # Ensure selected bendpoints are always visible
        for bendpoint in selected_bendpoints:
            bendpoint.setVisible(True)
    
    def start_relationship_mode(self, source_card: CharacterCard) -> None:
        """Start relationship addition mode.
        
        Args:
            source_card: The character card that initiated the relationship
        """
        self.relationship_mode = True
        self.relationship_source_card = source_card
        
        # Update status bar
        self.update_status_message("Select another character to add a relationship")
        
        # Visual feedback for the source card
        source_card.setZValue(10)  # Bring to front
        
        # Optionally add a visual indicator (like a glow effect)
        self._add_relationship_mode_visual_feedback(source_card)
    
    def cancel_relationship_mode(self) -> None:
        """Cancel relationship addition mode."""
        if self.relationship_mode and self.relationship_source_card:
            # Remove visual feedback
            self._remove_relationship_mode_visual_feedback(self.relationship_source_card)
            self.relationship_source_card.setZValue(0)  # Reset z-value
        
        self.relationship_mode = False
        self.relationship_source_card = None
        
        # Update status bar
        self.update_status_message("Relationship addition cancelled")
    
    def handle_character_click_in_relationship_mode(self, target_card: CharacterCard) -> None:
        """Handle character click when in relationship mode.
        
        Args:
            target_card: The character card that was clicked
        """
        if not self.relationship_mode or not self.relationship_source_card:
            return
        
        # Prevent self-relationships
        if target_card.character_id == self.relationship_source_card.character_id:
            self.update_status_message("Cannot create relationship with the same character")
            return
        
        # Get character data
        source_id = self.relationship_source_card.character_id
        source_name = self.relationship_source_card.character_data['name']
        target_id = target_card.character_id
        target_name = target_card.character_data['name']
        
        # Clean up relationship mode
        self.cancel_relationship_mode()
        
        # Show the relationship details dialog directly
        self.show_relationship_details_dialog(source_id, source_name, target_id, target_name)
    
    def show_relationship_details_dialog(self, source_id: int, source_name: str, 
                                       target_id: int, target_name: str) -> None:
        """Show the relationship details dialog.
        
        Args:
            source_id: ID of the source character
            source_name: Name of the source character
            target_id: ID of the target character
            target_name: Name of the target character
        """
        from app.views.relationship_details import RelationshipDetailsDialog
        
        # Get the parent widget (StoryBoardWidget)
        parent_widget = self.views()[0].parent() if self.views() else None
        
        # Create and show the dialog
        dialog = RelationshipDetailsDialog(
            self.db_conn,
            source_id,
            source_name,
            target_id,
            target_name,
            parent_widget
        )
        
        # Show the dialog (modal)
        result = dialog.exec()
        
        if result == dialog.DialogCode.Accepted:
            # Get the selected relationship types
            forward_rel, backward_rel = dialog.get_selected_relationships()
            
            # Refresh the story board to show the new relationships
            if parent_widget and hasattr(parent_widget, 'refresh_board'):
                parent_widget.refresh_board()
            
            self.update_status_message(f"Relationship added between {source_name} and {target_name}")
        else:
            self.update_status_message("Relationship addition cancelled")
    
    def update_status_message(self, message: str) -> None:
        """Update the status bar message.
        
        Args:
            message: Message to display
        """
        # Find the main window and update its status bar
        parent = self.parent()
        while parent and not hasattr(parent, 'statusBar'):
            parent = parent.parent()
        
        if parent and hasattr(parent, 'statusBar'):
            parent.statusBar().showMessage(message, 3000)  # Show for 3 seconds
    
    def _add_relationship_mode_visual_feedback(self, card: CharacterCard) -> None:
        """Add visual feedback for relationship mode.
        
        Args:
            card: Character card to add feedback to
        """
        # Add a subtle glow effect or border to indicate the source card
        # For now, we'll just use the existing selection visual feedback
        card.setSelected(True)
    
    def _remove_relationship_mode_visual_feedback(self, card: CharacterCard) -> None:
        """Remove visual feedback for relationship mode.
        
        Args:
            card: Character card to remove feedback from
        """
        # Remove the visual feedback
        card.setSelected(False)
    
    def set_grid_snap(self, enabled: bool) -> None:
        """Enable or disable grid snapping.
        
        Args:
            enabled: Whether grid snapping should be enabled
        """
        self.grid_snap_enabled = enabled
        self.update()
    
    def set_grid_size(self, size: int) -> None:
        """Set the grid size.
        
        Args:
            size: Grid size in pixels
        """
        self.grid_size = size
        self.update()
    
    def set_grid_visible(self, visible: bool) -> None:
        """Set grid visibility.
        
        Args:
            visible: Whether the grid should be visible
        """
        self.grid_visible = visible
        self.update()
    
    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        """Draw the scene background.
        
        Args:
            painter: Painter to use
            rect: Rectangle to draw in
        """
        super().drawBackground(painter, rect)
        
        # Draw grid if visible
        if self.grid_visible:
            # Save the painter state
            painter.save()
            
            # Set up the pen for grid lines
            painter.setPen(QPen(QColor(200, 200, 200, 100), 1, Qt.PenStyle.DotLine))
            
            # Calculate grid boundaries
            left = int(rect.left() - (rect.left() % self.grid_size))
            top = int(rect.top() - (rect.top() % self.grid_size))
            right = int(rect.right())
            bottom = int(rect.bottom())
            
            # Draw vertical grid lines
            for x in range(left, right + 1, self.grid_size):
                painter.drawLine(x, top, x, bottom)
            
            # Draw horizontal grid lines
            for y in range(top, bottom + 1, self.grid_size):
                painter.drawLine(left, y, right, y)
            
            # Restore the painter state
            painter.restore()
            
        # Ensure relationship styling is preserved when the scene is redrawn
        self.refresh_relationship_styling()
    
    def on_qt_selection_changed(self) -> None:
        """Handle selection changes from Qt's internal selection mechanism."""
        # Forward to our custom enforcement method
        self._enforce_selection_visibility()
        
        # Update bendpoint visibility based on which relationship lines are selected
        self._update_bendpoint_visibility()
    
    def get_selected_characters(self) -> List[Dict[str, Any]]:
        """Get data for all selected characters.
        
        Returns:
            List of character data dictionaries
        """
        selected_chars = []
        for char_id in self.selected_character_ids:
            if char_id in self.character_cards:
                card = self.character_cards[char_id]
                selected_chars.append(card.character_data)
        return selected_chars
    
    def select_characters_by_ids(self, character_ids: List[int]) -> None:
        """Select characters by their IDs.
        
        Args:
            character_ids: List of character IDs to select
        """
        # Block signals temporarily to avoid multiple updates
        self.blockSignals(True)
        
        try:
            # Clear current selection first
            self.clearSelection()
            
            # Select each character by ID
            for char_id in character_ids:
                if char_id in self.character_cards:
                    self.character_cards[char_id].setSelected(True)
        finally:
            # Restore signals
            self.blockSignals(False)
            
        # Force update of selection visuals
        self._enforce_selection_visibility()
    
    def _enforce_selection_visibility(self) -> None:
        """Enforce visibility of folded corners and shadows for all selected cards."""
        # Get all selected character cards
        selected_cards = [item for item in self.selectedItems() if isinstance(item, CharacterCard)]
        selected_ids = [card.character_id for card in selected_cards]
        
        # Update selection storage, but preserve multi-selection in progress
        if hasattr(self, '_in_multi_selection') and self._in_multi_selection:
            # If we're in multi-selection mode, merge with existing selection instead of replacing
            if not selected_ids:
                # If nothing is selected now, keep the old selection 
                # (this helps when selection events might be firing in the wrong order)
                pass
            else:
                # Update with new selection (could be adding or removing)
                self.selected_character_ids = selected_ids
        else:
            # Normal case - not in multi-selection mode
            self.selected_character_ids = selected_ids
        
        # Debug output
        print(f"Selection updated: {len(selected_ids)} cards selected: {selected_ids}")
        
        # Process both selected and unselected cards
        for card in self.character_cards.values():
            is_selected = card.isSelected()
            
            # Debug individual card selection state
            if is_selected:
                print(f"Card {card.character_id} is SELECTED")
            
            # Ensure folded corner visibility matches selection state
            if hasattr(card, 'folded_corner'):
                card.folded_corner.setVisible(is_selected)
                if is_selected:
                    card.folded_corner.setZValue(15)  # High z-value to ensure visibility
            
            # Handle shadow visibility and z-value based on selection
            if is_selected:
                # Create shadow if needed
                shadow_offset = 4
                if card.shadow_rect is None and card.scene():
                    card_width = CARD_WIDTH
                    card_height = CARD_HEIGHT
                    
                    # Create shadow rectangle
                    shadow_rect = QGraphicsRectItem(
                        shadow_offset, 
                        shadow_offset, 
                        card_width, 
                        card_height, 
                        parent=card
                    )
                    shadow_rect.setBrush(QBrush(QColor(0, 0, 0, 100)))
                    shadow_rect.setPen(QPen(Qt.PenStyle.NoPen))
                    shadow_rect.setZValue(-2)  # Behind the card
                    card.shadow_rect = shadow_rect
                    
                    # Also add to scene tracking
                    self.shadow_rects.append(shadow_rect)
                
                # Make sure shadow is visible
                if card.shadow_rect:
                    card.shadow_rect.setVisible(True)
                    card.shadow_rect.setZValue(-2)
            else:
                # Hide shadow for unselected cards
                if card.shadow_rect:
                    card.shadow_rect.setVisible(False)
        
        # Emit signal for further processing if needed
        if selected_ids != getattr(self, '_last_selection', []):
            self.selection_changed.emit(selected_ids)
            self._last_selection = selected_ids[:]
            
        # Update the selection indicator
        self.update_selection_indicator()
    
    def on_character_position_changed(self, character_id: int) -> None:
        """Handle character position change.
        
        Args:
            character_id: ID of the character that moved
        """
        # Refresh relationship styling
        self.refresh_relationship_styling()
        
        # Emit layout changed signal
        self.layout_changed.emit()
    
    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent) -> None:
        """Handle context menu events.
        
        Args:
            event: Context menu event
        """
        # Get the clicked position in scene coordinates
        scene_pos = event.scenePos()
        
        # Check if we clicked on an item
        clicked_item = self.itemAt(scene_pos, QTransform())
        if clicked_item:
            # Let the item handle its own context menu
            super().contextMenuEvent(event)
            return
            
        # Create menu for empty space click
        menu = QMenu()
        add_character_action = menu.addAction("Add Character Here")
        
        # Show menu and handle actions
        action = menu.exec(event.screenPos())
        
        if action == add_character_action:
            # Import here to avoid circular imports
            from app.views.character_dialog import CharacterDialog
            
            # Get the parent widget (StoryBoardWidget)
            parent_widget = self.views()[0].parent() if self.views() else None
            if not parent_widget or not hasattr(parent_widget, 'current_story_id'):
                return
            
            # Get current character count in database
            current_characters = get_story_characters(self.db_conn, parent_widget.current_story_id)
            print(f"ADD CHAR: Before adding - {len(current_characters)} characters in database for story {parent_widget.current_story_id}")
            
            # Log card count before adding character
            print(f"ADD CHAR: Before adding - {len(self.character_cards)} cards in scene")
                
            # Create and show the character dialog
            dialog = CharacterDialog(self.db_conn, parent_widget.current_story_id, parent=parent_widget)
            if dialog.exec():
                # Get the character ID from the dialog
                character_id = dialog.character_id
                print(f"DEBUG: Got character ID {character_id} from dialog")
                
                # Check character count in database after adding
                new_characters = get_story_characters(self.db_conn, parent_widget.current_story_id)
                print(f"ADD CHAR: After adding - {len(new_characters)} characters in database for story {parent_widget.current_story_id}")
                
                # Add the character to the current view's layout
                if parent_widget.current_view_id and character_id:
                    # Get the current layout
                    from app.db_sqlite import get_story_board_view, update_story_board_view_layout
                    view = get_story_board_view(self.db_conn, parent_widget.current_view_id)
                    layout = json.loads(view['layout_data']) if view['layout_data'] else {}
                    
                    # Initialize characters dictionary if it doesn't exist
                    if 'characters' not in layout:
                        layout['characters'] = {}
                    
                    # Add the character to the layout at the clicked position
                    layout['characters'][str(character_id)] = {
                        'x': scene_pos.x(),
                        'y': scene_pos.y()
                    }
                    
                    # Update the layout
                    update_story_board_view_layout(
                        self.db_conn,
                        parent_widget.current_view_id,
                        json.dumps(layout)
                    )
                    
                    # Get the complete character data from the database
                    complete_character_data = get_character(self.db_conn, character_id)
                    
                    # Add the character card directly to the scene at the clicked position
                    self.add_character_card(character_id, complete_character_data, scene_pos.x(), scene_pos.y())
                    
                    # Save the view without triggering a reload
                    parent_widget.save_current_view()
                    
                    # Log card count after adding character
                    print(f"ADD CHAR: After adding - {len(self.character_cards)} cards in scene")
    
    def update_selection_indicator(self) -> None:
        """Update the selection indicator with current selection information.
        
        This now updates the status bar in the main window instead of using scene graphics.
        """
        try:
            # Create selection text
            if not self.selected_character_ids:
                # No selection
                status_text = "No characters selected"
            else:
                num_selected = len(self.selected_character_ids)
                if num_selected == 1:
                    card = self.character_cards.get(self.selected_character_ids[0])
                    if card:
                        status_text = f"Selected: {card.character_data['name']}"
                    else:
                        status_text = "Selected: 1 character"
                else:
                    # Multiple characters selected
                    names = []
                    for char_id in self.selected_character_ids:
                        card = self.character_cards.get(char_id)
                        if card:
                            names.append(card.character_data['name'])
                    
                    status_text = f"Selected: {num_selected} characters - " + ", ".join(names)
            
            # Find the main window and update its status bar
            parent = self.parent()
            while parent and not hasattr(parent, 'statusBar'):
                parent = parent.parent()
            
            if parent and hasattr(parent, 'statusBar'):
                parent.statusBar().showMessage(status_text)
            
        except Exception as e:
            print(f"Error updating selection indicator: {str(e)}")
    
    def add_character_card(self, character_id: int, character_data: Dict[str, Any], x: float = 0, y: float = 0) -> CharacterCard:
        """Add a character card to the scene.
        
        Args:
            character_id: ID of the character
            character_data: Character data
            x: X coordinate
            y: Y coordinate
            
        Returns:
            The created character card
        """
        print(f"ADD CARD: Adding character {character_id} at position ({x}, {y})")
        
        # Check if card already exists
        if character_id in self.character_cards:
            print(f"ADD CARD: WARNING - Character {character_id} already exists in scene!")
        
        card = CharacterCard(character_id, character_data, x, y)
        self.addItem(card)
        self.character_cards[character_id] = card
        
        # Connect to position changed signal
        card.position_changed.connect(self.on_character_position_changed)
        
        # print(f"ADD CARD: Character {character_id} added successfully. Total cards: {len(self.character_cards)}")
        
        return card
    
    def add_relationship_line(self, relationship_id: int, relationship_data: Dict[str, Any],
                            source_id: int, target_id: int) -> Optional[RelationshipLine]:
        """Add a relationship line to the scene, grouping multiple relationships between the same characters.
        
        Args:
            relationship_id: ID of the relationship
            relationship_data: Relationship data
            source_id: ID of the source character
            target_id: ID of the target character
            
        Returns:
            The created or updated relationship line, or None if the characters don't exist
        """
        if source_id not in self.character_cards or target_id not in self.character_cards:
            return None
        
        # Create a key for this character pair (normalize order to ensure consistency)
        pair_key = f"{min(source_id, target_id)}_{max(source_id, target_id)}"
        
        # Add the relationship_id to the data for tracking
        relationship_data['id'] = relationship_id
        
        # Check if we already have a line for this character pair
        existing_line = None
        for line_id, line in self.relationship_lines.items():
            if isinstance(line, RelationshipLine):
                line_source_id = line.source_card.character_id
                line_target_id = line.target_card.character_id
                line_pair_key = f"{min(line_source_id, line_target_id)}_{max(line_source_id, line_target_id)}"
                
                if line_pair_key == pair_key:
                    print(f"Found existing relationship line between characters {source_id} and {target_id}")
                    print(f"Existing line has {len(line.relationships)} relationships")
                    existing_line = line
                    break
        
        if existing_line:
            print(f"ADD RELATIONSHIP: Adding relationship {relationship_id} to existing line with {len(existing_line.relationships)} relationships")
            
            # Add this relationship to the existing line
            existing_line.relationships.append(relationship_data)
            
            # Update the label using smart labeling
            from app.relationships import create_smart_relationship_label
            
            try:
                label_text = create_smart_relationship_label(existing_line.relationships, self.db_conn)
            except Exception as e:
                print(f"Error creating smart label, falling back to simple concatenation: {e}")
                # Fallback to the original concatenation method
                relationship_types = [rel['relationship_type'] for rel in existing_line.relationships]
                label_text = " / ".join(relationship_types)
            
            # Update the label
            doc = existing_line.label.document()
            escaped_text = label_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            html_text = f'<span style="letter-spacing: 0.5px;">{escaped_text}</span>'
            doc.setHtml(html_text)
            
            # Load any bendpoints for this relationship
            print(f"ADD RELATIONSHIP: Checking for bendpoints on relationship {relationship_id}")
            bendpoints_before = len(existing_line.bendpoints)
            
            # Load any bendpoints for this relationship ID and add them to the existing line
            new_bendpoints = load_bendpoints(existing_line, relationship_id)
            
            # Add new bendpoints to the scene and line
            for bendpoint in new_bendpoints:
                self.addItem(bendpoint)
                existing_line.bendpoints.append(bendpoint)
            
            bendpoints_after = len(existing_line.bendpoints)
            if bendpoints_after > bendpoints_before:
                print(f"ADD RELATIONSHIP: Added {bendpoints_after - bendpoints_before} bendpoints from relationship {relationship_id}")
            
            # Update position to recalculate label background and path
            existing_line.update_position()
            
            # Store this relationship_id mapping to the existing line
            self.relationship_lines[relationship_id] = existing_line
            
            return existing_line
        else:
            # Create a new line with this single relationship
            source_card = self.character_cards[source_id]
            target_card = self.character_cards[target_id]
            
            # Create smart label for the new line
            from app.relationships import create_smart_relationship_label
            
            try:
                smart_label = create_smart_relationship_label([relationship_data], self.db_conn)
            except Exception as e:
                print(f"Error creating smart label for new line, falling back to simple label: {e}")
                smart_label = relationship_data['relationship_type']
            
            line = RelationshipLine([relationship_data], source_card, target_card, smart_label)
            self.addItem(line)
            
            # Store the line with this relationship_id
            self.relationship_lines[relationship_id] = line
            return line
    
    def clear_board(self) -> None:
        """Clear all items from the scene."""
        # Make sure to remove any shadow rectangles
        for card in self.character_cards.values():
            if hasattr(card, 'shadow_rect') and card.shadow_rect is not None:
                self.removeItem(card.shadow_rect)
        
        self.character_cards.clear()
        self.relationship_lines.clear()
        self.clear()
    
    def get_layout_data(self) -> Dict[str, Any]:
        """Get the layout data for saving.
        
        Returns:
            Layout data as a dictionary
        """
        layout = {"characters": {}}
        
        # Add character positions
        for character_id, card in self.character_cards.items():
            pos = card.pos()
            layout["characters"][str(character_id)] = {"x": pos.x(), "y": pos.y()}
        
        return layout
    
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Handle mouse press events.
        
        Args:
            event: Mouse press event
        """
        # Get the clicked position
        pos = event.scenePos()
        
        # Check if we clicked on an item
        clicked_item = self.itemAt(pos, QTransform())
        
        # Handle relationship mode first
        if self.relationship_mode:
            # Check if we clicked on a character card
            if clicked_item and (isinstance(clicked_item, CharacterCard) or 
                          (clicked_item.parentItem() and isinstance(clicked_item.parentItem(), CharacterCard))):
                # Get the card itself
                card = clicked_item if isinstance(clicked_item, CharacterCard) else clicked_item.parentItem()
                
                # Verify click is within bounds
                local_pos = card.mapFromScene(pos)
                if QRectF(0, 0, CARD_WIDTH, CARD_HEIGHT).contains(local_pos):
                    # Handle the character click in relationship mode
                    self.handle_character_click_in_relationship_mode(card)
                    event.accept()
                    return
            else:
                # Clicked on empty space or other item - cancel relationship mode
                self.cancel_relationship_mode()
                # Continue with normal processing
        
        # Special handling for Ctrl+Click multi-selection
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Set a flag to indicate we're in multi-selection mode
            self._in_multi_selection = True
            
            # Only handle character cards or their children
            if clicked_item and (isinstance(clicked_item, CharacterCard) or 
                          (clicked_item.parentItem() and isinstance(clicked_item.parentItem(), CharacterCard))):
                # Get the card itself
                card = clicked_item if isinstance(clicked_item, CharacterCard) else clicked_item.parentItem()
                
                # Verify click is within bounds
                local_pos = card.mapFromScene(pos)
                if QRectF(0, 0, CARD_WIDTH, CARD_HEIGHT).contains(local_pos):
                    # Toggle the selection state of this card only
                    was_selected = card.isSelected()
                    
                    # Store current selection to preserve it
                    current_selection = self.selectedItems()
                    selected_cards = [item for item in current_selection if isinstance(item, CharacterCard)]
                    
                    # Add or remove this card from selection
                    if was_selected:
                        card.setSelected(False)
                    else:
                        card.setSelected(True)
                        
                    # Make sure we're not clearing other selections
                    for selected_card in selected_cards:
                        if selected_card != card:
                            selected_card.setSelected(True)
                    
                    # Immediately update selection visuals
                    self._enforce_selection_visibility()
                    
                    # Protect selection from being changed by events
                    QTimer.singleShot(50, self._finish_multi_selection)
                    
                    # Consume event to prevent Qt's default behavior
                    event.accept()
                    return
        
        # For all other clicks, use standard Qt behavior
        super().mousePressEvent(event)
        
        # Ensure selection visuals are updated
        QTimer.singleShot(0, self._enforce_selection_visibility)
    
    def keyPressEvent(self, event) -> None:
        """Handle key press events.
        
        Args:
            event: Key press event
        """
        # Handle ESC key to cancel relationship mode
        if event.key() == Qt.Key.Key_Escape and self.relationship_mode:
            self.cancel_relationship_mode()
            event.accept()
            return
        
        # For all other keys, use standard behavior
        super().keyPressEvent(event)
    
    def _finish_multi_selection(self) -> None:
        """Finish multi-selection mode and clean up."""
        # Clear the multi-selection flag
        self._in_multi_selection = False
        
        # Update selection visuals once more
        self._enforce_selection_visibility()
    
    def on_character_selected(self, character_id: int) -> None:
        """Handle single character selection.
        
        Args:
            character_id: ID of the selected character
        """
        # Ensure the character ID is in the selected list
        if character_id not in self.selected_character_ids:
            self.selected_character_ids = [character_id]
        
        # Get character data
        character_data = None
        if character_id in self.character_cards:
            character_data = self.character_cards[character_id].character_data
        
        # Emit the character selected signal with ID and data
        if character_data:
            self.character_selected.emit(character_id)
            
            # Display a status message
            main_window = self.window()
            if hasattr(main_window, 'status_bar'):
                main_window.status_bar.showPermanentMessage(f"Selected character: {character_data['name']}")
    
    def on_selection_changed(self, selected_ids: List[int]) -> None:
        """Handle multiple character selection.
        
        Args:
            selected_ids: List of IDs of the selected characters
        """
        self.selected_character_ids = selected_ids
        
        # Get character data for all selected characters
        selected_data = []
        for char_id in selected_ids:
            if char_id in self.character_cards:
                selected_data.append(self.character_cards[char_id].character_data)
        
        # Emit the selection changed signal with list of character data
        self.selection_changed.emit(selected_data)
        
        # Display a status message
        main_window = self.window()
        if hasattr(main_window, 'status_bar'):
            if len(selected_ids) > 1:
                main_window.status_bar.showPermanentMessage(f"Selected {len(selected_ids)} characters")
            elif len(selected_ids) == 0:
                main_window.status_bar.showPermanentMessage("No characters selected")


class StoryBoardView(QGraphicsView):
    """Custom graphics view for the story board."""
    
    def __init__(self, parent=None) -> None:
        """Initialize the story board view.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Set view properties
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # Set zoom properties
        self.current_zoom = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 4.0
        self.zoom_factor = 1.25
        
        # Enable focus for key events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Set scene rect to be large enough to accommodate all character positions
        self.setSceneRect(0, 0, 10000, 10000)
    
    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handle wheel events for zooming.
        
        Args:
            event: Wheel event
        """
        # Get the wheel delta
        delta = event.angleDelta().y()
        
        # Determine zoom direction
        if delta > 0:
            # Zoom in
            self.current_zoom *= self.zoom_factor
            if self.current_zoom > self.max_zoom:
                self.current_zoom = self.max_zoom
        else:
            # Zoom out
            self.current_zoom /= self.zoom_factor
            if self.current_zoom < self.min_zoom:
                self.current_zoom = self.min_zoom
        
        # Apply zoom
        self.setTransform(QTransform().scale(self.current_zoom, self.current_zoom))
    
    def center_on_characters(self) -> None:
        """Center the view on the characters in the scene."""
        print("DEBUG: Starting center_on_characters")
        
        # Get the scene object
        scene_obj = self.scene()
        
        # Check if we have a scene and character cards
        if not scene_obj:
            print("DEBUG: No scene object")
            return
            
        # If no characters, return
        if not hasattr(scene_obj, 'character_cards') or not scene_obj.character_cards:
            print("DEBUG: No character cards in scene")
            return
            
        print(f"DEBUG: Found {len(scene_obj.character_cards)} character cards")
        
        # Find the min and max coordinates of all cards
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        card_width = CARD_WIDTH  # Approximate width of a card
        card_height = CARD_HEIGHT  # Approximate height of a card
        
        # First pass: get the bounding box
        for character_id, card in scene_obj.character_cards.items():
            pos = card.pos()
            print(f"DEBUG: Character {character_id} position: ({pos.x()}, {pos.y()})")
            
            # Update min/max coordinates
            min_x = min(min_x, pos.x())
            min_y = min(min_y, pos.y())
            max_x = max(max_x, pos.x() + card_width)
            max_y = max(max_y, pos.y() + card_height)
        
        print(f"DEBUG: Bounding box: ({min_x}, {min_y}) to ({max_x}, {max_y})")
        
        # Create a rectangle that encompasses all cards
        scene_rect = QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
        print(f"DEBUG: Scene rect before padding: {scene_rect}")
        
        if not scene_rect.isEmpty():
            # Add padding (20% of the width/height)
            padding_x = scene_rect.width() * 0.2
            padding_y = scene_rect.height() * 0.2
            scene_rect.adjust(-padding_x, -padding_y, padding_x, padding_y)
            print(f"DEBUG: Scene rect after padding: {scene_rect}")
            
            # Calculate the center point
            center_x = scene_rect.center().x()
            center_y = scene_rect.center().y()
            
            # Reset the view transform
            self.setTransform(QTransform())
            
            # Center on the calculated point
            self.centerOn(center_x, center_y)
            
            # Calculate the scale to fit the view while maintaining a minimum scale
            view_rect = self.viewport().rect()
            scale_x = view_rect.width() / scene_rect.width()
            scale_y = view_rect.height() / scene_rect.height()
            scale = min(scale_x, scale_y)
            
            # Don't let the scale get too small
            min_scale = 0.5
            if scale < min_scale:
                scale = min_scale
            
            # Apply the scale transformation
            self.scale(scale, scale)
            
            print(f"DEBUG: Applied scale: {scale}")
            transform = self.transform()
            print(f"DEBUG: Final transform: m11={transform.m11()}, m12={transform.m12()}, m21={transform.m21()}, m22={transform.m22()}, dx={transform.dx()}, dy={transform.dy()}") 