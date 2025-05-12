#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to run the Character Badge Example for The Plot Thickens application.

This script initializes and displays the character badge example window.
"""

import sys
import os

# Add the project root directory to the system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import the example module and run the example
from PyQt6.QtWidgets import QApplication
from app.utils.character_badge_example import run_example

if __name__ == "__main__":
    # Create application if needed
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    # Run the example
    window = run_example()
    window.show()
    
    # Exit when done
    sys.exit(app.exec()) 