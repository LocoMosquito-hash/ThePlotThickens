"""
PyQt6 tab that hosts the FlowViz toolbar, canvas, and inspector.
"""

from __future__ import annotations

from typing import Dict, Optional, Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QSplitter, QVBoxLayout, QWidget

from .models import DummyGraphFactory, FlowVizGraph
from .ui import FlowVizCanvasWidget, FlowVizInspectorPanel, FlowVizToolbar


class FlowVizTab(QWidget):
    """
    Composite widget used both inside the Source Analysis tab stack and by the
    standalone launcher.  It currently loads a dummy dataset while the slot
    cache integration is finalized.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.current_story_id: Optional[int] = None
        self.graph: Optional[FlowVizGraph] = None
        self._init_ui()
        self._load_dummy_graph()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.toolbar = FlowVizToolbar()
        layout.addWidget(self.toolbar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        self.canvas_widget = FlowVizCanvasWidget()
        splitter.addWidget(self.canvas_widget)

        self.inspector = FlowVizInspectorPanel()
        splitter.addWidget(self.inspector)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)

        self.canvas_widget.node_selected.connect(self.inspector.show_node)

        self.toolbar.zoomInRequested.connect(self.canvas_widget.zoom_in)
        self.toolbar.zoomOutRequested.connect(self.canvas_widget.zoom_out)
        self.toolbar.fitRequested.connect(self.canvas_widget.fit_to_view)
        self.toolbar.resetLayoutRequested.connect(self.canvas_widget.reset_layout)

    def _load_dummy_graph(self) -> None:
        self.graph = DummyGraphFactory.build_morning_routine_graph()
        self.canvas_widget.load_graph(self.graph)
        self.toolbar.set_slots(["Demo Slot"])
        self.toolbar.status_label.setText("Demo narrative loaded")

    # --- API consumed by SourceAnalysisTab ---------------------------------
    def set_story(self, story_id: int, story_data: Dict[str, Any]) -> None:
        """
        Called by SourceAnalysisTab whenever the user switches stories.
        For now it keeps the dummy content but stores the context for the
        upcoming slot cache hookup.
        """
        self.current_story_id = story_id
        self.toolbar.set_slots([f"Slot cache pending (Story #{story_id})"])

