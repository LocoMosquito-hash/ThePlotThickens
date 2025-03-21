#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Timeline Widget for The Plot Thickens application.
This widget displays events on a timeline and allows for event management.
"""

import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Set, Union, cast

from PyQt6.QtCore import Qt, QRectF, QPointF, QSize, pyqtSignal, QEvent, QTimer
from PyQt6.QtGui import (
    QPainter, QBrush, QPen, QColor, QFont, QFontMetrics, 
    QMouseEvent, QPainterPath, QTransform, QPixmap, QKeyEvent, QTextCursor
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QFrame, QSizePolicy, QMenu, QDialog,
    QComboBox, QLineEdit, QTextEdit, QDateEdit, QSpinBox, 
    QCheckBox, QColorDialog, QMessageBox, QToolBar, QToolButton,
    QInputDialog, QListWidget, QListWidgetItem
)

from app.db_sqlite import (
    create_event, get_event, update_event, delete_event, 
    get_story_events, add_character_to_event, remove_character_from_event,
    get_event_characters, get_character_events, create_timeline_view,
    get_timeline_view, get_story_timeline_views, update_timeline_view,
    delete_timeline_view, get_story_characters
)

logger = logging.getLogger(__name__)


class EventItem(QWidget):
    """A widget representing an event on the timeline."""
    
    clicked = pyqtSignal(int)  # Signal emitted when event is clicked, passes event_id
    
    def __init__(self, event_data: Dict[str, Any], parent=None, conn=None):
        super().__init__(parent)
        self.event_data = event_data
        self.event_id = event_data['id']
        self.title = event_data['title']
        self.description = event_data.get('description', '')
        self.event_type = event_data.get('event_type', 'SCENE')
        self.start_date = event_data.get('start_date', '')
        self.end_date = event_data.get('end_date', '')
        self.location = event_data.get('location', '')
        self.importance = event_data.get('importance', 3)
        self.color = event_data.get('color', '#3498db')
        self.is_milestone = bool(event_data.get('is_milestone', False))
        self.conn = conn
        self.characters = []
        
        self.setMinimumSize(150, 50)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)
        
        # Load characters if connection is provided
        if self.conn:
            self.load_characters()
            
        self.setToolTip(self._create_tooltip())
        
        # Visual properties
        self.is_selected = False
        self.is_hovered = False
        
    def load_characters(self):
        """Load characters for this event."""
        try:
            self.characters = get_event_characters(self.conn, self.event_id)
        except Exception as e:
            logger.error(f"Error loading event characters: {e}")
            self.characters = []
        
    def _create_tooltip(self) -> str:
        """Create a tooltip with event details."""
        tooltip = f"<b>{self.title}</b>"
        if self.description:
            tooltip += f"<br>{self.description}"
        if self.start_date:
            tooltip += f"<br>Start: {self.start_date}"
        if self.end_date:
            tooltip += f"<br>End: {self.end_date}"
        if self.location:
            tooltip += f"<br>Location: {self.location}"
            
        # Add characters if available
        if self.characters:
            char_names = [char['name'] for char in self.characters]
            tooltip += f"<br>Characters: {', '.join(char_names)}"
            
        return tooltip
        
    def paintEvent(self, event):
        """Paint the event item."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate dimensions
        width = self.width()
        height = self.height()
        
        # Set up colors
        base_color = QColor(self.color)
        border_color = base_color.darker(150)
        text_color = QColor(Qt.GlobalColor.white) if base_color.lightness() < 128 else QColor(Qt.GlobalColor.black)
        
        # Draw background
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, width, height), 5, 5)
        
        if self.is_selected:
            # Draw selection highlight
            painter.setPen(QPen(QColor(255, 165, 0), 2))
            painter.drawPath(path)
            
        painter.fillPath(path, QBrush(base_color))
        
        # Draw border
        painter.setPen(QPen(border_color, 1))
        painter.drawPath(path)
        
        # Draw milestone indicator if applicable
        if self.is_milestone:
            milestone_size = 10
            painter.setBrush(QBrush(QColor(255, 215, 0)))
            painter.setPen(QPen(QColor(218, 165, 32), 1))
            painter.drawEllipse(width - milestone_size - 5, 5, milestone_size, milestone_size)
        
        # Draw title
        painter.setPen(QPen(text_color))
        font = QFont()
        font.setBold(True)
        painter.setFont(font)
        
        # Truncate title if too long
        fm = QFontMetrics(font)
        title_width = width - 20  # Padding
        elided_title = fm.elidedText(self.title, Qt.TextElideMode.ElideRight, title_width)
        
        painter.drawText(QRectF(10, 5, width - 20, 20), Qt.AlignmentFlag.AlignLeft, elided_title)
        
        # Draw date if available
        if self.start_date:
            font.setBold(False)
            font.setPointSize(8)
            painter.setFont(font)
            painter.drawText(QRectF(10, 25, width - 20, 20), Qt.AlignmentFlag.AlignLeft, self.start_date)
        
        painter.end()
        
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.event_id)
            self.is_selected = True
            self.update()
        super().mousePressEvent(event)
        
    def enterEvent(self, event: QEvent):
        """Handle mouse enter events."""
        self.is_hovered = True
        self.update()
        super().enterEvent(event)
        
    def leaveEvent(self, event: QEvent):
        """Handle mouse leave events."""
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)
        
    def set_selected(self, selected: bool):
        """Set the selection state of this event."""
        self.is_selected = selected
        self.update()


