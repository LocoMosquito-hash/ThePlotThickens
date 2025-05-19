#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for the RelationshipTypesManager window.
"""

import sys
import qdarktheme
import sqlite3
from PyQt6.QtWidgets import QApplication
from app.views.relationship_types_manager import RelationshipTypesManager

if __name__ == "__main__":
    # Connect to the database
    db_conn = sqlite3.connect('the_plot_thickens.db')
    
    app = QApplication(sys.argv)
    # Apply dark theme directly for the test script
    app.setStyleSheet(qdarktheme.load_stylesheet())
    
    # Create the window with the database connection
    window = RelationshipTypesManager(db_conn=db_conn)
    window.show()
    
    # Run the application and cleanup on exit
    try:
        sys.exit(app.exec())
    finally:
        db_conn.close() 