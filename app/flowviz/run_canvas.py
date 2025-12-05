"""
Standalone launcher for the FlowViz tab.

Usage:
    python app/flowviz/run_canvas.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMainWindow

# Ensure project root is on sys.path so `app.*` imports resolve when executed directly.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.flowviz.tab import FlowVizTab


class FlowVizStandaloneWindow(QMainWindow):
    """Minimal window that hosts the FlowViz tab for rapid iteration."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FlowViz – Standalone Preview")
        self.resize(1440, 900)
        self.tab = FlowVizTab()
        self.setCentralWidget(self.tab)


def main() -> int:
    """Entry point for launching the FlowViz UI in isolation."""
    app = QApplication(sys.argv)
    window = FlowVizStandaloneWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

