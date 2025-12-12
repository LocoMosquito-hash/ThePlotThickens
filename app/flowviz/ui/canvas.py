"""
Graphics scene, node/edge items, and minimap for FlowViz.

The canvas wraps a QGraphicsScene so we can reuse the same widget inside the
main Source Analysis tab and in the standalone launcher.  Rendering tries to
match the gradients, rounded rectangles, and edge colors defined in the Figma
README while keeping the code approachable for future contributors.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional

from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsItem,
    QGraphicsObject,
    QGraphicsPathItem,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QWidget,
)

from ..layout import LayeredLayoutEngine
from ..models import (
    EdgeType,
    FlowVizEdge,
    FlowVizGraph,
    FlowVizNode,
    FlowVizGeometry,
    NodeType,
)


class FlowVizPalette:
    """Centralized colors to mirror the Figma palette."""

    CANVAS_BG = QColor("#0a0a0f")
    PANEL_BG = QColor("#13131a")
    BORDER = QColor("#1f2937")
    TEXT_PRIMARY = QColor("#ffffff")
    TEXT_SECONDARY = QColor("#d1d5db")
    TEXT_MUTED = QColor("#6b7280")
    VISUAL_START_GRADIENT = ("#10b981", "#14b8a6")
    LABEL_GRADIENT = ("#3b82f6", "#6366f1")
    ENTRY_GRADIENT = ("#34d399", "#06b6d4")
    DEAD_END_GRADIENT = ("#ef4444", "#f43f5e")
    GHOST_GRADIENT = ("#6b7280", "#4b5563")
    MENU_GRADIENT = ("#fbbf24", "#f97316")
    SCREEN_GRADIENT = ("#8b5cf6", "#9333ea")

    EDGE_COLORS = {
        EdgeType.NARRATIVE: QColor("#ec4899"),
        EdgeType.MENU: QColor("#f59e0b"),
        EdgeType.SCREEN: QColor("#06b6d4"),
        EdgeType.CALL: QColor("#6b7280"),
    }


class FlowVizNodeItem(QGraphicsObject):
    """
    Visual representation of a FlowViz node.  Implements hover/selection styles
    and exposes anchor helpers so edges can snap to the correct side.
    """

    position_changed = pyqtSignal(str)

    def __init__(self, node: FlowVizNode):
        super().__init__()
        self.node = node
        self.width, self.height = FlowVizGeometry.node_dimensions(node)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self._hovered = False
        self.setZValue(1)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        gradient = self._build_gradient()
        painter.setBrush(gradient)
        border_color = self._border_color()
        pen = QPen(border_color, 2 if self.isSelected() else 1.2)
        if self.node.is_ghost:
            pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        radius = 20 if self.node.type is NodeType.VISUAL_START else 8
        painter.drawRoundedRect(self.boundingRect(), radius, radius)
        self._paint_content(painter)

    def _build_gradient(self) -> QLinearGradient:
        top_color, bottom_color = self._gradient_colors()
        gradient = QLinearGradient(0, 0, 0, self.height)
        gradient.setColorAt(0, QColor(top_color))
        gradient.setColorAt(1, QColor(bottom_color))
        gradient.setCoordinateMode(QLinearGradient.CoordinateMode.ObjectBoundingMode)
        return gradient

    def _gradient_colors(self) -> tuple[str, str]:
        if self.node.type is NodeType.VISUAL_START:
            return FlowVizPalette.VISUAL_START_GRADIENT
        if self.node.type is NodeType.LABEL:
            if self.node.is_ghost:
                return FlowVizPalette.GHOST_GRADIENT
            if not self.node.has_outgoing:
                return FlowVizPalette.DEAD_END_GRADIENT
            if self.node.is_entry:
                return FlowVizPalette.ENTRY_GRADIENT
            return FlowVizPalette.LABEL_GRADIENT
        if self.node.type is NodeType.MENU:
            return FlowVizPalette.MENU_GRADIENT
        if self.node.type is NodeType.SCREEN:
            return FlowVizPalette.SCREEN_GRADIENT
        return FlowVizPalette.LABEL_GRADIENT

    def _border_color(self) -> QColor:
        color = QColor("#ffffff")
        if self.node.type is NodeType.VISUAL_START:
            color = QColor("#34d399")
        elif self.node.type is NodeType.LABEL:
            color = QColor("#60a5fa")
        elif self.node.type is NodeType.MENU:
            color = QColor("#fbbf24")
        elif self.node.type is NodeType.SCREEN:
            color = QColor("#a78bfa")
        if self.isSelected():
            color = color.lighter(130)
        if self._hovered:
            color = color.lighter(115)
        return color

    def _paint_content(self, painter: QPainter) -> None:
        painter.save()
        painter.translate(0, 0)
        font = painter.font()
        font.setPointSizeF(10.5)
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)
        painter.setPen(FlowVizPalette.TEXT_PRIMARY)
        metrics = QFontMetrics(font)
        title = metrics.elidedText(self.node.title, Qt.TextElideMode.ElideRight, int(self.width - 24))
        painter.drawText(QRectF(16, 12, self.width - 32, 24), Qt.AlignmentFlag.AlignVCenter, title)
        painter.setPen(FlowVizPalette.TEXT_MUTED)

        if self.node.type is NodeType.LABEL:
            self._paint_label_meta(painter)
        elif self.node.type is NodeType.MENU:
            self._paint_menu_contents(painter)
        elif self.node.type is NodeType.SCREEN:
            self._paint_screen_contents(painter)
        painter.restore()

    def _paint_label_meta(self, painter: QPainter) -> None:
        meta_font = QFont(painter.font())
        meta_font.setPointSizeF(9)
        painter.setFont(meta_font)
        meta = f"{self.node.file or 'unknown'}:{self.node.line or '?'}"
        painter.drawText(
            QRectF(16, 44, self.width - 32, 20),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            meta,
        )
        if self.node.is_entry:
            painter.setPen(QPen(QColor("#34d399")))
            painter.drawText(
                QRectF(self.width - 70, 12, 54, 20),
                Qt.AlignmentFlag.AlignCenter,
                "ENTRY",
            )
        if not self.node.has_outgoing:
            painter.setPen(QColor("#f87171"))
            painter.drawText(
                QRectF(16, self.height - 28, self.width - 32, 18),
                Qt.AlignmentFlag.AlignLeft,
                "Dead End",
            )

    def _paint_menu_contents(self, painter: QPainter) -> None:
        painter.setPen(FlowVizPalette.TEXT_SECONDARY)
        painter.drawText(
            QRectF(16, 44, self.width - 32, 20),
            Qt.AlignmentFlag.AlignLeft,
            f"{len(self.node.choices)} options",
        )
        y = 80
        for idx, choice in enumerate(self.node.choices):
            rect = QRectF(16, y, self.width - 32, 28)
            bg = QColor("#a855f7" if not choice.is_broken else "#f87171")
            bg.setAlpha(55 if not choice.is_broken else 80)
            painter.fillRect(rect, bg)
            painter.setPen(QColor("#c084fc") if not choice.is_broken else QColor("#fca5a5"))
            painter.drawRoundedRect(rect, 6, 6)
            painter.setPen(FlowVizPalette.TEXT_PRIMARY)
            text_font = QFont(painter.font())
            text_font.setPointSizeF(10)
            painter.setFont(text_font)
            metrics = QFontMetrics(text_font)
            display = metrics.elidedText(choice.text, Qt.TextElideMode.ElideRight, int(rect.width() - 14))
            painter.drawText(rect.adjusted(8, 0, -8, 0), Qt.AlignmentFlag.AlignVCenter, display)
            y += 32

    def _paint_screen_contents(self, painter: QPainter) -> None:
        painter.setPen(FlowVizPalette.TEXT_SECONDARY)
        painter.drawText(
            QRectF(16, 44, self.width - 32, 20),
            Qt.AlignmentFlag.AlignLeft,
            f"{len(self.node.actions)} actions",
        )
        y = 80
        for action in self.node.actions:
            rect = QRectF(16, y, self.width - 32, 28)
            color = QColor("#4ade80") if action.has_edge and not action.is_broken else QColor("#9ca3af")
            if action.is_broken:
                color = QColor("#f87171")
            fill = QColor(color)
            fill.setAlpha(45)
            painter.fillRect(rect, fill)
            painter.setPen(color)
            painter.drawRoundedRect(rect, 6, 6)
            painter.setPen(FlowVizPalette.TEXT_PRIMARY if action.has_edge else FlowVizPalette.TEXT_MUTED)
            metrics = QFontMetrics(painter.font())
            display = metrics.elidedText(action.text, Qt.TextElideMode.ElideRight, int(rect.width() - 14))
            painter.drawText(rect.adjusted(8, 0, -8, 0), Qt.AlignmentFlag.AlignVCenter, display)
            y += 32

    def center_point(self) -> QPointF:
        rect = self.boundingRect()
        return self.scenePos() + QPointF(rect.width() / 2, rect.height() / 2)

    def choice_anchor(self, choice_index: int, side: str) -> QPointF:
        header = FlowVizGeometry.HEADER_HEIGHT
        padding = FlowVizGeometry.CONTAINER_VERTICAL_PADDING / 2
        row_height = FlowVizGeometry.ROW_HEIGHT
        y = (
            self.scenePos().y()
            + header
            + padding
            + choice_index * row_height
            + row_height / 2
        )
        x = self.scenePos().x() if side == "left" else self.scenePos().x() + self.width
        return QPointF(x, y)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.node.position.x = value.x()
            self.node.position.y = value.y()
            self.position_changed.emit(self.node.id)
        return super().itemChange(change, value)

    def hoverEnterEvent(self, event) -> None:
        self._hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        self._hovered = False
        self.update()
        super().hoverLeaveEvent(event)


class FlowVizEdgeItem(QGraphicsPathItem):
    """Cubic Bézier edge with color derived from the edge type."""

    def __init__(
        self,
        edge: FlowVizEdge,
        source_item: FlowVizNodeItem,
        target_item: FlowVizNodeItem,
    ):
        super().__init__()
        self.edge = edge
        self.source_item = source_item
        self.target_item = target_item
        self._arrow_size = 10.0
        self.setZValue(0)
        self.setPen(self._build_pen())
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.update_path()

    def boundingRect(self) -> QRectF:
        """
        Ensure the arrowhead is not clipped.

        QGraphicsPathItem's bounding rect only accounts for the path + pen width,
        but our arrowhead triangle is drawn on top and may extend beyond that.
        """
        base = super().boundingRect()
        pad = max(self._arrow_size, self.pen().widthF()) + 6.0
        return base.adjusted(-pad, -pad, pad, pad)

    def _build_pen(self) -> QPen:
        pen = QPen(FlowVizPalette.EDGE_COLORS[self.edge.type], 2.2)
        if self.edge.type is EdgeType.CALL:
            pen.setStyle(Qt.PenStyle.DashLine)
        pen.setCosmetic(True)
        return pen

    def update_path(self) -> None:
        (start, start_dock), (end, end_dock) = self._calculate_anchors()
        path = QPainterPath(start)
        control_distance = self._control_distance(start, end)
        start_dir = self._dock_direction_vector(start_dock)
        end_dir = self._dock_direction_vector(end_dock)
        control1 = start + (start_dir * control_distance)
        control2 = end + (end_dir * control_distance)
        path.cubicTo(control1, control2, end)
        self.setPath(path)

    def _calculate_anchors(self) -> tuple[tuple[QPointF, str], tuple[QPointF, str]]:
        # Use other-node center points for stable angle selection.
        start = self._anchor_for_item(
            self.source_item,
            self.target_item.center_point(),
            True,
            self.edge.choice_index,
        )
        end = self._anchor_for_item(
            self.target_item,
            self.source_item.center_point(),
            False,
            None,
        )
        return start, end

    def _anchor_for_item(
        self,
        item: FlowVizNodeItem,
        other_pos: QPointF,
        is_source: bool,
        choice_index: Optional[int],
    ) -> tuple[QPointF, str]:
        # Menu/Screen incoming edges should always dock on the top-center.
        if not is_source and item.node.type in {NodeType.MENU, NodeType.SCREEN}:
            return QPointF(item.scenePos().x() + item.width / 2.0, item.scenePos().y()), "n"
        # Special case for menu/screen rows.
        if item.node.type in {NodeType.MENU, NodeType.SCREEN} and choice_index is not None:
            side = "right" if other_pos.x() > item.scenePos().x() else "left"
            dock = "e" if side == "right" else "w"
            return item.choice_anchor(choice_index, side), dock
        # Standard 8-direction docking using best-fit angle.
        center = item.center_point()
        vector = other_pos - center
        angle = math.degrees(math.atan2(vector.y(), vector.x()))
        if -22.5 <= angle < 22.5:
            return QPointF(item.scenePos().x() + item.width, center.y()), "e"
        if 22.5 <= angle < 67.5:
            return (
                QPointF(item.scenePos().x() + item.width, item.scenePos().y() + item.height),
                "se",
            )
        if 67.5 <= angle < 112.5:
            return QPointF(center.x(), item.scenePos().y() + item.height), "s"
        if 112.5 <= angle < 157.5:
            return QPointF(item.scenePos().x(), item.scenePos().y() + item.height), "sw"
        if 157.5 <= angle < 202.5:
            return QPointF(item.scenePos().x(), center.y()), "w"
        if 202.5 <= angle < 247.5:
            return QPointF(item.scenePos().x(), item.scenePos().y()), "nw"
        if 247.5 <= angle < 292.5:
            return QPointF(center.x(), item.scenePos().y()), "n"
        if 292.5 <= angle < 337.5:
            return QPointF(item.scenePos().x() + item.width, item.scenePos().y()), "ne"
        # Fallback: align with vertical flow.
        if is_source:
            return QPointF(center.x(), item.scenePos().y() + item.height), "s"
        return QPointF(center.x(), item.scenePos().y()), "n"

    def _dock_direction_vector(self, dock: str) -> QPointF:
        """
        Return the outward-pointing normal for a docking point.

        This is used to shape the curve so it leaves/approaches nodes along the
        docking direction, ensuring arrowheads sit outside node borders.
        """
        vectors = {
            "n": QPointF(0.0, -1.0),
            "s": QPointF(0.0, 1.0),
            "e": QPointF(1.0, 0.0),
            "w": QPointF(-1.0, 0.0),
            "ne": QPointF(0.7071, -0.7071),
            "nw": QPointF(-0.7071, -0.7071),
            "se": QPointF(0.7071, 0.7071),
            "sw": QPointF(-0.7071, 0.7071),
        }
        return vectors.get(dock, QPointF(0.0, 1.0))

    def _control_distance(self, start: QPointF, end: QPointF) -> float:
        """Scale control point distance to keep curves smooth at different spans."""
        dx = abs(end.x() - start.x())
        dy = abs(end.y() - start.y())
        span = max(dx, dy)
        return max(60.0, min(220.0, span * 0.35))

    def paint(self, painter: QPainter, option, widget=None) -> None:
        super().paint(painter, option, widget)
        self._paint_arrowhead(painter)

    def _paint_arrowhead(self, painter: QPainter) -> None:
        end_point = self.path().pointAtPercent(1.0)
        # QPainterPath.angleAtPercent returns degrees. Build a direction vector
        # for the tangent and derive the arrow triangle around it.
        angle = math.radians(-self.path().angleAtPercent(1.0))
        arrow_size = self._arrow_size
        sin_a = math.sin(angle)
        cos_a = math.cos(angle)
        p1 = QPointF(
            end_point.x() - arrow_size * cos_a + (arrow_size / 2) * sin_a,
            end_point.y() - arrow_size * sin_a - (arrow_size / 2) * cos_a,
        )
        p2 = QPointF(
            end_point.x() - arrow_size * cos_a - (arrow_size / 2) * sin_a,
            end_point.y() - arrow_size * sin_a + (arrow_size / 2) * cos_a,
        )
        painter.setBrush(self.pen().color())
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        path = QPainterPath()
        path.moveTo(end_point)
        path.lineTo(p1)
        path.lineTo(p2)
        path.closeSubpath()
        painter.drawPath(path)


class FlowVizScene(QGraphicsScene):
    """QGraphicsScene wrapper that keeps track of node/edge items."""

    def __init__(self):
        super().__init__()
        self.node_items: Dict[str, FlowVizNodeItem] = {}
        self.edge_items: List[FlowVizEdgeItem] = []
        self.graph: Optional[FlowVizGraph] = None

    def load_graph(self, graph: FlowVizGraph) -> None:
        self.clear()
        self.graph = graph
        self.node_items = {}
        self.edge_items = []
        for node in graph.nodes:
            item = FlowVizNodeItem(node)
            item.setPos(node.position.x, node.position.y)
            item.position_changed.connect(self._handle_node_moved)
            self.addItem(item)
            self.node_items[node.id] = item

        for edge in graph.edges:
            source_item = self.node_items.get(edge.source_id)
            target_item = self.node_items.get(edge.target_id)
            if not source_item or not target_item:
                continue
            edge_item = FlowVizEdgeItem(edge, source_item, target_item)
            self.addItem(edge_item)
            self.edge_items.append(edge_item)

        bounds = self.itemsBoundingRect().adjusted(-300, -200, 300, 200)
        self.setSceneRect(bounds)

    def _handle_node_moved(self, node_id: str) -> None:
        for edge_item in self.edge_items:
            if (
                edge_item.edge.source_id == node_id
                or edge_item.edge.target_id == node_id
            ):
                edge_item.update_path()


class FlowVizCanvasView(QGraphicsView):
    """Custom QGraphicsView that supports smooth pan/zoom gestures."""

    viewChanged = pyqtSignal()

    def __init__(self, scene: FlowVizScene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.setBackgroundBrush(FlowVizPalette.CANVAS_BG)
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self._panning = False
        self._pan_start = QPointF()

    def wheelEvent(self, event) -> None:
        delta = event.angleDelta().y()
        if delta == 0:
            return
        zoom_factor = 1.1 if delta > 0 else 0.9
        mouse_pos = event.position()
        before = self.mapToScene(mouse_pos.toPoint())
        self.scale(zoom_factor, zoom_factor)
        after = self.mapToScene(mouse_pos.toPoint())
        self.translate(before.x() - after.x(), before.y() - after.y())
        self.viewChanged.emit()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start = event.position()
            QApplication.setOverrideCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._panning:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - int(delta.x())
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(delta.y())
            )
            self.viewChanged.emit()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton and self._panning:
            self._panning = False
            QApplication.restoreOverrideCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def fit_to_scene(self) -> None:
        rect = self.scene().itemsBoundingRect()
        if rect.isNull():
            return
        self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        self.viewChanged.emit()


class FlowVizMinimap(QWidget):
    """Bottom-right minimap that mirrors the scene contents."""

    def __init__(self, scene: FlowVizScene, view: FlowVizCanvasView, parent=None):
        super().__init__(parent)
        self.scene = scene
        self.view = view
        self.setFixedSize(220, 160)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: rgba(19,19,26,0.75); border: 1px solid #374151; border-radius: 8px;")
        self.view.viewChanged.connect(self.update)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bounds = self.scene.itemsBoundingRect()
        if bounds.isNull() or bounds.width() == 0 or bounds.height() == 0:
            return
        padding = 12
        scale = min(
            (self.width() - 2 * padding) / bounds.width(),
            (self.height() - 2 * padding) / bounds.height(),
        )
        painter.translate(padding, padding)
        painter.setPen(Qt.PenStyle.NoPen)

        for item in self.scene.node_items.values():
            node_color = FlowVizPalette.EDGE_COLORS.get(EdgeType.NARRATIVE).lighter(140)
            if item.node.type is NodeType.MENU:
                node_color = FlowVizPalette.EDGE_COLORS[EdgeType.MENU]
            elif item.node.type is NodeType.SCREEN:
                node_color = FlowVizPalette.EDGE_COLORS[EdgeType.SCREEN]
            elif item.node.type is NodeType.VISUAL_START:
                node_color = QColor("#10b981")
            rect = item.sceneBoundingRect()
            x = (rect.center().x() - bounds.left()) * scale
            y = (rect.center().y() - bounds.top()) * scale
            painter.setBrush(node_color)
            painter.drawEllipse(QPointF(x, y), 3, 3)

        # Draw viewport rectangle.
        self._draw_viewport(painter, bounds, scale)

    def _draw_viewport(self, painter: QPainter, bounds: QRectF, scale: float) -> None:
        view_rect = self.view.mapToScene(self.view.viewport().rect()).boundingRect()
        padding = 12
        x = (view_rect.left() - bounds.left()) * scale
        y = (view_rect.top() - bounds.top()) * scale
        width = view_rect.width() * scale
        height = view_rect.height() * scale
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor("#06b6d4"), 1.2))
        painter.drawRect(QRectF(x, y, width, height))

    def mousePressEvent(self, event) -> None:
        if not self.scene or not self.scene.items():
            return
        bounds = self.scene.itemsBoundingRect()
        if bounds.width() == 0 or bounds.height() == 0:
            return
        padding = 12
        scale = min(
            (self.width() - 2 * padding) / bounds.width(),
            (self.height() - 2 * padding) / bounds.height(),
        )
        scene_x = bounds.left() + (event.position().x() - padding) / scale
        scene_y = bounds.top() + (event.position().y() - padding) / scale
        self.view.centerOn(scene_x, scene_y)
        self.view.viewChanged.emit()


class FlowVizCanvasWidget(QWidget):
    """Composite widget containing the QGraphicsView and minimap overlay."""

    node_selected = pyqtSignal(object)

    def __init__(self, parent=None, layout_engine: Optional[LayeredLayoutEngine] = None):
        super().__init__(parent)
        self.layout_engine = layout_engine or LayeredLayoutEngine()
        self.graph: Optional[FlowVizGraph] = None
        self.scene = FlowVizScene()
        self.view = FlowVizCanvasView(self.scene)
        self.view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.BoundingRectViewportUpdate)
        self.scene.selectionChanged.connect(self._handle_selection_change)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)

        self.minimap = FlowVizMinimap(self.scene, self.view, parent=self)
        self.minimap.hide()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._position_minimap()

    def _position_minimap(self) -> None:
        margin = 24
        self.minimap.move(
            self.width() - self.minimap.width() - margin,
            self.height() - self.minimap.height() - margin,
        )
        if self.graph:
            self.minimap.show()

    def load_graph(self, graph: FlowVizGraph) -> None:
        self.graph = self.layout_engine.apply(graph)
        self.scene.load_graph(self.graph)
        self.view.fit_to_scene()
        self.minimap.update()
        self._position_minimap()

    def zoom_in(self) -> None:
        self.view.scale(1.1, 1.1)
        self.view.viewChanged.emit()

    def zoom_out(self) -> None:
        self.view.scale(0.9, 0.9)
        self.view.viewChanged.emit()

    def fit_to_view(self) -> None:
        self.view.fit_to_scene()

    def reset_layout(self) -> None:
        if not self.graph:
            return
        self.layout_engine.apply(self.graph)
        self.scene.load_graph(self.graph)
        self.view.fit_to_scene()

    def _handle_selection_change(self) -> None:
        items = self.scene.selectedItems()
        if not items:
            self.node_selected.emit(None)
            return
        item = items[0]
        if isinstance(item, FlowVizNodeItem):
            self.node_selected.emit(item.node)

