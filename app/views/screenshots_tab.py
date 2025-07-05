#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Screenshots Tab for The Plot Thickens application.

This module provides screenshot capture functionality with Ren'Py automation,
global hotkey monitoring, and image cropping capabilities. All functionality
is preserved exactly from the ideas-lab prototype.
"""

import os
import sys
import time
import ctypes
import glob
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QCheckBox, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QSettings, QThread, pyqtSignal, QTimer, QSize, QEvent
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
    import numpy as np
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Global hotkeys import
try:
    from global_hotkeys import register_hotkeys, start_checking_hotkeys, stop_checking_hotkeys, clear_hotkeys
    GLOBAL_HOTKEYS_AVAILABLE = True
except ImportError:
    GLOBAL_HOTKEYS_AVAILABLE = False

# Import the shared classes from window_selector_tab
from app.views.window_selector_tab import WindowInfo, CrosshairOverlay


class GlobalHotkeyMonitor(QThread):
    """
    Background thread for monitoring global hotkeys.
    
    This class runs in a separate thread to avoid blocking the main GUI
    and provides system-wide hotkey monitoring using the global-hotkeys library.
    """
    screenshot_requested = pyqtSignal()
    status_update = pyqtSignal(str, str)  # message, color
    
    def __init__(self):
        super().__init__()
        self.is_monitoring = False
        self.target_window_info = None
        self.daemon = True  # Thread will die when main program exits
        
    def set_target_window(self, window_info: Optional[WindowInfo]):
        """Set the target window to monitor for hotkey activation."""
        self.target_window_info = window_info
        
    def is_target_window_active(self) -> bool:
        """Check if the target window is currently in the foreground."""
        if not self.target_window_info:
            return False
            
        try:
            # Get the currently active window
            active_hwnd = win32gui.GetForegroundWindow()
            return active_hwnd == self.target_window_info.hwnd
        except Exception:
            return False
    
    def on_insert_pressed(self):
        """Callback function when INSERT key is pressed globally."""
        if self.is_target_window_active():
            self.status_update.emit("🎯 INSERT detected in target window - triggering screenshot...", "#1976d2")
            self.screenshot_requested.emit()
        else:
            # Optionally emit status for debugging
            self.status_update.emit("⚪ INSERT pressed but target window not active", "#666666")
    
    def start_monitoring(self):
        """Start global hotkey monitoring."""
        if not GLOBAL_HOTKEYS_AVAILABLE:
            self.status_update.emit("❌ Global hotkeys not available - install requirements", "#f44336")
            return False
            
        try:
            # Define hotkey binding for INSERT key
            bindings = [
                ["insert", None, self.on_insert_pressed, False]
            ]
            
            # Register the hotkey
            register_hotkeys(bindings)
            start_checking_hotkeys()
            
            self.is_monitoring = True
            self.status_update.emit("✅ Global hotkey monitoring active (INSERT key)", "#4caf50")
            return True
            
        except Exception as e:
            self.status_update.emit(f"❌ Failed to start global hotkeys: {str(e)}", "#f44336")
            return False
    
    def stop_monitoring(self):
        """Stop global hotkey monitoring."""
        try:
            if GLOBAL_HOTKEYS_AVAILABLE and self.is_monitoring:
                stop_checking_hotkeys()
                clear_hotkeys()
                
            self.is_monitoring = False
            self.status_update.emit("⏹️ Global hotkey monitoring stopped", "#ff9800")
            
            # Signal the thread to stop its run loop
            self.quit()
            
        except Exception as e:
            self.status_update.emit(f"⚠️ Error stopping hotkeys: {str(e)}", "#ff9800")
    
    def run(self):
        """Thread run method - not needed for global-hotkeys as it handles its own threading."""
        # global-hotkeys handles its own background threading
        # This method exists to satisfy QThread requirements
        while self.is_monitoring:
            self.msleep(100)  # Sleep 100ms


class ScreenshotsTab(QWidget):
    """Tab for capturing and displaying window screenshots with exact functionality from ideas-lab."""
    
    def __init__(self, db_conn, parent=None):
        """Initialize the Screenshots tab.
        
        Args:
            db_conn: Database connection (for future use)
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.current_pixmap = None
        self.current_image_path = None  # Track current image file path for overwriting
        self.image_stack_folder = "image-stack"
        self.selected_window: Optional[WindowInfo] = None
        
        # Initialize monitoring thread
        self.hotkey_monitor = GlobalHotkeyMonitor()
        self.hotkey_monitor.screenshot_requested.connect(self.capture_screenshot_from_hotkey)
        self.hotkey_monitor.status_update.connect(self.update_hotkey_status)
        
        self.init_ui()
        self.load_existing_images()
        
    def init_ui(self):
        """Initialize the user interface with exact layout from ideas-lab version."""
        # Main horizontal layout: thumbnails on left, main content on right
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        
        # Left panel: Vertical thumbnail list
        thumbnail_panel = QVBoxLayout()
        thumbnail_label = QLabel("📸 Image Stack")
        thumbnail_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        thumbnail_label.setStyleSheet("color: #333; padding: 5px;")
        thumbnail_panel.addWidget(thumbnail_label)
        
        # Thumbnail list widget
        self.thumbnail_list = QListWidget()
        self.thumbnail_list.setMaximumWidth(210)
        self.thumbnail_list.setMinimumWidth(210)
        self.thumbnail_list.setIconSize(QSize(150, 150))
        self.thumbnail_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.thumbnail_list.setSpacing(5)
        self.thumbnail_list.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.thumbnail_list.setStyleSheet("""
            QListWidget {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 3px;
                margin: 2px;
                padding: 2px;
            }
            QListWidget::item:selected {
                background-color: #2196f3;
                border: 2px solid #1976d2;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
                border: 1px solid #2196f3;
            }
            QListWidget::item:focus {
                background-color: #bbdefb;
                border: 2px solid #1976d2;
                outline: none;
            }
        """)
        self.thumbnail_list.itemClicked.connect(self.on_thumbnail_clicked)
        self.thumbnail_list.currentItemChanged.connect(self.on_thumbnail_selection_changed)
        self.thumbnail_list.installEventFilter(self)
        thumbnail_panel.addWidget(self.thumbnail_list)
        
        # Clear all images button
        clear_button = QPushButton("🗑️ Clear All Images")
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        clear_button.clicked.connect(self.clear_all_images)
        thumbnail_panel.addWidget(clear_button)
        
        # Create thumbnail panel widget
        thumbnail_widget = QWidget()
        thumbnail_widget.setLayout(thumbnail_panel)
        main_layout.addWidget(thumbnail_widget)
        
        # Right panel: Main screenshot interface
        right_layout = QVBoxLayout()
        
        # Global Hotkey Controls Section
        hotkey_group = QVBoxLayout()
        hotkey_label = QLabel("🎯 Global Hotkey Controls")
        hotkey_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        hotkey_group.addWidget(hotkey_label)
        
        hotkey_info = QLabel("Press INSERT while in the target window to capture screenshots in the background.")
        hotkey_info.setWordWrap(True)
        hotkey_info.setStyleSheet("color: #666; padding: 5px 0;")
        hotkey_group.addWidget(hotkey_info)
        
        hotkey_button_layout = QHBoxLayout()
        self.start_monitoring_button = QPushButton("🚀 Start Global Monitoring")
        self.start_monitoring_button.setStyleSheet("background-color: #4caf50; color: white; font-weight: bold; padding: 8px; border-radius: 4px;")
        self.start_monitoring_button.clicked.connect(self.start_global_monitoring)
        
        self.stop_monitoring_button = QPushButton("⏹️ Stop Monitoring")
        self.stop_monitoring_button.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 8px; border-radius: 4px;")
        self.stop_monitoring_button.clicked.connect(self.stop_global_monitoring)
        self.stop_monitoring_button.setEnabled(False)
        
        hotkey_button_layout.addWidget(self.start_monitoring_button)
        hotkey_button_layout.addWidget(self.stop_monitoring_button)
        hotkey_group.addLayout(hotkey_button_layout)
        
        right_layout.addLayout(hotkey_group)
        
        # Separator
        separator = QLabel()
        separator.setStyleSheet("border-bottom: 1px solid #ddd; margin: 10px 0;")
        right_layout.addWidget(separator)
        
        # Renpy checkbox
        self.hide_renpy_checkbox = QCheckBox("Hide Renpy text before and after capture")
        self.hide_renpy_checkbox.setToolTip("Sends 'H' key to toggle Renpy dialog text before and after screenshot")
        right_layout.addWidget(self.hide_renpy_checkbox)
        
        # Screenshot button
        button_layout = QHBoxLayout()
        self.screenshot_button = QPushButton("📸 Capture Screenshot (Client Area)")
        self.screenshot_button.setToolTip("Capture client area of selected window")
        self.screenshot_button.clicked.connect(self.capture_screenshot)
        button_layout.addWidget(self.screenshot_button)
        right_layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel("Select a window from the Window Selector tab to capture screenshots")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 4px; margin: 10px 0;")
        right_layout.addWidget(self.status_label)
        
        # Image display area
        image_layout = QVBoxLayout()
        image_label_title = QLabel("Screenshot Preview")
        image_label_title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        image_layout.addWidget(image_label_title)
        
        self.image_label = QLabel("Screenshot will appear here")
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setStyleSheet("border: 2px dashed #ccc; background-color: #fafafa; color: #999;")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(False)
        
        # Scroll area for large images
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.image_label)
        
        # Add crosshair overlay directly to image label for proper event handling
        self.crosshair_overlay = CrosshairOverlay(self.image_label)
        self.crosshair_overlay.hide()  # Start hidden
        
        self.scroll_area.setMinimumSize(400, 300)
        image_layout.addWidget(self.scroll_area)
        
        right_layout.addLayout(image_layout)
        
        # Create right panel widget  
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        main_layout.addWidget(right_widget)
        
        # Set proportions: thumbnail panel takes more space now, main content takes rest
        main_layout.setStretch(0, 2)  # Thumbnail panel (increased from 1)
        main_layout.setStretch(1, 5)  # Main content (adjusted from 4)
    
    def load_existing_images(self):
        """Load existing images from the image-stack folder into thumbnails."""
        if not os.path.exists(self.image_stack_folder):
            os.makedirs(self.image_stack_folder)
            
        image_files = glob.glob(os.path.join(self.image_stack_folder, "*.png"))
        image_files.extend(glob.glob(os.path.join(self.image_stack_folder, "*.jpg")))
        image_files.sort()  # Sort by filename (which includes timestamp) - date ascending
        
        for image_path in image_files:
            self.add_thumbnail_to_list(image_path)
            
        if image_files:
            self.status_label.setText(f"📁 Loaded {len(image_files)} existing images from image-stack folder")
            self.status_label.setStyleSheet("color: #2196f3;")
    
    def add_thumbnail_to_list(self, image_path: str):
        """Add a thumbnail to the vertical thumbnail list."""
        try:
            # Check if image path already exists in the list to prevent duplicates
            for i in range(self.thumbnail_list.count()):
                existing_item = self.thumbnail_list.item(i)
                if existing_item and existing_item.data(Qt.ItemDataRole.UserRole) == image_path:
                    # Image already exists in the list, skip adding
                    return
            
            # Generate thumbnail using PIL
            with Image.open(image_path) as img:
                # Create thumbnail (180x180 max size while maintaining aspect ratio)
                img.thumbnail((180, 180), Image.Resampling.LANCZOS)
                
                # Convert PIL Image to QPixmap
                img_qt = img.convert('RGBA')
                h, w, ch = img_qt.size[1], img_qt.size[0], 4
                bytes_per_line = ch * w
                qt_image = QImage(img_qt.tobytes(), w, h, bytes_per_line, QImage.Format.Format_RGBA8888)
                thumbnail_pixmap = QPixmap.fromImage(qt_image)
            
            # Create list widget item
            item = QListWidgetItem()
            scaled_pixmap = thumbnail_pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            item.setIcon(QIcon(scaled_pixmap))  # Convert QPixmap to QIcon
            item.setData(Qt.ItemDataRole.UserRole, image_path)  # Store full path
            item.setToolTip(f"Click to view: {os.path.basename(image_path)}\nPress DELETE to remove")
            
            # Add to the bottom of the list (date ascending - newest last)
            self.thumbnail_list.addItem(item)
            
        except Exception as e:
            print(f"Error creating thumbnail for {image_path}: {e}")
    
    def update_thumbnail_after_crop(self, image_path: str):
        """Update the thumbnail in the list after the image has been cropped."""
        try:
            # Find the thumbnail item with this image path
            for i in range(self.thumbnail_list.count()):
                item = self.thumbnail_list.item(i)
                if item is not None and item.data(Qt.ItemDataRole.UserRole) == image_path:
                    # Regenerate the thumbnail with the cropped image
                    with Image.open(image_path) as img:
                        # Create thumbnail (180x180 max size while maintaining aspect ratio)
                        img.thumbnail((180, 180), Image.Resampling.LANCZOS)
                        
                        # Convert PIL Image to QPixmap
                        img_qt = img.convert('RGBA')
                        h, w, ch = img_qt.size[1], img_qt.size[0], 4
                        bytes_per_line = ch * w
                        qt_image = QImage(img_qt.tobytes(), w, h, bytes_per_line, QImage.Format.Format_RGBA8888)
                        thumbnail_pixmap = QPixmap.fromImage(qt_image)
                        
                        # Update the icon
                        scaled_pixmap = thumbnail_pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        item.setIcon(QIcon(scaled_pixmap))
                        
                        # Update tooltip
                        item.setToolTip(f"Click to view: {os.path.basename(image_path)}\nPress DELETE to remove")
                        
                        break
                        
        except Exception as e:
            print(f"Error updating thumbnail for {image_path}: {e}")
    
    def on_thumbnail_clicked(self, item: QListWidgetItem):
        """Handle thumbnail click to display image."""
        image_path = item.data(Qt.ItemDataRole.UserRole)
        if image_path and os.path.exists(image_path):
            try:
                # Load and display the image
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    self.current_pixmap = pixmap
                    self.current_image_path = image_path
                    
                    # Scale to fit the image label size while maintaining aspect ratio (EXACT ORIGINAL APPROACH)
                    scaled_pixmap = pixmap.scaled(
                        self.image_label.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    
                    self.image_label.setPixmap(scaled_pixmap)
                    
                    # Show and update crosshair overlay position (EXACT ORIGINAL APPROACH)
                    self.crosshair_overlay.update_position()
                    self.crosshair_overlay.show()
                    
                    self.status_label.setText(f"📷 Viewing: {os.path.basename(image_path)}")
                    self.status_label.setStyleSheet("color: #1976d2;")
                    
            except Exception as e:
                self.status_label.setText(f"❌ Error loading image: {str(e)}")
                self.status_label.setStyleSheet("color: #f44336;")
    
    def on_thumbnail_selection_changed(self, current: QListWidgetItem, previous: QListWidgetItem):
        """Handle thumbnail selection change."""
        if current:
            self.on_thumbnail_clicked(current)
    
    def clear_all_images(self):
        """Clear all images from the directory and list."""
        from PyQt6.QtWidgets import QMessageBox
        
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
                for filename in os.listdir(self.image_stack_folder):
                    if filename.lower().endswith('.png') or filename.lower().endswith('.jpg'):
                        os.remove(os.path.join(self.image_stack_folder, filename))
                
                # Clear the list and display
                self.thumbnail_list.clear()
                self.image_label.clear()
                self.image_label.setText("Screenshot will appear here")
                self.current_pixmap = None
                self.current_image_path = None
                self.crosshair_overlay.hide()
                self.status_label.setText("🗑️ All images cleared")
                self.status_label.setStyleSheet("color: #ff5722;")
                
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to clear images: {e}")
    
    def update_hotkey_status(self, message: str, color: str):
        """Update status label with hotkey monitoring messages."""
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; padding: 10px; background-color: #f0f0f0; border-radius: 4px; margin: 10px 0;")
    
    def capture_screenshot_from_hotkey(self):
        """Capture screenshot triggered by global hotkey."""
        self.capture_screenshot()
    
    def start_global_monitoring(self):
        """Start global hotkey monitoring."""
        if not self.selected_window:
            self.status_label.setText("❌ Please select a target window first")
            self.status_label.setStyleSheet("color: #f44336; padding: 10px; background-color: #f0f0f0; border-radius: 4px; margin: 10px 0;")
            return
        
        # Set target window and start monitoring
        self.hotkey_monitor.set_target_window(self.selected_window)
        
        if self.hotkey_monitor.start_monitoring():
            # Start the QThread to keep the monitoring alive
            if not self.hotkey_monitor.isRunning():
                self.hotkey_monitor.start()
            
            self.start_monitoring_button.setEnabled(False)
            self.stop_monitoring_button.setEnabled(True)
    
    def stop_global_monitoring(self):
        """Stop global hotkey monitoring."""
        self.hotkey_monitor.stop_monitoring()
        
        # Stop the QThread if it's running
        if self.hotkey_monitor.isRunning():
            self.hotkey_monitor.quit()
            self.hotkey_monitor.wait(1000)  # Wait up to 1 second for thread to finish
        
        self.start_monitoring_button.setEnabled(True)
        self.stop_monitoring_button.setEnabled(False)
    
    def set_selected_window(self, window_info: Optional[WindowInfo]):
        """Set the currently selected window for screenshot capture."""
        self.selected_window = window_info
        
        if window_info:
            self.status_label.setText(f"Ready to capture: {window_info.title}")
            self.status_label.setStyleSheet("color: #1976d2; padding: 10px; background-color: #f0f0f0; border-radius: 4px; margin: 10px 0;")
            self.screenshot_button.setEnabled(True)
        else:
            self.status_label.setText("Select a window from the Window Selector tab to capture screenshots")
            self.status_label.setStyleSheet("color: #666; font-style: italic; padding: 10px; background-color: #f0f0f0; border-radius: 4px; margin: 10px 0;")
            self.screenshot_button.setEnabled(False)
    
    def set_story(self, story_id: int, story_data: Dict[str, Any]):
        """Set the current story context for screenshot organization."""
        # Update screenshot directory based on story
        story_dir = story_data.get('source_path', '')
        if story_dir:
            # Use story-specific image directory
            self.image_stack_folder = os.path.join(
                os.path.dirname(story_dir), "screenshots"
            )
        else:
            # Use default directory
            self.image_stack_folder = "image-stack"
        
        # Ensure directory exists and reload images
        if not os.path.exists(self.image_stack_folder):
            os.makedirs(self.image_stack_folder)
        
        # Clear existing thumbnails before reloading to prevent duplicates
        self.thumbnail_list.clear()
        
        self.load_existing_images()
    
    def capture_screenshot(self) -> None:
        """Capture screenshot of the selected window's client area with exact functionality from ideas-lab."""
        if not self.selected_window:
            self.status_label.setText("❌ No window selected. Please select a window first.")
            self.status_label.setStyleSheet("color: #d32f2f; padding: 10px; background-color: #f0f0f0; border-radius: 4px; margin: 10px 0;")
            return
            
        if not WINDOWS_API_AVAILABLE:
            self.status_label.setText("❌ Windows API not available. Please install pywin32 and psutil.")
            self.status_label.setStyleSheet("color: #d32f2f; padding: 10px; background-color: #f0f0f0; border-radius: 4px; margin: 10px 0;")
            return
            
        try:
            # Check if window still exists and is valid
            if not win32gui.IsWindow(self.selected_window.hwnd):
                self.status_label.setText("❌ Selected window no longer exists.")
                self.status_label.setStyleSheet("color: #d32f2f; padding: 10px; background-color: #f0f0f0; border-radius: 4px; margin: 10px 0;")
                return
                
            # Check if window is minimized
            if win32gui.IsIconic(self.selected_window.hwnd):
                self.status_label.setText("❌ Cannot capture minimized window. Please restore the window first.")
                self.status_label.setStyleSheet("color: #d32f2f; padding: 10px; background-color: #f0f0f0; border-radius: 4px; margin: 10px 0;")
                return
                
            # Check if window is visible
            if not win32gui.IsWindowVisible(self.selected_window.hwnd):
                self.status_label.setText("❌ Window is not visible.")
                self.status_label.setStyleSheet("color: #d32f2f; padding: 10px; background-color: #f0f0f0; border-radius: 4px; margin: 10px 0;")
                return
            
            # Handle Renpy text hiding if checkbox is checked
            checkbox_checked = self.hide_renpy_checkbox.isChecked()
            
            if checkbox_checked:
                self.status_label.setText("🎮 Checkbox CHECKED - Attempting to hide Renpy text...")
                self.status_label.setStyleSheet("color: #1976d2; padding: 10px; background-color: #f0f0f0; border-radius: 4px; margin: 10px 0;")
                
                # Send first 'H' key to hide text
                hide_success = self.send_h_key_to_window(self.selected_window.hwnd)
                if not hide_success:
                    self.status_label.setText("❌ FAILED to send hide keystroke, proceeding with capture...")
                    self.status_label.setStyleSheet("color: #ff9800; padding: 10px; background-color: #f0f0f0; border-radius: 4px; margin: 10px 0;")
                else:
                    self.status_label.setText("✅ Hide keystroke sent successfully, waiting for UI update...")
                    self.status_label.setStyleSheet("color: #4caf50; padding: 10px; background-color: #f0f0f0; border-radius: 4px; margin: 10px 0;")
                    time.sleep(0.3)  # Wait for UI update
            
            self.status_label.setText("📸 Capturing screenshot...")
            self.status_label.setStyleSheet("color: #1976d2; padding: 10px; background-color: #f0f0f0; border-radius: 4px; margin: 10px 0;")
            
            # Get client area dimensions
            client_rect = win32gui.GetClientRect(self.selected_window.hwnd)
            width = client_rect[2]
            height = client_rect[3]
            
            if width <= 0 or height <= 0:
                self.status_label.setText("❌ Invalid window dimensions.")
                self.status_label.setStyleSheet("color: #d32f2f; padding: 10px; background-color: #f0f0f0; border-radius: 4px; margin: 10px 0;")
                return
            
            # Create device contexts - use GetDC for client area only
            hwnd_dc = win32gui.GetDC(self.selected_window.hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()
            
            # Create bitmap
            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(save_bitmap)
            
            # Copy client area content
            result = save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)
            
            if result == 0:
                self.status_label.setText("❌ Failed to capture window content.")
                self.status_label.setStyleSheet("color: #d32f2f; padding: 10px; background-color: #f0f0f0; border-radius: 4px; margin: 10px 0;")
                return
            
            # Convert to PIL Image
            bmpinfo = save_bitmap.GetInfo()
            bmpstr = save_bitmap.GetBitmapBits(True)
            
            if PIL_AVAILABLE:
                pil_image = Image.frombuffer(
                    'RGB',
                    (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                    bmpstr, 'raw', 'BGRX', 0, 1
                )
                
                # Handle Renpy text restoration if checkbox is checked
                if checkbox_checked:
                    time.sleep(0.1)  # Minimal delay
                    self.status_label.setText("🎮 Attempting to restore Renpy text...")
                    self.status_label.setStyleSheet("color: #1976d2; padding: 10px; background-color: #f0f0f0; border-radius: 4px; margin: 10px 0;")
                    
                    # Send second 'H' key to restore text
                    restore_success = self.send_h_key_to_window(self.selected_window.hwnd)
                    if restore_success:
                        self.status_label.setText("✅ Restore keystroke sent successfully")
                        self.status_label.setStyleSheet("color: #4caf50; padding: 10px; background-color: #f0f0f0; border-radius: 4px; margin: 10px 0;")
                
                # Save screenshot
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
                filepath = os.path.join(self.image_stack_folder, filename)
                
                try:
                    pil_image.save(filepath, "PNG")
                    self.current_image_path = filepath
                    self.add_thumbnail_to_list(filepath)
                except Exception as save_error:
                    print(f"Failed to save screenshot: {str(save_error)}")
                
                # Display screenshot
                self.display_screenshot(pil_image, self.selected_window)
            
            # Clean up
            win32gui.DeleteObject(save_bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(self.selected_window.hwnd, hwnd_dc)
            
        except Exception as e:
            self.status_label.setText(f"❌ Screenshot capture failed: {str(e)}")
            self.status_label.setStyleSheet("color: #d32f2f; padding: 10px; background-color: #f0f0f0; border-radius: 4px; margin: 10px 0;")
    
    def display_screenshot(self, pil_image: Image.Image, window_info: WindowInfo) -> None:
        """Convert PIL image to QPixmap and display it."""
        try:
            # Convert PIL to QImage
            h, w, ch = pil_image.height, pil_image.width, 3
            bytes_per_line = ch * w
            qt_image = QImage(pil_image.tobytes(), w, h, bytes_per_line, QImage.Format.Format_RGB888)
            
            # Convert to QPixmap
            pixmap = QPixmap.fromImage(qt_image)
            self.current_pixmap = pixmap
            
            # Scale to fit the image label size while maintaining aspect ratio (EXACT ORIGINAL APPROACH)
            scaled_pixmap = pixmap.scaled(
                self.image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Display the scaled image
            self.image_label.setPixmap(scaled_pixmap)
            
            # Show and update crosshair overlay position to match the displayed image
            self.crosshair_overlay.update_position()
            self.crosshair_overlay.show()
            
            # Update status
            checkbox_state = "CHECKED" if self.hide_renpy_checkbox.isChecked() else "UNCHECKED"
            self.status_label.setText(
                f"✅ Screenshot captured! Size: {pixmap.width()}x{pixmap.height()} | "
                f"Window: {window_info.title} | Renpy: {checkbox_state}"
            )
            self.status_label.setStyleSheet("color: #388e3c; padding: 10px; background-color: #f0f0f0; border-radius: 4px; margin: 10px 0;")
            
        except Exception as e:
            self.status_label.setText(f"❌ Failed to display screenshot: {str(e)}")
            self.status_label.setStyleSheet("color: #d32f2f; padding: 10px; background-color: #f0f0f0; border-radius: 4px; margin: 10px 0;")
    
    def send_h_key_to_window(self, hwnd: int) -> bool:
        """Send 'H' keystroke to window without bringing it to foreground - EXACT copy from ideas-lab."""
        try:
            # Method 1: PostMessage WM_KEYDOWN/WM_KEYUP (works without focus)
            try:
                result1 = ctypes.windll.user32.PostMessageW(hwnd, 0x0100, 0x48, 0x00230001)  # WM_KEYDOWN 'H'
                time.sleep(0.05)
                result2 = ctypes.windll.user32.PostMessageW(hwnd, 0x0101, 0x48, 0xC0230001)  # WM_KEYUP 'H'
                
                if result1 and result2:
                    return True
            except Exception:
                pass
            
            # Method 2: SendMessage (synchronous, works without focus)
            try:
                result1 = ctypes.windll.user32.SendMessageW(hwnd, 0x0100, 0x48, 0x00230001)  # WM_KEYDOWN
                time.sleep(0.05)
                result2 = ctypes.windll.user32.SendMessageW(hwnd, 0x0101, 0x48, 0xC0230001)  # WM_KEYUP
                
                if result1 is not None and result2 is not None:
                    return True
            except Exception:
                pass
            
            # Method 3: WM_CHAR approach (character-based input)
            try:
                result = ctypes.windll.user32.PostMessageW(hwnd, 0x0102, ord('h'), 0)  # WM_CHAR lowercase
                if result:
                    return True
                result = ctypes.windll.user32.PostMessageW(hwnd, 0x0102, ord('H'), 0)  # WM_CHAR uppercase
                if result:
                    return True
            except Exception:
                pass
            
            return False
            
        except Exception:
            return False
    
    def eventFilter(self, obj, event):
        """Handle keyboard events for the thumbnail list."""
        if obj == self.thumbnail_list and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Delete:
                current_item = self.thumbnail_list.currentItem()
                if current_item:
                    self.delete_selected_thumbnail(current_item)
                return True
        return super().eventFilter(obj, event)
    
    def delete_selected_thumbnail(self, item: QListWidgetItem):
        """Delete the selected thumbnail and its associated file."""
        try:
            image_path = item.data(Qt.ItemDataRole.UserRole)
            
            if os.path.exists(image_path):
                os.remove(image_path)
                
            row = self.thumbnail_list.row(item)
            self.thumbnail_list.takeItem(row)
            
            filename = os.path.basename(image_path)
            self.status_label.setText(f"🗑️ Deleted: {filename}")
            self.status_label.setStyleSheet("color: #ff5722; padding: 10px; background-color: #f0f0f0; border-radius: 4px; margin: 10px 0;")
            
            if self.thumbnail_list.count() == 0:
                self.image_label.clear()
                self.image_label.setText("Screenshot will appear here")
                self.current_pixmap = None
                self.current_image_path = None
                self.crosshair_overlay.hide()
                
        except Exception as e:
            self.status_label.setText(f"❌ Failed to delete image: {str(e)}")
            self.status_label.setStyleSheet("color: #f44336; padding: 10px; background-color: #f0f0f0; border-radius: 4px; margin: 10px 0;") 