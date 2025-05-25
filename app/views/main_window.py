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
    QPushButton, QLabel, QMessageBox, QFileDialog,
    QMenuBar, QMenu, QDialog, QComboBox, QTextEdit, QListWidget, 
    QListWidgetItem, QFrame
)
from PyQt6.QtCore import Qt, QSize, QSettings, pyqtSignal, QEvent
from PyQt6.QtGui import QAction, QIcon, QTextCursor, QKeyEvent

from app.widgets.enhanced_status_bar import EnhancedStatusBar
from app.views.story_manager import StoryManagerWidget
from app.views.story_board_modular import StoryBoardWidget
from app.views.settings_dialog import SettingsDialog
from app.views.gallery_widget import GalleryWidget
from app.views.timeline_widget import TimelineWidget
from app.views.recognition_viewer import RecognitionDatabaseViewer
from app.views.decision_points_tab import DecisionPointsTab
from app.views.decision_point_dialog import DecisionPointDialog
from app.views.relationship_editor import RelationshipEditorDialog
from app.db_sqlite import (
    get_story_characters, create_quick_event, get_next_quick_event_sequence_number,
    get_character, search_quick_events
)
from app.utils.character_completer import CharacterCompleter
from app.utils.character_references import convert_mentions_to_char_refs, convert_char_refs_to_mentions
from app.utils.quick_event_utils import show_quick_event_dialog
from app.utils.icons import icon_manager


