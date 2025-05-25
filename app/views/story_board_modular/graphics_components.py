#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Graphics components for the story board.

This module contains the visual components: CharacterCard, RelationshipLine, BendPoint, etc.
"""

import os
import math
from typing import Optional, List, Dict, Any, Tuple, TYPE_CHECKING

from PyQt6.QtWidgets import (
    QGraphicsItemGroup, QGraphicsItem, QGraphicsPixmapItem, QGraphicsTextItem,
    QGraphicsRectItem, QMenu, QInputDialog, QColorDialog, QMessageBox,
    QGraphicsSceneContextMenuEvent, QGraphicsSceneMouseEvent, QGraphicsSceneHoverEvent,
    QGraphicsEllipseItem, QStyleOptionGraphicsItem, QWidget, QGraphicsPathItem,
    QDialog, QDialogButtonBox, QComboBox, QVBoxLayout, QLabel
)
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal, QTimer, QObject
from PyQt6.QtGui import (
    QPixmap, QColor, QPen, QBrush, QFont, QPainter, QPainterPath, QTransform,
    QTextDocument, QPainterPathStroker
)

from app.db_sqlite import (
    get_relationship_types, create_relationship, get_used_relationship_types,
    delete_character, get_character
)

from .utils import CARD_WIDTH, CARD_HEIGHT

# Forward declarations for type checking
if TYPE_CHECKING:
    pass


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
        self.relationships: List['RelationshipLine'] = []
        
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
        card_rect = QRectF(0, 0, CARD_WIDTH, CARD_HEIGHT)
        return card_rect.contains(point)
    
    def shape(self) -> QPainterPath:
        """Override shape to provide a more accurate hit testing area.
        
        Returns:
            A QPainterPath representing the shape for hit testing
        """
        # Create a path that matches the card's rectangular shape
        path = QPainterPath()
        path.addRect(0, 0, CARD_WIDTH, CARD_HEIGHT)
        return path
    
    def create_folded_corner(self) -> QGraphicsItemGroup:
        """Create a folded corner indicator for selection.
        
        Returns:
            A QGraphicsItemGroup representing a folded corner
        """
        # Size of the folded corner - INCREASE SIZE for better visibility
        fold_size = 40  # Increased from 30
        
        # Create a path for the folded corner (top-right of the card)
        path = QPainterPath()
        path.moveTo(CARD_WIDTH - fold_size, 0)  # Start at top right minus fold size
        path.lineTo(CARD_WIDTH, 0)              # Line to top right corner
        path.lineTo(CARD_WIDTH, fold_size)      # Line down fold size
        path.lineTo(CARD_WIDTH - fold_size, 0)  # Line back to start to close the triangle
        
        # Create shadow effect path for depth
        shadow_path = QPainterPath()
        shadow_path.moveTo(CARD_WIDTH - fold_size, 0)
        shadow_path.lineTo(CARD_WIDTH - fold_size, fold_size)
        shadow_path.lineTo(CARD_WIDTH, fold_size)
        shadow_path.lineTo(CARD_WIDTH - fold_size, 0)
        
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
        # Create card background
        card_rect = QGraphicsRectItem(0, 0, CARD_WIDTH, CARD_HEIGHT)
        card_rect.setBrush(QBrush(QColor("#ffffff")))
        card_rect.setPen(QPen(QColor("#000000"), 1))
        card_rect.setZValue(1.0)
        self.addToGroup(card_rect)
        
        # Create photo area
        photo_margin = 15
        photo_width = CARD_WIDTH - (photo_margin * 2)
        photo_height = CARD_HEIGHT - (photo_margin * 2) - 40  # Leave space for name at bottom
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
        name_text.setPos(CARD_WIDTH / 2 - name_text.boundingRect().width() / 2, CARD_HEIGHT - 35)
        name_text.setZValue(1.7)  # Ensure text is above everything
        self.addToGroup(name_text)
        
        # Create badges container
        badges_y = CARD_HEIGHT - 15  # Position below the name (increased space)
        self.add_gender_badge(CARD_WIDTH / 2, badges_y)
        
        # Add main character indicator if applicable
        if self.character_data.get('is_main_character', False):
            star_size = 15
            star_x = CARD_WIDTH - star_size - 5
            star_y = CARD_HEIGHT - star_size - 5
            
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
    
    def add_gender_badge(self, x: float, y: float) -> None:
        """Add a gender badge to the card.
        
        Args:
            x: X coordinate center position
            y: Y coordinate position
        """
        gender = self.character_data.get('gender', 'NOT_SPECIFIED')
        badge_size = 20  # Increased from 16 (25% larger)
        
        # Create badge background (circle)
        badge = QGraphicsEllipseItem(x - badge_size/2, y, badge_size, badge_size)
        
        # Set color based on gender
        if gender == 'FEMALE':
            badge.setBrush(QBrush(QColor("#FF69B4")))  # Pink
            badge.setPen(QPen(QColor("#C71585"), 1))  # Darker pink
            symbol = "♀"
        elif gender == 'MALE':
            badge.setBrush(QBrush(QColor("#87CEFA")))  # Light blue
            badge.setPen(QPen(QColor("#1E90FF"), 1))  # Darker blue
            symbol = "♂"
        elif gender == 'FUTA':
            badge.setBrush(QBrush(QColor("#BA55D3")))  # Purple
            badge.setPen(QPen(QColor("#9400D3"), 1))  # Darker purple
            symbol = "⚧"
        else:  # NOT_SPECIFIED
            badge.setBrush(QBrush(QColor("#333333")))  # Dark gray
            badge.setPen(QPen(QColor("#000000"), 1))  # Black
            symbol = "?"
        
        badge.setZValue(1.8)
        self.addToGroup(badge)
        
        # Add gender symbol
        symbol_text = QGraphicsTextItem(symbol)
        symbol_text.setFont(QFont("Arial", 11, QFont.Weight.Bold))  # Increased from 9 to 11
        symbol_text.setDefaultTextColor(QColor("#FFFFFF"))  # White text
        
        # Center text in badge
        symbol_rect = symbol_text.boundingRect()
        symbol_text.setPos(
            x - symbol_rect.width()/2,
            y + (badge_size - symbol_rect.height())/2
        )
        symbol_text.setZValue(1.9)
        self.addToGroup(symbol_text)
    
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
        painter.setClipRect(QRectF(0, 0, CARD_WIDTH, CARD_HEIGHT))
        
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
            # Remove bendpoints first
            for bendpoint in relationship.bendpoints.copy():
                relationship.remove_bendpoint(bendpoint)
                
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
        # Get the scene and database connection
        scene = self.scene()
        if not scene or not hasattr(scene, 'db_conn'):
            return
        
        # Create the relationship in the database
        relationship_data = {
            'relationship_type': relationship_type['name'],
            'color': "#FF0000",  # Default color
            'width': 6.0  # Thicker lines for better visibility but not excessive
        }
        
        relationship_id = create_relationship(
            scene.db_conn,
            self._character_id,
            target_id,
            relationship_type['name'],
            width=6.0  # Explicitly set width parameter to match the UI
        )
        
        # Add relationship line - this will automatically group with existing lines
        scene.add_relationship_line(relationship_id, relationship_data, self._character_id, target_id)
        
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
                'width': 6.0  # Thicker lines for better visibility but not excessive
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
                    inverse_name,
                    width=6.0  # Explicitly set width parameter to match the UI
                )
                
                # Add the inverse relationship line to the scene
                scene.add_relationship_line(inverse_id, inverse_data, target_id, self._character_id)
        
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
        gender_badge = None
        gender_symbol = None
        
        # Identify existing components
        for item in self.childItems():
            if isinstance(item, QGraphicsPixmapItem):
                pixmap_item = item
            elif isinstance(item, QGraphicsRectItem):
                # Check if this is the photo area (light gray background)
                if item.brush().color().name() == "#eeeeee":
                    photo_rect = item
            elif isinstance(item, QGraphicsTextItem):
                if isinstance(item.parentItem(), QGraphicsEllipseItem) or item.toPlainText() in ["♀", "♂", "⚧", "?"]:
                    gender_symbol = item
                elif item.toPlainText() == "MC":
                    mc_text = item
                else:
                    name_text = item
            elif isinstance(item, QGraphicsEllipseItem):
                if item.brush().color().name() in ["#ff69b4", "#87cefa", "#ba55d3", "#333333"]:  # Gender badge colors
                    gender_badge = item
                elif item.brush().color().name() == "#ffd700":  # Gold color for MC
                    mc_indicator = item
        
        # Photo area dimensions
        photo_margin = 15
        photo_width = CARD_WIDTH - (photo_margin * 2)
        photo_height = CARD_HEIGHT - (photo_margin * 2) - 40  # Leave space for name at bottom
        
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
            name_y = CARD_HEIGHT - 35
            name_text.setPos(CARD_WIDTH / 2 - name_text.boundingRect().width() / 2, name_y)
        
        # Update gender badge
        if gender_badge and gender_symbol:
            # Remove existing gender badge and symbol
            self.removeFromGroup(gender_badge)
            self.removeFromGroup(gender_symbol)
            scene = self.scene()
            if scene:
                scene.removeItem(gender_badge)
                scene.removeItem(gender_symbol)
        
        # Add new gender badge
        badges_y = CARD_HEIGHT - 15  # Position below the name (increased space)
        self.add_gender_badge(CARD_WIDTH / 2, badges_y)
        
        # Update main character indicator
        is_main_character = self.character_data.get('is_main_character', False)
        
        if is_main_character and not mc_indicator:
            # Add MC indicator if it doesn't exist
            star_size = 15
            star_x = CARD_WIDTH - star_size - 5
            star_y = CARD_HEIGHT - star_size - 5
            
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
        return QRectF(0, 0, CARD_WIDTH, CARD_HEIGHT)

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


class BendPoint(QGraphicsEllipseItem):
    """A bendpoint on a relationship line that can be dragged to create curves."""
    
    def __init__(self, relationship_line: 'RelationshipLine', position: float, 
                 x_offset: float = 0.0, y_offset: float = 0.0,
                 bendpoint_id: Optional[int] = None) -> None:
        """Initialize the bendpoint.
        
        Args:
            relationship_line: The relationship line this bendpoint belongs to
            position: Relative position along the line (0-1)
            x_offset: X offset from the base line
            y_offset: Y offset from the base line
            bendpoint_id: ID of the bendpoint in the database (if already exists)
        """
        # Size of the bendpoint
        self.POINT_SIZE = 15  # Increased from 10 to be more noticeable
        
        # Initialize the ellipse item with a temporary rect
        # The actual position will be set in update_position()
        super().__init__(-self.POINT_SIZE/2, -self.POINT_SIZE/2, self.POINT_SIZE, self.POINT_SIZE)
        
        self.relationship_line = relationship_line
        self.position = position  # Relative position along the line (0-1)
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.bendpoint_id = bendpoint_id
        
        # Set appearance with brighter color and thicker border
        self.setBrush(QBrush(QColor("#FF3333")))  # Brighter red
        self.setPen(QPen(QColor("#AA0000"), 2.5))  # Thicker border
        
        # Set flags
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        
        # Track dragging state
        self.is_dragging = False
        self.orig_cursor = None
        
        # Set z-value to be above the line but below other items
        self.setZValue(-5)  # Matches RelationshipLine hover z-value
        
        # Hide bendpoints by default - only show when parent line is selected
        self.setVisible(False)
        
        # Update position based on initial parameters
        self.update_position()
    
    def update_position(self) -> None:
        """Update the bendpoint position based on its relative position and offsets."""
        # Get the start and end points of the base line
        start, end = self.relationship_line.get_base_line_points()
        
        # Calculate the point on the base line according to position
        base_x = start.x() + (end.x() - start.x()) * self.position
        base_y = start.y() + (end.y() - start.y()) * self.position
        
        # Apply offsets
        x = base_x + self.x_offset
        y = base_y + self.y_offset
        
        # Set the position
        self.setPos(x, y)
    
    def calculate_offsets(self) -> None:
        """Calculate and update offsets based on current position."""
        # Get the base line points
        start, end = self.relationship_line.get_base_line_points()
        
        # Calculate the point on the base line according to position
        base_x = start.x() + (end.x() - start.x()) * self.position
        base_y = start.y() + (end.y() - start.y()) * self.position
        
        # Get current position
        current_pos = self.pos()
        
        # Calculate offsets
        self.x_offset = current_pos.x() - base_x
        self.y_offset = current_pos.y() - base_y
    
    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        """Change cursor on hover enter.
        
        Args:
            event: Hover event
        """
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        # Make bendpoint larger and brighter on hover
        self.setRect(-self.POINT_SIZE*0.7, -self.POINT_SIZE*0.7, 
                     self.POINT_SIZE*1.4, self.POINT_SIZE*1.4)
        # Use even brighter color on hover
        self.setBrush(QBrush(QColor("#FF6666")))
        self.setPen(QPen(QColor("#FF0000"), 3.0))
        # Set higher z-value to be more visible
        self.setZValue(-3)  # Higher than the default -5 to be above the line
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        """Reset cursor and appearance on hover leave.
        
        Args:
            event: Hover event
        """
        self.unsetCursor()
        # Reset size
        self.setRect(-self.POINT_SIZE/2, -self.POINT_SIZE/2, 
                     self.POINT_SIZE, self.POINT_SIZE)
        # Restore original colors
        self.setBrush(QBrush(QColor("#FF3333")))  # Back to normal red
        self.setPen(QPen(QColor("#AA0000"), 2.5))  # Normal border
        # Restore original z-value
        self.setZValue(-5)  # Back to the default z-value
        super().hoverLeaveEvent(event)
    
    def setSelected(self, selected: bool) -> None:
        """Override setSelected to ensure bendpoint stays visible when selected.
        
        Args:
            selected: Whether the bendpoint should be selected
        """
        super().setSelected(selected)
        
        # Always stay visible when selected
        if selected:
            self.setVisible(True)
            # Use even brighter color when selected
            self.setBrush(QBrush(QColor("#FF9999")))  # Brighter red for selection
            self.setPen(QPen(QColor("#FF0000"), 3.5))  # Thicker border
            # Bring to front
            self.setZValue(-2)  # Higher z-value to be above lines
    
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Handle mouse press events.
        
        Args:
            event: Mouse press event
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.orig_cursor = self.cursor()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Handle mouse release events.
        
        Args:
            event: Mouse release event
        """
        if event.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.is_dragging = False
            self.setCursor(self.orig_cursor or Qt.CursorShape.SizeAllCursor)
            
            # Recalculate offsets
            self.calculate_offsets()
            
            # Update the database
            self.save_to_database()
            
            # Update the line path
            self.relationship_line.update_path()
        super().mouseReleaseEvent(event)
    
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        """Handle item changes.
        
        Args:
            change: Type of change
            value: New value
            
        Returns:
            Modified value
        """
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.is_dragging:
            # While dragging, update the relationship line path in real-time
            QTimer.singleShot(0, self.relationship_line.update_path)
        
        return super().itemChange(change, value)
    
    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent) -> None:
        """Handle context menu events.
        
        Args:
            event: Context menu event
        """
        menu = QMenu()
        delete_action = menu.addAction("Delete Bendpoint")
        
        action = menu.exec(event.screenPos())
        
        if action == delete_action:
            # Remove this bendpoint
            self.relationship_line.remove_bendpoint(self)
    
    def save_to_database(self) -> None:
        """Save the bendpoint to the database."""
        scene = self.relationship_line.scene()
        if not scene or not hasattr(scene, 'db_conn'):
            return
        
        # Get all relationship IDs for this relationship line
        relationship_ids = [rel['id'] for rel in self.relationship_line.relationships]
        
        try:
            cursor = scene.db_conn.cursor()
            
            if self.bendpoint_id:
                # Update existing bendpoint
                cursor.execute('''
                    UPDATE relationship_bendpoints 
                    SET position = ?, x_offset = ?, y_offset = ? 
                    WHERE id = ?
                ''', (self.position, self.x_offset, self.y_offset, self.bendpoint_id))
                print(f"Updated bendpoint ID={self.bendpoint_id} with position={self.position}, offsets=({self.x_offset}, {self.y_offset})")
            else:
                # Create new bendpoint for the first relationship in the group
                # (bendpoints are shared across all relationships between the same characters)
                primary_relationship_id = relationship_ids[0] if relationship_ids else None
                if primary_relationship_id:
                    cursor.execute('''
                        INSERT INTO relationship_bendpoints (relationship_id, position, x_offset, y_offset)
                        VALUES (?, ?, ?, ?)
                    ''', (primary_relationship_id, self.position, self.x_offset, self.y_offset))
                    self.bendpoint_id = cursor.lastrowid
                    print(f"Created new bendpoint ID={self.bendpoint_id} for relationship {primary_relationship_id} with position={self.position}, offsets=({self.x_offset}, {self.y_offset})")
            
            scene.db_conn.commit()
            
        except Exception as e:
            print(f"Error saving bendpoint to database: {e}")
            scene.db_conn.rollback()
    
    def remove_from_database(self) -> None:
        """Remove the bendpoint from the database."""
        if not self.bendpoint_id:
            return
        
        scene = self.relationship_line.scene()
        if not scene or not hasattr(scene, 'db_conn'):
            return
        
        try:
            cursor = scene.db_conn.cursor()
            cursor.execute('DELETE FROM relationship_bendpoints WHERE id = ?', (self.bendpoint_id,))
            scene.db_conn.commit()
            print(f"Removed bendpoint ID={self.bendpoint_id} from database")
        except Exception as e:
            print(f"Error removing bendpoint from database: {e}")
            scene.db_conn.rollback()


