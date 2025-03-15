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
    QDialog, QDialogButtonBox, QStyleOptionGraphicsItem, QCheckBox, QLineEdit
)
from PyQt6.QtCore import Qt, QSize, QPointF, QRectF, QLineF, pyqtSignal, QTimer, QObject
from PyQt6.QtGui import (
    QPixmap, QImage, QColor, QPen, QBrush, QFont, QPainter, QPainterPath,
    QTransform, QCursor, QDrag, QMouseEvent, QWheelEvent, QKeyEvent
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
        
        # Set position after everything else is set up
        self.setPos(x, y)
    
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
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None) -> None:
        """Paint the item.
        
        Args:
            painter: Painter to use
            option: Style options
            widget: Widget being painted on
        """
        # Call the parent class paint method
        super().paint(painter, option, widget)
        
        # Draw the bounding rect if enabled - removed to eliminate dashed line
        # if hasattr(self, '_show_bounding_rect') and self._show_bounding_rect:
        #     # Draw a dashed red border around the bounding rect
        #     painter.setPen(QPen(QColor("#ff0000"), 2, Qt.PenStyle.DashLine))
        #     painter.drawRect(self.boundingRect())
    
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value) -> Any:
        """Handle item changes.
        
        Args:
            change: Type of change
            value: New value
            
        Returns:
            Modified value
        """
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
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
            story_id=self.character_data['story_id'],
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
            'width': 1.0  # Default width
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
                'width': 1.0  # Default width
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
        self.normal_width = float(relationship_data['width']) if relationship_data['width'] else 1.0
        self.hover_width = self.normal_width * 2  # Thicker on hover
        
        # Set initial pen
        self.setPen(QPen(self.normal_color, int(self.normal_width), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        
        # Set flags
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        
        # Create label
        self.label = QGraphicsTextItem(self)  # Make the label a child of the line
        self.label.setPlainText(relationship_data['relationship_type'])
        self.label.setFont(QFont("Arial", 9, QFont.Weight.Bold))  # Increased font size
        
        # Ensure text color has good contrast with background
        # Use white text for better readability against dark background
        self.label.setDefaultTextColor(QColor(255, 255, 255))
        
        # Create a background for the label to make it more readable
        self.label_background = QGraphicsRectItem(self)
        self.label_background.setBrush(QBrush(QColor(40, 40, 40, 230)))  # More opaque dark background
        
        # Add a thin border with the relationship color for better visibility
        border_pen = QPen(self.normal_color, 1)  # Use integer for width
        self.label_background.setPen(border_pen)
        
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
        
        # Change label appearance
        self.label.setFont(QFont("Arial", 10, QFont.Weight.Bold))  # Slightly larger font
        # Keep white text for readability, but update the border color
        border_pen = self.label_background.pen()
        border_pen.setColor(self.hover_color)
        border_pen.setWidth(2)  # Slightly thicker border on hover (integer value)
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
        
        # Restore label appearance
        self.label.setFont(QFont("Arial", 9, QFont.Weight.Bold))  # Original font size
        # Keep white text for readability, but restore the border color and width
        border_pen = self.label_background.pen()
        border_pen.setColor(self.normal_color)
        border_pen.setWidth(1)  # Restore original border width (integer value)
        self.label_background.setPen(border_pen)
        
        # Update the background to match the new label size
        self.update_position()
        
        # Restore z-value
        self.setZValue(0)
        
        super().hoverLeaveEvent(event)
    
    def update_position(self) -> None:
        """Update the position of the line and label."""
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
        
        # Set the background rectangle to match the label size with increased padding
        padding = 6  # Increased padding for better readability
        self.label_background.setRect(
            label_pos.x() - padding,
            label_pos.y() - padding,
            label_width + padding * 2,
            label_height + padding * 2
        )
        
        # Set the positions
        self.label_background.setPos(0, 0)  # Already positioned by its rect
        self.label.setPos(label_pos)
    
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
        
        # Grid snapping settings
        self.grid_snap_enabled = False
        self.grid_size = 50
        self.grid_visible = False
        
        # Set scene size
        self.setSceneRect(0, 0, 10000, 10000)
        
        # Connect signals
        self.selectionChanged.connect(self.on_selection_changed)
    
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
    
    def on_selection_changed(self) -> None:
        """Handle selection changes."""
        # Bring selected items to front
        for item in self.selectedItems():
            item.setZValue(1)
        
        # Reset z-value for non-selected items
        for item in self.items():
            if not item.isSelected():
                item.setZValue(0)
    
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
        
        print(f"ADD CARD: Character {character_id} added successfully. Total cards: {len(self.character_cards)}")
        
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
        super().mousePressEvent(event)
    
    def on_character_position_changed(self, character_id: int) -> None:
        """Handle character position change.
        
        Args:
            character_id: ID of the character that moved
        """
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
        
        # Add grid snapping controls
        self.grid_snap_checkbox = QCheckBox("Snap to Grid")
        self.grid_snap_checkbox.setChecked(False)
        self.grid_snap_checkbox.stateChanged.connect(self.on_grid_snap_changed)
        toolbar.addWidget(self.grid_snap_checkbox)
        
        self.grid_visible_checkbox = QCheckBox("Show Grid")
        self.grid_visible_checkbox.setChecked(False)
        self.grid_visible_checkbox.stateChanged.connect(self.on_grid_visible_changed)
        toolbar.addWidget(self.grid_visible_checkbox)
        
        self.grid_size_label = QLabel("Grid Size:")
        toolbar.addWidget(self.grid_size_label)
        
        self.grid_size_combo = QComboBox()
        self.grid_size_combo.addItems(["25", "50", "75", "100"])
        self.grid_size_combo.setCurrentIndex(1)  # Default to 50
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
        
        # Connect signals
        self.scene.layout_changed.connect(self.on_layout_changed)
        
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
            main_window.status_bar.showMessage("View layout saved", 2000)

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
    
    def on_grid_snap_changed(self, state: int) -> None:
        """Handle grid snap checkbox state change.
        
        Args:
            state: Checkbox state
        """
        if self.scene:
            self.scene.set_grid_snap(state == Qt.CheckState.Checked.value)
    
    def on_grid_visible_changed(self, state: int) -> None:
        """Handle grid visibility checkbox state change.
        
        Args:
            state: Checkbox state
        """
        if self.scene:
            self.scene.set_grid_visible(state == Qt.CheckState.Checked.value)
    
    def on_grid_size_changed(self, index: int) -> None:
        """Handle grid size combo box change.
        
        Args:
            index: Selected index
        """
        if self.scene:
            grid_size = int(self.grid_size_combo.currentText())
            self.scene.set_grid_size(grid_size)
    
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
            if str(character_id) in layout:
                position = layout[str(character_id)]
                x = position.get('x', 0)
                y = position.get('y', 0)
                print(f"DEBUG: Setting character {character_id} position to ({x}, {y})")
                
                # Get current position before setting new one
                current_pos = card.pos()
                print(f"DEBUG: Current position for character {character_id}: ({current_pos.x()}, {current_pos.y()})")
                
                # Set new position
                card.setPos(x, y)
                
                # Verify position was set
                new_pos = card.pos()
                print(f"DEBUG: New position for character {character_id}: ({new_pos.x()}, {new_pos.y()})")
            else:
                print(f"DEBUG: No position data found for character {character_id}")
        
        # Center on the characters
        self.view.center_on_characters()
        
        # Force the view to update
        self.view.viewport().update() 