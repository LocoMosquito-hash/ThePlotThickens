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
    QGraphicsItemGroup, QToolBar, QSizePolicy, QGraphicsEllipseItem, QFrame
)
from PyQt6.QtCore import Qt, QSize, QPointF, QRectF, QLineF, pyqtSignal, QTimer, QObject
from PyQt6.QtGui import (
    QPixmap, QImage, QColor, QPen, QBrush, QFont, QPainter, QPainterPath,
    QTransform, QCursor, QDrag, QMouseEvent, QWheelEvent, QKeyEvent
)

from app.db_sqlite import (
    get_story, get_story_characters, get_character_relationships,
    get_story_board_views, get_story_board_view, create_story_board_view,
    update_story_board_view_layout
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
        
        self.character_id = character_id
        self.character_data = character_data
        
        # Set flags before setting position
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        
        # Create card components
        self.create_card()
        
        # Track connected relationships
        self.relationships: List[RelationshipLine] = []
        
        # Track if we're currently moving
        self.is_moving = False
        
        # Set position after everything else is set up
        print(f"DEBUG: Setting initial position for character {character_id} to ({x}, {y})")
        self.setPos(x, y)
        pos = self.pos()
        print(f"DEBUG: Position after setPos: ({pos.x()}, {pos.y()})")
    
    def create_card(self) -> None:
        """Create the card components."""
        # Card dimensions
        card_width = 180
        card_height = 240
        
        # Create polaroid-style card background (white with a border)
        self.background = QGraphicsRectItem(0, 0, card_width, card_height)
        self.background.setBrush(QBrush(QColor("#FFFFFF")))  # White color
        self.background.setPen(QPen(QColor("#000000"), 2))
        self.addToGroup(self.background)
        
        # Create shadow effect
        shadow_rect = QGraphicsRectItem(5, 5, card_width, card_height)
        shadow_rect.setBrush(QBrush(QColor(0, 0, 0, 40)))  # Semi-transparent black
        shadow_rect.setPen(QPen(Qt.PenStyle.NoPen))  # No border
        self.addToGroup(shadow_rect)
        self.background.setZValue(1)  # Ensure background is above shadow
        
        # Create pushpin
        pin_size = 20
        pin = QGraphicsEllipseItem(card_width / 2 - pin_size / 2, -pin_size / 2, pin_size, pin_size)
        pin.setBrush(QBrush(QColor("#FF0000")))  # Red color
        pin.setPen(QPen(QColor("#800000"), 1))  # Dark red border
        pin.setZValue(2)  # Ensure pin is above background
        self.addToGroup(pin)
        
        # Create photo area (slightly inset from the card)
        photo_margin = 15
        photo_width = card_width - (photo_margin * 2)
        photo_height = card_height - (photo_margin * 2) - 40  # Leave space for name at bottom
        
        photo_rect = QGraphicsRectItem(photo_margin, photo_margin, photo_width, photo_height)
        photo_rect.setBrush(QBrush(QColor("#EEEEEE")))  # Light gray color
        photo_rect.setPen(QPen(QColor("#CCCCCC"), 1))  # Light gray border
        photo_rect.setZValue(1.5)  # Ensure photo area is above background but below pin
        self.addToGroup(photo_rect)
        
        # If avatar exists, load it
        if self.character_data['avatar_path'] and os.path.exists(self.character_data['avatar_path']):
            try:
                pixmap = QPixmap(self.character_data['avatar_path'])
                pixmap_item = QGraphicsPixmapItem(
                    pixmap.scaled(
                        photo_width,
                        photo_height,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                )
                
                # Center the pixmap in the photo area
                pixmap_width = pixmap_item.pixmap().width()
                pixmap_height = pixmap_item.pixmap().height()
                pixmap_x = photo_margin + (photo_width - pixmap_width) / 2
                pixmap_y = photo_margin + (photo_height - pixmap_height) / 2
                
                pixmap_item.setPos(pixmap_x, pixmap_y)
                pixmap_item.setZValue(1.6)  # Ensure pixmap is above photo area
                self.addToGroup(pixmap_item)
            except Exception as e:
                print(f"Error loading avatar: {e}")
        
        # Create character name (at the bottom of the polaroid)
        name_y = card_height - 35
        name = QGraphicsTextItem(self.character_data['name'])
        name.setPos(card_width / 2 - name.boundingRect().width() / 2, name_y)
        name.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        name.setDefaultTextColor(QColor("#000000"))
        name.setZValue(1.7)  # Ensure name is above everything
        self.addToGroup(name)
        
        # Add a small indicator if this is a main character
        if self.character_data.get('is_main_character', False):
            star_size = 15
            star_x = card_width - star_size - 5
            star_y = card_height - star_size - 5
            
            # Create a simple star indicator (just a yellow circle for now)
            star = QGraphicsEllipseItem(star_x, star_y, star_size, star_size)
            star.setBrush(QBrush(QColor("#FFD700")))  # Gold color
            star.setPen(QPen(QColor("#DAA520"), 1))  # Darker gold border
            star.setZValue(1.8)  # Ensure star is above everything
            self.addToGroup(star)
            
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
    
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value) -> Any:
        """Handle item changes.
        
        Args:
            change: Type of change
            value: New value
            
        Returns:
            Modified value
        """
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            # Update connected relationship lines
            for relationship in self.relationships:
                relationship.update_position()
            
            # Set moving flag
            self.is_moving = True
        
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged and self.is_moving:
            # Position has changed, emit signal
            self.is_moving = False
            # Use QTimer to emit the signal after a short delay to avoid excessive updates
            QTimer.singleShot(100, lambda: self.signals.position_changed.emit(self.character_id))
        
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
            self.relationships.remove(relationship)
    
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
                if character_id != self.character_id:
                    relationship_menu.addAction(f"To: {card.character_data['name']}")
        
        action = menu.exec(event.screenPos())
        
        if action == edit_action:
            # TODO: Implement character editing
            QMessageBox.information(None, "Not Implemented", "Character editing is not yet implemented.")
        elif action == delete_action:
            # TODO: Implement character deletion
            QMessageBox.information(None, "Not Implemented", "Character deletion is not yet implemented.")
        elif action and action.text().startswith("To: "):
            # TODO: Implement relationship creation
            target_name = action.text()[4:]  # Remove "To: " prefix
            QMessageBox.information(None, "Not Implemented", f"Creating relationship to {target_name} is not yet implemented.")


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
        color = QColor(relationship_data['color']) if relationship_data['color'] else QColor("#FF0000")
        width = float(relationship_data['width']) if relationship_data['width'] else 1.0
        self.setPen(QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        
        # Set flags
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        
        # Create label
        self.label = QGraphicsTextItem()
        self.label.setPlainText(relationship_data['relationship_type'])
        self.label.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        self.label.setDefaultTextColor(color)
        
        # Update position
        self.update_position()
    
    def update_position(self) -> None:
        """Update the position of the line and label."""
        # Get the center points of the character cards
        source_center = self.source_card.sceneBoundingRect().center()
        target_center = self.target_card.sceneBoundingRect().center()
        
        # Set the line
        self.setLine(QLineF(source_center, target_center))
        
        # Update label position
        if self.label.scene():
            # Position the label at the midpoint of the line
            midpoint = QPointF(
                (source_center.x() + target_center.x()) / 2,
                (source_center.y() + target_center.y()) / 2
            )
            
            # Offset the label to avoid overlapping with the line
            angle = math.atan2(target_center.y() - source_center.y(), target_center.x() - source_center.x())
            offset = 10  # Offset distance
            label_pos = QPointF(
                midpoint.x() + offset * math.sin(angle),
                midpoint.y() - offset * math.cos(angle)
            )
            
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
    
    def __init__(self, parent=None) -> None:
        """Initialize the story board scene.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Set scene properties
        self.setSceneRect(0, 0, 10000, 10000)  # Increase scene size to accommodate larger positions
        self.setBackgroundBrush(QBrush(QColor("#2D2D30")))  # Dark background
        
        # Track items
        self.character_cards: Dict[int, CharacterCard] = {}
        self.relationship_lines: Dict[int, RelationshipLine] = {}
        
        # Track state
        self.is_creating_relationship = False
        self.relationship_start_card = None
        self.temp_line = None
    
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
        card = CharacterCard(character_id, character_data, x, y)
        self.addItem(card)
        self.character_cards[character_id] = card
        
        # Connect to position changed signal
        card.position_changed.connect(self.on_character_position_changed)
        
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
        
        # Add the label to the scene
        self.addItem(line.label)
        
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
        layout = {}
        
        # Add character positions
        for character_id, card in self.character_cards.items():
            pos = card.pos()
            layout[str(character_id)] = {"x": pos.x(), "y": pos.y()}
        
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
        toolbar = QHBoxLayout()
        
        # Create view selector
        self.view_selector = QComboBox()
        self.view_selector.currentIndexChanged.connect(self.on_view_changed)
        toolbar.addWidget(QLabel("View:"))
        toolbar.addWidget(self.view_selector)
        
        # Add spacer
        toolbar.addWidget(create_vertical_line())
        
        # Create view buttons
        self.new_view_button = QPushButton("New View")
        self.new_view_button.clicked.connect(self.on_new_view)
        toolbar.addWidget(self.new_view_button)
        
        self.save_view_button = QPushButton("Save View")
        self.save_view_button.clicked.connect(self.on_save_view)
        toolbar.addWidget(self.save_view_button)
        
        # Add spacer
        toolbar.addWidget(create_vertical_line())
        
        # Create character button
        self.add_character_button = QPushButton("Add Character")
        self.add_character_button.clicked.connect(self.on_add_character)
        toolbar.addWidget(self.add_character_button)
        
        # Add spacer
        toolbar.addWidget(create_vertical_line())
        
        # Create zoom buttons
        self.zoom_in_button = QPushButton("Zoom In")
        self.zoom_in_button.clicked.connect(self.on_zoom_in)
        toolbar.addWidget(self.zoom_in_button)
        
        self.zoom_out_button = QPushButton("Zoom Out")
        self.zoom_out_button.clicked.connect(self.on_zoom_out)
        toolbar.addWidget(self.zoom_out_button)
        
        self.reset_zoom_button = QPushButton("Reset Zoom")
        self.reset_zoom_button.clicked.connect(self.on_reset_zoom)
        toolbar.addWidget(self.reset_zoom_button)
        
        # Add spacer
        toolbar.addWidget(create_vertical_line())
        
        # Create reset positions button
        self.reset_positions_button = QPushButton("Reset Positions")
        self.reset_positions_button.clicked.connect(self.reset_character_positions)
        self.reset_positions_button.setToolTip("Reset character positions to a default grid layout")
        toolbar.addWidget(self.reset_positions_button)
        
        # Add spacer
        toolbar.addWidget(create_vertical_line())
        
        # Create position cards button
        self.position_cards_button = QPushButton("Position Cards")
        self.position_cards_button.clicked.connect(self.position_cards)
        self.position_cards_button.setToolTip("Position cards according to saved layout")
        toolbar.addWidget(self.position_cards_button)
        
        main_layout.addLayout(toolbar)
        
        # Create graphics view
        self.scene = StoryBoardScene(self)
        self.scene.layout_changed.connect(self.on_layout_changed)
        self.view = StoryBoardView(self)
        self.view.setScene(self.scene)
        main_layout.addWidget(self.view)
        
        # Disable controls initially
        self.view_selector.setEnabled(False)
        self.new_view_button.setEnabled(False)
        self.save_view_button.setEnabled(False)
        self.add_character_button.setEnabled(False)
        self.zoom_in_button.setEnabled(False)
        self.zoom_out_button.setEnabled(False)
        self.reset_zoom_button.setEnabled(False)
        self.reset_positions_button.setEnabled(False)
        self.position_cards_button.setEnabled(False)
        
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
        self.new_view_button.setEnabled(True)
        self.save_view_button.setEnabled(True)
        self.add_character_button.setEnabled(True)
        self.zoom_in_button.setEnabled(True)
        self.zoom_out_button.setEnabled(True)
        self.reset_zoom_button.setEnabled(True)
        self.reset_positions_button.setEnabled(True)
        self.position_cards_button.setEnabled(True)
        
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
        
        # Create empty layout
        layout = {}
        
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
            
            layout[str(character_id)] = {"x": x, "y": y}
        
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
        """Load a specific view.
        
        Args:
            view_id: ID of the view
        """
        print(f"\nDEBUG: Loading view {view_id}")
        
        # Get view data
        view = get_story_board_view(self.db_conn, view_id)
        if not view:
            print("DEBUG: Could not find view data")
            return
        
        print(f"DEBUG: Retrieved view data: {view}")
        
        # Set current view
        self.current_view_id = view_id
        
        # Reset view transform and scene
        print("DEBUG: Resetting view transform")
        self.view.setTransform(QTransform())
        self.view.current_zoom = 1.0
        
        # Clear the scene and set its rect
        print("DEBUG: Clearing scene")
        self.scene.clear_board()
        self.scene.setSceneRect(0, 0, 10000, 10000)
        
        # Load layout
        layout = json.loads(view['layout_data'])
        print(f"DEBUG: Parsed layout data: {layout}")
        
        # Load characters
        characters = get_story_characters(self.db_conn, self.current_story_id)
        print(f"DEBUG: Found {len(characters)} characters")
        
        # Add character cards to the scene
        for character in characters:
            character_id = character['id']
            
            # Check if we have layout data for this character
            x, y = 0, 0
            if str(character_id) in layout:
                position = layout[str(character_id)]
                x = float(position.get('x', 0))
                y = float(position.get('y', 0))
                print(f"DEBUG: Found position for character {character_id}: ({x}, {y})")
            else:
                # Default position if none is specified
                x = 100 + (character_id % 5) * 200
                y = 100 + (character_id // 5) * 300
                print(f"DEBUG: Using default position for character {character_id}: ({x}, {y})")
            
            # Add the character card to the scene
            card = self.scene.add_character_card(character_id, character, x, y)
            
            # Verify position was set correctly
            pos = card.pos()
            print(f"DEBUG: Character {character_id} position after adding to scene: ({pos.x()}, {pos.y()})")
        
        # Update relationships
        for character in characters:
            relationships = get_character_relationships(self.db_conn, character['id'])
            for relationship in relationships:
                # Check if both characters are in the scene
                if relationship['source_id'] in self.scene.character_cards and relationship['target_id'] in self.scene.character_cards:
                    # Add the relationship line
                    self.scene.add_relationship_line(
                        relationship['id'],
                        relationship,
                        relationship['source_id'],
                        relationship['target_id']
                    )
        
        # Center the view on the characters
        print("DEBUG: Centering view on characters")
        self.view.center_on_characters()
        
        # Force the view to update
        print("DEBUG: Updating viewport")
        self.view.viewport().update()
        print("DEBUG: View loading complete")
    
    def on_view_changed(self, index: int) -> None:
        """Handle view selection change.
        
        Args:
            index: Index of the selected view
        """
        if index < 0:
            return
        
        view_id = self.view_selector.itemData(index)
        self.load_view(view_id)
    
    def on_new_view(self) -> None:
        """Handle new view button click."""
        if not self.current_story_id:
            return
        
        # Get view name
        name, ok = QInputDialog.getText(self, "New View", "Enter view name:")
        if not ok or not name:
            return
        
        # Create empty layout
        layout = {}
        
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
            
            layout[str(character_id)] = {"x": x, "y": y}
        
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
    
    def on_add_character(self) -> None:
        """Handle add character button click."""
        if not self.current_story_id:
            return
        
        # Import here to avoid circular imports
        from app.views.character_dialog import CharacterDialog
        
        # Create and show the character dialog
        dialog = CharacterDialog(self, self.current_story_id)
        if dialog.exec():
            character_data = dialog.get_character_data()
            
            # Create the character in the database
            from app.db_sqlite import create_character
            
            character_id = create_character(
                self.db_conn,
                name=character_data['name'],
                story_id=self.current_story_id,
                aliases=character_data['aliases'],
                is_main_character=character_data['is_main_character'],
                age_value=character_data['age_value'],
                age_category=character_data['age_category'],
                gender=character_data['gender'],
                avatar_path=character_data['avatar_path']
            )
            
            # Add the character to the current view
            if self.current_view_id:
                # Get the current layout
                from app.db_sqlite import get_story_board_view
                view = get_story_board_view(self.db_conn, self.current_view_id)
                layout = json.loads(view['layout_data'])
                
                # Add the character to the layout
                # Position it in the center of the view
                layout['characters'].append({
                    'id': character_id,
                    'x': 500,  # Center of the scene
                    'y': 300   # Center of the scene
                })
                
                # Update the layout
                from app.db_sqlite import update_story_board_view_layout
                update_story_board_view_layout(
                    self.db_conn,
                    self.current_view_id,
                    json.dumps(layout)
                )
                
                # Reload the view
                self.load_view(self.current_view_id)
            
            # Show a success message
            QMessageBox.information(
                self,
                "Character Created",
                f"Character '{character_data['name']}' created successfully."
            )
    
    def on_layout_changed(self) -> None:
        """Handle layout changed signal."""
        # Start auto-save timer
        self.auto_save_timer.start()
    
    def save_current_view(self) -> None:
        """Save the current view layout."""
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
        
        # Verify the save by reading back from the database
        view = get_story_board_view(self.db_conn, self.current_view_id)
        saved_layout = json.loads(view['layout_data'])
        
        # Show a brief status message
        main_window = self.window()
        if hasattr(main_window, 'status_bar'):
            main_window.status_bar.showMessage("View layout saved", 2000)
    
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