def load_bendpoints(relationship_line: 'RelationshipLine', relationship_id: int) -> List[BendPoint]:
    """Load bendpoints from the database for a specific relationship.
    
    Args:
        relationship_line: The relationship line to load bendpoints for
        relationship_id: ID of the relationship
        
    Returns:
        List of BendPoint objects
    """
    scene = relationship_line.scene()
    if not scene or not hasattr(scene, 'db_conn'):
        print(f"ERROR: No scene or database connection for relationship {relationship_id}")
        return []
    
    try:
        print(f"LOADING BENDPOINTS: Querying for relationship ID {relationship_id}")
        
        # Get the character IDs for this relationship
        source_id = relationship_line.source_card.character_id
        target_id = relationship_line.target_card.character_id
        
        # Check for any bendpoints related to this character pair, not just the specific relationship
        # This handles the case where bendpoints are stored for one direction of a relationship
        # but might be loaded from another relationship ID
        query = """
        SELECT bp.id, bp.position, bp.x_offset, bp.y_offset, bp.relationship_id
        FROM relationship_bendpoints bp
        JOIN relationships r ON bp.relationship_id = r.id
        WHERE (r.source_id = ? AND r.target_id = ?) OR (r.source_id = ? AND r.target_id = ?)
        ORDER BY bp.position
        """
        
        cursor = scene.db_conn.cursor()
        cursor.execute(query, (source_id, target_id, target_id, source_id))
        rows = cursor.fetchall()
        
        print(f"LOADING BENDPOINTS: Found {len(rows)} bendpoints for character pair ({source_id}, {target_id})")
        
        bendpoints = []
        # Track bendpoint IDs we've already added to avoid duplicates
        added_bendpoint_ids = set()
        
        for row in rows:
            bendpoint_id = row[0]
            
            # Skip if we've already added this bendpoint
            if bendpoint_id in added_bendpoint_ids:
                continue
                
            added_bendpoint_ids.add(bendpoint_id)
            
            position = row[1]
            x_offset = row[2]
            y_offset = row[3]
            rel_id = row[4]
            
            print(f"LOADING BENDPOINT: ID={bendpoint_id}, position={position}, offsets=({x_offset}, {y_offset}), from relationship ID={rel_id}")
            
            # Check if this bendpoint's relationship ID matches the one we're looking for
            # or if it belongs to any relationship ID in this line's relationships
            rel_ids_in_line = [rel['id'] for rel in relationship_line.relationships]
            
            if rel_id == relationship_id or rel_id in rel_ids_in_line:
                # Create bendpoint
                bendpoint = BendPoint(
                    relationship_line,
                    position,
                    x_offset,
                    y_offset,
                    bendpoint_id
                )
                
                # Add to the list
                bendpoints.append(bendpoint)
        
        if len(bendpoints) > 0:
            # Get line info
            start, end = relationship_line.get_base_line_points()
            print(f"RELATIONSHIP LINE: Start=({start.x()}, {start.y()}), End=({end.x()}, {end.y()})")
            print(f"RELATIONSHIP SOURCE: ID={relationship_line.source_card.character_id}")
            print(f"RELATIONSHIP TARGET: ID={relationship_line.target_card.character_id}")
        
        return bendpoints
        
    except Exception as e:
        print(f"ERROR loading bendpoints: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


class RelationshipLine(QGraphicsPathItem):
    """A graphical item representing a relationship between characters on the story board."""
    
    def __init__(self, relationships: List[Dict[str, Any]], 
                source_card: CharacterCard, target_card: CharacterCard) -> None:
        """Initialize the relationship line.
        
        Args:
            relationships: List of relationship data dictionaries, each containing 'id', 'relationship_type', 'color', 'width'
            source_card: Source character card
            target_card: Target character card
        """
        super().__init__()
        
        self.relationships = relationships  # Store all relationships between these characters
        self.source_card = source_card
        self.target_card = target_card
        
        # Add this relationship line to the character cards
        self.source_card.add_relationship(self)
        self.target_card.add_relationship(self)
        
        # Use the first relationship for base line properties (could be enhanced later)
        primary_relationship = relationships[0]
        self.normal_color = QColor(primary_relationship['color']) if primary_relationship['color'] else QColor("#FF0000")
        self.hover_color = self.normal_color.lighter(130)  # Lighter version for hover
        self.normal_width = float(primary_relationship['width']) if primary_relationship['width'] else 6.0  # Thicker lines but not excessive
        self.hover_width = self.normal_width * 1.5  # Thicker on hover
        
        # Set initial pen
        self.setPen(QPen(self.normal_color, int(self.normal_width), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        
        # Set flags
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        
        # Set z-value to ensure relationship lines always appear behind character cards
        self.setZValue(-10)  # Negative z-value to stay behind character cards
        
        # Create label using QGraphicsTextItem with a QTextDocument for letter spacing
        self.label = QGraphicsTextItem(self)  # Make the label a child of the line
        
        # Create and configure a text document to control letter-spacing
        doc = QTextDocument()
        # Increase font size by 50% (from 14 to 21)
        doc.setDefaultFont(QFont("Courier New", 21, QFont.Weight.Bold))
        
        # Create label text from all relationships
        relationship_types = [rel['relationship_type'] for rel in relationships]
        label_text = " / ".join(relationship_types)  # Join multiple relationships with " / "
        
        # Apply CSS-like styling to the text document
        # We need to escape the text content for HTML
        escaped_text = label_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
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
        
        # Bendpoints list
        self.bendpoints = []
        
        # Minimum distance between bendpoints (in relative position units 0-1)
        self.min_bendpoint_distance = 0.05
        
        # Load existing bendpoints from database
        self.load_bendpoints()
        
        # Update position and path
        self.update_position()
        
    @property
    def relationship_id(self) -> int:
        """Get the primary relationship ID for this line.
        
        Returns:
            The ID of the first relationship in this line
        """
        return self.relationships[0]['id'] if self.relationships else 0
        
    def setSelected(self, selected: bool) -> None:
        """Override setSelected to show/hide bendpoints based on selection state.
        
        Args:
            selected: Whether the line should be selected
        """
        # Call the parent implementation first
        super().setSelected(selected)
        
        # Update bendpoints visibility based on selection state
        for bendpoint in self.bendpoints:
            bendpoint.setVisible(selected)
            
        # If selected, bring to front temporarily
        if selected:
            self.setZValue(-2)  # Higher than normal (-10) but still behind character cards
        else:
            # If not selected, ensure normal z-value
            if not self.is_hovered:
                self.setZValue(-10)  # Normal z-value
    
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
        
        # Bring to front but still behind character cards
        self.setZValue(-5)  # Higher than normal (-10) but still behind character cards (0+)
        
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
        
        # Restore z-value to stay behind character cards
        self.setZValue(-10)  # Back to original z-value behind character cards
        
        super().hoverLeaveEvent(event)
    
    def shape(self) -> QPainterPath:
        """Override shape to create a wider hit area for the path.
        
        Returns:
            A wider path shape for hit detection
        """
        # Get the normal path
        path = self.path()
        
        # Create a stroker to make the path wider for hit detection
        stroker = QPainterPathStroker()
        # Make hit area wider (3x the visual width) for better clickability
        stroker.setWidth(self.pen().width() * 3)
        
        # Create the wider path
        return stroker.createStroke(path)
    
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
        
        # Draw a glow effect first (larger, semi-transparent line)
        glow_pen = QPen(self.pen())
        glow_color = QColor(self.pen().color())
        glow_color.setAlpha(100)  # Semi-transparent glow
        glow_pen.setColor(glow_color)
        glow_pen.setWidth(int(self.pen().width() * 2))  # Double width for moderate glow effect
        painter.setPen(glow_pen)
        painter.drawPath(self.path())
        
        # Now draw the actual line
        painter.setPen(self.pen())
        painter.drawPath(self.path())
        
        # Restore the painter state
        painter.restore()
        
        # Don't call the parent implementation as we're completely replacing it
    
    def get_base_line_points(self) -> Tuple[QPointF, QPointF]:
        """Get the start and end points of the base line (original straight line).
        
        Returns:
            Tuple of start and end points
        """
        # Get the bounding rectangles of the character cards
        source_rect = self.source_card.sceneBoundingRect()
        target_rect = self.target_card.sceneBoundingRect()
        
        # Calculate pin positions (centered at the top of each card)
        
        # Calculate the center of the pin for each card
        source_pin = QPointF(
            source_rect.x() + CARD_WIDTH / 2,  # Center of the card horizontally
            source_rect.y()                     # Top of the card
        )
        
        target_pin = QPointF(
            target_rect.x() + CARD_WIDTH / 2,  # Center of the card horizontally
            target_rect.y()                     # Top of the card
        )
        
        return source_pin, target_pin
    
    def update_position(self) -> None:
        """Update the position of the line and label."""
        # Save current styling before repositioning
        current_text_color = self.label.defaultTextColor()
        current_font = self.label.document().defaultFont()
        
        # Get the start and end points
        start, end = self.get_base_line_points()
        
        # Update path with bendpoints
        self.update_path()
        
        # Get the actual path for calculating label position
        path = self.path()
        
        # Calculate position for label (40% of the way along the path)
        label_position_factor = 0.4
        
        # Get point along the actual path, accounting for curves
        if self.bendpoints:
            # If we have bendpoints, calculate position along the path
            path_length = path.length()
            
            # Find a good position for the label
            # Try to avoid placing it too close to bendpoints
            found_good_position = False
            best_label_factor = label_position_factor
            
            # Try a few positions to find one not too close to a bendpoint
            test_positions = [0.3, 0.4, 0.5, 0.25, 0.6]
            min_distance_to_bendpoint = 50  # Minimum pixel distance from bendpoint
            
            for test_factor in test_positions:
                test_point = path.pointAtPercent(test_factor)
                
                # Check distance to all bendpoints
                too_close = False
                for bendpoint in self.bendpoints:
                    bp_pos = self.mapToScene(bendpoint.pos())
                    distance = math.sqrt((test_point.x() - bp_pos.x())**2 + (test_point.y() - bp_pos.y())**2)
                    if distance < min_distance_to_bendpoint:
                        too_close = True
                        break
                
                if not too_close:
                    best_label_factor = test_factor
                    found_good_position = True
                    break
            
            # Get the label point using the best factor
            label_point = path.pointAtPercent(best_label_factor)
        else:
            # For straight lines, use the original calculation
            label_point = QPointF(
                start.x() + (end.x() - start.x()) * label_position_factor,
                start.y() + (end.y() - start.y()) * label_position_factor
            )
        
        # Convert to local coordinates since the label is now a child item
        local_label_point = self.mapFromScene(label_point)
        
        # Get label dimensions
        label_rect = self.label.boundingRect()
        label_width = label_rect.width()
        label_height = label_rect.height()
        
        # Position the label centered on the calculated point
        label_pos = QPointF(
            local_label_point.x() - label_width / 2,
            local_label_point.y() - label_height / 2
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
        
        # Update bendpoint positions
        self.update_bendpoint_positions()
    
    def update_path(self) -> None:
        """Update the path with bendpoints."""
        # Get base line points
        start, end = self.get_base_line_points()
        
        # Create a path
        path = QPainterPath()
        path.moveTo(start)
        
        # Add bendpoints if they exist, otherwise it's a straight line
        if self.bendpoints and len(self.bendpoints) > 0:
            print(f"UPDATE PATH: Using {len(self.bendpoints)} bendpoints for relationship")
            
            # Sort bendpoints by position for consistent curve
            sorted_bendpoints = sorted(self.bendpoints, key=lambda bp: bp.position)
            
            # Debug info about bendpoints
            for i, bp in enumerate(sorted_bendpoints):
                print(f"  Bendpoint {i+1}: ID={bp.bendpoint_id}, position={bp.position}, at ({bp.pos().x()}, {bp.pos().y()})")
            
            if len(sorted_bendpoints) == 1:
                # With just one bendpoint, create a smooth quadratic curve
                bp_pos = sorted_bendpoints[0].pos()
                scene_pos = self.mapToScene(bp_pos)
                print(f"  Using single bendpoint at ({scene_pos.x()}, {scene_pos.y()}) to curve from ({start.x()}, {start.y()}) to ({end.x()}, {end.y()})")
                path.quadTo(scene_pos, end)
            else:
                # With multiple bendpoints, create a smooth curve through all points
                prev_point = start
                
                for i, bendpoint in enumerate(sorted_bendpoints):
                    bp_pos = bendpoint.pos()
                    scene_pos = self.mapToScene(bp_pos)
                    
                    if i == 0:
                        # First bendpoint - create curve from start to this point
                        midpoint = QPointF(
                            (prev_point.x() + scene_pos.x()) / 2,
                            (prev_point.y() + scene_pos.y()) / 2
                        )
                        path.quadTo(prev_point, midpoint)
                    else:
                        # For subsequent bendpoints, create smooth curves between them
                        prev_bp_pos = sorted_bendpoints[i-1].pos()
                        prev_scene_pos = self.mapToScene(prev_bp_pos)
                        
                        # Create control point halfway between the points
                        control_point = QPointF(
                            (prev_scene_pos.x() + scene_pos.x()) / 2,
                            (prev_scene_pos.y() + scene_pos.y()) / 2
                        )
                        path.quadTo(control_point, scene_pos)
                    
                    prev_point = scene_pos
                
                # Create final curve from last bendpoint to end
                path.quadTo(prev_point, end)
        else:
            # No bendpoints, use a straight line
            print(f"UPDATE PATH: No bendpoints for relationship, using straight line from ({start.x()}, {start.y()}) to ({end.x()}, {end.y()})")
            path.lineTo(end)
        
        # Set the path
        self.setPath(path)
    
    def update_bendpoint_positions(self) -> None:
        """Update the positions of all bendpoints."""
        for bendpoint in self.bendpoints:
            bendpoint.update_position()
    
    def load_bendpoints(self) -> None:
        """Load bendpoints from the database for all relationships in this line."""
        scene = self.scene()
        if not scene:
            print("ERROR: No scene found for relationship line when loading bendpoints")
            return
            
        print(f"RELATIONSHIP: Loading bendpoints for relationship group with {len(self.relationships)} relationships")
        print(f"RELATIONSHIP IDS: {[rel['id'] for rel in self.relationships]}")
        print(f"RELATIONSHIP TYPE: {self.relationships[0]['relationship_type']}")
        print(f"RELATIONSHIP SOURCE: ID={self.source_card.character_id}, Name={self.source_card.character_data['name']}")
        print(f"RELATIONSHIP TARGET: ID={self.target_card.character_id}, Name={self.target_card.character_data['name']}")
            
        # Get all relationship IDs in this group
        all_bendpoints = []
        for relationship in self.relationships:
            relationship_id = relationship['id']
            
            # Load bendpoints for this relationship
            new_bendpoints = load_bendpoints(self, relationship_id)
            
            # Add to temporary list
            all_bendpoints.extend(new_bendpoints)
        
        # Add all bendpoints to the scene
        for bendpoint in all_bendpoints:
            scene.addItem(bendpoint)
            self.bendpoints.append(bendpoint)
            
        # Log debug info about loaded bendpoints
        if all_bendpoints:
            print(f"Loaded {len(all_bendpoints)} bendpoints across {len(self.relationships)} relationships")
            for i, bp in enumerate(all_bendpoints):
                print(f"  Bendpoint {i+1}: ID={bp.bendpoint_id}, position={bp.position}, offsets=({bp.x_offset}, {bp.y_offset})")
        else:
            print(f"WARNING: No bendpoints found for relationship group {[rel['id'] for rel in self.relationships]}")
            
        # Force an update of the path
        self.update_path()
    
    def add_bendpoint(self, position: float) -> None:
        """Add a bendpoint to the line.
        
        Args:
            position: Relative position along the line (0-1)
        """
        # Check for minimum distance from existing bendpoints
        for bp in self.bendpoints:
            if abs(bp.position - position) < self.min_bendpoint_distance:
                # Too close to an existing bendpoint
                return
        
        # Create new bendpoint
        bendpoint = BendPoint(self, position)
        
        # Add to scene
        scene = self.scene()
        if scene:
            scene.addItem(bendpoint)
            
        # Add to list
        self.bendpoints.append(bendpoint)
        
        # Save to database
        bendpoint.save_to_database()
        
        # Update path
        self.update_path()
    
    def remove_bendpoint(self, bendpoint: BendPoint) -> None:
        """Remove a bendpoint from the line.
        
        Args:
            bendpoint: The bendpoint to remove
        """
        if bendpoint in self.bendpoints:
            # Remove from database first
            if bendpoint.bendpoint_id:
                bendpoint.remove_from_database()
                
            # Remove from list
            self.bendpoints.remove(bendpoint)
            
            # Remove from scene
            scene = self.scene()
            if scene:
                scene.removeItem(bendpoint)
            
            # Update path
            self.update_path()
            
            print(f"Removed bendpoint ID={bendpoint.bendpoint_id} from relationship line")
    
    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent) -> None:
        """Handle context menu events.
        
        Args:
            event: Context menu event
        """
        menu = QMenu()
        
        # Add actions
        add_bendpoint_action = menu.addAction("Add Bendpoint")
        menu.addSeparator()
        edit_action = menu.addAction("Edit Relationship")
        color_action = menu.addAction("Change Color")
        width_action = menu.addAction("Change Width")
        delete_action = menu.addAction("Delete Relationship")
        
        # Show menu and handle actions
        action = menu.exec(event.screenPos())
        
        if action == add_bendpoint_action:
            # Get mouse position relative to line
            scene_pos = event.scenePos()
            
            # Get line start and end points
            start, end = self.get_base_line_points()
            
            # Calculate relative position along the line
            line_length = math.sqrt((end.x() - start.x())**2 + (end.y() - start.y())**2)
            
            # Project the point onto the line
            t = ((scene_pos.x() - start.x()) * (end.x() - start.x()) + 
                 (scene_pos.y() - start.y()) * (end.y() - start.y())) / (line_length**2)
            
            # Clamp t to [0, 1]
            t = max(0, min(1, t))
            
            # Add bendpoint at this position
            self.add_bendpoint(t)
            
        elif action == edit_action:
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
            # Confirm deletion
            reply = QMessageBox.question(
                None,
                "Delete Relationship",
                f"Are you sure you want to delete this relationship?\n({self.relationships[0]['relationship_type']})",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Delete relationship from database
                self.delete_relationship()
    
    def delete_relationship(self) -> None:
        """Delete this relationship from the database and remove it from the scene."""
        # Get the scene
        scene = self.scene()
        if not scene or not hasattr(scene, 'db_conn'):
            return
            
        try:
            # Delete bendpoints for all relationships in this group
            cursor = scene.db_conn.cursor()
            relationship_ids = [rel['id'] for rel in self.relationships]
            
            # Use parameterized query with placeholder for each ID
            placeholders = ', '.join(['?'] * len(relationship_ids))
            cursor.execute(f"DELETE FROM relationship_bendpoints WHERE relationship_id IN ({placeholders})",
                          relationship_ids)
            
            print(f"Deleted bendpoints for relationship IDs: {relationship_ids}")
            
            # Delete relationship from database
            cursor.execute("DELETE FROM relationships WHERE id = ?", (self.relationships[0]['id'],))
            scene.db_conn.commit()
            
            # Remove from the character cards' relationship lists
            self.source_card.remove_relationship(self)
            self.target_card.remove_relationship(self)
            
            # Remove from scene's tracking dictionary
            if self.relationships[0]['id'] in scene.relationship_lines:
                del scene.relationship_lines[self.relationships[0]['id']]
            
            # Remove from scene
            scene.removeItem(self)
            
            # Emit layout changed signal to trigger auto-save
            if hasattr(scene, 'layout_changed'):
                scene.layout_changed.emit()
                
            # Find main window and trigger board refresh if possible
            parent_widget = scene.views()[0].parent() if scene.views() else None
            if parent_widget and hasattr(parent_widget, 'refresh_board'):
                # Use QTimer to call refresh_board after this event has finished processing
                QTimer.singleShot(100, lambda: parent_widget.refresh_board())
                
        except Exception as e:
            QMessageBox.critical(
                None,
                "Error",
                f"Failed to delete relationship: {str(e)}"
            ) 