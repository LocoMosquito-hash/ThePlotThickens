#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Story Notepad Widgets for The Plot Thickens application.

This module provides widgets for managing plot details and plot questions
in the Story Notepad panel, including drag-and-drop reordering, context menus,
character tagging functionality, and database persistence.
"""

import re
import json
from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
    QMenu, QInputDialog, QMessageBox, QTextEdit, QLineEdit,
    QAbstractItemView, QFrame, QStyledItemDelegate, QStyle
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QTimer, QRect, QSize
from PyQt6.QtGui import QDrag, QPixmap, QFont, QAction, QTextCharFormat, QBrush, QColor, QPainter, QFontMetrics

from app.db_sqlite import (
    get_plot_details, create_plot_detail, update_plot_detail, delete_plot_detail,
    get_plot_questions, create_plot_question, create_plot_answer,
    update_plot_question, update_plot_answer, delete_plot_question, delete_plot_answer,
    reorder_plot_details, get_story_characters
)
from app.widgets.character_input_dialog import CharacterInputDialog
from app.utils.character_references import convert_mentions_to_char_refs, convert_char_refs_to_mentions


class MultiLineListDelegate(QStyledItemDelegate):
    """Custom delegate to handle multi-line text in QListWidget items."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def sizeHint(self, option, index):
        """Calculate the size hint for multi-line text."""
        text = index.data(Qt.ItemDataRole.DisplayRole)
        if not text:
            return super().sizeHint(option, index)
        
        # Get the font metrics
        font = option.font
        font_metrics = QFontMetrics(font)
        
        # Calculate available width (subtract margins and padding)
        available_width = option.rect.width() - 20  # margin for padding
        if available_width <= 0:
            available_width = 250  # fallback width
        
        # Calculate the height needed for wrapped text
        text_rect = font_metrics.boundingRect(
            0, 0, available_width, 0,
            Qt.TextFlag.TextWordWrap | Qt.TextFlag.TextWrapAnywhere,
            text
        )
        
        # Add some padding
        height = max(text_rect.height() + 10, 25)  # minimum height of 25
        return QSize(available_width, height)
    
    def paint(self, painter, option, index):
        """Custom paint method for multi-line text."""
        text = index.data(Qt.ItemDataRole.DisplayRole)
        if not text:
            super().paint(painter, option, index)
            return
        
        # Set up the painter
        painter.save()
        
        # Draw background if selected
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
            painter.setPen(option.palette.highlightedText().color())
        else:
            painter.setPen(option.palette.text().color())
        
        # Set font (including strikeout if needed)
        painter.setFont(option.font)
        
        # Calculate text rectangle with padding
        text_rect = option.rect.adjusted(5, 5, -5, -5)
        
        # Draw the text
        painter.drawText(
            text_rect,
            Qt.TextFlag.TextWordWrap | Qt.TextFlag.TextWrapAnywhere | Qt.AlignmentFlag.AlignTop,
            text
        )
        
        painter.restore()


