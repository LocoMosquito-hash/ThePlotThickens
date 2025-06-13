#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Launcher script for Tier Maker.

This script launches the standalone tier maker application.
"""

import sys
import os

# Add the current directory to the Python path so we can import our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import and run the main application
from main import main

if __name__ == "__main__":
    main() 