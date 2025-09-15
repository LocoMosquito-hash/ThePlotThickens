 #!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
The Plot Thickens - Launcher

This script launches the main application.
"""

import sys
import os

# Fix Unicode encoding issues on Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and run the application
from app.main import main

if __name__ == "__main__":
    main()