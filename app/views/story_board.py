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
    QGraphicsItemGroup, QToolBar, QSizePolicy, QGraphicsEllipseItem
)
from PyQt6.QtCore import Qt, QSize, QPointF, QRectF, QLineF, pyqtSignal, QTimer
from PyQt6.QtGui import (
    QPixmap, QImage, QColor, QPen, QBrush, QFont, QPainter, QPainterPath,
    QTransform, QCursor, QDrag, QMouseEvent, QWheelEvent, QKeyEvent
)

from app.db_sqlite import (
    get_story, get_story_characters, get_character_relationships,
    get_story_board_views, get_story_board_view, create_story_board_view,
    update_story_board_view_layout
)


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
        
        self.character_id = character_id
        self.character_data = character_data
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        
        # Create card components
        self.create_card()
        
        # Track connected relationships
        self.relationships: List[RelationshipLine] = []
    
    def create_card(self) -> None:
        """Create the card components."""
        # Card dimensions
        card_width = 150
        card_height = 200
        
        # Create card background
        self.background = QGraphicsRectItem(0, 0, card_width, card_height)
        self.background.setBrush(QBrush(QColor("#F5F5DC")))  # Beige color
        self.background.setPen(QPen(QColor("#000000"), 2))
        self.addToGroup(self.background)
        
        # Create pushpin
        pin_size = 20
        pin = QGraphicsEllipseItem(card_width / 2 - pin_size / 2, -pin_size / 2, pin_size, pin_size)
        pin.setBrush(QBrush(QColor("#FF0000")))  # Red color
        pin.setPen(QPen(QColor("#800000"), 1))  # Dark red border
        self.addToGroup(pin)
        
        # Create character name
        name = QGraphicsTextItem(self.character_data['name'])
        name.setPos(10, 10)
        name.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        name.setTextWidth(card_width - 20)
        self.addToGroup(name)
        
        # Create avatar placeholder or actual avatar
        avatar_rect = QGraphicsRectItem(10, 40, card_width - 20, card_height - 60)
        avatar_rect.setBrush(QBrush(QColor("#CCCCCC")))  # Gray color
        avatar_rect.setPen(QPen(QColor("#999999"), 1))  # Darker gray border
        self.addToGroup(avatar_rect)
        
        # If avatar exists, load it
        if self.character_data['avatar_path'] and os.path.exists(self.character_data['avatar_path']):
            try:
                pixmap = QPixmap(self.character_data['avatar_path'])
                if not pixmap.isNull():
                    avatar = QGraphicsPixmapItem(pixmap.scaled(
                        int(card_width - 20), int(card_height - 60),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    ))
                    avatar.setPos(10, 40)
                    self.addToGroup(avatar)
            except Exception as e:
                print(f"Error loading avatar: {e}")
        
        # Create character info
        info_text = ""
        if self.character_data['is_main_character']:
            info_text += "Main Character\n"
        
        if self.character_data['gender'] and self.character_data['gender'] != "NOT_SPECIFIED":
            info_text += f"Gender: {self.character_data['gender'].title()}\n"
        
        if self.character_data['age_value'] is not None:
            info_text += f"Age: {self.character_data['age_value']}\n"
        elif self.character_data['age_category']:
            info_text += f"Age: {self.character_data['age_category']}\n"
        
        if info_text:
            info = QGraphicsTextItem(info_text)
            info.setPos(10, card_height - 40)
            info.setFont(QFont("Arial", 8))
            info.setTextWidth(card_width - 20)
            self.addToGroup(info)
    
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        """Handle item changes.
        
        Args:
            change: Type of change
            value: New value
            
        Returns:
            Modified value
        """
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            # Update connected relationships
            for relationship in self.relationships:
                relationship.update_position()
        
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
        
        # Add actions
        edit_action = menu.addAction("Edit Character")
        delete_action = menu.addAction("Delete Character")
        
        # Show menu and handle actions
        action = menu.exec(event.screenPos())
        
        if action == edit_action:
            # TODO: Implement character editing
            QMessageBox.information(None, "Not Implemented", "Character editing is not yet implemented.")
        elif action == delete_action:
            # TODO: Implement character deletion
            QMessageBox.information(None, "Not Implemented", "Character deletion is not yet implemented.")


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
    
    def __init__(self, parent=None) -> None:
        """Initialize the story board scene.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Set scene properties
        self.setSceneRect(0, 0, 2000, 2000)
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
        layout = {
            "characters": [],
            "relationships": []
        }
        
        # Add character positions
        for character_id, card in self.character_cards.items():
            layout["characters"].append({
                "id": character_id,
                "x": card.x(),
                "y": card.y()
            })
        
        # Add relationship data
        for relationship_id, line in self.relationship_lines.items():
            layout["relationships"].append({
                "id": relationship_id,
                "color": line.pen().color().name(),
                "width": line.pen().width()
            })
        
        return layout
    
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Handle mouse press events.
        
        Args:
            event: Mouse press event
        """
        super().mousePressEvent(event)


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
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # Set up zoom
        self.zoom_factor = 1.15
        self.min_zoom = 0.1
        self.max_zoom = 10.0
        self.current_zoom = 1.0
    
    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handle wheel events for zooming.
        
        Args:
            event: Wheel event
        """
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Zoom with Ctrl+Wheel
            zoom_in = event.angleDelta().y() > 0
            
            if zoom_in:
                zoom_factor = self.zoom_factor
            else:
                zoom_factor = 1.0 / self.zoom_factor
            
            new_zoom = self.current_zoom * zoom_factor
            
            # Limit zoom level
            if self.min_zoom <= new_zoom <= self.max_zoom:
                self.current_zoom = new_zoom
                self.setTransform(QTransform().scale(self.current_zoom, self.current_zoom))
            
            event.accept()
        else:
            # Normal scrolling
            super().wheelEvent(event)


class StoryBoardWidget(QWidget):
    """Widget for the story board visualization."""
    
    def __init__(self, db_conn) -> None:
        """Initialize the story board widget.
        
        Args:
            db_conn: Database connection
        """
        super().__init__()
        
        self.db_conn = db_conn
        self.current_story_id: Optional[int] = None
        self.current_story_data: Optional[Dict[str, Any]] = None
        self.current_view_id: Optional[int] = None
        
        self.init_ui()
    
    def init_ui(self) -> None:
        """Set up the user interface."""
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        
        # Create view selector
        self.view_selector = QComboBox()
        self.view_selector.setMinimumWidth(200)
        self.view_selector.currentIndexChanged.connect(self.on_view_changed)
        toolbar.addWidget(QLabel("View:"))
        toolbar.addWidget(self.view_selector)
        toolbar.addSeparator()
        
        # Create view buttons
        self.new_view_button = QPushButton("New View")
        self.new_view_button.clicked.connect(self.on_new_view)
        toolbar.addWidget(self.new_view_button)
        
        self.save_view_button = QPushButton("Save View")
        self.save_view_button.clicked.connect(self.on_save_view)
        toolbar.addWidget(self.save_view_button)
        
        toolbar.addSeparator()
        
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
        
        main_layout.addWidget(toolbar)
        
        # Create graphics view
        self.scene = StoryBoardScene(self)
        self.view = StoryBoardView(self)
        self.view.setScene(self.scene)
        main_layout.addWidget(self.view)
        
        # Disable controls initially
        self.view_selector.setEnabled(False)
        self.new_view_button.setEnabled(False)
        self.save_view_button.setEnabled(False)
        self.zoom_in_button.setEnabled(False)
        self.zoom_out_button.setEnabled(False)
        self.reset_zoom_button.setEnabled(False)
    
    def set_story(self, story_id: int, story_data: Dict[str, Any]) -> None:
        """Set the current story.
        
        Args:
            story_id: ID of the story
            story_data: Story data
        """
        self.current_story_id = story_id
        self.current_story_data = story_data
        
        # Enable controls
        self.view_selector.setEnabled(True)
        self.new_view_button.setEnabled(True)
        self.save_view_button.setEnabled(True)
        self.zoom_in_button.setEnabled(True)
        self.zoom_out_button.setEnabled(True)
        self.reset_zoom_button.setEnabled(True)
        
        # Load views
        self.load_views()
    
    def load_views(self) -> None:
        """Load all views for the current story."""
        if not self.current_story_id:
            return
        
        # Get views
        views = get_story_board_views(self.db_conn, self.current_story_id)
        
        # Update view selector
        self.view_selector.clear()
        
        if views:
            for view in views:
                self.view_selector.addItem(view['name'], view['id'])
            
            # Select the first view
            self.view_selector.setCurrentIndex(0)
        else:
            # Create a default "Main" view without showing the input dialog
            self.create_default_view()
    
    def create_default_view(self) -> None:
        """Create a default 'Main' view for the story."""
        if not self.current_story_id:
            return
        
        # Create empty layout
        layout = {
            "characters": [],
            "relationships": []
        }
        
        # Get all characters
        characters = get_story_characters(self.db_conn, self.current_story_id)
        
        # Add characters to layout with default positions
        for i, character in enumerate(characters):
            # Arrange characters in a grid
            cols = max(1, int(math.sqrt(len(characters))))
            row = i // cols
            col = i % cols
            
            layout["characters"].append({
                "id": character['id'],
                "x": 100 + col * 200,
                "y": 100 + row * 250
            })
        
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
        # Get view data
        view = get_story_board_view(self.db_conn, view_id)
        if not view:
            return
        
        # Set current view
        self.current_view_id = view_id
        
        # Clear the scene
        self.scene.clear_board()
        
        # Load layout
        layout = json.loads(view['layout_data'])
        
        # Load characters
        characters = get_story_characters(self.db_conn, self.current_story_id)
        character_dict = {character['id']: character for character in characters}
        
        # Add character cards
        for character_data in layout.get('characters', []):
            character_id = character_data['id']
            if character_id in character_dict:
                self.scene.add_character_card(
                    character_id,
                    character_dict[character_id],
                    character_data.get('x', 0),
                    character_data.get('y', 0)
                )
        
        # Load relationships
        for character in characters:
            relationships = get_character_relationships(self.db_conn, character['id'])
            for relationship in relationships:
                # Only add relationships where this character is the source
                # to avoid adding the same relationship twice
                if relationship['source_id'] == character['id']:
                    # Find relationship in layout
                    relationship_layout = None
                    for rel_data in layout.get('relationships', []):
                        if rel_data['id'] == relationship['id']:
                            relationship_layout = rel_data
                            break
                    
                    # Update relationship data with layout data
                    if relationship_layout:
                        if 'color' in relationship_layout:
                            relationship['color'] = relationship_layout['color']
                        if 'width' in relationship_layout:
                            relationship['width'] = relationship_layout['width']
                    
                    # Add relationship line
                    self.scene.add_relationship_line(
                        relationship['id'],
                        relationship,
                        relationship['source_id'],
                        relationship['target_id']
                    )
    
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
        layout = {
            "characters": [],
            "relationships": []
        }
        
        # Get all characters
        characters = get_story_characters(self.db_conn, self.current_story_id)
        
        # Add characters to layout with default positions
        for i, character in enumerate(characters):
            # Arrange characters in a grid
            cols = max(1, int(math.sqrt(len(characters))))
            row = i // cols
            col = i % cols
            
            layout["characters"].append({
                "id": character['id'],
                "x": 100 + col * 200,
                "y": 100 + row * 250
            })
        
        # Create view
        view_id = create_story_board_view(
            self.db_conn,
            name=name,
            story_id=self.current_story_id,
            layout_data=json.dumps(layout)
        )
        
        # Reload views
        self.load_views()
        
        # Select the new view
        for i in range(self.view_selector.count()):
            if self.view_selector.itemData(i) == view_id:
                self.view_selector.setCurrentIndex(i)
                break
    
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