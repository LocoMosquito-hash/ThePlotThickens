"""
Right-side inspector panel showing details for the selected node.
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QFrame,
)

from ..models import FlowVizNode, NodeType, MenuChoice, ScreenAction


class FlowVizInspectorPanel(QFrame):
    """Displays contextual metadata when a node is selected."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FlowVizInspectorPanel")
        self.setStyleSheet(
            """
            #FlowVizInspectorPanel {
                background-color: #13131a;
                border-left: 1px solid #1f2937;
            }
            QLabel {
                color: #d1d5db;
            }
            QLabel.title {
                color: #ffffff;
                font-size: 16px;
                font-weight: 600;
            }
            QLabel.section {
                color: #6b7280;
                font-size: 11px;
                letter-spacing: 2px;
            }
            QLabel.value {
                color: #ffffff;
                font-size: 13px;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.title_label = QLabel("Inspector")
        self.title_label.setProperty("class", "title")
        layout.addWidget(self.title_label)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)

        self._placeholder = QLabel("Select a node to see details")
        self._placeholder.setStyleSheet("color: #6b7280; font-style: italic;")
        self.scroll_layout.addWidget(self._placeholder)

    def show_node(self, node: Optional[FlowVizNode]) -> None:
        """Populate the panel with node data or show the placeholder."""
        self._clear_content()
        if not node:
            self._placeholder.show()
            return

        self._placeholder.hide()
        self._add_section("TYPE", node.type.value.title())
        self._add_section("ID", node.id, monospace=True)
        self._add_section("TITLE", node.title)
        if node.file:
            self._add_section("SOURCE", f"{node.file}:{node.line or '?'}", monospace=True)

        if node.type is NodeType.LABEL:
            self._add_label_sections(node)
        elif node.type is NodeType.MENU:
            self._add_menu_sections(node)
        elif node.type is NodeType.SCREEN:
            self._add_screen_sections(node)

    def _add_label_sections(self, node: FlowVizNode) -> None:
        if node.is_entry:
            self._add_section("ENTRY POINT", "Yes")
        self._add_section("OUTGOING", "Yes" if node.has_outgoing else "No")
        if node.is_ghost:
            self._add_section("STATUS", "Ghost reference detected")

    def _add_menu_sections(self, node: FlowVizNode) -> None:
        self._add_section("PROMPT", node.title)
        for idx, choice in enumerate(node.choices, start=1):
            label = f"CHOICE {idx}"
            value = self._format_choice(choice)
            self._add_section(label, value)

    def _add_screen_sections(self, node: FlowVizNode) -> None:
        self._add_section("SCREEN NAME", node.title, monospace=True)
        for idx, action in enumerate(node.actions, start=1):
            label = f"ACTION {idx}"
            value = self._format_action(action)
            self._add_section(label, value)

    def _format_choice(self, choice: MenuChoice) -> str:
        status = "OK"
        if choice.is_broken:
            status = "Broken target"
        elif not choice.has_edge:
            status = "No destination"
        return f"{choice.text} ({status})"

    def _format_action(self, action: ScreenAction) -> str:
        status = "Actionable" if action.has_edge else "Passive"
        if action.is_broken:
            status = "Broken target"
        return f"{action.text} ({status})"

    def _add_section(self, title: str, value: str, monospace: bool = False) -> None:
        label = QLabel(title)
        label.setProperty("class", "section")
        self.scroll_layout.addWidget(label)
        value_label = QLabel(value)
        value_label.setWordWrap(True)
        value_label.setProperty("class", "value")
        if monospace:
            value_label.setStyleSheet("font-family: 'JetBrains Mono', 'Consolas', monospace; color: #f3f4f6;")
        self.scroll_layout.addWidget(value_label)

    def _clear_content(self) -> None:
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget and widget is not self._placeholder:
                widget.setParent(None)

