#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ren'Py Options tab for managing story source slots.

This module provides the PyQt6 widgets that replicate the Setup Tab Design
mockup from Figma using native components already employed by The Plot
Thickens (Qt Material styling, icon manager, etc.). The tab focuses on the
slot workflow, allowing users to add, edit, delete, and reorder source slots
in-memory while offering fully wired file dialogs and drag-and-drop helpers.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import time
import zipfile
from dataclasses import dataclass
from datetime import datetime
from functools import partial
from typing import Any, Dict, List, Literal, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QButtonGroup,
    QApplication,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.db_sqlite import (
    create_story_slot as db_create_story_slot,
    delete_story_slot as db_delete_story_slot,
    get_story_slot as db_get_story_slot,
    get_story_slots as db_get_story_slots,
    update_story_slot_record as db_update_story_slot,
)
from app.utils.icons import icon_manager


def _format_path_for_display(path: str) -> str:
    """Ensure Windows-friendly path formatting for UI display."""
    if not path:
        return ""
    normalized = os.path.normpath(path)
    return normalized.replace("/", "\\")


def _parse_db_timestamp(value: Optional[str]) -> datetime:
    if not value:
        return datetime.now()
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return datetime.now()

SourceType = Literal["directory", "compressed"]


@dataclass
class RenpySlot:
    """Represents a configured source slot."""

    slot_id: str
    slot_number: int
    source_type: SourceType
    destination_path: str
    original_source_path: str
    date_added: datetime


@dataclass
class SlotFormData:
    """Data returned from the slot modal form."""

    source_path: str
    source_type: SourceType
    destination_path: str
    slot_number: int


