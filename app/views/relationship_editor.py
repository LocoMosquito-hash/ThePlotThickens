#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Relationship Editor for The Plot Thickens application.

This module defines a dialog for creating and editing relationships between characters.
"""

from typing import List, Dict, Any, Optional, Tuple, Set

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, 
    QListWidgetItem, QLabel, QWidget, QFrame, QSizePolicy, QMessageBox,
    QToolTip
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint, QRect, QEvent, QTimer
from PyQt6.QtGui import (
    QPixmap, QIcon, QColor, QPalette, QPainter, QPen, QPolygon,
    QMouseEvent, QFont, QBrush
)

from app.db_sqlite import get_story_characters, get_character_relationships


class RelationshipCountBadge(QLabel):
    """A badge that shows the number of relationships a character has."""
    
    def __init__(self, count: int, parent=None):
        """Initialize the relationship count badge.
        
        Args:
            count: The number of relationships to display
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Set the text to the count
        self.setText(str(count))
        
        # Set size
        self.setFixedSize(24, 24)
        
        # Set alignment
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Set font
        font = QFont()
        font.setBold(True)
        self.setFont(font)
        
        # Set text color
        self.setStyleSheet("color: white;")
        
        # Hide if count is 0
        self.setVisible(count > 0)
    
    def paintEvent(self, event):
        """Paint the badge as a circle with red background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Set brush for circle
        painter.setBrush(QBrush(QColor("red")))
        painter.setPen(Qt.PenStyle.NoPen)  # No border
        
        # Draw circle
        painter.drawEllipse(0, 0, self.width(), self.height())
        
        # Call parent to draw text
        super().paintEvent(event)


class CharacterItemWidget(QWidget):
    """Custom widget for character list items."""
    
    def __init__(self, character_data: Dict[str, Any], relationship_count: int = 0, parent=None):
        """Initialize the character item widget.
        
        Args:
            character_data: Character data dictionary
            relationship_count: Number of relationships the character has
            parent: Parent widget
        """
        super().__init__(parent)
        self.character_data = character_data
        self.relationship_count = relationship_count
        self.relationship_details = []
        
        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Create avatar placeholder
        self.avatar_label = QLabel()
        self.avatar_label.setMinimumSize(40, 40)
        self.avatar_label.setMaximumSize(40, 40)
        self.avatar_label.setStyleSheet("background-color: #D8C6F3; border-radius: 5px;")
        
        # Load avatar if available
        if character_data.get('avatar_path'):
            pixmap = QPixmap(character_data['avatar_path'])
            if not pixmap.isNull():
                # Scale the pixmap to fit
                pixmap = pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.avatar_label.setPixmap(pixmap)
        
        layout.addWidget(self.avatar_label)
        
        # Create name label
        self.name_label = QLabel(character_data['name'])
        self.name_label.setStyleSheet("color: white; font-weight: bold;")
        layout.addWidget(self.name_label)
        
        # Add spacer to push badge to the right
        layout.addStretch()
        
        # Create relationship count badge
        self.badge = RelationshipCountBadge(relationship_count)
        layout.addWidget(self.badge)
        
        # Set the background color for the widget
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#555555"))
        self.setPalette(palette)
        
        # Set fixed height for consistency
        self.setFixedHeight(50)
        
        # Install event filter for handling hover events
        self.installEventFilter(self)
    
    def update_relationship_count(self, count: int) -> None:
        """Update the relationship count badge.
        
        Args:
            count: The new relationship count
        """
        self.relationship_count = count
        self.badge.setText(str(count))
        self.badge.setVisible(count > 0)
    
    def set_relationship_details(self, details: List[Dict[str, Any]]) -> None:
        """Set the relationship details for hover display.
        
        Args:
            details: List of relationship details
        """
        self.relationship_details = details
    
    def show_tooltip(self, pos: QPoint, text: str) -> None:
        """Show tooltip at the specified position.
        
        Args:
            pos: Position to show tooltip
            text: Tooltip text
        """
        QToolTip.showText(pos, text)
    
    def eventFilter(self, obj, event) -> bool:
        """Event filter for handling hover events.
        
        Args:
            obj: Object that triggered the event
            event: Event to be filtered
            
        Returns:
            bool: True if the event was handled, False otherwise
        """
        if obj == self and event.type() == QEvent.Type.Enter and self.relationship_count > 0:
            # Show tooltip with relationship details
            if self.relationship_details:
                tooltip_text = "<b>Relationships:</b><br>"
                # Limit to 5 items
                for i, relationship in enumerate(self.relationship_details[:5]):
                    tooltip_text += f"• {relationship['name']}: {relationship['type']}<br>"
                
                # Show tooltip at the right position without timeout
                self.show_tooltip(
                    self.mapToGlobal(QPoint(self.badge.x(), self.badge.y() + self.badge.height())), 
                    tooltip_text
                )
            return True
            
        elif obj == self and event.type() == QEvent.Type.Leave:
            # Hide tooltip when mouse leaves
            QToolTip.hideText()
            return True
            
        return super().eventFilter(obj, event)


class CharacterListItem(QListWidgetItem):
    """An item in the character list that displays a character's avatar and name."""
    
    def __init__(self, character_data: Dict[str, Any]):
        """Initialize the character list item.
        
        Args:
            character_data: Character data dictionary
        """
        super().__init__()
        self.character_data = character_data
        self.character_id = character_data['id']
        
        # Set size hint for the item
        self.setSizeHint(QSize(0, 50))


