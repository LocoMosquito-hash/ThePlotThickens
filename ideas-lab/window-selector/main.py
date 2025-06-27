"""
Window Selector - Experimental Window Capture Tool
A PyQt6 application for listing and interacting with visible windows on Windows 11.
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
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap, QImage
import io
from PIL import Image

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
        self.init_ui()
        
    def init_ui(self) -> None:
        """Initialize the Screenshots tab UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Screenshots")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Elevation warning if not admin
        if not is_admin():
            warning_label = QLabel("⚠️ Running without administrator privileges. Keyboard automation may fail due to Windows 11 UAC security.")
            warning_label.setStyleSheet("color: #ff9800; background-color: #fff3e0; padding: 8px; border-radius: 4px;")
            warning_label.setWordWrap(True)
            layout.addWidget(warning_label)
        
        # Renpy checkbox
        self.hide_renpy_checkbox = QCheckBox("Hide Renpy text before and after capture")
        self.hide_renpy_checkbox.setToolTip("Sends 'H' key to toggle Renpy dialog text before and after screenshot")
        layout.addWidget(self.hide_renpy_checkbox)
        
        # Test keyboard automation button
        test_layout = QHBoxLayout()
        self.test_keyboard_button = QPushButton("🧪 Test Keyboard Automation (on Notepad)")
        self.test_keyboard_button.setToolTip("Opens Notepad and tests if keyboard automation works by typing 'H'")
        self.test_keyboard_button.clicked.connect(self.test_keyboard_automation)
        self.test_keyboard_button.setStyleSheet("background-color: #2196f3; color: white;")
        test_layout.addWidget(self.test_keyboard_button)
        test_layout.addStretch()
        layout.addLayout(test_layout)
        
        # Capture button
        button_layout = QHBoxLayout()
        self.capture_button = QPushButton("Capture Screenshot (Client Area)")
        self.capture_button.clicked.connect(self.capture_screenshot)
        button_layout.addWidget(self.capture_button)
        
        # Admin restart button
        if not is_admin():
            self.admin_button = QPushButton("Restart as Administrator")
            self.admin_button.setToolTip("Restart this application with administrator privileges for better keyboard automation")
            self.admin_button.clicked.connect(self.restart_as_admin)
            self.admin_button.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
            button_layout.addWidget(self.admin_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Status/Message label
        self.status_label = QLabel("No window selected. Please select a window from the Window Properties tab.")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)
        
        # Image display area with scroll
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setStyleSheet("border: 1px solid #ccc; background-color: #f9f9f9;")
        self.image_label.setText("No screenshot captured")
        
        self.scroll_area.setWidget(self.image_label)
        layout.addWidget(self.scroll_area)
    
    def restart_as_admin(self):
        """Restart the application with administrator privileges."""
        try:
            # Show confirmation dialog
            reply = QMessageBox.question(
                self, 
                'Restart as Administrator', 
                'This will restart the application with administrator privileges, which may resolve keyboard automation issues.\n\nContinue?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Get current script path
                script_path = sys.argv[0]
                
                # Use ShellExecute with "runas" to prompt for elevation
                ctypes.windll.shell32.ShellExecuteW(
                    None, 
                    "runas", 
                    sys.executable, 
                    f'"{script_path}"', 
                    None, 
                    1  # SW_SHOWNORMAL
                )
                
                # Close current instance
                QApplication.quit()
                
        except Exception as e:
            QMessageBox.warning(self, "Restart Failed", f"Failed to restart as administrator: {str(e)}")
    
    def test_keyboard_automation(self):
        """Test keyboard automation by opening Notepad and sending 'H' key."""
        try:
            import subprocess
            import time
            
            self.status_label.setText("🧪 Opening Notepad for keyboard test...")
            self.status_label.setStyleSheet("color: #1976d2;")
            
            # Open Notepad
            process = subprocess.Popen(['notepad.exe'])
            time.sleep(2)  # Wait for Notepad to open
            
            # Find Notepad window
            notepad_hwnd = None
            
            def find_notepad_callback(hwnd, lparam):
                nonlocal notepad_hwnd
                if win32gui.IsWindowVisible(hwnd):
                    window_text = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)
                    if 'Notepad' in window_text or class_name == 'Notepad':
                        notepad_hwnd = hwnd
                return True
            
            win32gui.EnumWindows(find_notepad_callback, None)
            
            if not notepad_hwnd:
                self.status_label.setText("❌ Could not find Notepad window")
                self.status_label.setStyleSheet("color: #d32f2f;")
                return
            
            self.status_label.setText("🎯 Found Notepad window, testing keyboard methods...")
            self.status_label.setStyleSheet("color: #1976d2;")
            
            # Test keyboard automation on Notepad
            success = self.send_h_key_to_window(notepad_hwnd)
            
            if success:
                self.status_label.setText("✅ Keyboard automation test SUCCESSFUL! Check Notepad for 'H' character.")
                self.status_label.setStyleSheet("color: #4caf50;")
                QMessageBox.information(self, "Test Result", "✅ Keyboard automation is working!\n\nCheck Notepad - you should see an 'H' character typed.\n\nThis means the keyboard methods work and the issue might be:\n1. Renpy-specific behavior\n2. Window focusing issues\n3. Timing problems")
            else:
                self.status_label.setText("❌ Keyboard automation test FAILED on Notepad")
                self.status_label.setStyleSheet("color: #d32f2f;")
                QMessageBox.warning(self, "Test Result", "❌ Keyboard automation failed even on Notepad.\n\nThis indicates a fundamental issue with keyboard automation on this system.\n\nTry:\n1. Running as Administrator\n2. Checking Windows security settings\n3. Temporarily disabling antivirus")
                
        except Exception as e:
            self.status_label.setText(f"❌ Test failed: {str(e)}")
            self.status_label.setStyleSheet("color: #d32f2f;")
    
    def send_h_key_to_window(self, hwnd: int) -> bool:
        """Send 'H' key to window using multiple methods with Windows restrictions bypass."""
        try:
            self.status_label.setText("🔑 DEBUG: Starting keyboard automation...")
            self.status_label.setStyleSheet("color: #1976d2;")
            QApplication.processEvents()
            
            # Method 1: Advanced SetForegroundWindow with AttachThreadInput bypass
            success = self.force_window_foreground_advanced(hwnd)
            if success:
                self.status_label.setText("✅ Window focused successfully using advanced method")
                self.status_label.setStyleSheet("color: #388e3c;")
            else:
                self.status_label.setText("⚠️ Advanced focus failed, trying fallback methods...")
                self.status_label.setStyleSheet("color: #ff9800;")
            
            QApplication.processEvents()
            time.sleep(0.5)  # Wait for focus to settle
            
            # Try multiple input methods
            methods_tried = []
            
            # Method A: SendInput API (works best when properly focused)
            try:
                if self.send_input_h_key(hwnd):
                    methods_tried.append("SendInput: SUCCESS ✅")
                    self.status_label.setText(f"🎯 SendInput method worked! H key sent successfully")
                    self.status_label.setStyleSheet("color: #388e3c;")
                    return True
                else:
                    methods_tried.append("SendInput: FAILED ❌")
            except Exception as e:
                methods_tried.append(f"SendInput: ERROR - {str(e)}")
            
            # Method B: PostMessage WM_KEYDOWN/WM_KEYUP
            try:
                result1 = ctypes.windll.user32.PostMessageW(hwnd, 0x0100, 0x48, 0x00230001)  # WM_KEYDOWN
                time.sleep(0.1)
                result2 = ctypes.windll.user32.PostMessageW(hwnd, 0x0101, 0x48, 0xC0230001)  # WM_KEYUP
                
                if result1 and result2:
                    methods_tried.append("PostMessage: SUCCESS ✅")
                    self.status_label.setText(f"🎯 PostMessage method worked! H key sent successfully")
                    self.status_label.setStyleSheet("color: #388e3c;")
                    return True
                else:
                    methods_tried.append("PostMessage: FAILED ❌")
            except Exception as e:
                methods_tried.append(f"PostMessage: ERROR - {str(e)}")
            
            # Method C: SendMessage (synchronous)
            try:
                result1 = ctypes.windll.user32.SendMessageW(hwnd, 0x0100, 0x48, 0x00230001)  # WM_KEYDOWN
                time.sleep(0.1)
                result2 = ctypes.windll.user32.SendMessageW(hwnd, 0x0101, 0x48, 0xC0230001)  # WM_KEYUP
                
                if result1 is not None and result2 is not None:
                    methods_tried.append("SendMessage: SUCCESS ✅")
                    self.status_label.setText(f"🎯 SendMessage method worked! H key sent successfully")
                    self.status_label.setStyleSheet("color: #388e3c;")
                    return True
                else:
                    methods_tried.append("SendMessage: FAILED ❌")
            except Exception as e:
                methods_tried.append(f"SendMessage: ERROR - {str(e)}")
            
            # Method D: WM_CHAR approach
            try:
                result = ctypes.windll.user32.PostMessageW(hwnd, 0x0102, ord('h'), 0)  # WM_CHAR lowercase
                if result:
                    methods_tried.append("WM_CHAR(h): SUCCESS ✅")
                    self.status_label.setText(f"🎯 WM_CHAR method worked! H key sent successfully")
                    self.status_label.setStyleSheet("color: #388e3c;")
                    return True
                else:
                    methods_tried.append("WM_CHAR(h): FAILED ❌")
                    
                # Try uppercase H
                result = ctypes.windll.user32.PostMessageW(hwnd, 0x0102, ord('H'), 0)  # WM_CHAR uppercase
                if result:
                    methods_tried.append("WM_CHAR(H): SUCCESS ✅")
                    self.status_label.setText(f"🎯 WM_CHAR(H) method worked! H key sent successfully")
                    self.status_label.setStyleSheet("color: #388e3c;")
                    return True
                else:
                    methods_tried.append("WM_CHAR(H): FAILED ❌")
            except Exception as e:
                methods_tried.append(f"WM_CHAR: ERROR - {str(e)}")
            
            # All methods failed
            failed_methods = "\n".join(methods_tried)
            self.status_label.setText(f"❌ All keyboard methods failed:\n{failed_methods}")
            self.status_label.setStyleSheet("color: #f44336;")
            
            return False
            
        except Exception as e:
            self.status_label.setText(f"💥 Critical error in keyboard automation: {str(e)}")
            self.status_label.setStyleSheet("color: #f44336;")
            return False
    
    def force_window_foreground_advanced(self, hwnd: int) -> bool:
        """Advanced window focusing that bypasses Windows SetForegroundWindow restrictions."""
        try:
            if not ctypes.windll.user32.IsWindow(hwnd):
                return False
            
            # Get current foreground window and thread info
            current_hwnd = ctypes.windll.user32.GetForegroundWindow()
            current_thread_id = ctypes.windll.user32.GetWindowThreadProcessId(current_hwnd, None)
            target_thread_id = ctypes.windll.user32.GetWindowThreadProcessId(hwnd, None)
            
            self.status_label.setText(f"🔍 Current window: {current_hwnd}, Target: {hwnd}")
            self.status_label.setStyleSheet("color: #1976d2;")
            QApplication.processEvents()
            
            # If same thread, simple SetForegroundWindow should work
            if current_thread_id == target_thread_id:
                result = ctypes.windll.user32.SetForegroundWindow(hwnd)
                if result:
                    self.status_label.setText("✅ Same thread - SetForegroundWindow worked")
                    return True
            
            # Different threads - use AttachThreadInput bypass
            self.status_label.setText("🔧 Different threads detected, using AttachThreadInput bypass...")
            self.status_label.setStyleSheet("color: #ff9800;")
            QApplication.processEvents()
            
            # Attach input processing
            attach_result = ctypes.windll.user32.AttachThreadInput(current_thread_id, target_thread_id, True)
            
            try:
                # Try to bring window to front
                ctypes.windll.user32.BringWindowToTop(hwnd)
                ctypes.windll.user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE or SW_SHOW
                result = ctypes.windll.user32.SetForegroundWindow(hwnd)
                
                if result:
                    self.status_label.setText("✅ AttachThreadInput bypass successful!")
                    self.status_label.setStyleSheet("color: #388e3c;")
                    return True
                else:
                    self.status_label.setText("⚠️ AttachThreadInput bypass attempted but SetForegroundWindow still failed")
                    self.status_label.setStyleSheet("color: #ff9800;")
                    
            finally:
                # Always detach threads
                if attach_result:
                    ctypes.windll.user32.AttachThreadInput(current_thread_id, target_thread_id, False)
            
            return False
            
        except Exception as e:
            self.status_label.setText(f"💥 Error in advanced focus: {str(e)}")
            self.status_label.setStyleSheet("color: #f44336;")
            return False
    
    def send_input_h_key(self, hwnd: int) -> bool:
        """Send H key using SendInput API with proper INPUT structure."""
        try:
            # Structures for SendInput
            class INPUT(Structure):
                _fields_ = [("type", ctypes.c_ulong),
                           ("union", ctypes.c_ulong * 6)]
            
            # Constants
            INPUT_KEYBOARD = 1
            KEYEVENTF_KEYUP = 0x0002
            VK_H = 0x48
            
            # Create input events
            inputs = (INPUT * 2)()
            
            # Key down
            inputs[0].type = INPUT_KEYBOARD
            inputs[0].union[1] = VK_H  # wVk
            inputs[0].union[2] = 0     # wScan
            inputs[0].union[3] = 0     # dwFlags
            
            # Key up  
            inputs[1].type = INPUT_KEYBOARD
            inputs[1].union[1] = VK_H  # wVk
            inputs[1].union[2] = 0     # wScan
            inputs[1].union[3] = KEYEVENTF_KEYUP  # dwFlags
            
            # Send the input
            result = ctypes.windll.user32.SendInput(2, inputs, ctypes.sizeof(INPUT))
            
            return result == 2  # Should return number of events successfully sent
            
        except Exception as e:
            print(f"SendInput error: {e}")
            return False
    
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
                    # Wait for the UI to update
                    time.sleep(1)  # 1 second delay
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
                # Wait before restoring text
                time.sleep(0.2)  # 200ms delay
                
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
        """Get the currently selected window information."""
        current_row = self.table.currentRow()
        if current_row >= 0 and current_row < len(self.windows_data):
            return self.windows_data[current_row]
        return None


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