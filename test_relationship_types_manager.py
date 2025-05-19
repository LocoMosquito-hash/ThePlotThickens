#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for the RelationshipTypesManager window.
"""

import sys
import qdarktheme
from PyQt6.QtWidgets import QApplication
from app.views.relationship_types_manager import RelationshipTypesManager

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Apply dark theme directly for the test script
    app.setStyleSheet(qdarktheme.load_stylesheet())
    window = RelationshipTypesManager()
    window.show()
    sys.exit(app.exec()) 