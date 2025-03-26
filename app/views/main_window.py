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
    QMenuBar, QMenu, QDialog, QComboBox, QTextEdit, QListWidget, 
    QListWidgetItem
)
from PyQt6.QtCore import Qt, QSize, QSettings, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QTextCursor

from app.views.story_manager import StoryManagerWidget
from app.views.story_board import StoryBoardWidget
from app.views.settings_dialog import SettingsDialog
from app.views.gallery_widget import GalleryWidget
from app.views.timeline_widget import TimelineWidget
from app.views.recognition_viewer import RecognitionDatabaseViewer
from app.db_sqlite import (
    get_story_characters, create_quick_event, get_next_quick_event_sequence_number,
    get_character
)


class CharacterTagCompleter(QWidget):
    """Popup widget for character tag autocompletion."""
    
    character_selected = pyqtSignal(str)  # Signal emitted when a character is selected
    
    def __init__(self, parent=None):
        """Initialize the character tag completer.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.characters = []
        self.filtered_characters = []
        
        self.setWindowFlags(Qt.WindowType.Popup)
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # List widget for displaying character suggestions
        self.list_widget = QListWidget()
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        
        layout.addWidget(self.list_widget)
        
        # Set a fixed size
        self.setFixedSize(200, 150)
        
    def set_characters(self, characters):
        """Set the available characters for autocompletion.
        
        Args:
            characters: List of character dictionaries
        """
        self.characters = characters
        self.filtered_characters = characters
        self.update_suggestions()
        
    def set_filter(self, filter_text):
        """Filter the character suggestions based on the input text.
        
        Args:
            filter_text: Text to filter by
        """
        if not filter_text:
            self.filtered_characters = self.characters
        else:
            filter_text = filter_text.lower()
            self.filtered_characters = [
                char for char in self.characters
                if filter_text in char['name'].lower()
            ]
            
        self.update_suggestions()
        
        # Show or hide the widget based on whether there are suggestions
        if self.filtered_characters:
            self.show()
        else:
            self.hide()
            
    def update_suggestions(self):
        """Update the list widget with filtered character suggestions."""
        self.list_widget.clear()
        
        for char in self.filtered_characters:
            item = QListWidgetItem(char['name'])
            item.setData(Qt.ItemDataRole.UserRole, char['id'])
            self.list_widget.addItem(item)
            
        # Select the first item if there are any
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
            
    def on_item_clicked(self, item):
        """Handle item click events.
        
        Args:
            item: The clicked item
        """
        character_name = item.text()
        self.character_selected.emit(character_name)
        self.hide()
        
    def keyPressEvent(self, event):
        """Handle key press events.
        
        Args:
            event: Key press event
        """
        key = event.key()
        
        if key == Qt.Key.Key_Escape:
            self.hide()
            event.accept()
        elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            current_item = self.list_widget.currentItem()
            if current_item:
                self.on_item_clicked(current_item)
            event.accept()
        elif key == Qt.Key.Key_Up:
            current_row = self.list_widget.currentRow()
            if current_row > 0:
                self.list_widget.setCurrentRow(current_row - 1)
            event.accept()
        elif key == Qt.Key.Key_Down:
            current_row = self.list_widget.currentRow()
            if current_row < self.list_widget.count() - 1:
                self.list_widget.setCurrentRow(current_row + 1)
            event.accept()
        else:
            # Let the parent handle other key presses
            event.ignore()


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
        
        self.init_ui()
        
        # Create character tag completer
        self.tag_completer = CharacterTagCompleter(self)
        self.tag_completer.set_characters(self.characters)
        self.tag_completer.character_selected.connect(self.insert_character_tag)
        self.tag_completer.hide()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Create Quick Event")
        self.resize(450, 200)
        
        layout = QVBoxLayout(self)
        
        # Text edit - main focus of the dialog
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Enter quick event text. Use @name to tag characters (e.g., @John kissed @Mary)")
        self.text_edit.textChanged.connect(self.check_for_character_tag)
        layout.addWidget(self.text_edit)
        
        # Available characters
        if self.characters:
            char_names = [f"@{char['name']}" for char in self.characters]
            characters_label = QLabel("Available character tags: " + ", ".join(char_names))
            characters_label.setWordWrap(True)
            characters_label.setStyleSheet("color: #666; font-style: italic;")
            layout.addWidget(characters_label)
        
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
        # Convert @mentions to [char:ID] for storage
        return self.convert_mentions_to_char_refs(display_text)
        
    def convert_mentions_to_char_refs(self, text: str) -> str:
        """Convert @mentions to [char:ID] format for storage.
        
        Args:
            text: Text with @CharacterName mentions
            
        Returns:
            Text with [char:ID] references
        """
        import re
        
        # Create a mapping of character names to IDs (case insensitive)
        char_name_to_id = {char['name'].lower(): str(char['id']) for char in self.characters}
        
        # Replace @CharacterName with [char:ID]
        def replace_mention(match):
            char_name = match.group(1)
            if char_name.lower() in char_name_to_id:
                char_id = char_name_to_id[char_name.lower()]
                return f"[char:{char_id}]"
            return match.group(0)  # Keep original if no match
        
        # Process the text with regex substitution to handle mentions
        processed_text = re.sub(r'@(\w+)', replace_mention, text)
        
        return processed_text
        
    def get_character_id(self) -> Optional[int]:
        """Get the character ID from the first mentioned character.
        
        If no characters are mentioned, return None to indicate a characterless event.
        
        Returns:
            ID of the character or None if no character is mentioned
        """
        # Get the text
        text = self.text_edit.toPlainText()
        
        # Find all character mentions
        import re
        mentions = re.findall(r'@(\w+)', text)
        
        if mentions:
            # Get the first mentioned character
            first_mention = mentions[0].lower()
            
            # Find the character ID
            for char in self.characters:
                if char['name'].lower() == first_mention:
                    return char['id']
        
        # If no characters are mentioned, return None
        return None if not mentions else self.get_default_character_id()
    
    def get_default_character_id(self) -> int:
        """Get the ID of the default character to use when no specific character is mentioned.
        
        Returns:
            ID of the default character (first in the list)
        """
        # Get the first character or None if no characters
        if self.characters:
            return self.characters[0]['id']
        return None
        
    def check_for_character_tag(self):
        """Check if the user is typing a character tag and provide suggestions."""
        cursor = self.text_edit.textCursor()
        text = self.text_edit.toPlainText()
        
        # Find the current word being typed
        pos = cursor.position()
        start = max(0, pos - 1)
        
        # Check if we're in the middle of typing a tag
        if start >= 0 and pos <= len(text):
            # Look backward to find the start of the current tag
            tag_start = text.rfind('@', 0, pos)
            
            if tag_start >= 0 and tag_start < pos:
                # We found a @ character before the cursor
                # Extract the partial tag text
                partial_tag = text[tag_start + 1:pos]
                
                # Only show suggestions if we're actively typing a tag
                if tag_start == pos - 1 or partial_tag.strip():
                    # Position the completer popup below the cursor
                    cursor_rect = self.text_edit.cursorRect()
                    global_pos = self.text_edit.mapToGlobal(cursor_rect.bottomLeft())
                    
                    self.tag_completer.set_filter(partial_tag)
                    self.tag_completer.move(global_pos)
                    return
                    
        # Hide the completer if we're not typing a tag
        self.tag_completer.hide()
        
    def insert_character_tag(self, character_name: str):
        """Insert a character tag at the current cursor position.
        
        Args:
            character_name: Name of the character to tag
        """
        cursor = self.text_edit.textCursor()
        text = self.text_edit.toPlainText()
        pos = cursor.position()
        
        # Find the start of the current tag
        tag_start = text.rfind('@', 0, pos)
        
        if tag_start >= 0:
            # Replace the partial tag with the full tag
            cursor.setPosition(tag_start, QTextCursor.MoveMode.MoveAnchor)
            cursor.setPosition(pos, QTextCursor.MoveMode.KeepAnchor)
            cursor.insertText(f"@{character_name}")
            
            # Add a space after the tag
            cursor.insertText(" ")
            
            # Set focus back to the text edit
            self.text_edit.setFocus()


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
    
    def on_open_recognition_viewer(self) -> None:
        """Open the recognition database viewer dialog."""
        recognition_viewer = RecognitionDatabaseViewer(self.db_conn, self)
        recognition_viewer.exec()
        self.status_bar.showMessage("Recognition database viewer closed", 3000)
    
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

    def add_quick_event(self) -> None:
        """Open dialog to add a new quick event from any tab.
        
        This method can be triggered from any tab using Ctrl+Q shortcut.
        It allows users to create quick events without having to go to a character's profile.
        """
        # Check if we have a story selected
        if not self.current_story_id:
            QMessageBox.warning(
                self,
                "No Story Selected",
                "Please select a story first to add a quick event."
            )
            return
            
        # Open the quick event dialog
        dialog = QuickEventDialog(self.db_conn, self.current_story_id, self)
        
        if dialog.exec():
            try:
                # Get the text
                text = dialog.get_text()
                
                if not text.strip():
                    QMessageBox.warning(self, "Error", "Quick event text cannot be empty.")
                    return
                
                # Get character ID (may be None if no character specified)
                character_id = dialog.get_character_id()
                
                if character_id is None:
                    # If no character is specified, check if we have characters
                    if dialog.characters:
                        # Use the first character as default
                        character_id = dialog.characters[0]['id']
                        
                        # Show a more specific message
                        QMessageBox.information(
                            self,
                            "No Character Specified",
                            f"No character was tagged in the text. Using the first character as default."
                        )
                    else:
                        QMessageBox.warning(
                            self,
                            "No Characters Available",
                            "Cannot create a quick event without any characters in the story."
                        )
                        return
                
                # Get the next sequence number for this character
                sequence_number = get_next_quick_event_sequence_number(self.db_conn, character_id)
                
                # Create the quick event
                quick_event_id = create_quick_event(
                    self.db_conn,
                    text,
                    character_id,
                    sequence_number
                )
                
                if quick_event_id:
                    # Get character name for the success message
                    character = get_character(self.db_conn, character_id)
                    char_name = character.get('name', 'Unknown') if character else 'Unknown'
                    
                    QMessageBox.information(
                        self,
                        "Success",
                        f"Created a new quick event for {char_name}."
                    )
                    
                    # If we're on the character board, refresh it
                    current_tab = self.tab_widget.currentWidget()
                    
                    # Refresh the timeline tab if it's currently visible
                    if current_tab is self.timeline:
                        # Reload quick events in the quick events tab
                        if hasattr(self.timeline, 'quick_events_tab'):
                            self.timeline.quick_events_tab.load_quick_events()
                            
                    # Refresh the gallery tab if it's currently visible
                    elif current_tab is self.gallery:
                        # Reload quick events if we're viewing image details
                        if hasattr(self.gallery, 'refresh_quick_events'):
                            self.gallery.refresh_quick_events()
                else:
                    QMessageBox.warning(self, "Error", "Failed to create quick event.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to create quick event: {str(e)}")

    def keyPressEvent(self, event) -> None:
        """Handle key press events.
        
        Args:
            event: The key press event
        """
        # Check for Ctrl+Q shortcut for adding quick events
        if event.key() == Qt.Key.Key_Q and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.add_quick_event()
        else:
            # Pass the event to the parent class
            super().keyPressEvent(event) 