class SlotDropArea(QFrame):
    """Simple drag-and-drop helper that accepts directories or archives."""

    path_dropped = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._mode: SourceType = "directory"
        self._is_dragging = False

        self.setObjectName("SlotDropArea")
        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumHeight(170)
        self.setStyleSheet(
            """
            #SlotDropArea {
                border: 2px dashed rgba(255, 255, 255, 0.25);
                border-radius: 10px;
                background-color: rgba(255, 255, 255, 0.02);
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(4)

        self._icon_label = QLabel("⭳")
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_font = QFont()
        icon_font.setPointSize(24)
        self._icon_label.setFont(icon_font)
        self._icon_label.setStyleSheet("color: rgba(255, 255, 255, 0.6);")

        self._headline_label = QLabel()
        self._headline_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._headline_label.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-weight: 600;")

        self._body_label = QLabel()
        self._body_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._body_label.setStyleSheet("color: rgba(255, 255, 255, 0.5);")
        self._body_label.setWordWrap(True)

        layout.addWidget(self._icon_label)
        layout.addWidget(self._headline_label)
        layout.addWidget(self._body_label)

        self._update_copy()

    def set_mode(self, mode: SourceType) -> None:
        """Switch drop validation depending on the selected source type."""
        if mode not in ("directory", "compressed"):
            raise ValueError("Unsupported drop mode.")
        self._mode = mode
        self._update_copy()

    # Drag and drop events -------------------------------------------------
    def dragEnterEvent(self, event):  # type: ignore[override]
        if self._supported_path_from_event(event):
            self._is_dragging = True
            self._update_border()
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):  # type: ignore[override]
        self._is_dragging = False
        self._update_border()
        event.accept()

    def dropEvent(self, event):  # type: ignore[override]
        self._is_dragging = False
        self._update_border()

        dropped_path = self._supported_path_from_event(event)
        if dropped_path:
            self.path_dropped.emit(dropped_path)
            event.acceptProposedAction()
        else:
            event.ignore()

    # Helpers --------------------------------------------------------------
    def _update_border(self) -> None:
        border_color = "#4dabf7" if self._is_dragging else "rgba(255, 255, 255, 0.25)"
        background = "rgba(77, 171, 247, 0.08)" if self._is_dragging else "rgba(255, 255, 255, 0.02)"
        self.setStyleSheet(
            f"""
            #SlotDropArea {{
                border: 2px dashed {border_color};
                border-radius: 10px;
                background-color: {background};
            }}
            """
        )

    def _supported_path_from_event(self, event) -> Optional[str]:
        mime_data = event.mimeData()
        if not mime_data.hasUrls():
            return None
        for url in mime_data.urls():
            local_path = url.toLocalFile()
            if not local_path:
                continue
            if self._mode == "directory" and os.path.isdir(local_path):
                return local_path
            if self._mode == "compressed" and os.path.isfile(local_path):
                extension = os.path.splitext(local_path)[1].lower()
                if extension in {".zip", ".7z", ".rar"}:
                    return local_path
        return None

    def _update_copy(self) -> None:
        if self._mode == "compressed":
            self._headline_label.setText("Drag & drop archive files")
            self._body_label.setText("Supports .zip, .7z, and .rar packages.")
        else:
            self._headline_label.setText("Drag & drop a Ren'Py directory")
            self._body_label.setText("Point to the folder that contains .rpy files.")


class EmptyStateWidget(QWidget):
    """Empty state used when no slots have been configured."""

    add_slot_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)

        icon_label = QLabel()
        icon_pixmap = icon_manager.get_icon("folder").pixmap(64, 64)
        icon_label.setPixmap(icon_pixmap)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel("No slots configured")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        body_label = QLabel(
            "Add a slot to tell The Plot Thickens where the Ren'Py files for this story live."
        )
        body_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body_label.setWordWrap(True)
        body_label.setStyleSheet("color: rgba(255, 255, 255, 0.6);")

        self.add_button = QPushButton("Add Your First Slot")
        self.add_button.setIcon(icon_manager.get_icon("plus"))
        self.add_button.clicked.connect(self.add_slot_requested.emit)

        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(body_label)
        layout.addWidget(self.add_button)


class SlotItemWidget(QFrame):
    """Card-style widget that displays a slot entry."""

    edit_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)
    move_up_requested = pyqtSignal(str)
    move_down_requested = pyqtSignal(str)

    def __init__(self, slot: RenpySlot, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.slot = slot
        self.setObjectName("SlotItemWidget")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            """
            #SlotItemWidget {
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                background-color: rgba(255, 255, 255, 0.04);
            }
            """
        )

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # Slot information
        info_layout = QVBoxLayout()
        info_layout.setSpacing(6)

        badges_layout = QHBoxLayout()
        badges_layout.setSpacing(8)

        self.slot_label = QLabel()
        self.slot_label.setStyleSheet(
            """
            QLabel {
                background-color: rgba(255, 255, 255, 0.08);
                border-radius: 4px;
                padding: 2px 8px;
                font-weight: 600;
            }
            """
        )

        self.type_label = QLabel()
        self.type_label.setStyleSheet(
            """
            QLabel {
                background-color: rgba(77, 171, 247, 0.15);
                color: #4dabf7;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 9pt;
            }
            """
        )

        badges_layout.addWidget(self.slot_label)
        badges_layout.addWidget(self.type_label)
        badges_layout.addStretch()

        path_title = QLabel("Path:")
        path_title.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 9pt;")

        self.path_label = QLabel(_format_path_for_display(slot.destination_path))
        self.path_label.setWordWrap(True)
        self.path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.path_label.setStyleSheet("font-family: Consolas, 'Fira Code', monospace;")
        origin_display = _format_path_for_display(slot.original_source_path)
        self.path_label.setToolTip(f"Copied from: {origin_display}")

        self.date_label = QLabel()
        self.date_label.setStyleSheet("color: rgba(255, 255, 255, 0.5); font-size: 9pt;")

        info_layout.addLayout(badges_layout)
        info_layout.addWidget(path_title)
        info_layout.addWidget(self.path_label)
        info_layout.addWidget(self.date_label)

        # Actions (edit/delete horizontally, move controls to the far right)
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(12)
        actions_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.move_up_button = QPushButton()
        self.move_up_button.setIcon(icon_manager.get_icon("chevron_up"))
        self.move_up_button.setToolTip("Move slot up")
        self.move_up_button.clicked.connect(lambda: self.move_up_requested.emit(self.slot.slot_id))

        self.move_down_button = QPushButton()
        self.move_down_button.setIcon(icon_manager.get_icon("chevron_down"))
        self.move_down_button.setToolTip("Move slot down")
        self.move_down_button.clicked.connect(lambda: self.move_down_requested.emit(self.slot.slot_id))

        self.edit_button = QPushButton()
        self.edit_button.setIcon(icon_manager.get_icon("edit"))
        self.edit_button.setToolTip("Edit slot")
        self.edit_button.clicked.connect(lambda: self.edit_requested.emit(self.slot.slot_id))

        self.delete_button = QPushButton()
        self.delete_button.setIcon(icon_manager.get_icon("trash"))
        self.delete_button.setToolTip("Delete slot")
        self.delete_button.clicked.connect(lambda: self.delete_requested.emit(self.slot.slot_id))

        for button in (self.move_up_button, self.move_down_button, self.edit_button, self.delete_button):
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMaximumWidth(32)

        edit_delete_layout = QHBoxLayout()
        edit_delete_layout.setSpacing(6)
        edit_delete_layout.addWidget(self.edit_button)
        edit_delete_layout.addWidget(self.delete_button)

        move_layout = QVBoxLayout()
        move_layout.setSpacing(4)
        move_layout.addWidget(self.move_up_button)
        move_layout.addWidget(self.move_down_button)

        actions_layout.addLayout(edit_delete_layout)
        actions_layout.addLayout(move_layout)

        main_layout.addLayout(info_layout, stretch=1)
        main_layout.addLayout(actions_layout)

        self.update_positioning(0, 1)
        self._refresh(slot)

    def update_positioning(self, index: int, total: int) -> None:
        """Enable or disable movement buttons based on current order."""
        self.move_up_button.setEnabled(index > 0)
        self.move_down_button.setEnabled(index < total - 1)
        self.slot_label.setText(f"Slot {self.slot.slot_number}")

    def update_slot(self, slot: RenpySlot) -> None:
        """Update textual information after edits."""
        self.slot = slot
        self._refresh(slot)

    def _refresh(self, slot: RenpySlot) -> None:
        source_text = "Directory" if slot.source_type == "directory" else "Compressed"
        self.type_label.setText(source_text)
        self.path_label.setText(_format_path_for_display(slot.destination_path))
        self.path_label.setToolTip(f"Copied from: {_format_path_for_display(slot.original_source_path)}")
        self.date_label.setText(f"Added: {slot.date_added.strftime('%b %d, %Y %H:%M')}")


class SlotModal(QDialog):
    """Modal dialog used to add or edit slots."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        slot: Optional[RenpySlot] = None,
        slot_number: int = 1,
        destination_path: Optional[str] = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Ren'Py Slot")
        self.setModal(True)
        self._slot = slot
        self._slot_number = slot_number
        self._destination_path = destination_path or ""
        self._form_data: Optional[SlotFormData] = None
        self._allowed_extensions = {".zip", ".7z", ".rar"}

        self.resize(560, 520)
        self._init_ui()

    def get_form_data(self) -> SlotFormData:
        """Return the captured form data (caller must ensure dialog accepted)."""
        if not self._form_data:
            raise ValueError("No form data captured. Ensure the dialog was accepted.")
        return self._form_data

    # UI -------------------------------------------------------------------
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        header = QLabel("Add New Slot" if self._slot is None else "Edit Slot")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header.setFont(header_font)

        subtitle = QLabel("Point to a Ren'Py source directory or drop a compressed package.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.7);")

        layout.addWidget(header)
        layout.addWidget(subtitle)

        # Source type selection
        self.source_type_group = QButtonGroup(self)
        self.dir_radio = QRadioButton("Source Directory")
        self.archive_radio = QRadioButton("Compressed File")
        self.source_type_group.addButton(self.dir_radio)
        self.source_type_group.addButton(self.archive_radio)

        radios_layout = QHBoxLayout()
        radios_layout.addWidget(self.dir_radio)
        radios_layout.addWidget(self.archive_radio)
        radios_layout.addStretch()
        layout.addLayout(radios_layout)

        # Default selection
        if self._slot and self._slot.source_type == "compressed":
            self.archive_radio.setChecked(True)
        else:
            self.dir_radio.setChecked(True)

        # Path input with browse button
        path_layout = QGridLayout()
        self.path_caption_label = QLabel(
            "Archive File Path *" if self.archive_radio.isChecked() else "VN Source Path *"
        )
        path_layout.addWidget(self.path_caption_label, 0, 0, 1, 2)

        initial_path = self._slot.original_source_path if self._slot else ""
        self.path_edit = QLineEdit(initial_path)
        self.path_edit.setPlaceholderText("C:/games/MyVisualNovel" if self.dir_radio.isChecked() else "C:/archives/MyVisualNovel.zip")
        path_layout.addWidget(self.path_edit, 1, 0)

        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self._handle_browse)
        path_layout.addWidget(self.browse_button, 1, 1)

        layout.addLayout(path_layout)

        # Drag and drop helper
        self.drop_area = SlotDropArea()
        self.drop_area.path_dropped.connect(self.path_edit.setText)
        layout.addWidget(self.drop_area)

        helper_label = QLabel(
            "Archives will be unpacked automatically. Directories should contain your .rpy files."
        )
        helper_label.setWordWrap(True)
        helper_label.setStyleSheet("color: rgba(255, 255, 255, 0.55); font-size: 9pt;")
        layout.addWidget(helper_label)

        # Destination preview
        preview_frame = QFrame()
        preview_frame.setFrameShape(QFrame.Shape.StyledPanel)
        preview_frame.setStyleSheet(
            """
            QFrame {
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 6px;
                background-color: rgba(255, 255, 255, 0.02);
            }
            """
        )
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(12, 10, 12, 10)

        preview_title = QLabel("Will be saved to:")
        preview_title.setStyleSheet("color: rgba(255, 255, 255, 0.5); font-size: 9pt;")

        raw_destination = self._slot.destination_path if self._slot else (self._destination_path or "")
        destination_text = _format_path_for_display(raw_destination)
        self.destination_label = QLabel(destination_text)
        self.destination_label.setStyleSheet("font-family: Consolas, 'Fira Code', monospace;")

        preview_layout.addWidget(preview_title)
        preview_layout.addWidget(self.destination_label)

        layout.addWidget(preview_frame)

        placeholder_frame = QFrame()
        placeholder_frame.setFrameShape(QFrame.Shape.StyledPanel)
        placeholder_frame.setStyleSheet(
            """
            QFrame {
                border: 1px dashed rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                background-color: rgba(255, 255, 255, 0.01);
            }
            """
        )
        placeholder_layout = QVBoxLayout(placeholder_frame)
        placeholder_layout.setContentsMargins(12, 12, 12, 12)
        placeholder_hint = QLabel("Additional parameters will live here (exclusions, checkboxes, etc.).")
        placeholder_hint.setStyleSheet("color: rgba(255, 255, 255, 0.5);")
        placeholder_hint.setWordWrap(True)
        placeholder_layout.addWidget(placeholder_hint)
        layout.addWidget(placeholder_frame)

        # Footer actions
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        save_label = "Save Changes" if self._slot else "Add Slot"
        save_button = QPushButton(save_label)
        save_button.setDefault(True)
        save_button.clicked.connect(self._handle_accept)

        footer_layout.addWidget(cancel_button)
        footer_layout.addWidget(save_button)
        layout.addLayout(footer_layout)

        # React to radio toggles
        self.dir_radio.toggled.connect(self._handle_source_type_change)
        self._handle_source_type_change(self.dir_radio.isChecked())

    # Slots ----------------------------------------------------------------
    def _handle_source_type_change(self, is_directory_selected: bool) -> None:
        source_type: SourceType = "directory" if is_directory_selected else "compressed"
        self.drop_area.set_mode(source_type)
        label_text = "VN Source Path *" if source_type == "directory" else "Archive File Path *"
        placeholder = (
            "C:/games/MyVisualNovel"
            if source_type == "directory"
            else "C:/archives/MyVisualNovel.zip"
        )
        self.path_edit.setPlaceholderText(placeholder)
        self.path_caption_label.setText(label_text)

    def _handle_browse(self) -> None:
        source_type: SourceType = "directory" if self.dir_radio.isChecked() else "compressed"
        if source_type == "directory":
            selected = QFileDialog.getExistingDirectory(
                self,
                "Select Visual Novel Directory",
                "",
                QFileDialog.Option.ShowDirsOnly,
            )
            if selected:
                self.path_edit.setText(selected)
        else:
            selected, _ = QFileDialog.getOpenFileName(
                self,
                "Select Archive File",
                "",
                "Archive Files (*.zip *.7z *.rar)",
            )
            if selected:
                self.path_edit.setText(selected)

    def _handle_accept(self) -> None:
        form_data = self._validate_form()
        if not form_data:
            return
        self._form_data = form_data
        self.accept()

    def _validate_form(self) -> Optional[SlotFormData]:
        path = self.path_edit.text().strip()
        source_type: SourceType = "directory" if self.dir_radio.isChecked() else "compressed"

        if not path:
            QMessageBox.warning(self, "Missing Path", "Please provide a path before continuing.")
            return None

        if source_type == "directory":
            if not os.path.isdir(path):
                QMessageBox.warning(self, "Invalid Directory", "Select an existing Ren'Py directory.")
                return None
        else:
            if not os.path.isfile(path):
                QMessageBox.warning(self, "Invalid File", "Select an existing archive file.")
                return None
            extension = os.path.splitext(path)[1].lower()
            if extension not in self._allowed_extensions:
                QMessageBox.warning(
                    self,
                    "Unsupported Archive",
                    "Please choose a .zip, .7z, or .rar file.",
                )
                return None

        destination_path = self._slot.destination_path if self._slot else self._destination_path
        if not destination_path:
            QMessageBox.warning(self, "Missing Destination", "Unable to resolve a slot destination path.")
            return None

        if source_type == "directory":
            confirm = QMessageBox.question(
                self,
                "Copy Slot",
                f"Copy the source directory into:\n{destination_path}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return None
        else:
            confirm = QMessageBox.question(
                self,
                "Extract Slot",
                f"Extract the ZIP contents into:\n{destination_path}?\nExisting files will be replaced.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return None

        normalized_source = os.path.normpath(path)
        normalized_destination = os.path.normpath(destination_path)

        return SlotFormData(
            source_path=normalized_source,
            source_type=source_type,
            destination_path=normalized_destination,
            slot_number=self._slot.slot_number if self._slot else self._slot_number,
        )


class RenpyOptionsTab(QWidget):
    """Main widget for the Ren'Py Options tab."""

    def __init__(self, db_conn, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.db_conn = db_conn
        self.story_id: Optional[int] = None
        self.current_story_data: Optional[Dict[str, object]] = None
        self.story_slots: Dict[int, List[RenpySlot]] = {}
        self.slots: List[RenpySlot] = []
        self._init_ui()

    # Public API -----------------------------------------------------------
    def set_story(self, story_id: int, story_data: Dict[str, object]) -> None:
        """Load slots for the given story (in-memory only for now)."""
        self.story_id = story_id
        self.current_story_data = story_data

        loaded_slots = self._load_slots_from_db(story_id)
        self.story_slots[story_id] = loaded_slots
        self.slots = loaded_slots

        slots_root = self._get_slots_root()
        if slots_root:
            os.makedirs(slots_root, exist_ok=True)

        self._refresh_slot_views()
        can_manage = bool(slots_root)
        self.add_slot_button.setEnabled(can_manage)
        self.empty_state.add_button.setEnabled(can_manage)

    def _get_slots_root(self) -> Optional[str]:
        if not self.current_story_data:
            return None
        folder_path = self.current_story_data.get("folder_path")
        if not folder_path:
            return None
        return os.path.normpath(os.path.join(str(folder_path), "slots"))

    def _get_next_slot_number(self) -> int:
        if not self.slots:
            return 1
        return max(slot.slot_number for slot in self.slots) + 1

    # UI -------------------------------------------------------------------
    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(18)

        header = QLabel("Ren'Py Options")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header.setFont(header_font)

        description = QLabel(
            "Configure Ren'Py source slots for the selected story. Slots keep working copies "
            "of your game versions so FlowViz and other features can reuse the cached data."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: rgba(255, 255, 255, 0.7);")

        main_layout.addWidget(header)
        main_layout.addWidget(description)

        card_frame = QFrame()
        card_frame.setObjectName("RenpyOptionsCard")
        card_frame.setFrameShape(QFrame.Shape.StyledPanel)
        card_frame.setStyleSheet(
            """
            #RenpyOptionsCard {
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 12px;
                background-color: rgba(0, 0, 0, 0.35);
            }
            """
        )
        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(16)

        header_row = QHBoxLayout()
        title = QLabel("Source Slots")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)

        self.add_slot_button = QPushButton("Add Slot")
        self.add_slot_button.setIcon(icon_manager.get_icon("plus"))
        self.add_slot_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_slot_button.clicked.connect(self._handle_add_slot_clicked)
        self.add_slot_button.setEnabled(False)

        header_row.addWidget(title)
        header_row.addStretch()
        header_row.addWidget(self.add_slot_button)

        card_layout.addLayout(header_row)

        self.content_stack = QStackedWidget()
        card_layout.addWidget(self.content_stack)

        self.empty_state = EmptyStateWidget()
        self.empty_state.add_slot_requested.connect(self._handle_add_slot_clicked)
        self.empty_state.add_button.setEnabled(False)
        self.content_stack.addWidget(self.empty_state)

        self.slot_scroll_area = QScrollArea()
        self.slot_scroll_area.setWidgetResizable(True)
        self.slot_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.slot_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.scroll_content = QWidget()
        self.slot_list_layout = QVBoxLayout(self.scroll_content)
        self.slot_list_layout.setSpacing(12)
        self.slot_list_layout.addStretch()
        if self.story_id is not None:
            self.story_slots[self.story_id] = self.slots

        self.slot_scroll_area.setWidget(self.scroll_content)
        self.content_stack.addWidget(self.slot_scroll_area)

        main_layout.addWidget(card_frame)
        main_layout.addStretch()

    # Slots ----------------------------------------------------------------
    def _handle_add_slot_clicked(self) -> None:
        if self.story_id is None or not self.current_story_data:
            QMessageBox.warning(self, "No Story Selected", "Select a story to manage slots.")
            return

        slots_root = self._get_slots_root()
        if not slots_root:
            QMessageBox.critical(
                self,
                "Missing Story Folder",
                "The selected story does not have a valid data folder. Please configure the story folder before adding slots.",
            )
            return

        os.makedirs(slots_root, exist_ok=True)
        next_number = self._get_next_slot_number()
        destination_path = os.path.normpath(os.path.join(slots_root, str(next_number)))

        dialog = SlotModal(self, slot_number=next_number, destination_path=destination_path)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_form_data()
        if data.source_type == "directory":
            if not self._copy_directory_slot(data.source_path, data.destination_path, overwrite=False):
                return
        else:
            if not self._extract_zip_slot(data.source_path, data.destination_path):
                return

        db_slot_id = db_create_story_slot(
            self.db_conn,
            self.story_id,
            data.slot_number,
            data.source_type,
            data.destination_path,
            data.source_path,
        )
        row = db_get_story_slot(self.db_conn, db_slot_id)
        if row:
            new_slot = self._slot_from_row(row)
        else:
            new_slot = RenpySlot(
                slot_id=str(db_slot_id),
                slot_number=data.slot_number,
                source_type=data.source_type,
                destination_path=data.destination_path,
                original_source_path=data.source_path,
                date_added=datetime.now(),
            )
        self.slots.append(new_slot)
        self._update_slot_cache()
        self._refresh_slot_views()

    def _handle_edit_slot(self, slot_id: str) -> None:
        slot = self._find_slot(slot_id)
        if not slot:
            return
        dialog = SlotModal(
            self,
            slot=slot,
            slot_number=slot.slot_number,
            destination_path=os.path.normpath(slot.destination_path),
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_form_data()
            if data.source_type == "directory":
                if not self._copy_directory_slot(
                    data.source_path,
                    data.destination_path,
                    overwrite=True,
                ):
                    return
            else:
                if not self._extract_zip_slot(
                    data.source_path,
                    data.destination_path,
                ):
                    return
            db_slot_id = self._slot_db_id(slot)
            if db_slot_id is not None:
                db_update_story_slot(
                    self.db_conn,
                    db_slot_id,
                    source_type=data.source_type,
                    destination_path=data.destination_path,
                    original_source_path=data.source_path,
                )

            slot.source_type = data.source_type
            slot.destination_path = data.destination_path
            slot.original_source_path = data.source_path
            self._update_slot_cache()
            self._refresh_slot_views()

    def _handle_delete_slot(self, slot_id: str) -> None:
        slot = self._find_slot(slot_id)
        if not slot:
            return
        confirm = QMessageBox.question(
            self,
            "Delete Slot",
            "Are you sure you want to delete this slot?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            db_slot_id = self._slot_db_id(slot)
            if db_slot_id is not None:
                db_delete_story_slot(self.db_conn, db_slot_id)
            self.slots.remove(slot)
            self._update_slot_cache()
            self._refresh_slot_views()

    def _handle_move_slot(self, slot_id: str, direction: int) -> None:
        index = self._find_slot_index(slot_id)
        if index is None:
            return
        new_index = index + direction
        if new_index < 0 or new_index >= len(self.slots):
            return
        self.slots[index], self.slots[new_index] = self.slots[new_index], self.slots[index]
        self._refresh_slot_views()

    # Helpers --------------------------------------------------------------
    def _refresh_slot_views(self) -> None:
        while self.slot_list_layout.count():
            item = self.slot_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if not self.slots:
            self.content_stack.setCurrentIndex(0)
            self.slot_list_layout.addStretch()
            return

        self.content_stack.setCurrentIndex(1)
        total_slots = len(self.slots)
        for index, slot in enumerate(self.slots):
            card = SlotItemWidget(slot)
            card.update_positioning(index, total_slots)
            card.update_slot(slot)
            card.edit_requested.connect(self._handle_edit_slot)
            card.delete_requested.connect(self._handle_delete_slot)
            card.move_up_requested.connect(partial(self._handle_move_slot, direction=-1))
            card.move_down_requested.connect(partial(self._handle_move_slot, direction=1))
            self.slot_list_layout.addWidget(card)

        self.slot_list_layout.addStretch()

    def _find_slot(self, slot_id: str) -> Optional[RenpySlot]:
        return next((slot for slot in self.slots if slot.slot_id == slot_id), None)

    def _find_slot_index(self, slot_id: str) -> Optional[int]:
        for index, slot in enumerate(self.slots):
            if slot.slot_id == slot_id:
                return index
        return None

    def _copy_directory_slot(self, source: str, destination: str, overwrite: bool) -> bool:
        if not os.path.isdir(source):
            QMessageBox.warning(self, "Invalid Source", "The selected directory no longer exists.")
            return False

        if os.path.exists(destination):
            if not overwrite:
                QMessageBox.warning(
                    self,
                    "Destination Exists",
                    f"The slot destination already exists:\n{destination}\nPlease remove it or choose another slot number.",
                )
                return False
            if not self._cleanup_failed_copy(destination):
                QMessageBox.critical(
                    self,
                    "Cleanup Failed",
                    "Could not prepare the destination folder for copying. Please close files inside that folder and try again.",
                )
                return False

        file_count = 0
        for _, _, files in os.walk(source):
            file_count += len(files)
        max_value = max(file_count, 1)

        progress = QProgressDialog("Copying slot files...", "Cancel", 0, max_value, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setWindowTitle("Copying Slot")
        progress.setAutoClose(False)
        progress.setValue(0)

        copied = 0
        cancelled = False
        try:
            for root, dirs, files in os.walk(source):
                rel_path = os.path.relpath(root, source)
                target_dir = destination if rel_path in (".", "") else os.path.join(destination, rel_path)
                os.makedirs(target_dir, exist_ok=True)

                for directory in dirs:
                    os.makedirs(os.path.join(target_dir, directory), exist_ok=True)

                for file_name in files:
                    if progress.wasCanceled():
                        cancelled = True
                        raise RuntimeError("Copy cancelled by user.")
                    src_file = os.path.join(root, file_name)
                    dst_file = os.path.join(target_dir, file_name)
                    shutil.copy2(src_file, dst_file)
                    copied += 1
                    progress.setValue(min(copied, max_value))
                    QApplication.processEvents()

            progress.setValue(max_value)
            return True
        except Exception as exc:
            self._cleanup_failed_copy(destination)
            if cancelled:
                QMessageBox.information(
                    self,
                    "Copy Cancelled",
                    "The copy operation was cancelled. The destination slot folder has been cleaned up.",
                )
            else:
                QMessageBox.critical(
                    self,
                    "Copy Failed",
                    f"Could not copy slot files:\n{exc}",
                )
            return False
        finally:
            progress.close()

    def _cleanup_failed_copy(self, folder_path: str, retries: int = 3) -> bool:
        for attempt in range(retries):
            if not os.path.exists(folder_path):
                return True
            try:
                shutil.rmtree(folder_path)
                return True
            except Exception:
                time.sleep(0.25)
        return False

    def _extract_zip_slot(self, zip_path: str, destination: str) -> bool:
        if not zip_path.lower().endswith(".zip"):
            QMessageBox.warning(self, "Unsupported Archive", "Only .zip files are supported.")
            return False

        if not os.path.isfile(zip_path):
            QMessageBox.warning(self, "Invalid File", "The selected ZIP file cannot be found.")
            return False

        temp_dir = tempfile.mkdtemp(prefix="tpt_slot_zip_")
        try:
            progress = QProgressDialog("Extracting ZIP contents...", "Cancel", 0, 0, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setWindowTitle("Extracting Slot")
            progress.setRange(0, 0)  # Busy indicator
            progress.show()
            QApplication.processEvents()

            with zipfile.ZipFile(zip_path, "r") as archive:
                members = archive.infolist()
                progress.setRange(0, len(members))
                for index, member in enumerate(members, start=1):
                    if progress.wasCanceled():
                        raise RuntimeError("Extraction cancelled by user.")
                    archive.extract(member, temp_dir)
                    progress.setValue(index)
                    QApplication.processEvents()

            candidate_root = self._locate_renpy_root(temp_dir)
            if not candidate_root:
                raise RuntimeError(
                    "Extracted archive does not contain Ren'Py 'game', 'renpy', and 'lib' folders at the same level."
                )

            if os.path.exists(destination):
                if not self._cleanup_failed_copy(destination):
                    raise RuntimeError("Unable to prepare destination folder. Close files in that slot and try again.")
            shutil.move(candidate_root, destination)
            self._cleanup_failed_copy(temp_dir)
            progress.close()
            return True
        except Exception as exc:
            self._cleanup_failed_copy(destination)
            self._cleanup_failed_copy(temp_dir)
            QMessageBox.critical(
                self,
                "ZIP Extraction Failed",
                f"Could not import the ZIP file:\n{exc}",
            )
            return False
        finally:
            try:
                progress.close()
            except Exception:
                pass

    def _locate_renpy_root(self, extracted_path: str) -> Optional[str]:
        required = {"game", "renpy", "lib"}

        def has_required(sub_path: str) -> bool:
            try:
                contents = {entry.name.lower() for entry in os.scandir(sub_path) if entry.is_dir()}
            except PermissionError:
                return False
            return required.issubset(contents)

        queue = [extracted_path]
        while queue:
            current = queue.pop(0)
            if has_required(current):
                return current
            try:
                for entry in os.scandir(current):
                    if entry.is_dir():
                        queue.append(entry.path)
            except PermissionError:
                continue
        return None

    def _load_slots_from_db(self, story_id: int) -> List[RenpySlot]:
        if not story_id:
            return []
        rows = db_get_story_slots(self.db_conn, story_id)
        return [self._slot_from_row(row) for row in rows]

    def _slot_from_row(self, row: Dict[str, Any]) -> RenpySlot:
        date_added = _parse_db_timestamp(row.get("created_at"))
        return RenpySlot(
            slot_id=str(row["id"]),
            slot_number=row["slot_number"],
            source_type=row["source_type"],
            destination_path=row["destination_path"],
            original_source_path=row.get("original_source_path") or "",
            date_added=date_added,
        )

    def _slot_db_id(self, slot: RenpySlot) -> Optional[int]:
        try:
            return int(slot.slot_id)
        except (TypeError, ValueError):
            return None

    def _update_slot_cache(self) -> None:
        if self.story_id is not None:
            self.story_slots[self.story_id] = self.slots

