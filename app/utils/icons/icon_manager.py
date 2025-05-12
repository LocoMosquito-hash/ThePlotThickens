#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Icon Manager for The Plot Thickens application.

This module provides a centralized way to manage and access Tabler icons
throughout the application.
"""

import os
import logging
from typing import Optional, Literal, Dict, Any, Union
from PyQt6.QtGui import QIcon, QColor, QPixmap, QImage
from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QStyle, QApplication

# Try to import pytablericons first (preferred)
try:
    from pytablericons import TablerIcons, OutlineIcon, FilledIcon
    HAS_PYTABLERICONS = True
    logging.info("pytablericons package found. Using TablerIcons for icons.")
except ImportError:
    HAS_PYTABLERICONS = False
    logging.warning("pytablericons package not found.")

    # If pytablericons is not available, try tabler-qicon as fallback
    try:
        from tablerqicon import TablerQIcon
        HAS_TABLER_QICON = True
        logging.info("tabler-qicon package found. Using TablerQIcon for icons.")
    except ImportError:
        HAS_TABLER_QICON = False
        logging.warning("tabler-qicon package not found. Using Qt standard icons as fallback.")


class IconManager:
    """
    Manages application icons using Tabler Icons.
    
    This class provides a centralized way to access and customize icons
    throughout the application, with consistent styling.
    """
    
    def __init__(self):
        """Initialize the icon manager."""
        self._cached_icons: Dict[str, QIcon] = {}
        self._current_theme: Literal["dark", "light"] = "dark"
        
        # Default colors for icons based on theme
        self._theme_colors = {
            "dark": "#ffffff",  # White for dark theme
            "light": "#000000"  # Black for light theme
        }
        
        # Variables to track which icon library is being used
        self._using_pytablericons = False
        self._using_tabler_qicon = False
        
        # Initialize pytablericons if available (preferred)
        if HAS_PYTABLERICONS:
            try:
                # Nothing to initialize for pytablericons, just set flag
                self._using_pytablericons = True
                logging.info("Using pytablericons for icon management")
            except Exception as e:
                logging.warning(f"Failed to initialize pytablericons: {str(e)}")
                self._using_pytablericons = False
        
        # Initialize tabler-qicon if pytablericons is not available
        if not self._using_pytablericons and HAS_TABLER_QICON:
            try:
                self._tabler = TablerQIcon(
                    color=self._theme_colors[self._current_theme],
                    size=24,
                    stroke_width=1.5
                )
                self._using_tabler_qicon = True
                logging.info("Using tabler-qicon for icon management")
            except Exception as e:
                logging.warning(f"Failed to initialize TablerQIcon: {str(e)}")
                self._using_tabler_qicon = False
        
        # Log which icon system we're using
        if not self._using_pytablericons and not self._using_tabler_qicon:
            logging.warning("No Tabler icons library available. Using Qt standard icons as fallback.")
    
    def set_theme(self, theme: Literal["dark", "light"]) -> None:
        """
        Set the theme for icons.
        
        Args:
            theme: The theme ("dark" or "light")
        """
        if theme not in ["dark", "light"]:
            raise ValueError("Theme must be 'dark' or 'light'")
        
        self._current_theme = theme
        
        # Update tabler-qicon with new theme color if using it
        if self._using_tabler_qicon:
            try:
                self._tabler = TablerQIcon(
                    color=self._theme_colors[self._current_theme],
                    size=24,
                    stroke_width=1.5
                )
            except Exception as e:
                logging.warning(f"Failed to update TablerQIcon theme: {str(e)}")
        
        # Clear cached icons to force regeneration with new theme
        self._cached_icons.clear()
    
    def get_icon(self, icon_name: str) -> QIcon:
        """
        Get an icon by name.
        
        Args:
            icon_name: The name of the icon to retrieve
            
        Returns:
            QIcon instance for the requested icon
        """
        # Check cache first
        cache_key = f"{icon_name}_{self._current_theme}"
        if cache_key in self._cached_icons:
            return self._cached_icons[cache_key]
        
        try:
            icon = self._load_icon(icon_name)
            self._cached_icons[cache_key] = icon
            return icon
        except Exception as e:
            logging.warning(f"Error loading icon '{icon_name}': {str(e)}")
            return self._get_fallback_icon(icon_name)
    
    def _load_icon(self, icon_name: str) -> QIcon:
        """
        Load an icon by name using the available icon library.
        
        Args:
            icon_name: The name of the icon to load
            
        Returns:
            QIcon instance
        """
        # Try pytablericons first if available (preferred)
        if self._using_pytablericons:
            try:
                # Convert icon name to uppercase for OutlineIcon format
                outline_icon_name = icon_name.upper()
                
                # Handle hyphen to underscore conversion
                outline_icon_name = outline_icon_name.replace("-", "_")
                
                # Try to get the icon from OutlineIcon enum
                try:
                    # Get outline icon (most common)
                    outline_icon = getattr(OutlineIcon, outline_icon_name)
                    icon = TablerIcons.load(
                        outline_icon, 
                        size=24, 
                        color=self._theme_colors[self._current_theme],
                        stroke_width=1.5
                    )
                    
                    # Convert Pillow Image to QIcon
                    return self._pil_to_qicon(icon)
                    
                except (AttributeError, TypeError):
                    # Try filled icon as fallback
                    try:
                        filled_icon = getattr(FilledIcon, outline_icon_name)
                        icon = TablerIcons.load(
                            filled_icon, 
                            size=24, 
                            color=self._theme_colors[self._current_theme]
                        )
                        
                        # Convert Pillow Image to QIcon
                        return self._pil_to_qicon(icon)
                        
                    except (AttributeError, TypeError):
                        # Neither outline nor filled icon found
                        logging.debug(f"Icon '{icon_name}' not found in pytablericons")
                        return self._get_fallback_icon(icon_name)
            
            except Exception as e:
                logging.warning(f"Error loading icon '{icon_name}' from pytablericons: {str(e)}")
                # Fall through to other methods
        
        # Try tabler-qicon if pytablericons failed
        if self._using_tabler_qicon:
            try:
                # Get the icon from TablerQIcon
                icon = getattr(self._tabler, icon_name, None)
                if icon is not None:
                    return icon
                else:
                    logging.debug(f"Icon '{icon_name}' not found in TablerQIcon")
                    return self._get_fallback_icon(icon_name)
            except Exception as e:
                logging.warning(f"Error accessing TablerQIcon '{icon_name}': {str(e)}")
                return self._get_fallback_icon(icon_name)
        
        # If no Tabler icons library is available, use fallback
        return self._get_fallback_icon(icon_name)
    
    def _pil_to_qicon(self, pil_image) -> QIcon:
        """
        Convert a PIL/Pillow Image to a QIcon.
        
        Args:
            pil_image: PIL Image object
            
        Returns:
            QIcon object
        """
        try:
            # Use PyQt6-specific method if available
            if hasattr(pil_image, 'toqpixmap'):
                # If the pil_image object already has a toqpixmap method (from pytablericons)
                pixmap = pil_image.toqpixmap()
                icon = QIcon(pixmap)
                return icon
            
            # Standard conversion for regular PIL images
            from PyQt6.QtGui import QImage
            
            # Convert to RGBA mode to ensure alpha channel
            img = pil_image.convert("RGBA")
            
            # Get image data and create QImage
            data = img.tobytes("raw", "RGBA")
            qimage = QImage(
                data,
                img.width,
                img.height,
                QImage.Format.Format_RGBA8888
            )
            
            # Create pixmap and icon
            pixmap = QPixmap.fromImage(qimage)
            icon = QIcon(pixmap)
            return icon
            
        except Exception as e:
            logging.error(f"Error converting PIL image to QIcon: {str(e)}")
            # Create a fallback icon
            blank_icon = QIcon()
            blank_pixmap = QPixmap(QSize(24, 24))
            blank_pixmap.fill(QColor(0, 0, 0, 0))  # Transparent
            blank_icon.addPixmap(blank_pixmap)
            return blank_icon
    
    def _get_fallback_icon(self, icon_name: str) -> QIcon:
        """
        Get a fallback icon when the requested icon is not available.
        
        Args:
            icon_name: The name of the originally requested icon
            
        Returns:
            QIcon instance from built-in Qt resources
        """
        # Map common icon names to Qt standard icons
        style = QApplication.style()
        
        # Map of common Tabler icon names to Qt standard icons
        icon_map = {
            "check": QStyle.StandardPixmap.SP_DialogApplyButton,
            "x": QStyle.StandardPixmap.SP_DialogCancelButton,
            "alert_triangle": QStyle.StandardPixmap.SP_MessageBoxWarning,
            "alert_circle": QStyle.StandardPixmap.SP_MessageBoxCritical,
            "info_circle": QStyle.StandardPixmap.SP_MessageBoxInformation,
            "help": QStyle.StandardPixmap.SP_MessageBoxQuestion,
            "arrow_back": QStyle.StandardPixmap.SP_ArrowBack,
            "arrow_forward": QStyle.StandardPixmap.SP_ArrowForward,
            "chevron_left": QStyle.StandardPixmap.SP_ArrowLeft,
            "chevron_right": QStyle.StandardPixmap.SP_ArrowRight,
            "chevron_up": QStyle.StandardPixmap.SP_ArrowUp,
            "chevron_down": QStyle.StandardPixmap.SP_ArrowDown,
            "trash": QStyle.StandardPixmap.SP_TrashIcon,
            "device_floppy": QStyle.StandardPixmap.SP_DialogSaveButton,
            "folder": QStyle.StandardPixmap.SP_DirIcon,
            "folder_open": QStyle.StandardPixmap.SP_DirOpenIcon,
            "file": QStyle.StandardPixmap.SP_FileIcon,
            "home": QStyle.StandardPixmap.SP_DirHomeIcon,
            "refresh": QStyle.StandardPixmap.SP_BrowserReload,
            "x_circle": QStyle.StandardPixmap.SP_DialogCloseButton,
            "player_play": QStyle.StandardPixmap.SP_MediaPlay,
            "player_pause": QStyle.StandardPixmap.SP_MediaPause,
            "player_stop": QStyle.StandardPixmap.SP_MediaStop,
            # Add moon/sun for theme toggle
            "moon": QStyle.StandardPixmap.SP_ToolBarHorizontalExtensionButton,
            "sun": QStyle.StandardPixmap.SP_ToolBarVerticalExtensionButton,
            "settings": QStyle.StandardPixmap.SP_FileDialogDetailedView,
            "user": QStyle.StandardPixmap.SP_DesktopIcon,
            "edit": QStyle.StandardPixmap.SP_FileDialogContentsView,
            "plus": QStyle.StandardPixmap.SP_FileDialogNewFolder,
            "minus": QStyle.StandardPixmap.SP_DialogResetButton,
            "calendar": QStyle.StandardPixmap.SP_FileDialogInfoView,
        }
        
        # Use mapped standard icon if available, or a default icon if not
        try:
            if icon_name in icon_map:
                return style.standardIcon(icon_map[icon_name])
            else:
                # Default to a generic icon if no mapping exists
                return style.standardIcon(QStyle.StandardPixmap.SP_TitleBarMenuButton)
        except Exception as e:
            logging.warning(f"Error getting standard icon for '{icon_name}': {str(e)}")
            # Last resort fallback - create a simple blank icon
            blank_icon = QIcon()
            blank_pixmap = QPixmap(QSize(24, 24))
            blank_pixmap.fill(QColor(0, 0, 0, 0))  # Transparent
            blank_icon.addPixmap(blank_pixmap)
            return blank_icon
    
    def get_all_icon_names(self) -> list:
        """
        Get a list of all available icon names.
        
        Returns:
            List of icon names
        """
        if self._using_pytablericons:
            try:
                # Get all OutlineIcon names and convert to lowercase
                return [name.lower() for name in dir(OutlineIcon) if not name.startswith('_')]
            except Exception as e:
                logging.warning(f"Error getting icon names from pytablericons: {str(e)}")
        
        if self._using_tabler_qicon:
            try:
                return TablerQIcon.get_icon_names()
            except Exception as e:
                logging.warning(f"Error getting icon names from tabler-qicon: {str(e)}")
        
        return []  # Empty list if no Tabler icons library is available


# Create a singleton instance for use throughout the application
icon_manager = IconManager() 