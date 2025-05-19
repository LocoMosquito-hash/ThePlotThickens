#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Story Board widget for The Plot Thickens application.

This module defines the widget for the story board visualization.
"""

import os
import sys
import json
import math
from typing import Optional, List, Dict, Any, Tuple

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QPushButton, QLabel,
    QComboBox, QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsPixmapItem,
    QGraphicsLineItem, QGraphicsTextItem, QGraphicsRectItem, QMenu, QInputDialog,
    QColorDialog, QMessageBox, QGraphicsSceneMouseEvent, QGraphicsSceneContextMenuEvent,
    QGraphicsSceneHoverEvent, QGraphicsSceneDragDropEvent, QGraphicsSceneWheelEvent,
    QGraphicsItemGroup, QToolBar, QSizePolicy, QGraphicsEllipseItem, QFrame,
    QDialog, QDialogButtonBox, QStyleOptionGraphicsItem, QCheckBox, QLineEdit,
    QGraphicsPathItem
)
from PyQt6.QtCore import Qt, QSize, QPointF, QRectF, QLineF, pyqtSignal, QTimer, QObject, QSettings
from PyQt6.QtGui import (
    QPixmap, QImage, QColor, QPen, QBrush, QFont, QPainter, QPainterPath,
    QTransform, QCursor, QDrag, QMouseEvent, QWheelEvent, QKeyEvent,
    QTextDocument, QTextOption
)

from app.db_sqlite import (
    get_story, get_story_characters, get_character_relationships,
    get_story_board_views, get_story_board_view, create_story_board_view,
    update_story_board_view_layout, get_relationship_types, create_relationship,
    get_story_relationships, get_used_relationship_types, delete_character,
    get_character
)


def create_vertical_line() -> QFrame:
    """Create a vertical line for use as a separator.
    
    Returns:
        A vertical line widget
    """
    line = QFrame()
    line.setFrameShape(QFrame.Shape.VLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    line.setFixedWidth(2)
    line.setFixedHeight(24)
    return line


# Create a custom class that combines QObject and QGraphicsItemGroup
class CharacterCardSignals(QObject):
    """Signals for the CharacterCard class."""
    position_changed = pyqtSignal(int)  # Signal emitted when position changes, with character ID


class CharacterCard(QGraphicsItemGroup):
    """A graphical item representing a character on the story board."""
    
    def __init__(self, character_id: int, character_data: Dict[str, Any], x: float = 0, y: float = 0) -> None:
        """Initialize the character card.
        
        Args:
            character_id: ID of the character
            character_data: Character data
            x: X coordinate
            y: Y coordinate
        """
        super().__init__()
        
        # Set clip behavior to ensure nothing draws outside card boundaries
        self.setFlags(self.flags() | QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape)
        
        # Create signals object
        self.signals = CharacterCardSignals()
        self.position_changed = self.signals.position_changed
        
        self._character_id = character_id  # Store as private attribute
        self.character_data = character_data
        
        # Set flags before setting position
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        
        # Flags for controlling position updates
        self.is_moving = False
        self.suppress_position_updates = False
        
        # Create card components
        self.create_card()
        
        # Track connected relationships
        self.relationships: List[RelationshipLine] = []
        
        # Create folded corner indicator for selection (initially hidden)
        self.folded_corner = self.create_folded_corner()
        self.folded_corner.setVisible(False)
        self.addToGroup(self.folded_corner)
        
        # Set position after everything else is set up
        self.setPos(x, y)
        
        # Keep track of selection shadow as a separate item outside the group
        self.shadow_rect = None
    
    def __del__(self) -> None:
        """Clean up when the object is deleted."""
        try:
            # Remove shadow from scene if it exists
            if hasattr(self, 'shadow_rect') and self.shadow_rect:
                scene = self.scene()
                if scene:
                    scene.removeItem(self.shadow_rect)
                self.shadow_rect = None
        except RuntimeError:
            # Ignore errors during application shutdown when C++ objects are already deleted
            pass
    
    def contains(self, point: QPointF) -> bool:
        """Override contains to only accept clicks on the actual card area.
        
        Args:
            point: The point to test
            
        Returns:
            True if the point is within the card's visual area
        """
        # Only accept points within the card's rectangular area
        card_rect = QRectF(0, 0, 180, 240)
        return card_rect.contains(point)
    
    def shape(self) -> QPainterPath:
        """Override shape to provide a more accurate hit testing area.
        
        Returns:
            A QPainterPath representing the shape for hit testing
        """
        # Create a path that matches the card's rectangular shape
        path = QPainterPath()
        path.addRect(0, 0, 180, 240)
        return path
    
    def create_folded_corner(self) -> QGraphicsItemGroup:
        """Create a folded corner indicator for selection.
        
        Returns:
            A QGraphicsItemGroup representing a folded corner
        """
        # Card dimensions
        card_width = 180
        card_height = 240
        
        # Size of the folded corner - INCREASE SIZE for better visibility
        fold_size = 40  # Increased from 30
        
        # Create a path for the folded corner (top-right of the card)
        path = QPainterPath()
        path.moveTo(card_width - fold_size, 0)  # Start at top right minus fold size
        path.lineTo(card_width, 0)              # Line to top right corner
        path.lineTo(card_width, fold_size)      # Line down fold size
        path.lineTo(card_width - fold_size, 0)  # Line back to start to close the triangle
        
        # Create shadow effect path for depth
        shadow_path = QPainterPath()
        shadow_path.moveTo(card_width - fold_size, 0)
        shadow_path.lineTo(card_width - fold_size, fold_size)
        shadow_path.lineTo(card_width, fold_size)
        shadow_path.lineTo(card_width - fold_size, 0)
        
        # Create a group for both paths
        corner_group = QGraphicsItemGroup()
        
        # Create shadow path item with darker color
        shadow_item = QGraphicsPathItem(shadow_path)
        shadow_item.setBrush(QBrush(QColor("#555555")))  # Darker shadow
        shadow_item.setPen(QPen(QColor("#555555"), 1.5))  # Thicker pen
        shadow_item.setZValue(3.0)  # Ensure it's above other card elements
        corner_group.addToGroup(shadow_item)
        
        # Create fold path item with brighter, more noticeable colors
        fold_item = QGraphicsPathItem(path)
        fold_item.setBrush(QBrush(QColor("#ffcc00")))  # Bright yellow/gold for visibility
        fold_item.setPen(QPen(QColor("#e60000"), 1.5))  # Red outline
        fold_item.setZValue(3.1)  # Above shadow
        corner_group.addToGroup(fold_item)
        
        # Set the entire group to a high z-value to ensure visibility
        corner_group.setZValue(10)
        
        return corner_group
    
    @property
    def character_id(self) -> int:
        """Get the character ID.
        
        Returns:
            The character ID
        """
        return self._character_id
    
    def create_card(self) -> None:
        """Create the card components."""
        # Card dimensions
        card_width = 180
        card_height = 240
        
        # Create card background
        card_rect = QGraphicsRectItem(0, 0, card_width, card_height)
        card_rect.setBrush(QBrush(QColor("#ffffff")))
        card_rect.setPen(QPen(QColor("#000000"), 1))
        card_rect.setZValue(1.0)
        self.addToGroup(card_rect)
        
        # Create photo area
        photo_margin = 15
        photo_width = card_width - (photo_margin * 2)
        photo_height = card_height - (photo_margin * 2) - 40  # Leave space for name at bottom
        photo_rect = QGraphicsRectItem(photo_margin, photo_margin, photo_width, photo_height)
        photo_rect.setBrush(QBrush(QColor("#eeeeee")))
        photo_rect.setPen(QPen(QColor("#cccccc"), 1))
        photo_rect.setZValue(1.5)
        self.addToGroup(photo_rect)
        
        # Add avatar if it exists
        if self.character_data['avatar_path'] and os.path.exists(self.character_data['avatar_path']):
            try:
                pixmap = QPixmap(self.character_data['avatar_path'])
                scaled_pixmap = pixmap.scaled(
                    photo_width,
                    photo_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                # Center the pixmap in the photo area
                pixmap_width = scaled_pixmap.width()
                pixmap_height = scaled_pixmap.height()
                pixmap_x = photo_margin + (photo_width - pixmap_width) / 2
                pixmap_y = photo_margin + (photo_height - pixmap_height) / 2
                
                pixmap_item = QGraphicsPixmapItem(scaled_pixmap)
                pixmap_item.setPos(pixmap_x, pixmap_y)
                pixmap_item.setZValue(1.6)  # Ensure pixmap is above photo area
                self.addToGroup(pixmap_item)
            except Exception as e:
                print(f"Error loading avatar: {e}")
        
        # Add character name
        name_text = QGraphicsTextItem(self.character_data['name'])
        name_text.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        name_text.setDefaultTextColor(QColor("#000000"))
        name_text.setPos(card_width / 2 - name_text.boundingRect().width() / 2, card_height - 35)
        name_text.setZValue(1.7)  # Ensure text is above everything
        self.addToGroup(name_text)
        
        # Add main character indicator if applicable
        if self.character_data.get('is_main_character', False):
            star_size = 15
            star_x = card_width - star_size - 5
            star_y = card_height - star_size - 5
            
            # Create a simple star indicator 
            mc_indicator = QGraphicsEllipseItem(star_x, star_y, star_size, star_size)
            mc_indicator.setBrush(QBrush(QColor("#FFD700")))  # Gold color
            mc_indicator.setPen(QPen(QColor("#DAA520"), 1))  # Darker gold border
            mc_indicator.setZValue(1.8)  # Ensure star is above everything
            self.addToGroup(mc_indicator)
            
            # Add "MC" text
            mc_text = QGraphicsTextItem("MC")
            mc_text.setFont(QFont("Arial", 7, QFont.Weight.Bold))
            mc_text.setDefaultTextColor(QColor("#000000"))
            mc_text.setPos(
                star_x + (star_size - mc_text.boundingRect().width()) / 2,
                star_y + (star_size - mc_text.boundingRect().height()) / 2
            )
            mc_text.setZValue(1.9)  # Ensure text is above star
            self.addToGroup(mc_text)
        
        # Make the group container visible with a border and opacity
        self.setOpacity(0.95)  # Slight transparency to see the group
        
        # Add a visible border around the entire group
        # We need to use a custom paint method for this
        self.setBoundingRectVisible(True)
    
    def setBoundingRectVisible(self, visible: bool) -> None:
        """Set whether the bounding rect is visible.
        
        Args:
            visible: Whether the bounding rect should be visible
        """
        self._show_bounding_rect = visible
        
        # Never actually show any bounding rect
        visible = False
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None) -> None:
        """Paint the item.
        
        Args:
            painter: Painter to use
            option: Style options
            widget: Widget being painted on
        """
        # Set up clipping to ensure nothing draws outside card boundaries
        painter.save()
        painter.setClipRect(QRectF(0, 0, 180, 240))
        
        # Call the parent class paint method
        super().paint(painter, option, widget)
        
        # Restore painter state
        painter.restore()
    
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value) -> Any:
        """Handle item changes.
        
        Args:
            change: Type of change
            value: New value
            
        Returns:
            Modified value
        """
        # Define shadow_offset at the method level so it's available to all code paths
        shadow_offset = 4  # Shadow offset in pixels
        
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            # This provides a hint before selection is actually changed
            # The visual changes will be handled in setSelected
            pass
            
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            # If shadow exists, update its position too
            if self.shadow_rect and self.shadow_rect.isVisible():
                # shadow_offset is now accessible here
                new_pos = value
                self.shadow_rect.setPos(new_pos + QPointF(shadow_offset/2, shadow_offset/2))
            
            # Check if grid snapping is enabled in the scene
            if hasattr(self.scene(), 'grid_snap_enabled') and self.scene().grid_snap_enabled:
                # Get the new position
                new_pos = value
                
                # Get the grid size from the scene
                grid_size = getattr(self.scene(), 'grid_size', 50)
                
                # Snap to grid
                snapped_x = round(new_pos.x() / grid_size) * grid_size
                snapped_y = round(new_pos.y() / grid_size) * grid_size
                
                # Return the snapped position
                value = QPointF(snapped_x, snapped_y)
            
            # Update connected relationship lines
            for relationship in self.relationships:
                relationship.update_position()
            
            # Only set moving flag if not suppressing updates
            if not self.suppress_position_updates:
                self.is_moving = True
        
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged and self.is_moving:
            # Position has changed, emit signal only if not suppressing updates
            if not self.suppress_position_updates:
                self.is_moving = False
                
                # When a character is moved, update all relationship lines in the scene to preserve styling
                scene = self.scene()
                if scene and hasattr(scene, 'relationship_lines'):
                    for relationship_id, relationship_line in scene.relationship_lines.items():
                        # Only update positions of lines not connected to this card (connected ones were already updated)
                        if relationship_line.source_card != self and relationship_line.target_card != self:
                            # Force a styling refresh for all relationship lines
                            relationship_line.update_position()
                
                # Use QTimer to emit the signal after a short delay to avoid excessive updates
                QTimer.singleShot(100, lambda: self.signals.position_changed.emit(self._character_id))
        
        return super().itemChange(change, value)
    
    def get_position_change_source(self) -> str:
        """Get the source of the position change by inspecting the call stack.
        
        Returns:
            A string describing where the position change was triggered from
        """
        import traceback
        stack = traceback.extract_stack()
        # Look for relevant method names in the call stack
        for frame in stack:
            method_name = frame.name
            if method_name in ['on_character_updated', 'create_card', 'load_view', 
                             'reset_character_positions', 'position_cards', 'setPos']:
                return f"Method: {method_name}"
        return "Unknown source"
    
    def add_relationship(self, relationship: 'RelationshipLine') -> None:
        """Add a relationship to this character.
        
        Args:
            relationship: Relationship line
        """
        self.relationships.append(relationship)
    
    def remove_relationship(self, relationship: 'RelationshipLine') -> None:
        """Remove a relationship from this character.
        
        Args:
            relationship: Relationship line
        """
        if relationship in self.relationships:
            self.relationships.remove(relationship)
    
    def delete_character(self) -> None:
        """Delete the character and its relationships."""
        # Get the scene
        scene = self.scene()
        if not scene or not hasattr(scene, 'db_conn'):
            return
            
        # Ask for confirmation
        reply = QMessageBox.question(
            None,
            "Delete Character",
            f"Are you sure you want to delete '{self.character_data['name']}'?\n\nThis will also delete all relationships involving this character.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Import the delete function
        from app.db_sqlite import delete_character
        
        # Delete the character from the database
        if delete_character(scene.db_conn, self._character_id):
            # Remove all relationships involving this character
            relationships_to_remove = self.relationships.copy()  # Create a copy to avoid modifying while iterating
            for relationship in relationships_to_remove:
                # Remove the relationship line from the scene
                scene.removeItem(relationship)
                # Remove from scene's relationship tracking
                if relationship.relationship_id in scene.relationship_lines:
                    del scene.relationship_lines[relationship.relationship_id]
            
            # Remove the character card from the scene
            # First remove the shadow if it exists
            if self.shadow_rect:
                scene.removeItem(self.shadow_rect)
                self.shadow_rect = None
                
            scene.removeItem(self)
            # Remove from scene's character tracking
            if self._character_id in scene.character_cards:
                del scene.character_cards[self._character_id]
            
            # Emit layout changed signal to trigger auto-save
            scene.layout_changed.emit()
            
            # Show success message
            QMessageBox.information(
                None,
                "Success",
                f"Character '{self.character_data['name']}' deleted successfully."
            )
        else:
            # Show error message
            QMessageBox.critical(
                None,
                "Error",
                f"Failed to delete character '{self.character_data['name']}'."
            )
    
    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent) -> None:
        """Handle context menu events.
        
        Args:
            event: Context menu event
        """
        menu = QMenu()
        
        edit_action = menu.addAction("Edit Character")
        delete_action = menu.addAction("Delete Character")
        
        # Add relationship submenu
        relationship_menu = menu.addMenu("Add Relationship")
        
        # Get all characters in the scene
        scene = self.scene()
        if scene:
            for character_id, card in scene.character_cards.items():
                if character_id != self._character_id:
                    target_action = relationship_menu.addAction(f"To: {card.character_data['name']}")
                    target_action.setData(character_id)
        
        action = menu.exec(event.screenPos())
        
        if action == edit_action:
            self.edit_character()
        elif action == delete_action:
            self.delete_character()
        elif action and action.text().startswith("To: "):
            # Get the target character ID
            target_id = action.data()
            target_card = scene.character_cards[target_id]
            target_name = target_card.character_data['name']
            
            # Show relationship type selection dialog
            self.show_relationship_dialog(target_id, target_name)
    
    def edit_character(self) -> None:
        """Open the character edit dialog."""
        from app.views.character_dialog import CharacterDialog
        
        scene = self.scene()
        if not scene or not hasattr(scene, 'db_conn'):
            return
        
        # Get the parent widget (StoryBoardWidget)
        parent_widget = scene.views()[0].parent() if scene.views() else None
        if not parent_widget:
            return
        
        # Create and show the dialog
        dialog = CharacterDialog(
            db_conn=scene.db_conn,
            story_id=parent_widget.current_story_id,  # Use story_id from parent widget
            character_id=self._character_id,
            parent=parent_widget
        )
        
        # Connect the character_updated signal to the parent widget's handler
        dialog.character_updated.connect(parent_widget.on_character_updated)
        
        # Show the dialog
        dialog.exec()
    
    def show_relationship_dialog(self, target_id: int, target_name: str) -> None:
        """Show a dialog to select the relationship type.
        
        Args:
            target_id: ID of the target character
            target_name: Name of the target character
        """
        # Get the scene and database connection
        scene = self.scene()
        if not scene or not hasattr(scene, 'db_conn'):
            return
        
        # Get standard relationship types
        standard_types = get_relationship_types(scene.db_conn)
        
        # Get previously used relationship types
        used_types = get_used_relationship_types(scene.db_conn)
        
        # Create a combined list with used types at the top
        relationship_items = []
        
        # Add used types first (if they exist)
        if used_types:
            relationship_items.extend(used_types)
            relationship_items.append("---")  # Separator
        
        # Add standard types
        relationship_items.extend([rt['name'] for rt in standard_types])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_items = []
        for item in relationship_items:
            if item not in seen and item != "---":
                seen.add(item)
                unique_items.append(item)
            elif item == "---" and unique_items:  # Only add separator if we have items before it
                unique_items.append(item)
        
        # Create a custom dialog with autocomplete
        dialog = QDialog()
        dialog.setWindowTitle(f"Add Relationship to {target_name}")
        
        layout = QVBoxLayout(dialog)
        
        # Add label
        label = QLabel(f"Select relationship type from {self.character_data['name']} to {target_name}:")
        layout.addWidget(label)
        
        # Add combobox with autocomplete
        combo = QComboBox()
        combo.setEditable(True)
        combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)  # Don't add items when typing
        combo.addItems(unique_items)
        combo.setCurrentIndex(-1)  # No selection by default
        
        # Enable autocomplete
        combo.setCompleter(combo.completer())
        combo.completer().setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        
        layout.addWidget(combo)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # Show dialog
        if dialog.exec():
            relationship_type = combo.currentText()
            
            # Skip if empty or separator
            if not relationship_type or relationship_type == "---":
                return
            
            # Find the selected relationship type in standard types
            selected_type = None
            for rt in standard_types:
                if rt['name'] == relationship_type:
                    selected_type = rt
                    break
            
            # If the relationship type doesn't exist in standard types, create a custom one
            if not selected_type:
                selected_type = {
                    'id': -1,  # Temporary ID for custom type
                    'name': relationship_type,
                    'has_inverse': False
                }
            
            # Create the relationship
            self.create_relationship(target_id, selected_type)
    
    def create_relationship(self, target_id: int, relationship_type: Dict[str, Any]) -> None:
        """Create a relationship to another character.
        
        Args:
            target_id: ID of the target character
            relationship_type: Relationship type data
        """
        from app.db_sqlite import create_relationship
        
        # Get the scene and database connection
        scene = self.scene()
        if not scene or not hasattr(scene, 'db_conn'):
            return
        
        # Create the relationship in the database
        relationship_data = {
            'relationship_type': relationship_type['name'],
            'color': "#FF0000",  # Default color
            'width': 4.0  # 4x the original width
        }
        
        relationship_id = create_relationship(
            scene.db_conn,
            self._character_id,
            target_id,
            relationship_type['name']
        )
        
        # Add the relationship line to the scene
        scene.add_relationship_line(
            relationship_id,
            relationship_data,
            self._character_id,
            target_id
        )
        
        # If the relationship type has an inverse, create the inverse relationship
        if relationship_type.get('has_inverse', False):
            # Determine the inverse relationship type
            inverse_name = relationship_type.get('inverse_name')
            
            # If no explicit inverse name, check gender-specific variants
            if not inverse_name:
                target_card = scene.character_cards[target_id]
                target_gender = target_card.character_data.get('gender', 'NOT_SPECIFIED')
                
                if target_gender == 'MALE' and relationship_type.get('male_variant'):
                    inverse_name = relationship_type['male_variant']
                elif target_gender == 'FEMALE' and relationship_type.get('female_variant'):
                    inverse_name = relationship_type['female_variant']
            
            # If still no inverse name, use the same name
            if not inverse_name:
                inverse_name = relationship_type['name']
            
            # Create the inverse relationship
            inverse_data = {
                'relationship_type': inverse_name,
                'color': "#FF0000",  # Default color
                'width': 4.0  # 4x the original width
            }
            
            # Ask user if they want to create the inverse relationship
            reply = QMessageBox.question(
                None,
                "Create Inverse Relationship",
                f"Do you want to create the inverse relationship?\n{target_card.character_data['name']} is {inverse_name} of {self.character_data['name']}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Create the inverse relationship in the database
                inverse_id = create_relationship(
                    scene.db_conn,
                    target_id,
                    self._character_id,
                    inverse_name
                )
                
                # Add the inverse relationship line to the scene
                scene.add_relationship_line(
                    inverse_id,
                    inverse_data,
                    target_id,
                    self._character_id
                )
        
        # Emit layout changed signal
        if hasattr(scene, 'layout_changed'):
            scene.layout_changed.emit()

    def update_card(self) -> None:
        """Update the card components without recreating it."""
        # Find existing components by type
        pixmap_item = None
        photo_rect = None
        name_text = None
        mc_indicator = None
        mc_text = None
        
        # Identify existing components
        for item in self.childItems():
            if isinstance(item, QGraphicsPixmapItem):
                pixmap_item = item
            elif isinstance(item, QGraphicsRectItem):
                # Check if this is the photo area (light gray background)
                if item.brush().color().name() == "#eeeeee":
                    photo_rect = item
            elif isinstance(item, QGraphicsTextItem):
                name_text = item
            elif isinstance(item, QGraphicsEllipseItem) and item.brush().color().name() == "#ffd700":  # Gold color for MC
                mc_indicator = item
                # Find the MC text which is usually added right after the indicator
                for i in range(self.childItems().index(item) + 1, len(self.childItems())):
                    if isinstance(self.childItems()[i], QGraphicsTextItem) and self.childItems()[i].toPlainText() == "MC":
                        mc_text = self.childItems()[i]
                        break
        
        # Card dimensions
        card_width = 180
        card_height = 240
        
        # Photo area dimensions
        photo_margin = 15
        photo_width = card_width - (photo_margin * 2)
        photo_height = card_height - (photo_margin * 2) - 40  # Leave space for name at bottom
        
        # Update avatar if it exists
        if self.character_data['avatar_path'] and os.path.exists(self.character_data['avatar_path']):
            try:
                # Load new pixmap
                pixmap = QPixmap(self.character_data['avatar_path'])
                scaled_pixmap = pixmap.scaled(
                    photo_width,
                    photo_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                # Center the pixmap in the photo area
                pixmap_width = scaled_pixmap.width()
                pixmap_height = scaled_pixmap.height()
                pixmap_x = photo_margin + (photo_width - pixmap_width) / 2
                pixmap_y = photo_margin + (photo_height - pixmap_height) / 2
                
                # If we have an existing pixmap item, update it
                if pixmap_item:
                    # Remove the old pixmap item first
                    self.removeFromGroup(pixmap_item)
                    scene = self.scene()
                    if scene:
                        scene.removeItem(pixmap_item)
                
                # Create a new pixmap item
                pixmap_item = QGraphicsPixmapItem(scaled_pixmap)
                pixmap_item.setPos(pixmap_x, pixmap_y)
                pixmap_item.setZValue(1.6)  # Ensure pixmap is above photo area
                self.addToGroup(pixmap_item)
                
            except Exception as e:
                print(f"Error updating avatar: {e}")
        elif pixmap_item:
            # If there's no avatar path but we have a pixmap item, remove it
            self.removeFromGroup(pixmap_item)
            scene = self.scene()
            if scene:
                scene.removeItem(pixmap_item)
        
        # Update character name
        if name_text:
            name_text.setPlainText(self.character_data['name'])
            # Recenter name
            name_y = card_height - 35
            name_text.setPos(card_width / 2 - name_text.boundingRect().width() / 2, name_y)
        
        # Update main character indicator
        is_main_character = self.character_data.get('is_main_character', False)
        
        if is_main_character and not mc_indicator:
            # Add MC indicator if it doesn't exist
            star_size = 15
            star_x = card_width - star_size - 5
            star_y = card_height - star_size - 5
            
            # Create a simple star indicator 
            mc_indicator = QGraphicsEllipseItem(star_x, star_y, star_size, star_size)
            mc_indicator.setBrush(QBrush(QColor("#FFD700")))  # Gold color
            mc_indicator.setPen(QPen(QColor("#DAA520"), 1))  # Darker gold border
            mc_indicator.setZValue(1.8)  # Ensure star is above everything
            self.addToGroup(mc_indicator)
            
            # Add "MC" text
            mc_text = QGraphicsTextItem("MC")
            mc_text.setFont(QFont("Arial", 7, QFont.Weight.Bold))
            mc_text.setDefaultTextColor(QColor("#000000"))
            mc_text.setPos(
                star_x + (star_size - mc_text.boundingRect().width()) / 2,
                star_y + (star_size - mc_text.boundingRect().height()) / 2
            )
            mc_text.setZValue(1.9)  # Ensure text is above star
            self.addToGroup(mc_text)
        elif not is_main_character and mc_indicator:
            # Remove MC indicator if character is no longer a main character
            self.removeFromGroup(mc_indicator)
            if mc_text:
                self.removeFromGroup(mc_text)
            # Actually remove them from the scene
            scene = self.scene()
            if scene:
                if mc_indicator:
                    scene.removeItem(mc_indicator)
                if mc_text:
                    scene.removeItem(mc_text)

    def boundingRect(self) -> QRectF:
        """Override boundingRect to constrain it to the actual card size.
        
        Returns:
            The bounding rectangle of the card
        """
        # Return a fixed bounding rect for the character card, matching its intended dimensions
        # This prevents the card from having an unnecessarily large interactive area
        return QRectF(0, 0, 180, 240)

    def setSelected(self, selected: bool) -> None:
        """Override setSelected to ensure proper visual feedback.
        
        Args:
            selected: Whether the card should be selected
        """
        # Call the parent implementation
        super().setSelected(selected)
        
        # We'll let the scene's _enforce_selection_visibility method handle all visual indicators
        # This prevents inconsistencies between Qt's selection and our visual indicators
        
        # Force a redraw to reflect selection state changes
        self.update()
        
        # The folded corner and shadow visibility will be managed by StoryBoardScene._enforce_selection_visibility
    
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value) -> Any:
        """Handle item changes.
        
        Args:
            change: Type of change
            value: New value
            
        Returns:
            Modified value
        """
        # Define shadow_offset at the method level so it's available to all code paths
        shadow_offset = 4  # Shadow offset in pixels
        
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            # This provides a hint before selection is actually changed
            # The visual changes will be handled in setSelected
            pass
            
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            # If shadow exists, update its position too
            if self.shadow_rect and self.shadow_rect.isVisible():
                # shadow_offset is now accessible here
                new_pos = value
                self.shadow_rect.setPos(new_pos + QPointF(shadow_offset/2, shadow_offset/2))
            
            # Check if grid snapping is enabled in the scene
            if hasattr(self.scene(), 'grid_snap_enabled') and self.scene().grid_snap_enabled:
                # Get the new position
                new_pos = value
                
                # Get the grid size from the scene
                grid_size = getattr(self.scene(), 'grid_size', 50)
                
                # Snap to grid
                snapped_x = round(new_pos.x() / grid_size) * grid_size
                snapped_y = round(new_pos.y() / grid_size) * grid_size
                
                # Return the snapped position
                value = QPointF(snapped_x, snapped_y)
            
            # Update connected relationship lines
            for relationship in self.relationships:
                relationship.update_position()
            
            # Only set moving flag if not suppressing updates
            if not self.suppress_position_updates:
                self.is_moving = True
        
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged and self.is_moving:
            # Position has changed, emit signal only if not suppressing updates
            if not self.suppress_position_updates:
                self.is_moving = False
                
                # When a character is moved, update all relationship lines in the scene to preserve styling
                scene = self.scene()
                if scene and hasattr(scene, 'relationship_lines'):
                    for relationship_id, relationship_line in scene.relationship_lines.items():
                        # Only update positions of lines not connected to this card (connected ones were already updated)
                        if relationship_line.source_card != self and relationship_line.target_card != self:
                            # Force a styling refresh for all relationship lines
                            relationship_line.update_position()
                
                # Use QTimer to emit the signal after a short delay to avoid excessive updates
                QTimer.singleShot(100, lambda: self.signals.position_changed.emit(self._character_id))
        
        return super().itemChange(change, value)


class RoundedRectItem(QGraphicsPathItem):
    """A graphics item that draws a rounded rectangle."""
    
    def __init__(self, rect: QRectF, radius: float = 4.0, parent=None) -> None:
        """Initialize the rounded rectangle.
        
        Args:
            rect: Rectangle to draw
            radius: Corner radius
            parent: Parent item
        """
        super().__init__(parent)
        
        self._rect = rect
        self._radius = radius
        self._brush = QBrush()
        self._pen = QPen()
        
        self.update_path()
    
    def update_path(self) -> None:
        """Update the path to match the current rectangle and radius."""
        path = QPainterPath()
        path.addRoundedRect(self._rect, self._radius, self._radius)
        self.setPath(path)
    
    def setRect(self, rect: QRectF) -> None:
        """Set the rectangle.
        
        Args:
            rect: New rectangle
        """
        self._rect = rect
        self.update_path()
    
    def rect(self) -> QRectF:
        """Get the rectangle.
        
        Returns:
            Current rectangle
        """
        return self._rect
    
    def setBrush(self, brush: QBrush) -> None:
        """Set the brush.
        
        Args:
            brush: New brush
        """
        self._brush = brush
        self.update()
    
    def setPen(self, pen: QPen) -> None:
        """Set the pen.
        
        Args:
            pen: New pen
        """
        self._pen = pen
        self.update()
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None) -> None:
        """Paint the item.
        
        Args:
            painter: Painter to use
            option: Style options
            widget: Widget being painted on
        """
        painter.setPen(self._pen)
        painter.setBrush(self._brush)
        painter.drawPath(self.path())


class RelationshipLine(QGraphicsLineItem):
    """A graphical item representing a relationship between characters on the story board."""
    
    def __init__(self, relationship_id: int, relationship_data: Dict[str, Any], 
                source_card: CharacterCard, target_card: CharacterCard) -> None:
        """Initialize the relationship line.
        
        Args:
            relationship_id: ID of the relationship
            relationship_data: Relationship data
            source_card: Source character card
            target_card: Target character card
        """
        super().__init__()
        
        self.relationship_id = relationship_id
        self.relationship_data = relationship_data
        self.source_card = source_card
        self.target_card = target_card
        
        # Add this relationship to the character cards
        self.source_card.add_relationship(self)
        self.target_card.add_relationship(self)
        
        # Set line properties
        self.normal_color = QColor(relationship_data['color']) if relationship_data['color'] else QColor("#FF0000")
        self.hover_color = self.normal_color.lighter(130)  # Lighter version for hover
        self.normal_width = float(relationship_data['width']) if relationship_data['width'] else 4.0  # 4x the original width
        self.hover_width = self.normal_width * 1.5  # Thicker on hover (reduced multiplier since lines are already thick)
        
        # Set initial pen
        self.setPen(QPen(self.normal_color, int(self.normal_width), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        
        # Set flags
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        
        # Create label using QGraphicsTextItem with a QTextDocument for letter spacing
        self.label = QGraphicsTextItem(self)  # Make the label a child of the line
        
        # Create and configure a text document to control letter-spacing
        doc = QTextDocument()
        # Increase font size by 50% (from 14 to 21)
        doc.setDefaultFont(QFont("Courier New", 21, QFont.Weight.Bold))
        
        # Apply CSS-like styling to the text document
        # We need to escape the text content for HTML
        escaped_text = relationship_data['relationship_type'].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        html_text = f'<span style="letter-spacing: 0.5px;">{escaped_text}</span>'
        doc.setHtml(html_text)
        
        # Set the document and color - use the same red color as the line but brighter for better visibility
        self.label.setDocument(doc)
        # Use a brighter version of the line color to ensure visibility
        bright_text_color = QColor(self.normal_color)
        bright_text_color.setRed(min(bright_text_color.red() + 50, 255))
        self.label.setDefaultTextColor(bright_text_color)
        
        # Create a background for the label to make it more readable - using RoundedRectItem
        # Using our custom RoundedRectItem instead of QGraphicsRectItem to get rounded corners
        self.label_background = RoundedRectItem(QRectF(), 4.0, self)  # 4.0 is the border radius
        
        # Make the background slightly more transparent to improve text visibility
        self.label_background.setBrush(QBrush(QColor(30, 30, 30, 200)))
        
        # border: 1px solid matching the relationship color
        border_pen = QPen(self.normal_color, 1)
        self.label_background.setPen(border_pen)
        
        # Ensure proper z-ordering - background below, text above
        self.label_background.setZValue(-1)
        self.label.setZValue(1)
        
        # Track hover state
        self.is_hovered = False
        
        # Update position
        self.update_position()
    
    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        """Handle hover enter events.
        
        Args:
            event: Hover enter event
        """
        self.is_hovered = True
        
        # Change line appearance
        pen = self.pen()
        pen.setColor(self.hover_color)
        pen.setWidth(int(self.hover_width))  # Convert to int
        self.setPen(pen)
        
        # Change label appearance - apply hover enhancements
        # Update the document with larger font and letter spacing
        doc = self.label.document()
        # Increase hover font size to match the new larger base size
        doc.setDefaultFont(QFont("Courier New", 21, QFont.Weight.Bold))
        
        # Apply bright version of hover color for better visibility
        bright_hover_color = QColor(self.hover_color)
        bright_hover_color.setRed(min(bright_hover_color.red() + 50, 255))
        self.label.setDefaultTextColor(bright_hover_color)
        
        # Update border with hover color and thicker border
        border_pen = QPen(self.hover_color, 2)
        self.label_background.setPen(border_pen)
        
        # Update the background to match the new label size
        self.update_position()
        
        # Bring to front
        self.setZValue(2)
        
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        """Handle hover leave events.
        
        Args:
            event: Hover leave event
        """
        self.is_hovered = False
        
        # Restore line appearance
        pen = self.pen()
        pen.setColor(self.normal_color)
        pen.setWidth(int(self.normal_width))  # Convert to int
        self.setPen(pen)
        
        # Restore label appearance to match the CSS styling
        doc = self.label.document()
        # Restore to larger base font size
        doc.setDefaultFont(QFont("Courier New", 21, QFont.Weight.Bold))
        
        # Restore original text color to match the line color but brighter
        bright_text_color = QColor(self.normal_color)
        bright_text_color.setRed(min(bright_text_color.red() + 50, 255))
        self.label.setDefaultTextColor(bright_text_color)
        
        # Restore original border to match the line color
        border_pen = QPen(self.normal_color, 1)
        self.label_background.setPen(border_pen)
        
        # Update the background to match the new label size
        self.update_position()
        
        # Restore z-value
        self.setZValue(0)
        
        super().hoverLeaveEvent(event)
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None) -> None:
        """Override the paint method to draw a more visible line with glow effect.
        
        Args:
            painter: The painter to use
            option: Style options for the item
            widget: The widget being painted on
        """
        # Save the painter state
        painter.save()
        
        # Enable antialiasing for smoother lines
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get the line
        line = self.line()
        
        # Draw a glow effect first (larger, semi-transparent line)
        glow_pen = QPen(self.pen())
        glow_color = QColor(self.pen().color())
        glow_color.setAlpha(80)  # Semi-transparent
        glow_pen.setColor(glow_color)
        glow_pen.setWidth(int(self.pen().width() * 2))  # Double width for glow
        painter.setPen(glow_pen)
        painter.drawLine(line)
        
        # Now draw the actual line
        painter.setPen(self.pen())
        painter.drawLine(line)
        
        # Restore the painter state
        painter.restore()
        
        # Don't call the parent implementation as we're completely replacing it
    
    def update_position(self) -> None:
        """Update the position of the line and label."""
        # Save current styling before repositioning
        current_text_color = self.label.defaultTextColor()
        current_font = self.label.document().defaultFont()
        
        # Get the bounding rectangles of the character cards
        source_rect = self.source_card.sceneBoundingRect()
        target_rect = self.target_card.sceneBoundingRect()
        
        # Calculate pin positions (centered at the top of each card)
        card_width = 180  # Width of the character card
        pin_size = 20     # Size of the pin
        
        # Calculate the center of the pin for each card
        source_pin = QPointF(
            source_rect.x() + card_width / 2,  # Center of the card horizontally
            source_rect.y()                     # Top of the card
        )
        
        target_pin = QPointF(
            target_rect.x() + card_width / 2,  # Center of the card horizontally
            target_rect.y()                     # Top of the card
        )
        
        # Set the line to connect the pins
        self.setLine(QLineF(source_pin, target_pin))
        
        # FORCE a much thicker line width regardless of stored value
        force_width = 8.0  # Set to a very visible value
        if self.is_hovered:
            force_width = 12.0  # Even thicker on hover
            
        pen = self.pen()
        pen.setWidth(int(force_width))
        self.setPen(pen)
        
        # Calculate midpoint of the line
        midpoint = QPointF(
            (source_pin.x() + target_pin.x()) / 2,
            (source_pin.y() + target_pin.y()) / 2
        )
        
        # Calculate angle of the line
        angle = math.atan2(target_pin.y() - source_pin.y(), target_pin.x() - source_pin.x())
        
        # Calculate label position
        # Convert to local coordinates since the label is now a child item
        local_midpoint = self.mapFromScene(midpoint)
        
        # Get label dimensions
        label_rect = self.label.boundingRect()
        label_width = label_rect.width()
        label_height = label_rect.height()
        
        # Position the label centered on the midpoint of the line
        label_pos = QPointF(
            local_midpoint.x() - label_width / 2,
            local_midpoint.y() - label_height / 2
        )
        
        # Set the background rectangle to match the label size with padding
        # Using horizontal padding of 6px and vertical padding of 2px as per CSS
        h_padding = 6
        v_padding = 2
        
        bg_rect = QRectF(
            label_pos.x() - h_padding,
            label_pos.y() - v_padding,
            label_width + h_padding * 2,
            label_height + v_padding * 2
        )
        
        # Update the rounded rectangle
        self.label_background.setRect(bg_rect)
        
        # Set the positions
        self.label_background.setPos(0, 0)
        self.label.setPos(label_pos)
        
        # Restore z-ordering to ensure proper layering
        self.label_background.setZValue(-1)
        self.label.setZValue(1)
        
        # Restore text color and font that might have been lost during repositioning
        self.label.setDefaultTextColor(current_text_color)
        
        # Restore the font
        doc = self.label.document()
        doc.setDefaultFont(current_font)
    
    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent) -> None:
        """Handle context menu events.
        
        Args:
            event: Context menu event
        """
        menu = QMenu()
        
        # Add actions
        edit_action = menu.addAction("Edit Relationship")
        color_action = menu.addAction("Change Color")
        width_action = menu.addAction("Change Width")
        delete_action = menu.addAction("Delete Relationship")
        
        # Show menu and handle actions
        action = menu.exec(event.screenPos())
        
        if action == edit_action:
            # TODO: Implement relationship editing
            QMessageBox.information(None, "Not Implemented", "Relationship editing is not yet implemented.")
        elif action == color_action:
            # Change color
            current_color = self.pen().color()
            color = QColorDialog.getColor(current_color, None, "Select Relationship Color")
            if color.isValid():
                pen = self.pen()
                pen.setColor(color)
                self.setPen(pen)
                self.label.setDefaultTextColor(color)
                # TODO: Update relationship in database
        elif action == width_action:
            # Change width
            current_width = self.pen().width()
            width, ok = QInputDialog.getDouble(
                None, "Change Width", "Enter line width:", current_width, 0.5, 10.0, 1
            )
            if ok:
                pen = self.pen()
                pen.setWidth(width)
                self.setPen(pen)
                # TODO: Update relationship in database
        elif action == delete_action:
            # TODO: Implement relationship deletion
            QMessageBox.information(None, "Not Implemented", "Relationship deletion is not yet implemented.")


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
        
        # Grid snapping settings
        self.grid_snap_enabled = False
        self.grid_size = 50
        self.grid_visible = False
        
        # Set scene size
        self.setSceneRect(0, 0, 10000, 10000)
        
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
            # Just ensure the z-ordering and styling are preserved
            # No need to update positions as that's handled elsewhere
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
                    card_width = 180
                    card_height = 240
                    
                    # Create shadow rectangle as a separate scene item
                    card.shadow_rect = QGraphicsRectItem()
                    card.shadow_rect.setRect(0, 0, card_width, card_height)
                    card.shadow_rect.setBrush(QBrush(QColor(0, 0, 0, 50)))
                    card.shadow_rect.setPen(QPen(Qt.PenStyle.NoPen))
                    card.shadow_rect.setZValue(-1)
                    self.addItem(card.shadow_rect)
                
                # Show and position shadow
                if card.shadow_rect:
                    card.shadow_rect.setPos(card.pos() + QPointF(shadow_offset/2, shadow_offset/2))
                    card.shadow_rect.setVisible(True)
                
                # Bring card to front
                card.setZValue(5)
            else:
                # Hide shadow for unselected cards
                if card.shadow_rect:
                    card.shadow_rect.setVisible(False)
                
                # Reset z-value
                card.setZValue(0)
        
        # Update selection indicator
        self.update_selection_indicator()
        
        # Emit signals if needed
        if not hasattr(self, '_last_selection') or self._last_selection != set(selected_ids):
            self._last_selection = set(selected_ids)
            self.selection_changed.emit(selected_ids)
            
            # If exactly one character is selected, emit the single character selected signal
            if len(selected_ids) == 1:
                self.character_selected.emit(selected_ids[0])
    
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
            from app.db_sqlite import get_story_characters
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
                    from app.db_sqlite import get_story_board_view, update_story_board_view_layout, get_character
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
        """Add a relationship line to the scene.
        
        Args:
            relationship_id: ID of the relationship
            relationship_data: Relationship data
            source_id: ID of the source character
            target_id: ID of the target character
            
        Returns:
            The created relationship line, or None if the characters don't exist
        """
        if source_id not in self.character_cards or target_id not in self.character_cards:
            return None
        
        source_card = self.character_cards[source_id]
        target_card = self.character_cards[target_id]
        
        line = RelationshipLine(relationship_id, relationship_data, source_card, target_card)
        self.addItem(line)
        
        # No need to add the label separately as it's now a child item of the line
        
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
                if QRectF(0, 0, 180, 240).contains(local_pos):
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
        
        card_width = 180  # Approximate width of a card
        card_height = 240  # Approximate height of a card
        
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
        
        # If no views, create a default one
        if not views:
            self.create_default_view()
        else:
            # Select the first view
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
                try:
                    card.setPos(x, y)
                finally:
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
            
            # Add relationship line
            self.scene.add_relationship_line(relationship_id, relationship_data, source_id, target_id)
        
        # Log card count after loading
        print(f"LOAD VIEW: After loading - {len(self.scene.character_cards)} cards in scene")
        
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