#!/usr/bin/env python3
"""
Minimal UI test to check if PyQt6 works without complex graphics.
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QPushButton, QLabel, QComboBox, QTextEdit
)
from PyQt6.QtCore import Qt

class MinimalTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minimal PyQt6 Test")
        self.setGeometry(100, 100, 600, 400)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout(central_widget)
        
        # Simple components
        layout.addWidget(QLabel("PyQt6 Basic Test"))
        
        self.path_combo = QComboBox()
        self.path_combo.setEditable(True)
        self.path_combo.setPlaceholderText("Test combo box...")
        layout.addWidget(self.path_combo)
        
        self.test_button = QPushButton("Test Button")
        self.test_button.clicked.connect(self.on_test_button_clicked)
        layout.addWidget(self.test_button)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)
        
        self.output_text.append("UI initialized successfully!")
    
    def on_test_button_clicked(self):
        self.output_text.append("Button clicked - PyQt6 events working!")
        print("Button clicked successfully")

def main():
    app = QApplication(sys.argv)
    
    # Test basic PyQt6 functionality
    window = MinimalTestWindow()
    window.show()
    
    print("Basic UI test window created and shown")
    
    # Run for a short time then exit
    import threading
    import time
    
    def auto_exit():
        time.sleep(3)
        app.quit()
    
    # Auto exit after 3 seconds for testing
    timer_thread = threading.Thread(target=auto_exit)
    timer_thread.daemon = True
    timer_thread.start()
    
    exit_code = app.exec()
    print(f"Application exited with code: {exit_code}")
    return exit_code

if __name__ == "__main__":
    main() 