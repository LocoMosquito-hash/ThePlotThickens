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
import random
import string
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QCheckBox, QListWidget, QListWidgetItem, QMessageBox, QProgressDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter
)
from PyQt6.QtCore import Qt, QSettings, QThread, pyqtSignal, QTimer, QSize, QEvent, QPoint, QRect, QUrl
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

# Import video utilities for video thumbnail generation
from app.utils.video_utils import is_video_file, generate_video_thumbnail, get_video_info

# Import video playback components
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget


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
        
        # Initialize story context (will be set via set_story method)
        self.story_id: Optional[int] = None
        self.story_data: Optional[Dict[str, Any]] = None
        
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
        
        # Thumbnail list widget - now using QTableWidget
        self.thumbnail_table = QTableWidget()
        # Remove width constraints to allow horizontal expansion
        self.thumbnail_table.setMinimumWidth(300)  # Set a reasonable minimum width
        
        # Configure table structure
        self.thumbnail_table.setColumnCount(4)  # Thumbnail, Original Filename, Duplicate Count, and Dialog Context columns
        self.thumbnail_table.setHorizontalHeaderLabels(["Thumbnail", "Original Filename", "Duplicates", "Dialog Context"])
        
        # Configure headers
        vertical_header = self.thumbnail_table.verticalHeader()
        horizontal_header = self.thumbnail_table.horizontalHeader()
        
        if vertical_header:
            vertical_header.setVisible(False)
            vertical_header.setDefaultSectionSize(160)  # Thumbnail height + padding
            
        if horizontal_header:
            horizontal_header.setVisible(True)  # Show headers now that we have meaningful columns
            # Configure column sizing: Make all columns resizable
            horizontal_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Thumbnail - resizable
            horizontal_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # Filename - resizable
            horizontal_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Duplicates - resizable
            horizontal_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # Dialog Context - resizable
            
            # Set default column widths
            self.thumbnail_table.setColumnWidth(0, 200)  # Thumbnail column
            self.thumbnail_table.setColumnWidth(1, 150)  # Filename column
            self.thumbnail_table.setColumnWidth(2, 80)   # Duplicates column
            self.thumbnail_table.setColumnWidth(3, 200)  # Dialog Context column
        self.thumbnail_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.thumbnail_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # Configure appearance with dark theme compatibility
        self.thumbnail_table.setStyleSheet("""
            QTableWidget {
                background-color: #2b2b2b;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px;
                gridline-color: transparent;
                color: #ffffff;
            }
            QTableWidget::item {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 3px;
                margin: 2px;
                padding: 5px;
                color: #ffffff;
            }
            QTableWidget::item:selected {
                background-color: #0d7377;
                border: 2px solid #14a085;
                color: #ffffff;
            }
            QTableWidget::item:hover {
                background-color: #4a4a4a;
                border: 1px solid #14a085;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 8px;
                font-weight: bold;
            }
        """)
        
        # Connect signals
        self.thumbnail_table.cellClicked.connect(self.on_thumbnail_clicked)
        self.thumbnail_table.currentCellChanged.connect(self.on_thumbnail_selection_changed)
        self.thumbnail_table.installEventFilter(self)
        
        thumbnail_panel.addWidget(self.thumbnail_table)
        
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
        
        # Copy Media to Gallery button
        copy_to_gallery_button = QPushButton("📚 Copy Media to Gallery")
        copy_to_gallery_button.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """)
        copy_to_gallery_button.clicked.connect(self.copy_media_to_gallery)
        thumbnail_panel.addWidget(copy_to_gallery_button)
        
        # Create thumbnail panel widget
        thumbnail_widget = QWidget()
        thumbnail_widget.setLayout(thumbnail_panel)
        
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
        
        # Media display area (images and videos)
        media_layout = QVBoxLayout()
        media_label_title = QLabel("Media Preview")
        media_label_title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        media_layout.addWidget(media_label_title)
        
        # Image display
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
        media_layout.addWidget(self.scroll_area)
        
        # Video player setup
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(400, 300)
        self.video_widget.setStyleSheet("border: 2px solid #2196f3; background-color: #000;")
        self.video_widget.hide()  # Start hidden
        
        # Media player 
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        
        # Configure for looping
        self.media_player.mediaStatusChanged.connect(self._on_media_status_changed)
        self.media_player.positionChanged.connect(self._on_position_changed)
        
        media_layout.addWidget(self.video_widget)
        
        # Video controls
        self.video_controls_layout = QHBoxLayout()
        self.play_pause_button = QPushButton("⏸️ Pause")
        self.play_pause_button.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        self.play_pause_button.clicked.connect(self._toggle_play_pause)
        self.play_pause_button.hide()  # Start hidden
        
        self.video_controls_layout.addWidget(self.play_pause_button)
        self.video_controls_layout.addStretch()
        
        media_layout.addLayout(self.video_controls_layout)
        
        # Current media tracking
        self.current_media_path = None
        self.current_media_type = None
        
        right_layout.addLayout(media_layout)
        
        # Create right panel widget  
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        
        # Create a splitter to combine thumbnail panel and right panel
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(thumbnail_widget)
        self.splitter.addWidget(right_widget)
        
        # Set initial splitter proportions (thumbnail panel gets 1/3, media preview gets 2/3)
        self.splitter.setSizes([400, 800])  # Initial sizes for thumbnail and media preview
        
        main_layout.addWidget(self.splitter)
    
    def load_existing_images(self):
        """Load all existing images and videos from the image-stack folder."""
        if not os.path.exists(self.image_stack_folder):
            os.makedirs(self.image_stack_folder)
            return
        
        # Clear table before loading
        self.thumbnail_table.setRowCount(0)
        
        # Load all supported media files
        supported_extensions = ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.tiff',
                               '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.ogg', '.ogv')
        
        media_files = []
        for filename in os.listdir(self.image_stack_folder):
            if filename.lower().endswith(supported_extensions):
                full_path = os.path.join(self.image_stack_folder, filename)
                media_files.append(full_path)
        
        # Sort files by creation time (oldest first) for consistent ordering
        media_files.sort(key=lambda x: os.path.getctime(x))
        
        # Add thumbnails for each media file
        for media_path in media_files:
            self.add_thumbnail_to_table(media_path)
        
        # Update status based on what was loaded
        if media_files:
            # Count images and videos separately for better status reporting
            image_extensions = ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.tiff')
            video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.ogg', '.ogv')
            
            image_count = len([f for f in media_files if any(f.lower().endswith(ext) for ext in image_extensions)])
            video_count = len([f for f in media_files if any(f.lower().endswith(ext) for ext in video_extensions)])
            
            if video_count > 0:
                self.status_label.setText(f"📁 Loaded {image_count} images and {video_count} videos from image-stack folder")
            else:
                self.status_label.setText(f"📁 Loaded {image_count} images from image-stack folder")
            self.status_label.setStyleSheet("color: #2196f3;")

    def add_thumbnail_to_table(self, media_path: str):
        """Add a thumbnail to the table (supports both images and videos)."""
        try:
            # Check if media path already exists in the table to prevent duplicates
            for row in range(self.thumbnail_table.rowCount()):
                existing_item = self.thumbnail_table.item(row, 0)
                if existing_item and existing_item.data(Qt.ItemDataRole.UserRole) == media_path:
                    # Media already exists in the table, skip adding
                    return
            
            # Determine if this is a video file
            is_video = is_video_file(media_path)
            
            if is_video:
                # Generate video thumbnail
                thumbnail_pixmap = self._generate_video_thumbnail(media_path)
                media_type = "video"
            else:
                # Generate image thumbnail using PIL
                with Image.open(media_path) as img:
                    # Create thumbnail (180x180 max size while maintaining aspect ratio)
                    img.thumbnail((180, 180), Image.Resampling.LANCZOS)
                    
                    # Convert PIL Image to QPixmap
                    img_qt = img.convert('RGBA')
                    h, w, ch = img_qt.size[1], img_qt.size[0], 4
                    bytes_per_line = ch * w
                    qt_image = QImage(img_qt.tobytes(), w, h, bytes_per_line, QImage.Format.Format_RGBA8888)
                    thumbnail_pixmap = QPixmap.fromImage(qt_image)
                media_type = "image"
            
            # Add new row to table
            row_position = self.thumbnail_table.rowCount()
            self.thumbnail_table.insertRow(row_position)
            
            # Create a QLabel to hold the thumbnail
            thumbnail_label = QLabel()
            scaled_pixmap = thumbnail_pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            thumbnail_label.setPixmap(scaled_pixmap)
            thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            thumbnail_label.setStyleSheet("border: 1px solid #ccc; border-radius: 3px; margin: 2px; padding: 2px;")
            
            # Set the thumbnail as cell widget
            self.thumbnail_table.setCellWidget(row_position, 0, thumbnail_label)
            
            # Create table item to store data for thumbnail column
            item = QTableWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, media_path)  # Store full path
            item.setData(Qt.ItemDataRole.UserRole + 1, media_type)  # Store media type
            
            # Add tooltip
            if is_video:
                item.setToolTip(f"🎬 Click to play: {os.path.basename(media_path)}\nPress DELETE to remove")
            else:
                item.setToolTip(f"Click to view: {os.path.basename(media_path)}\nPress DELETE to remove")
            
            # Set the item in the thumbnail column
            self.thumbnail_table.setItem(row_position, 0, item)
            
            # Add original asset name to the second column (from metadata if available)
            original_asset_name = self._get_original_asset_name(media_path)
            filename_item = QTableWidgetItem(original_asset_name)
            filename_item.setFlags(filename_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make read-only
            filename_item.setToolTip(f"Original Ren'Py asset name: {original_asset_name}")
            
            # Store additional data in filename item for future use
            filename_item.setData(Qt.ItemDataRole.UserRole, media_path)  # Store full path for reference
            filename_item.setData(Qt.ItemDataRole.UserRole + 2, original_asset_name)  # Store original asset name
            
            self.thumbnail_table.setItem(row_position, 1, filename_item)
            
            # Add duplicate count to the third column (initially empty)
            duplicate_item = QTableWidgetItem("")
            duplicate_item.setFlags(duplicate_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make read-only
            duplicate_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.thumbnail_table.setItem(row_position, 2, duplicate_item)
            
            # Add dialog context to the fourth column (from metadata if available)
            dialog_context = self._get_dialog_context(media_path)
            dialog_item = QTableWidgetItem(dialog_context)
            dialog_item.setFlags(dialog_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make read-only
            dialog_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            
            # Set tooltip with full dialog context if it's truncated
            if len(dialog_context) > 50:  # If text is long, show full text in tooltip
                dialog_item.setToolTip(dialog_context)
            else:
                dialog_item.setToolTip("Dialog context that appears after this asset in the script")
            
            self.thumbnail_table.setItem(row_position, 3, dialog_item)
            
            # Adjust row height to fit thumbnail
            self.thumbnail_table.setRowHeight(row_position, 160)
            
            # Update duplicate counts for all rows
            self._update_duplicate_counts()
            
        except Exception as e:
            print(f"Error creating thumbnail for {media_path}: {e}")
            
    def _get_original_asset_name(self, media_path: str) -> str:
        """Get the original Ren'Py asset name from metadata file.
        
        Args:
            media_path: Path to the media file
            
        Returns:
            Original asset name if found in metadata, otherwise filename
        """
        try:
            import json
            
            # Check for metadata file
            base_path = os.path.splitext(media_path)[0]
            metadata_path = f"{base_path}.meta"
            
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    original_name = metadata.get('original_asset_name', '')
                    if original_name:
                        return original_name
                        
        except Exception as e:
            print(f"Warning: Could not read metadata for {media_path}: {e}")
        
        # Fallback to filename if no metadata or error
        return os.path.basename(media_path)
    
    def _get_dialog_context(self, media_path: str) -> str:
        """Get the dialog context from metadata file.
        
        Args:
            media_path: Path to the media file
            
        Returns:
            Dialog context if found in metadata, otherwise empty string
        """
        try:
            import json
            
            # Check for metadata file
            base_path = os.path.splitext(media_path)[0]
            metadata_path = f"{base_path}.meta"
            
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    dialog_context = metadata.get('dialog_context', '')
                    if dialog_context:
                        return dialog_context
                        
        except Exception as e:
            print(f"Warning: Could not read dialog context metadata for {media_path}: {e}")
        
        # Return empty string if no dialog context found
        return ""
    
    def _update_duplicate_counts(self):
        """Update duplicate counts for all rows in the table.
        
        For each row, count how many rows above it have the same original asset name.
        If count > 0, show the count in the third column; otherwise leave blank.
        """
        try:
            row_count = self.thumbnail_table.rowCount()
            
            for current_row in range(row_count):
                # Get the original asset name for the current row
                filename_item = self.thumbnail_table.item(current_row, 1)
                if not filename_item:
                    continue
                
                current_asset_name = filename_item.text()
                
                # Count occurrences of this asset name in rows above the current row
                duplicate_count = 0
                for check_row in range(current_row):
                    check_filename_item = self.thumbnail_table.item(check_row, 1)
                    if check_filename_item and check_filename_item.text() == current_asset_name:
                        duplicate_count += 1
                
                # Update the duplicate count column
                duplicate_item = self.thumbnail_table.item(current_row, 2)
                if duplicate_item:
                    if duplicate_count > 0:
                        duplicate_item.setText(str(duplicate_count))
                        duplicate_item.setToolTip(f"This asset appears {duplicate_count + 1} times total")
                    else:
                        duplicate_item.setText("")
                        duplicate_item.setToolTip("First occurrence of this asset")
                        
        except Exception as e:
            print(f"Error updating duplicate counts: {e}")
            
    def _generate_video_thumbnail(self, video_path: str) -> QPixmap:
        """Generate a static thumbnail for a video file.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            QPixmap containing the video thumbnail
        """
        try:
            import tempfile
            import os
            
            # Generate a temporary thumbnail file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_thumb_path = temp_file.name
            
            # Generate static thumbnail using video utilities (use_gif=False for PNG)
            success = generate_video_thumbnail(
                video_path, 
                temp_thumb_path, 
                max_dimension=180, 
                use_gif=False  # Generate static PNG thumbnail
            )
            
            if success and os.path.exists(temp_thumb_path):
                # Load the generated thumbnail
                thumbnail_pixmap = QPixmap(temp_thumb_path)
                
                # Clean up temporary file
                try:
                    os.unlink(temp_thumb_path)
                except:
                    pass  # Ignore cleanup errors
                
                if not thumbnail_pixmap.isNull():
                    return thumbnail_pixmap
            
            # Fallback: create a placeholder with video icon
            return self._create_video_placeholder_thumbnail()
            
        except Exception as e:
            print(f"Error generating video thumbnail for {video_path}: {e}")
            return self._create_video_placeholder_thumbnail()
            
    def _create_video_placeholder_thumbnail(self) -> QPixmap:
        """Create a placeholder thumbnail for videos when thumbnail generation fails.
        
        Returns:
            QPixmap containing a video placeholder icon
        """
        # Create a dark placeholder with video icon
        placeholder = QPixmap(180, 180)
        placeholder.fill(QColor(30, 30, 40))
        
        from PyQt6.QtGui import QPainter, QFont
        painter = QPainter(placeholder)
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        # Draw play icon (triangle)
        from PyQt6.QtGui import QPolygon
        from PyQt6.QtCore import QPoint
        play_triangle = QPolygon([
            QPoint(70, 60),
            QPoint(70, 120),
            QPoint(110, 90)
        ])
        painter.setBrush(QColor(255, 255, 255))
        painter.drawPolygon(play_triangle)
        
        # Draw "VIDEO" text
        painter.drawText(60, 140, "VIDEO")
        painter.end()
        
        return placeholder
    
    def _on_media_status_changed(self, status):
        """Handle media status changes for video looping."""
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            # Loop the video by seeking to the beginning
            self.media_player.setPosition(0)
            self.media_player.play()
    
    def _on_position_changed(self, position):
        """Handle position changes (currently unused but needed for connection)."""
        pass
    
    def _toggle_play_pause(self):
        """Toggle play/pause state of the video."""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.play_pause_button.setText("▶️ Play")
        else:
            self.media_player.play()
            self.play_pause_button.setText("⏸️ Pause")
    
    def _stop_video_playback(self):
        """Stop video playback and release media player resources to prevent file locking."""
        try:
            # Stop playback
            self.media_player.stop()
            
            # Clear the media source to release file lock
            self.media_player.setSource(QUrl())
            
            # Update UI
            self.play_pause_button.setText("▶️ Play")
            
            # Hide video components and show image placeholder
            self.video_widget.hide()
            self.play_pause_button.hide()
            self.scroll_area.show()
            
            # Clear image display
            self.image_label.clear()
            self.image_label.setText("Media preview will appear here")
            self.crosshair_overlay.hide()
            
            # Clear current media tracking
            self.current_media_path = None
            self.current_media_type = None
            
            print("[DEBUG] Video playback stopped and media player resources released")
            
        except Exception as e:
            print(f"[DEBUG] Error stopping video playback: {e}")
    
    def update_thumbnail_after_crop(self, image_path: str):
        """Update the thumbnail in the table after the image has been cropped."""
        try:
            # Find the thumbnail item with this image path
            for row in range(self.thumbnail_table.rowCount()):
                item = self.thumbnail_table.item(row, 0)
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
                        
                        # Update the thumbnail display
                        thumbnail_label = self.thumbnail_table.cellWidget(row, 0)
                        if isinstance(thumbnail_label, QLabel):
                            scaled_pixmap = thumbnail_pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                            thumbnail_label.setPixmap(scaled_pixmap)
                        
                        # Update filename in second column if needed (filename shouldn't change after crop)
                        filename_item = self.thumbnail_table.item(row, 1)
                        if filename_item:
                            filename = os.path.basename(image_path)
                            filename_item.setText(filename)
                            filename_item.setToolTip(f"Original filename: {filename}")
                    
                    print(f"[DEBUG] Thumbnail updated for cropped image: {image_path}")
                    break
                    
        except Exception as e:
            print(f"Error updating thumbnail for {image_path}: {e}")
    
    def on_thumbnail_clicked(self, row: int, column: int):
        """Handle thumbnail click to display image or play video."""
        item = self.thumbnail_table.item(row, 0)
        if not item:
            return
            
        media_path = item.data(Qt.ItemDataRole.UserRole)
        media_type = item.data(Qt.ItemDataRole.UserRole + 1)
        
        if media_path and os.path.exists(media_path):
            try:
                # Store current media info
                self.current_media_path = media_path
                self.current_media_type = media_type
                
                if media_type == "video":
                    # Handle video playback
                    self._display_video(media_path)
                else:
                    # Handle image display
                    self._display_image(media_path)
                    
            except Exception as e:
                self.status_label.setText(f"❌ Error loading media: {str(e)}")
                self.status_label.setStyleSheet("color: #f44336;")
                
    def _display_image(self, image_path: str):
        """Display an image in the preview area with crosshair overlay."""
        # Hide video components
        self.video_widget.hide()
        self.play_pause_button.hide()
        
        # Show image components
        self.scroll_area.show()
        
        # Load and display the image
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            self.current_pixmap = pixmap
            self.current_image_path = image_path
            
            # Scale to fit the image label size while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                self.image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.image_label.setPixmap(scaled_pixmap)
            
            # Show and update crosshair overlay position
            self.crosshair_overlay.update_position()
            self.crosshair_overlay.show()
            
            self.status_label.setText(f"📷 Viewing: {os.path.basename(image_path)}")
            self.status_label.setStyleSheet("color: #1976d2;")
    
    def _display_video(self, video_path: str):
        """Display and auto-play a video in the preview area."""
        # Hide image components
        self.scroll_area.hide()
        self.crosshair_overlay.hide()
        
        # Show video components
        self.video_widget.show()
        self.play_pause_button.show()
        
        # Load and play the video
        video_url = QUrl.fromLocalFile(os.path.abspath(video_path))
        self.media_player.setSource(video_url)
        
        # Auto-start playback
        self.media_player.play()
        self.play_pause_button.setText("⏸️ Pause")
        
        self.status_label.setText(f"🎬 Playing: {os.path.basename(video_path)}")
        self.status_label.setStyleSheet("color: #1976d2;")
    
    def on_thumbnail_selection_changed(self, current_row: int, current_column: int, previous_row: int, previous_column: int):
        """Handle thumbnail selection change."""
        if current_row >= 0:
            self.on_thumbnail_clicked(current_row, current_column)
    
    def clear_all_images(self):
        """Clear all images and videos from the directory and table."""
        from PyQt6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            "Clear All Media",
            "Are you sure you want to delete all screenshots and videos? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Remove all supported image and video files
                supported_extensions = ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.tiff',
                                      '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.ogg', '.ogv')
                for filename in os.listdir(self.image_stack_folder):
                    if filename.lower().endswith(supported_extensions):
                        os.remove(os.path.join(self.image_stack_folder, filename))
                
                # Clear the table and display
                self.thumbnail_table.setRowCount(0)
                self.image_label.clear()
                self.image_label.setText("Screenshot will appear here")
                self.current_pixmap = None
                self.current_image_path = None
                self.crosshair_overlay.hide()
                self.status_label.setText("🗑️ All media cleared")
                self.status_label.setStyleSheet("color: #ff5722;")
                
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to clear media: {e}")
    
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
        # Store story context for Gallery integration
        self.story_id = story_id
        self.story_data = story_data
        
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
        self.thumbnail_table.setRowCount(0)
        
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
                    self.add_thumbnail_to_table(filepath)
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
        """Handle keyboard events for the thumbnail table."""
        if obj == self.thumbnail_table and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Delete:
                current_row = self.thumbnail_table.currentRow()
                if current_row >= 0:
                    current_item = self.thumbnail_table.item(current_row, 0)
                    if current_item:
                        self.delete_selected_thumbnail(current_item, current_row)
                return True
        return super().eventFilter(obj, event)
    
    def delete_selected_thumbnail(self, item: QTableWidgetItem, row: int):
        """Delete the selected thumbnail and its associated file."""
        try:
            image_path = item.data(Qt.ItemDataRole.UserRole)
            
            # Stop any video playback first to prevent file locking issues
            # This ensures the file can be safely deleted even if it's currently playing
            self._stop_video_playback()
            
            if os.path.exists(image_path):
                os.remove(image_path)
                
            self.thumbnail_table.removeRow(row)
            
            # Update duplicate counts after removal
            self._update_duplicate_counts()
            
            filename = os.path.basename(image_path)
            self.status_label.setText(f"🗑️ Deleted: {filename}")
            self.status_label.setStyleSheet("color: #ff5722; padding: 10px; background-color: #f0f0f0; border-radius: 4px; margin: 10px 0;")
            
            if self.thumbnail_table.rowCount() == 0:
                self.image_label.clear()
                self.image_label.setText("Screenshot will appear here")
                self.current_pixmap = None
                self.current_image_path = None
                self.crosshair_overlay.hide()
                
        except Exception as e:
            self.status_label.setText(f"❌ Failed to delete image: {str(e)}")
            self.status_label.setStyleSheet("color: #f44336; padding: 10px; background-color: #f0f0f0; border-radius: 4px; margin: 10px 0;")
    
    def copy_media_to_gallery(self):
        """Copy all images from the stack to the Gallery."""
        try:
            # Stop any video playback and release media player resources first
            # This prevents file locking issues when copying video files
            self._stop_video_playback()
            
            # Check if we have a story context
            if not hasattr(self, 'story_id') or not self.story_id:
                QMessageBox.warning(self, "Error", "No story selected. Please select a story first.")
                return
            
            # Get all image paths from thumbnail table
            image_paths = []
            for i in range(self.thumbnail_table.rowCount()):
                item = self.thumbnail_table.item(i, 0)
                if item and item.data(Qt.ItemDataRole.UserRole):
                    image_paths.append(item.data(Qt.ItemDataRole.UserRole))
            
            if not image_paths:
                QMessageBox.information(self, "Info", "No images to copy to Gallery.")
                return
            
            # Count images and videos for better user information
            actual_images = [path for path in image_paths if not is_video_file(path)]
            video_count = len(image_paths) - len(actual_images)
            
            # Create confirmation message
            if video_count > 0 and len(actual_images) > 0:
                message = f"Copy {len(actual_images)} image(s) and {video_count} video(s) from the stack to the Gallery?\n\n"
                message += "Images will be saved as PNG files with thumbnails.\n"
                message += "Videos will be saved with animated GIF thumbnails.\n"
                message += "Media will be added to the current story's gallery with automatic thumbnails."
            elif video_count > 0:
                message = f"Copy {video_count} video(s) from the stack to the Gallery?\n\n"
                message += "Videos will be saved with animated GIF thumbnails.\n"
                message += "Media will be added to the current story's gallery."
            else:
                message = f"Copy {len(actual_images)} image(s) from the stack to the Gallery?\n\n"
                message += "Images will be saved as PNG files with thumbnails.\n"
                message += "Media will be added to the current story's gallery."
            
            reply = QMessageBox.question(
                self,
                "Copy Media to Gallery",
                message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            # Show simple progress dialog
            progress = QProgressDialog(
                f"Copying {len(image_paths)} files to Gallery...",
                "Cancel", 0, len(image_paths), self
            )
            progress.setWindowTitle("Copy to Gallery")
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumDuration(0)  # Show immediately
            progress.setValue(0)
            
            # Process each file (both images and videos)
            successful_copies = 0
            failed_copies = []
            
            for i, image_path in enumerate(image_paths):
                # Check if user cancelled
                if progress.wasCanceled():
                    progress.close()
                    QMessageBox.information(self, "Cancelled", 
                                          f"Copy operation cancelled. {successful_copies} files were copied successfully.")
                    return
                
                # Update progress
                file_type = "video" if is_video_file(image_path) else "image"
                progress.setLabelText(f"Copying {file_type} {i+1} of {len(image_paths)}...")
                progress.setValue(i)
                
                # Copy single file to Gallery
                try:
                    self._copy_single_image_to_gallery(image_path)
                    successful_copies += 1
                except Exception as e:
                    failed_copies.append((image_path, str(e)))
            
            # Close progress dialog
            progress.setValue(len(image_paths))
            progress.close()
            
            # Handle results
            if failed_copies and successful_copies == 0:
                # All failed
                self._handle_copy_errors(failed_copies, image_paths)
            elif failed_copies and successful_copies > 0:
                # Partial success
                QMessageBox.warning(
                    self,
                    "Partial Success",
                    f"Successfully copied {successful_copies} files to Gallery.\n"
                    f"{len(failed_copies)} files failed to copy.\n\n"
                    f"Failed files:\n" + "\n".join([os.path.basename(path) for path, _ in failed_copies[:5]])
                )
            else:
                # Complete success
                QMessageBox.information(
                    self,
                    "Success",
                    f"Successfully copied {successful_copies} files to Gallery!"
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to copy media to Gallery: {str(e)}")
            print(f"Error in copy_media_to_gallery: {e}")
    
    def _copy_single_image_to_gallery(self, image_path: str):
        """Copy a single image or video to the Gallery using the same process as Gallery's save_image_to_story."""
        # Import video utilities to check file type
        from app.utils.video_utils import is_video_file, generate_video_thumbnail
        import shutil
        
        # Load the file
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"File not found: {image_path}")
        
        # Check if this is a video file
        is_video = is_video_file(image_path)
        
        # Get the story data
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT * FROM stories WHERE id = ?", (self.story_id,))
        story_data = dict(cursor.fetchone())
        
        if not story_data:
            raise ValueError("Story data not found in database")
        
        # Get folder paths using the utility function
        from app.db_sqlite import get_story_folder_paths, ensure_story_folders_exist
        
        # Ensure all story folders exist
        ensure_story_folders_exist(story_data)
        
        # Get paths
        folder_paths = get_story_folder_paths(story_data)
        images_folder = folder_paths['images_folder']
        thumbnails_folder = folder_paths['thumbnails_folder']
        
        # Create folders if they don't exist
        os.makedirs(images_folder, exist_ok=True)
        os.makedirs(thumbnails_folder, exist_ok=True)
        
        # Generate unique filename with appropriate prefix
        timestamp = time.strftime("%Y%m%d%H%M%S")
        random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        
        if is_video:
            # Keep original extension for video files
            original_ext = os.path.splitext(image_path)[1]
            file_name = f"vid_{timestamp}_{random_string}{original_ext}"
            thumbnail_name = f"vid_{timestamp}_{random_string}.gif"  # Use GIF for video thumbnails
        else:
            # Use PNG for image files
            file_name = f"img_{timestamp}_{random_string}.png"
            thumbnail_name = file_name  # Same name for image thumbnails
        
        # Define full file paths
        gallery_file_path = os.path.join(images_folder, file_name)
        thumbnail_path = os.path.join(thumbnails_folder, thumbnail_name)
        
        if is_video:
            # Copy video file to gallery
            shutil.copy2(image_path, gallery_file_path)
            
            # Generate GIF thumbnail for video
            success = generate_video_thumbnail(
                image_path,
                thumbnail_path,
                max_dimension=320,
                use_gif=True
            )
            
            if not success:
                # If GIF generation failed, try PNG fallback
                thumbnail_name = f"vid_{timestamp}_{random_string}.png"
                thumbnail_path = os.path.join(thumbnails_folder, thumbnail_name)
                success = generate_video_thumbnail(
                    image_path,
                    thumbnail_path,
                    max_dimension=320,
                    use_gif=False
                )
                
                if not success:
                    raise IOError(f"Could not generate thumbnail for video: {image_path}")
            
            # Get video dimensions (approximate)
            try:
                video_info = get_video_info(image_path)
                width = video_info.get('width', 640) if video_info else 640
                height = video_info.get('height', 480) if video_info else 480
            except:
                width, height = 640, 480  # Default fallback
        else:
            # Handle regular image files
            # Load with PIL first, then convert to QImage for Gallery processing
            with Image.open(image_path) as pil_image:
                # Convert PIL to QImage
                if pil_image.mode != 'RGB':
                    pil_image = pil_image.convert('RGB')
                
                h, w = pil_image.height, pil_image.width
                bytes_per_line = 3 * w
                qt_image = QImage(pil_image.tobytes(), w, h, bytes_per_line, QImage.Format.Format_RGB888)
                
                if qt_image.isNull():
                    raise ValueError(f"Could not convert image to QImage: {image_path}")
            
            # Generate thumbnail using Gallery's method
            thumbnail_image = self._generate_thumbnail(qt_image)
            
            # Save the full image
            if not qt_image.save(gallery_file_path, "PNG"):
                raise IOError(f"Could not save image to {gallery_file_path}")
            
            # Save the thumbnail
            if not thumbnail_image.save(thumbnail_path, "PNG"):
                print(f"Warning: Could not save thumbnail to {thumbnail_path}")
            
            # Get image dimensions
            width = qt_image.width()
            height = qt_image.height()
        
        # Create timestamp
        now = datetime.now().isoformat()
        
        # Insert into database
        query = """
            INSERT INTO images (story_id, title, path, created_at, updated_at, width, height, is_featured, filename)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(
            query,
            (
                self.story_id,
                "Imported Video" if is_video else "Imported Image",  # title
                images_folder,         # path (store folder path)
                now,                   # created_at
                now,                   # updated_at
                width,                 # width
                height,                # height
                0,                     # is_featured (not NSFW)
                file_name              # filename
            )
        )
        
        # Commit changes
        self.db_conn.commit()
        
        print(f"Successfully copied {'video' if is_video else 'image'} {os.path.basename(image_path)} to Gallery as {file_name}")
    
    def _generate_thumbnail(self, image: QImage, max_dimension: int = 320) -> QImage:
        """Generate a thumbnail from the image (copied from Gallery's method)."""
        if image.isNull():
            return QImage()
        
        # Calculate thumbnail size while maintaining aspect ratio
        original_width = image.width()
        original_height = image.height()
        
        if original_width <= max_dimension and original_height <= max_dimension:
            # Image is already small enough
            return image.copy()
        
        # Calculate scaling factor
        scale_factor = min(max_dimension / original_width, max_dimension / original_height)
        
        # Calculate new dimensions
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        
        # Scale the image
        scaled_image = image.scaled(
            new_width, new_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        return scaled_image
    
    def _handle_copy_errors(self, failed_copies, original_paths):
        """Handle copy errors with retry/abort options."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Copy Errors")
        msg.setText(f"Failed to copy {len(failed_copies)} files to Gallery.")
        msg.setDetailedText("\n".join([f"{os.path.basename(path)}: {error}" for path, error in failed_copies]))
        msg.setIcon(QMessageBox.Icon.Warning)
        
        # Add custom buttons
        retry_button = msg.addButton("Retry Failed", QMessageBox.ButtonRole.ActionRole)
        abort_button = msg.addButton("Abort", QMessageBox.ButtonRole.RejectRole)
        msg.setDefaultButton(retry_button)
        
        msg.exec()
        
        if msg.clickedButton() == retry_button:
            # Retry only the failed files
            failed_paths = [path for path, _ in failed_copies]
            self._retry_failed_copies(failed_paths)
    
    def _retry_failed_copies(self, failed_paths):
        """Retry copying failed files."""
        if not failed_paths:
            return
        
        # Show progress for retry
        progress = QProgressDialog(
            f"Retrying {len(failed_paths)} failed files...",
            "Cancel", 0, len(failed_paths), self
        )
        progress.setWindowTitle("Retry Copy")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        
        successful_retries = 0
        still_failed = []
        
        for i, image_path in enumerate(failed_paths):
            if progress.wasCanceled():
                break
                
            file_type = "video" if is_video_file(image_path) else "image"
            progress.setLabelText(f"Retrying {file_type} {i+1} of {len(failed_paths)}...")
            progress.setValue(i)
            
            try:
                self._copy_single_image_to_gallery(image_path)
                successful_retries += 1
            except Exception as e:
                still_failed.append((image_path, str(e)))
        
        progress.setValue(len(failed_paths))
        progress.close()
        
        # Show retry results
        if still_failed:
            QMessageBox.warning(
                self,
                "Retry Results",
                f"Retry completed:\n"
                f"• Successfully copied: {successful_retries}\n"
                f"• Still failed: {len(still_failed)}"
            )
        else:
            QMessageBox.information(
                self,
                "Retry Success",
                f"Successfully copied all {successful_retries} files on retry!"
            ) 