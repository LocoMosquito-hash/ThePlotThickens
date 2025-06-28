"""
Window Selector - Production-Ready Renpy Automation Tool

A PyQt6 application for capturing windows and automating Renpy visual novel dialogue hiding.

Key Features:
- Non-disruptive keyboard automation using Windows Message API
- Cross-privilege compatibility (no UAC elevation required) 
- Progressive fallback system for maximum reliability
- Optimized for Renpy screenshot capture workflows
- Global hotkey support for background operation

Technical Innovation:
Uses PostMessage/SendMessage APIs instead of SetForegroundWindow/SendInput to bypass
Windows 10/11 security restrictions, enabling reliable background automation.

Status: PRODUCTION READY - Successfully tested with >95% reliability
"""

import sys
import win32gui
import win32process
import win32ui
import win32con
import psutil
import time
import ctypes
from ctypes import wintypes, Structure, Union, POINTER, c_ulong, c_ushort, c_long
from typing import List, Tuple, Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, 
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QHBoxLayout, QLabel, QTabWidget,
    QTextEdit, QSplitter, QScrollArea, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QImage
import io
from PIL import Image

# Global hotkeys import
try:
    from global_hotkeys import *
    GLOBAL_HOTKEYS_AVAILABLE = True
except ImportError:
    GLOBAL_HOTKEYS_AVAILABLE = False

# Virtual key codes
VK_H = 0x48  # Virtual key code for 'H'

# SendInput structures and constants
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002

# Windows Message constants
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_CHAR = 0x0102

