#!/usr/bin/env python3
"""
Menu Graphics Items for VN Flow Visualizer
==========================================

Custom PyQt6 graphics items for rendering menu containers with choice buttons.
"""

from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsTextItem, QStyleOptionGraphicsItem
from PyQt6.QtCore import QRectF, Qt, pyqtSignal
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