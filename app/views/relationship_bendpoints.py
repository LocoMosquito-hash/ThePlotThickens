#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Relationship bendpoints for The Plot Thickens application.

This module defines classes for managing bendpoints on relationship lines
in the story board visualization.
"""

from typing import Optional, List, Dict, Any, Tuple, TYPE_CHECKING
import math

from PyQt6.QtWidgets import (
    QGraphicsEllipseItem, QGraphicsItem, QMenu, QGraphicsSceneContextMenuEvent,
    QGraphicsSceneMouseEvent, QGraphicsSceneHoverEvent, QMessageBox
)
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QColor, QPen, QBrush, QPainterPath

# Conditional imports to avoid circular imports
if TYPE_CHECKING:
    from app.views.story_board import RelationshipLine


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
            # Update the relationship line as we drag
            self.relationship_line.update_path()
        
        return super().itemChange(change, value)
    
    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent) -> None:
        """Handle context menu events.
        
        Args:
            event: Context menu event
        """
        menu = QMenu()
        remove_action = menu.addAction("Remove Bendpoint")
        
        action = menu.exec(event.screenPos())
        
        if action == remove_action:
            self.remove_from_database()
            self.relationship_line.remove_bendpoint(self)
    
    def save_to_database(self) -> None:
        """Save the bendpoint to the database."""
        # Get the database connection from the scene
        scene = self.relationship_line.scene()
        if not scene or not hasattr(scene, 'db_conn'):
            print(f"ERROR: Could not save bendpoint - no scene or db connection")
            return
        
        try:
            if self.bendpoint_id:
                # Update existing bendpoint
                query = """
                UPDATE relationship_bendpoints 
                SET position = ?, x_offset = ?, y_offset = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """
                params = (self.position, self.x_offset, self.y_offset, self.bendpoint_id)
                print(f"Updating bendpoint ID: {self.bendpoint_id}, position: {self.position}, offsets: ({self.x_offset}, {self.y_offset})")
            else:
                # Insert new bendpoint
                query = """
                INSERT INTO relationship_bendpoints 
                (relationship_id, position, x_offset, y_offset)
                VALUES (?, ?, ?, ?)
                """
                # Get the relationship ID from the primary relationship
                # Always use the first relationship in the group for consistency
                relationship_id = self.relationship_line.relationships[0]['id']
                print(f"Saving new bendpoint for relationship ID: {relationship_id}, position: {self.position}, offsets: ({self.x_offset}, {self.y_offset})")
                params = (relationship_id, self.position, self.x_offset, self.y_offset)
            
            cursor = scene.db_conn.cursor()
            cursor.execute(query, params)
            
            # Get the bendpoint ID if it was a new insertion
            if not self.bendpoint_id:
                self.bendpoint_id = cursor.lastrowid
                print(f"New bendpoint created with ID: {self.bendpoint_id}")
            
            scene.db_conn.commit()
        except Exception as e:
            print(f"ERROR saving bendpoint: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def remove_from_database(self) -> None:
        """Remove the bendpoint from the database."""
        if not self.bendpoint_id:
            print(f"Cannot remove bendpoint from database - no bendpoint ID")
            return
            
        # Get the database connection from the scene
        scene = self.relationship_line.scene()
        if not scene or not hasattr(scene, 'db_conn'):
            print(f"ERROR: Could not remove bendpoint - no scene or db connection")
            return
        
        try:
            print(f"Removing bendpoint ID {self.bendpoint_id} from database")
            query = "DELETE FROM relationship_bendpoints WHERE id = ?"
            cursor = scene.db_conn.cursor()
            cursor.execute(query, (self.bendpoint_id,))
            rows_affected = cursor.rowcount
            scene.db_conn.commit()
            print(f"Deleted bendpoint ID {self.bendpoint_id} - {rows_affected} rows affected")
        except Exception as e:
            print(f"ERROR removing bendpoint: {str(e)}")
            import traceback
            traceback.print_exc()


def load_bendpoints(relationship_line: 'RelationshipLine', relationship_id: int) -> List[BendPoint]:
    """Load bendpoints for a relationship from the database.
    
    Args:
        relationship_line: The relationship line to add bendpoints to
        relationship_id: ID of the relationship
        
    Returns:
        List of created bendpoints
    """
    bendpoints = []
    
    # Get the database connection from the scene
    scene = relationship_line.scene()
    if not scene or not hasattr(scene, 'db_conn'):
        print(f"ERROR: No scene or db_conn found for relationship line")
        return bendpoints
    
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
                    relationship_line=relationship_line,
                    position=position,
                    x_offset=x_offset,
                    y_offset=y_offset,
                    bendpoint_id=bendpoint_id
                )
                
                # Add to the list
                bendpoints.append(bendpoint)
        
        if len(bendpoints) > 0:
            # Get line info
            start, end = relationship_line.get_base_line_points()
            print(f"RELATIONSHIP LINE: Start=({start.x()}, {start.y()}), End=({end.x()}, {end.y()})")
            print(f"RELATIONSHIP SOURCE: ID={relationship_line.source_card.character_id}")
            print(f"RELATIONSHIP TARGET: ID={relationship_line.target_card.character_id}")
            
    except Exception as e:
        print(f"ERROR loading bendpoints: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return bendpoints 