class QuickEventDialog(QDialog):
    """Dialog for creating a quick event."""
    
    def __init__(self, db_conn, story_id: int, parent=None):
        """Initialize the quick event dialog.
        
        Args:
            db_conn: Database connection
            story_id: ID of the story
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.story_id = story_id
        
        # Get all characters for the story for tagging
        self.characters = get_story_characters(db_conn, self.story_id)
        
        # Load recent quick events
        self.recent_events = self.load_recent_events()
        
        self.init_ui()
        
        # Create character completer (using the new centralized implementation)
        self.tag_completer = CharacterCompleter(self)
        self.tag_completer.set_characters(self.characters)
        self.tag_completer.character_selected.connect(self.on_character_selected)
        self.tag_completer.attach_to_widget(
            self.text_edit,
            add_shortcut=True,
            shortcut_key="Ctrl+Space",
            at_trigger=True
        )
        
    def load_recent_events(self, limit: int = 3):
        """Load the most recent quick events for this story.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of recent quick events
        """
        try:
            # Using search_quick_events with no filters to get all events, sorted by date
            events = search_quick_events(
                self.db_conn,
                self.story_id,
                text_query=None,
                character_id=None,
                from_date=None,
                to_date=None
            )
            
            # Format the events with character names
            formatted_events = []
            for event in events[:limit]:
                # Get character name if character_id is present
                character_id = event.get('character_id')
                if character_id:
                    character = get_character(self.db_conn, character_id)
                    character_name = character.get('name', 'Unknown') if character else 'Unknown'
                else:
                    character_name = "General Event"
                
                # Format the text (replace [char:ID] with @Name)
                text = event.get('text', '')
                formatted_text = self.format_character_references(text)
                
                formatted_events.append({
                    'character_name': character_name,
                    'text': formatted_text
                })
                
            return formatted_events
            
        except Exception as e:
            print(f"Error loading recent events: {e}")
            return []
            
    def format_character_references(self, text: str) -> str:
        """Format character references in text, converting [char:ID] to @Name.
        
        Args:
            text: Text containing character references
            
        Returns:
            Text with formatted character references
        """
        # Use the centralized utility function
        return convert_char_refs_to_mentions(text, self.characters)
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Create Quick Event")
        self.resize(450, 200)
        
        layout = QVBoxLayout(self)
        
        # Text edit - main focus of the dialog
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Enter quick event text. Use @name to tag characters (e.g., @John kissed @Mary)")
        layout.addWidget(self.text_edit)
        
        # Available characters
        if self.characters:
            char_names = [f"@{char['name']}" for char in self.characters]
            characters_label = QLabel("Available character tags: " + ", ".join(char_names))
            characters_label.setWordWrap(True)
            characters_label.setStyleSheet("color: #666; font-style: italic;")
            layout.addWidget(characters_label)
            
            # Add note about optional character tagging
            note_label = QLabel("Note: Character tagging is optional. You can create events without any character.")
            note_label.setWordWrap(True)
            note_label.setStyleSheet("color: #666; font-style: italic;")
            layout.addWidget(note_label)
        else:
            # No characters available
            no_chars_label = QLabel("No characters available. You can still create a general event.")
            no_chars_label.setWordWrap(True)
            no_chars_label.setStyleSheet("color: #666; font-style: italic;")
            layout.addWidget(no_chars_label)
            
        # Recent events section
        if self.recent_events:
            recent_label = QLabel("Recent events:")
            recent_label.setStyleSheet("color: #666; font-style: italic; margin-top: 5px;")
            layout.addWidget(recent_label)
            
            # Display each recent event
            for event in self.recent_events:
                text = f"{event['character_name']}: {event['text']}"
                event_label = QLabel(text)
                event_label.setWordWrap(True)
                event_label.setStyleSheet("color: #888; font-size: 11px; margin-left: 10px;")
                layout.addWidget(event_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
    def get_text(self) -> str:
        """Get the edited text, converting @mentions to [char:ID] format for storage.
        
        Returns:
            The text from the editor with character references in [char:ID] format
        """
        display_text = self.text_edit.toPlainText()
        # Convert @mentions to [char:ID] for storage using the centralized utility function
        return convert_mentions_to_char_refs(display_text, self.characters)
        
    def get_character_id(self) -> Optional[int]:
        """Get the character ID from the first mentioned character.
        
        If no characters are mentioned, return None to indicate a characterless event.
        
        Returns:
            ID of the character or None if no character is mentioned
        """
        import re
        
        # Get the text
        text = self.text_edit.toPlainText()
        
        # Sort characters by name length (longest first)
        sorted_characters = sorted(self.characters, key=lambda x: len(x.get('name', '')), reverse=True)
        
        # Check for character mentions by looking for each possible character name
        for char in sorted_characters:
            name = char['name'].lower()
            # Create pattern that matches '@' followed by the exact name
            pattern = r'@(' + re.escape(name) + r')(\b|\s|$)'
            
            # If this character is mentioned, return their ID
            if re.search(pattern, text, re.IGNORECASE):
                return char['id']
        
        # If no characters are mentioned, return None
        return None
    
    def get_default_character_id(self) -> int:
        """Get the ID of the default character to use when no specific character is mentioned.
        
        Returns:
            ID of the default character (first in the list)
        """
        # Get the first character or None if no characters
        if self.characters:
            return self.characters[0]['id']
        return None
    
    def on_character_selected(self, character_name: str):
        """Handle character selection.
        
        Args:
            character_name: Name of the selected character
        """
        # Call the completer's insert method to actually insert the tag
        self.tag_completer.insert_character_tag(character_name)


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
        self.theme_manager = None  # This will be set in main.py
        
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
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        main_layout.addWidget(self.tab_widget)
        
        # Create story manager tab
        self.story_manager = StoryManagerWidget(self.db_conn)
        self.story_manager.story_selected.connect(self.on_story_selected)
        self.tab_widget.addTab(self.story_manager, "Story Manager")
        
        # Add "book" icon to the Story Manager tab
        story_manager_index = 0  # First tab
        self.tab_widget.setTabIcon(story_manager_index, icon_manager.get_icon("book"))
        
        # Create story board tab (initially disabled)
        self.story_board = StoryBoardWidget(self.db_conn)
        self.story_board_tab_index = self.tab_widget.addTab(self.story_board, "Story Board")
        self.tab_widget.setTabEnabled(self.story_board_tab_index, False)
        
        # Add "layout-board" icon to Story Board tab
        self.tab_widget.setTabIcon(self.story_board_tab_index, icon_manager.get_icon("layout_board"))
        
        # Create gallery tab with refresh button (initially disabled)
        gallery_container = QWidget()
        gallery_layout = QVBoxLayout(gallery_container)
        gallery_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add refresh button for gallery tab
        gallery_button_layout = QHBoxLayout()
        gallery_button_layout.setContentsMargins(5, 5, 5, 0)
        gallery_refresh_btn = QPushButton("Refresh Gallery")
        gallery_refresh_btn.setToolTip("Refresh gallery contents")
        gallery_refresh_btn.clicked.connect(self.refresh_gallery)
        gallery_button_layout.addWidget(gallery_refresh_btn)
        gallery_button_layout.addStretch()
        gallery_layout.addLayout(gallery_button_layout)
        
        # Add gallery widget
        self.gallery = GalleryWidget(self.db_conn)
        gallery_layout.addWidget(self.gallery)
        
        self.gallery_tab_index = self.tab_widget.addTab(gallery_container, "Gallery")
        self.tab_widget.setTabEnabled(self.gallery_tab_index, False)
        
        # Add "photo" icon to Gallery tab
        self.tab_widget.setTabIcon(self.gallery_tab_index, icon_manager.get_icon("photo"))
        
        # Create timeline tab with refresh button (initially disabled)
        timeline_container = QWidget()
        timeline_layout = QVBoxLayout(timeline_container)
        timeline_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add refresh button for timeline tab
        timeline_button_layout = QHBoxLayout()
        timeline_button_layout.setContentsMargins(5, 5, 5, 0)
        timeline_refresh_btn = QPushButton("Refresh Timeline")
        timeline_refresh_btn.setToolTip("Refresh timeline contents")
        timeline_refresh_btn.clicked.connect(self.refresh_timeline)
        timeline_button_layout.addWidget(timeline_refresh_btn)
        timeline_button_layout.addStretch()
        timeline_layout.addLayout(timeline_button_layout)
        
        # Add timeline widget
        self.timeline = TimelineWidget(self.db_conn, 0)
        timeline_layout.addWidget(self.timeline)
        
        self.timeline_tab_index = self.tab_widget.addTab(timeline_container, "Timeline")
        self.tab_widget.setTabEnabled(self.timeline_tab_index, False)
        
        # Add "timeline" icon to Timeline tab
        self.tab_widget.setTabIcon(self.timeline_tab_index, icon_manager.get_icon("timeline"))
        
        # Create decision points tab with refresh button (initially disabled)
        decision_points_container = QWidget()
        decision_points_layout = QVBoxLayout(decision_points_container)
        decision_points_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add refresh button for decision points tab
        decision_points_button_layout = QHBoxLayout()
        decision_points_button_layout.setContentsMargins(5, 5, 5, 0)
        decision_points_refresh_btn = QPushButton("Refresh Decision Points")
        decision_points_refresh_btn.setToolTip("Refresh decision points list")
        decision_points_refresh_btn.clicked.connect(self.refresh_decision_points)
        decision_points_button_layout.addWidget(decision_points_refresh_btn)
        decision_points_button_layout.addStretch()
        decision_points_layout.addLayout(decision_points_button_layout)
        
        # Add decision points widget
        self.decision_points = DecisionPointsTab(self.db_conn, 0)
        decision_points_layout.addWidget(self.decision_points)
        
        self.decision_points_tab_index = self.tab_widget.addTab(decision_points_container, "Decision Points")
        self.tab_widget.setTabEnabled(self.decision_points_tab_index, False)
        
        # Add "git-fork" icon to Decision Points tab
        self.tab_widget.setTabIcon(self.decision_points_tab_index, icon_manager.get_icon("git_fork"))
        
        # Status bar
        self.status_bar = EnhancedStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showPermanentMessage("Ready")
    
    def create_menus(self) -> None:
        """Create the application menus."""
        # Create menu bar
        menu_bar = self.menuBar()
        
        # Create File menu
        file_menu = menu_bar.addMenu("&File")
        
        # Add Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Create Tools menu
        tools_menu = menu_bar.addMenu("&Tools")
        
        # Add Recognition Database Viewer action
        recog_db_action = QAction("&Recognition Database Viewer", self)
        recog_db_action.setStatusTip("View and test the image recognition database")
        recog_db_action.triggered.connect(self.on_open_recognition_viewer)
        tools_menu.addAction(recog_db_action)
        
        # Add Quick Event action
        quick_event_action = QAction("Add Quick &Event", self)
        quick_event_action.setShortcut("Ctrl+Q")
        quick_event_action.setStatusTip("Add a new quick event")
        quick_event_action.triggered.connect(self.add_quick_event)
        tools_menu.addAction(quick_event_action)
        
        # Create Settings menu
        settings_menu = menu_bar.addMenu("&Settings")
        
        # Add Preferences action
        preferences_action = QAction("&Preferences", self)
        preferences_action.setShortcut("Ctrl+P")
        preferences_action.setStatusTip("Open the settings dialog")
        preferences_action.triggered.connect(self.on_open_settings)
        settings_menu.addAction(preferences_action)
        
        # Add Theme toggle action with icon
        self.theme_action = QAction("Toggle &Theme (Dark/Light)", self)
        self.theme_action.setShortcut("Ctrl+T")
        self.theme_action.setStatusTip("Toggle between dark and light themes")
        # Add icon based on current theme
        current_theme = self.theme_manager.get_current_theme() if self.theme_manager else "dark"
        if current_theme == "dark":
            self.theme_action.setIcon(icon_manager.get_icon("moon"))
        else:
            self.theme_action.setIcon(icon_manager.get_icon("sun"))
        self.theme_action.triggered.connect(self.on_toggle_theme)
        settings_menu.addAction(self.theme_action)
    
    def on_open_recognition_viewer(self) -> None:
        """Open the recognition database viewer dialog."""
        recognition_viewer = RecognitionDatabaseViewer(self.db_conn, self)
        recognition_viewer.exec()
        self.status_bar.showPermanentMessage("Recognition database viewer closed")
    
    def on_open_settings(self) -> None:
        """Open the settings dialog."""
        settings_dialog = SettingsDialog(self)
        if settings_dialog.exec():
            self.status_bar.showPermanentMessage("Settings saved")
    
    def on_toggle_theme(self) -> None:
        """Toggle between dark and light themes."""
        if self.theme_manager:
            self.theme_manager.toggle_theme()
            
            # Update the theme action icon based on the new theme
            current_theme = self.theme_manager.get_current_theme()
            if current_theme == "dark":
                self.theme_action.setIcon(icon_manager.get_icon("moon"))
            else:
                self.theme_action.setIcon(icon_manager.get_icon("sun"))
    
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
        self.decision_points.set_story_id(story_id)
        self.tab_widget.setTabEnabled(self.story_board_tab_index, True)
        self.tab_widget.setTabEnabled(self.gallery_tab_index, True)
        self.tab_widget.setTabEnabled(self.timeline_tab_index, True)
        self.tab_widget.setTabEnabled(self.decision_points_tab_index, True)
        self.tab_widget.setCurrentIndex(self.story_board_tab_index)
        self.status_bar.showPermanentMessage(f"Loaded story: {story_data['title']}")
    
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

    def add_quick_event(self) -> None:
        """Add a quick event to the database."""
        if not hasattr(self, 'current_story_id') or not self.current_story_id:
            QMessageBox.warning(self, "No Story Selected", "Please select a story first.")
            return
        
        try:
            # Get the current tab name for context
            current_tab_index = self.tab_widget.currentIndex()
            tab_name = self.tab_widget.tabText(current_tab_index)
            
            # Create context dictionary for the quick event dialog
            context = {
                "source": "main_window",
                "current_tab": current_tab_index,
                "tab_name": tab_name,
                "shortcut": "CTRL+Q"
            }
            
            # Debug output to confirm we're using the new module
            print(f"\n[DEBUG] QuickEventDialog called from new module - context: {context}\n")
            
            # Show the dialog with the callback to handle the result
            from app.utils.quick_event_utils import show_quick_event_dialog
            
            show_quick_event_dialog(
                db_conn=self.db_conn,
                story_id=self.current_story_id,
                parent=self,
                callback=self.on_quick_event_created,
                context=context,
                options={
                    "show_recent_events": True,
                    "show_character_tags": True,
                    "title": f"Quick Event - {tab_name} Tab"
                }
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Error creating quick event: {str(e)}",
                QMessageBox.StandardButton.Ok
            )

    def on_quick_event_created(self, event_id: int, text: str, context: Dict[str, Any]) -> None:
        """Handle the quick event created signal.
        
        Args:
            event_id: ID of the created quick event
            text: Text of the quick event
            context: Context dictionary passed to the dialog
        """
        if not event_id:
            return
        
        # Get character_id to display a proper message
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT character_id FROM quick_events WHERE id = ?", (event_id,))
        row = cursor.fetchone()
        character_id = row['character_id'] if row else None
        
        # Show a success message
        if character_id:
            # Get character name for the success message
            from app.db_sqlite import get_character
            character = get_character(self.db_conn, character_id)
            char_name = character.get('name', 'Unknown') if character else 'Unknown'
            
            QMessageBox.information(
                self,
                "Success",
                f"Created a new quick event for {char_name}."
            )
        else:
            QMessageBox.information(
                self,
                "Success",
                "Created a new general quick event."
            )
        
        # Refresh the appropriate UI components based on the current tab
        current_tab = self.tab_widget.currentWidget()
        
        # Refresh the timeline tab if it's currently visible
        if current_tab is self.timeline:
            # Reload quick events in the quick events tab
            if hasattr(self.timeline, 'quick_events_tab') and hasattr(self.timeline.quick_events_tab, 'load_quick_events'):
                self.timeline.quick_events_tab.load_quick_events()
                
        # Refresh the gallery tab if it's currently visible
        elif current_tab is self.gallery:
            # Reload quick events if we're viewing image details
            if hasattr(self.gallery, 'refresh_quick_events'):
                self.gallery.refresh_quick_events()

    def keyPressEvent(self, event) -> None:
        """Handle key press events.
        
        Args:
            event: The key press event
        """
        # Check for Ctrl+Q shortcut for adding quick events
        if event.key() == Qt.Key.Key_Q and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.add_quick_event()
        # Check for Ctrl+R shortcut for editing relationships
        elif event.key() == Qt.Key.Key_R and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.open_relationship_editor()
        else:
            # Pass the event to the parent class
            super().keyPressEvent(event)

    def on_tab_changed(self, index: int) -> None:
        """Handle tab change events.
        
        Args:
            index: Index of the selected tab
        """
        # Check if the selected tab is the Decision Points tab
        if hasattr(self, 'decision_points_tab_index') and index == self.decision_points_tab_index and self.current_story_id:
            # Refresh decision points
            self.decision_points.load_decision_points()

    # Add refresh methods for each tab
    def refresh_gallery(self) -> None:
        """Refresh the gallery tab contents."""
        if hasattr(self, 'gallery') and self.gallery:
            self.gallery.load_images()
            self.status_bar.showPermanentMessage("Gallery refreshed")
    
    def refresh_timeline(self) -> None:
        """Refresh the timeline tab contents."""
        if hasattr(self, 'timeline') and self.timeline:
            self.timeline.load_events()
            self.timeline.load_timeline_views()
            self.status_bar.showPermanentMessage("Timeline refreshed")
    
    def refresh_decision_points(self) -> None:
        """Refresh the decision points tab contents."""
        if hasattr(self, 'decision_points') and self.decision_points:
            self.decision_points.load_decision_points()
            self.status_bar.showPermanentMessage("Decision points refreshed")
    
    def open_relationship_editor(self) -> None:
        """Open the relationship editor dialog."""
        if not hasattr(self, 'current_story_id') or not self.current_story_id:
            QMessageBox.warning(self, "No Story Selected", "Please select a story first.")
            return
        
        try:
            # Create and show the relationship editor dialog
            dialog = RelationshipEditorDialog(
                db_conn=self.db_conn,
                story_id=self.current_story_id,
                parent=self
            )
            
            # Show the dialog
            if dialog.exec():
                # TODO: Handle relationship creation/editing after dialog is implemented fully
                pass
                
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Error opening relationship editor: {str(e)}",
                QMessageBox.StandardButton.Ok
            ) 