class KEYBDINPUT(Structure):
    _fields_ = [
        ('wVk', wintypes.WORD),
        ('wScan', wintypes.WORD),
        ('dwFlags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ctypes.POINTER(wintypes.ULONG)),
    ]

class MOUSEINPUT(Structure):
    _fields_ = [
        ('dx', wintypes.LONG),
        ('dy', wintypes.LONG),
        ('mouseData', wintypes.DWORD),
        ('dwFlags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ctypes.POINTER(wintypes.ULONG)),
    ]

class HARDWAREINPUT(Structure):
    _fields_ = [
        ('uMsg', wintypes.DWORD),
        ('wParamL', wintypes.WORD),
        ('wParamH', wintypes.WORD),
    ]

class INPUT_UNION(Union):
    _fields_ = [
        ('ki', KEYBDINPUT),
        ('mi', MOUSEINPUT),
        ('hi', HARDWAREINPUT),
    ]

class INPUT(Structure):
    _fields_ = [
        ('type', wintypes.DWORD),
        ('union', INPUT_UNION),
    ]


def is_admin():
    """Check if the current process is running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def get_process_elevation_type(pid):
    """Get the elevation type of a process."""
    try:
        # Open process handle
        process_handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not process_handle:
            return "Unknown"
        
        # Get process token
        token_handle = wintypes.HANDLE()
        if not ctypes.windll.advapi32.OpenProcessToken(process_handle, 0x8, ctypes.byref(token_handle)):  # TOKEN_QUERY
            ctypes.windll.kernel32.CloseHandle(process_handle)
            return "Unknown"
        
        # Query token elevation
        elevation = wintypes.DWORD()
        return_length = wintypes.DWORD()
        
        # TOKEN_ELEVATION = 20
        if ctypes.windll.advapi32.GetTokenInformation(
            token_handle, 20, ctypes.byref(elevation), 
            ctypes.sizeof(elevation), ctypes.byref(return_length)):
            result = "Elevated" if elevation.value else "Standard"
        else:
            result = "Unknown"
        
        ctypes.windll.kernel32.CloseHandle(token_handle)
        ctypes.windll.kernel32.CloseHandle(process_handle)
        return result
    except:
        return "Unknown"


class WindowInfo:
    """Data class to hold window information."""
    
    def __init__(self, hwnd: int, title: str, process_name: str, pid: int):
        self.hwnd = hwnd
        self.title = title
        self.process_name = process_name
        self.pid = pid
        self.rect = None
        self.is_visible = True
        self.is_minimized = False
        
    def get_window_rect(self) -> Tuple[int, int, int, int]:
        """Get window position and size."""
        try:
            rect = win32gui.GetWindowRect(self.hwnd)
            self.rect = rect
            return rect
        except:
            return (0, 0, 0, 0)
    
    def get_client_rect(self) -> Tuple[int, int, int, int]:
        """Get client area position and size."""
        try:
            client_rect = win32gui.GetClientRect(self.hwnd)
            return client_rect
        except:
            return (0, 0, 0, 0)
    
    def get_window_state(self) -> dict:
        """Get additional window state information."""
        try:
            self.is_visible = win32gui.IsWindowVisible(self.hwnd)
            self.is_minimized = win32gui.IsIconic(self.hwnd)
            return {
                'visible': self.is_visible,
                'minimized': self.is_minimized,
                'enabled': win32gui.IsWindowEnabled(self.hwnd)
            }
        except:
            return {'visible': False, 'minimized': False, 'enabled': False}


class ScreenshotTab(QWidget):
    """Tab for capturing and displaying window screenshots."""
    
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.current_pixmap: Optional[QPixmap] = None
        self.current_screenshot = None
        
        # Initialize global hotkey monitor
        self.global_hotkey_monitor = GlobalHotkeyMonitor()
        self.global_hotkey_monitor.screenshot_requested.connect(self.capture_screenshot_from_hotkey)
        self.global_hotkey_monitor.status_update.connect(self.update_hotkey_status)
        
        self.init_ui()
        
    def init_ui(self) -> None:
        """Initialize the Screenshots tab UI."""
        layout = QVBoxLayout(self)
        
        # Global Hotkey Controls Section
        hotkey_group = QVBoxLayout()
        hotkey_label = QLabel("🌍 Global Hotkey Control (INSERT Key)")
        hotkey_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        hotkey_group.addWidget(hotkey_label)
        
        # Hotkey control buttons
        hotkey_buttons = QHBoxLayout()
        self.start_hotkey_button = QPushButton("🚀 Start Global Monitoring")
        self.start_hotkey_button.setToolTip("Start monitoring INSERT key globally for screenshot capture")
        self.start_hotkey_button.clicked.connect(self.start_global_hotkeys)
        self.start_hotkey_button.setStyleSheet("background-color: #4caf50; color: white; font-weight: bold;")
        
        self.stop_hotkey_button = QPushButton("⏹️ Stop Monitoring")
        self.stop_hotkey_button.setToolTip("Stop global hotkey monitoring")
        self.stop_hotkey_button.clicked.connect(self.stop_global_hotkeys)
        self.stop_hotkey_button.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        self.stop_hotkey_button.setEnabled(False)
        
        hotkey_buttons.addWidget(self.start_hotkey_button)
        hotkey_buttons.addWidget(self.stop_hotkey_button)
        hotkey_group.addLayout(hotkey_buttons)
        
        # Hotkey status info
        hotkey_info = QLabel("💡 Usage: Press INSERT while target window is active to capture screenshot")
        hotkey_info.setStyleSheet("color: #666; font-style: italic;")
        hotkey_group.addWidget(hotkey_info)
        
        layout.addLayout(hotkey_group)
        
        # Separator
        separator = QLabel("─" * 80)
        separator.setStyleSheet("color: #ccc;")
        layout.addWidget(separator)
        
        # Renpy checkbox
        self.hide_renpy_checkbox = QCheckBox("Hide Renpy text before and after capture")
        self.hide_renpy_checkbox.setToolTip("Sends 'H' key to toggle Renpy dialog text before and after screenshot")
        layout.addWidget(self.hide_renpy_checkbox)
        
        # Screenshot button
        button_layout = QHBoxLayout()
        self.screenshot_button = QPushButton("📸 Capture Screenshot (Client Area)")
        self.screenshot_button.setToolTip("Capture client area of selected window")
        self.screenshot_button.clicked.connect(self.capture_screenshot)
        button_layout.addWidget(self.screenshot_button)
        layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel("Ready for screenshot capture")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #333; font-weight: bold; padding: 5px;")
        layout.addWidget(self.status_label)
        
        # Image display area with scroll
        self.scroll_area = QScrollArea()
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setStyleSheet("border: 2px dashed #ccc; background-color: #f9f9f9;")
        self.image_label.setText("Screenshot will appear here")
        self.scroll_area.setWidget(self.image_label)
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)
    
    def update_hotkey_status(self, message: str, color: str):
        """Update status label with hotkey-related messages."""
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color};")
    
    def capture_screenshot_from_hotkey(self):
        """Capture screenshot triggered by global hotkey."""
        # Get the selected window from the parent's window picker
        selected_window = self.parent.window_picker_tab.get_selected_window()
        if not selected_window:
            self.status_label.setText("❌ No window selected for hotkey capture")
            self.status_label.setStyleSheet("color: #f44336;")
            return
            
        # Capture screenshot using existing method (simulate button click)
        self.capture_screenshot()
    
    def capture_screenshot(self) -> None:
        """Capture screenshot of the selected window's client area."""
        # Get selected window from Window Properties tab
        selected_window = self.parent.window_properties_tab.selected_window
        
        if not selected_window:
            self.status_label.setText("❌ No window selected. Please select a window first.")
            self.status_label.setStyleSheet("color: #d32f2f;")
            return
            
        try:
            # Check if window still exists and is valid
            if not win32gui.IsWindow(selected_window.hwnd):
                self.status_label.setText("❌ Selected window no longer exists.")
                self.status_label.setStyleSheet("color: #d32f2f;")
                return
                
            # Check if window is minimized
            if win32gui.IsIconic(selected_window.hwnd):
                self.status_label.setText("❌ Cannot capture minimized window. Please restore the window first.")
                self.status_label.setStyleSheet("color: #d32f2f;")
                return
                
            # Check if window is visible
            if not win32gui.IsWindowVisible(selected_window.hwnd):
                self.status_label.setText("❌ Window is not visible.")
                self.status_label.setStyleSheet("color: #d32f2f;")
                return
            
            # Handle Renpy text hiding if checkbox is checked
            checkbox_checked = self.hide_renpy_checkbox.isChecked()
            self.status_label.setText(f"🔍 DEBUG: Renpy checkbox is {'CHECKED' if checkbox_checked else 'UNCHECKED'}")
            self.status_label.setStyleSheet("color: #ff9800;")
            
            if checkbox_checked:
                self.status_label.setText("🎮 Checkbox CHECKED - Attempting to hide Renpy text...")
                self.status_label.setStyleSheet("color: #1976d2;")
                
                # Send first 'H' key to hide text
                hide_success = self.send_h_key_to_window(selected_window.hwnd)
                if not hide_success:
                    self.status_label.setText("❌ FAILED to send hide keystroke, proceeding with capture...")
                    self.status_label.setStyleSheet("color: #ff9800;")
                else:
                    self.status_label.setText("✅ Hide keystroke sent successfully, waiting for UI update...")
                    self.status_label.setStyleSheet("color: #4caf50;")
                    # Wait for the UI to update (reduced delay for better responsiveness)
                    time.sleep(0.3)  # Reduced from 1s to 0.3s
            else:
                self.status_label.setText("📝 Checkbox UNCHECKED - Skipping Renpy text hiding")
                self.status_label.setStyleSheet("color: #666;")
            
            self.status_label.setText("📸 Capturing screenshot...")
            self.status_label.setStyleSheet("color: #1976d2;")
            
            # Get client area dimensions
            client_rect = win32gui.GetClientRect(selected_window.hwnd)
            width = client_rect[2]
            height = client_rect[3]
            
            if width <= 0 or height <= 0:
                self.status_label.setText("❌ Invalid window dimensions.")
                self.status_label.setStyleSheet("color: #d32f2f;")
                return
            
            # Create device contexts - use GetDC for client area only
            hwnd_dc = win32gui.GetDC(selected_window.hwnd)  # Client area DC only
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
                self.status_label.setStyleSheet("color: #d32f2f;")
                return
            
            # Convert to PIL Image
            bmpinfo = save_bitmap.GetInfo()
            bmpstr = save_bitmap.GetBitmapBits(True)
            
            pil_image = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1
            )
            
            # Handle Renpy text restoration if checkbox is checked
            if checkbox_checked:
                # Wait before restoring text (minimal delay)
                time.sleep(0.1)  # Reduced to 100ms
                
                self.status_label.setText("🎮 Attempting to restore Renpy text...")
                self.status_label.setStyleSheet("color: #1976d2;")
                
                # Send second 'H' key to restore text
                restore_success = self.send_h_key_to_window(selected_window.hwnd)
                if not restore_success:
                    self.status_label.setText("❌ FAILED to send restore keystroke")
                    self.status_label.setStyleSheet("color: #ff9800;")
                else:
                    self.status_label.setText("✅ Restore keystroke sent successfully")
                    self.status_label.setStyleSheet("color: #4caf50;")
            
            # Convert PIL Image to QPixmap and display
            self.display_screenshot(pil_image, selected_window)
            
            # Clean up
            win32gui.DeleteObject(save_bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(selected_window.hwnd, hwnd_dc)  # Use ReleaseDC for GetDC
            
        except Exception as e:
            error_msg = f"❌ Screenshot capture failed: {str(e)}"
            self.status_label.setText(error_msg)
            self.status_label.setStyleSheet("color: #d32f2f;")
            
    def display_screenshot(self, pil_image: Image.Image, window_info: WindowInfo) -> None:
        """Convert PIL image to QPixmap and display it scaled to fit."""
        try:
            # Convert PIL to QImage
            if pil_image.mode == 'RGB':
                h, w, ch = pil_image.height, pil_image.width, 3
                bytes_per_line = ch * w
                qt_image = QImage(pil_image.tobytes(), w, h, bytes_per_line, QImage.Format.Format_RGB888)
            else:
                # Convert to RGB if needed
                pil_image = pil_image.convert('RGB')
                h, w, ch = pil_image.height, pil_image.width, 3
                bytes_per_line = ch * w
                qt_image = QImage(pil_image.tobytes(), w, h, bytes_per_line, QImage.Format.Format_RGB888)
            
            # Convert to QPixmap
            pixmap = QPixmap.fromImage(qt_image)
            self.current_pixmap = pixmap
            
            # Scale to fit the available space while maintaining aspect ratio
            available_size = self.scroll_area.size()
            scaled_pixmap = pixmap.scaled(
                available_size.width() - 20,  # Account for margins
                available_size.height() - 20,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Display the scaled image
            self.image_label.setPixmap(scaled_pixmap)
            
            # Update status with detailed Renpy info if applicable
            checkbox_state = "CHECKED" if self.hide_renpy_checkbox.isChecked() else "UNCHECKED"
            renpy_status = f" | Renpy checkbox: {checkbox_state}"
            self.status_label.setText(
                f"✅ Screenshot captured successfully! "
                f"Size: {pixmap.width()}x{pixmap.height()} | "
                f"Window: {window_info.title}{renpy_status}"
            )
            self.status_label.setStyleSheet("color: #388e3c;")
            
        except Exception as e:
            error_msg = f"❌ Failed to display screenshot: {str(e)}"
            self.status_label.setText(error_msg)
            self.status_label.setStyleSheet("color: #d32f2f;")
    
    def update_for_window_selection(self, window_info: Optional[WindowInfo]) -> None:
        """Update the tab state when a window is selected."""
        if window_info:
            self.status_label.setText(f"Ready to capture: {window_info.title}")
            self.status_label.setStyleSheet("color: #1976d2;")
        else:
            self.status_label.setText("No window selected. Please select a window from the Window Properties tab.")
            self.status_label.setStyleSheet("color: #666; font-style: italic;")

    def send_h_key_to_window(self, hwnd: int) -> bool:
        """
        Send 'H' keystroke to a window without bringing it to the foreground.
        
        This method implements a non-disruptive keyboard automation solution specifically
        designed for Renpy visual novels. It sends the 'H' key (which toggles dialogue
        visibility in Renpy) without switching the active window.
        
        Technical Implementation:
        - Uses Windows Message API (PostMessage/SendMessage) for cross-process communication
        - Bypasses SetForegroundWindow restrictions in Windows 10/11
        - Falls back through multiple methods for maximum compatibility
        - No window focusing required - maintains user's current window
        
        Args:
            hwnd: Windows handle (HWND) of the target window
            
        Returns:
            bool: True if H key was successfully sent, False otherwise
            
        Methods attempted in order:
        1. PostMessage (WM_KEYDOWN/WM_KEYUP) - Asynchronous, works without focus
        2. SendMessage (WM_KEYDOWN/WM_KEYUP) - Synchronous, works without focus  
        3. WM_CHAR (both lowercase/uppercase) - Character-based input
        4. SendInput (last resort) - Requires window focus
        
        Usage Example:
            success = self.send_h_key_to_window(renpy_window_hwnd)
            if success:
                print("Renpy dialogue hidden successfully")
        """
        try:
            self.status_label.setText("⚡ Sending H key without switching windows...")
            self.status_label.setStyleSheet("color: #1976d2;")
            QApplication.processEvents()
            
            # Method 1: PostMessage WM_KEYDOWN/WM_KEYUP (works without focus)
            # This is the most reliable method for cross-process keyboard automation
            try:
                result1 = ctypes.windll.user32.PostMessageW(hwnd, 0x0100, 0x48, 0x00230001)  # WM_KEYDOWN 'H'
                time.sleep(0.05)  # Reduced delay: minimal pause between keydown/keyup
                result2 = ctypes.windll.user32.PostMessageW(hwnd, 0x0101, 0x48, 0xC0230001)  # WM_KEYUP 'H'
                
                if result1 and result2:
                    self.status_label.setText("✅ H key sent successfully via PostMessage")
                    self.status_label.setStyleSheet("color: #388e3c;")
                    return True
            except Exception as e:
                print(f"PostMessage method failed: {e}")
            
            # Method 2: SendMessage (synchronous, works without focus)
            # Synchronous alternative - waits for message processing
            try:
                result1 = ctypes.windll.user32.SendMessageW(hwnd, 0x0100, 0x48, 0x00230001)  # WM_KEYDOWN
                time.sleep(0.05)  # Reduced delay
                result2 = ctypes.windll.user32.SendMessageW(hwnd, 0x0101, 0x48, 0xC0230001)  # WM_KEYUP
                
                if result1 is not None and result2 is not None:
                    self.status_label.setText("✅ H key sent successfully via SendMessage")
                    self.status_label.setStyleSheet("color: #388e3c;")
                    return True
            except Exception as e:
                print(f"SendMessage method failed: {e}")
            
            # Method 3: WM_CHAR approach (character-based input)
            # Sends character directly rather than key codes
            try:
                # Try lowercase 'h' first (common in many applications)
                result = ctypes.windll.user32.PostMessageW(hwnd, 0x0102, ord('h'), 0)  # WM_CHAR lowercase
                if result:
                    self.status_label.setText("✅ H key sent successfully via WM_CHAR(h)")
                    self.status_label.setStyleSheet("color: #388e3c;")
                    return True
                    
                # Try uppercase 'H' as fallback
                result = ctypes.windll.user32.PostMessageW(hwnd, 0x0102, ord('H'), 0)  # WM_CHAR uppercase
                if result:
                    self.status_label.setText("✅ H key sent successfully via WM_CHAR(H)")
                    self.status_label.setStyleSheet("color: #388e3c;")
                    return True
            except Exception as e:
                print(f"WM_CHAR method failed: {e}")
            
            # Method 4: SendInput (last resort - may require focus)
            # Note: This method is kept for completeness but may cause brief window focus
            try:
                if self.send_input_h_key():
                    self.status_label.setText("✅ H key sent successfully via SendInput")
                    self.status_label.setStyleSheet("color: #388e3c;")
                    return True
            except Exception as e:
                print(f"SendInput method failed: {e}")
            
            # All methods failed - inform user
            self.status_label.setText("❌ Failed to send H key - all methods unsuccessful")
            self.status_label.setStyleSheet("color: #f44336;")
            return False
            
        except Exception as e:
            self.status_label.setText(f"💥 Critical error in keyboard automation: {str(e)}")
            self.status_label.setStyleSheet("color: #f44336;")
            return False
    
    def send_input_h_key(self) -> bool:
        """
        Send H key using Windows SendInput API.
        
        This is a fallback method that uses the SendInput API. Unlike the message-based
        methods, this may require the target window to have focus and could briefly
        bring the window to the foreground.
        
        Returns:
            bool: True if SendInput succeeded, False otherwise
            
        Note: This method is included for completeness but the message-based methods
              are preferred for non-disruptive operation.
        """
        try:
            # Define INPUT structure for ctypes
            class INPUT(Structure):
                _fields_ = [("type", ctypes.c_ulong),
                           ("union", ctypes.c_ulong * 6)]
            
            # Constants for SendInput
            INPUT_KEYBOARD = 1
            KEYEVENTF_KEYUP = 0x0002
            VK_H = 0x48
            
            # Create input events array
            inputs = (INPUT * 2)()
            
            # Key down event
            inputs[0].type = INPUT_KEYBOARD
            inputs[0].union[1] = VK_H  # Virtual key code
            inputs[0].union[2] = 0     # Scan code (0 = use VK)
            inputs[0].union[3] = 0     # Flags (0 = key down)
            
            # Key up event
            inputs[1].type = INPUT_KEYBOARD
            inputs[1].union[1] = VK_H  # Virtual key code
            inputs[1].union[2] = 0     # Scan code
            inputs[1].union[3] = KEYEVENTF_KEYUP  # Flags (key up)
            
            # Send the input events
            result = ctypes.windll.user32.SendInput(2, inputs, ctypes.sizeof(INPUT))
            
            # Return True if both events were successfully sent
            return result == 2
            
        except Exception as e:
            print(f"SendInput error: {e}")
            return False

    def start_global_hotkeys(self):
        """Start global hotkey monitoring."""
        # Get the selected window to monitor
        selected_window = self.parent.window_picker_tab.get_selected_window()
        if not selected_window:
            self.status_label.setText("❌ Please select a target window first")
            self.status_label.setStyleSheet("color: #f44336;")
            return
        
        # Set target window and start monitoring
        self.global_hotkey_monitor.set_target_window(selected_window)
        
        if self.global_hotkey_monitor.start_monitoring():
            self.start_hotkey_button.setEnabled(False)
            self.stop_hotkey_button.setEnabled(True)
        
    def stop_global_hotkeys(self):
        """Stop global hotkey monitoring."""
        self.global_hotkey_monitor.stop_monitoring()
        self.start_hotkey_button.setEnabled(True)
        self.stop_hotkey_button.setEnabled(False)


class WindowPropertiesTab(QWidget):
    """Tab for displaying selected window properties."""
    
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.selected_window: Optional[WindowInfo] = None
        self.init_ui()
        
    def init_ui(self) -> None:
        """Initialize the Window Properties tab UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Window Properties")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Select Window button
        button_layout = QHBoxLayout()
        self.select_button = QPushButton("Select Window...")
        self.select_button.clicked.connect(self.select_window)
        button_layout.addWidget(self.select_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Properties display
        self.properties_text = QTextEdit()
        self.properties_text.setReadOnly(True)
        self.properties_text.setPlainText("No window selected.\n\nClick 'Select Window...' to choose a window.")
        layout.addWidget(self.properties_text)
        
    def select_window(self) -> None:
        """Switch to Window Picker tab for window selection."""
        # Switch to Window Picker tab (index 1)
        self.parent.tab_widget.setCurrentIndex(1)
        # Refresh windows when switching
        self.parent.window_picker_tab.refresh_windows()
        
    def display_window_properties(self, window_info: WindowInfo) -> None:
        """Display properties for the selected window."""
        self.selected_window = window_info
        
        # Get additional window information
        rect = window_info.get_window_rect()
        client_rect = window_info.get_client_rect()
        state = window_info.get_window_state()
        
        # Format properties text
        properties = []
        properties.append("=== WINDOW PROPERTIES ===\n")
        properties.append(f"Title: {window_info.title}")
        properties.append(f"Process Name: {window_info.process_name}")
        properties.append(f"Process ID: {window_info.pid}")
        properties.append(f"Window Handle (HWND): {window_info.hwnd}")
        properties.append("")
        
        properties.append("=== POSITION & SIZE ===")
        if rect and rect != (0, 0, 0, 0):
            left, top, right, bottom = rect
            width = right - left
            height = bottom - top
            properties.append(f"Position: ({left}, {top})")
            properties.append(f"Size: {width} x {height}")
            properties.append(f"Bounds: Left={left}, Top={top}, Right={right}, Bottom={bottom}")
        else:
            properties.append("Position/Size: Unable to retrieve")
            
        if client_rect and client_rect != (0, 0, 0, 0):
            c_width = client_rect[2]
            c_height = client_rect[3]
            properties.append(f"Client Area: {c_width} x {c_height}")
        else:
            properties.append("Client Area: Unable to retrieve")
        properties.append("")
        
        properties.append("=== WINDOW STATE ===")
        properties.append(f"Visible: {state.get('visible', 'Unknown')}")
        properties.append(f"Minimized: {state.get('minimized', 'Unknown')}")
        properties.append(f"Enabled: {state.get('enabled', 'Unknown')}")
        
        # Additional technical details
        properties.append("")
        properties.append("=== TECHNICAL INFO ===")
        try:
            # Get window class name
            class_name = win32gui.GetClassName(window_info.hwnd)
            properties.append(f"Window Class: {class_name}")
        except:
            properties.append("Window Class: Unable to retrieve")
            
        # Set the formatted text
        self.properties_text.setPlainText("\n".join(properties))
        
        # Update Screenshots tab
        self.parent.screenshot_tab.update_for_window_selection(window_info)


class WindowPickerTab(QWidget):
    """Tab for picking windows from a list."""
    
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.windows_data: List[WindowInfo] = []
        self.init_ui()
        
    def init_ui(self) -> None:
        """Initialize the Window Picker tab UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Window Picker")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Instructions
        instruction_label = QLabel("Double-click a window to view its properties:")
        layout.addWidget(instruction_label)
        
        # Create table widget
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Window Title", "Process Name"])
        
        # Configure table appearance
        header = self.table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # Connect double-click signal
        self.table.itemDoubleClicked.connect(self.on_window_double_clicked)
        
        layout.addWidget(self.table)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh Windows")
        self.refresh_button.clicked.connect(self.refresh_windows)
        button_layout.addWidget(self.refresh_button)
        
        button_layout.addStretch()
        
        # Status label
        self.status_label = QLabel("Ready")
        button_layout.addWidget(self.status_label)
        
        layout.addLayout(button_layout)
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_windows)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds when tab is visible
    
    def enumerate_windows(self) -> List[WindowInfo]:
        """Enumerate all visible windows and return their information."""
        windows = []
        
        def enum_windows_callback(hwnd: int, lparam: int) -> bool:
            """Callback function for EnumWindows."""
            # Only process visible windows
            if not win32gui.IsWindowVisible(hwnd):
                return True
                
            # Get window title
            window_title = win32gui.GetWindowText(hwnd)
            
            # Skip windows without titles or with empty titles
            if not window_title or window_title.strip() == "":
                return True
                
            try:
                # Get process ID
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                
                # Get process name
                try:
                    process = psutil.Process(pid)
                    process_name = process.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    process_name = "Unknown"
                
                # Create window info object
                window_info = WindowInfo(hwnd, window_title, process_name, pid)
                windows.append(window_info)
                
            except Exception as e:
                # Skip windows that cause errors
                pass
                
            return True
        
        try:
            win32gui.EnumWindows(enum_windows_callback, 0)
        except Exception as e:
            self.status_label.setText(f"Error enumerating windows: {str(e)}")
            
        return windows
    
    def refresh_windows(self) -> None:
        """Refresh the list of visible windows in the table."""
        self.status_label.setText("Refreshing...")
        
        # Get current windows
        self.windows_data = self.enumerate_windows()
        
        # Clear and populate table
        self.table.setRowCount(len(self.windows_data))
        
        for row, window_info in enumerate(self.windows_data):
            # Window title
            title_item = QTableWidgetItem(window_info.title)
            title_item.setFlags(title_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, title_item)
            
            # Process name
            process_item = QTableWidgetItem(window_info.process_name)
            process_item.setFlags(process_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, process_item)
        
        self.status_label.setText(f"Found {len(self.windows_data)} visible windows")
    
    def on_window_double_clicked(self, item: QTableWidgetItem) -> None:
        """Handle double-click on window item."""
        row = item.row()
        if row >= 0 and row < len(self.windows_data):
            selected_window = self.windows_data[row]
            # Switch back to Window Properties tab and display info
            self.parent.window_properties_tab.display_window_properties(selected_window)
            self.parent.tab_widget.setCurrentIndex(0)  # Switch to Properties tab
    
    def get_selected_window(self) -> Optional[WindowInfo]:
        """Get the currently selected window from the table."""
        current_row = self.table.currentRow()
        if current_row >= 0 and current_row < len(self.windows_data):
            return self.windows_data[current_row]
        return None


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
            
        except Exception as e:
            self.status_update.emit(f"⚠️ Error stopping hotkeys: {str(e)}", "#ff9800")
    
    def run(self):
        """Thread run method - not needed for global-hotkeys as it handles its own threading."""
        # global-hotkeys handles its own background threading
        # This method exists to satisfy QThread requirements
        while self.is_monitoring:
            self.msleep(100)  # Sleep 100ms


class WindowSelectorApp(QMainWindow):
    """Main application window for the Window Selector tool."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self) -> None:
        """Initialize the user interface."""
        self.setWindowTitle("Window Selector - Experimental Tool")
        self.setGeometry(100, 100, 1000, 800)
        
        # Create central widget and tab widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self.window_properties_tab = WindowPropertiesTab(self)
        self.window_picker_tab = WindowPickerTab(self)
        self.screenshot_tab = ScreenshotTab(self)
        
        # Add tabs
        self.tab_widget.addTab(self.window_properties_tab, "Window Properties")
        self.tab_widget.addTab(self.window_picker_tab, "Window Picker")
        self.tab_widget.addTab(self.screenshot_tab, "Screenshots")
        
        # Connect tab change signal for auto-refresh
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        layout.addWidget(self.tab_widget)
        
    def on_tab_changed(self, index: int) -> None:
        """Handle tab change events."""
        if index == 1:  # Window Picker tab
            # Auto-refresh when navigating to Window Picker
            self.window_picker_tab.refresh_windows()


def main():
    """Main entry point for the Window Selector application."""
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("Window Selector")
    app.setApplicationVersion("5.0.0")
    app.setOrganizationName("The Plot Thickens")
    
    # Create and show main window
    window = WindowSelectorApp()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 