class CharacterTagCompleter(QWidget):
    """Popup widget for character tag autocompletion."""
    
    character_selected = pyqtSignal(str)  # Signal emitted when a character is selected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.characters = []
        self.filtered_characters = []
        self.current_filter = ""
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create a list widget for character suggestions
        self.list_widget = QListWidget()
        self.list_widget.setFrameShape(QFrame.Shape.NoFrame)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.setMaximumHeight(200)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        
        # Style the list widget
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #2D2D30;
                color: #FFFFFF;
                border: 1px solid #3E3E42;
                border-radius: 3px;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #007ACC;
            }
        """)
        
        layout.addWidget(self.list_widget)
        
    def set_characters(self, characters: List[Dict[str, Any]]):
        """Set the available characters for autocompletion.
        
        Args:
            characters: List of character dictionaries
        """
        self.characters = characters
        self.update_suggestions()
        
    def set_filter(self, filter_text: str):
        """Set the filter text for character suggestions.
        
        Args:
            filter_text: Text to filter characters by
        """
        self.current_filter = filter_text.lower()
        self.update_suggestions()
        
    def update_suggestions(self):
        """Update the list of character suggestions based on the current filter."""
        self.list_widget.clear()
        
        if not self.characters:
            self.hide()
            return
            
        # Filter characters based on the current filter
        self.filtered_characters = []
        for char in self.characters:
            name = char['name']
            if self.current_filter in name.lower():
                self.filtered_characters.append(char)
                
                # Create a list item with the character name
                item = QListWidgetItem(name)
                item.setData(Qt.ItemDataRole.UserRole, char['id'])
                
                # Bold for main characters
                if char.get('is_main_character'):
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                    
                self.list_widget.addItem(item)
                
        # Show or hide the widget based on whether there are suggestions
        if self.filtered_characters:
            self.list_widget.setCurrentRow(0)  # Select the first item
            self.show()
        else:
            self.hide()
            
    def on_item_clicked(self, item: QListWidgetItem):
        """Handle item click events.
        
        Args:
            item: The clicked list item
        """
        name = item.text()
        self.character_selected.emit(name)
        self.hide()
        
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events.
        
        Args:
            event: Key event
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
            super().keyPressEvent(event)


class EventDialog(QDialog):
    """Dialog for creating or editing an event."""
    
    def __init__(self, conn, story_id: int, parent=None, event_id: Optional[int] = None):
        super().__init__(parent)
        self.conn = conn
        self.story_id = story_id
        self.event_id = event_id
        self.event_data = None
        self.characters = []  # Store available characters
        
        if event_id:
            self.event_data = get_event(conn, event_id)
            self.setWindowTitle("Edit Event")
        else:
            self.setWindowTitle("Create New Event")
            # Set default sequence number for new events
            self.default_sequence_number = self.get_next_sequence_number()
            
        # Load characters for this story
        self.load_characters()
        
        self.init_ui()
        
        # Create character tag completer
        self.tag_completer = CharacterTagCompleter(self)
        self.tag_completer.set_characters(self.characters)
        self.tag_completer.character_selected.connect(self.insert_character_tag)
        self.tag_completer.hide()
        
        if self.event_data:
            self.load_event_data()
        else:
            # Set default sequence number for new events
            self.sequence_spin.setValue(self.default_sequence_number)
            
    def load_characters(self):
        """Load characters for the current story."""
        try:
            self.characters = get_story_characters(self.conn, self.story_id)
        except Exception as e:
            logger.error(f"Error loading characters: {e}")
            self.characters = []
            
    def parse_character_tags(self, text: str) -> List[int]:
        """Parse character tags from text using @ symbol.
        
        Args:
            text: Text to parse for character tags
            
        Returns:
            List of character IDs that were tagged
        """
        if not text or not self.characters:
            return []
            
        # Find all @mentions in the text
        mentions = re.findall(r'@(\w+)', text)
        
        # Match mentions to character names
        character_ids = []
        for mention in mentions:
            mention_lower = mention.lower()
            
            # Check for exact character name matches
            for character in self.characters:
                char_name = character['name'].lower()
                
                # Check if the mention matches the character name
                if mention_lower == char_name or mention_lower in char_name.split():
                    character_ids.append(character['id'])
                    break
                    
                # Check aliases if available
                if character.get('aliases'):
                    aliases = character['aliases'].lower().split(',')
                    aliases = [alias.strip() for alias in aliases]
                    if mention_lower in aliases:
                        character_ids.append(character['id'])
                        break
                        
        return character_ids
        
    def init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout()
        
        # Title
        title_layout = QHBoxLayout()
        title_label = QLabel("Title:")
        self.title_edit = QLineEdit()
        self.title_edit.textChanged.connect(self.check_for_character_tag_in_title)
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.title_edit)
        layout.addLayout(title_layout)
        
        # Description
        desc_layout = QVBoxLayout()
        desc_label = QLabel("Description:")
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(100)
        self.desc_edit.textChanged.connect(self.check_for_character_tag)
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.desc_edit)
        
        # Character tag help
        char_tag_help = QLabel("Tip: Tag characters using @name (e.g., @John) in title or description")
        char_tag_help.setStyleSheet("color: #888; font-style: italic;")
        desc_layout.addWidget(char_tag_help)
        
        # Character suggestions
        self.char_suggestions_label = QLabel("Available characters:")
        self.char_suggestions = QLabel("")
        self.char_suggestions.setWordWrap(True)
        self.char_suggestions.setStyleSheet("color: #007ACC;")
        desc_layout.addWidget(self.char_suggestions_label)
        desc_layout.addWidget(self.char_suggestions)
        
        # Update character suggestions
        self.update_character_suggestions()
        
        layout.addLayout(desc_layout)
        
        # Event type
        type_layout = QHBoxLayout()
        type_label = QLabel("Event Type:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["SCENE", "CHAPTER", "ARC", "SUBPLOT", "OTHER"])
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)
        
        # Dates
        date_layout = QHBoxLayout()
        start_label = QLabel("Start Date:")
        self.start_date = QLineEdit()
        end_label = QLabel("End Date:")
        self.end_date = QLineEdit()
        date_layout.addWidget(start_label)
        date_layout.addWidget(self.start_date)
        date_layout.addWidget(end_label)
        date_layout.addWidget(self.end_date)
        layout.addLayout(date_layout)
        
        # Location
        location_layout = QHBoxLayout()
        location_label = QLabel("Location:")
        self.location_edit = QLineEdit()
        location_layout.addWidget(location_label)
        location_layout.addWidget(self.location_edit)
        layout.addLayout(location_layout)
        
        # Importance and color
        imp_color_layout = QHBoxLayout()
        
        importance_label = QLabel("Importance:")
        self.importance_spin = QSpinBox()
        self.importance_spin.setMinimum(1)
        self.importance_spin.setMaximum(5)
        self.importance_spin.setValue(3)
        
        color_label = QLabel("Color:")
        self.color_button = QPushButton()
        self.color_button.setFixedSize(30, 30)
        self.color = "#3498db"
        self.update_color_button()
        self.color_button.clicked.connect(self.choose_color)
        
        imp_color_layout.addWidget(importance_label)
        imp_color_layout.addWidget(self.importance_spin)
        imp_color_layout.addWidget(color_label)
        imp_color_layout.addWidget(self.color_button)
        layout.addLayout(imp_color_layout)
        
        # Milestone checkbox
        milestone_layout = QHBoxLayout()
        self.milestone_check = QCheckBox("Is Milestone Event")
        milestone_layout.addWidget(self.milestone_check)
        layout.addLayout(milestone_layout)
        
        # Sequence number for ordering
        sequence_layout = QHBoxLayout()
        sequence_label = QLabel("Sequence Number:")
        self.sequence_spin = QSpinBox()
        self.sequence_spin.setMinimum(0)
        self.sequence_spin.setMaximum(9999)
        self.sequence_spin.setValue(0)
        self.sequence_spin.setToolTip("Lower numbers appear earlier in the timeline")
        sequence_layout.addWidget(sequence_label)
        sequence_layout.addWidget(self.sequence_spin)
        layout.addLayout(sequence_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        
        self.save_button.clicked.connect(self.save_event)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.resize(400, 500)  # Make dialog taller to accommodate character suggestions
        
    def update_color_button(self):
        """Update the color button appearance."""
        self.color_button.setStyleSheet(f"background-color: {self.color};")
        
    def choose_color(self):
        """Open color dialog to choose event color."""
        color = QColorDialog.getColor(QColor(self.color), self)
        if color.isValid():
            self.color = color.name()
            self.update_color_button()
            
    def load_event_data(self):
        """Load event data into the form."""
        if not self.event_data:
            return
            
        self.title_edit.setText(self.event_data.get('title', ''))
        self.desc_edit.setText(self.event_data.get('description', ''))
        
        event_type = self.event_data.get('event_type', 'SCENE')
        index = self.type_combo.findText(event_type)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)
            
        self.start_date.setText(self.event_data.get('start_date', ''))
        self.end_date.setText(self.event_data.get('end_date', ''))
        self.location_edit.setText(self.event_data.get('location', ''))
        self.importance_spin.setValue(self.event_data.get('importance', 3))
        
        self.color = self.event_data.get('color', '#3498db')
        self.update_color_button()
        
        self.milestone_check.setChecked(bool(self.event_data.get('is_milestone', False)))
        self.sequence_spin.setValue(self.event_data.get('sequence_number', 0))
        
    def get_event_data(self) -> Dict[str, Any]:
        """Get event data from the form."""
        return {
            'title': self.title_edit.text(),
            'description': self.desc_edit.toPlainText(),
            'event_type': self.type_combo.currentText(),
            'start_date': self.start_date.text(),
            'end_date': self.end_date.text(),
            'location': self.location_edit.text(),
            'importance': self.importance_spin.value(),
            'color': self.color,
            'is_milestone': self.milestone_check.isChecked(),
            'sequence_number': self.sequence_spin.value(),
            'story_id': self.story_id
        }
        
    def save_event(self):
        """Save the event data."""
        event_data = self.get_event_data()
        
        if not event_data['title']:
            QMessageBox.warning(self, "Validation Error", "Event title is required.")
            return
            
        try:
            if self.event_id:
                # Update existing event
                success = update_event(
                    self.conn,
                    self.event_id,
                    title=event_data['title'],
                    description=event_data['description'],
                    event_type=event_data['event_type'],
                    start_date=event_data['start_date'],
                    end_date=event_data['end_date'],
                    location=event_data['location'],
                    importance=event_data['importance'],
                    color=event_data['color'],
                    is_milestone=event_data['is_milestone'],
                    sequence_number=event_data['sequence_number']
                )
                
                if success:
                    # Process character tags
                    self.process_character_tags(self.event_id, event_data)
                    self.accept()
                else:
                    QMessageBox.critical(self, "Error", "Failed to update event.")
            else:
                # Create new event
                event_id = create_event(
                    self.conn,
                    title=event_data['title'],
                    story_id=self.story_id,
                    description=event_data['description'],
                    event_type=event_data['event_type'],
                    start_date=event_data['start_date'],
                    end_date=event_data['end_date'],
                    location=event_data['location'],
                    importance=event_data['importance'],
                    color=event_data['color'],
                    is_milestone=event_data['is_milestone'],
                    sequence_number=event_data['sequence_number']
                )
                
                if event_id:
                    # Process character tags
                    self.process_character_tags(event_id, event_data)
                    self.event_id = event_id
                    self.accept()
                else:
                    QMessageBox.critical(self, "Error", "Failed to create event.")
                    
        except Exception as e:
            logger.error(f"Error saving event: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            
    def process_character_tags(self, event_id: int, event_data: Dict[str, Any]):
        """Process character tags from title and description.
        
        Args:
            event_id: ID of the event
            event_data: Event data dictionary
        """
        # Extract character tags from title and description
        title_tags = self.parse_character_tags(event_data['title'])
        desc_tags = self.parse_character_tags(event_data['description'])
        
        # Combine and remove duplicates
        character_ids = list(set(title_tags + desc_tags))
        
        if not character_ids:
            return
            
        # Get existing character associations
        try:
            existing_chars = get_event_characters(self.conn, event_id)
            existing_char_ids = [char['id'] for char in existing_chars]
            
            # Add new character associations
            for char_id in character_ids:
                if char_id not in existing_char_ids:
                    add_character_to_event(self.conn, event_id, char_id, "TAGGED")
                    
        except Exception as e:
            logger.error(f"Error processing character tags: {e}")
            # Continue without failing the whole save operation

    def update_character_suggestions(self):
        """Update the character suggestions label."""
        if not self.characters:
            self.char_suggestions_label.hide()
            self.char_suggestions.hide()
            return
            
        # Create a formatted list of character names
        char_names = []
        for char in self.characters:
            name = char['name']
            if char.get('is_main_character'):
                name = f"<b>{name}</b>"  # Bold for main characters
            char_names.append(name)
            
        # Join with commas
        char_list = ", ".join(char_names)
        self.char_suggestions.setText(char_list)
        
    def check_for_character_tag(self):
        """Check if the user is typing a character tag and provide suggestions."""
        cursor = self.desc_edit.textCursor()
        text = self.desc_edit.toPlainText()
        
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
                    cursor_rect = self.desc_edit.cursorRect()
                    global_pos = self.desc_edit.mapToGlobal(cursor_rect.bottomLeft())
                    
                    self.tag_completer.set_filter(partial_tag)
                    self.tag_completer.move(global_pos)
                    return
                    
        # Hide the completer if we're not typing a tag
        self.tag_completer.hide()
        
    def check_for_character_tag_in_title(self):
        """Check if the user is typing a character tag in the title field and provide suggestions."""
        text = self.title_edit.text()
        cursor_pos = self.title_edit.cursorPosition()
        
        # Find the current word being typed
        start = max(0, cursor_pos - 1)
        
        # Check if we're in the middle of typing a tag
        if start >= 0 and cursor_pos <= len(text):
            # Look backward to find the start of the current tag
            tag_start = text.rfind('@', 0, cursor_pos)
            
            if tag_start >= 0 and tag_start < cursor_pos:
                # We found a @ character before the cursor
                # Extract the partial tag text
                partial_tag = text[tag_start + 1:cursor_pos]
                
                # Only show suggestions if we're actively typing a tag
                if tag_start == cursor_pos - 1 or partial_tag.strip():
                    # Position the completer popup below the cursor
                    cursor_rect = self.title_edit.cursorRect()
                    global_pos = self.title_edit.mapToGlobal(cursor_rect.bottomLeft())
                    
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
        # Check which widget has focus
        if self.desc_edit.hasFocus():
            cursor = self.desc_edit.textCursor()
            text = self.desc_edit.toPlainText()
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
                self.desc_edit.setFocus()
        elif self.title_edit.hasFocus():
            text = self.title_edit.text()
            pos = self.title_edit.cursorPosition()
            
            # Find the start of the current tag
            tag_start = text.rfind('@', 0, pos)
            
            if tag_start >= 0:
                # Replace the partial tag with the full tag
                new_text = text[:tag_start] + f"@{character_name} " + text[pos:]
                self.title_edit.setText(new_text)
                
                # Set cursor position after the inserted tag
                new_pos = tag_start + len(f"@{character_name} ")
                self.title_edit.setCursorPosition(new_pos)
                
                # Set focus back to the line edit
                self.title_edit.setFocus()

    def get_next_sequence_number(self) -> int:
        """Get the next sequence number for a new event.
        
        Returns:
            The sequence number that will place the new event after the last event
        """
        try:
            # Get all events for this story
            events = get_story_events(self.conn, self.story_id)
            
            if not events:
                return 0
                
            # Find the maximum sequence number
            max_sequence = max(event.get('sequence_number', 0) for event in events)
            
            # Return the next sequence number (max + 1)
            return max_sequence + 1
            
        except Exception as e:
            logger.error(f"Error getting next sequence number: {e}")
            return 0


class TimelineWidget(QWidget):
    """Widget for displaying and managing a timeline of events."""
    
    def __init__(self, conn, story_id: int, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.story_id = story_id
        self.events = []
        self.selected_event_id = None
        self.timeline_views = []
        self.current_view_id = None
        self.current_view_type = "CHRONOLOGICAL"
        
        self.init_ui()
        self.load_events()
        self.load_timeline_views()
        
    def init_ui(self):
        """Initialize the UI components."""
        main_layout = QVBoxLayout()
        
        # Toolbar
        toolbar = QToolBar()
        
        # Add event button
        self.add_event_btn = QToolButton()
        self.add_event_btn.setText("Add Event")
        self.add_event_btn.setToolTip("Add a new event")
        self.add_event_btn.clicked.connect(self.add_event)
        toolbar.addWidget(self.add_event_btn)
        
        toolbar.addSeparator()
        
        # View selector
        view_label = QLabel("Timeline View:")
        toolbar.addWidget(view_label)
        
        self.view_selector = QComboBox()
        self.view_selector.setMinimumWidth(150)
        self.view_selector.currentIndexChanged.connect(self.change_view)
        toolbar.addWidget(self.view_selector)
        
        # Add view button
        self.add_view_btn = QToolButton()
        self.add_view_btn.setText("+")
        self.add_view_btn.setToolTip("Create new timeline view")
        self.add_view_btn.clicked.connect(self.add_timeline_view)
        toolbar.addWidget(self.add_view_btn)
        
        # Edit view button
        self.edit_view_btn = QToolButton()
        self.edit_view_btn.setText("⚙")
        self.edit_view_btn.setToolTip("Edit current timeline view")
        self.edit_view_btn.clicked.connect(self.edit_timeline_view)
        toolbar.addWidget(self.edit_view_btn)
        
        toolbar.addSeparator()
        
        # View type selector
        view_type_label = QLabel("View Type:")
        toolbar.addWidget(view_type_label)
        
        self.view_type_selector = QComboBox()
        self.view_type_selector.addItems(["Chronological", "Hierarchical"])
        self.view_type_selector.currentIndexChanged.connect(self.change_view_type)
        toolbar.addWidget(self.view_type_selector)
        
        toolbar.addSeparator()
        
        # Filter options
        filter_label = QLabel("Filter:")
        toolbar.addWidget(filter_label)
        
        self.filter_type = QComboBox()
        self.filter_type.addItems(["All", "Scenes", "Chapters", "Arcs", "Milestones"])
        self.filter_type.currentIndexChanged.connect(self.apply_filters)
        toolbar.addWidget(self.filter_type)
        
        main_layout.addWidget(toolbar)
        
        # Timeline content area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create a container for the timeline content
        self.timeline_container = QWidget()
        self.timeline_container_layout = QVBoxLayout(self.timeline_container)
        
        # Create the horizontal timeline widget
        self.horizontal_timeline = HorizontalTimelineWidget(self)
        self.horizontal_timeline.event_clicked.connect(self.select_event)
        self.timeline_container_layout.addWidget(self.horizontal_timeline)
        
        # Create the list view widget (initially hidden)
        self.timeline_content = QWidget()
        self.timeline_layout = QVBoxLayout(self.timeline_content)
        self.timeline_container_layout.addWidget(self.timeline_content)
        self.timeline_content.hide()  # Hide by default, show horizontal timeline
        
        self.scroll_area.setWidget(self.timeline_container)
        main_layout.addWidget(self.scroll_area)
        
        # Event details area
        self.details_frame = QFrame()
        self.details_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.details_frame.setMaximumHeight(150)
        
        details_layout = QVBoxLayout(self.details_frame)
        
        self.event_title_label = QLabel("Select an event to view details")
        self.event_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        self.event_title_label.setFont(font)
        
        self.event_details_label = QLabel("")
        self.event_details_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.event_details_label.setWordWrap(True)
        
        details_button_layout = QHBoxLayout()
        self.edit_event_btn = QPushButton("Edit Event")
        self.edit_event_btn.clicked.connect(self.edit_event)
        self.edit_event_btn.setEnabled(False)
        
        self.delete_event_btn = QPushButton("Delete Event")
        self.delete_event_btn.clicked.connect(self.delete_event)
        self.delete_event_btn.setEnabled(False)
        
        # Add move left/right buttons for reordering events
        self.move_left_btn = QPushButton("← Move Earlier")
        self.move_left_btn.clicked.connect(self.move_event_earlier)
        self.move_left_btn.setEnabled(False)
        
        self.move_right_btn = QPushButton("Move Later →")
        self.move_right_btn.clicked.connect(self.move_event_later)
        self.move_right_btn.setEnabled(False)
        
        details_button_layout.addWidget(self.move_left_btn)
        details_button_layout.addWidget(self.edit_event_btn)
        details_button_layout.addWidget(self.delete_event_btn)
        details_button_layout.addWidget(self.move_right_btn)
        
        details_layout.addWidget(self.event_title_label)
        details_layout.addWidget(self.event_details_label)
        details_layout.addLayout(details_button_layout)
        
        main_layout.addWidget(self.details_frame)
        
        self.setLayout(main_layout)
        
    def load_events(self):
        """Load events from the database."""
        try:
            if self.story_id <= 0:
                return
                
            self.events = get_story_events(self.conn, self.story_id)
            self.display_events()
            self.horizontal_timeline.set_events(self.filter_events())
        except Exception as e:
            logger.error(f"Error loading events: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load events: {str(e)}")
            
    def display_events(self):
        """Display events in the timeline."""
        # Clear existing events
        while self.timeline_layout.count():
            item = self.timeline_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        # Apply filters
        filtered_events = self.filter_events()
        
        if not filtered_events:
            empty_label = QLabel("No events to display. Create your first event using the 'Add Event' button.")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.timeline_layout.addWidget(empty_label)
            return
            
        # Create a chronological layout
        for event in filtered_events:
            event_widget = EventItem(event, conn=self.conn)
            event_widget.clicked.connect(self.select_event)
            
            if self.selected_event_id and event['id'] == self.selected_event_id:
                event_widget.set_selected(True)
                
            self.timeline_layout.addWidget(event_widget)
            
        # Add stretch to push events to the top
        self.timeline_layout.addStretch()
        
    def filter_events(self) -> List[Dict[str, Any]]:
        """Apply filters to the events list."""
        filter_text = self.filter_type.currentText()
        
        if filter_text == "All":
            return self.events
            
        filtered = []
        for event in self.events:
            if filter_text == "Scenes" and event.get('event_type') == "SCENE":
                filtered.append(event)
            elif filter_text == "Chapters" and event.get('event_type') == "CHAPTER":
                filtered.append(event)
            elif filter_text == "Arcs" and event.get('event_type') == "ARC":
                filtered.append(event)
            elif filter_text == "Milestones" and event.get('is_milestone'):
                filtered.append(event)
                
        return filtered
        
    def apply_filters(self):
        """Apply the current filters and refresh the display."""
        self.display_events()
        self.horizontal_timeline.set_events(self.filter_events())
        
    def select_event(self, event_id: int):
        """Handle event selection."""
        self.selected_event_id = event_id
        
        # Update UI
        self.edit_event_btn.setEnabled(True)
        self.delete_event_btn.setEnabled(True)
        self.move_left_btn.setEnabled(True)
        self.move_right_btn.setEnabled(True)
        
        # Get event details
        event = next((e for e in self.events if e['id'] == event_id), None)
        if event:
            self.event_title_label.setText(event['title'])
            
            details = ""
            if event.get('description'):
                details += f"<b>Description:</b> {event['description']}<br>"
            if event.get('event_type'):
                details += f"<b>Type:</b> {event['event_type']}<br>"
            if event.get('start_date'):
                details += f"<b>Start:</b> {event['start_date']}"
                if event.get('end_date'):
                    details += f" <b>End:</b> {event['end_date']}"
                details += "<br>"
            if event.get('location'):
                details += f"<b>Location:</b> {event['location']}<br>"
            
            # Add sequence number to details
            details += f"<b>Sequence:</b> {event.get('sequence_number', 0)}<br>"
            
            # Add tagged characters
            try:
                event_characters = get_event_characters(self.conn, event_id)
                if event_characters:
                    char_names = [char['name'] for char in event_characters]
                    details += f"<b>Characters:</b> {', '.join(char_names)}<br>"
            except Exception as e:
                logger.error(f"Error getting event characters: {e}")
                
            self.event_details_label.setText(details)
            
            # Update selection in horizontal timeline
            self.horizontal_timeline.set_selected_event(event_id)
        
        # Refresh display to update selection
        self.display_events()
        
    def add_event(self):
        """Open dialog to add a new event."""
        dialog = EventDialog(self.conn, self.story_id, self)
        if dialog.exec():
            self.load_events()
            
            # Select the newly created event
            if dialog.event_id:
                self.selected_event_id = dialog.event_id
                self.select_event(dialog.event_id)
                
                # Ensure the horizontal timeline is scrolled to show the new event
                if self.current_view_type == "CHRONOLOGICAL":
                    # Use QTimer to ensure the UI has updated before scrolling
                    QTimer.singleShot(100, self.scroll_to_selected_event)
            
    def edit_event(self):
        """Open dialog to edit the selected event."""
        if not self.selected_event_id:
            return
            
        dialog = EventDialog(self.conn, self.story_id, self, self.selected_event_id)
        if dialog.exec():
            self.load_events()
            
    def delete_event(self):
        """Delete the selected event."""
        if not self.selected_event_id:
            return
            
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this event? This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            success = delete_event(self.conn, self.selected_event_id)
            if success:
                self.selected_event_id = None
                self.edit_event_btn.setEnabled(False)
                self.delete_event_btn.setEnabled(False)
                self.event_title_label.setText("Select an event to view details")
                self.event_details_label.setText("")
                self.load_events()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete event.")
                
    def load_timeline_views(self):
        """Load timeline views from the database."""
        try:
            if self.story_id <= 0:
                return
                
            self.timeline_views = get_story_timeline_views(self.conn, self.story_id)
            
            # Clear and repopulate the view selector
            self.view_selector.clear()
            
            if not self.timeline_views:
                # Create a default view if none exists
                default_view_id = create_timeline_view(
                    self.conn,
                    "Default View",
                    self.story_id,
                    "Default chronological view",
                    "CHRONOLOGICAL"
                )
                
                if default_view_id:
                    self.timeline_views = get_story_timeline_views(self.conn, self.story_id)
                    
            for view in self.timeline_views:
                self.view_selector.addItem(view['name'], view['id'])
                
            # Select the first view or the current view if it exists
            if self.current_view_id:
                index = self.view_selector.findData(self.current_view_id)
                if index >= 0:
                    self.view_selector.setCurrentIndex(index)
                else:
                    self.current_view_id = None
                    
            if not self.current_view_id and self.timeline_views:
                self.current_view_id = self.timeline_views[0]['id']
                
        except Exception as e:
            logger.error(f"Error loading timeline views: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load timeline views: {str(e)}")
            
    def change_view(self, index: int):
        """Change the current timeline view."""
        if index < 0 or not self.timeline_views:
            return
            
        view_id = self.view_selector.itemData(index)
        if view_id != self.current_view_id:
            self.current_view_id = view_id
            # In a real implementation, this would load the specific view layout
            self.display_events()
            self.horizontal_timeline.set_events(self.filter_events())
            
    def change_view_type(self, index: int):
        """Change the timeline view type."""
        view_type = self.view_type_selector.currentText()
        
        if view_type == "Chronological":
            self.current_view_type = "CHRONOLOGICAL"
            self.horizontal_timeline.show()
            self.timeline_content.hide()
        else:
            self.current_view_type = "HIERARCHICAL"
            self.horizontal_timeline.hide()
            self.timeline_content.show()
            
    def add_timeline_view(self):
        """Add a new timeline view."""
        # This would be a dialog in a real implementation
        name, ok = QInputDialog.getText(self, "New Timeline View", "View Name:")
        if ok and name:
            view_id = create_timeline_view(self.conn, name, self.story_id)
            if view_id:
                self.load_timeline_views()
                # Select the new view
                index = self.view_selector.findData(view_id)
                if index >= 0:
                    self.view_selector.setCurrentIndex(index)
            else:
                QMessageBox.critical(self, "Error", "Failed to create timeline view.")
                
    def edit_timeline_view(self):
        """Edit the current timeline view."""
        if not self.current_view_id:
            return
            
        # This would be a dialog in a real implementation
        view = next((v for v in self.timeline_views if v['id'] == self.current_view_id), None)
        if not view:
            return
            
        name, ok = QInputDialog.getText(
            self, "Edit Timeline View", "View Name:", 
            QLineEdit.EchoMode.Normal, view['name']
        )
        
        if ok and name:
            success = update_timeline_view(self.conn, self.current_view_id, name=name)
            if success:
                self.load_timeline_views()
            else:
                QMessageBox.critical(self, "Error", "Failed to update timeline view.")

    def move_event_earlier(self):
        """Move the selected event earlier in the timeline (decrease sequence number)."""
        if not self.selected_event_id:
            return
            
        # Get the current event
        event = next((e for e in self.events if e['id'] == self.selected_event_id), None)
        if not event:
            return
            
        # Get current sequence number
        current_seq = event.get('sequence_number', 0)
        
        # Find events with lower sequence numbers
        earlier_events = [e for e in self.events if e.get('sequence_number', 0) < current_seq]
        
        if not earlier_events:
            # Already at the beginning
            QMessageBox.information(self, "Information", "This event is already at the beginning of the timeline.")
            return
            
        # Find the closest earlier event
        closest_earlier = max(earlier_events, key=lambda e: e.get('sequence_number', 0))
        new_seq = closest_earlier.get('sequence_number', 0)
        
        # Update the sequence number
        success = update_event(
            self.conn,
            self.selected_event_id,
            sequence_number=new_seq
        )
        
        if success:
            # Update the closest earlier event to have the current event's sequence number
            update_event(
                self.conn,
                closest_earlier['id'],
                sequence_number=current_seq
            )
            
            # Reload events
            self.load_events()
        else:
            QMessageBox.critical(self, "Error", "Failed to move event earlier.")
            
    def move_event_later(self):
        """Move the selected event later in the timeline (increase sequence number)."""
        if not self.selected_event_id:
            return
            
        # Get the current event
        event = next((e for e in self.events if e['id'] == self.selected_event_id), None)
        if not event:
            return
            
        # Get current sequence number
        current_seq = event.get('sequence_number', 0)
        
        # Find events with higher sequence numbers
        later_events = [e for e in self.events if e.get('sequence_number', 0) > current_seq]
        
        if not later_events:
            # Already at the end
            QMessageBox.information(self, "Information", "This event is already at the end of the timeline.")
            return
            
        # Find the closest later event
        closest_later = min(later_events, key=lambda e: e.get('sequence_number', 0))
        new_seq = closest_later.get('sequence_number', 0)
        
        # Update the sequence number
        success = update_event(
            self.conn,
            self.selected_event_id,
            sequence_number=new_seq
        )
        
        if success:
            # Update the closest later event to have the current event's sequence number
            update_event(
                self.conn,
                closest_later['id'],
                sequence_number=current_seq
            )
            
            # Reload events
            self.load_events()
        else:
            QMessageBox.critical(self, "Error", "Failed to move event later.")

    def scroll_to_selected_event(self):
        """Scroll the timeline to make the selected event visible."""
        if not self.selected_event_id or not self.horizontal_timeline.event_positions:
            return
            
        # Get the x position of the selected event
        x_pos = self.horizontal_timeline.event_positions.get(self.selected_event_id)
        if x_pos is None:
            return
            
        # Calculate the scroll position to center the event
        scroll_area_width = self.scroll_area.width()
        scroll_pos = max(0, x_pos - scroll_area_width // 2)
        
        # Set the horizontal scroll position
        self.scroll_area.horizontalScrollBar().setValue(scroll_pos)


class HorizontalTimelineWidget(QWidget):
    """Widget for displaying a horizontal timeline visualization."""
    
    event_clicked = pyqtSignal(int)  # Signal emitted when an event is clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.events = []
        self.selected_event_id = None
        self.timeline_start = None
        self.timeline_end = None
        self.event_positions = {}  # Maps event_id to x position
        self.conn = None
        self.event_characters = {}  # Maps event_id to list of characters
        
        # Get database connection from parent if available
        if parent and hasattr(parent, 'conn'):
            self.conn = parent.conn
        
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
    def set_events(self, events: List[Dict[str, Any]]):
        """Set the events to display on the timeline."""
        # Sort primarily by sequence_number
        self.events = sorted(events, key=lambda e: (e.get('sequence_number', 0), e.get('start_date', '')))
        self.calculate_timeline_range()
        
        # Load character data for each event
        self.load_event_characters()
        
        self.update()
        
    def load_event_characters(self):
        """Load character data for all events."""
        self.event_characters = {}
        
        if not self.conn or not self.events:
            return
            
        for event in self.events:
            try:
                characters = get_event_characters(self.conn, event['id'])
                if characters:
                    self.event_characters[event['id']] = characters
            except Exception as e:
                logger.error(f"Error loading characters for event {event['id']}: {e}")
                
    def set_selected_event(self, event_id: int):
        """Set the selected event."""
        self.selected_event_id = event_id
        self.update()
        
    def calculate_timeline_range(self):
        """Calculate the start and end of the timeline based on event dates."""
        if not self.events:
            self.timeline_start = "0"
            self.timeline_end = "100"
            return
            
        # For sequence-based timelines, use sequence numbers
        min_seq = min(e.get('sequence_number', 0) for e in self.events)
        max_seq = max(e.get('sequence_number', 0) for e in self.events)
        
        # If all events have the same sequence number, space them evenly
        if min_seq == max_seq:
            self.timeline_start = "0"
            self.timeline_end = str(len(self.events))
        else:
            self.timeline_start = str(min_seq)
            self.timeline_end = str(max_seq)
            
    def get_event_x_position(self, event: Dict[str, Any]) -> int:
        """Calculate the x position for an event based on its sequence number."""
        width = self.width() - 100  # Leave margin on both sides
        
        # Use sequence number as primary positioning factor
        sequence = event.get('sequence_number', 0)
        
        # Get min and max sequence numbers
        min_seq = int(self.timeline_start) if self.timeline_start.isdigit() else 0
        max_seq = int(self.timeline_end) if self.timeline_end.isdigit() else 100
        
        # If all events have the same sequence, space them evenly
        if min_seq == max_seq:
            index = self.events.index(event)
            return int(50 + (index / max(1, len(self.events) - 1)) * width)
        
        # Calculate position based on sequence number
        range_width = max(1, max_seq - min_seq)  # Avoid division by zero
        position = (sequence - min_seq) / range_width
        
        return int(50 + position * width)
            
    def paintEvent(self, event):
        """Paint the horizontal timeline."""
        if not self.events:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate dimensions
        width = self.width()
        height = self.height()
        timeline_y = height // 2
        
        # Draw timeline line
        painter.setPen(QPen(QColor(150, 150, 150), 2))
        painter.drawLine(50, timeline_y, width - 50, timeline_y)
        
        # Draw events
        self.event_positions = {}  # Reset positions
        
        for event in self.events:
            x_pos = self.get_event_x_position(event)
            self.event_positions[event['id']] = x_pos
            
            # Draw event marker
            event_radius = 8
            if event.get('is_milestone'):
                event_radius = 12  # Larger for milestones
                
            # Determine color
            color = QColor(event.get('color', '#3498db'))
            
            # Draw selection highlight if selected
            if self.selected_event_id and event['id'] == self.selected_event_id:
                painter.setPen(QPen(QColor(255, 165, 0), 2))
                painter.setBrush(QBrush(color))
                painter.drawEllipse(x_pos - event_radius - 2, timeline_y - event_radius - 2, 
                                   event_radius * 2 + 4, event_radius * 2 + 4)
                                   
            # Draw event marker
            painter.setPen(QPen(color.darker(150), 1))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(x_pos - event_radius, timeline_y - event_radius, 
                               event_radius * 2, event_radius * 2)
                               
            # Draw character indicators if this event has characters
            if event['id'] in self.event_characters and self.event_characters[event['id']]:
                char_count = len(self.event_characters[event['id']])
                
                # Draw a small indicator showing character count
                if char_count > 0:
                    indicator_size = 12
                    painter.setPen(QPen(QColor(255, 255, 255), 1))
                    painter.setBrush(QBrush(QColor(50, 150, 50)))  # Green for character indicator
                    
                    # Position the indicator at the top right of the event marker
                    indicator_x = x_pos + event_radius - indicator_size/2
                    indicator_y = timeline_y - event_radius - indicator_size/2
                    
                    # Create a QRectF for the ellipse
                    indicator_rect = QRectF(indicator_x, indicator_y, indicator_size, indicator_size)
                    painter.drawEllipse(indicator_rect)
                    
                    # Draw the character count
                    painter.setPen(QPen(QColor(255, 255, 255)))
                    font = QFont()
                    font.setPointSize(7)
                    painter.setFont(font)
                    
                    # Format the count text
                    count_text = str(char_count) if char_count < 10 else "9+"
                    
                    # Draw the text centered in the indicator
                    painter.drawText(
                        QRectF(indicator_x, indicator_y, indicator_size, indicator_size),
                        Qt.AlignmentFlag.AlignCenter,
                        count_text
                    )
                               
            # Draw event title
            # Alternate between above and below the timeline to avoid overlap
            index = self.events.index(event)
            if index % 2 == 0:
                text_y = timeline_y - 30
                line_start_y = timeline_y - event_radius
                line_end_y = text_y + 15
                alignment = Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter
            else:
                text_y = timeline_y + 30
                line_start_y = timeline_y + event_radius
                line_end_y = text_y - 15
                alignment = Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter
                
            # Draw connecting line - make it more visible
            painter.setPen(QPen(QColor(255, 255, 255), 1.5, Qt.PenStyle.DashLine))
            painter.drawLine(x_pos, line_start_y, x_pos, line_end_y)
            
            # Draw text
            painter.setPen(QPen(QColor(255, 255, 255)))
            font = QFont()
            font.setBold(True)
            painter.setFont(font)
            
            # Truncate title if too long
            fm = QFontMetrics(font)
            title = event['title']
            elided_title = fm.elidedText(title, Qt.TextElideMode.ElideRight, 150)
            
            # Draw text background
            text_rect = QRectF(x_pos - 75, text_y - 15, 150, 30)
            bg_path = QPainterPath()
            bg_path.addRoundedRect(text_rect, 5, 5)
            
            # Fill with semi-transparent background
            bg_color = QColor(40, 40, 40, 200)  # Semi-transparent dark background
            painter.fillPath(bg_path, QBrush(bg_color))
            
            # Add border
            painter.setPen(QPen(QColor(100, 100, 100), 1))
            painter.drawPath(bg_path)
            
            # Draw text
            painter.drawText(text_rect, alignment, elided_title)
            
        painter.end()
        
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events to select events."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Find the closest event to the click position
            click_x = event.position().x()
            closest_event_id = None
            closest_distance = float('inf')
            
            for event_id, x_pos in self.event_positions.items():
                distance = abs(click_x - x_pos)
                if distance < closest_distance and distance < 20:  # Within 20 pixels
                    closest_distance = distance
                    closest_event_id = event_id
                    
            if closest_event_id is not None:
                self.selected_event_id = closest_event_id
                self.event_clicked.emit(closest_event_id)
                self.update()
                
        super().mousePressEvent(event) 