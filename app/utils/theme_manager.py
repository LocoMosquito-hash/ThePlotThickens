#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Theme manager for The Plot Thickens application.

This module provides utilities for managing and switching application themes.
"""

import os
import json
from typing import Literal, Optional

from qt_material import apply_stylesheet
from PyQt6.QtWidgets import QApplication

# Import our icon manager reference
from app.utils.icons.icon_manager import icon_manager


class ThemeManager:
    """Manages application themes using Qt-Material."""
    
    CONFIG_FILE = "theme_config.json"
    ThemeType = Literal["dark", "light", "auto"]
    DEFAULT_DENSITY_SCALE: float = 0.85
    
    # Qt-Material theme mappings
    THEME_MAP = {
        "dark": "dark_blue.xml",
        "light": "light_blue.xml",
        "auto": "dark_blue.xml"  # Default to dark for auto
    }
    
    def __init__(self, app_dir: str):
        """Initialize the theme manager.
        
        Args:
            app_dir: The application directory path
        """
        self.app_dir = app_dir
        self.config_path = os.path.join(app_dir, self.CONFIG_FILE)
        self.current_theme = self._load_theme_config()
        self.density_scale: float = self.DEFAULT_DENSITY_SCALE
    
    def _load_theme_config(self) -> ThemeType:
        """Load theme configuration from file.
        
        Returns:
            The current theme setting
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    theme = config.get("theme", "dark")
                    if theme in ["dark", "light", "auto"]:
                        return theme
            except Exception:
                pass
        
        # Default to dark theme
        return "dark"
    
    def _save_theme_config(self) -> None:
        """Save current theme configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump({"theme": self.current_theme}, f)
        except Exception as e:
            print(f"Error saving theme configuration: {e}")
    
    def set_density_scale(self, scale: float) -> None:
        """Set the density scale used by Qt-Material.
        
        Args:
            scale: Multiplier applied to widget metrics; values under 1.0 create denser UIs.
        """
        if scale <= 0:
            raise ValueError("Density scale must be greater than zero.")
        self.density_scale = scale
    
    def apply_theme(self, theme: Optional[ThemeType] = None) -> None:
        """Apply the specified theme or the current theme if none specified.
        
        Args:
            theme: The theme to apply ("dark", "light", or "auto")
        """
        if theme is not None and theme in ["dark", "light", "auto"]:
            self.current_theme = theme
            self._save_theme_config()
        
        # Apply the theme using Qt-Material
        app = QApplication.instance()
        if app:
            extra_options = {
                "density_scale": self.density_scale,
            }
            apply_stylesheet(
                app,
                theme=self.THEME_MAP[self.current_theme],
                extra=extra_options,
            )
            
            # Apply custom CSS to make UI elements more compact
            extra_css = """
            * {
                font-size: 10pt;
            }
            QPushButton {
                padding: 4px 8px;
                font-size: 10pt;
            }
            QComboBox {
                padding: 3px 5px;
                font-size: 10pt;
            }
            QCheckBox, QRadioButton {
                font-size: 10pt;
            }
            QLineEdit, QTextEdit, QPlainTextEdit {
                padding: 4px;
                font-size: 10pt;
            }
            QTreeView, QListView, QTableView {
                font-size: 10pt;
            }
            """
            
            # Append our custom styles to the existing stylesheet
            current_stylesheet = app.styleSheet()
            app.setStyleSheet(current_stylesheet + extra_css)
        
        # Update icons to match the current theme
        if self.current_theme == "auto":
            # For auto theme, we need to determine if it's currently dark or light
            # This would depend on system settings, but for simplicity we'll default to dark
            icon_manager.set_theme("dark")
        else:
            icon_manager.set_theme(self.current_theme)
    
    def toggle_theme(self) -> None:
        """Toggle between light and dark themes."""
        if self.current_theme == "dark":
            self.apply_theme("light")
        else:
            self.apply_theme("dark")
    
    def get_current_theme(self) -> ThemeType:
        """Get the current theme.
        
        Returns:
            The current theme setting
        """
        return self.current_theme 