class MultiLineTreeDelegate(QStyledItemDelegate):
    """Custom delegate to handle multi-line text in QTreeWidget items."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def sizeHint(self, option, index):
        """Calculate the size hint for multi-line text."""
        text = index.data(Qt.ItemDataRole.DisplayRole)
        if not text:
            return super().sizeHint(option, index)
        
        # Get the font metrics
        font = option.font
        font_metrics = QFontMetrics(font)
        
        # Calculate available width (subtract margins and indentation)
        available_width = option.rect.width() - 40  # margin for padding and indentation
        if available_width <= 0:
            available_width = 200  # fallback width
        
        # Calculate the height needed for wrapped text
        text_rect = font_metrics.boundingRect(
            0, 0, available_width, 0,
            Qt.TextFlag.TextWordWrap | Qt.TextFlag.TextWrapAnywhere,
            text
        )
        
        # Add some padding
        height = max(text_rect.height() + 8, 20)  # minimum height of 20
        return QSize(available_width, height)
    
    def paint(self, painter, option, index):
        """Custom paint method for multi-line text."""
        text = index.data(Qt.ItemDataRole.DisplayRole)
        if not text:
            super().paint(painter, option, index)
            return
        
        # Set up the painter
        painter.save()
        
        # Draw background if selected
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
            painter.setPen(option.palette.highlightedText().color())
        else:
            painter.setPen(option.palette.text().color())
        
        # Set font (including strikeout if needed)
        painter.setFont(option.font)
        
        # Calculate text rectangle with padding
        text_rect = option.rect.adjusted(5, 2, -5, -2)
        
        # Draw the text
        painter.drawText(
            text_rect,
            Qt.TextFlag.TextWordWrap | Qt.TextFlag.TextWrapAnywhere | Qt.AlignmentFlag.AlignTop,
            text
        )
        
        painter.restore()


class DraggableListItem(QListWidgetItem):
    """A list item that supports drag and drop with data storage."""
    
    def __init__(self, text: str = "", parent: Optional[QListWidget] = None):
        super().__init__(text, parent)
        self.data_dict = {}
        self.is_scratched = False
        self.setFlags(self.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsDragEnabled)
    
    def set_data(self, key: str, value: Any) -> None:
        """Set custom data for this item."""
        self.data_dict[key] = value
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """Get custom data for this item."""
        return self.data_dict.get(key, default)
    
    def set_scratched(self, scratched: bool) -> None:
        """Set the scratched state of this item."""
        self.is_scratched = scratched
        self._update_appearance()
    
    def _update_appearance(self) -> None:
        """Update the visual appearance based on state."""
        font = self.font()
        if self.is_scratched:
            font.setStrikeOut(True)
        else:
            font.setStrikeOut(False)
        self.setFont(font)


class DraggableTreeItem(QTreeWidgetItem):
    """A tree item that supports drag and drop with data storage."""
    
    def __init__(self, parent: Optional[QTreeWidget] = None, strings: List[str] = None):
        if strings is None:
            strings = [""]
        super().__init__(parent, strings)
        self.data_dict = {}
        self.is_scratched = False
        self.setFlags(self.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsDragEnabled)
    
    def set_data_custom(self, key: str, value: Any) -> None:
        """Set custom data for this item."""
        self.data_dict[key] = value
    
    def get_data_custom(self, key: str, default: Any = None) -> Any:
        """Get custom data for this item."""
        return self.data_dict.get(key, default)
    
    def set_scratched(self, scratched: bool) -> None:
        """Set the scratched state of this item."""
        self.is_scratched = scratched
        self._update_appearance()
    
    def _update_appearance(self) -> None:
        """Update the visual appearance based on state."""
        font = self.font(0)
        if self.is_scratched:
            font.setStrikeOut(True)
        else:
            font.setStrikeOut(False)
        self.setFont(0, font)


class CharacterTagger:
    """Utility class for handling character tagging in text."""
    
    CHARACTER_TAG_PATTERN = r'@([A-Za-z0-9_\s]+?)(?=\s|$|[^A-Za-z0-9_\s])'
    
    @staticmethod
    def extract_character_tags(text: str) -> List[str]:
        """Extract character names from @CharacterName tags in text."""
        matches = re.findall(CharacterTagger.CHARACTER_TAG_PATTERN, text)
        return [match.strip() for match in matches]
    
    @staticmethod
    def highlight_character_tags(text: str, available_characters: List[str]) -> str:
        """Return HTML-formatted text with character tags highlighted."""
        def replace_tag(match):
            character_name = match.group(1).strip()
            if character_name in available_characters:
                return f'<span style="background-color: #90EE90; padding: 2px;">@{character_name}</span>'
            else:
                return f'<span style="background-color: #FFB6C1; padding: 2px;">@{character_name}</span>'
        
        return re.sub(CharacterTagger.CHARACTER_TAG_PATTERN, replace_tag, text)


class PlotDetailsWidget(QWidget):
    """Widget for managing plot details with drag-and-drop reordering."""
    
    items_changed = pyqtSignal()  # Emitted when items are modified
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.available_characters = []
        self.story_id = None
        self.db_conn = None
        self.init_ui()
    
    def set_database(self, db_conn, story_id: int) -> None:
        """Set the database connection and story ID.
        
        Args:
            db_conn: Database connection
            story_id: ID of the current story
        """
        self.db_conn = db_conn
        self.story_id = story_id
        self.load_from_database()
    
    def load_from_database(self) -> None:
        """Load plot details from the database."""
        if not self.db_conn or not self.story_id:
            return
        
        self.list_widget.clear()
        details = get_plot_details(self.db_conn, self.story_id)
        
        for detail in details:
            item = DraggableListItem()
            # Convert [char:ID] back to @mentions for display
            display_text = convert_char_refs_to_mentions(detail['text'], self._get_character_data())
            item.setText(display_text)
            item.set_scratched(detail['is_scratched'])
            
            # Store database info
            item.set_data('db_id', detail['id'])
            item.set_data('original_text', detail['text'])  # Store the original [char:ID] format
            item.set_data('character_refs', detail['character_refs'])
            item.set_data('custom_data', detail['custom_data'])
            
            self.list_widget.addItem(item)
        
        # Update item sizes after loading all items
        QTimer.singleShot(50, self._update_item_sizes)
    
    def _get_character_data(self) -> List[Dict[str, Any]]:
        """Get character data for conversion functions."""
        if not self.db_conn or not self.story_id:
            return []
        
        characters = get_story_characters(self.db_conn, self.story_id)
        return characters
    
    def init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Header with title and add button
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Plot Details")
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        
        self.add_button = QPushButton("+")
        self.add_button.setFixedSize(24, 24)
        self.add_button.setToolTip("Add new plot detail")
        self.add_button.clicked.connect(self.add_detail)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.add_button)
        
        layout.addLayout(header_layout)
        
                # List widget for details
        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.list_widget.itemChanged.connect(self._on_item_changed)
        
        # Enable text wrapping for multi-line items
        self.list_widget.setWordWrap(True)
        self.list_widget.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        
        # Set custom delegate for multi-line text rendering
        self.list_delegate = MultiLineListDelegate(self.list_widget)
        self.list_widget.setItemDelegate(self.list_delegate)
        
        # Enable drag and drop reordering
        self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        
        layout.addWidget(self.list_widget)
    
    def add_detail(self, text: str = "") -> None:
        """Add a new plot detail."""
        if not text:
            # Use the custom character input dialog
            characters = self._get_character_data()
            text, ok = CharacterInputDialog.get_text_input(
                parent=self,
                title="New Plot Detail",
                label="Enter plot detail:",
                characters=characters
            )
            if not ok or not text.strip():
                return
        
        # Convert @mentions to [char:ID] for storage
        characters = self._get_character_data()
        storage_text = convert_mentions_to_char_refs(text.strip(), characters)
        
        # Save to database
        if self.db_conn and self.story_id:
            detail_id = create_plot_detail(
                self.db_conn,
                self.story_id,
                storage_text,
                is_scratched=False,
                order_index=self.list_widget.count()
            )
            
            # Create list item
            item = DraggableListItem(text.strip())
            item.set_data('db_id', detail_id)
            item.set_data('original_text', storage_text)
            self.list_widget.addItem(item)
        else:
            # Fallback for when database is not available
            item = DraggableListItem(text.strip())
            self.list_widget.addItem(item)
        
        # Update item sizes to accommodate multi-line text
        QTimer.singleShot(0, self._update_item_sizes)
        self.items_changed.emit()
    
    def show_context_menu(self, position) -> None:
        """Show context menu for list items."""
        item = self.list_widget.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        
        # Edit action
        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(lambda: self.edit_item(item))
        menu.addAction(edit_action)
        
        # Scratch action
        scratch_text = "Unstratch" if item.is_scratched else "Scratch"
        scratch_action = QAction(scratch_text, self)
        scratch_action.triggered.connect(lambda: self.toggle_scratch_item(item))
        menu.addAction(scratch_action)
        
        # Delete action
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.delete_item(item))
        menu.addAction(delete_action)
        
        menu.exec(self.list_widget.mapToGlobal(position))
    
    def edit_item(self, item: DraggableListItem) -> None:
        """Edit the text of an item."""
        current_text = item.text()
        characters = self._get_character_data()
        
        text, ok = CharacterInputDialog.get_text_input(
            parent=self,
            title="Edit Plot Detail",
            label="Edit detail:",
            text=current_text,
            characters=characters
        )
        
        if ok and text.strip():
            # Convert @mentions to [char:ID] for storage
            storage_text = convert_mentions_to_char_refs(text.strip(), characters)
            
            # Update database
            db_id = item.get_data('db_id')
            if self.db_conn and db_id:
                update_plot_detail(
                    self.db_conn,
                    db_id,
                    text=storage_text
                )
                item.set_data('original_text', storage_text)
            
            item.setText(text.strip())
            # Update item sizes to accommodate multi-line text
            QTimer.singleShot(0, self._update_item_sizes)
            self.items_changed.emit()
    
    def toggle_scratch_item(self, item: DraggableListItem) -> None:
        """Toggle the scratched state of an item."""
        new_scratched = not item.is_scratched
        item.set_scratched(new_scratched)
        
        # Update database
        db_id = item.get_data('db_id')
        if self.db_conn and db_id:
            update_plot_detail(
                self.db_conn,
                db_id,
                is_scratched=new_scratched
            )
        
        self.items_changed.emit()
    
    def delete_item(self, item: DraggableListItem) -> None:
        """Delete an item after confirmation."""
        reply = QMessageBox.question(
            self, "Delete Detail", 
            f"Are you sure you want to delete this detail?\n\n{item.text()}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Delete from database
            db_id = item.get_data('db_id')
            if self.db_conn and db_id:
                delete_plot_detail(self.db_conn, db_id)
            
            row = self.list_widget.row(item)
            self.list_widget.takeItem(row)
            self.items_changed.emit()
    
    def _on_item_changed(self, item: QListWidgetItem) -> None:
        """Handle item text changes."""
        self.items_changed.emit()
        # Schedule a size update to accommodate new text length
        QTimer.singleShot(0, self._update_item_sizes)
    
    def _update_item_sizes(self) -> None:
        """Update all item sizes to fit their content."""
        # Force the list widget to recalculate item sizes
        self.list_widget.doItemsLayout()
        self.list_widget.updateGeometries()
        # Force a repaint to ensure proper display
        self.list_widget.viewport().update()
    
    def set_available_characters(self, characters: List[str]) -> None:
        """Set the list of available characters for tagging."""
        self.available_characters = characters
    
    def get_all_details(self) -> List[Dict[str, Any]]:
        """Get all plot details as a list of dictionaries."""
        details = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if isinstance(item, DraggableListItem):
                detail = {
                    'text': item.text(),
                    'is_scratched': item.is_scratched,
                    'character_tags': CharacterTagger.extract_character_tags(item.text()),
                    'data': item.data_dict.copy()
                }
                details.append(detail)
        return details
    
    def load_details(self, details: List[Dict[str, Any]]) -> None:
        """Load plot details from a list of dictionaries."""
        self.list_widget.clear()
        for detail in details:
            item = DraggableListItem(detail.get('text', ''))
            item.set_scratched(detail.get('is_scratched', False))
            item.data_dict = detail.get('data', {}).copy()
            self.list_widget.addItem(item)


class PlotQuestionsWidget(QWidget):
    """Widget for managing plot questions in a hierarchical tree structure."""
    
    items_changed = pyqtSignal()  # Emitted when items are modified
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.available_characters = []
        self.story_id = None
        self.db_conn = None
        self.init_ui()
    
    def set_database(self, db_conn, story_id: int) -> None:
        """Set the database connection and story ID.
        
        Args:
            db_conn: Database connection
            story_id: ID of the current story
        """
        self.db_conn = db_conn
        self.story_id = story_id
        self.load_from_database()
    
    def load_from_database(self) -> None:
        """Load plot questions from the database."""
        if not self.db_conn or not self.story_id:
            return
        
        self.tree_widget.clear()
        questions = get_plot_questions(self.db_conn, self.story_id)
        characters = self._get_character_data()
        
        for question_data in questions:
            # Convert [char:ID] back to @mentions for display
            display_text = convert_char_refs_to_mentions(question_data['text'], characters)
            
            question_item = DraggableTreeItem(self.tree_widget, [display_text])
            question_item.set_scratched(question_data['is_scratched'])
            
            # Store database info
            question_item.set_data_custom('db_id', question_data['id'])
            question_item.set_data_custom('original_text', question_data['text'])
            question_item.set_data_custom('character_refs', question_data['character_refs'])
            question_item.set_data_custom('custom_data', question_data['custom_data'])
            
            # Add answers
            for answer_data in question_data.get('answers', []):
                answer_display_text = convert_char_refs_to_mentions(answer_data['text'], characters)
                answer_item = DraggableTreeItem(question_item, [answer_display_text])
                answer_item.set_scratched(answer_data['is_scratched'])
                
                # Store database info
                answer_item.set_data_custom('db_id', answer_data['id'])
                answer_item.set_data_custom('original_text', answer_data['text'])
                answer_item.set_data_custom('character_refs', answer_data['character_refs'])
                answer_item.set_data_custom('custom_data', answer_data['custom_data'])
                answer_item.set_data_custom('is_answer', True)
            
            self.tree_widget.addTopLevelItem(question_item)
            self.tree_widget.expandItem(question_item)
        
        # Update item sizes after loading all items
        QTimer.singleShot(50, self._update_tree_item_sizes)
    
    def _get_character_data(self) -> List[Dict[str, Any]]:
        """Get character data for conversion functions."""
        if not self.db_conn or not self.story_id:
            return []
        
        characters = get_story_characters(self.db_conn, self.story_id)
        return characters
    
    def init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Header with title and add button
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Plot Questions")
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        
        self.add_button = QPushButton("+")
        self.add_button.setFixedSize(24, 24)
        self.add_button.setToolTip("Add new plot question")
        self.add_button.clicked.connect(self.add_question)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.add_button)
        
        layout.addLayout(header_layout)
        
        # Tree widget for questions and answers
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.tree_widget.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.tree_widget.itemChanged.connect(self._on_item_changed)
        
        # Enable text wrapping for multi-line items
        self.tree_widget.setWordWrap(True)
        self.tree_widget.setTextElideMode(Qt.TextElideMode.ElideNone)
        
        # Set custom delegate for multi-line text rendering
        self.tree_delegate = MultiLineTreeDelegate(self.tree_widget)
        self.tree_widget.setItemDelegate(self.tree_delegate)
        
        # Connect to resize columns when items change
        self.tree_widget.itemExpanded.connect(self._adjust_column_width)
        self.tree_widget.itemCollapsed.connect(self._adjust_column_width)
        
        layout.addWidget(self.tree_widget)
    
    def add_question(self, text: str = "") -> None:
        """Add a new plot question."""
        if not text:
            characters = self._get_character_data()
            text, ok = CharacterInputDialog.get_text_input(
                parent=self,
                title="New Plot Question",
                label="Enter question:",
                characters=characters
            )
            if not ok or not text.strip():
                return
        
        # Convert @mentions to [char:ID] for storage
        characters = self._get_character_data()
        storage_text = convert_mentions_to_char_refs(text.strip(), characters)
        
        # Save to database
        if self.db_conn and self.story_id:
            question_id = create_plot_question(
                self.db_conn,
                self.story_id,
                storage_text,
                is_scratched=False,
                order_index=self.tree_widget.topLevelItemCount()
            )
            
            # Create tree item
            item = DraggableTreeItem(self.tree_widget, [text.strip()])
            item.set_data_custom('db_id', question_id)
            item.set_data_custom('original_text', storage_text)
            self.tree_widget.addTopLevelItem(item)
        else:
            # Fallback for when database is not available
            item = DraggableTreeItem(self.tree_widget, [text.strip()])
            self.tree_widget.addTopLevelItem(item)
        
        self.tree_widget.expandItem(item)
        # Update item sizes to accommodate multi-line text
        QTimer.singleShot(0, self._update_tree_item_sizes)
        self.items_changed.emit()
    
    def add_answer(self, parent_item: DraggableTreeItem, text: str = "") -> None:
        """Add a new answer to a question."""
        if not text:
            characters = self._get_character_data()
            text, ok = CharacterInputDialog.get_text_input(
                parent=self,
                title="New Answer",
                label="Enter possible answer:",
                characters=characters
            )
            if not ok or not text.strip():
                return
        
        # Convert @mentions to [char:ID] for storage
        characters = self._get_character_data()
        storage_text = convert_mentions_to_char_refs(text.strip(), characters)
        
        # Save to database
        if self.db_conn and self.story_id:
            parent_db_id = parent_item.get_data_custom('db_id')
            if parent_db_id:
                answer_id = create_plot_answer(
                    self.db_conn,
                    parent_db_id,
                    storage_text,
                    is_scratched=False,
                    order_index=parent_item.childCount()
                )
                
                # Create tree item
                answer_item = DraggableTreeItem(parent_item, [text.strip()])
                answer_item.set_data_custom('db_id', answer_id)
                answer_item.set_data_custom('original_text', storage_text)
                answer_item.set_data_custom('is_answer', True)
            else:
                # Fallback for items without database ID
                answer_item = DraggableTreeItem(parent_item, [text.strip()])
                answer_item.set_data_custom('is_answer', True)
        else:
            # Fallback for when database is not available
            answer_item = DraggableTreeItem(parent_item, [text.strip()])
            answer_item.set_data_custom('is_answer', True)
        
        parent_item.addChild(answer_item)
        self.tree_widget.expandItem(parent_item)
        # Update item sizes to accommodate multi-line text
        QTimer.singleShot(0, self._update_tree_item_sizes)
        self.items_changed.emit()
    
    def show_context_menu(self, position) -> None:
        """Show context menu for tree items."""
        item = self.tree_widget.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        
        # Edit action
        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(lambda: self.edit_item(item))
        menu.addAction(edit_action)
        
        # Add answer action (only for top-level questions)
        if item.parent() is None:  # Top-level question
            add_answer_action = QAction("Add Answer", self)
            add_answer_action.triggered.connect(lambda: self.add_answer(item))
            menu.addAction(add_answer_action)
        
        menu.addSeparator()
        
        # Scratch action
        scratch_text = "Unstratch" if item.is_scratched else "Scratch"
        scratch_action = QAction(scratch_text, self)
        scratch_action.triggered.connect(lambda: self.toggle_scratch_item(item))
        menu.addAction(scratch_action)
        
        # Delete action
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.delete_item(item))
        menu.addAction(delete_action)
        
        menu.exec(self.tree_widget.mapToGlobal(position))
    
    def edit_item(self, item: DraggableTreeItem) -> None:
        """Edit the text of an item."""
        current_text = item.text(0)
        item_type = "Question" if item.parent() is None else "Answer"
        characters = self._get_character_data()
        
        text, ok = CharacterInputDialog.get_text_input(
            parent=self,
            title=f"Edit {item_type}",
            label=f"Edit {item_type.lower()}:",
            text=current_text,
            characters=characters
        )
        
        if ok and text.strip():
            # Convert @mentions to [char:ID] for storage
            storage_text = convert_mentions_to_char_refs(text.strip(), characters)
            
            # Update database
            db_id = item.get_data_custom('db_id')
            if self.db_conn and db_id:
                if item.parent() is None:  # Question
                    update_plot_question(
                        self.db_conn,
                        db_id,
                        text=storage_text
                    )
                else:  # Answer
                    update_plot_answer(
                        self.db_conn,
                        db_id,
                        text=storage_text
                    )
                item.set_data_custom('original_text', storage_text)
            
            item.setText(0, text.strip())
            # Update item sizes to accommodate multi-line text
            QTimer.singleShot(0, self._update_tree_item_sizes)
            self.items_changed.emit()
    
    def toggle_scratch_item(self, item: DraggableTreeItem) -> None:
        """Toggle the scratched state of an item."""
        new_scratched = not item.is_scratched
        item.set_scratched(new_scratched)
        
        # Update database
        db_id = item.get_data_custom('db_id')
        if self.db_conn and db_id:
            if item.parent() is None:  # Question
                update_plot_question(
                    self.db_conn,
                    db_id,
                    is_scratched=new_scratched
                )
            else:  # Answer
                update_plot_answer(
                    self.db_conn,
                    db_id,
                    is_scratched=new_scratched
                )
        
        self.items_changed.emit()
    
    def delete_item(self, item: DraggableTreeItem) -> None:
        """Delete an item after confirmation."""
        item_type = "question" if item.parent() is None else "answer"
        reply = QMessageBox.question(
            self, f"Delete {item_type.title()}", 
            f"Are you sure you want to delete this {item_type}?\n\n{item.text(0)}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Delete from database
            db_id = item.get_data_custom('db_id')
            if self.db_conn and db_id:
                if item.parent() is None:  # Question
                    delete_plot_question(self.db_conn, db_id)
                else:  # Answer
                    delete_plot_answer(self.db_conn, db_id)
            
            if item.parent() is None:
                # Top-level item
                index = self.tree_widget.indexOfTopLevelItem(item)
                self.tree_widget.takeTopLevelItem(index)
            else:
                # Child item
                item.parent().removeChild(item)
            self.items_changed.emit()
    
    def _on_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle item text changes."""
        self.items_changed.emit()
        self._adjust_column_width()
    
    def _adjust_column_width(self) -> None:
        """Adjust column width to fit content and enable proper wrapping."""
        self.tree_widget.resizeColumnToContents(0)
        # Schedule item size update
        QTimer.singleShot(0, self._update_tree_item_sizes)
    
    def _update_tree_item_sizes(self) -> None:
        """Update all tree item sizes to fit their content."""
        # Force a refresh of the tree widget to update item heights
        self.tree_widget.doItemsLayout()
        # Update the viewport to reflect size changes
        self.tree_widget.viewport().update()
    
    def set_available_characters(self, characters: List[str]) -> None:
        """Set the list of available characters for tagging."""
        self.available_characters = characters
    
    def get_all_questions(self) -> List[Dict[str, Any]]:
        """Get all plot questions as a list of dictionaries."""
        questions = []
        for i in range(self.tree_widget.topLevelItemCount()):
            item = self.tree_widget.topLevelItem(i)
            if isinstance(item, DraggableTreeItem):
                question = {
                    'text': item.text(0),
                    'is_scratched': item.is_scratched,
                    'character_tags': CharacterTagger.extract_character_tags(item.text(0)),
                    'data': item.data_dict.copy(),
                    'answers': []
                }
                
                # Get answers
                for j in range(item.childCount()):
                    child = item.child(j)
                    if isinstance(child, DraggableTreeItem):
                        answer = {
                            'text': child.text(0),
                            'is_scratched': child.is_scratched,
                            'character_tags': CharacterTagger.extract_character_tags(child.text(0)),
                            'data': child.data_dict.copy()
                        }
                        question['answers'].append(answer)
                
                questions.append(question)
        return questions
    
    def load_questions(self, questions: List[Dict[str, Any]]) -> None:
        """Load plot questions from a list of dictionaries."""
        self.tree_widget.clear()
        for question_data in questions:
            question_item = DraggableTreeItem(self.tree_widget, [question_data.get('text', '')])
            question_item.set_scratched(question_data.get('is_scratched', False))
            question_item.data_dict = question_data.get('data', {}).copy()
            
            # Add answers
            for answer_data in question_data.get('answers', []):
                answer_item = DraggableTreeItem(question_item, [answer_data.get('text', '')])
                answer_item.set_scratched(answer_data.get('is_scratched', False))
                answer_item.data_dict = answer_data.get('data', {}).copy()
            
            self.tree_widget.addTopLevelItem(question_item)
            self.tree_widget.expandItem(question_item)


