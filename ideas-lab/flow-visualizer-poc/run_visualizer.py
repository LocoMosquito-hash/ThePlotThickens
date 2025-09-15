#!/usr/bin/env python3
"""
Simple launcher for the Renpy Flow Visualizer POC.

Usage: python run_visualizer.py
"""

import sys
import os

# Fix Unicode encoding issues on Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from renpy_flow_visualizer_v2_main import main
    print("Starting Renpy Flow Visualizer POC (Clean Architecture)...")
    main()
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you have all required dependencies installed:")
    print("  pip install PyQt6 networkx")
    sys.exit(1)
except Exception as e:
    print(f"Error starting application: {e}")
    sys.exit(1) 