"""
Top toolbar used by the FlowViz tab and the standalone window.
"""

from __future__ import annotations

from typing import List

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
    QSizePolicy,
)


class FlowVizToolbar(QFrame):
    """Simple toolbar exposing slot selection and canvas controls."""

    slotChanged = pyqtSignal(str)
    zoomInRequested = pyqtSignal()
    zoomOutRequested = pyqtSignal()
    fitRequested = pyqtSignal()
    resetLayoutRequested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("FlowVizToolbar")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(64)
        self.setStyleSheet(
            """
            #FlowVizToolbar {
                background-color: #0f172a;
                border-bottom: 1px solid #1f2937;
            }
            QLabel {
                color: #cbd5f5;
            }
            QComboBox {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                padding: 2px 6px;
                min-width: 200px;
            }
            QPushButton {
                background-color: #1d4ed8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton#secondary {
                background-color: #334155;
            }
            """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(10)

        self.slot_label = QLabel("Slot")
        layout.addWidget(self.slot_label)

        self.slot_combo = QComboBox()
        layout.addWidget(self.slot_combo)
        self.slot_combo.currentTextChanged.connect(self.slotChanged)

        layout.addSpacing(24)

        self.zoom_label = QLabel("Zoom:")
        layout.addWidget(self.zoom_label)

        self.zoom_out_btn = QPushButton("−")
        self.zoom_out_btn.setObjectName("secondary")
        layout.addWidget(self.zoom_out_btn)
        self.zoom_out_btn.clicked.connect(self.zoomOutRequested.emit)

        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setObjectName("secondary")
        layout.addWidget(self.zoom_in_btn)
        self.zoom_in_btn.clicked.connect(self.zoomInRequested.emit)

        self.fit_btn = QPushButton("Fit View")
        self.fit_btn.setObjectName("secondary")
        layout.addWidget(self.fit_btn)
        self.fit_btn.clicked.connect(self.fitRequested.emit)

        self.reset_btn = QPushButton("Reset Layout")
        layout.addWidget(self.reset_btn)
        self.reset_btn.clicked.connect(self.resetLayoutRequested.emit)

        layout.addStretch()

        self.status_label = QLabel("Demo dataset loaded")
        layout.addWidget(self.status_label)

    def set_slots(self, slots: List[str]) -> None:
        """Populate the slot combo box."""
        self.slot_combo.clear()
        self.slot_combo.addItems(slots)
        if slots:
            self.slot_combo.setCurrentIndex(0)

