 #!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
The Plot Thickens - Launcher

This script launches the main application.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and run the application
from app.main import main

if __name__ == "__main__":
    main()