class Arrow:
    """A class representing an arrow drawn between two characters."""
    
    def __init__(self, source_id: int, target_id: int, source_pos: QPoint, target_pos: QPoint):
        """Initialize an arrow.
        
        Args:
            source_id: ID of the source character
            target_id: ID of the target character
            source_pos: Starting position of the arrow
            target_pos: Ending position of the arrow
        """
        self.source_id = source_id
        self.target_id = target_id
        self.source_pos = source_pos
        self.target_pos = target_pos
    
    def __eq__(self, other):
        if not isinstance(other, Arrow):
            return False
        return (self.source_id == other.source_id and 
                self.target_id == other.target_id)


class ArrowCanvas(QWidget):
    """Canvas for drawing relationship arrows between characters."""
    
    def __init__(self, parent=None):
        """Initialize the arrow canvas.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.arrows: List[Arrow] = []
        self.temp_arrow: Optional[Tuple[QPoint, QPoint]] = None
        
        # Set background to transparent but allow mouse events
        self.setMouseTracking(True)
        # Make sure we can receive mouse events from other widgets
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        
    def add_arrow(self, source_id: int, target_id: int, source_pos: QPoint, target_pos: QPoint) -> None:
        """Add a new arrow.
        
        Args:
            source_id: ID of the source character
            target_id: ID of the target character
            source_pos: Starting position of the arrow
            target_pos: Ending position of the arrow
        """
        # Check if arrow already exists
        for arrow in self.arrows:
            if arrow.source_id == source_id and arrow.target_id == target_id:
                return
        
        # Create and add the new arrow
        self.arrows.append(Arrow(source_id, target_id, source_pos, target_pos))
        self.update()  # Request repaint
    
    def set_temp_arrow(self, source_pos: QPoint, target_pos: QPoint) -> None:
        """Set a temporary arrow that follows the mouse.
        
        Args:
            source_pos: Starting position of the arrow
            target_pos: Ending position of the arrow
        """
        self.temp_arrow = (source_pos, target_pos)
        self.update()  # Request repaint
    
    def clear_temp_arrow(self) -> None:
        """Clear the temporary arrow."""
        self.temp_arrow = None
        self.update()  # Request repaint
    
    def paintEvent(self, event) -> None:
        """Draw the arrows on the canvas.
        
        Args:
            event: Paint event
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create a pen for the arrows
        pen = QPen(QColor("red"), 4)
        painter.setPen(pen)
        
        # Draw permanent arrows
        for arrow in self.arrows:
            self._draw_arrow(painter, arrow.source_pos, arrow.target_pos)
        
        # Draw temporary arrow if exists
        if self.temp_arrow:
            self._draw_arrow(painter, self.temp_arrow[0], self.temp_arrow[1])
    
    def _draw_arrow(self, painter: QPainter, start_pos: QPoint, end_pos: QPoint) -> None:
        """Draw an arrow from start_pos to end_pos.
        
        Args:
            painter: QPainter object
            start_pos: Starting position of the arrow
            end_pos: Ending position of the arrow
        """
        # Draw the line
        painter.drawLine(start_pos, end_pos)
        
        # Calculate the arrowhead
        arrow_length = 15
        
        # Vector from end to start
        dx = start_pos.x() - end_pos.x()
        dy = start_pos.y() - end_pos.y()
        
        # Normalize the vector
        length = (dx**2 + dy**2)**0.5
        if length > 0:
            dx /= length
            dy /= length
        
        # Calculate arrowhead points
        p1 = QPoint(
            int(end_pos.x() + arrow_length * (dx * 0.866 - dy * 0.5)),
            int(end_pos.y() + arrow_length * (dx * 0.5 + dy * 0.866))
        )
        p2 = QPoint(
            int(end_pos.x() + arrow_length * (dx * 0.866 + dy * 0.5)),
            int(end_pos.y() + arrow_length * (-dx * 0.5 + dy * 0.866))
        )
        
        # Draw the arrowhead
        arrowhead = QPolygon([end_pos, p1, p2])
        painter.setBrush(QColor("red"))
        painter.drawPolygon(arrowhead)