class StoryNotepadContent(QWidget):
    """Main content widget for the Story Notepad containing both Plot Details and Plot Questions."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.db_conn = None
        self.story_id = None
        self.init_ui()
    
    def init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Plot Details section
        self.plot_details = PlotDetailsWidget()
        layout.addWidget(self.plot_details)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Plot Questions section
        self.plot_questions = PlotQuestionsWidget()
        layout.addWidget(self.plot_questions)
        
        # Connect signals
        self.plot_details.items_changed.connect(self._on_content_changed)
        self.plot_questions.items_changed.connect(self._on_content_changed)
    
    def set_database(self, db_conn, story_id: int) -> None:
        """Set the database connection for both child widgets.
        
        Args:
            db_conn: Database connection
            story_id: ID of the current story
        """
        self.db_conn = db_conn
        self.story_id = story_id
        
        # Pass database connection to child widgets
        self.plot_details.set_database(db_conn, story_id)
        self.plot_questions.set_database(db_conn, story_id)
    
    def _on_content_changed(self) -> None:
        """Handle content changes - this can be used for auto-save functionality."""
        # Content is now automatically saved to database, so we don't need to do anything here
        pass
    
    def set_available_characters(self, characters: List[str]) -> None:
        """Set the list of available characters for both widgets."""
        self.plot_details.set_available_characters(characters)
        self.plot_questions.set_available_characters(characters)
    
    def get_all_data(self) -> Dict[str, Any]:
        """Get all notepad data from the database.
        
        This method is kept for compatibility but now reads from the database.
        """
        if not self.db_conn or not self.story_id:
            return {'plot_details': [], 'plot_questions': []}
        
        # Get data from database
        plot_details_data = get_plot_details(self.db_conn, self.story_id)
        plot_questions_data = get_plot_questions(self.db_conn, self.story_id)
        
        # Convert to the expected format
        characters = get_story_characters(self.db_conn, self.story_id)
        
        details = []
        for detail in plot_details_data:
            # Convert [char:ID] back to @mentions for display
            display_text = convert_char_refs_to_mentions(detail['text'], characters)
            details.append({
                'text': display_text,
                'is_scratched': detail['is_scratched'],
                'character_tags': CharacterTagger.extract_character_tags(display_text),
                'data': json.loads(detail.get('custom_data', '{}'))
            })
        
        questions = []
        for question in plot_questions_data:
            # Convert [char:ID] back to @mentions for display
            display_text = convert_char_refs_to_mentions(question['text'], characters)
            question_item = {
                'text': display_text,
                'is_scratched': question['is_scratched'],
                'character_tags': CharacterTagger.extract_character_tags(display_text),
                'data': json.loads(question.get('custom_data', '{}')),
                'answers': []
            }
            
            # Process answers
            for answer in question.get('answers', []):
                answer_display_text = convert_char_refs_to_mentions(answer['text'], characters)
                question_item['answers'].append({
                    'text': answer_display_text,
                    'is_scratched': answer['is_scratched'],
                    'character_tags': CharacterTagger.extract_character_tags(answer_display_text),
                    'data': json.loads(answer.get('custom_data', '{}'))
                })
            
            questions.append(question_item)
        
        return {
            'plot_details': details,
            'plot_questions': questions
        }
    
    def load_data(self, data: Dict[str, Any]) -> None:
        """Load notepad data.
        
        This method is kept for compatibility but data is now loaded from database automatically.
        """
        # If database is available, reload from database instead
        if self.db_conn and self.story_id:
            self.plot_details.load_from_database()
            self.plot_questions.load_from_database()
        else:
            # Fallback to old method for compatibility
            if 'plot_details' in data:
                self.plot_details.load_details(data['plot_details'])
            if 'plot_questions' in data:
                self.plot_questions.load_questions(data['plot_questions']) 