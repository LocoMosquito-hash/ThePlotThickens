#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Collapsible Panel Widget for The Plot Thickens application.

This module provides a collapsible side panel similar to Visual Studio's tool windows,
with auto-hide functionality, pin button, and focus awareness.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QSizePolicy, QApplication, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QPalette


class CollapsiblePanel(QWidget):
    """A collapsible panel widget with auto-hide and pin functionality."""
    
    # Signals
    expanded = pyqtSignal()  # Emitted when panel is expanded
    collapsed = pyqtSignal()  # Emitted when panel is collapsed
    pinned_changed = pyqtSignal(bool)  # Emitted when pin state changes
    
    def __init__(self, title: str = "Panel", width: int = 250, parent: Optional[QWidget] = None) -> None:
        """Initialize the collapsible panel.
        
        Args:
            title: Title text to display in the panel header
            width: Width of the panel when expanded
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.title = title
        self.expanded_width = width
        self.collapsed_width = 30  # Width of just the tab when collapsed
        self.is_expanded = False
        self.is_pinned = False
        self.mouse_in_panel = False
        
        # Auto-hide timer
        self.auto_hide_timer = QTimer(self)
        self.auto_hide_timer.setSingleShot(True)
        self.auto_hide_timer.timeout.connect(self._auto_collapse)
        self.auto_hide_delay = 500  # milliseconds
        
        # Animation for smooth expand/collapse
        self.animation = QPropertyAnimation(self, b"maximumWidth")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.init_ui()
        self.collapse(animate=False)  # Start collapsed
    
    def init_ui(self) -> None:
        """Initialize the user interface."""
        self.setFixedWidth(self.collapsed_width)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create header section
        self.header_frame = QFrame()
        self.header_frame.setFixedHeight(30)
        self.header_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        self.header_frame.mousePressEvent = self._on_header_clicked
        
        # Header layout
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(5, 2, 5, 2)
        
        # Title label (rotated when collapsed)
        self.title_label = QLabel(self.title)
        font = QFont()
        font.setBold(True)
        font.setPointSize(9)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Pin button
        self.pin_button = QPushButton()
        self.pin_button.setFixedSize(16, 16)
        self.pin_button.setCheckable(True)
        self.pin_button.setChecked(self.is_pinned)
        self.pin_button.clicked.connect(self._on_pin_clicked)
        self.pin_button.setToolTip("Pin panel to keep it visible")
        self._update_pin_button()
        
        # Expand/collapse button
        self.toggle_button = QPushButton()
        self.toggle_button.setFixedSize(16, 16)
        self.toggle_button.clicked.connect(self.toggle)
        self._update_toggle_button()
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.pin_button)
        header_layout.addWidget(self.toggle_button)
        
        main_layout.addWidget(self.header_frame)
        
        # Content area
        self.content_frame = QFrame()
        self.content_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        self.content_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Content layout (to be used by the parent)
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        
        main_layout.addWidget(self.content_frame)
        
        # Apply styling
        self._apply_styling()
        
        # Install event filter for focus tracking
        self.installEventFilter(self)
        QApplication.instance().focusChanged.connect(self._on_focus_changed)
    
    def _apply_styling(self) -> None:
        """Apply custom styling to the panel."""
        # Header styling - more Visual Studio-like
        self.header_frame.setStyleSheet("""
            QFrame {
                background-color: palette(alternate-base);
                border: 1px solid palette(mid);
                border-bottom: none;
                font-weight: bold;
            }
            QFrame:hover {
                background-color: palette(highlight);
                color: palette(highlighted-text);
            }
        """)
        
        # Content styling
        self.content_frame.setStyleSheet("""
            QFrame {
                background-color: palette(base);
                border: 1px solid palette(mid);
                border-top: none;
            }
        """)
        
        # Button styling - more VS-like
        button_style = """
            QPushButton {
                border: none;
                border-radius: 1px;
                background-color: transparent;
                padding: 2px;
                font-size: 10px;
                color: palette(text);
            }
            QPushButton:hover {
                background-color: palette(highlight);
                color: palette(highlighted-text);
            }
            QPushButton:pressed {
                background-color: palette(dark);
                color: palette(highlighted-text);
            }
            QPushButton:checked {
                background-color: palette(highlight);
                color: palette(highlighted-text);
            }
        """
        self.pin_button.setStyleSheet(button_style)
        self.toggle_button.setStyleSheet(button_style)
    
    def _update_pin_button(self) -> None:
        """Update the pin button appearance."""
        if self.is_pinned:
            self.pin_button.setText("📌")  # Pinned
            self.pin_button.setToolTip("Unpin panel (auto-hide)")
        else:
            self.pin_button.setText("📍")  # Unpinned
            self.pin_button.setToolTip("Pin panel to keep it visible")
    
    def _update_toggle_button(self) -> None:
        """Update the toggle button appearance."""
        if self.is_expanded:
            self.toggle_button.setText("◀")  # Collapse
            self.toggle_button.setToolTip("Collapse panel")
        else:
            self.toggle_button.setText("▶")  # Expand
            self.toggle_button.setToolTip("Expand panel")
    
    def _on_header_clicked(self, event) -> None:
        """Handle header click to expand the panel."""
        if not self.is_expanded:
            self.expand()
    
    def _on_pin_clicked(self) -> None:
        """Handle pin button click."""
        self.is_pinned = self.pin_button.isChecked()
        self._update_pin_button()
        self.pinned_changed.emit(self.is_pinned)
        
        if not self.is_pinned and not self.mouse_in_panel:
            # Start auto-hide timer if unpinned and mouse not in panel
            self.auto_hide_timer.start(self.auto_hide_delay)
    
    def _on_focus_changed(self, old_widget: Optional[QWidget], new_widget: Optional[QWidget]) -> None:
        """Handle application focus changes for auto-hide behavior."""
        if not self.is_pinned and self.is_expanded:
            # Check if new focus is within this panel
            focus_in_panel = False
            if new_widget:
                current = new_widget
                while current:
                    if current == self:
                        focus_in_panel = True
                        break
                    current = current.parent()
            
            if not focus_in_panel and not self.mouse_in_panel:
                # Focus moved outside panel, start auto-hide timer
                self.auto_hide_timer.start(self.auto_hide_delay)
            else:
                # Focus within panel, stop auto-hide timer
                self.auto_hide_timer.stop()
    
    def _auto_collapse(self) -> None:
        """Auto-collapse the panel if conditions are met."""
        if not self.is_pinned and self.is_expanded and not self.mouse_in_panel:
            self.collapse()
    
    def enterEvent(self, event) -> None:
        """Handle mouse enter event."""
        self.mouse_in_panel = True
        self.auto_hide_timer.stop()
        if not self.is_expanded:
            # Small delay before expanding on hover
            QTimer.singleShot(100, self.expand)
        super().enterEvent(event)
    
    def leaveEvent(self, event) -> None:
        """Handle mouse leave event."""
        self.mouse_in_panel = False
        if not self.is_pinned and self.is_expanded:
            # Start auto-hide timer when mouse leaves
            self.auto_hide_timer.start(self.auto_hide_delay)
        super().leaveEvent(event)
    
    def expand(self, animate: bool = True) -> None:
        """Expand the panel.
        
        Args:
            animate: Whether to animate the expansion
        """
        if self.is_expanded:
            return
        
        self.is_expanded = True
        self._update_toggle_button()
        
        # Show content frame
        self.content_frame.show()
        
        if animate:
            # Animate width change
            self.animation.setStartValue(self.collapsed_width)
            self.animation.setEndValue(self.expanded_width)
            self.animation.finished.connect(self._on_expand_finished)
            self.animation.start()
        else:
            self.setFixedWidth(self.expanded_width)
            self._on_expand_finished()
    
    def collapse(self, animate: bool = True) -> None:
        """Collapse the panel.
        
        Args:
            animate: Whether to animate the collapse
        """
        if not self.is_expanded:
            return
        
        self.is_expanded = False
        self._update_toggle_button()
        
        if animate:
            # Animate width change
            self.animation.setStartValue(self.expanded_width)
            self.animation.setEndValue(self.collapsed_width)
            self.animation.finished.connect(self._on_collapse_finished)
            self.animation.start()
        else:
            self.setFixedWidth(self.collapsed_width)
            self._on_collapse_finished()
    
    def toggle(self) -> None:
        """Toggle the panel between expanded and collapsed states."""
        if self.is_expanded:
            self.collapse()
        else:
            self.expand()
    
    def _on_expand_finished(self) -> None:
        """Handle expansion animation completion."""
        self.setFixedWidth(self.expanded_width)
        self.setMaximumWidth(self.expanded_width)
        self.expanded.emit()
        try:
            self.animation.finished.disconnect()
        except TypeError:
            pass  # No connections to disconnect
    
    def _on_collapse_finished(self) -> None:
        """Handle collapse animation completion."""
        self.setFixedWidth(self.collapsed_width)
        self.setMaximumWidth(self.collapsed_width)
        self.content_frame.hide()
        self.collapsed.emit()
        try:
            self.animation.finished.disconnect()
        except TypeError:
            pass  # No connections to disconnect
    
    def set_pinned(self, pinned: bool) -> None:
        """Set the pin state programmatically.
        
        Args:
            pinned: Whether the panel should be pinned
        """
        self.is_pinned = pinned
        self.pin_button.setChecked(pinned)
        self._update_pin_button()
        self.pinned_changed.emit(pinned)
    
    def get_content_layout(self) -> QVBoxLayout:
        """Get the content layout for adding widgets.
        
        Returns:
            The content layout where child widgets should be added
        """
        return self.content_layout
    
    def add_content_widget(self, widget: QWidget) -> None:
        """Add a widget to the content area.
        
        Args:
            widget: Widget to add to the content area
        """
        self.content_layout.addWidget(widget)
    
    def set_title(self, title: str) -> None:
        """Set the panel title.
        
        Args:
            title: New title text
        """
        self.title = title
        self.title_label.setText(title)

class SimpleCollapsibleWidget(QWidget):
    """A simple, reliable collapsible widget with visible controls."""
    
    # Signals
    expanded = pyqtSignal()  # Emitted when content is expanded
    collapsed = pyqtSignal()  # Emitted when content is collapsed
    
    def __init__(self, title: str = "Section", collapsed: bool = False, parent: Optional[QWidget] = None) -> None:
        """Initialize the simple collapsible widget.
        
        Args:
            title: Title text to display
            collapsed: Whether to start in collapsed state
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._is_collapsed = collapsed
        self._title = title
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Header with toggle button
        self.header_widget = QWidget()
        self.header_widget.setStyleSheet("""
            QWidget {
                background-color: palette(button);
                border: 1px solid palette(mid);
                border-radius: 3px;
                margin: 1px;
            }
            QWidget:hover {
                background-color: palette(light);
            }
        """)
        
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(8, 4, 8, 4)
        
        # Toggle button - make it very visible
        self.toggle_button = QPushButton()
        self.toggle_button.setFixedSize(20, 20)
        self.toggle_button.clicked.connect(self.toggle)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                border: 1px solid palette(dark);
                background-color: palette(button);
                border-radius: 3px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: palette(highlight);
                color: palette(highlighted-text);
            }
            QPushButton:pressed {
                background-color: palette(dark);
            }
        """)
        
        # Title label
        self.title_label = QLabel(self._title)
        font = QFont()
        font.setBold(True)
        self.title_label.setFont(font)
        
        header_layout.addWidget(self.toggle_button)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        
        self.main_layout.addWidget(self.header_widget)
        
        # Content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        
        self.main_layout.addWidget(self.content_widget)
        
        # Set initial state
        self._update_button_appearance()
        if self._is_collapsed:
            self.collapse()
        else:
            self.expand()
    
    def _update_button_appearance(self) -> None:
        """Update the toggle button appearance."""
        if self._is_collapsed:
            self.toggle_button.setText("▼")  # Down arrow when collapsed
            self.toggle_button.setToolTip(f"Expand {self._title}")
        else:
            self.toggle_button.setText("▲")  # Up arrow when expanded
            self.toggle_button.setToolTip(f"Collapse {self._title}")
    
    def toggle(self) -> None:
        """Toggle between expanded and collapsed states."""
        if self._is_collapsed:
            self.expand()
        else:
            self.collapse()
    
    def expand(self) -> None:
        """Expand the content widget."""
        if not self._is_collapsed:
            return
            
        self._is_collapsed = False
        self.content_widget.setVisible(True)
        self._update_button_appearance()
        self.expanded.emit()
    
    def collapse(self) -> None:
        """Collapse the content widget."""
        if self._is_collapsed:
            return
            
        self._is_collapsed = True
        self.content_widget.setVisible(False)
        self._update_button_appearance()
        self.collapsed.emit()
    
    def is_collapsed(self) -> bool:
        """Check if the widget is currently collapsed.
        
        Returns:
            True if collapsed, False if expanded
        """
        return self._is_collapsed
    
    def get_content_layout(self) -> QVBoxLayout:
        """Get the content layout for adding widgets.
        
        Returns:
            The content layout where widgets should be added
        """
        return self.content_layout
    
    def add_content_widget(self, widget: QWidget) -> None:
        """Add a widget to the content area.
        
        Args:
            widget: Widget to add to the content
        """
        self.content_layout.addWidget(widget)
    
    def set_title(self, title: str) -> None:
        """Set the title text.
        
        Args:
            title: New title text
        """
        self._title = title
        self.title_label.setText(title)
        self._update_button_appearance()

# Keep the old CollapsibleGroupBox for compatibility but it's buggy
class CollapsibleGroupBox(QGroupBox):
    """A simple collapsible group box widget for inline content."""
    
    # Signals
    expanded = pyqtSignal()  # Emitted when content is expanded
    collapsed = pyqtSignal()  # Emitted when content is collapsed
    
    def __init__(self, title: str = "Group", collapsed: bool = False, parent: Optional[QWidget] = None) -> None:
        """Initialize the collapsible group box.
        
        Args:
            title: Title text to display in the group header
            collapsed: Whether to start in collapsed state
            parent: Parent widget
        """
        super().__init__(title, parent)
        
        self._is_collapsed = collapsed
        self._original_title = title
        
        # Create toggle button and integrate into title
        self.toggle_button = QPushButton()
        self.toggle_button.setFixedSize(16, 16)
        self.toggle_button.clicked.connect(self.toggle)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                font-weight: bold;
                color: palette(text);
            }
            QPushButton:hover {
                background-color: palette(highlight);
                color: palette(highlighted-text);
                border-radius: 2px;
            }
        """)
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 20, 10, 10)  # Leave space for title
        
        # Title layout to include toggle button
        self.title_layout = QHBoxLayout()
        self.title_layout.setContentsMargins(0, 0, 0, 5)
        
        # Content widget that will be shown/hidden
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.main_layout.addLayout(self.title_layout)
        self.main_layout.addWidget(self.content_widget)
        
        # Set up the custom title with toggle button
        self._setup_custom_title()
        
        # Set initial state
        if self._is_collapsed:
            self.collapse()
        else:
            self.expand()
        
        self._update_button_appearance()
    
    def _setup_custom_title(self) -> None:
        """Set up custom title layout with toggle button."""
        # Clear any existing title layout
        for i in reversed(range(self.title_layout.count())):
            item = self.title_layout.itemAt(i)
            if item and item.widget():
                item.widget().setParent(None)
        
        # Add toggle button
        self.title_layout.addWidget(self.toggle_button)
        
        # Add title label
        self.title_label = QLabel(self._original_title)
        font = QFont()
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_layout.addWidget(self.title_label)
        
        # Add stretch to push everything to the left
        self.title_layout.addStretch()
        
        # Remove the default QGroupBox title since we're using custom layout
        super().setTitle("")
    
    def _update_button_appearance(self) -> None:
        """Update the toggle button appearance."""
        if self._is_collapsed:
            self.toggle_button.setText("▶")
            self.toggle_button.setToolTip(f"Expand {self._original_title}")
        else:
            self.toggle_button.setText("▼")
            self.toggle_button.setToolTip(f"Collapse {self._original_title}")
    
    def toggle(self) -> None:
        """Toggle between expanded and collapsed states."""
        if self._is_collapsed:
            self.expand()
        else:
            self.collapse()
    
    def expand(self) -> None:
        """Expand the content widget."""
        if not self._is_collapsed:
            return
            
        self._is_collapsed = False
        self.content_widget.setVisible(True)
        self._update_button_appearance()
        self.expanded.emit()
    
    def collapse(self) -> None:
        """Collapse the content widget."""
        if self._is_collapsed:
            return
            
        self._is_collapsed = True
        self.content_widget.setVisible(False)
        self._update_button_appearance()
        self.collapsed.emit()
    
    def is_collapsed(self) -> bool:
        """Check if the group box is currently collapsed.
        
        Returns:
            True if collapsed, False if expanded
        """
        return self._is_collapsed
    
    def get_content_layout(self) -> QVBoxLayout:
        """Get the content layout for adding widgets.
        
        Returns:
            The content layout where widgets should be added
        """
        return self.content_layout
    
    def add_content_widget(self, widget: QWidget) -> None:
        """Add a widget to the content area.
        
        Args:
            widget: Widget to add to the content
        """
        self.content_layout.addWidget(widget)
    
    def set_title(self, title: str) -> None:
        """Set the title text.
        
        Args:
            title: New title text
        """
        self._original_title = title
        self.title_label.setText(title)
        self._update_button_appearance() 