class RelationshipEditorDialog(QDialog):
    """Dialog for creating and editing relationships between characters."""
    
    def __init__(self, db_conn, story_id: int, parent=None):
        """Initialize the relationship editor dialog.
        
        Args:
            db_conn: Database connection
            story_id: ID of the story
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.story_id = story_id
        
        # Store the characters data
        self.characters = get_story_characters(db_conn, story_id)
        
        # Sort characters alphabetically by name
        self.characters.sort(key=lambda x: x['name'])
        
        # Arrow drawing state
        self.is_drawing = False
        self.source_item = None
        self.source_list = None
        self.arrow_start_pos = None
        
        # Initialize relationship data
        self.character_relationships = {}
        
        self.load_relationships()
        
        self.init_ui()
    
    def load_relationships(self) -> None:
        """Load relationship data for all characters."""
        for character in self.characters:
            character_id = character['id']
            # Get all relationships for this character
            relationships = get_character_relationships(self.db_conn, character_id)
            
            # Store relationship data - all relationships for count, but limit details to 5
            self.character_relationships[character_id] = {
                'count': len(relationships),
                'details': relationships[:5]  # Only keep the 5 most recent for display
            }
    
    def refresh_relationship_counts(self) -> None:
        """Refresh the relationship counts for all characters in both lists."""
        # Reload relationship data
        self.load_relationships()
        
        # Update counts in left list
        for i in range(self.left_characters_list.count()):
            item = self.left_characters_list.item(i)
            character_id = item.character_id
            
            widget = self.left_characters_list.itemWidget(item)
            if widget and character_id in self.character_relationships:
                relationship_data = self.character_relationships[character_id]
                widget.update_relationship_count(relationship_data['count'])
                widget.set_relationship_details(relationship_data['details'])
        
        # Update counts in right list
        for i in range(self.right_characters_list.count()):
            item = self.right_characters_list.item(i)
            character_id = item.character_id
            
            widget = self.right_characters_list.itemWidget(item)
            if widget and character_id in self.character_relationships:
                relationship_data = self.character_relationships[character_id]
                widget.update_relationship_count(relationship_data['count'])
                widget.set_relationship_details(relationship_data['details'])
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Edit Relationship")
        self.resize(900, 600)  # Set a reasonable size
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create horizontal layout for the character lists
        lists_layout = QHBoxLayout()
        
        # Left characters list
        left_list_container = QWidget()
        left_list_layout = QVBoxLayout(left_list_container)
        
        left_list_label = QLabel("List A:")
        left_list_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        left_list_layout.addWidget(left_list_label)
        
        self.left_characters_list = QListWidget()
        self.left_characters_list.setStyleSheet("""
            QListWidget {
                background-color: #333333;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                border-bottom: 1px solid #444444;
                padding: 2px;
            }
            QListWidget::item:selected {
                background-color: #4a4a6a;
            }
            QListWidget::item:hover {
                background-color: #444466;
            }
        """)
        self.left_characters_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        left_list_layout.addWidget(self.left_characters_list)
        
        # Create arrow canvas in the middle
        self.arrow_canvas = ArrowCanvas()
        self.arrow_canvas.setMinimumWidth(200)
        
        # Right characters list
        right_list_container = QWidget()
        right_list_layout = QVBoxLayout(right_list_container)
        
        right_list_label = QLabel("List B:")
        right_list_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        right_list_layout.addWidget(right_list_label)
        
        self.right_characters_list = QListWidget()
        self.right_characters_list.setStyleSheet("""
            QListWidget {
                background-color: #333333;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                border-bottom: 1px solid #444444;
                padding: 2px;
            }
            QListWidget::item:selected {
                background-color: #4a4a6a;
            }
            QListWidget::item:hover {
                background-color: #444466;
            }
        """)
        self.right_characters_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        right_list_layout.addWidget(self.right_characters_list)
        
        # Set fixed width for the list containers to ensure they're the same size
        left_list_container.setMinimumWidth(250)
        right_list_container.setMinimumWidth(250)
        
        # Add the lists to the horizontal layout
        lists_layout.addWidget(left_list_container)
        lists_layout.addWidget(self.arrow_canvas, 1)  # Add canvas with stretch
        lists_layout.addWidget(right_list_container)
        
        # Add the lists layout to the main layout
        main_layout.addLayout(lists_layout)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setMinimumWidth(100)
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept)
        self.save_button.setMinimumWidth(100)
        
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.save_button)
        
        main_layout.addLayout(buttons_layout)
        
        # Populate the character lists
        self.populate_character_lists()
        
        # Set dialog to be modal
        self.setModal(True)
        
        # Install event filter on list widgets to handle mouse events
        self.left_characters_list.viewport().installEventFilter(self)
        self.right_characters_list.viewport().installEventFilter(self)
        
        # Install event filter on the dialog itself to handle mouse movements and cancellation
        self.installEventFilter(self)
        
        # Also make the dialog track mouse movements
        self.setMouseTracking(True)
    
    def populate_character_lists(self):
        """Populate the character lists with character data."""
        # Clear the lists first
        self.left_characters_list.clear()
        self.right_characters_list.clear()
        
        # Add characters to both lists
        for character in self.characters:
            character_id = character['id']
            relationship_count = 0
            relationship_details = []
            
            # Get relationship data if available
            if character_id in self.character_relationships:
                relationship_count = self.character_relationships[character_id]['count']
                relationship_details = self.character_relationships[character_id]['details']
            
            # Create list items for each list
            left_item = CharacterListItem(character)
            right_item = CharacterListItem(character)
            
            # Add to respective lists
            self.left_characters_list.addItem(left_item)
            self.right_characters_list.addItem(right_item)
            
            # Create and set custom widgets
            left_widget = CharacterItemWidget(character, relationship_count)
            left_widget.set_relationship_details(relationship_details)
            
            right_widget = CharacterItemWidget(character, relationship_count)
            right_widget.set_relationship_details(relationship_details)
            
            # Set as item widgets
            self.left_characters_list.setItemWidget(left_item, left_widget)
            self.right_characters_list.setItemWidget(right_item, right_widget)
    
    def eventFilter(self, obj, event) -> bool:
        """Event filter to handle mouse events on list widgets.
        
        Args:
            obj: Object that triggered the event
            event: Event to be filtered
            
        Returns:
            bool: True if the event was handled, False otherwise
        """
        # Handle mouse events
        if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            if obj in [self.left_characters_list.viewport(), self.right_characters_list.viewport()]:
                print(f"DEBUG: Mouse press in {'left' if obj == self.left_characters_list.viewport() else 'right'} list")
                return self.handle_mouse_press(obj, event)
                
        elif event.type() == QEvent.Type.MouseMove:
            if self.is_drawing:
                print(f"DEBUG: Mouse move event detected, is_drawing={self.is_drawing}")
                return self.handle_mouse_move(event)
                
        elif event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
            if self.is_drawing:
                print(f"DEBUG: Mouse release event detected, is_drawing={self.is_drawing}")
                return self.handle_mouse_release(event)
                
        elif event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.RightButton:
            if self.is_drawing:
                self.cancel_drawing()
                return True
        
        return super().eventFilter(obj, event)
    
    def get_edge_point(self, list_widget: QListWidget, item: QListWidgetItem, is_left_list: bool) -> Tuple[QPoint, QPoint]:
        """Get the edge point of a list item for arrow attachment.
        
        Args:
            list_widget: The list widget containing the item
            item: The list item
            is_left_list: Whether the list is the left list
            
        Returns:
            Tuple containing local point and global point
        """
        item_rect = list_widget.visualItemRect(item)
        
        if is_left_list:
            # For left list, use the right edge
            local_point = QPoint(
                item_rect.right(),
                item_rect.top() + item_rect.height() // 2
            )
        else:
            # For right list, use the left edge
            local_point = QPoint(
                item_rect.left(),
                item_rect.top() + item_rect.height() // 2
            )
        
        # Convert to global point
        global_point = list_widget.viewport().mapToGlobal(local_point)
        
        print(f"DEBUG: Edge point for {'left' if is_left_list else 'right'} list item:")
        print(f"  Item rect: {item_rect.x()}, {item_rect.y()}, {item_rect.width()}x{item_rect.height()}")
        print(f"  Local point: {local_point.x()}, {local_point.y()}")
        print(f"  Global point: {global_point.x()}, {global_point.y()}")
        
        return local_point, global_point
    
    def handle_mouse_press(self, obj, event: QMouseEvent) -> bool:
        """Handle mouse press events to start drawing an arrow.
        
        Args:
            obj: Object that triggered the event
            event: Mouse event
            
        Returns:
            bool: True if the event was handled, False otherwise
        """
        # Determine which list widget was clicked
        if obj == self.left_characters_list.viewport():
            list_widget = self.left_characters_list
            is_left_list = True
            source_list = "left"
            target_list = self.right_characters_list
        else:
            list_widget = self.right_characters_list
            is_left_list = False
            source_list = "right"
            target_list = self.left_characters_list
        
        # Get the item at the click position
        click_pos = event.position().toPoint()
        item = list_widget.itemAt(click_pos)
        print(f"DEBUG: Click position in {source_list} list: {click_pos.x()}, {click_pos.y()}")
        
        if item:
            print(f"DEBUG: Clicked on item: {item.character_data['name']} (ID: {item.character_id})")
            
            # Start drawing arrow
            self.is_drawing = True
            self.source_item = item
            self.source_list = source_list
            
            # Disable the same character in the target list to prevent self-relationships
            self.disable_matching_character(item.character_id, target_list)
            
            # Get the edge point for this item
            local_point, global_point = self.get_edge_point(list_widget, item, is_left_list)
            
            # Convert to canvas coordinates for the start position
            self.arrow_start_pos = self.arrow_canvas.mapFromGlobal(global_point)
            print(f"DEBUG: Arrow start position in canvas: {self.arrow_start_pos.x()}, {self.arrow_start_pos.y()}")
            
            # Initial target position is the current mouse position mapped to the canvas
            mouse_pos = self.mapToGlobal(event.position().toPoint())
            canvas_mouse_pos = self.arrow_canvas.mapFromGlobal(mouse_pos)
            print(f"DEBUG: Initial mouse position in canvas: {canvas_mouse_pos.x()}, {canvas_mouse_pos.y()}")
            
            # Set the temporary arrow with initial positions
            self.arrow_canvas.set_temp_arrow(self.arrow_start_pos, canvas_mouse_pos)
            
            # Grab the mouse to ensure we get all mouse events even when the cursor leaves our widget
            self.grabMouse()
            
            return True
        else:
            print("DEBUG: No item clicked")
        
        return False
    
    def disable_matching_character(self, character_id: int, target_list: QListWidget) -> None:
        """Disable the matching character in the target list to prevent self-relationships.
        
        Args:
            character_id: ID of the character to disable
            target_list: The target list widget
        """
        # Find and disable the matching character
        for i in range(target_list.count()):
            item = target_list.item(i)
            if item.character_id == character_id:
                # Make the item non-selectable and visually disabled
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                # Apply a disabled visual style to the item widget
                widget = target_list.itemWidget(item)
                if widget:
                    widget.setStyleSheet("background-color: #333333; opacity: 0.5;")
                    widget.setEnabled(False)
                break
    
    def enable_all_characters(self) -> None:
        """Re-enable all characters in both lists."""
        # Re-enable all items in both lists
        for list_widget in [self.left_characters_list, self.right_characters_list]:
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                # Restore the item's flags
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEnabled)
                # Restore the item widget's style
                widget = list_widget.itemWidget(item)
                if widget:
                    widget.setStyleSheet("")
                    widget.setEnabled(True)
    
    def handle_mouse_move(self, event: QMouseEvent) -> bool:
        """Handle mouse move events to update the temporary arrow.
        
        Args:
            event: Mouse event
            
        Returns:
            bool: True if the event was handled, False otherwise
        """
        if self.is_drawing and self.arrow_start_pos:
            # Map the current mouse position to the canvas coordinates
            mouse_pos = self.mapToGlobal(event.position().toPoint())
            canvas_mouse_pos = self.arrow_canvas.mapFromGlobal(mouse_pos)
            
            # Print only occasionally to avoid flooding the console
            if event.position().toPoint().x() % 20 == 0:  # Print every 20 pixels moved horizontally
                print(f"DEBUG: Mouse move - Canvas pos: {canvas_mouse_pos.x()}, {canvas_mouse_pos.y()}")
                print(f"DEBUG: Source list: {self.source_list}, Arrow start: {self.arrow_start_pos.x()}, {self.arrow_start_pos.y()}")
            
            # Update the temporary arrow
            self.arrow_canvas.set_temp_arrow(self.arrow_start_pos, canvas_mouse_pos)
            return True
        
        return False
    
    def handle_mouse_release(self, event: QMouseEvent) -> bool:
        """Handle mouse release events to finalize drawing an arrow.
        
        Args:
            event: Mouse event
            
        Returns:
            bool: True if the event was handled, False otherwise
        """
        # Release the mouse grab if we were drawing
        if self.is_drawing:
            self.releaseMouse()
            
        if not self.is_drawing:
            print("DEBUG: handle_mouse_release called but is_drawing is False")
            return False
        
        print(f"DEBUG: Mouse release - Processing arrow completion")
        print(f"DEBUG: Source list: {self.source_list}, Source item: {self.source_item.character_data['name'] if self.source_item else 'None'}")
        
        # Determine target list (opposite of source list)
        if self.source_list == "left":
            target_list = self.right_characters_list
            is_target_left_list = False
        else:
            target_list = self.left_characters_list
            is_target_left_list = True
        
        # Get the global release position
        release_global_pos = self.mapToGlobal(event.position().toPoint())
        release_list_pos = target_list.viewport().mapFromGlobal(release_global_pos)
        
        print(f"DEBUG: Release global pos: {release_global_pos.x()}, {release_global_pos.y()}")
        print(f"DEBUG: Release list pos: {release_list_pos.x()}, {release_list_pos.y()}")
        
        # Check if release is over an item in the target list
        target_item = target_list.itemAt(release_list_pos)
        
        if target_item:
            print(f"DEBUG: Target item found: {target_item.character_data['name']} (ID: {target_item.character_id})")
            
            # Get the edge point for the target item
            _, target_global_point = self.get_edge_point(target_list, target_item, is_target_left_list)
            target_canvas_pos = self.arrow_canvas.mapFromGlobal(target_global_point)
            
            print(f"DEBUG: Target canvas pos: {target_canvas_pos.x()}, {target_canvas_pos.y()}")
            
            # Add the permanent arrow
            source_id = self.source_item.character_id
            target_id = target_item.character_id
            
            self.arrow_canvas.add_arrow(
                source_id, 
                target_id, 
                self.arrow_start_pos, 
                target_canvas_pos
            )
            
            # Show the relationship details dialog
            self.show_relationship_placeholder(
                source_id=source_id,
                source_name=self.source_item.character_data['name'],
                target_id=target_id,
                target_name=target_item.character_data['name']
            )
            
            # Refresh relationship counts after adding a relationship
            self.refresh_relationship_counts()
        else:
            print("DEBUG: No target item found at release position")
        
        # Re-enable all characters
        self.enable_all_characters()
        
        # Clear the temporary arrow and reset state
        self.arrow_canvas.clear_temp_arrow()
        self.is_drawing = False
        self.source_item = None
        self.arrow_start_pos = None
        
        return True
    
    def show_relationship_placeholder(self, source_id: int, source_name: str, target_id: int, target_name: str) -> None:
        """Show the relationship details dialog.
        
        Opens the RelationshipDetailsDialog to define the relationship type between two characters.
        
        Args:
            source_id: ID of the source character
            source_name: Name of the source character
            target_id: ID of the target character
            target_name: Name of the target character
        """
        from app.views.relationship_details import RelationshipDetailsDialog
        
        # Create the relationship details dialog
        dialog = RelationshipDetailsDialog(
            self.db_conn,
            source_id,
            source_name,
            target_id,
            target_name,
            self
        )
        
        # Show the dialog (modal)
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            # Get the selected relationship types
            forward_rel, backward_rel = dialog.get_selected_relationships()
            
            # This is where we would save the relationships to the database
            # in a future implementation
            print(f"DEBUG: Forward relationship: {forward_rel}")
            print(f"DEBUG: Backward relationship: {backward_rel}")
            
            # For now, just show a message box confirming the relationships
            if forward_rel or backward_rel:
                message = "Relationships selected:\n\n"
                if forward_rel:
                    message += f"{source_name} is {target_name}'s: {forward_rel}\n"
                if backward_rel:
                    message += f"{target_name} is {source_name}'s: {backward_rel}\n"
                
                QMessageBox.information(
                    self,
                    "Relationships Defined",
                    message
                )
    
    def cancel_drawing(self) -> None:
        """Cancel the current arrow drawing operation."""
        if self.is_drawing:
            # Release mouse grab if we were drawing
            self.releaseMouse()
            
            # Re-enable all characters
            self.enable_all_characters()
            
            self.arrow_canvas.clear_temp_arrow()
            self.is_drawing = False
            self.source_item = None
            self.arrow_start_pos = None 