#!/usr/bin/env python3
"""
Menu Graphics Items for VN Flow Visualizer
==========================================

Custom PyQt6 graphics items for rendering menu containers with choice buttons.
"""

from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsTextItem, QStyleOptionGraphicsItem
from PyQt6.QtCore import QRectF, Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QFontMetrics


class ChoiceButtonGraphicsItem(QGraphicsRectItem):
    """
    Individual choice button within a menu container.
    
    Represents a single menu choice with text and visual styling.
    """
    
    def __init__(self, choice_text: str, choice_index: int, destination: Optional[str] = None, parent=None):
        super().__init__(parent)
        
        self.choice_text = choice_text
        self.choice_index = choice_index
        self.destination = destination
        
        # Visual settings
        self.button_width = 180
        self.button_height = 24
        self.font_size = 9
        
        # Set up the button rectangle
        self.setRect(0, 0, self.button_width, self.button_height)
        
        # Create text item for choice text
        self.text_item = QGraphicsTextItem(parent=self)
        self.text_item.setPlainText(self._format_choice_text())
        self._setup_text_styling()
        self._position_text()
        
        # Set up visual styling
        self._setup_visual_styling()
    
    def _format_choice_text(self) -> str:
        """Format the choice text to fit within button bounds."""
        max_length = 25  # Approximate characters that fit
        if len(self.choice_text) <= max_length:
            return self.choice_text
        return self.choice_text[:max_length-3] + "..."
    
    def _setup_text_styling(self):
        """Set up text font and styling."""
        font = QFont("Arial", self.font_size)
        font.setBold(False)
        self.text_item.setFont(font)
        self.text_item.setDefaultTextColor(QColor(40, 40, 40))  # Dark gray text
    
    def _position_text(self):
        """Center the text within the button."""
        text_rect = self.text_item.boundingRect()
        button_rect = self.rect()
        
        # Center horizontally and vertically
        x = (button_rect.width() - text_rect.width()) / 2
        y = (button_rect.height() - text_rect.height()) / 2
        
        self.text_item.setPos(x, y)
    
    def _setup_visual_styling(self):
        """Set up the visual appearance of the choice button."""
        # Light blue background for choice buttons
        self.setBrush(QBrush(QColor(220, 235, 255)))  # Light blue
        
        # Subtle border
        pen = QPen(QColor(180, 180, 180))
        pen.setWidth(1)
        self.setPen(pen)
        
        # Make it selectable but not movable
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)


