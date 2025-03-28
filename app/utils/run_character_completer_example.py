#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Launch script for the CharacterCompleter example.

This script can be run directly to test the CharacterCompleter functionality.
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the example application
from app.utils.character_completer_example import CharacterCompleterExample
from PyQt6.QtWidgets import QApplication


def main():
    """Run the CharacterCompleter example application."""
    app = QApplication(sys.argv)
    window = CharacterCompleterExample()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 