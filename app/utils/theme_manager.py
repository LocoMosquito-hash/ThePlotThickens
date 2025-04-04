#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Theme manager for The Plot Thickens application.

This module provides utilities for managing and switching application themes.
"""

import os
import json
from typing import Literal, Optional
import qdarktheme
from PyQt6.QtWidgets import QApplication


class ThemeManager:
    """Manages application themes using PyQtDarkTheme."""
    
    CONFIG_FILE = "theme_config.json"
    ThemeType = Literal["dark", "light", "auto"]
    
    def __init__(self, app_dir: str):
        """Initialize the theme manager.
        
        Args:
            app_dir: The application directory path
        """
        self.app_dir = app_dir
        self.config_path = os.path.join(app_dir, self.CONFIG_FILE)
        self.current_theme = self._load_theme_config()
    
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
    
    def apply_theme(self, theme: Optional[ThemeType] = None) -> None:
        """Apply the specified theme or the current theme if none specified.
        
        Args:
            theme: The theme to apply ("dark", "light", or "auto")
        """
        if theme is not None and theme in ["dark", "light", "auto"]:
            self.current_theme = theme
            self._save_theme_config()
        
        # Apply the theme using PyQtDarkTheme
        qdarktheme.setup_theme(self.current_theme)
    
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