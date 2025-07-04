#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Window Selector Tab for The Plot Thickens application.

This module provides window management and screenshot capture functionality
integrated into the Source Analysis tab, specifically designed for Ren'Py
visual novel development workflows.
"""

import os
import sys
import time
import ctypes
import shutil
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
from ctypes import wintypes, Structure, Union, POINTER, c_ulong, c_ushort, c_long

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QScrollArea, QCheckBox, QMessageBox, QListWidget, 
    QListWidgetItem, QSplitter, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt, QSettings, QThread, pyqtSignal, QTimer, QSize, QRect
from PyQt6.QtGui import QFont, QPixmap, QImage, QIcon, QPainter, QColor, QPen

# Windows API imports (only on Windows)
if sys.platform == "win32":
    try:
        import win32gui
        import win32process
        import win32ui
        import win32con
        import psutil
        WINDOWS_API_AVAILABLE = True
    except ImportError:
        WINDOWS_API_AVAILABLE = False
else:
    WINDOWS_API_AVAILABLE = False

# PIL for image processing
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# Windows Message constants
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_CHAR = 0x0102
VK_H = 0x48  # Virtual key code for 'H'

# SendInput structures for keyboard automation
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002


class KEYBDINPUT(Structure):
    """Keyboard input structure for SendInput."""
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", POINTER(wintypes.ULONG))
    ]


class MOUSEINPUT(Structure):
    """Mouse input structure for SendInput."""
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", POINTER(wintypes.ULONG))
    ]


class HARDWAREINPUT(Structure):
    """Hardware input structure for SendInput."""
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD)
    ]


class INPUT_UNION(Union):
    """Union for different input types."""
    _fields_ = [
        ("ki", KEYBDINPUT),
        ("mi", MOUSEINPUT),
        ("hi", HARDWAREINPUT)
    ]


class INPUT(Structure):
    """Input structure for SendInput."""
    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", INPUT_UNION)
    ]


class WindowInfo:
    """Information about a window for automation and display."""
    
    def __init__(self, hwnd: int, title: str, process_name: str, pid: int):
        """Initialize window information.
        
        Args:
            hwnd: Window handle
            title: Window title
            process_name: Process name
            pid: Process ID
        """
        self.hwnd = hwnd
        self.title = title
        self.process_name = process_name
        self.pid = pid
    
    def get_window_rect(self) -> Tuple[int, int, int, int]:
        """Get window rectangle coordinates."""
        if not WINDOWS_API_AVAILABLE:
            return (0, 0, 0, 0)
        try:
            return win32gui.GetWindowRect(self.hwnd)
        except:
            return (0, 0, 0, 0)
    
    def get_client_rect(self) -> Tuple[int, int, int, int]:
        """Get client area rectangle coordinates."""
        if not WINDOWS_API_AVAILABLE:
            return (0, 0, 0, 0)
        try:
            rect = win32gui.GetClientRect(self.hwnd)
            return (0, 0, rect[2], rect[3])
        except:
            return (0, 0, 0, 0)
    
    def get_window_state(self) -> Dict[str, Any]:
        """Get detailed window state information."""
        if not WINDOWS_API_AVAILABLE:
            return {"visible": False, "minimized": False, "maximized": False}
        
        try:
            return {
                "visible": win32gui.IsWindowVisible(self.hwnd),
                "minimized": win32gui.IsIconic(self.hwnd),
                "maximized": win32gui.IsZoomed(self.hwnd)
            }
        except:
            return {"visible": False, "minimized": False, "maximized": False}


class CrosshairOverlay(QWidget):
    """Overlay widget for image cropping with crosshair guides."""
    
    def __init__(self, parent_widget):
        """Initialize the crosshair overlay.
        
        Args:
            parent_widget: Parent widget to overlay on
        """
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.mouse_pos = None
        self.is_hovering = False
        
        # Rectangle drawing state
        self.is_drawing_rect = False
        self.rect_start = None
        self.rect_end = None
        self.crop_rect = None
        
        # Enable mouse tracking
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        
        # Make overlay fill parent
        self.resize(parent_widget.size())
        self.move(0, 0)
        self.hide()
    
    def paintEvent(self, event):
        """Draw crosshair lines and crop rectangle."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw crosshair lines when hovering and not drawing rectangle  
        if self.is_hovering and self.mouse_pos and not self.is_drawing_rect:
            crosshair_pen = QPen(QColor(0, 255, 0), 2, Qt.PenStyle.DashLine)
            painter.setPen(crosshair_pen)
            
            x, y = self.mouse_pos.x(), self.mouse_pos.y()
            
            # Draw horizontal line (full width)
            painter.drawLine(0, y, self.width(), y)
            
            # Draw vertical line (full height)
            painter.drawLine(x, 0, x, self.height())
        
        # Draw crop rectangle when dragging
        if self.is_drawing_rect and self.rect_start and self.rect_end:
            rect_pen = QPen(QColor(0, 255, 0), 4, Qt.PenStyle.SolidLine)
            painter.setPen(rect_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            
            x1, y1 = self.rect_start.x(), self.rect_start.y()
            x2, y2 = self.rect_end.x(), self.rect_end.y()
            
            rect = QRect(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
            painter.drawRect(rect)
    
    def update_position(self):
        """Update overlay position to match parent widget."""
        self.resize(self.parent_widget.size())
        self.move(0, 0)
    
    def mousePressEvent(self, event):
        """Start rectangle drawing on left mouse button press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_drawing_rect = True
            self.rect_start = event.position().toPoint()
            self.rect_end = self.rect_start
            self.update()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Update crosshair position or rectangle end point."""
        self.mouse_pos = event.position().toPoint()
        
        if self.is_drawing_rect and self.rect_start:
            self.rect_end = self.mouse_pos
        
        self.update()
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Complete rectangle drawing and show crop confirmation."""
        if event.button() == Qt.MouseButton.LeftButton and self.is_drawing_rect:
            self.is_drawing_rect = False
            
            if self.rect_start and self.rect_end:
                x1, y1 = self.rect_start.x(), self.rect_start.y()
                x2, y2 = self.rect_end.x(), self.rect_end.y()
                
                self.crop_rect = QRect(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
                
                if self.crop_rect.width() > 10 and self.crop_rect.height() > 10:
                    self.show_crop_confirmation()
                else:
                    self.clear_rectangle()
        
        super().mouseReleaseEvent(event)
    
    def show_crop_confirmation(self):
        """Show dialog asking user if they want to crop the image."""
        reply = QMessageBox.question(
            self.parent_widget,
            "Crop Image",
            "Do you want to crop the image to the selected area?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.perform_crop()
        else:
            self.clear_rectangle()
    
    def perform_crop(self):
        """Crop the current image and overwrite the original file."""
        # Implementation would go here - placeholder for now
        self.clear_rectangle()
    
    def clear_rectangle(self):
        """Clear the drawn rectangle."""
        self.rect_start = None
        self.rect_end = None
        self.crop_rect = None
        self.update()
    
    def enterEvent(self, event):
        """Mouse entered the overlay area - show crosshairs."""
        self.is_hovering = True
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Mouse left the overlay area - hide crosshairs."""
        self.is_hovering = False
        self.update()
        super().leaveEvent(event)


class WindowPickerWidget(QWidget):
    """Widget for selecting and managing windows."""
    
    # Signal emitted when a window is selected
    window_selected = pyqtSignal(object)  # WindowInfo object
    
    def __init__(self, parent=None):
        """Initialize the window picker widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.selected_window: Optional[WindowInfo] = None
        self.init_ui()
        self.refresh_windows()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("Refresh Windows")
        self.refresh_button.clicked.connect(self.refresh_windows)
        controls_layout.addWidget(self.refresh_button)
        
        self.select_button = QPushButton("Select Window")
        self.select_button.clicked.connect(self.select_current_window)
        self.select_button.setEnabled(False)
        controls_layout.addWidget(self.select_button)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Windows table
        self.windows_table = QTableWidget()
        self.windows_table.setColumnCount(4)
        self.windows_table.setHorizontalHeaderLabels(["Title", "Process", "PID", "Visible"])
        
        # Configure table
        header = self.windows_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        self.windows_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.windows_table.itemSelectionChanged.connect(self.on_selection_changed)
        self.windows_table.itemDoubleClicked.connect(self.on_window_double_clicked)
        
        layout.addWidget(self.windows_table)
    
    def enumerate_windows(self) -> List[WindowInfo]:
        """Enumerate all visible windows."""
        if not WINDOWS_API_AVAILABLE:
            return []
        
        windows = []
        
        def enum_windows_callback(hwnd: int, lparam: int) -> bool:
            if win32gui.IsWindowVisible(hwnd):
                try:
                    title = win32gui.GetWindowText(hwnd)
                    if title:  # Only include windows with titles
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        try:
                            process = psutil.Process(pid)
                            process_name = process.name()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            process_name = "Unknown"
                        
                        windows.append(WindowInfo(hwnd, title, process_name, pid))
                except:
                    pass  # Skip windows that cause errors
            
            return True  # Continue enumeration
        
        try:
            win32gui.EnumWindows(enum_windows_callback, 0)
        except:
            pass  # Handle enumeration errors gracefully
        
        return windows
    
    def refresh_windows(self):
        """Refresh the windows list."""
        windows = self.enumerate_windows()
        
        # Clear and populate table
        self.windows_table.setRowCount(len(windows))
        
        for i, window in enumerate(windows):
            # Store WindowInfo object in the first column
            title_item = QTableWidgetItem(window.title)
            title_item.setData(Qt.ItemDataRole.UserRole, window)
            self.windows_table.setItem(i, 0, title_item)
            
            self.windows_table.setItem(i, 1, QTableWidgetItem(window.process_name))
            self.windows_table.setItem(i, 2, QTableWidgetItem(str(window.pid)))
            
            state = window.get_window_state()
            visible_text = "Yes" if state["visible"] else "No"
            self.windows_table.setItem(i, 3, QTableWidgetItem(visible_text))
    
    def on_selection_changed(self):
        """Handle window selection change."""
        current_row = self.windows_table.currentRow()
        self.select_button.setEnabled(current_row >= 0)
    
    def on_window_double_clicked(self, item: QTableWidgetItem):
        """Handle window double-click."""
        self.select_current_window()
    
    def select_current_window(self):
        """Select the currently highlighted window."""
        current_row = self.windows_table.currentRow()
        if current_row >= 0:
            title_item = self.windows_table.item(current_row, 0)
            if title_item:
                self.selected_window = title_item.data(Qt.ItemDataRole.UserRole)
                self.window_selected.emit(self.selected_window)
    
    def get_selected_window(self) -> Optional[WindowInfo]:
        """Get the currently selected window."""
        return self.selected_window


class ScreenshotWidget(QWidget):
    """Widget for capturing and managing screenshots."""
    
    def __init__(self, parent=None):
        """Initialize the screenshot widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.current_window: Optional[WindowInfo] = None
        self.current_pixmap: Optional[QPixmap] = None
        self.image_dir = "image-stack"
        self.init_ui()
        self.ensure_image_directory()
        self.load_existing_images()
    
    def init_ui(self):
        """Initialize the user interface."""
        # Main horizontal layout: thumbnails on left, main content on right
        main_layout = QHBoxLayout(self)
        
        # Left panel: thumbnails and controls
        left_panel = QWidget()
        left_panel.setFixedWidth(200)
        left_layout = QVBoxLayout(left_panel)
        
        # Thumbnail list
        self.thumbnail_list = QListWidget()
        self.thumbnail_list.setIconSize(QSize(150, 100))
        self.thumbnail_list.itemClicked.connect(self.on_thumbnail_clicked)
        left_layout.addWidget(QLabel("Screenshots:"))
        left_layout.addWidget(self.thumbnail_list)
        
        # Control buttons
        self.capture_button = QPushButton("Capture Screenshot")
        self.capture_button.clicked.connect(self.capture_screenshot)
        self.capture_button.setEnabled(False)
        left_layout.addWidget(self.capture_button)
        
        self.hide_dialogue_button = QPushButton("Hide Dialogue + Capture")
        self.hide_dialogue_button.clicked.connect(self.hide_dialogue_and_capture)
        self.hide_dialogue_button.setEnabled(False)
        left_layout.addWidget(self.hide_dialogue_button)
        
        self.clear_button = QPushButton("Clear All Images")
        self.clear_button.clicked.connect(self.clear_all_images)
        left_layout.addWidget(self.clear_button)
        
        main_layout.addWidget(left_panel)
        
        # Right panel: main image display
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Status label
        self.status_label = QLabel("Select a window to begin capturing screenshots")
        self.status_label.setStyleSheet("color: #666; padding: 10px;")
        right_layout.addWidget(self.status_label)
        
        # Scroll area for image display
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid #ccc;")
        self.scroll_area.setWidget(self.image_label)
        
        right_layout.addWidget(self.scroll_area)
        main_layout.addWidget(right_panel)
        
        # Create crosshair overlay
        self.crosshair_overlay = CrosshairOverlay(self.image_label)
    
    def ensure_image_directory(self):
        """Ensure the image directory exists."""
        if not os.path.exists(self.image_dir):
            os.makedirs(self.image_dir)
    
    def load_existing_images(self):
        """Load existing images from the image directory."""
        if not os.path.exists(self.image_dir):
            return
        
        # Clear current thumbnails
        self.thumbnail_list.clear()
        
        # Load PNG images
        for filename in sorted(os.listdir(self.image_dir)):
            if filename.lower().endswith('.png'):
                image_path = os.path.join(self.image_dir, filename)
                self.add_thumbnail_to_list(image_path)
    
    def add_thumbnail_to_list(self, image_path: str):
        """Add a thumbnail to the list widget."""
        try:
            # Create thumbnail
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Scale to thumbnail size
                thumbnail = pixmap.scaled(150, 100, Qt.AspectRatioMode.KeepAspectRatio, 
                                        Qt.TransformationMode.SmoothTransformation)
                
                # Create list item
                item = QListWidgetItem()
                item.setIcon(QIcon(thumbnail))
                item.setText(os.path.basename(image_path))
                item.setData(Qt.ItemDataRole.UserRole, image_path)
                
                self.thumbnail_list.addItem(item)
        except Exception as e:
            print(f"Error adding thumbnail: {e}")
    
    def on_thumbnail_clicked(self, item: QListWidgetItem):
        """Handle thumbnail click."""
        image_path = item.data(Qt.ItemDataRole.UserRole)
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                self.current_pixmap = pixmap
                self.display_image(pixmap)
    
    def display_image(self, pixmap: QPixmap):
        """Display an image in the main view."""
        self.image_label.setPixmap(pixmap)
        self.crosshair_overlay.resize(self.image_label.size())
        self.crosshair_overlay.move(0, 0)
    
    def clear_all_images(self):
        """Clear all images from the directory and list."""
        reply = QMessageBox.question(
            self,
            "Clear All Images",
            "Are you sure you want to delete all screenshots? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Remove all PNG files
                for filename in os.listdir(self.image_dir):
                    if filename.lower().endswith('.png'):
                        os.remove(os.path.join(self.image_dir, filename))
                
                # Clear the list and display
                self.thumbnail_list.clear()
                self.image_label.clear()
                self.current_pixmap = None
                self.status_label.setText("All images cleared")
                
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to clear images: {e}")
    
    def update_for_window_selection(self, window_info: Optional[WindowInfo]):
        """Update the widget when a window is selected."""
        self.current_window = window_info
        
        if window_info:
            self.capture_button.setEnabled(True)
            self.hide_dialogue_button.setEnabled(True)
            self.status_label.setText(f"Ready to capture: {window_info.title}")
        else:
            self.capture_button.setEnabled(False)
            self.hide_dialogue_button.setEnabled(False)
            self.status_label.setText("Select a window to begin capturing screenshots")
    
    def capture_screenshot(self):
        """Capture a screenshot of the selected window."""
        if not self.current_window or not WINDOWS_API_AVAILABLE:
            return
        
        try:
            # Capture the window
            hwnd = self.current_window.hwnd
            
            # Get window dimensions
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top
            
            # Capture the window
            hwnd_dc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()
            
            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(save_bitmap)
            
            # Copy the window content
            save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)
            
            # Convert to PIL Image
            bmpinfo = save_bitmap.GetInfo()
            bmpstr = save_bitmap.GetBitmapBits(True)
            
            if PIL_AVAILABLE:
                pil_image = Image.frombuffer(
                    'RGB',
                    (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                    bmpstr, 'raw', 'BGRX', 0, 1
                )
                
                # Save the image
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
                image_path = os.path.join(self.image_dir, filename)
                pil_image.save(image_path)
                
                # Add to thumbnail list
                self.add_thumbnail_to_list(image_path)
                
                # Display the screenshot
                qimage = QImage(image_path)
                pixmap = QPixmap.fromImage(qimage)
                self.current_pixmap = pixmap
                self.display_image(pixmap)
                
                self.status_label.setText(f"Screenshot saved: {filename}")
            
            # Cleanup
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)
            
        except Exception as e:
            QMessageBox.warning(self, "Screenshot Error", f"Failed to capture screenshot: {e}")
    
    def hide_dialogue_and_capture(self):
        """Hide Ren'Py dialogue and capture screenshot."""
        if not self.current_window:
            return
        
        # Send 'H' key to hide dialogue
        if self.send_h_key_to_window(self.current_window.hwnd):
            # Small delay to let the dialogue hide
            QTimer.singleShot(100, self.capture_screenshot)
        else:
            QMessageBox.warning(self, "Key Send Error", "Failed to send hide key to window")
    
    def send_h_key_to_window(self, hwnd: int) -> bool:
        """Send 'H' key to window using Windows Message API."""
        if not WINDOWS_API_AVAILABLE:
            return False
        
        try:
            # Method 1: PostMessage (preferred)
            win32gui.PostMessage(hwnd, WM_KEYDOWN, VK_H, 0)
            time.sleep(0.05)
            win32gui.PostMessage(hwnd, WM_KEYUP, VK_H, 0)
            return True
        except:
            try:
                # Method 2: SendMessage (fallback)
                win32gui.SendMessage(hwnd, WM_KEYDOWN, VK_H, 0)
                time.sleep(0.05)
                win32gui.SendMessage(hwnd, WM_KEYUP, VK_H, 0)
                return True
            except:
                return False


class WindowPropertiesWidget(QWidget):
    """Widget for displaying window properties."""
    
    def __init__(self, parent=None):
        """Initialize the window properties widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.current_window: Optional[WindowInfo] = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel("Select a window from the Window Picker to view its properties")
        instructions.setStyleSheet("color: #666; font-style: italic; padding: 10px;")
        layout.addWidget(instructions)
        
        # Properties display
        self.properties_text = QTextEdit()
        self.properties_text.setReadOnly(True)
        self.properties_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.properties_text)
        
        # Select window button
        self.select_button = QPushButton("Select This Window")
        self.select_button.clicked.connect(self.select_window)
        self.select_button.setEnabled(False)
        layout.addWidget(self.select_button)
    
    def display_window_properties(self, window_info: WindowInfo):
        """Display properties for the given window."""
        self.current_window = window_info
        self.select_button.setEnabled(True)
        
        # Get window information
        rect = window_info.get_window_rect()
        client_rect = window_info.get_client_rect()
        state = window_info.get_window_state()
        
        # Format properties text
        properties = f"""Window Properties:

Title: {window_info.title}
Process: {window_info.process_name}
Process ID: {window_info.pid}
Window Handle: {window_info.hwnd}

Window Rectangle:
  Left: {rect[0]}
  Top: {rect[1]}
  Right: {rect[2]}
  Bottom: {rect[3]}
  Width: {rect[2] - rect[0]}
  Height: {rect[3] - rect[1]}

Client Rectangle:
  Width: {client_rect[2]}
  Height: {client_rect[3]}

Window State:
  Visible: {state['visible']}
  Minimized: {state['minimized']}
  Maximized: {state['maximized']}
"""
        
        self.properties_text.setPlainText(properties)
    
    def select_window(self):
        """Select the current window (placeholder for future functionality)."""
        if self.current_window:
            # This could emit a signal or perform some action
            QMessageBox.information(
                self,
                "Window Selected",
                f"Selected window: {self.current_window.title}"
            )


class WindowSelectorTab(QWidget):
    """Main Window Selector tab for the Source Analysis interface."""
    
    # Signal emitted when a window is selected (for communication with other tabs)
    window_selected = pyqtSignal(object)  # WindowInfo object
    
    def __init__(self, db_conn, parent=None):
        """Initialize the Window Selector tab.
        
        Args:
            db_conn: Database connection
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.story_id: Optional[int] = None
        self.settings = QSettings("ThePlotThickens", "ThePlotThickens")
        
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Check for Windows API availability
        if not WINDOWS_API_AVAILABLE:
            error_msg = QLabel("Window Selector requires Windows with pywin32 and psutil installed.")
            error_msg.setStyleSheet("color: red; font-weight: bold; padding: 20px; background: #ffe6e6;")
            layout.addWidget(error_msg)
            return
        
        # Create tab widget for sub-functionality
        self.tab_widget = QTabWidget()
        
        # Window Picker tab
        self.window_picker = WindowPickerWidget()
        self.tab_widget.addTab(self.window_picker, "Window Picker")
        
        # Window Properties tab
        self.window_properties = WindowPropertiesWidget()
        self.tab_widget.addTab(self.window_properties, "Properties")
        
        # Screenshot tab
        self.screenshot_widget = ScreenshotWidget()
        self.tab_widget.addTab(self.screenshot_widget, "Screenshots")
        
        layout.addWidget(self.tab_widget)
    
    def setup_connections(self):
        """Setup signal connections between widgets."""
        if not WINDOWS_API_AVAILABLE:
            return
        
        # Connect window selection to other widgets
        self.window_picker.window_selected.connect(self.on_window_selected)
    
    def on_window_selected(self, window_info: WindowInfo):
        """Handle window selection from the picker."""
        # Update properties widget
        self.window_properties.display_window_properties(window_info)
        
        # Update screenshot widget
        self.screenshot_widget.update_for_window_selection(window_info)
        
        # Switch to properties tab to show the selection
        self.tab_widget.setCurrentWidget(self.window_properties)
        
        # Forward the signal to external listeners (Screenshots tab)
        self.window_selected.emit(window_info)
    
    def set_story(self, story_id: int, story_data: Dict[str, Any]):
        """Set the current story context.
        
        Args:
            story_id: ID of the current story
            story_data: Story data dictionary
        """
        self.story_id = story_id
        
        # Update screenshot directory based on story
        if hasattr(self, 'screenshot_widget'):
            story_dir = story_data.get('source_path', '')
            if story_dir:
                # Use story-specific image directory
                self.screenshot_widget.image_dir = os.path.join(
                    os.path.dirname(story_dir), "screenshots"
                )
            else:
                # Use default directory
                self.screenshot_widget.image_dir = "image-stack"
            
            self.screenshot_widget.ensure_image_directory()
            self.screenshot_widget.load_existing_images() 