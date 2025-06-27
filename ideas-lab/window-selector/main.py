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
from typing import List, Tuple, Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, 
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QHBoxLayout, QLabel, QTabWidget,
    QTextEdit, QSplitter, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap, QImage
import io
from PIL import Image


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
        
        # Capture button
        button_layout = QHBoxLayout()
        self.capture_button = QPushButton("Capture Screenshot (Client Area)")
        self.capture_button.clicked.connect(self.capture_screenshot)
        button_layout.addWidget(self.capture_button)
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
            
            # Convert PIL Image to QPixmap
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
            
            # Update status
            self.status_label.setText(
                f"✅ Screenshot captured successfully! "
                f"Original size: {pixmap.width()}x{pixmap.height()} | "
                f"Window: {window_info.title}"
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
    app.setApplicationVersion("3.0.0")
    app.setOrganizationName("The Plot Thickens")
    
    # Create and show main window
    window = WindowSelectorApp()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 