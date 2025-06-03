#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Story Notepad Widgets for The Plot Thickens application.

This module provides widgets for managing plot details and plot questions
in the Story Notepad panel, including drag-and-drop reordering, context menus,
and character tagging functionality.
"""

import re
from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
    QMenu, QInputDialog, QMessageBox, QTextEdit, QLineEdit,
    QAbstractItemView, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QTimer
from PyQt6.QtGui import QDrag, QPixmap, QFont, QAction, QTextCharFormat, QBrush, QColor


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
        self.init_ui()
    
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
        
        # Enable drag and drop reordering
        self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        
        layout.addWidget(self.list_widget)
    
    def add_detail(self, text: str = "") -> None:
        """Add a new plot detail."""
        if not text:
            text, ok = QInputDialog.getText(self, "New Plot Detail", "Enter plot detail:")
            if not ok or not text.strip():
                return
        
        item = DraggableListItem(text.strip())
        self.list_widget.addItem(item)
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
        text, ok = QInputDialog.getText(self, "Edit Plot Detail", "Edit detail:", text=current_text)
        if ok and text.strip():
            item.setText(text.strip())
            self.items_changed.emit()
    
    def toggle_scratch_item(self, item: DraggableListItem) -> None:
        """Toggle the scratched state of an item."""
        item.set_scratched(not item.is_scratched)
        self.items_changed.emit()
    
    def delete_item(self, item: DraggableListItem) -> None:
        """Delete an item after confirmation."""
        reply = QMessageBox.question(
            self, "Delete Detail", 
            f"Are you sure you want to delete this detail?\n\n{item.text()}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            row = self.list_widget.row(item)
            self.list_widget.takeItem(row)
            self.items_changed.emit()
    
    def _on_item_changed(self, item: QListWidgetItem) -> None:
        """Handle item text changes."""
        self.items_changed.emit()
    
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
        self.init_ui()
    
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
        
        layout.addWidget(self.tree_widget)
    
    def add_question(self, text: str = "") -> None:
        """Add a new plot question."""
        if not text:
            text, ok = QInputDialog.getText(self, "New Plot Question", "Enter question:")
            if not ok or not text.strip():
                return
        
        item = DraggableTreeItem(self.tree_widget, [text.strip()])
        self.tree_widget.addTopLevelItem(item)
        self.tree_widget.expandItem(item)
        self.items_changed.emit()
    
    def add_answer(self, parent_item: DraggableTreeItem, text: str = "") -> None:
        """Add a new answer to a question."""
        if not text:
            text, ok = QInputDialog.getText(self, "New Answer", "Enter possible answer:")
            if not ok or not text.strip():
                return
        
        answer_item = DraggableTreeItem(parent_item, [text.strip()])
        parent_item.addChild(answer_item)
        self.tree_widget.expandItem(parent_item)
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
        text, ok = QInputDialog.getText(self, f"Edit {item_type}", f"Edit {item_type.lower()}:", text=current_text)
        if ok and text.strip():
            item.setText(0, text.strip())
            self.items_changed.emit()
    
    def toggle_scratch_item(self, item: DraggableTreeItem) -> None:
        """Toggle the scratched state of an item."""
        item.set_scratched(not item.is_scratched)
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
    
    def _on_content_changed(self) -> None:
        """Handle content changes - this can be used for auto-save functionality."""
        # TODO: Implement auto-save or signal to parent
        pass
    
    def set_available_characters(self, characters: List[str]) -> None:
        """Set the list of available characters for both widgets."""
        self.plot_details.set_available_characters(characters)
        self.plot_questions.set_available_characters(characters)
    
    def get_all_data(self) -> Dict[str, Any]:
        """Get all notepad data."""
        return {
            'plot_details': self.plot_details.get_all_details(),
            'plot_questions': self.plot_questions.get_all_questions()
        }
    
    def load_data(self, data: Dict[str, Any]) -> None:
        """Load notepad data."""
        if 'plot_details' in data:
            self.plot_details.load_details(data['plot_details'])
        if 'plot_questions' in data:
            self.plot_questions.load_questions(data['plot_questions']) 