class MenuContainerGraphicsItem(QGraphicsRectItem):
    """
    Menu container that holds multiple choice buttons.
    
    Visually represents a menu with all its choices laid out vertically.
    """
    
    def __init__(self, menu_id: str, menu_choices: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        
        self.menu_id = menu_id
        self.menu_choices = menu_choices
        self.choice_buttons: List[ChoiceButtonGraphicsItem] = []
        
        # Container dimensions (fixed size as requested)
        self.container_width = 200
        self.padding = 10
        self.choice_spacing = 4
        self.header_height = 25
        
        # Calculate container height based on number of choices
        choice_height = 24  # Height of each choice button
        total_choice_height = len(menu_choices) * choice_height + (len(menu_choices) - 1) * self.choice_spacing
        self.container_height = self.header_height + self.padding + total_choice_height + self.padding
        
        # Set up the container rectangle
        self.setRect(0, 0, self.container_width, self.container_height)
        
        # Create header text
        self._create_header()
        
        # Create choice buttons
        self._create_choice_buttons()
        
        # Set up visual styling
        self._setup_visual_styling()
    
    def _create_header(self):
        """Create the header text showing menu name."""
        self.header_item = QGraphicsTextItem(parent=self)
        
        # Format header text
        header_text = f"Menu: {self.menu_id.replace('_menu_container', '')}"
        self.header_item.setPlainText(header_text)
        
        # Style the header
        font = QFont("Arial", 10)
        font.setBold(True)
        self.header_item.setFont(font)
        self.header_item.setDefaultTextColor(QColor(60, 60, 60))
        
        # Position the header
        header_rect = self.header_item.boundingRect()
        x = (self.container_width - header_rect.width()) / 2
        y = 3
        self.header_item.setPos(x, y)
    
    def _create_choice_buttons(self):
        """Create choice button items for each menu choice."""
        start_y = self.header_height + self.padding
        
        for i, choice_data in enumerate(self.menu_choices):
            # Extract choice information
            choice_text = choice_data.get('text', f'Choice {i+1}')
            destination = choice_data.get('destination', None)
            
            # Create choice button
            choice_button = ChoiceButtonGraphicsItem(
                choice_text=choice_text,
                choice_index=i,
                destination=destination,
                parent=self
            )
            
            # Position the choice button
            x = self.padding
            y = start_y + i * (24 + self.choice_spacing)  # 24 = button height
            choice_button.setPos(x, y)
            
            self.choice_buttons.append(choice_button)
    
    def _setup_visual_styling(self):
        """Set up the visual appearance of the menu container."""
        # Gold/orange background for menu container (matching prototype)
        self.setBrush(QBrush(QColor(255, 215, 100)))  # Golden yellow
        
        # Darker border
        pen = QPen(QColor(200, 150, 50))
        pen.setWidth(2)
        self.setPen(pen)
        
        # Make it selectable but not movable by default
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)  # Allow moving the entire container
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)  # Enable geometry change notifications
        
        # Initialize connected edges list for edge following
        self.connected_edges = []
    
    def itemChange(self, change, value):
        """Handle item changes (like position updates) to update connected edges."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Notify connected edges to update when menu container moves
            if hasattr(self, 'connected_edges'):
                for edge in self.connected_edges:
                    edge.update_path()
        return super().itemChange(change, value)
    
    def get_choice_destinations(self) -> List[Optional[str]]:
        """Get list of destinations for all choices in this menu."""
        return [choice.destination for choice in self.choice_buttons]
    
    def get_menu_data(self) -> Dict[str, Any]:
        """Get comprehensive data about this menu container."""
        return {
            'menu_id': self.menu_id,
            'num_choices': len(self.choice_buttons),
            'choices': [
                {
                    'text': choice.choice_text,
                    'destination': choice.destination,
                    'index': choice.choice_index
                }
                for choice in self.choice_buttons
            ]
        }
    
    def get_choice_by_destination(self, destination: str) -> Optional[Dict[str, Any]]:
        """Find choice data by destination label."""
        for i, choice_data in enumerate(self.menu_choices):
            if choice_data.get('destination') == destination:
                return {
                    'text': choice_data.get('text', f'Choice {i+1}'),
                    'destination': destination,
                    'index': i,
                    'button': self.choice_buttons[i] if i < len(self.choice_buttons) else None
                }
        return None
    
    def calculate_choice_landing_zones(self) -> Dict[int, Dict[str, Any]]:
        """
        Calculate landing zones for each choice on the container borders.
        
        Returns:
            Dict mapping choice_index to landing zone data including boundaries
        """
        landing_zones = {}
        
        # Container boundaries in local coordinates
        container_rect = self.rect()
        left = container_rect.left()
        right = container_rect.right()
        top = container_rect.top()
        bottom = container_rect.bottom()
        
        # Header zone boundaries
        header_bottom = self.header_height
        choice_start_y = header_bottom + self.padding
        choice_height = 24
        
        for i, choice_button in enumerate(self.choice_buttons):
            choice_top = choice_start_y + i * (choice_height + self.choice_spacing)
            choice_bottom = choice_top + choice_height
            
            # Calculate landing zone boundaries for this choice
            # Each choice gets its vertical slice of the container sides
            landing_zones[i] = {
                'choice_text': choice_button.choice_text,
                'destination': choice_button.destination,
                'boundaries': {
                    # Left side zone
                    'left_top': (left, choice_top),
                    'left_bottom': (left, choice_bottom),
                    # Right side zone  
                    'right_top': (right, choice_top),
                    'right_bottom': (right, choice_bottom),
                    # Choice vertical range
                    'choice_y_min': choice_top,
                    'choice_y_max': choice_bottom,
                    'choice_center_y': choice_top + choice_height / 2
                }
            }
        
        # Header zone (for incoming connections)
        landing_zones['header'] = {
            'choice_text': 'Header Zone',
            'destination': None,
            'boundaries': {
                'left_top': (left, top),
                'left_bottom': (left, header_bottom),
                'right_top': (right, top), 
                'right_bottom': (right, header_bottom),
                'top_left': (left, top),
                'top_right': (right, top),
                'choice_y_min': top,
                'choice_y_max': header_bottom,
                'choice_center_y': header_bottom / 2
            }
        }
        
        return landing_zones
    
    def get_landing_point_for_choice(self, choice_index: int, connection_angle: float, 
                                   connection_target: str) -> Optional[QPointF]:
        """
        Get specific landing point for a choice based on connection angle.
        
        Args:
            choice_index: Index of the choice (0-based)
            connection_angle: Angle of incoming connection in radians
            connection_target: Target destination for validation
            
        Returns:
            QPointF of the landing point in local coordinates
        """
        landing_zones = self.calculate_choice_landing_zones()
        
        if choice_index not in landing_zones:
            return None
            
        zone = landing_zones[choice_index]
        boundaries = zone['boundaries']
        
        # Determine which side of the container to use based on angle
        # Angle 0 = right, π/2 = down, π = left, 3π/2 = up
        import math
        
        # Normalize angle to 0-2π range
        angle = connection_angle % (2 * math.pi)
        
        choice_center_y = boundaries['choice_center_y']
        
        # Choose side based on angle - prefer left/right over top/bottom for clarity
        if angle < math.pi / 4 or angle > 7 * math.pi / 4:
            # Connection coming from left -> land on right side
            return QPointF(boundaries['right_top'][0], choice_center_y)
        elif angle > 3 * math.pi / 4 and angle < 5 * math.pi / 4:
            # Connection coming from right -> land on left side  
            return QPointF(boundaries['left_top'][0], choice_center_y)
        elif angle >= math.pi / 4 and angle <= 3 * math.pi / 4:
            # Connection coming from above -> prefer side, but can use choice area
            # Use right side by default
            return QPointF(boundaries['right_top'][0], choice_center_y)
        else:
            # Connection coming from below -> prefer side
            # Use right side by default
            return QPointF(boundaries['right_top'][0], choice_center_y)
    
    def get_outgoing_connection_point(self, destination: str, target_position: Optional[QPointF] = None) -> Optional[QPointF]:
        """
        Get connection point for outgoing connection to specific destination.
        
        Args:
            destination: Target label destination
            target_position: Position of the target node (in scene coordinates) for optimal side selection
            
        Returns:
            QPointF of the connection point in local coordinates
        """
        # Find which choice this destination corresponds to
        choice_data = self.get_choice_by_destination(destination)
        if not choice_data:
            # If destination not found, use center-right as fallback
            container_rect = self.rect()
            return QPointF(container_rect.right(), container_rect.center().y())
        
        choice_index = choice_data['index']
        landing_zones = self.calculate_choice_landing_zones()
        
        if choice_index not in landing_zones:
            return None
            
        zone = landing_zones[choice_index]
        boundaries = zone['boundaries']
        choice_center_y = boundaries['choice_center_y']
        
        # Direction-aware side selection
        if target_position is not None:
            # Convert target position to local coordinates for comparison
            menu_center_scene = self.mapToScene(self.rect().center())
            
            # If target is to the left of the menu container, use left side
            if target_position.x() < menu_center_scene.x():
                return QPointF(boundaries['left_top'][0], choice_center_y)
            else:
                # If target is to the right or same position, use right side
                return QPointF(boundaries['right_top'][0], choice_center_y)
        else:
            # Fallback: use right side if no target position provided
            return QPointF(boundaries['right_top'][0], choice_center_y) 