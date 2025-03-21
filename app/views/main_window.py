#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main window for The Plot Thickens application.

This module defines the main window of the application.
"""

import os
import sys
from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QStatusBar, QMessageBox, QFileDialog,
    QMenuBar, QMenu
)
from PyQt6.QtCore import Qt, QSize, QSettings
from PyQt6.QtGui import QAction, QIcon

from app.views.story_manager import StoryManagerWidget
from app.views.story_board import StoryBoardWidget
from app.views.settings_dialog import SettingsDialog
from app.views.gallery_widget import GalleryWidget
from app.views.timeline_widget import TimelineWidget


class MainWindow(QMainWindow):
    """Main window of the application."""
    
    def __init__(self, db_conn) -> None:
        """Initialize the main window.
        
        Args:
            db_conn: Database connection
        """
        super().__init__()
        
        self.db_conn = db_conn
        self.current_story_id: Optional[int] = None
        self.settings = QSettings("ThePlotThickens", "ThePlotThickens")
        
        self.init_ui()
        self.restore_window_state()
    
    def init_ui(self) -> None:
        """Set up the user interface."""
        # Set window properties
        self.setWindowTitle("The Plot Thickens")
        self.setMinimumSize(1200, 800)
        
        # Set window icon
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "icons", "favicon.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            else:
                print(f"Warning: Favicon not found at {icon_path}")
        except Exception as e:
            print(f"Warning: Failed to load favicon: {e}")
        
        # Create menu bar
        self.create_menus()
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create story manager tab
        self.story_manager = StoryManagerWidget(self.db_conn)
        self.story_manager.story_selected.connect(self.on_story_selected)
        self.tab_widget.addTab(self.story_manager, "Story Manager")
        
        # Create story board tab (initially disabled)
        self.story_board = StoryBoardWidget(self.db_conn)
        self.story_board_tab_index = self.tab_widget.addTab(self.story_board, "Story Board")
        self.tab_widget.setTabEnabled(self.story_board_tab_index, False)
        
        # Create gallery tab (initially disabled)
        self.gallery = GalleryWidget(self.db_conn)
        self.gallery_tab_index = self.tab_widget.addTab(self.gallery, "Gallery")
        self.tab_widget.setTabEnabled(self.gallery_tab_index, False)
        
        # Create timeline tab (initially disabled)
        self.timeline = TimelineWidget(self.db_conn, 0)
        self.timeline_tab_index = self.tab_widget.addTab(self.timeline, "Timeline")
        self.tab_widget.setTabEnabled(self.timeline_tab_index, False)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Set dark theme
        self.set_dark_theme()
    
    def create_menus(self) -> None:
        """Create the application menus."""
        # Create menu bar
        menu_bar = self.menuBar()
        
        # Create File menu
        file_menu = menu_bar.addMenu("&File")
        
        # Add Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Create Settings menu
        settings_menu = menu_bar.addMenu("&Settings")
        
        # Add Preferences action
        preferences_action = QAction("&Preferences", self)
        preferences_action.setShortcut("Ctrl+P")
        preferences_action.setStatusTip("Open the settings dialog")
        preferences_action.triggered.connect(self.on_open_settings)
        settings_menu.addAction(preferences_action)
    
    def on_open_settings(self) -> None:
        """Open the settings dialog."""
        settings_dialog = SettingsDialog(self)
        if settings_dialog.exec():
            self.status_bar.showMessage("Settings saved", 3000)
    
    def set_dark_theme(self) -> None:
        """Apply dark theme to the application."""
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #2D2D30;
                color: #FFFFFF;
            }
            QTabWidget::pane {
                border: 1px solid #3E3E42;
                background-color: #2D2D30;
            }
            QTabBar::tab {
                background-color: #3E3E42;
                color: #FFFFFF;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #007ACC;
            }
            QPushButton {
                background-color: #3E3E42;
                color: #FFFFFF;
                border: 1px solid #555555;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #007ACC;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #333337;
                color: #FFFFFF;
                border: 1px solid #555555;
                padding: 3px;
            }
            QStatusBar {
                background-color: #007ACC;
                color: #FFFFFF;
            }
            QMenuBar {
                background-color: #2D2D30;
                color: #FFFFFF;
            }
            QMenuBar::item {
                background-color: #2D2D30;
                color: #FFFFFF;
            }
            QMenuBar::item:selected {
                background-color: #3E3E42;
            }
            QMenu {
                background-color: #2D2D30;
                color: #FFFFFF;
                border: 1px solid #3E3E42;
            }
            QMenu::item:selected {
                background-color: #3E3E42;
            }
        """)
    
    def on_story_selected(self, story_id: int, story_data: Dict[str, Any]) -> None:
        """Handle story selection.
        
        Args:
            story_id: ID of the selected story
            story_data: Data of the selected story
        """
        self.current_story_id = story_id
        self.story_board.set_story(story_id, story_data)
        self.gallery.set_story(story_id, story_data)
        self.timeline.story_id = story_id
        self.timeline.load_events()
        self.timeline.load_timeline_views()
        self.tab_widget.setTabEnabled(self.story_board_tab_index, True)
        self.tab_widget.setTabEnabled(self.gallery_tab_index, True)
        self.tab_widget.setTabEnabled(self.timeline_tab_index, True)
        self.tab_widget.setCurrentIndex(self.story_board_tab_index)
        self.status_bar.showMessage(f"Loaded story: {story_data['title']}")
    
    def restore_window_state(self) -> None:
        """Restore the window state from settings."""
        # Restore window geometry
        geometry = self.settings.value("window/geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # Restore window state (maximized, etc.)
        state = self.settings.value("window/state")
        if state:
            self.restoreState(state)
        
        # Restore maximized state
        is_maximized = self.settings.value("window/maximized", False, type=bool)
        if is_maximized:
            self.showMaximized()
    
    def save_window_state(self) -> None:
        """Save the window state to settings."""
        # Save window geometry
        self.settings.setValue("window/geometry", self.saveGeometry())
        
        # Save window state (maximized, etc.)
        self.settings.setValue("window/state", self.saveState())
        
        # Save maximized state
        self.settings.setValue("window/maximized", self.isMaximized())
    
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        # Save window state
        self.save_window_state()
        
        # Accept the event
        event.accept() 