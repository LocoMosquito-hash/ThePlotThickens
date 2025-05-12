#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Character Badge for The Plot Thickens application.

This module provides a customizable character badge widget that can display
character information in a compact, visually appealing format.
"""

import os
from typing import Optional, Dict, Any, List, Union, Callable, Tuple

from PyQt6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout, QSizePolicy,
    QFrame, QToolButton, QPushButton
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QEvent
from PyQt6.QtGui import QPixmap, QIcon, QColor, QPalette, QMouseEvent

from app.utils.icons.icon_manager import icon_manager


class StatusIcon:
    """Represents a status icon that can be added to a character badge."""
    
    def __init__(
        self, 
        icon_name: str,
        tooltip: str,
        color: Optional[Union[str, QColor]] = None,
        size: int = 16,
        is_visible: bool = True,
        on_click: Optional[Callable] = None
    ):
        """Initialize a status icon.
        
        Args:
            icon_name: Name of the icon from the icon manager
            tooltip: Tooltip text when hovering over the icon
            color: Optional color override for the icon
            size: Icon size in pixels
            is_visible: Whether the icon is initially visible
            on_click: Optional callback function when the icon is clicked
        """
        self.icon_name = icon_name
        self.tooltip = tooltip
        self.color = color
        self.size = size
        self.is_visible = is_visible
        self.on_click = on_click
        self.button: Optional[QToolButton] = None


class CharacterBadge(QFrame):
    """
    A customizable badge widget displaying character information.
    
    The badge can display a character's avatar, name, and optional status icons.
    It can be configured in different sizes and styles to fit various use cases
    throughout the application.
    """
    
    # Signals
    clicked = pyqtSignal(int)  # Emitted when the badge is clicked, passes character ID
    icon_clicked = pyqtSignal(int, str)  # Emitted when an icon is clicked, passes character ID and icon name
    
    # Predefined badge sizes
    SIZE_TINY = "tiny"        # 24x24 - Just the avatar or initials
    SIZE_SMALL = "small"      # 32x32 - Small avatar with very minimal text
    SIZE_MEDIUM = "medium"    # 48x48 - Avatar with name, no status icons
    SIZE_LARGE = "large"      # 64x64 - Avatar with name and basic icons
    SIZE_XLARGE = "xlarge"    # 96x96 - Full feature badge with all content
    
    # Badge styles
    STYLE_FLAT = "flat"           # Flat appearance, no borders, transparent background
    STYLE_OUTLINED = "outlined"   # Thin border, transparent background
    STYLE_FILLED = "filled"       # Filled background with optional border
    STYLE_SHADOWED = "shadowed"   # Shadowed appearance for more depth
    
    def __init__(
        self, 
        character_id: int,
        character_data: Dict[str, Any],
        size: str = SIZE_MEDIUM,
        style: str = STYLE_OUTLINED,
        show_avatar: bool = True,
        show_name: bool = True,
        show_main_character: bool = True,
        parent: Optional[QWidget] = None
    ):
        """Initialize the character badge.
        
        Args:
            character_id: The ID of the character
            character_data: Dictionary containing character data
            size: Badge size, one of the SIZE_* constants or custom dimensions
            style: Badge style, one of the STYLE_* constants
            show_avatar: Whether to show the character's avatar
            show_name: Whether to show the character's name
            show_main_character: Whether to show an indicator if the character is a main character
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.character_id = character_id
        self.character_data = character_data
        self.badge_size = size
        self.badge_style = style
        self.show_avatar = show_avatar
        self.show_name = show_name
        self.show_main_character = show_main_character
        
        # Status icons
        self.status_icons: List[StatusIcon] = []
        
        # UI elements
        self.avatar_label: Optional[QLabel] = None
        self.name_label: Optional[QLabel] = None
        self.icons_layout: Optional[QHBoxLayout] = None
        self.main_layout: Optional[QHBoxLayout] = None
        
        # Set up the badge
        self._init_ui()
        self._setup_style()
        
        # Make the badge clickable
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def _init_ui(self) -> None:
        """Initialize the user interface components."""
        # Create the main layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(4, 4, 4, 4)
        self.main_layout.setSpacing(4)
        
        # Get pixel sizes based on the badge size
        avatar_size, font_size, badge_height = self._get_size_values()
        
        # Create the avatar label if needed
        if self.show_avatar:
            self.avatar_label = QLabel()
            self.avatar_label.setFixedSize(avatar_size, avatar_size)
            self.avatar_label.setScaledContents(True)
            self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Load the avatar image or set default
            self._set_avatar_image(avatar_size)
            
            self.main_layout.addWidget(self.avatar_label)
        
        # Create vertical layout for name and icons if showing the name
        if self.show_name and self.badge_size not in [self.SIZE_TINY, self.SIZE_SMALL]:
            content_layout = QVBoxLayout()
            content_layout.setContentsMargins(0, 0, 0, 0)
            content_layout.setSpacing(2)
            
            # Create the name label
            self.name_label = QLabel(self.character_data.get('name', 'Unknown'))
            self.name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            font = self.name_label.font()
            font.setPointSize(font_size)
            self.name_label.setFont(font)
            content_layout.addWidget(self.name_label)
            
            # Create a layout for status icons
            self.icons_layout = QHBoxLayout()
            self.icons_layout.setContentsMargins(0, 0, 0, 0)
            self.icons_layout.setSpacing(2)
            self.icons_layout.addStretch()
            content_layout.addLayout(self.icons_layout)
            
            # Add the content layout to the main layout
            self.main_layout.addLayout(content_layout)
            self.main_layout.addStretch()
        elif self.show_name and self.badge_size == self.SIZE_SMALL:
            # For small size, just add the name next to the avatar
            self.name_label = QLabel(self.character_data.get('name', 'Unknown'))
            self.name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            font = self.name_label.font()
            font.setPointSize(font_size)
            self.name_label.setFont(font)
            self.main_layout.addWidget(self.name_label)
        
        # Add main character indicator if needed and the character is a main character
        if self.show_main_character and self.character_data.get('is_main_character', False):
            self._add_main_character_indicator()
        
        # Set a fixed height based on content
        self.setFixedHeight(badge_height)
        
        # Set minimum width based on content
        min_width = avatar_size + 8  # avatar + margins
        if self.show_name and self.badge_size not in [self.SIZE_TINY]:
            min_width += 60  # name width
        self.setMinimumWidth(min_width)
    
    def _get_size_values(self) -> Tuple[int, int, int]:
        """Get pixel values for the badge based on the size.
        
        Returns:
            Tuple of (avatar_size, font_size, badge_height)
        """
        if self.badge_size == self.SIZE_TINY:
            return 24, 7, 24
        elif self.badge_size == self.SIZE_SMALL:
            return 24, 8, 32
        elif self.badge_size == self.SIZE_MEDIUM:
            return 32, 9, 40
        elif self.badge_size == self.SIZE_LARGE:
            return 48, 10, 56
        elif self.badge_size == self.SIZE_XLARGE:
            return 64, 11, 72
        else:
            # Default to medium
            return 32, 9, 40
    
    def _set_avatar_image(self, avatar_size: int) -> None:
        """Set the avatar image.
        
        Args:
            avatar_size: Size of the avatar in pixels
        """
        if not self.avatar_label:
            return
            
        avatar_path = self.character_data.get('avatar_path')
        if avatar_path and os.path.exists(avatar_path):
            # Load and scale the avatar image
            pixmap = QPixmap(avatar_path)
            scaled_pixmap = pixmap.scaled(
                avatar_size, avatar_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.avatar_label.setPixmap(scaled_pixmap)
        else:
            # Display initials as a fallback
            name = self.character_data.get('name', 'Unknown')
            initials = ''.join([word[0] for word in name.split() if word])[:2].upper()
            
            self.avatar_label.setText(initials)
            
            # Style the initials label to look like an avatar
            self.avatar_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {self._get_name_color(name)};
                    color: white;
                    border-radius: {avatar_size // 2}px;
                    font-weight: bold;
                    font-size: {avatar_size // 2}px;
                }}
            """)
    
    def _get_name_color(self, name: str) -> str:
        """Generate a consistent color based on the character's name.
        
        Args:
            name: Character name
            
        Returns:
            Hex color string
        """
        # Use a simple hash function to generate a consistent color
        name_hash = sum(ord(c) for c in name)
        hue = (name_hash % 360) / 360.0
        
        # Convert HSV to RGB (simple implementation)
        # Using saturation and value that ensure good contrast with white text
        h = hue * 6
        i = int(h)
        f = h - i
        
        p = 0.5  # Value
        q = 0.5 * (1 - 0.7 * f)
        t = 0.5 * (1 - 0.7 * (1 - f))
        
        r, g, b = 0, 0, 0
        if i == 0 or i == 6:
            r, g, b = p, t, 0.2
        elif i == 1:
            r, g, b = q, p, 0.2
        elif i == 2:
            r, g, b = 0.2, p, t
        elif i == 3:
            r, g, b = 0.2, q, p
        elif i == 4:
            r, g, b = t, 0.2, p
        elif i == 5:
            r, g, b = p, 0.2, q
        
        # Convert to hex
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
    
    def _setup_style(self) -> None:
        """Apply the selected style to the badge."""
        # Base style
        base_style = """
            QFrame {
                padding: 2px;
            }
        """
        
        # Apply specific style based on the badge style
        if self.badge_style == self.STYLE_FLAT:
            self.setStyleSheet(base_style + """
                QFrame {
                    border: none;
                    background-color: transparent;
                }
            """)
        elif self.badge_style == self.STYLE_OUTLINED:
            self.setStyleSheet(base_style + """
                QFrame {
                    border: 1px solid #aaaaaa;
                    border-radius: 5px;
                    background-color: transparent;
                }
            """)
        elif self.badge_style == self.STYLE_FILLED:
            self.setStyleSheet(base_style + """
                QFrame {
                    border: 1px solid #aaaaaa;
                    border-radius: 5px;
                    background-color: #f5f5f5;
                }
            """)
        elif self.badge_style == self.STYLE_SHADOWED:
            self.setStyleSheet(base_style + """
                QFrame {
                    border: 1px solid #aaaaaa;
                    border-radius: 5px;
                    background-color: #f5f5f5;
                    margin: 2px;
                }
            """)
            # Add drop shadow effect
            self.setGraphicsEffect(self._create_shadow_effect())
    
    def _create_shadow_effect(self) -> 'QGraphicsEffect':
        """Create a shadow effect for the badge.
        
        Returns:
            A QGraphicsEffect object for the shadow
        """
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 70))
        shadow.setOffset(2, 2)
        return shadow
    
    def _add_main_character_indicator(self) -> None:
        """Add an indicator that this is a main character."""
        # Create a star icon
        if self.badge_size in [self.SIZE_MEDIUM, self.SIZE_LARGE, self.SIZE_XLARGE]:
            self.add_status_icon("star", "Main Character", "#FFD700")
        else:
            # For smaller badges, add a small icon at the bottom right
            mc_indicator = QLabel()
            mc_indicator.setFixedSize(12, 12)
            mc_indicator.setPixmap(
                icon_manager.get_icon("star").pixmap(QSize(12, 12))
            )
            mc_indicator.setToolTip("Main Character")
            self.main_layout.addWidget(mc_indicator)
    
    def add_status_icon(
        self, 
        icon_name: str, 
        tooltip: str,
        color: Optional[Union[str, QColor]] = None,
        size: int = 16,
        is_visible: bool = True,
        on_click: Optional[Callable] = None
    ) -> Optional[StatusIcon]:
        """Add a status icon to the badge.
        
        Args:
            icon_name: Name of the icon from the icon manager
            tooltip: Tooltip text when hovering over the icon
            color: Optional color override for the icon
            size: Icon size in pixels
            is_visible: Whether the icon is initially visible
            on_click: Optional callback function when the icon is clicked
            
        Returns:
            The created StatusIcon object or None if the icon couldn't be added
        """
        # Check if we have an icons layout
        if not hasattr(self, 'icons_layout') or not self.icons_layout:
            return None
        
        # Create the status icon
        status_icon = StatusIcon(icon_name, tooltip, color, size, is_visible, on_click)
        
        # Create a button for the icon
        button = QToolButton()
        button.setFixedSize(size, size)
        button.setIconSize(QSize(size - 2, size - 2))
        button.setIcon(icon_manager.get_icon(icon_name))
        button.setToolTip(tooltip)
        button.setStyleSheet("QToolButton { border: none; background-color: transparent; }")
        
        # Set icon color if specified
        if color:
            # For now, we just apply a stylesheet
            if isinstance(color, str):
                color_str = color
            else:
                color_str = f"rgb({color.red()}, {color.green()}, {color.blue()})"
                
            button.setStyleSheet(f"QToolButton {{ border: none; color: {color_str}; }}")
        
        # Set visibility
        button.setVisible(is_visible)
        
        # Connect the click signal
        if on_click:
            button.clicked.connect(
                lambda: on_click(self.character_id, icon_name)
            )
        
        # Add to layout
        self.icons_layout.insertWidget(0, button)
        
        # Store the button in the status icon
        status_icon.button = button
        
        # Add to our list
        self.status_icons.append(status_icon)
        
        return status_icon
    
    def remove_status_icon(self, icon_name: str) -> bool:
        """Remove a status icon from the badge.
        
        Args:
            icon_name: Name of the icon to remove
            
        Returns:
            True if the icon was removed, False otherwise
        """
        for i, icon in enumerate(self.status_icons):
            if icon.icon_name == icon_name and icon.button:
                # Remove the button from the layout
                self.icons_layout.removeWidget(icon.button)
                icon.button.deleteLater()
                
                # Remove from our list
                self.status_icons.pop(i)
                return True
        
        return False
    
    def get_status_icon(self, icon_name: str) -> Optional[StatusIcon]:
        """Get a status icon by name.
        
        Args:
            icon_name: Name of the icon to get
            
        Returns:
            The StatusIcon object or None if not found
        """
        for icon in self.status_icons:
            if icon.icon_name == icon_name:
                return icon
        return None
    
    def show_status_icon(self, icon_name: str, visible: bool = True) -> None:
        """Show or hide a status icon.
        
        Args:
            icon_name: Name of the icon to show/hide
            visible: Whether the icon should be visible
        """
        icon = self.get_status_icon(icon_name)
        if icon and icon.button:
            icon.is_visible = visible
            icon.button.setVisible(visible)
    
    def update_from_data(self, character_data: Dict[str, Any]) -> None:
        """Update the badge with new character data.
        
        Args:
            character_data: New character data
        """
        self.character_data = character_data
        
        # Update avatar if it exists
        if self.show_avatar and self.avatar_label:
            avatar_size = self.avatar_label.width()
            self._set_avatar_image(avatar_size)
        
        # Update name if it exists
        if self.show_name and self.name_label:
            self.name_label.setText(character_data.get('name', 'Unknown'))
        
        # Update main character indicator if needed
        is_main_character = character_data.get('is_main_character', False)
        main_char_icon = self.get_status_icon("star")
        
        if is_main_character and not main_char_icon and self.show_main_character:
            # Add main character indicator
            self._add_main_character_indicator()
        elif not is_main_character and main_char_icon:
            # Remove main character indicator
            self.remove_status_icon("star")
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press events.
        
        Args:
            event: Mouse event
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.character_id)
        super().mousePressEvent(event)
    
    def enterEvent(self, event: QEvent) -> None:
        """Handle mouse enter events.
        
        Args:
            event: Event object
        """
        # Highlight the badge on hover
        if self.badge_style == self.STYLE_FLAT:
            self.setStyleSheet("""
                QFrame {
                    border: 1px solid #aaaaaa;
                    border-radius: 5px;
                    background-color: rgba(200, 200, 200, 30);
                    padding: 2px;
                }
            """)
        elif self.badge_style == self.STYLE_OUTLINED:
            self.setStyleSheet("""
                QFrame {
                    border: 1px solid #666666;
                    border-radius: 5px;
                    background-color: rgba(200, 200, 200, 30);
                    padding: 2px;
                }
            """)
        elif self.badge_style == self.STYLE_FILLED:
            self.setStyleSheet("""
                QFrame {
                    border: 1px solid #666666;
                    border-radius: 5px;
                    background-color: #e0e0e0;
                    padding: 2px;
                }
            """)
        
        super().enterEvent(event)
    
    def leaveEvent(self, event: QEvent) -> None:
        """Handle mouse leave events.
        
        Args:
            event: Event object
        """
        # Restore original style
        self._setup_style()
        super().leaveEvent(event)


# Factory function to create character badges
def create_character_badge(
    character_id: int,
    character_data: Dict[str, Any],
    size: str = CharacterBadge.SIZE_MEDIUM,
    style: str = CharacterBadge.STYLE_OUTLINED,
    show_avatar: bool = True,
    show_name: bool = True,
    show_main_character: bool = True,
    parent: Optional[QWidget] = None
) -> CharacterBadge:
    """Create a character badge.
    
    Args:
        character_id: The ID of the character
        character_data: Dictionary containing character data
        size: Badge size, one of the CharacterBadge.SIZE_* constants
        style: Badge style, one of the CharacterBadge.STYLE_* constants
        show_avatar: Whether to show the character's avatar
        show_name: Whether to show the character's name
        show_main_character: Whether to show an indicator if the character is a main character
        parent: Parent widget
        
    Returns:
        A CharacterBadge instance
    """
    return CharacterBadge(
        character_id,
        character_data,
        size,
        style,
        show_avatar,
        show_name,
        show_main_character,
        parent
    ) 